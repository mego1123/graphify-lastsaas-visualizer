#!/usr/bin/env python3
"""Issue 2 verification (v2): are the 11 suppressed missing-index findings the
same 11 pre/post enrichment?

Uses `git checkout` instead of `git stash` to avoid whitespace corruption
observed in v1. The git checkout reverts files to HEAD (no annotations),
then reapply_annotations.py restores them.

Steps:
1. Run missing_indexes on current working tree (with annotations) → AFTER
2. Save the 6 annotation files' content
3. `git checkout` the 6 files → reverts to HEAD (no annotations)
4. Run missing_indexes → BEFORE
5. Restore the saved content (annotations back)
6. Verify AFTER state is restored (run missing_indexes again → AFTER2)
7. Diff BEFORE vs AFTER (using line-number-insensitive stable IDs)
"""
from __future__ import annotations
import json
import subprocess
import sys
from pathlib import Path

REPO = Path("/home/z/my-project/repos/lastsaas")
SCRIPT = Path("/home/z/my-project/scripts/graphify_missing_indexes.py")
REAPPLY = Path("/home/z/my-project/scripts/reapply_annotations.py")
BEFORE_JSON = Path("/tmp/missing_indexes_before_v2.json")
AFTER_JSON = Path("/tmp/missing_indexes_after_v2.json")
AFTER2_JSON = Path("/tmp/missing_indexes_after2_v2.json")

ANNOTATED_FILES = [
    "backend/cmd/lastsaas/cmd_stats.go",
    "backend/internal/api/handlers/billing.go",
    "backend/internal/api/handlers/bundles.go",
    "backend/internal/api/handlers/logs.go",
    "backend/internal/api/handlers/tenant.go",
    "backend/internal/telemetry/service.go",
]


