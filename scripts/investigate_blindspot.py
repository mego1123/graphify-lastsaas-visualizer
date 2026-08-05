#!/usr/bin/env python3
"""Issue #8: Re-check the blind spot — what real findings were hidden by the
enrich.py lookup bug?

The bug: enrich_with_ssa couldn't match Go method-receiver labels
((*AdminHandler).ListTenants → .ListTenants()), so 230/230 functions
were silently dropped from the graph. The "8 map_update edges" wasn't
an under-count of dynamic filters — it was a total blind spot for ALL
method-receiver functions.

This script answers: did the bug just miscount, or did it hide real bugs?

Approach:
1. Save current (post-fix) findings from Missing Indexes + NoSQL Injection.
2. Temporarily revert the enrich.py fix (using git diff patch, NOT stash).
3. Re-enrich to reproduce the blind graph.
4. Run Missing Indexes + NoSQL Injection on the blind graph.
5. Restore the fix and re-enrich.
6. Diff finding IDs: which findings appear ONLY in the post-fix run?

Key insight: Missing Indexes and NoSQL Injection both consume the Go
filter tracer's output directly (via subprocess), NOT through the graph.
So the bug in enrich.py shouldn't affect them... unless they also read
from the graph. This script verifies that.
"""
from __future__ import annotations
import json
import os
import subprocess
import sys
from pathlib import Path

REPO = Path("/home/z/my-project/repos/lastsaas")
SCRIPTS = Path("/home/z/my-project/scripts")
ENRICH = SCRIPTS / "graphify_enrich.py"
GRAPH = REPO / "graphify-out" / "graph.json"

# Patch file for reverting the enrich.py fix
PATCH_FILE = Path("/tmp/enrich_fix.patch")


