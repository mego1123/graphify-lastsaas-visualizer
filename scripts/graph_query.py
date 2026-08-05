"""Shared helper for querying the enriched graphify graph.

All Python analysis tools use this instead of calling Go tools as subprocesses.
The graph must be enriched first: python graphify_enrich.py . --all
"""
import json
from pathlib import Path
from typing import Optional


def load_graph(repo: Path, warn_stale: bool = True) -> dict:
    """Load the enriched graph.json.
    
    If warn_stale is True, checks if the graph is stale (source files changed
    since enrichment) and prints a warning to stderr.
    """
    graph_path = repo / "graphify-out" / "graph.json"
    if not graph_path.exists():
        return {"nodes": [], "links": []}
    
    graph = json.loads(graph_path.read_text(encoding="utf-8"))
    
    # Staleness check
    if warn_stale and is_graph_enriched(graph):
        import sys
        import hashlib
        
        stored_hash = graph.get("graph", {}).get("enrichment_source_hash", {})
        stored_combined = stored_hash.get("_combined", "")
        
        if stored_combined:
            backend_dir = repo / "backend" if (repo / "backend").exists() else repo
            combined = hashlib.sha256()
            for go_file in sorted(backend_dir.rglob("*.go")):
                if "node_modules" in str(go_file) or "vendor" in str(go_file):
                    continue
                if "graphify-out" in str(go_file):
                    continue
                try:
                    combined.update(go_file.read_bytes())
                except Exception:
                    continue
            
            current_combined = combined.hexdigest()[:32]
            if stored_combined != current_combined:
                print(f"⚠️  WARNING: Enriched graph is STALE — source files changed since last enrichment.", file=sys.stderr)
                print(f"   Run: python scripts/graphify_enrich.py . --all", file=sys.stderr)
    
    return graph


def get_struct_fields(graph: dict, struct_name: str) -> set[str]:
    """Get all JSON field names for a struct, including embedded fields.
    
    Queries type_resolves_to edges in the enriched graph.
    Falls back to empty set if graph is not enriched.
    """
    # Find the struct definition node (in models/ directory, not a variable)
    struct_node = None
    for n in graph.get("nodes", []):
        if n.get("label") == struct_name and n.get("file_type") == "code":
            src = n.get("source_file", "")
            # Prefer the models/ definition, not variable declarations
            if "models/" in src or "types/" in src:
                struct_node = n
                break
    
    # Fallback: any node with this label
    if not struct_node:
        for n in graph.get("nodes", []):
            if n.get("label") == struct_name and n.get("file_type") == "code":
                struct_node = n
                break
    
    if not struct_node:
        return set()
    
    # Query type_resolves_to edges
    struct_id = struct_node["id"]
    fields = set()
    for edge in graph.get("links", []):
        if edge.get("source") == struct_id and edge.get("relation") == "type_resolves_to":
            field_node = next((n for n in graph["nodes"] if n["id"] == edge["target"]), None)
            if field_node:
                field_name = field_node.get("label", "")
                if field_name and field_name != "-":
                    fields.add(field_name)
    
    return fields


def get_function_filter_fields(graph: dict, function_name: str) -> set[str]:
    """Get all filter field names written by a function.
    
    Queries filter_writes_field edges in the enriched graph.
    Returns fields from both literal and dynamic (map_update) construction.
    """
    func_node = _find_function_node(graph, function_name)
    if not func_node:
        return set()

    func_id = func_node["id"]
    fields = set()
    for edge in graph.get("links", []):
        if edge.get("source") == func_id and edge.get("relation") == "filter_writes_field":
            field_node = next((n for n in graph["nodes"] if n["id"] == edge["target"]), None)
            if field_node:
                field_name = field_node.get("label", "")
                if field_name and field_name != "?":
                    fields.add(field_name)

    return fields


def is_graph_enriched(graph: dict) -> bool:
    """Check if the graph has been enriched with go/types + go/ssa data."""
    return graph.get("graph", {}).get("enriched", False)


def has_struct_field(graph: dict, struct_name: str, field_name: str) -> bool:
    """Check if a struct has a specific field (including embedded)."""
    return field_name in get_struct_fields(graph, struct_name)


