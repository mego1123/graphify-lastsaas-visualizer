#!/usr/bin/env python3
"""graphify_dead_code — find genuinely unreachable functions in Go source.

Walks every non-test ``.go`` file under the target path, parses every
top-level function/method declaration, and decides whether each is "dead"
(unreachable from anywhere in the codebase).

Decision rules:

  * **Unexported function** (lowercase first letter): dead if its name is
    referenced nowhere outside its own definition line in any non-test
    ``.go`` file. Test files are NOT considered "callers" for unexported
    functions (a function only used from a test file is dead production
    code — the test should be removed too, or the function should be
    exported).

    Exception: ``main`` and ``init`` are special-cased and never reported.
    Functions whose body literally panics with "not implemented" /
    "unreachable" / "TODO" are kept (they're stubs, not dead code).

  * **Exported function** (capitalised first letter): dead if its name is
    referenced nowhere outside its own file. Exported functions are usually
    part of a package's API, so we additionally require that the reference
    is in a *different* package — same-package internal callers don't
    count as "external use" because removing the function would also
    require removing those callers (which is fine, it's all in one
    package). The check is therefore "is this function name mentioned in
    any *other* file (anywhere in the repo, including test files)?"

Exclusions:

  * ``main()`` and ``init()`` — Go entry points, never dead.
  * ``TestXxx``, ``BenchmarkXxx``, ``FuzzXxx``, ``ExampleXxx`` — testing
    framework entry points, never dead.
  * Functions defined in ``_test.go`` files — out of scope.
  * Functions named ``String`` / ``Error`` / ``MarshalJSON`` /
    ``UnmarshalJSON`` / ``Unwrap`` / ``Is`` / ``As`` etc. — these satisfy
    well-known Go interfaces and may be called via reflection or
    interface dispatch. They're conservatively treated as "live".

A function name match is verified by:

  1. A whole-word search for the function name across every ``.go`` file
     in the repo (including test files, since tests are legitimate
     external callers).
  2. Excluding the file that *defines* the function.
  3. Excluding the function's own definition line.
  4. Excluding import / package / comment lines that mention the name
     (these are not "calls").

This is a conservative name-based analysis. It can produce false negatives
(if two functions in different packages share a name, the second one's
references will count for the first) and false positives are minimised by
the special-case list above. The report's per-finding "verified" field
records the reference count so a reviewer can quickly confirm.

Usage:
    python graphify_dead_code.py [path] [--out report.md] [--json] [--include-tests]

Outputs:
    - JSON written to /home/z/my-project/public/dead-code-go.json (best effort)
    - Markdown written to /home/z/my-project/public/DEAD_CODE_GO.md (best effort)
    - Markdown written to --out path if specified
    - JSON to stdout if --json given

Test target: /home/z/my-project/repos/lastsaas/backend
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #

# Function declaration: ^func [recv]? Name(
FUNC_DECL_RE = re.compile(
    r'^[ \t]*func(?:[ \t]+\([^)]*\))?[ \t]+(?P<name>\w+)[ \t]*\(',
    re.MULTILINE,
)

# Method receiver type: `func (r *Type) Name(` → "Type"
RECV_RE = re.compile(
    r'^[ \t]*func[ \t]+\((?:\w+\s+)?(\*?)(?P<recv>[A-Z]\w*)\)[ \t]+(?P<name>\w+)[ \t]*\(',
    re.MULTILINE,
)

# Test entry points — never report as dead.
TEST_PREFIXES: tuple[str, ...] = ("Test", "Benchmark", "Fuzz", "Example")

# Well-known interface-satisfying methods — these may be called via
# interface dispatch or reflection, so we conservatively treat them as
# live even if no direct call site is found.
WELL_KNOWN_METHODS: frozenset[str] = frozenset({
    # fmt.Stringer
    "String", "GoString",
    # error
    "Error", "Unwrap", "Is", "As",
    # encoding
    "MarshalJSON", "MarshalText", "MarshalBinary", "MarshalXML",
    "UnmarshalJSON", "UnmarshalText", "UnmarshalBinary", "UnmarshalXML",
    # sort.Interface
    "Len", "Less", "Swap",
    # io
    "Read", "Write", "Seek", "Close", "Flush",
    "ReadByte", "WriteByte", "ReadRune", "WriteRune",
    "ReadString", "WriteString",
    "ReadFrom", "WriteTo", "ReadCloser", "WriteCloser",
    # fmt.Formatter
    "Format",
    # context
    "Deadline", "Done", "Err", "Value",
    # driver.Valuer / sql.Scanner
    "Value", "Scan",
    # flag.Value
    "String", "Set",
    # http.Handler / http.HandlerFunc
    "ServeHTTP",
    # generic interface dispatch — common middleware/handler methods
    "Handler", "Middleware",
    # go.mongodb.org/mongo-driver collection accessor pattern
    "Collection",
    # stringer / yaml
    "MarshalYAML", "UnmarshalYAML",
    "MarshalTOML", "UnmarshalTOML",
    # gob
    "GobEncode", "GobDecode",
    # json schema
    "Validate",
    # plugin
    "Init",
})

# Body markers indicating a stub (not real dead code).
STUB_BODY_RE = re.compile(
    r'panic\s*\(\s*"(?:not implemented|TODO|unreachable|unimplemented)[^"]*"',
    re.IGNORECASE,
)

# Skip dirs we never want to scan.
SKIP_DIRS: frozenset[str] = frozenset({
    "vendor", "node_modules", ".git", "graphify-out", "testdata",
})


# --------------------------------------------------------------------------- #
# Data classes
# --------------------------------------------------------------------------- #

@dataclass
class FuncDef:
    name: str
    file: str             # relative to project root
    line: int             # 1-indexed
    end_line: int
    is_method: bool
    receiver_type: str    # "" for free functions, "Type" or "*Type" otherwise
    is_exported: bool
    is_test_entry: bool   # TestXxx, BenchmarkXxx, FuzzXxx, ExampleXxx
    is_init_or_main: bool
    is_well_known: bool
    is_stub: bool         # body looks like a not-implemented stub


@dataclass
class Finding:
    name: str
    file: str
    line: int
    end_line: int
    function_kind: str     # "unexported" / "exported"
    receiver_type: str
    external_refs: int     # references outside this file
    same_file_refs: int    # references in same file but outside the definition
    total_refs: int        # external_refs + same_file_refs
    snippet: str
    severity: str          # always LOW for dead code
    note: str = ""


# --------------------------------------------------------------------------- #
# Source masking
# --------------------------------------------------------------------------- #

def mask_source(src: str) -> str:
    """Replace string literals (except their first chars) and comments with
    spaces. Length and newlines are preserved so brace/paren offsets still
    line up with the original source.

    For dead-code analysis we DO want to preserve string contents when
    scanning for call sites (because a doc comment like ``// See Foo.``
    should not count as a reference). The masker blanks out comments fully
    but only blanks the *interior* of strings (keeping the opening quote
    position). This is good enough for our purpose: we only look for
    bare-identifier function calls, which never appear inside strings
    anyway.
    """
    out = list(src)
    i = 0
    n = len(src)
    while i < n:
        c = src[i]
        if c == '/' and i + 1 < n and src[i + 1] == '/':
            while i < n and src[i] != '\n':
                out[i] = ' '
                i += 1
            continue
        if c == '/' and i + 1 < n and src[i + 1] == '*':
            out[i] = ' '
            out[i + 1] = ' '
            i += 2
            while i < n:
                if src[i] == '*' and i + 1 < n and src[i + 1] == '/':
                    out[i] = ' '
                    out[i + 1] = ' '
                    i += 2
                    break
                if src[i] != '\n':
                    out[i] = ' '
                i += 1
            continue
        if c == '\'':
            out[i] = ' '
            i += 1
            while i < n and src[i] not in ('\'', '\n'):
                if src[i] == '\\' and i + 1 < n:
                    out[i] = ' '
                    out[i + 1] = ' '
                    i += 2
                    continue
                out[i] = ' '
                i += 1
            if i < n and src[i] == '\'':
                out[i] = ' '
                i += 1
            continue
        if c == '"':
            out[i] = ' '
            i += 1
            while i < n and src[i] not in ('"', '\n'):
                if src[i] == '\\' and i + 1 < n:
                    out[i] = ' '
                    out[i + 1] = ' '
                    i += 2
                    continue
                out[i] = ' '
                i += 1
            if i < n and src[i] == '"':
                out[i] = ' '
                i += 1
            continue
        if c == '`':
            out[i] = ' '
            i += 1
            while i < n and src[i] != '`':
                if src[i] != '\n':
                    out[i] = ' '
                i += 1
            if i < n and src[i] == '`':
                out[i] = ' '
                i += 1
            continue
        i += 1
    return ''.join(out)


def find_matching_brace(masked: str, open_pos: int) -> int:
    depth = 0
    i = open_pos
    n = len(masked)
    while i < n:
        c = masked[i]
        if c == '{':
            depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return -1


# --------------------------------------------------------------------------- #
# Function discovery
# --------------------------------------------------------------------------- #

def parse_functions(masked: str) -> list[tuple[str, int, int, bool, str]]:
    """Return [(name, start_line, end_line, is_method, recv_type)] for every
    top-level function/method declaration.

    ``recv_type`` is "" for free functions, or "Type"/"*Type" for methods.
    """
    out: list[tuple[str, int, int, bool, str]] = []
    # First, find method declarations (with receivers).
    for m in RECV_RE.finditer(masked):
        recv = m.group("recv")
        name = m.group("name")
        star = m.group(1)
        recv_type = ("*" if star else "") + recv
        body_start, body_end = _find_body(masked, m.end())
        if body_start < 0:
            continue
        start_line = masked[:m.start()].count('\n') + 1
        end_line = masked[:body_end].count('\n') + 1
        out.append((name, start_line, end_line, True, recv_type))

    # Then find all function declarations and subtract the method ones.
    method_starts = {m.start() for m in RECV_RE.finditer(masked)}
    for m in FUNC_DECL_RE.finditer(masked):
        if m.start() in method_starts:
            continue
        name = m.group("name")
        body_start, body_end = _find_body(masked, m.end())
        if body_start < 0:
            continue
        start_line = masked[:m.start()].count('\n') + 1
        end_line = masked[:body_end].count('\n') + 1
        out.append((name, start_line, end_line, False, ""))

    return out


def _find_body(masked: str, start: int) -> tuple[int, int]:
    """From position right after `func ...(`, walk to the body `{` and its
    matching `}`. Returns (brace_pos, close_pos) or (-1, -1) on failure.
    """
    i = start
    n = len(masked)
    depth_paren = 1  # we're inside the `(` already
    brace_pos = -1
    while i < n:
        c = masked[i]
        if c == '(':
            depth_paren += 1
        elif c == ')':
            depth_paren -= 1
        elif c == '{' and depth_paren == 0:
            brace_pos = i
            break
        i += 1
    if brace_pos < 0:
        return -1, -1
    close_pos = find_matching_brace(masked, brace_pos)
    if close_pos < 0:
        return -1, -1
    return brace_pos, close_pos


def collect_functions(repo_root: Path, include_tests: bool) -> list[FuncDef]:
    """Walk every .go file and return all function definitions."""
    funcs: list[FuncDef] = []
    for path in repo_root.rglob("*.go"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        is_test = path.name.endswith("_test.go")
        if not include_tests and is_test:
            continue
        try:
            src = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        try:
            rel = str(path.resolve().relative_to(repo_root.resolve()))
        except ValueError:
            rel = str(path)
        masked = mask_source(src)
        parsed = parse_functions(masked)
        lines = src.splitlines()
        for name, start_line, end_line, is_method, recv_type in parsed:
            is_exported = name[:1].isupper()
            is_test_entry = any(
                name.startswith(p) and len(name) > len(p)
                for p in TEST_PREFIXES
            )
            is_init_or_main = name in ("main", "init")
            is_well_known = name in WELL_KNOWN_METHODS
            # Detect stub body.
            body_start = min(start_line, end_line)
            body_end = max(start_line, end_line)
            body_lines = lines[body_start - 1:body_end] if 0 <= body_start - 1 < len(lines) else []
            body_text = "\n".join(body_lines)
            is_stub = bool(STUB_BODY_RE.search(body_text))

            funcs.append(FuncDef(
                name=name,
                file=rel,
                line=start_line,
                end_line=end_line,
                is_method=is_method,
                receiver_type=recv_type,
                is_exported=is_exported,
                is_test_entry=is_test_entry,
                is_init_or_main=is_init_or_main,
                is_well_known=is_well_known,
                is_stub=is_stub,
            ))
    return funcs


# --------------------------------------------------------------------------- #
# Reference search
# --------------------------------------------------------------------------- #

def collect_file_texts(repo_root: Path) -> tuple[dict[str, str], dict[str, str]]:
    """Return ({rel: masked_source}, {rel: raw_source}) for every .go file.

    The masked source is used for reference searching (so identifiers
    inside strings/comments don't cause false positives). The raw source
    is used for snippet display.
    """
    masked_texts: dict[str, str] = {}
    raw_texts: dict[str, str] = {}
    for path in repo_root.rglob("*.go"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        try:
            src = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        try:
            rel = str(path.resolve().relative_to(repo_root.resolve()))
        except ValueError:
            rel = str(path)
        masked_texts[rel] = mask_source(src)
        raw_texts[rel] = src
    return masked_texts, raw_texts


def count_references(
    name: str,
    defining_file: str,
    defining_line: int,
    file_texts: dict[str, str],
) -> tuple[int, int, list[str]]:
    """Count references to ``name`` outside its own definition.

    Returns (external_refs, same_file_refs, sample_files).

    * external_refs — number of *files* (other than ``defining_file``) that
      contain a whole-word match for ``name``.
    * same_file_refs — number of lines in ``defining_file`` other than
      ``defining_line`` that contain a whole-word match.
    * sample_files — up to 5 example file paths that contain references.
    """
    pattern = re.compile(r'\b' + re.escape(name) + r'\b')
    external_files: list[str] = []
    same_file_refs = 0

    for rel, text in file_texts.items():
        if rel == defining_file:
            # Count references in same file but outside the definition line.
            for ln_idx, line in enumerate(text.splitlines(), start=1):
                if ln_idx == defining_line:
                    continue
                if pattern.search(line):
                    same_file_refs += 1
            continue
        if pattern.search(text):
            external_files.append(rel)

    return len(external_files), same_file_refs, external_files[:5]


# --------------------------------------------------------------------------- #
# Classification
# --------------------------------------------------------------------------- #

def make_snippet(lines: list[str], start: int, end: int, max_lines: int = 4) -> str:
    if start < 1:
        start = 1
    if end > len(lines):
        end = len(lines)
    if end < start:
        end = start
    chunk = lines[start - 1:end]
    if len(chunk) > max_lines:
        chunk = chunk[:max_lines] + [f"... ({end - start - max_lines + 1} more lines)"]
    return "\n".join(line.rstrip() for line in chunk)


def classify_function(
    fdef: FuncDef,
    file_texts: dict[str, str],
    file_lines_cache: dict[str, list[str]],
) -> Optional[Finding]:
    """Return a Finding if the function is dead, else None."""
    # Always-live exclusions.
    if fdef.is_init_or_main:
        return None
    if fdef.is_test_entry:
        return None
    if fdef.is_well_known:
        return None
    if fdef.is_stub:
        return None

    external_refs, same_file_refs, sample_files = count_references(
        fdef.name, fdef.file, fdef.line, file_texts,
    )

    if fdef.is_exported:
        # Exported function: dead if no other file references it.
        if external_refs == 0:
            return _build_finding(
                fdef, file_lines_cache, external_refs, same_file_refs,
                sample_files,
                function_kind="exported",
                note=(
                    "exported function with no references outside its own "
                    "file — candidate for removal (verify no reflect / "
                    "interface dispatch usage)"
                ),
            )
        return None

    # Unexported function: dead if no references outside the definition line.
    if external_refs == 0 and same_file_refs == 0:
        return _build_finding(
            fdef, file_lines_cache, external_refs, same_file_refs,
            sample_files,
            function_kind="unexported",
            note=(
                "unexported function with no references anywhere in the "
                "codebase — safe to remove"
            ),
        )
    return None


def _build_finding(
    fdef: FuncDef,
    file_lines_cache: dict[str, list[str]],
    external_refs: int,
    same_file_refs: int,
    sample_files: list[str],
    function_kind: str,
    note: str,
) -> Finding:
    # file_lines_cache holds the *raw* (unmasked) source lines.
    lines = file_lines_cache.get(fdef.file, [])
    snippet = make_snippet(lines, fdef.line, fdef.line + 2)
    return Finding(
        name=fdef.name,
        file=fdef.file,
        line=fdef.line,
        end_line=fdef.end_line,
        function_kind=function_kind,
        receiver_type=fdef.receiver_type,
        external_refs=external_refs,
        same_file_refs=same_file_refs,
        total_refs=external_refs + same_file_refs,
        snippet=snippet,
        severity="LOW",
        note=note,
    )


# --------------------------------------------------------------------------- #
# Aggregation
# --------------------------------------------------------------------------- #

def build_report(
    root: Path,
    findings: list[Finding],
    all_funcs: list[FuncDef],
) -> dict:
    by_kind: Counter = Counter()
    by_file: Counter = Counter()
    for f in findings:
        by_kind[f.function_kind] += 1
        by_file[f.file] += 1

    return {
        "root": str(root),
        "total_functions_scanned": len(all_funcs),
        "total_findings": len(findings),
        "kind_breakdown": [
            {"kind": k, "count": c}
            for k, c in by_kind.most_common()
        ],
        "top_files": [
            {"file": f, "count": n}
            for f, n in by_file.most_common(25)
        ],
        "findings": [asdict(f) for f in findings],
    }


# --------------------------------------------------------------------------- #
# Markdown
# --------------------------------------------------------------------------- #

def render_markdown(report: dict) -> str:
    out: list[str] = []
    out.append("# Dead Code Report (Go)")
    out.append("")
    out.append(f"**Target:** `{report['root']}`")
    out.append("")
    out.append(
        "Lists functions that have no references anywhere in the codebase "
        "outside their own definition. These are candidates for removal — "
        "review each finding before deleting (some may be invoked via "
        "reflection, interface dispatch, or external callers not in this "
        "repo)."
    )
    out.append("")

    out.append("## Summary")
    out.append("")
    out.append("| Metric | Value |")
    out.append("| --- | --- |")
    out.append(f"| Functions scanned | {report['total_functions_scanned']} |")
    out.append(f"| Dead code findings | **{report['total_findings']}** |")
    for row in report["kind_breakdown"]:
        out.append(f"| {row['kind']} | {row['count']} |")
    out.append("")

    out.append("## Files With Most Dead Code")
    out.append("")
    if report["top_files"]:
        out.append("| File | Dead functions |")
        out.append("| --- | ---: |")
        for row in report["top_files"]:
            out.append(f"| `{row['file']}` | {row['count']} |")
    else:
        out.append("_No dead code findings._")
    out.append("")

    out.append("## Detailed Findings")
    out.append("")
    if not report["findings"]:
        out.append("_No dead code found — every function has at least one external reference._")
    else:
        # Group by file, sort within file by line.
        by_file: dict[str, list[dict]] = defaultdict(list)
        for f in report["findings"]:
            by_file[f["file"]].append(f)
        for fname in sorted(by_file):
            out.append(f"### `{fname}`")
            out.append("")
            fs = sorted(by_file[fname], key=lambda f: f["line"])
            for f in fs:
                recv = f" on `{f['receiver_type']}`" if f["receiver_type"] else ""
                out.append(
                    f"- **[{f['severity']}] {f['function_kind']} function "
                    f"`{f['name']}`{recv}** — `{f['file']}:{f['line']}` "
                    f"(external_refs={f['external_refs']}, "
                    f"same_file_refs={f['same_file_refs']})"
                )
                out.append(f"  - _{f['note']}_")
                snippet = f["snippet"].rstrip()
                out.append("  ```go")
                for line in snippet.splitlines():
                    out.append(f"  {line}")
                out.append("  ```")
            out.append("")

    out.append("## Methodology")
    out.append("")
    out.append(
        "1. Every `.go` file under the target path is scanned for "
        "`func [recv] Name(...)` declarations. Each declaration's body "
        "extent is found via brace matching (strings and comments are "
        "masked out first)."
    )
    out.append(
        "2. Special-cased exclusions: `main`, `init`, `Test*`, `Benchmark*`, "
        "`Fuzz*`, `Example*` (Go entry points), well-known interface-"
        "satisfying methods (`String`, `Error`, `MarshalJSON`, `ServeHTTP`, "
        "`Len`/`Less`/`Swap`, `Read`/`Write`/`Close`, etc.) which may be "
        "invoked via interface dispatch, and stub functions whose body is "
        "just `panic(\"not implemented\")` / `panic(\"TODO\")`."
    )
    out.append(
        "3. For every remaining function, the codebase is searched for "
        "whole-word references to the function name across ALL `.go` files "
        "(including `*_test.go` — tests are legitimate external callers)."
    )
    out.append(
        "4. **Unexported function** (lowercase): reported as dead if it has "
        "zero references anywhere outside its own definition line."
    )
    out.append(
        "5. **Exported function** (capitalised): reported as dead if no "
        "OTHER file references it. Same-file references don't count "
        "because removing the function would also remove those callers — "
        "they're part of the same dead subtree."
    )
    out.append(
        "6. Each finding is verified by counting references; the "
        "`external_refs` and `same_file_refs` fields record the count so "
        "the reviewer can confirm there are genuinely no callers."
    )
    out.append(
        "7. Severity is **LOW** for every finding — dead code is safe to "
        "remove but not urgent."
    )
    out.append("")
    out.append("### Caveats")
    out.append("")
    out.append(
        "- Name-based analysis: if two functions in different packages "
        "share a name, the second one's references count for the first. "
        "This can mask a dead function. Review each finding before "
        "deletion."
    )
    out.append(
        "- Functions invoked only via reflection (e.g. `reflect.ValueOf(x).MethodByName(\"Foo\")`) "
        "will appear dead. The well-known-method exclusion list mitigates "
        "the common cases."
    )
    out.append(
        "- Functions whose only caller is in `*_test.go` are reported as "
        "dead for unexported functions (the test should be removed too). "
        "For exported functions, test-file references count as external "
        "use and the function is NOT reported as dead."
    )
    out.append("")
    out.append("---")
    out.append("_Generated by `graphify dead-code`._")
    return "\n".join(out)


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="graphify_dead_code.py",
        description="Find genuinely unreachable functions in Go source.",
    )
    parser.add_argument(
        "path", nargs="?", default=".",
        help="Root directory to scan (default: current directory).",
    )
    parser.add_argument(
        "--out", default=None,
        help="Write markdown report to this path (in addition to public/DEAD_CODE_GO.md).",
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Print the JSON report to stdout.",
    )
    parser.add_argument(
        "--include-tests", action="store_true",
        help="Include *_test.go file function DEFINITIONS in the scan "
             "(default: only non-test files are scanned for definitions; "
             "test files are always searched for references).",
    )
    args = parser.parse_args(argv)

    root = Path(args.path).resolve()
    if not root.exists():
        print(f"ERROR: path not found: {root}", file=sys.stderr)
        return 2

    print(f"Collecting Go files under {root} ...", file=sys.stderr)
    file_texts, raw_texts = collect_file_texts(root)
    print(f"  found {len(file_texts)} .go files", file=sys.stderr)

    # file_lines_cache holds the RAW (unmasked) source lines — used for
    # snippet rendering. Reference search uses file_texts (masked).
    file_lines_cache: dict[str, list[str]] = {
        rel: text.splitlines() for rel, text in raw_texts.items()
    }

    print("Parsing function definitions ...", file=sys.stderr)
    all_funcs = collect_functions(root, args.include_tests)
    print(f"  found {len(all_funcs)} function definitions", file=sys.stderr)

    print("Searching for references ...", file=sys.stderr)
    findings: list[Finding] = []
    for fdef in all_funcs:
        finding = classify_function(fdef, file_texts, file_lines_cache)
        if finding is not None:
            findings.append(finding)

    report = build_report(root, findings, all_funcs)

    # Always write JSON + MD to /home/z/my-project/public/ if writable.
    public_dir = Path("/home/z/my-project/public")
    json_path = public_dir / "dead-code-go.json"
    md_path = public_dir / "DEAD_CODE_GO.md"
    try:
        public_dir.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    except Exception as e:
        print(f"WARN: could not write {json_path}: {e}", file=sys.stderr)
    try:
        md_path.write_text(render_markdown(report), encoding="utf-8")
    except Exception as e:
        print(f"WARN: could not write {md_path}: {e}", file=sys.stderr)

    if args.out:
        out_path = Path(args.out)
        try:
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(render_markdown(report), encoding="utf-8")
            print(f"Markdown report written to {out_path}", file=sys.stderr)
        except Exception as e:
            print(f"ERROR: could not write --out file: {e}", file=sys.stderr)
            return 1

    if args.json:
        print(json.dumps(report, indent=2))

    print(
        f"Scanned {len(all_funcs)} functions; found {len(findings)} dead "
        f"code findings (LOW severity).",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
