"""Export the architecture breakdown as JSON for the web app's treemap tab.

Produces a nested structure:
  subsystems: [{ name, communities: [{ id, label, color, count, top_symbols: [...] }], total_nodes }]
  god_nodes: [{ rank, label, degree, source_file, community, community_name }]
  checklist: [{ capability, subsystem, present }]
"""
import json
from collections import defaultdict, Counter
from pathlib import Path

GRAPH = Path("/home/z/my-project/repos/lastsaas/graphify-out/graph.json")
LABELS = Path("/home/z/my-project/repos/lastsaas/graphify-out/community_labels.json")
OUT = Path("/home/z/my-project/public/architecture.json")

# Inline copy of classify() from architecture_map.py to avoid running its main body on import
def classify(members):
    src_files = [m.get("source_file", "") for m in members if m.get("source_file")]
    src_joined = " ".join(src_files).lower()
    labels = [m.get("label", "") for m in members]
    label_joined = " ".join(labels).lower()
    comm_names = [m.get("community_name", "") for m in members if m.get("community_name")]
    comm_name_joined = " ".join(comm_names).lower()
    joined = src_joined + " " + label_joined + " " + comm_name_joined

    # Frontend route groups
    if "pages/public/" in src_joined or "landingpage" in label_joined or "custompage" in label_joined:
        return "Public Site (marketing / custom pages)"
    if "pages/auth/" in src_joined or any(k in label_joined for k in ["loginpage", "signuppage", "authcallback", "resetpassword", "forgotpassword", "verifyemail", "mfachallenge", "magiclinkverify"]):
        return "Auth UI (login / signup / MFA flows)"
    if "pages/app/" in src_joined or any(k in label_joined for k in ["dashboardpage", "settingspage", "activitypage", "teampage", "billingpage", "buillcreditspage", "buycreditspage", "plansuccesspage", "billingsuccesspage", "billingcancelpage", "onboardingpage", "planpage", "testentitlementspage"]):
        return "End-User Dashboard (tenant app)"
    if "pages/admin/" in src_joined or any(k in label_joined for k in ["adminpage", "userspage", "tenantspage", "planspage", "configpage", "announcementpage", "logspage", "apikeypage", "financialpage", "dashboardpage", "healthpage", "brandingpage", "promotionspage", "rootmemberspage", "pmpage", "aboutpage", "userprofilepage", "tenantprofilepage"]):
        return "Admin UI (operator console)"

    # Pre-check: LLM-generated community_name
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

    # Backend domain areas
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

data = json.loads(GRAPH.read_text(encoding="utf-8"))
nodes = data["nodes"]
edges = data["links"]

degree = Counter()
for e in edges:
    degree[e["source"]] += 1
    degree[e["target"]] += 1

# Group nodes by community
comm_members: dict[int, list[dict]] = defaultdict(list)
for n in nodes:
    cid = n.get("community")
    if cid is None: continue
    comm_members[cid].append(n)

# Classify each community
comm_to_subsystem: dict[int, str] = {}
for cid, members in comm_members.items():
    comm_to_subsystem[cid] = classify(members)

# Load community colors from the extracted communities JSON
communities_colors = {}
communities_json = Path("/home/z/my-project/public/graph-communities.json")
if communities_json.exists():
    for c in json.loads(communities_json.read_text(encoding="utf-8")):
        cid = c.get("id")
        color = c.get("color")
        if cid is not None and color:
            communities_colors[cid] = color

# Build subsystem -> communities structure
subsystem_data: dict[str, list[dict]] = defaultdict(list)
for cid, members in comm_members.items():
    members_sorted = sorted(members, key=lambda m: degree.get(m["id"], 0), reverse=True)
    top_symbols = [
        {"label": m["label"], "degree": degree.get(m["id"], 0), "source_file": m.get("source_file", "")}
        for m in members_sorted[:8]
    ]
    subsystem_data[comm_to_subsystem[cid]].append({
        "id": cid,
        "label": members[0].get("community_name", f"Community {cid}"),
        "color": communities_colors.get(cid, "#888888"),
        "count": len(members),
        "top_symbols": top_symbols,
    })

# Sort subsystems by total node count desc
subsystems_list = []
for name, comms in subsystem_data.items():
    total = sum(c["count"] for c in comms)
    comms.sort(key=lambda c: -c["count"])
    subsystems_list.append({
        "name": name,
        "communities": comms,
        "total_communities": len(comms),
        "total_nodes": total,
    })
subsystems_list.sort(key=lambda s: -s["total_nodes"])

# God nodes (top 20 by degree)
top_god = sorted(nodes, key=lambda n: degree.get(n["id"], 0), reverse=True)[:20]
god_nodes = [
    {
        "rank": i + 1,
        "label": n["label"],
        "degree": degree.get(n["id"], 0),
        "source_file": n.get("source_file", ""),
        "community": n.get("community"),
        "community_name": n.get("community_name", ""),
    }
    for i, n in enumerate(top_god)
]

# Capability checklist
checklist_caps = [
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
subsystem_names = {s["name"] for s in subsystems_list}
checklist = [
    {"capability": cap, "subsystem": sub, "present": sub in subsystem_names}
    for cap, sub in checklist_caps
]

out = {
    "subsystems": subsystems_list,
    "god_nodes": god_nodes,
    "checklist": checklist,
    "totals": {
        "nodes": len(nodes),
        "edges": len(edges),
        "communities": len(comm_members),
        "subsystems": len(subsystems_list),
    },
}
OUT.write_text(json.dumps(out), encoding="utf-8")
print(f"wrote {OUT}")
print(f"  {len(subsystems_list)} subsystems, {len(god_nodes)} god nodes, {len(checklist)} checklist items")
