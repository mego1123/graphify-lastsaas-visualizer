#!/usr/bin/env python3
"""graphify_context_check — verify MongoDB operations receive proper context.

Walks every ``.go`` file under the target path, identifies MongoDB query
calls (``Find`` / ``FindOne`` / ``InsertOne`` / ``UpdateOne`` / ``DeleteOne``
/ ``Aggregate`` / ``CountDocuments`` and friends), and inspects the first
positional argument (the ``context.Context`` parameter).

A DB operation that receives ``context.Background()`` or ``context.TODO()``
instead of a request-derived context (``ctx`` / ``r.Context()`` /
``context.WithTimeout(ctx, ...)``) cannot be cancelled when the client
disconnects — the operation runs until completion even if the user aborted
the request.

Risk classification:

  * ``HIGH`` — ``context.Background()`` / ``context.TODO()`` used inside a
    function whose signature marks it as an HTTP handler (i.e. it takes
    ``http.ResponseWriter`` and ``*http.Request``).
  * ``LOW``  — ``context.Background()`` / ``context.TODO()`` used inside a
    non-HTTP function (background goroutine, CLI command, startup code,
    constructor, test helper). ``context.Background()`` is appropriate in
    these contexts.
  * Proper-context calls (``ctx``, ``r.Context()``,
    ``context.WithTimeout(ctx, ...)``, ``context.WithCancel(ctx, ...)``)
    are NOT flagged as findings; their totals appear in the summary.

Usage:
    python graphify_context_check.py [path] [--out report.md] [--json]

Outputs:
    - JSON written to /home/z/my-project/public/context-check.json (best effort)
    - Markdown written to /home/z/my-project/public/CONTEXT_CHECK.md (best effort)
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

# MongoDB collection methods that take a context.Context as the first arg.
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
    # Cursor operations
    "Next",
    "TryNext",
    "All",
    "Close",
    "Decode",
    # Session/transaction operations
    "WithTransaction",
    "StartTransaction",
    "CommitTransaction",
    "AbortTransaction",
    # Database / collection admin
    "Drop",
    "CreateCollection",
    "CreateIndex",
    "Indexes",
    "Ping",
    "Disconnect",
    "Connect",
    "ListDatabaseNames",
    "ListCollections",
    # Index view operations
    "CreateOne",
    "CreateMany",
    "DropOne",
    "DropAll",
    "List",
)

# Pattern matching a MongoDB method call.
OP_CALL_RE = re.compile(
    r"\.(" + "|".join(OPERATIONS) + r")\s*\("
)

# Function declaration: ``func [recv] Name(args) (rets) {``.
FUNC_DECL_RE = re.compile(
    r"^[ \t]*func(?:[ \t]+\([^)]*\))?[ \t]+(?P<name>\w+)[ \t]*\(",
    re.MULTILINE,
)

# Improper context expressions.
IMPROPER_CTX_RE = re.compile(
    r"\bcontext\.(?:Background|TODO)\s*\(\s*\)"
)

# Proper context expressions — if the first arg matches one of these, the
# call is OK.
PROPER_CTX_PATTERNS = [
    re.compile(r"^\s*r\.Context\s*\(\s*\)\s*[,)]"),
    re.compile(r"^\s*ctx\s*[,)]"),
    re.compile(r"^\s*request\.Context\s*\(\s*\)\s*[,)]"),
    re.compile(r"^\s*req\.Context\s*\(\s*\)\s*[,)]"),
    # ``context.WithTimeout(ctx, ...)``, ``context.WithCancel(ctx, ...)``,
    # ``context.WithDeadline(ctx, ...)``, ``context.WithValue(ctx, ...)``.
    re.compile(r"^\s*context\.With(?:Timeout|Cancel|Deadline|Value)\s*\("),
    # ``context.TODO()`` is also improper, but we flag it separately.
    # ``sc`` (session context from WithTransaction) — proper.
    re.compile(r"^\s*sc\s*[,)]"),
    # ``txnCtx`` — common name for transaction context.
    re.compile(r"^\s*txnCtx\s*[,)]"),
]

# HTTP handler signature detection — does the function signature contain
# both ``http.ResponseWriter`` and ``*http.Request``?
HTTP_HANDLER_SIG_RE = re.compile(
    r"http\..ResponseWriter.*?\*http\.Request"
    r"|\*http\.Request.*?http\.Writer",
)

# Goroutine detection — is the call inside a ``go func() { ... }()`` block?
GO_FUNC_RE = re.compile(r"\bgo\s+func\s*\([^)]*\)\s*\{")

# Skip directories.
SKIP_DIRS = {"vendor", "node_modules", ".git", "graphify-out", "testdata"}

RISK_HIGH = "HIGH"
RISK_LOW = "LOW"


# --------------------------------------------------------------------------- #
# Data classes
# --------------------------------------------------------------------------- #

@dataclass
class Finding:
    file: str
    line: int
    end_line: int
    function: str
    operation: str
    context_used: str           # the actual first-arg expression
    is_http_handler: bool
    in_goroutine: bool
    risk: str
    snippet: str
    note: str = ""


@dataclass
class FileStats:
    path: str
    is_test: bool
    lines: int = 0
    operations_scanned: int = 0
    proper_context: int = 0
    improper_context: int = 0
    findings: int = 0


@dataclass
class FuncRange:
    name: str
    start_line: int
    end_line: int
    start_offset: int
    end_offset: int
    signature: str   # the function signature text (params)
    is_http_handler: bool


# --------------------------------------------------------------------------- #
# Source masking
# --------------------------------------------------------------------------- #

def mask_source(src: str) -> str:
    """Replace string literals and comments with spaces (length-preserving)."""
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


def parse_functions(masked: str, src: str) -> list[FuncRange]:
    """Find named top-level function/method declarations and their body ranges.

    Also extracts the function signature (the ``(...)`` parameter list) so
    we can detect HTTP handlers.
    """
    funcs: list[FuncRange] = []
    for m in FUNC_DECL_RE.finditer(masked):
        name = m.group('name')
        # The signature paren starts at m.end() - 1.
        sig_open = m.end() - 1
        sig_close = find_matching_paren(masked, sig_open)
        if sig_close < 0:
            continue
        sig_text = src[sig_open + 1:sig_close]
        # Find the body brace (after the signature).
        i = sig_close + 1
        n = len(masked)
        brace_pos = -1
        while i < n:
            c = masked[i]
            if c == '{':
                brace_pos = i
                break
            # Skip return types, whitespace, etc. — anything but `{`.
            i += 1
        if brace_pos < 0:
            continue
        close_pos = find_matching_brace(masked, brace_pos)
        if close_pos < 0:
            continue
        start_line = masked[:m.start()].count('\n') + 1
        end_line = masked[:close_pos].count('\n') + 1
        is_handler = bool(HTTP_HANDLER_SIG_RE.search(sig_text))
        funcs.append(FuncRange(
            name=name,
            start_line=start_line,
            end_line=end_line,
            start_offset=m.start(),
            end_offset=close_pos,
            signature=sig_text,
            is_http_handler=is_handler,
        ))
    return funcs


def make_snippet(lines: list[str], start: int, end: int, max_lines: int = 6) -> str:
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


def _read_balanced_arg(masked: str, open_paren_pos: int) -> tuple[str, int, int]:
    """Read the first top-level argument of a call.

    Returns ``(arg_text_masked, start_offset, end_offset)`` where the
    offsets are positions in ``masked`` (start is the first non-whitespace
    char of the arg, end is one past the last).
    """
    n = len(masked)
    i = open_paren_pos + 1
    # Skip leading whitespace.
    while i < n and masked[i] in ' \t\r\n':
        i += 1
    start = i
    depth_paren = 0
    depth_bracket = 0
    depth_brace = 0
    while i < n:
        c = masked[i]
        if c == '(':
            depth_paren += 1
        elif c == ')':
            if depth_paren == 0 and depth_bracket == 0 and depth_brace == 0:
                # End of call.
                end = i
                # Trim trailing whitespace.
                while end > start and masked[end - 1] in ' \t\r\n':
                    end -= 1
                return masked[start:end], start, end
            if depth_paren > 0:
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
            end = i
            while end > start and masked[end - 1] in ' \t\r\n':
                end -= 1
            return masked[start:end], start, end
        i += 1
    return "", start, n


def _in_goroutine(masked: str, offset: int) -> bool:
    """Check if the offset is inside a ``go func() { ... }()`` block."""
    # Walk backward to find the enclosing ``go func() {``.
    depth = 0
    i = offset - 1
    while i >= 0:
        c = masked[i]
        if c == '}':
            depth += 1
        elif c == '{':
            if depth == 0:
                # This is the enclosing block's opening brace.
                # Look backward for ``go func``.
                head = masked[max(0, i - 200):i]
                if re.search(r"\bgo\s+func\s*\([^)]*\)\s*$", head):
                    return True
                # Not a goroutine — keep walking backward to find the
                # next outer block.
                return False
            else:
                depth -= 1
        i -= 1
    return False


# --------------------------------------------------------------------------- #
# Per-file scan
# --------------------------------------------------------------------------- #

def is_proper_context(arg_masked: str) -> bool:
    """Does the first-arg expression represent a proper request-derived context?"""
    for pat in PROPER_CTX_PATTERNS:
        if pat.match(arg_masked):
            return True
    return False


def is_improper_context(arg_masked: str) -> bool:
    """Does the first-arg expression use context.Background() / context.TODO()?"""
    return bool(IMPROPER_CTX_RE.search(arg_masked))


def scan_file(path: Path, project_root: Path) -> tuple[list[Finding], FileStats]:
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
    funcs = parse_functions(masked, src)

    findings: list[Finding] = []
    ops_scanned = 0
    proper_count = 0
    improper_count = 0

    # Build a sorted list of function ranges for containment lookup.
    for f in funcs:
        func_masked = masked[f.start_offset:f.end_offset + 1]
        func_src = src[f.start_offset:f.end_offset + 1]
        for m in OP_CALL_RE.finditer(func_masked):
            op = m.group(1)
            open_paren = m.end() - 1
            # Translate to absolute offset in the file.
            abs_open_paren = f.start_offset + open_paren
            close_paren = find_matching_paren(masked, abs_open_paren)
            if close_paren < 0:
                continue
            # Read the first argument.
            arg_masked, arg_start, arg_end = _read_balanced_arg(masked, abs_open_paren)
            if not arg_masked:
                continue
            arg_src = src[arg_start:arg_end]
            ops_scanned += 1
            call_line = _line_of(masked, abs_open_paren)
            call_end_line = _line_of(masked, close_paren)
            snippet = make_snippet(lines, call_line, call_end_line, max_lines=6)

            if is_proper_context(arg_masked):
                proper_count += 1
                continue
            if not is_improper_context(arg_masked):
                # Neither proper nor improper — skip (could be a custom
                # context variable, a method receiver, etc.). Count as
                # proper for stats purposes (no finding emitted).
                proper_count += 1
                continue
            # Improper context.
            improper_count += 1
            # Determine if the call is inside a goroutine within the
            # containing function.
            in_goro = _in_goroutine(masked, abs_open_paren)
            # Risk classification.
            if f.is_http_handler and not in_goro:
                risk = RISK_HIGH
                note = (
                    f"HTTP handler '{f.name}' uses {arg_src.strip()} for a "
                    "DB operation — the operation cannot be cancelled if "
                    "the client disconnects. Use r.Context() (or a derived "
                    "context.WithTimeout(r.Context(), ...)) instead."
                )
            else:
                risk = RISK_LOW
                if in_goro:
                    note = (
                        f"DB operation in goroutine inside '{f.name}' uses "
                        f"{arg_src.strip()}. This is acceptable for "
                        "background work that should outlive the request, "
                        "but ensure a timeout is set via "
                        "context.WithTimeout(context.Background(), ...)."
                    )
                else:
                    note = (
                        f"DB operation in non-HTTP function '{f.name}' "
                        f"uses {arg_src.strip()}. Acceptable for CLI "
                        "commands, startup code, and constructors."
                    )
            findings.append(Finding(
                file=rel_path,
                line=call_line,
                end_line=call_line,
                function=f.name,
                operation=op,
                context_used=arg_src.strip(),
                is_http_handler=f.is_http_handler,
                in_goroutine=in_goro,
                risk=risk,
                snippet=snippet,
                note=note,
            ))

    stats = FileStats(
        path=rel_path,
        is_test=is_test,
        lines=len(lines),
        operations_scanned=ops_scanned,
        proper_context=proper_count,
        improper_context=improper_count,
        findings=len(findings),
    )
    return findings, stats


# --------------------------------------------------------------------------- #
# Aggregation
# --------------------------------------------------------------------------- #

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
    all_findings: list[Finding] = []
    all_stats: list[FileStats] = []
    for path in files:
        findings, stats = scan_file(path, root)
        all_stats.append(stats)
        if not stats.is_test:
            all_findings.extend(findings)

    non_test_stats = [s for s in all_stats if not s.is_test]
    test_stats = [s for s in all_stats if s.is_test]

    risk_counts = Counter(f.risk for f in all_findings)
    # Only HIGH findings are real risks; LOW is informational.
    risky_findings = [f for f in all_findings if f.risk == RISK_HIGH]

    by_file: dict[str, dict] = defaultdict(lambda: {
        "operations": 0, "proper": 0, "improper": 0, "findings": 0,
        "high": 0, "low": 0,
    })
    for s in non_test_stats:
        by_file[s.path]["operations"] += s.operations_scanned
        by_file[s.path]["proper"] += s.proper_context
        by_file[s.path]["improper"] += s.improper_context
    for f in all_findings:
        by_file[f.file]["findings"] += 1
        rk = f.risk.lower()
        if rk in by_file[f.file]:
            by_file[f.file][rk] += 1

    top_files = sorted(
        by_file.items(),
        key=lambda kv: (-kv[1]["high"], -kv[1]["improper"], kv[0]),
    )[:25]

    op_counts = Counter(f.operation for f in all_findings)
    ctx_counts = Counter(f.context_used for f in all_findings)

    return {
        "root": str(root),
        "summary": {
            "total_files": len(files),
            "non_test_files": len(non_test_stats),
            "test_files": len(test_stats),
            "non_test_lines": sum(s.lines for s in non_test_stats),
            "test_lines": sum(s.lines for s in test_stats),
            "operations_scanned": sum(s.operations_scanned for s in non_test_stats),
            "proper_context": sum(s.proper_context for s in non_test_stats),
            "improper_context": sum(s.improper_context for s in non_test_stats),
            "total_findings": len(all_findings),
            "high_risk_findings": len(risky_findings),
            "low_risk_findings": risk_counts.get(RISK_LOW, 0),
            "by_risk": {
                "HIGH": risk_counts.get(RISK_HIGH, 0),
                "LOW":  risk_counts.get(RISK_LOW, 0),
            },
            "test": {
                "operations_scanned": sum(s.operations_scanned for s in test_stats),
                "proper_context": sum(s.proper_context for s in test_stats),
                "improper_context": sum(s.improper_context for s in test_stats),
            },
        },
        "top_files": [
            {"file": f, **stats} for f, stats in top_files
        ],
        "by_operation": dict(op_counts),
        "by_context_used": dict(ctx_counts),
        "findings": [asdict(f) for f in all_findings],
        "file_stats": [asdict(s) for s in all_stats],
    }


# --------------------------------------------------------------------------- #
# Markdown rendering
# --------------------------------------------------------------------------- #

def render_markdown(report: dict) -> str:
    s = report["summary"]
    by_risk = s["by_risk"]
    by_op = report["by_operation"]
    by_ctx = report["by_context_used"]
    findings = report["findings"]
    top_files = report["top_files"]

    out: list[str] = []
    out.append("# Context Propagation Audit")
    out.append("")
    out.append(f"**Target:** `{report['root']}`")
    out.append("")
    out.append("## Summary (non-test files)")
    out.append("")
    out.append("| Metric | Value |")
    out.append("| --- | ---: |")
    out.append(f"| Files scanned | {s['non_test_files']} |")
    out.append(f"| Total lines | {s['non_test_lines']:,} |")
    out.append(f"| MongoDB operations scanned | **{s['operations_scanned']}** |")
    out.append(f"| Proper context (ctx / r.Context() / WithTimeout) | {s['proper_context']} |")
    out.append(f"| Improper context (context.Background / TODO) | **{s['improper_context']}** |")
    out.append(f"| Total findings | {s['total_findings']} |")
    out.append(f"| HIGH risk (in HTTP handlers) | **{s['high_risk_findings']}** |")
    out.append(f"| LOW risk (background / CLI / goroutine) | {s['low_risk_findings']} |")
    out.append("")

    out.append("### Findings by risk")
    out.append("")
    out.append("| Risk | Count | Meaning |")
    out.append("| --- | ---: | --- |")
    out.append(f"| HIGH | {by_risk['HIGH']} | `context.Background()`/`TODO()` in HTTP handler — op can't be cancelled on client disconnect |")
    out.append(f"| LOW | {by_risk['LOW']} | `context.Background()`/`TODO()` in non-HTTP code (CLI, startup, goroutine) — acceptable |")
    out.append("")

    if by_op:
        out.append("### Improper-context calls by operation")
        out.append("")
        out.append("| Operation | Count |")
        out.append("| --- | ---: |")
        for op, n in sorted(by_op.items(), key=lambda kv: -kv[1]):
            out.append(f"| `{op}` | {n} |")
        out.append("")

    if by_ctx:
        out.append("### Improper context expressions used")
        out.append("")
        out.append("| Expression | Count |")
        out.append("| --- | ---: |")
        for ctx_expr, n in sorted(by_ctx.items(), key=lambda kv: -kv[1]):
            out.append(f"| `{ctx_expr}` | {n} |")
        out.append("")

    out.append("## Top Files by Improper Context Usage")
    out.append("")
    if not top_files:
        out.append("_No files with findings._")
    else:
        out.append("| File | Operations | Proper | Improper | HIGH | LOW |")
        out.append("| --- | ---: | ---: | ---: | ---: | ---: |")
        for f in top_files:
            st = f
            out.append(
                f"| `{f['file']}` | {st['operations']} | {st['proper']} | "
                f"{st['improper']} | {st['high']} | {st['low']} |"
            )
    out.append("")

    by_file: dict[str, list[dict]] = {}
    for f in findings:
        by_file.setdefault(f["file"], []).append(f)

    out.append("## Detailed Findings")
    out.append("")
    if not by_file:
        out.append("_No improper context usage detected — all MongoDB operations receive a request-derived context._")
    else:
        sev_order = {"HIGH": 0, "LOW": 1}
        for file in sorted(by_file):
            file_findings = by_file[file]
            file_findings.sort(
                key=lambda f: (sev_order.get(f["risk"], 2), f["line"])
            )
            out.append(f"### `{file}`")
            out.append("")
            for f in file_findings:
                out.append(
                    f"- **[{f['risk']}] {f['operation']}** — "
                    f"`{f['file']}:{f['line']}` in `{f['function']}`"
                )
                out.append(f"  - **Context used:** `{f['context_used']}`")
                tags = []
                if f["is_http_handler"]:
                    tags.append("HTTP handler")
                if f["in_goroutine"]:
                    tags.append("in goroutine")
                if tags:
                    out.append(f"  - **Context:** {', '.join(tags)}")
                if f["note"]:
                    out.append(f"  - _{f['note']}_")
                snippet = f["snippet"].rstrip()
                out.append("  ```go")
                for line in snippet.splitlines():
                    out.append(f"  {line}")
                out.append("  ```")
            out.append("")

    out.append("## Test File Context Usage (summary)")
    out.append("")
    out.append("| Metric | Value |")
    out.append("| --- | --- |")
    out.append(f"| Test files scanned | {s['test_files']} |")
    out.append(f"| Total lines | {s['test_lines']:,} |")
    out.append(f"| MongoDB operations scanned | {s['test']['operations_scanned']} |")
    out.append(f"| Proper context | {s['test']['proper_context']} |")
    out.append(f"| Improper context | {s['test']['improper_context']} |")
    out.append("")
    out.append(
        "_Test files are scanned for completeness but their findings are "
        "not included in the detailed list — `context.Background()` in a "
        "test is appropriate (no real HTTP request to cancel)._"
    )
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
        "1. **Function detection.** Each top-level function/method is "
        "located via brace matching on a masked source (strings/comments "
        "blanked). The function signature (the ``(...)`` parameter list) "
        "is extracted and checked for the ``http.ResponseWriter`` + "
        "``*http.Request`` pair — if both are present, the function is "
        "classified as an HTTP handler."
    )
    out.append(
        "2. **MongoDB operation detection.** Every call to a known "
        "mongo-driver method (``Find``, ``FindOne``, ``InsertOne``, "
        "``UpdateOne``, ``DeleteOne``, ``Aggregate``, ``CountDocuments``, "
        "``UpdateByID``, cursor ops like ``Close`` / ``All`` / ``Next``, "
        "session ops like ``WithTransaction``, etc.) is located via "
        "paren matching."
    )
    out.append(
        "3. **First-arg inspection.** The first positional argument "
        "(the ``context.Context`` parameter) is extracted. It is classified "
        "as **proper** if it matches ``ctx``, ``r.Context()``, "
        "``context.WithTimeout(ctx, ...)``, ``context.WithCancel(ctx, ...)``, "
        "``context.WithDeadline(ctx, ...)``, ``context.WithValue(ctx, ...)``, "
        "``sc`` (session context), or ``txnCtx``. It is **improper** if it "
        "contains ``context.Background()`` or ``context.TODO()``."
    )
    out.append(
        "4. **Goroutine detection.** For each improper-context call, the "
        "scanner walks backward to check whether the call is inside a "
        "``go func() { ... }()`` block. If so, the call is treated as a "
        "background operation (LOW risk) regardless of the containing "
        "function's signature."
    )
    out.append(
        "5. **Risk classification.** ``HIGH`` for ``context.Background()`` "
        "or ``context.TODO()`` in an HTTP handler function (not in a "
        "goroutine) — the DB operation will run to completion even if the "
        "client disconnects. ``LOW`` for the same patterns in non-handler "
        "functions (CLI commands, startup code, constructors, background "
        "goroutines) where ``context.Background()`` is appropriate."
    )
    out.append("")
    out.append(
        "**Why this matters:** when a client cancels an HTTP request, Go's "
        "``net/http`` package cancels the request's context. Any DB "
        "operation that receives ``r.Context()`` (or a derivative) will be "
        "cancelled, freeing the DB connection promptly. Operations that "
        "receive ``context.Background()`` are *not* cancelled — they run to "
        "completion, consuming a connection and CPU until the DB returns. "
        "In high-load scenarios, this can exhaust the connection pool."
    )
    out.append("")
    return "\n".join(out)


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Verify MongoDB operations in Go source receive proper context.",
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
        help="Write markdown report to this path (in addition to public/CONTEXT_CHECK.md).",
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
    json_path = public_dir / "context-check.json"
    md_path = public_dir / "CONTEXT_CHECK.md"
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

    s = report["summary"]
    print(
        f"Scanned {s['non_test_files']} non-test Go files "
        f"({s['operations_scanned']} MongoDB operations).",
        file=sys.stderr,
    )
    print(
        f"Proper context: {s['proper_context']}  "
        f"Improper: {s['improper_context']}  "
        f"HIGH: {s['high_risk_findings']}  "
        f"LOW: {s['low_risk_findings']}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
