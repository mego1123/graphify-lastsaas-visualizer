#!/usr/bin/env python3
"""
graphify_api_endpoints.py

Parses Go source code to map HTTP API endpoints to their handler functions.

It scans every .go file under the target path for router registration patterns:

    router.HandleFunc("/path", handler.Method)
    router.HandleFunc("/path", handlerFunc)
    mux.HandleFunc / http.HandleFunc / r.HandleFunc / router.HandleFunc / subRouter.HandleFunc
    router.Methods("GET").Path("/path").HandlerFunc(handler.Method)

It also understands sub-routers built via `parent.PathPrefix("/x").Subrouter()`
and the rate-limited / auth-wrapped variants:

    guarded.HandleFunc("/auth/login", rateLimiter.RateLimitHandler(
        middleware.LoginAttemptLimit,
        func(r *http.Request) string { return middleware.GetClientIP(r) },
        authHandler.Login,
    )).Methods("POST")

    guarded.Handle("/plans", authMiddleware.RequireAuth(http.HandlerFunc(
        plansHandler.ListPlansPublic,
    ))).Methods("GET")

For every endpoint it extracts: HTTP method, full URL path, handler function
name, the .go file/line that declares the route, and the handler's struct
(if any). When a `graph.json` is available (built by the graphify tooling)
the script cross-references each handler method against the graph to attach
its community + degree.

Outputs:
  - a JSON report (default: api-endpoints.json next to the script)
  - a Markdown report (default: API_ENDPOINTS.md next to the script)

CLI:
  python graphify_api_endpoints.py [path] [--out report.md] [--json out.json]
                                   [--graph graph.json] [--no-skip-tests]

`path` defaults to the current working directory.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Go source tokenisation helpers
# ---------------------------------------------------------------------------

# Match: <var> := <parent>.PathPrefix("<prefix>").Subrouter()
# Captures: var name, parent var, prefix string (may be empty).
SUBROUTER_RE = re.compile(
    r'(\w+)\s*:?=\s*(\w+)\.PathPrefix\(\s*"([^"]*)"\s*\)\.Subrouter\(\)'
)

# Match the start of a router.<HandleFunc|Handle>("path", ...) call.
# Captures: router var, call kind (HandleFunc | Handle), path string.
# Path may be empty (subrouter routes registered with HandleFunc("")).
ROUTER_CALL_RE = re.compile(
    r'(\w+)\.(HandleFunc|Handle)\(\s*"([^"]*)"\s*,'
)

# Match a trailing `.Methods("GET")` (possibly on a later line).
METHODS_RE = re.compile(r'\.Methods\(\s*"([A-Z]+)"\s*\)')

# Match the gorilla/mux chained form:
#   r.Methods("GET").Path("/x").HandlerFunc(handler.X)
CHAIN_RE = re.compile(
    r'(\w+)\.Methods\(\s*"([A-Z]+)"\s*\)\s*\.Path\(\s*"([^"]+)"\s*\)'
    r'\s*\.(HandlerFunc|Handler)\('
)

# Match: <var> := handlers.NewXHandler(...)
# We use the constructor name to derive the struct name (NewAuthHandler -> AuthHandler).
HANDLER_VAR_RE = re.compile(
    r'(\w+)\s*:?=\s*handlers\.New(\w+)\s*\('
)

# Match any `var.Method` or `var.Func` reference (no parens) — used to scan
# handler expressions for the actual handler.
MEMBER_REF_RE = re.compile(r'\b([a-zA-Z_]\w*)\.([A-Z]\w*)\b')

# Match a package-level handler reference like `handlers.DocsHTML` (no method,
# but capitalised member on the `handlers` package).
PACKAGE_FUNC_REF_RE = re.compile(r'\bhandlers\.([A-Z]\w*)\b')


def _strip_comments_and_strings_aware(text: str) -> str:
    """Replace Go comments and string/rune literals with whitespace so the
    regex-based scanner never gets confused by `//` or `"` inside them.

    We keep newlines so line numbers stay intact.
    """
    out: List[str] = []
    i = 0
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
                out.append(c)
            else:
                out.append(' ')
            i += 1
            continue
        if in_block_comment:
            if c == '*' and nxt == '/':
                in_block_comment = False
                out.append('  ')
                i += 2
                continue
            if c == '\n':
                out.append('\n')
            else:
                out.append(' ')
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
            if c == '\n':
                out.append('\n')
            else:
                out.append(' ')
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
        # Not in any string/comment.
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


def _read_balanced(text: str, open_idx: int) -> Tuple[Optional[str], int]:
    """Given `text` and an index pointing at an opening `(`, return
    `(content, end_idx)` where content is everything inside the outermost
    parens (excluding them) and `end_idx` is the index *after* the matching
    close paren. Returns `(None, -1)` if unbalanced.
    """
    assert text[open_idx] == '('
    depth = 0
    i = open_idx
    n = len(text)
    while i < n:
        c = text[i]
        if c == '(':
            depth += 1
        elif c == ')':
            depth -= 1
            if depth == 0:
                return text[open_idx + 1:i], i + 1
        i += 1
    return None, -1


def _line_number(text: str, idx: int) -> int:
    """Return the 1-based line number for a character index."""
    return text.count('\n', 0, idx) + 1


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class Endpoint:
    method: str
    path: str
    handler_func: str            # e.g. "AuthHandler.Login" or "handlers.DocsHTML"
    handler_struct: Optional[str] = None   # e.g. "AuthHandler"
    handler_method: Optional[str] = None   # e.g. "Login"
    handler_var: Optional[str] = None      # source var (e.g. "authHandler")
    route_file: Optional[str] = None       # file where route was registered
    route_line: int = 0
    handler_file: Optional[str] = None     # file where the handler is defined
    community: Optional[int] = None
    community_name: Optional[str] = None
    degree: Optional[int] = None
    node_id: Optional[str] = None
    middleware: List[str] = field(default_factory=list)
    prefix: str = ""             # matched prefix group (e.g. "/api/auth")
    raw_handler_expr: Optional[str] = None  # original handler expr (debug)


@dataclass
class ParsedFile:
    path: Path
    subrouters: Dict[str, Tuple[str, str]]  # var -> (parent_var, prefix)
    handler_vars: Dict[str, str]            # var -> struct name
    endpoints: List[Endpoint] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Per-file parsing
# ---------------------------------------------------------------------------

# Standard middleware wrappers we want to peel off when looking for the real
# handler inside a `.Handle(...)` or `.HandleFunc(...)` expression.
WRAPPER_FUNCS = {
    "RateLimitHandler", "RequireAuth", "RequireRole", "RequireTenant",
    "RequireRootTenant", "RequireActiveBilling", "HandlerFunc",
}


def _extract_handler_ref(expr: str,
                         handler_vars: Dict[str, str]) -> Tuple[Optional[str], Optional[str], Optional[str], List[str]]:
    """Given the handler expression (the args of HandleFunc/Handle after the
    path string, up to the trailing `.Methods(...)`), return:
      (handler_func, handler_struct, handler_method, middleware_chain)

    `handler_func` is a friendly label like "AuthHandler.Login" or
    "handlers.DocsHTML" or "<inline>".
    """
    expr = expr.strip()
    middleware_chain: List[str] = []

    # Collect wrappers we see (best-effort, ordered by appearance).
    for w in WRAPPER_FUNCS:
        # Match `pkg.Wrapper(` or `Wrapper(` to record middleware presence.
        m = re.search(r'\b(\w+\.)?' + w + r'\(', expr)
        if m:
            middleware_chain.append(w)

    # 1. Anonymous function literal — `func(w http.ResponseWriter, r *http.Request) {...}`
    if expr.startswith('func(') or expr.startswith('func ('):
        return ("<inline>", None, None, middleware_chain)

    # 2. Package-level handler reference: `handlers.DocsHTML`
    m = PACKAGE_FUNC_REF_RE.search(expr)
    if m and not _is_inside_rate_limiter_arg(expr, m.start()):
        # Make sure it's the top-level expression (not buried in an arg list
        # we should peel). If the whole expr starts with this ref or with
        # wrappers around it, treat it as the handler.
        ref = 'handlers.' + m.group(1)
        # Sanity: this should be the only handler-shaped ref in the expr
        # OR the last one (rate-limited case has middleware lambdas).
        all_refs = PACKAGE_FUNC_REF_RE.findall(expr)
        if all_refs and all_refs[-1] == m.group(1):
            return (ref, None, m.group(1), middleware_chain)

    # 3. Collect all member refs and prefer ones whose var is a known handler var.
    candidate_refs: List[Tuple[str, str, int]] = []
    for mm in MEMBER_REF_RE.finditer(expr):
        var = mm.group(1)
        method = mm.group(2)
        # Skip false positives like `middleware.RequireRole`, `http.HandlerFunc`,
        # `models.RoleOwner`, `authMiddleware.RequireAuth` — these are wrappers,
        # not the actual handler.
        if var in {'middleware', 'http', 'models', 'mux', 'r', 'fmt', 'strings',
                   'context', 'time', 'os', 'syscall', 'signal', 'path', 'filepath',
                   'bson', 'options', 'primitive'}:
            continue
        if method in WRAPPER_FUNCS:
            continue
        candidate_refs.append((var, method, mm.start()))

    # Prefer refs whose var is a registered handler var (e.g. `authHandler`).
    handler_match = None
    for var, method, _ in candidate_refs:
        if var in handler_vars:
            handler_match = (var, method)
            break

    # Fallback: if no handler var match, take the LAST candidate (rate-limited
    # routes pass the real handler as the final positional arg).
    if handler_match is None and candidate_refs:
        var, method, _ = candidate_refs[-1]
        handler_match = (var, method)

    if handler_match is None:
        # Last resort: maybe it's a bare function name passed as a value.
        bare = re.match(r'^\s*([A-Z]\w*)\s*[\),]', expr)
        if bare:
            return (bare.group(1), None, bare.group(1), middleware_chain)
        return (None, None, None, middleware_chain)

    var, method = handler_match
    struct = handler_vars.get(var)
    if struct:
        return (f"{struct}.{method}", struct, method, middleware_chain)
    # Unknown var (e.g. a wrapper struct we didn't recognise) — still emit it.
    return (f"{var}.{method}", None, method, middleware_chain)


def _is_inside_rate_limiter_arg(expr: str, idx: int) -> bool:
    """Heuristic: returns True if `idx` is not the *last* `handlers.X`
    reference in `expr`. Used to skip non-handler `handlers.X` matches
    inside the RateLimitHandler arg list.
    """
    matches = list(PACKAGE_FUNC_REF_RE.finditer(expr))
    if not matches:
        return False
    return matches[-1].start() != idx


# ---------------------------------------------------------------------------
# Graph cross-reference
# ---------------------------------------------------------------------------

class GraphIndex:
    """Indexes graph.json for fast handler lookups."""

    def __init__(self, graph_path: Optional[Path]):
        self.nodes_by_struct_method: Dict[Tuple[str, str], dict] = {}
        self.nodes_by_pkg_func: Dict[str, dict] = {}
        self.degrees: Dict[str, int] = {}
        self.community_labels: Dict[int, str] = {}
        self._all_nodes_by_id: Dict[str, dict] = {}
        self.loaded = False
        self.graph_path = graph_path
        if graph_path and graph_path.exists():
            self._load(graph_path)

    def _load(self, path: Path) -> None:
        try:
            with path.open('r', encoding='utf-8') as f:
                g = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            print(f"  ! could not load graph.json: {e}", file=sys.stderr)
            return
        self.loaded = True
        nodes = g.get('nodes', [])
        links = g.get('links', g.get('edges', []))

        # Index all nodes by id (used to fill in handler_file later).
        for n in nodes:
            nid = n.get('id')
            if nid:
                self._all_nodes_by_id[nid] = n

        # Compute degree.
        deg: Dict[str, int] = defaultdict(int)
        for link in links:
            src = link.get('source')
            tgt = link.get('target')
            if src:
                deg[src] += 1
            if tgt and tgt != src:
                deg[tgt] += 1
        self.degrees = dict(deg)

        # Index handler-struct method nodes by (struct, method).
        # Label format is `.Method()` for receiver methods.
        for n in nodes:
            label = n.get('label', '')
            sf = n.get('source_file', '')
            if not sf.startswith('backend/internal/api/handlers/'):
                continue
            if label.startswith('.') and label.endswith('()'):
                method = label[1:-2]
                # Find the struct this method belongs to: look at the file
                # node's name (e.g. `auth.go` -> `auth`) and try a few
                # struct candidates.
                # The node id for an AuthHandler method is `handlers_authhandler_<method>`.
                nid = n.get('id', '')
                m = re.match(r'handlers_(\w+?)_(\w+)$', nid)
                if m:
                    struct = m.group(1)
                    # Camel-case the struct properly (Authhandler -> AuthHandler
                    # isn't perfect, but graphify uses lowercased ids so the
                    # *label* of the struct node is what we want).
                    struct_label = self._struct_label(struct, sf)
                    self.nodes_by_struct_method[(struct_label, method)] = n
            elif label.endswith('()') and not label.startswith('.'):
                # Package-level func like `DocsHTML()`.
                func_name = label[:-2]
                self.nodes_by_pkg_func[func_name] = n
            # Also collect struct-name -> community for community label lookup.
        # Load community labels (if a graph-communities.json exists alongside).
        comm_path = path.parent / 'graph-communities.json'
        if comm_path.exists():
            try:
                with comm_path.open('r', encoding='utf-8') as f:
                    comms = json.load(f)
                for c in comms:
                    self.community_labels[c['id']] = c.get('label', f"Community {c['id']}")
            except (OSError, json.JSONDecodeError):
                pass

    def _struct_label(self, struct_key: str, source_file: str) -> str:
        """Map the graph node-id fragment (e.g. `authhandler`) back to the
        real struct label (e.g. `AuthHandler`) by looking up the file's
        struct nodes. Falls back to capitalising the key.
        """
        # Cache the struct labels per file the first time we need them.
        cache = self.__dict__.setdefault('_struct_label_cache', {})
        if source_file in cache:
            return cache[source_file].get(struct_key, struct_key.capitalize())
        # Lazy-load: re-open graph.json is wasteful, so we cache from the
        # already-loaded nodes (we kept a reference at load time).
        # Walk self._struct_nodes_by_file.
        snodes = self._struct_nodes_by_file.get(source_file, {})
        cache[source_file] = snodes
        return snodes.get(struct_key, struct_key.capitalize())

    @property
    def _struct_nodes_by_file(self) -> Dict[str, Dict[str, str]]:
        """Lazily computed: file -> {struct_key: struct_label}."""
        if not self.loaded or self.graph_path is None:
            return {}
        cache = self.__dict__.get('_snbf')
        if cache is not None:
            return cache
        cache = defaultdict(dict)
        try:
            with self.graph_path.open('r', encoding='utf-8') as f:
                g = json.load(f)
        except (OSError, json.JSONDecodeError):
            self.__dict__['_snbf'] = cache
            return cache
        for n in g.get('nodes', []):
            sf = n.get('source_file', '')
            label = n.get('label', '')
            if not sf.startswith('backend/internal/api/handlers/'):
                continue
            nid = n.get('id', '')
            # Struct node: id is `handlers_<lower_struct>` and label is the
            # PascalCase struct name with no trailing parens.
            m = re.match(r'handlers_(\w+)$', nid)
            if m and not label.endswith('()') and not label.startswith('.'):
                cache[sf][m.group(1)] = label
        self.__dict__['_snbf'] = cache
        return cache

    def lookup(self, handler_func: str, handler_struct: Optional[str],
               handler_method: Optional[str]) -> Tuple[Optional[int], Optional[str], Optional[int], Optional[str], Optional[str]]:
        """Return (community, community_name, degree, node_id, source_file) for a handler."""
        if not self.loaded:
            return (None, None, None, None, None)
        node = None
        # 1. Struct method.
        if handler_struct and handler_method:
            node = self.nodes_by_struct_method.get((handler_struct, handler_method))
        # 2. Package-level func.
        if node is None and handler_method and not handler_struct:
            node = self.nodes_by_pkg_func.get(handler_method)
        if node is None:
            return (None, None, None, None, None)
        nid = node.get('id')
        comm = node.get('community')
        comm_name = node.get('community_name') or self.community_labels.get(comm) if comm is not None else None
        deg = self.degrees.get(nid) if nid else None
        sf = node.get('source_file')
        return (comm, comm_name, deg, nid, sf)


# ---------------------------------------------------------------------------
# File scanning
# ---------------------------------------------------------------------------

def parse_go_file(path: Path, repo_root: Path,
                  skip_tests: bool) -> ParsedFile:
    """Parse a single .go file and return endpoints + subrouter info."""
    try:
        raw = path.read_text(encoding='utf-8', errors='replace')
    except OSError:
        return ParsedFile(path=path, subrouters={}, handler_vars={})
    if skip_tests and path.name.endswith('_test.go'):
        return ParsedFile(path=path, subrouters={}, handler_vars={})

    # Strip comments and string contents so regex scanning is safe.
    # We keep string *delimiters* (so quotes are still there) but blank out
    # the contents — *except* the path strings we need to read. Compromise:
    # use the raw text but be careful. The patterns we match (HandleFunc,
    # PathPrefix, etc.) don't generally appear inside Go string literals in
    # this codebase, and we use a balanced-paren reader for handler args.
    text = raw  # use raw text; we handle string literals in _read_balanced.

    # 1. Collect handler var -> struct name mappings.
    handler_vars: Dict[str, str] = {}
    for m in HANDLER_VAR_RE.finditer(text):
        var = m.group(1)
        ctor = m.group(2)
        # `NewAuthHandler` -> `AuthHandler` (strip leading `New`).
        struct = ctor[3:] if ctor.startswith('New') else ctor
        handler_vars[var] = struct

    # 2. Collect subrouter var -> (parent, prefix).
    # Walk through matches in order so we can resolve transitively.
    raw_subrouters: List[Tuple[str, str, str, int]] = []
    for m in SUBROUTER_RE.finditer(text):
        var = m.group(1)
        parent = m.group(2)
        prefix = m.group(3)
        raw_subrouters.append((var, parent, prefix, m.start()))

    # Resolve to absolute prefixes (parent's prefix + this prefix).
    # We process them in source order; later subrouters may reference earlier ones.
    resolved: Dict[str, Tuple[str, str]] = {}  # var -> (root_router_var, full_prefix)
    # Seed with the top-level router vars we know about (router, mux, r, http, etc.)
    # by giving them an empty prefix.
    known_routers = {'router', 'mux', 'r', 'mainRouter', 'http', 'api'}
    for var in known_routers:
        resolved[var] = (var, '')

    # Iterate to fixpoint (subrouters can reference subrouters).
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

    # Drop the seeded entries (we only care about actual subrouter vars).
    subrouters = {v: (p[0], p[1]) for v, p in resolved.items()
                  if v not in known_routers}

    parsed = ParsedFile(path=path, subrouters=subrouters,
                        handler_vars=handler_vars)

    # 3. Scan for HandleFunc / Handle calls.
    for m in ROUTER_CALL_RE.finditer(text):
        router_var = m.group(1)
        call_kind = m.group(2)
        path_str = m.group(3)
        # Find the opening paren of the args list.
        # The match ends at the `,` after the path string.
        # Locate the open paren that began the call: search backward from
        # the path-string start for `(`.
        # Easier: scan forward from the end of the match for the balanced
        # closing paren of the OUTER call.
        # The args list starts at the position of the `(` before the path
        # string. The match ended right after the comma — we need the full
        # contents of the call.
        # Re-find the opening paren: it's between the call kind and the path
        # string. Look for `(` after `call_kind`.
        call_start = m.start()
        open_paren_idx = text.find('(', m.start(2))
        if open_paren_idx == -1 or open_paren_idx > m.end():
            continue
        args, close_idx = _read_balanced(text, open_paren_idx)
        if args is None:
            continue
        # The args contain: "path", handler_expr
        # Strip the leading path string (with optional trailing comma).
        # The args string starts with `"path"` followed by `,` then the
        # handler expr.
        # Match: `"<path>"\s*,\s*(.*)`
        am = re.match(r'\s*"' + re.escape(path_str) + r'"\s*,\s*(.*)',
                      args, re.DOTALL)
        if not am:
            # The path string in the file may contain escape sequences; try
            # a looser match.
            am = re.match(r'\s*"[^"]*"\s*,\s*(.*)', args, re.DOTALL)
            if not am:
                continue
        handler_expr = am.group(1).strip()

        # Look for `.Methods("X")` immediately after the closing paren.
        method = "ANY"
        tail = text[close_idx:close_idx + 200]
        mm = METHODS_RE.search(tail)
        if mm and mm.start() < 50:
            method = mm.group(1)

        # Build the full path from the subrouter's prefix.
        prefix_info = subrouters.get(router_var)
        if prefix_info:
            full_prefix = prefix_info[1]
        elif router_var in resolved:
            full_prefix = resolved[router_var][1]
        else:
            full_prefix = ''
        full_path = full_prefix + path_str
        # Normalise: collapse duplicate slashes from empty-prefix subrouters.
        full_path = re.sub(r'/+', '/', full_path)
        if not full_path.startswith('/'):
            full_path = '/' + full_path

        # Extract the handler reference.
        handler_func, handler_struct, handler_method, mw = _extract_handler_ref(
            handler_expr, handler_vars)

        if handler_func is None:
            # Fall back to a raw label so the route isn't lost.
            handler_func = handler_expr[:80] + ('...' if len(handler_expr) > 80 else '')

        ep = Endpoint(
            method=method,
            path=full_path,
            handler_func=handler_func,
            handler_struct=handler_struct,
            handler_method=handler_method,
            handler_var=None,  # could set if needed
            route_file=str(path.relative_to(repo_root)) if _is_relative(path, repo_root) else str(path),
            route_line=_line_number(text, m.start()),
            middleware=mw,
            prefix=_categorise_prefix(full_path),
            raw_handler_expr=handler_expr[:120],
        )
        parsed.endpoints.append(ep)

    # 4. Scan for the chained `router.Methods("X").Path("/y").HandlerFunc(h)` form.
    for m in CHAIN_RE.finditer(text):
        router_var = m.group(1)
        method = m.group(2)
        path_str = m.group(3)
        call_kind = m.group(4)
        open_paren_idx = text.find('(', m.end() - 1)
        if open_paren_idx == -1:
            continue
        args, close_idx = _read_balanced(text, open_paren_idx)
        if args is None:
            continue
        handler_expr = args.strip()
        prefix_info = subrouters.get(router_var) or resolved.get(router_var)
        full_prefix = prefix_info[1] if prefix_info else ''
        full_path = re.sub(r'/+', '/', full_prefix + path_str)
        if not full_path.startswith('/'):
            full_path = '/' + full_path
        handler_func, handler_struct, handler_method, mw = _extract_handler_ref(
            handler_expr, handler_vars)
        if handler_func is None:
            handler_func = handler_expr[:80] + ('...' if len(handler_expr) > 80 else '')
        ep = Endpoint(
            method=method,
            path=full_path,
            handler_func=handler_func,
            handler_struct=handler_struct,
            handler_method=handler_method,
            route_file=str(path.relative_to(repo_root)) if _is_relative(path, repo_root) else str(path),
            route_line=_line_number(text, m.start()),
            middleware=mw,
            prefix=_categorise_prefix(full_path),
            raw_handler_expr=handler_expr[:120],
        )
        parsed.endpoints.append(ep)

    return parsed


def _is_relative(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


# ---------------------------------------------------------------------------
# Prefix grouping
# ---------------------------------------------------------------------------

# Order matters — more specific prefixes first so /api/admin doesn't get
# bucketed into /api/auth (it wouldn't anyway, but keep it explicit).
PREFIX_GROUPS = [
    ("/api/auth",            "Auth"),
    ("/api/tenant",          "Tenant"),
    ("/api/messages",        "Messages"),
    ("/api/plans",           "Plans"),
    ("/api/credit-bundles",  "Credit Bundles"),
    ("/api/announcements",   "Announcements"),
    ("/api/usage",           "Usage"),
    ("/api/telemetry",       "Telemetry"),
    ("/api/billing",         "Billing"),
    ("/api/admin",           "Admin"),
    ("/api/branding",        "Branding"),
    ("/api/bootstrap",       "Bootstrap"),
    ("/api/docs",            "Docs"),
    ("/api",                 "API (other)"),
    ("/health",              "Health"),
    ("/",                    "Static / SPA"),
]


def _categorise_prefix(path: str) -> str:
    for prefix, label in PREFIX_GROUPS:
        if path == prefix or path.startswith(prefix + "/") or path == prefix.rstrip("/"):
            return prefix
    # Unknown — return the first path segment.
    parts = path.split("/", 2)
    if len(parts) > 1:
        seg = "/" + parts[1]
        return seg
    return path


# ---------------------------------------------------------------------------
# Cross-reference handlers with graph.json
# ---------------------------------------------------------------------------

def cross_reference(endpoints: List[Endpoint], graph: GraphIndex) -> None:
    for ep in endpoints:
        comm, comm_name, deg, nid, sf = graph.lookup(
            ep.handler_func, ep.handler_struct, ep.handler_method)
        ep.community = comm
        ep.community_name = comm_name
        ep.degree = deg
        ep.node_id = nid
        if sf:
            ep.handler_file = sf


# ---------------------------------------------------------------------------
# Output: JSON + Markdown
# ---------------------------------------------------------------------------

def build_json_report(endpoints: List[Endpoint], parsed_files: List[ParsedFile],
                      repo_root: Path, graph_path: Optional[Path]) -> dict:
    # Deduplicate identical endpoints that appear in both main.go and test
    # helpers (when --no-skip-tests is used).
    seen: Dict[Tuple[str, str, str], Endpoint] = {}
    for ep in endpoints:
        key = (ep.method, ep.path, ep.handler_func)
        if key not in seen:
            seen[key] = ep
    unique_eps = list(seen.values())

    # Group by prefix.
    by_prefix: Dict[str, List[Endpoint]] = defaultdict(list)
    for ep in unique_eps:
        by_prefix[ep.prefix].append(ep)
    for k in by_prefix:
        by_prefix[k].sort(key=lambda e: (e.path, e.method))

    prefix_summary = [
        {"prefix": p, "label": lbl, "count": len(by_prefix.get(p, []))}
        for p, lbl in PREFIX_GROUPS
        if p in by_prefix
    ]

    return {
        "repo": str(repo_root),
        "graph": str(graph_path) if graph_path else None,
        "graph_loaded": graph_path is not None and graph_path.exists(),
        "total_endpoints": len(unique_eps),
        "total_files_scanned": len(parsed_files),
        "files_with_routes": [
            str(pf.path.relative_to(repo_root)) if _is_relative(pf.path, repo_root) else str(pf.path)
            for pf in parsed_files if pf.endpoints
        ],
        "prefix_summary": prefix_summary,
        "by_prefix": {
            p: [asdict(ep) for ep in eps]
            for p, eps in by_prefix.items()
        },
        "endpoints": [asdict(ep) for ep in unique_eps],
    }


def build_markdown_report(endpoints: List[Endpoint], parsed_files: List[ParsedFile],
                          repo_root: Path, graph_path: Optional[Path]) -> str:
    seen: Dict[Tuple[str, str, str], Endpoint] = {}
    for ep in endpoints:
        key = (ep.method, ep.path, ep.handler_func)
        if key not in seen:
            seen[key] = ep
    unique_eps = list(seen.values())

    by_prefix: Dict[str, List[Endpoint]] = defaultdict(list)
    for ep in unique_eps:
        by_prefix[ep.prefix].append(ep)
    for k in by_prefix:
        by_prefix[k].sort(key=lambda e: (e.path, e.method))

    lines: List[str] = []
    lines.append("# API Endpoints Map")
    lines.append("")
    lines.append(f"- **Repo scanned:** `{repo_root}`")
    if graph_path:
        lines.append(f"- **Graph reference:** `{graph_path}` "
                     f"({'loaded' if graph_path.exists() else 'missing'})")
    else:
        lines.append("- **Graph reference:** none provided")
    lines.append(f"- **Files scanned:** {len(parsed_files)}")
    files_with_routes = [pf for pf in parsed_files if pf.endpoints]
    lines.append(f"- **Files with route registrations:** {len(files_with_routes)}")
    lines.append(f"- **Total endpoints:** {len(unique_eps)}")
    lines.append("")

    # Prefix summary table.
    lines.append("## Summary by prefix")
    lines.append("")
    lines.append("| Prefix | Label | Endpoints |")
    lines.append("| --- | --- | ---: |")
    for prefix, label in PREFIX_GROUPS:
        if prefix in by_prefix:
            lines.append(f"| `{prefix}` | {label} | {len(by_prefix[prefix])} |")
    lines.append("")

    # Per-prefix breakdown.
    for prefix, label in PREFIX_GROUPS:
        if prefix not in by_prefix:
            continue
        lines.append(f"## {label}  (`{prefix}`)")
        lines.append("")
        lines.append("| Method | Path | Handler | Struct | Method | Community | Degree | Handler File | Route File:Line |")
        lines.append("| --- | --- | --- | --- | --- | --- | ---: | --- | --- |")
        for ep in by_prefix[prefix]:
            struct = ep.handler_struct or "—"
            method = ep.handler_method or "—"
            comm = ep.community_name or (f"#{ep.community}" if ep.community is not None else "—")
            deg = str(ep.degree) if ep.degree is not None else "—"
            route_loc = f"{ep.route_file}:{ep.route_line}" if ep.route_file else "—"
            handler_loc = ep.handler_file or "—"
            mw = f" `<{', '.join(ep.middleware)}>`" if ep.middleware else ""
            lines.append(
                f"| `{ep.method}` | `{ep.path}` | `{ep.handler_func}`{mw} "
                f"| {struct} | {method} | {comm} | {deg} | `{handler_loc}` | `{route_loc}` |"
            )
        lines.append("")

    # Handler coverage: which handler structs were referenced.
    lines.append("## Handler structs referenced")
    lines.append("")
    structs: Dict[str, int] = defaultdict(int)
    for ep in unique_eps:
        if ep.handler_struct:
            structs[ep.handler_struct] += 1
    if structs:
        lines.append("| Struct | Endpoints |")
        lines.append("| --- | ---: |")
        for s, c in sorted(structs.items(), key=lambda kv: -kv[1]):
            lines.append(f"| `{s}` | {c} |")
    else:
        lines.append("_No handler structs identified._")
    lines.append("")

    # Unmatched handlers (no graph node).
    if graph_path and graph_path.exists():
        unmatched = [ep for ep in unique_eps if ep.node_id is None
                     and ep.handler_func not in ("<inline>",)]
        if unmatched:
            lines.append("## Handlers not found in graph.json")
            lines.append("")
            lines.append("These handlers were referenced from a route but could "
                         "not be matched to a node in `graph.json`.")
            lines.append("")
            lines.append("| Handler | Method | Path | Route File:Line |")
            lines.append("| --- | --- | --- | --- |")
            for ep in unmatched:
                route_loc = f"{ep.route_file}:{ep.route_line}" if ep.route_file else "—"
                lines.append(f"| `{ep.handler_func}` | `{ep.method}` | `{ep.path}` | `{route_loc}` |")
            lines.append("")

    # Notes.
    lines.append("## Notes")
    lines.append("")
    lines.append("- `degree` = number of graph edges (in + out) touching the handler node.")
    lines.append("- `<inline>` = anonymous `func(w, r)` literal registered as the handler.")
    lines.append("- Middleware column lists wrappers peeled to find the real handler "
                 "(e.g. `RateLimitHandler`, `RequireAuth`, `RequireRole`).")
    lines.append("- Sub-router prefixes (e.g. `/api`, `/api/auth`, `/api/admin`) are "
                 "resolved by tracking `PathPrefix(\"…\").Subrouter()` assignments.")
    lines.append("- `_test.go` files are skipped by default; pass `--no-skip-tests` "
                 "to include them (will produce duplicate routes from test helpers).")
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(
        prog="graphify_api_endpoints.py",
        description="Parse Go source to map HTTP API endpoints to handlers.")
    p.add_argument("path", nargs="?", default=".",
                   help="Repo path to scan (default: cwd)")
    p.add_argument("--out", default="API_ENDPOINTS.md",
                   help="Markdown output path (default: API_ENDPOINTS.md)")
    p.add_argument("--json", dest="json_out", default="api-endpoints.json",
                   help="JSON output path (default: api-endpoints.json)")
    p.add_argument("--graph", default=None,
                   help="Path to graph.json (default: auto-detect "
                        "<path>/graphify-out/graph.json or public/graph.json)")
    p.add_argument("--no-skip-tests", action="store_true",
                   help="Include _test.go files when scanning")
    args = p.parse_args(argv)

    repo_root = Path(args.path).resolve()
    if not repo_root.exists():
        print(f"error: path does not exist: {repo_root}", file=sys.stderr)
        return 2

    # Find graph.json.
    graph_path: Optional[Path] = None
    if args.graph:
        graph_path = Path(args.graph).resolve()
    else:
        candidates = [
            repo_root / "graphify-out" / "graph.json",
            repo_root / "public" / "graph.json",
            Path.cwd() / "public" / "graph.json",
            Path.cwd() / "graph.json",
        ]
        for c in candidates:
            if c.exists():
                graph_path = c
                break

    graph = GraphIndex(graph_path)

    # Walk all .go files.
    go_files: List[Path] = []
    for dirpath, dirnames, filenames in os.walk(repo_root):
        # Skip vendor / node_modules / .git / graphify-out cache.
        dirnames[:] = [d for d in dirnames if d not in {
            'vendor', 'node_modules', '.git', 'cache', '__pycache__'
        } and not d.startswith('.')]
        for fn in filenames:
            if fn.endswith('.go'):
                go_files.append(Path(dirpath) / fn)
    go_files.sort()

    parsed_files: List[ParsedFile] = []
    all_endpoints: List[Endpoint] = []
    for fp in go_files:
        pf = parse_go_file(fp, repo_root, skip_tests=not args.no_skip_tests)
        parsed_files.append(pf)
        all_endpoints.extend(pf.endpoints)

    # Cross-reference with graph.
    cross_reference(all_endpoints, graph)

    # Write outputs.
    json_out_path = Path(args.json_out).resolve()
    md_out_path = Path(args.out).resolve()

    json_report = build_json_report(all_endpoints, parsed_files, repo_root, graph_path)
    json_out_path.parent.mkdir(parents=True, exist_ok=True)
    json_out_path.write_text(json.dumps(json_report, indent=2), encoding='utf-8')
    print(f"wrote JSON: {json_out_path}  ({json_report['total_endpoints']} endpoints)")

    md_report = build_markdown_report(all_endpoints, parsed_files, repo_root, graph_path)
    md_out_path.parent.mkdir(parents=True, exist_ok=True)
    md_out_path.write_text(md_report, encoding='utf-8')
    print(f"wrote MD:   {md_out_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
