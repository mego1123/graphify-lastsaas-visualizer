#!/usr/bin/env python3
"""graphify middleware — Go HTTP middleware chain visualizer.

Scans all .go files in a repository and:

  1. Detects middleware usage patterns:
       - `router.Use(...)` / `r.Use(...)` / `api.Use(...)` — gorilla/mux style
       - `middleware.Func(...)` factory calls
       - Manual nesting: `handler := m1(m2(m3(finalHandler)))`
       - `http.Handler` wrapping (`http.HandlerFunc(...)`, `c.Handler(...)`)
       - Method-style: `metricsCollector.Middleware(router)`
       - `rateLimiter.RateLimitHandler(config, keyFunc, handler)`

  2. Reconstructs the execution order for every chain site. The outermost
     wrapper runs first; the innermost (the actual handler) runs last.

  3. For each middleware, identifies:
       - name, file, doc comment
       - whether it runs *before* the handler (does work then calls
         `next.ServeHTTP`)
       - whether it runs *after* the handler (calls `next.ServeHTTP` first,
         then does work — e.g. metrics, panic recovery via `defer`)
       - whether it short-circuits (returns early without invoking
         `next.ServeHTTP`, e.g. on auth failure or rate-limit exceeded)

  4. Emits a visual chain for every router, e.g.:

       Request → Recovery → BodySizeLimit → SecurityHeaders → CORS → Metrics → Router → Handler → Response

Usage:
  python graphify_middleware.py [path] [--out report.md] [--json]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

# ---------------------------------------------------------------------------
# Regexes
# ---------------------------------------------------------------------------

# `router.Use(...)` — capture router variable name and the call inside.
# Tolerates optional `(` after the identifier (for `r.Use(middleware.Foo(...))`).
RE_USE_CALL = re.compile(
    r"\b(?P<router>[a-zA-Z_]\w*)\.Use\(\s*(?P<arg>[^)]+?(?:\([^)]*\)[^)]*)*)\s*\)"
)

# A middleware factory call: `middleware.RequireRole(models.RoleAdmin)` or
# `middleware.RequireActiveBilling()` — captures the function name.
RE_MIDDLEWARE_CALL = re.compile(
    r"\bmiddleware\.(?P<name>[A-Z]\w*)\s*\("
)

# A method-style middleware call: `authMiddleware.RequireAuth` (no parens —
# it's already a function value) or `metricsCollector.Middleware(...)`.
RE_RECEIVER_METHOD = re.compile(
    r"\b(?P<recv>[a-z]\w*)\.(?P<method>[A-Z]\w*)\b"
)

# RateLimitHandler call: `rateLimiter.RateLimitHandler(config, keyFunc, handler)`.
RE_RATELIMIT_HANDLER = re.compile(
    r"\b(?P<recv>[a-z]\w*)\.RateLimitHandler\("
)

# `func Name(next http.Handler) http.Handler` — a top-level middleware function.
RE_MIDDLEWARE_FUNC_DEF = re.compile(
    r"func\s+(?P<name>[A-Z]\w*)\s*\(\s*next\s+\*?http\.Handler\s*\)\s+http\.Handler"
)

# `func (recv *Type) Method(next http.Handler) http.Handler` — method-style.
RE_MIDDLEWARE_METHOD_DEF = re.compile(
    r"func\s+\(\s*(?P<recv>\w+)\s+\*?(?P<type>[A-Z]\w*)\s*\)\s+"
    r"(?P<method>[A-Z]\w*)\s*\(\s*next\s+\*?http\.Handler\s*\)\s+http\.Handler"
)

# `func Name(next http.HandlerFunc) http.HandlerFunc` — chi-style middleware.
RE_MIDDLEWARE_HANDLERFUNC_DEF = re.compile(
    r"func\s+(?P<name>[A-Z]\w*)\s*\(\s*next\s+http\.HandlerFunc\s*\)\s+http\.HandlerFunc"
)

# `func (recv *Type) Method(...) func(http.Handler) http.Handler` — factory
# style that returns a middleware closure (e.g. RequireRole, RequireActiveBilling).
RE_MIDDLEWARE_FACTORY_DEF = re.compile(
    r"func\s+\(\s*(?P<recv>\w+)\s+\*?(?P<type>[A-Z]\w*)\s*\)\s+"
    r"(?P<method>[A-Z]\w*)\s*\([^)]*\)\s*func\s*\(\s*http\.Handler\s*\)\s*http\.Handler"
)

# Top-level factory: `func RequireRole(minRole X) func(http.Handler) http.Handler`.
RE_MIDDLEWARE_FACTORY_FUNC_DEF = re.compile(
    r"func\s+(?P<name>[A-Z]\w*)\s*\([^)]*\)\s*func\s*\(\s*http\.Handler\s*\)\s*http\.Handler"
)

# http.Handler wrap: `http.HandlerFunc(func(w, r) { ... })` — we don't dive
# in, just note the wrap exists.
RE_HTTP_HANDLER_FUNC = re.compile(r"\bhttp\.HandlerFunc\(")

# Detect `next.ServeHTTP(` to determine whether the middleware forwards.
RE_NEXT_CALL = re.compile(r"\bnext\.ServeHTTP\(")

# Detect an early return (a `return` statement that does NOT come after the
# `next.ServeHTTP` call). We use this to decide short-circuit behaviour.
RE_RETURN = re.compile(r"^\s*return\b", re.MULTILINE)

# Detect http.Error writes — strong signal of a short-circuit.
RE_HTTP_ERROR = re.compile(
    r"http\.Error\([^)]+,\s*http\.Status(?:Unauthorized|Forbidden|TooManyRequests|"
    r"BadRequest|NotFound|PaymentRequired|InternalServerError|ServiceUnavailable|"
    r"RequestTimeout|Conflict|Gone)"
)

# Detect a `WriteHeader(` followed by an HTTP error code, indicating a
# short-circuit response.
RE_WRITEHEADER_ERR = re.compile(
    r"WriteHeader\(\s*http\.Status(?:Unauthorized|Forbidden|TooManyRequests|"
    r"BadRequest|NotFound|PaymentRequired|InternalServerError|ServiceUnavailable)\s*\)"
)

# Doc comment capture (one or more `//` lines immediately above a definition).
RE_DOC_LINE = re.compile(r"^\s*//\s*(?P<text>.*)$")

# Package declaration.
RE_PACKAGE = re.compile(r"^\s*package\s+(\w+)", re.MULTILINE)


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class MiddlewareDef:
    name: str
    file: str
    package: str
    line: int
    doc: str
    is_method: bool = False          # method on a struct (vs free function)
    receiver_type: Optional[str] = None
    is_factory: bool = False         # returns `func(http.Handler) http.Handler`
    short_circuits: bool = False
    runs_before: bool = False        # work done before next.ServeHTTP
    runs_after: bool = False         # work done after next.ServeHTTP (or via defer)
    raw_signature: str = ""


@dataclass
class ChainSite:
    router: str
    file: str
    line: int
    pattern: str                     # "use", "manual-wrap", "ratelimit"
    links: List[str]                 # ordered middleware names (outermost first)
    raw: str = ""


# ---------------------------------------------------------------------------
# File walking
# ---------------------------------------------------------------------------

def find_go_files(repo: Path, include_tests: bool = False) -> List[Path]:
    skip_dirs = {"vendor", "node_modules", ".git", "graphify-out", "dist", "build"}
    out: List[Path] = []
    for p in repo.rglob("*.go"):
        if any(part in skip_dirs for part in p.parts):
            continue
        if not include_tests and p.name.endswith("_test.go"):
            continue
        out.append(p)
    return sorted(out)


def line_of(content: str, idx: int) -> int:
    return content.count("\n", 0, idx) + 1


def preceding_doc(content: str, idx: int) -> str:
    lines = content[:idx].splitlines()
    out: List[str] = []
    for line in reversed(lines):
        m = RE_DOC_LINE.match(line)
        if m:
            out.append(m.group("text").strip())
        elif line.strip() == "":
            continue
        else:
            break
    return " ".join(reversed(out)).strip()


# ---------------------------------------------------------------------------
# Middleware definition parsing
# ---------------------------------------------------------------------------

def parse_middleware_defs(content: str, file: str, package: str) -> List[MiddlewareDef]:
    out: List[MiddlewareDef] = []
    # We need to find the function body for each definition so we can decide
    # short-circuit / before / after behaviour.
    for m in list(RE_MIDDLEWARE_METHOD_DEF.finditer(content)):
        out.append(_build_def(content, file, package, m, name=m.group("method"),
                             is_method=True, receiver_type=m.group("type"),
                             is_factory=False, raw=m.group(0)))
    for m in list(RE_MIDDLEWARE_FUNC_DEF.finditer(content)):
        out.append(_build_def(content, file, package, m, name=m.group("name"),
                             is_method=False, receiver_type=None,
                             is_factory=False, raw=m.group(0)))
    for m in list(RE_MIDDLEWARE_HANDLERFUNC_DEF.finditer(content)):
        out.append(_build_def(content, file, package, m, name=m.group("name"),
                             is_method=False, receiver_type=None,
                             is_factory=False, raw=m.group(0)))
    for m in list(RE_MIDDLEWARE_FACTORY_DEF.finditer(content)):
        out.append(_build_def(content, file, package, m, name=m.group("method"),
                             is_method=True, receiver_type=m.group("type"),
                             is_factory=True, raw=m.group(0)))
    for m in list(RE_MIDDLEWARE_FACTORY_FUNC_DEF.finditer(content)):
        out.append(_build_def(content, file, package, m, name=m.group("name"),
                             is_method=False, receiver_type=None,
                             is_factory=True, raw=m.group(0)))
    return out


def _build_def(
    content: str,
    file: str,
    package: str,
    match: re.Match,
    *,
    name: str,
    is_method: bool,
    receiver_type: Optional[str],
    is_factory: bool,
    raw: str,
) -> MiddlewareDef:
    """Construct a MiddlewareDef, scanning the function body for behaviour."""
    # Find the body: from the `(` of the params to the closing `{...}`.
    brace_idx = content.find("{", match.end() - 1)
    if brace_idx == -1:
        brace_idx = content.find("{", match.end())
    body = ""
    if brace_idx != -1 and brace_idx < len(content):
        depth = 0
        i = brace_idx
        while i < len(content):
            if content[i] == "{":
                depth += 1
            elif content[i] == "}":
                depth -= 1
                if depth == 0:
                    body = content[brace_idx + 1 : i]
                    break
            i += 1

    # Find every `next.ServeHTTP` call in the body (including inside nested
    # closures — factory middleware wraps its real logic in a returned
    # `http.HandlerFunc(func(w, r) {...})`).
    next_calls = list(RE_NEXT_CALL.finditer(body))
    runs_before = False
    runs_after = False
    short_circuits = False

    if next_calls:
        # Find the FIRST next.ServeHTTP — work before it runs "before", work
        # after it runs "after". A `defer` block always runs after.
        first_next = next_calls[0]
        before_part = body[: first_next.start()]
        after_part = body[first_next.end() :]
        if _has_executable_code(before_part):
            runs_before = True
        if _has_executable_code(after_part) or re.search(r"\bdefer\b", before_part):
            runs_after = True
    else:
        # No `next.ServeHTTP` at all — could be a pure terminal middleware
        # (rare) or just a factory whose body is `return func(...) {...}`
        # with the real logic in the closure. We'll catch short-circuits
        # via the http.Error scan below.
        if body.strip():
            runs_before = True

    # Short-circuit detection: look for `http.Error(...)` or
    # `WriteHeader(http.StatusXXX)` calls that are NOT inside a `defer`
    # block. Those represent proactive request rejection.
    short_circuit_signals = _find_short_circuit_signals(body)
    if short_circuit_signals:
        short_circuits = True
        runs_before = True  # short-circuiting middleware always runs (before)

    # `runs_after` only if there is executable code AFTER next.ServeHTTP
    # (or a defer). Recovery-style middleware wraps next in a defer recover().
    if not runs_after and re.search(r"\bdefer\b.*?recover\(\)", body, re.DOTALL):
        runs_after = True

    return MiddlewareDef(
        name=name,
        file=file,
        package=package,
        line=line_of(content, match.start()),
        doc=preceding_doc(content, match.start()),
        is_method=is_method,
        receiver_type=receiver_type,
        is_factory=is_factory,
        short_circuits=short_circuits,
        runs_before=runs_before,
        runs_after=runs_after,
        raw_signature=raw.strip(),
    )


def _find_short_circuit_signals(body: str) -> List[Tuple[int, str]]:
    """Find every `http.Error(...)` or `WriteHeader(http.StatusXXX)` call
    that is NOT inside a `defer` block. Returns a list of (position, kind).
    """
    out: List[Tuple[int, str]] = []
    # Identify the byte ranges of every `defer ... { ... }` block so we can
    # exclude http.Error calls that live inside them (e.g. Recovery).
    defer_ranges: List[Tuple[int, int]] = []
    for dm in re.finditer(r"\bdefer\b", body):
        # Find the next `{` after `defer` (could be `defer func() { ... }()`
        # or `defer cleanup()`).
        brace_idx = body.find("{", dm.end())
        if brace_idx == -1 or brace_idx - dm.end() > 200:
            # `defer foo()` — no block, just a function call. Skip — we
            # can't easily attribute http.Error calls to it.
            continue
        # Find the matching close brace.
        depth = 0
        i = brace_idx
        while i < len(body):
            if body[i] == "{":
                depth += 1
            elif body[i] == "}":
                depth -= 1
                if depth == 0:
                    defer_ranges.append((brace_idx, i + 1))
                    break
            i += 1

    def _in_defer(idx: int) -> bool:
        for start, end in defer_ranges:
            if start <= idx < end:
                return True
        return False

    for em in RE_HTTP_ERROR.finditer(body):
        if not _in_defer(em.start()):
            out.append((em.start(), "http.Error"))
    for wm in RE_WRITEHEADER_ERR.finditer(body):
        if not _in_defer(wm.start()):
            out.append((wm.start(), "WriteHeader"))
    return out


def _has_executable_code(snippet: str) -> bool:
    """Return True if the snippet contains an executable Go statement
    (not just comments / whitespace / declarations like `:=` for context
    setup also counts). We treat any non-comment, non-blank line as code.
    """
    for raw in snippet.splitlines():
        line = raw.strip()
        if not line or line.startswith("//") or line.startswith("/*") or line.startswith("*"):
            continue
        return True
    return False


# ---------------------------------------------------------------------------
# Chain detection
# ---------------------------------------------------------------------------

def parse_use_chains(content: str, file: str) -> List[ChainSite]:
    """`router.Use(mw)` style — each `.Use(...)` call is one site (one link)."""
    out: List[ChainSite] = []
    for m in RE_USE_CALL.finditer(content):
        arg = m.group("arg").strip()
        router = m.group("router")
        # The argument may be `middleware.Foo`, `middleware.Foo(args)`,
        # `recv.Method`, or `recv.Method(args)`.
        name = _extract_middleware_name(arg)
        out.append(ChainSite(
            router=router,
            file=file,
            line=line_of(content, m.start()),
            pattern="use",
            links=[name] if name else [],
            raw=m.group(0).strip(),
        ))
    return out


def _extract_middleware_name(arg: str) -> str:
    """Pull the bare middleware name out of a `Use(...)` argument string."""
    arg = arg.strip()
    # `middleware.Foo(...)` → Foo
    m = RE_MIDDLEWARE_CALL.search(arg)
    if m:
        return m.group("name")
    # `middleware.Foo` (no parens) → Foo
    m = re.match(r"middleware\.(?P<name>[A-Z]\w*)\s*$", arg)
    if m:
        return m.group("name")
    # `recv.Method` (no parens) — combine into `recv.Method` form so we can
    # match against method-style middleware defs.
    m = re.match(r"(?P<recv>[a-z]\w*)\.(?P<method>[A-Z]\w*)\s*$", arg)
    if m:
        return m.group("method")
    # `recv.Method(args)` → Method
    m = re.match(r"(?P<recv>[a-z]\w*)\.(?P<method>[A-Z]\w*)\s*\(", arg)
    if m:
        return m.group("method")
    # `BootstrapGuard` (bare identifier) — return as-is.
    if re.match(r"^[A-Z]\w*$", arg):
        return arg
    return arg


def parse_manual_wrap_chains(
    content: str,
    file: str,
    known_middleware_names: Optional[Set[str]] = None,
) -> List[ChainSite]:
    """Manual nesting like `handler := m1(m2(m3(router)))`.

    Only emit a chain if at least one of the wrapper functions matches a
    known middleware name (so we don't pick up constructor calls like
    `handler := handlers.NewFoo(db)` as middleware chains).
    """
    out: List[ChainSite] = []
    for m in re.finditer(
        r"(?P<lhs>\w*[Hh]andler)\s*(?::=|=)\s*(?P<rhs>[^\n;]+)",
        content,
    ):
        rhs = m.group("rhs").strip().rstrip(";")
        links = _unwrap_chain(rhs)
        if len(links) < 2:
            continue
        # Filter: at least one non-terminal link must be a known middleware
        # name. This excludes `bootstrapHandler := NewBootstrapHandler(db)`.
        wrapper_links = links[:-1]  # all but the terminal handler
        if known_middleware_names is None:
            # Without a known set, require 3+ links to be considered a chain.
            if len(links) < 3:
                continue
        else:
            if not any(w in known_middleware_names for w in wrapper_links):
                continue
        out.append(ChainSite(
            router="(global)",
            file=file,
            line=line_of(content, m.start()),
            pattern="manual-wrap",
            links=links,
            raw=m.group(0).strip(),
        ))
    return out


def _find_matching_paren(s: str, open_idx: int) -> int:
    """Given `s` and the index of an opening `(`, return the index of the
    matching closing `)`. Returns -1 if unbalanced.
    """
    depth = 0
    for i in range(open_idx, len(s)):
        if s[i] == "(":
            depth += 1
        elif s[i] == ")":
            depth -= 1
            if depth == 0:
                return i
    return -1


def _unwrap_chain(rhs: str) -> List[str]:
    """Given `a(b(c(d)))`, return ["a", "b", "c", "d"].

    Walks the call nesting from outside in. Stops when the innermost
    argument is not itself a function call (that's the terminal handler).
    """
    links: List[str] = []
    s = rhs.strip()
    # Strip trailing comment if any.
    if "//" in s:
        s = s.split("//", 1)[0].strip()
    # Strip a trailing semicolon.
    s = s.rstrip(";").strip()

    call_re = re.compile(r"^(?P<call>(?:[A-Za-z_]\w*\.)*[A-Za-z_]\w*)\s*\(")
    while True:
        m = call_re.match(s)
        if not m:
            # Terminal handler — bare identifier (possibly with trailing
            # close parens that belong to outer calls we've already closed).
            tail = s.rstrip(")").strip()
            if tail:
                links.append(tail)
            break
        call = m.group("call")
        # Take the last component (e.g. `middleware.Recovery` → `Recovery`).
        short = call.rsplit(".", 1)[-1]
        links.append(short)
        # Find the matching close paren of this call.
        open_idx = m.end() - 1  # position of `(`
        close_idx = _find_matching_paren(s, open_idx)
        if close_idx == -1:
            # Unbalanced — bail.
            break
        # The argument list is between open_idx+1 and close_idx.
        args = s[open_idx + 1 : close_idx].strip()
        # What's after this call (should be empty or only outer close parens).
        after = s[close_idx + 1 :].strip()
        # If `after` is not just close parens, the chain is malformed — bail.
        if after and not re.match(r"^\)+$", after):
            break
        # Now: is `args` itself a single function call?
        inner_m = call_re.match(args)
        if inner_m:
            # Recurse — the args is itself a call (e.g. `b(c(d))`).
            # But we also need to handle the case where args is just `b(c(d))`
            # with no other arguments. If args contains commas at depth 0,
            # it's multiple args — the chain ends here (terminal handler is
            # the full arg list).
            if _has_top_level_comma(args):
                # Terminal — args is the handler (e.g. a closure).
                links.append(args[:80])
                break
            s = args
            continue
        # Terminal handler — args is the innermost expression (e.g. `router`
        # or a closure `func(w, r) { ... }`).
        if args:
            # If it's a bare identifier, record just the name; otherwise
            # truncate to keep the report readable.
            bare = re.match(r"^(?:[A-Za-z_]\w*\.)*[A-Za-z_]\w*$", args)
            if bare:
                links.append(args)
            else:
                # It's a closure or value — label it generically.
                links.append("(handler)")
        break
    return links


def _has_top_level_comma(s: str) -> bool:
    """Return True if `s` has a comma at brace/paren depth 0."""
    depth = 0
    for ch in s:
        if ch in "({[":
            depth += 1
        elif ch in ")}]":
            depth -= 1
        elif ch == "," and depth == 0:
            return True
    return False


def parse_ratelimit_chains(content: str, file: str) -> List[ChainSite]:
    """`rateLimiter.RateLimitHandler(config, keyFunc, handler)` — terminal
    middleware that wraps a single handler. We record the site but the chain
    is only one link deep (RateLimitHandler).
    """
    out: List[ChainSite] = []
    for m in RE_RATELIMIT_HANDLER.finditer(content):
        out.append(ChainSite(
            router="(ratelimit)",
            file=file,
            line=line_of(content, m.start()),
            pattern="ratelimit",
            links=["RateLimitHandler"],
            raw=m.group(0).strip(),
        ))
    return out


# ---------------------------------------------------------------------------
# Chain consolidation
# ---------------------------------------------------------------------------

def consolidate_use_chains(
    chains: List[ChainSite],
) -> List[ChainSite]:
    """Multiple `.Use(...)` calls on the same router in the same file
    accumulate into a single chain (mux semantics: applied in order)."""
    grouped: Dict[Tuple[str, str], ChainSite] = {}
    for c in chains:
        key = (c.router, c.file)
        if key not in grouped:
            grouped[key] = ChainSite(
                router=c.router,
                file=c.file,
                line=c.line,
                pattern="use",
                links=list(c.links),
                raw=c.raw,
            )
        else:
            grouped[key].links.extend(c.links)
            grouped[key].raw += " ; " + c.raw
    return list(grouped.values())


def attach_defs(
    chains: List[ChainSite],
    defs: Dict[str, MiddlewareDef],
) -> List[ChainSite]:
    """No-op placeholder — we keep defs separate but available for the
    reporter. Returns chains unchanged."""
    return chains


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def describe_middleware(d: MiddlewareDef) -> str:
    """One-line human description of what a middleware does, derived from
    its name and doc comment."""
    name = d.name
    doc = d.doc
    # If we have a doc, use its first sentence.
    if doc:
        first = doc.split(".")[0].strip()
        if first:
            return f"{name} — {first}"
    # Otherwise, infer from name.
    name_map = {
        "Recovery": "recovers from panics in downstream handlers",
        "BodySizeLimit": "limits request body size to 1MB",
        "SecurityHeaders": "sets CSP, HSTS, X-Frame-Options and related headers",
        "RequestID": "generates and propagates an X-Request-ID",
        "APIVersion": "sets the X-API-Version response header",
        "RequireAuth": "validates JWT or API key, blocks anonymous requests",
        "RequireTenant": "resolves X-Tenant-ID and loads tenant membership",
        "RequireRole": "blocks requests below a minimum tenant role",
        "RequireRootTenant": "blocks requests to non-root tenants",
        "RequireActiveBilling": "blocks requests when subscription is inactive",
        "RequireEntitlement": "checks plan entitlement for a specific feature",
        "BootstrapGuard": "blocks requests until the system is bootstrapped",
        "RateLimitHandler": "applies per-key rate limiting, 429s on overflow",
        "Middleware": "collects latency / status metrics for downstream handlers",
        "CORS": "applies CORS headers",
    }
    if name in name_map:
        return f"{name} — {name_map[name]}"
    return f"{name} — middleware"


# Friendly display-name overrides for the visual chain. When a name appears
# in this map we substitute the friendlier label in the rendered chain.
DISPLAY_NAME_OVERRIDES = {
    "Handler": "CORS",            # `c.Handler(...)` from gorilla/handlers
    "Middleware": "Metrics",      # `metricsCollector.Middleware(...)`
    "router": "Router",           # the inner mux router
    "RateLimitHandler": "RateLimit",
}


def _display_name(name: str) -> str:
    return DISPLAY_NAME_OVERRIDES.get(name, name)


def visual_chain(links: List[str], defs: Dict[str, MiddlewareDef]) -> str:
    """Render a chain like `Request → A → B → Handler → Response`."""
    parts: List[str] = ["Request"]
    for i, name in enumerate(links):
        is_last = i == len(links) - 1
        d = defs.get(name)
        marker = " ✋" if d and d.short_circuits else ""
        if is_last and not _looks_like_middleware(name, defs):
            parts.append(f"{_display_name(name)}{marker} (Handler)")
        else:
            parts.append(f"{_display_name(name)}{marker}")
    parts.append("Response")
    return " → ".join(parts)


def _looks_like_middleware(name: str, defs: Dict[str, MiddlewareDef]) -> bool:
    return name in defs


def emit_markdown(
    defs: List[MiddlewareDef],
    chains: List[ChainSite],
    repo: Path,
) -> str:
    lines: List[str] = []
    lines.append("# Middleware Chain Report")
    lines.append("")
    lines.append(f"Repository: `{repo}`")
    lines.append("")
    lines.append(f"- **Middleware definitions**: {len(defs)}")
    lines.append(f"- **Chain sites**: {len(chains)}")
    short_circuit_count = sum(1 for d in defs if d.short_circuits)
    before_count = sum(1 for d in defs if d.runs_before)
    after_count = sum(1 for d in defs if d.runs_after)
    lines.append(
        f"- **Short-circuiting**: {short_circuit_count} / {len(defs)}"
    )
    lines.append(
        f"- **Run before handler**: {before_count} / {len(defs)}"
    )
    lines.append(
        f"- **Run after handler**: {after_count} / {len(defs)}"
    )
    lines.append("")

    defs_by_name = {d.name: d for d in defs}

    # --- Definitions table ------------------------------------------------
    lines.append("## Middleware Definitions")
    lines.append("")
    lines.append(
        "| Name | File | Method? | Factory? | Before | After | Short-circuits | Description |"
    )
    lines.append(
        "|------|------|---------|----------|--------|-------|----------------|-------------|"
    )
    for d in sorted(defs, key=lambda x: (x.file, x.name)):
        method = f"`{d.receiver_type}`" if d.is_method else "—"
        factory = "✓" if d.is_factory else "—"
        before = "✓" if d.runs_before else "—"
        after = "✓" if d.runs_after else "—"
        sc = "✋ yes" if d.short_circuits else "—"
        lines.append(
            f"| `{d.name}` | `{d.file}:{d.line}` | {method} | {factory} | "
            f"{before} | {after} | {sc} | {describe_middleware(d)} |"
        )
    lines.append("")

    # --- Chain sites ------------------------------------------------------
    lines.append("## Chain Sites")
    lines.append("")
    for c in sorted(chains, key=lambda x: (x.file, x.line)):
        lines.append(
            f"### `{c.router}` — `{c.file}:{c.line}` ({c.pattern})"
        )
        lines.append("")
        lines.append("```go")
        lines.append(c.raw)
        lines.append("```")
        lines.append("")
        lines.append("**Execution order** (outer → inner):")
        lines.append("")
        for i, name in enumerate(c.links, start=1):
            d = defs_by_name.get(name)
            tag = ""
            if d:
                bits = []
                if d.short_circuits:
                    bits.append("✋ short-circuits")
                if d.runs_before and d.runs_after:
                    bits.append("wraps (before+after)")
                elif d.runs_before:
                    bits.append("runs before handler")
                elif d.runs_after:
                    bits.append("runs after handler")
                if bits:
                    tag = f" — _{'; '.join(bits)}_"
            lines.append(f"{i}. `{name}`{tag}")
        lines.append("")
        lines.append("**Visual chain:**")
        lines.append("")
        lines.append("```")
        lines.append(visual_chain(c.links, defs_by_name))
        lines.append("```")
        lines.append("")

    # --- Global handler chain --------------------------------------------
    global_chains = [c for c in chains if c.pattern == "manual-wrap"]
    if global_chains:
        lines.append("## Global Handler Chain")
        lines.append("")
        lines.append(
            "The outermost HTTP handler in `main.go` wraps the router with "
            "cross-cutting middleware. This is the request pipeline every "
            "API call traverses, in order:"
        )
        lines.append("")
        # Pick the longest chain — that's the global wrap.
        longest = max(global_chains, key=lambda c: len(c.links), default=None)
        if longest:
            lines.append("```")
            lines.append(visual_chain(longest.links, defs_by_name))
            lines.append("```")
            lines.append("")

    # --- Per-router summaries --------------------------------------------
    use_chains = [c for c in chains if c.pattern == "use"]
    if use_chains:
        lines.append("## Per-Router Middleware Stacks")
        lines.append("")
        # Group by router name.
        by_router: Dict[str, List[ChainSite]] = {}
        for c in use_chains:
            by_router.setdefault(c.router, []).append(c)
        for router in sorted(by_router):
            sites = by_router[router]
            # Merge all .Use calls on the same router across files (tests + main).
            all_links: List[str] = []
            seen: Set[int] = set()
            for c in sorted(sites, key=lambda x: (x.file, x.line)):
                for l in c.links:
                    all_links.append(l)
            lines.append(f"### `{router}`")
            lines.append("")
            lines.append(
                f"Applied at {len(sites)} site(s); merged middleware order:"
            )
            lines.append("")
            lines.append("```")
            lines.append(visual_chain(all_links, defs_by_name))
            lines.append("```")
            lines.append("")

    # --- Rate-limit sites -------------------------------------------------
    rl_chains = [c for c in chains if c.pattern == "ratelimit"]
    if rl_chains:
        lines.append("## Rate-Limited Endpoints")
        lines.append("")
        lines.append(
            "These endpoints are wrapped with `RateLimitHandler` — requests "
            "exceeding the configured quota are rejected with HTTP 429 before "
            "the handler runs."
        )
        lines.append("")
        lines.append("| File | Line | Call |")
        lines.append("|------|------|------|")
        for c in sorted(rl_chains, key=lambda x: (x.file, x.line)):
            lines.append(f"| `{c.file}` | {c.line} | `{c.raw}` |")
        lines.append("")

    # --- Recommendations --------------------------------------------------
    lines.append("## Recommendations")
    lines.append("")
    sc_defs = [d for d in defs if d.short_circuits]
    if sc_defs:
        lines.append(
            f"- ✋ **{len(sc_defs)} middleware short-circuit.** Make sure logs / "
            "metrics are emitted *before* the short-circuit so rejected "
            "requests are still observable. Short-circuiting middleware:"
        )
        for d in sc_defs:
            lines.append(f"    - `{d.name}` (`{d.file}:{d.line}`)")
    after_only = [d for d in defs if d.runs_after and not d.runs_before]
    if after_only:
        lines.append("")
        lines.append(
            f"- 🔄 **{len(after_only)} middleware run only after the handler** "
            "(observability / cleanup). These don't block the request — "
            "good. Just confirm they're cheap:"
        )
        for d in after_only:
            lines.append(f"    - `{d.name}` (`{d.file}:{d.line}`)")
    lines.append("")
    lines.append(
        "- Run `go vet ./...` and consider `go tool pprof` to validate that "
        "the middleware stack isn't a hotspot under load."
    )
    lines.append("")
    return "\n".join(lines)


def emit_json(
    defs: List[MiddlewareDef],
    chains: List[ChainSite],
    repo: Path,
) -> str:
    payload = {
        "repository": str(repo),
        "summary": {
            "middleware_definitions": len(defs),
            "chain_sites": len(chains),
            "short_circuiting": sum(1 for d in defs if d.short_circuits),
            "runs_before": sum(1 for d in defs if d.runs_before),
            "runs_after": sum(1 for d in defs if d.runs_after),
        },
        "definitions": [asdict(d) for d in defs],
        "chains": [
            {
                "router": c.router,
                "file": c.file,
                "line": c.line,
                "pattern": c.pattern,
                "links": c.links,
                "raw": c.raw,
                "visual": visual_chain(c.links, {d.name: d for d in defs}),
            }
            for c in chains
        ],
    }
    return json.dumps(payload, indent=2)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def analyze(repo: Path, include_tests: bool = False) -> Tuple[List[MiddlewareDef], List[ChainSite]]:
    files = find_go_files(repo, include_tests=include_tests)
    print(f"  Scanning {len(files)} .go files", file=sys.stderr)

    # Pass 1: collect every middleware definition. We need the full set of
    # names before parsing manual-wrap chains so we can filter constructor
    # calls (`x := NewFoo(db)`) from real middleware wraps
    # (`handler := Recovery(BodySizeLimit(...))`).
    file_data: List[Tuple[Path, str, str]] = []
    defs: Dict[str, MiddlewareDef] = {}
    for f in files:
        try:
            content = f.read_text(encoding="utf-8", errors="replace")
        except Exception as exc:
            print(f"  ! could not read {f}: {exc}", file=sys.stderr)
            continue
        package_m = RE_PACKAGE.search(content)
        package = package_m.group(1) if package_m else ""
        rel = str(f.relative_to(repo))
        file_data.append((f, content, rel))
        for d in parse_middleware_defs(content, rel, package):
            key = d.name
            if key not in defs:
                defs[key] = d

    known = set(defs.keys())
    use_chains: List[ChainSite] = []
    wrap_chains: List[ChainSite] = []
    rl_chains: List[ChainSite] = []
    for _f, content, rel in file_data:
        use_chains.extend(parse_use_chains(content, rel))
        wrap_chains.extend(parse_manual_wrap_chains(
            content, rel, known_middleware_names=known
        ))
        rl_chains.extend(parse_ratelimit_chains(content, rel))

    use_chains = consolidate_use_chains(use_chains)
    all_chains = use_chains + wrap_chains + rl_chains

    return list(defs.values()), all_chains


def main():
    ap = argparse.ArgumentParser(
        prog="graphify middleware",
        description="Go HTTP middleware chain visualizer.",
    )
    ap.add_argument("path", nargs="?", default=".", help="Path to the Go project.")
    ap.add_argument("--out", "-o", help="Output markdown file (default: stdout).")
    ap.add_argument("--json", action="store_true", help="Emit JSON instead of markdown.")
    ap.add_argument(
        "--include-tests",
        action="store_true",
        help="Include *_test.go files (default: skip).",
    )
    args = ap.parse_args()

    repo = Path(args.path).resolve()
    print(f"graphify middleware — scanning {repo}", file=sys.stderr)
    if not repo.exists():
        print(f"error: path does not exist: {repo}", file=sys.stderr)
        sys.exit(1)

    defs, chains = analyze(repo, include_tests=args.include_tests)

    print(
        f"  Found {len(defs)} middleware definitions, {len(chains)} chain sites",
        file=sys.stderr,
    )

    if args.json:
        output = emit_json(defs, chains, repo)
    else:
        output = emit_markdown(defs, chains, repo)

    if args.out:
        Path(args.out).write_text(output, encoding="utf-8")
        print(f"Report written to {args.out}", file=sys.stderr)
    else:
        workspace_root = Path(os.environ.get("GRAPHIFY_ROOT", "/home/z/my-project"))
        public_dir = workspace_root / "public"
        if public_dir.exists():
            (public_dir / "middleware.json").write_text(
                emit_json(defs, chains, repo), encoding="utf-8"
            )
            (public_dir / "MIDDLEWARE.md").write_text(
                emit_markdown(defs, chains, repo), encoding="utf-8"
            )
            print(
                f"  Wrote public/middleware.json and public/MIDDLEWARE.md",
                file=sys.stderr,
            )
        print(output)


if __name__ == "__main__":
    main()
