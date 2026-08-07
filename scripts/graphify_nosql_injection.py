#!/usr/bin/env python3
"""graphify_nosql_injection — scan Go source code for NoSQL injection risks.

Walks every ``.go`` file under the target path, identifies MongoDB query
calls (``Find`` / ``FindOne`` / ``InsertOne`` / ``UpdateOne`` / ``DeleteOne``
/ ``Aggregate`` / ``CountDocuments`` and friends), and checks whether user
input flows into the query filter without sanitization.

User input sources tracked:

  * HTTP query string  — ``r.URL.Query().Get("...")``, ``q.Get("...")``
    where ``q := r.URL.Query()``.
  * HTTP form values   — ``r.FormValue("...")``, ``r.PostFormValue("...")``.
  * Path parameters    — ``chi.URLParam(r, "...")``,
    ``mux.Vars(r)["..."]``, ``chi.URLParamFromCtx(ctx, "...")``.
  * JSON request body  — fields of a struct decoded via
    ``json.NewDecoder(r.Body).Decode(&req)`` — any ``req.<Field>`` access
    is treated as user input.

Sanitizers (a value passed through one of these is considered safe):

  * ``primitive.ObjectIDFromHex(...)``
  * ``escapeRegexInput(...)``
  * ``strconv.Atoi`` / ``strconv.ParseInt`` / ``strconv.ParseFloat`` /
    ``strconv.ParseBool``
  * ``time.Parse(...)``
  * ``primitive.Regex{Pattern: ...escapeRegexInput(...)...}``
  * Allowlist validation via ``switch X { case "...": ... }`` where each
    case body assigns a literal (not ``X`` itself) to the filter.

Risk levels:

  * ``CRITICAL`` — ``$where`` with user input (allows JS injection).
  * ``HIGH``     — direct user input in a filter field, or ``$regex`` with
    user input (regex DoS / injection).
  * ``MEDIUM``   — user input inside an ``$or`` / ``$and`` / ``$nor``
    array element.
  * ``LOW``      — user input that was sanitized before reaching the filter
    (recorded for completeness, not a real risk).

Usage:
    python graphify_nosql_injection.py [path] [--out report.md] [--json]

Outputs:
    - JSON written to /home/z/my-project/public/nosql-injection.json (best effort)
    - Markdown written to /home/z/my-project/public/NOSQL_INJECTION.md (best effort)
    - Markdown written to --out path if specified
    - JSON to stdout if --json given

Test target: /home/z/my-project/repos/lastsaas/backend
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional


# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #

OPERATIONS: tuple[str, ...] = (
    "Find",
    "FindOne",
    "FindOneAndDelete",
    "FindOneAndReplace",
    "FindOneAndUpdate",
    "InsertOne",
    "InsertMany",
    "UpdateOne",
    "UpdateMany",
    "UpdateByID",
    "ReplaceOne",
    "DeleteOne",
    "DeleteMany",
    "Aggregate",
    "CountDocuments",
    "EstimatedDocumentCount",
    "BulkWrite",
)

OP_FILTER_POS: dict[str, int] = {
    "Find":               1,
    "FindOne":            1,
    "FindOneAndDelete":   1,
    "FindOneAndReplace":  1,
    "FindOneAndUpdate":   1,
    "InsertOne":          1,
    "InsertMany":         1,
    "UpdateOne":          1,
    "UpdateMany":         1,
    "UpdateByID":         1,
    "ReplaceOne":         1,
    "DeleteOne":          1,
    "DeleteMany":         1,
    "Aggregate":          1,
    "CountDocuments":     1,
    "EstimatedDocumentCount": -1,
    "BulkWrite":          1,
}

OP_CALL_RE = re.compile(
    r"\.(" + "|".join(OPERATIONS) + r")\s*\("
)

FUNC_DECL_RE = re.compile(
    r"^[ \t]*func(?:[ \t]+\([^)]*\))?[ \t]+(?P<name>\w+)[ \t]*\(",
    re.MULTILINE,
)

# User input source patterns. Run on ORIGINAL source (string literals intact).
URL_QUERY_GET_RE = re.compile(
    r"\b(?P<var>\w+)\s*:?=\s*"
    r"(?:strings\.TrimSpace\()?"
    r"(?:(?P<chain>\w+(?:\.\w+)*)\.)?"
    r"(?:URL\.Query\(\)\.Get|q\.Get|query\.Get|values\.Get)"
    r"\(\s*\"(?P<key>[^\"]*)\"\s*\)"
    r"(?:\s*\))?"
)
FORM_VALUE_RE = re.compile(
    r"\b(?P<var>\w+)\s*:?=\s*r\.FormValue\(\s*\"(?P<key>[^\"]*)\"\s*\)"
)
POST_FORM_VALUE_RE = re.compile(
    r"\b(?P<var>\w+)\s*:?=\s*r\.PostFormValue\(\s*\"(?P<key>[^\"]*)\"\s*\)"
)
CHI_URLPARAM_RE = re.compile(
    r"\b(?P<var>\w+)\s*:?=\s*chi\.URLParam"
    r"(?:FromCtx)?\s*\(\s*\w+\s*,\s*\"(?P<key>[^\"]*)\"\s*\)"
)
MUX_VARS_RE = re.compile(
    r"\b(?P<var>\w+)\s*:?=\s*mux\.Vars\(\s*\w+\s*\)\[\"(?P<key>[^\"]*)\"\]"
)

# JSON body decode: ``json.NewDecoder(r.Body).Decode(&req)``.
JSON_DECODE_RE = re.compile(
    r"json\.NewDecoder\(\s*\w+\.Body\s*\)\.Decode\(\s*&(?P<target>\w+)\s*\)"
)
JSON_DECODE_ALIAS_RE = re.compile(
    r"(?P<dec>\w+)\s*:?=\s*json\.NewDecoder\(\s*\w+\.Body\s*\)"
    r"(?:[^;]*?;\s*(?P=dec)\.Decode\(\s*&(?P<target>\w+)\s*\))?"
)

SANITIZER_NAMES = [
    "primitive.ObjectIDFromHex",
    "escapeRegexInput",
    "strconv.Atoi",
    "strconv.ParseInt",
    "strconv.ParseUint",
    "strconv.ParseFloat",
    "strconv.ParseBool",
    "strconv.ParseUint",
    "time.Parse",
    "time.ParseInLocation",
    "url.PathEscape",
    "url.QueryEscape",
    "url.PathUnescape",
    "regexp.MustCompile",
    "regexp.Compile",
    "uuid.Parse",
    "uuid.MustParse",
]
SANI_CALL_RE = re.compile(
    r"\b(" + "|".join(re.escape(n) for n in SANITIZER_NAMES) + r")\s*\("
)

# Struct-validation calls — when a JSON-decoded struct is passed through
# one of these, all of its fields are considered validated. The project
# uses both ``validator.Struct(...)`` (the underlying library) and
# ``validation.Validate(...)`` (a project-specific wrapper that calls
# ``validator.Struct`` internally).
STRUCT_VALIDATOR_CALL_RE = re.compile(
    r"\b(?:validator\.Struct|validation\.Validate|v\.Struct|validate\.Struct)\s*\(\s*&?\s*(?P<arg>\w+)\s*\)"
)

# Per-field custom validator pattern: a conditional ``if !<fn>(<var>) {
# respondWithError ... }`` block that returns early on invalid input.
# The function name typically starts with ``isValid`` / ``valid`` /
# ``validate`` (e.g. ``isValidEmail``, ``validateToken``). We treat the
# variable passed to such a function as sanitized if the call is
# followed by an early-return guard.
PER_FIELD_VALIDATOR_RE = re.compile(
    r"\bif\s+!?(?P<fn>is[A-Z]\w*|valid\w*|validate\w*|check\w*)\s*\(\s*(?P<arg>[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)?)\s*\)\s*\{"
)

# Compiled-regex method-call validator: ``<regexVar>.Match(<arg>)`` or
# ``<regexVar>.MatchString(<arg>)``. Common pattern for validating format
# (e.g. ``validDefName.MatchString(req.Name)``). We look for this pattern
# anywhere in the function (typically inside an ``if`` guard with an
# early return); if found, the argument is considered validated.
REGEX_MATCH_VALIDATOR_RE = re.compile(
    r"\b(?P<regexVar>[A-Za-z_]\w*)\.(?:Match|MatchString)\s*\(\s*(?P<arg>[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)?)\s*\)"
)

# Error-returning validator pattern: ``if err := <validate-fn>(&<var>);
# err != nil { ... return }``. Functions like ``validateBundleRequest``,
# ``validatePlanRequest``, ``validateWebhookRequest`` take a pointer to
# the request struct and return an error. When this pattern appears
# before a query, all fields of the validated struct are considered
# sanitized.
ERROR_VALIDATOR_RE = re.compile(
    r"\bif\s+(?:err\s*:?=\s*|_,\s*err\s*:?=\s*)"
    r"(?P<fn>validate\w*|valid\w*|check\w*|sanitize\w*|normalize\w*)"
    r"\s*\(\s*&\s*(?P<arg>\w+)\s*\)"
)

# bson.M / bson.D / bson.A literal start. Run on MASKED source.
BSON_LITERAL_RE = re.compile(
    r"\b(bson\.M|bson\.D|bson\.A)\s*\{"
)

# Assignment to a filter map: ``filter["key"] = value``.
# Run on ORIGINAL source.
FILTER_ASSIGN_RE = re.compile(
    r"\b(?P<filter>\w+)\[\"(?P<key>[^\"]*)\"\]\s*(?::=|=)\s*(?P<value>.+)$",
    re.MULTILINE,
)

SKIP_DIRS = {"vendor", "node_modules", ".git", "graphify-out", "testdata"}

RISK_CRITICAL = "CRITICAL"
RISK_HIGH = "HIGH"
RISK_MEDIUM = "MEDIUM"
RISK_LOW = "LOW"


# --------------------------------------------------------------------------- #
# Data classes
# --------------------------------------------------------------------------- #

@dataclass
class UserInput:
    var: str
    source: str
    line: int
    sanitized: bool = False
    sanitizer: str = ""
    sanitized_at_line: int = 0   # line where the sanitizer was applied (0 = n/a)


@dataclass
class Finding:
    file: str
    line: int
    end_line: int
    function: str
    operation: str
    query: str
    source: str
    source_var: str
    field: str
    risk: str
    sanitized: bool
    sanitizer: str
    snippet: str
    note: str = ""


@dataclass
class FileStats:
    path: str
    is_test: bool
    lines: int = 0
    queries_scanned: int = 0
    findings: int = 0


@dataclass
class FuncRange:
    name: str
    start_line: int
    end_line: int
    start_offset: int
    end_offset: int


# --------------------------------------------------------------------------- #
# Source masking
# --------------------------------------------------------------------------- #

def mask_source(src: str) -> str:
    """Replace string literals and comments with spaces.

    Length and newlines are preserved so character offsets still line up
    with the original source — only the *content* of strings/comments is
    blanked out. This makes brace/paren matching safe.
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


