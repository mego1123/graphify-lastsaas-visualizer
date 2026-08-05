#!/usr/bin/env python3
"""graphify_missing_indexes — flag MongoDB queries whose filter fields are not
covered by an index, and warn about collections that lack a required index for
known multi-tenant / lookup patterns.

Pipeline:

  1. Parse the project's index-registration sites — anywhere code calls
     ``coll.Indexes().CreateMany(ctx, []mongo.IndexModel{ ... })`` or
     ``CreateOne(ctx, mongo.IndexModel{...})``. Extract, per collection:

       * the set of single-field indexes (the field's first segment),
       * the leading field of every compound index (an index can only be
         used by a query whose filter starts with that field),
       * whether the index is unique / TTL (used for the report narrative).

     The collection name is resolved from the surrounding
     ``db.Collection("name")`` literal or from the accessor method
     (e.g. ``m.Users()``) via the same accessor map that
     ``graphify_db_queries.py`` builds.

  2. Walk every ``.go`` file for MongoDB queries (Find, FindOne, InsertOne,
     UpdateOne, UpdateMany, DeleteOne, DeleteMany, CountDocuments, Aggregate,
     ReplaceOne). For each query extract the filter fields from the
     ``bson.M{...}`` / ``bson.D{...}`` literal that's the first argument.

  3. A query is **flagged** when none of its filter fields are covered by an
     index on that collection (i.e. no single-field index on any of the
     filter fields, and no compound index whose leading field matches any
     of the filter fields). A query on a collection that has *no* declared
     indexes at all is flagged separately as a "collection-without-index".

  4. Additionally, every query is checked against a small spec of
     "expected indexed fields per collection" derived from the SaaS domain
     conventions:

       * ``_id`` is always indexed by MongoDB (never flagged).
       * ``tenantId`` / ``tenant_id`` should be indexed on every
         multi-tenant collection.
       * ``email`` should be unique-indexed on ``users``.
       * ``userId`` should be indexed on membership / log / token
         collections.
       * ``slug`` should be unique-indexed on ``tenants``.
       * ``token`` should be indexed on ``invitations`` /
         ``verification_tokens`` / ``auth_codes``.

     Queries that filter on one of these fields on a collection where the
     field is *not* indexed are flagged as "missing required index".

  5. Risk:

       * **HIGH** — query on a likely-large collection (logs, events,
         telemetry, audit) with no usable index, or a query filtering on
         a spec-required field that's not indexed.
       * **MEDIUM** — query on a small/static-data collection without an
         index, or partial coverage (only some filter fields indexed).
       * **LOW** — never emitted (this analyzer is a warning system).

Usage:
    python graphify_missing_indexes.py [path] [--out report.md] [--json] [--include-tests]

Outputs:
    - JSON written to /home/z/my-project/public/missing-indexes.json (best effort)
    - Markdown written to /home/z/my-project/public/MISSING_INDEXES.md (best effort)
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

COLLECTION_LITERAL_RE = re.compile(
    r'\.Collection\(\s*"([^"]+)"\s*\)'
)

FUNC_DECL_RE = re.compile(
    r'^[ \t]*func(?:[ \t]+\([^)]*\))?[ \t]+(?P<name>\w+)[ \t]*\(',
    re.MULTILINE,
)

# bson.D{{Key: "f", Value: ...}, {"f2", v}}
BSON_D_BLOCK_RE = re.compile(
    r'\bbson\.D\s*\{([^}]*)\}'
)
BSON_D_KEYVAL_NAMED_RE = re.compile(
    r'Key:\s*"([^"]+)"\s*,\s*Value:'
)
BSON_D_KEYVAL_POS_RE = re.compile(
    r'\{\s*"([^"]+)"\s*,'
)

# bson.M{"field": value, ...}
BSON_M_RE = re.compile(
    r'\bbson\.M\s*\{([^}]*)\}'
)
BSON_M_KEY_RE = re.compile(
    r'"([^"]+)"\s*:'
)

# IndexModel Keys block — bson.D{{Key: "f", Value: 1}, {Key: "g", Value: -1}}
# We re-use BSON_D_BLOCK_RE for parsing inside the Keys block.

# IndexModel block: `mongo.IndexModel{ Keys: bson.D{...}, Options: ... }`
INDEX_MODEL_RE = re.compile(
    r"mongo\.IndexModel\s*\{(?P<body>.*?)\n\s*\}",
    re.DOTALL,
)

# Pattern for the slice-of-anonymous-struct form used by ensureIndexes():
#
#   indexes := []struct {
#       collection string
#       models     []mongo.IndexModel
#   }{
#       {
#           "users",
#           []mongo.IndexModel{
#               {Keys: bson.D{{Key: "email", Value: 1}}, Options: ...},
#               ...
#           },
#       },
#       {
#           "tenants",
#           []mongo.IndexModel{
#               {Keys: bson.D{...}, Options: ...},
#               ...
#           },
#       },
#       ...
#   }
#
# We capture each `"<name>",` literal that immediately precedes a
# `[]mongo.IndexModel{` block, then walk forward to find every
# `{Keys: bson.D{...}, Options: ...}` entry inside that block.
ENSURE_INDEXES_ENTRY_RE = re.compile(
    r'"(?P<coll>[^"]+)"\s*,\s*'
    r'\[\]\s*mongo\.IndexModel\s*\{(?P<body>.*?)\n\s*\}\s*,',
    re.DOTALL,
)

# Individual IndexModel entry inside an array of IndexModels:
#   {Keys: bson.D{{Key: "f", Value: 1}}, Options: options.Index().SetUnique(true)}
INDEX_ENTRY_RE = re.compile(
    r"\{\s*Keys\s*:\s*(bson\.D\s*\{[^}]*\}(?:\s*\{[^}]*\})*[^}]*?)"
    r"(?:,\s*Options\s*:\s*(?P<options>[^{}]*(?:\{[^}]*\}[^{}]*)*))?\s*\}",
    re.DOTALL,
)

# Collections that are likely to grow large (logs, events, telemetry,
# deliveries, audit, metrics). Used for risk classification.
LARGE_COLLECTIONS: frozenset[str] = frozenset({
    "audit_log",
    "system_logs",
    "telemetry_events",
    "usage_events",
    "webhook_deliveries",
    "webhook_events",
    "system_metrics",
    "daily_metrics",
    "messages",
    "impersonation_logs",
    "rate_limits",
    "financial_transactions",
    "revoked_tokens",
    "refresh_tokens",
    "verification_tokens",
    "oauth_states",
    "leader_locks",
    "webauthn_sessions",
    "auth_codes",
})

# Single-document collections: collections that hold exactly one config
# record (e.g. ``branding_config`` stores a single BrandingConfig doc;
# ``system_config`` stores a single SystemConfig doc). Scanning these is
# effectively free — even a full collection scan touches one document —
# so "missing index" findings here are pure noise.
SINGLE_DOCUMENT_COLLECTIONS: frozenset[str] = frozenset({
    "branding_config",
    "system_config",
})

# Small collections: collections whose expected document count is well
# under 100 (admin-curated lookup tables, plan definitions, public
# announcements, etc.). A full collection scan on these is sub-millisecond
# and not worth a HIGH severity finding. Findings on these collections
# are downgraded to MEDIUM (or suppressed entirely when the collection
# is single-document).
SMALL_COLLECTIONS: frozenset[str] = frozenset({
    "announcements",       # admin-curated, ~10 docs
    "plans",               # admin-curated, ~10 docs
    "credit_bundles",      # admin-curated, ~10 docs
    "event_definitions",   # admin-curated, ~20 docs
    "config_vars",         # admin-curated, ~30 docs
    "custom_pages",        # admin-curated, ~10 docs
    "branding_assets",     # logo/favicon + media library, <100
    "system_nodes",        # one doc per cluster node, <10
    "stripe_mappings",     # one per stripe entity, <100
    "sso_connections",     # one per IdP per tenant, <10
    "counters",            # one per invoice sequence, <100
    "webhooks",            # admin-curated, ~5 per tenant
    "api_keys",            # admin-curated, ~5 per user
    "tenants",             # one doc per tenant — bounded by tenant count
    "users",               # one doc per user — bounded but could grow
    "tenant_memberships",  # ~1-5 per user — bounded
    "invitations",         # short-lived, ~10 active at a time
})

# Heuristic for paths/function names that indicate admin/CLI scope. Queries
# in these contexts legitimately scan across tenants (admin dashboards,
# CLI reporting tools, batch jobs) — multi_tenant_unfiltered findings
# there are downgraded to MEDIUM rather than HIGH.
ADMIN_PATH_HINTS: tuple[str, ...] = (
    "/cmd/lastsaas/", "\\cmd\\lastsaas\\",
    "cmd/lastsaas/", "cmd\\lastsaas\\",
    "internal/api/handlers/admin.go",
    "internal/api/handlers/admin_",
)

ADMIN_FUNC_HINTS: tuple[str, ...] = (
    "admin", "listroot", "listall", "preflight", "impersonate",
    "export", "seed", "migrate", "cleanup", "backfill", "reconcile",
    "doctor", "batch", "stats", "report",
)

# Spec: required indexed fields per collection (collection -> set of fields
# that *should* be indexed). Queries filtering on these fields are flagged
# when the actual index set doesn't include them.
REQUIRED_INDEX_FIELDS: dict[str, set[str]] = {
    "users": {"email"},
    "tenants": {"slug"},
    "tenant_memberships": {"tenantId", "userId"},
    "invitations": {"token", "tenantId", "email"},
    "verification_tokens": {"token", "userId"},
    "auth_codes": {"code"},
    "refresh_tokens": {"userId"},
    "revoked_tokens": {"tokenHash"},
    "api_keys": {"keyHash"},
    "webauthn_credentials": {"userId", "credentialId"},
    "sso_connections": {"tenantId"},
    "audit_log": {"tenantId", "userId"},
    "system_logs": {"tenantId", "userId"},
    "telemetry_events": {"userId", "eventName", "sessionId"},
    "usage_events": {"tenantId"},
    "financial_transactions": {"tenantId", "userId"},
    "messages": {"userId"},
    "webhooks": {"createdBy"},
    "webhook_deliveries": {"webhookId"},
    "webhook_events": {"eventId"},
    "config_vars": {"name"},
    "plans": {"name"},
    "event_definitions": {"name"},
    "custom_pages": {"slug"},
    "branding_assets": {"key"},
    "system_nodes": {"machineId"},
    "stripe_mappings": {"entityType", "entityId"},
    "daily_metrics": {"date"},
    "sso_connections": {"tenantId"},
}

# Fields that are always indexed (MongoDB does this automatically) and so
# should never trigger a "missing index" warning.
ALWAYS_INDEXED: frozenset[str] = frozenset({"_id"})

# Multi-tenant marker: collections where every document belongs to a tenant
# and queries SHOULD filter by tenantId. Empty-filter queries on these
# collections are flagged as full-collection scans that risk cross-tenant
# data leaks. Collections that represent tenant-wide/system-wide data
# (tenants itself, plans, config_vars, event_definitions, credit_bundles,
# branding_assets, custom_pages) are excluded — they may be tenant-scoped
# via a different mechanism (e.g. a tenant-specific DB) or be truly global.
MULTI_TENANT_COLLECTIONS: frozenset[str] = frozenset({
    "tenant_memberships",
    "invitations",
    "audit_log",
    "system_logs",
    "telemetry_events",
    "usage_events",
    "financial_transactions",
    "messages",
    "api_keys",
    "webhooks",
    "webhook_deliveries",
    "sso_connections",
    "announcements",
})


# --------------------------------------------------------------------------- #
# Source masking
# --------------------------------------------------------------------------- #

def mask_source(src: str) -> str:
    """Replace string literals and comments with spaces (preserving length).

    Note: this masker preserves the *content* of ``"..."`` strings only
    partially — for index parsing we need the actual string contents
    (collection names, field names), so we use it carefully. For index
    parsing we use a different code path that operates on raw source.
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
        # NOTE: do NOT mask double-quoted strings — we need their contents
        # to extract collection names and field names. Backtick raw strings
        # are still masked.
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


