#!/usr/bin/env python3
"""Issue 1 investigation: is map_update (8) under-counting dynamic filters?

Three sub-questions:
  A. How many findings from go-filters.json made it into the graph as edges?
     Broken down by method (literal / map_update / struct_type).
  B. For findings that DIDN'T make it: why? (function not in graph / empty field)
  C. For dynamic filter patterns in the Go source that the tracer might miss:
     - helper functions that mutate a filter param
     - loop-built filters (for k, v := range ...)
     - builder/chaining patterns
     Cross-check each against the graph.
"""
from __future__ import annotations
import json
import re
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path("/home/z/my-project/repos/lastsaas")
BACKEND = REPO / "backend"
GRAPH_PATH = REPO / "graphify-out" / "graph.json"
FILTERS_PATH = Path("/home/z/my-project/public/go-filters.json")


def load_graph() -> dict:
    return json.loads(GRAPH_PATH.read_text(encoding="utf-8"))


def load_filters() -> list[dict]:
    return json.loads(FILTERS_PATH.read_text(encoding="utf-8"))


def build_func_node_index(graph: dict) -> dict:
    """Map (function_name, file_substring) -> node_id, and function_name -> [node_ids]."""
    by_name = defaultdict(list)
    by_name_lower = defaultdict(list)
    for n in graph["nodes"]:
        label = n.get("label", "")
        if not label:
            continue
        by_name[label].append(n)
        by_name_lower[label.lower()].append(n)
    return {"exact": by_name, "lower": by_name_lower}


def find_func_node(func_name: str, func_file: str, index: dict) -> str | None:
    """Mirror graphify_enrich.py's lookup logic."""
    # Try exact name match
    candidates = index["exact"].get(func_name, [])
    if not candidates:
        candidates = index["exact"].get(func_name + "()", [])
    if not candidates:
        candidates = index["lower"].get(func_name.lower(), [])

    if not candidates:
        return None

    # Try matching by file
    if func_file:
        for n in candidates:
            src = n.get("source_file", "")
            if func_file in src:
                return n.get("id", "")
            # Also try with backend/ prefix
            if f"backend/{func_file}" in src:
                return n.get("id", "")

    # Fallback: first candidate
    return candidates[0].get("id", "")


def question_a_and_b():
    """How many findings made it to graph edges, and why are some dropped?"""
    print("=" * 70)
    print("QUESTION A+B: Finding-to-edge conversion breakdown")
    print("=" * 70)

    graph = load_graph()
    filters = load_filters()
    index = build_func_node_index(graph)

    # Count edges by method in graph
    graph_edges_by_method = Counter()
    for e in graph["links"]:
        if e.get("relation") == "filter_writes_field":
            graph_edges_by_method[e.get("method", "?")] += 1

    # Count findings by method in go-filters.json
    findings_by_method = Counter()
    findings_total_fields_by_method = Counter()  # expected edges if all converted
    dropped_no_func_node = Counter()
    dropped_no_field = Counter()
    converted = Counter()
    dropped_funcs = set()  # functions whose node wasn't found

    for func in filters:
        func_name = func.get("function", "")
        func_file = func.get("file", "")
        func_node_id = find_func_node(func_name, func_file, index)

        for finding in func.get("findings", []):
            method = finding.get("method", "?")
            findings_by_method[method] += 1
            fields = finding.get("fields", [])
            findings_total_fields_by_method[method] += len(fields)

            if not func_node_id:
                dropped_no_func_node[method] += 1
                dropped_funcs.add((func_name, func_file, method))
                continue

            # Count fields that would be dropped (empty or "?")
            valid_fields = [f for f in fields if f and f != "?"]
            dropped = len(fields) - len(valid_fields)
            if dropped > 0:
                dropped_no_field[method] += dropped

            converted[method] += len(valid_fields)

    print("\nFindings in go-filters.json (per finding):")
    for m, c in sorted(findings_by_method.items()):
        print(f"  {m}: {c} findings")

    print("\nExpected edges if all findings converted (per field):")
    for m, c in sorted(findings_total_fields_by_method.items()):
        print(f"  {m}: {c} field-edges")

    print("\nActual edges in enriched graph:")
    for m, c in sorted(graph_edges_by_method.items()):
        print(f"  {m}: {c} edges")

    print("\nConverted (function found + valid field):")
    for m, c in sorted(converted.items()):
        print(f"  {m}: {c} field-edges")

    print("\nDropped because function node not found in graph:")
    for m, c in sorted(dropped_no_func_node.items()):
        print(f"  {m}: {c} findings")

    print("\nDropped because field was empty or '?':")
    for m, c in sorted(dropped_no_field.items()):
        print(f"  {m}: {c} field-edges")

    print(f"\nFunctions whose node wasn't found in graph: {len(dropped_funcs)}")
    # Sample some
    by_method_dropped = defaultdict(list)
    for fn, f, m in dropped_funcs:
        by_method_dropped[m].append((fn, f))
    for m, items in sorted(by_method_dropped.items()):
        print(f"\n  Method '{m}' — {len(items)} functions missing from graph:")
        for fn, f in items[:10]:
            print(f"    {fn}  ({f})")
        if len(items) > 10:
            print(f"    ... and {len(items) - 10} more")

    return {
        "findings_by_method": dict(findings_by_method),
        "expected_edges_by_method": dict(findings_total_fields_by_method),
        "actual_edges_by_method": dict(graph_edges_by_method),
        "converted_by_method": dict(converted),
        "dropped_no_func_node": dict(dropped_no_func_node),
        "dropped_no_field": dict(dropped_no_field),
        "dropped_funcs": sorted([(fn, f, m) for fn, f, m in dropped_funcs]),
    }


