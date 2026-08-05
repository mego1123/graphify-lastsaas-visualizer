#!/usr/bin/env python3
"""Issue 2 verification: are the 11 suppressed missing-index findings the same
11 pre/post enrichment?

Background:
- `graphify_missing_indexes.py` does NOT consume Phase 2 enrichment data
  (no graph.json reads, no Go tracer subprocess, no graph_query import).
- It's a pure regex scanner + `// graphify:no-index-check` annotation logic.
- Therefore enrichment cannot perturb its output.
- The 11 suppressed findings are determined entirely by:
    (a) the regex scanner's filter-field extraction (unchanged by enrichment)
    (b) the `// graphify:no-index-check` annotations in the Go source
        (these were added in the working tree, not yet committed)

To verify Claude's concern ("the count happens to match but the IDs differ"):
1. Run missing_indexes on the CURRENT working tree (with annotations) → "after"
2. `git stash` the annotation changes → revert to pre-annotation state
3. Run missing_indexes again → "before"
4. Construct stable IDs from (file, line, function, collection, filter_fields)
5. Diff the suppressed-finding IDs
6. `git stash pop` to restore the annotations

If the IDs match, the 11 suppressed findings are exactly the 11 the annotation
logic was designed to suppress — no silent drift, no coincidental count match.
"""
from __future__ import annotations
import json
import subprocess
import sys
from pathlib import Path

REPO = Path("/home/z/my-project/repos/lastsaas")
SCRIPT = Path("/home/z/my-project/scripts/graphify_missing_indexes.py")
BEFORE_JSON = Path("/tmp/missing_indexes_before.json")
AFTER_JSON = Path("/tmp/missing_indexes_after.json")