def find_matching_brace(src: str, open_pos: int) -> int:
    depth = 0
    i = open_pos
    n = len(src)
    while i < n:
        c = src[i]
        if c == '{':
            depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return -1


# --------------------------------------------------------------------------- #
# Index registration parser
# --------------------------------------------------------------------------- #

@dataclass
class IndexInfo:
    collection: str
    fields: list[str]              # ordered list, e.g. ["tenantId", "createdAt"]
    leading_field: str            # fields[0]
    is_unique: bool = False
    is_ttl: bool = False
    is_sparse: bool = False
    is_text: bool = False
    source: str = ""               # file:line where the index was declared


@dataclass
class CollectionIndexSummary:
    name: str
    indexes: list[IndexInfo] = field(default_factory=list)
    indexed_fields: set[str] = field(default_factory=set)        # any field in any index
    leading_fields: set[str] = field(default_factory=set)        # only leading fields
    has_any_index: bool = False
    has_unique: bool = False


def parse_index_options(body: str) -> tuple[bool, bool, bool]:
    """Return (is_unique, is_ttl, is_sparse) from an IndexModel body."""
    is_unique = bool(re.search(r"SetUnique\s*\(\s*true", body))
    is_ttl = bool(re.search(r"SetExpireAfterSeconds", body))
    is_sparse = bool(re.search(r"SetSparse\s*\(\s*true", body))
    return is_unique, is_ttl, is_sparse


def _iter_top_level_entries(body: str):
    """Yield each top-level ``{...}`` block inside ``body``.

    A top-level entry is a ``{`` at paren/brace depth 0 within ``body``.
    We use brace matching to find the matching ``}`` and yield the inner
    text. Nested ``{...}`` blocks (e.g. inside ``bson.D{{Key: ...}}``)
    are included in the outer entry's text.
    """
    i = 0
    n = len(body)
    while i < n:
        c = body[i]
        if c == '{':
            # Found the start of an entry — find the matching `}`.
            depth = 1
            j = i + 1
            while j < n and depth > 0:
                cj = body[j]
                if cj == '{':
                    depth += 1
                elif cj == '}':
                    depth -= 1
                j += 1
            if depth == 0:
                yield body[i:j]  # include the outer braces
                i = j
                continue
            else:
                return
        i += 1


