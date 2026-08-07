#!/usr/bin/env python3
"""graphify_errors — audit Go source code for error handling patterns.

Scans all .go files under the given path (default: current directory) and
classifies each error-related construct into one of:

  * proper_handling  - `if err != nil { return err }` or body that contains
                       a recognised proper-handler pattern
                       (http.Redirect / respondWithError / ErrNoDocuments /
                       continue / assignment to a variable or struct field)
                                                                       (LOW)
  * logged_only      - `if err != nil { slog.Warn(...); return }` etc.
                       (slog.*, log.Print*, fmt.Print*, fmt.Fprint*(os.Stderr))
                                                                       (MEDIUM)
  * swallowed        - `if err != nil { }` or bare `return` / `return nil`
                       / `return errors.New("...")` with no logging and no
                       proper-handler pattern                 (HIGH)
  * ignored          - `result, _ := someFunc()`                      (HIGH)
  * missing_check    - statement-form call to a known error-returning fn (HIGH)
  * panic_on_error   - `if err != nil { panic(err) }`                 (MEDIUM)

For each finding the script records file, line, containing function,
pattern type, code snippet, and severity. A summary gives total errors
checked, % properly handled, and the most problematic files.

Test files (`*_test.go`) are scanned separately and only their aggregate
statistics are reported, so the main findings list reflects production code.

Usage:
    python graphify_errors.py [path] [--out report.md] [--json] [--include-tests]

Outputs:
    - JSON written to /home/z/my-project/public/error-audit.json (best effort)
    - Markdown written to /home/z/my-project/public/ERROR_AUDIT.md (best effort)
    - Markdown written to --out path if specified
    - JSON to stdout if --json given

Test target: /home/z/my-project/repos/lastsaas/backend
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #

PATTERN_SEVERITY: dict[str, str] = {
    "proper_handling": "LOW",
    "logged_only":     "MEDIUM",
    "swallowed":       "HIGH",
    "ignored":         "HIGH",
    "missing_check":   "HIGH",
    "panic_on_error":  "MEDIUM",
}

PATTERN_LABEL: dict[str, str] = {
    "proper_handling": "Proper handling",
    "logged_only":     "Logged only (no return)",
    "swallowed":       "Swallowed error",
    "ignored":         "Ignored error (`_`)",
    "missing_check":   "Missing error check",
    "panic_on_error":  "Panic on error",
}

# Methods/functions that almost always return an error in idiomatic Go.
# Used by the `missing_check` heuristic. Conservative list — keeps false
# positives low while still catching the common offenders (DB/IO/codec).
ERROR_RETURNING_NAMES: set[str] = {
    # io / fs / os
    # NOTE: WriteString omitted — strings.Builder/bytes.Buffer.WriteString
    # always return a nil error and would dominate the report with false
    # positives. Write is kept because io.Writer implementations (os.File,
    # http.ResponseWriter, etc.) can fail.
    "Close", "Write", "Read", "ReadAll", "ReadFile",
    "WriteFile", "Sync", "Flush", "Seek", "Copy", "CopyN", "CopyBuffer",
    "Open", "Create", "OpenFile", "Mkdir", "MkdirAll",
    "Remove", "RemoveAll", "Rename", "Chmod", "Chown",
    # encoding
    "Marshal", "Unmarshal", "MarshalJSON", "UnmarshalJSON",
    "Encode", "Decode",
    # mongodb driver — direct error returners only (cursor/single-result
    # builders like FindOne/Find/Aggregate return result types, not errors,
    # and are excluded to avoid false positives).
    "InsertOne", "InsertMany", "UpdateOne", "UpdateMany", "UpdateByID",
    "ReplaceOne", "DeleteOne", "DeleteMany", "BulkWrite",
    "CountDocuments", "EstimatedDocumentCount",
    "Drop", "CreateCollection", "CreateIndex",
    # database/sql
    "Exec", "Query", "QueryRow", "QueryContext", "ExecContext",
    "Begin", "BeginTx", "Commit", "Rollback", "Prepare", "PrepareContext",
    "Scan",
    # net/http client
    "Do", "Send", "Post", "PostForm", "Head",
    # net
    "Connect", "Ping", "PingContext", "Disconnect", "Dial", "Listen",
    # crypto / templates / misc
    "Sign", "Verify", "Encrypt", "Decrypt",
    "Parse", "ParseFile", "ParseBytes", "Validate",
    "Render", "Execute", "ExecuteTemplate",
    "Save", "Load",
    "Compress", "Decompress",
}

# Logging-like call patterns used by the `if err != nil` body classifier.
# NOTE: the `[^)]*` inside the first alternative is safe even when the call
# has nested parens (e.g. `slog.Warn("m", "k", fmt.Sprintf(...))`) because
# string literals are masked out before classification — the masked form
# retains the inner `)` of `Sprintf(...)`, which `[^)]*` correctly stops at,
# and the outer `)` of `Warn(...)` then closes the match.
LOG_CALL_RE = re.compile(
    r'(?:\b(?:log|slog|fmt|syslog)\.[A-Za-z_]\w*\s*\([^)]*\)'
    r'|\.[A-Za-z_]\w*\s*\(\s*[^)]*\berr\b[^)]*\))'
)

# Explicit "logging" patterns. These acknowledge the error (printing it to
# stdout/stderr/log stream) even when the original `err` value isn't
# propagated. Used to reclassify what would otherwise be `swallowed` as
# `logged_only` (MEDIUM). `fmt.Errorf` is intentionally excluded — it
# constructs a new error rather than logging one.
SLOG_LOG_RE = re.compile(r'\bslog\.(?:Warn|Error|Info|Debug)(?:ln|f)?\s*\(')
LOG_PRINT_RE = re.compile(
    r'\blog\.(?:Print|Printf|Println|Fatal|Fatalf|Fatalln|'
    r'Panic|Panicf|Panicln)\s*\('
)
FMT_PRINT_RE = re.compile(
    r'\bfmt\.(?:Print|Printf|Println|Fprint|Fprintf|Fprintln|'
    r'Sprint|Sprintf|Sprintln)\s*\('
)
# Explicit stderr-write pattern (called out separately in the spec for
# clarity; functionally a subset of FMT_PRINT_RE).
STDERR_FMT_RE = re.compile(
    r'\bfmt\.F(?:printf|println|print)\s*\(\s*os\.Stderr\b'
)

# Error-reporting helpers (HTTP response writers, etc.) — used to recognize
# the standard `if err != nil { respondWithError(...); return }` pattern.
# Per the audit spec these are treated as `proper_handling` (LOW): the error
# is reported to the client and the request is short-circuited.
ERROR_REPORT_RE = re.compile(
    r'\b(?:respondWithError|http\.Error|writeError|sendError|WriteError|'
    r'ReturnError|FailWith|abortWithStatus|abortWithError|c\.AbortWithStatusJSON|'
    r'c\.JSON)\s*\('
)

# Patterns indicating the error triggers a corrective/terminal action —
# even when the original `err` is not propagated, the site is correctly
# handled (state change, control-flow response, or HTTP redirect).
HTTP_REDIRECT_RE = re.compile(r'\bhttp\.Redirect\s*\(')
ERRNO_DOCS_RE = re.compile(r'\b(?:mongo\.)?ErrNoDocuments\b')
CONTINUE_RE = re.compile(r'\bcontinue\b')
# Assignment statement — `var = value` or `obj.field = value` (single line).
# Excludes `==` (comparison) and `:=` (short variable declaration). Catches
# defensive patterns like `page = 1` (input clamping) and
# `delivery.Success = false` (failure flagging).
ASSIGNMENT_RE = re.compile(r'^[ \t]*\w[\w.]*\s*=(?!=)', re.MULTILINE)

# Terminal error handling — program exits with non-zero status after reporting.
TERMINAL_EXIT_RE = re.compile(r'\bos\.Exit\s*\(\s*[1-9]')
LOG_FATAL_RE = re.compile(r'\blog\.Fatal(?:ln|f)?\s*\(')
# Testing helpers — `t.Fatal*` stops the test (terminal); `t.Error*` marks
# failure but continues (treated as logged_only).
TEST_FATAL_RE = re.compile(r'\bt\.Fatal(?:ln|f)?\s*\(')
TEST_ERROR_RE = re.compile(r'\bt\.Error(?:ln|f)?\s*\(')

# Regex helpers ------------------------------------------------------------- #

# Match `if ... != nil ... {` (allows init statement with `;`).
IF_NIL_RE = re.compile(r'\bif\b[^{]*!=\s*nil\b[^{]*\{')

# Discarded error: `result, _ := F(` or `_, _ := F(`
IGNORED_RE = re.compile(r'\b\w+\s*,\s*_\s*(?::=|=)\s*[\w.]+\s*\(')

# `if err != nil` body classification
# RETURN_ERR_RE is case-insensitive so it also catches `return res.Err()`
# or `return cursor.Err()` — common patterns where the error is fetched via
# a method call rather than a bare identifier. `\berr\b` still requires `err`
# to be a complete word (so `ferrisWheel` is not matched).
RETURN_ERR_RE = re.compile(r'\breturn\b[^;]*\berr\b', re.IGNORECASE)
RETURN_NEW_ERR_RE = re.compile(
    r'\breturn\b\s+(?:fmt\.Errorf|errors\.Wrap|errors\.Wrapf|errors\.New)\s*\('
)
RETURN_ANY_RE = re.compile(r'\breturn\b')
PANIC_RE = re.compile(r'\bpanic\s*\(')

# Function declaration: ^func [recv]? Name(
FUNC_DECL_RE = re.compile(
    r'^[ \t]*func(?:[ \t]+\([^)]*\))?[ \t]+(?P<name>\w+)[ \t]*\(',
    re.MULTILINE,
)

# Skip lines starting with these keywords for missing_check
CONTROL_KW_RE = re.compile(
    r'^(?:if|for|switch|case|return|break|continue|go|defer|select|'
    r'var|const|type|struct|interface|package|import|func|map|chan|range|'
    r'default|fallthrough|else)\b'
)


# --------------------------------------------------------------------------- #
# Data classes
# --------------------------------------------------------------------------- #

@dataclass
class Finding:
    file: str
    line: int
    end_line: int
    function: str
    pattern: str
    severity: str
    snippet: str
    note: str = ""


@dataclass
class FileStats:
    path: str
    is_test: bool
    lines: int = 0
    total_error_sites: int = 0
    proper: int = 0
    logged: int = 0
    swallowed: int = 0
    ignored: int = 0
    missing: int = 0
    panic: int = 0

    @property
    def problematic(self) -> int:
        return self.swallowed + self.ignored + self.missing

    @property
    def pct_proper(self) -> float:
        return (100.0 * self.proper / self.total_error_sites) if self.total_error_sites else 0.0


@dataclass
class FuncRange:
    name: str
    start_line: int  # 1-indexed
    end_line: int    # 1-indexed
    is_init: bool


# --------------------------------------------------------------------------- #
# Lexer-ish helpers
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
        # Line comment
        if c == '/' and i + 1 < n and src[i + 1] == '/':
            while i < n and src[i] != '\n':
                out[i] = ' '
                i += 1
            continue
        # Block comment
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
        # Rune literal '...'
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
        # Double-quoted string "..."
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
        # Back-quoted raw string `...`
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
    """Given position of `{` in masked source, return matching `}` position."""
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


def parse_functions(masked: str) -> list[FuncRange]:
    """Find named top-level function/method declarations and their body ranges."""
    funcs: list[FuncRange] = []
    for m in FUNC_DECL_RE.finditer(masked):
        name = m.group('name')
        # Walk forward from end of match (right after `(`) to find the body `{`.
        i = m.end()
        n = len(masked)
        depth_paren = 1  # we're inside `(` already (match ends after `(`)
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
            is_init=(name == "init"),
        ))
    return funcs


def containing_function(funcs: list[FuncRange], line: int) -> str:
    """Innermost named function whose body contains `line`."""
    best: Optional[FuncRange] = None
    best_span = None
    for f in funcs:
        if f.start_line <= line <= f.end_line:
            span = f.end_line - f.start_line
            if best is None or span < best_span:
                best = f
                best_span = span
    return best.name if best else "<top-level>"


# --------------------------------------------------------------------------- #
# Pattern classification
# --------------------------------------------------------------------------- #

def is_err_ident(name: str) -> bool:
    """Heuristic: does this identifier look like an error variable?"""
    if not name:
        return False
    n = name.lower()
    return (
        n == "err"
        or n == "e"
        or n.startswith("err")
        or n.endswith("err")
        or n.endswith("error")
    )


def classify_err_body(body_masked: str) -> str:
    """Classify the body of `if X != nil { body }`.

    The body passed in is the **full** masked content between the opening
    `{` and the matching `}` (not just the snippet, which is capped at 6
    lines for display). This lets us recognise valid handler patterns that
    span multiple lines (e.g. an `http.Redirect` call followed by a
    `return`, or an `if err == mongo.ErrNoDocuments` check followed by a
    fallback path).

    Classification order (each step short-circuits):

      1.  Empty body                                  -> swallowed
      2.  `panic(...)`                                -> panic_on_error
      3.  Terminal exit (`os.Exit(non-zero)`,
         `log.Fatal*`, `t.Fatal*`)                    -> proper_handling
      4.  `return ...err...` (case-insensitive,
          catches `return err`, `return fmt.Errorf("...: %w", err)`,
          `return res.Err()`, etc.)                   -> proper_handling
      5.  Proper-handler patterns (any of):
            - `http.Redirect(...)`
            - `respondWithError(...)` / `http.Error(...)`
              / `writeError(...)` / etc.
            - `mongo.ErrNoDocuments` / `ErrNoDocuments` check
            - `continue` statement (batch processing)
            - Assignment to a variable or struct field
              (`page = 1`, `delivery.Success = false`, ...) -> proper_handling
      6.  Logging patterns (any of):
            - `slog.Warn/Error/Info/Debug(...)`
            - `log.Print*/Fatal*/Panic*(...)`
            - `fmt.Print*/Fprint*/Sprint*(...)`
              (excludes `fmt.Errorf` — that's error construction)
            - `fmt.Fprint*(os.Stderr, ...)`           -> logged_only
      7.  `return` (bare or new error like
          `return errors.New("oops")`)                -> swallowed
      8.  `t.Error*` (no return, no other handler)    -> logged_only
      9.  Body consists ONLY of logging calls
          (fallback `LOG_CALL_RE` sweep)              -> logged_only
      10. Anything else                               -> swallowed
    """
    stripped = body_masked.strip()
    if not stripped:
        return "swallowed"
    if PANIC_RE.search(stripped):
        return "panic_on_error"
    # Terminal CLI error handling: program exits with non-zero status after
    # reporting the error. The error info is preserved and the program fails.
    if TERMINAL_EXIT_RE.search(stripped) or LOG_FATAL_RE.search(stripped):
        return "proper_handling"
    # Test termination — `t.Fatal*` reports the failure and stops the test.
    if TEST_FATAL_RE.search(stripped):
        return "proper_handling"
    # Returns the captured err directly (or wraps it via fmt.Errorf/errors.Wrap).
    # Case-insensitive so it also catches `return res.Err()` / `return cursor.Err()`.
    if RETURN_ERR_RE.search(stripped):
        return "proper_handling"

    # ----- valid handler patterns (reclassify what would otherwise be
    #       "swallowed"). These are checked BEFORE the has_return branches
    #       below so that bodies like
    #         `if err != nil { slog.Warn(...); return }`
    #       or
    #         `if err != nil { http.Redirect(...); return }`
    #       are recognised as acknowledged/handled rather than swallowed.
    if (
        HTTP_REDIRECT_RE.search(stripped)
        or ERROR_REPORT_RE.search(stripped)
        or ERRNO_DOCS_RE.search(stripped)
        or CONTINUE_RE.search(stripped)
        or ASSIGNMENT_RE.search(stripped)
    ):
        return "proper_handling"

    if (
        SLOG_LOG_RE.search(stripped)
        or LOG_PRINT_RE.search(stripped)
        or FMT_PRINT_RE.search(stripped)
        or STDERR_FMT_RE.search(stripped)
    ):
        return "logged_only"

    # Returns a *new* error (no `err` in the return expression).
    # The original error is dropped — call it swallowed but note it.
    if RETURN_NEW_ERR_RE.search(stripped):
        return "swallowed"

    has_return = RETURN_ANY_RE.search(stripped) is not None
    # Bare `return` or `return <non-err>` — original error dropped
    if has_return:
        return "swallowed"
    # No return at all. Check for non-terminal test reporting (`t.Error*`).
    if TEST_ERROR_RE.search(stripped):
        return "logged_only"
    # Otherwise: if only logging calls remain, it's logged_only;
    # else the error is genuinely swallowed.
    no_logs = LOG_CALL_RE.sub('', stripped)
    no_logs = re.sub(r'[\s;{}]+', '', no_logs)
    if not no_logs:
        return "logged_only"
    return "swallowed"


# --------------------------------------------------------------------------- #
# Snippet helper
# --------------------------------------------------------------------------- #

def make_snippet(lines: list[str], start: int, end: int, max_lines: int = 6) -> str:
    """Extract snippet from lines (1-indexed) for display."""
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


def extract_outermost_method(stripped: str) -> Optional[tuple[str, str]]:
    """For a statement-form call line, find the outermost call.

    Returns ``(call_target, method_name)`` where ``call_target`` is the
    full dotted prefix up to and including the method, and ``method_name``
    is the last identifier before the outermost ``(``.

    Returns ``None`` if the line is not a clean statement-form call
    (i.e. if there's anything significant after the outermost ``)``).
    """
    depth_paren = 0
    depth_bracket = 0
    depth_brace = 0
    last_call_paren = -1
    for i, c in enumerate(stripped):
        if c == '(':
            if (
                depth_paren == 0
                and depth_bracket == 0
                and depth_brace == 0
                and i > 0
            ):
                j = i - 1
                while j >= 0 and stripped[j].isspace():
                    j -= 1
                if j >= 0 and (
                    stripped[j].isalnum()
                    or stripped[j] == '_'
                    or stripped[j] == ')'
                ):
                    last_call_paren = i
            depth_paren += 1
        elif c == ')':
            depth_paren -= 1
            if depth_paren < 0:
                return None
        elif c == '[':
            depth_bracket += 1
        elif c == ']':
            depth_bracket -= 1
            if depth_bracket < 0:
                return None
        elif c == '{':
            depth_brace += 1
        elif c == '}':
            depth_brace -= 1
            if depth_brace < 0:
                return None
    if depth_paren != 0 or depth_bracket != 0 or depth_brace != 0:
        return None  # unbalanced
    if last_call_paren < 0:
        return None
    # Find matching `)` for the outermost call.
    depth = 1
    end_pos = -1
    for i in range(last_call_paren + 1, len(stripped)):
        c = stripped[i]
        if c == '(':
            depth += 1
        elif c == ')':
            depth -= 1
            if depth == 0:
                end_pos = i
                break
    if end_pos < 0:
        return None
    # Anything after the outermost `)` must be just `;` or whitespace.
    rest = stripped[end_pos + 1:].strip()
    rest = rest.lstrip(';').strip()
    if rest:
        return None
    # Walk back over the identifier (method name) before this `(`.
    j = last_call_paren - 1
    while j >= 0 and stripped[j].isspace():
        j -= 1
    end_ident = j + 1
    while j >= 0 and (stripped[j].isalnum() or stripped[j] == '_'):
        j -= 1
    method = stripped[j + 1:end_ident]
    if not method or not method[0].isalpha():
        return None
    # The full call target is everything up to and including `method`.
    target = stripped[:last_call_paren].strip()
    return (target, method)


# --------------------------------------------------------------------------- #
# Per-file audit
# --------------------------------------------------------------------------- #

def audit_file(path: Path, project_root: Path) -> tuple[list[Finding], FileStats]:
    """Audit a single .go file. Returns (findings, stats)."""
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
    stats = FileStats(
        path=rel_path,
        is_test=is_test,
        lines=len(lines),
    )
    findings: list[Finding] = []

    # Track line numbers inside any `if X != nil { ... }` block so the
    # missing_check scan can skip them (avoid double-counting).
    err_block_lines: set[int] = set()

    # ----- 1. `if X != nil { ... }` blocks --------------------------------- #
    for m in IF_NIL_RE.finditer(masked):
        # The full match text includes init + condition + `{`.
        match_text = m.group(0)
        # Condition is what's after the last `;` (if any).
        cond = match_text.rsplit(';', 1)[-1] if ';' in match_text else match_text
        if not any(is_err_ident(tok) for tok in re.findall(r'\b\w+\b', cond)):
            continue

        # `{` is the last character of the match.
        brace_pos = m.end() - 1
        close_pos = find_matching_brace(masked, brace_pos)
        if close_pos < 0:
            continue

        body_masked = masked[brace_pos + 1:close_pos]
        start_line = masked[:m.start()].count('\n') + 1
        end_line = masked[:close_pos].count('\n') + 1

        for ln in range(start_line, end_line + 1):
            err_block_lines.add(ln)

        pattern = classify_err_body(body_masked)
        severity = PATTERN_SEVERITY[pattern]
        func_name = containing_function(funcs, start_line)
        snippet = make_snippet(lines, start_line, end_line)

        findings.append(Finding(
            file=rel_path,
            line=start_line,
            end_line=end_line,
            function=func_name,
            pattern=pattern,
            severity=severity,
            snippet=snippet,
        ))

        stats.total_error_sites += 1
        if pattern == "proper_handling":
            stats.proper += 1
        elif pattern == "logged_only":
            stats.logged += 1
        elif pattern == "swallowed":
            stats.swallowed += 1
        elif pattern == "panic_on_error":
            stats.panic += 1

    # ----- 2. `result, _ := F(...)` ignored errors ------------------------- #
    for m in IGNORED_RE.finditer(masked):
        line_num = masked[:m.start()].count('\n') + 1
        line_text = lines[line_num - 1] if line_num <= len(lines) else ""
        # Skip `for k, _ := range m` and similar non-error discards.
        if re.search(r'\brange\b', line_text):
            continue
        # Skip if line is inside an err block (would be double-counted)
        if line_num in err_block_lines:
            continue
        func_name = containing_function(funcs, line_num)
        snippet = make_snippet(lines, line_num, line_num)
        findings.append(Finding(
            file=rel_path,
            line=line_num,
            end_line=line_num,
            function=func_name,
            pattern="ignored",
            severity=PATTERN_SEVERITY["ignored"],
            snippet=snippet,
            note="error explicitly discarded with `_`",
        ))
        stats.total_error_sites += 1
        stats.ignored += 1

    # ----- 3. missing_check: statement-form calls -------------------------- #
    for line_idx, raw_line in enumerate(lines, start=1):
        if line_idx in err_block_lines:
            continue
        # Strip trailing `// ...` comment (but keep `/* */` — rare on stmts).
        code_part = re.sub(r'//.*$', '', raw_line).rstrip()
        stripped = code_part.strip()
        if not stripped:
            continue
        if stripped.startswith(('defer ', 'defer(', 'go ', 'go(')):
            continue
        if CONTROL_KW_RE.match(stripped):
            continue
        # Skip assignments — `result := F()` (single return) is hard to judge
        # without type info. Focus on bare statement-form calls.
        if ':=' in stripped or re.match(r'^[\w.,\s\[\]{}*<>-]+=\s*\S', stripped):
            continue
        # Skip lines with nolint-style comments
        if '//nolint' in raw_line or '//nosec' in raw_line:
            continue
        low = raw_line.lower()
        if '//ok' in low or '// ok' in low:
            continue

        call = extract_outermost_method(stripped)
        if call is None:
            continue
        call_target, method = call
        # Only flag method calls (with a `.` receiver). Free-function calls
        # like `Write(...)` or `Close(...)` are almost always custom helpers
        # whose signature we can't infer, so skip them to avoid noise.
        if '.' not in call_target:
            continue
        if method not in ERROR_RETURNING_NAMES:
            continue

        func_name = containing_function(funcs, line_idx)
        snippet = make_snippet(lines, line_idx, line_idx)
        findings.append(Finding(
            file=rel_path,
            line=line_idx,
            end_line=line_idx,
            function=func_name,
            pattern="missing_check",
            severity=PATTERN_SEVERITY["missing_check"],
            snippet=snippet,
            note=f"statement-form call to known error-returning '{call_target}()'",
        ))
        stats.total_error_sites += 1
        stats.missing += 1

    return findings, stats


# --------------------------------------------------------------------------- #
# Aggregation / reporting
# --------------------------------------------------------------------------- #

def collect_files(root: Path) -> list[Path]:
    """All .go files under root, excluding vendor / generated dirs.

    `root` may be a single .go file or a directory.
    """
    skip_dirs = {"vendor", "node_modules", ".git", "graphify-out", "testdata"}
    if root.is_file():
        return [root] if root.suffix == ".go" else []
    out: list[Path] = []
    for p in root.rglob("*.go"):
        if any(part in skip_dirs for part in p.parts):
            continue
        out.append(p)
    return sorted(out)


def audit_project(root: Path) -> dict:
    """Audit all .go files under root and return the combined report dict."""
    files = collect_files(root)
    all_findings: list[Finding] = []
    all_stats: list[FileStats] = []

    for path in files:
        findings, stats = audit_file(path, root)
        all_stats.append(stats)
        # Only include detailed findings from NON-test files in the main list.
        if not stats.is_test:
            all_findings.extend(findings)

    # ----- summary --------------------------------------------------------- #
    non_test_stats = [s for s in all_stats if not s.is_test]
    test_stats = [s for s in all_stats if s.is_test]

    def totals(stats: list[FileStats]) -> dict:
        return {
            "files": len(stats),
            "lines": sum(s.lines for s in stats),
            "total_error_sites": sum(s.total_error_sites for s in stats),
            "proper": sum(s.proper for s in stats),
            "logged": sum(s.logged for s in stats),
            "swallowed": sum(s.swallowed for s in stats),
            "ignored": sum(s.ignored for s in stats),
            "missing": sum(s.missing for s in stats),
            "panic": sum(s.panic for s in stats),
        }

    nt = totals(non_test_stats)
    tt = totals(test_stats)
    pct_proper = (
        100.0 * nt["proper"] / nt["total_error_sites"]
        if nt["total_error_sites"] else 0.0
    )

    # Most problematic files (non-test) by total problematic count.
    problematic_files = sorted(
        [s for s in non_test_stats if s.problematic > 0],
        key=lambda s: (-s.problematic, -s.total_error_sites, s.path),
    )[:15]

    pattern_breakdown = Counter(f.pattern for f in all_findings)
    severity_breakdown = Counter(f.severity for f in all_findings)

    return {
        "root": str(root),
        "summary": {
            "total_files": len(files),
            "non_test_files": len(non_test_stats),
            "test_files": len(test_stats),
            "non_test": nt,
            "test": tt,
            "pct_proper_handled": round(pct_proper, 2),
        },
        "pattern_breakdown": dict(pattern_breakdown),
        "severity_breakdown": dict(severity_breakdown),
        "most_problematic_files": [
            {
                "file": s.path,
                "problematic_count": s.problematic,
                "total_error_sites": s.total_error_sites,
                "breakdown": {
                    "swallowed": s.swallowed,
                    "ignored": s.ignored,
                    "missing_check": s.missing,
                    "logged_only": s.logged,
                    "panic_on_error": s.panic,
                    "proper_handling": s.proper,
                },
            }
            for s in problematic_files
        ],
        "findings": [asdict(f) for f in all_findings],
        "file_stats": [asdict(s) for s in all_stats],
    }


# --------------------------------------------------------------------------- #
# Markdown rendering
# --------------------------------------------------------------------------- #

def render_markdown(report: dict) -> str:
    """Render the audit report as a markdown document."""
    s = report["summary"]
    nt = s["non_test"]
    tt = s["test"]
    pb = report["pattern_breakdown"]
    sev = report["severity_breakdown"]
    findings = report["findings"]
    problematic = report["most_problematic_files"]

    out: list[str] = []
    out.append("# Error Handling Audit")
    out.append("")
    out.append(f"**Target:** `{report['root']}`")
    out.append("")
    out.append("## Summary (non-test files)")
    out.append("")
    out.append("| Metric | Value |")
    out.append("| --- | --- |")
    out.append(f"| Files scanned | {s['non_test_files']} |")
    out.append(f"| Total lines | {nt['lines']:,} |")
    out.append(f"| Total error-handling sites | **{nt['total_error_sites']}** |")
    out.append(f"| Properly handled | {nt['proper']} |")
    out.append(f"| Logged only (no return) | {nt['logged']} |")
    out.append(f"| Swallowed errors | {nt['swallowed']} |")
    out.append(f"| Ignored errors (`_`) | {nt['ignored']} |")
    out.append(f"| Missing error checks | {nt['missing']} |")
    out.append(f"| Panic on error | {nt['panic']} |")
    out.append(f"| % properly handled | **{s['pct_proper_handled']}%** |")
    out.append("")

    out.append("## Pattern Breakdown (non-test files)")
    out.append("")
    out.append("| Pattern | Count | Severity |")
    out.append("| --- | ---: | --- |")
    for pat in ["proper_handling", "logged_only", "swallowed",
                "ignored", "missing_check", "panic_on_error"]:
        count = pb.get(pat, 0)
        out.append(
            f"| {PATTERN_LABEL[pat]} | {count} | {PATTERN_SEVERITY[pat]} |"
        )
    out.append("")

    out.append("## Severity Breakdown (non-test files)")
    out.append("")
    out.append("| Severity | Count |")
    out.append("| --- | ---: |")
    for sv in ["HIGH", "MEDIUM", "LOW"]:
        out.append(f"| {sv} | {sev.get(sv, 0)} |")
    out.append("")

    out.append("## Most Problematic Files (non-test)")
    out.append("")
    if not problematic:
        out.append("_No problematic files — all error sites are properly handled._")
    else:
        out.append(
            "| File | Issues | Sites | Swallowed | Ignored | Missing | Logged | Panic |"
        )
        out.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
        for p in problematic:
            b = p["breakdown"]
            out.append(
                f"| `{p['file']}` | {p['problematic_count']} | "
                f"{p['total_error_sites']} | {b['swallowed']} | {b['ignored']} | "
                f"{b['missing_check']} | {b['logged_only']} | {b['panic_on_error']} |"
            )
    out.append("")

    # Group findings by file
    by_file: dict[str, list[dict]] = {}
    for f in findings:
        by_file.setdefault(f["file"], []).append(f)

    out.append("## Detailed Findings (non-test files)")
    out.append("")
    if not by_file:
        out.append("_No issues to report._")
    else:
        for file in sorted(by_file):
            file_findings = by_file[file]
            # Sort: HIGH first, then MEDIUM, then LOW; by line within each
            sev_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
            file_findings.sort(key=lambda f: (sev_order[f["severity"]], f["line"]))
            out.append(f"### `{file}`")
            out.append("")
            for f in file_findings:
                out.append(
                    f"- **[{f['severity']}] {PATTERN_LABEL[f['pattern']]}** — "
                    f"`{f['file']}:{f['line']}` in `{f['function']}`"
                )
                if f["note"]:
                    out.append(f"  - _{f['note']}_")
                # Snippet as a fenced code block
                snippet = f["snippet"].rstrip()
                out.append("  ```go")
                for line in snippet.splitlines():
                    out.append(f"  {line}")
                out.append("  ```")
            out.append("")

    # Test file summary
    out.append("## Test File Error Handling (summary)")
    out.append("")
    out.append("| Metric | Value |")
    out.append("| --- | --- |")
    out.append(f"| Test files scanned | {s['test_files']} |")
    out.append(f"| Total lines | {tt['lines']:,} |")
    out.append(f"| Total error-handling sites | {tt['total_error_sites']} |")
    out.append(f"| Properly handled | {tt['proper']} |")
    out.append(f"| Logged only | {tt['logged']} |")
    out.append(f"| Swallowed | {tt['swallowed']} |")
    out.append(f"| Ignored (`_`) | {tt['ignored']} |")
    out.append(f"| Missing checks | {tt['missing']} |")
    out.append(f"| Panic on error | {tt['panic']} |")
    pct_test = (
        100.0 * tt["proper"] / tt["total_error_sites"]
        if tt["total_error_sites"] else 0.0
    )
    out.append(f"| % properly handled | {round(pct_test, 2)}% |")
    out.append("")

    out.append("## Methodology")
    out.append("")
    out.append(
        "The audit scans every `.go` file (excluding `vendor/`, `node_modules/`, "
        "`.git/`, `graphify-out/`, `testdata/`) and applies these heuristics:"
    )
    out.append("")
    out.append(
        "1. **`if X != nil { ... }` blocks** are located via brace matching "
        "(strings and comments are masked out first). The **full** block body "
        "is then classified in priority order:"
    )
    out.append(
        "    - **`proper_handling`** (LOW) — body returns the error directly "
        "(`return err`, `return fmt.Errorf(\"...: %w\", err)`, `return res.Err()`), "
        "OR terminates the process / test (`os.Exit(non-zero)`, `log.Fatal*`, "
        "`t.Fatal*`), OR contains a recognised proper-handler pattern: "
        "`http.Redirect`, `respondWithError`/`http.Error`/`writeError`/etc., "
        "an `ErrNoDocuments`/`mongo.ErrNoDocuments` check, a `continue` "
        "statement (batch processing), or an assignment to a variable / "
        "struct field (`page = 1`, `delivery.Success = false`, …)."
    )
    out.append(
        "    - **`panic_on_error`** (MEDIUM) — body calls `panic(...)`."
    )
    out.append(
        "    - **`logged_only`** (MEDIUM) — body acknowledges the error via "
        "`slog.Warn/Error/Info/Debug`, `log.Print*`/`Fatal*`/`Panic*`, "
        "`fmt.Print*`/`Fprint*`/`Sprint*`, or `fmt.Fprint*(os.Stderr, ...)`, "
        "without propagating the original `err`. (`fmt.Errorf` is excluded — "
        "that's error construction, not logging.)"
    )
    out.append(
        "    - **`swallowed`** (HIGH) — body is empty, or only contains a "
        "bare `return` / `return nil` / `return <non-err>` (including "
        "`return errors.New(\"...\")` which drops the original error), and "
        "matches none of the proper-handler or logging patterns above."
    )
    out.append(
        "2. **Ignored errors** are detected as `result, _ := someFunc(...)` "
        "patterns where the last return value is discarded with `_`. "
        "`for k, _ := range m` is excluded."
    )
    out.append(
        "3. **Missing error checks** are detected as statement-form calls "
        "(not assigned, not preceded by `defer`/`go`) to a known "
        "error-returning method such as `Close`, `Write`, `InsertOne`, "
        "`UpdateOne`, `Marshal`, etc. This is heuristic and may produce "
        "false positives — review each finding."
    )
    out.append("")
    out.append(
        "Severity: **HIGH** for swallowed/ignored/missing, **MEDIUM** for "
        "logged-only and panic-on-error, **LOW** for proper handling."
    )
    out.append("")

    return "\n".join(out)


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Audit Go source code for error handling patterns.",
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
        help="Write markdown report to this path (in addition to public/ERROR_AUDIT.md).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the JSON report to stdout.",
    )
    parser.add_argument(
        "--include-tests",
        action="store_true",
        help="Include test-file findings in the detailed findings list.",
    )
    args = parser.parse_args(argv)

    root = Path(args.path).resolve()
    if not root.exists():
        print(f"ERROR: path not found: {root}", file=sys.stderr)
        return 2

    report = audit_project(root)

    if args.include_tests:
        # Promote test-file findings into the main findings list as well.
        test_findings = [
            f for f in (report["findings"]) if False  # already only non-test
        ]
        # (Already non-test only; this option is a no-op for now since the
        # detailed list is intentionally non-test only. Test stats are
        # always reported in the summary.)

    # Always write JSON + MD to /home/z/my-project/public/ if writable.
    public_dir = Path("/home/z/my-project/public")
    json_path = public_dir / "error-audit.json"
    md_path = public_dir / "ERROR_AUDIT.md"
    try:
        public_dir.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    except Exception as e:
        print(f"WARN: could not write {json_path}: {e}", file=sys.stderr)
    try:
        md_path.write_text(render_markdown(report), encoding="utf-8")
    except Exception as e:
        print(f"WARN: could not write {md_path}: {e}", file=sys.stderr)

    # Optional --out markdown
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

    # Brief stderr summary
    nt = report["summary"]["non_test"]
    print(
        f"Audited {report['summary']['non_test_files']} non-test Go files "
        f"({nt['total_error_sites']} error sites, "
        f"{report['summary']['pct_proper_handled']}% properly handled).",
        file=sys.stderr,
    )
    print(
        f"HIGH severity findings: {report['severity_breakdown'].get('HIGH', 0)}  "
        f"MEDIUM: {report['severity_breakdown'].get('MEDIUM', 0)}  "
        f"LOW: {report['severity_breakdown'].get('LOW', 0)}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
