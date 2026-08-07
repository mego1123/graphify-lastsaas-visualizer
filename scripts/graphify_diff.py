#!/usr/bin/env python3
"""graphify diff — compare two graph.json snapshots to see structural changes.

Shows what was added, removed, or modified between two graph builds:
- New nodes (added code)
- Removed nodes (deleted code)
- New edges (new connections)
- Removed edges (broken connections)
- Community changes (restructured modules)
- God node changes (shifts in architecture)
- Growth metrics (nodes/edges/communities delta)

Usage:
  python graphify_diff.py <old.json> <new.json> [--out report.md]
  python graphify_diff.py graph-v1.json graph-v2.json
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class DiffResult:
    # Node changes
    added_nodes: list[dict] = field(default_factory=list)
    removed_nodes: list[dict] = field(default_factory=list)
    # Edge changes
    added_edges: list[dict] = field(default_factory=list)
    removed_edges: list[dict] = field(default_factory=list)
    # Community changes
    new_communities: list[dict] = field(default_factory=list)
    removed_communities: list[dict] = field(default_factory=list)
    grown_communities: list[dict] = field(default_factory=list)
    shrunk_communities: list[dict] = field(default_factory=list)
    # God node changes
    new_god_nodes: list[dict] = field(default_factory=list)
    demoted_god_nodes: list[dict] = field(default_factory=list)
    # Stats
    old_stats: dict = field(default_factory=dict)
    new_stats: dict = field(default_factory=dict)
    deltas: dict = field(default_factory=dict)


def load_graph(path: str) -> dict:
    p = Path(path)
    if not p.exists():
        print(f"ERROR: {path} not found", file=sys.stderr)
        sys.exit(2)
    return json.loads(p.read_text(encoding="utf-8"))


def compute_degree(graph: dict) -> Counter:
    degree = Counter()
    for e in graph.get("links", []):
        degree[e.get("source", "")] += 1
        degree[e.get("target", "")] += 1
    return degree


def get_god_nodes(graph: dict, top_n: int = 20) -> list[dict]:
    degree = compute_degree(graph)
    nodes_sorted = sorted(
        graph.get("nodes", []),
        key=lambda n: degree.get(n.get("id", ""), 0),
        reverse=True,
    )[:top_n]
    return [
        {
            "id": n.get("id", ""),
            "label": n.get("label", ""),
            "degree": degree.get(n.get("id", ""), 0),
            "community": n.get("community"),
            "community_name": n.get("community_name", ""),
            "source_file": n.get("source_file", ""),
        }
        for n in nodes_sorted
    ]


def diff_graphs(old: dict, new: dict) -> DiffResult:
    """Compare two graph.json snapshots."""
    result = DiffResult()

    old_nodes = {n["id"]: n for n in old.get("nodes", [])}
    new_nodes = {n["id"]: n for n in new.get("nodes", [])}

    old_edges = {(e.get("source", ""), e.get("target", ""), e.get("relation", "")): e
                 for e in old.get("links", [])}
    new_edges = {(e.get("source", ""), e.get("target", ""), e.get("relation", "")): e
                 for e in new.get("links", [])}

    # Node changes
    result.added_nodes = [new_nodes[id] for id in new_nodes if id not in old_nodes]
    result.removed_nodes = [old_nodes[id] for id in old_nodes if id not in new_nodes]

    # Edge changes
    result.added_edges = [new_edges[k] for k in new_edges if k not in old_edges]
    result.removed_edges = [old_edges[k] for k in old_edges if k not in new_edges]

    # Community changes
    old_comms: dict[int, list] = defaultdict(list)
    new_comms: dict[int, list] = defaultdict(list)
    for n in old.get("nodes", []):
        cid = n.get("community")
        if cid is not None:
            old_comms[cid].append(n)
    for n in new.get("nodes", []):
        cid = n.get("community")
        if cid is not None:
            new_comms[cid].append(n)

    old_comm_ids = set(old_comms.keys())
    new_comm_ids = set(new_comms.keys())

    for cid in new_comm_ids - old_comm_ids:
        nodes = new_comms[cid]
        result.new_communities.append({
            "id": cid,
            "name": nodes[0].get("community_name", f"Community {cid}"),
            "node_count": len(nodes),
        })

    for cid in old_comm_ids - new_comm_ids:
        nodes = old_comms[cid]
        result.removed_communities.append({
            "id": cid,
            "name": nodes[0].get("community_name", f"Community {cid}"),
            "node_count": len(nodes),
        })

    for cid in old_comm_ids & new_comm_ids:
        old_size = len(old_comms[cid])
        new_size = len(new_comms[cid])
        delta = new_size - old_size
        if delta > 2:
            result.grown_communities.append({
                "id": cid,
                "name": new_comms[cid][0].get("community_name", f"Community {cid}"),
                "old_size": old_size,
                "new_size": new_size,
                "delta": delta,
            })
        elif delta < -2:
            result.shrunk_communities.append({
                "id": cid,
                "name": old_comms[cid][0].get("community_name", f"Community {cid}"),
                "old_size": old_size,
                "new_size": new_size,
                "delta": delta,
            })

    # God node changes
    old_gods = {g["id"]: g for g in get_god_nodes(old)}
    new_gods = {g["id"]: g for g in get_god_nodes(new)}

    result.new_god_nodes = [new_gods[id] for id in new_gods if id not in old_gods]
    result.demoted_god_nodes = [old_gods[id] for id in old_gods if id not in new_gods]

    # Stats
    result.old_stats = {
        "nodes": len(old.get("nodes", [])),
        "edges": len(old.get("links", [])),
        "communities": len(old_comms),
    }
    result.new_stats = {
        "nodes": len(new.get("nodes", [])),
        "edges": len(new.get("links", [])),
        "communities": len(new_comms),
    }
    result.deltas = {
        "nodes": result.new_stats["nodes"] - result.old_stats["nodes"],
        "edges": result.new_stats["edges"] - result.old_stats["edges"],
        "communities": result.new_stats["communities"] - result.old_stats["communities"],
    }

    return result


def emit_diff_report(result: DiffResult, old_path: str, new_path: str) -> str:
    lines = [
        "# 📐 Graph Diff Report",
        "",
        f"**Old:** `{old_path}` ({result.old_stats['nodes']:,} nodes, {result.old_stats['edges']:,} edges)",
        f"**New:** `{new_path}` ({result.new_stats['nodes']:,} nodes, {result.new_stats['edges']:,} edges)",
        "",
        "## Summary",
        "",
        "| Metric | Old | New | Delta |",
        "|--------|-----|-----|-------|",
    ]

    for metric in ["nodes", "edges", "communities"]:
        old_v = result.old_stats[metric]
        new_v = result.new_stats[metric]
        delta = result.deltas[metric]
        sign = "+" if delta > 0 else ""
        lines.append(f"| {metric.capitalize()} | {old_v:,} | {new_v:,} | {sign}{delta} |")

    lines.append("")

    # Added/removed nodes
    if result.added_nodes:
        lines.append(f"## ➕ Added Nodes ({len(result.added_nodes)})")
        lines.append("")
        lines.append("New code added since the last snapshot:")
        lines.append("")
        lines.append("| Node | Type | Community | Source |")
        lines.append("|------|------|-----------|--------|")
        for n in result.added_nodes[:20]:
            lines.append(f"| `{n.get('label', '?')}` | {n.get('file_type', '?')} | {n.get('community_name', '?')} | `{n.get('source_file', '?')}` |")
        if len(result.added_nodes) > 20:
            lines.append(f"| _... and {len(result.added_nodes) - 20} more_ | | | |")
        lines.append("")

    if result.removed_nodes:
        lines.append(f"## ➖ Removed Nodes ({len(result.removed_nodes)})")
        lines.append("")
        lines.append("Code that was deleted since the last snapshot:")
        lines.append("")
        lines.append("| Node | Type | Community | Source |")
        lines.append("|------|------|-----------|--------|")
        for n in result.removed_nodes[:20]:
            lines.append(f"| `{n.get('label', '?')}` | {n.get('file_type', '?')} | {n.get('community_name', '?')} | `{n.get('source_file', '?')}` |")
        if len(result.removed_nodes) > 20:
            lines.append(f"| _... and {len(result.removed_nodes) - 20} more_ | | | |")
        lines.append("")

    # Edge changes
    if result.added_edges:
        lines.append(f"## 🔗 New Connections ({len(result.added_edges)})")
        lines.append("")
        lines.append("| From | Relation | To |")
        lines.append("|------|----------|-----|")
        # Resolve node labels
        for e in result.added_edges[:15]:
            lines.append(f"| `{e.get('source', '?')[:40]}` | {e.get('relation', '?')} | `{e.get('target', '?')[:40]}` |")
        if len(result.added_edges) > 15:
            lines.append(f"| _... and {len(result.added_edges) - 15} more_ | | |")
        lines.append("")

    if result.removed_edges:
        lines.append(f"## ✂️ Removed Connections ({len(result.removed_edges)})")
        lines.append("")
        lines.append("Connections that no longer exist:")
        lines.append("")
        lines.append("| From | Relation | To |")
        lines.append("|------|----------|-----|")
        for e in result.removed_edges[:15]:
            lines.append(f"| `{e.get('source', '?')[:40]}` | {e.get('relation', '?')} | `{e.get('target', '?')[:40]}` |")
        if len(result.removed_edges) > 15:
            lines.append(f"| _... and {len(result.removed_edges) - 15} more_ | | |")
        lines.append("")

    # Community changes
    if result.new_communities or result.removed_communities or result.grown_communities or result.shrunk_communities:
        lines.append("## 🏘️ Community Changes")
        lines.append("")

        if result.new_communities:
            lines.append("### New Communities")
            lines.append("")
            for c in result.new_communities[:10]:
                lines.append(f"- **{c['name']}** ({c['node_count']} nodes)")
            lines.append("")

        if result.removed_communities:
            lines.append("### Removed Communities")
            lines.append("")
            for c in result.removed_communities[:10]:
                lines.append(f"- **{c['name']}** (was {c['node_count']} nodes)")
            lines.append("")

        if result.grown_communities:
            lines.append("### Grown Communities")
            lines.append("")
            lines.append("| Community | Old | New | Growth |")
            lines.append("|-----------|-----|-----|--------|")
            for c in sorted(result.grown_communities, key=lambda x: -x["delta"])[:10]:
                lines.append(f"| {c['name']} | {c['old_size']} | {c['new_size']} | +{c['delta']} |")
            lines.append("")

        if result.shrunk_communities:
            lines.append("### Shrunk Communities")
            lines.append("")
            lines.append("| Community | Old | New | Shrink |")
            lines.append("|-----------|-----|-----|--------|")
            for c in sorted(result.shrunk_communities, key=lambda x: x["delta"])[:10]:
                lines.append(f"| {c['name']} | {c['old_size']} | {c['new_size']} | {c['delta']} |")
            lines.append("")

    # God node changes
    if result.new_god_nodes or result.demoted_god_nodes:
        lines.append("## 🏛️ God Node Changes")
        lines.append("")

        if result.new_god_nodes:
            lines.append("### 🆕 New God Nodes (entered top 20)")
            lines.append("")
            for g in result.new_god_nodes:
                lines.append(f"- `{g['label']}` — {g['degree']} connections ({g['community_name']})")
            lines.append("")

        if result.demoted_god_nodes:
            lines.append("### 📉 Demoted God Nodes (left top 20)")
            lines.append("")
            for g in result.demoted_god_nodes:
                lines.append(f"- `{g['label']}` — was {g['degree']} connections ({g['community_name']})")
            lines.append("")

    # Insights
    lines.append("## 💡 Insights")
    lines.append("")

    node_delta = result.deltas["nodes"]
    edge_delta = result.deltas["edges"]

    if node_delta > 50:
        lines.append(f"- 📈 **Significant growth**: +{node_delta} nodes — the codebase is expanding rapidly")
    elif node_delta < -20:
        lines.append(f"- 📉 **Code reduction**: {node_delta} nodes removed — cleanup or feature removal?")
    elif abs(node_delta) <= 5:
        lines.append(f"- ➡️ **Stable**: node count changed by only {node_delta}")

    if len(result.added_edges) > len(result.removed_edges) * 2:
        lines.append(f"- 🔗 **Increasing coupling**: {len(result.added_edges)} new connections vs {len(result.removed_edges)} removed")
    elif len(result.removed_edges) > len(result.added_edges) * 2:
        lines.append(f"- ✂️ **Decoupling**: {len(result.removed_edges)} connections removed vs {len(result.added_edges)} added")

    if result.new_god_nodes:
        lines.append(f"- 🏛️ **Architecture shift**: {len(result.new_god_nodes)} new god node(s) — new central abstractions emerging")

    if not result.added_nodes and not result.removed_nodes:
        lines.append("- ✅ **No structural changes** — the codebase is identical between snapshots")

    lines.append("")

    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(
        prog="graphify diff",
        description="Compare two graph.json snapshots to see structural changes.",
    )
    ap.add_argument("old", help="Path to old graph.json")
    ap.add_argument("new", help="Path to new graph.json")
    ap.add_argument("--out", "-o", help="Output file (default: stdout)")
    ap.add_argument("--json", action="store_true", help="Output as JSON")
    args = ap.parse_args()

    old = load_graph(args.old)
    new = load_graph(args.new)

    print(f"graphify diff — comparing {args.old} vs {args.new}", file=sys.stderr)

    result = diff_graphs(old, new)

    if args.json:
        output = json.dumps({
            "old_stats": result.old_stats,
            "new_stats": result.new_stats,
            "deltas": result.deltas,
            "added_nodes": len(result.added_nodes),
            "removed_nodes": len(result.removed_nodes),
            "added_edges": len(result.added_edges),
            "removed_edges": len(result.removed_edges),
            "new_communities": result.new_communities,
            "removed_communities": result.removed_communities,
            "grown_communities": result.grown_communities,
            "shrunk_communities": result.shrunk_communities,
            "new_god_nodes": result.new_god_nodes,
            "demoted_god_nodes": result.demoted_god_nodes,
        }, indent=2)
    else:
        output = emit_diff_report(result, args.old, args.new)

    if args.out:
        Path(args.out).write_text(output, encoding="utf-8")
        print(f"Report written to {args.out}", file=sys.stderr)
    else:
        print(output)

    print(f"\nDelta: {result.deltas['nodes']:+d} nodes, {result.deltas['edges']:+d} edges", file=sys.stderr)


if __name__ == "__main__":
    main()