def mask_comments_only(src: str) -> str:
    """Like ``mask_source`` but only blanks comments, keeping string literals.

    Used for regex matching of user-input patterns: we don't want to match
    patterns that appear inside comments, but we DO need string literals
    (e.g. the ``"key"`` in ``mux.Vars(r)["key"]``) to be intact.
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
        if c == '"':
            # Skip the string but keep its contents.
            i += 1
            while i < n and src[i] not in ('"', '\n'):
                if src[i] == '\\' and i + 1 < n:
                    i += 2
                    continue
                i += 1
            if i < n and src[i] == '"':
                i += 1
            continue
        if c == '`':
            i += 1
            while i < n and src[i] != '`':
                i += 1
            if i < n and src[i] == '`':
                i += 1
            continue
        if c == '\'':
            i += 1
            while i < n and src[i] not in ('\'', '\n'):
                if src[i] == '\\' and i + 1 < n:
                    i += 2
                    continue
                i += 1
            if i < n and src[i] == '\'':
                i += 1
            continue
        i += 1
    return ''.join(out)


# --------------------------------------------------------------------------- #
# Brace matching
# --------------------------------------------------------------------------- #

def find_matching(masked: str, open_pos: int, open_ch: str, close_ch: str) -> int:
    depth = 0
    i = open_pos
    n = len(masked)
    while i < n:
        c = masked[i]
        if c == open_ch:
            depth += 1
        elif c == close_ch:
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return -1


def find_matching_paren(masked: str, open_pos: int) -> int:
    return find_matching(masked, open_pos, '(', ')')


def find_matching_brace(masked: str, open_pos: int) -> int:
    return find_matching(masked, open_pos, '{', '}')


def find_matching_bracket(masked: str, open_pos: int) -> int:
    return find_matching(masked, open_pos, '[', ']')


def parse_functions(masked: str) -> list[FuncRange]:
    funcs: list[FuncRange] = []
    for m in FUNC_DECL_RE.finditer(masked):
        name = m.group('name')
        i = m.end()
        n = len(masked)
        depth_paren = 1
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
            continue
        close_pos = find_matching_brace(masked, brace_pos)
        if close_pos < 0:
            continue
        start_line = masked[:m.start()].count('\n') + 1
        end_line = masked[:close_pos].count('\n') + 1
        funcs.append(FuncRange(
            name=name,
            start_line=start_line,
            end_line=end_line,
            start_offset=m.start(),
            end_offset=close_pos,
        ))
    return funcs


def make_snippet(lines: list[str], start: int, end: int, max_lines: int = 8) -> str:
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


def _line_of(text: str, offset: int) -> int:
    return text[:offset].count('\n') + 1


def _read_balanced(text: str, open_pos: int, open_ch: str, close_ch: str) -> str:
    close_pos = find_matching(text, open_pos, open_ch, close_ch)
    if close_pos < 0:
        return text[open_pos + 1:]
    return text[open_pos + 1:close_pos]


# --------------------------------------------------------------------------- #
# User input tracking
# --------------------------------------------------------------------------- #

def collect_user_inputs(
    func_src: str,
    func_masked: str,
    func_start_line: int,
) -> dict[str, UserInput]:
    """Build a map of variables holding user input.

    Patterns are matched against ``func_src`` (original source) so that
    string literals like the ``"key"`` in ``mux.Vars(r)["key"]`` are
    preserved. Comments are pre-stripped via ``mask_comments_only`` to
    avoid matching patterns inside comments.
    """
    # Use comment-masked source for regex matching.
    func_no_comments = mask_comments_only(func_src)

    inputs: dict[str, UserInput] = {}
    json_structs: set[str] = set()

    def add(var: str, source: str, line: int) -> None:
        if not var:
            return
        if var in inputs and inputs[var].sanitized:
            return
        if var not in inputs:
            inputs[var] = UserInput(
                var=var, source=source, line=line, sanitized=False,
            )

    # 1. JSON body decodes -> struct names.
    for m in JSON_DECODE_RE.finditer(func_no_comments):
        json_structs.add(m.group('target'))
    # Also catch ``dec.Decode(&req)`` patterns where ``dec`` was created
    # from r.Body.
    for m in re.finditer(r"(\w+)\.Decode\(\s*&(\w+)\s*\)", func_no_comments):
        target = m.group(2)
        window_start = max(0, m.start() - 1000)
        window = func_no_comments[window_start:m.start()]
        if re.search(r"json\.NewDecoder\(\s*\w+\.Body\s*\)", window):
            json_structs.add(target)

    # 2. Direct user-input assignments.
    for m in URL_QUERY_GET_RE.finditer(func_no_comments):
        add(m.group('var'), f"query:{m.group('key')}",
            _line_of(func_no_comments, m.start()) + func_start_line - 1)
    for m in FORM_VALUE_RE.finditer(func_no_comments):
        add(m.group('var'), f"form:{m.group('key')}",
            _line_of(func_no_comments, m.start()) + func_start_line - 1)
    for m in POST_FORM_VALUE_RE.finditer(func_no_comments):
        add(m.group('var'), f"postform:{m.group('key')}",
            _line_of(func_no_comments, m.start()) + func_start_line - 1)
    for m in CHI_URLPARAM_RE.finditer(func_no_comments):
        add(m.group('var'), f"path:{m.group('key')}",
            _line_of(func_no_comments, m.start()) + func_start_line - 1)
    for m in MUX_VARS_RE.finditer(func_no_comments):
        add(m.group('var'), f"path:{m.group('key')}",
            _line_of(func_no_comments, m.start()) + func_start_line - 1)

    # 3. JSON body struct fields: ``req.Email``, ``req.Password``, etc.
    for struct_name in json_structs:
        for fm in re.finditer(
            rf"\b{re.escape(struct_name)}\.(?P<field>[A-Za-z_]\w*)",
            func_no_comments,
        ):
            full = f"{struct_name}.{fm.group('field')}"
            line = _line_of(func_no_comments, fm.start()) + func_start_line - 1
            if full not in inputs:
                inputs[full] = UserInput(
                    var=full,
                    source=f"json-body:{full}",
                    line=line,
                    sanitized=False,
                )

    # 4. Sanitized derivatives: variables assigned from a sanitizer call.
    for m in SANI_CALL_RE.finditer(func_no_comments):
        sani_name = m.group(1)
        window_start = max(0, m.start() - 400)
        window = func_no_comments[window_start:m.start()].replace('\n', ' ')
        out_vars: list[str] = []
        mr = re.search(r"(\w+)\s*,\s*\w+\s*:?=\s*$", window)
        if mr:
            out_vars.append(mr.group(1))
        else:
            sr = re.search(r"(\w+)\s*:?=\s*$", window)
            if sr:
                out_vars.append(sr.group(1))
        if not out_vars:
            vd = re.search(
                r"\bvar\s+(\w+)\s+\w+(?:\.\w+)?\s*$", window
            )
            if vd:
                out_vars.append(vd.group(1))
        for out in out_vars:
            if not out or out == '_':
                continue
            line = _line_of(func_no_comments, m.start()) + func_start_line - 1
            arg_text = _read_balanced(func_no_comments, m.end() - 1, '(', ')')
            inputs[out] = UserInput(
                var=out,
                source=f"sanitized:{sani_name}({arg_text.strip()})",
                line=line,
                sanitized=True,
                sanitizer=sani_name,
            )

    # 5. primitive.Regex{Pattern: ...escapeRegexInput(x)...} — the
    #    resulting variable's ``.Pattern`` field is sanitized.
    for m in re.finditer(r"\bprimitive\.Regex\s*\{", func_no_comments):
        brace_pos = m.end() - 1
        close_pos = find_matching_brace(func_masked, brace_pos)
        if close_pos < 0:
            continue
        body_masked = func_masked[brace_pos + 1:close_pos]
        if "escapeRegexInput" not in body_masked:
            continue
        window_start = max(0, m.start() - 200)
        window = func_no_comments[window_start:m.start()].replace('\n', ' ')
        out_match = re.search(r"(\w+)\s*:?=\s*$", window)
        if not out_match:
            continue
        out = out_match.group(1)
        if not out or out == '_':
            continue
        line = _line_of(func_no_comments, m.start()) + func_start_line - 1
        inputs[out] = UserInput(
            var=out,
            source="sanitized:primitive.Regex{...escapeRegexInput(...)...}",
            line=line,
            sanitized=True,
            sanitizer="primitive.Regex+escapeRegexInput",
        )
        inputs[f"{out}.Pattern"] = UserInput(
            var=f"{out}.Pattern",
            source="sanitized:primitive.Regex{...escapeRegexInput(...)...}",
            line=line,
            sanitized=True,
            sanitizer="primitive.Regex+escapeRegexInput",
        )

    # 6. Aliasing: ``var2 := var1`` on a single line — inherit status.
    alias_line_re = re.compile(r"^\s*(?P<dst>\w+)\s*:?=\s*(?P<src>\w+)\s*(?://.*)?$")
    for raw_line in func_no_comments.split('\n'):
        m = alias_line_re.match(raw_line)
        if not m:
            continue
        dst = m.group('dst')
        src = m.group('src')
        if dst == '_' or dst == src:
            continue
        if src in inputs:
            src_in = inputs[src]
            if dst not in inputs:
                inputs[dst] = UserInput(
                    var=dst,
                    source=src_in.source,
                    line=func_start_line,
                    sanitized=src_in.sanitized,
                    sanitizer=src_in.sanitizer,
                    sanitized_at_line=src_in.sanitized_at_line,
                )

    # 7. Per-field custom validators: ``if !isValidEmail(req.Email) {
    # respondWithError ... }`` — the variable passed to such a function
    # is validated and safe to use in subsequent queries. Functions whose
    # names start with ``isValid`` / ``valid`` / ``validate`` / ``check``
    # and which appear in a negated ``if`` guard are treated as
    # sanitizers.
    for m in PER_FIELD_VALIDATOR_RE.finditer(func_no_comments):
        arg = m.group('arg')
        line = _line_of(func_no_comments, m.start()) + func_start_line - 1
        # The arg may be ``req.Email`` (struct field) or a bare variable.
        if arg in inputs:
            ui = inputs[arg]
            # Only mark sanitized if not already sanitized earlier.
            if not ui.sanitized or ui.sanitized_at_line == 0 or ui.sanitized_at_line > line:
                inputs[arg] = UserInput(
                    var=ui.var,
                    source=ui.source,
                    line=ui.line,
                    sanitized=True,
                    sanitizer=f"custom-validator:{m.group('fn')}",
                    sanitized_at_line=line,
                )
        elif '.' in arg:
            # Struct field: validate the head var (e.g. ``req.Email``
            # → mark ``req`` as having its ``Email`` field validated).
            head = arg.split('.', 1)[0]
            if head in inputs and inputs[head].source.startswith("json-body:"):
                # Register the dotted form too.
                inputs[arg] = UserInput(
                    var=arg,
                    source=f"json-body:{arg}",
                    line=inputs[head].line,
                    sanitized=True,
                    sanitizer=f"custom-validator:{m.group('fn')}",
                    sanitized_at_line=line,
                )

    # 7b. Compiled-regex validators: ``if !validDefName.MatchString(req.Name) {
    # respondWithError ... }`` — the variable passed to ``MatchString`` /
    # ``Match`` is validated against the regex.
    for m in REGEX_MATCH_VALIDATOR_RE.finditer(func_no_comments):
        arg = m.group('arg')
        line = _line_of(func_no_comments, m.start()) + func_start_line - 1
        sani = f"regex-validator:{m.group('regexVar')}.MatchString"
        if arg in inputs:
            ui = inputs[arg]
            if not ui.sanitized or ui.sanitized_at_line == 0 or ui.sanitized_at_line > line:
                inputs[arg] = UserInput(
                    var=ui.var,
                    source=ui.source,
                    line=ui.line,
                    sanitized=True,
                    sanitizer=sani,
                    sanitized_at_line=line,
                )
        elif '.' in arg:
            head = arg.split('.', 1)[0]
            if head in inputs and inputs[head].source.startswith("json-body:"):
                inputs[arg] = UserInput(
                    var=arg,
                    source=f"json-body:{arg}",
                    line=inputs[head].line,
                    sanitized=True,
                    sanitizer=sani,
                    sanitized_at_line=line,
                )

    # 8. Struct-level validators: ``validator.Struct(&req)`` /
    # ``validation.Validate(&req)`` — the entire struct's fields are
    # validated. Mark every ``req.*`` input derived from the validated
    # struct as sanitized.
    for m in STRUCT_VALIDATOR_CALL_RE.finditer(func_no_comments):
        target = m.group('arg')
        line = _line_of(func_no_comments, m.start()) + func_start_line - 1
        # Mark the bare struct name (e.g. ``req``) as sanitized — this
        # catches lazy ``req.X`` lookups via the json-body fallback in
        # ``is_user_input``.
        if target in inputs:
            ui = inputs[target]
            if not ui.sanitized or ui.sanitized_at_line == 0 or ui.sanitized_at_line > line:
                inputs[target] = UserInput(
                    var=ui.var,
                    source=ui.source,
                    line=ui.line,
                    sanitized=True,
                    sanitizer="validator.Struct",
                    sanitized_at_line=line,
                )
        # Also mark every explicit ``target.Field`` input that was
        # registered earlier.
        for var_name, ui in list(inputs.items()):
            if var_name.startswith(f"{target}.") and ui.source.startswith("json-body:"):
                if not ui.sanitized or ui.sanitized_at_line == 0 or ui.sanitized_at_line > line:
                    inputs[var_name] = UserInput(
                        var=ui.var,
                        source=ui.source,
                        line=ui.line,
                        sanitized=True,
                        sanitizer="validator.Struct",
                        sanitized_at_line=line,
                    )

    # 9. Error-returning request validators: ``if err := validateX(&req);
    # err != nil { return }``. Functions like ``validateBundleRequest``,
    # ``validatePlanRequest``, ``validateWebhookRequest`` validate the
    # whole request struct. Mark all the struct's fields as sanitized.
    for m in ERROR_VALIDATOR_RE.finditer(func_no_comments):
        target = m.group('arg')
        line = _line_of(func_no_comments, m.start()) + func_start_line - 1
        sani = f"custom-validator:{m.group('fn')}"
        # Mark the bare struct name.
        if target in inputs:
            ui = inputs[target]
            if not ui.sanitized or ui.sanitized_at_line == 0 or ui.sanitized_at_line > line:
                inputs[target] = UserInput(
                    var=ui.var,
                    source=ui.source,
                    line=ui.line,
                    sanitized=True,
                    sanitizer=sani,
                    sanitized_at_line=line,
                )
        # Mark every explicit ``target.Field`` input.
        for var_name, ui in list(inputs.items()):
            if var_name.startswith(f"{target}.") and ui.source.startswith("json-body:"):
                if not ui.sanitized or ui.sanitized_at_line == 0 or ui.sanitized_at_line > line:
                    inputs[var_name] = UserInput(
                        var=ui.var,
                        source=ui.source,
                        line=ui.line,
                        sanitized=True,
                        sanitizer=sani,
                        sanitized_at_line=line,
                    )

    return inputs


def is_user_input(
    expr_src: str,
    expr_masked: str,
    inputs: dict[str, UserInput],
    query_line: int = 0,
) -> Optional[UserInput]:
    """Check if an expression references a user-input variable.

    ``expr_src`` is the original source of the expression; ``expr_masked``
    is the masked version (same length). If the user-input identifier
    appears INSIDE a sanitizer call's argument list (e.g.
    ``escapeRegexInput(search)``), the returned UserInput is marked as
    sanitized.

    ``query_line`` is the line where the MongoDB query that consumes
    this expression appears. When non-zero, struct/per-field validators
    applied AFTER the query are NOT considered sanitizers (the input was
    unvalidated at the time of the query). When zero (caller didn't pass
    a line), validator-based sanitization is trusted unconditionally.
    """
    expr_src = expr_src.strip() if expr_src else ""
    if not expr_src:
        return None
    # Direct match — but only for very simple expressions (no function calls).
    if expr_src in inputs and '(' not in expr_src:
        ui = inputs[expr_src]
        return _validated_before_query(ui, query_line)
    # Find sanitizer call argument ranges in expr_masked.
    sanitizer_ranges: list[tuple[int, int, str]] = []
    for m in SANI_CALL_RE.finditer(expr_masked):
        open_paren = m.end() - 1
        close_paren = find_matching_paren(expr_masked, open_paren)
        if close_paren < 0:
            continue
        sanitizer_ranges.append((open_paren + 1, close_paren, m.group(1)))
    # Find all identifiers in expr_src.
    for m in re.finditer(r"\b[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)?", expr_src):
        tok = m.group(0)
        if tok in inputs:
            # Check if this identifier is inside a sanitizer argument.
            for s, e, sani in sanitizer_ranges:
                if s <= m.start() < e:
                    ui = inputs[tok]
                    return UserInput(
                        var=ui.var,
                        source=f"sanitized:{sani}(...{tok}...)",
                        line=ui.line,
                        sanitized=True,
                        sanitizer=sani,
                        sanitized_at_line=query_line,
                    )
            return _validated_before_query(inputs[tok], query_line)
        # Lazy struct field case.
        head = tok.split('.')[0]
        if head in inputs and inputs[head].source.startswith("json-body:"):
            ui = inputs[head]
            # If the head was validated via validator.Struct, the field
            # is also validated (after the validator's line).
            validated_ui = _validated_before_query(ui, query_line)
            if validated_ui.sanitized:
                return UserInput(
                    var=tok,
                    source=f"json-body:{tok}",
                    line=ui.line,
                    sanitized=True,
                    sanitizer=validated_ui.sanitizer,
                    sanitized_at_line=validated_ui.sanitized_at_line,
                )
            # If the dotted form was explicitly registered (e.g. via a
            # per-field validator), use that.
            if tok in inputs:
                return _validated_before_query(inputs[tok], query_line)
            return UserInput(
                var=tok,
                source=f"json-body:{tok}",
                line=ui.line,
                sanitized=False,
            )
    return None


def _validated_before_query(ui: UserInput, query_line: int) -> UserInput:
    """Return a copy of ``ui`` whose ``sanitized`` flag reflects whether
    the sanitization happened before the query (when ``query_line`` is
    known). If the sanitizer was applied AFTER the query, return an
    unsanitized copy so the finding is still raised.
    """
    if not ui.sanitized:
        return ui
    if ui.sanitized_at_line == 0 or query_line == 0:
        # No line info — trust the sanitized flag.
        return ui
    if ui.sanitized_at_line < query_line:
        return ui
    # Sanitizer was applied AFTER the query — input was unvalidated at
    # the time of the query.
    return UserInput(
        var=ui.var,
        source=ui.source,
        line=ui.line,
        sanitized=False,
        sanitizer="",
        sanitized_at_line=0,
    )


# --------------------------------------------------------------------------- #
# bson literal parsing
# --------------------------------------------------------------------------- #

@dataclass
class FilterHit:
    field: str
    value_expr: str
    is_operator: bool
    value_start: int  # offset of value within the content
    value_end: int


def parse_bson_pairs(content: str) -> list[FilterHit]:
    """Parse the inside of a ``bson.M{...}`` literal into key/value pairs.

    ``content`` is the text BETWEEN the ``{`` and ``}`` (original source).
    Returns a list of (field, value_expr, value_start_offset, value_end_offset)
    where the offsets are relative to ``content``.
    """
    hits: list[FilterHit] = []
    i = 0
    n = len(content)
    while i < n:
        while i < n and content[i] in ' \t\r\n,':
            i += 1
        if i >= n:
            break
        # Expect a quoted key (or ``Key: "..."`` for bson.D named form).
        if content[i] != '"':
            m = re.match(r"Key:\s*", content[i:])
            if m:
                i += m.end()
                if i >= n or content[i] != '"':
                    while i < n and content[i] not in ',\n':
                        i += 1
                    continue
            else:
                while i < n and content[i] not in ',\n':
                    i += 1
                continue
        # Read the quoted key.
        j = i + 1
        while j < n and content[j] != '"':
            if content[j] == '\\' and j + 1 < n:
                j += 2
                continue
            j += 1
        key = content[i + 1:j]
        i = j + 1
        while i < n and content[i] in ' \t\r\n':
            i += 1
        if i < n and content[i] == ':':
            i += 1
        elif i < n and content[i] == ',':
            i += 1
        else:
            break
        while i < n and content[i] in ' \t\r\n':
            i += 1
        # Read the value.
        value_start = i
        depth_brace = 0
        depth_paren = 0
        depth_bracket = 0
        while i < n:
            c = content[i]
            if c == '{':
                depth_brace += 1
            elif c == '}':
                if depth_brace == 0:
                    break
                depth_brace -= 1
            elif c == '(':
                depth_paren += 1
            elif c == ')':
                if depth_paren == 0:
                    break
                depth_paren -= 1
            elif c == '[':
                depth_bracket += 1
            elif c == ']':
                if depth_bracket == 0:
                    break
                depth_bracket -= 1
            elif c == ',' and depth_brace == 0 and depth_paren == 0 and depth_bracket == 0:
                break
            i += 1
        value_expr = content[value_start:i].strip()
        hits.append(FilterHit(
            field=key,
            value_expr=value_expr,
            is_operator=key.startswith("$"),
            value_start=value_start,
            value_end=i,
        ))
        while i < n and content[i] in ' \t\r\n,':
            i += 1
    return hits


def risk_for_field(field: str, is_operator: bool) -> str:
    if field == "$where":
        return RISK_CRITICAL
    if field == "$regex":
        return RISK_HIGH
    if field in ("$or", "$and", "$nor"):
        return RISK_MEDIUM
    return RISK_HIGH


# --------------------------------------------------------------------------- #
# Filter analysis
# --------------------------------------------------------------------------- #

def analyze_filter_literal(
    content_start: int,
    content_end: int,
    func_masked: str,
    func_src: str,
    inputs: dict[str, UserInput],
    findings: list[Finding],
    file: str,
    function: str,
    operation: str,
    call_line: int,
    lines: list[str],
    query_snippet: str,
    parent_field: str = "",
) -> None:
    """Walk a parsed bson.M/bson.D literal and emit findings.

    ``content_start`` and ``content_end`` are offsets (relative to
    ``func_masked`` and ``func_src``, which have the same length) of the
    literal's inner content — i.e. between the ``{`` and ``}``.
    """
    content_src = func_src[content_start:content_end]
    content_masked = func_masked[content_start:content_end]
    hits = parse_bson_pairs(content_src)
    for hit in hits:
        field = (parent_field + "." if parent_field else "") + hit.field
        # The value expression's offsets are relative to ``content_src``;
        # translate to func_src offsets for nested-literal scanning.
        v_start_abs = content_start + hit.value_start
        v_end_abs = content_start + hit.value_end
        v_masked = func_masked[v_start_abs:v_end_abs]
        v_src = func_src[v_start_abs:v_end_abs]
        # Find any nested bson.M{...} / bson.D{...} / bson.A{...} literals.
        nested = list(BSON_LITERAL_RE.finditer(v_masked))
        if nested:
            for nm in nested:
                brace_in_v = nm.end() - 1
                close_in_v = find_matching_brace(v_masked, brace_in_v)
                if close_in_v < 0:
                    continue
                # Translate back to func_masked offsets.
                inner_start = v_start_abs + brace_in_v + 1
                inner_end = v_start_abs + close_in_v
                analyze_filter_literal(
                    inner_start, inner_end,
                    func_masked, func_src, inputs, findings,
                    file, function, operation, call_line, lines,
                    query_snippet, parent_field=field,
                )
            # Also check the bare-identifier part of the value (if any).
            stripped_v_masked = BSON_LITERAL_RE.sub("", v_masked)
            stripped_v_src = BSON_LITERAL_RE.sub("", v_src)
            ui = is_user_input(stripped_v_src, stripped_v_masked, inputs, call_line)
            if ui:
                _emit_finding(
                    findings, file, function, operation, call_line,
                    lines, query_snippet,
                    field=field, ui=ui, value_expr=v_src,
                )
        else:
            ui = is_user_input(v_src, v_masked, inputs, call_line)
            if ui:
                _emit_finding(
                    findings, file, function, operation, call_line,
                    lines, query_snippet,
                    field=field, ui=ui, value_expr=v_src,
                )


def _emit_finding(
    findings: list[Finding],
    file: str,
    function: str,
    operation: str,
    call_line: int,
    lines: list[str],
    query_snippet: str,
    field: str,
    ui: UserInput,
    value_expr: str,
) -> None:
    base_risk = risk_for_field(field.split(".")[-1], field.startswith("$"))
    if ui.sanitized:
        risk = RISK_LOW
    else:
        risk = base_risk
    note_parts: list[str] = []
    if ui.sanitized:
        note_parts.append(
            f"value passed through sanitizer '{ui.sanitizer}' before query"
        )
    leaf = field.split(".")[-1]
    if leaf == "$where":
        note_parts.append(
            "$where allows JavaScript execution in MongoDB — CRITICAL if "
            "the value is attacker-controlled"
        )
    elif leaf == "$regex":
        note_parts.append(
            "$regex with user input enables regex injection / ReDoS — "
            "ensure input is escaped via escapeRegexInput()"
        )
    elif leaf in ("$or", "$and", "$nor"):
        note_parts.append(
            f"user input inside {leaf} array element — "
            "validate structure before query"
        )
    else:
        note_parts.append(
            "direct user input in filter value — ensure type checking "
            "(e.g. primitive.ObjectIDFromHex) prevents operator injection"
        )
    findings.append(Finding(
        file=file,
        line=call_line,
        end_line=call_line,
        function=function,
        operation=operation,
        query=query_snippet,
        source=ui.source,
        source_var=ui.var,
        field=field,
        risk=risk,
        sanitized=ui.sanitized,
        sanitizer=ui.sanitizer,
        snippet=query_snippet,
        note="; ".join(note_parts),
    ))


def analyze_filter_var(
    var_name: str,
    func_masked: str,
    func_src: str,
    func_start_line: int,
    inputs: dict[str, UserInput],
    findings: list[Finding],
    file: str,
    function: str,
    operation: str,
    call_line: int,
    lines: list[str],
    query_snippet: str,
) -> None:
    """When a query call passes a filter *variable* (not a literal),
    scan the function for ``varname["..."] = value`` assignments.
    """
    func_no_comments = mask_comments_only(func_src)
    for m in FILTER_ASSIGN_RE.finditer(func_no_comments):
        if m.group('filter') != var_name:
            continue
        key = m.group('key')
        value = m.group('value').strip()
        value = re.sub(r"//.*$", "", value).strip()
        if not value:
            continue
        assign_line = _line_of(func_no_comments, m.start()) + func_start_line - 1
        # Find the value's offsets within func_src.
        v_start_abs = m.start('value')
        v_end_abs = m.end('value')
        v_masked = func_masked[v_start_abs:v_end_abs]
        v_src = func_src[v_start_abs:v_end_abs]
        nested = list(BSON_LITERAL_RE.finditer(v_masked))
        if nested:
            for nm in nested:
                brace_in_v = nm.end() - 1
                close_in_v = find_matching_brace(v_masked, brace_in_v)
                if close_in_v < 0:
                    continue
                inner_start = v_start_abs + brace_in_v + 1
                inner_end = v_start_abs + close_in_v
                analyze_filter_literal(
                    inner_start, inner_end,
                    func_masked, func_src, inputs, findings,
                    file, function, operation, assign_line, lines,
                    query_snippet, parent_field=key,
                )
            stripped_v_masked = BSON_LITERAL_RE.sub("", v_masked)
            stripped_v_src = BSON_LITERAL_RE.sub("", v_src)
            ui = is_user_input(stripped_v_src, stripped_v_masked, inputs, assign_line)
            if ui:
                _emit_finding(
                    findings, file, function, operation, assign_line,
                    lines, query_snippet,
                    field=key, ui=ui, value_expr=v_src,
                )
        else:
            ui = is_user_input(v_src, v_masked, inputs, assign_line)
            if ui:
                # Determine if the assignment is inside a switch allowlist.
                if _in_switch_allowlist(func_masked, m.start(), var_name, ui):
                    ui = UserInput(
                        var=ui.var,
                        source=ui.source,
                        line=ui.line,
                        sanitized=True,
                        sanitizer="switch-allowlist",
                        sanitized_at_line=assign_line,
                    )
                _emit_finding(
                    findings, file, function, operation, assign_line,
                    lines, query_snippet,
                    field=key, ui=ui, value_expr=v_src,
                )


def _in_switch_allowlist(
    func_masked: str, assign_offset: int, filter_var: str, ui: UserInput,
) -> bool:
    """Check if an assignment is inside a ``switch <expr> { ... }`` block
    whose expression mentions the user-input variable (allowlist validation
    pattern like ``switch models.BillingStatus(bs) { case ...: filter[...] = bs }``).
    """
    depth = 0
    i = assign_offset - 1
    while i >= 0:
        c = func_masked[i]
        if c == '}':
            depth += 1
        elif c == '{':
            if depth == 0:
                # Found the enclosing block's opening brace. Look backward
                # for ``switch <expr>``.
                head = func_masked[max(0, i - 300):i]
                sm = re.search(
                    r"\bswitch\s+(?P<expr>[^{;]+?)\s*$", head,
                )
                if sm:
                    expr = sm.group('expr')
                    # Check if the user input variable appears in expr.
                    ui_var = ui.var
                    # Match as a whole word.
                    if re.search(rf"\b{re.escape(ui_var)}\b", expr):
                        return True
                return False
            else:
                depth -= 1
        i -= 1
    return False


# --------------------------------------------------------------------------- #
# Per-file scan
# --------------------------------------------------------------------------- #

def _split_args(masked_args_text: str) -> list[tuple[int, int, int]]:
    """Split a call's argument list on top-level commas.

    Returns a list of (start_offset, end_offset, depth_close) tuples —
    but actually we return (start, end) offsets relative to
    ``masked_args_text``.
    """
    args: list[tuple[int, int]] = []
    depth_paren = 0
    depth_bracket = 0
    depth_brace = 0
    start = 0
    for i, c in enumerate(masked_args_text):
        if c == '(':
            depth_paren += 1
        elif c == ')':
            depth_paren -= 1
        elif c == '[':
            depth_bracket += 1
        elif c == ']':
            depth_bracket -= 1
        elif c == '{':
            depth_brace += 1
        elif c == '}':
            depth_brace -= 1
        elif c == ',' and depth_paren == 0 and depth_bracket == 0 and depth_brace == 0:
            args.append((start, i))
            start = i + 1
    args.append((start, len(masked_args_text)))
    return args


def scan_query_calls(
    func_masked: str,
    func_src: str,
    func_start_line: int,
    inputs: dict[str, UserInput],
    findings: list[Finding],
    file: str,
    function: str,
    lines: list[str],
    filter_tracer_fields: Optional[dict[str, list[str]]] = None,
) -> int:
    """Find all MongoDB query calls in the function and analyze their filters."""
    count = 0
    for m in OP_CALL_RE.finditer(func_masked):
        op = m.group(1)
        open_paren = m.end() - 1
        close_paren = find_matching_paren(func_masked, open_paren)
        if close_paren < 0:
            continue
        call_line = _line_of(func_masked, m.start()) + func_start_line - 1
        call_end_line = _line_of(func_masked, close_paren) + func_start_line - 1
        snippet = make_snippet(lines, call_line, call_end_line, max_lines=8)
        # Split args on the masked source.
        args_start = open_paren + 1
        args_end = close_paren
        arg_spans = _split_args(func_masked[args_start:args_end])
        # Translate arg spans to func_masked offsets.
        arg_spans_abs = [(args_start + s, args_start + e) for s, e in arg_spans]
        # Skip leading ``ctx`` arg (position 0).
        count += 1
        filter_pos = OP_FILTER_POS.get(op, 1)
        if filter_pos < 0 or filter_pos >= len(arg_spans_abs):
            continue
        fs, fe = arg_spans_abs[filter_pos]
        filter_masked = func_masked[fs:fe]
        filter_src = func_src[fs:fe]
        # Strip whitespace.
        stripped = filter_masked.strip()
        lead = len(filter_masked) - len(filter_masked.lstrip())
        if lead:
            fs += lead
        trail = len(filter_masked) - len(filter_masked.rstrip())
        if trail:
            fe -= trail
        filter_masked = func_masked[fs:fe]
        filter_src = func_src[fs:fe]
        if not filter_masked:
            continue
        # If filter is a bson.M{...} / bson.D{...} / bson.A{...} literal:
        bsm = BSON_LITERAL_RE.match(filter_masked)
        if bsm:
            brace_pos_in_arg = bsm.end() - 1
            close_in_arg = find_matching_brace(filter_masked, brace_pos_in_arg)
            if close_in_arg >= 0:
                inner_start = fs + brace_pos_in_arg + 1
                inner_end = fs + close_in_arg
                analyze_filter_literal(
                    inner_start, inner_end,
                    func_masked, func_src, inputs, findings,
                    file, function, op, call_line, lines, snippet,
                )
        elif re.fullmatch(r"\w+", filter_masked):
            # Filter is a bare variable — scan for varname["..."] = ...
            analyze_filter_var(
                filter_masked, func_masked, func_src, func_start_line,
                inputs, findings, file, function, op, call_line, lines,
                snippet,
            )
            # If the regex scan produced no findings AND the Go filter
            # tracer has data for this call site, record the tracer's
            # fields as LOW-risk informational findings (manual review
            # recommended — we can't statically resolve the value
            # expressions for dynamic filter constructions across
            # helper functions / conditional branches).
            if filter_tracer_fields:
                traced = _lookup_filter_tracer_fields(
                    file, call_line, filter_tracer_fields,
                )
                if traced:
                    # Count findings emitted by the regex scan for this
                    # call line so we know if the tracer adds anything.
                    before = sum(
                        1 for f in findings if f.line == call_line
                    )
                    for field_name in traced:
                        if field_name.startswith("$"):
                            continue
                        findings.append(Finding(
                            file=file,
                            line=call_line,
                            end_line=call_line,
                            function=function,
                            operation=op,
                            query=snippet,
                            source="tracer:filter-tracer",
                            source_var=filter_masked,
                            field=field_name,
                            risk=RISK_LOW,
                            sanitized=True,
                            sanitizer="go/ssa-filter-tracer",
                            snippet=snippet,
                            note=(
                                f"filter field `{field_name}` detected by "
                                f"go/ssa filter tracer on variable "
                                f"`{filter_masked}` — value expression "
                                f"could not be statically resolved; "
                                f"manual review recommended"
                            ),
                        ))
                    after = sum(
                        1 for f in findings if f.line == call_line
                    )
                    if after > before:
                        # The tracer added findings — also re-evaluate
                        # any HIGH-risk findings the regex emitted for
                        # this call (they may now be redundant).
                        pass
        # For UpdateByID, also scan the update doc (3rd arg).
        if op == "UpdateByID" and len(arg_spans_abs) >= 3:
            us, ue = arg_spans_abs[2]
            upd_masked = func_masked[us:ue]
            ubm = BSON_LITERAL_RE.match(upd_masked)
            if ubm:
                brace_pos_in_arg = ubm.end() - 1
                close_in_arg = find_matching_brace(upd_masked, brace_pos_in_arg)
                if close_in_arg >= 0:
                    inner_start = us + brace_pos_in_arg + 1
                    inner_end = us + close_in_arg
                    analyze_filter_literal(
                        inner_start, inner_end,
                        func_masked, func_src, inputs, findings,
                        file, function, op, call_line, lines, snippet,
                    )
    return count


def scan_file(
    path: Path,
    project_root: Path,
    filter_tracer_fields: Optional[dict[str, list[str]]] = None,
) -> tuple[list[Finding], FileStats]:
    try:
        src = path.read_text(encoding='utf-8', errors='replace')
    except Exception:
        return [], FileStats(path=str(path), is_test=path.name.endswith("_test.go"))

    try:
        rel_path = str(path.relative_to(project_root))
        if rel_path == ".":
            rel_path = path.name
    except ValueError:
        rel_path = str(path)

    is_test = path.name.endswith("_test.go")
    masked = mask_source(src)
    lines = src.splitlines()
    funcs = parse_functions(masked)

    findings: list[Finding] = []
    queries_scanned = 0
    for f in funcs:
        func_masked = masked[f.start_offset:f.end_offset + 1]
        func_src = src[f.start_offset:f.end_offset + 1]
        inputs = collect_user_inputs(func_src, func_masked, f.start_line)
        queries_scanned += scan_query_calls(
            func_masked, func_src, f.start_line, inputs,
            findings, rel_path, f.name, lines,
            filter_tracer_fields=filter_tracer_fields,
        )

    stats = FileStats(
        path=rel_path,
        is_test=is_test,
        lines=len(lines),
        queries_scanned=queries_scanned,
        findings=len(findings),
    )
    return findings, stats


# --------------------------------------------------------------------------- #
# Aggregation
# --------------------------------------------------------------------------- #

# Path to the Go filter tracer source. Resolved relative to this script
# so the tool works regardless of the current working directory.
FILTER_TRACER_PATH = Path(__file__).resolve().parent / 'go' / 'graphify_filter_tracer' / 'main.go'


def load_go_filter_tracer(repo_root: Path) -> dict[str, list[str]]:
    """Run the Go filter tracer over the backend module and return a
    ``{position_key: [field_names]}`` map.

    The position key is ``"file:line"`` (relative file path + the line
    number of the MongoDB call site). The tracer uses go/ssa to follow
    ``filter["x"] = y`` patterns and struct-typed InsertOne arguments,
    so the returned fields include dynamically constructed filter keys
    (which the regex-based parser cannot see).

    Returns an empty dict if the Go toolchain is unavailable or the
    tracer fails.
    """
    env = os.environ.copy()
    go_path = Path('/home/z/.local/go/bin')
    if go_path.exists():
        env['PATH'] = f'{go_path}:{env.get("PATH", "")}'
    env.setdefault('GOTOOLCHAIN', 'auto')

    backend_dir = repo_root / 'backend'
    if not backend_dir.is_dir():
        backend_dir = repo_root
    if not FILTER_TRACER_PATH.is_file():
        print(
            f'  ! filter tracer not found at {FILTER_TRACER_PATH}',
            file=sys.stderr,
        )
        return {}

    out_file = Path('/tmp/graphify-nosql-filters.json')
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

    out: dict[str, list[str]] = {}
    for entry in data:
        for finding in entry.get('findings', []):
            method = finding.get('method', '')
            if method not in ('literal', 'map_update'):
                continue
            position = finding.get('position', '')
            if not position or ':' not in position:
                continue
            for f in finding.get('fields', []):
                if f and not f.startswith('$'):
                    out.setdefault(position, []).append(f)
    print(
        f'  Loaded filter tracer data for {len(out)} call sites',
        file=sys.stderr,
    )
    return out


def _lookup_filter_tracer_fields(
    file: str,
    line: int,
    tracer_data: dict[str, list[str]],
) -> Optional[list[str]]:
    """Look up the dynamic filter fields for a query at ``file:line``.

    Tries multiple key forms (with and without a leading ``backend/``
    prefix) since the tracer's file paths are relative to the module
    root but the auditor's ``file`` attribute may be relative to the
    repo root (which includes the ``backend/`` prefix).
    """
    if not tracer_data or not file or not line:
        return None
    candidates = [
        f'{file}:{line}',
        f'backend/{file}:{line}' if not file.startswith('backend/') else f'{file[len("backend/"):]}:{line}',
    ]
    for key in candidates:
        fields = tracer_data.get(key)
        if fields:
            seen: set[str] = set()
            out: list[str] = []
            for f in fields:
                if f not in seen:
                    seen.add(f)
                    out.append(f)
            return out
    return None


def collect_files(root: Path) -> list[Path]:
    if root.is_file():
        return [root] if root.suffix == ".go" else []
    out: list[Path] = []
    for p in root.rglob("*.go"):
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        out.append(p)
    return sorted(out)


def scan_project(root: Path) -> dict:
    files = collect_files(root)
    # Run the Go filter tracer (go/ssa-based, sees dynamic filter["x"] = y
    # patterns the regex parser misses). Falls back gracefully to an
    # empty dict if the Go toolchain is unavailable.
    filter_tracer_fields = load_go_filter_tracer(root)
    all_findings: list[Finding] = []
    all_stats: list[FileStats] = []
    for path in files:
        findings, stats = scan_file(
            path, root,
            filter_tracer_fields=filter_tracer_fields,
        )
        all_stats.append(stats)
        if not stats.is_test:
            all_findings.extend(findings)

    non_test_stats = [s for s in all_stats if not s.is_test]
    test_stats = [s for s in all_stats if s.is_test]

    risk_counts = Counter(f.risk for f in all_findings)
    risky_findings = [f for f in all_findings if f.risk != RISK_LOW]

    by_file: dict[str, dict] = defaultdict(lambda: {
        "queries": 0, "findings": 0, "critical": 0, "high": 0, "medium": 0, "low": 0,
    })
    for s in non_test_stats:
        by_file[s.path]["queries"] += s.queries_scanned
    for f in all_findings:
        by_file[f.file]["findings"] += 1
        rk = f.risk.lower()
        if rk in by_file[f.file]:
            by_file[f.file][rk] += 1

    top_files = sorted(
        by_file.items(),
        key=lambda kv: (
            -kv[1]["critical"],
            -kv[1]["high"],
            -kv[1]["medium"],
            -kv[1]["findings"],
            kv[0],
        ),
    )[:20]

    source_counts = Counter(f.source.split(":")[0] for f in all_findings)

    return {
        "root": str(root),
        "summary": {
            "total_files": len(files),
            "non_test_files": len(non_test_stats),
            "test_files": len(test_stats),
            "non_test_lines": sum(s.lines for s in non_test_stats),
            "queries_scanned": sum(s.queries_scanned for s in non_test_stats),
            "total_findings": len(all_findings),
            "risky_findings": len(risky_findings),
            "sanitized_findings": risk_counts.get(RISK_LOW, 0),
            "by_risk": {
                "CRITICAL": risk_counts.get(RISK_CRITICAL, 0),
                "HIGH":     risk_counts.get(RISK_HIGH, 0),
                "MEDIUM":   risk_counts.get(RISK_MEDIUM, 0),
                "LOW":      risk_counts.get(RISK_LOW, 0),
            },
            "by_source": dict(source_counts),
        },
        "top_files": [
            {"file": f, **stats} for f, stats in top_files
        ],
        "findings": [asdict(f) for f in all_findings],
        "file_stats": [asdict(s) for s in all_stats],
    }


# --------------------------------------------------------------------------- #
# Markdown rendering
# --------------------------------------------------------------------------- #

def render_markdown(report: dict) -> str:
    s = report["summary"]
    by_risk = s["by_risk"]
    by_source = s["by_source"]
    findings = report["findings"]
    top_files = report["top_files"]

    out: list[str] = []
    out.append("# NoSQL Injection Audit")
    out.append("")
    out.append(f"**Target:** `{report['root']}`")
    out.append("")
    out.append("## Summary (non-test files)")
    out.append("")
    out.append("| Metric | Value |")
    out.append("| --- | ---: |")
    out.append(f"| Files scanned | {s['non_test_files']} |")
    out.append(f"| Total lines | {s['non_test_lines']:,} |")
    out.append(f"| MongoDB queries scanned | **{s['queries_scanned']}** |")
    out.append(f"| Total findings | {s['total_findings']} |")
    out.append(f"| Risky findings (CRITICAL/HIGH/MEDIUM) | **{s['risky_findings']}** |")
    out.append(f"| Sanitized (LOW) | {s['sanitized_findings']} |")
    out.append("")
    out.append("### Findings by risk")
    out.append("")
    out.append("| Risk | Count | Meaning |")
    out.append("| --- | ---: | --- |")
    out.append(f"| CRITICAL | {by_risk['CRITICAL']} | `$where` with user input — JS injection |")
    out.append(f"| HIGH | {by_risk['HIGH']} | Direct user input in filter / `$regex` injection |")
    out.append(f"| MEDIUM | {by_risk['MEDIUM']} | User input in `$or`/`$and`/`$nor` arrays |")
    out.append(f"| LOW | {by_risk['LOW']} | User input was sanitized before query |")
    out.append("")
    out.append("### Findings by user-input source")
    out.append("")
    out.append("| Source | Count |")
    out.append("| --- | ---: |")
    for src, n in sorted(by_source.items(), key=lambda kv: -kv[1]):
        out.append(f"| {src} | {n} |")
    out.append("")

    out.append("## Top Files by Risk")
    out.append("")
    if not top_files:
        out.append("_No files with findings._")
    else:
        out.append("| File | Queries | Findings | CRITICAL | HIGH | MEDIUM | LOW |")
        out.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: |")
        for f in top_files:
            st = {k: f[k] for k in ("queries", "findings", "critical", "high", "medium", "low")}
            out.append(
                f"| `{f['file']}` | {st['queries']} | {st['findings']} | "
                f"{st['critical']} | {st['high']} | {st['medium']} | {st['low']} |"
            )
    out.append("")

    by_file: dict[str, list[dict]] = {}
    for f in findings:
        by_file.setdefault(f["file"], []).append(f)

    out.append("## Detailed Findings")
    out.append("")
    if not by_file:
        out.append("_No injection risks detected._")
    else:
        sev_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        for file in sorted(by_file):
            file_findings = by_file[file]
            file_findings.sort(
                key=lambda f: (sev_order.get(f["risk"], 4), f["line"])
            )
            out.append(f"### `{file}`")
            out.append("")
            for f in file_findings:
                out.append(
                    f"- **[{f['risk']}] {f['operation']}** — "
                    f"`{f['file']}:{f['line']}` in `{f['function']}`"
                )
                out.append(f"  - **Field:** `{f['field']}`")
                out.append(f"  - **Source:** `{f['source']}` (var `{f['source_var']}`)")
                if f["sanitized"]:
                    out.append(
                        f"  - **Sanitized:** yes, via `{f['sanitizer']}`"
                    )
                else:
                    out.append(f"  - **Sanitized:** no")
                if f["note"]:
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
        "The scanner walks every `.go` file (excluding `vendor/`, "
        "`node_modules/`, `.git/`, `graphify-out/`, `testdata/`) and "
        "applies these heuristics:"
    )
    out.append("")
    out.append(
        "1. **Function-level user input tracking.** For each top-level "
        "function/method, build a map of variables that hold user input. "
        "Sources recognized: `r.URL.Query().Get(...)`, `q.Get(...)` (where "
        "`q := r.URL.Query()`), `r.FormValue(...)`, `chi.URLParam(...)`, "
        "`mux.Vars(r)[...]`, and JSON-body struct fields (`req.Field` "
        "where `req` was decoded from `r.Body`). String literals are "
        "preserved during pattern matching (only comments are stripped)."
    )
    out.append(
        "2. **Sanitizer tracking.** Variables assigned from "
        "`primitive.ObjectIDFromHex(...)`, `escapeRegexInput(...)`, "
        "`strconv.Atoi/ParseInt/ParseFloat/ParseBool(...)`, "
        "`time.Parse(...)`, `url.PathEscape/QueryEscape(...)`, "
        "`regexp.MustCompile(...)`, `uuid.Parse(...)`, or "
        "`primitive.Regex{Pattern: ...escapeRegexInput(...)...}` are marked "
        "sanitized. `switch X { case ... }` allowlist validation is also "
        "recognized when the case body assigns a literal (not `X`) to the "
        "filter. Struct-level validation via `validator.Struct(&req)` or "
        "the project's `validation.Validate(&req)` wrapper marks every "
        "`req.*` field as sanitized (when the validation call occurs "
        "BEFORE the query). Per-field custom validators "
        "(`if !isValidEmail(req.Email) { return ... }`) are recognized "
        "by function-name prefix (`is*`/`valid*`/`validate*`/`check*`) "
        "and mark their argument as sanitized."
    )
    out.append(
        "3. **MongoDB query detection.** Every call to a known mongo-driver "
        "method (`Find`, `FindOne`, `InsertOne`, `UpdateOne`, `DeleteOne`, "
        "`Aggregate`, `CountDocuments`, etc.) is located via paren matching "
        "on a masked source (strings/comments blanked out)."
    )
    out.append(
        "4. **Filter analysis.** The filter argument (positional after "
        "`ctx`) is parsed. If it's a `bson.M{...}` / `bson.D{...}` "
        "literal, every key/value pair is extracted via balanced-brace "
        "matching on the masked source, then re-read from the original "
        "source to preserve string-literal field names; nested literals "
        "(e.g. inside `$or` arrays) are recursed. If the filter is a "
        "variable, the function is scanned for "
        "`varname[\"...\"] = value` assignments."
    )
    out.append(
        "5. **Risk classification.** `$where` with user input → CRITICAL "
        "(JS execution). Direct user input in a field value, or `$regex` "
        "with user input → HIGH. User input in `$or`/`$and`/`$nor` array "
        "elements → MEDIUM. Sanitized user input → LOW (informational)."
    )
    out.append("")
    out.append(
        "**Note on Go type safety:** Go struct fields and `string`-returning "
        "APIs (`r.URL.Query().Get`) are statically typed, so classic "
        "operator-injection (`{\"$ne\": null}` passed as a *string*) is "
        "not directly exploitable. The real risks in Go are (a) `$where` "
        "(JavaScript execution context), (b) `$regex` (ReDoS), and (c) "
        "any code path that decodes user JSON into an `interface{}` / "
        "`map[string]interface{}` and passes it directly to a query. The "
        "HIGH findings for plain string fields are flagged conservatively "
        "for human review — most are safe but warrant a glance."
    )
    out.append("")
    return "\n".join(out)


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Scan Go source for NoSQL injection risks in MongoDB queries.",
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Path to scan (file or directory). Default: current directory.",
    )
    parser.add_argument(
        "--out",
        default=None,
        help="Write markdown report to this path (in addition to public/NOSQL_INJECTION.md).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the JSON report to stdout.",
    )
    args = parser.parse_args(argv)

    root = Path(args.path).resolve()
    if not root.exists():
        print(f"ERROR: path not found: {root}", file=sys.stderr)
        return 2

    print(f"Scanning {root} ...", file=sys.stderr)
    report = scan_project(root)

    public_dir = Path("/home/z/my-project/public")
    json_path = public_dir / "nosql-injection.json"
    md_path = public_dir / "NOSQL_INJECTION.md"
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
            # When --json is set, --out receives JSON (matching
            # graphify_api_shapes.py's behavior). Without --json, --out
            # receives the markdown report.
            if args.json:
                out_path.write_text(
                    json.dumps(report, indent=2) + "\n", encoding="utf-8",
                )
            else:
                out_path.write_text(render_markdown(report), encoding="utf-8")
            print(f"Report written to {out_path}", file=sys.stderr)
        except Exception as e:
            print(f"ERROR: could not write --out file: {e}", file=sys.stderr)
            return 1

    if args.json:
        print(json.dumps(report, indent=2))

    s = report["summary"]
    print(
        f"Scanned {s['non_test_files']} non-test Go files "
        f"({s['queries_scanned']} MongoDB queries).",
        file=sys.stderr,
    )
    print(
        f"Findings: CRITICAL={s['by_risk']['CRITICAL']}  "
        f"HIGH={s['by_risk']['HIGH']}  "
        f"MEDIUM={s['by_risk']['MEDIUM']}  "
        f"LOW={s['by_risk']['LOW']}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
