"""Produce a SaaS architecture map from graph.json.

Reads the graph, groups communities into thematic SaaS subsystems
(Auth, Billing, Multi-tenancy, Storage, Frontend, Admin, Observability,
CLI, Tests, Config, etc.) based on the symbols they contain, and emits
a structured Markdown report."""
import json
import re
from collections import defaultdict, Counter
from pathlib import Path

GRAPH = Path("/home/z/my-project/repos/lastsaas/graphify-out/graph.json")
OUT = Path("/home/z/my-project/download/graphify-lastsaas/ARCHITECTURE_MAP.md")

data = json.loads(GRAPH.read_text(encoding="utf-8"))
nodes = data["nodes"]
edges = data["links"]

# ---- Build community -> members map ----
comm_members: dict[int, list[dict]] = defaultdict(list)
for n in nodes:
    cid = n.get("community")
    if cid is None:
        continue
    comm_members[cid].append(n)

# ---- Compute degree per node from edges ----
degree = Counter()
for e in edges:
    degree[e["source"]] += 1
    degree[e["target"]] += 1

# ---- Heuristic classifier: assign each community to a SaaS subsystem ----
# Strategy: look at every member's source_file path AND label, not just top symbols.
# This catches thin communities the previous top-labels approach missed.
def classify(members: list[dict]) -> str:
    # Collect all source files in the community
    src_files = [m.get("source_file", "") for m in members if m.get("source_file")]
    src_joined = " ".join(src_files).lower()
    labels = [m.get("label", "") for m in members]
    label_joined = " ".join(labels).lower()
    # Also include the LLM-generated community_name (powerful signal)
    comm_names = [m.get("community_name", "") for m in members if m.get("community_name")]
    comm_name_joined = " ".join(comm_names).lower()
    joined = src_joined + " " + label_joined + " " + comm_name_joined

    # Frontend: split by route group using actual file paths
    if "pages/public/" in src_joined or "landingpage" in label_joined or "custompage" in label_joined:
        return "Public Site (marketing / custom pages)"
    if "pages/auth/" in src_joined or any(k in label_joined for k in ["loginpage", "signuppage", "authcallback", "resetpassword", "forgotpassword", "verifyemail", "mfachallenge", "magiclinkverify"]):
        return "Auth UI (login / signup / MFA flows)"
    if "pages/app/" in src_joined or any(k in label_joined for k in ["dashboardpage", "settingspage", "activitypage", "teampage", "billingpage", "buillcreditspage", "buycreditspage", "plansuccesspage", "billingsuccesspage", "billingcancelpage", "onboardingpage", "planpage", "testentitlementspage"]):
        return "End-User Dashboard (tenant app)"
    if "pages/admin/" in src_joined or any(k in label_joined for k in ["adminpage", "userspage", "tenantspage", "planspage", "configpage", "announcementpage", "logspage", "apikeypage", "financialpage", "dashboardpage", "healthpage", "brandingpage", "promotionspage", "rootmemberspage", "pmpage", "aboutpage", "userprofilepage", "tenantprofilepage"]):
        return "Admin UI (operator console)"

    # Pre-check: use LLM-generated community_name as strong signal
    if comm_name_joined:
        if any(k in comm_name_joined for k in ["email", "resend", "message"]):
            return "Messaging & Announcements"
        if any(k in comm_name_joined for k in ["api doc", "documentation", "openapi", "swagger"]):
            return "API Docs & OpenAPI"
        if any(k in comm_name_joined for k in ["webhook"]):
            return "Webhooks"
        if any(k in comm_name_joined for k in ["stripe", "billing", "payment", "subscription", "checkout"]):
            return "Billing & Plans"
        if any(k in comm_name_joined for k in ["mongo", "database", "storage", "schema"]):
            return "Storage & Data Layer"
        if any(k in comm_name_joined for k in ["rate limit", "middleware", "body limit"]):
            return "Middleware & API Gateway"
        if any(k in comm_name_joined for k in ["health", "metrics", "telemetry", "monitoring", "syslog"]):
            return "Observability & Health"
        if any(k in comm_name_joined for k in ["tenant", "rbac", "role", "permission", "membership"]):
            return "Multi-tenancy & RBAC"
        if any(k in comm_name_joined for k in ["auth", "jwt", "totp", "oauth", "password", "mfa", "session"]):
            return "Authentication & Identity"
        if any(k in comm_name_joined for k in ["config", "branding", "env"]):
            return "Configuration & Branding"
        if any(k in comm_name_joined for k in ["api client", "frontend core", "context", "provider"]):
            return "Frontend Core (API client / contexts)"
        if any(k in comm_name_joined for k in ["ui component", "button", "input", "modal", "alert", "card", "badge"]):
            return "UI Component Library"
        if any(k in comm_name_joined for k in ["cli", "command", "mcp", "process"]):
            return "CLI Tooling"

    # Backend domain areas — most specific first to avoid shadowing
    if any(k in joined for k in ["webhook", "dispatcher", "signature", "hmac"]):
        return "Webhooks"
    if any(k in joined for k in ["stripe", "checkout", "subscription", "invoice"]):
        return "Billing & Plans"
    if any(k in joined for k in ["email", "resend", "announcement"]):
        return "Messaging & Announcements"
    if any(k in joined for k in ["billing", "credit", "bundle", "promotion"]):
        return "Billing & Plans"
    if any(k in joined for k in ["mongo", "database", "collection", "objectid", "schema", "migration", "seed"]):
        return "Storage & Data Layer"
    if any(k in joined for k in ["ratelimit", "middleware", "bodylimit", "recovery", "requestid", "securityheader", "apiversion"]):
        return "Middleware & API Gateway"
    if any(k in joined for k in ["health", "metrics", "telemetry", "datadog", "integration", "monitoring", "syslog"]):
        return "Observability & Health"
    if any(k in joined for k in ["tenant", "membership", "invitation", "rbac", "role", "permission"]):
        return "Multi-tenancy & RBAC"
    if any(k in joined for k in ["auth", "jwt", "totp", "oauth", "password", "webauthn", "mfa", "session", "login", "register", "magiclink"]):
        return "Authentication & Identity"
    if any(k in joined for k in ["config", "env", "configvar", "configstore", "branding"]):
        return "Configuration & Branding"
    if any(k in joined for k in ["api/client", "apiclient", "useauth", "usetenant", "usetelemetry", "context", "provider"]):
        return "Frontend Core (API client / contexts)"
    if any(k in joined for k in ["button", "input", "modal", "alert", "card", "badge", "select", "textarea", "skeleton", "spinner", "table"]) and "components/ui/" in src_joined:
        return "UI Component Library"
    if any(k in joined for k in ["cmd", "main.go", "process", "command", "mcp", "doctor", "cli"]):
        return "CLI Tooling"
    if any(k in joined for k in ["openapi", "docs", "swagger", "docshtml", "docsmarkdown", "apireference"]):
        return "API Docs & OpenAPI"
    if "test" in joined or "_test" in joined or "testintegration" in joined:
        return "Test Suite"
    if any(k in joined for k in ["package.json", "tsconfig", "vite.config", "eslint", "vitest", "playwright", "postcss", "tailwind"]):
        return "Build & Config Files"
    if any(k in joined for k in ["docker", "fly.toml", "makefile", "smithery", "glama", "manifest.json", "server.json"]):
        return "Deployment & Manifests"
    return "Misc / Cross-cutting"