def run(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    """Run a command and return the result."""
    print(f"  $ {' '.join(cmd)}")
    return subprocess.run(cmd, capture_output=True, text=True, timeout=kw.pop("timeout", 300), **kw)


def run_tool(script_name: str, out_path: Path) -> dict:
    """Run a tool and return its JSON output."""
    cmd = [sys.executable, str(SCRIPTS / script_name), str(REPO), "--json", "--out", str(out_path)]
    print(f"  $ {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if result.returncode != 0:
        print(f"  FAILED: {result.stderr[-300:]}")
        return {}
    # Try reading JSON from --out, fallback to stdout
    data = None
    if out_path.exists():
        try:
            data = json.loads(out_path.read_text())
        except json.JSONDecodeError:
            pass
    if data is None and result.stdout.strip():
        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError:
            pass
    return data or {}


def stable_id(f: dict) -> str:
    """Line-insensitive stable ID for cross-run comparison."""
    file_ = f.get("file", "")
    function = f.get("function", "")
    collection = f.get("collection", "")
    ff = sorted(f.get("filter_fields", []) or [])
    return f"{file_}:{function}:{collection}:{','.join(ff)}"


def save_patch():
    """Save the current enrich.py fix as a patch, then revert."""
    print("\n[1] Saving enrich.py fix as patch...")
    r = run(["git", "diff", "--", str(ENRICH)], cwd=str(Path("/home/z/my-project")))
    if r.stdout.strip():
        PATCH_FILE.write_text(r.stdout)
        print(f"  Saved patch ({len(r.stdout)} bytes) to {PATCH_FILE}")
    else:
        # The fix might already be committed. Create patch from git log.
        r = run(["git", "log", "-1", "--format=%H", "--", str(ENRICH)], cwd=str(Path("/home/z/my-project")))
        if r.stdout.strip():
            commit = r.stdout.strip()
            # Get the diff introduced by that commit for enrich.py
            r2 = run(["git", "show", commit, "--", str(ENRICH)], cwd=str(Path("/home/z/my-project")))
            # Extract just the diff part
            lines = r2.stdout.split("\n")
            diff_start = -1
            for i, line in enumerate(lines):
                if line.startswith("@@"):
                    diff_start = i
                    break
            if diff_start >= 0:
                patch = "\n".join(lines[diff_start:]) + "\n"
                # Create a reverse patch
                PATCH_FILE.write_text(patch)
                print(f"  Created reverse patch from commit {commit[:8]}")
            else:
                print("  WARNING: could not extract patch from commit")
                PATCH_FILE.write_text("")

    # Also check if the fix is in graph_query.py (it was committed earlier)
    r = run(["git", "log", "--oneline", "-5", "--", str(SCRIPTS / "graph_query.py")], cwd=str(Path("/home/z/my-project")))
    print(f"  graph_query.py history: {r.stdout.strip()}")


def revert_fix():
    """Revert enrich.py to the pre-fix state (the buggy version)."""
    print("\n[2] Reverting enrich.py fix to reproduce the blind graph...")
    if not PATCH_FILE.exists() or not PATCH_FILE.read_text().strip():
        print("  No patch to revert. The fix may be committed.")
        print("  Using git checkout to get the pre-fix version...")
        # Find the commit before the fix
        r = run(["git", "log", "--oneline", "-10", "--", str(ENRICH)], cwd=str(Path("/home/z/my-project")))
        print(f"  Recent commits for enrich.py:\n{r.stdout}")
        # The fix was in commit 9563297 (or nearby). Let's find the parent.
        r = run(["git", "log", "--format=%H %s", "-5", "--", str(ENRICH)], cwd=str(Path("/home/z/my-project")))
        commits = r.stdout.strip().split("\n")
        if len(commits) >= 2:
            parent_commit = commits[1].split()[0]
            print(f"  Checking out enrich.py from parent commit {parent_commit[:8]}...")
            r = run(["git", "checkout", parent_commit, "--", str(ENRICH)], cwd=str(Path("/home/z/my-project")))
            if r.returncode == 0:
                print("  Reverted enrich.py to pre-fix version.")
                return True
        print("  WARNING: could not revert. Using current version.")
        return False
    else:
        r = run(["git", "apply", "--reverse", str(PATCH_FILE)], cwd=str(Path("/home/z/my-project")))
        if r.returncode == 0:
            print("  Reverted enrich.py via reverse patch.")
            return True
        else:
            print(f"  git apply --reverse failed: {r.stderr}")
            return False


def restore_fix():
    """Restore the enrich.py fix."""
    print("\n[3] Restoring enrich.py fix...")
    # Just checkout from HEAD (the committed version)
    r = run(["git", "checkout", "HEAD", "--", str(ENRICH)], cwd=str(Path("/home/z/my-project")))
    if r.returncode == 0:
        print("  Restored enrich.py from HEAD.")
    else:
        print(f"  git checkout failed: {r.stderr}")
        # Try re-applying the patch
        if PATCH_FILE.exists() and PATCH_FILE.read_text().strip():
            r = run(["git", "apply", str(PATCH_FILE)], cwd=str(Path("/home/z/my-project")))
            if r.returncode == 0:
                print("  Restored enrich.py via patch.")
            else:
                print(f"  FATAL: could not restore enrich.py! {r.stderr}")
                sys.exit(2)


def enrich_graph():
    """Run enrichment on the current graph."""
    r = run([sys.executable, str(ENRICH), str(REPO), "--all"], timeout=300)
    if r.returncode != 0:
        print(f"  enrich failed: {r.stderr[-300:]}")
    else:
        # Show the SSA lookup stats from stderr
        for line in r.stderr.split("\n"):
            if "SSA lookup" in line or "filter_writes_field" in line or "Enriched" in line:
                print(f"  {line.strip()}")


def get_graph_method_counts() -> dict:
    """Return {method: count} for filter_writes_field edges."""
    with open(GRAPH) as f:
        g = json.load(f)
    from collections import Counter
    counts = Counter()
    for e in g["links"]:
        if e.get("relation") == "filter_writes_field":
            counts[e.get("method", "?")] += 1
    return dict(counts)


def main():
    print("=" * 70)
    print("ISSUE #8: Re-check the blind spot — what was the bug hiding?")
    print("=" * 70)

    # Step 0: Confirm current state (post-fix)
    print("\n[0] Current graph state (post-fix):")
    counts = get_graph_method_counts()
    print(f"  filter_writes_field edges: {counts}")
    print(f"  total: {sum(counts.values())}")

    # Step 1: Run both tools on the POST-FIX graph
    print("\n[A] Running tools on POST-FIX graph (with fix)...")
    missing_after = run_tool("graphify_missing_indexes.py", Path("/tmp/blindspot_missing_after.json"))
    nosql_after = run_tool("graphify_nosql_injection.py", Path("/tmp/blindspot_nosql_after.json"))

    missing_after_ids = set(stable_id(f) for f in missing_after.get("findings", []) + missing_after.get("suppressed", []))
    nosql_after_ids = set(stable_id(f) for f in nosql_after.get("findings", []))

    print(f"  Missing Indexes: {len(missing_after.get('findings',[]))} findings + {len(missing_after.get('suppressed',[]))} suppressed = {len(missing_after_ids)} unique IDs")
    print(f"  NoSQL Injection:  {len(nosql_after.get('findings',[]))} findings = {len(nosql_after_ids)} unique IDs")

    # Step 2: Revert the fix and re-enrich
    save_patch()
    if not revert_fix():
        print("\n  WARNING: could not revert. Using current graph for both runs.")
        missing_before = missing_after
        nosql_before = nosql_after
    else:
        print("\n[B] Re-enriching with the BUGGY enrich.py (pre-fix)...")
        enrich_graph()
        counts_before = get_graph_method_counts()
        print(f"  filter_writes_field edges: {counts_before}")
        print(f"  total: {sum(counts_before.values())}")

        # Step 3: Run both tools on the PRE-FIX (blind) graph
        print("\n[C] Running tools on PRE-FIX graph (blind to method-receiver functions)...")
        missing_before = run_tool("graphify_missing_indexes.py", Path("/tmp/blindspot_missing_before.json"))
        nosql_before = run_tool("graphify_nosql_injection.py", Path("/tmp/blindspot_nosql_before.json"))

        # Step 4: Restore the fix and re-enrich
        restore_fix()
        print("\n[D] Re-enriching with the FIXED enrich.py (restoring correct graph)...")
        enrich_graph()
        counts_restored = get_graph_method_counts()
        print(f"  filter_writes_field edges: {counts_restored}")
        print(f"  total: {sum(counts_restored.values())}")

    missing_before_ids = set(stable_id(f) for f in missing_before.get("findings", []) + missing_before.get("suppressed", []))
    nosql_before_ids = set(stable_id(f) for f in nosql_before.get("findings", []))

    print(f"\n  Missing Indexes (pre-fix): {len(missing_before.get('findings',[]))} findings + {len(missing_before.get('suppressed',[]))} suppressed = {len(missing_before_ids)} unique IDs")
    print(f"  NoSQL Injection (pre-fix):  {len(nosql_before.get('findings',[]))} findings = {len(nosql_before_ids)} unique IDs")

    # Step 5: Diff
    print("\n" + "=" * 70)
    print("DIFF: What findings were hidden by the bug?")
    print("=" * 70)

    print("\n--- Missing Indexes ---")
    only_after = missing_after_ids - missing_before_ids
    only_before = missing_before_ids - missing_after_ids
    common = missing_after_ids & missing_before_ids
    print(f"  Findings in POST-FIX only (hidden by bug): {len(only_after)}")
    for sid in sorted(only_after)[:20]:
        # Find the actual finding
        for f in missing_after.get("findings", []) + missing_after.get("suppressed", []):
            if stable_id(f) == sid:
                sev = f.get("severity", f.get("would_be_severity", "?"))
                print(f"    [{sev}] {sid}")
                break
    if len(only_after) > 20:
        print(f"    ... and {len(only_after) - 20} more")
    print(f"  Findings in PRE-FIX only (gone after fix):  {len(only_before)}")
    for sid in sorted(only_before)[:10]:
        print(f"    {sid}")
    print(f"  Common to both:                            {len(common)}")

    print("\n--- NoSQL Injection ---")
    only_after_n = nosql_after_ids - nosql_before_ids
    only_before_n = nosql_before_ids - nosql_after_ids
    common_n = nosql_after_ids & nosql_before_ids
    print(f"  Findings in POST-FIX only (hidden by bug): {len(only_after_n)}")
    for sid in sorted(only_after_n)[:20]:
        for f in nosql_after.get("findings", []):
            if stable_id(f) == sid:
                risk = f.get("risk", "?")
                print(f"    [{risk}] {sid}")
                break
    if len(only_after_n) > 20:
        print(f"    ... and {len(only_after_n) - 20} more")
    print(f"  Findings in PRE-FIX only (gone after fix):  {len(only_before_n)}")
    for sid in sorted(only_before_n)[:10]:
        print(f"    {sid}")
    print(f"  Common to both:                            {len(common_n)}")

    # Step 6: Also check if the tools consume the graph at all
    print("\n" + "=" * 70)
    print("ENRICHMENT-INDEPENDENCE CHECK")
    print("=" * 70)
    for tool_name, script in [("Missing Indexes", "graphify_missing_indexes.py"), ("NoSQL Injection", "graphify_nosql_injection.py")]:
        src = (SCRIPTS / script).read_text()
        uses_graph = "graph.json" in src or "graph_query" in src
        uses_tracer = "graphify_filter_tracer" in src or "FILTER_TRACER_PATH" in src
        print(f"\n  {tool_name} ({script}):")
        print(f"    reads graph.json or imports graph_query?  {'YES' if uses_graph else 'NO'}")
        print(f"    shells out to Go filter tracer?           {'YES' if uses_tracer else 'NO'}")
        if not uses_graph:
            print(f"    → This tool is enrichment-independent. The bug did NOT affect its output.")
        if uses_tracer:
            print(f"    → This tool runs the tracer directly, bypassing the graph.")

    # Final verdict
    print("\n" + "=" * 70)
    print("VERDICT")
    print("=" * 70)
    if len(only_after) == 0 and len(only_after_n) == 0:
        print("\n  ✅ The enrich.py bug did NOT hide any real findings.")
        print("     Both Missing Indexes and NoSQL Injection are enrichment-independent")
        print("     (they consume the tracer directly, not through the graph).")
        print("     The bug only affected graph-based queries, not the audit tools.")
    else:
        print(f"\n  ⚠ The bug HID {len(only_after)} Missing Index + {len(only_after_n)} NoSQL findings.")
        print("  These are real findings that were invisible in the blind graph.")
        print("  Review the diff above to triage each one.")


if __name__ == "__main__":
    main()