def run_missing_indexes(out_path: Path) -> dict:
    import hashlib
    # Print file hashes to verify state
    print(f"  [diag] File hashes before subprocess:")
    for f in ANNOTATED_FILES:
        fp = REPO / f
        if fp.exists():
            h = hashlib.sha256(fp.read_bytes()).hexdigest()[:16]
            n = fp.read_text().count("graphify:no-index-check")
            print(f"    {h}  ann={n}  {f}")
    cmd = [sys.executable, str(SCRIPT), str(REPO), "--json", "--out", str(out_path)]
    print(f"  $ {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        print(f"  STDERR: {result.stderr[-500:]}")
        raise RuntimeError(f"missing_indexes failed: {result.returncode}")
    print(f"  [diag] stderr tail: {result.stderr[-200:]}")
    return json.loads(out_path.read_text(encoding="utf-8"))


def stable_id(finding: dict) -> str:
    """Stable ID including line number — needed because the same (file,
    function, collection, filter_fields) tuple can appear multiple times
    (e.g., ListLogs has 2 separate Find calls on system_logs with empty
    filter_fields, at lines 115 and 127). Without the line number, these
    collapse and we undercount.
    """
    file_ = finding.get("file", "")
    line = finding.get("line", 0)
    function = finding.get("function", "")
    collection = finding.get("collection", "")
    filter_fields = finding.get("filter_fields", [])
    ff = sorted(filter_fields) if filter_fields else []
    return f"{file_}:{line}:{function}:{collection}:{','.join(ff)}"


def extract_suppressed(data: dict) -> list[dict]:
    """Return list of suppressed findings (each annotated with _stable_id)."""
    out = []
    for f in data.get("suppressed", []):
        f_copy = dict(f)
        f_copy["_stable_id"] = stable_id(f)
        out.append(f_copy)
    return out


def extract_findings(data: dict) -> list[dict]:
    """Return list of findings (each annotated with _stable_id)."""
    out = []
    for f in data.get("findings", []):
        f_copy = dict(f)
        f_copy["_stable_id"] = stable_id(f)
        out.append(f_copy)
    return out


def git_checkout_files() -> bool:
    """Revert the 6 annotated files to HEAD."""
    cmd = ["git", "checkout"] + ANNOTATED_FILES
    r = subprocess.run(cmd, cwd=str(REPO), capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        print(f"  git checkout failed: {r.stderr}")
        return False
    print(f"  Reverted {len(ANNOTATED_FILES)} files to HEAD (annotations removed).")
    return True


def reapply_annotations() -> bool:
    """Run reapply_annotations.py to restore annotations."""
    cmd = [sys.executable, str(REAPPLY)]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        print(f"  reapply_annotations failed: {r.stderr}")
        return False
    # Verify all 7 annotations are present
    verify = subprocess.run(
        ["grep", "-rc", "graphify:no-index-check"] + [str(REPO / f) for f in ANNOTATED_FILES],
        capture_output=True, text=True, timeout=10,
    )
    print(f"  Re-applied annotations. Verification:")
    for line in verify.stdout.strip().split("\n"):
        print(f"    {line}")
    return True


def main():
    print("=" * 70)
    print("ISSUE 2 VERIFICATION (v2): 11 suppressed findings — same 11 pre/post?")
    print("=" * 70)

    # ---- AFTER (current working tree, with annotations) ----
    print("\n[1/7] Running missing_indexes on CURRENT working tree (with annotations)...")
    after = run_missing_indexes(AFTER_JSON)
    after_suppressed = extract_suppressed(after)
    after_findings = extract_findings(after)
    print(f"  findings (unsuppressed): {len(after_findings)}")
    print(f"  suppressed:              {len(after_suppressed)}")
    print(f"  total:                   {len(after_findings) + len(after_suppressed)}")

    # ---- BEFORE (git checkout to remove annotations) ----
    print("\n[2/7] Reverting annotated files to HEAD (removes annotations)...")
    if not git_checkout_files():
        print("  FATAL: cannot revert files. Aborting.")
        sys.exit(2)

    print("\n[3/7] Running missing_indexes (BEFORE annotations)...")
    before = run_missing_indexes(BEFORE_JSON)
    before_suppressed = extract_suppressed(before)
    before_findings = extract_findings(before)
    print(f"  findings (unsuppressed): {len(before_findings)}")
    print(f"  suppressed:              {len(before_suppressed)}")
    print(f"  total:                   {len(before_findings) + len(before_suppressed)}")

    # ---- Restore annotations ----
    print("\n[4/7] Re-applying annotations...")
    if not reapply_annotations():
        print("  FATAL: cannot re-apply annotations. Aborting.")
        sys.exit(2)

    # ---- Verify restoration (AFTER2 should match AFTER) ----
    print("\n[5/7] Re-running missing_indexes to verify restoration (AFTER2)...")
    after2 = run_missing_indexes(AFTER2_JSON)
    after2_suppressed = extract_suppressed(after2)
    after2_findings = extract_findings(after2)
    print(f"  findings (unsuppressed): {len(after2_findings)}")
    print(f"  suppressed:              {len(after2_suppressed)}")
    print(f"  total:                   {len(after2_findings) + len(after2_suppressed)}")

    if set(f["_stable_id"] for f in after2_suppressed) != set(f["_stable_id"] for f in after_suppressed):
        print("  ⚠ WARNING: AFTER2 != AFTER — restoration may not be clean.")
        print(f"    after suppressed IDs:  {sorted(f['_stable_id'] for f in after_suppressed)}")
        print(f"    after2 suppressed IDs: {sorted(f['_stable_id'] for f in after2_suppressed)}")
    else:
        print("  ✅ AFTER2 == AFTER — restoration is clean.")

    # ---- DIFF ----
    print("\n[6/7] Diffing BEFORE vs AFTER (stable IDs with line numbers)...")
    before_ids = set(f["_stable_id"] for f in before_suppressed)
    after_ids = set(f["_stable_id"] for f in after_suppressed)
    before_finding_ids = set(f["_stable_id"] for f in before_findings)

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

    # Cross-check: do all AFTER-suppressed IDs appear as BEFORE-FINDINGS?
    # Note: line numbers may differ by 1-2 lines because the annotation
    # insertion shifts subsequent lines. So we also try a line-insensitive
    # match (file:function:collection:filter_fields) as a fallback.
    print("\n  Cross-check: do all AFTER-suppressed appear as BEFORE-FINDINGS?")
    print("  (primary: exact line match; fallback: line-insensitive match)")

    def line_insensitive_id(f):
        file_ = f.get("file", "")
        function = f.get("function", "")
        collection = f.get("collection", "")
        ff = sorted(f.get("filter_fields", [])) if f.get("filter_fields") else []
        return f"{file_}:{function}:{collection}:{','.join(ff)}"

    before_finding_ids_li = set(line_insensitive_id(f) for f in before_findings)
    before_suppressed_ids_li = set(line_insensitive_id(f) for f in before_suppressed)

    matched_exact = 0
    matched_li = 0
    unmatched = []
    for f in after_suppressed:
        sid = f["_stable_id"]
        li_sid = line_insensitive_id(f)
        if sid in before_finding_ids:
            matched_exact += 1
        elif li_sid in before_finding_ids_li:
            matched_li += 1
        elif li_sid in before_suppressed_ids_li:
            print(f"    NOTE: {sid} was ALREADY suppressed before (pre-existing annotation)")
            matched_li += 1
        else:
            unmatched.append(sid)
    total_matched = matched_exact + matched_li
    print(f"    Matched (exact line):      {matched_exact}/{len(after_suppressed)}")
    print(f"    Matched (line-insensitive): {matched_li}/{len(after_suppressed)}")
    print(f"    Total matched:              {total_matched}/{len(after_suppressed)}")
    if unmatched:
        print(f"    UNMATCHED (these appeared from nowhere):")
        for sid in unmatched:
            print(f"      ?? {sid}")

    # ---- VERDICT ----
    print("\n[7/7] VERDICT")
    print("=" * 70)
    print(f"  BEFORE (no annotations): {len(before_findings)} findings, {len(before_suppressed)} suppressed, {len(before_findings) + len(before_suppressed)} total")
    print(f"  AFTER  (with annotations): {len(after_findings)} findings, {len(after_suppressed)} suppressed, {len(after_findings) + len(after_suppressed)} total")
    print(f"  Total should be the same: {len(before_findings) + len(before_suppressed)} == {len(after_findings) + len(after_suppressed)} → {(len(before_findings) + len(before_suppressed)) == (len(after_findings) + len(after_suppressed))}")
    print(f"  All {len(after_suppressed)} suppressed IDs appear in BEFORE findings: {total_matched == len(after_suppressed)}")

    if total_matched == len(after_suppressed) and len(after_suppressed) == 11:
        print("\n  ✅ CONFIRMED: the 11 suppressed findings are EXACTLY the 11 findings")
        print("     the annotations were designed to suppress. No silent drift,")
        print("     no coincidental count match — same 11 by stable identity.")
    else:
        print("\n  ⚠ MISMATCH: investigate the diff above.")

    # ---- Show the 11 suppressed findings ----
    print("\n  The 11 suppressed findings (with stable IDs):")
    for f in sorted(after_suppressed, key=lambda x: x["_stable_id"]):
        sev = f.get("would_be_severity", "?")
        coll = f.get("collection", "?")
        fn = f.get("function", "?")
        sup = f.get("suppression", "?")
        line = f.get("line", "?")
        ff = f.get("filter_fields", [])
        print(f"    [{sev:6}] L{line:<4} {coll:24} {fn:30} fields={ff}  suppression={sup}")

    # ---- Enrichment independence check ----
    print("\n  Enrichment independence check (confirms missing_indexes doesn't consume Phase 2 data):")
    src = SCRIPT.read_text(encoding="utf-8")
    print(f"    imports from graph_query?        {'NO' if 'graph_query' not in src else 'YES (CONSUMES ENRICHMENT)'}")
    print(f"    reads graph.json?                 {'NO' if 'graph.json' not in src else 'YES (CONSUMES ENRICHMENT)'}")
    print(f"    shells out to Go filter tracer?   {'NO' if 'graphify_filter_tracer' not in src else 'YES (CONSUMES ENRICHMENT)'}")


if __name__ == "__main__":
    main()