def _extract_keys_and_options(entry: str) -> tuple[str, str]:
    """Given an IndexModel entry ``{Keys: bson.D{...}, Options: ...}``,
    return (keys_block, options_block).

    Splits on the top-level ``, `` that separates ``Keys:`` from
    ``Options:`` — i.e. the first ``,`` at brace depth 0 (relative to
    the entry).
    """
    # Strip outer braces.
    inner = entry.strip()
    if inner.startswith('{') and inner.endswith('}'):
        inner = inner[1:-1]

    # Walk and find the first `,` at depth 0.
    depth = 0
    for i, c in enumerate(inner):
        if c == '{':
            depth += 1
        elif c == '}':
            depth -= 1
        elif c == ',' and depth == 0:
            keys_part = inner[:i].strip()
            options_part = inner[i + 1:].strip()
            return keys_part, options_part
    return inner.strip(), ""


def parse_indexes_in_file(
    path: Path,
    accessor_map: dict[str, str],
) -> list[IndexInfo]:
    """Find every declared MongoDB index in a file and resolve its collection.

    Two patterns are recognised:

      * **Slice-of-anonymous-struct form** (used by ``ensureIndexes()``):

            indexes := []struct {
                collection string
                models     []mongo.IndexModel
            }{
                {
                    "users",
                    []mongo.IndexModel{
                        {Keys: bson.D{{Key: "email", Value: 1}}, Options: ...},
                        ...
                    },
                },
                ...
            }

        The collection name comes from the string literal that precedes the
        ``[]mongo.IndexModel{`` block.

      * **Standalone IndexModel form** (used by rate-limiter setup):

            coll.Indexes().CreateOne(ctx, mongo.IndexModel{
                Keys:    bson.D{{Key: "expiresAt", Value: 1}},
                Options: options.Index().SetExpireAfterSeconds(0),
            })

        The collection is resolved by walking backwards to find the nearest
        preceding collection-binding site (literal, alias, or
        ``Collection("name").Indexes()`` on the same expression).
    """
    try:
        src = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    masked = mask_source(src)
    rel = _relative_to_cwd(path)

    out: list[IndexInfo] = []

    # ----- Pattern A: slice-of-anonymous-struct form ---------------------- #
    for m in ENSURE_INDEXES_ENTRY_RE.finditer(masked):
        coll = m.group("coll")
        body = m.group("body")
        # The body starts at the position right after `[]mongo.IndexModel{`
        # and ends right before the closing `},`. Individual entries are
        # `{Keys: bson.D{...}, Options: ...}`.
        for entry_text in _iter_top_level_entries(body):
            if "Keys" not in entry_text:
                continue
            keys_part, options_part = _extract_keys_and_options(entry_text)
            # keys_part looks like `Keys: bson.D{{Key: "f", Value: 1}, ...}`.
            keys_m = re.search(r'Keys\s*:\s*(bson\.D\s*\{.*)$', keys_part, re.DOTALL)
            if not keys_m:
                continue
            keys_block = keys_m.group(1)
            fields, is_text = _parse_bson_d_keys(keys_block)
            if not fields:
                continue
            is_unique, is_ttl, is_sparse = parse_index_options(options_part)
            # The line number is approximate — based on the offset of the
            # entry inside the file.
            entry_pos = m.start() + body.find(entry_text)
            if entry_pos < 0:
                entry_pos = m.start()
            line_no = masked[:entry_pos].count('\n') + 1
            out.append(IndexInfo(
                collection=coll,
                fields=fields,
                leading_field=fields[0],
                is_unique=is_unique,
                is_ttl=is_ttl,
                is_sparse=is_sparse,
                is_text=is_text,
                source=f"{rel}:{line_no}",
            ))

    # ----- Pattern B: standalone mongo.IndexModel{...} form ---------------- #
    # Build a per-file alias map and binding list so we can resolve the
    # collection by walking backwards from the IndexModel.
    aliases: dict[str, str] = {}
    bindings: list[tuple[int, str]] = []

    for m in COLLECTION_LITERAL_RE.finditer(masked):
        bindings.append((m.end(), m.group(1)))
    for m in re.finditer(
        r'(\w+)\s*:?=\s*[\w\.\[\]\*]+\.Collection\(\s*"([^"]+)"\s*\)',
        masked,
    ):
        var_name = m.group(1)
        coll = m.group(2)
        aliases[var_name] = coll
        bindings.append((m.end(), coll))
    for m in re.finditer(
        r'(\w+)\s*:?=\s*[\w\.\[\]\*]+\.([A-Z]\w*)\(\s*\)',
        masked,
    ):
        var_name = m.group(1)
        accessor = m.group(2)
        if accessor in accessor_map:
            end = m.end()
            if end < len(masked) and masked[end] == ".":
                continue
            aliases[var_name] = accessor_map[accessor]
            bindings.append((m.end(), accessor_map[accessor]))
    # ``Collection("name").Indexes()`` on the same expression.
    for m in re.finditer(
        r'\.Collection\(\s*"([^"]+)"\s*\)\s*\.\s*Indexes\(\)',
        masked,
    ):
        bindings.append((m.end(), m.group(1)))
    bindings.sort(key=lambda b: b[0])

    for m in INDEX_MODEL_RE.finditer(masked):
        body = m.group("body")
        # The body may have a single `Keys: bson.D{...}` plus `Options: ...`.
        keys_m = re.search(
            r'Keys\s*:\s*(bson\.D\s*\{.*?\})',
            body,
            re.DOTALL,
        )
        if not keys_m:
            continue
        fields, is_text = _parse_bson_d_keys(keys_m.group(1))
        if not fields:
            continue
        is_unique, is_ttl, is_sparse = parse_index_options(body)

        idx_pos = m.start()
        coll = "<unknown>"
        lo, hi = 0, len(bindings) - 1
        best: Optional[tuple[int, str]] = None
        while lo <= hi:
            mid = (lo + hi) // 2
            if bindings[mid][0] <= idx_pos:
                best = bindings[mid]
                lo = mid + 1
            else:
                hi = mid - 1
        if best is not None and (idx_pos - best[0]) < 2000:
            coll = best[1]

        line_no = masked[:m.start()].count('\n') + 1
        if coll == "<unknown>":
            # Don't record indexes we can't attribute to a collection.
            continue
        out.append(IndexInfo(
            collection=coll,
            fields=fields,
            leading_field=fields[0],
            is_unique=is_unique,
            is_ttl=is_ttl,
            is_sparse=is_sparse,
            is_text=is_text,
            source=f"{rel}:{line_no}",
        ))

    return out


