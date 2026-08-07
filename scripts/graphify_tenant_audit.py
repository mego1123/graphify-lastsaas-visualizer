#!/usr/bin/env python3
"""graphify_tenant_audit — tenant-isolation security auditor for Go MongoDB code.

Scans all .go files under the target path and finds MongoDB queries that are
missing a ``tenantId`` filter — the #1 cause of cross-tenant data leakage in a
multi-tenant SaaS.

For every detected query (``Find`` / ``FindOne`` / ``InsertOne`` /
``UpdateOne`` / ``UpdateMany`` / ``DeleteOne`` / ``DeleteMany`` / ``Aggregate``
/ ``CountDocuments`` / ``FindOneAndUpdate`` / ``FindOneAndDelete`` /
``FindOneAndReplace`` / ``ReplaceOne`` / ``UpdateByID`` / ``InsertMany`` /
``BulkWrite``), the script:

  1. Resolves the underlying MongoDB collection (via direct ``.Collection("x")``
     calls or accessor methods like ``h.db.Users()`` defined in the codebase).
  2. Extracts the filter argument — handling inline ``bson.M{}`` / ``bson.D{}``
     literals, ``nil``, and *variable* filters by tracing the variable back to
     its definition (including dynamic field additions like
     ``filter["tenantId"] = tenant.ID``).
  3. Checks whether the filter contains ``tenantId`` or ``tenant_id``.
  4. Classifies the query as OK / MEDIUM / HIGH / CRITICAL:
       - OK       — has a ``tenantId`` filter.
       - MEDIUM   — on a "global" collection (``tenants``, ``plans``,
                    ``system_config``, ``system_logs``, ``users``) that
                    legitimately doesn't need tenant filtering (or is
                    cross-tenant by nature).
       - HIGH     — read op (Find/FindOne/Aggregate/CountDocuments) without
                    ``tenantId`` on a tenant-scoped collection.
       - CRITICAL — write op (InsertOne/UpdateOne/DeleteOne/...) without
                    ``tenantId`` on a tenant-scoped collection.

  5. Records each query with file, line, collection, function, operation,
     filter fields, the raw snippet, a safe-key heuristic flag (queries that
     filter on a globally-unique key like ``_id`` / ``tokenHash`` / ``slug``
     are noted as likely false positives), and a human-readable note.

A "violation" is any query classified as HIGH or CRITICAL. MEDIUM queries on
global collections are reported separately for context.

Usage:
    python graphify_tenant_audit.py [path] [--out report.md] [--json]

Outputs:
    - JSON written to /home/z/my-project/public/tenant-audit.json (best effort)
    - Markdown written to /home/z/my-project/public/TENANT_AUDIT.md (best effort)
    - Markdown written to --out path if specified
    - JSON to stdout if --json given (without a value)

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

# Operations covered by the audit. The 12 in the spec plus the closely-related
# UpdateByID / InsertMany / BulkWrite / ReplaceOne / FindOneAndReplace, which
# share the same tenant-isolation concerns.
READ_OPS: set[str] = {
    "Find",
    "FindOne",
    "Aggregate",
    "CountDocuments",
    "EstimatedDocumentCount",  # never has a filter; informational only
}

WRITE_OPS: set[str] = {
    "InsertOne",
    "InsertMany",
    "UpdateOne",
    "UpdateMany",
    "DeleteOne",
    "DeleteMany",
    "FindOneAndUpdate",
    "FindOneAndDelete",
    "FindOneAndReplace",
    "ReplaceOne",
    "UpdateByID",
    "BulkWrite",
}

# Operations where the 2nd positional argument is the *filter*.
FILTER_AT_POS_2: set[str] = {
    "Find",
    "FindOne",
    "UpdateOne",
    "UpdateMany",
    "DeleteOne",
    "DeleteMany",
    "CountDocuments",
    "FindOneAndUpdate",
    "FindOneAndDelete",
    "FindOneAndReplace",
    "ReplaceOne",
}

ALL_OPERATIONS: tuple[str, ...] = tuple(
    sorted(READ_OPS | WRITE_OPS)
)

OP_RE = re.compile(
    r"\.(" + "|".join(re.escape(op) for op in ALL_OPERATIONS) + r")\s*\("
)

# Function declaration: ``func (recv) Name(args) (rets) {`` or ``func Name(...) {``.
FUNC_RE = re.compile(
    r"^func\s+(?:\([^)]*\)\s+)?([A-Za-z_]\w*)\s*[(<]"
)

# Direct collection access: ``db.Collection("name")``.
COLLECTION_LITERAL_RE = re.compile(
    r'\.Collection\(\s*"([^"]+)"\s*\)'
)

# Accessor definition: ``func (recv) Name() *mongo.Collection { return <expr>.Collection("name") }``.
ACCESSOR_DEF_RE = re.compile(
    r"func\s+(?:\([^)]*\)\s+)?([A-Z]\w*)\s*\(\s*\)\s*\*mongo\.Collection\s*\{[^}]*?"
    r'\.Collection\(\s*"([^"]+)"\s*\)',
    re.DOTALL,
)

# Variable aliasing a collection accessor result.
#   ``col := m.Database.Collection("plans")``
#   ``col := s.db.Plans()``
ALIAS_LITERAL_RE = re.compile(
    r"(\w+)\s*:?=\s*[\w\.\[\]\*]+\.Collection\(\s*\"([^\"]+)\"\s*\)"
)
ALIAS_ACCESSOR_RE = re.compile(
    r"(\w+)\s*:?=\s*[\w\.\[\]\*]+\.(\w+)\(\s*\)"
)

# bson.D blocks: ``bson.D{{Key: "f", Value: ...}, {"f2", v}}``.
BSON_D_BLOCK_RE = re.compile(
    r'\bbson\.D\s*\{([^}]*)\}'
)
BSON_D_KEYVAL_NAMED_RE = re.compile(
    r'Key:\s*"([^"]+)"\s*,\s*Value:'
)
BSON_D_KEYVAL_POS_RE = re.compile(
    r'\{\s*"([^"]+)"\s*,'
)

# bson.M{"field": value, "other": value}
BSON_M_RE = re.compile(
    r'\bbson\.M\s*\{([^}]*)\}'
)
BSON_M_KEY_RE = re.compile(
    r'"([^"]+)"\s*:'
)

# map[string]interface{}{"field": value} — occasionally used in tests.
MAP_LITERAL_RE = re.compile(
    r'map\[string\]interface\{\}\s*\{([^}]*)\}'
)
MAP_KEY_RE = re.compile(
    r'"([^"]+)"\s*:'
)

# Variable assignment of a filter:
#   ``filter := bson.M{...}``
#   ``filter := bson.D{...}``
#   ``filter := map[string]interface{}{...}``
FILTER_VAR_DEF_RE = re.compile(
    r"(\w+)\s*:?=\s*(bson\.M|bson\.D|map\[string\]interface\{\})\s*\{"
)

# Variable assignment of a struct literal:
#   ``invitation := models.Invitation{...}``
#   ``user := &models.User{...}``
# Used by InsertOne / InsertMany to detect whether the inserted document
# carries a tenantId field.
STRUCT_VAR_DEF_RE = re.compile(
    r"(\w+)\s*:?=\s*&?(models\.)?([A-Z]\w*)\s*\{"
)

# Dynamic field addition to a map:
#   ``filter["tenantId"] = tenant.ID``
#   ``filter["$or"] = []bson.M{...}``
FILTER_VAR_SET_RE = re.compile(
    r'(\w+)\[\s*"([^"]+)"\s*\]\s*=?='
)

# Variable assignment of an aggregate pipeline:
#   ``pipeline := []bson.M{...}``
#   ``pipeline := mongo.Pipeline{...}``
#   ``pipeline := bson.A{...}``  (BSON array — also used for pipelines)
PIPELINE_VAR_DEF_RE = re.compile(
    r"(\w+)\s*:?=\s*(\[\]bson\.M|\[\]bson\.D|mongo\.Pipeline|bson\.A)\s*\{"
)

# Tenant-id field names. The codebase uses camelCase ``tenantId`` for the
# MongoDB field name and snake_case ``tenant_id`` is included for robustness.
TENANT_ID_FIELDS: set[str] = {"tenantId", "tenant_id"}

# Collections that are *global* and legitimately do not need tenant filtering.
# Per the spec:
#   tenants        — the tenant records themselves
#   plans          — global subscription plans
#   system_config  — system-wide config
#   system_logs    — may be filtered differently (by category, severity, etc.)
#   users          — users exist across tenants (but queries should still be
#                    scoped; flagged as MEDIUM, not OK)
EXEMPT_COLLECTIONS: set[str] = {
    "tenants",
    "plans",
    "system_config",
    "system_logs",
    "users",
}

# Collections whose accessor names map to a global collection — used to make
# the "exempt" check robust when collection resolution falls back to the
# accessor name. Mirrors EXEMPT_COLLECTIONS but in PascalCase.
EXEMPT_ACCESSORS: set[str] = {
    "Tenants",
    "Plans",
    "SystemConfig",
    "SystemLogs",
    "Users",
}

# Filter keys that are *globally unique* identifiers — a query that filters
# on one of these keys cannot accidentally leak cross-tenant data because the
# key uniquely identifies a single document regardless of tenant.
SAFE_UNIQUE_KEYS: set[str] = {
    "_id",
    "slug",
    "tokenHash",
    "token",
    "keyHash",
    "code",
    "eventId",
    "credentialId",
    "machineId",
    "email",
    "name",
    "invoiceNumber",
    "familyId",
    "codeHash",
    "credentialID",
    "webhookId",
}

# --------------------------------------------------------------------------- #
# False-positive suppression — context heuristics
# --------------------------------------------------------------------------- #
#
# In real-world multi-tenant codebases, many MongoDB queries legitimately
# omit ``tenantId`` for one of the following reasons. The auditor now
# recognises all of these and downgrades them from HIGH/CRITICAL violations
# to MEDIUM informational notes (so they still appear in the report for
# review, but don't inflate the violation count).

# Functions that run as background system tasks (started via ``go func()``,
# tickers, or worker loops). They have no request context and therefore no
# ``tenantId`` available — they operate on system-wide collections by design.
BACKGROUND_TASK_FUNCS: set[str] = {
    "flushLoop",            # log buffer flusher
    "tryAcquireOrRenew",    # leader-election lock acquisition
    "heartbeat",            # node heartbeat
    "registerNode",         # node registration
    "dispatch",             # webhook dispatcher loop
    "deliverWithRetry",     # webhook delivery with retry
    "collectDaily",         # daily metrics collection
    "collectAndStore",      # generic collector
    "aggregateDailyPoints", # daily aggregation
    "isLeader",             # leader check
    "releaseLock",          # leader-lock release
    "handleCheckoutCompleted",      # Stripe webhook handler (background)
    "handleInvoicePaymentFailed",   # Stripe webhook handler (background)
    "computeLiveRevenue",           # background revenue computation
    "sendUpgradeMessage",           # post-upgrade side-effect message
    "cleanupExpired",               # generic TTL cleanup
    "CleanupCollections",           # generic TTL cleanup
    "NextInvoiceNumber",            # counter increment (atomic, no tenant context)
}

# Internal service methods called from admin HTTP handlers (the route
# classifier only catches the *handler* names registered on routers, not
# the underlying service methods they delegate to). These methods compute
# admin analytics over system-wide collections and don't take a tenantId
# — they're called from ``pmHandler.GetFunnel`` / ``GetKPIs`` / etc.,
# which are registered on ``adminAPI`` (root tenant + user role, sees ALL
# tenants by design).
ADMIN_SERVICE_FUNCS: set[str] = {
    # telemetry/service.go — called from pmHandler (admin)
    "FunnelMetrics",
    "CustomEventSummary",
    "EngagementMetrics",
    "RetentionCohorts",
    "KPIs",
    "ListEventTypes",
    "countDistinct",
    "weeklyActiveUsers",
    "monthlyActiveUsers",
    "topCustomEvents",
    "creditConsumptionTrend",
    "medianTimeToFirstPurchase",
    "subscriberTrend",
    "mrrTrend",
    "GetAggregateMetrics",
    "GetCurrentMetrics",
    "GetIntegrationCounts24h",
    "FunnelMetrics",
    # billing/service.go — admin-side metrics
    "AdminGetMetrics",
    "AdminListTransactions",
    # Stripe webhook handler internals
    "GetOrCreatePrice",
    "resolveStripeProducts",
    "buildProductNameMap",
    # Config-store helpers (called from admin handlers)
    "Load",
    "Reload",
    "Set",
    "Seed",
}

# Public endpoint handlers — no auth, content visible to everyone. These
# legitimately query published/global content without ``tenantId``.
PUBLIC_ENDPOINT_FUNCS: set[str] = {
    "ListPublic",
    "ListPublicPages",
    "ListBundlesPublic",
    "ListPlansPublic",
    "GetPublicPage",
    "GetBranding",
    "ServeAsset",
    "ServeMedia",
    "DocsHTML",
    "DocsMarkdown",
    "DocsOpenAPI",
    "Status",            # bootstrap status
    "HandleWebhook",     # Stripe webhook (signature-verified, not tenant-scoped)
    "TrackAnonymous",    # anonymous telemetry
    "GetProviders",      # auth provider discovery
}

# Auth-flow handlers — operate on user-scoped collections (refresh_tokens,
# verification_tokens, etc.) where the user hasn't selected a tenant yet.
# Filters on userId / token / tokenHash are valid scopes here.
AUTH_FLOW_FUNCS: set[str] = {
    "Register", "Login", "Refresh", "VerifyEmail", "ResendVerification",
    "ForgotPassword", "ResetPassword", "ExchangeCode", "MagicLinkRequest",
    "MagicLinkVerify", "MFAChallenge", "MFASetup", "MFAVerifySetup",
    "MFADisable", "MFARegenerateRecoveryCodes",
    "GoogleOAuth", "GoogleOAuthCallback",
    "GitHubOAuth", "GitHubOAuthCallback",
    "MicrosoftOAuth", "MicrosoftOAuthCallback",
    "GetMe", "Logout", "ChangePassword", "AcceptInvitation",
    "ListSessions", "RevokeSession", "RevokeAllSessions",
    "UpdatePreferences", "CompleteOnboarding",
    "DeleteAccount", "ExportData",
    "storeRefreshToken", "sendVerificationEmail", "createAuthCodeRedirect",
    "isTokenRevoked", "authenticateAPIKey",
    "lookupUserWithMemberships", "getUserMemberships",
    "acceptInvitationForUser",
    # User-scoped message inbox
    "ListMessages", "UnreadCount", "MarkRead",
}

# User-scoped collections — documents belong to a user (not a tenant). A
# filter on ``userId`` is a valid scope. Populated below in
# ``build_user_scoped_collections`` once struct fields are known, but a
# hardcoded seed list is kept here as a fallback.
USER_SCOPED_COLLECTIONS_SEED: set[str] = {
    "refresh_tokens",
    "verification_tokens",
    "revoked_tokens",
    "messages",
    "webauthn_credentials",
    "auth_codes",
}

# Collections known to be global by design even when their struct isn't
# found by the naming heuristic (e.g. ``counters`` → ``InvoiceCounter``).
GLOBAL_COLLECTIONS_EXTRA: set[str] = {
    "counters",
    "leader_locks",
    "webhook_events",
    "webhook_deliveries",
    "oauth_states",
    "impersonation_logs",
    "audit_log",
    "webauthn_sessions",
}

# Subdirectory paths (relative to repo root) that contain CLI tools — these
# are not HTTP request handlers and don't carry a tenantId in their context.
CLI_PATH_PARTS: tuple[str, ...] = ("cmd", "lastsaas")

# Router variable names used in main.go and their route scope. Used by
# ``build_route_classifier`` to map a HandleFunc call to a route scope.
ADMIN_ROUTERS: set[str] = {
    "adminAPI", "adminWrite", "adminOwner",
}
TENANT_ROUTERS: set[str] = {
    "tenantAPI", "tenantSettingsRouter", "inviteRouter",
    "removeRouter", "ownerRouter", "usageAPI",
    "telemetryAPI", "billingAPI", "billingOwner",
}

# Patterns we never want to count as a real query:
# - ``options.Find()`` / ``options.FindOneAndUpdate()`` etc. — these construct
#   options structs, not real queries.
OPTIONS_BUILDER_RE = re.compile(r"\boptions\s*$")


# --------------------------------------------------------------------------- #
# Data containers
# --------------------------------------------------------------------------- #


@dataclass
class Query:
    """A single MongoDB query occurrence with tenant-isolation classification."""

    file: str
    line: int
    function: str
    collection: str
    operation: str
    filter_fields: list[str] = field(default_factory=list)
    has_tenant_id: bool = False
    filter_source: str = ""          # inline | variable:<name> | nil | unknown
    risk_level: str = "OK"           # OK | MEDIUM | HIGH | CRITICAL
    is_violation: bool = False
    is_exempt_collection: bool = False
    safe_key_filter: bool = False    # filter contains a globally-unique key
    filter_snippet: str = ""
    note: str = ""
    # ---- Context heuristics (false-positive suppression) ----
    route_scope: str = "unknown"     # admin | tenant | auth | public | cli | background | unknown
    is_admin_handler: bool = False
    is_background_task: bool = False
    is_public_endpoint: bool = False
    is_auth_flow: bool = False
    is_cli_tool: bool = False
    collection_has_tenant_id: Optional[bool] = None  # None if struct not found
    collection_is_user_scoped: bool = False
    has_user_id_filter: bool = False
    suppression_reason: str = ""     # populated when downgraded from violation to MEDIUM

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class FileInfo:
    """Per-file aggregate stats."""

    path: str
    total_queries: int = 0
    violations: int = 0
    by_risk: Counter = field(default_factory=Counter)


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #


def _relative(root: Path, p: str | Path) -> str:
    try:
        return str(Path(p).resolve().relative_to(root.resolve()))
    except ValueError:
        return str(p)


def mask_strings_and_comments(text: str) -> str:
    """Replace string literals and comments with spaces (preserving length and
    newlines) so brace/paren matching is robust against braces inside strings.

    Go has raw strings (```...```), interpreted strings (``"..."``), rune
    literals (``'...'``), line comments (``//...``), and block comments
    (``/*...*/``). All are masked here.
    """
    out: list[str] = []
    i = 0
    n = len(text)
    while i < n:
        c = text[i]
        # Block comment
        if c == "/" and i + 1 < n and text[i + 1] == "*":
            end = text.find("*/", i + 2)
            if end == -1:
                # Unterminated — mask to end of file.
                for j in range(i, n):
                    out.append("\n" if text[j] == "\n" else " ")
                return "".join(out)
            for j in range(i, end + 2):
                out.append("\n" if text[j] == "\n" else " ")
            i = end + 2
            continue
        # Line comment
        if c == "/" and i + 1 < n and text[i + 1] == "/":
            end = text.find("\n", i + 2)
            if end == -1:
                end = n
            for j in range(i, end):
                out.append(" ")
            i = end
            continue
        # Raw string literal
        if c == "`":
            end = text.find("`", i + 1)
            if end == -1:
                end = n
            for j in range(i, end + 1 if end < n else n):
                out.append("\n" if text[j] == "\n" else " ")
            i = end + 1
            continue
        # Interpreted string literal
        if c == '"':
            j = i + 1
            while j < n:
                if text[j] == "\\" and j + 1 < n:
                    out.append(" ")
                    out.append(" ")
                    j += 2
                    continue
                if text[j] == '"':
                    break
                if text[j] == "\n":
                    # Unterminated string at EOL — bail.
                    break
                out.append(" ")
                j += 1
            # Mask the opening & closing quotes too.
            out.append(" ")  # opening quote already added via outer loop? no.
            # We didn't append the opening quote yet — fix that.
            # Actually the outer loop hasn't appended c yet, so we handle it here.
            i = j + 1
            # Append the closing quote as a space (if present).
            if j < n and text[j] == '"':
                out.append(" ")
            continue
        # Rune literal (single-char, possibly escaped).
        if c == "'":
            j = i + 1
            while j < n:
                if text[j] == "\\" and j + 1 < n:
                    j += 2
                    continue
                if text[j] == "'":
                    break
                if text[j] == "\n":
                    break
                j += 1
            out.append(" ")  # opening '
            for _ in range(i + 1, min(j + 1, n)):
                out.append(" ")
            i = j + 1
            continue
        out.append(c)
        i += 1
    return "".join(out)


def build_accessor_map(repo_root: Path) -> dict[str, str]:
    """Build {accessor_method_name: collection_name}.

    Scans every .go file for ``func (recv) Name() *mongo.Collection {
    return <expr>.Collection("name") }``.
    """
    accessor_map: dict[str, str] = {}
    for path in repo_root.rglob("*.go"):
        if "graphify-out" in path.parts:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except (OSError, UnicodeDecodeError):
            continue
        # NOTE: do NOT mask strings here — the collection name is itself a
        # string literal that we need to capture.
        for m in ACCESSOR_DEF_RE.finditer(text):
            name, coll = m.group(1), m.group(2)
            accessor_map.setdefault(name, coll)
    return accessor_map


def collect_struct_fields(repo_root: Path) -> dict[str, set[str]]:
    """Build {struct_name: set_of_bson_field_names}.

    Walks every Go struct declaration and extracts the bson field names from
    struct-tag annotations (e.g. ``bson:"tenantId,omitempty"`` → ``tenantId``).
    Used to check whether an Insert target struct carries a tenantId field.
    """
    struct_re = re.compile(r"^type\s+([A-Z]\w*)\s+struct\s*\{")
    # Matches the bson tag in a struct field annotation:
    #   `json:"x" bson:"tenantId,omitempty" validate:"required"`
    # captures ``tenantId`` (up to the first ``,`` or ``"``).
    tag_re = re.compile(r'bson:"([^",]+)')
    structs: dict[str, set[str]] = {}
    for path in repo_root.rglob("*.go"):
        if "graphify-out" in path.parts:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except (OSError, UnicodeDecodeError):
            continue
        lines = text.splitlines()
        i = 0
        n = len(lines)
        while i < n:
            m = struct_re.match(lines[i].strip())
            if not m:
                i += 1
                continue
            name = m.group(1)
            fields: set[str] = set()
            i += 1
            depth = 1
            while i < n and depth > 0:
                line = lines[i]
                depth += line.count("{") - line.count("}")
                if depth <= 0:
                    break
                # Extract the bson tag (first field name, ignoring omitempty etc.)
                tm = tag_re.search(line)
                if tm:
                    fname = tm.group(1).split(",")[0]
                    if fname and fname != "-":
                        fields.add(fname)
                i += 1
            structs.setdefault(name, set())
            structs[name].update(fields)
    return structs


def _collection_to_struct_name(collection: str) -> str:
    """Convert a snake_case collection name to a PascalCase struct name.

    Heuristic:
      - "ies" suffix → "y"     (e.g. webhook_deliveries → WebhookDelivery)
      - "s"  suffix  → ""      (e.g. users → User, tenant_memberships → TenantMembership)
      - otherwise   → unchanged (e.g. system_config → SystemConfig)

    Then snake_case → PascalCase (split on ``_``, capitalise each segment).
    """
    name = collection
    if name.endswith("ies"):
        name = name[:-3] + "y"
    elif name.endswith("s"):
        name = name[:-1]
    parts = [p for p in name.split("_") if p]
    return "".join(p[:1].upper() + p[1:] for p in parts)


# --------------------------------------------------------------------------- #
# Go filter tracer integration
# --------------------------------------------------------------------------- #
#
# The Python regex-based scanner in this file can't always resolve the
# fields of a *variable* filter (e.g. ``coll.Find(ctx, filter)`` where
# ``filter`` was built dynamically via ``filter["x"] = y`` patterns
# across multiple lines, possibly inside helper functions). The Go
# tool at ``scripts/go/graphify_filter_tracer/main.go`` uses go/ssa to
# trace these dynamic constructions. We invoke it as a subprocess and
# load the JSON output to get a ``{position_key: [field_names]}`` map
# keyed by ``"file:line"`` (the source location of the MongoDB call).

FILTER_TRACER_PATH = Path(__file__).resolve().parent / 'go' / 'graphify_filter_tracer' / 'main.go'


def load_go_filter_tracer(repo_root: Path) -> dict[str, list[str]]:
    """Run the Go filter tracer over the backend module and return a
    ``{position_key: [field_names]}`` map.

    The position key is ``"file:line"`` (relative file path + the line
    number of the MongoDB call site). Callers look up the dynamic
    filter fields for a query by constructing the same key from the
    query's ``file`` and ``line`` attributes.

    Returns an empty dict if the Go toolchain is unavailable or the
    tracer fails (the auditor falls back to its regex-based parser).
    """
    import os
    import subprocess
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

    out_file = Path('/tmp/graphify-tenant-filters.json')
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
            # Normalise to "relative_path:line". The tracer's file paths
            # are already relative to the module root, but the leading
            # ``backend/`` may or may not be present depending on where
            # the tool was invoked from. We try both forms when looking
            # up the position later (in ``_lookup_filter_tracer_fields``).
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
            # De-duplicate while preserving order.
            seen: set[str] = set()
            out: list[str] = []
            for f in fields:
                if f not in seen:
                    seen.add(f)
                    out.append(f)
            return out
    return None


def build_collection_struct_map(
    accessor_map: dict[str, str],
    struct_fields: dict[str, set[str]],
) -> dict[str, str]:
    """Build {collection_name: struct_name} using the snake→Pascal heuristic.

    For each collection referenced by an accessor, derive the candidate
    struct name and confirm it exists in ``struct_fields``. If the heuristic
    doesn't match, fall back to checking known special cases (e.g.
    ``counters`` → ``InvoiceCounter``).
    """
    # Hardcoded overrides for cases the naming heuristic can't resolve
    # (collections whose struct name uses acronym capitalization like
    # ``APIKey`` instead of ``ApiKey``).
    overrides: dict[str, str] = {
        "counters": "InvoiceCounter",
        "api_keys": "APIKey",
        "oauth_states": "OAuthState",
        "sso_connections": "SSOConnection",
        "webauthn_credentials": "WebAuthnCredential",
    }
    coll_to_struct: dict[str, str] = {}
    collections = set(accessor_map.values()) | set(overrides.keys())
    for coll in collections:
        if coll in overrides and overrides[coll] in struct_fields:
            coll_to_struct[coll] = overrides[coll]
            continue
        candidate = _collection_to_struct_name(coll)
        if candidate in struct_fields:
            coll_to_struct[coll] = candidate
            continue
        # Try without singularisation (some collections are already
        # singular in the DB but use a plural struct name in Go).
        if coll in struct_fields:
            coll_to_struct[coll] = coll
    return coll_to_struct


def build_user_scoped_collections(
    collection_struct_map: dict[str, str],
    struct_fields: dict[str, set[str]],
) -> set[str]:
    """Identify collections whose struct has a ``userId`` bson field.

    For these collections, filtering on ``userId`` is a valid scope — even
    if the collection also has a ``tenantId`` field, the ``userId`` filter
    already constrains the query to a single user's data (and a user's data
    can span tenants via ``tenant_memberships``).
    """
    out: set[str] = set(USER_SCOPED_COLLECTIONS_SEED)
    for coll, struct_name in collection_struct_map.items():
        fields = struct_fields.get(struct_name, set())
        if "userId" in fields:
            out.add(coll)
    return out


def build_global_collections(
    collection_struct_map: dict[str, str],
    struct_fields: dict[str, set[str]],
) -> set[str]:
    """Identify collections whose struct does NOT declare a ``tenantId`` field.

    These collections are GLOBAL BY DESIGN — they have no tenantId field to
    filter on. Examples: ``webhooks``, ``plans``, ``system_nodes``,
    ``event_definitions``, ``branding_assets``, ``api_keys``.
    """
    out: set[str] = set(EXEMPT_COLLECTIONS) | set(GLOBAL_COLLECTIONS_EXTRA)
    for coll, struct_name in collection_struct_map.items():
        fields = struct_fields.get(struct_name, set())
        if not (TENANT_ID_FIELDS & fields):
            out.add(coll)
    return out


# --------------------------------------------------------------------------- #
# Route classification — parse main.go to map handler functions to route scope
# --------------------------------------------------------------------------- #

# Matches ``<router>.HandleFunc("/path", HANDLER)`` or ``<router>.Handle("/path", ...)``
# capturing the router variable. The handler can be either a bare method value
# (``handler.Foo``) or wrapped in ``rateLimiter.RateLimitHandler(...,
# handler.Foo,)``.
ROUTER_HANDLE_RE = re.compile(
    r'\b(\w+)\.(?:HandleFunc|Handle)\s*\(\s*"[^"]*"'
)

# Matches a handler method value like ``authHandler.Login`` or
# ``plansHandler.ListPlans`` (last identifier is the function name).
HANDLER_METHOD_RE = re.compile(
    r'\b(\w+Handler)\.([A-Z]\w*)\b'
)

# Matches ``http.HandlerFunc(handler.X)`` — the X is the actual handler.
HTTPHANDLERFUNC_RE = re.compile(
    r'\bhttp\.HandlerFunc\s*\(\s*(\w+Handler)\.([A-Z]\w*)\s*\)'
)


def build_route_classifier(repo_root: Path) -> dict[str, set[str]]:
    """Parse ``cmd/server/main.go`` to extract handler-function → route-scope.

    Returns a dict with three sets of handler function names:
      - ``admin``   — registered on adminAPI/adminWrite/adminOwner (sees ALL tenants)
      - ``tenant``  — registered on tenantAPI/usageAPI/telemetryAPI/billingAPI
      - ``auth``    — registered on guarded/protectedAuth (auth flow, user-scoped)
      - ``public``  — registered on api/router (no auth)

    Falls back to an empty dict if main.go cannot be found.
    """
    result: dict[str, set[str]] = {
        "admin": set(),
        "tenant": set(),
        "auth": set(),
        "public": set(),
    }
    # Look for cmd/server/main.go under the repo root.
    candidates = [
        repo_root / "cmd" / "server" / "main.go",
        repo_root / "backend" / "cmd" / "server" / "main.go",
    ]
    main_go: Optional[Path] = None
    for c in candidates:
        if c.is_file():
            main_go = c
            break
    if main_go is None:
        # Last resort: rglob.
        for p in repo_root.rglob("main.go"):
            if "cmd" in p.parts and "server" in p.parts:
                main_go = p
                break
    if main_go is None or not main_go.is_file():
        return result

    try:
        text = main_go.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return result

    masked = mask_strings_and_comments(text)
    # Walk HandleFunc/Handle calls. We match the router.HandleFunc("/path", ...)
    # pattern on the RAW text (so the string literal "/path" is visible), but
    # use the MASKED text to find the closing paren of the call (so parens
    # inside string literals don't confuse depth tracking).
    for m in ROUTER_HANDLE_RE.finditer(text):
        router = m.group(1)
        # Find the corresponding index in the masked text (same offset since
        # mask_strings_and_comments preserves length).
        open_paren = masked.find("(", m.start())
        if open_paren == -1:
            continue
        close_paren = find_block_end(masked, open_paren, "(", ")")
        if close_paren == -1:
            continue
        call_span = text[m.start():close_paren]
        # Find all handler.Foo references in the call span. The LAST one is
        # the actual handler (rateLimiter.RateLimitHandler takes the handler
        # as its last positional argument).
        handlers = HANDLER_METHOD_RE.findall(call_span)
        if not handlers:
            # Try http.HandlerFunc(handler.X) form.
            hfd = HTTPHANDLERFUNC_RE.findall(call_span)
            handlers = hfd
        if not handlers:
            continue
        # Take the LAST handler reference (in rate-limited form, the actual
        # handler is the last positional argument).
        _, func_name = handlers[-1]
        if router in ADMIN_ROUTERS:
            result["admin"].add(func_name)
        elif router in TENANT_ROUTERS:
            result["tenant"].add(func_name)
        elif router in ("guarded", "protectedAuth", "api", "router"):
            # Auth flow + public — the heuristic below refines further.
            if func_name in PUBLIC_ENDPOINT_FUNCS:
                result["public"].add(func_name)
            else:
                result["auth"].add(func_name)
    return result


def extract_filter_fields_from_text(text: str) -> list[str]:
    """Pull field names out of bson.M / bson.D / map literals in the given
    text. Returns a de-duplicated list (preserving first-seen order).
    """
    fields: list[str] = []

    # bson.D blocks
    for block in BSON_D_BLOCK_RE.finditer(text):
        inner = block.group(1)
        for m in BSON_D_KEYVAL_NAMED_RE.finditer(inner):
            fields.append(m.group(1))
        for m in BSON_D_KEYVAL_POS_RE.finditer(inner):
            fields.append(m.group(1))

    # bson.M blocks
    for m in BSON_M_RE.finditer(text):
        for km in BSON_M_KEY_RE.finditer(m.group(1)):
            fields.append(km.group(1))

    # map[string]interface{} blocks
    for m in MAP_LITERAL_RE.finditer(text):
        for km in MAP_KEY_RE.finditer(m.group(1)):
            fields.append(km.group(1))

    # Dedupe, drop operators and empty strings.
    seen: set[str] = set()
    out: list[str] = []
    for f in fields:
        if not f or f.startswith("$") or f in seen:
            continue
        seen.add(f)
        out.append(f)
    return out


def find_block_end(text: str, start: int, open_ch: str, close_ch: str) -> int:
    """Return the index of the matching closing bracket starting at ``start``
    (which must point at ``open_ch``). Returns -1 if no match is found.
    """
    assert text[start] == open_ch
    depth = 0
    i = start
    n = len(text)
    while i < n:
        c = text[i]
        if c == open_ch:
            depth += 1
        elif c == close_ch:
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return -1


def extract_call_args(
    masked: str, raw: str, open_paren_idx: int
) -> list[str]:
    """Given the index of the opening ``(`` of a call in ``masked`` (and the
    corresponding ``raw`` text of identical length), return the list of
    top-level argument source strings (split on commas at depth 1).

    Depth tracking uses ``masked`` (so commas/braces/parens inside string
    literals don't confuse the splitter), but the returned argument text is
    sliced from ``raw`` so that filter field extraction can see the actual
    string keys (e.g. ``"tenantId"``).
    """
    if open_paren_idx >= len(masked) or masked[open_paren_idx] != "(":
        return []
    close_idx = find_block_end(masked, open_paren_idx, "(", ")")
    if close_idx == -1:
        return []
    # The inner text spans [open_paren_idx+1, close_idx) in both masked & raw.
    args: list[str] = []
    depth_paren = 0
    depth_brace = 0
    depth_brack = 0
    buf_start = open_paren_idx + 1
    i = buf_start
    n = close_idx
    while i < n:
        c = masked[i]
        if c == "(":
            depth_paren += 1
        elif c == ")":
            depth_paren -= 1
        elif c == "{":
            depth_brace += 1
        elif c == "}":
            depth_brace -= 1
        elif c == "[":
            depth_brack += 1
        elif c == "]":
            depth_brack -= 1
        elif c == "," and depth_paren == 0 and depth_brace == 0 and depth_brack == 0:
            args.append(raw[buf_start:i].strip())
            buf_start = i + 1
        i += 1
    tail = raw[buf_start:close_idx].strip()
    if tail:
        args.append(tail)
    return args


# --------------------------------------------------------------------------- #
# Per-file scanner
# --------------------------------------------------------------------------- #


def _collect_brace_window(
    masked_lines: list[str],
    raw_lines: list[str],
    start_idx: int,
    start_col: int,
    max_lines: int = 80,
) -> str:
    """Build a multi-line text window starting at
    ``raw_lines[start_idx][start_col:]`` and extending until the braces
    opened on the first line are balanced.

    Depth tracking uses ``masked_lines`` (so braces/parens inside string
    literals don't prematurely close the window), but the returned text is
    sliced from ``raw_lines`` so that filter field extraction can see the
    actual string keys (e.g. ``"tenantId"``).

    The two line arrays must have identical length and newline positions
    (which is guaranteed when both are derived from the same source via
    :func:`mask_strings_and_comments`).
    """
    n = len(masked_lines)
    if start_idx >= n:
        return ""
    first_masked = masked_lines[start_idx][start_col:]
    first_raw = raw_lines[start_idx][start_col:]
    window_lines = [first_raw]
    depth = 0
    for ch in first_masked:
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
    i = start_idx + 1
    while depth > 0 and i < n and (i - start_idx) < max_lines:
        nxt_masked = masked_lines[i]
        window_lines.append(raw_lines[i])
        for ch in nxt_masked:
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
        i += 1
    return "\n".join(window_lines)


def scan_file(
    path: Path,
    repo_root: Path,
    accessor_map: dict[str, str],
    struct_fields: dict[str, set[str]],
    queries: list[Query],
    file_index: dict[str, FileInfo],
    route_classifier: Optional[dict[str, set[str]]] = None,
    collection_struct_map: Optional[dict[str, str]] = None,
    user_scoped_collections: Optional[set[str]] = None,
    global_collections: Optional[set[str]] = None,
    filter_tracer_fields: Optional[dict[str, list[str]]] = None,
) -> None:
    """Scan a single Go file for MongoDB queries and classify each."""
    try:
        raw = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return
    masked = mask_strings_and_comments(raw)
    lines = masked.splitlines()
    raw_lines = raw.splitlines()

    rel = _relative(repo_root, path)
    finfo = file_index.setdefault(rel, FileInfo(path=rel))

    # Pre-compute per-file context flags.
    is_cli_file = CLI_PATH_PARTS[0] in path.parts and CLI_PATH_PARTS[1] in path.parts
    is_testutil = "testutil" in path.parts or path.name == "testutil.go"
    is_test_file = path.name.endswith("_test.go") or is_testutil
    route_classifier = route_classifier or {}
    collection_struct_map = collection_struct_map or {}
    user_scoped_collections = user_scoped_collections or set()
    global_collections = global_collections or set()

    # Per-file alias + filter-variable tracking.
    #   aliases[var_name]      = collection_name           (collection-typed vars)
    #   filter_vars[var_name]  = {fields, def_line, ...}   (bson.M/bson.D/map vars)
    #   pipeline_vars[var_name]= {fields, def_line, ...}   ([]bson.M / mongo.Pipeline)
    #   struct_vars[var_name]  = struct_name               (models.Invitation, etc.)
    aliases: dict[str, str] = {}
    filter_vars: dict[str, dict] = {}
    pipeline_vars: dict[str, dict] = {}
    struct_vars: dict[str, str] = {}

    current_func = "<package-init>"
    n = len(lines)
    masked_full = masked
    raw_full = raw

    # Single pass: walk line-by-line, tracking function context and variable
    # assignments. When a MongoDB operation call is found on the current
    # line, extract its arguments from the full masked/raw text (so multi-
    # line calls are handled) and classify the query.
    #
    # NOTE: function/alias/var-def tracking uses the MASKED line (so braces
    # inside strings don't confuse depth tracking), but dynamic field-addition
    # detection (``filter["tenantId"] = ...``) uses the RAW line because the
    # string key must be visible to the regex.
    for idx in range(n):
        line = lines[idx]
        raw_line = raw_lines[idx]
        line_no = idx + 1
        stripped = line.lstrip()

        # ---- Track current function (and reset per-function state) ----
        if stripped.startswith("func"):
            fm = FUNC_RE.match(stripped)
            if fm:
                current_func = fm.group(1)
                filter_vars.clear()
                pipeline_vars.clear()
                aliases.clear()
                struct_vars.clear()
                continue

        # ---- Track collection-alias assignments ----
        for m in ALIAS_LITERAL_RE.finditer(line):
            aliases[m.group(1)] = m.group(2)
        for m in ALIAS_ACCESSOR_RE.finditer(line):
            var_name = m.group(1)
            accessor = m.group(2)
            end = m.end()
            if end < len(line) and line[end] == ".":
                continue  # chained call, not a bare alias
            if accessor in accessor_map:
                aliases[var_name] = accessor_map[accessor]

        # ---- Track filter-variable definitions ----
        # ``filter := bson.M{...}`` — capture the multi-line literal that
        # follows, starting at the variable name so the ``bson.M`` prefix is
        # preserved (the field-extraction regexes require it).
        for m in FILTER_VAR_DEF_RE.finditer(line):
            var_name = m.group(1)
            window = _collect_brace_window(lines, raw_lines, idx, m.start(), max_lines=30)
            fields = extract_filter_fields_from_text(window)
            filter_vars[var_name] = {
                "fields": set(fields),
                "def_line": line_no,
                "source": "inline-literal",
            }

        # ---- Track filter-variable dynamic field additions ----
        # ``filter["tenantId"] = ...`` — uses the RAW line so the string key
        # is visible (the masked line has the key's characters replaced with
        # spaces).
        for m in FILTER_VAR_SET_RE.finditer(raw_line):
            var_name = m.group(1)
            field_name = m.group(2)
            if var_name in filter_vars:
                filter_vars[var_name]["fields"].add(field_name)
            else:
                # Variable defined elsewhere (function param, loop var, etc.)
                filter_vars[var_name] = {
                    "fields": {field_name},
                    "def_line": line_no,
                    "source": "dynamic-only",
                }

        # ---- Track pipeline-variable definitions (for Aggregate) ----
        for m in PIPELINE_VAR_DEF_RE.finditer(line):
            var_name = m.group(1)
            window = _collect_brace_window(lines, raw_lines, idx, m.start(), max_lines=80)
            fields = _extract_pipeline_match_fields(window)
            pipeline_vars[var_name] = {
                "fields": set(fields),
                "def_line": line_no,
                "source": "inline-literal",
                "window": window,
            }

        # ---- Track struct-literal variable assignments ----
        # ``invitation := models.Invitation{...}`` — records the struct name
        # so InsertOne(ctx, invitation) can be checked for tenantId presence
        # via the struct's bson field tags. Uses the RAW line so that the
        # struct name (which is a Go identifier, not a string) is visible.
        for m in STRUCT_VAR_DEF_RE.finditer(raw_line):
            var_name = m.group(1)
            struct_name = m.group(3)
            # Only track if the struct is known (has bson field tags). This
            # filters out generic-looking assignments like ``x := Foo{}``
            # where Foo isn't a tracked struct.
            if struct_name in struct_fields:
                struct_vars[var_name] = struct_name

        # ---- Find operation calls on this line ----
        line_offset = sum(len(lines[k]) + 1 for k in range(idx))  # +1 for \n
        for op_m in OP_RE.finditer(line):
            operation = op_m.group(1)
            # OP_RE matches ``.Find(`` etc. — op_m.end() is just past the "(".
            open_paren_idx_in_line = op_m.end() - 1
            open_paren_idx_full = line_offset + open_paren_idx_in_line

            # Skip option-builder calls (``options.Find()`` etc.). Uses the
            # RAW prefix so the literal ``options`` token is reliably visible.
            raw_prefix = raw_line[: op_m.start()]
            if OPTIONS_BUILDER_RE.search(raw_prefix):
                continue

            # ---- Resolve the collection ----
            # The prefix search uses the RAW line so that collection literals
            # like ``db.Collection("users")`` (which contain a string) are
            # visible. Depth tracking isn't needed here — we're just looking
            # for the last accessor call or collection literal before ``.Op(``.
            collection: Optional[str] = None
            accessor_used: Optional[str] = None

            lit_m = COLLECTION_LITERAL_RE.search(raw_prefix)
            if lit_m:
                collection = lit_m.group(1)
            else:
                acc_m = re.search(r"([A-Z]\w*)\(\s*\)\s*$", raw_prefix)
                if acc_m:
                    accessor_used = acc_m.group(1)
                    collection = accessor_map.get(accessor_used)
                else:
                    var_m = re.search(r"([A-Za-z_]\w*)\s*$", raw_prefix)
                    if var_m:
                        collection = aliases.get(var_m.group(1))

            # Fallback: look back a couple of lines for a collection literal
            # or accessor call (handles calls split across lines). Uses RAW
            # lines for the same reason as above.
            if collection is None:
                for back in range(idx - 1, max(idx - 4, -1), -1):
                    if back < 0 or back >= n:
                        continue
                    prev_raw = raw_lines[back]
                    lit_m2 = COLLECTION_LITERAL_RE.search(prev_raw)
                    if lit_m2:
                        collection = lit_m2.group(1)
                        break
                    acc_m2 = re.search(r"([A-Z]\w*)\(\s*\)", prev_raw)
                    if acc_m2 and acc_m2.group(1) in accessor_map:
                        collection = accessor_map[acc_m2.group(1)]
                        if accessor_used is None:
                            accessor_used = acc_m2.group(1)
                        break

            if collection is None:
                # Last resort: if the accessor name is in the exempt set,
                # use it as the collection name (so we can still classify).
                if accessor_used and accessor_used in EXEMPT_ACCESSORS:
                    collection = _accessor_to_collection(accessor_used)
                else:
                    collection = "<unknown>"

            # ---- Extract the call arguments ----
            args = extract_call_args(masked_full, raw_full, open_paren_idx_full)

            # Determine which argument holds the filter/document/pipeline.
            filter_text = ""
            filter_source = "unknown"
            filter_fields: list[str] = []
            has_tenant_id = False

            # MongoDB driver convention: first arg is always ctx (or t in
            # tests). The filter/document/pipeline is the second arg.
            if operation == "EstimatedDocumentCount":
                # No filter argument.
                filter_source = "no-filter"
            elif operation == "BulkWrite":
                # BulkWrite(ctx, []mongo.WriteModel{...}) — the models slice
                # is too complex to analyse statically.
                filter_source = "bulk-write-models"
                if len(args) >= 2:
                    filter_text = args[1]
            elif operation == "InsertMany":
                # InsertMany(ctx, []interface{}{...}) — the slice contains
                # the documents to insert.
                if len(args) >= 2:
                    filter_text = args[1]
                    filter_fields = extract_filter_fields_from_text(filter_text)
                    filter_source = "inline-document-slice"
                else:
                    filter_source = "missing-arg"
            elif operation == "InsertOne":
                # InsertOne(ctx, document) — document may be a bson.M literal,
                # an inline struct literal (``models.Foo{...}``), or a
                # variable holding a struct literal (``foo`` assigned from
                # ``models.Foo{...}`` earlier in the function).
                if len(args) >= 2:
                    filter_text = args[1]
                    if "bson.M" in filter_text or "bson.D" in filter_text or "map[string]" in filter_text:
                        filter_fields = extract_filter_fields_from_text(filter_text)
                        filter_source = "inline-document"
                    else:
                        # Try inline struct literal first.
                        struct_name = _extract_struct_name(filter_text)
                        # Then fall back to a struct-typed variable alias.
                        if struct_name is None or struct_name not in struct_fields:
                            var_m = re.match(r"^&?(\w+)\s*$", filter_text.strip())
                            if var_m and var_m.group(1) in struct_vars:
                                struct_name = struct_vars[var_m.group(1)]
                                filter_source = f"struct-var:{var_m.group(1)}:{struct_name}"
                        if struct_name and struct_name in struct_fields:
                            if not filter_source.startswith("struct-var:"):
                                filter_source = f"struct:{struct_name}"
                            bson_fields = struct_fields[struct_name]
                            # Don't pollute filter_fields with every struct
                            # field — just record the ones relevant for
                            # tenant filtering. We expose the full field set
                            # for context, but only treat tenantId presence
                            # as "has_tenant_id" if the struct HAS a
                            # tenantId bson field.
                            filter_fields = sorted(
                                f for f in bson_fields if not f.startswith("_")
                            )
                            if TENANT_ID_FIELDS & bson_fields:
                                has_tenant_id = True
                        else:
                            filter_source = "struct:unknown"
                else:
                    filter_source = "missing-arg"
            elif operation == "UpdateByID":
                # UpdateByID(ctx, id, update) — id is the document _id (unique).
                filter_source = "by-id"
                if len(args) >= 2:
                    filter_text = args[1]
                    # Mark as having a safe unique key.
                    filter_fields = ["_id"]
            elif operation == "Aggregate":
                # Aggregate(ctx, pipeline) — pipeline is a slice of stages.
                if len(args) >= 2:
                    filter_text = args[1]
                    if (
                        filter_text.startswith("bson.M")
                        or filter_text.startswith("bson.D")
                        or filter_text.startswith("bson.A")
                        or filter_text.startswith("[]bson")
                        or filter_text.startswith("mongo.Pipeline")
                    ):
                        # Inline pipeline literal.
                        filter_fields = _extract_pipeline_match_fields(filter_text)
                        filter_source = "inline-pipeline"
                    else:
                        # Variable pipeline — look up in pipeline_vars.
                        var_m = re.match(r"^(\w+)\s*$", filter_text.strip())
                        if var_m and var_m.group(1) in pipeline_vars:
                            info = pipeline_vars[var_m.group(1)]
                            filter_fields = sorted(info["fields"])
                            filter_source = f"variable-pipeline:{var_m.group(1)}"
                        else:
                            # Fall back to the Go filter tracer (go/ssa)
                            # if it produced data for this call site.
                            traced = _lookup_filter_tracer_fields(
                                rel, line_no, filter_tracer_fields or {},
                            )
                            if traced:
                                filter_fields = traced
                                filter_source = (
                                    f"variable-pipeline:tracer:{filter_text.strip()[:40]}"
                                )
                            else:
                                filter_source = "variable-pipeline:unknown"
                else:
                    filter_source = "missing-arg"
            elif operation in FILTER_AT_POS_2:
                # Standard filter-bearing call: <Op>(ctx, filter, ...).
                if len(args) >= 2:
                    filter_text = args[1]
                    if filter_text == "nil":
                        filter_source = "nil"
                        filter_fields = []
                    elif filter_text.startswith("bson.M") or filter_text.startswith("bson.D") or filter_text.startswith("map[string]"):
                        filter_fields = extract_filter_fields_from_text(filter_text)
                        filter_source = "inline"
                    else:
                        # Variable filter — look up in filter_vars.
                        var_m = re.match(r"^(\w+)\s*$", filter_text.strip())
                        if var_m and var_m.group(1) in filter_vars:
                            info = filter_vars[var_m.group(1)]
                            filter_fields = sorted(info["fields"])
                            filter_source = f"variable:{var_m.group(1)}"
                        else:
                            # Fall back to the Go filter tracer (go/ssa)
                            # if it produced data for this call site.
                            traced = _lookup_filter_tracer_fields(
                                rel, line_no, filter_tracer_fields or {},
                            )
                            if traced:
                                filter_fields = traced
                                filter_source = (
                                    f"variable:tracer:{filter_text.strip()[:40]}"
                                )
                            else:
                                filter_source = f"variable:unknown:{filter_text.strip()[:40]}"
                else:
                    filter_source = "missing-arg"
            else:
                # Should not happen — every op is handled above.
                filter_source = "unhandled"

            # ---- Determine has_tenant_id ----
            if filter_fields:
                field_set = set(filter_fields)
                if TENANT_ID_FIELDS & field_set:
                    has_tenant_id = True

            # ---- Classify ----
            is_exempt = _is_exempt_collection(collection, accessor_used)
            safe_key = _has_safe_unique_key(filter_fields, operation)
            has_user_id = "userId" in filter_fields or "user_id" in filter_fields

            # ---- Compute context heuristics (false-positive suppression) ----
            # These are checked in priority order; the first match wins and
            # downgrades the query from a violation to MEDIUM informational.
            # Auth flow handlers are user-scoped (operate on refresh_tokens,
            # verification_tokens, etc.) — not admin handlers.
            is_auth_flow = (
                current_func in route_classifier.get("auth", set())
                or current_func in AUTH_FLOW_FUNCS
            )
            is_admin_handler = (
                current_func in route_classifier.get("admin", set())
                or current_func in ADMIN_SERVICE_FUNCS
            )
            is_public_endpoint = (
                current_func in route_classifier.get("public", set())
                or current_func in PUBLIC_ENDPOINT_FUNCS
            )
            is_background_task = current_func in BACKGROUND_TASK_FUNCS
            # Resolve the underlying struct for this collection.
            struct_name = collection_struct_map.get(collection)
            coll_has_tid: Optional[bool] = None
            if struct_name and struct_name in struct_fields:
                coll_has_tid = bool(
                    TENANT_ID_FIELDS & struct_fields[struct_name]
                )
            # ``collection_is_user_scoped`` is True when the struct has a
            # ``userId`` bson field — for these, a ``userId`` filter is a
            # valid scope (the user's data spans tenants).
            coll_is_user_scoped = collection in user_scoped_collections
            # ``collection_is_global`` is True when the struct does NOT
            # declare a tenantId field — these collections are global by
            # design (e.g. ``webhooks``, ``plans``, ``system_nodes``).
            collection_is_global = (
                collection in global_collections
                or coll_has_tid is False
            )
            # Decide the route scope label (for the report).
            if is_testutil:
                route_scope = "testutil"
            elif is_cli_file:
                route_scope = "cli"
            elif is_background_task:
                route_scope = "background"
            elif is_public_endpoint:
                route_scope = "public"
            elif is_admin_handler:
                route_scope = "admin"
            elif is_auth_flow:
                route_scope = "auth"
            elif current_func in route_classifier.get("tenant", set()):
                route_scope = "tenant"
            else:
                route_scope = "unknown"

            suppression_reason: str = ""

            # ---- Apply false-positive suppressions in priority order ----
            if has_tenant_id:
                risk_level = "OK"
                is_violation = False
                note = "Filter contains tenantId."
            elif is_testutil:
                risk_level = "MEDIUM"
                is_violation = False
                suppression_reason = "test-util"
                note = (
                    "Query is in a test-utility file (internal/testutil/) — "
                    "test helpers reset/clean test databases between test "
                    "runs. Not production code."
                )
            elif is_cli_file:
                risk_level = "MEDIUM"
                is_violation = False
                suppression_reason = "cli-tool"
                note = (
                    "Query is in a CLI tool (cmd/lastsaas/) — CLI tools have "
                    "no HTTP request context and operate on system-wide "
                    "collections by design."
                )
            elif is_background_task:
                risk_level = "MEDIUM"
                is_violation = False
                suppression_reason = "background-task"
                note = (
                    f"Function '{current_func}' is a background system task "
                    "(no request context, no tenantId available). Operates "
                    "on system-wide collections by design."
                )
            elif is_admin_handler:
                risk_level = "MEDIUM"
                is_violation = False
                suppression_reason = "admin-handler"
                note = (
                    f"Function '{current_func}' is an admin handler "
                    "(registered on /api/admin/*). Admin handlers see ALL "
                    "tenants by design — no tenantId filter needed."
                )
            elif is_public_endpoint:
                risk_level = "MEDIUM"
                is_violation = False
                suppression_reason = "public-endpoint"
                note = (
                    f"Function '{current_func}' is a public endpoint (no "
                    "auth) — returns published/global content to everyone."
                )
            elif collection_is_global:
                risk_level = "MEDIUM"
                is_violation = False
                suppression_reason = "global-by-design"
                if struct_name:
                    note = (
                        f"Collection '{collection}' maps to struct "
                        f"'{struct_name}' which does NOT declare a tenantId "
                        f"bson field — this collection is global by design."
                    )
                else:
                    note = (
                        f"Collection '{collection}' is in the global list "
                        f"(no tenantId field) — global by design."
                    )
            elif coll_is_user_scoped and has_user_id:
                risk_level = "OK"
                is_violation = False
                suppression_reason = "user-scoped"
                note = (
                    f"Collection '{collection}' is user-scoped (has userId "
                    f"field) and the filter contains userId — a user's data "
                    f"spans tenants, so userId is a valid scope."
                )
            elif is_auth_flow and (has_user_id or safe_key):
                risk_level = "MEDIUM"
                is_violation = False
                suppression_reason = "auth-flow"
                note = (
                    f"Auth-flow handler '{current_func}' operates on user-"
                    f"scoped collections (the user hasn't selected a tenant "
                    f"yet during auth). Filter on userId/token/tokenHash is "
                    f"a valid scope."
                )
            elif safe_key:
                risk_level = "MEDIUM"
                is_violation = False
                suppression_reason = "safe-unique-key"
                note = (
                    f"Filter contains a globally-unique key "
                    f"({', '.join(f for f in filter_fields if f in SAFE_UNIQUE_KEYS)}) "
                    f"— the query will only ever return one document "
                    f"regardless of tenant."
                )
            elif is_exempt:
                risk_level = "MEDIUM"
                is_violation = False
                suppression_reason = "exempt-collection"
                note = (
                    f"Collection '{collection}' is in the exempt (global) "
                    f"list; tenant filtering is not strictly required, but "
                    f"queries should still be reviewed for appropriate "
                    f"scoping."
                )
            elif operation in ("InsertOne", "InsertMany") and (
                filter_source in ("inline-document", "inline-document-slice")
                or filter_source == "missing-arg"
            ) and coll_has_tid is True:
                # The inserted struct (or slice of structs) declares a
                # ``tenantId`` bson field. The auditor can't statically
                # verify the value is set at runtime, but the struct
                # SUPPORTS tenant scoping — caller is responsible. Common
                # case: a tenant-scoped HTTP handler populates the struct
                # from request context before calling the service method.
                risk_level = "MEDIUM"
                is_violation = False
                suppression_reason = "struct-supports-tenant-id"
                note = (
                    f"{operation} inserts a document (or slice of documents) "
                    f"whose struct '{struct_name}' declares a tenantId bson "
                    f"field. The value cannot be verified statically — caller "
                    f"is responsible for setting it (typically the tenant-"
                    f"scoped HTTP handler reads tenantId from request context "
                    f"and populates the struct before calling this method)."
                )
            elif operation in WRITE_OPS:
                risk_level = "CRITICAL"
                is_violation = True
                if filter_source == "by-id":
                    note = (
                        "UpdateByID uses the document _id (globally unique) — "
                        "tenant filtering is implicit. Likely safe."
                    )
                elif filter_source.startswith("struct:"):
                    struct_name_src = filter_source.split(":", 1)[1]
                    if struct_name_src == "unknown":
                        note = (
                            "InsertOne with an unrecognised struct value; "
                            "could not statically verify tenantId presence. "
                            "Manual review required."
                        )
                    else:
                        note = (
                            f"InsertOne with a {struct_name_src} struct "
                            f"value; tenantId presence inferred from the "
                            f"struct definition — verify the value is "
                            f"actually set at runtime."
                        )
                elif filter_source.startswith("struct-var:"):
                    parts = filter_source.split(":")
                    var_name = parts[1] if len(parts) > 1 else "?"
                    struct_name_src = parts[2] if len(parts) > 2 else "?"
                    note = (
                        f"InsertOne with {var_name} (a {struct_name_src} "
                        f"struct); the struct definition does NOT declare a "
                        f"tenantId bson field. CRITICAL: inserted document "
                        f"will be orphaned across tenants."
                    )
                elif operation in ("InsertOne", "InsertMany") and (
                    filter_source in ("inline-document", "inline-document-slice")
                    or filter_source == "missing-arg"
                ):
                    note = (
                        f"{operation} inserts a document with no tenantId "
                        f"field. CRITICAL: the inserted document will be "
                        f"orphaned — readable/modifiable by any tenant that "
                        f"queries without a tenantId filter, or invisible to "
                        f"queries that DO filter by tenantId."
                    )
                elif operation == "BulkWrite":
                    note = (
                        "BulkWrite with a slice of WriteModel operations — "
                        "individual model filters cannot be analysed "
                        "statically. CRITICAL: manual review required to "
                        "confirm every UpdateOne/DeleteOne/ReplaceOne model "
                        "in the slice includes a tenantId filter."
                    )
                elif filter_source == "nil":
                    note = (
                        f"{operation} with nil filter — affects ALL "
                        f"documents in the collection. CRITICAL: this can "
                        f"modify/delete data across all tenants."
                    )
                elif not filter_fields and operation in (
                    "UpdateOne", "UpdateMany", "DeleteOne", "DeleteMany",
                    "FindOneAndUpdate", "FindOneAndDelete", "FindOneAndReplace",
                    "ReplaceOne",
                ):
                    note = (
                        f"{operation} with an empty filter — affects ALL "
                        f"documents. CRITICAL: cross-tenant data corruption "
                        f"risk."
                    )
                else:
                    note = (
                        f"{operation} on a tenant-scoped collection without "
                        f"tenantId in the filter. CRITICAL: this can "
                        f"modify/delete data belonging to other tenants."
                    )
            else:
                # Read operation.
                risk_level = "HIGH"
                is_violation = True
                if filter_source == "no-filter":
                    note = (
                        f"{operation} returns aggregate info about ALL "
                        f"documents in the collection (no filter is taken). "
                        f"HIGH: leaks the total document count across all "
                        f"tenants."
                    )
                elif filter_source == "nil":
                    note = (
                        "Read operation with nil filter — returns ALL "
                        "documents in the collection. HIGH: cross-tenant "
                        "data leakage risk."
                    )
                elif not filter_fields:
                    note = (
                        "Read operation with an empty filter — returns ALL "
                        "documents. HIGH: cross-tenant data leakage risk."
                    )
                elif filter_source.startswith("variable:unknown"):
                    note = (
                        "Read operation whose filter is a variable that "
                        "could not be traced to a definition. Manual review "
                        "required to confirm tenantId is set."
                    )
                elif filter_source.startswith("variable-pipeline:unknown"):
                    note = (
                        "Aggregate pipeline variable could not be traced to "
                        "a definition; cannot verify whether a $match stage "
                        "filters on tenantId. Manual review required."
                    )
                else:
                    note = (
                        "Read operation on a tenant-scoped collection "
                        "without tenantId in the filter. HIGH: cross-tenant "
                        "data leakage risk."
                    )

            # ---- Build a snippet from the RAW source (not masked) ----
            snippet = _build_snippet(raw_lines, line_no, filter_text)

            q = Query(
                file=rel,
                line=line_no,
                function=current_func,
                collection=collection,
                operation=operation,
                filter_fields=filter_fields,
                has_tenant_id=has_tenant_id,
                filter_source=filter_source,
                risk_level=risk_level,
                is_violation=is_violation,
                is_exempt_collection=is_exempt,
                safe_key_filter=safe_key or filter_source == "by-id",
                filter_snippet=snippet,
                note=note,
                route_scope=route_scope,
                is_admin_handler=is_admin_handler,
                is_background_task=is_background_task,
                is_public_endpoint=is_public_endpoint,
                is_auth_flow=is_auth_flow,
                is_cli_tool=is_cli_file,
                collection_has_tenant_id=coll_has_tid,
                collection_is_user_scoped=coll_is_user_scoped,
                has_user_id_filter=has_user_id,
                suppression_reason=suppression_reason,
            )
            queries.append(q)
            finfo.total_queries += 1
            finfo.by_risk[risk_level] += 1
            if is_violation:
                finfo.violations += 1


def _extract_pipeline_match_fields(text: str) -> list[str]:
    """Extract field names from ``$match`` stages in an aggregate pipeline.

    A ``$match`` stage looks like ``{"$match": bson.M{...}}`` or
    ``bson.D{{Key: "$match", Value: bson.D{...}}}``. We locate the inner
    filter literal and delegate to :func:`extract_filter_fields_from_text`,
    passing enough surrounding context (the ``bson.M`` / ``bson.D`` prefix)
    that the BSON regexes can match.
    """
    fields: list[str] = []
    match_re = re.compile(
        r'"\$match"\s*:\s*(bson\.M|bson\.D)\s*\{', re.IGNORECASE
    )
    for m in match_re.finditer(text):
        # Find the closing brace of the ``bson.M{...}`` block.
        brace_idx = m.end() - 1
        end = find_block_end(text, brace_idx, "{", "}")
        if end == -1:
            continue
        # Include the ``bson.M`` prefix in the slice so that
        # ``BSON_M_RE`` / ``BSON_D_RE`` (which require the prefix) match.
        bson_prefix_start = m.start(1)
        inner = text[bson_prefix_start : end + 1]
        fields.extend(extract_filter_fields_from_text(inner))
    # Dedupe.
    seen: set[str] = set()
    out: list[str] = []
    for f in fields:
        if f and not f.startswith("$") and f not in seen:
            seen.add(f)
            out.append(f)
    return out


def _extract_struct_name(text: str) -> Optional[str]:
    """Best-effort: extract the struct name from an argument like
    ``models.User{...}`` or ``&models.User{...}`` or ``User{...}``.
    """
    m = re.search(r"&?([\w\.]+)\s*\{", text)
    if m:
        # Take the last component after any dots.
        name = m.group(1).split(".")[-1]
        return name
    return None


def _is_exempt_collection(collection: str, accessor: Optional[str]) -> bool:
    """Return True if the collection is in the exempt (global) list."""
    if collection in EXEMPT_COLLECTIONS:
        return True
    if accessor and accessor in EXEMPT_ACCESSORS:
        return True
    return False


def _accessor_to_collection(accessor: str) -> str:
    """Convert a PascalCase accessor name (e.g. ``Users``) to its snake_case
    collection name (e.g. ``users``). Best-effort.
    """
    # Handle common acronyms first.
    out: list[str] = []
    cur = ""
    for ch in accessor:
        if ch.isupper():
            if cur:
                out.append(cur)
                cur = ch.lower()
            else:
                cur = ch.lower()
        else:
            cur += ch
    if cur:
        out.append(cur)
    return "_".join(out)


def _has_safe_unique_key(filter_fields: list[str], operation: str) -> bool:
    """Return True if the filter contains a globally-unique key."""
    if operation == "UpdateByID":
        return True
    for f in filter_fields:
        if f in SAFE_UNIQUE_KEYS:
            return True
    return False


def _build_snippet(raw_lines: list[str], line_no: int, filter_text: str) -> str:
    """Build a compact human-readable snippet for the report.

    Uses the raw (unmasked) source lines so the snippet shows the actual code
    the developer wrote (with strings/comments intact).
    """
    if 1 <= line_no <= len(raw_lines):
        first = raw_lines[line_no - 1].strip()
    else:
        first = ""
    # Include up to 3 following lines if the call clearly continues.
    snippet_lines = [first]
    depth_paren = first.count("(") - first.count(")")
    depth_brace = first.count("{") - first.count("}")
    i = line_no + 1
    while (depth_paren > 0 or depth_brace > 0) and i <= len(raw_lines) and (i - line_no) < 5:
        nxt = raw_lines[i - 1].rstrip()
        snippet_lines.append(nxt)
        depth_paren += nxt.count("(") - nxt.count(")")
        depth_brace += nxt.count("{") - nxt.count("}")
        i += 1
    snippet = "\n".join(snippet_lines).strip()
    if len(snippet) > 400:
        snippet = snippet[:397] + "..."
    return snippet


# --------------------------------------------------------------------------- #
# Output rendering
# --------------------------------------------------------------------------- #


def build_summary(
    queries: list[Query],
    file_index: dict[str, FileInfo],
    accessor_map: dict[str, str],
    repo_root: Path,
    collection_struct_map: Optional[dict[str, str]] = None,
    user_scoped_collections: Optional[set[str]] = None,
    global_collections: Optional[set[str]] = None,
    route_classifier: Optional[dict[str, set[str]]] = None,
) -> dict:
    """Build the JSON-serialisable summary object."""
    total = len(queries)
    with_tenant = sum(1 for q in queries if q.has_tenant_id)
    without_tenant = total - with_tenant
    violations = [q for q in queries if q.is_violation]
    critical = [q for q in violations if q.risk_level == "CRITICAL"]
    high = [q for q in violations if q.risk_level == "HIGH"]
    medium = [q for q in queries if q.risk_level == "MEDIUM"]
    ok = [q for q in queries if q.risk_level == "OK"]
    safe_key_violations = [q for q in violations if q.safe_key_filter]
    real_violations = [q for q in violations if not q.safe_key_filter]

    # Suppression breakdown — how many queries were downgraded from a
    # potential violation to MEDIUM informational by each heuristic.
    suppression_counts: Counter = Counter()
    for q in queries:
        if q.suppression_reason:
            suppression_counts[q.suppression_reason] += 1
    route_scope_counts: Counter = Counter(q.route_scope for q in queries)

    by_collection: Counter = Counter()
    by_operation: Counter = Counter()
    violations_by_collection: Counter = Counter()
    violations_by_file: Counter = Counter()
    for q in queries:
        by_collection[q.collection] += 1
        by_operation[q.operation] += 1
        if q.is_violation:
            violations_by_collection[q.collection] += 1
            violations_by_file[q.file] += 1

    # Top files by violation count.
    top_files = [
        {"file": f, "violations": v, "total": file_index[f].total_queries}
        for f, v in violations_by_file.most_common(20)
    ]

    return {
        "repo_root": str(repo_root),
        "total_queries": total,
        "queries_with_tenant_id": with_tenant,
        "queries_without_tenant_id": without_tenant,
        "violations": len(violations),
        "critical_violations": len(critical),
        "high_violations": len(high),
        "medium_global_collection_queries": len(medium),
        "ok_queries": len(ok),
        "safe_key_violations": len(safe_key_violations),
        "real_violations_needing_review": len(real_violations),
        "pct_with_tenant_id": (
            round(100.0 * with_tenant / total, 2) if total else 0.0
        ),
        "queries_by_collection": [
            {"collection": c, "queries": n}
            for c, n in by_collection.most_common()
        ],
        "queries_by_operation": [
            {"operation": op, "count": n}
            for op, n in by_operation.most_common()
        ],
        "violations_by_collection": [
            {"collection": c, "violations": n}
            for c, n in violations_by_collection.most_common()
        ],
        "top_files_by_violations": top_files,
        "exempt_collections": sorted(EXEMPT_COLLECTIONS),
        "tenant_id_fields": sorted(TENANT_ID_FIELDS),
        "safe_unique_keys": sorted(SAFE_UNIQUE_KEYS),
        "accessor_map_size": len(accessor_map),
        "suppression_breakdown": [
            {"reason": r, "count": n}
            for r, n in suppression_counts.most_common()
        ],
        "route_scope_breakdown": [
            {"scope": s, "count": n}
            for s, n in route_scope_counts.most_common()
        ],
        "user_scoped_collections": sorted(user_scoped_collections or set()),
        "global_collections": sorted(global_collections or set()),
        "collection_struct_map": collection_struct_map or {},
        "route_classifier_sizes": {
            "admin": len((route_classifier or {}).get("admin", set())),
            "tenant": len((route_classifier or {}).get("tenant", set())),
            "auth": len((route_classifier or {}).get("auth", set())),
            "public": len((route_classifier or {}).get("public", set())),
        },
    }


def render_markdown(summary: dict, queries: list[Query]) -> str:
    """Render the summary + queries as a Markdown report."""
    lines: list[str] = []
    lines.append("# Tenant Isolation Audit\n")
    lines.append(
        "MongoDB query audit for **cross-tenant data leakage** risks. The "
        "auditor flags queries on tenant-scoped collections that lack a "
        "`tenantId` filter — but first applies a series of context-aware "
        "heuristics to suppress known false positives (global-by-design "
        "collections, admin handlers, background tasks, public endpoints, "
        "user-scoped filters, globally-unique keys, and CLI tools).\n"
    )
    lines.append(f"Repo: `{summary['repo_root']}`\n")

    # ---- Headline numbers ----
    lines.append("## Summary\n")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append(f"| Total MongoDB queries | **{summary['total_queries']}** |")
    lines.append(
        f"| Queries with `tenantId` filter | **{summary['queries_with_tenant_id']}** "
        f"({summary['pct_with_tenant_id']}%) |"
    )
    lines.append(
        f"| Queries without `tenantId` filter | **{summary['queries_without_tenant_id']}** |"
    )
    lines.append(f"| OK (suppressed: user-scoped, has tenantId, etc.) | {summary['ok_queries']} |")
    lines.append(f"| MEDIUM (suppressed: global/admin/CLI/background/public) | {summary['medium_global_collection_queries']} |")
    lines.append(f"| **Total violations** | **{summary['violations']}** |")
    lines.append(f"| → CRITICAL (write ops, no tenantId) | **{summary['critical_violations']}** |")
    lines.append(f"| → HIGH (read ops, no tenantId) | **{summary['high_violations']}** |")
    lines.append(
        f"| **Real violations needing review** | **{summary['real_violations_needing_review']}** |"
    )
    lines.append("")

    # ---- Suppression breakdown ----
    if summary.get("suppression_breakdown"):
        lines.append("### False-positive suppressions applied\n")
        lines.append("The following heuristics downgraded potential violations to MEDIUM informational notes:\n")
        lines.append("| Suppression reason | Queries affected |")
        lines.append("|--------------------|-----------------|")
        reason_labels = {
            "test-util": "Test utility (internal/testutil/) — not production code",
            "cli-tool": "CLI tool (cmd/lastsaas/) — no request context",
            "background-task": "Background system task (no request context)",
            "admin-handler": "Admin handler (/api/admin/*) — sees all tenants by design",
            "public-endpoint": "Public endpoint (no auth) — published content",
            "global-by-design": "Collection's struct has no tenantId field — global by design",
            "user-scoped": "User-scoped collection with userId filter — valid scope",
            "auth-flow": "Auth-flow handler — user hasn't selected a tenant yet",
            "safe-unique-key": "Filter uses a globally-unique key — single-doc query",
            "struct-supports-tenant-id": "Inserted struct declares tenantId — caller responsibility",
            "exempt-collection": "Collection in exempt list (legacy)",
        }
        for r in summary["suppression_breakdown"]:
            label = reason_labels.get(r["reason"], r["reason"])
            lines.append(f"| {label} | {r['count']} |")
        lines.append("")

    # ---- Route scope breakdown ----
    if summary.get("route_scope_breakdown"):
        lines.append("### Route scope breakdown\n")
        lines.append("| Scope | Queries |")
        lines.append("|-------|---------|")
        for s in summary["route_scope_breakdown"]:
            lines.append(f"| `{s['scope']}` | {s['count']} |")
        lines.append("")

    # ---- Risk-level legend ----
    lines.append("### Risk levels\n")
    lines.append(
        "- **CRITICAL** — write operation (`InsertOne`, `UpdateOne`, "
        "`DeleteOne`, `FindOneAndUpdate`, ...) on a tenant-scoped collection "
        "without a `tenantId` filter. Can modify or delete data belonging to "
        "other tenants.\n"
        "- **HIGH** — read operation (`Find`, `FindOne`, `Aggregate`, "
        "`CountDocuments`) on a tenant-scoped collection without a "
        "`tenantId` filter. Can leak data across tenants.\n"
        "- **MEDIUM** — query that was *suppressed* by a false-positive "
        "heuristic (global-by-design collection, admin handler, background "
        "task, public endpoint, user-scoped filter, globally-unique key, "
        "or CLI tool). Not a strict violation but listed for review.\n"
        "- **OK** — query has a `tenantId` filter, or is on a user-scoped "
        "collection filtered by `userId` (a valid scope since a user's "
        "data spans tenants).\n"
    )
    lines.append(
        "The `safe_key_filter` flag marks queries whose filter contains a "
        "globally-unique key (e.g. `_id`, `tokenHash`, `slug`, `webhookId`). "
        "Such queries are downgraded to MEDIUM because the unique key "
        "already constrains the query to a single document regardless of "
        "tenant.\n"
    )

    # ---- Top files ----
    if summary["top_files_by_violations"]:
        lines.append("## Top Files by Violations\n")
        lines.append("| File | Violations | Total queries |")
        lines.append("|------|------------|---------------|")
        for f in summary["top_files_by_violations"]:
            lines.append(f"| `{f['file']}` | {f['violations']} | {f['total']} |")
        lines.append("")

    # ---- Violations by collection ----
    if summary["violations_by_collection"]:
        lines.append("## Violations by Collection\n")
        lines.append("| Collection | Violations |")
        lines.append("|------------|------------|")
        for c in summary["violations_by_collection"]:
            lines.append(f"| `{c['collection']}` | {c['violations']} |")
        lines.append("")

    # ---- CRITICAL violations (real, no safe key) ----
    crit_real = [
        q for q in queries
        if q.risk_level == "CRITICAL" and not q.safe_key_filter
    ]
    lines.append(
        f"## CRITICAL Violations — Write Ops without tenantId "
        f"({len(crit_real)} real)\n"
    )
    if crit_real:
        lines.append(_render_violation_table(crit_real))
    else:
        lines.append("_None — all write operations include a `tenantId` filter or were suppressed by a context heuristic._\n")

    # ---- HIGH violations (real, no safe key) ----
    high_real = [
        q for q in queries
        if q.risk_level == "HIGH" and not q.safe_key_filter
    ]
    lines.append(
        f"## HIGH Violations — Read Ops without tenantId "
        f"({len(high_real)} real)\n"
    )
    if high_real:
        lines.append(_render_violation_table(high_real))
    else:
        lines.append("_None — all read operations include a `tenantId` filter or were suppressed by a context heuristic._\n")

    # ---- Safe-key queries (now downgraded to MEDIUM) ----
    safe_key_qs = [q for q in queries if q.safe_key_filter and not q.is_violation]
    lines.append(
        f"## Safe-Key Queries — Globally-Unique Filter ({len(safe_key_qs)})\n"
    )
    lines.append(
        "These queries lack a `tenantId` filter but constrain on a "
        "globally-unique key (`_id`, `tokenHash`, `slug`, `webhookId`, "
        "etc.). The unique key already constrains the query to a single "
        "document regardless of tenant — downgraded to MEDIUM.\n"
    )
    if safe_key_qs:
        lines.append(_render_violation_table(safe_key_qs[:50]))
        if len(safe_key_qs) > 50:
            lines.append(f"\n_…and {len(safe_key_qs) - 50} more (see JSON)._\n")
    else:
        lines.append("_None._\n")

    # ---- MEDIUM — suppressed queries ----
    medium = [q for q in queries if q.risk_level == "MEDIUM"]
    lines.append(
        f"## MEDIUM — Suppressed Queries ({len(medium)})\n"
    )
    if medium:
        lines.append(_render_violation_table(medium[:50]))
        if len(medium) > 50:
            lines.append(f"\n_…and {len(medium) - 50} more (see JSON and All Queries by File below)._\n")
    else:
        lines.append("_None._\n")

    # ---- All queries grouped by file ----
    lines.append("## All Queries by File\n")
    by_file: dict[str, list[Query]] = defaultdict(list)
    for q in queries:
        by_file[q.file].append(q)
    for file in sorted(by_file):
        lines.append(f"### `{file}`\n")
        lines.append(_render_violation_table(by_file[file]))
        lines.append("")

    lines.append("---")
    lines.append("_Generated by `graphify_tenant_audit.py`._")
    return "\n".join(lines)


def _render_violation_table(qs: list[Query]) -> str:
    """Render a list of queries as a markdown table."""
    out: list[str] = []
    out.append(
        "| Line | Function | Op | Collection | Filter | Scope | Risk | "
        "Suppression | Note |"
    )
    out.append(
        "|------|----------|----|------------|--------|-------|------|"
        "-------------|------|"
    )
    for q in sorted(qs, key=lambda q: (q.file, q.line)):
        fields = ", ".join(f"`{f}`" for f in q.filter_fields) if q.filter_fields else "—"
        note = q.note.replace("|", "\\|")
        if len(note) > 90:
            note = note[:87] + "..."
        supp = q.suppression_reason or ""
        out.append(
            f"| {q.line} | `{q.function}` | `{q.operation}` | "
            f"`{q.collection}` | {fields} | `{q.route_scope}` | "
            f"{q.risk_level} | {supp} | {note} |"
        )
    out.append("")
    return "\n".join(out)


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #


PUBLIC_DIR = Path("/home/z/my-project/public")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="graphify_tenant_audit.py",
        description=(
            "Tenant-isolation security auditor: scan Go source for MongoDB "
            "queries missing a tenantId filter."
        ),
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

    print(f"building accessor map from {repo_root}...", file=sys.stderr)
    accessor_map = build_accessor_map(repo_root)
    print(f"  found {len(accessor_map)} collection accessors", file=sys.stderr)

    print("collecting struct field definitions...", file=sys.stderr)
    struct_fields = collect_struct_fields(repo_root)
    print(f"  found {len(struct_fields)} struct definitions", file=sys.stderr)

    print("building collection→struct map...", file=sys.stderr)
    collection_struct_map = build_collection_struct_map(accessor_map, struct_fields)
    print(f"  resolved {len(collection_struct_map)} collections to structs", file=sys.stderr)

    print("building user-scoped + global collection lists...", file=sys.stderr)
    user_scoped_collections = build_user_scoped_collections(
        collection_struct_map, struct_fields
    )
    global_collections = build_global_collections(
        collection_struct_map, struct_fields
    )
    print(
        f"  {len(user_scoped_collections)} user-scoped collections, "
        f"{len(global_collections)} global collections",
        file=sys.stderr,
    )

    print("parsing main.go for route classification...", file=sys.stderr)
    route_classifier = build_route_classifier(repo_root)
    print(
        f"  admin={len(route_classifier['admin'])}, "
        f"tenant={len(route_classifier['tenant'])}, "
        f"auth={len(route_classifier['auth'])}, "
        f"public={len(route_classifier['public'])} handlers",
        file=sys.stderr,
    )

    # Run the Go filter tracer (go/ssa-based, sees dynamic filter["x"] = y
    # patterns the regex parser misses). Falls back gracefully to an
    # empty dict if the Go toolchain is unavailable.
    filter_tracer_fields = load_go_filter_tracer(repo_root)

    queries: list[Query] = []
    file_index: dict[str, FileInfo] = {}

    scanned = 0
    for path in sorted(repo_root.rglob("*.go")):
        if not args.include_tests and path.name.endswith("_test.go"):
            continue
        if "graphify-out" in path.parts:
            continue
        if "vendor" in path.parts:
            continue
        scan_file(
            path=path,
            repo_root=repo_root,
            accessor_map=accessor_map,
            struct_fields=struct_fields,
            queries=queries,
            file_index=file_index,
            route_classifier=route_classifier,
            collection_struct_map=collection_struct_map,
            user_scoped_collections=user_scoped_collections,
            global_collections=global_collections,
            filter_tracer_fields=filter_tracer_fields,
        )
        scanned += 1
    print(f"scanned {scanned} .go files", file=sys.stderr)

    summary = build_summary(
        queries,
        file_index,
        accessor_map,
        repo_root,
        collection_struct_map=collection_struct_map,
        user_scoped_collections=user_scoped_collections,
        global_collections=global_collections,
        route_classifier=route_classifier,
    )
    payload = {
        "summary": summary,
        "queries": [q.to_dict() for q in queries],
        "accessor_map": accessor_map,
    }

    json_text = json.dumps(payload, indent=2, default=str)

    # ---- JSON output ----
    if args.json is not None:
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

    # ---- Best-effort write to public/ ----
    try:
        PUBLIC_DIR.mkdir(parents=True, exist_ok=True)
        (PUBLIC_DIR / "tenant-audit.json").write_text(
            json_text + "\n", encoding="utf-8"
        )
        (PUBLIC_DIR / "TENANT_AUDIT.md").write_text(
            md_text + "\n", encoding="utf-8"
        )
        print(
            f"wrote public/tenant-audit.json and public/TENANT_AUDIT.md "
            f"({summary['violations']} violations, "
            f"{summary['real_violations_needing_review']} real)",
            file=sys.stderr,
        )
    except OSError as e:
        print(f"warning: could not write to public/: {e}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
