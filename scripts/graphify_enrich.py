#!/usr/bin/env python3
"""graphify enrich — Phase 2: ingest go/types + go/ssa data into graph.json.

Runs the Go struct flattener and filter tracer, then adds their output
as new nodes and edges in the existing graph.json:

New node types:
  - type_field: a resolved struct field (e.g., "seatQuantity" from embedded Tenant)
  - filter_field: a dynamically-traced filter field (e.g., "tenantId" from bson.M var)

New edge types:
  - type_resolves_to: struct node → field node (struct HAS this field, including embedded)
  - filter_writes_field: function node → field node (function writes this field to a filter)

This makes the type and filter data available to all Python analyzers
via graph queries instead of subprocess calls.

Usage:
  python graphify_enrich.py [path] [--types] [--ssa] [--all]
  python graphify_enrich.py . --all         # run both enrichment passes
  python graphify_enrich.py . --types       # only struct flattener
  python graphify_enrich.py . --ssa         # only filter tracer
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


GO_STRUCT_FLATTENER = Path(__file__).parent / "go" / "graphify_struct_flattener" / "main.go"
GO_FILTER_TRACER = Path(__file__).parent / "go" / "graphify_filter_tracer" / "main.go"


def run_go_tool(go_file: Path, backend_dir: Path, output_path: Path) -> dict:
    """Run a Go tool and return its JSON output."""
    env = os.environ.copy()
    # Find Go binary
    go_bin = None
    for candidate in ["/home/z/.local/go/bin/go", "go"]:
        try:
            result = subprocess.run([candidate, "version"], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                go_bin = candidate
                break
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue

    if not go_bin:
        print("ERROR: Go not found. Set PATH to include go binary.", file=sys.stderr)
        sys.exit(2)

    env["GOTOOLCHAIN"] = "auto"
    env["PATH"] = f"/home/z/.local/go/bin:{env.get('PATH', '')}"

    print(f"  Running {go_file.name}...", file=sys.stderr)
    result = subprocess.run(
        [go_bin, "run", str(go_file), "-out", str(output_path)],
        cwd=str(backend_dir),
        capture_output=True,
        text=True,
        timeout=300,
        env=env,
    )

    if result.returncode != 0:
        print(f"  ERROR: {go_file.name} failed: {result.stderr[:300]}", file=sys.stderr)
        return {}

    if not output_path.exists():
        print(f"  ERROR: {go_file.name} produced no output", file=sys.stderr)
        return {}

    return json.loads(output_path.read_text(encoding="utf-8"))


def enrich_with_types(graph: dict, structs: list[dict], repo: Path) -> dict:
    """Add type_resolves_to edges from struct nodes to field nodes.

    For each struct in the Go code:
    1. Find the corresponding node in the graph (by label match)
    2. For each field (including embedded/resolved), create a type_field node
    3. Add a type_resolves_to edge from struct node → field node
    """
    nodes = graph.get("nodes", [])
    links = graph.get("links", [])

    # Build lookup: struct name → graph node ID
    # Try multiple match strategies
    node_by_label: dict[str, str] = {}
    node_by_label_lower: dict[str, str] = {}
    for n in nodes:
        label = n.get("label", "")
        nid = n.get("id", "")
        node_by_label[label] = nid
        node_by_label_lower[label.lower()] = nid

    new_nodes = []
    new_links = []

    for struct in structs:
        struct_name = struct.get("name", "")
        struct_file = struct.get("file", "")

        # Find the graph node for this struct
        # Strategy 1: match by label AND source_file (most precise)
        struct_node_id = None
        if struct_file:
            for n in nodes:
                if n.get("label") == struct_name and n.get("file_type") == "code":
                    src = n.get("source_file", "")
                    if struct_file in src:
                        struct_node_id = n.get("id", "")
                        break

        # Strategy 2: match by label only (fallback — first node with this label)
        if not struct_node_id:
            for n in nodes:
                if n.get("label") == struct_name and n.get("file_type") == "code":
                    struct_node_id = n.get("id", "")
                    break

        if not struct_node_id:
            continue  # Struct not in graph (maybe a local type or unused)

        for field in struct.get("fields", []):
            json_name = field.get("jsonName", "")
            bson_name = field.get("bsonName", "")
            field_name = field.get("name", "")
            field_type = field.get("type", "")
            embedded = field.get("embedded", False)

            if not json_name or json_name == "-":
                continue  # Skip unexported/hidden fields

            # Create a unique field node ID
            field_node_id = f"type_field_{struct_name}_{json_name}"

            # Check if we already have this field node (idempotent)
            if any(n.get("id") == field_node_id for n in new_nodes):
                # Already created — just add another edge if struct is different
                pass
            else:
                new_nodes.append({
                    "id": field_node_id,
                    "label": json_name,
                    "file_type": "type_field",
                    "source_file": struct_file,
                    "source_location": "",
                    "_origin": "go_types",
                    "field_name": field_name,
                    "field_json_name": json_name,
                    "field_bson_name": bson_name,
                    "field_type": field_type,
                    "field_embedded": embedded,
                    "parent_struct": struct_name,
                })

            # Add edge: struct → field
            new_links.append({
                "source": struct_node_id,
                "target": field_node_id,
                "relation": "type_resolves_to",
                "confidence": "EXTRACTED",
                "_origin": "go_types",
                "source_file": struct_file,
                "weight": 1.0,
            })

    graph["nodes"].extend(new_nodes)
    graph["links"].extend(new_links)

    print(f"  Types: added {len(new_nodes)} field nodes, {len(new_links)} type_resolves_to edges", file=sys.stderr)
    return graph


def enrich_with_ssa(graph: dict, functions: list[dict], repo: Path) -> dict:
    """Add filter_writes_field edges from function nodes to field nodes.

    For each function with filter findings:
    1. Find the corresponding function node in the graph
    2. For each filter field found, create a filter_field node (if not exists)
    3. Add a filter_writes_field edge from function node → field node
    """
    nodes = graph.get("nodes", [])
    links = graph.get("links", [])

    # Build lookup: function name → graph node ID
    node_by_label: dict[str, str] = {}
    for n in nodes:
        label = n.get("label", "")
        nid = n.get("id", "")
        # Try exact match and () suffix match
        node_by_label[label] = nid
        node_by_label[label + "()"] = nid
        node_by_label[label.lower()] = nid

    new_nodes = []
    new_links = []
    seen_field_ids = set()

    for func in functions:
        func_name = func.get("function", "")
        func_file = func.get("file", "")
        func_line = func.get("line", 0)

        # Find the graph node for this function
        func_node_id = node_by_label.get(func_name) or node_by_label.get(func_name + "()") or node_by_label.get(func_name.lower())

        # Try matching by file + function name
        if not func_node_id:
            for n in nodes:
                src = n.get("source_file", "")
                if func_file and func_file in src:
                    label = n.get("label", "")
                    if label == func_name or label == func_name + "()":
                        func_node_id = n.get("id", "")
                        break

        if not func_node_id:
            continue

        for finding in func.get("findings", []):
            method = finding.get("method", "")
            operation = finding.get("operation", "")
            position = finding.get("position", "")
            fields = finding.get("fields", [])

            for field_name in fields:
                if not field_name or field_name == "?":
                    continue

                field_node_id = f"filter_field_{field_name}"

                if field_node_id not in seen_field_ids:
                    seen_field_ids.add(field_node_id)
                    new_nodes.append({
                        "id": field_node_id,
                        "label": field_name,
                        "file_type": "filter_field",
                        "source_file": "",
                        "source_location": "",
                        "_origin": "go_ssa",
                        "field_name": field_name,
                    })

                new_links.append({
                    "source": func_node_id,
                    "target": field_node_id,
                    "relation": "filter_writes_field",
                    "confidence": "EXTRACTED",
                    "_origin": "go_ssa",
                    "source_file": func_file,
                    "source_location": f"L{func_line}" if func_line else "",
                    "weight": 1.0,
                    "method": method,
                    "operation": operation,
                    "position": position,
                })

    graph["nodes"].extend(new_nodes)
    graph["links"].extend(new_links)

    print(f"  SSA: added {len(new_nodes)} field nodes, {len(new_links)} filter_writes_field edges", file=sys.stderr)
    return graph


def main():
    ap = argparse.ArgumentParser(
        prog="graphify enrich",
        description="Phase 2: Enrich graph.json with go/types + go/ssa data.",
    )
    ap.add_argument("path", nargs="?", default=".", help="Path to the repo")
    ap.add_argument("--types", action="store_true", help="Run go/types struct flattener enrichment")
    ap.add_argument("--ssa", action="store_true", help="Run go/ssa filter tracer enrichment")
    ap.add_argument("--all", action="store_true", help="Run both enrichment passes")
    args = ap.parse_args()

    repo = Path(args.path).resolve()
    backend_dir = repo / "backend" if (repo / "backend").exists() else repo
    graph_path = repo / "graphify-out" / "graph.json"

    if not graph_path.exists():
        print(f"ERROR: {graph_path} not found. Run graphify extract first.", file=sys.stderr)
        sys.exit(2)

    run_types = args.types or args.all
    run_ssa = args.ssa or args.all

    if not run_types and not run_ssa:
        print("Specify --types, --ssa, or --all", file=sys.stderr)
        sys.exit(2)

    print(f"graphify enrich — enriching {graph_path}", file=sys.stderr)

    # Load the existing graph
    graph = json.loads(graph_path.read_text(encoding="utf-8"))
    print(f"  Loaded graph: {len(graph['nodes'])} nodes, {len(graph['links'])} links", file=sys.stderr)

    # Remove existing enrichment nodes/edges (idempotent)
    before_nodes = len(graph["nodes"])
    before_links = len(graph["links"])
    graph["nodes"] = [n for n in graph["nodes"] if n.get("_origin") not in ("go_types", "go_ssa")]
    graph["links"] = [l for l in graph["links"] if l.get("_origin") not in ("go_types", "go_ssa")]
    removed_nodes = before_nodes - len(graph["nodes"])
    removed_links = before_links - len(graph["links"])
    if removed_nodes or removed_links:
        print(f"  Removed {removed_nodes} stale enrichment nodes, {removed_links} edges", file=sys.stderr)

    # Run enrichment passes
    if run_types:
        print("Running go/types enrichment...", file=sys.stderr)
        structs_output = Path("/tmp/graphify-structs.json")
        structs = run_go_tool(GO_STRUCT_FLATTENER, backend_dir, structs_output)
        if structs:
            graph = enrich_with_types(graph, structs, repo)

    if run_ssa:
        print("Running go/ssa enrichment...", file=sys.stderr)
        filters_output = Path("/tmp/graphify-filters.json")
        functions = run_go_tool(GO_FILTER_TRACER, backend_dir, filters_output)
        if functions:
            graph = enrich_with_ssa(graph, functions, repo)

    # Mark the graph as enriched
    if "graph" not in graph:
        graph["graph"] = {}
    graph["graph"]["enriched"] = True
    graph["graph"]["enrichment_passes"] = []
    if run_types:
        graph["graph"]["enrichment_passes"].append("go_types")
    if run_ssa:
        graph["graph"]["enrichment_passes"].append("go_ssa")

    # Save the enriched graph
    graph_path.write_text(json.dumps(graph), encoding="utf-8")
    print(f"\n  Enriched graph: {len(graph['nodes'])} nodes, {len(graph['links'])} links", file=sys.stderr)
    print(f"  Written to {graph_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
