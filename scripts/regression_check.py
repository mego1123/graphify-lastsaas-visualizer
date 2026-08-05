#!/usr/bin/env python3
"""Regression check: verify the 5 tools produce correct output on the
re-enriched graph (with the fixed enrich.py lookup).

Tools to check:
1. graphify_errors.py — Error Auditor (was 0% false positive)
2. graphify_tenant_audit.py — Tenant Audit (was 0% false positive)
3. graphify_n_plus_1.py — N+1 Query Detector (was 0% false positive)
4. graphify_nosql_injection.py — NoSQL Injection Scanner
5. graphify_missing_indexes.py — Missing Indexes (was 11 suppressed)

For each tool, run it and capture:
- key metric (finding count, severity breakdown)
- compare to expected value from worklog
- flag any unexpected changes
"""
from __future__ import annotations
import json
import subprocess
import sys
from pathlib import Path

REPO = Path("/home/z/my-project/repos/lastsaas")
SCRIPTS = Path("/home/z/my-project/scripts")


def run_tool(script_name: str, out_path: Path) -> dict:
    """Run a tool and return its JSON output.

    Some tools write JSON to --out (when --json is set), others write
    markdown to --out and JSON to stdout. We capture stdout as a fallback.
    """
    cmd = [sys.executable, str(SCRIPTS / script_name), str(REPO), "--json", "--out", str(out_path)]
    print(f"  $ {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    if result.returncode != 0:
        print(f"  FAILED (exit {result.returncode})")
        print(f"  stderr: {result.stderr[-500:]}")
        return {}

    # Try reading JSON from the --out file first
    data = None
    if out_path.exists():
        try:
            data = json.loads(out_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            data = None  # --out wrote markdown, not JSON

    # Fallback: parse JSON from stdout
    if data is None and result.stdout.strip():
        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError:
            print(f"  Could not parse JSON from stdout (first 200 chars): {result.stdout[:200]}")
            return {}

    if data is None:
        print(f"  NO JSON OUTPUT")
        return {}

    return data


def check_errors() -> dict:
    """1. Error Auditor — should be 0% false positive."""
    print("\n[1/5] Error Auditor (graphify_errors.py)...")
    data = run_tool("graphify_errors.py", Path("/tmp/regress_errors.json"))
    if not data:
        return {"status": "FAILED"}
    # Extract key metrics
    total = data.get("total_findings", 0)
    by_severity = data.get("severity_breakdown", {})
    by_type = data.get("type_breakdown", {})
    print(f"  total_findings: {total}")
    print(f"  severity_breakdown: {by_severity}")
    print(f"  type_breakdown (top 3): {dict(list(by_type.items())[:3]) if isinstance(by_type, dict) else by_type}")
    return {
        "status": "OK",
        "total_findings": total,
        "severity_breakdown": by_severity,
    }


def check_tenant_audit() -> dict:
    """2. Tenant Audit — should be 0 violations."""
    print("\n[2/5] Tenant Audit (graphify_tenant_audit.py)...")
    data = run_tool("graphify_tenant_audit.py", Path("/tmp/regress_tenant.json"))
    if not data:
        return {"status": "FAILED"}
    total = data.get("total_findings", 0)
    violations = data.get("violation_count", 0)
    by_severity = data.get("severity_breakdown", {})
    print(f"  total_findings: {total}")
    print(f"  violation_count: {violations}")
    print(f"  severity_breakdown: {by_severity}")
    return {
        "status": "OK",
        "total_findings": total,
        "violation_count": violations,
        "severity_breakdown": by_severity,
    }


def check_n_plus_1() -> dict:
    """3. N+1 Query Detector — should be 0% false positive."""
    print("\n[3/5] N+1 Query Detector (graphify_n_plus_1.py)...")
    data = run_tool("graphify_n_plus_1.py", Path("/tmp/regress_nplus1.json"))
    if not data:
        return {"status": "FAILED"}
    total = data.get("total_findings", 0)
    by_severity = data.get("severity_breakdown", {})
    findings = data.get("findings", [])
    print(f"  total_findings: {total}")
    print(f"  severity_breakdown: {by_severity}")
    if findings:
        print(f"  sample finding: {json.dumps(findings[0], indent=2)[:300]}")
    return {
        "status": "OK",
        "total_findings": total,
        "severity_breakdown": by_severity,
    }


def check_nosql_injection() -> dict:
    """4. NoSQL Injection Scanner — should be 25 HIGH + 126 LOW (4 from tracer)."""
    print("\n[4/5] NoSQL Injection Scanner (graphify_nosql_injection.py)...")
    data = run_tool("graphify_nosql_injection.py", Path("/tmp/regress_nosql.json"))
    if not data:
        return {"status": "FAILED"}
    summary = data.get("summary", {})
    findings = data.get("findings", [])
    total = summary.get("total_findings", len(findings))
    by_risk = summary.get("by_risk", {})
    by_source = summary.get("by_source", {})
    print(f"  total_findings: {total}")
    print(f"  by_risk: {by_risk}")
    print(f"  by_source: {by_source}")
    return {
        "status": "OK",
        "total_findings": total,
        "by_risk": by_risk,
        "by_source": by_source,
    }


def check_missing_indexes() -> dict:
    """5. Missing Indexes — should be 22 findings + 11 suppressed."""
    print("\n[5/5] Missing Indexes (graphify_missing_indexes.py)...")
    data = run_tool("graphify_missing_indexes.py", Path("/tmp/regress_missing.json"))
    if not data:
        return {"status": "FAILED"}
    findings = len(data.get("findings", []))
    suppressed = len(data.get("suppressed", []))
    by_severity = data.get("severity_breakdown", {})
    suppression_breakdown = data.get("suppression_breakdown", {})
    print(f"  findings: {findings}")
    print(f"  suppressed: {suppressed}")
    print(f"  total: {findings + suppressed}")
    print(f"  severity_breakdown: {by_severity}")
    print(f"  suppression_breakdown: {suppression_breakdown}")
    return {
        "status": "OK",
        "findings": findings,
        "suppressed": suppressed,
        "severity_breakdown": by_severity,
        "suppression_breakdown": suppression_breakdown,
    }


def main():
    print("=" * 70)
    print("REGRESSION CHECK: 5 tools on re-enriched graph (fixed enrich.py)")
    print("=" * 70)
    print(f"Repo: {REPO}")
    print(f"Graph: {REPO}/graphify-out/graph.json")

    # Verify graph state
    graph_path = REPO / "graphify-out" / "graph.json"
    with open(graph_path) as f:
        g = json.load(f)
    from collections import Counter
    fwf_methods = Counter()
    for e in g["links"]:
        if e.get("relation") == "filter_writes_field":
            fwf_methods[e.get("method", "?")] += 1
    print(f"\nGraph stats: {len(g['nodes'])} nodes, {len(g['links'])} links")
    print(f"filter_writes_field edges by method: {dict(fwf_methods)}")
    print(f"  total filter_writes_field: {sum(fwf_methods.values())}")

    results = {}
    results["errors"] = check_errors()
    results["tenant_audit"] = check_tenant_audit()
    results["n_plus_1"] = check_n_plus_1()
    results["nosql_injection"] = check_nosql_injection()
    results["missing_indexes"] = check_missing_indexes()

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    for tool, r in results.items():
        status = r.get("status", "?")
        print(f"  {tool:20} status={status}")

    # Specific assertions
    print("\nAssertions:")
    mi = results.get("missing_indexes", {})
    if mi.get("suppressed") == 11:
        print(f"  ✅ Missing Indexes: 11 suppressed (expected 11)")
    else:
        print(f"  ⚠ Missing Indexes: {mi.get('suppressed')} suppressed (expected 11)")

    ta = results.get("tenant_audit", {})
    if ta.get("violation_count") == 0:
        print(f"  ✅ Tenant Audit: 0 violations (expected 0)")
    else:
        print(f"  ⚠ Tenant Audit: {ta.get('violation_count')} violations (expected 0)")


if __name__ == "__main__":
    main()
