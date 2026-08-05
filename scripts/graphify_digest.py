#!/usr/bin/env python3
"""graphify digest — on-demand markdown engineering report in your terminal.

Generates a comprehensive report including:
  - Recent commits and activity
  - Changed files/functions since last digest
  - Verification status (from verify-status.json)
  - Graph health (god nodes, community changes, knowledge gaps)
  - Architecture summary (subsystem sizes, growth areas)
  - Actionable insights (what to review, test, or investigate)

Usage:
  python graphify_digest.py [path] [--since DAYS] [--out FILE]
  python graphify_digest.py . --since 7   # last 7 days
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional


def git_log(repo: Path, since: str = "7 days ago") -> list[dict]:
    """Get commits since a date."""
    result = subprocess.run(
        ["git", "log", "--format=%H|%an|%ad|%s", "--date=short", f"--since={since}"],
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
                "author": parts[1],
                "date": parts[2],
                "message": parts[3],
            })
    return commits


def git_changed_since(repo: Path, since: str = "7 days ago") -> list[dict]:
    """Get files changed since a date."""
    result = subprocess.run(
        ["git", "log", "--name-only", "--format=", f"--since={since}"],
        cwd=repo, capture_output=True, text=True, timeout=10,
    )
    files = [f.strip() for f in result.stdout.strip().split("\n") if f.strip() and not f.strip().startswith("graphify-out")]
    file_counts = Counter(files)
    return [{"file": f, "times_changed": c} for f, c in file_counts.most_common(20)]


def git_contributors(repo: Path, since: str = "7 days ago") -> list[dict]:
    """Get contributor stats since a date by parsing git log output."""
    result = subprocess.run(
        ["git", "log", "--format=%an", f"--since={since}"],
        cwd=repo, capture_output=True, text=True, timeout=10,
    )
    counts = Counter(line.strip() for line in result.stdout.strip().split("\n") if line.strip())
    return [{"commits": c, "author": a} for a, c in counts.most_common(10)]


def load_graph(repo: Path) -> dict:
    graph_path = repo / "graphify-out" / "graph.json"
    if not graph_path.exists():
        return {"nodes": [], "links": []}
    return json.loads(graph_path.read_text(encoding="utf-8"))


def load_verify_status(repo: Path) -> Optional[dict]:
    status_path = repo / "graphify-out" / "verify-status.json"
    if not status_path.exists():
        return None
    return json.loads(status_path.read_text(encoding="utf-8"))


def load_graph_report(repo: Path) -> Optional[str]:
    report_path = repo / "graphify-out" / "GRAPH_REPORT.md"
    if not report_path.exists():
        return None
    return report_path.read_text(encoding="utf-8")


def compute_stats(graph: dict) -> dict:
    """Compute graph statistics."""
    nodes = graph.get("nodes", [])
    edges = graph.get("links", [])

    # Degree
    degree = Counter()
    for e in edges:
        degree[e.get("source", "")] += 1
        degree[e.get("target", "")] += 1

    # Communities
    communities = defaultdict(list)
    for n in nodes:
        cid = n.get("community")
        if cid is not None:
            communities[cid].append(n)

    # Isolated nodes (degree <= 1)
    isolated = [n for n in nodes if degree.get(n.get("id", ""), 0) <= 1]

    # Edge confidence breakdown
    extracted = sum(1 for e in edges if e.get("confidence") == "EXTRACTED")
    inferred = sum(1 for e in edges if e.get("confidence") == "INFERRED")

    return {
        "total_nodes": len(nodes),
        "total_edges": len(edges),
        "communities": len(communities),
        "isolated_nodes": len(isolated),
        "extracted_edges": extracted,
        "inferred_edges": inferred,
        "largest_community": max(communities.items(), key=lambda x: len(x[1])) if communities else None,
    }


def get_god_nodes(graph: dict, top_n: int = 10) -> list[dict]:
    """Get top-N most connected nodes."""
    degree = Counter()
    for e in graph.get("links", []):
        degree[e.get("source", "")] += 1
        degree[e.get("target", "")] += 1

    nodes_sorted = sorted(
        graph.get("nodes", []),
        key=lambda n: degree.get(n.get("id", ""), 0),
        reverse=True,
    )[:top_n]

    return [
        {
            "label": n.get("label", ""),
            "degree": degree.get(n.get("id", ""), 0),
            "source_file": n.get("source_file", ""),
            "community_name": n.get("community_name", ""),
        }
        for n in nodes_sorted
    ]


def categorize_isolated_nodes(graph: dict, isolated_nodes: list[dict]) -> dict:
    """Categorize isolated nodes into meaningful buckets instead of labeling all as 'dead code'."""
    categories = {
        "builtin_types": [],      # Context, MongoDB, Time — referenced but no source
        "api_types": [],          # Request/Response structs — leaf by design
        "react_pages": [],        # Imported once in router
        "type_definitions": [],   # TS/Go type defs
        "config_fields": [],      # package.json fields, tsconfig
        "e2e_tests": [],          # Playwright spec files
        "init_functions": [],     # Go init() — called automatically
        "true_dead_code": [],     # Genuinely unused (degree 0, has source)
        "documents": [],          # Doc/concept nodes
    }

    degree = Counter()
    for e in graph.get("links", []):
        degree[e.get("source", "")] += 1
        degree[e.get("target", "")] += 1

    for n in isolated_nodes:
        src = n.get("source_file", "")
        label = n.get("label", "")
        ft = n.get("file_type", "code")
        deg = degree.get(n.get("id", ""), 0)

        if not src:
            categories["builtin_types"].append({"label": label, "degree": deg})
        elif ft == "document" or ft == "concept":
            categories["documents"].append({"label": label, "source": src, "degree": deg})
        elif "_test.go" in src or "test" in label.lower():
            categories["init_functions"].append({"label": label, "source": src, "degree": deg}) if label == "init()" else categories["documents"].append({"label": label, "source": src, "degree": deg})
        elif ".spec.ts" in src or "playwright" in src or "e2e" in src:
            categories["e2e_tests"].append({"label": label, "source": src, "degree": deg})
        elif src.endswith("package.json") or src.endswith("tsconfig.json") or "config" in src.lower():
            categories["config_fields"].append({"label": label, "source": src, "degree": deg})
        elif label.endswith("Request") or label.endswith("Response") or label.endswith("Claims"):
            categories["api_types"].append({"label": label, "source": src, "degree": deg})
        elif src.endswith(".tsx") and ("Page" in label or "Modal" in label or "Tab" in label):
            categories["react_pages"].append({"label": label, "source": src, "degree": deg})
        elif label[0:1].isupper() and not label.endswith("()") and not label.startswith("."):
            categories["type_definitions"].append({"label": label, "source": src, "degree": deg})
        elif label == "init()":
            categories["init_functions"].append({"label": label, "source": src, "degree": deg})
        elif deg == 0 and src:
            categories["true_dead_code"].append({"label": label, "source": src, "degree": deg})
        else:
            categories["true_dead_code"].append({"label": label, "source": src, "degree": deg})

    return categories


def get_hotspots(graph: dict, changed_files: list[str]) -> list[dict]:
    """Find graph nodes in files that changed recently."""
    changed_set = set(changed_files)
    hotspots = []
    for n in graph.get("nodes", []):
        if n.get("source_file") in changed_set:
            hotspots.append({
                "label": n.get("label", ""),
                "source_file": n.get("source_file", ""),
                "community_name": n.get("community_name", ""),
            })
    return hotspots[:20]


def generate_digest(repo: Path, since_days: int = 7) -> str:
    """Generate the full engineering digest."""
    since = f"{since_days} days ago"
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    commits = git_log(repo, since)
    changed = git_changed_since(repo, since)
    contributors = git_contributors(repo, since)
    graph = load_graph(repo)
    stats = compute_stats(graph)
    god_nodes = get_god_nodes(graph)
    verify = load_verify_status(repo)

    # Get changed file paths for hotspot analysis
    changed_file_paths = [c["file"] for c in changed]
    hotspots = get_hotspots(graph, changed_file_paths)

    lines = [
        f"# 📊 Engineering Digest — {repo.name}",
        "",
        f"**Generated:** {now} | **Period:** last {since_days} days | "
        f"**Branch:** {subprocess.run(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], cwd=repo, capture_output=True, text=True).stdout.strip()}",
        "",
        "---",
        "",
        "## 🚀 Activity Summary",
        "",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Commits | {len(commits)} |",
        f"| Contributors | {len(contributors)} |",
        f"| Files touched | {len(changed)} |",
        f"| Active hotspots | {len(hotspots)} |",
        "",
    ]

    if commits:
        lines.append("### Recent Commits")
        lines.append("")
        lines.append("| Date | Author | Message |")
        lines.append("|------|--------|---------|")
        for c in commits[:15]:
            msg = c["message"][:70] + ("…" if len(c["message"]) > 70 else "")
            lines.append(f"| {c['date']} | {c['author']} | {msg} |")
        if len(commits) > 15:
            lines.append(f"| | | _... and {len(commits) - 15} more_ |")
        lines.append("")

    if contributors:
        lines.append("### Contributors")
        lines.append("")
        for c in contributors[:5]:
            bar = "█" * min(c["commits"], 20)
            lines.append(f"- **{c['author']}** — {c['commits']} commits {bar}")
        lines.append("")

    if changed:
        lines.append("### Most Changed Files")
        lines.append("")
        lines.append("| File | Times changed |")
        lines.append("|------|--------------|")
        for c in changed[:10]:
            lines.append(f"| `{c['file']}` | {c['times_changed']} |")
        lines.append("")

    # Graph health section
    lines.append("---")
    lines.append("")
    lines.append("## 🏗️ Graph Health")
    lines.append("")
    lines.append(f"| Metric | Value |")
    lines.append(f"|--------|-------|")
    lines.append(f"| Total nodes | {stats['total_nodes']:,} |")
    lines.append(f"| Total edges | {stats['total_edges']:,} |")
    lines.append(f"| Communities | {stats['communities']} |")
    lines.append(f"| Isolated nodes | {stats['isolated_nodes']} |")
    lines.append(f"| EXTRACTED edges | {stats['extracted_edges']:,} ({100*stats['extracted_edges']/max(stats['total_edges'],1):.0f}%) |")
    lines.append(f"| INFERRED edges | {stats['inferred_edges']:,} ({100*stats['inferred_edges']/max(stats['total_edges'],1):.0f}%) |")
    lines.append("")

    if stats["largest_community"]:
        lc = stats["largest_community"]
        lines.append(f"**Largest community:** {lc[1][0].get('community_name', f'Community {lc[0]}')} ({len(lc[1])} nodes)")
        lines.append("")

    # Compute degree for isolated node categorization
    all_nodes = graph.get("nodes", [])
    degree = Counter()
    for e in graph.get("links", []):
        degree[e.get("source", "")] += 1
        degree[e.get("target", "")] += 1

    cats: dict = {}
    if stats["isolated_nodes"] > 0:
        # Categorize isolated nodes instead of labeling all as dead code
        isolated_list = [n for n in all_nodes if degree.get(n.get("id", ""), 0) <= 1]
        cats = categorize_isolated_nodes(graph, isolated_list)

        lines.append(f"### 📋 Isolated Nodes Breakdown ({stats['isolated_nodes']} total, {100*stats['isolated_nodes']/max(stats['total_nodes'],1):.0f}%)")
        lines.append("")
        lines.append("These nodes have degree ≤ 1. Most are **NOT dead code** — they're leaf nodes by design:")
        lines.append("")
        lines.append("| Category | Count | What it means |")
        lines.append("|----------|-------|--------------|")
        lines.append(f"| Built-in types (no source) | {len(cats['builtin_types'])} | `Context`, `MongoDB`, `Time` — referenced everywhere but have no definition file |")
        lines.append(f"| API request/response types | {len(cats['api_types'])} | `RegisterRequest`, `LoginResponse` — leaf structs used once at API boundary |")
        lines.append(f"| React page components | {len(cats['react_pages'])} | Imported once in `App.tsx` router — normal |")
        lines.append(f"| Type definitions | {len(cats['type_definitions'])} | Struct/interface defs — referenced in their definition file |")
        lines.append(f"| Config file fields | {len(cats['config_fields'])} | `package.json` keys like `name`, `version` |")
        lines.append(f"| E2E test files | {len(cats['e2e_tests'])} | Playwright spec files — not imported by app code |")
        lines.append(f"| init() functions | {len(cats['init_functions'])} | Go `init()` — called automatically by runtime |")
        lines.append(f"| Documents/concepts | {len(cats['documents'])} | Doc nodes — connected to content, not code |")
        lines.append(f"| **Actual dead code** | {len(cats['true_dead_code'])} | Degree 0 with a source file — genuinely unused |")
        lines.append("")

        if cats["true_dead_code"]:
            lines.append("#### 🗑️ Actual Dead Code (degree 0, has source file)")
            lines.append("")
            for item in cats["true_dead_code"][:10]:
                lines.append(f"- `{item['label']}` — `{item['source']}`")
            if len(cats["true_dead_code"]) > 10:
                lines.append(f"- _... and {len(cats['true_dead_code']) - 10} more_")
            lines.append("")

    # God nodes
    lines.append("### 🏛️ God Nodes (Architectural Pillars)")
    lines.append("")
    lines.append("These are the most-connected symbols. Changes here ripple widely:")
    lines.append("")
    lines.append("| # | Symbol | Degree | Community | Source |")
    lines.append("|---|--------|--------|-----------|--------|")
    for i, gn in enumerate(god_nodes, 1):
        lines.append(f"| {i} | `{gn['label']}` | {gn['degree']} | {gn['community_name']} | `{gn['source_file']}` |")
    lines.append("")

    # Verification status
    if verify:
        lines.append("---")
        lines.append("")
        lines.append("## ✅ Verification Status")
        lines.append("")
        s = verify.get("summary", {})
        lines.append(f"- **Last run:** {verify.get('last_run', 'unknown')}")
        lines.append(f"- **✓ Equivalent:** {s.get('equivalent', 0)}")
        lines.append(f"- **✗ Breaking:** {s.get('breaking', 0)}")
        lines.append(f"- **? Other:** {s.get('inconclusive', 0)}")
        lines.append("")

        results = verify.get("results", [])
        if results:
            lines.append("| Function | Status | Inputs |")
            lines.append("|----------|--------|--------|")
            for r in results[:10]:
                icon = {"EQUIVALE": "✓", "BREAKING": "✗", "INCONCLUSIVE": "?", "ERROR": "!"}.get(r["status"], "·")
                lines.append(f"| `{r['function']}` | {icon} {r['status']} | {r.get('iterations', '?')} |")
            lines.append("")

    # Hotspots
    if hotspots:
        lines.append("---")
        lines.append("")
        lines.append("## 🔥 Active Hotspots")
        lines.append("")
        lines.append("Graph nodes in files that changed recently:")
        lines.append("")
        lines.append("| Symbol | File | Community |")
        lines.append("|--------|------|-----------|")
        for h in hotspots[:15]:
            lines.append(f"| `{h['label']}` | `{h['source_file']}` | {h['community_name']} |")
        lines.append("")

    # Insights & recommendations
    lines.append("---")
    lines.append("")
    lines.append("## 💡 Insights & Recommendations")
    lines.append("")

    insights = []

    # Insight: high commit velocity
    if len(commits) > 20:
        insights.append(f"📈 **High commit velocity** ({len(commits)} commits in {since_days} days) — consider whether the pace is sustainable")

    # Insight: actual dead code (not all isolated nodes)
    true_dead = len(cats.get("true_dead_code", [])) if cats else 0
    if true_dead > 5:
        insights.append(f"🗑️ **{true_dead} genuinely dead code nodes** (degree 0 with source file) — candidates for removal")

    # Insight: inferred edges ratio
    if stats["total_edges"] > 0:
        inferred_pct = 100 * stats["inferred_edges"] / stats["total_edges"]
        if inferred_pct > 30:
            lines.append(f"🔮 **{inferred_pct:.0f}% of edges are INFERRED** — graphify resolved {stats['inferred_edges']:,} method calls by type analysis (e.g., `s.Validate()` → `JWTService.Validate()`). This is cross-file resolution, not guessing — every INFERRED edge has a confidence score.")
        elif inferred_pct > 10:
            lines.append(f"🔮 **{inferred_pct:.0f}% of edges are INFERRED** — {stats['inferred_edges']:,} method calls were resolved by cross-file type analysis. This is healthy: it means graphify is connecting method calls to their implementations across files.")

    # Insight: breaking changes
    if verify and verify.get("summary", {}).get("breaking", 0) > 0:
        insights.append(f"🚨 **{verify['summary']['breaking']} breaking change(s) detected** — run `graphify verify` for details before merging")

    # Insight: god node churn
    if hotspots:
        god_labels = {gn["label"] for gn in god_nodes}
        god_in_hotspots = [h for h in hotspots if h["label"] in god_labels]
        if god_in_hotspots:
            insights.append(f"⚠️ **{len(god_in_hotspots)} god node(s) changed recently** — high-centrality symbols are being modified, review carefully")

    # Insight: contributor concentration
    if contributors and len(contributors) > 0:
        top_contributor_pct = 100 * contributors[0]["commits"] / max(len(commits), 1)
        if top_contributor_pct > 70 and len(contributors) > 1:
            insights.append(f"👥 **{contributors[0]['author']} wrote {top_contributor_pct:.0f}% of commits** — consider knowledge sharing")

    if not insights:
        insights.append("✅ No critical insights — the codebase looks healthy")

    for ins in insights:
        lines.append(f"- {ins}")
    lines.append("")

    # Suggested commands
    lines.append("---")
    lines.append("")
    lines.append("## 🛠️ Suggested Commands")
    lines.append("")
    lines.append("```bash")
    lines.append("# Map a PR's blast radius")
    lines.append("python scripts/graphify_prs.py . --base main --head HEAD")
    lines.append("")
    lines.append("# Verify behavior preservation for changed functions")
    lines.append("python scripts/graphify_verify.py .")
    lines.append("")
    lines.append("# Start auto-verify watcher")
    lines.append("python scripts/graphify_verify_watch.py .")
    lines.append("")
    lines.append("# Query the graph")
    lines.append(f"graphify query \"how does auth work\" --graph {repo}/graphify-out/graph.json")
    lines.append("")
    lines.append("# Find affected callers of a symbol")
    lines.append(f"graphify affected \"AuthHandler\" --graph {repo}/graphify-out/graph.json")
    lines.append("```")
    lines.append("")

    lines.append("---")
    lines.append(f"_Generated by `graphify digest` at {now}_")

    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(
        prog="graphify digest",
        description="On-demand markdown engineering report in your terminal.",
    )
    ap.add_argument("path", nargs="?", default=".", help="Path to the repo (default: .)")
    ap.add_argument("--since", "-s", type=int, default=7, help="Days to include (default: 7)")
    ap.add_argument("--out", "-o", help="Output file (default: stdout)")
    args = ap.parse_args()

    repo = Path(args.path).resolve()
    if not (repo / ".git").exists():
        print(f"ERROR: {repo} is not a git repository", file=sys.stderr)
        sys.exit(2)

    print(f"graphify digest — generating report for last {args.since} days...", file=sys.stderr)

    digest = generate_digest(repo, since_days=args.since)

    if args.out:
        Path(args.out).write_text(digest, encoding="utf-8")
        print(f"Digest written to {args.out}", file=sys.stderr)
    else:
        print(digest)


if __name__ == "__main__":
    main()