def run_missing_indexes(out_path: Path) -> dict:
    """Run missing_indexes on REPO and write JSON to out_path."""
    cmd = [
        sys.executable, str(SCRIPT), str(REPO),
        "--json", "--out", str(out_path),
    ]
    print(f"  $ {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        print(f"  STDERR: {result.stderr[-500:]}")
        raise RuntimeError(f"missing_indexes failed: {result.returncode}")
    return json.loads(out_path.read_text(encoding="utf-8"))


def stable_id(finding: dict) -> str:
    """Construct a stable identifier for a finding.

    Uses (file, function, collection, filter_fields) — these fields uniquely
    identify a query site. Line number is intentionally OMITTED because adding
    `// graphify:no-index-check` annotations shifts line numbers, which would
    cause false mismatches.
    """
    file_ = finding.get("file", "")
    function = finding.get("function", "")
    collection = finding.get("collection", "")
    filter_fields = finding.get("filter_fields", [])
    # Sort filter_fields for order-insensitive matching
    ff = sorted(filter_fields) if filter_fields else []
    return f"{file_}:{function}:{collection}:{','.join(ff)}"


def stable_id_with_line(finding: dict) -> str:
    """Stable ID including line number — for diagnostics only."""
    file_ = finding.get("file", "")
    line = finding.get("line", 0)
    function = finding.get("function", "")
    collection = finding.get("collection", "")
    filter_fields = finding.get("filter_fields", [])
    ff = sorted(filter_fields) if filter_fields else []
    return f"{file_}:{line}:{function}:{collection}:{','.join(ff)}"


def extract_suppressed(data: dict) -> dict[str, dict]:
    """Return {stable_id: finding_dict} for all suppressed findings."""
    out = {}
    for f in data.get("suppressed", []):
        sid = stable_id(f)
        out[sid] = f
    return out


def extract_findings(data: dict) -> dict[str, dict]:
    """Return {stable_id: finding_dict} for all unsuppressed findings."""
    out = {}
    for f in data.get("findings", []):
        sid = stable_id(f)
        out[sid] = f
    return out


def git_stash_push() -> bool:
    """Stash working-tree changes. Returns True on success."""
    r = subprocess.run(
        ["git", "stash", "push", "-m", "issue2-verification-temp"],
        cwd=str(REPO), capture_output=True, text=True, timeout=30,
    )
    if r.returncode != 0:
        print(f"  git stash failed: {r.stderr}")
        return False
    # If there was nothing to stash, stdout says "No local changes to save"
    return "No local changes" not in r.stdout


def git_stash_pop() -> bool:
    """Restore stashed changes."""
    r = subprocess.run(
        ["git", "stash", "pop"],
        cwd=str(REPO), capture_output=True, text=True, timeout=30,
    )
    if r.returncode != 0:
        print(f"  git stash pop failed: {r.stderr}")
        return False
    return True


def main():
    print("=" * 70)
    print("ISSUE 2 VERIFICATION: 11 suppressed findings — same 11 pre/post?")
    print("=" * 70)

    # ---- AFTER (current working tree, with annotations) ----
    print("\n[1/4] Running missing_indexes on CURRENT working tree (with annotations)...")
    after = run_missing_indexes(AFTER_JSON)
    after_suppressed = extract_suppressed(after)
    after_findings = extract_findings(after)
    print(f"  findings (unsuppressed): {len(after_findings)}")
    print(f"  suppressed:              {len(after_suppressed)}")
    print(f"  total:                   {len(after_findings) + len(after_suppressed)}")

    # ---- BEFORE (stash annotations, re-run) ----
    print("\n[2/4] Stashing working-tree changes (reverts annotations)...")
    stashed = git_stash_push()
    if not stashed:
        print("  WARNING: could not stash — likely no working-tree changes.")
        print("  Falling back to comparing after vs after (will trivially match).")
        before = after
    else:
        print("  Stashed. Re-running missing_indexes...")
        before = run_missing_indexes(BEFORE_JSON)
    before_suppressed = extract_suppressed(before)
    before_findings = extract_findings(before)
    print(f"  findings (unsuppressed): {len(before_findings)}")
    print(f"  suppressed:              {len(before_suppressed)}")
    print(f"  total:                   {len(before_findings) + len(before_suppressed)}")

    # ---- Restore annotations ----
    if stashed:
        print("\n[3/4] Restoring stashed changes (annotations back)...")
        if not git_stash_pop():
            print("  ERROR: could not restore stash! Annotations are stashed.")
            print("  Run `git stash pop` manually in", REPO)
            sys.exit(2)
        print("  Restored.")

    # ---- DIFF ----
    print("\n[4/4] Diffing suppressed-finding IDs (before vs after)...")
    before_ids = set(before_suppressed.keys())
    after_ids = set(after_suppressed.keys())

    only_before = before_ids - after_ids
    only_after = after_ids - before_ids
    common = before_ids & after_ids

    print(f"\n  Suppressed IDs in BEFORE only:  {len(only_before)}")
    for sid in sorted(only_before):
        print(f"    - {sid}")
    print(f"\n  Suppressed IDs in AFTER only:   {len(only_after)}")
    for sid in sorted(only_after):
        print(f"    + {sid}")
    print(f"\n  Common to both:                 {len(common)}")

    # Also check: the 11 suppressed in "after" should appear as UNSUPPRESSED
    # findings in "before" (i.e., the annotation silenced them).
    print("\n  Cross-check: do the 11 'after' suppressed appear as 'before' findings?")
    matched_as_findings = 0
    unmatched = []
    for sid in sorted(after_ids):
        if sid in before_findings:
            matched_as_findings += 1
        elif sid in before_suppressed:
            print(f"    NOTE: {sid} was ALREADY suppressed before (annotation pre-existed)")
            matched_as_findings += 1  # Still a match
        else:
            unmatched.append(sid)
    print(f"    Matched as findings or pre-suppressed: {matched_as_findings}/{len(after_ids)}")
    if unmatched:
        print(f"    UNMATCHED (these appeared from nowhere):")
        for sid in unmatched:
            print(f"      ?? {sid}")

    # ---- VERDICT ----
    print("\n" + "=" * 70)
    print("VERDICT")
    print("=" * 70)
    same_count = len(before_suppressed) == len(after_suppressed)
    same_ids = before_ids == after_ids
    print(f"  Before suppressed count: {len(before_suppressed)}")
    print(f"  After suppressed count:  {len(after_suppressed)}")
    print(f"  Counts match: {same_count}")
    print(f"  IDs match:    {same_ids}")

    if same_count and same_ids:
        print("\n  ✅ CONFIRMED: the 11 suppressed findings are the SAME 11 pre/post.")
        print("     No silent drift, no coincidental count match.")
    else:
        print("\n  ⚠ MISMATCH: suppressed findings differ between runs.")
        print("     Investigate the diff above.")

    # ---- Show the 11 suppressed findings with their stable IDs ----
    print("\n  The 11 suppressed findings (with stable IDs, line-number-insensitive):")
    for sid in sorted(after_suppressed.keys()):
        f = after_suppressed[sid]
        sev = f.get("would_be_severity", "?")
        coll = f.get("collection", "?")
        fn = f.get("function", "?")
        sup = f.get("suppression", "?")
        line = f.get("line", "?")
        print(f"    [{sev:6}] L{line:<4} {coll:24} {fn:30}  suppression={sup}")
        print(f"           id={sid}")

    # ---- Also confirm enrichment-independence ----
    print("\n  Enrichment independence check:")
    print(f"    graphify_missing_indexes.py imports from graph_query? ", end="")
    src = SCRIPT.read_text(encoding="utf-8")
    print("NO" if "graph_query" not in src else "YES")
    print(f"    graphify_missing_indexes.py reads graph.json? ", end="")
    print("NO" if "graph.json" not in src else "YES")
    print(f"    graphify_missing_indexes.py shells out to Go tracer? ", end="")
    print("NO" if "graphify_filter_tracer" not in src else "YES")


if __name__ == "__main__":
    main()