def grep_go_patterns():
    """Grep for dynamic filter construction patterns in the Go source."""
    print("\n" + "=" * 70)
    print("QUESTION C: Dynamic filter patterns in Go source")
    print("=" * 70)

    patterns = {
        "bson.M literals": r"bson\.M\{",
        "bson.D literals": r"bson\.D\{",
        "filter[ map updates": r"\bfilter\[\s*[\"`]",
        "any map_update on bson.M var": r"\b\w+\[\s*[\"`]\w+[\"`]\s*\]\s*=",  # anyvar["x"] =
        "helper functions taking bson.M": r"func\s+\w+\s*\([^)]*\bbson\.M\b[^)]*\)",
        "loop-built filters (range + filter[)": r"for\s+\w+\s*,\s*\w+\s*:?=\s*range",
        "builder chaining (.Where/.AddFilter)": r"\.(Where|WithFilter|AddFilter|Filter)\s*\(",
        "mergeBson helper": r"\bmergeBson\b|\bmergeFilters\b|\bbuildFilter\b",
    }

    results = {}
    for label, pat in patterns.items():
        try:
            r = subprocess.run(
                ["rg", "-c", "--no-heading", "-g", "*.go", "-g", "!*_test.go", pat, str(BACKEND)],
                capture_output=True, text=True, timeout=30,
            )
            counts = {}
            for line in r.stdout.strip().split("\n"):
                if not line:
                    continue
                if ":" in line:
                    f, c = line.rsplit(":", 1)
                    try:
                        counts[f] = int(c)
                    except ValueError:
                        pass
            total = sum(counts.values())
            results[label] = {"total": total, "files": len(counts), "top_files": sorted(counts.items(), key=lambda x: -x[1])[:5]}
            print(f"\n  {label}: {total} matches across {len(counts)} files")
            for f, c in results[label]["top_files"]:
                print(f"    {c:4d}  {f.replace(str(BACKEND) + '/', '')}")
        except Exception as e:
            print(f"\n  {label}: ERROR {e}")
            results[label] = {"error": str(e)}

    return results


def find_helper_functions() -> list[tuple[str, str]]:
    """Find Go functions that take a bson.M parameter (helper functions that mutate filters)."""
    print("\n" + "-" * 70)
    print("HELPER FUNCTIONS: functions taking bson.M as a parameter")
    print("-" * 70)

    r = subprocess.run(
        ["rg", "-n", "--no-heading", "-g", "*.go", "-g", "!*_test.go",
         r"func\s+(\([^)]+\)\s+)?(\w+)\s*\([^)]*\bbson\.M\b[^)]*\)", str(BACKEND)],
        capture_output=True, text=True, timeout=30,
    )
    helpers = []
    for line in r.stdout.strip().split("\n"):
        if not line:
            continue
        # Extract file:line:match
        m = re.match(r"^(.+?):(\d+):\s*(.*)$", line)
        if m:
            f, ln, code = m.group(1), int(m.group(2)), m.group(3)
            rel = f.replace(str(BACKEND) + "/", "")
            helpers.append((rel, ln, code.strip()))
    print(f"  Found {len(helpers)} helper functions taking bson.M:")
    for rel, ln, code in helpers[:20]:
        print(f"    {rel}:{ln}  {code[:100]}")
    if len(helpers) > 20:
        print(f"    ... and {len(helpers) - 20} more")
    return [(rel, ln) for rel, ln, _ in helpers]