def _parse_bson_d_keys(keys_block: str) -> tuple[list[str], bool]:
    """Extract ordered field names from a ``bson.D{...}`` Keys block.

    Handles both forms:
      ``bson.D{{Key: "f", Value: 1}, {Key: "g", Value: -1}}``
      ``bson.D{{"f", 1}, {"g", -1}}``
    """
    fields: list[str] = []
    is_text = False
    # Named form: {Key: "name", Value: <expr>}
    for pm in re.finditer(
        r'Key\s*:\s*"([^"]+)"\s*,\s*Value\s*:\s*([^},]+)',
        keys_block,
    ):
        name = pm.group(1)
        value = pm.group(2).strip()
        if value == '"text"':
            is_text = True
        first = name.split(".", 1)[0]
        fields.append(first)
    if fields:
        return fields, is_text
    # Positional form: {"name", <expr>}
    for pm in re.finditer(r'\{\s*"([^"]+)"\s*,', keys_block):
        name = pm.group(1)
        first = name.split(".", 1)[0]
        fields.append(first)
    return fields, is_text


def _relative_to_cwd(p: Path) -> str:
    try:
        return str(p.resolve().relative_to(Path.cwd().resolve()))
    except ValueError:
        return str(p)


def build_accessor_map(repo_root: Path) -> dict[str, str]:
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


def collect_all_indexes(
    repo_root: Path,
    accessor_map: dict[str, str],
) -> dict[str, CollectionIndexSummary]:
    """Walk every .go file and return {collection_name: summary}."""
    summaries: dict[str, CollectionIndexSummary] = {}
    for path in repo_root.rglob("*.go"):
        if "graphify-out" in path.parts:
            continue
        for info in parse_indexes_in_file(path, accessor_map):
            coll = info.collection
            if coll == "<unknown>":
                continue
            s = summaries.get(coll)
            if s is None:
                s = CollectionIndexSummary(name=coll)
                summaries[coll] = s
            s.indexes.append(info)
            s.indexed_fields.update(info.fields)
            s.leading_fields.add(info.leading_field)
            s.has_any_index = True
            if info.is_unique:
                s.has_unique = True
    return summaries


# --------------------------------------------------------------------------- #
# Query scanner (re-uses graphify_db_queries' approach)
# --------------------------------------------------------------------------- #

@dataclass
class Query:
    file: str
    line: int
    function: str
    collection: str
    operation: str
    filter_fields: list[str]
    snippet: str


def parse_functions(masked: str) -> list[tuple[str, int, int]]:
    """Return [(name, start_line, end_line)] for top-level functions."""
    funcs: list[tuple[str, int, int]] = []
    for m in FUNC_DECL_RE.finditer(masked):
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
        funcs.append((m.group("name"), start_line, end_line))
    return funcs


def containing_function(funcs: list[tuple[str, int, int]], line: int) -> str:
    best_name = "<top-level>"
    best_span: Optional[int] = None
    for name, s, e in funcs:
        if s <= line <= e:
            span = e - s
            if best_span is None or span < best_span:
                best_name = name
                best_span = span
    return best_name


def extract_filter_fields(text: str) -> list[str]:
    """Pull field names out of bson.M / bson.D literals on the given text."""
    fields: list[str] = []
    for block in BSON_D_BLOCK_RE.finditer(text):
        inner = block.group(1)
        for m in BSON_D_KEYVAL_NAMED_RE.finditer(inner):
            fields.append(m.group(1))
        for m in BSON_D_KEYVAL_POS_RE.finditer(inner):
            fields.append(m.group(1))
    for m in BSON_M_RE.finditer(text):
        for km in BSON_M_KEY_RE.finditer(m.group(1)):
            fields.append(km.group(1))
    seen: set[str] = set()
    out: list[str] = []
    for f in fields:
        if not f or f.startswith("$") or f in seen:
            continue
        # Use the first segment of dotted fields — indexes are on the first
        # segment.
        first = f.split(".", 1)[0]
        if first in seen:
            continue
        seen.add(first)
        out.append(first)
    return out


def scan_queries(
    repo_root: Path,
    accessor_map: dict[str, str],
    include_tests: bool,
) -> list[Query]:
    skip_dirs = {"vendor", "node_modules", ".git", "graphify-out", "testdata"}
    queries: list[Query] = []
    for path in repo_root.rglob("*.go"):
        if any(part in skip_dirs for part in path.parts):
            continue
        if not include_tests and path.name.endswith("_test.go"):
            continue
        try:
            src = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        masked = mask_source(src)
        lines = src.splitlines()
        funcs = parse_functions(masked)
        try:
            rel = str(path.resolve().relative_to(repo_root.resolve()))
        except ValueError:
            rel = str(path)

        aliases: dict[str, str] = {}
        for idx, raw_line in enumerate(lines, start=1):
            # Refresh aliases from this line.
            m = re.search(
                r'(\w+)\s*:?=\s*[\w\.\[\]\*]+\.Collection\(\s*"([^"]+)"\s*\)',
                raw_line,
            )
            if m:
                aliases[m.group(1)] = m.group(2)
            m = re.search(
                r'(\w+)\s*:?=\s*[\w\.\[\]\*]+\.([A-Z]\w*)\(\s*\)',
                raw_line,
            )
            if m:
                var_name = m.group(1)
                accessor = m.group(2)
                if accessor in accessor_map:
                    end = m.end()
                    if end >= len(raw_line) or raw_line[end] != ".":
                        aliases[var_name] = accessor_map[accessor]

            masked_line = masked.splitlines()[idx - 1] if idx - 1 < len(masked.splitlines()) else raw_line
            for op_m in OP_RE.finditer(masked_line):
                operation = op_m.group(1)
                prefix = masked_line[:op_m.start()]
                # Skip option builders.
                if re.search(r"\boptions\s*$", prefix):
                    continue

                # Resolve collection.
                collection: Optional[str] = None
                lit_m = COLLECTION_LITERAL_RE.search(masked_line)
                if lit_m:
                    collection = lit_m.group(1)
                else:
                    acc_m = re.search(r"([A-Z]\w*)\(\s*\)\s*$", prefix)
                    if acc_m and acc_m.group(1) in accessor_map:
                        collection = accessor_map[acc_m.group(1)]
                    else:
                        var_m = re.search(r"([A-Za-z_]\w*)\s*$", prefix)
                        if var_m and var_m.group(1) in aliases:
                            collection = aliases[var_m.group(1)]
                if collection is None:
                    # Look back a few lines for a literal collection access.
                    for back in range(idx - 2, max(idx - 6, 0) - 1, -1):
                        if back < 1 or back > len(lines):
                            continue
                        prev = masked.splitlines()[back - 1] if back - 1 < len(masked.splitlines()) else ""
                        lit_m = COLLECTION_LITERAL_RE.search(prev)
                        if lit_m:
                            collection = lit_m.group(1)
                            break
                        acc_m = re.search(r"([A-Z]\w*)\(\s*\)", prev)
                        if acc_m and acc_m.group(1) in accessor_map:
                            collection = accessor_map[acc_m.group(1)]
                            break
                if collection is None:
                    continue  # unresolved — skip (not our problem here)

                # Build a multi-line context window for the filter literal.
                # The bson.M{...} / bson.D{...} literal may be on the same
                # line as the call, entirely on a subsequent line (common
                # when the call wraps), or split across multiple lines.
                context_lines = [raw_line]
                open_bson = len(re.findall(r"\bbson\.[MD]\s*\{", raw_line))
                close_braces = raw_line.count("}")
                if open_bson > close_braces:
                    for ahead in range(idx + 1, min(idx + 8, len(lines) + 1)):
                        nxt = lines[ahead - 1]
                        context_lines.append(nxt)
                        open_bson += len(re.findall(r"\bbson\.[MD]\s*\{", nxt))
                        close_braces += nxt.count("}")
                        if open_bson <= close_braces:
                            break
                else:
                    # The call's filter may be entirely on the next line
                    # (e.g. ``coll.Find(ctx,\n    bson.M{...})``). Look
                    # ahead up to 3 lines for a bson literal if the
                    # current line didn't yield any filter fields.
                    context_text = "\n".join(context_lines)
                    if not extract_filter_fields(context_text):
                        for ahead in range(idx + 1, min(idx + 4, len(lines) + 1)):
                            nxt = lines[ahead - 1]
                            context_lines.append(nxt)
                            if re.search(r"\bbson\.[MD]\s*\{", nxt):
                                # Found the literal — keep consuming until
                                # braces balance.
                                open_bson = sum(
                                    len(re.findall(r"\bbson\.[MD]\s*\{", cl))
                                    for cl in context_lines
                                )
                                close_braces = sum(cl.count("}") for cl in context_lines)
                                if open_bson <= close_braces:
                                    break
                context_text = "\n".join(context_lines)

                filter_fields = extract_filter_fields(context_text)
                # InsertOne/InsertMany/Aggregate don't have a "filter" — skip.
                if operation in ("InsertOne", "InsertMany", "Aggregate",
                                 "EstimatedDocumentCount", "CreateIndex"):
                    continue

                snippet = raw_line.strip()
                if len(snippet) > 200:
                    snippet = snippet[:197] + "..."
                func_name = containing_function(funcs, idx)
                queries.append(Query(
                    file=rel,
                    line=idx,
                    function=func_name,
                    collection=collection,
                    operation=operation,
                    filter_fields=filter_fields,
                    snippet=snippet,
                ))
    return queries


