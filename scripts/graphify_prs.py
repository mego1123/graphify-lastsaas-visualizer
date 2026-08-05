#!/usr/bin/env python3
"""graphify prs — map a PR's blast radius across the codebase.

Given a PR (by number, branch, or commit range), this tool:
  1. Identifies changed files and functions via git diff
  2. Cross-references each changed symbol with graph.json
  3. Performs reverse traversal to find all downstream callers
  4. Maps affected communities and subsystems
  5. Assesses risk (high if god nodes or cross-subsystem bridges are touched)
  6. Emits a markdown report suitable for pasting into the PR description

Usage:
  python graphify_prs.py [path] --base main --head feature-branch
  python graphify_prs.py [path] --pr 42        # GitHub PR #42
  python graphify_prs.py [path]                # defaults to HEAD vs main
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import defaultdict, Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class ChangedFile:
    path: str
    status: str  # added, modified, deleted, renamed
    additions: int = 0
    deletions: int = 0

@dataclass
class ChangedFunction:
    name: str
    file: str
    kind: str  # added, modified, removed
    old_body: Optional[str] = None
    new_body: Optional[str] = None

@dataclass
class BlastRadiusResult:
    changed_files: list[ChangedFile] = field(default_factory=list)
    changed_functions: list[ChangedFunction] = field(default_factory=list)
    affected_communities: dict[int, dict] = field(default_factory=dict)  # cid -> {name, color, nodes_touched}
    affected_subsystems: dict[str, int] = field(default_factory=dict)  # subsystem -> count
    downstream_callers: dict[str, list[str]] = field(default_factory=dict)  # function -> callers
    god_nodes_touched: list[dict] = field(default_factory=list)
    cross_subsystem_bridges_touched: list[dict] = field(default_factory=list)
    risk_level: str = "LOW"  # LOW, MEDIUM, HIGH, CRITICAL
    risk_factors: list[str] = field(default_factory=list)
    stats: dict = field(default_factory=dict)


# ---------- git helpers ----------

def git_diff_files(repo: Path, base: str, head: str) -> list[ChangedFile]:
    """Get list of changed files between base and head, excluding generated files."""
    result = subprocess.run(
        ["git", "diff", "--name-status", "--numstat", f"{base}...{head}"],
        cwd=repo, capture_output=True, text=True, timeout=10,
    )
    files = []
    for line in result.stdout.strip().split("\n"):
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) >= 4:
            status = parts[0]
            additions = int(parts[1]) if parts[1].isdigit() else 0
            deletions = int(parts[2]) if parts[2].isdigit() else 0
            path = parts[3]
        elif len(parts) == 2:
            status = parts[0]
            additions = 0
            deletions = 0
            path = parts[1]
        else:
            continue
        # Normalize status
        status = status[0] if status else "M"
        # Skip generated/build files
        if any(path.startswith(skip) for skip in ["graphify-out/", "node_modules/", ".next/", "dist/", "build/"]):
            continue
        if path.endswith((".json", ".lock", ".svg", ".png", ".jpg", ".md")) and "graphify" not in path:
            # Skip non-code files unless they're graphify-related
            if path not in ("package.json", "tsconfig.json"):
                continue
        files.append(ChangedFile(path=path, status=status, additions=additions, deletions=deletions))
    return files


def git_show_file(repo: Path, file_path: str, ref: str) -> Optional[str]:
    """Get file content at a git ref."""
    try:
        result = subprocess.run(
            ["git", "show", f"{ref}:{file_path}"],
            cwd=repo, capture_output=True, text=True, timeout=10,
        )
        return result.stdout if result.returncode == 0 else None
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return None


def git_commits(repo: Path, base: str, head: str) -> list[dict]:
    """Get list of commits between base and head."""
    result = subprocess.run(
        ["git", "log", "--oneline", "--format=%H|%s|%an|%ad", f"{base}..{head}"],
        cwd=repo, capture_output=True, text=True, timeout=10,
    )
    commits = []
    for line in result.stdout.strip().split("\n"):
        if not line.strip():
            continue
        parts = line.split("|", 3)
        if len(parts) == 4:
            commits.append({
                "hash": parts[0][:8],
                "message": parts[1],
                "author": parts[2],
                "date": parts[3],
            })
    return commits


def git_default_branch(repo: Path) -> str:
    """Detect the default branch (main or master)."""
    for branch in ["main", "master"]:
        result = subprocess.run(
            ["git", "rev-parse", "--verify", branch],
            cwd=repo, capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            return branch
    return "main"


# ---------- graph analysis ----------

def load_graph(repo: Path) -> dict:
    """Load graph.json from the repo."""
    graph_path = repo / "graphify-out" / "graph.json"
    if not graph_path.exists():
        return {"nodes": [], "links": []}
    return json.loads(graph_path.read_text(encoding="utf-8"))


def find_nodes_by_file(graph: dict, file_path: str) -> list[dict]:
    """Find all graph nodes whose source_file matches."""
    return [n for n in graph.get("nodes", []) if n.get("source_file") == file_path]


def find_node_by_label(graph: dict, label: str) -> Optional[dict]:
    """Find a node by its label (exact or suffix match)."""
    for n in graph.get("nodes", []):
        if n.get("label") == label:
            return n
    # Suffix match (e.g. ".Validate()" matches "JWTService.Validate()")
    for n in graph.get("nodes", []):
        nl = n.get("label", "")
        if nl.endswith(f".{label}") or nl.endswith(f".{label}()"):
            return n
    return None


def find_downstream_callers(graph: dict, node_id: str, max_depth: int = 3) -> list[str]:
    """Reverse traversal: find all nodes that call/reference the given node."""
    callers: set[str] = set()
    frontier = {node_id}
    visited: set[str] = set()

    for _ in range(max_depth):
        next_frontier: set[str] = set()
        for edge in graph.get("links", []):
            if edge.get("relation") in ("calls", "indirect_call", "references", "uses"):
                target = edge.get("target", "")
                source = edge.get("source", "")
                if target in frontier and source not in visited:
                    callers.add(source)
                    next_frontier.add(source)
        visited.update(frontier)
        frontier = next_frontier
        if not frontier:
            break

    return list(callers)


def resolve_node_labels(graph: dict, node_ids: list[str]) -> list[str]:
    """Convert node IDs to human-readable labels."""
    id_to_node = {n["id"]: n for n in graph.get("nodes", [])}
    labels = []
    for nid in node_ids:
        node = id_to_node.get(nid)
        if node:
            labels.append(node.get("label", nid))
        else:
            labels.append(nid)
    return labels


def get_god_nodes(graph: dict, top_n: int = 20) -> list[dict]:
    """Get the top-N most connected nodes."""
    degree = Counter()
    for edge in graph.get("links", []):
        degree[edge.get("source", "")] += 1
        degree[edge.get("target", "")] += 1

    nodes_by_degree = sorted(
        graph.get("nodes", []),
        key=lambda n: degree.get(n.get("id", ""), 0),
        reverse=True,
    )[:top_n]

    return [
        {
            "label": n.get("label", ""),
            "degree": degree.get(n.get("id", ""), 0),
            "id": n.get("id", ""),
            "source_file": n.get("source_file", ""),
            "community": n.get("community"),
            "community_name": n.get("community_name", ""),
        }
        for n in nodes_by_degree
    ]


def get_cross_subsystem_bridges(graph: dict, threshold: int = 3) -> list[dict]:
    """Find nodes that connect 3+ communities (high betweenness)."""
    node_communities: dict[str, set] = defaultdict(set)
    for n in graph.get("nodes", []):
        cid = n.get("community")
        if cid is not None:
            node_communities[n.get("id", "")].add(cid)

    for edge in graph.get("links", []):
        s, t = edge.get("source", ""), edge.get("target", "")
        sn = next((n for n in graph.get("nodes", []) if n.get("id") == s), None)
        tn = next((n for n in graph.get("nodes", []) if n.get("id") == t), None)
        if sn and tn:
            sc, tc = sn.get("community"), tn.get("community")
            if sc is not None and tc is not None and sc != tc:
                node_communities[s].add(tc)
                node_communities[t].add(sc)

    bridges = []
    for n in graph.get("nodes", []):
        nid = n.get("id", "")
        if len(node_communities.get(nid, set())) >= threshold:
            bridges.append({
                "label": n.get("label", ""),
                "id": nid,
                "communities_touched": len(node_communities[nid]),
                "source_file": n.get("source_file", ""),
            })
    bridges.sort(key=lambda x: -x["communities_touched"])
    return bridges


def classify_subsystem(community_name: str) -> str:
    """Classify a community into a SaaS subsystem (simplified)."""
    cn = community_name.lower()
    if any(k in cn for k in ["auth", "jwt", "totp", "oauth", "password", "mfa"]):
        return "Authentication & Identity"
    if any(k in cn for k in ["stripe", "billing", "payment", "subscription", "checkout"]):
        return "Billing & Plans"
    if any(k in cn for k in ["tenant", "rbac", "role", "permission", "membership"]):
        return "Multi-tenancy & RBAC"
    if any(k in cn for k in ["mongo", "database", "storage", "schema"]):
        return "Storage & Data Layer"
    if any(k in cn for k in ["webhook", "dispatcher"]):
        return "Webhooks"
    if any(k in cn for k in ["middleware", "rate limit", "body limit"]):
        return "Middleware & API Gateway"
    if any(k in cn for k in ["health", "metrics", "telemetry", "monitoring"]):
        return "Observability & Health"
    if any(k in cn for k in ["email", "resend", "message", "announcement"]):
        return "Messaging & Announcements"
    if any(k in cn for k in ["config", "branding", "env"]):
        return "Configuration & Branding"
    if any(k in cn for k in ["admin", "dashboard"]):
        return "Admin UI"
    if any(k in cn for k in ["login", "signup", "auth callback"]):
        return "Auth UI"
    if any(k in cn for k in ["landing", "public", "custom page"]):
        return "Public Site"
    if any(k in cn for k in ["cli", "command", "mcp", "process"]):
        return "CLI Tooling"
    if any(k in cn for k in ["test"]):
        return "Test Suite"
    if any(k in cn for k in ["api doc", "documentation", "openapi"]):
        return "API Docs & OpenAPI"
    if any(k in cn for k in ["docker", "deploy", "manifest"]):
        return "Deployment & Manifests"
    return "Other"


# ---------- main analysis ----------

def analyze_pr(repo: Path, base: str, head: str, graph: dict) -> BlastRadiusResult:
    """Analyze the blast radius of changes between base and head."""
    result = BlastRadiusResult()

    # 1. Get changed files
    result.changed_files = git_diff_files(repo, base, head)

    # 2. Get changed functions (simplified: use function-level diff)
    for cf in result.changed_files:
        if not cf.path.endswith((".go", ".ts", ".tsx")):
            continue
        old_source = git_show_file(repo, cf.path, base) if cf.status != "A" else None
        new_source = git_show_file(repo, cf.path, head) if cf.status != "D" else None

        if old_source and new_source:
            # Find changed functions by comparing function names
            old_funcs = set(re.findall(r'(?:^|\n)\s*(?:export\s+)?func\s+(\w+)', old_source))
            new_funcs = set(re.findall(r'(?:^|\n)\s*(?:export\s+)?func\s+(\w+)', new_source))

            for name in new_funcs - old_funcs:
                result.changed_functions.append(ChangedFunction(name=name, file=cf.path, kind="added"))
            for name in old_funcs - new_funcs:
                result.changed_functions.append(ChangedFunction(name=name, file=cf.path, kind="removed"))
            for name in old_funcs & new_funcs:
                result.changed_functions.append(ChangedFunction(name=name, file=cf.path, kind="modified"))
        elif new_source and cf.status == "A":
            new_funcs = set(re.findall(r'(?:^|\n)\s*(?:export\s+)?func\s+(\w+)', new_source))
            for name in new_funcs:
                result.changed_functions.append(ChangedFunction(name=name, file=cf.path, kind="added"))
        elif old_source and cf.status == "D":
            old_funcs = set(re.findall(r'(?:^|\n)\s*(?:export\s+)?func\s+(\w+)', old_source))
            for name in old_funcs:
                result.changed_functions.append(ChangedFunction(name=name, file=cf.path, kind="removed"))

    # 3. Cross-reference with graph.json
    god_nodes = get_god_nodes(graph)
    god_labels = {gn["label"] for gn in god_nodes}
    god_ids = {gn["id"] for gn in god_nodes}
    bridges = get_cross_subsystem_bridges(graph)
    bridge_labels = {b["label"] for b in bridges}

    id_to_node = {n["id"]: n for n in graph.get("nodes", [])}

    # Check file-level: if any changed file contains god nodes or bridges
    changed_file_set = {cf.path for cf in result.changed_files}
    for gn in god_nodes:
        if gn.get("source_file", "") in changed_file_set:
            result.god_nodes_touched.append({
                "name": gn["label"],
                "degree": gn["degree"],
                "community": gn.get("community_name", ""),
                "file": gn.get("source_file", ""),
            })

    for cf in result.changed_functions:
        # Find this function in the graph
        node = find_node_by_label(graph, cf.name)
        if not node:
            continue

        cid = node.get("community")
        cname = node.get("community_name", f"Community {cid}")

        # Track affected communities
        if cid is not None:
            if cid not in result.affected_communities:
                result.affected_communities[cid] = {
                    "name": cname,
                    "color": "",
                    "nodes_touched": 0,
                    "functions": [],
                }
            result.affected_communities[cid]["nodes_touched"] += 1
            result.affected_communities[cid]["functions"].append(cf.name)

            # Track subsystems
            subsystem = classify_subsystem(cname)
            result.affected_subsystems[subsystem] = result.affected_subsystems.get(subsystem, 0) + 1

        # Find downstream callers
        callers = find_downstream_callers(graph, node["id"], max_depth=3)
        if callers:
            caller_labels = resolve_node_labels(graph, callers)
            result.downstream_callers[cf.name] = caller_labels[:15]  # cap at 15

        # Check if this is a god node
        if cf.name in god_labels or any(cf.name == gn["label"] for gn in god_nodes):
            result.god_nodes_touched.append({
                "name": cf.name,
                "degree": next((gn["degree"] for gn in god_nodes if gn["label"] == cf.name), 0),
                "community": cname,
            })

        # Check if this is a cross-subsystem bridge
        if cf.name in bridge_labels or any(cf.name == b["label"] for b in bridges):
            result.cross_subsystem_bridges_touched.append({
                "name": cf.name,
                "communities_touched": next((b["communities_touched"] for b in bridges if b["label"] == cf.name), 0),
            })

    # 4. Assess risk
    result.risk_factors = []
    if result.god_nodes_touched:
        result.risk_factors.append(f"Touches {len(result.god_nodes_touched)} god node(s) — high-centrality symbols")
        result.risk_level = "HIGH"
    if result.cross_subsystem_bridges_touched:
        result.risk_factors.append(f"Touches {len(result.cross_subsystem_bridges_touched)} cross-subsystem bridge(s)")
        result.risk_level = "HIGH"
    if len(result.affected_subsystems) >= 3:
        result.risk_factors.append(f"Spans {len(result.affected_subsystems)} subsystems — wide blast radius")
        if result.risk_level != "HIGH":
            result.risk_level = "MEDIUM"
    total_downstream = sum(len(v) for v in result.downstream_callers.values())
    if total_downstream >= 20:
        result.risk_factors.append(f"{total_downstream} downstream callers affected")
        if result.risk_level == "LOW":
            result.risk_level = "MEDIUM"
    if result.god_nodes_touched and result.cross_subsystem_bridges_touched:
        result.risk_level = "CRITICAL"
    if not result.risk_factors:
        result.risk_factors.append("No high-centrality or cross-subsystem nodes touched")

    # 5. Stats
    result.stats = {
        "files_changed": len(result.changed_files),
        "functions_changed": len(result.changed_functions),
        "communities_affected": len(result.affected_communities),
        "subsystems_affected": len(result.affected_subsystems),
        "downstream_callers": total_downstream,
        "additions": sum(f.additions for f in result.changed_files),
        "deletions": sum(f.deletions for f in result.changed_files),
    }

    return result


def emit_pr_report(result: BlastRadiusResult, base: str, head: str, commits: list[dict]) -> str:
    """Emit a markdown PR blast radius report."""
    lines = [
        f"# PR Blast Radius: `{base}...{head}`",
        "",
        f"**Commits:** {len(commits)} | **Files changed:** {result.stats['files_changed']} | "
        f"**Functions changed:** {result.stats['functions_changed']} | "
        f"+{result.stats['additions']} -{result.stats['deletions']}",
        "",
        f"## Risk Assessment: {result.risk_level}",
        "",
    ]

    risk_icon = {"LOW": "🟢", "MEDIUM": "🟡", "HIGH": "🟠", "CRITICAL": "🔴"}[result.risk_level]
    lines[0] = f"# {risk_icon} PR Blast Radius: `{base}...{head}`"

    lines.append("### Risk Factors")
    lines.append("")
    for rf in result.risk_factors:
        lines.append(f"- {rf}")
    lines.append("")

    if commits:
        lines.append("## Commits")
        lines.append("")
        lines.append("| Hash | Message | Author |")
        lines.append("|------|---------|--------|")
        for c in commits[:10]:
            lines.append(f"| `{c['hash']}` | {c['message'][:80]} | {c['author']} |")
        if len(commits) > 10:
            lines.append(f"| ... | _{len(commits) - 10} more commits_ | |")
        lines.append("")

    lines.append("## Changed Files")
    lines.append("")
    lines.append("| Status | File | +/− |")
    lines.append("|--------|------|-----|")
    for cf in result.changed_files:
        icon = {"A": "➕", "M": "✏️", "D": "❌", "R": "📝"}.get(cf.status, "✏️")
        lines.append(f"| {icon} {cf.status} | `{cf.path}` | +{cf.additions} -{cf.deletions} |")
    lines.append("")

    lines.append("## Changed Functions")
    lines.append("")
    if not result.changed_functions:
        lines.append("_No functions detected as changed (or changes are in non-code files)._")
    else:
        lines.append("| Function | File | Change |")
        lines.append("|----------|------|--------|")
        for cf in result.changed_functions:
            icon = {"added": "🟢", "modified": "🟡", "removed": "🔴"}.get(cf.kind, "❓")
            lines.append(f"| `{cf.name}` | `{cf.file}` | {icon} {cf.kind} |")
    lines.append("")

    if result.affected_communities:
        lines.append("## Affected Communities")
        lines.append("")
        lines.append("| Community | Functions Touched |")
        lines.append("|-----------|-------------------|")
        for cid, info in sorted(result.affected_communities.items(), key=lambda x: -x[1]["nodes_touched"]):
            funcs = ", ".join(f"`{f}`" for f in info["functions"][:5])
            more = f" +{len(info['functions']) - 5} more" if len(info["functions"]) > 5 else ""
            lines.append(f"| **{info['name']}** | {funcs}{more} |")
        lines.append("")

    if result.affected_subsystems:
        lines.append("## Affected Subsystems")
        lines.append("")
        for sub, count in sorted(result.affected_subsystems.items(), key=lambda x: -x[1]):
            lines.append(f"- **{sub}**: {count} function(s)")
        lines.append("")

    if result.god_nodes_touched:
        lines.append("## ⚠ God Nodes Touched (High Centrality)")
        lines.append("")
        lines.append("These are the most-connected symbols in the codebase. Changes here ripple widely.")
        lines.append("")
        for gn in result.god_nodes_touched:
            lines.append(f"- **`{gn['name']}`** — {gn['degree']} connections, community: {gn['community']}")
        lines.append("")

    if result.cross_subsystem_bridges_touched:
        lines.append("## ⚠ Cross-Subsystem Bridges Touched")
        lines.append("")
        lines.append("These nodes connect multiple subsystems. Changes here can break integrations.")
        lines.append("")
        for b in result.cross_subsystem_bridges_touched:
            lines.append(f"- **`{b['name']}`** — touches {b['communities_touched']} communities")
        lines.append("")

    if result.downstream_callers:
        lines.append("## Downstream Callers (Blast Radius)")
        lines.append("")
        lines.append("These functions call the changed functions and may be affected:")
        lines.append("")
        for func, callers in result.downstream_callers.items():
            lines.append(f"### `{func}`")
            lines.append(f"_{len(callers)} downstream caller(s)_")
            lines.append("")
            for c in callers[:10]:
                lines.append(f"- `{c}`")
            if len(callers) > 10:
                lines.append(f"- _... and {len(callers) - 10} more_")
            lines.append("")

    lines.append("## Recommendations")
    lines.append("")
    if result.risk_level in ("HIGH", "CRITICAL"):
        lines.append("- 🔴 **High risk PR** — consider breaking into smaller PRs")
        lines.append("- Run full test suite, not just unit tests for changed files")
        lines.append("- Pay special attention to the downstream callers listed above")
        lines.append("- Consider running `graphify verify` to prove behavior preservation")
    elif result.risk_level == "MEDIUM":
        lines.append("- 🟡 **Moderate risk** — standard review process")
        lines.append("- Run tests for affected communities")
        lines.append("- Check the downstream callers for breaking changes")
    else:
        lines.append("- 🟢 **Low risk** — changes are isolated")
        lines.append("- Standard review process is sufficient")

    lines.append("")
    lines.append("---")
    lines.append(f"_Generated by `graphify prs` — {len(result.changed_files)} files, "
                 f"{len(result.changed_functions)} functions, "
                 f"{result.stats['downstream_callers']} downstream callers_")

    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(
        prog="graphify prs",
        description="Map a PR's blast radius across the codebase.",
    )
    ap.add_argument("path", nargs="?", default=".", help="Path to the repo (default: .)")
    ap.add_argument("--base", "-b", help="Base branch (default: main/master)")
    ap.add_argument("--head", "-H", help="Head branch/commit (default: HEAD)")
    ap.add_argument("--pr", type=int, help="GitHub PR number (fetches base/head from PR)")
    ap.add_argument("--out", "-o", help="Output file (default: stdout)")
    args = ap.parse_args()

    repo = Path(args.path).resolve()
    if not (repo / ".git").exists():
        print(f"ERROR: {repo} is not a git repository", file=sys.stderr)
        sys.exit(2)

    base = args.base or git_default_branch(repo)
    head = args.head or "HEAD"

    print(f"graphify prs — analyzing {base}...{head}", file=sys.stderr)

    graph = load_graph(repo)
    if not graph.get("nodes"):
        print("WARNING: graph.json is empty or missing. Run `graphify extract .` first.", file=sys.stderr)

    commits = git_commits(repo, base, head)
    result = analyze_pr(repo, base, head, graph)

    report = emit_pr_report(result, base, head, commits)

    if args.out:
        Path(args.out).write_text(report, encoding="utf-8")
        print(f"Report written to {args.out}", file=sys.stderr)
    else:
        print(report)

    # Exit code based on risk
    if result.risk_level == "CRITICAL":
        sys.exit(3)
    elif result.risk_level == "HIGH":
        sys.exit(2)
    elif result.risk_level == "MEDIUM":
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
