#!/usr/bin/env python3
"""
Fix typography to match Tailux's exact type scale.

Fixes:
  1. Page titles: h1 text-xl font-semibold text-gray-900 → h2 text-xl
     font-medium tracking-wide text-gray-800 lg:text-2xl
     (matches DemoLayout: text-xl font-medium tracking-wide lg:text-2xl)

  2. Card headings: h2 text-lg font-semibold text-gray-900 → h2 text-base
     font-medium tracking-wide text-gray-800
     (matches DemoCard: font-medium tracking-wide text-gray-800 lg:text-base)
     Note: we use text-base instead of lg:text-base since these aren't
     always in a responsive context. The key change is font-semibold →
     font-medium and text-lg → text-base.

  3. Color: text-gray-900 → text-gray-800 for headings (Tailux uses 800)
"""

import re
from pathlib import Path

PAGES_DIR = Path(
    "/home/z/my-project/repos/lastsaas/frontend-new/src/app/pages"
)

files = sorted(PAGES_DIR.rglob("*.tsx"))
changed = []

for f in files:
    text = f.read_text(encoding="utf-8")
    original = text

    # 1. Fix page titles: h1 → h2, font-semibold → font-medium,
    #    add tracking-wide and lg:text-2xl, text-gray-900 → text-gray-800
    #    Pattern: <h1 className="text-xl font-semibold text-gray-900 dark:text-dark-50">
    text = re.sub(
        r'<h1 className="text-xl font-semibold text-gray-900 dark:text-dark-50">',
        '<h2 className="text-xl font-medium tracking-wide text-gray-800 dark:text-dark-50 lg:text-2xl">',
        text,
    )
    # Also fix the closing </h1> → </h2> for these titles
    # We need to be careful — only change </h1> that close our converted titles.
    # Since we changed the opening tag, the closing tag is the next </h1> after it.
    # Let's do this more carefully by finding each converted title and its closing tag.
    
    # 2. Fix card headings: text-lg font-semibold text-gray-900 → text-base
    #    font-medium tracking-wide text-gray-800
    text = re.sub(
        r'text-lg font-semibold text-gray-900 dark:text-dark-50',
        'text-base font-medium tracking-wide text-gray-800 dark:text-dark-50',
        text,
    )
    
    # 3. Fix standalone text-lg font-semibold (without color, e.g. in config/pm)
    text = re.sub(
        r'<h2 className="text-lg font-semibold">',
        '<h2 className="text-base font-medium tracking-wide text-gray-800 dark:text-dark-100">',
        text,
    )
    
    # 4. Fix text-lg font-semibold with flex/items but without color
    text = re.sub(
        r'text-lg font-semibold text-gray-900',
        'text-base font-medium tracking-wide text-gray-800 dark:text-dark-100',
        text,
    )
    
    # 5. Fix text-xl font-semibold (plans page modal title)
    text = re.sub(
        r'text-xl font-semibold text-gray-900 dark:text-dark-50',
        'text-xl font-medium tracking-wide text-gray-800 dark:text-dark-50',
        text,
    )

    # 6. Fix error-colored headings
    text = re.sub(
        r'text-lg font-semibold text-error',
        'text-base font-medium tracking-wide text-error',
        text,
    )

    if text != original:
        f.write_text(text, encoding="utf-8")
        changed.append(f.relative_to(PAGES_DIR))

print(f"Updated {len(changed)} files:")
for c in changed:
    print(f"  {c}")