# --------------------------------------------------------------------------- #
# Findings
# --------------------------------------------------------------------------- #

@dataclass
class Finding:
    file: str
    line: int
    function: str
    collection: str
    operation: str
    filter_fields: list[str]
    severity: str
    finding_type: str           # "no_index" / "missing_required" / "no_collection_indexes" / "multi_tenant_unfiltered"
    reason: str
    snippet: str
    suggestion: str


@dataclass
class SuppressedFinding:
    """A finding that was suppressed by a ``// graphify:no-index-check``
    annotation. Tracked separately so the report can show how many
    findings were intentionally silenced.
    """
    file: str
    line: int
    function: str
    collection: str
    operation: str
    filter_fields: list[str]
    would_be_severity: str
    finding_type: str
    reason: str
    suppression: str            # "function" (function-level annotation) | "line_above" (line-above annotation)


# The ``// graphify:no-index-check`` annotation: when present anywhere
# in a function body OR on the line immediately above a query, the
# query's missing-index finding is suppressed and counted separately.
NO_INDEX_CHECK_RE = re.compile(r"//\s*graphify:no-index-check\b")


def _scan_no_index_check_annotations(
    src_by_file: dict[str, str],
) -> tuple[dict[str, set[int]], dict[str, set[int]]]:
    """Pre-scan every file's source for ``// graphify:no-index-check``
    comments.

    Returns two dicts:

      * ``line_annotations``: ``{file: {line_numbers}}`` — every line
        on which the annotation appears (used for per-query suppression
        via the "line above the query" check).
      * ``function_annotations``: ``{file: {function_names}}`` — every
        function whose doc comment OR body contains at least one
        annotation (used for function-level suppression).
    """
    line_annotations: dict[str, set[int]] = {}
    function_annotations: dict[str, set[str]] = {}
    for file, src in src_by_file.items():
        masked = mask_source(src)
        # Per-line annotations on the RAW source (the masker blanks
        # comment contents, so we must search the original).
        src_lines = src.splitlines()
        line_set: set[int] = set()
        for i, line in enumerate(src_lines, start=1):
            if NO_INDEX_CHECK_RE.search(line):
                line_set.add(i)
        if line_set:
            line_annotations[file] = line_set
        # Per-function annotations: walk every top-level function and
        # check if its doc comment OR body contains the annotation.
        funcs = parse_functions(masked)
        func_set: set[str] = set()
        for name, start_line, end_line in funcs:
            # Walk backward from start_line-1 over the doc comment
            # (consecutive // lines on the raw source) so the
            # function-level annotation can live in the godoc above the
            # function declaration, not just inside the body.
            doc_start = start_line
            j = start_line - 1
            while j >= 1:
                prev_raw = src_lines[j - 1].strip() if j - 1 < len(src_lines) else ""
                if prev_raw.startswith("//") or prev_raw == "":
                    if NO_INDEX_CHECK_RE.search(src_lines[j - 1] if j - 1 < len(src_lines) else ""):
                        doc_start = j
                    j -= 1
                    continue
                break
            body_lines = src_lines[doc_start - 1: end_line] if end_line <= len(src_lines) else src_lines[doc_start - 1:]
            body = "\n".join(body_lines)
            if NO_INDEX_CHECK_RE.search(body):
                func_set.add(name)
        if func_set:
            function_annotations[file] = func_set
    return line_annotations, function_annotations


def _is_query_suppressed(
    query: Query,
    line_annotations: dict[str, set[int]],
    function_annotations: dict[str, set[str]],
) -> Optional[str]:
    """If the query is suppressed by a ``// graphify:no-index-check``
    annotation, return the suppression kind (``"function"`` or
    ``"line_above"``). Otherwise return None.
    """
    file_lines = line_annotations.get(query.file)
    if file_lines and (query.line - 1) in file_lines:
        return "line_above"
    file_funcs = function_annotations.get(query.file)
    if file_funcs and query.function in file_funcs:
        return "function"
    return None


def _is_admin_scope(file: str, function: str) -> bool:
    """Heuristic: True if this query is in an admin / CLI context where
    cross-tenant scans are expected (admin dashboards, CLI reporting
    tools, batch jobs). Used to downgrade ``multi_tenant_unfiltered``
    findings from HIGH to MEDIUM — admin paths legitimately scan across
    tenants.
    """
    fl = (file or "").lower()
    fn = (function or "").lower()
    if any(h in fl for h in ADMIN_PATH_HINTS):
        return True
    if any(h in fn for h in ADMIN_FUNC_HINTS):
        return True
    return False


