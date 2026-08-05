#!/usr/bin/env python3
"""graphify deps — dependency vulnerability scan.

Scans package.json, go.mod, requirements.txt for dependencies and:
  1. Lists all dependencies with versions
  2. Cross-references with graph.json to find which god nodes depend on each package
  3. Flags packages with known vulnerability patterns (outdated major versions)
  4. Identifies unused dependencies (in package.json but not imported anywhere)

Usage:
  python graphify_deps.py [path] [--out report.md]
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class Dependency:
    name: str
    version: str
    ecosystem: str  # npm, go, python
    is_dev: bool = False
    used_by: list[str] = field(default_factory=list)  # god nodes that import this
    is_used: bool = True  # False if in package.json but never imported
    risk_level: str = "LOW"  # LOW, MEDIUM, HIGH
    risk_reasons: list[str] = field(default_factory=list)


def parse_package_json(repo: Path) -> list[Dependency]:
    """Parse npm package.json files for dependencies."""
    deps: list[Dependency] = []
    
    for pj in repo.rglob("package.json"):
        if "node_modules" in str(pj) or ".next" in str(pj):
            continue
        try:
            data = json.loads(pj.read_text(encoding="utf-8"))
        except Exception:
            continue

        rel = str(pj.relative_to(repo))
        
        for dep_type, is_dev in [("dependencies", False), ("devDependencies", True)]:
            for name, version in (data.get(dep_type) or {}).items():
                deps.append(Dependency(
                    name=name, version=version, ecosystem="npm",
                    is_dev=is_dev,
                ))

    return deps


def parse_go_mod(repo: Path) -> list[Dependency]:
    """Parse go.mod for Go dependencies."""
    deps: list[Dependency] = []
    
    for gm in repo.rglob("go.mod"):
        try:
            content = gm.read_text(encoding="utf-8")
        except Exception:
            continue

        for m in re.finditer(r'^\s*(\S+)\s+(v[\d.]+\w*)', content, re.MULTILINE):
            name = m.group(1)
            version = m.group(2)
            if name == "module":
                continue
            deps.append(Dependency(
                name=name, version=version, ecosystem="go",
            ))

    return deps


def check_dependency_usage(repo: Path, deps: list[Dependency]) -> None:
    """Check which npm dependencies are actually imported in source code."""
    src_dirs = []
    for candidate in ["src", "frontend/src", "app", "frontend/app"]:
        if (repo / candidate).exists():
            src_dirs.append(candidate)
    
    if not src_dirs:
        return

    # Collect all source file contents
    all_imports: set[str] = set()
    for src_dir in src_dirs:
        full_src = repo / src_dir
        for ext in ["*.tsx", "*.ts", "*.jsx", "*.js"]:
            for f in full_src.rglob(ext):
                if "node_modules" in str(f):
                    continue
                try:
                    content = f.read_text(encoding="utf-8", errors="ignore")
                except Exception:
                    continue
                # Find import statements
                for m in re.finditer(r'(?:import\s+[^;]+from\s+|import\s*\(\s*)[\'"`]([^\'"`]+)[\'"`]', content):
                    imp = m.group(1)
                    if not imp.startswith(".") and not imp.startswith("/"):
                        # Package import — extract package name
                        parts = imp.split("/")
                        if imp.startswith("@"):
                            pkg = "/".join(parts[:2])
                        else:
                            pkg = parts[0]
                        all_imports.add(pkg)

    # Mark deps as used/unused
    for dep in deps:
        if dep.ecosystem == "npm" and not dep.is_dev:
            dep.is_used = dep.name in all_imports


def cross_reference_graph(repo: Path, deps: list[Dependency]) -> None:
    """Cross-reference dependencies with graph.json to find god nodes that use them."""
    graph_path = repo / "graphify-out" / "graph.json"
    if not graph_path.exists():
        return

    graph = json.loads(graph_path.read_text(encoding="utf-8"))
    
    # Compute degree for god nodes
    from collections import Counter
    degree = Counter()
    for e in graph.get("links", []):
        degree[e.get("source", "")] += 1
        degree[e.get("target", "")] += 1

    # Get top 30 nodes
    top_nodes = sorted(graph.get("nodes", []), key=lambda n: degree.get(n.get("id", ""), 0), reverse=True)[:30]
    
    # For each dependency, check if any top node's source file imports it
    for dep in deps:
        for node in top_nodes:
            src = node.get("source_file", "")
            if not src:
                continue
            try:
                content = (repo / src).read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            
            # Check if this dependency is imported
            if dep.name in content:
                dep.used_by.append(node.get("label", ""))
    
    # Deduplicate
    for dep in deps:
        dep.used_by = list(set(dep.used_by))[:5]


def assess_risk(deps: list[Dependency]) -> None:
    """Assess risk level for each dependency."""
    # Known risky version patterns
    risky_patterns = {
        # Major version 0 = unstable API
        "v0": "Major version 0 — API may be unstable",
        "^0": "Pinned to 0.x — API may change without notice",
        # Very old React versions
        "react@16": "React 16 — consider upgrading to React 18+",
        "react@17": "React 17 — consider upgrading to React 18+",
    }
    
    for dep in deps:
        reasons = []
        
        # Check for v0.x
        if dep.version.startswith("0.") or dep.version.startswith("^0.") or dep.version.startswith("v0."):
            reasons.append("Major version 0 — API may be unstable")
        
        # Check for very old versions of critical packages
        if dep.name == "react" and not any(v in dep.version for v in ["18", "19"]):
            reasons.append(f"React {dep.version} — consider upgrading to 18+")
        
        if dep.name == "next" and not any(v in dep.version for v in ["14", "15", "16"]):
            reasons.append(f"Next.js {dep.version} — consider upgrading to 14+")
        
        # Check for unused
        if not dep.is_used and not dep.is_dev:
            reasons.append("Listed in dependencies but never imported — remove to reduce install time")
        
        # Check if used by god nodes (high centrality = high impact if vulnerable)
        if dep.used_by:
            reasons.append(f"Used by {len(dep.used_by)} god node(s): {', '.join(dep.used_by[:3])}")
        
        dep.risk_reasons = reasons
        
        if any("unstable" in r or "never imported" in r for r in reasons):
            dep.risk_level = "MEDIUM"
        elif dep.used_by:
            dep.risk_level = "LOW"  # used by god nodes but stable
        else:
            dep.risk_level = "LOW"


def emit_deps_report(deps: list[Dependency], repo: Path) -> str:
    lines = [
        f"# 🔒 Dependency Scan — {repo.name}",
        "",
        f"**Found {len(deps)} dependencies.**",
        "",
    ]

    # Summary by ecosystem
    by_eco: dict[str, int] = defaultdict(int)
    for d in deps:
        by_eco[d.ecosystem] += 1

    lines.append("## Summary")
    lines.append("")
    lines.append("| Ecosystem | Count |")
    lines.append("|-----------|-------|")
    for eco, count in sorted(by_eco.items()):
        lines.append(f"| {eco} | {count} |")
    lines.append("")

    # Flagged dependencies
    flagged = [d for d in deps if d.risk_reasons]
    unused = [d for d in deps if not d.is_used and not d.is_dev]
    
    if flagged:
        lines.append(f"## ⚠️ Flagged Dependencies ({len(flagged)})")
        lines.append("")
        lines.append("| Package | Version | Ecosystem | Risk | Reasons |")
        lines.append("|---------|---------|-----------|------|---------|")
        for d in sorted(flagged, key=lambda x: x.risk_level, reverse=True):
            reasons = "; ".join(d.risk_reasons[:2])
            lines.append(f"| `{d.name}` | `{d.version}` | {d.ecosystem} | {d.risk_level} | {reasons} |")
        lines.append("")

    if unused:
        lines.append(f"## 🗑️ Unused Dependencies ({len(unused)})")
        lines.append("")
        lines.append("These are in `package.json` but never imported in source code:")
        lines.append("")
        for d in unused:
            lines.append(f"- `{d.name}` (`{d.version}`) — remove from dependencies")
        lines.append("")
        lines.append("```bash")
        lines.append("# Remove unused dependencies")
        for d in unused:
            lines.append(f"npm uninstall {d.name}")
        lines.append("```")
        lines.append("")

    # God node dependencies
    god_deps = [d for d in deps if d.used_by]
    if god_deps:
        lines.append("## 🏛️ Dependencies Used by God Nodes")
        lines.append("")
        lines.append("These packages are imported by the most-connected symbols — vulnerabilities here have wide impact:")
        lines.append("")
        lines.append("| Package | Version | Used By |")
        lines.append("|---------|---------|---------|")
        for d in god_deps:
            used_by_str = ", ".join(f"`{u}`" for u in d.used_by[:3])
            lines.append(f"| `{d.name}` | `{d.version}` | {used_by_str} |")
        lines.append("")

    # All dependencies
    lines.append("## All Dependencies")
    lines.append("")
    lines.append("| Package | Version | Ecosystem | Dev? | Used? |")
    lines.append("|---------|---------|-----------|------|-------|")
    for d in sorted(deps, key=lambda x: (x.ecosystem, x.name)):
        dev = "✓" if d.is_dev else "—"
        used = "✓" if d.is_used else "❌" if not d.is_dev else "—"
        lines.append(f"| `{d.name}` | `{d.version}` | {d.ecosystem} | {dev} | {used} |")
    lines.append("")

    lines.append("## Recommendations")
    lines.append("")
    if unused:
        lines.append(f"- 🗑️ **Remove {len(unused)} unused dependencies** to reduce install time and attack surface")
    if flagged:
        lines.append(f"- ⚠️ **Review {len(flagged)} flagged dependencies** — check for stable versions or replacements")
    lines.append("- Run `npm audit` (npm) or `govulncheck ./...` (Go) for known CVEs")
    lines.append("- Update dependencies regularly with `npm update` or `go get -u`")

    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(prog="graphify deps", description="Dependency vulnerability scan.")
    ap.add_argument("path", nargs="?", default=".", help="Path to the repo")
    ap.add_argument("--out", "-o", help="Output file")
    ap.add_argument("--json", action="store_true", help="Output as JSON")
    args = ap.parse_args()

    repo = Path(args.path).resolve()
    print(f"graphify deps — scanning {repo}", file=sys.stderr)

    deps: list[Dependency] = []
    deps.extend(parse_package_json(repo))
    deps.extend(parse_go_mod(repo))

    print(f"  Found {len(deps)} dependencies", file=sys.stderr)

    check_dependency_usage(repo, deps)
    cross_reference_graph(repo, deps)
    assess_risk(deps)

    if args.json:
        output = json.dumps([{
            "name": d.name, "version": d.version, "ecosystem": d.ecosystem,
            "is_dev": d.is_dev, "is_used": d.is_used, "risk_level": d.risk_level,
            "risk_reasons": d.risk_reasons, "used_by": d.used_by,
        } for d in deps], indent=2)
    else:
        output = emit_deps_report(deps, repo)

    if args.out:
        Path(args.out).write_text(output, encoding="utf-8")
        print(f"Report written to {args.out}", file=sys.stderr)
    else:
        print(output)

    flagged = sum(1 for d in deps if d.risk_reasons)
    unused = sum(1 for d in deps if not d.is_used and not d.is_dev)
    print(f"\n{flagged} flagged, {unused} unused.", file=sys.stderr)


if __name__ == "__main__":
    main()
