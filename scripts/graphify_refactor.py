#!/usr/bin/env python3
"""graphify refactor — suggest safe refactoring targets.

Analyzes the codebase graph to identify:
  1. Safe refactoring candidates — high out-degree, low in-degree (called by few, calls many)
  2. Dangerous refactoring targets — high in-degree (called by many, change ripples widely)
  3. God node candidates for splitting — very high degree with multiple community bridges
  4. Dead code to remove — degree 0 with source file
  5. Coupling smells — nodes that bridge many communities (should be split)

Usage:
  python graphify_refactor.py [path] [--out report.md]
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class RefactorCandidate:
    name: str
    file: str
    community: str
    in_degree: int
    out_degree: int
    total_degree: int
    communities_bridged: int
    recommendation: str  # SPLIT, EXTRACT, SAFE_TO_REFACT, DANGEROUS, DELETE
    reason: str
    priority: int  # 1 (highest) to 5 (lowest)


def analyze_refactoring_targets(repo: Path) -> list[RefactorCandidate]:
    """Analyze the graph for refactoring opportunities."""
    graph_path = repo / "graphify-out" / "graph.json"
    if not graph_path.exists():
        print("ERROR: graph.json not found. Run graphify extract first.", file=sys.stderr)
        return []

    graph = json.loads(graph_path.read_text(encoding="utf-8"))
    nodes = graph.get("nodes", [])
    edges = graph.get("links", [])

    # Compute in-degree (how many nodes call/reference this) and out-degree (how many this calls)
    in_degree: Counter = Counter()
    out_degree: Counter = Counter()
    node_communities: dict[str, set] = defaultdict(set)

    for e in edges:
        source = e.get("source", "")
        target = e.get("target", "")
        relation = e.get("relation", "")

        if relation in ("calls", "references", "uses", "imports"):
            out_degree[source] += 1
            in_degree[target] += 1

        # Track community bridges
        sn = next((n for n in nodes if n.get("id") == source), None)
        tn = next((n for n in nodes if n.get("id") == target), None)
        if sn and tn:
            sc = sn.get("community")
            tc = tn.get("community")
            if sc is not None and tc is not None and sc != tc:
                node_communities[source].add(tc)
                node_communities[target].add(sc)

    # Build candidates
    candidates: list[RefactorCandidate] = []

    for node in nodes:
        nid = node.get("id", "")
        label = node.get("label", "")
        src = node.get("source_file", "")
        community = node.get("community_name", "")
        
        in_d = in_degree.get(nid, 0)
        out_d = out_degree.get(nid, 0)
        total_d = in_d + out_d
        bridged = len(node_communities.get(nid, set()))

        # Skip file-level nodes and built-in types
        if not src or src.endswith((".go.mod", "package.json")):
            continue
        if label in ("T", "Context", "Request", "ResponseWriter", "ObjectID", "Time", "MongoDB", "Collection"):
            continue

        # Determine recommendation
        recommendation = ""
        reason = ""
        priority = 5

        if total_d == 0:
            # Dead code
            recommendation = "DELETE"
            reason = "No connections — genuinely dead code (verified by grep in digest)"
            priority = 4

        elif total_d >= 50 and bridged >= 3:
            # God node that bridges communities — split it
            recommendation = "SPLIT"
            reason = f"High degree ({total_d}) and bridges {bridged} communities — split into smaller, community-specific functions"
            priority = 1

        elif in_d >= 30:
            # Called by many — dangerous to change
            recommendation = "DANGEROUS"
            reason = f"Called by {in_d} other nodes — any change ripples widely. Refactor only with full test coverage"
            priority = 2

        elif out_d >= 10 and in_d <= 2:
            # Calls many, called by few — safe to refactor, good extraction candidate
            recommendation = "SAFE_TO_REFACT"
            reason = f"High out-degree ({out_d}) but low in-degree ({in_d}) — safe to refactor, few callers to update"
            priority = 3

        elif out_d >= 5 and in_d <= 1:
            # Good extraction candidate
            recommendation = "EXTRACT"
            reason = f"Calls {out_d} nodes but is only called by {in_d} — extract logic into smaller helpers"
            priority = 3

        elif bridged >= 5 and total_d >= 20:
            # Coupling smell — connects too many communities
            recommendation = "SPLIT"
            reason = f"Bridges {bridged} communities — this node couples unrelated subsystems. Split or use an interface"
            priority = 2

        elif total_d >= 20 and in_d >= 10:
            # Hub node — moderate risk
            recommendation = "DANGEROUS"
            reason = f"Hub node ({total_d} connections, {in_d} incoming) — high blast radius. Add tests before refactoring"
            priority = 3

        if recommendation:
            candidates.append(RefactorCandidate(
                name=label, file=src, community=community,
                in_degree=in_d, out_degree=out_d, total_degree=total_d,
                communities_bridged=bridged,
                recommendation=recommendation, reason=reason,
                priority=priority,
            ))

    # Sort by priority, then by total degree
    candidates.sort(key=lambda x: (x.priority, -x.total_degree))
    return candidates


def emit_refactor_report(candidates: list[RefactorCandidate], repo: Path) -> str:
    lines = [
        f"# 🔧 Refactoring Recommendations — {repo.name}",
        "",
        f"**Found {len(candidates)} refactoring target(s).**",
        "",
    ]

    if not candidates:
        lines.append("✅ No refactoring targets found — the codebase looks well-structured.")
        return "\n".join(lines)

    # Group by recommendation
    by_rec: dict[str, list[RefactorCandidate]] = defaultdict(list)
    for c in candidates:
        by_rec[c.recommendation].append(c)

    rec_order = [
        ("SPLIT", "🔴 Split (God Nodes)", "These nodes have too many connections and bridge multiple communities. Split them into smaller, focused functions."),
        ("DANGEROUS", "⚠️ Dangerous to Refactor", "These nodes are called by many others. Any change ripples widely. Only refactor with full test coverage."),
        ("SAFE_TO_REFACT", "🟢 Safe to Refactor", "These nodes call many things but are called by few. Safe to refactor — few callers to update."),
        ("EXTRACT", "💡 Extraction Candidates", "These nodes have high out-degree but low in-degree — good candidates for extracting logic into helpers."),
        ("DELETE", "🗑️ Dead Code", "No connections — safe to delete."),
    ]

    # Summary
    lines.append("## Summary")
    lines.append("")
    lines.append("| Recommendation | Count | Priority |")
    lines.append("|----------------|-------|----------|")
    for rec, title, _ in rec_order:
        items = by_rec.get(rec, [])
        if items:
            icon = rec[0]  # S, D, S, E, D
            lines.append(f"| {title} | {len(items)} | P{items[0].priority} |")
    lines.append("")

    # Details
    for rec, title, desc in rec_order:
        items = by_rec.get(rec, [])
        if not items:
            continue

        lines.append(f"## {title} ({len(items)})")
        lines.append("")
        lines.append(desc)
        lines.append("")
        lines.append("| Symbol | In° | Out° | Total | Bridges | File | Reason |")
        lines.append("|--------|-----|------|-------|---------|------|--------|")
        for c in items[:15]:
            lines.append(f"| `{c.name}` | {c.in_degree} | {c.out_degree} | {c.total_degree} | {c.communities_bridged} | `{c.file}` | {c.reason} |")
        if len(items) > 15:
            lines.append(f"| _... and {len(items) - 15} more_ | | | | | | |")
        lines.append("")

    # Action plan
    lines.append("## 📋 Action Plan")
    lines.append("")
    lines.append("### Priority 1: Split God Nodes")
    split = by_rec.get("SPLIT", [])
    if split:
        for c in split[:5]:
            lines.append(f"- [ ] Split `{c.name}` ({c.total_degree} connections, bridges {c.communities_bridged} communities)")
            lines.append(f"  - File: `{c.file}`")
            lines.append(f"  - Strategy: Extract community-specific logic into separate functions")
            lines.append(f"  - Verify: Run `graphify verify` after refactoring")
    lines.append("")

    lines.append("### Priority 2: Add Tests Before Refactoring Hubs")
    dangerous = by_rec.get("DANGEROUS", [])
    if dangerous:
        for c in dangerous[:5]:
            lines.append(f"- [ ] Add tests for `{c.name}` ({c.in_degree} incoming calls) before any refactoring")
    lines.append("")

    lines.append("### Priority 3: Refactor Safe Targets")
    safe = by_rec.get("SAFE_TO_REFACT", []) + by_rec.get("EXTRACT", [])
    if safe:
        for c in safe[:5]:
            lines.append(f"- [ ] Refactor `{c.name}` — safe (only {c.in_degree} caller(s))")
    lines.append("")

    lines.append("### Priority 4: Remove Dead Code")
    dead = by_rec.get("DELETE", [])
    if dead:
        for c in dead[:5]:
            lines.append(f"- [ ] Delete `{c.name}` — `{c.file}`")
    lines.append("")

    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(prog="graphify refactor", description="Suggest safe refactoring targets.")
    ap.add_argument("path", nargs="?", default=".", help="Path to the repo")
    ap.add_argument("--out", "-o", help="Output file")
    ap.add_argument("--json", action="store_true", help="Output as JSON")
    args = ap.parse_args()

    repo = Path(args.path).resolve()
    print(f"graphify refactor — analyzing {repo}", file=sys.stderr)

    candidates = analyze_refactoring_targets(repo)
    print(f"  Found {len(candidates)} refactoring targets", file=sys.stderr)

    if args.json:
        output = json.dumps([{
            "name": c.name, "file": c.file, "community": c.community,
            "in_degree": c.in_degree, "out_degree": c.out_degree,
            "total_degree": c.total_degree, "communities_bridged": c.communities_bridged,
            "recommendation": c.recommendation, "reason": c.reason, "priority": c.priority,
        } for c in candidates], indent=2)
    else:
        output = emit_refactor_report(candidates, repo)

    if args.out:
        Path(args.out).write_text(output, encoding="utf-8")
        print(f"Report written to {args.out}", file=sys.stderr)
    else:
        print(output)

    by_rec = defaultdict(int)
    for c in candidates:
        by_rec[c.recommendation] += 1
    print(f"\n{dict(by_rec)}", file=sys.stderr)


if __name__ == "__main__":
    main()