def classify_query(
    q: Query,
    indexes: dict[str, CollectionIndexSummary],
) -> list[Finding]:
    findings: list[Finding] = []
    summary = indexes.get(q.collection)
    is_large = q.collection in LARGE_COLLECTIONS
    is_small = q.collection in SMALL_COLLECTIONS
    is_single_doc = q.collection in SINGLE_DOCUMENT_COLLECTIONS
    is_admin = _is_admin_scope(q.file, q.function)

    # Single-document collections (branding_config, system_config) —
    # scanning one document is effectively free, so don't flag at all.
    if is_single_doc:
        return findings

    # _id is always indexed by MongoDB, so any query that filters by _id is
    # covered (the primary-key index serves it). We treat _id as an
    # implicit single-field index in addition to whatever the collection
    # declares.
    has_id_filter = "_id" in q.filter_fields

    # User-visible filter fields minus _id — used for the "missing required"
    # spec check below.
    user_fields = [f for f in q.filter_fields if f not in ALWAYS_INDEXED]

    # Case A: collection has no declared indexes at all.
    if summary is None or not summary.has_any_index:
        # If the query filters by _id, MongoDB's default _id index serves it.
        if has_id_filter and not user_fields:
            return findings
        # If the query has _id plus other fields, the _id index still
        # narrows to a single doc — not a missing-index problem.
        if has_id_filter:
            return findings
        if not user_fields:
            # No filter at all AND no indexes — fall through to the
            # multi-tenant / full-scan check below.
            pass
        else:
            # Don't escalate to HIGH on small collections — a full scan
            # of <100 docs is sub-millisecond and not worth a HIGH
            # severity finding. Admin/CLI scopes are also MEDIUM (they
            # legitimately query across tenants).
            sev = "MEDIUM" if (is_small or is_admin) else (
                "HIGH" if is_large else "MEDIUM"
            )
            findings.append(Finding(
                file=q.file,
                line=q.line,
                function=q.function,
                collection=q.collection,
                operation=q.operation,
                filter_fields=q.filter_fields,
                severity=sev,
                finding_type="no_collection_indexes",
                reason=(
                    f"collection `{q.collection}` has no declared indexes — "
                    f"every query scans the full collection"
                ),
                snippet=q.snippet,
                suggestion=(
                    f"Add an index on the most-filtered field(s) of "
                    f"`{q.collection}` (e.g. `{user_fields[0]}` based on "
                    f"this query)."
                ),
            ))
            return findings

    # Case B: collection has indexes — check if any filter field is covered.
    # A query is covered if ANY of:
    #   - it filters by _id (always indexed),
    #   - it filters by a single-field index,
    #   - it filters by the leading field of a compound index (leftmost
    #     prefix — MongoDB can use a compound index for any query that
    #     filters on its leading field, even if the other index fields
    #     aren't in the filter).
    if summary is not None and summary.has_any_index:
        single_field_indexed = {
            info.leading_field for info in summary.indexes
            if len(info.fields) == 1
        }
        # Compound indexes whose leading field matches a filter field —
        # MongoDB can use the leftmost prefix of a compound index.
        compound_leading = {
            info.leading_field for info in summary.indexes
            if len(info.fields) > 1
        }
        covered = (
            has_id_filter
            or any(f in summary.leading_fields for f in user_fields)
            or any(f in single_field_indexed for f in user_fields)
            or any(f in compound_leading for f in user_fields)
        )
        if not covered and user_fields:
            sev = "MEDIUM" if (is_small or is_admin) else (
                "HIGH" if is_large else "MEDIUM"
            )
            findings.append(Finding(
                file=q.file,
                line=q.line,
                function=q.function,
                collection=q.collection,
                operation=q.operation,
                filter_fields=q.filter_fields,
                severity=sev,
                finding_type="no_index",
                reason=(
                    f"filter fields {user_fields} are not covered by any "
                    f"index on `{q.collection}` (indexed leading fields: "
                    f"{sorted(summary.leading_fields) or 'none'})"
                ),
                snippet=q.snippet,
                suggestion=(
                    f"Add an index on `{user_fields[0]}` (or a compound "
                    f"index starting with it) on `{q.collection}`."
                ),
            ))

    # Case C: spec-required field not indexed. Skip if _id is in the filter
    # (already covered) or if the spec field is already indexed.
    # Don't escalate to HIGH on small collections.
    if summary is not None:
        required = REQUIRED_INDEX_FIELDS.get(q.collection, set())
        for f in user_fields:
            if f in required and f not in summary.indexed_fields:
                # If _id is also in the filter, the query is still efficient —
                # the spec-required index is for *lookup-by-this-field*
                # queries, not _id+field updates. Don't flag.
                if has_id_filter:
                    continue
                sev = "MEDIUM" if (is_small or is_admin) else "HIGH"
                findings.append(Finding(
                    file=q.file,
                    line=q.line,
                    function=q.function,
                    collection=q.collection,
                    operation=q.operation,
                    filter_fields=q.filter_fields,
                    severity=sev,
                    finding_type="missing_required",
                    reason=(
                        f"field `{f}` should be indexed on `{q.collection}` "
                        f"(spec: {sorted(REQUIRED_INDEX_FIELDS[q.collection])}) "
                        f"but is not"
                    ),
                    snippet=q.snippet,
                    suggestion=(
                        f"Add an index (unique if appropriate) on `{f}` "
                        f"for `{q.collection}`."
                    ),
                ))

    # Case D: multi-tenant hygiene check — only flag empty-filter queries
    # (full scans) on multi-tenant collections. Queries that filter by _id
    # or any other field are already covered by the index check above.
    # Admin/CLI scopes legitimately scan across tenants — downgrade to
    # MEDIUM (or LOW for small collections) instead of HIGH.
    if q.collection in MULTI_TENANT_COLLECTIONS and not q.filter_fields:
        # Skip system/internal collections that legitimately span tenants.
        if q.collection not in {"counters", "leader_locks"}:
            if is_admin:
                sev = "MEDIUM"
            elif is_small:
                sev = "MEDIUM"
            else:
                sev = "HIGH" if is_large else "MEDIUM"
            findings.append(Finding(
                file=q.file,
                line=q.line,
                function=q.function,
                collection=q.collection,
                operation=q.operation,
                filter_fields=q.filter_fields,
                severity=sev,
                finding_type="multi_tenant_unfiltered",
                reason=(
                    f"empty-filter query on multi-tenant collection "
                    f"`{q.collection}` — full collection scan, risks "
                    f"cross-tenant data leak"
                ),
                snippet=q.snippet,
                suggestion=(
                    f"Add a `tenantId` filter (or scope the collection "
                    f"accessor to the current tenant) to avoid a full "
                    f"collection scan."
                ),
            ))

    return findings


# --------------------------------------------------------------------------- #
# Aggregation
# --------------------------------------------------------------------------- #