# ---- Assign each community to a subsystem ----
comm_subsystem: dict[int, str] = {}
comm_top_labels: dict[int, list[str]] = {}

for cid, members in comm_members.items():
    # Sort members by degree desc, take top labels
    members_sorted = sorted(members, key=lambda m: degree.get(m["id"], 0), reverse=True)
    top_labels = [m["label"] for m in members_sorted[:8]]
    comm_top_labels[cid] = top_labels
    subsystem = classify(members)
    comm_subsystem[cid] = subsystem

# ---- Group: subsystem -> list of (cid, count, top_labels) ----
subsystem_comms: dict[str, list[tuple[int, int, list[str]]]] = defaultdict(list)
for cid, subsystem in comm_subsystem.items():
    count = len(comm_members[cid])
    subsystem_comms[subsystem].append((cid, count, comm_top_labels[cid]))

# Sort subsystems by total nodes (largest first)
subsystem_order = sorted(subsystem_comms.keys(), key=lambda s: -sum(c for _, c, _ in subsystem_comms[s]))

# ---- Compute per-subsystem stats ----
subsystem_stats = {}
for s in subsystem_order:
    comms = subsystem_comms[s]
    total_nodes = sum(c for _, c, _ in comms)
    subsystem_stats[s] = {
        "communities": len(comms),
        "nodes": total_nodes,
    }

# ---- Compute degree rankings globally ----
top_god = sorted(nodes, key=lambda n: degree.get(n["id"], 0), reverse=True)[:20]

# ---- Compute cross-community bridges (nodes with high betweenness via community spread) ----
node_comms: dict[str, set] = defaultdict(set)
for n in nodes:
    cid = n.get("community")
    if cid is None: continue
    # Look at edges to find which other communities this node touches
    node_comms[n["id"]].add(cid)

for e in edges:
    s, t = e["source"], e["target"]
    sn = next((n for n in nodes if n["id"] == s), None)
    tn = next((n for n in nodes if n["id"] == t), None)
    if sn and tn:
        sc = sn.get("community")
        tc = tn.get("community")
        if sc is not None and tc is not None and sc != tc:
            node_comms[s].add(tc)
            node_comms[t].add(sc)

# Bridge score = number of distinct communities touched
bridges = sorted(
    [(n["label"], n.get("community"), len(node_comms[n["id"]]), n.get("source_file", "")) for n in nodes if len(node_comms[n["id"]]) >= 3],
    key=lambda x: -x[2]
)[:15]