def get_all_struct_names(graph: dict) -> list[str]:
    """Get all struct names that have type_resolves_to edges."""
    struct_ids = set()
    for edge in graph.get("links", []):
        if edge.get("relation") == "type_resolves_to":
            struct_ids.add(edge.get("source", ""))
    
    names = []
    for n in graph.get("nodes", []):
        if n.get("id") in struct_ids:
            names.append(n.get("label", ""))
    return sorted(set(names))


def _candidate_labels_for_function(function_name: str) -> list[str]:
    """Return all possible graph-label forms for a function name.

    Handles:
      - Plain functions: "cmdDoctor" → ["cmdDoctor", "cmdDoctor()", "cmddoctor", "cmddoctor()"]
      - Methods: "(*AdminHandler).ListTenants" → [".ListTenants()", ".ListTenants",
        "ListTenants", "ListTenants()", "listtenants", ".listtenants()"]
    """
    candidates = [function_name, function_name + "()", function_name.lower(), function_name.lower() + "()"]
    if ")." in function_name:
        idx = function_name.rfind(").")
        method = function_name[idx + 2:]
        if method:
            candidates.extend([
                f".{method}()",
                f".{method}",
                method,
                method + "()",
                method.lower(),
                f".{method.lower()}()",
            ])
    return candidates


def _find_function_node(graph: dict, function_name: str) -> dict | None:
    """Find a function node in the graph by name, with disambiguation.

    When multiple nodes share the same label (e.g., .ExchangeCode() exists
    on AuthHandler, GitHubOAuthService, GoogleOAuthService, MicrosoftOAuthService),
    disambiguate using the receiver type extracted from function_name.

    For "(*AuthHandler).ExchangeCode", prefers nodes whose id or source_file
    contains "authhandler" or "auth" (derived from the receiver type).
    """
    candidate_set = set(_candidate_labels_for_function(function_name))
    matches = [n for n in graph.get("nodes", []) if n.get("label", "") in candidate_set]
    if not matches:
        return None
    if len(matches) == 1:
        return matches[0]

    # Multiple matches — disambiguate by receiver type.
    # Extract receiver type from function_name like "(*AdminHandler).ListTenants"
    receiver_type = ""
    if ")." in function_name:
        idx = function_name.rfind(").")
        receiver_part = function_name[:idx + 1]  # e.g. "(*AdminHandler)"
        # Extract the type name (AdminHandler)
        import re
        m = re.search(r"\(\s*\*?\s*(\w+)\s*\)", receiver_part)
        if m:
            receiver_type = m.group(1)

    if receiver_type:
        # Try to find a node whose id or source_file contains the receiver type
        receiver_lower = receiver_type.lower()
        for n in matches:
            nid = n.get("id", "").lower()
            src = n.get("source_file", "").lower()
            if receiver_lower in nid or receiver_lower in src:
                return n

    # Fallback: first match
    return matches[0]


def get_function_filter_fields_with_confidence(graph: dict, function_name: str) -> dict[str, str]:
    """Get filter field names with their method/confidence level.
    
    Returns: {field_name: method} where method is:
    - "literal": static bson.M{"field": value} — high confidence
    - "map_update": dynamic filter["field"] = value — medium confidence
    - "struct_type": InsertOne(ctx, struct) — inferred from struct type
    """
    func_node = _find_function_node(graph, function_name)
    if not func_node:
        return {}

    func_id = func_node["id"]
    fields = {}
    for edge in graph.get("links", []):
        if edge.get("source") == func_id and edge.get("relation") == "filter_writes_field":
            field_node = next((n for n in graph["nodes"] if n["id"] == edge["target"]), None)
            if field_node:
                field_name = field_node.get("label", "")
                method = edge.get("method", "unknown")
                if field_name and field_name != "?":
                    fields[field_name] = method

    return fields


def is_filter_field_static(graph: dict, function_name: str, field_name: str) -> bool:
    """Check if a filter field is written via a static literal (high confidence)
    vs dynamic map_update (medium confidence).

    Returns True for:
    - "literal": static bson.M{"field": value} — high confidence, statically known
    - "struct_type": InsertOne(ctx, struct) — inferred from struct type's bson tags,
      which are compile-time constants (the struct definition doesn't change at runtime)

    Returns False for:
    - "map_update": dynamic filter["field"] = value — the field NAME is known but
      the VALUE is computed at runtime, so the filter shape is only partially static
    - "unknown" or missing: can't determine
    """
    fields = get_function_filter_fields_with_confidence(graph, function_name)
    method = fields.get(field_name, "")
    return method in ("literal", "struct_type")