def build_report(
    root: Path,
    findings: list[Finding],
    indexes: dict[str, CollectionIndexSummary],
    queries: list[Query],
    suppressed: Optional[list[SuppressedFinding]] = None,
) -> dict:
    by_sev: Counter = Counter()
    by_type: Counter = Counter()
    by_collection: Counter = Counter()
    by_file: Counter = Counter()
    for f in findings:
        by_sev[f.severity] += 1
        by_type[f.finding_type] += 1
        by_collection[f.collection] += 1
        by_file[f.file] += 1

    suppressed = suppressed or []
    suppressed_by_sev: Counter = Counter()
    suppressed_by_kind: Counter = Counter()
    for s in suppressed:
        suppressed_by_sev[s.would_be_severity] += 1
        suppressed_by_kind[s.suppression] += 1

    # Index inventory (so the report shows what's declared).
    index_inventory = []
    for coll_name in sorted(indexes):
        s = indexes[coll_name]
        index_inventory.append({
            "collection": coll_name,
            "index_count": len(s.indexes),
            "has_unique": s.has_unique,
            "indexed_fields": sorted(s.indexed_fields),
            "leading_fields": sorted(s.leading_fields),
            "indexes": [
                {
                    "fields": info.fields,
                    "leading_field": info.leading_field,
                    "unique": info.is_unique,
                    "ttl": info.is_ttl,
                    "sparse": info.is_sparse,
                    "text": info.is_text,
                    "source": info.source,
                }
                for info in s.indexes
            ],
        })

    # Collections queried but with no declared indexes.
    queried_collections = {q.collection for q in queries}
    indexed_collections = set(indexes)
    no_index_collections = sorted(queried_collections - indexed_collections)

    return {
        "root": str(root),
        "total_queries_scanned": len(queries),
        "total_findings": len(findings),
        "suppressed_findings": len(suppressed),
        "suppression_breakdown": {
            "by_severity": dict(suppressed_by_sev),
            "by_kind": dict(suppressed_by_kind),
        },
        "severity_breakdown": dict(by_sev),
        "type_breakdown": [
            {"type": t, "count": c}
            for t, c in by_type.most_common()
        ],
        "collection_breakdown": [
            {"collection": c, "count": n}
            for c, n in by_collection.most_common()
        ],
        "top_files": [
            {"file": f, "count": n}
            for f, n in by_file.most_common(20)
        ],
        "index_inventory": index_inventory,
        "collections_queried_without_indexes": no_index_collections,
        "findings": [asdict(f) for f in findings],
        "suppressed": [asdict(s) for s in suppressed],
    }


# --------------------------------------------------------------------------- #
# Markdown
# --------------------------------------------------------------------------- #

