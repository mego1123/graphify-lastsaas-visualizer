#!/usr/bin/env python3
"""graphify db-queries — scan Go source code for MongoDB queries and map them
to their data models.

Walks every .go file under the target path, identifies MongoDB collection
operations (Find / FindOne / InsertOne / InsertMany / UpdateOne / UpdateMany /
DeleteOne / DeleteMany / Aggregate / CountDocuments), resolves the underlying
collection name (via direct ``db.Collection("name")`` calls or via accessor
methods like ``m.Users()`` defined in the codebase), extracts the query
filter fields from ``bson.D`` / ``bson.M`` literals, and maps each collection
to the Go struct that models it.

Usage:
    python graphify_db_queries.py [path] [--out report.md] [--json]

Examples:
    python graphify_db_queries.py /home/z/my-project/repos/lastsaas/backend
    python graphify_db_queries.py . --out db-queries.md --json
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

# ---------------------------------------------------------------------------
# Static configuration
# ---------------------------------------------------------------------------

# The 10 canonical mongo-driver collection methods we track.
OPERATIONS: tuple[str, ...] = (
    "Find",
    "FindOne",
    "InsertOne",
    "InsertMany",
    "UpdateOne",
    "UpdateMany",
    "DeleteOne",
    "DeleteMany",
    "Aggregate",
    "CountDocuments",
)

# A regex that captures any of those operations when called as a method.
# Example matches: ``.Find(``, ``.FindOne(``, ``.CountDocuments(``
OP_RE = re.compile(
    r"\.(" + "|".join(OPERATIONS) + r")\s*\("
)

# Direct collection access: ``db.Collection("name")`` or ``m.Database.Collection("name")``.
# Captures the literal collection name.
COLLECTION_LITERAL_RE = re.compile(
    r'\.Collection\(\s*"([^"]+)"\s*\)'
)

# Accessor method call: ``<expr>.Users()`` — the trailing ``()`` is required
# to distinguish from a struct field access. The accessor name (e.g. ``Users``)
# is captured and resolved to a collection name via the accessor map.
ACCESSOR_CALL_RE = re.compile(
    r"(?:[\w\.\[\]\*]+\.)?(\w+)\(\s*\)"
)

# Function declaration: ``func (recv) Name(args) (rets) {`` or ``func Name(...) {``.
FUNC_RE = re.compile(
    r"^func\s+(?:\([^)]*\)\s+)?([A-Za-z_]\w*)\s*[(<]"
)

# Variable aliasing a collection accessor result:
#   ``col := m.Database.Collection("plans")``
#   ``col := s.db.Plans()``
ALIAS_LITERAL_RE = re.compile(
    r"(\w+)\s*:?=\s*[\w\.\[\]\*]+\.Collection\(\s*\"([^\"]+)\"\s*\)"
)
ALIAS_ACCESSOR_RE = re.compile(
    r"(\w+)\s*:?=\s*[\w\.\[\]\*]+\.(\w+)\(\s*\)"
)

# bson.D blocks: ``bson.D{{Key: "f", Value: ...}, {"f2", v}}``.
# We capture the inner content and then pull keys out of it.
BSON_D_BLOCK_RE = re.compile(
    r'\bbson\.D\s*\{([^}]*)\}'
)
# Inside a bson.D block:
#   {Key: "field", Value: ...}    (named form)
#   {"field", value}              (positional form)
BSON_D_KEYVAL_NAMED_RE = re.compile(
    r'Key:\s*"([^"]+)"\s*,\s*Value:'
)
BSON_D_KEYVAL_POS_RE = re.compile(
    r'\{\s*"([^"]+)"\s*,'
)

# bson.M{"field": value, "other": value}
# Captures quoted keys. Operator keys ($set, $inc, ...) are filtered out.
BSON_M_RE = re.compile(
    r'\bbson\.M\s*\{([^}]*)\}'
)
BSON_M_KEY_RE = re.compile(
    r'"([^"]+)"\s*:'
)

# Known wrapper helpers that wrap a real mongo call. They mention the
# collection by string literal, e.g. ``testutil.CountDocuments(t, db, "users", bson.M{...})``.
WRAPPER_PATTERNS: list[tuple[re.Pattern, str]] = [
    (
        re.compile(r'testutil\.CountDocuments\s*\(\s*[^,]+,\s*[^,]+,\s*"([^"]+)"'),
        "CountDocuments",
    ),
]

# Acronyms that should remain uppercase when converting snake_case → PascalCase.
ACRONYMS = {
    "api": "API",
    "sso": "SSO",
    "totp": "TOTP",
    "id": "ID",
    "url": "URL",
    "uri": "URI",
    "sql": "SQL",
    "json": "JSON",
    "xml": "XML",
    "http": "HTTP",
    "https": "HTTPS",
    "ip": "IP",
    "tcp": "TCP",
    "udp": "UDP",
    "ssl": "SSL",
    "tls": "TLS",
    "oauth": "OAuth",
    "uuid": "UUID",
    "guid": "GUID",
    "uid": "UID",
    "db": "DB",
    "ui": "UI",
    "cpu": "CPU",
    "ram": "RAM",
    "smtp": "SMTP",
    "imap": "IMAP",
    "pop": "POP",
    "ws": "WS",
    "wss": "WSS",
    "rpc": "RPC",
    "grpc": "GRPC",
    "html": "HTML",
    "css": "CSS",
    "js": "JS",
    "ts": "TS",
    "ftp": "FTP",
    "ssh": "SSH",
    "vpn": "VPN",
    "ttl": "TTL",
    "mfa": "MFA",
    "sms": "SMS",
    "pdf": "PDF",
    "csv": "CSV",
    "yaml": "YAML",
    "yml": "YML",
}

# Irregular plural → singular rules for collection → model mapping.
SINGULAR_RULES = {
    "ies": "y",   # tenants → tenant, properties → property (suffix "ies")
    "ses": "s",   # analyses → analysis (rough)
    "ches": "ch", # watches → watch
    "shes": "sh",
    "xes": "x",
    "zes": "z",
    "sso_connections": "sso_connection",
    "men": "man",
    "children": "child",
}

# Known one-off collection → model overrides for cases where the heuristic
# would otherwise pick the wrong struct. These are derived from the codebase
# under backend/internal/models/.
COLLECTION_MODEL_OVERRIDES: dict[str, str] = {
    "refresh_tokens": "RefreshToken",
    "verification_tokens": "VerificationToken",
    "oauth_states": "OAuthState",
    "revoked_tokens": "RevokedToken",
    "tenant_memberships": "TenantMembership",
    "audit_log": "SystemLog",          # audit_log is logged into SystemLog entries
    "system_logs": "SystemLog",
    "config_vars": "ConfigVar",
    "system_config": "SystemConfig",
    "system_nodes": "SystemNode",
    "system_metrics": "SystemMetric",
    "financial_transactions": "FinancialTransaction",
    "stripe_mappings": "StripeMapping",
    "daily_metrics": "DailyMetric",
    "leader_locks": "LeaderLock",
    "webhook_events": "WebhookEvent",
    "webhook_deliveries": "WebhookDelivery",
    "api_keys": "APIKey",
    "credit_bundles": "CreditBundle",
    "custom_pages": "CustomPage",
    "branding_assets": "BrandingAsset",
    "branding_config": "BrandingConfig",
    "webauthn_credentials": "WebAuthnCredential",
    "webauthn_sessions": "WebAuthnSession",
    "sso_connections": "SSOConnection",
    "auth_codes": "AuthCode",
    "usage_events": "UsageEvent",
    "telemetry_events": "TelemetryEvent",
    "event_definitions": "EventDefinition",
    "impersonation_logs": "SystemLog",   # also stored as SystemLog entries
    "rate_limits": "RateLimitEntry",
    "counters": "InvoiceCounter",
}


# ---------------------------------------------------------------------------
# Data containers
# ---------------------------------------------------------------------------


@dataclass
class Query:
    """A single MongoDB query occurrence."""

    file: str
    line: int
    function: str
    collection: str
    operation: str
    model: Optional[str]
    model_file: Optional[str]
    filter_fields: list[str] = field(default_factory=list)
    snippet: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class CollectionInfo:
    """Aggregated info about a single collection."""

    name: str
    accessors: list[str] = field(default_factory=list)  # e.g. ["Users", "User"]
    model: Optional[str] = None
    model_file: Optional[str] = None
    files: set[str] = field(default_factory=set)
    operations: Counter = field(default_factory=Counter)
    total_queries: int = 0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def singularize_collection(name: str) -> str:
    """Best-effort singularize a collection name."""
    if name in COLLECTION_MODEL_OVERRIDES:
        # Use the override as-is for pluralization concerns.
        stem = name
    else:
        stem = name
    for suffix, repl in SINGULAR_RULES.items():
        if stem.endswith(suffix):
            return stem[: -len(suffix)] + repl
    if stem.endswith("s") and not stem.endswith("ss"):
        return stem[:-1]
    return stem


def snake_to_pascal(snake: str) -> str:
    """Convert snake_case → PascalCase, honouring known acronyms."""
    parts = [p for p in snake.split("_") if p]
    out: list[str] = []
    for p in parts:
        lower = p.lower()
        if lower in ACRONYMS:
            out.append(ACRONYMS[lower])
        else:
            out.append(p[:1].upper() + p[1:])
    return "".join(out)


def collect_struct_definitions(repo_root: Path) -> dict[str, str]:
    """Walk repo for Go files and return {struct_name: file_path}."""
    structs: dict[str, str] = {}
    struct_re = re.compile(r"^type\s+([A-Z]\w*)\s+struct\s*\{")
    for path in repo_root.rglob("*.go"):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except (OSError, UnicodeDecodeError):
            continue
        for line in text.splitlines():
            m = struct_re.match(line.strip())
            if m:
                name = m.group(1)
                # Only record the first occurrence (most likely the canonical
                # definition in models/).
                if name not in structs:
                    structs[name] = str(path)
    return structs


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
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except (OSError, UnicodeDecodeError):
            continue
        for m in accessor_re.finditer(text):
            name, coll = m.group(1), m.group(2)
            accessor_map.setdefault(name, coll)
    return accessor_map


def resolve_collection_for_model(
    collection: str, struct_index: dict[str, str], repo_root: Path
) -> tuple[Optional[str], Optional[str]]:
    """Map a collection name to its likely Go model struct + file path."""
    if collection in COLLECTION_MODEL_OVERRIDES:
        candidate = COLLECTION_MODEL_OVERRIDES[collection]
        if candidate in struct_index:
            return candidate, _relative(repo_root, struct_index[candidate])
        return candidate, None

    singular = singularize_collection(collection)
    pascal = snake_to_pascal(singular)
    if pascal in struct_index:
        return pascal, _relative(repo_root, struct_index[pascal])
    # Fall back to the raw PascalCase of the plural name.
    pascal_plural = snake_to_pascal(collection)
    if pascal_plural in struct_index:
        return pascal_plural, _relative(repo_root, struct_index[pascal_plural])
    return pascal or None, None


def _relative(root: Path, p: str | Path) -> str:
    try:
        return str(Path(p).resolve().relative_to(root.resolve()))
    except ValueError:
        return str(p)


def extract_filter_fields(line: str) -> list[str]:
    """Pull field names out of bson.M / bson.D literals on this line."""
    fields: list[str] = []

    # bson.D blocks: pull all blocks, then look for keys inside each.
    for block in BSON_D_BLOCK_RE.finditer(line):
        inner = block.group(1)
        for m in BSON_D_KEYVAL_NAMED_RE.finditer(inner):
            fields.append(m.group(1))
        for m in BSON_D_KEYVAL_POS_RE.finditer(inner):
            fields.append(m.group(1))

    # bson.M{"field": value, ...}
    for m in BSON_M_RE.finditer(line):
        for km in BSON_M_KEY_RE.finditer(m.group(1)):
            fields.append(km.group(1))

    # Dedupe while preserving order, drop operators ($set etc.) and empty.
    seen: set[str] = set()
    out: list[str] = []
    for f in fields:
        if not f or f.startswith("$") or f in seen:
            continue
        seen.add(f)
        out.append(f)
    return out


# ---------------------------------------------------------------------------
# Per-file scanner
# ---------------------------------------------------------------------------


def scan_file(
    path: Path,
    repo_root: Path,
    accessor_map: dict[str, str],
    struct_index: dict[str, str],
    collection_index: dict[str, CollectionInfo],
    queries: list[Query],
) -> None:
    """Scan a single Go file and append Query records to ``queries``."""
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return

    # Local variable alias table — refreshed per file.
    aliases: dict[str, str] = {}
    current_func = "<package-init>"

    rel = _relative(repo_root, path)

    for idx, raw_line in enumerate(lines, start=1):
        line = raw_line.rstrip("\n")

        # Track current function context.
        # Cheap test first: lines starting with "func".
        stripped = line.lstrip()
        if stripped.startswith("func"):
            fm = FUNC_RE.match(stripped)
            if fm:
                current_func = fm.group(1)
                continue

        # Update alias table from explicit collection literals.
        for m in ALIAS_LITERAL_RE.finditer(line):
            aliases[m.group(1)] = m.group(2)

        # Update alias table from accessor calls. We do this BEFORE
        # scanning for queries so that ``col := s.db.Plans()`` followed
        # immediately by ``col.FindOne(...)`` on a later line resolves
        # correctly. We must be careful not to mis-classify a real query
        # call as an alias assignment — the alias pattern requires a
        # ``:=`` or ``=`` token before the accessor call.
        # Match ``<ident> := <expr>.<Accessor>()`` only when the accessor
        # is followed by ``()`` AND is not immediately followed by another
        # chained method call (``.Find(`` etc.).
        for m in ALIAS_ACCESSOR_RE.finditer(line):
            var_name = m.group(1)
            accessor = m.group(2)
            # Skip if this is actually a chained call like ``h.db.Users().Find(...)``
            # — the alias pattern would also match the accessor portion.
            # We check that the character right after ``()`` is not ``.``
            # (i.e. no further method call on the returned collection).
            end = m.end()
            if end < len(line) and line[end] == ".":
                continue
            # Only register the alias if the accessor is a known collection
            # accessor (so we don't pollute the table with random helper calls).
            if accessor in accessor_map:
                aliases[var_name] = accessor_map[accessor]

        # Build a multi-line context window starting at the current line so
        # we can capture filter fields from multi-line ``bson.M{`` / ``bson.D{``
        # literals that span across newlines. We extend the window only as far
        # as needed: starting from the current line, keep adding lines until
        # the number of ``bson.M{`` / ``bson.D{`` opening tokens is balanced
        # by the number of ``}`` closing braces. This deliberately ignores
        # unrelated braces (e.g. ``if ... {``) so we don't bleed into the
        # next query on the following line.
        def _bson_open_count(s: str) -> int:
            return len(re.findall(r"\bbson\.[MD]\s*\{", s))

        context_lines = [line]
        open_bson = _bson_open_count(line)
        close_braces = line.count("}")
        if open_bson > close_braces:
            for ahead in range(idx + 1, min(idx + 8, len(lines) + 1)):
                nxt = lines[ahead - 1]
                context_lines.append(nxt)
                open_bson += _bson_open_count(nxt)
                close_braces += nxt.count("}")
                if open_bson <= close_braces:
                    break
        context_window = "\n".join(context_lines)

        # ---- Direct wrapper helpers (testutil.CountDocuments etc.) ----
        for wre, wop in WRAPPER_PATTERNS:
            for m in wre.finditer(line):
                coll = m.group(1)
                _record_query(
                    queries=queries,
                    collection_index=collection_index,
                    accessor_map=accessor_map,
                    struct_index=struct_index,
                    repo_root=repo_root,
                    file=rel,
                    line=idx,
                    function=current_func,
                    collection=coll,
                    operation=wop,
                    line_text=line,
                    context_text=context_window,
                    aliases=aliases,
                )
                # The wrapper regex matches the same line; we don't want to
                # double-count if the underlying call also appears. The
                # underlying call (database.Database.Collection(...).CountDocuments)
                # would be on a separate line in testutil.go itself, which
                # is fine — we want to record both.

        # ---- Direct query operations ----
        for op_m in OP_RE.finditer(line):
            operation = op_m.group(1)
            op_start = op_m.start()
            # Look at the text *before* the operation to find the receiver.
            prefix = line[:op_start]
            # Filter out option-builder calls like ``options.Find()`` and
            # ``options.FindOne()`` — they construct *options.FindOptions
            # structs and are not real MongoDB queries. The OP_RE consumes
            # the leading ``.`` of the call, so the prefix ends with
            # ``options`` (no trailing dot) when the call is an option
            # builder.
            if re.search(r"\boptions\s*$", prefix):
                continue

            collection: Optional[str] = None
            accessor_used: Optional[str] = None

            # Strategy 1: literal ``.Collection("name").<Op>`` chain.
            lit_m = COLLECTION_LITERAL_RE.search(prefix)
            if lit_m:
                collection = lit_m.group(1)
            else:
                # Strategy 2: accessor call ``<expr>.<Accessor>().<Op>``.
                # The accessor name is the identifier right before the final ``()``.
                # We walk backwards from op_start looking for ``<ident>()``.
                acc_m = re.search(r"([A-Z]\w*)\(\s*\)\s*$", prefix)
                if acc_m:
                    accessor_used = acc_m.group(1)
                    collection = accessor_map.get(accessor_used)
                else:
                    # Strategy 3: aliased variable ``<ident>.<Op>``.
                    var_m = re.search(r"([A-Za-z_]\w*)\s*$", prefix)
                    if var_m:
                        var_name = var_m.group(1)
                        collection = aliases.get(var_name)

            # If we still couldn't resolve a collection, try scanning the
            # previous few lines for a literal collection access — this
            # handles cases where the query call is split across lines.
            if collection is None:
                for back in range(idx - 2, max(idx - 6, 0) - 1, -1):
                    if back < 1 or back > len(lines):
                        continue
                    prev = lines[back - 1]
                    lit_m = COLLECTION_LITERAL_RE.search(prev)
                    if lit_m:
                        collection = lit_m.group(1)
                        break
                    acc_m = re.search(r"([A-Z]\w*)\(\s*\)", prev)
                    if acc_m and acc_m.group(1) in accessor_map:
                        collection = accessor_map[acc_m.group(1)]
                        break

            if collection is None:
                # Truly unresolvable — record with empty collection so the
                # user can investigate. We still keep the query for completeness.
                collection = "<unknown>"

            _record_query(
                queries=queries,
                collection_index=collection_index,
                accessor_map=accessor_map,
                struct_index=struct_index,
                repo_root=repo_root,
                file=rel,
                line=idx,
                function=current_func,
                collection=collection,
                operation=operation,
                line_text=line,
                context_text=context_window,
                aliases=aliases,
                accessor_used=accessor_used,
            )


def _record_query(
    *,
    queries: list[Query],
    collection_index: dict[str, CollectionInfo],
    accessor_map: dict[str, str],
    struct_index: dict[str, str],
    repo_root: Path,
    file: str,
    line: int,
    function: str,
    collection: str,
    operation: str,
    line_text: str,
    context_text: str = "",
    aliases: dict[str, str],
    accessor_used: Optional[str] = None,
) -> None:
    """Build and register a Query record + update collection aggregates."""
    info = collection_index.get(collection)
    if info is None:
        info = CollectionInfo(name=collection)
        collection_index[collection] = info
        # Resolve model + model_file once per collection.
        model, model_file = resolve_collection_for_model(
            collection, struct_index, repo_root
        )
        info.model = model
        info.model_file = model_file
    if accessor_used and accessor_used not in info.accessors:
        info.accessors.append(accessor_used)

    # Find accessor aliases that point at this collection (cosmetic).
    if not info.accessors:
        for acc, coll in accessor_map.items():
            if coll == collection:
                info.accessors.append(acc)

    info.files.add(file)
    info.operations[operation] += 1
    info.total_queries += 1

    # Extract filter fields from the multi-line context (which includes
    # the current line + the next few lines, so multi-line ``bson.M{``
    # literals are captured).
    filter_fields = extract_filter_fields(context_text or line_text)
    # Compact snippet for human inspection.
    snippet = line_text.strip()
    if len(snippet) > 200:
        snippet = snippet[:197] + "..."

    queries.append(
        Query(
            file=file,
            line=line,
            function=function,
            collection=collection,
            operation=operation,
            model=info.model,
            model_file=info.model_file,
            filter_fields=filter_fields,
            snippet=snippet,
        )
    )


# ---------------------------------------------------------------------------
# Output rendering
# ---------------------------------------------------------------------------


def build_summary(
    queries: list[Query],
    collection_index: dict[str, CollectionInfo],
    repo_root: Path,
) -> dict:
    """Build the JSON-serialisable summary object."""
    collections_by_access = sorted(
        (
            {
                "collection": name,
                "queries": info.total_queries,
                "model": info.model,
                "model_file": info.model_file,
                "accessors": info.accessors,
                "files": len(info.files),
                "operations": dict(info.operations),
            }
            for name, info in collection_index.items()
        ),
        key=lambda c: -c["queries"],
    )

    operations_by_usage: Counter = Counter()
    models_by_activity: Counter = Counter()
    files_with_queries: Counter = Counter()
    for q in queries:
        operations_by_usage[q.operation] += 1
        if q.model:
            models_by_activity[q.model] += 1
        files_with_queries[q.file] += 1

    models_sorted = [
        {"model": m, "queries": c, "collection": next(
            (ci.name for ci in collection_index.values() if ci.model == m),
            None,
        )}
        for m, c in models_by_activity.most_common()
    ]

    return {
        "repo_root": str(repo_root),
        "total_queries": len(queries),
        "total_collections": len(collection_index),
        "total_files_with_queries": len(files_with_queries),
        "collections_by_access_count": collections_by_access,
        "operations_by_usage": [
            {"operation": op, "count": c}
            for op, c in operations_by_usage.most_common()
        ],
        "models_by_query_activity": models_sorted,
        "files_with_most_queries": [
            {"file": f, "queries": c}
            for f, c in files_with_queries.most_common(15)
        ],
        "collections_to_models": {
            name: info.model
            for name, info in collection_index.items()
            if info.model
        },
    }


def render_markdown(summary: dict, queries: list[Query]) -> str:
    """Render the summary + queries as a Markdown report."""
    lines: list[str] = []
    lines.append("# MongoDB Query Map\n")
    lines.append(
        f"Scanned **{summary['total_files_with_queries']}** files, "
        f"found **{summary['total_queries']}** MongoDB queries across "
        f"**{summary['total_collections']}** collections.\n"
    )
    lines.append(f"Repo: `{summary['repo_root']}`\n")

    # ---- Collections by access count ----
    lines.append("## Collections by Access Count\n")
    lines.append(
        "| Rank | Collection | Queries | Model | Model File | Files | Operations |"
    )
    lines.append(
        "|------|------------|---------|-------|------------|-------|------------|"
    )
    for i, c in enumerate(summary["collections_by_access_count"], 1):
        ops = ", ".join(
            f"{op}×{n}" for op, n in sorted(c["operations"].items(), key=lambda x: -x[1])
        )
        model = c["model"] or "—"
        model_file = f"`{c['model_file']}`" if c["model_file"] else "—"
        lines.append(
            f"| {i} | `{c['collection']}` | {c['queries']} | {model} | "
            f"{model_file} | {c['files']} | {ops or '—'} |"
        )
    lines.append("")

    # ---- Operations by usage ----
    lines.append("## Operations by Usage\n")
    lines.append("| Operation | Count |")
    lines.append("|-----------|-------|")
    for op in summary["operations_by_usage"]:
        lines.append(f"| `{op['operation']}` | {op['count']} |")
    lines.append("")

    # ---- Models by query activity ----
    lines.append("## Models by Query Activity\n")
    lines.append("| Rank | Model struct | Queries | Primary collection |")
    lines.append("|------|--------------|---------|--------------------|")
    for i, m in enumerate(summary["models_by_query_activity"], 1):
        coll = m["collection"] or "—"
        lines.append(f"| {i} | `{m['model']}` | {m['queries']} | `{coll}` |")
    lines.append("")

    # ---- Files with most queries ----
    lines.append("## Files with Most Queries\n")
    lines.append("| File | Queries |")
    lines.append("|------|---------|")
    for f in summary["files_with_most_queries"]:
        lines.append(f"| `{f['file']}` | {f['queries']} |")
    lines.append("")

    # ---- Collection → Model map ----
    lines.append("## Collection → Model Map\n")
    lines.append("| Collection | Model struct |")
    lines.append("|------------|--------------|")
    for coll, model in sorted(summary["collections_to_models"].items()):
        lines.append(f"| `{coll}` | `{model}` |")
    lines.append("")

    # ---- All queries (per file, sorted) ----
    lines.append("## All Queries\n")
    by_file: dict[str, list[Query]] = defaultdict(list)
    for q in queries:
        by_file[q.file].append(q)
    for file in sorted(by_file):
        lines.append(f"### `{file}`\n")
        lines.append("| Line | Function | Operation | Collection | Model | Filter fields |")
        lines.append("|------|----------|-----------|------------|-------|---------------|")
        for q in sorted(by_file[file], key=lambda q: q.line):
            fields = ", ".join(f"`{f}`" for f in q.filter_fields) if q.filter_fields else "—"
            model = f"`{q.model}`" if q.model else "—"
            lines.append(
                f"| {q.line} | `{q.function}` | `{q.operation}` | "
                f"`{q.collection}` | {model} | {fields} |"
            )
        lines.append("")

    lines.append("---")
    lines.append("_Generated by `graphify db-queries`._")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="graphify_db_queries.py",
        description="Scan Go source for MongoDB queries and map them to models.",
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Root directory to scan (default: current directory).",
    )
    parser.add_argument(
        "--out",
        default=None,
        help="Path to write the Markdown report (default: stdout).",
    )
    parser.add_argument(
        "--json",
        nargs="?",
        const="__stdout__",
        default=None,
        help="Path to write the JSON report. If passed without a value, "
        "writes to stdout.",
    )
    parser.add_argument(
        "--include-tests",
        action="store_true",
        default=False,
        help="Include *_test.go files in the scan (default: skipped).",
    )
    args = parser.parse_args(argv)

    repo_root = Path(args.path).resolve()
    if not repo_root.is_dir():
        print(f"error: {repo_root} is not a directory", file=sys.stderr)
        return 2

    # Build global maps.
    struct_index = collect_struct_definitions(repo_root)
    accessor_map = build_accessor_map(repo_root)

    collection_index: dict[str, CollectionInfo] = {}
    queries: list[Query] = []

    for path in sorted(repo_root.rglob("*.go")):
        if not args.include_tests and path.name.endswith("_test.go"):
            continue
        # Skip graphify-out cache directories if present.
        if "graphify-out" in path.parts:
            continue
        scan_file(
            path=path,
            repo_root=repo_root,
            accessor_map=accessor_map,
            struct_index=struct_index,
            collection_index=collection_index,
            queries=queries,
        )

    summary = build_summary(queries, collection_index, repo_root)
    payload = {
        "summary": summary,
        "queries": [q.to_dict() for q in queries],
        "accessor_map": accessor_map,
    }

    # ---- JSON output ----
    if args.json is not None:
        json_text = json.dumps(payload, indent=2, default=str)
        if args.json == "__stdout__":
            print(json_text)
        else:
            Path(args.json).parent.mkdir(parents=True, exist_ok=True)
            Path(args.json).write_text(json_text + "\n", encoding="utf-8")
            print(f"wrote JSON to {args.json}", file=sys.stderr)

    # ---- Markdown output ----
    md_text = render_markdown(summary, queries)
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(md_text + "\n", encoding="utf-8")
        print(f"wrote markdown to {args.out}", file=sys.stderr)
    elif args.json is None:
        # If neither --out nor --json were provided, print MD to stdout so
        # the script is still useful out of the box.
        print(md_text)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