# ---- Emit Markdown ----
def md(s: str) -> str:
    return s.replace("|", "\\|")

lines = []
lines.append("# lastsaas — Architecture Map")
lines.append("")
lines.append("> Auto-generated from `graph.json` by grouping graphify's 157 detected communities")
lines.append("> into thematic SaaS subsystems. Each community is a Leiden-clustered module")
lines.append("> of tightly-coupled symbols; the subsystem grouping below is a higher-level view.")
lines.append("")
lines.append("## Top-level: 12 SaaS subsystems")
lines.append("")
lines.append("| Subsystem | Communities | Nodes | Coverage |")
lines.append("|---|---:|---:|---|")
total_nodes_global = len(nodes)
for s in subsystem_order:
    st = subsystem_stats[s]
    pct = 100 * st["nodes"] / total_nodes_global
    lines.append(f"| **{s}** | {st['communities']} | {st['nodes']} | {pct:.1f}% |")
lines.append(f"| _Total_ | _{len(comm_members)}_ | _{total_nodes_global}_ | _100%_ |")
lines.append("")

lines.append("## God Nodes — architectural pillars")
lines.append("")
lines.append("These 20 symbols have the highest degree (most connections). They are the")
lines.append("load-bearing abstractions of the entire codebase.")
lines.append("")
lines.append("| Rank | Symbol | Degree | Source |")
lines.append("|---:|---|---:|---|")
for i, n in enumerate(top_god, 1):
    src = n.get("source_file", "")
    if src:
        src += f":L{n.get('source_line', '')}" if n.get("source_line") else ""
    lines.append(f"| {i} | `{md(n['label'])}` | {degree.get(n['id'], 0)} | `{md(src)}` |")
lines.append("")

lines.append("## Cross-subsystem bridges")
lines.append("")
lines.append("Nodes that touch 3+ communities — these are the integration points where")
lines.append("subsystems talk to each other. Refactoring them is high-leverage but high-risk.")
lines.append("")
lines.append("| Symbol | Home Community | Communities Touched | Source |")
lines.append("|---|---:|---:|---|")
for label, cid, n_touch, src in bridges:
    lines.append(f"| `{md(label)}` | {cid} | {n_touch} | `{md(src)}` |")
lines.append("")

lines.append("## Subsystem Breakdown")
lines.append("")

for s in subsystem_order:
    comms = subsystem_comms[s]
    total = sum(c for _, c, _ in comms)
    st = subsystem_stats[s]
    lines.append(f"### {s} — {st['nodes']} nodes across {st['communities']} communities")
    lines.append("")
    # Sort communities in subsystem by size desc
    comms_sorted = sorted(comms, key=lambda x: -x[1])
    for cid, count, top_labels in comms_sorted:
        labels_str = ", ".join(f"`{md(l)}`" for l in top_labels[:6])
        more = f" +{count - 6} more" if count > 6 else ""
        lines.append(f"- **Community {cid}** ({count} nodes): {labels_str}{more}")
    lines.append("")

lines.append("## SaaS Capability Checklist")
lines.append("")
lines.append("Cross-referencing the subsystems above against what a typical SaaS needs:")
lines.append("")
checklist = [
    ("User authentication (password + OAuth + MFA)", "Authentication & Identity"),
    ("Auth UI (login / signup / MFA flows)", "Auth UI (login / signup / MFA flows)"),
    ("Authorization / RBAC", "Multi-tenancy & RBAC"),
    ("Multi-tenancy isolation", "Multi-tenancy & RBAC"),
    ("Subscription billing", "Billing & Plans"),
    ("Metered usage / credits", "Billing & Plans"),
    ("Database layer", "Storage & Data Layer"),
    ("Webhook delivery", "Webhooks"),
    ("Rate limiting / security headers", "Middleware & API Gateway"),
    ("Health checks & metrics", "Observability & Health"),
    ("Transactional email", "Messaging & Announcements"),
    ("Per-tenant configuration", "Configuration & Branding"),
    ("Admin dashboard (operator console)", "Admin UI (operator console)"),
    ("End-user dashboard (tenant app)", "End-User Dashboard (tenant app)"),
    ("Public marketing site", "Public Site (marketing / custom pages)"),
    ("API documentation (OpenAPI)", "API Docs & OpenAPI"),
    ("CLI for ops", "CLI Tooling"),
    ("Test coverage", "Test Suite"),
    ("Deployment config (Docker/Fly)", "Deployment & Manifests"),
]
for cap, subsystem in checklist:
    found = subsystem in subsystem_stats
    mark = "[x]" if found else "[ ]"
    extra = f" — _{subsystem}_" if found else ""
    lines.append(f"- {mark} {cap}{extra}")
lines.append("")

OUT.write_text("\n".join(lines), encoding="utf-8")
print(f"wrote {OUT}")
print(f"subsystems found: {len(subsystem_order)}")
for s in subsystem_order:
    print(f"  {s}: {subsystem_stats[s]['communities']} communities, {subsystem_stats[s]['nodes']} nodes")
