#!/usr/bin/env python3
"""graphify_goroutines — detect potential goroutine leaks in Go source code.

Walks a Go codebase, finds every `go func()` and `go someFunc()` launch site,
and analyses the goroutine body for the five leak-prevention signals:

  1. Context usage       — receives or uses a `context.Context`
  2. Done channel        — `<-ctx.Done()` or `<-done` channel receive inside
  3. WaitGroup           — paired `wg.Add(1)` + `wg.Done()`
  4. Timeout / Deadline  — `context.WithTimeout` or `context.WithDeadline`
  5. Panic recovery      — `defer recover()` or `recover()` somewhere in body

Each goroutine is then classified:

  SAFE       — has context cancellation OR WaitGroup
  RISKY      — no context, no WaitGroup, no timeout (may run forever)
  DANGEROUS  — no context, no WaitGroup, no timeout, AND no panic recovery

Usage:
  python graphify_goroutines.py [path] [--out report.md] [--json] [--include-tests]

Default target: /home/z/my-project/repos/lastsaas/backend
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional


# --------------------------------------------------------------------------- #
# Data model
# --------------------------------------------------------------------------- #

@dataclass
class GoroutineFinding:
    file: str
    line: int
    column: int
    enclosing_function: str
    launch_kind: str            # "func_literal" | "func_call"
    launch_text: str            # the literal `go ...` statement (truncated)
    purpose: str                # heuristic description
    has_context: bool
    has_done_channel: bool
    has_waitgroup: bool
    has_timeout: bool
    has_recover: bool
    risk_level: str             # "SAFE" | "RISKY" | "DANGEROUS"
    signals: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    is_test_file: bool = False
    body_preview: str = ""      # first ~12 lines of the goroutine body


# --------------------------------------------------------------------------- #
# Go-aware text scanning
# --------------------------------------------------------------------------- #

# Matches: `go func(`, `go func(ctx,`
RE_GO_FUNC = re.compile(r"\bgo\s+func\s*\(")
# Matches: `go someFunc(`, `go pkg.Func(`, `go obj.method(`
RE_GO_CALL = re.compile(r"\bgo\s+([A-Za-z_][\w.]*)\s*\(")

# Pattern detectors (applied to the goroutine body, sometimes to a
# small pre-window for WaitGroup.Add).
RE_CONTEXT_PARAM = re.compile(
    r"\b(?:ctx|context)\s+\w*\.?Context|\bcontext\.Background|"
    r"\bcontext\.TODO|\bcontext\.With",
    re.IGNORECASE,
)
RE_CTX_DONE = re.compile(r"<-\s*\w+\.Done\s*\(\s*\)")
# Match `<-done`, `<-stop`, `<-quit` etc., optionally with a receiver prefix
# (`<-s.stop`, `<-rl.done`, `<-srv.quit`).
RE_DONE_CHAN = re.compile(
    r"<-\s*(?:\w+\.)?(done|stop|stopCh|doneCh|quit|exit|cancelCh|halting|halt)\b"
)
RE_WG_ADD = re.compile(r"\b(\w+)\.Add\s*\(\s*\d")
RE_WG_DONE = re.compile(r"\b(\w+)\.Done\s*\(\s*\)")
RE_TIMEOUT = re.compile(r"context\.With(?:Timeout|Deadline|Cancel)\b")
RE_RECOVER = re.compile(r"\brecover\s*\(\s*\)")

# Enclosing function header. Catches both `func Name(...)` and
# `func (recv) Name(...)` and `func (recv *T) Name(...)`.
RE_FUNC_HEADER = re.compile(
    r"\bfunc\s+(?:\([^)]*\)\s+)?([A-Za-z_]\w*)\s*\("
)


def strip_go_comments(src: str) -> str:
    """Remove // line comments and /* */ block comments.

    We keep newlines so line numbers are preserved.
    """
    out_chars: list[str] = []
    i = 0
    n = len(src)
    in_string = False      # "..."
    in_raw_string = False  # `...`
    in_rune = False        # '...'
    while i < n:
        c = src[i]
        nxt = src[i + 1] if i + 1 < n else ""
        if in_string:
            out_chars.append(c)
            if c == "\\" and i + 1 < n:
                out_chars.append(nxt)
                i += 2
                continue
            if c == '"':
                in_string = False
            i += 1
            continue
        if in_raw_string:
            out_chars.append(c)
            if c == "`":
                in_raw_string = False
            i += 1
            continue
        if in_rune:
            out_chars.append(c)
            if c == "\\" and i + 1 < n:
                out_chars.append(nxt)
                i += 2
                continue
            if c == "'":
                in_rune = False
            i += 1
            continue
        # Not inside any literal.
        if c == '"':
            in_string = True
            out_chars.append(c)
            i += 1
            continue
        if c == "`":
            in_raw_string = True
            out_chars.append(c)
            i += 1
            continue
        if c == "'":
            in_rune = True
            out_chars.append(c)
            i += 1
            continue
        if c == "/" and nxt == "/":
            # line comment — consume to end of line, preserve newline
            while i < n and src[i] != "\n":
                i += 1
            continue
        if c == "/" and nxt == "*":
            # block comment — consume to */, preserve newlines
            i += 2
            while i < n - 1 and not (src[i] == "*" and src[i + 1] == "/"):
                if src[i] == "\n":
                    out_chars.append("\n")
                i += 1
            i += 2  # skip */
            continue
        out_chars.append(c)
        i += 1
    return "".join(out_chars)


def line_of_offset(src: str, offset: int) -> int:
    """1-based line number for a character offset."""
    return src.count("\n", 0, offset) + 1


def find_matching_brace(src: str, open_idx: int) -> int:
    """Given index of `{`, return index of matching `}`.

    Handles strings/runes/comments conservatively by reusing strip_go_comments
    on the slice after the brace. Returns -1 if unbalanced.
    """
    depth = 0
    i = open_idx
    n = len(src)
    # We strip comments/strings from the slice starting at open_idx to avoid
    # braces inside literals confusing the matcher.
    cleaned = strip_go_comments(src[open_idx:])
    j = 0
    m = len(cleaned)
    while j < m:
        c = cleaned[j]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return open_idx + j
        j += 1
    return -1


def extract_func_literal_body(src: str, go_idx: int) -> tuple[str, int, int]:
    """For `go func(...) { ... }`, return (body_text, body_start_idx, body_end_idx).

    body_text is the content between the outermost braces (exclusive).
    Returns ("", -1, -1) if the body cannot be extracted.
    """
    # find the `func(` after `go `
    m = RE_GO_FUNC.match(src, go_idx)
    if not m:
        return "", -1, -1
    # walk forward to the matching `{` that opens the body, skipping the
    # parameter list (and any return-type clause) which is wrapped in ()
    i = m.end()  # just past `func(`
    depth_paren = 1
    n = len(src)
    while i < n and depth_paren > 0:
        c = src[i]
        if c == "(":
            depth_paren += 1
        elif c == ")":
            depth_paren -= 1
        i += 1
    # i is now just past the closing `)` of the param list. Skip whitespace
    # and an optional return-type clause. The body starts at the first `{`.
    while i < n and src[i] != "{":
        # bail if we hit a newline-block or semicolon without finding `{`
        if src[i] == ";" or (src[i] == "\n" and "{" not in src[i:i + 200]):
            # keep scanning a bit further; func literal always has a `{`
            pass
        i += 1
    if i >= n:
        return "", -1, -1
    open_brace = i
    close_brace = find_matching_brace(src, open_brace)
    if close_brace == -1:
        return "", -1, -1
    body = src[open_brace + 1:close_brace]
    return body, open_brace + 1, close_brace


def resolve_named_function_body(
    src: str, cleaned_src: str, func_name: str
) -> Optional[tuple[str, int, int]]:
    """Look for `func Name(` or `func (recv) Name(` in the same file.

    Returns (body, body_start, body_end) or None.
    """
    pattern = re.compile(
        r"\bfunc\s+(?:\([^)]*\)\s+)?" + re.escape(func_name) + r"\s*\("
    )
    m = pattern.search(cleaned_src)
    if not m:
        return None
    # walk to the first `{` after the param list / return clause
    i = m.end()
    depth = 1
    n = len(cleaned_src)
    while i < n and depth > 0:
        c = cleaned_src[i]
        if c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
        i += 1
    while i < n and cleaned_src[i] != "{":
        i += 1
    if i >= n:
        return None
    open_brace = i
    close_brace = find_matching_brace(cleaned_src, open_brace)
    if close_brace == -1:
        return None
    body = cleaned_src[open_brace + 1:close_brace]
    return body, open_brace + 1, close_brace


def find_enclosing_function(cleaned_src: str, offset: int) -> str:
    """Walk backwards from `offset` to find the nearest `func` header.

    Returns the function name, or "<top-level>" if none found.
    """
    # Scan backwards looking for `func Name(` or `func (recv) Name(`.
    # We look at each `\bfunc\s` occurrence with a header match.
    chunk = cleaned_src[:offset]
    last_match = None
    for m in RE_FUNC_HEADER.finditer(chunk):
        last_match = m
    if not last_match:
        return "<top-level>"
    # sanity: ensure the func body actually contains our offset by checking
    # that no other top-level `func` header appears between this match and
    # our offset (which finditer already gives us — last_match is nearest).
    return last_match.group(1)


def preceding_window(src: str, go_idx: int, lines: int = 6) -> str:
    """Return up to `lines` lines of source immediately before go_idx."""
    start = max(0, go_idx - 1)
    # walk backwards to find start of `lines` lines
    nl_count = 0
    i = start
    while i > 0 and nl_count < lines:
        if src[i] == "\n":
            nl_count += 1
        i -= 1
    return src[i:go_idx]


def following_lines(src: str, go_idx: int, lines: int = 1) -> str:
    """Return up to `lines` lines of source immediately after go_idx."""
    end = go_idx
    nl_count = 0
    while end < len(src) and nl_count < lines:
        if src[end] == "\n":
            nl_count += 1
        end += 1
    return src[go_idx:end]


def guess_purpose(
    body: str,
    enclosing_function: str,
    preceding: str,
    launch_text: str,
    named_func: Optional[str] = None,
) -> str:
    """Best-effort guess of what the goroutine is for."""
    # 0) For `go x.fooBar()` launches, infer from the called function name.
    if named_func:
        short = named_func.split(".")[-1]
        low = short.lower()
        if "metricsflush" in low:
            return "DataDog metrics flush loop"
        if "eventsflush" in low:
            return "DataDog events flush loop"
        if "logsflush" in low:
            return "DataDog logs flush loop"
        if "checksflush" in low:
            return "DataDog service-check flush loop"
        if "flushloop" in low:
            return "Telemetry flush loop"
        if "retryworker" in low:
            return "Webhook retry worker loop"
        if short == "run" and "metrics" in (body or "").lower():
            return "Metrics leader-election / collection loop"
        if "heartbeatloop" in low:
            return "Health heartbeat loop"
        if "collectorloop" in low:
            return "Metrics collector loop"
        if "integrationcheckloop" in low:
            return "Integration-check loop"

    # 1) Use a `// ...` comment immediately above the launch.
    preceding_lines = [ln.strip() for ln in preceding.splitlines() if ln.strip()]
    for ln in reversed(preceding_lines):
        if ln.startswith("//"):
            return ln.lstrip("/").strip()[:120]

    # 2) Keyword heuristics on the goroutine body.
    text = (body or launch_text).lower()
    if "sendpasswordreset" in text or "passwordreset" in text:
        return "Send password-reset email in the background"
    if "sendverification" in text or "verificationemail" in text:
        return "Send verification email in the background"
    if "sendmagiclink" in text or "magiclink" in text:
        return "Send magic-link email in the background"
    if "sendinvitationemail" in text or "invitationemail" in text:
        return "Send invitation email in the background"
    if "sendemail" in text or "emailservice" in text:
        return "Send email asynchronously"
    if "deliverwithretry" in text or "webhook" in text:
        return "Webhook dispatch / delivery"
    if "heartbeat" in text:
        return "Health heartbeat loop"
    if "collectorloop" in text or "collectormetrics" in text:
        return "Metrics collector loop"
    if "integrationcheck" in text:
        return "Integration-check loop"
    if "cleanup" in text or "cleanupexpired" in text:
        return "Periodic cleanup of expired entries"
    if "autoreload" in text or "auto-reload" in text or ("load(" in text and "ticker" in text):
        return "Background config auto-reload"
    if "ticker" in text and "select" in text:
        return "Periodic ticker-driven background task"
    if "listenandserve" in text:
        return "HTTP server ListenAndServe (shutdown via http.Server.Shutdown)"
    if "updatebyid" in text or "updateone" in text:
        return "Asynchronous DB update"
    if "insertmany" in text or "telemetryevents" in text:
        return "Background telemetry flush"
    if "slog" in text:
        return "Background logging / side-effect"

    # 3) Fall back to the enclosing function name.
    if enclosing_function and enclosing_function != "<top-level>":
        return f"Background work spawned from {enclosing_function}()"

    return "Unknown background goroutine"


# --------------------------------------------------------------------------- #
# Core scanner
# --------------------------------------------------------------------------- #

def scan_file(path: Path, root: Path) -> list[GoroutineFinding]:
    try:
        raw = path.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:
        print(f"[warn] could not read {path}: {exc}", file=sys.stderr)
        return []

    cleaned = strip_go_comments(raw)
    rel_path = str(path.relative_to(root))
    is_test = path.name.endswith("_test.go")
    findings: list[GoroutineFinding] = []

    # ---- 1. `go func(...)` launches ----
    for m in RE_GO_FUNC.finditer(cleaned):
        go_idx = m.start()
        body, body_start, body_end = extract_func_literal_body(cleaned, go_idx)
        if body_start == -1:
            # malformed; record the call line only
            body = ""
        launch_text = cleaned[go_idx:go_idx + 80].replace("\n", " ")
        preceding = preceding_window(cleaned, go_idx, lines=6)
        findings.append(
            _build_finding(
                rel_path=rel_path,
                raw_src=cleaned,
                go_idx=go_idx,
                body=body,
                preceding=preceding,
                launch_text=launch_text,
                launch_kind="func_literal",
                is_test=is_test,
            )
        )

    # ---- 2. `go someFunc(...)` launches ----
    # Skip matches that overlap with `go func(` (already handled above).
    occupied = set()
    for m in RE_GO_FUNC.finditer(cleaned):
        for i in range(m.start(), m.end()):
            occupied.add(i)

    for m in RE_GO_CALL.finditer(cleaned):
        if any(i in occupied for i in range(m.start(), m.end())):
            continue
        func_name = m.group(1)
        # Skip keywords that aren't function names.
        if func_name in ("func", "return", "defer"):
            continue
        go_idx = m.start()
        # Try to resolve the named function body in the same file.
        body = ""
        resolved = resolve_named_function_body(raw, cleaned, func_name.split(".")[-1])
        if resolved:
            body = resolved[0]
        launch_text = cleaned[go_idx:go_idx + 80].replace("\n", " ")
        preceding = preceding_window(cleaned, go_idx, lines=6)
        findings.append(
            _build_finding(
                rel_path=rel_path,
                raw_src=cleaned,
                go_idx=go_idx,
                body=body,
                preceding=preceding,
                launch_text=launch_text,
                launch_kind="func_call",
                is_test=is_test,
                named_func=func_name,
            )
        )

    return findings


def _build_finding(
    rel_path: str,
    raw_src: str,
    go_idx: int,
    body: str,
    preceding: str,
    launch_text: str,
    launch_kind: str,
    is_test: bool,
    named_func: Optional[str] = None,
) -> GoroutineFinding:
    line = line_of_offset(raw_src, go_idx)
    column = go_idx - (raw_src.rfind("\n", 0, go_idx) + 1) + 1
    enclosing = find_enclosing_function(raw_src, go_idx)

    # --- signal detection ---
    # Context usage: a `ctx context.Context`-ish parameter, or use of
    # context.Background/TODO/With* in the body.
    has_context = bool(RE_CONTEXT_PARAM.search(body or ""))

    # Done channel: `<-ctx.Done()` or `<-done`-style receive.
    has_done_channel = bool(
        RE_CTX_DONE.search(body or "") or RE_DONE_CHAN.search(body or "")
    )

    # WaitGroup: `wg.Add(` in the preceding window AND/OR `wg.Done()` in body.
    wg_add_match = RE_WG_ADD.search(preceding)
    wg_done_match = RE_WG_DONE.search(body or "")
    has_waitgroup = bool(wg_add_match or wg_done_match)

    # Timeout / deadline / cancel derived from context.
    has_timeout = bool(RE_TIMEOUT.search(body or ""))

    # Panic recovery anywhere in the body.
    has_recover = bool(RE_RECOVER.search(body or ""))

    # --- classification ---
    signals: list[str] = []
    if has_context:
        signals.append("context")
    if has_done_channel:
        signals.append("done-channel")
    if has_waitgroup:
        signals.append("waitgroup")
    if has_timeout:
        signals.append("timeout")
    if has_recover:
        signals.append("recover")

    if has_done_channel or has_waitgroup or has_timeout:
        risk = "SAFE"
    elif has_recover:
        risk = "RISKY"
    else:
        risk = "DANGEROUS"

    # --- notes ---
    notes: list[str] = []
    if wg_add_match and not wg_done_match:
        notes.append("wg.Add() before launch but no wg.Done() in body — check goroutine exits")
    if wg_done_match and not wg_add_match:
        notes.append("wg.Done() in body but no nearby wg.Add() — check caller adds to WaitGroup")
    if has_context and not has_done_channel and not has_timeout:
        notes.append("uses context.Context but no ctx.Done() receive or WithTimeout — context may not actually cancel the goroutine")
    if not has_recover:
        notes.append("no defer recover() — a panic will crash the process")
    if launch_kind == "func_call" and not body:
        notes.append(f"could not resolve body of {named_func}() in same file — signals may be incomplete")

    purpose = guess_purpose(
        body or "", enclosing, preceding, launch_text, named_func=named_func
    )

    # body preview: first ~12 non-empty lines, trimmed
    body_preview_lines = [
        ln.rstrip() for ln in (body or "").splitlines() if ln.strip()
    ][:12]
    body_preview = "\n".join(body_preview_lines)

    return GoroutineFinding(
        file=rel_path,
        line=line,
        column=column,
        enclosing_function=enclosing,
        launch_kind=launch_kind,
        launch_text=launch_text.strip()[:100],
        purpose=purpose,
        has_context=has_context,
        has_done_channel=has_done_channel,
        has_waitgroup=has_waitgroup,
        has_timeout=has_timeout,
        has_recover=has_recover,
        risk_level=risk,
        signals=signals,
        notes=notes,
        is_test_file=is_test,
        body_preview=body_preview,
    )


# --------------------------------------------------------------------------- #
# Path discovery
# --------------------------------------------------------------------------- #

EXCLUDED_DIRS = {
    "vendor", "node_modules", "graphify-out", "dist", "build",
    ".git", ".idea", ".vscode", "coverage", "testdata",
}


def iter_go_files(root: Path, include_tests: bool) -> list[Path]:
    files: list[Path] = []
    for p in root.rglob("*.go"):
        if any(part in EXCLUDED_DIRS for part in p.parts):
            continue
        if not include_tests and p.name.endswith("_test.go"):
            continue
        files.append(p)
    files.sort()
    return files


# --------------------------------------------------------------------------- #
# Report rendering
# --------------------------------------------------------------------------- #

RISK_EMOJI = {
    "SAFE": "SAFE",
    "RISKY": "RISKY",
    "DANGEROUS": "DANGEROUS",
}


def build_markdown(findings: list[GoroutineFinding], root: Path) -> str:
    lines: list[str] = []
    lines.append("# Goroutine Leak Audit")
    lines.append("")
    lines.append(f"_Target: `{root}`_  ")
    total = len(findings)
    safe = sum(1 for f in findings if f.risk_level == "SAFE")
    risky = sum(1 for f in findings if f.risk_level == "RISKY")
    danger = sum(1 for f in findings if f.risk_level == "DANGEROUS")
    lines.append(
        f"**Summary:** {total} goroutine launches "
        f"— SAFE: {safe} | RISKY: {risky} | DANGEROUS: {danger}"
    )
    lines.append("")
    lines.append("## Classification key")
    lines.append("")
    lines.append("- SAFE — goroutine has a `<-ctx.Done()` channel, a WaitGroup, "
                 "or a `context.WithTimeout`/`WithDeadline` so it can be torn down.")
    lines.append("- RISKY — no context, no WaitGroup, no timeout. May run forever; "
                 "but at least has `defer recover()` so a panic won't kill the process.")
    lines.append("- DANGEROUS — no context, no WaitGroup, no timeout, **and** no "
                 "panic recovery. Highest leak / crash risk.")
    lines.append("")

    # Group by risk level, dangerous first.
    order = ["DANGEROUS", "RISKY", "SAFE"]
    for risk in order:
        group = [f for f in findings if f.risk_level == risk]
        if not group:
            continue
        emoji = {"DANGEROUS": "DANGEROUS", "RISKY": "RISKY", "SAFE": "SAFE"}[risk]
        lines.append(f"## {emoji} ({len(group)})")
        lines.append("")
        for f in group:
            lines.append(f"### `{f.file}:{f.line}` — {f.purpose}")
            lines.append("")
            lines.append(f"- **Enclosing function:** `{f.enclosing_function}`")
            lines.append(f"- **Launch kind:** `{f.launch_kind}`")
            lines.append(f"- **Launch text:** `{f.launch_text}`")
            lines.append(f"- **Risk level:** **{f.risk_level}**")
            sig = ", ".join(f.signals) if f.signals else "(none detected)"
            lines.append(f"- **Signals detected:** {sig}")
            if f.notes:
                for note in f.notes:
                    lines.append(f"  - {note}")
            if f.body_preview:
                lines.append("")
                lines.append("<details><summary>Goroutine body preview</summary>")
                lines.append("")
                lines.append("```go")
                lines.append(f.body_preview)
                lines.append("```")
                lines.append("")
                lines.append("</details>")
            lines.append("")

    # File-level table.
    lines.append("## All findings (table)")
    lines.append("")
    lines.append("| File | Line | Function | Purpose | Risk | Signals |")
    lines.append("|------|------|----------|---------|------|---------|")
    for f in findings:
        sig = ", ".join(f.signals) if f.signals else "—"
        purpose_short = f.purpose[:60].replace("|", "\\|")
        func_short = f.enclosing_function.replace("|", "\\|")
        lines.append(
            f"| {f.file} | {f.line} | {func_short} | {purpose_short} | {f.risk_level} | {sig} |"
        )
    lines.append("")

    # Recommendations.
    lines.append("## Recommendations")
    lines.append("")
    if danger > 0:
        lines.append(f"1. **Fix {danger} DANGEROUS goroutine(s) first** — add `defer recover()` "
                     "and a cancellation path (`context.WithTimeout` or a `<-done` select).")
    if risky > 0:
        lines.append(f"2. **Review {risky} RISKY goroutine(s)** — they have `recover()` but no "
                     "shutdown signal. If they perform I/O, wrap with `context.WithTimeout` so a "
                     "stuck downstream call can't pin the goroutine forever.")
    if danger == 0 and risky == 0:
        lines.append("1. No high-risk goroutines detected — keep the existing discipline.")
    lines.append("3. For HTTP-handler fire-and-forget email sends, prefer passing a request-scoped "
                 "context or a small bounded `context.WithTimeout(context.Background(), 30*time.Second)`.")
    lines.append("4. For long-lived background loops, ensure they expose a `Stop()` method that "
                 "closes a `stopCh` and that callers actually invoke it on shutdown.")
    lines.append("")

    return "\n".join(lines)


def build_json_report(
    findings: list[GoroutineFinding], root: Path
) -> dict:
    safe = sum(1 for f in findings if f.risk_level == "SAFE")
    risky = sum(1 for f in findings if f.risk_level == "RISKY")
    danger = sum(1 for f in findings if f.risk_level == "DANGEROUS")
    return {
        "target": str(root),
        "total_goroutines": len(findings),
        "summary": {
            "SAFE": safe,
            "RISKY": risky,
            "DANGEROUS": danger,
        },
        "findings": [asdict(f) for f in findings],
    }


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Detect potential goroutine leaks in Go source code.",
    )
    parser.add_argument(
        "path",
        nargs="?",
        default="/home/z/my-project/repos/lastsaas/backend",
        help="Path to scan (default: /home/z/my-project/repos/lastsaas/backend)",
    )
    parser.add_argument(
        "--out",
        default=None,
        help="Write the markdown report to this path.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON to stdout instead of a markdown report.",
    )
    parser.add_argument(
        "--json-out",
        default=None,
        help="Write the JSON report to this path (in addition to --out).",
    )
    parser.add_argument(
        "--include-tests",
        action="store_true",
        help="Include *_test.go files (skipped by default).",
    )
    args = parser.parse_args(argv)

    root = Path(args.path).resolve()
    if not root.exists():
        print(f"[error] path does not exist: {root}", file=sys.stderr)
        return 2

    files = iter_go_files(root, include_tests=args.include_tests)
    if not files:
        print(f"[warn] no .go files found under {root}", file=sys.stderr)

    findings: list[GoroutineFinding] = []
    for f in files:
        findings.extend(scan_file(f, root))

    # Sort: dangerous first, then by file:line.
    risk_order = {"DANGEROUS": 0, "RISKY": 1, "SAFE": 2}
    findings.sort(key=lambda f: (risk_order.get(f.risk_level, 9), f.file, f.line))

    # Always build both payloads; --out / --json-out write to disk,
    # --json additionally dumps JSON to stdout, otherwise markdown goes to
    # stdout (when no --out is given).
    json_payload = build_json_report(findings, root)
    md_payload = build_markdown(findings, root)

    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(md_payload, encoding="utf-8")
        print(f"[ok] markdown report -> {out_path}", file=sys.stderr)

    if args.json_out:
        json_path = Path(args.json_out)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(
            json.dumps(json_payload, indent=2), encoding="utf-8"
        )
        print(f"[ok] json report -> {json_path}", file=sys.stderr)

    if args.json:
        print(json.dumps(json_payload, indent=2))
    elif not args.out:
        # No file target and no --json: print markdown to stdout.
        print(md_payload)

    # Always print a one-line summary to stderr for visibility.
    safe = sum(1 for f in findings if f.risk_level == "SAFE")
    risky = sum(1 for f in findings if f.risk_level == "RISKY")
    danger = sum(1 for f in findings if f.risk_level == "DANGEROUS")
    print(
        f"[summary] {len(findings)} goroutines — "
        f"SAFE={safe} RISKY={risky} DANGEROUS={danger}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