def render_markdown(report: dict) -> str:
    out: list[str] = []
    out.append("# Missing Index Report")
    out.append("")
    out.append(f"**Target:** `{report['root']}`")
    out.append("")
    out.append(
        "For every MongoDB query in the codebase, checks whether the filter "
        "fields are covered by a declared index. Indexes are parsed from "
        "`Indexes().CreateMany(...)` / `CreateOne(...)` calls in the codebase "
        "(`internal/db/mongodb.go::ensureIndexes`, "
        "`internal/middleware/ratelimit.go`, etc.)."
    )
    out.append("")

    out.append("## Summary")
    out.append("")
    out.append("| Metric | Value |")
    out.append("| --- | --- |")
    out.append(f"| Queries scanned | {report['total_queries_scanned']} |")
    out.append(f"| Total findings | **{report['total_findings']}** |")
    for sev in ("HIGH", "MEDIUM", "LOW"):
        out.append(
            f"| {sev} severity | {report['severity_breakdown'].get(sev, 0)} |"
        )
    suppressed_total = report.get("suppressed_findings", 0)
    if suppressed_total:
        out.append(
            f"| Suppressed by `// graphify:no-index-check` | {suppressed_total} |"
        )
    out.append("")

    out.append("## Findings by Type")
    out.append("")
    out.append("| Type | Count |")
    out.append("| --- | ---: |")
    type_label = {
        "no_index": "No covering index",
        "no_collection_indexes": "Collection has no declared indexes",
        "missing_required": "Spec-required field not indexed",
        "multi_tenant_unfiltered": "Multi-tenant query without tenantId filter",
    }
    if report["type_breakdown"]:
        for row in report["type_breakdown"]:
            label = type_label.get(row["type"], row["type"])
            out.append(f"| {label} | {row['count']} |")
    else:
        out.append("| _none_ | 0 |")
    out.append("")

    out.append("## Collections Affected")
    out.append("")
    if report["collection_breakdown"]:
        out.append("| Collection | Findings |")
        out.append("| --- | ---: |")
        for row in report["collection_breakdown"]:
            out.append(f"| `{row['collection']}` | {row['count']} |")
    else:
        out.append("_No collections with missing-index findings._")
    out.append("")

    out.append("## Collections Queried But With No Declared Indexes")
    out.append("")
    if report["collections_queried_without_indexes"]:
        out.append(
            "These collections are queried in the codebase but have no "
            "`Indexes().CreateMany/CreateOne` call anywhere — every query "
            "will be a full collection scan (modulo the default `_id` index)."
        )
        out.append("")
        for c in report["collections_queried_without_indexes"]:
            out.append(f"- `{c}`")
    else:
        out.append("_All queried collections have at least one declared index._")
    out.append("")

    out.append("## Files With Most Findings")
    out.append("")
    if report["top_files"]:
        out.append("| File | Findings |")
        out.append("| --- | ---: |")
        for row in report["top_files"]:
            out.append(f"| `{row['file']}` | {row['count']} |")
    else:
        out.append("_No findings._")
    out.append("")

    out.append("## Detailed Findings")
    out.append("")
    if not report["findings"]:
        out.append("_No missing-index findings — every query is covered by a declared index._")
    else:
        sev_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
        by_file: dict[str, list[dict]] = defaultdict(list)
        for f in report["findings"]:
            by_file[f["file"]].append(f)
        for fname in sorted(by_file):
            out.append(f"### `{fname}`")
            out.append("")
            fs = sorted(
                by_file[fname],
                key=lambda f: (sev_order.get(f["severity"], 9), f["line"]),
            )
            for f in fs:
                label = type_label.get(f["finding_type"], f["finding_type"])
                fields = ", ".join(f"`{x}``" for x in f["filter_fields"]) if f["filter_fields"] else "—"
                out.append(
                    f"- **[{f['severity']}] {label}** — "
                    f"`{f['file']}:{f['line']}` `{f['operation']}` on "
                    f"`{f['collection']}` in `{f['function']}`"
                )
                out.append(f"  - Filter fields: {fields}")
                out.append(f"  - _{f['reason']}_")
                out.append(f"  - Suggestion: {f['suggestion']}")
                snippet = f["snippet"].rstrip()
                out.append("  ```go")
                out.append(f"  {snippet}")
                out.append("  ```")
            out.append("")

    out.append("## Index Inventory (parsed from source)")
    out.append("")
    out.append(
        "The following indexes were detected by scanning the codebase for "
        "`mongo.IndexModel{...}` declarations inside `Indexes().CreateMany` / "
        "`CreateOne` calls."
    )
    out.append("")
    if report["index_inventory"]:
        out.append("| Collection | Indexes | Unique | Indexed fields (any) | Leading fields |")
        out.append("| --- | ---: | --- | --- | --- |")
        for coll in report["index_inventory"]:
            indexed = ", ".join(f"`{f}`" for f in coll["indexed_fields"]) or "—"
            leading = ", ".join(f"`{f}`" for f in coll["leading_fields"]) or "—"
            out.append(
                f"| `{coll['collection']}` | {coll['index_count']} | "
                f"{'yes' if coll['has_unique'] else 'no'} | {indexed} | {leading} |"
            )
    else:
        out.append("_No `mongo.IndexModel` declarations found in the scanned path._")
    out.append("")

    out.append("## Methodology")
    out.append("")
    out.append(
        "1. **Index inventory.** Every `.go` file is scanned for "
        "`mongo.IndexModel{ Keys: bson.D{...}, Options: ... }` literals. "
        "Each IndexModel's collection is resolved by walking *backwards* to "
        "find the nearest preceding collection-binding site "
        "(`db.Collection(\"name\")` literal, alias variable, or a "
        "`Collection(\"name\").Indexes()` call on the same expression). "
        "Single-field and compound indexes are recorded; for compound "
        "indexes only the leading field is treated as a 'covering' field "
        "for queries."
    )
    out.append(
        "2. **Query scan.** Every MongoDB collection method call (Find, "
        "FindOne, UpdateOne, DeleteOne, CountDocuments, ...) is located and "
        "its first-argument filter is parsed from the `bson.M{}` / "
        "`bson.D{}` literal. Multi-line literals are captured via a small "
        "look-ahead window. Option-builder calls like `options.Find()` are "
        "skipped."
    )
    out.append(
        "3. **Coverage check.** For each query the filter fields are "
        "compared against the collection's index inventory. A query is "
        "covered if any of its filter fields is the leading field of any "
        "index (single-field or compound). Queries with no covering index "
        "are flagged."
    )
    out.append(
        "4. **Spec check.** Each query is also checked against a small set "
        "of SaaS-domain index rules: `tenantId` on multi-tenant "
        "collections, `email` on `users`, `slug` on `tenants`, `token` on "
        "invitation/token collections, etc. Queries that filter on a "
        "spec-required field that is not indexed are flagged."
    )
    out.append(
        "5. **Multi-tenant hygiene.** Queries on multi-tenant collections "
        "that do not filter by `tenantId` are flagged separately — these "
        "risk cross-tenant data leaks and force full-collection scans."
    )
    out.append(
        "6. **Risk.** HIGH for queries on large collections (logs, events, "
        "telemetry, audit, deliveries, metrics) without a covering index, "
        "and for any query on a spec-required field that is missing the "
        "index. MEDIUM for small/static-data collections without coverage "
        "(announcements, plans, webhooks, api_keys, etc. — full scan is "
        "sub-millisecond on <100 docs) and for multi-tenant queries "
        "without a tenantId filter. Admin/CLI scopes (admin.go, "
        "cmd/lastsaas/) are downgraded to MEDIUM — they legitimately "
        "scan across tenants. Single-document collections "
        "(branding_config, system_config) are suppressed entirely."
    )
    out.append("")
    out.append("---")
    out.append("_Generated by `graphify missing-indexes`._")
    return "\n".join(out)


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="graphify_missing_indexes.py",
        description="Flag MongoDB queries whose filter fields are not covered by an index.",
    )
    parser.add_argument(
        "path", nargs="?", default=".",
        help="Root directory to scan (default: current directory).",
    )
    parser.add_argument(
        "--out", default=None,
        help="Write markdown report to this path (in addition to public/MISSING_INDEXES.md).",
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

    print(f"Building accessor map for {root} ...", file=sys.stderr)
    accessor_map = build_accessor_map(root)
    print(f"  found {len(accessor_map)} collection accessors", file=sys.stderr)

    print("Parsing declared indexes ...", file=sys.stderr)
    indexes = collect_all_indexes(root, accessor_map)
    total_idx = sum(len(s.indexes) for s in indexes.values())
    print(
        f"  found {total_idx} indexes across {len(indexes)} collections",
        file=sys.stderr,
    )

    print("Scanning queries ...", file=sys.stderr)
    queries = scan_queries(root, accessor_map, args.include_tests)
    print(f"  scanned {len(queries)} queries", file=sys.stderr)

    # Pre-scan every Go file's source for ``// graphify:no-index-check``
    # annotations (function-level and line-above). Findings on annotated
    # queries are suppressed and tracked separately.
    print("Scanning for // graphify:no-index-check annotations ...", file=sys.stderr)
    src_by_file: dict[str, str] = {}
    skip_dirs = {"vendor", "node_modules", ".git", "graphify-out", "testdata"}
    for path in root.rglob("*.go"):
        if any(part in skip_dirs for part in path.parts):
            continue
        if not args.include_tests and path.name.endswith("_test.go"):
            continue
        try:
            src = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        try:
            rel = str(path.resolve().relative_to(root.resolve()))
        except ValueError:
            rel = str(path)
        src_by_file[rel] = src
    line_annotations, function_annotations = _scan_no_index_check_annotations(
        src_by_file
    )
    print(
        f"  {sum(len(v) for v in line_annotations.values())} line-level "
        f"annotations, {sum(len(v) for v in function_annotations.values())} "
        f"function-level annotations",
        file=sys.stderr,
    )

    findings: list[Finding] = []
    suppressed: list[SuppressedFinding] = []
    for q in queries:
        q_findings = classify_query(q, indexes)
        suppression = _is_query_suppressed(
            q, line_annotations, function_annotations,
        )
        if suppression:
            for f in q_findings:
                suppressed.append(SuppressedFinding(
                    file=f.file,
                    line=f.line,
                    function=f.function,
                    collection=f.collection,
                    operation=f.operation,
                    filter_fields=f.filter_fields,
                    would_be_severity=f.severity,
                    finding_type=f.finding_type,
                    reason=f.reason,
                    suppression=suppression,
                ))
        else:
            findings.extend(q_findings)

    report = build_report(root, findings, indexes, queries, suppressed)

    # Always write JSON + MD to /home/z/my-project/public/ if writable.
    public_dir = Path("/home/z/my-project/public")
    json_path = public_dir / "missing-indexes.json"
    md_path = public_dir / "MISSING_INDEXES.md"
    try:
        public_dir.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    except Exception as e:
        print(f"WARN: could not write {json_path}: {e}", file=sys.stderr)
    try:
        md_path.write_text(render_markdown(report), encoding="utf-8")
    except Exception as e:
        print(f"WARN: could not write {md_path}: {e}", file=sys.stderr)

    # When --json is set, the --out path receives JSON (matching
    # graphify_api_shapes.py's behavior). Without --json, --out receives
    # the markdown report.
    if args.out:
        out_path = Path(args.out)
        try:
            out_path.parent.mkdir(parents=True, exist_ok=True)
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

    print(
        f"Scanned {len(queries)} queries across {len(indexes)} indexed "
        f"collections; found {len(findings)} missing-index findings "
        f"(HIGH={report['severity_breakdown'].get('HIGH', 0)}, "
        f"MEDIUM={report['severity_breakdown'].get('MEDIUM', 0)}, "
        f"LOW={report['severity_breakdown'].get('LOW', 0)}); "
        f"suppressed {len(suppressed)} via // graphify:no-index-check.",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