def find_loop_built_filters() -> list[tuple[str, int]]:
    """Find for-range loops that mutate a filter map."""
    print("\n" + "-" * 70)
    print("LOOP-BUILT FILTERS: for k, v := range ... { filter[k] = v }")
    print("-" * 70)

    # Use multiline ripgrep to find "for ... range" blocks that contain filter[ writes
    r = subprocess.run(
        ["rg", "-n", "--no-heading", "-g", "*.go", "-g", "!*_test.go", "-U",
         r"for\s+\w+\s*,?\s*\w*\s*:?=\s*range[^{]*\{[^}]*\w+\[[^\]]+\]\s*=", str(BACKEND)],
        capture_output=True, text=True, timeout=30,
    )
    loops = []
    for block in r.stdout.strip().split("\n--\n") if r.stdout else []:
        first_line = block.split("\n")[0]
        m = re.match(r"^(.+?):(\d+):", first_line)
        if m:
            rel = m.group(1).replace(str(BACKEND) + "/", "")
            loops.append((rel, int(m.group(2))))
    # Dedup
    loops = sorted(set(loops))
    print(f"  Found {len(loops)} loop-built filter sites:")
    for rel, ln in loops[:20]:
        print(f"    {rel}:{ln}")
    if len(loops) > 20:
        print(f"    ... and {len(loops) - 20} more")
    return loops


def cross_check_functions_in_graph(func_names: list[str], graph: dict) -> dict:
    """Check which functions appear in the graph (as nodes) and which don't."""
    # Build a quick lookup of all labels in the graph
    labels = set()
    labels_lower = set()
    for n in graph["nodes"]:
        l = n.get("label", "")
        if l:
            labels.add(l)
            labels_lower.add(l.lower())
    found, missing = [], []
    for fn in func_names:
        if fn in labels or fn + "()" in labels or fn.lower() in labels_lower:
            found.append(fn)
        else:
            missing.append(fn)
    return {"found": found, "missing": missing}


def question_c_cross_check():
    """For each dynamic-filter pattern found via grep, check if it appears in the graph."""
    print("\n" + "=" * 70)
    print("QUESTION C: Cross-check dynamic-filter functions against graph")
    print("=" * 70)

    graph = load_graph()
    filters = load_filters()

    # All functions in go-filters.json (these are functions the tracer analyzed)
    tracer_funcs = [f["function"] for f in filters]
    print(f"\nTracer analyzed {len(tracer_funcs)} functions (in go-filters.json)")

    # All functions in the graph that have at least one filter_writes_field edge
    funcs_with_edges = set()
    for e in graph["links"]:
        if e.get("relation") == "filter_writes_field":
            funcs_with_edges.add(e["source"])
    print(f"Graph has {len(funcs_with_edges)} function nodes with filter_writes_field edges")

    # Which tracer functions have at least one map_update finding?
    funcs_with_map_update = []
    for f in filters:
        for finding in f.get("findings", []):
            if finding.get("method") == "map_update":
                funcs_with_map_update.append((f["function"], f["file"], finding.get("position"), finding.get("fields")))
                break
    print(f"\nTracer found map_update findings in {len(funcs_with_map_update)} functions:")
    for fn, f, pos, fields in funcs_with_map_update:
        print(f"  {fn}  ({pos})  fields={fields}")

    # Now check specific admin-analytics functions that likely use dynamic filters
    # (these were called out in the worklog as having dynamic filter construction)
    suspect_funcs = [
        "(*AdminHandler).ListTenants",
        "(*AdminHandler).ExportTenantsCSV",
        "(*AdminHandler).ListUsers",
        "(*AdminHandler).ExportUsersCSV",
        "(*TenantHandler).GetActivity",
        "(*LogsHandler).ListLogs",
        "(*BillingHandler).AdminListTransactions",
        "(*AdminHandler).FunnelMetrics",
        "(*AdminHandler).DashboardMetrics",
        "(*AdminHandler).RevenueMetrics",
        "(*AdminHandler).UserGrowthMetrics",
        "(*AdminHandler).ActiveUsersMetrics",
    ]
    print(f"\nCross-checking {len(suspect_funcs)} suspect dynamic-filter functions:")

    # Build function-name → graph node lookup
    index = build_func_node_index(graph)

    # Build function-name → tracer findings lookup
    tracer_by_name = {f["function"]: f for f in filters}

    for fn in suspect_funcs:
        in_tracer = fn in tracer_by_name
        graph_node_id = find_func_node(fn, "", index)
        graph_node_exists = graph_node_id is not None

        # Count edges from this function in the graph
        edge_count = 0
        edge_methods = Counter()
        if graph_node_id:
            for e in graph["links"]:
                if e.get("source") == graph_node_id and e.get("relation") == "filter_writes_field":
                    edge_count += 1
                    edge_methods[e.get("method", "?")] += 1

        # Count findings from tracer
        finding_count = 0
        finding_methods = Counter()
        finding_fields = []
        if in_tracer:
            for f in tracer_by_name[fn].get("findings", []):
                finding_count += 1
                finding_methods[f.get("method", "?")] += 1
                finding_fields.extend(f.get("fields", []))

        status = "OK" if (in_tracer and graph_node_exists and edge_count > 0) else "CHECK"
        print(f"\n  [{status}] {fn}")
        print(f"      in_tracer: {in_tracer}  graph_node: {graph_node_exists}  edges: {edge_count}  findings: {finding_count}")
        if finding_methods:
            print(f"      tracer findings by method: {dict(finding_methods)}")
        if edge_methods:
            print(f"      graph edges by method:     {dict(edge_methods)}")
        if in_tracer and finding_methods.get("map_update", 0) == 0 and finding_methods.get("literal", 0) > 0:
            print(f"      NOTE: has literal findings but NO map_update — could be misclassified dynamic filter")
        if not in_tracer:
            print(f"      NOTE: function NOT in tracer output — either doesn't call mongo or tracer skipped it")
        if not graph_node_exists:
            print(f"      NOTE: function NOT in graph nodes — findings would be dropped at enrich time")


