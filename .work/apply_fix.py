#!/usr/bin/env python3
"""
Apply targeted error-handling fixes to Go handler files.
Preserves original tab indentation by using literal \t in replacement strings.
Each fix is a (old, new) tuple applied via str.replace() with a count check.
"""
import sys
import os
import subprocess

REPO = "/home/z/my-project/repos/lastsaas/backend"
HANDLERS = os.path.join(REPO, "internal", "api", "handlers")

def apply_fixes(file_rel, fixes):
    """Apply a list of (old, new) replacements to a file. Asserts each occurs exactly once."""
    path = os.path.join(HANDLERS, file_rel)
    with open(path) as f:
        content = f.read()
    for i, (old, new, desc) in enumerate(fixes, 1):
        cnt = content.count(old)
        if cnt != 1:
            print(f"  ERROR [{file_rel} #{i} {desc}]: expected 1 match, found {cnt}")
            print(f"  old (first 200 chars): {old[:200]!r}")
            return False
        content = content.replace(old, new, 1)
    with open(path, "w") as f:
        f.write(content)
    print(f"  Applied {len(fixes)} fixes to {file_rel}")
    return True

def go_build(pkg="./internal/api/handlers/"):
    """Verify the handlers package builds."""
    r = subprocess.run(
        ["/home/z/.local/go/bin/go", "build", pkg],
        cwd=REPO, capture_output=True, text=True,
    )
    if r.returncode != 0:
        print(f"  BUILD FAILED:\n{r.stdout}\n{r.stderr}")
        return False
    print(f"  BUILD OK")
    return True

if __name__ == "__main__":
    pass
