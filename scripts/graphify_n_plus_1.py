#!/usr/bin/env python3
"""graphify_n_plus_1 — detect MongoDB queries running inside loops (N+1 problems).

Walks every ``.go`` file (excluding ``*_test.go`` unless ``--include-tests``)
under the target path, locates loop bodies (``for ... range ...``,
``for i; cond; post { ... }``, ``for cond { ... }``, ``for { ... }``),
and inspects the body for MongoDB collection operations:

  * Find / FindOne / InsertOne / InsertMany
  * UpdateOne / UpdateMany / ReplaceOne
  * DeleteOne / DeleteMany
  * CountDocuments / EstimatedDocumentCount
  * Aggregate

A query inside a loop body is an N+1 problem: the loop runs N times, and
each iteration hits the database. The standard fix is to batch the IDs and
issue a single ``$in`` query, e.g.::

    // Before (N+1):
    for _, id := range ids {
        user, err := col.FindOne(ctx, bson.M{"_id": id}).Decode(&u)
    }
    // After (single query):
    cur, err := col.Find(ctx, bson.M{"_id": bson.M{"$in": ids}})

For each finding the script records:

  * file, line (loop start), end_line (loop close)
  * loop variable name and loop kind (range / three-form / condition / infinite)
  * the MongoDB operation name (Find, FindOne, ...)
  * the collection name (resolved via ``db.Collection("name")`` literal,
    via the codebase's collection accessor methods like ``m.Users()``, or
    via an aliased local variable like ``col := m.Users()``)
  * the containing function
  * the call line (where the DB op actually appears in the loop body)
  * a code snippet
  * a remediation suggestion
  * risk: HIGH for queries in user-facing handlers; MEDIUM for admin/batch

Usage:
    python graphify_n_plus_1.py [path] [--out report.md] [--json] [--include-tests]

Outputs:
    - JSON written to /home/z/my-project/public/n-plus-1.json (best effort)
    - Markdown written to /home/z/my-project/public/N_PLUS_1.md (best effort)
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

# MongoDB collection methods we treat as queries. Same set as
# graphify_db_queries.py plus ReplaceOne.
OPERATIONS: tuple[str, ...] = (
    "Find",
    "FindOne",
    "InsertOne",
    "InsertMany",
    "UpdateOne",
    "UpdateMany",
    "ReplaceOne",
    "DeleteOne",
    "DeleteMany",
    "Aggregate",
    "CountDocuments",
    "EstimatedDocumentCount",
)

OP_RE = re.compile(
    r"\.(" + "|".join(OPERATIONS) + r")\s*\("
)

# Direct collection access: ``db.Collection("name")``
COLLECTION_LITERAL_RE = re.compile(
    r'\.Collection\(\s*"([^"]+)"\s*\)'
)

# Function declaration: ``func [recv] Name(``
FUNC_DECL_RE = re.compile(
    r'^[ \t]*func(?:[ \t]+\([^)]*\))?[ \t]+(?P<name>\w+)[ \t]*\(',
    re.MULTILINE,
)

# Loop start. Captures the whole ``for ...`` header up to and including the
# opening brace (the brace is consumed so we can find the matching close).
LOOP_HEADER_RE = re.compile(
    r'^[ \t]*for\b(?P<header>[^{;]*)',
    re.MULTILINE,
)

# Detect which kind of loop it is by inspecting the header.
#   for _, x := range items {        -> "range"
#   for i := 0; i < n; i++ {          -> "three-form"
#   for cond {                         -> "condition"
#   for {                              -> "infinite"
#   for k := range m {                 -> "range" (single-var form)
def classify_loop(header: str) -> tuple[str, str]:
    """Return (kind, loop_variable) for a loop header (without `for` or `{`)."""
    h = header.strip()
    if not h:
        return "infinite", "_"
    if "range" in h:
        # forms:
        #   _, x := range items   -> x
        #   k, v := range items   -> k (or both)
        #   x := range items      -> x
        #   for range items       -> (no var) "_"
        m = re.search(r'(?P<lhs>[^=:]*?)\s*(?::=|=)\s*range\b', h)
        if m:
            lhs = m.group("lhs").strip()
            # take the last identifier in the lhs list
            ids = re.findall(r'\b\w+\b', lhs)
            if ids:
                return "range", ids[-1]
            return "range", "_"
        return "range", "_"
    if ";" in h:
        # three-form: init; cond; post
        parts = [p.strip() for p in h.split(";")]
        init = parts[0] if parts else ""
        m = re.search(r'(\w+)\s*(?::=|=)', init)
        if m:
            return "three-form", m.group(1)
        # Could be `i++` or empty
        m2 = re.match(r'(\w+)\s*\+\+', init)
        if m2:
            return "three-form", m2.group(1)
        return "three-form", "_"
    return "condition", "_"


# --------------------------------------------------------------------------- #
# Source masking (so brace matching is safe against strings/comments)
# --------------------------------------------------------------------------- #

def mask_source(src: str) -> str:
    """Replace string literals and comments with spaces (preserving length)."""
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


# --------------------------------------------------------------------------- #
# Data containers
# --------------------------------------------------------------------------- #

@dataclass
class FuncRange:
    name: str
    start_line: int  # 1-indexed
    end_line: int    # 1-indexed


@dataclass
class LoopRange:
    start_line: int
    end_line: int
    kind: str
    loop_var: str


@dataclass
class Finding:
    file: str
    line: int           # loop start line
    end_line: int       # loop close line
    call_line: int      # line where the DB op actually appears
    function: str
    loop_kind: str
    loop_var: str
    operation: str
    collection: str
    snippet: str
    suggestion: str
    severity: str       # HIGH / MEDIUM / LOW
    note: str = ""


# --------------------------------------------------------------------------- #
# Function / loop parsing
# --------------------------------------------------------------------------- #

def parse_functions(masked: str) -> list[FuncRange]:
    """Find named top-level function/method declarations and their body ranges."""
    funcs: list[FuncRange] = []
    for m in FUNC_DECL_RE.finditer(masked):
        # Walk forward from end of match to find the body `{`.
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
            name=m.group("name"),
            start_line=start_line,
            end_line=end_line,
        ))
    return funcs


def containing_function(funcs: list[FuncRange], line: int) -> str:
    """Innermost named function whose body contains ``line``."""
    best: Optional[FuncRange] = None
    best_span: Optional[int] = None
    for f in funcs:
        if f.start_line <= line <= f.end_line:
            span = f.end_line - f.start_line
            if best is None or span < best_span:
                best = f
                best_span = span
    return best.name if best else "<top-level>"


def parse_loops(masked: str) -> list[LoopRange]:
    """Find every loop header and the matching closing brace.

    Returns loops sorted by start_line. The loop body extends from the line
    after the header's `{` to the line of the matching `}`. Nested loops are
    included as separate entries.
    """
    loops: list[LoopRange] = []
    n = len(masked)
    for m in LOOP_HEADER_RE.finditer(masked):
        header_text = m.group("header")
        # Walk forward from end of match to find the body `{`. We must skip
        # over any `;`/`)`/whitespace and (importantly) balance any `(` that
        # appears in the header.
        i = m.end()
        depth_paren = 0
        brace_pos = -1
        while i < n:
            c = masked[i]
            if c == '(':
                depth_paren += 1
            elif c == ')':
                depth_paren -= 1
                if depth_paren < 0:
                    depth_paren = 0
            elif c == '{' and depth_paren == 0:
                brace_pos = i
                break
            elif c == ';' and depth_paren == 0:
                # Three-form for: `for i := 0; i < n; i++ {`
                # The semicolons are part of the header — keep going.
                pass
            elif c == '\n':
                pass
            i += 1
        if brace_pos < 0:
            continue
        close_pos = find_matching_brace(masked, brace_pos)
        if close_pos < 0:
            continue
        start_line = masked[:m.start()].count('\n') + 1
        end_line = masked[:close_pos].count('\n') + 1
        kind, loop_var = classify_loop(header_text)
        loops.append(LoopRange(
            start_line=start_line,
            end_line=end_line,
            kind=kind,
            loop_var=loop_var,
        ))
    loops.sort(key=lambda L: L.start_line)
    return loops


# --------------------------------------------------------------------------- #
# Collection resolution
# --------------------------------------------------------------------------- #

def build_accessor_map(repo_root: Path) -> dict[str, str]:
    """Build {accessor_method_name: collection_name}.

    Scans every .go file for ``func (recv) Name() *mongo.Collection {
    return <expr>.Collection("name") }``.
    """
    accessor_re = re.compile(
        r"func\s+(?:\([^)]*\)\s+)?([A-Z]\w*)\s*\(\s*\)\s*\*mongo\.Collection\s*\{[^}]*?"
        r'\.Collection\(\s*"([^"]+)"\s*\)',
        re.DOTALL,
    )
    accessor_map: dict[str, str] = {}
    for path in repo_root.rglob("*.go"):
        if "graphify-out" in path.parts:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for m in accessor_re.finditer(text):
            name, coll = m.group(1), m.group(2)
            accessor_map.setdefault(name, coll)
    return accessor_map


def resolve_collection(
    line_text: str,
    aliases: dict[str, str],
    accessor_map: dict[str, str],
) -> Optional[str]:
    """Resolve which collection a DB-op call on this line targets.

    Strategy (in order):

      1. literal ``.Collection("name")`` in the prefix
      2. dynamic ``.Collection(<var>)`` (e.g. ``.Collection(name)``) → "dynamic"
      3. accessor call ``<expr>.<Accessor>()`` in the prefix (e.g. ``m.Users()``)
      4. aliased local variable ``<ident>.<Op>`` (e.g. ``col.FindOne(...)``)
    """
    # Strategy 1: literal ``.Collection("name").<Op>``
    lit_m = COLLECTION_LITERAL_RE.search(line_text)
    if lit_m:
        return lit_m.group(1)

    # Strategy 2: dynamic ``.Collection(<var>)``
    dyn_m = re.search(r'\.Collection\(\s*([A-Za-z_]\w*)\s*\)', line_text)
    if dyn_m:
        return f"dynamic:{dyn_m.group(1)}"

    # Strategy 3: accessor call ``<expr>.<Accessor>().<Op>``
    acc_m = re.search(r"([A-Z]\w*)\(\s*\)", line_text)
    if acc_m:
        accessor = acc_m.group(1)
        if accessor in accessor_map:
            return accessor_map[accessor]

    # Strategy 4: aliased variable ``<ident>.<Op>``
    # The OP_RE consumes the ``.`` so look at the identifier right before the op.
    op_m = OP_RE.search(line_text)
    if op_m:
        prefix = line_text[:op_m.start()]
        var_m = re.search(r"([A-Za-z_]\w*)\s*$", prefix.rstrip())
        if var_m:
            var_name = var_m.group(1)
            if var_name in aliases:
                return aliases[var_name]
    return None


def update_aliases_for_line(line_text: str, aliases: dict[str, str],
                            accessor_map: dict[str, str]) -> None:
    """Refresh the alias table from a single line.

    Recognises:
      ``col := <expr>.Collection("name")``
      ``col := <expr>.<Accessor>()``   (when accessor is a known one)
    """
    # literal form
    m = re.search(
        r"(\w+)\s*:?=\s*[\w\.\[\]\*]+\.Collection\(\s*\"([^\"]+)\"\s*\)",
        line_text,
    )
    if m:
        aliases[m.group(1)] = m.group(2)
        return
    # accessor form
    m = re.search(
        r"(\w+)\s*:?=\s*[\w\.\[\]\*]+\.([A-Z]\w*)\(\s*\)",
        line_text,
    )
    if m:
        var_name = m.group(1)
        accessor = m.group(2)
        if accessor in accessor_map:
            # Make sure this isn't a chained call like ``h.db.Users().Find(...)``
            # by checking that the match doesn't end with ``.``.
            end = m.end()
            if end < len(line_text) and line_text[end] == ".":
                return
            aliases[var_name] = accessor_map[accessor]


# --------------------------------------------------------------------------- #
# Risk classification
# --------------------------------------------------------------------------- #

# Heuristic: paths whose file path or function name suggests admin/CLI/batch
# processing get MEDIUM (these are typically not user-facing request loops);
# everything else gets HIGH.
ADMIN_HINTS: tuple[str, ...] = (
    "/admin", "/cmd/", "admin_test", "cmd_", "seed", "migrate", "cleanup",
    "batch", "doctor", "backfill",
)

ADMIN_FUNC_HINTS: tuple[str, ...] = (
    "admin", "seed", "migrate", "cleanup", "backfill", "reconcile",
    "doctor", "batch",
)

# Paths that are always excluded from N+1 analysis — they're either test
# scaffolding (where deleting rows in a loop is the whole point) or CLI
# tooling (where the loop is intentional admin processing, not a
# request-path performance problem).
SKIP_PATH_FRAGMENTS: tuple[str, ...] = (
    "/testutil/", "\\testutil\\",
    "/cmd/lastsaas/", "\\cmd\\lastsaas\\",
    "cmd/lastsaas/", "cmd\\lastsaas\\",
)

# Loop variables whose iteration count is structurally tiny. A loop over a
# user's memberships iterates ~1-5 times (a typical user belongs to a
# handful of tenants); a loop over a tenant's tenants list iterates even
# less. FindOne-by-ID inside such a loop is NOT an N+1 problem in
# practice — flagging it as HIGH creates noise the team learns to ignore.
SMALL_N_LOOP_VARS: frozenset[str] = frozenset({
    "membership", "memberships", "m", "mem",
    "tenant", "tenants", "t",
    "membershipInfo", "membershipInfos",
    "invite", "invitations",
    "member",
})

# Loop variables / range expressions that iterate over collections which
# could grow large (users, logs, transactions, events). Only these stay
# HIGH; everything else with a small-N loop var is downgraded to LOW.
LARGE_N_LOOP_VARS: frozenset[str] = frozenset({
    "user", "users", "u",
    "log", "logs", "logEntry", "logEntries",
    "transaction", "transactions", "txn",
    "event", "events", "evt",
    "delivery", "deliveries",
    "message", "messages",
    "metric", "metrics",
    "record", "records",
    "row", "rows",
    "item", "items",
})


def _is_skipped_path(rel: str) -> bool:
    """True for paths that are explicitly excluded from N+1 analysis
    (test utilities and CLI tools)."""
    rl = rel.lower()
    return any(frag.lower() in rl for frag in SKIP_PATH_FRAGMENTS)


def classify_risk(rel_file: str, function: str,
                  loop_var: str = "_",
                  loop_kind: str = "",
                  collection: str = "") -> str:
    fl = rel_file.lower()
    fn = (function or "").lower()
    lv = (loop_var or "_").lstrip("_").lower() or "_"
    # Test/CLI scaffolding: don't flag at all (these aren't request-path
    # performance problems). The caller may still record the finding but
    # with LOW risk so it doesn't surface in the HIGH/MEDIUM rollups.
    if _is_skipped_path(rel_file):
        return "LOW"
    # Small-N loops over memberships/tenants: N is typically 1-5 — not a
    # real N+1 problem, regardless of whether the surrounding code is an
    # admin path or a user-facing handler. The loop variable is a much
    # stronger signal than the file path, so check it FIRST.
    if lv in SMALL_N_LOOP_VARS:
        return "LOW"
    if any(h in fl for h in ADMIN_HINTS):
        return "MEDIUM"
    if any(h in fn for h in ADMIN_FUNC_HINTS):
        return "MEDIUM"
    # Only flag as HIGH for collections that could actually grow large.
    if lv in LARGE_N_LOOP_VARS:
        return "HIGH"
    # Default: medium (we can't prove the loop is bounded by a tiny N,
    # but we also can't prove it grows unboundedly).
    return "MEDIUM"


# --------------------------------------------------------------------------- #
# Per-file scanner
# --------------------------------------------------------------------------- #

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


def scan_file(
    path: Path,
    repo_root: Path,
    accessor_map: dict[str, str],
) -> list[Finding]:
    try:
        src = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    try:
        rel = str(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        rel = str(path)

    masked = mask_source(src)
    lines = src.splitlines()
    funcs = parse_functions(masked)
    loops = parse_loops(masked)

    findings: list[Finding] = []
    # Aliases are file-scoped (resets per file). We refresh on every line so
    # that an alias defined before the loop is visible inside.
    aliases: dict[str, str] = {}

    # Walk line-by-line, refreshing aliases, then for each line check whether
    # it falls inside any loop body and contains a DB op.
    for idx, raw_line in enumerate(lines, start=1):
        masked_line = masked.splitlines()[idx - 1] if idx - 1 < len(masked.splitlines()) else raw_line
        update_aliases_for_line(raw_line, aliases, accessor_map)

        # Skip option-builder calls like ``options.Find()`` — they're not real
        # queries.
        if re.search(r"\boptions\s*\.\s*(Find|FindOne)\b", raw_line):
            continue

        op_match = OP_RE.search(masked_line)
        if not op_match:
            continue

        # Is this line inside a loop body?
        in_loop: Optional[LoopRange] = None
        for L in loops:
            if L.start_line < idx <= L.end_line:
                # Pick the innermost (smallest) loop containing this line.
                if in_loop is None or (L.end_line - L.start_line) < (in_loop.end_line - in_loop.start_line):
                    in_loop = L
        if in_loop is None:
            continue

        operation = op_match.group(1)
        collection = resolve_collection(raw_line, aliases, accessor_map) or "<unknown>"

        # Slight different suggestion for write operations vs reads.
        if operation in ("Find", "FindOne", "CountDocuments", "Aggregate"):
            suggestion = (
                "Use $in operator with a batch of IDs instead of querying in a loop. "
                "e.g. `col.Find(ctx, bson.M{\"_id\": bson.M{\"$in\": ids}})`"
            )
        elif operation in ("InsertOne",):
            suggestion = (
                "Use InsertMany with a slice of documents instead of InsertOne in a loop."
            )
        elif operation in ("UpdateOne", "ReplaceOne"):
            suggestion = (
                "Use BulkWrite with a []mongo.WriteModel (UpdateOne models) "
                "instead of issuing UpdateOne per iteration."
            )
        elif operation in ("DeleteOne",):
            suggestion = (
                "Use DeleteMany with an $in filter instead of DeleteOne in a loop."
            )
        else:
            suggestion = (
                "Batch this operation — issue a single bulk/multi-document call "
                "instead of one DB call per loop iteration."
            )

        func_name = containing_function(funcs, idx)
        risk = classify_risk(
            rel, func_name,
            loop_var=in_loop.loop_var,
            loop_kind=in_loop.kind,
            collection=collection,
        )

        snippet = make_snippet(lines, in_loop.start_line, in_loop.end_line)

        findings.append(Finding(
            file=rel,
            line=in_loop.start_line,
            end_line=in_loop.end_line,
            call_line=idx,
            function=func_name,
            loop_kind=in_loop.kind,
            loop_var=in_loop.loop_var,
            operation=operation,
            collection=collection,
            snippet=snippet,
            suggestion=suggestion,
            severity=risk,
            note=f"{operation} call inside {in_loop.kind} loop",
        ))

    return findings


# --------------------------------------------------------------------------- #
# Aggregation
# --------------------------------------------------------------------------- #

def collect_files(root: Path, include_tests: bool) -> list[Path]:
    skip_dirs = {"vendor", "node_modules", ".git", "graphify-out", "testdata"}
    if root.is_file():
        return [root] if root.suffix == ".go" else []
    out: list[Path] = []
    for p in root.rglob("*.go"):
        if any(part in skip_dirs for part in p.parts):
            continue
        if not include_tests and p.name.endswith("_test.go"):
            continue
        # Skip test utilities and CLI tools entirely — deleting rows in a
        # loop in test cleanup, or iterating results for CLI display, is
        # intentional and not an N+1 problem.
        rel = str(p)
        if _is_skipped_path(rel):
            continue
        out.append(p)
    return sorted(out)


def build_report(root: Path, findings: list[Finding]) -> dict:
    by_file: dict[str, list[Finding]] = defaultdict(list)
    by_op: Counter = Counter()
    by_collection: Counter = Counter()
    by_severity: Counter = Counter()
    by_kind: Counter = Counter()
    for f in findings:
        by_file[f.file].append(f)
        by_op[f.operation] += 1
        by_collection[f.collection] += 1
        by_severity[f.severity] += 1
        by_kind[f.loop_kind] += 1

    top_files = sorted(
        ({"file": k, "count": len(v)} for k, v in by_file.items()),
        key=lambda d: -d["count"],
    )[:20]

    return {
        "root": str(root),
        "total_findings": len(findings),
        "severity_breakdown": dict(by_severity),
        "operation_breakdown": [
            {"operation": op, "count": c}
            for op, c in by_op.most_common()
        ],
        "collection_breakdown": [
            {"collection": c, "count": n}
            for c, n in by_collection.most_common()
        ],
        "loop_kind_breakdown": [
            {"kind": k, "count": n}
            for k, n in by_kind.most_common()
        ],
        "top_files": top_files,
        "findings": [asdict(f) for f in findings],
    }


# --------------------------------------------------------------------------- #
# Markdown rendering
# --------------------------------------------------------------------------- #

def render_markdown(report: dict) -> str:
    out: list[str] = []
    out.append("# N+1 Query Detection Report")
    out.append("")
    out.append(f"**Target:** `{report['root']}`")
    out.append("")
    out.append(
        "Finds MongoDB queries that run inside loop bodies. Each such query "
        "is an N+1 problem: the loop runs N times, and each iteration hits "
        "the database — N+1 round trips instead of one."
    )
    out.append("")
    out.append("## Summary")
    out.append("")
    out.append("| Metric | Value |")
    out.append("| --- | --- |")
    out.append(f"| Total N+1 findings | **{report['total_findings']}** |")
    for sev in ("HIGH", "MEDIUM", "LOW"):
        out.append(
            f"| {sev} severity | {report['severity_breakdown'].get(sev, 0)} |"
        )
    out.append("")

    out.append("## Operations Involved")
    out.append("")
    out.append("| Operation | Count |")
    out.append("| --- | ---: |")
    for row in report["operation_breakdown"]:
        out.append(f"| `{row['operation']}` | {row['count']} |")
    out.append("")

    out.append("## Collections Affected")
    out.append("")
    out.append("| Collection | Count |")
    out.append("| --- | ---: |")
    for row in report["collection_breakdown"]:
        out.append(f"| `{row['collection']}` | {row['count']} |")
    out.append("")

    out.append("## Loop Kinds")
    out.append("")
    out.append("| Loop kind | Count |")
    out.append("| --- | ---: |")
    for row in report["loop_kind_breakdown"]:
        out.append(f"| `{row['kind']}` | {row['count']} |")
    out.append("")

    out.append("## Files With Most Findings")
    out.append("")
    if not report["top_files"]:
        out.append("_No N+1 queries found._")
    else:
        out.append("| File | Findings |")
        out.append("| --- | ---: |")
        for row in report["top_files"]:
            out.append(f"| `{row['file']}` | {row['count']} |")
    out.append("")

    out.append("## Detailed Findings")
    out.append("")
    findings = report["findings"]
    if not findings:
        out.append("_No N+1 queries found — every database query appears to be issued outside of a loop._")
    else:
        # Group by file, then sort within file by severity then loop start.
        sev_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
        by_file: dict[str, list[dict]] = defaultdict(list)
        for f in findings:
            by_file[f["file"]].append(f)
        for fname in sorted(by_file):
            out.append(f"### `{fname}`")
            out.append("")
            fs = sorted(
                by_file[fname],
                key=lambda f: (sev_order.get(f["severity"], 9), f["line"]),
            )
            for f in fs:
                out.append(
                    f"- **[{f['severity']}] {f['operation']} on `{f['collection']}`**"
                    f" — `{f['file']}:{f['call_line']}` (loop at line {f['line']}, "
                    f"{f['loop_kind']} loop over `{f['loop_var']}`) in `{f['function']}`"
                )
                out.append(f"  - _{f['note']}_")
                out.append(f"  - Suggestion: {f['suggestion']}")
                snippet = f["snippet"].rstrip()
                out.append("  ```go")
                for line in snippet.splitlines():
                    out.append(f"  {line}")
                out.append("  ```")
            out.append("")

    out.append("## Methodology")
    out.append("")
    out.append(
        "1. Each `.go` file is masked (strings/comments blanked out, length and "
        "newlines preserved) so brace-matching is safe."
    )
    out.append(
        "2. Every loop header (`for ... {`) is located and the matching `}` is "
        "found via depth counting. The loop body spans lines `start_line+1` to "
        "`end_line`. Nested loops are recorded separately."
    )
    out.append(
        "3. Every line is scanned for a MongoDB collection method call ("
        + ", ".join(OPERATIONS)
        + "). Option-builder calls like `options.Find()` are skipped."
    )
    out.append(
        "4. For each DB-op line that falls inside a loop body, the collection "
        "is resolved via (a) literal `db.Collection(\"name\")`, (b) an accessor "
        "call like `m.Users()`, or (c) an aliased local variable like "
        "`col := m.Users()`."
    )
    out.append(
        "5. Risk is **HIGH** for queries whose loop iterates over a "
        "potentially-large collection (users, logs, transactions, events, "
        "messages, deliveries). **MEDIUM** for admin/CLI/batch code paths. "
        "**LOW** for loops over small-N collections (memberships, tenants — "
        "N is typically 1-5) and for test/CLI scaffolding that is excluded "
        "from the analysis entirely."
    )
    out.append(
        "6. Test files (`*_test.go`), test utilities (`internal/testutil/`), "
        "and CLI tools (`cmd/lastsaas/`) are skipped entirely — deleting "
        "rows in a loop in test cleanup, or iterating results for CLI "
        "display, is intentional and not an N+1 problem."
    )
    out.append("")
    out.append("---")
    out.append("_Generated by `graphify n-plus-1`._")
    return "\n".join(out)


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="graphify_n_plus_1.py",
        description="Detect N+1 queries: MongoDB calls running inside loops.",
    )
    parser.add_argument(
        "path", nargs="?", default=".",
        help="Root directory to scan (default: current directory).",
    )
    parser.add_argument(
        "--out", default=None,
        help="Write markdown report to this path (in addition to public/N_PLUS_1.md).",
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Print the JSON report to stdout.",
    )
    parser.add_argument(
        "--include-tests", action="store_true",
        help="Include *_test.go files in the scan (default: skipped).",
    )
    args = parser.parse_args(argv)

    root = Path(args.path).resolve()
    if not root.exists():
        print(f"ERROR: path not found: {root}", file=sys.stderr)
        return 2

    accessor_map = build_accessor_map(root)

    findings: list[Finding] = []
    files = collect_files(root, args.include_tests)
    for path in files:
        try:
            file_findings = scan_file(path, root, accessor_map)
        except Exception as e:
            print(f"WARN: failed to scan {path}: {e}", file=sys.stderr)
            continue
        findings.extend(file_findings)

    report = build_report(root, findings)

    # Always write JSON + MD to /home/z/my-project/public/ if writable.
    public_dir = Path("/home/z/my-project/public")
    json_path = public_dir / "n-plus-1.json"
    md_path = public_dir / "N_PLUS_1.md"
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
        f"Scanned {len(files)} Go files; found {len(findings)} N+1 findings "
        f"(HIGH={report['severity_breakdown'].get('HIGH', 0)}, "
        f"MEDIUM={report['severity_breakdown'].get('MEDIUM', 0)}, "
        f"LOW={report['severity_breakdown'].get('LOW', 0)}).",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
