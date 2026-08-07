#!/usr/bin/env python3
"""Re-apply // graphify:no-index-check annotations to lastsaas Go files.

The annotations were lost when `git stash pop` corrupted whitespace.
This script re-inserts them with proper tab indentation.

Each annotation is inserted at the function level (above the func keyword)
or as a line_above (immediately above the Find/CountDocuments call).
"""
from pathlib import Path
import re

REPO = Path("/home/z/my-project/repos/lastsaas/backend")

# (file, function_or_pattern, annotation_text, placement)
# placement: "function" = above the func keyword (godoc-style)
#             "line_above" = immediately above the Find/CountDocuments/InsertOne call
ANNOTATIONS = [
    # 1. cmd_stats.go — cmdStats (function-level)
    {
        "file": "cmd/lastsaas/cmd_stats.go",
        "function": "cmdStats",
        "text": [
            "// graphify:no-index-check — CLI stats command: bounded admin query",
            "// (counts active users for the `lastsaas stats` CLI report).",
        ],
        "placement": "line_above",
        "anchor_pattern": r"activeUsers,\s*err\s*:=\s*database\.Users\(\)\.CountDocuments",
    },
    # 2. billing.go — ListTransactions (function-level)
    {
        "file": "internal/api/handlers/billing.go",
        "function": "ListTransactions",
        "text": [
            "// graphify:no-index-check — tenant-scoped query whose filter is",
            "// built on a separate line and passed by variable; the tenantId",
            "// index covers it but the static analyzer can't see the variable's fields.",
        ],
        "placement": "function",
    },
    # 3. tenant.go — GetActivity (function-level)
    {
        "file": "internal/api/handlers/tenant.go",
        "function": "GetActivity",
        "text": [
            "// graphify:no-index-check — admin activity-log query whose filter",
            "// is built dynamically from query params via filter[\"...\"] patterns",
            "// the regex parser can't fully trace.",
        ],
        "placement": "function",
    },
    # 4. logs.go — ListLogs (function-level)
    {
        "file": "internal/api/handlers/logs.go",
        "function": "ListLogs",
        "text": [
            "// graphify:no-index-check — admin log query whose filter is built",
            "// dynamically via h.buildFilter(q).",
        ],
        "placement": "function",
    },
    # 5. bundles.go — ListBundlesPublic (function-level — simpler/more reliable than line_above)
    {
        "file": "internal/api/handlers/bundles.go",
        "function": "ListBundlesPublic",
        "text": [
            "// graphify:no-index-check — public endpoint, ~10-doc static catalog",
        ],
        "placement": "function",
    },
    # 6. telemetry/service.go — FunnelMetrics (function-level)
    {
        "file": "internal/telemetry/service.go",
        "function": "FunnelMetrics",
        "text": [
            "// graphify:no-index-check — admin analytics query whose filter is",
            "// built dynamically via mergeBson(dateFilter, bson.M{...}) and",
            "// the regex parser can't see the merged fields.",
        ],
        "placement": "function",
    },
    # 7. telemetry/service.go — CustomEventSummary (function-level)
    {
        "file": "internal/telemetry/service.go",
        "function": "CustomEventSummary",
        "text": [
            "// graphify:no-index-check — admin telemetry query whose filter is",
            "// built dynamically and the regex parser can't trace the field names.",
        ],
        "placement": "function",
    },
]


def find_function_line(lines: list[str], func_name: str) -> int:
    """Find the line index (0-based) where `func ... funcName(` appears."""
    pat = re.compile(rf"^\s*func\s+(\([^)]+\)\s+)?{re.escape(func_name)}\b")
    for i, line in enumerate(lines):
        if pat.search(line):
            return i
    return -1


def find_anchor_line(lines: list[str], pattern: str) -> int:
    """Find the line index (0-based) matching the anchor pattern."""
    pat = re.compile(pattern)
    for i, line in enumerate(lines):
        if pat.search(line):
            return i
    return -1


def apply_annotation(file_path: Path, ann: dict) -> bool:
    """Apply one annotation. Returns True if applied, False if skipped."""
    text = file_path.read_text(encoding="utf-8")
    lines = text.split("\n")

    if ann["placement"] == "function":
        func_line = find_function_line(lines, ann["function"])
        if func_line < 0:
            print(f"  SKIP {ann['file']}::{ann['function']} — function not found")
            return False
        # Walk backward to find the end of the existing doc comment (if any)
        insert_at = func_line
        # If there's a doc comment above, insert ABOVE the doc comment's first //
        # Actually, the convention is: insert immediately above the `func` keyword
        # (after any existing doc comment). But to be safe, insert immediately
        # above the func line.
        new_lines = []
        for j, line in enumerate(lines):
            if j == func_line:
                for ann_line in ann["text"]:
                    new_lines.append(ann_line)
            new_lines.append(line)
        file_path.write_text("\n".join(new_lines), encoding="utf-8")
        print(f"  OK   {ann['file']}::{ann['function']} — function-level annotation inserted at line {func_line + 1}")
        return True

    elif ann["placement"] == "line_above":
        anchor_idx = find_anchor_line(lines, ann["anchor_pattern"])
        if anchor_idx < 0:
            print(f"  SKIP {ann['file']}::{ann['function']} — anchor pattern not found")
            return False
        # Detect the indentation of the anchor line and apply it to the
        # annotation lines so the insertion matches surrounding code.
        anchor_line = lines[anchor_idx]
        indent = ""
        for ch in anchor_line:
            if ch in (" ", "\t"):
                indent += ch
            else:
                break
        new_lines = []
        for j, line in enumerate(lines):
            if j == anchor_idx:
                for ann_line in ann["text"]:
                    # If the annotation text already starts with whitespace,
                    # use it as-is; otherwise prepend the detected indent.
                    if ann_line.startswith((" ", "\t")):
                        new_lines.append(ann_line)
                    else:
                        new_lines.append(indent + ann_line)
            new_lines.append(line)
        file_path.write_text("\n".join(new_lines), encoding="utf-8")
        print(f"  OK   {ann['file']}::{ann['function']} — line_above annotation inserted at line {anchor_idx + 1}")
        return True

    return False


def main():
    print("Re-applying // graphify:no-index-check annotations...")
    applied = 0
    for ann in ANNOTATIONS:
        fp = REPO / ann["file"]
        if not fp.exists():
            print(f"  SKIP {ann['file']} — file not found")
            continue
        if apply_annotation(fp, ann):
            applied += 1
    print(f"\nApplied {applied}/{len(ANNOTATIONS)} annotations.")

    # Verify with grep
    print("\nVerification (grep):")
    import subprocess
    r = subprocess.run(
        ["grep", "-rn", "graphify:no-index-check", str(REPO)],
        capture_output=True, text=True,
    )
    print(r.stdout)


if __name__ == "__main__":
    main()