def investigate_logs_listlogs():
    """logs.ListLogs was annotated with // graphify:no-index-check because of dynamic filter.
    Check if the tracer actually found its filter fields."""
    print("\n" + "-" * 70)
    print("SPOT-CHECK: logs.ListLogs (annotated as dynamic-filter)")
    print("-" * 70)

    filters = load_filters()
    for f in filters:
        if "ListLogs" in f["function"] or "logsFollow" in f["function"]:
            print(f"\n  {f['function']}  ({f['file']}:{f['line']})")
            for finding in f.get("findings", []):
                print(f"    {finding}")

    # Also look at the actual Go source for ListLogs to see the filter construction
    listlogs_path = BACKEND / "internal" / "api" / "handlers" / "logs.go"
    if listlogs_path.exists():
        text = listlogs_path.read_text(encoding="utf-8")
        # Find ListLogs function
        m = re.search(r"func\s+\([^)]+\)\s+ListLogs\b.*?(?=\nfunc\s|\Z)", text, re.DOTALL)
        if m:
            body = m.group(0)
            # Show the filter construction lines
            print("\n  Filter construction in ListLogs source:")
            for i, line in enumerate(body.split("\n"), 1):
                if "filter" in line.lower() and ("[" in line or "bson.M" in line or "buildFilter" in line or "mergeBson" in line):
                    print(f"    {i:3d}: {line.rstrip()}")


def investigate_get_activity():
    """tenant.GetActivity was annotated as dynamic-filter. Check tracer output."""
    print("\n" + "-" * 70)
    print("SPOT-CHECK: tenant.GetActivity (annotated as dynamic-filter)")
    print("-" * 70)

    filters = load_filters()
    for f in filters:
        if "GetActivity" in f["function"]:
            print(f"\n  {f['function']}  ({f['file']}:{f['line']})")
            for finding in f.get("findings", []):
                print(f"    {finding}")


def main():
    results_a_b = question_a_and_b()
    grep_results = grep_go_patterns()
    helpers = find_helper_functions()
    loops = find_loop_built_filters()
    question_c_cross_check()
    investigate_logs_listlogs()
    investigate_get_activity()

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    actual = results_a_b["actual_edges_by_method"]
    expected = results_a_b["expected_edges_by_method"]
    print(f"  literal:    expected {expected.get('literal', 0)} edges, actual {actual.get('literal', 0)} edges  ({actual.get('literal', 0) / max(expected.get('literal', 1), 1) * 100:.1f}%)")
    print(f"  map_update: expected {expected.get('map_update', 0)} edges, actual {actual.get('map_update', 0)} edges  ({actual.get('map_update', 0) / max(expected.get('map_update', 1), 1) * 100:.1f}%)")
    print(f"  struct_type: expected {expected.get('struct_type', 0)} edges, actual {actual.get('struct_type', 0)} edges  ({actual.get('struct_type', 0) / max(expected.get('struct_type', 1), 1) * 100:.1f}%)")


if __name__ == "__main__":
    main()
