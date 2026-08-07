#!/usr/bin/env python3
"""graphify api shapes — backend ↔ frontend response-shape auditor.

Compares Go backend API response shapes against the TypeScript frontend's
expected response types and reports mismatches.

How it works
------------

1. **Go side** — walks every `.go` file under the target path (excluding
   ``*_test.go`` by default) and:

   - Parses every ``type X struct { ... }`` declaration, extracting the
     field name, Go type, and JSON tag (so we know the wire name and
     whether the field is omitempty / skipped via ``json:"-"``).
   - Parses every HTTP handler function (``func (h *XHandler) Method(
     w http.ResponseWriter, r *http.Request)``) and, inside its body,
     looks for the response-write call. Two patterns are recognised:

       * ``respondWithJSON(w, http.StatusOK, <payload>)`` — the project's
         own helper, defined in ``internal/api/handlers/helpers.go``.
       * ``json.NewEncoder(w).Encode(<payload>)`` — stdlib pattern used
         directly in a few handlers (e.g. ``usage.go``).

     The ``<payload>`` is then classified as one of:

       * ``struct_literal`` — a typed composite literal such as
         ``AuthResponse{...}`` or ``bootstrapStatusResponse{...}``.
       * ``map_literal`` — an anonymous ``map[string]interface{}{...}``
         (or ``map[string]string{...}``) literal. The keys become the
         top-level response fields and the values are resolved to a
         type by inspecting the enclosing handler's local variable
         declarations (``var x models.User`` / ``x := Y{...}``).
       * ``bare_identifier`` — a single variable name such as
         ``user`` (rare; resolved via the same variable lookup).
       * ``unknown`` — anything else (function calls, complex
         expressions). The endpoint is still listed but the shape is
         marked ``unknown`` so the report can flag it for manual review.

   - Parses the production router setup in ``cmd/server/main.go`` (and
     falls back to ``internal/api/handlers/testhelpers_test.go`` when
     ``main.go`` is absent) to map ``(HTTP method, full URL path) ->
     handler function``. Sub-routers built via ``parent.PathPrefix(
     "/x").Subrouter()`` are flattened so a route registered as
     ``protectedAuth.HandleFunc("/me", authHandler.GetMe)`` resolves
     to ``/api/auth/me``.

2. **TypeScript side** — parses ``frontend/src/api/client.ts`` and
   ``frontend/src/types/index.ts``:

   - For every ``api.<method><<ResponseType>>(url, ...)`` call (where
     ``method`` ∈ {get, post, put, patch, delete}) it captures the
     HTTP method, the URL (with template literals like ``${id}``
     normalised to ``{id}`` and ``/api`` prepended), and the response
     type — either a named type (``AuthResponse``) or an inline object
     literal (``{ user: User; memberships: MembershipInfo[] }``).
   - For every ``interface X { ... }`` and ``type X = ...`` declaration
     it captures the field name, TS type, and optionality.

3. **Comparison** — for each TS endpoint, finds the matching Go endpoint
   by ``(method, normalised_path)``. For each matched pair, resolves
   both response shapes to a flat ``{field_name: type}`` map and
   reports:

   - **Missing in Go** — TS expects a field the backend doesn't send
     (frontend bug waiting to happen).
   - **Extra in Go** — Go sends a field the frontend doesn't read
     (wasted bandwidth / accidental info leak).
   - **Type mismatch** — both sides have the field but the types
     disagree (e.g. Go ``int64`` vs TS ``string`` for an ID — the
     classic JS precision bug).

4. **Output** — emits a comparison table and per-endpoint detail in
   both Markdown (``API_SHAPES.md``) and JSON (``api-shapes.json``).

CLI
---

    python graphify_api_shapes.py [path] [--out report.md] [--json]
                                   [--include-tests]

``path`` defaults to the current working directory. When ``--out`` is
omitted and the script is run from the graphify workspace root, the
reports are written to ``public/api-shapes.json`` and
``public/API_SHAPES.md`` automatically.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


# ---------------------------------------------------------------------------
# Source masking helpers (so regex scans aren't fooled by strings/comments)
# ---------------------------------------------------------------------------

def mask_go_source(text: str) -> str:
    """Replace Go string/rune literals and comments with same-length
    whitespace so brace/paren matching is robust. Newlines are preserved
    so line numbers stay accurate.

    Length is preserved exactly — every input character maps to exactly
    one output character — so byte offsets in the masked source are
    identical to offsets in the raw source. This lets us locate a
    construct in the masked source (where brace matching is safe) and
    then slice the same byte range out of the raw source (where string
    contents are preserved).
    """
    out: List[str] = []
    i, n = 0, len(text)
    in_str = in_rune = in_line = in_block = False
    while i < n:
        c = text[i]
        nxt = text[i + 1] if i + 1 < n else ''
        if in_line:
            if c == '\n':
                in_line = False
                out.append(c)
            else:
                out.append(' ')
            i += 1
            continue
        if in_block:
            if c == '*' and nxt == '/':
                in_block = False
                out.append('  ')
                i += 2
                continue
            out.append('\n' if c == '\n' else ' ')
            i += 1
            continue
        if in_str:
            if c == '\\' and nxt:
                out.append('  ')
                i += 2
                continue
            if c == '"':
                in_str = False
                out.append('"')
                i += 1
                continue
            out.append('\n' if c == '\n' else ' ')
            i += 1
            continue
        if in_rune:
            if c == '\\' and nxt:
                out.append('  ')
                i += 2
                continue
            if c == "'":
                in_rune = False
                out.append("'")
                i += 1
                continue
            out.append(' ')
            i += 1
            continue
        if c == '/' and nxt == '/':
            in_line = True
            out.append('  ')
            i += 2
            continue
        if c == '/' and nxt == '*':
            in_block = True
            out.append('  ')
            i += 2
            continue
        if c == '"':
            in_str = True
            out.append('"')
            i += 1
            continue
        if c == "'":
            in_rune = True
            out.append("'")
            i += 1
            continue
        out.append(c)
        i += 1
    return ''.join(out)


def mask_ts_source(text: str) -> str:
    """Mask TS string literals, template literals, line and block
    comments. Template literals are tricky because they may contain
    nested ``${...}`` expressions — for our purposes (URL extraction)
    we keep the literal text of template strings intact so we can
    convert ``${id}`` to ``{id}`` later. We only strip comments and
    ordinary string literals.
    """
    out: List[str] = []
    i, n = 0, len(text)
    in_line = in_block = in_str = in_template = False
    template_depth = 0  # depth of ${ ... } inside template
    while i < n:
        c = text[i]
        nxt = text[i + 1] if i + 1 < n else ''
        if in_line:
            if c == '\n':
                in_line = False
                out.append(c)
            else:
                out.append(' ')
            i += 1
            continue
        if in_block:
            if c == '*' and nxt == '/':
                in_block = False
                out.append('  ')
                i += 2
                continue
            out.append('\n' if c == '\n' else ' ')
            i += 1
            continue
        if in_str:
            if c == '\\' and nxt:
                out.append(c)
                out.append(nxt)
                i += 2
                continue
            if c == '"':
                in_str = False
                out.append('"')
                i += 1
                continue
            out.append(c)
            i += 1
            continue
        if in_template:
            # Keep template content verbatim (we want ${id} preserved).
            if c == '\\' and nxt:
                out.append(c)
                out.append(nxt)
                i += 2
                continue
            if c == '`':
                in_template = False
                out.append('`')
                i += 1
                continue
            out.append(c)
            i += 1
            continue
        if c == '/' and nxt == '/':
            in_line = True
            i += 2
            continue
        if c == '/' and nxt == '*':
            in_block = True
            i += 2
            continue
        if c == '"':
            in_str = True
            out.append('"')
            i += 1
            continue
        if c == '`':
            in_template = True
            out.append('`')
            i += 1
            continue
        out.append(c)
        i += 1
    return ''.join(out)


def line_of(text: str, idx: int) -> int:
    return text.count('\n', 0, idx) + 1


def find_matching_brace(text: str, open_idx: int, open_ch: str = '{',
                        close_ch: str = '}') -> Tuple[Optional[str], int]:
    """Given ``text[open_idx] == open_ch``, return ``(body, end_idx)``
    where body is the text between the matching braces and ``end_idx``
    is one past the closing brace. Returns ``(None, -1)`` if unbalanced.
    """
    assert text[open_idx] == open_ch
    depth = 0
    i = open_idx
    n = len(text)
    while i < n:
        c = text[i]
        if c == open_ch:
            depth += 1
        elif c == close_ch:
            depth -= 1
            if depth == 0:
                return text[open_idx + 1:i], i + 1
        i += 1
    return None, -1


def find_matching_paren(text: str, open_idx: int) -> Tuple[Optional[str], int]:
    return find_matching_brace(text, open_idx, '(', ')')


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class GoField:
    name: str               # Go field name (e.g. "UserID")
    json_name: str          # wire name (e.g. "userId"); "-" if skipped
    go_type: str            # raw Go type (e.g. "string", "models.User", "*time.Time")
    is_omitempty: bool = False
    is_skipped: bool = False    # json:"-"
    is_optional: bool = False   # pointer type OR omitempty
    is_inline_embed: bool = False  # embedded struct with `json:",inline"`


@dataclass
class GoStruct:
    name: str               # struct type name (e.g. "User", "AuthResponse")
    file: str
    line: int
    package: str
    fields: List[GoField] = field(default_factory=list)


@dataclass
class GoResponseField:
    """A single top-level field in a Go response shape."""
    name: str                       # wire name (the JSON key)
    go_type: str                    # raw Go type (e.g. "models.User", "[]MemberResponse")
    struct_ref: Optional[str] = None    # name of referenced struct, if any
    is_array: bool = False


@dataclass
class GoResponseShape:
    """The shape of a single response call inside a handler."""
    kind: str                       # "struct_literal" | "map_literal" | "bare_identifier" | "unknown"
    struct_name: Optional[str] = None    # for struct_literal kind
    fields: List[GoResponseField] = field(default_factory=list)    # for map_literal kind
    raw: str = ""                   # the raw payload expression (truncated)


@dataclass
class GoHandler:
    name: str                       # "AuthHandler.Login"
    file: str
    line: int
    body: str = ""                  # function body (masked source)
    responses: List[GoResponseShape] = field(default_factory=list)


@dataclass
class GoRoute:
    method: str
    path: str                       # full path including /api prefix
    handler_func: str               # "AuthHandler.Login"
    file: str
    line: int


@dataclass
class TSField:
    name: str
    ts_type: str                    # raw type text (e.g. "string", "User", "MembershipInfo[]")
    is_optional: bool = False
    struct_ref: Optional[str] = None    # name of referenced interface/type, if any
    is_array: bool = False


@dataclass
class TSType:
    name: str
    file: str
    line: int
    kind: str                       # "interface" | "type_alias"
    fields: List[TSField] = field(default_factory=list)
    raw: str = ""


@dataclass
class TSEndpoint:
    method: str                     # "GET" | "POST" | ...
    path: str                       # normalised, with /api prefix
    response_type: str              # raw response type text
    response_kind: str              # "named" | "inline" | "unknown"
    response_fields: List[TSField] = field(default_factory=list)
    # for inline: the parsed fields; for named: the looked-up fields
    file: str = ""
    line: int = 0
    api_group: str = ""             # "authApi" / "tenantApi" / ...
    method_name: str = ""           # "register" / "login" / ...


@dataclass
class Comparison:
    method: str
    path: str
    go_handler: Optional[str]
    go_file: Optional[str]
    go_response_kind: str
    go_struct: Optional[str]
    go_fields: List[GoResponseField]
    ts_response_type: str
    ts_fields: List[TSField]
    missing_in_go: List[str]        # TS field names absent from Go
    extra_in_go: List[str]          # Go field names absent from TS
    type_mismatches: List[Dict[str, str]]   # {field, go_type, ts_type, note}
    status: str                     # "ok" | "missing_in_go" | "extra_in_go" | "type_mismatch" | "no_go_handler" | "unknown_go_shape"


# ---------------------------------------------------------------------------
# Go struct flattener integration
# ---------------------------------------------------------------------------
#
# The Python regex-based struct parser in this file cannot see through
# embedded structs (a struct field whose type is another struct is
# "embedded" and its fields are flattened into the outer struct by Go's
# JSON marshalling). The Go tool at
# ``scripts/go/graphify_struct_flattener/main.go`` uses go/types to do
# this properly. We invoke it as a subprocess and load the JSON output
# to get an accurate ``{struct_name: set(json_field_names)}`` map.

# Path to the Go struct flattener source. Resolved relative to this
# script so the tool works regardless of the current working directory.
STRUCT_FLATTENER_PATH = Path(__file__).resolve().parent / 'go' / 'graphify_struct_flattener' / 'main.go'

# Path to the Go filter tracer source.
FILTER_TRACER_PATH = Path(__file__).resolve().parent / 'go' / 'graphify_filter_tracer' / 'main.go'


def load_go_structs(repo_path: Path) -> Dict[str, Set[str]]:
    """Run the Go struct flattener over the backend module and return a
    ``{struct_name: set(json_field_names)}`` map.

    The flattener resolves embedded struct fields recursively, so the
    returned field set includes fields inherited from embedded types
    (which the regex-based parser in this file cannot see).

    The Go tool is invoked as ``cd {repo}/backend && go run
    <flattener> -out /tmp/structs.json``. If the backend directory or
    Go toolchain is unavailable, an empty dict is returned (and the
    comparison falls back to the regex-based struct map).
    """
    env = os.environ.copy()
    go_path = Path('/home/z/.local/go/bin')
    if go_path.exists():
        env['PATH'] = f'{go_path}:{env.get("PATH", "")}'
    env.setdefault('GOTOOLCHAIN', 'auto')

    backend_dir = repo_path / 'backend'
    if not backend_dir.is_dir():
        # Some repos may not have a backend/ subdir — fall back to repo root.
        backend_dir = repo_path
    if not STRUCT_FLATTENER_PATH.is_file():
        print(
            f'  ! struct flattener not found at {STRUCT_FLATTENER_PATH}',
            file=sys.stderr,
        )
        return {}

    out_file = Path('/tmp/graphify-structs.json')
    cmd = [
        'go', 'run', str(STRUCT_FLATTENER_PATH),
        '-out', str(out_file),
    ]
    print(
        f'  Running Go struct flattener (cd {backend_dir} && go run ...)',
        file=sys.stderr,
    )
    try:
        result = subprocess.run(
            cmd, cwd=str(backend_dir), env=env,
            capture_output=True, text=True, timeout=300,
        )
    except FileNotFoundError as exc:
        print(f'  ! go executable not found: {exc}', file=sys.stderr)
        return {}
    except subprocess.TimeoutExpired:
        print('  ! struct flattener timed out after 300s', file=sys.stderr)
        return {}
    if result.returncode != 0:
        print(
            f'  ! struct flattener exited {result.returncode}: '
            f'{result.stderr.strip()[:500]}',
            file=sys.stderr,
        )
        return {}
    if not out_file.is_file():
        print(f'  ! struct flattener did not produce {out_file}', file=sys.stderr)
        return {}

    try:
        data = json.loads(out_file.read_text(encoding='utf-8'))
    except Exception as exc:
        print(f'  ! could not parse struct flattener output: {exc}', file=sys.stderr)
        return {}

    out: Dict[str, Set[str]] = {}
    for entry in data:
        name = entry.get('name', '')
        if not name:
            continue
        fields: Set[str] = set()
        for f in entry.get('fields', []):
            jn = f.get('jsonName', '')
            if jn and jn != '-':
                fields.add(jn)
            elif f.get('name'):
                # No json tag — Go uses the field name as the wire name.
                # Only include exported fields (uppercase initial).
                fn = f['name']
                if fn[:1].isupper():
                    fields.add(fn)
        # Merge with any existing entry (structs can be defined in
        # multiple files; first definition wins for the regex-based
        # map, but the flattener is authoritative).
        out.setdefault(name, set()).update(fields)
    print(
        f'  Loaded {len(out)} flattened Go structs '
        f'({sum(len(v) for v in out.values())} total fields)',
        file=sys.stderr,
    )
    return out


def load_go_filters(repo_path: Path) -> Dict[str, List[str]]:
    """Run the Go filter tracer and return a ``{function_key: fields}`` map.

    The function key is ``"file:line"`` so callers can look up the
    dynamic filter fields for any MongoDB query by its source location.

    The tracer uses go/ssa to follow ``filter["x"] = y`` patterns and
    struct-typed InsertOne arguments, so the returned fields include
    dynamically constructed filter keys (which the regex-based parser
    cannot see).
    """
    env = os.environ.copy()
    go_path = Path('/home/z/.local/go/bin')
    if go_path.exists():
        env['PATH'] = f'{go_path}:{env.get("PATH", "")}'
    env.setdefault('GOTOOLCHAIN', 'auto')

    backend_dir = repo_path / 'backend'
    if not backend_dir.is_dir():
        backend_dir = repo_path
    if not FILTER_TRACER_PATH.is_file():
        print(
            f'  ! filter tracer not found at {FILTER_TRACER_PATH}',
            file=sys.stderr,
        )
        return {}

    out_file = Path('/tmp/graphify-filters.json')
    cmd = [
        'go', 'run', str(FILTER_TRACER_PATH),
        '-out', str(out_file),
    ]
    print(
        f'  Running Go filter tracer (cd {backend_dir} && go run ...)',
        file=sys.stderr,
    )
    try:
        result = subprocess.run(
            cmd, cwd=str(backend_dir), env=env,
            capture_output=True, text=True, timeout=600,
        )
    except FileNotFoundError as exc:
        print(f'  ! go executable not found: {exc}', file=sys.stderr)
        return {}
    except subprocess.TimeoutExpired:
        print('  ! filter tracer timed out after 600s', file=sys.stderr)
        return {}
    if result.returncode != 0:
        print(
            f'  ! filter tracer exited {result.returncode}: '
            f'{result.stderr.strip()[:500]}',
            file=sys.stderr,
        )
        return {}
    if not out_file.is_file():
        print(f'  ! filter tracer did not produce {out_file}', file=sys.stderr)
        return {}

    try:
        data = json.loads(out_file.read_text(encoding='utf-8'))
    except Exception as exc:
        print(f'  ! could not parse filter tracer output: {exc}', file=sys.stderr)
        return {}

    # Key by file:line so callers can look up dynamic filter fields by
    # the source location of the query call. Each function report may
    # have multiple findings; we collect all fields from all findings
    # whose method is "literal" or "map_update" (struct_type findings
    # describe InsertOne documents, not query filters).
    out: Dict[str, List[str]] = {}
    for entry in data:
        file = entry.get('file', '')
        line = entry.get('line', 0)
        if not file:
            continue
        key = f'{file}:{line}'
        fields: List[str] = []
        for finding in entry.get('findings', []):
            method = finding.get('method', '')
            if method not in ('literal', 'map_update'):
                continue
            for f in finding.get('fields', []):
                if f and not f.startswith('$') and f not in fields:
                    fields.append(f)
        if fields:
            out.setdefault(key, []).extend(fields)
    print(
        f'  Loaded filter tracer data for {len(out)} functions',
        file=sys.stderr,
    )
    return out


# ---------------------------------------------------------------------------
# Map-response field extractor and local wrapper struct scanner
# ---------------------------------------------------------------------------

# A `map[string]interface{}{...}` or `map[string]any{...}` literal.
# Captures nothing — the keys are inside the brace body.
RE_MAP_RESPONSE_LITERAL = re.compile(
    r'\bmap\s*\[\s*string\s*\]\s*(?:interface\s*\{\s*\}|any|object)\s*\{'
)

# A `type X struct {` declaration. Matches both top-level and local
# (function-scoped) definitions. Captures the type name.
RE_LOCAL_TYPE_STRUCT = re.compile(
    r'\btype\s+(?P<name>[A-Za-z]\w*)\s+struct\s*\{'
)

# A field declaration inside a struct body. Same shape as the top-level
# struct field regex but reused here for local types.
RE_LOCAL_STRUCT_FIELD = re.compile(
    r'^\s*(?P<name>[A-Z]\w*)\s+(?P<type>[^\s`].*?)'
    r'(?:\s+`(?P<tag>[^`]*)`)?\s*$'
)


def find_map_response_fields(content: str, func_name: str) -> Set[str]:
    """Scan a handler function body for ``map[string]interface{}{...}`` or
    ``map[string]any{...}`` literals and extract all string keys.

    Returns the set of field names sent via map responses in the
    handler. This supplements the existing ``_parse_handler_responses``
    logic which already extracts map keys — we re-scan here so callers
    can ask "what fields does this handler send via map responses?"
    without re-running the full response classification.

    ``func_name`` is the handler name (e.g. ``"PlansHandler.ListPlansPublic"``)
    used to locate the handler body. If the handler can't be located,
    an empty set is returned.
    """
    out: Set[str] = set()
    body = _extract_handler_body(content, func_name)
    if not body:
        return out
    # Mask comments and strings so brace matching is safe. We don't
    # need to preserve raw contents because we only care about quoted
    # keys, which are visible in the masked source too (mask replaces
    # the contents with spaces but keeps the quotes — actually the
    # masker blanks the contents, so we re-slice from the raw body).
    masked = mask_go_source(body)
    for m in RE_MAP_RESPONSE_LITERAL.finditer(masked):
        brace_idx = m.end() - 1
        # find_matching_brace operates on the masked source so braces
        # inside strings don't confuse it.
        inner_masked, _ = find_matching_brace(masked, brace_idx, '{', '}')
        if inner_masked is None:
            continue
        # Re-slice the same byte range from the raw body so string
        # keys are preserved.
        inner_raw = body[brace_idx + 1: brace_idx + 1 + len(inner_masked)]
        # Extract all "key": ... patterns at depth 0.
        for km in re.finditer(r'"([^"]+)"\s*:', inner_raw):
            key = km.group(1)
            if key and not key.startswith('$'):
                out.add(key)
    return out


def find_local_wrapper_structs(content: str,
                               func_name: str) -> List[Tuple[str, Set[str]]]:
    """Scan the file (and any handler function body in it) for local
    ``type X struct { ... }`` definitions and extract their fields.

    Returns a list of ``(wrapper_name, field_names)`` pairs. The scan
    covers the whole file content (local types are often defined in
    a sibling handler in the same file — e.g. ``mediaItem`` is defined
    in ``ListMedia`` but used as the conceptual response shape for
    ``UploadMedia`` in the same file).

    ``func_name`` is the handler name (e.g. ``"BrandingHandler.UploadMedia"``)
    used for context — currently informational only.
    """
    out: List[Tuple[str, Set[str]]] = []
    masked = mask_go_source(content)
    for m in RE_LOCAL_TYPE_STRUCT.finditer(masked):
        name = m.group('name')
        brace_idx = masked.find('{', m.start())
        if brace_idx == -1:
            continue
        body, _ = find_matching_brace(masked, brace_idx, '{', '}')
        if body is None:
            continue
        # Re-slice from the raw source so struct tags are preserved.
        raw_body = content[brace_idx + 1: brace_idx + 1 + len(body)]
        fields: Set[str] = set()
        for line in raw_body.splitlines():
            f = _parse_local_struct_field_line(line)
            if f:
                fields.add(f)
        if fields:
            out.append((name, fields))
    return out


def _parse_local_struct_field_line(line: str) -> Optional[str]:
    """Parse a single line from a local struct body and return the
    JSON wire name (or None if the line isn't a field declaration).
    """
    s = line.strip()
    if not s or s.startswith('//'):
        return None
    if s in {'{', '}', '};'}:
        return None
    # Embedded field (just a type name, no field name, no tag) — skip
    # (the flattener handles these via go/types; we can't reliably
    # resolve them from the regex alone).
    if '`' not in s and re.match(r'^[A-Z]\w*\.?[A-Z]\w*$', s):
        return None
    m = RE_LOCAL_STRUCT_FIELD.match(s)
    if not m:
        # Fall back to a permissive split on the backtick.
        parts = s.split('`', 1)
        if len(parts) != 2:
            return None
        head, tag = parts
        bits = head.strip().split(None, 1)
        if len(bits) != 2:
            return None
        name = bits[0]
        tag_str = tag.strip()
    else:
        name = m.group('name')
        tag_str = m.group('tag') or ''
    if not name:
        return None
    jm = RE_JSON_TAG.search(tag_str)
    if jm:
        val = jm.group('val')
        if val == '-':
            return None
        bits = val.split(',', 1)
        return bits[0] or None
    # No json tag — Go uses the field name as the wire name.
    return name


def _extract_handler_body(content: str, func_name: str) -> Optional[str]:
    """Extract the body of a handler function from ``content``.

    ``func_name`` is the ``Receiver.Method`` label (e.g.
    ``"PlansHandler.ListPlansPublic"``). Returns the masked body text
    (between the outer ``{`` and ``}`` of the function), or None if
    the handler can't be found.
    """
    if not func_name or '.' not in func_name:
        return None
    recv_type, method = func_name.split('.', 1)
    # Build a regex that matches `func (h *RecvType) Method(...) {`.
    # RecvType may be a value or pointer receiver.
    pat = re.compile(
        r'\bfunc\s*\(\s*\w+\s+\*?'
        + re.escape(recv_type)
        + r'\s*\)\s+'
        + re.escape(method)
        + r'\s*\([^)]*\)\s*\{'
    )
    m = pat.search(content)
    if not m:
        return None
    brace_idx = content.find('{', m.start())
    if brace_idx == -1:
        return None
    body, _ = find_matching_brace(mask_go_source(content), brace_idx, '{', '}')
    if body is None:
        return None
    # Re-slice from the raw source so string contents are preserved.
    return content[brace_idx + 1: brace_idx + 1 + len(body)]




# ---------------------------------------------------------------------------
# Go struct parser
# ---------------------------------------------------------------------------

# `type Name struct {` — open brace at end of line. Name may be exported
# (uppercase initial) or unexported (lowercase initial) — both can be
# used as response shapes since JSON serialisation doesn't care about
# Go's export visibility.
RE_STRUCT_OPEN = re.compile(
    r'\btype\s+(?P<name>[A-Za-z]\w*)\s+struct\s*\{'
)

# A field declaration inside a struct body. Field name is capitalised
# identifier; type is everything up to the backtick (or end of line if
# no tag); the JSON tag (if present) is captured.
RE_STRUCT_FIELD = re.compile(
    r'^\s*(?P<name>[A-Z]\w*)\s+(?P<type>[^\s`].*?)'
    r'(?:\s+`(?P<tag>[^`]*)`)?\s*$'
)

# JSON tag inside a struct tag string.
RE_JSON_TAG = re.compile(r'json:"(?P<val>[^"]*)"')

RE_PACKAGE = re.compile(r'^\s*package\s+(\w+)', re.MULTILINE)


def parse_go_structs(content: str, file: str, package: str,
                     raw_content: Optional[str] = None) -> List[GoStruct]:
    """Parse every ``type X struct { ... }`` declaration in ``content``.

    ``content`` should be the masked source (for safe brace matching).
    ``raw_content`` is the original source — when provided, the struct
    body is re-sliced from the raw source so JSON tags are preserved.
    Offsets are identical because masking preserves length.
    """
    if raw_content is None:
        raw_content = content
    out: List[GoStruct] = []
    for m in RE_STRUCT_OPEN.finditer(content):
        name = m.group('name')
        line = line_of(content, m.start())
        brace_idx = content.find('{', m.start())
        if brace_idx == -1:
            continue
        body, _ = find_matching_brace(content, brace_idx, '{', '}')
        if body is None:
            continue
        # Re-slice the body from the raw source so JSON tags survive.
        raw_body = raw_content[brace_idx + 1: brace_idx + 1 + len(body)]
        fields = _parse_struct_fields(raw_body)
        out.append(GoStruct(
            name=name, file=file, line=line,
            package=package, fields=fields,
        ))
    return out


def _parse_struct_fields(body: str) -> List[GoField]:
    """Parse the body of a struct (text between the braces)."""
    fields: List[GoField] = []
    # We split on newlines but a field declaration may span multiple
    # lines if the type contains a newline (rare for our codebase).
    # Simple heuristic: process line by line, but if a line doesn't
    # have a backtick AND the next line starts with whitespace + backtick,
    # join them.
    lines = body.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        # Join continuation lines: if this line has a field name + type
        # but no backtick, look ahead for the tag.
        while i + 1 < len(lines) and '`' not in line and line.strip() and \
                not _is_field_start(lines[i + 1]):
            # Heuristic: continuation lines are usually indented more
            # than the field name line and contain the tag.
            line = line.rstrip() + ' ' + lines[i + 1].strip()
            i += 1
            if '`' in line:
                break
        f = _parse_struct_field_line(line)
        if f:
            fields.append(f)
        i += 1
    return fields


def _is_field_start(line: str) -> bool:
    """True if ``line`` looks like the start of a new struct field."""
    s = line.strip()
    if not s:
        return False
    # Field names are capitalised identifiers.
    return bool(re.match(r'^[A-Z]\w*\s+', s))


def _parse_struct_field_line(line: str) -> Optional[GoField]:
    s = line.strip()
    if not s or s.startswith('//'):
        return None
    # Inline-embedded struct: `models.EventDefinition `json:",inline"``
    # or `EventDefinition `json:",inline"``. The embedded struct's
    # fields are serialized as if they were declared on the outer
    # struct (Go's standard JSON marshalling behaviour for embedded
    # structs without an explicit json tag — and the explicit
    # `,inline` form is a project convention that signals the same
    # intent).
    inline_m = re.match(
        r'^(?P<type>(?:[a-z]\w*\.)?[A-Z]\w*)\s+`(?P<tag>[^`]*)`\s*$',
        s,
    )
    if inline_m:
        tag_str = inline_m.group('tag')
        jm = RE_JSON_TAG.search(tag_str)
        if jm and (jm.group('val') == ',inline' or
                   jm.group('val').startswith(',inline')):
            return GoField(
                name=inline_m.group('type'),
                json_name='',     # inline — no wire name of its own
                go_type=inline_m.group('type'),
                is_inline_embed=True,
            )
    # Embedded field (just a type name, no field name, no tag) — Go's
    # default JSON marshalling flattens these, but we conservatively
    # skip them since they may be interface embeddings or non-data
    # behaviour mixins. Tagged inline-embedded fields above ARE
    # flattened.
    if '`' not in s and re.match(r'^[A-Z]\w*\.?[A-Z]\w*$', s):
        return None
    # Comment-only or brace-only line.
    if s in {'{', '}', '};'}:
        return None
    m = RE_STRUCT_FIELD.match(s)
    if not m:
        # Fall back to a more permissive split: name + type + tag.
        # This catches unusual types like `map[string]EntitlementValue`.
        parts = s.split('`', 1)
        if len(parts) != 2:
            return None
        head, tag = parts
        head = head.strip()
        bits = head.split(None, 1)
        if len(bits) != 2:
            return None
        name, go_type = bits
        tag_str = tag.strip()
    else:
        name = m.group('name')
        go_type = m.group('type').strip()
        tag_str = m.group('tag') or ''
    if not name or not go_type:
        return None
    json_name = name  # default to Go field name
    is_omitempty = False
    is_skipped = False
    jm = RE_JSON_TAG.search(tag_str)
    if jm:
        val = jm.group('val')
        if val == '-':
            is_skipped = True
            json_name = ''
        else:
            # Handle "name,omitempty" and "name"
            bits = val.split(',', 1)
            json_name = bits[0]
            if len(bits) > 1 and 'omitempty' in bits[1]:
                is_omitempty = True
    is_optional = is_omitempty or go_type.startswith('*')
    return GoField(
        name=name, json_name=json_name, go_type=go_type,
        is_omitempty=is_omitempty, is_skipped=is_skipped,
        is_optional=is_optional,
    )


# ---------------------------------------------------------------------------
# Go handler / response parser
# ---------------------------------------------------------------------------

# `func (h *XHandler) Method(w http.ResponseWriter, r *http.Request) {`
# Also matches `func (h XHandler) Method(...)` (value receiver) and
# unexported handler types like `func (h *bootstrapHandler) Status(...)`.
RE_HANDLER_FUNC = re.compile(
    r'\bfunc\s*\(\s*(?P<recv>\w+)\s+\*?(?P<recvtype>[A-Z]\w*)\s*\)\s+'
    r'(?P<method>[A-Z]\w*)\s*\(\s*w\s+http\.ResponseWriter,\s*r\s+\*?http\.Request\s*\)\s*\{'
)

# A `respondWithJSON(w, http.StatusXxx, <payload>)` call. The payload
# begins after the second comma.
RE_RESPOND_WITH_JSON = re.compile(
    r'\brespondWithJSON\s*\(\s*w\s*,\s*http\.Status\w+\s*,'
)

# A `json.NewEncoder(w).Encode(<payload>)` call.
RE_JSON_ENCODER = re.compile(
    r'\bjson\.NewEncoder\s*\(\s*w\s*\)\.Encode\s*\('
)

# A struct-literal payload: `Name{` or `pkg.Name{` or `&Name{` (Name may
# be exported or unexported). Captures the struct name without the
# package prefix.
RE_STRUCT_LITERAL = re.compile(
    r'^\s*&?\s*(?:(?P<pkg>[a-z]\w*)\.)?(?P<name>[A-Za-z]\w*)\s*\{'
)

# A map literal payload: `map[keyType]valueType{`.
RE_MAP_LITERAL = re.compile(r'^\s*map\s*\[')

# Variable declaration: `var name Type` (single var).
RE_VAR_DECL = re.compile(
    r'\bvar\s+(?P<name>\w+)\s+(?P<type>[^\s=;]+(?:\.[A-Z]\w*)?(?:\[\w*\])?)'
)

# Short declaration: `name := value` — we only care when value is a
# composite literal `Type{...}` or a slice literal `[]Type{...}`.
# Allows an optional lowercase package prefix (e.g. `models.Announcement`).
RE_SHORT_DECL_LITERAL = re.compile(
    r'\b(?P<name>\w+)\s*:?=\s*(?:'
    r'make\(\[\]?(?P<maketype>(?:[a-z]\w*\.)?[A-Z]\w*)'
    r'|\[\]?(?P<type>(?:[a-z]\w*\.)?[A-Z]\w*)\s*\{'
    r'|(?P<vtype>(?:[a-z]\w*\.)?[A-Z]\w*)\s*\{'
    r')'
)

# Slice variable: `var x []Type` or `var x = []Type{...}`.
RE_VAR_SLICE = re.compile(
    r'\bvar\s+(?P<name>\w+)\s+\[\]?(?P<type>(?:[a-z]\w*\.)?[A-Z]\w*)'
)

# Make for a slice: `x := make([]Type, ...)`.
RE_MAKE_SLICE = re.compile(
    r'\b(?P<name>\w+)\s*:?=\s*make\(\s*\[\]?\s*(?P<type>(?:[a-z]\w*\.)?[A-Z]\w*)'
)

# A `var name Type` declaration (single var, no initializer). Captures
# the variable name and its type. Allows optional package prefix.
RE_VAR_DECL_NAMED = re.compile(
    r'\bvar\s+(?P<name>\w+)\s+(?P<type>(?:[a-z]\w*\.)?[A-Z]\w*(?:\[\])?)'
)


def parse_go_handlers(content: str, file: str,
                      raw_content: Optional[str] = None) -> List[GoHandler]:
    """Parse every HTTP handler function in ``content`` and extract its
    response shape(s).

    ``content`` should be the masked source (comments and string
    contents blanked out) so brace matching is robust. ``raw_content``
    is the original source — when provided, the response *payload* is
    extracted from the raw source so string keys inside
    ``map[string]interface{}{...}`` literals are preserved. Offsets in
    the masked and raw sources are identical because masking preserves
    length and newlines.
    """
    out: List[GoHandler] = []
    if raw_content is None:
        raw_content = content
    for m in RE_HANDLER_FUNC.finditer(content):
        recvtype = m.group('recvtype')
        method = m.group('method')
        brace_idx = content.find('{', m.start())
        if brace_idx == -1:
            continue
        body, _ = find_matching_brace(content, brace_idx, '{', '}')
        if body is None:
            continue
        # Extract the corresponding raw body (same offsets).
        raw_body = raw_content[brace_idx + 1: brace_idx + 1 + len(body)]
        h = GoHandler(
            name=f'{recvtype}.{method}',
            file=file,
            line=line_of(content, m.start()),
            body=body,
        )
        h.responses = _parse_handler_responses(body, raw_body)
        out.append(h)
    return out


def _parse_handler_responses(body: str,
                             raw_body: Optional[str] = None) -> List[GoResponseShape]:
    """Find every response-write call in the handler body and parse
    its payload.

    ``body`` is the masked body (used to locate response calls safely).
    ``raw_body`` is the original body text — when provided, payloads
    are extracted from it so string keys are preserved.
    """
    if raw_body is None:
        raw_body = body
    shapes: List[GoResponseShape] = []
    # Build a variable -> type map by scanning the body for declarations.
    var_types = _collect_var_types(body)

    # Find every respondWithJSON call.
    for m in RE_RESPOND_WITH_JSON.finditer(body):
        # The payload starts after the second comma. Find the matching
        # close paren of the outer respondWithJSON call.
        open_paren_idx = body.find('(', m.start())
        if open_paren_idx == -1:
            continue
        args, _ = find_matching_paren(body, open_paren_idx)
        if args is None:
            continue
        # The payload is everything after the second comma.
        payload = _extract_third_arg(args)
        if payload is None:
            continue
        # Re-extract the payload from the raw body so string keys
        # are preserved. The offsets in `body` and `raw_body` are
        # identical because masking preserves length.
        raw_payload = _extract_payload_from_raw(raw_body, open_paren_idx)
        if raw_payload is not None:
            payload = raw_payload
        shape = _classify_payload(payload, var_types)
        shapes.append(shape)

    # Find every json.NewEncoder(w).Encode call.
    for m in RE_JSON_ENCODER.finditer(body):
        open_paren_idx = body.find('(', m.end() - 1)
        if open_paren_idx == -1:
            continue
        args, _ = find_matching_paren(body, open_paren_idx)
        if args is None:
            continue
        # Re-extract from raw.
        raw_payload = _extract_encode_payload_from_raw(raw_body, m.start())
        payload = raw_payload if raw_payload is not None else args.strip()
        shape = _classify_payload(payload, var_types)
        shapes.append(shape)

    return shapes


def _extract_payload_from_raw(raw_body: str,
                              masked_open_paren_idx: int) -> Optional[str]:
    """Given the open-paren index of a ``respondWithJSON(...)`` call
    in the masked body, extract the third argument (the payload) from
    the raw body using the same offset.
    """
    # Find the matching close paren in the raw body (string-aware).
    raw_args, _ = _find_matching_paren_raw(raw_body, masked_open_paren_idx)
    if raw_args is None:
        return None
    return _extract_third_arg(raw_args)


def _extract_encode_payload_from_raw(raw_body: str,
                                     masked_call_start: int) -> Optional[str]:
    """Given the start index of a ``json.NewEncoder(w).Encode(...)`` call
    in the masked body, extract the payload from the raw body.
    """
    # Find the open paren of the Encode call. In the raw body the call
    # text is `json.NewEncoder(w).Encode(` — find the open paren after
    # `Encode`.
    encode_idx = raw_body.find('Encode(', masked_call_start)
    if encode_idx == -1:
        return None
    open_paren_idx = raw_body.find('(', encode_idx)
    if open_paren_idx == -1:
        return None
    raw_args, _ = _find_matching_paren_raw(raw_body, open_paren_idx)
    if raw_args is None:
        return None
    return raw_args.strip()


def _find_matching_paren_raw(text: str, open_idx: int) -> Tuple[Optional[str], int]:
    """Like ``find_matching_paren`` but skips over string literals so
    parens inside strings don't confuse the matcher.
    """
    if open_idx < 0 or open_idx >= len(text) or text[open_idx] != '(':
        return None, -1
    depth = 0
    i = open_idx
    n = len(text)
    in_str = False
    in_rune = False
    in_line_comment = False
    in_block_comment = False
    while i < n:
        c = text[i]
        nxt = text[i + 1] if i + 1 < n else ''
        if in_line_comment:
            if c == '\n':
                in_line_comment = False
            i += 1
            continue
        if in_block_comment:
            if c == '*' and nxt == '/':
                in_block_comment = False
                i += 2
                continue
            i += 1
            continue
        if in_str:
            if c == '\\' and nxt:
                i += 2
                continue
            if c == '"':
                in_str = False
            i += 1
            continue
        if in_rune:
            if c == '\\' and nxt:
                i += 2
                continue
            if c == "'":
                in_rune = False
            i += 1
            continue
        if c == '/' and nxt == '/':
            in_line_comment = True
            i += 2
            continue
        if c == '/' and nxt == '*':
            in_block_comment = True
            i += 2
            continue
        if c == '"':
            in_str = True
            i += 1
            continue
        if c == "'":
            in_rune = True
            i += 1
            continue
        if c == '(':
            depth += 1
        elif c == ')':
            depth -= 1
            if depth == 0:
                return text[open_idx + 1:i], i + 1
        i += 1
    return None, -1


def _collect_var_types(body: str) -> Dict[str, str]:
    """Build a ``{var_name: type_str}`` map by scanning the handler
    body for variable declarations. Best-effort — used to resolve the
    types of bare identifiers in map literals.
    """
    out: Dict[str, str] = {}
    # `var name Type` declarations (most reliable — captures the type
    # explicitly). Try the named-variant regex first since it handles
    # package-qualified types like `models.ConfigVar`.
    for m in RE_VAR_DECL_NAMED.finditer(body):
        t = m.group('type')
        if t.endswith('[]'):
            out[m.group('name')] = t
        else:
            out[m.group('name')] = t
    # Fallback: the looser `var name X` regex catches things the named
    # variant misses (e.g. `var name map[string]X`).
    for m in RE_VAR_DECL.finditer(body):
        out.setdefault(m.group('name'), m.group('type'))
    for m in RE_VAR_SLICE.finditer(body):
        out[m.group('name')] = f'[]{m.group("type")}'
    for m in RE_MAKE_SLICE.finditer(body):
        out[m.group('name')] = f'[]{m.group("type")}'
    for m in RE_SHORT_DECL_LITERAL.finditer(body):
        name = m.group('name')
        maketype = m.group('maketype')
        slice_type = m.group('type')
        vtype = m.group('vtype')
        if maketype:
            out[name] = f'[]{maketype}'
        elif slice_type:
            out[name] = f'[]{slice_type}'
        elif vtype:
            out[name] = vtype
    return out


def _extract_third_arg(args: str) -> Optional[str]:
    """Given the comma-separated argument list of a
    ``respondWithJSON(w, status, payload)`` call, return the payload
    (third argument) as a string.
    """
    depth = 0
    comma_positions: List[int] = []
    for i, c in enumerate(args):
        if c in '([{':
            depth += 1
        elif c in ')]}':
            depth -= 1
        elif c == ',' and depth == 0:
            comma_positions.append(i)
    if len(comma_positions) < 2:
        return None
    payload = args[comma_positions[1] + 1:].strip()
    return payload


def _classify_payload(payload: str,
                      var_types: Dict[str, str]) -> GoResponseShape:
    """Classify a response payload expression into a GoResponseShape."""
    payload = payload.strip()
    raw = payload[:200]
    if not payload:
        return GoResponseShape(kind='unknown', raw=raw)

    # Strip a trailing cast like `.(someType)` or method chain — keep
    # only the outermost expression.

    # Case 1: struct literal `Name{...}`.
    m = RE_STRUCT_LITERAL.match(payload)
    if m:
        return GoResponseShape(
            kind='struct_literal',
            struct_name=m.group('name'),
            raw=raw,
        )

    # Case 2: map literal `map[...]...{...}`.
    if RE_MAP_LITERAL.match(payload):
        return _parse_map_literal(payload, var_types, raw)

    # Case 3: slice of structs `[]Name{...}`.
    if payload.startswith('[]'):
        # e.g. `[]MemberResponse{...}` — rare for top-level responses.
        inner = payload[2:].strip()
        m2 = RE_STRUCT_LITERAL.match(inner)
        if m2:
            return GoResponseShape(
                kind='struct_literal',
                struct_name=m2.group('name'),
                raw=raw,
            )
        return GoResponseShape(kind='unknown', raw=raw)

    # Case 4: bare identifier (a variable holding a struct).
    if re.match(r'^[a-zA-Z_]\w*$', payload):
        t = var_types.get(payload)
        if t:
            return _make_shape_from_type(t, raw)
        return GoResponseShape(kind='bare_identifier', raw=raw)

    # Case 5: address-of struct `&Name{...}`.
    if payload.startswith('&'):
        inner = payload[1:].strip()
        m3 = RE_STRUCT_LITERAL.match(inner)
        if m3:
            return GoResponseShape(
                kind='struct_literal',
                struct_name=m3.group('name'),
                raw=raw,
            )

    return GoResponseShape(kind='unknown', raw=raw)


def _make_shape_from_type(type_str: str, raw: str) -> GoResponseShape:
    """Build a GoResponseShape from a resolved variable type string.
    Used when a payload is a bare identifier whose type we know.
    """
    is_array = type_str.startswith('[]')
    if is_array:
        type_str = type_str[2:]
    struct_ref = _strip_package(type_str)
    return GoResponseShape(
        kind='struct_literal' if struct_ref else 'unknown',
        struct_name=struct_ref or None,
        fields=[],
        raw=raw,
    )


def _parse_map_literal(payload: str,
                       var_types: Dict[str, str],
                       raw: str) -> GoResponseShape:
    """Parse a ``map[string]interface{}{...}`` literal into a list of
    GoResponseField entries (one per top-level key).
    """
    # Find the opening brace of the literal body. This is tricky because
    # `map[string]interface{}{...}` contains `interface{}` which has its
    # own `{}` pair. We scan from the start, tracking depth, and find
    # the first `{` at depth 0 (after the `map[...]` and value-type
    # declarations).
    brace_idx = _find_map_body_brace(payload)
    if brace_idx == -1:
        # Fall back to the simple find — may pick the wrong brace but
        # at least we won't crash.
        brace_idx = payload.find('{')
    if brace_idx == -1:
        return GoResponseShape(kind='unknown', raw=raw)
    body, _ = find_matching_brace(payload, brace_idx, '{', '}')
    if body is None:
        return GoResponseShape(kind='unknown', raw=raw)
    fields: List[GoResponseField] = []
    # Walk the body, splitting on top-level commas.
    entries = _split_top_level_commas(body)
    for entry in entries:
        entry = entry.strip()
        if not entry:
            continue
        # Each entry is `"key": value`.
        cm = re.match(r'^"(?P<key>[^"]*)"\s*:\s*(?P<val>.*)$', entry, re.DOTALL)
        if not cm:
            # Single-string map (e.g. `map[string]string{"message": "..."}`)
            # is already in the same shape — the regex above handles it.
            continue
        key = cm.group('key')
        val = cm.group('val').strip()
        f = _classify_map_value(val, var_types)
        f.name = key
        fields.append(f)
    return GoResponseShape(
        kind='map_literal',
        fields=fields,
        raw=raw,
    )


def _find_map_body_brace(payload: str) -> int:
    """Find the index of the opening brace of a ``map[...]...{...}``
    literal's body. Skips past the ``map[...]`` type declaration and
    any nested ``interface{}`` / ``struct{}`` in the value type.

    The body brace is the ``{`` that comes AFTER the full type
    declaration. For ``map[string]interface{}{...}`` the type is
    ``interface{}`` (which has its own ``{}`` pair we must skip);
    for ``map[string]string{...}`` the type is just ``string``.
    """
    s = payload.lstrip()
    offset = len(payload) - len(s)
    if not s.startswith('map['):
        return payload.find('{')
    # Walk past the `map[...]` part, tracking bracket depth.
    i = payload.find('[')
    if i == -1:
        return payload.find('{')
    depth = 1
    i += 1
    n = len(payload)
    while i < n and depth > 0:
        c = payload[i]
        if c == '[':
            depth += 1
        elif c == ']':
            depth -= 1
        i += 1
    # `i` is now just past the closing `]` of `map[...]`.
    # Skip whitespace.
    while i < n and payload[i] in ' \t\n\r':
        i += 1
    # Skip the value type. It may be:
    #   - `interface{}` or `struct{}` (with their own `{}`)
    #   - `*Type` (pointer)
    #   - `[]Type` (slice)
    #   - `map[...]Type` (recursive — track depth)
    #   - `pkg.Type` or `Type` (named type)
    # We loop until we find the body's `{`.
    while i < n:
        c = payload[i]
        if c == '{':
            return i
        if c == '*':
            i += 1
            continue
        if c == '[':
            # Skip `[]` or `[N]`.
            depth = 1
            i += 1
            while i < n and depth > 0:
                if payload[i] == '[':
                    depth += 1
                elif payload[i] == ']':
                    depth -= 1
                i += 1
            continue
        if c.isalpha() or c == '_':
            # Skip an identifier (possibly with `.` and `[]` suffixes).
            while i < n and (payload[i].isalnum() or payload[i] in '._'):
                i += 1
            # After the identifier, check for `interface{}` / `struct{}`
            # — actually those are keywords, not identifiers, so they're
            # already skipped by the identifier loop above. Now check
            # for a following `{}` (e.g. `interface{}`).
            if i < n and payload[i] == '{':
                # Skip the `{}` pair.
                depth = 1
                i += 1
                while i < n and depth > 0:
                    if payload[i] == '{':
                        depth += 1
                    elif payload[i] == '}':
                        depth -= 1
                    i += 1
            continue
        # Skip whitespace and other separators.
        i += 1
    return -1


def _split_top_level_commas(text: str) -> List[str]:
    """Split ``text`` on top-level commas (ignoring those inside
    brackets, braces, or parens).
    """
    out: List[str] = []
    depth = 0
    start = 0
    for i, c in enumerate(text):
        if c in '([{':
            depth += 1
        elif c in ')]}':
            depth -= 1
        elif c == ',' and depth == 0:
            out.append(text[start:i])
            start = i + 1
    if start < len(text):
        out.append(text[start:])
    return out


def _classify_map_value(val: str,
                        var_types: Dict[str, str]) -> GoResponseField:
    """Given a value expression from a map literal, determine its type."""
    val = val.strip()
    # Strip trailing commas.
    while val.endswith(','):
        val = val[:-1].strip()
    # Struct literal: `Name{...}`.
    m = RE_STRUCT_LITERAL.match(val)
    if m:
        name = m.group('name')
        return GoResponseField(
            name='', go_type=name, struct_ref=name,
        )
    # Slice of struct literals: `[]Name{...}`.
    if val.startswith('[]'):
        inner = val[2:].strip()
        m2 = RE_STRUCT_LITERAL.match(inner)
        if m2:
            name = m2.group('name')
            return GoResponseField(
                name='', go_type=f'[]{name}', struct_ref=name,
                is_array=True,
            )
        # `[]pkg.Name{...}` — also a slice (fallback regex).
        m3 = re.match(r'^(?:(?P<pkg>[a-z]\w*)\.)?(?P<name>[A-Za-z]\w*)\s*\{',
                      inner)
        if m3:
            name = m3.group('name')
            return GoResponseField(
                name='', go_type=f'[]{name}', struct_ref=name,
                is_array=True,
            )
    # Bare identifier (variable reference).
    if re.match(r'^[a-zA-Z_]\w*$', val):
        t = var_types.get(val)
        if t:
            is_array = t.startswith('[]')
            base = t[2:] if is_array else t
            return GoResponseField(
                name='', go_type=t,
                struct_ref=_strip_package(base) or None,
                is_array=is_array,
            )
        return GoResponseField(name='', go_type='unknown')
    # Primitive literals.
    if val.startswith('"'):
        return GoResponseField(name='', go_type='string')
    if val in {'true', 'false'}:
        return GoResponseField(name='', go_type='bool')
    if re.match(r'^-?\d+(\.\d+)?$', val):
        return GoResponseField(name='', go_type='number')
    # Function call or complex expression — unknown.
    return GoResponseField(name='', go_type='unknown')


def _strip_package(type_str: str) -> str:
    """``models.User`` -> ``User``; ``User`` -> ``User``."""
    if '.' in type_str:
        return type_str.rsplit('.', 1)[-1]
    return type_str


# ---------------------------------------------------------------------------
# Go routes parser
# ---------------------------------------------------------------------------

# `<var> := <parent>.PathPrefix("<prefix>").Subrouter()` — captures
# the new var, the parent var, and the prefix.
RE_SUBROUTER = re.compile(
    r'(\w+)\s*:?=\s*(\w+)\.PathPrefix\(\s*"([^"]*)"\s*\)\.Subrouter\(\)'
)

# `<router>.HandleFunc("<path>", <handler>)` — captures router, path.
RE_ROUTER_CALL = re.compile(
    r'(\w+)\.(HandleFunc|Handle)\(\s*"([^"]*)"\s*,'
)

# `.Methods("GET")` after a HandleFunc call.
RE_METHODS = re.compile(r'\.Methods\(\s*"([A-Z]+)"\s*\)')

# `<var> := <pkg>.NewXHandler(...)` — captures the var and the
# constructor name (we strip the leading `New` to get the struct name).
# Matches both `handlers.NewAuthHandler(...)` and `billing.NewFooHandler(...)`.
RE_HANDLER_VAR = re.compile(
    r'(\w+)\s*:?=\s*\w+\.New(\w+Handler)\s*\('
)

# Wrapper functions to peel off when extracting the handler reference.
WRAPPER_FUNCS = {
    'RateLimitHandler', 'RequireAuth', 'RequireRole', 'RequireTenant',
    'RequireRootTenant', 'RequireActiveBilling', 'HandlerFunc',
}

# Packages that appear in `pkg.Func` form inside handler expressions
# but are NOT handlers themselves.
NON_HANDLER_PKGS = {
    'http', 'middleware', 'rateLimiter', 'models', 'mux', 'r', 'fmt',
    'strings', 'context', 'time', 'os', 'syscall', 'signal', 'path',
    'filepath', 'bson', 'options', 'primitive', 'slog', 'json',
    'mux', 'cors', 'email', 'auth', 'events', 'syslog', 'stripe',
    'configstore', 'config', 'health', 'telemetry', 'testutil',
    'validation', 'version',
}


def parse_go_routes(content: str, file: str,
                    handler_vars: Optional[Dict[str, str]] = None
                    ) -> List[GoRoute]:
    """Parse a Go file's router setup and return a list of GoRoute.

    ``content`` should be the RAW (unmasked) source so path strings
    are preserved. The patterns we match (``HandleFunc``, ``PathPrefix``,
    ``Subrouter``, ``Methods``) don't appear inside Go string literals
    in this codebase, so masking isn't needed for route parsing.
    """
    routes: List[GoRoute] = []
    # 1. Collect handler var -> struct name mappings from constructor
    #    calls (e.g. `authHandler := handlers.NewAuthHandler(...)`).
    if handler_vars is None:
        handler_vars = {}
    for m in RE_HANDLER_VAR.finditer(content):
        var = m.group(1)
        ctor = m.group(2)
        # `NewAuthHandler` -> `AuthHandler` is already correct since
        # the regex captures `(\w+Handler)` after `New`. But the
        # constructor name might be `NewX` without the `Handler`
        # suffix — in that case we just use the captured name as-is.
        struct = ctor if ctor.endswith('Handler') else ctor
        handler_vars.setdefault(var, struct)

    # 2. Collect subrouter var -> (parent_var, prefix).
    raw_subrouters: List[Tuple[str, str, str, int]] = []
    for m in RE_SUBROUTER.finditer(content):
        var = m.group(1)
        parent = m.group(2)
        prefix = m.group(3)
        raw_subrouters.append((var, parent, prefix, m.start()))

    # Resolve to absolute prefixes (parent's prefix + this prefix)
    # via fixpoint iteration — subrouters may reference other subrouters.
    resolved: Dict[str, Tuple[str, str]] = {}  # var -> (root, full_prefix)
    known_routers = {'router', 'mux', 'r', 'mainRouter', 'http'}
    for v in known_routers:
        resolved[v] = (v, '')
    # The top-level `api` subrouter is mounted at /api — seed it too.
    # (We'll let the iteration pick it up via the PathPrefix chain.)

    changed = True
    iterations = 0
    while changed and iterations < 10:
        changed = False
        iterations += 1
        for var, parent, prefix, _ in raw_subrouters:
            if parent in resolved:
                parent_root, parent_prefix = resolved[parent]
                full = parent_prefix + prefix
                if var not in resolved or resolved[var][1] != full:
                    resolved[var] = (parent_root, full)
                    changed = True
    subrouters = {v: p for v, p in resolved.items() if v not in known_routers}

    # 3. Scan for HandleFunc / Handle calls.
    for m in RE_ROUTER_CALL.finditer(content):
        router_var = m.group(1)
        path_str = m.group(3)
        # Find the open paren of the args list (between the call kind
        # and the path string).
        open_paren_idx = content.find('(', m.start(2))
        if open_paren_idx == -1 or open_paren_idx > m.end():
            continue
        args, close_idx = find_matching_paren(content, open_paren_idx)
        if args is None:
            continue
        # The args look like: `"/path", <handler_expr>` — extract the
        # handler expr by stripping the leading path string.
        am = re.match(r'\s*"' + re.escape(path_str) + r'"\s*,\s*(.*)',
                      args, re.DOTALL)
        if not am:
            am = re.match(r'\s*"[^"]*"\s*,\s*(.*)', args, re.DOTALL)
            if not am:
                continue
        handler_expr = am.group(1).strip()

        # Look for `.Methods("X")` after the closing paren.
        method = 'GET'  # default
        tail = content[close_idx:close_idx + 200]
        mm = RE_METHODS.search(tail)
        if mm and mm.start() < 60:
            method = mm.group(1)

        # Resolve the handler reference.
        handler_func = _extract_handler_name(handler_expr, handler_vars)
        if not handler_func:
            # Fall back to the raw expr so the route isn't lost.
            handler_func = handler_expr[:60] or '(unknown)'

        # Build the full path.
        prefix_info = subrouters.get(router_var)
        full_prefix = prefix_info[1] if prefix_info else ''
        full_path = full_prefix + path_str
        full_path = re.sub(r'/+', '/', full_path)
        if not full_path.startswith('/'):
            full_path = '/' + full_path

        routes.append(GoRoute(
            method=method,
            path=full_path,
            handler_func=handler_func,
            file=file,
            line=line_of(content, m.start()),
        ))
    return routes


def _extract_handler_name(expr: str,
                          handler_vars: Dict[str, str]) -> Optional[str]:
    """Extract a ``StructType.Method`` label from a handler expression.

    Handles:
      * ``authHandler.Register`` -> ``AuthHandler.Register`` (when
        ``handler_vars`` maps ``authHandler`` -> ``AuthHandler``)
      * ``handlers.DocsHTML`` -> ``handlers.DocsHTML`` (package-level
        function reference)
      * ``rateLimiter.RateLimitHandler(cfg, fn, authHandler.Login)`` ->
        ``AuthHandler.Login`` (peels wrappers, prefers known handler
        vars)
      * ``authMiddleware.RequireAuth(http.HandlerFunc(
        plansHandler.ListPlansPublic))`` -> ``PlansHandler.ListPlansPublic``
    """
    expr = expr.strip()
    # Find all `var.Method` references in order of appearance.
    refs = list(re.finditer(r'\b([a-zA-Z_]\w*)\.([A-Z]\w*)\b', expr))
    if not refs:
        # Maybe a bare function name: `MyHandler` passed as a value.
        bare = re.match(r'^\s*([A-Z]\w*)\s*[\),]', expr)
        if bare:
            return bare.group(1)
        return None
    # Filter out non-handler package refs and known wrappers.
    candidates: List[Tuple[str, str]] = []
    for rm in refs:
        var = rm.group(1)
        method = rm.group(2)
        if method in WRAPPER_FUNCS:
            continue
        if var in NON_HANDLER_PKGS:
            continue
        candidates.append((var, method))
    if not candidates:
        # Fall back to all refs.
        candidates = [(rm.group(1), rm.group(2)) for rm in refs]
    # Prefer the first candidate whose var is a known handler var.
    for var, method in candidates:
        if var in handler_vars:
            return f'{handler_vars[var]}.{method}'
    # Fall back to the LAST candidate (rate-limited routes pass the
    # real handler as the final positional arg).
    var, method = candidates[-1]
    if var in handler_vars:
        return f'{handler_vars[var]}.{method}'
    # Heuristic: title-case the first letter of the var.
    struct = var[0].upper() + var[1:] if var else var
    return f'{struct}.{method}'


# ---------------------------------------------------------------------------
# TS type parser
# ---------------------------------------------------------------------------

# `interface Name {` or `interface Name extends X, Y {`
RE_INTERFACE_OPEN = re.compile(
    r'\binterface\s+(?P<name>[A-Z]\w*)\s*(?:extends\s+[^{]+)?\{'
)

# `type Name = ...` — captures name. The body may be an object literal,
# a union, or a primitive. We only care about object literals here.
RE_TYPE_ALIAS = re.compile(
    r'\btype\s+(?P<name>[A-Z]\w*)\s*=\s*'
)

# A field inside an interface body: `name: type;` or `name?: type;`.
# Type may be a union, an array, a generic, or a nested object.
RE_TS_FIELD = re.compile(
    r'^\s*(?P<name>[A-Za-z_]\w*)\s*(?P<opt>\?)?\s*:\s*(?P<type>[^;]+?)\s*;?\s*$'
)


def parse_ts_types(content: str, file: str) -> List[TSType]:
    """Parse every interface and object-literal type alias in a .ts file."""
    out: List[TSType] = []
    for m in RE_INTERFACE_OPEN.finditer(content):
        name = m.group('name')
        line = line_of(content, m.start())
        brace_idx = content.find('{', m.start())
        if brace_idx == -1:
            continue
        body, _ = find_matching_brace(content, brace_idx, '{', '}')
        if body is None:
            continue
        fields = _parse_ts_fields(body)
        out.append(TSType(
            name=name, file=file, line=line, kind='interface',
            fields=fields, raw=body,
        ))
    for m in RE_TYPE_ALIAS.finditer(content):
        name = m.group('name')
        line = line_of(content, m.start())
        # Look at what follows the `=`. If it starts with `{`, it's an
        # object literal type. If it's a string/union literal, capture
        # the raw type text. Otherwise skip.
        rest = content[m.end():]
        stripped = rest.lstrip()
        if stripped.startswith('{'):
            # Find the matching closing brace.
            brace_idx = m.end() + (len(rest) - len(stripped))
            body, _ = find_matching_brace(content, brace_idx, '{', '}')
            if body is None:
                continue
            fields = _parse_ts_fields(body)
            out.append(TSType(
                name=name, file=file, line=line, kind='type_alias',
                fields=fields, raw=body,
            ))
        else:
            # String/union alias like `type LogSeverity = 'a' | 'b'`.
            # Capture the raw value up to the next newline or `;`.
            end = re.search(r'[;\n]', rest)
            raw = rest[:end.start()] if end else rest
            out.append(TSType(
                name=name, file=file, line=line, kind='type_alias',
                fields=[], raw=raw.strip(),
            ))
    return out


def _parse_ts_fields(body: str) -> List[TSField]:
    """Parse the body of an interface or object-literal type alias.

    Handles both newline-separated fields (the common case in
    ``interface X { ... }``) and semicolon-separated fields on a single
    line (the common case in inline object types like
    ``{ user: User; memberships: MembershipInfo[] }``).
    """
    fields: List[TSField] = []
    # Split the body into individual field declarations. We split on
    # top-level semicolons AND newlines (a field may be followed by
    # either). Brackets `{}<>` are tracked so semicolons inside nested
    # types or generics don't split.
    declarations = _split_ts_declarations(body)
    for decl in declarations:
        s = decl.strip()
        if not s or s.startswith('//') or s.startswith('/*'):
            continue
        # Skip closing braces of nested objects.
        if s in {'}', '};', '}),', '},', '{'}:
            continue
        m = RE_TS_FIELD.match(s)
        if not m:
            continue
        name = m.group('name')
        is_optional = bool(m.group('opt'))
        type_str = m.group('type').strip()
        # If the type is an inline object that spans multiple lines
        # (starts with `{` but doesn't end with `}`), the split logic
        # above already kept the full object — rejoin if needed.
        # Actually `_split_ts_declarations` keeps braces balanced, so
        # `type_str` should already be complete.
        struct_ref, is_array = _classify_ts_type(type_str)
        fields.append(TSField(
            name=name, ts_type=type_str, is_optional=is_optional,
            struct_ref=struct_ref, is_array=is_array,
        ))
    return fields


def _split_ts_declarations(body: str) -> List[str]:
    """Split a TS interface/type body into individual field declarations.

    Splits on top-level semicolons and newlines, tracking depth in
    ``{}``, ``[]``, ``<>``, and ``()`` so nested types aren't split.
    """
    out: List[str] = []
    cur: List[str] = []
    depth = 0
    for c in body:
        if c in '{[<(':
            depth += 1
            cur.append(c)
        elif c in '}]>)':
            depth -= 1
            cur.append(c)
        elif c == ';' and depth == 0:
            out.append(''.join(cur))
            cur = []
        elif c == '\n' and depth == 0:
            out.append(''.join(cur))
            cur = []
        else:
            cur.append(c)
    if cur:
        out.append(''.join(cur))
    return out


def _classify_ts_type(type_str: str) -> Tuple[Optional[str], bool]:
    """Return ``(struct_ref, is_array)`` for a TS type expression.

    * ``User`` -> (``"User"``, False)
    * ``User[]`` -> (``"User"``, True)
    * ``Array<User>`` -> (``"User"``, True)
    * ``string`` / ``number`` / ``boolean`` -> (None, False)
    * ``'a' | 'b'`` -> (None, False)  (string literal union)
    * ``Record<string, X>`` -> (None, False)
    * ``{ sub: type }`` -> (None, False)  (inline object)
    """
    t = type_str.strip()
    # Array forms.
    if t.endswith('[]'):
        inner = t[:-2].strip()
        ref = _extract_named_ref(inner)
        return (ref, True)
    m = re.match(r'^Array<(.+)>$', t)
    if m:
        inner = m.group(1).strip()
        ref = _extract_named_ref(inner)
        return (ref, True)
    # Plain named type.
    ref = _extract_named_ref(t)
    return (ref, False)


def _extract_named_ref(type_str: str) -> Optional[str]:
    """If ``type_str`` is a single named identifier (e.g. ``User``,
    ``MembershipInfo``), return it. Otherwise return None.
    """
    t = type_str.strip()
    # Strip parens.
    while t.startswith('(') and t.endswith(')'):
        t = t[1:-1].strip()
    if re.match(r'^[A-Z]\w*$', t):
        return t
    # `import('...').X` form — extract X.
    m = re.match(r'^import\([^)]*\)\.([A-Z]\w*)$', t)
    if m:
        return m.group(1)
    return None


# ---------------------------------------------------------------------------
# TS client parser
# ---------------------------------------------------------------------------

# `api.<method><<Type>>(url, ...)` — captures method, optional Type,
# and the URL (string or template literal).
RE_API_CALL = re.compile(
    r'\bapi\.(?P<method>get|post|put|patch|delete)'
    r'(?:\s*<\s*(?P<type>[^>]+?)\s*>)?'
    r'\s*\(\s*'
)

# A simple URL string: `'/foo'` or `"/foo"`.
RE_URL_STRING = re.compile(r'^\s*[\'"](?P<url>[^\'"]+)[\'"]')

# A template-literal URL: `` `/foo/${id}` ``.
RE_URL_TEMPLATE = re.compile(r'^\s*`(?P<url>[^`]+)`')


def parse_ts_client(content: str, file: str) -> List[TSEndpoint]:
    """Parse ``client.ts`` and extract every API endpoint.

    For each ``api.<method><<Type>>(url, ...)`` call we capture:
      * HTTP method (uppercased)
      * URL (with ``${var}`` normalised to ``{var}`` and ``/api`` prepended)
      * Response type (raw text)
    """
    endpoints: List[TSEndpoint] = []
    # We need to also capture the surrounding API group and method name
    # for context. Walk the file looking for `export const xxxApi = {`
    # blocks and attribute each api.* call to the most recently seen
    # group.
    current_group = ''
    current_method = ''
    lines = content.splitlines()
    # Build a map of line -> (group, method) for context attribution.
    context_by_line: Dict[int, Tuple[str, str]] = {}
    line_no = 0
    in_group = False
    for line in lines:
        line_no += 1
        # `export const authApi = {`
        gm = re.match(r'^\s*export\s+const\s+(\w+Api)\s*=\s*\{', line)
        if gm:
            current_group = gm.group(1)
            current_method = ''
            in_group = True
            continue
        if in_group:
            # `methodName: (args) =>` — capture method name.
            mm = re.match(r'^\s*(\w+)\s*:\s*(?:async\s*)?\(', line)
            if mm:
                current_method = mm.group(1)
            # Detect end of group: a line with just `};` at column 0.
            if re.match(r'^\};?\s*$', line):
                in_group = False
                current_group = ''
                current_method = ''
            else:
                context_by_line[line_no] = (current_group, current_method)

    for m in RE_API_CALL.finditer(content):
        method = m.group('method').upper()
        type_str = (m.group('type') or '').strip()
        line = line_of(content, m.start())
        # The URL follows the open paren.
        rest = content[m.end():]
        url = _extract_url(rest)
        if url is None:
            continue
        normalised = _normalise_ts_url(url)
        # Classify the response type.
        response_kind, response_fields = _classify_ts_response(type_str)
        group, method_name = context_by_line.get(line, ('', ''))
        endpoints.append(TSEndpoint(
            method=method,
            path=normalised,
            response_type=type_str or '(unknown)',
            response_kind=response_kind,
            response_fields=response_fields,
            file=file,
            line=line,
            api_group=group,
            method_name=method_name,
        ))
    return endpoints


def _extract_url(rest: str) -> Optional[str]:
    """Extract the URL string (or template literal) from the start of
    ``rest`` (the text immediately after ``api.method<TYPE>(``).
    """
    # Try a simple quoted string first.
    m = RE_URL_STRING.match(rest)
    if m:
        return m.group('url')
    # Try a template literal.
    m = RE_URL_TEMPLATE.match(rest)
    if m:
        return m.group('url')
    # Backtick template that may span multiple lines — find the next
    # backtick.
    if rest.lstrip().startswith('`'):
        idx = rest.find('`')
        end = rest.find('`', idx + 1)
        if end != -1:
            return rest[idx + 1:end]
    return None


def _normalise_ts_url(url: str) -> str:
    """Normalise a TS URL to match the Go route form.

    * Convert ``${var}`` to ``{var}`` (gorilla/mux syntax).
    * Prepend ``/api`` if not already present.
    * Collapse duplicate slashes.
    """
    # Replace ${var} with {var}.
    url = re.sub(r'\$\{(\w+)\}', r'{\1}', url)
    # Prepend /api if missing.
    if not url.startswith('/api'):
        if url.startswith('/'):
            url = '/api' + url
        else:
            url = '/api/' + url
    # Collapse duplicate slashes (but keep the leading double-slash if any).
    url = re.sub(r'/+', '/', url)
    return url


def _classify_ts_response(type_str: str) -> Tuple[str, List[TSField]]:
    """Classify a TS response type string and parse inline fields.

    Returns ``(kind, fields)`` where kind is one of
    ``"named"``, ``"inline"``, ``"unknown"``.
    """
    if not type_str:
        return ('unknown', [])
    t = type_str.strip()
    # Strip a union like `AuthResponse | MFARequiredResponse` — take
    # the first named branch.
    if '|' in t and not t.startswith('{'):
        bits = [b.strip() for b in t.split('|')]
        for b in bits:
            if re.match(r'^[A-Z]\w*$', b):
                return ('named', [])
        return ('unknown', [])
    # Inline object literal: `{ user: User; memberships: MembershipInfo[] }`.
    if t.startswith('{'):
        # Parse the fields.
        body = t[1:]
        # Find the matching closing brace (the type string may have
        # been truncated by the `<...>` regex if it contained `>` —
        # best-effort: strip a trailing `}` if present).
        if body.endswith('}'):
            body = body[:-1]
        fields = _parse_ts_fields(body)
        return ('inline', fields)
    # Named type.
    if re.match(r'^[A-Z]\w*$', t):
        return ('named', [])
    return ('unknown', [])


# ---------------------------------------------------------------------------
# Shape comparison
# ---------------------------------------------------------------------------

# Go primitive types that map to TS `number`.
GO_NUMERIC_TYPES = {
    'int', 'int8', 'int16', 'int32', 'int64',
    'uint', 'uint8', 'uint16', 'uint32', 'uint64',
    'float32', 'float64',
    'byte', 'rune',
}

# Go types that JSON-marshal as a string.
GO_STRING_TYPES = {
    'string', 'time.Time', 'primitive.ObjectID', 'primitive.DateTime',
    'json.RawMessage',
}

# Set of Go named types that are aliases for a primitive (e.g.
# ``type MemberRole string``). Populated at parse time by scanning
# every Go file for ``type X <primitive>`` declarations. Used by
# ``normalise_go_type`` to treat these aliases as their underlying
# primitive (so ``MemberRole`` matches TS ``string``).
GO_PRIMITIVE_ALIASES: Dict[str, str] = {}

# Map of TS type-alias names to their normalised underlying type
# (e.g. ``ConfigVarType`` -> ``string`` when the alias is
# ``'string' | 'numeric' | 'enum' | 'template'``). Populated at parse
# time from ``type X = ...`` declarations whose RHS is a primitive
# literal union. Used by ``normalise_ts_type`` to collapse named
# aliases to their underlying primitive (mirroring Go's primitive
# alias handling).
TS_PRIMITIVE_ALIASES: Dict[str, str] = {}


def _scan_primitive_aliases(repo: Path) -> None:
    """Populate ``GO_PRIMITIVE_ALIASES`` by scanning every Go file for
    ``type X string`` / ``type X int`` / etc. declarations.
    """
    GO_PRIMITIVE_ALIASES.clear()
    alias_re = re.compile(
        r'\btype\s+(?P<name>[A-Z]\w*)\s+(?P<underlying>string|int|int8|int16|int32|int64|uint|uint8|uint16|uint32|uint64|float32|float64|byte|rune|bool)\b'
    )
    for f in find_go_files(repo):
        try:
            text = f.read_text(encoding='utf-8', errors='replace')
        except Exception:
            continue
        for m in alias_re.finditer(text):
            GO_PRIMITIVE_ALIASES.setdefault(m.group('name'), m.group('underlying'))


def _scan_ts_primitive_aliases(ts_types: List['TSType']) -> None:
    """Populate ``TS_PRIMITIVE_ALIASES`` from parsed TS type aliases.

    A TS alias is considered a "primitive alias" if its raw value is a
    union of string/number/boolean literals (e.g. ``'a' | 'b'``) or a
    single primitive. The alias name maps to its normalised primitive.
    """
    TS_PRIMITIVE_ALIASES.clear()
    for t in ts_types:
        if t.kind != 'type_alias' or not t.raw:
            continue
        # Try to normalise the raw value. If it resolves to a primitive
        # (string/number/boolean), record the alias.
        normalised = normalise_ts_type(t.raw)
        base = normalised.rstrip('?')
        if base in {'string', 'number', 'boolean'}:
            TS_PRIMITIVE_ALIASES.setdefault(t.name, base)


def normalise_go_type(go_type: str) -> str:
    """Normalise a Go type to a canonical form for comparison with TS.

    Examples:
      ``string``           -> ``string``
      ``*string``          -> ``string?``
      ``int64``            -> ``number``
      ``*time.Time``       -> ``string?``
      ``primitive.ObjectID`` -> ``string``
      ``models.User``      -> ``User``
      ``[]string``         -> ``string[]``
      ``[]models.User``    -> ``User[]``
      ``map[string]X``     -> ``Record<string, X>``
      ``MemberRole``       -> ``string`` (if ``type MemberRole string``
      was found in the codebase)
    """
    t = go_type.strip()
    # Strip a leading `*` (pointer).
    optional = False
    if t.startswith('*'):
        optional = True
        t = t[1:].strip()
    # Slice.
    if t.startswith('[]'):
        inner = t[2:].strip()
        return normalise_go_type(inner) + '[]'
    # Map (best-effort — we don't recurse into the value type).
    if t.startswith('map['):
        # Extract the value type.
        m = re.match(r'^map\[[^\]]+\](.+)$', t)
        if m:
            val = normalise_go_type(m.group(1).strip())
            return f'Record<string, {val}>'
    # String-serialising types (check BEFORE stripping the package
    # prefix — the set contains fully-qualified names like
    # `time.Time` and `primitive.ObjectID`).
    if t in GO_STRING_TYPES:
        return 'string' + ('?' if optional else '')
    # Package-qualified type.
    if '.' in t:
        base = t.rsplit('.', 1)[-1]
        # Check if the base is a known primitive alias.
        if base in GO_PRIMITIVE_ALIASES:
            underlying = GO_PRIMITIVE_ALIASES[base]
            return normalise_go_type(underlying) + ('?' if optional else '')
        return base + ('?' if optional else '')
    # Primitive alias (e.g. ``MemberRole`` -> ``string``).
    if t in GO_PRIMITIVE_ALIASES:
        underlying = GO_PRIMITIVE_ALIASES[t]
        return normalise_go_type(underlying) + ('?' if optional else '')
    # Primitive mappings.
    if t in GO_NUMERIC_TYPES:
        return 'number' + ('?' if optional else '')
    if t == 'bool':
        return 'boolean' + ('?' if optional else '')
    if t == 'interface{}' or t == 'any':
        return 'unknown'
    return t + ('?' if optional else '')


def normalise_ts_type(ts_type: str) -> str:
    """Normalise a TS type to a canonical form for comparison with Go.

    Examples:
      ``string``           -> ``string``
      ``string | undefined`` -> ``string?``
      ``number``           -> ``number``
      ``User``             -> ``User``
      ``User[]``           -> ``User[]``
      ``'a' | 'b'``        -> ``string``  (literal union collapses to string)
      ``Record<string, X>`` -> ``Record<string, X>``
      ``ConfigVarType``    -> ``string``  (if the alias resolves to a
      string literal union)
    """
    t = ts_type.strip()
    # Strip parens.
    while t.startswith('(') and t.endswith(')'):
        t = t[1:-1].strip()
    # Named alias that resolves to a primitive (e.g. ``ConfigVarType``
    # whose definition is ``'string' | 'numeric' | 'enum' | 'template'``).
    if re.match(r'^[A-Z]\w*$', t) and t in TS_PRIMITIVE_ALIASES:
        return TS_PRIMITIVE_ALIASES[t]
    # Union with undefined/null -> optional.
    optional = False
    if '|' in t:
        bits = [b.strip() for b in t.split('|')]
        if 'undefined' in bits:
            optional = True
            bits = [b for b in bits if b != 'undefined']
        # If all remaining bits are string literals, collapse to string.
        if bits and all(re.match(r"^['\"]", b) for b in bits):
            return 'string' + ('?' if optional else '')
        # If all remaining bits are number literals, collapse to number.
        if bits and all(re.match(r'^-?\d+(\.\d+)?$', b) for b in bits):
            return 'number' + ('?' if optional else '')
        # If exactly one non-null branch remains, recurse.
        if len(bits) == 1:
            t = bits[0]
        else:
            # Mixed union — keep as a sorted union string.
            return ' | '.join(sorted(bits)) + ('?' if optional else '')
    # Array.
    if t.endswith('[]'):
        inner = t[:-2].strip()
        return normalise_ts_type(inner) + '[]'
    m = re.match(r'^Array<(.+)>$', t)
    if m:
        return normalise_ts_type(m.group(1).strip()) + '[]'
    # String literal.
    if t.startswith("'") or t.startswith('"'):
        return 'string' + ('?' if optional else '')
    # Boolean literal.
    if t in {'true', 'false'}:
        return 'boolean' + ('?' if optional else '')
    # Number literal.
    if re.match(r'^-?\d+(\.\d+)?$', t):
        return 'number' + ('?' if optional else '')
    return t + ('?' if optional else '')


def types_compatible(go_type: str, ts_type: str) -> Tuple[bool, str]:
    """Return ``(is_compatible, note)`` for a Go↔TS type pair.

    The note explains the mismatch when not compatible.

    A Go type of ``unknown`` (used when the response payload contains a
    value the auditor can't statically resolve — e.g. a package-qualified
    constant like ``version.Current``) is treated as compatible with any
    TS type, since we can't know the actual type without type info.
    """
    g = normalise_go_type(go_type)
    t = normalise_ts_type(ts_type)
    # `unknown` Go types are compatible with anything — we can't know
    # the actual type without full Go type inference.
    if g == 'unknown' or go_type.strip() == 'unknown':
        return (True, 'Go type unknown — not statically resolvable')
    if g == t:
        return (True, '')
    # Strip optional markers for the comparison — optionality is
    # handled separately (a Go field is optional if it's a pointer or
    # omitempty; a TS field is optional if marked with `?`).
    g_base = g.rstrip('?')
    t_base = t.rstrip('?')
    if g_base == t_base:
        return (True, 'optional differs')
    # Record<string, X> on both sides — recurse on X (best-effort: skip).
    if g_base.startswith('Record<string,') and t_base.startswith('Record<string,'):
        return (True, 'record values not deeply compared')
    # Known mismatch patterns:
    # Go int64 / number vs TS string — classic JS precision bug for IDs.
    if g_base == 'number' and t_base == 'string':
        return (False, f'Go {go_type} (number) vs TS {ts_type} (string) — possible ID precision bug')
    if g_base == 'string' and t_base == 'number':
        return (False, f'Go {go_type} (string) vs TS {ts_type} (number)')
    if g_base == 'boolean' and t_base != 'boolean':
        return (False, f'Go {go_type} (boolean) vs TS {ts_type}')
    # Named struct references that differ in name.
    if g_base and t_base and g_base[0].isupper() and t_base[0].isupper():
        if g_base != t_base:
            return (False, f'struct name mismatch: Go {g_base} vs TS {t_base}')
    return (False, f'Go {g} vs TS {t}')


# ---------------------------------------------------------------------------
# Endpoint matching + comparison
# ---------------------------------------------------------------------------

def normalise_path_for_matching(path: str) -> str:
    """Normalise a URL path for endpoint matching.

    Strips trailing slashes (except root) and lowercases path parameter
    names so ``/users/{userId}`` and ``/users/${userId}`` both become
    ``/users/{userid}``.
    """
    p = path
    # Strip query string.
    if '?' in p:
        p = p.split('?', 1)[0]
    # Strip trailing slash (except root).
    if len(p) > 1 and p.endswith('/'):
        p = p[:-1]
    # Lowercase path parameter names so {userId} and {userid} match.
    p = re.sub(r'\{(\w+)\}', lambda m: '{' + m.group(1).lower() + '}', p)
    return p


def build_go_endpoint_shapes(
    routes: List[GoRoute],
    handlers_by_name: Dict[str, GoHandler],
    structs_by_name: Dict[str, GoStruct],
) -> Dict[str, List[GoResponseShape]]:
    """Build a ``{(method, normalised_path): [GoResponseShape, ...]}`` map.

    For each route, look up the handler and collect ALL its non-error
    response shapes (handlers may have multiple success-path responses,
    e.g. an MFA branch and a normal branch). Error responses (maps
    with only ``message``/``error`` keys) are skipped.
    """
    out: Dict[str, List[GoResponseShape]] = {}
    for r in routes:
        key = f'{r.method} {normalise_path_for_matching(r.path)}'
        handler = handlers_by_name.get(r.handler_func)
        if not handler:
            out[key] = [GoResponseShape(kind='unknown',
                                        raw=f'(no handler found: {r.handler_func})')]
            continue
        if not handler.responses:
            out[key] = [GoResponseShape(kind='unknown',
                                        raw='(no respondWithJSON call found)')]
            continue
        # Collect all non-error response shapes.
        shapes: List[GoResponseShape] = []
        for shape in handler.responses:
            if shape.kind == 'map_literal':
                names = [f.name for f in shape.fields]
                if names and all(n in {'message', 'error'} for n in names):
                    continue
            shapes.append(shape)
        if not shapes:
            shapes = [handler.responses[0]]
        out[key] = shapes
    return out


def resolve_go_shape_fields(
    shape: GoResponseShape,
    structs_by_name: Dict[str, GoStruct],
) -> List[GoResponseField]:
    """Resolve a GoResponseShape into a flat list of top-level fields.

    For a ``struct_literal`` shape, look up the struct's fields and
    return them as GoResponseField entries (with ``struct_ref`` set to
    the struct name for nested comparison).

    For a ``map_literal`` shape, return the parsed fields directly.

    Inline-embedded struct fields (``models.EventDefinition
    `json:",inline"` ``) are recursively flattened: the embedded
    struct's fields are spliced into the output at the position of the
    embedding. This matches Go's standard JSON marshalling behaviour
    for embedded structs.
    """
    if shape.kind == 'struct_literal' and shape.struct_name:
        s = structs_by_name.get(shape.struct_name)
        if not s:
            return []
        return _flatten_struct_fields(s, structs_by_name, set())
    if shape.kind == 'map_literal':
        return shape.fields
    return []


def _flatten_struct_fields(
    struct: GoStruct,
    structs_by_name: Dict[str, GoStruct],
    visited: Set[str],
) -> List[GoResponseField]:
    """Return the struct's fields as GoResponseField entries, recursing
    into inline-embedded struct fields.

    ``visited`` is the set of struct names already being expanded —
    prevents infinite recursion on cyclic embeddings (which shouldn't
    exist but are guarded against defensively).
    """
    if struct.name in visited:
        return []
    visited = visited | {struct.name}
    out: List[GoResponseField] = []
    for f in struct.fields:
        if f.is_skipped:
            continue
        if f.is_inline_embed:
            # Recurse into the embedded struct.
            embedded_name = _strip_package(f.go_type)
            embedded_struct = structs_by_name.get(embedded_name)
            if embedded_struct:
                out.extend(_flatten_struct_fields(
                    embedded_struct, structs_by_name, visited,
                ))
            # If we couldn't resolve the embedded struct, the fields
            # are silently dropped (best-effort — the report will
            # note the shape as incomplete via the missing-in-go check).
            continue
        base_type = f.go_type
        is_array = base_type.startswith('[]')
        if is_array:
            base_type = base_type[2:]
        struct_ref = _strip_package(base_type)
        # Heuristic: only treat as a struct reference if the name
        # starts with an uppercase letter and isn't a primitive.
        if struct_ref and not struct_ref[0].isupper():
            struct_ref = None
        elif struct_ref and struct_ref in GO_NUMERIC_TYPES | GO_STRING_TYPES | {'bool', 'interface{}', 'any'}:
            struct_ref = None
        out.append(GoResponseField(
            name=f.json_name,
            go_type=f.go_type,
            struct_ref=struct_ref,
            is_array=is_array,
        ))
    return out


def resolve_ts_response_fields(
    endpoint: TSEndpoint,
    ts_types_by_name: Dict[str, TSType],
) -> List[TSField]:
    """Resolve a TS endpoint's response type into a flat list of fields.

    For a named type, look it up in ``ts_types_by_name`` and return
    its fields. For an inline object, return the parsed fields
    directly. For a union, take the first named branch.
    """
    if endpoint.response_kind == 'inline':
        return endpoint.response_fields
    if endpoint.response_kind == 'named':
        t = ts_types_by_name.get(endpoint.response_type.strip())
        if t:
            return t.fields
    return []


def resolve_ts_response_candidates(
    endpoint: TSEndpoint,
    ts_types_by_name: Dict[str, TSType],
) -> List[Tuple[str, List[TSField]]]:
    """Resolve a TS endpoint's response type into a list of candidate
    ``(type_name, fields)`` pairs.

    For a union type like ``AuthResponse | MFARequiredResponse``, this
    returns both branches. For a named or inline type, returns a single
    candidate. Used by the comparison logic to try matching the Go
    shape against each branch and report OK if any matches.
    """
    out: List[Tuple[str, List[TSField]]] = []
    if endpoint.response_kind == 'inline':
        out.append((endpoint.response_type, endpoint.response_fields))
        return out
    if endpoint.response_kind == 'named':
        t = endpoint.response_type.strip()
        # Handle union types: split on `|` and try each named branch.
        if '|' in t:
            for branch in t.split('|'):
                b = branch.strip()
                # Strip `import('...').X` form.
                m = re.match(r"^import\([^)]*\)\.([A-Z]\w*)$", b)
                if m:
                    b = m.group(1)
                if re.match(r'^[A-Z]\w*$', b):
                    tt = ts_types_by_name.get(b)
                    if tt:
                        out.append((b, tt.fields))
            return out
        # Single named type.
        tt = ts_types_by_name.get(t)
        if tt:
            out.append((t, tt.fields))
    return out


def compare_endpoint(
    method: str,
    path: str,
    ts_ep: TSEndpoint,
    go_shapes: List[GoResponseShape],
    go_handler: Optional[GoHandler],
    structs_by_name: Dict[str, GoStruct],
    ts_types_by_name: Dict[str, TSType],
    available_field_names: Optional[Set[str]] = None,
) -> Comparison:
    """Compare a single TS endpoint against its Go counterpart.

    For TS union types (e.g. ``AuthResponse | MFARequiredResponse``),
    each Go response shape is matched against each TS branch — if any
    pair matches, the endpoint is reported as OK. This handles handlers
    that return different shapes on different code paths (e.g. an MFA
    branch and a normal branch).

    ``available_field_names`` is an optional set of field names that
    are "available" in the Go handler but not necessarily in the
    response shape (e.g. fields of structs referenced by handler
    variables, fields of local wrapper structs in the same file,
    fields of map responses elsewhere in the handler). A TS field in
    this set is not flagged as "missing in Go" — this suppresses
    false positives where the regex-based parser can't see the field
    but it's actually present in the Go code.
    """
    candidates = resolve_ts_response_candidates(ts_ep, ts_types_by_name)
    if not candidates:
        ts_fields: List[TSField] = []
        candidates = [(ts_ep.response_type, ts_fields)]
    if not go_shapes:
        ts_fields = candidates[0][1]
        return Comparison(
            method=method, path=path,
            go_handler=None, go_file=None,
            go_response_kind='no_handler',
            go_struct=None,
            go_fields=[],
            ts_response_type=ts_ep.response_type,
            ts_fields=ts_fields,
            missing_in_go=[f.name for f in ts_fields],
            extra_in_go=[],
            type_mismatches=[],
            status='no_go_handler',
        )

    if available_field_names is None:
        available_field_names = set()

    # Try each (Go shape, TS candidate) pair and pick the best match.
    best: Optional[Comparison] = None
    best_score = -1
    alias_cache: Set[Tuple[str, str]] = set()
    for go_shape in go_shapes:
        go_fields = resolve_go_shape_fields(go_shape, structs_by_name)
        # If we couldn't resolve any Go fields, treat the shape as unknown.
        if go_shape.kind == 'unknown' or (
            not go_fields and go_shape.kind != 'map_literal'
        ):
            if go_shape.kind == 'map_literal' and not go_shape.fields:
                pass  # empty map — fall through
            else:
                ts_fields = candidates[0][1]
                comp = Comparison(
                    method=method, path=path,
                    go_handler=go_handler.name if go_handler else None,
                    go_file=go_handler.file if go_handler else None,
                    go_response_kind='unknown',
                    go_struct=None,
                    go_fields=[],
                    ts_response_type=ts_ep.response_type,
                    ts_fields=ts_fields,
                    missing_in_go=[],
                    extra_in_go=[],
                    type_mismatches=[],
                    status='unknown_go_shape',
                )
                score = 1
                if score > best_score:
                    best = comp
                    best_score = score
                continue
        for cand_type, ts_fields in candidates:
            comp = _compare_fields(
                method=method, path=path,
                ts_ep=ts_ep, ts_fields=ts_fields,
                go_shape=go_shape, go_handler=go_handler,
                go_fields=go_fields,
                structs_by_name=structs_by_name,
                ts_types_by_name=ts_types_by_name,
                _alias_cache=alias_cache,
                available_field_names=available_field_names,
            )
            score = {
                'ok': 5,
                'extra_in_go': 4,
                'missing_in_go': 3,
                'type_mismatch': 2,
                'unknown_go_shape': 1,
                'no_go_handler': 0,
            }.get(comp.status, 0)
            if score > best_score:
                best = comp
                best_score = score

    # If there are multiple Go shapes (e.g. an MFA branch + a normal
    # branch), also try the UNION of all Go shapes' fields. This handles
    # TS types that declare all fields as optional (e.g.
    # `{ accessToken?: string; mfaRequired?: boolean; ... }`) where the
    # Go handler returns a different subset on each code path.
    if len(go_shapes) > 1:
        merged_fields: Dict[str, GoResponseField] = {}
        merged_shape_kind = 'map_literal'
        for gs in go_shapes:
            gf = resolve_go_shape_fields(gs, structs_by_name)
            for f in gf:
                if f.name and f.name not in merged_fields:
                    merged_fields[f.name] = f
        merged_go_fields = list(merged_fields.values())
        if merged_go_fields:
            merged_shape = GoResponseShape(
                kind=merged_shape_kind,
                fields=merged_go_fields,
                raw='(merged from multiple response shapes)',
            )
            for cand_type, ts_fields in candidates:
                comp = _compare_fields(
                    method=method, path=path,
                    ts_ep=ts_ep, ts_fields=ts_fields,
                    go_shape=merged_shape, go_handler=go_handler,
                    go_fields=merged_go_fields,
                    structs_by_name=structs_by_name,
                    ts_types_by_name=ts_types_by_name,
                    _alias_cache=alias_cache,
                    available_field_names=available_field_names,
                )
                score = {
                    'ok': 5,
                    'extra_in_go': 4,
                    'missing_in_go': 3,
                    'type_mismatch': 2,
                    'unknown_go_shape': 1,
                    'no_go_handler': 0,
                }.get(comp.status, 0)
                if score > best_score:
                    best = comp
                    best_score = score

    return best if best is not None else Comparison(
        method=method, path=path,
        go_handler=go_handler.name if go_handler else None,
        go_file=go_handler.file if go_handler else None,
        go_response_kind='unknown',
        go_struct=None,
        go_fields=[],
        ts_response_type=ts_ep.response_type,
        ts_fields=candidates[0][1],
        missing_in_go=[],
        extra_in_go=[],
        type_mismatches=[],
        status='unknown_go_shape',
    )


def _compare_fields(
    method: str,
    path: str,
    ts_ep: TSEndpoint,
    ts_fields: List[TSField],
    go_shape: GoResponseShape,
    go_handler: Optional[GoHandler],
    go_fields: List[GoResponseField],
    structs_by_name: Optional[Dict[str, GoStruct]] = None,
    ts_types_by_name: Optional[Dict[str, TSType]] = None,
    _alias_cache: Optional[Set[Tuple[str, str]]] = None,
    available_field_names: Optional[Set[str]] = None,
) -> Comparison:
    """Compare a specific TS field set against the Go fields.

    ``structs_by_name`` and ``ts_types_by_name`` are optional — when
    provided, struct-name mismatches (e.g. Go ``MemberResponse`` vs TS
    ``TenantMember``) are checked recursively: if both structs have
    field-compatible shapes, the names are treated as aliases and the
    mismatch is suppressed. This eliminates false positives where the
    Go and TS codebases use different names for the same shape.

    ``available_field_names`` is an optional set of field names that
    are "available" in the Go handler (e.g. fields of structs
    referenced by handler variables, fields of local wrapper structs
    in the same file, fields of map responses elsewhere in the
    handler). A TS-required field in this set is NOT flagged as
    "missing in Go" — this suppresses false positives where the
    regex-based parser can't see the field but it's actually present
    in the Go code (e.g. the handler has access to a struct field
    that the response map doesn't explicitly include).
    """
    go_field_map: Dict[str, GoResponseField] = {f.name: f for f in go_fields if f.name}
    ts_field_map: Dict[str, TSField] = {f.name: f for f in ts_fields if f.name}
    if available_field_names is None:
        available_field_names = set()
    # A TS field marked optional (`field?: type`) does NOT need to be
    # sent by Go — the frontend tolerates its absence. Only flag a TS
    # field as "missing in Go" if it's required (non-optional) AND not
    # present in the Go response AND not "available" via any of the
    # supplementary sources (struct flattener, local wrappers, map
    # responses elsewhere in the handler).
    missing = [
        n for n, ts_f in ts_field_map.items()
        if n not in go_field_map
        and not ts_f.is_optional
        and n not in available_field_names
    ]
    extra = [n for n in go_field_map if n not in ts_field_map]
    mismatches: List[Dict[str, str]] = []
    if _alias_cache is None:
        _alias_cache = set()
    for name, ts_f in ts_field_map.items():
        go_f = go_field_map.get(name)
        if not go_f:
            continue
        ok, note = types_compatible(go_f.go_type, ts_f.ts_type)
        if not ok:
            # Try struct-alias reconciliation: if Go and TS both
            # reference struct types whose fields are recursively
            # compatible, treat them as aliases (e.g. Go
            # ``MemberResponse`` vs TS ``TenantMember`` — same shape,
            # different names).
            if structs_by_name and ts_types_by_name:
                if _is_struct_alias(
                    go_f.go_type, ts_f.ts_type,
                    structs_by_name, ts_types_by_name,
                    _alias_cache,
                ):
                    ok = True
                    note = f'struct alias: Go {go_f.go_type} ≡ TS {ts_f.ts_type} (same field shapes)'
            if not ok:
                mismatches.append({
                    'field': name,
                    'go_type': go_f.go_type,
                    'ts_type': ts_f.ts_type,
                    'note': note,
                })
    if mismatches:
        status = 'type_mismatch'
    elif missing:
        status = 'missing_in_go'
    elif extra:
        status = 'extra_in_go'
    else:
        status = 'ok'
    return Comparison(
        method=method, path=path,
        go_handler=go_handler.name if go_handler else None,
        go_file=go_handler.file if go_handler else None,
        go_response_kind=go_shape.kind,
        go_struct=go_shape.struct_name,
        go_fields=go_fields,
        ts_response_type=ts_ep.response_type,
        ts_fields=ts_fields,
        missing_in_go=missing,
        extra_in_go=extra,
        type_mismatches=mismatches,
        status=status,
    )


def _is_struct_alias(
    go_type: str,
    ts_type: str,
    structs_by_name: Dict[str, GoStruct],
    ts_types_by_name: Dict[str, TSType],
    alias_cache: Set[Tuple[str, str]],
    _depth: int = 0,
) -> bool:
    """Return True if ``go_type`` and ``ts_type`` are struct references
    whose field shapes are recursively compatible (i.e. they're the
    same shape under different names — a common pattern when the Go
    backend uses an internal response struct and the TS frontend uses
    a domain-named interface).

    Cycle-safe via ``alias_cache`` and a depth guard.
    """
    if _depth > 5:
        return False
    # Strip array markers from both sides.
    g = go_type.strip()
    t = ts_type.strip()
    while g.startswith('[]'):
        g = g[2:].strip()
    while t.endswith('[]'):
        t = t[:-2].strip()
    # Strip pointer.
    if g.startswith('*'):
        g = g[1:].strip()
    # Strip package prefix from Go side.
    g_name = _strip_package(g)
    # Strip TS parens / unions / generics (best-effort).
    t_name = t.strip()
    while t_name.startswith('(') and t_name.endswith(')'):
        t_name = t_name[1:-1].strip()
    # Only attempt reconciliation if both look like named struct refs.
    if not (g_name and t_name and
            g_name[0].isupper() and t_name[0].isupper()):
        return False
    # Only single-token TS names (no unions / generics).
    if not re.match(r'^[A-Z]\w*$', t_name):
        return False
    cache_key = (g_name, t_name)
    if cache_key in alias_cache:
        return True
    # Look up the structs.
    go_struct = structs_by_name.get(g_name)
    ts_struct = ts_types_by_name.get(t_name)
    if not go_struct or not ts_struct:
        return False
    # Compare field shapes (best-effort: only top-level field names +
    # type compatibility, without recursing into nested struct refs
    # beyond the alias check).
    go_fields = _flatten_struct_fields(go_struct, structs_by_name, set())
    ts_fields = ts_struct.fields
    go_map = {f.name: f for f in go_fields if f.name}
    ts_map = {f.name: f for f in ts_fields if f.name}
    # All TS fields must be present in Go (TS optionality tolerated).
    for ts_n, ts_f in ts_map.items():
        if ts_n not in go_map:
            if ts_f.is_optional:
                continue
            return False
    # All Go fields must be present in TS (Go extras tolerated only if
    # they're optional; otherwise the shapes differ enough that we
    # shouldn't claim aliasing).
    for go_n in go_map:
        if go_n not in ts_map:
            return False
    # Field types must be compatible (recursively, via alias check).
    for ts_n, ts_f in ts_map.items():
        go_f = go_map.get(ts_n)
        if not go_f:
            continue
        ok, _ = types_compatible(go_f.go_type, ts_f.ts_type)
        if ok:
            continue
        # Try nested alias reconciliation.
        if _is_struct_alias(
            go_f.go_type, ts_f.ts_type,
            structs_by_name, ts_types_by_name,
            alias_cache, _depth + 1,
        ):
            continue
        return False
    alias_cache.add(cache_key)
    return True


# ---------------------------------------------------------------------------
# File walking
# ---------------------------------------------------------------------------

SKIP_DIRS = {'vendor', 'node_modules', '.git', 'graphify-out', 'dist',
             'build', 'testdata'}


def find_go_files(repo: Path, include_tests: bool = False) -> List[Path]:
    out: List[Path] = []
    for p in repo.rglob('*.go'):
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        if not include_tests and p.name.endswith('_test.go'):
            continue
        out.append(p)
    return sorted(out)


def find_ts_files(repo: Path) -> List[Path]:
    out: List[Path] = []
    for p in repo.rglob('*.ts'):
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        if p.name.endswith('.d.ts'):
            continue
        out.append(p)
    return sorted(out)


# ---------------------------------------------------------------------------
# Markdown + JSON emitters
# ---------------------------------------------------------------------------

def emit_json(
    comparisons: List[Comparison],
    unmatched_ts: List[TSEndpoint],
    unmatched_go: List[GoRoute],
    go_structs: List[GoStruct],
    ts_types: List[TSType],
    repo: Path,
) -> str:
    payload = {
        'repository': str(repo),
        'summary': {
            'ts_endpoints': len(comparisons) + len(unmatched_ts),
            'go_endpoints': len(comparisons) + len(unmatched_go),
            'matched_endpoints': len(comparisons),
            'ok_endpoints': sum(1 for c in comparisons if c.status == 'ok'),
            'missing_in_go': sum(len(c.missing_in_go) for c in comparisons),
            'extra_in_go': sum(len(c.extra_in_go) for c in comparisons),
            'type_mismatches': sum(len(c.type_mismatches) for c in comparisons),
            'unknown_go_shape': sum(1 for c in comparisons if c.status == 'unknown_go_shape'),
            'no_go_handler': sum(1 for c in comparisons if c.status == 'no_go_handler'),
        },
        'comparisons': [_comparison_to_dict(c) for c in comparisons],
        'unmatched_ts_endpoints': [
            {
                'method': e.method, 'path': e.path,
                'response_type': e.response_type,
                'file': e.file, 'line': e.line,
                'api_group': e.api_group, 'method_name': e.method_name,
            } for e in unmatched_ts
        ],
        'unmatched_go_endpoints': [
            {
                'method': r.method, 'path': r.path,
                'handler_func': r.handler_func,
                'file': r.file, 'line': r.line,
            } for r in unmatched_go
        ],
        'go_structs': [
            {
                'name': s.name, 'file': s.file, 'line': s.line,
                'package': s.package,
                'fields': [
                    {
                        'name': f.name, 'json_name': f.json_name,
                        'go_type': f.go_type,
                        'is_omitempty': f.is_omitempty,
                        'is_skipped': f.is_skipped,
                        'is_optional': f.is_optional,
                    } for f in s.fields
                ],
            } for s in go_structs
        ],
        'ts_types': [
            {
                'name': t.name, 'file': t.file, 'line': t.line,
                'kind': t.kind,
                'fields': [
                    {
                        'name': f.name, 'ts_type': f.ts_type,
                        'is_optional': f.is_optional,
                        'struct_ref': f.struct_ref,
                        'is_array': f.is_array,
                    } for f in t.fields
                ],
            } for t in ts_types
        ],
    }
    return json.dumps(payload, indent=2)


def _comparison_to_dict(c: Comparison) -> Dict:
    return {
        'endpoint': f'{c.method} {c.path}',
        'method': c.method,
        'path': c.path,
        'go_handler': c.go_handler,
        'go_file': c.go_file,
        'go_response_kind': c.go_response_kind,
        'go_struct': c.go_struct,
        'go_fields': [asdict(f) for f in c.go_fields],
        'ts_response_type': c.ts_response_type,
        'ts_fields': [asdict(f) for f in c.ts_fields],
        'missing_in_go': c.missing_in_go,
        'extra_in_go': c.extra_in_go,
        'type_mismatches': c.type_mismatches,
        'status': c.status,
    }


STATUS_BADGE = {
    'ok': '✅ ok',
    'missing_in_go': '🔴 missing in Go',
    'extra_in_go': '🟡 extra in Go',
    'type_mismatch': '🟠 type mismatch',
    'no_go_handler': '⚫ no Go handler',
    'unknown_go_shape': '⚪ Go shape unknown',
}


def emit_markdown(
    comparisons: List[Comparison],
    unmatched_ts: List[TSEndpoint],
    unmatched_go: List[GoRoute],
    go_structs: List[GoStruct],
    ts_types: List[TSType],
    repo: Path,
) -> str:
    lines: List[str] = []
    lines.append('# API Shapes — Backend ↔ Frontend Response Audit')
    lines.append('')
    lines.append(f'**Repository**: `{repo}`')
    lines.append('')
    lines.append('Compares Go backend API response shapes against the')
    lines.append('TypeScript frontend\'s expected response types. Each')
    lines.append('matched endpoint is checked for:')
    lines.append('')
    lines.append('- **Missing in Go** — the frontend expects a field the')
    lines.append('  backend doesn\'t send (frontend bug waiting to happen).')
    lines.append('- **Extra in Go** — the backend sends a field the frontend')
    lines.append('  doesn\'t read (wasted bandwidth / accidental info leak).')
    lines.append('- **Type mismatch** — both sides have the field but the')
    lines.append('  types disagree (e.g. Go `int64` vs TS `string` for an')
    lines.append('  ID — the classic JS precision bug).')
    lines.append('')

    # Summary
    ok = sum(1 for c in comparisons if c.status == 'ok')
    missing = sum(len(c.missing_in_go) for c in comparisons)
    extra = sum(len(c.extra_in_go) for c in comparisons)
    mismatches = sum(len(c.type_mismatches) for c in comparisons)
    unknown = sum(1 for c in comparisons if c.status == 'unknown_go_shape')
    no_handler = sum(1 for c in comparisons if c.status == 'no_go_handler')
    lines.append('## Summary')
    lines.append('')
    lines.append(f'- TS endpoints scanned: **{len(comparisons) + len(unmatched_ts)}**')
    lines.append(f'- Go endpoints scanned: **{len(comparisons) + len(unmatched_go)}**')
    lines.append(f'- Matched endpoints: **{len(comparisons)}**')
    lines.append(f'- ✅ OK: **{ok}**')
    lines.append(f'- ⚪ Unknown Go shape: **{unknown}**')
    lines.append(f'- ⚫ No Go handler: **{no_handler}**')
    lines.append(f'- 🔴 Missing-in-Go fields: **{missing}**')
    lines.append(f'- 🟡 Extra-in-Go fields: **{extra}**')
    lines.append(f'- 🟠 Type mismatches: **{mismatches}**')
    lines.append(f'- Unmatched TS endpoints: **{len(unmatched_ts)}**')
    lines.append(f'- Unmatched Go endpoints: **{len(unmatched_go)}**')
    lines.append('')

    # Comparison table
    lines.append('## Comparison Table')
    lines.append('')
    lines.append('| Endpoint | Go handler | Go struct | TS type | Missing in Go | Extra in Go | Mismatches | Status |')
    lines.append('|----------|------------|-----------|---------|---------------|-------------|------------|--------|')
    for c in sorted(comparisons, key=lambda x: (x.path, x.method)):
        ep = f'`{c.method} {c.path}`'
        handler = f'`{c.go_handler}`' if c.go_handler else '—'
        go_struct = f'`{c.go_struct}`' if c.go_struct else ('(map)' if c.go_response_kind == 'map_literal' else '—')
        ts_type = f'`{c.ts_response_type}`' if c.ts_response_type else '—'
        missing_str = ', '.join(f'`{m}`' for m in c.missing_in_go) if c.missing_in_go else '—'
        extra_str = ', '.join(f'`{m}`' for m in c.extra_in_go) if c.extra_in_go else '—'
        mm_str = str(len(c.type_mismatches)) if c.type_mismatches else '—'
        status = STATUS_BADGE.get(c.status, c.status)
        # Truncate long fields for the table.
        if len(ts_type) > 50:
            ts_type = ts_type[:47] + '…`'
        lines.append(
            f'| {ep} | {handler} | {go_struct} | {ts_type} | {missing_str} | {extra_str} | {mm_str} | {status} |'
        )
    lines.append('')

    # Detail sections for problematic endpoints
    problematic = [c for c in comparisons if c.status != 'ok']
    if problematic:
        lines.append('## Problematic Endpoints — Detail')
        lines.append('')
        for c in sorted(problematic, key=lambda x: (x.status, x.path, x.method)):
            lines.append(f'### `{c.method} {c.path}`')
            lines.append('')
            lines.append(f'- **Status**: {STATUS_BADGE.get(c.status, c.status)}')
            if c.go_handler:
                lines.append(f'- **Go handler**: `{c.go_handler}` (`{c.go_file}`)')
            else:
                lines.append('- **Go handler**: _(not found — endpoint may be unregistered or use an inline closure)_')
            if c.go_struct:
                lines.append(f'- **Go struct**: `{c.go_struct}`')
            elif c.go_response_kind == 'map_literal':
                lines.append('- **Go response**: anonymous `map[string]interface{}` literal')
            elif c.go_response_kind == 'unknown':
                lines.append('- **Go response**: _unparseable (function call or complex expression)_')
            lines.append(f'- **TS response type**: `{c.ts_response_type}`')
            lines.append('')

            # Field comparison table.
            go_field_map = {f.name: f for f in c.go_fields if f.name}
            ts_field_map = {f.name: f for f in c.ts_fields if f.name}
            all_names = sorted(set(go_field_map) | set(ts_field_map))
            if all_names:
                lines.append('| Field | Go type | TS type | Notes |')
                lines.append('|------|---------|---------|-------|')
                for name in all_names:
                    go_f = go_field_map.get(name)
                    ts_f = ts_field_map.get(name)
                    go_t = go_f.go_type if go_f else '_(missing)_'
                    ts_t = ts_f.ts_type if ts_f else '_(missing)_'
                    notes: List[str] = []
                    if not go_f:
                        notes.append('🔴 missing in Go')
                    if not ts_f:
                        notes.append('🟡 extra in Go')
                    if go_f and ts_f:
                        ok, note = types_compatible(go_f.go_type, ts_f.ts_type)
                        if not ok:
                            notes.append(f'🟠 {note}')
                    lines.append(
                        f'| `{name}` | `{go_t}` | `{ts_t}` | ' + '; '.join(notes) + ' |'
                    )
                lines.append('')

            # Highlight type mismatches explicitly.
            if c.type_mismatches:
                lines.append('**Type mismatches:**')
                lines.append('')
                for mm in c.type_mismatches:
                    lines.append(
                        f'- `{mm["field"]}`: Go `{mm["go_type"]}` vs TS'
                        f' `{mm["ts_type"]}` — {mm["note"]}'
                    )
                lines.append('')

    # Unmatched TS endpoints
    if unmatched_ts:
        lines.append('## Unmatched TS Endpoints')
        lines.append('')
        lines.append('These frontend API calls have no matching Go route. The')
        lines.append('backend may not implement them, or the URL/method may')
        lines.append('differ from what the frontend expects.')
        lines.append('')
        lines.append('| Method | Path | TS type | File |')
        lines.append('|--------|------|---------|------|')
        for e in sorted(unmatched_ts, key=lambda x: (x.path, x.method)):
            ts_type = f'`{e.response_type}`' if e.response_type else '—'
            if len(ts_type) > 50:
                ts_type = ts_type[:47] + '…`'
            lines.append(
                f'| `{e.method}` | `{e.path}` | {ts_type} | `{e.file}:{e.line}` |'
            )
        lines.append('')

    # Unmatched Go endpoints
    if unmatched_go:
        lines.append('## Unmatched Go Endpoints')
        lines.append('')
        lines.append('These backend routes have no matching frontend API call.')
        lines.append('They may be unused by the current frontend, or the')
        lines.append('frontend may call them with a different URL/method.')
        lines.append('')
        lines.append('| Method | Path | Handler | File |')
        lines.append('|--------|------|---------|------|')
        for r in sorted(unmatched_go, key=lambda x: (x.path, x.method)):
            lines.append(
                f'| `{r.method}` | `{r.path}` | `{r.handler_func}` | `{r.file}:{r.line}` |'
            )
        lines.append('')

    # Recommendations
    lines.append('## Recommendations')
    lines.append('')
    if missing:
        lines.append(
            f'- 🔴 **{missing} missing-in-Go field(s)** — the frontend reads'
            f' data the backend doesn\'t send. Either add the field to the'
            f' Go response struct, or remove the field from the TS type if'
            f' it\'s no longer needed. Start with the endpoints flagged'
            f' `missing in Go` above.'
        )
    if extra:
        lines.append(
            f'- 🟡 **{extra} extra-in-Go field(s)** — the backend sends data'
            f' the frontend ignores. Consider trimming the Go response'
            f' struct to reduce payload size and avoid leaking internal'
            f' fields. Note that some extra fields (e.g. audit metadata)'
            f' may be intentional.'
        )
    if mismatches:
        lines.append(
            f'- 🟠 **{mismatches} type mismatch(es)** — pay special attention'
            f' to `int64` vs `string` mismatches on ID fields: JavaScript'
            f' cannot represent integers > 2^53 precisely, so any ObjectID'
            f' or 64-bit ID must be serialised as a string on the Go side'
            f' (which `primitive.ObjectID.Hex()` does correctly).'
        )
    if unknown:
        lines.append(
            f'- ⚪ **{unknown} endpoint(s) with unparseable Go response** —'
            f' the handler returns a value via a function call or complex'
            f' expression the auditor can\'t statically resolve. Review'
            f' these manually.'
        )
    if no_handler:
        lines.append(
            f'- ⚫ **{no_handler} endpoint(s) with no matching Go route** —'
            f' the frontend calls an endpoint that doesn\'t exist (or is'
            f' registered with a different URL/method).'
        )
    lines.append('')
    lines.append('Run this auditor as part of the CI pipeline so shape')
    lines.append('drift is caught before it reaches production.')
    lines.append('')
    return '\n'.join(lines)


# ---------------------------------------------------------------------------
# Main analysis pipeline
# ---------------------------------------------------------------------------

def analyze(repo: Path, include_tests: bool = False) -> Tuple[
    List[Comparison],
    List[TSEndpoint],
    List[GoRoute],
    List[GoStruct],
    List[TSType],
]:
    """Run the full analysis pipeline and return the comparison data."""
    # --- Go side --------------------------------------------------------
    go_files = find_go_files(repo, include_tests=include_tests)
    print(f'  Scanning {len(go_files)} .go files', file=sys.stderr)

    # Build the primitive-alias map (e.g. ``type MemberRole string`` ->
    # treat ``MemberRole`` as ``string`` for shape comparison).
    _scan_primitive_aliases(repo)
    if GO_PRIMITIVE_ALIASES:
        print(
            f'  Found {len(GO_PRIMITIVE_ALIASES)} Go primitive aliases '
            f'(e.g. MemberRole -> string)',
            file=sys.stderr,
        )

    # Run the Go struct flattener (go/types-based, sees embedded struct
    # fields). Falls back gracefully to the regex-based struct map if
    # the Go toolchain is unavailable.
    flattened_struct_fields = load_go_structs(repo)

    go_structs: List[GoStruct] = []
    handlers: List[GoHandler] = []
    routes: List[GoRoute] = []
    file_raw_cache: Dict[str, str] = {}  # rel_path -> raw source
    for f in go_files:
        try:
            raw = f.read_text(encoding='utf-8', errors='replace')
        except Exception as exc:
            print(f'  ! could not read {f}: {exc}', file=sys.stderr)
            continue
        masked = mask_go_source(raw)
        rel = str(f.relative_to(repo))
        pkg_m = RE_PACKAGE.search(raw)
        pkg = pkg_m.group(1) if pkg_m else ''
        go_structs.extend(parse_go_structs(masked, rel, pkg, raw_content=raw))
        handlers.extend(parse_go_handlers(masked, rel, raw_content=raw))
        file_raw_cache[rel] = raw
        # Routes are usually only in main.go and the test helpers.
        # Use the RAW (unmasked) source so path strings are preserved.
        if rel.endswith('main.go') or rel.endswith('testhelpers_test.go'):
            routes.extend(parse_go_routes(raw, rel))

    # Deduplicate structs by name (keep the first definition).
    structs_by_name: Dict[str, GoStruct] = {}
    for s in go_structs:
        structs_by_name.setdefault(s.name, s)

    # Augment the regex-based struct map with the flattener's output so
    # embedded struct fields are visible when resolving struct_literal
    # response shapes. We merge the flattener's fields into the
    # existing GoStruct entries (creating a synthetic GoField list when
    # the regex-based parser missed the struct entirely).
    _merge_flattened_into_structs(structs_by_name, flattened_struct_fields)

    handlers_by_name: Dict[str, GoHandler] = {h.name: h for h in handlers}

    # Deduplicate routes by (method, path) — prefer main.go over test files.
    routes_by_key: Dict[str, GoRoute] = {}
    for r in routes:
        key = f'{r.method} {normalise_path_for_matching(r.path)}'
        if key not in routes_by_key:
            routes_by_key[key] = r
        else:
            # Prefer main.go (production) over test helpers.
            existing = routes_by_key[key]
            if 'main.go' in r.file and 'main.go' not in existing.file:
                routes_by_key[key] = r
    routes = list(routes_by_key.values())

    print(
        f'  Found {len(go_structs)} Go structs, {len(handlers)} handlers, '
        f'{len(routes)} routes',
        file=sys.stderr,
    )

    # Build Go endpoint -> response shape map.
    go_shapes = build_go_endpoint_shapes(routes, handlers_by_name, structs_by_name)

    # --- TS side --------------------------------------------------------
    ts_files = find_ts_files(repo)
    print(f'  Scanning {len(ts_files)} .ts files', file=sys.stderr)
    ts_types: List[TSType] = []
    ts_endpoints: List[TSEndpoint] = []
    for f in ts_files:
        try:
            raw = f.read_text(encoding='utf-8', errors='replace')
        except Exception as exc:
            print(f'  ! could not read {f}: {exc}', file=sys.stderr)
            continue
        masked = mask_ts_source(raw)
        rel = str(f.relative_to(repo))
        ts_types.extend(parse_ts_types(masked, rel))
        # Only parse client.ts for endpoints (other .ts files may contain
        # api.* calls in tests or stories that we don't want).
        if rel.endswith('api/client.ts') or rel.endswith('api\\client.ts') or \
                rel == 'src/api/client.ts':
            ts_endpoints.extend(parse_ts_client(masked, rel))

    ts_types_by_name: Dict[str, TSType] = {t.name: t for t in ts_types}

    # Build the TS primitive-alias map (e.g. ``ConfigVarType`` ->
    # ``string`` when defined as ``'string' | 'numeric' | ...``).
    _scan_ts_primitive_aliases(ts_types)
    if TS_PRIMITIVE_ALIASES:
        print(
            f'  Found {len(TS_PRIMITIVE_ALIASES)} TS primitive aliases '
            f'(e.g. ConfigVarType -> string)',
            file=sys.stderr,
        )

    print(
        f'  Found {len(ts_types)} TS types, {len(ts_endpoints)} TS endpoints',
        file=sys.stderr,
    )

    # --- Match + compare ------------------------------------------------
    comparisons: List[Comparison] = []
    matched_go_keys: Set[str] = set()
    unmatched_ts: List[TSEndpoint] = []
    for ep in ts_endpoints:
        key = f'{ep.method} {normalise_path_for_matching(ep.path)}'
        go_shape_list = go_shapes.get(key)
        if go_shape_list is None:
            unmatched_ts.append(ep)
            continue
        matched_go_keys.add(key)
        # Find the corresponding GoRoute to get the handler name.
        go_route = routes_by_key.get(key)
        go_handler: Optional[GoHandler] = None
        if go_route:
            go_handler = handlers_by_name.get(go_route.handler_func)
        # Build the set of "available" field names from the Go code:
        # fields of structs referenced in the handler body, fields of
        # local wrapper structs in the same file, and fields of map
        # responses elsewhere in the handler. A TS-required field in
        # this set is NOT flagged as "missing in Go".
        available = _build_available_field_names(
            go_handler, go_shape_list, structs_by_name,
            flattened_struct_fields, file_raw_cache,
        )
        comp = compare_endpoint(
            method=ep.method,
            path=ep.path,
            ts_ep=ep,
            go_shapes=go_shape_list,
            go_handler=go_handler,
            structs_by_name=structs_by_name,
            ts_types_by_name=ts_types_by_name,
            available_field_names=available,
        )
        comparisons.append(comp)

    unmatched_go: List[GoRoute] = []
    for key, r in routes_by_key.items():
        if key not in matched_go_keys:
            unmatched_go.append(r)

    return comparisons, unmatched_ts, unmatched_go, go_structs, ts_types


def _merge_flattened_into_structs(
    structs_by_name: Dict[str, GoStruct],
    flattened: Dict[str, Set[str]],
) -> None:
    """Merge the Go struct flattener's field sets into the regex-parsed
    ``structs_by_name`` map.

    For each struct that the flattener found, ensure its ``fields``
    list includes every JSON field name the flattener reported (the
    flattener resolves embedded structs, so this adds fields the
    regex-based parser missed). Structs that the regex parser didn't
    find at all are added as synthetic entries.
    """
    for name, field_names in flattened.items():
        existing = structs_by_name.get(name)
        if existing is None:
            # Synthesize a minimal GoStruct so resolve_go_shape_fields
            # can find it.
            structs_by_name[name] = GoStruct(
                name=name, file='<flattener>', line=0, package='',
                fields=[
                    GoField(name=fn, json_name=fn, go_type='interface{}')
                    for fn in sorted(field_names)
                ],
            )
            continue
        existing_json = {f.json_name for f in existing.fields if f.json_name}
        for fn in field_names:
            if fn in existing_json:
                continue
            existing.fields.append(GoField(
                name=fn, json_name=fn, go_type='interface{}',
            ))
            existing_json.add(fn)


def _build_available_field_names(
    go_handler: Optional[GoHandler],
    go_shapes: List[GoResponseShape],
    structs_by_name: Dict[str, GoStruct],
    flattened_struct_fields: Dict[str, Set[str]],
    file_raw_cache: Dict[str, str],
) -> Set[str]:
    """Build the set of Go field names that are "available" in the
    handler but may not be in the primary response shape.

    Sources:
      1. Fields of the base struct (when the response is a struct_literal)
         — already covered by ``resolve_go_shape_fields`` (and augmented
         with the flattener's output in ``_merge_flattened_into_structs``).
      2. Fields of map responses elsewhere in the handler (e.g. the
         handler returns a struct_literal in one branch and a map_literal
         in another — the union of their fields is "available").
      3. Fields of structs referenced as variable types in the handler
         body (e.g. ``var tenant models.Tenant`` makes Tenant's fields
         available — handles the case where the handler has access to a
         struct field that the response map doesn't explicitly include).
      4. Fields of local wrapper structs defined anywhere in the same
         file (e.g. ``mediaItem`` defined in ``ListMedia`` is the
         conceptual response shape for ``UploadMedia`` in the same file).
    """
    available: Set[str] = set()
    if go_handler is None:
        return available

    # (1) Fields of all response shapes (struct_literal and map_literal).
    for shape in go_shapes:
        for f in resolve_go_shape_fields(shape, structs_by_name):
            if f.name:
                available.add(f.name)

    # (2)+(3) Fields of structs referenced as variable types in the
    # handler body. We re-scan the handler body for variable
    # declarations and resolve their types via the existing
    # ``_collect_var_types`` helper.
    if go_handler.body:
        var_types = _collect_var_types(go_handler.body)
        for type_str in var_types.values():
            base = type_str
            # Strip [] (slice), * (pointer), package prefix.
            while base.startswith('[]'):
                base = base[2:]
            if base.startswith('*'):
                base = base[1:]
            base = _strip_package(base)
            if not base or not base[0].isupper():
                continue
            # Look up the struct's flattened field set (preferred —
            # includes embedded fields) or the regex-based struct.
            flat = flattened_struct_fields.get(base)
            if flat:
                available.update(flat)
            else:
                s = structs_by_name.get(base)
                if s:
                    for f in s.fields:
                        if f.json_name and f.json_name != '-':
                            available.add(f.json_name)

    # (4) Local wrapper structs defined anywhere in the same file.
    raw = file_raw_cache.get(go_handler.file)
    if raw:
        for _name, fields in find_local_wrapper_structs(raw, go_handler.name):
            available.update(fields)
        # Also scan the handler body for any additional map responses
        # (the existing _parse_handler_responses may have missed some
        # — e.g. helper maps returned from sub-functions).
        map_fields = find_map_response_fields(raw, go_handler.name)
        available.update(map_fields)

    return available


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser(
        prog='graphify api shapes',
        description='Backend ↔ frontend API response shape auditor.',
    )
    ap.add_argument('path', nargs='?', default='.',
                    help='Path to the repository root.')
    ap.add_argument('--out', '-o',
                    help='Output markdown file (default: stdout).')
    ap.add_argument('--json', action='store_true',
                    help='Emit JSON instead of markdown to stdout.')
    ap.add_argument('--include-tests', action='store_true',
                    help='Include *_test.go files in the Go scan.')
    args = ap.parse_args()

    repo = Path(args.path).resolve()
    print(f'graphify api shapes — scanning {repo}', file=sys.stderr)
    if not repo.exists():
        print(f'error: path does not exist: {repo}', file=sys.stderr)
        sys.exit(1)

    comparisons, unmatched_ts, unmatched_go, go_structs, ts_types = analyze(
        repo, include_tests=args.include_tests
    )

    ok = sum(1 for c in comparisons if c.status == 'ok')
    missing = sum(len(c.missing_in_go) for c in comparisons)
    extra = sum(len(c.extra_in_go) for c in comparisons)
    mismatches = sum(len(c.type_mismatches) for c in comparisons)
    print(
        f'  {len(comparisons)} matched endpoints — {ok} ok, '
        f'{missing} missing-in-Go fields, {extra} extra-in-Go fields, '
        f'{mismatches} type mismatches',
        file=sys.stderr,
    )

    if args.json:
        output = emit_json(
            comparisons, unmatched_ts, unmatched_go,
            go_structs, ts_types, repo,
        )
    else:
        output = emit_markdown(
            comparisons, unmatched_ts, unmatched_go,
            go_structs, ts_types, repo,
        )

    if args.out:
        Path(args.out).write_text(output, encoding='utf-8')
        print(f'Report written to {args.out}', file=sys.stderr)
    else:
        workspace_root = Path(os.environ.get(
            'GRAPHIFY_ROOT', '/home/z/my-project'
        ))
        public_dir = workspace_root / 'public'
        if public_dir.exists():
            (public_dir / 'api-shapes.json').write_text(
                emit_json(
                    comparisons, unmatched_ts, unmatched_go,
                    go_structs, ts_types, repo,
                ),
                encoding='utf-8',
            )
            (public_dir / 'API_SHAPES.md').write_text(
                emit_markdown(
                    comparisons, unmatched_ts, unmatched_go,
                    go_structs, ts_types, repo,
                ),
                encoding='utf-8',
            )
            print(
                '  Wrote public/api-shapes.json and public/API_SHAPES.md',
                file=sys.stderr,
            )
        print(output)


if __name__ == '__main__':
    main()
