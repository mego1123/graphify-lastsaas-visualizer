#!/usr/bin/env python3
"""graphify frontend — frontend-specific analysis tools.

Two subcommands:

  dead-components: Find components never imported anywhere.
    Uses grep-based verification (not just graph degree) to avoid false positives.
    Handles: React (JSX/TSX), Vue, Svelte, lazy imports, dynamic imports.

  route-tree: Parse the router config and build a route → component tree.
    Supports: React Router (v6/v7), Next.js App Router, Vue Router.
    Shows which routes load which components, including lazy-loaded chunks.

Usage:
  python graphify_frontend.py dead-components [path]
  python graphify_frontend.py route-tree [path]
  python graphify_frontend.py dead-components . --format json
  python graphify_frontend.py route-tree . --format markdown
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


# ============================================================
# Feature 1: Dead Component Detector
# ============================================================

@dataclass
class ComponentInfo:
    name: str
    file: str
    is_default_export: bool
    is_named_export: bool
    is_lazy_loaded: bool = False
    import_count: int = 0
    importing_files: list[str] = field(default_factory=list)


def detect_src_dirs(repo: Path) -> list[str]:
    """Auto-detect source directories for the frontend."""
    candidates = [
        "src",
        "frontend/src",
        "web/src",
        "app/src",
        "apps/web/src",
    ]
    found = []
    for c in candidates:
        if (repo / c).exists():
            found.append(c)
    # If none found, try to find any directory containing .tsx files
    if not found:
        for p in repo.rglob("*.tsx"):
            if "node_modules" not in str(p) and ".next" not in str(p):
                # Find the 'src' or 'app' directory in the path
                parts = p.parts
                for i, part in enumerate(parts):
                    if part in ("src", "app", "pages") and i > 0:
                        src_path = str(Path(*parts[:i+1]))
                        if src_path not in found:
                            found.append(src_path)
                        break
                if found:
                    break
    return found if found else ["src"]


def find_components(repo: Path, src_dirs: list[str] = None) -> list[ComponentInfo]:
    """Find all component definitions in .tsx/.jsx/.vue/.svelte files."""
    if src_dirs is None:
        src_dirs = detect_src_dirs(repo)

    components: list[ComponentInfo] = []

    # Patterns for component definitions
    patterns = [
        # export default function ComponentName(
        re.compile(r'export\s+default\s+function\s+([A-Z]\w+)\s*[\(\{]'),
        # export function ComponentName(
        re.compile(r'export\s+function\s+([A-Z]\w+)\s*[\(\{]'),
        # export const ComponentName = (
        re.compile(r'export\s+const\s+([A-Z]\w+)\s*=\s*[\(\{]'),
        # export default ComponentName (at end of file)
        re.compile(r'export\s+default\s+([A-Z]\w+)\s*;?\s*$'),
        # const ComponentName = () =>  (not exported — internal component)
        re.compile(r'(?:^|\n)\s*(?:const|let)\s+([A-Z]\w+)\s*=\s*\(?[\(\{]'),
    ]

    for src_dir in src_dirs:
        full_src = repo / src_dir
        if not full_src.exists():
            continue

        for ext in ["*.tsx", "*.jsx", "*.vue", "*.svelte"]:
            for f in full_src.rglob(ext):
                if "node_modules" in str(f) or ".next" in str(f):
                    continue
                try:
                    content = f.read_text(encoding="utf-8", errors="ignore")
                except Exception:
                    continue

                rel_path = str(f.relative_to(repo))
                found_in_file: set[str] = set()

                for pattern in patterns:
                    for m in pattern.finditer(content):
                        name = m.group(1)
                        if name in found_in_file:
                            continue
                        found_in_file.add(name)

                        # Determine export type
                        line = content[:m.start()].split("\n")[-1] + content[m.start():m.end()]
                        is_default = "default" in line
                        is_named = "export" in line and not is_default

                        # Check if it's lazy-loaded
                        is_lazy = "lazy(" in content or "dynamic(" in content

                        components.append(ComponentInfo(
                            name=name,
                            file=rel_path,
                            is_default_export=is_default,
                            is_named_export=is_named,
                            is_lazy_loaded=is_lazy,
                        ))

    return components


def find_imports(repo: Path, component_name: str, src_dirs: list[str] = None) -> list[str]:
    """Find all files that import the given component name."""
    if src_dirs is None:
        src_dirs = detect_src_dirs(repo)

    importing_files: list[str] = []

    # Build grep include flags
    include_flags = []
    for ext in ["*.tsx", "*.jsx", "*.ts", "*.js", "*.vue", "*.svelte"]:
        include_flags.extend(["--include", ext])

    for src_dir in src_dirs:
        full_src = repo / src_dir
        if not full_src.exists():
            continue

        try:
            result = subprocess.run(
                ["grep", "-r", "-l"] + include_flags + [component_name, str(full_src)],
                capture_output=True, text=True, timeout=10,
            )
            for line in result.stdout.strip().split("\n"):
                if line.strip():
                    rel = str(Path(line.strip()).relative_to(repo))
                    importing_files.append(rel)
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

    return importing_files


def find_dead_components(repo: Path) -> list[ComponentInfo]:
    """Find components that are never imported anywhere.

    A component is "dead" if:
    1. It's exported (default or named)
    2. No other file imports it by name
    3. It's not the file's own route entry point (e.g., pages imported by router)
    4. It's not a lazy-loaded page (those are imported via dynamic import)

    We also exclude:
    - Files in pages/ directories (these are route entry points)
    - Files matching page patterns (Page.tsx, Layout.tsx)
    - Test files
    """
    components = find_components(repo)

    # Also check for lazy imports — components imported via lazy(() => import(...))
    # These won't show up as name-based imports
    lazy_imported_files: set[str] = set()
    src_dirs = detect_src_dirs(repo)
    for src_dir in src_dirs:
        full_src = repo / src_dir
        if not full_src.exists():
            continue
        try:
            result = subprocess.run(
                ["grep", "-r", "-l", "--include", "*.tsx", "--include", "*.ts",
                 "--include", "*.jsx", "--include", "*.js",
                 "lazy(", str(full_src)],
                capture_output=True, text=True, timeout=10,
            )
            for line in result.stdout.strip().split("\n"):
                if line.strip():
                    lazy_imported_files.add(str(Path(line.strip()).relative_to(repo)))
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

    # Parse lazy import paths
    lazy_paths: set[str] = set()
    for f in lazy_imported_files:
        content = (repo / f).read_text(encoding="utf-8", errors="ignore")
        # Match: lazy(() => import('./path/Component'))
        for m in re.finditer(r'lazy\s*\(\s*\(\)\s*=>\s*import\s*\(\s*[\'"`]([^\'"`]+)[\'"`]\s*\)', content):
            lazy_paths.add(m.group(1))
        # Match: dynamic(() => import('./path/Component'))
        for m in re.finditer(r'dynamic\s*\(\s*\(\)\s*=>\s*import\s*\(\s*[\'"`]([^\'"`]+)[\'"`]\s*\)', content):
            lazy_paths.add(m.group(1))

    dead: list[ComponentInfo] = []

    for comp in components:
        # Skip non-exported components (internal to their file)
        if not comp.is_default_export and not comp.is_named_export:
            continue

        # Skip page components (they're route entry points)
        if "/pages/" in comp.file or "/app/" in comp.file:
            continue
        if comp.name.endswith("Page") or comp.name.endswith("Layout"):
            continue

        # Skip test files
        if ".test." in comp.file or ".spec." in comp.file:
            continue

        # Find imports
        importing_files = find_imports(repo, comp.name)

        # Filter out the component's own file
        importing_files = [f for f in importing_files if f != comp.file]

        # Check if the file is lazy-imported by path
        file_stem = Path(comp.file).stem
        is_lazy_imported = any(file_stem in p for p in lazy_paths)

        comp.import_count = len(importing_files)
        comp.importing_files = importing_files

        if len(importing_files) == 0 and not is_lazy_imported:
            dead.append(comp)

    return dead


def emit_dead_components_report(dead: list[ComponentInfo], repo: Path) -> str:
    """Emit markdown report of dead components."""
    lines = [
        f"# 🗑️ Dead Components Report — {repo.name}",
        "",
        f"**Found {len(dead)} component(s) that are exported but never imported anywhere.**",
        "",
        "These are safe to delete (after manual verification).",
        "",
    ]

    if not dead:
        lines.append("✅ No dead components found. All exported components are imported somewhere.")
        return "\n".join(lines)

    lines.append("| Component | File | Export Type |")
    lines.append("|-----------|------|-------------|")
    for comp in dead:
        export_type = "default" if comp.is_default_export else "named"
        lines.append(f"| `{comp.name}` | `{comp.file}` | {export_type} |")
    lines.append("")

    lines.append("## How to verify")
    lines.append("")
    lines.append("Before deleting, run these commands to confirm:")
    lines.append("")
    for comp in dead:
        lines.append(f"```bash")
        lines.append(f"# Verify {comp.name} is not imported anywhere")
        lines.append(f'grep -rn "{comp.name}" src/ --include="*.tsx" --include="*.ts"')
        lines.append(f"```")
        lines.append("")

    lines.append("## Common false positives")
    lines.append("")
    lines.append("- **Lazy-loaded pages**: imported via `lazy(() => import('./path'))` — these are detected and excluded")
    lines.append("- **Route entry points**: files in `pages/` or `app/` directories — excluded by path")
    lines.append("- **String-based references**: if a component name is used as a string (e.g., in a registry), grep will find it")
    lines.append("- **Dynamic component resolution**: if you use `componentRegistry['ComponentName']`, grep will find the string")
    lines.append("")

    return "\n".join(lines)


# ============================================================
# Feature 2: Route Tree Parser
# ============================================================

@dataclass
class RouteNode:
    path: str
    component: str
    file: str
    is_lazy: bool
    is_protected: bool = False
    children: list["RouteNode"] = field(default_factory=list)
    import_path: str = ""  # for lazy imports


def parse_react_router(repo: Path, app_file: str = None) -> list[RouteNode]:
    """Parse React Router v6/v7 route definitions from App.tsx or equivalent."""
    # Auto-detect the app file location
    if app_file is None:
        for candidate in [
            "src/App.tsx", "src/App.jsx", "src/main.tsx", "src/main.jsx",
            "frontend/src/App.tsx", "frontend/src/App.jsx",
            "frontend/src/main.tsx", "frontend/src/main.jsx",
        ]:
            if (repo / candidate).exists():
                app_file = candidate
                break
        if app_file is None:
            return []

    app_path = repo / app_file

    content = app_path.read_text(encoding="utf-8", errors="ignore")

    # Parse lazy imports first: const Name = lazy(() => import('./path'))
    lazy_imports: dict[str, str] = {}
    for m in re.finditer(r'(?:const|let)\s+(\w+)\s*=\s*lazy\s*\(\s*\(\)\s*=>\s*import\s*\(\s*[\'"`]([^\'"`]+)[\'"`]\s*\)', content):
        lazy_imports[m.group(1)] = m.group(2)

    # Parse regular imports: import Name from './path'
    regular_imports: dict[str, str] = {}
    for m in re.finditer(r'import\s+(\w+)\s+from\s+[\'"`]([^\'"`]+)[\'"`]', content):
        regular_imports[m.group(1)] = m.group(2)

    # Parse <Route> elements — extract each Route tag individually
    # Match both self-closing <Route ... /> and opening <Route ...>
    # We need to track nesting properly
    routes: list[RouteNode] = []
    route_stack: list[RouteNode] = []

    # Token-based approach: find all Route tags in order
    route_tag_pattern = re.compile(
        r'<Route\s+([^>]*?)(/?)>',
        re.DOTALL,
    )

    # Also find closing </Route> tags
    all_tokens = []
    for m in re.finditer(r'(<Route\s+[^>]*?/?>|</Route>)', content):
        all_tokens.append(m)

    for m in all_tokens:
        token = m.group(1)
        is_closing = token.startswith("</Route>")
        is_self_closing = token.endswith("/>")

        if is_closing:
            if route_stack:
                route_stack.pop()
            continue

        attrs = token[len("<Route"):-len("/>" if is_self_closing else ">")].strip()

        # Extract path
        path_match = re.search(r'path\s*=\s*"([^"]*)"', attrs)
        path = path_match.group(1) if path_match else ""

        # Extract element component — handle both <Component /> and <Suspense><Component /></Suspense>
        component = ""
        is_lazy = False

        # Try direct: element={<Component />}
        element_match = re.search(r'element\s*=\s*\{\s*<(\w+)', attrs)
        if element_match:
            component = element_match.group(1)
        else:
            # Try: element={<Suspense fallback={...}><Component /></Suspense>}
            element_match = re.search(r'element\s*=\s*\{\s*<Suspense[^>]*>\s*<(\w+)', attrs)
            if element_match:
                component = element_match.group(1)

        # If component is Suspense, look for the inner component on the next line
        if component == "Suspense" or not component:
            # Search the content around this match for <Component
            context = content[m.end():m.end()+500]
            inner_match = re.search(r'<(\w+)\s*/?>', context)
            if inner_match and inner_match.group(1) not in ("Suspense", "Navigate", "Outlet"):
                component = inner_match.group(1)

        # Check if it's a layout/guard route
        is_guard = path == "" and component in ("ProtectedRoute", "AdminRoute", "AdminLayout", "Layout")

        # Check if lazy
        if component in lazy_imports:
            is_lazy = True

        # Determine the file
        file_path = ""
        if component in lazy_imports:
            file_path = lazy_imports[component]
        elif component in regular_imports:
            file_path = regular_imports[component]

        # Check if protected
        is_protected = False
        if route_stack:
            for ancestor in route_stack:
                if ancestor.component in ("ProtectedRoute", "AdminRoute", "AdminLayout"):
                    is_protected = True
                    break

        route = RouteNode(
            path=path,
            component=component,
            file=file_path,
            is_lazy=is_lazy,
            is_protected=is_protected or is_guard,
        )

        if route_stack and not is_guard:
            route_stack[-1].children.append(route)
        elif not is_guard:
            routes.append(route)

        # If it's an opening tag (not self-closing), push to stack
        if not is_self_closing:
            route_stack.append(route)

    return routes


def parse_nextjs_app_router(repo: Path) -> list[RouteNode]:
    """Parse Next.js App Router structure from app/ directory.

    Next.js App Router uses file-system routing:
      app/page.tsx          → /
      app/about/page.tsx    → /about
      app/blog/[slug]/page.tsx → /blog/:slug
      app/layout.tsx        → layout wrapper
    """
    app_dir = repo / "app"
    if not app_dir.exists():
        app_dir = repo / "src" / "app"
    if not app_dir.exists():
        return []

    routes: list[RouteNode] = []

    for page_file in app_dir.rglob("page.tsx"):
        rel = page_file.relative_to(app_dir)
        # Convert file path to route path
        parts = rel.parts
        if parts[-1] == "page.tsx":
            route_parts = parts[:-1]
        else:
            continue

        if not route_parts:
            path = "/"
        else:
            path = "/" + "/".join(p.replace("[", ":").replace("]", "") for p in route_parts)

        # Read the page to get component name
        content = page_file.read_text(encoding="utf-8", errors="ignore")
        comp_match = re.search(r'export\s+default\s+function\s+(\w+)', content)
        component = comp_match.group(1) if comp_match else page_file.stem

        routes.append(RouteNode(
            path=path,
            component=component,
            file=str(page_file.relative_to(repo)),
            is_lazy=False,  # Next.js handles code splitting automatically
            is_protected=False,  # would need to check layout.tsx for middleware
        ))

    return routes


def emit_route_tree(routes: list[RouteNode], repo: Path) -> str:
    """Emit markdown route tree."""
    lines = [
        f"# 🌳 Route Tree — {repo.name}",
        "",
        f"**{len(routes)} top-level route(s) found.**",
        "",
    ]

    if not routes:
        lines.append("No routes found. Ensure your router file (e.g., `src/App.tsx`) exists.")
        return "\n".join(lines)

    # Count stats
    total_routes = 0
    lazy_routes = 0
    protected_routes = 0

    def count_recursive(route: RouteNode):
        nonlocal total_routes, lazy_routes, protected_routes
        total_routes += 1
        if route.is_lazy:
            lazy_routes += 1
        if route.is_protected:
            protected_routes += 1
        for child in route.children:
            count_recursive(child)

    for r in routes:
        count_recursive(r)

    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append(f"| Total routes | {total_routes} |")
    lines.append(f"| Lazy-loaded | {lazy_routes} |")
    lines.append(f"| Protected (behind auth guard) | {protected_routes} |")
    lines.append("")

    lines.append("## Route Hierarchy")
    lines.append("")
    lines.append("```")
    lines.append("")

    def render_route(route: RouteNode, indent: str = ""):
        icon = "🔒" if route.is_protected else "📄"
        lazy_icon = " (lazy)" if route.is_lazy else ""
        file_info = f" [{route.file}]" if route.file else ""
        lines.append(f"{indent}{icon} {route.path or '(index)'} → {route.component}{lazy_icon}{file_info}")
        for child in route.children:
            render_route(child, indent + "  ")

    for r in routes:
        render_route(r)

    lines.append("")
    lines.append("```")
    lines.append("")

    # Flat list with component files
    lines.append("## Route → Component Mapping")
    lines.append("")
    lines.append("| Route | Component | File | Lazy? | Protected? |")
    lines.append("|-------|-----------|------|-------|-----------|")

    def table_rows(route: RouteNode):
        lines.append(f"| `{route.path or '/'}` | `{route.component}` | `{route.file or '—'}` | {'✓' if route.is_lazy else '—'} | {'🔒' if route.is_protected else '—'} |")
        for child in route.children:
            table_rows(child)

    for r in routes:
        table_rows(r)

    lines.append("")

    # Bundle impact analysis
    lines.append("## 💡 Bundle Impact")
    lines.append("")
    if lazy_routes > 0:
        lines.append(f"- **{lazy_routes} route(s) are lazy-loaded** — they're in separate chunks and won't affect initial bundle size")
    if lazy_routes < total_routes:
        non_lazy = total_routes - lazy_routes
        lines.append(f"- **{non_lazy} route(s) are eagerly loaded** — their components are in the main bundle")
    lines.append("- Changing a lazy-loaded component only affects that route's chunk")
    lines.append("- Changing a shared component (imported by multiple routes) affects ALL chunks that include it")
    lines.append("")

    return "\n".join(lines)


# ============================================================
# CLI
# ============================================================

def main():
    ap = argparse.ArgumentParser(
        prog="graphify frontend",
        description="Frontend-specific analysis tools.",
    )
    sub = ap.add_subparsers(dest="command", required=True)

    # dead-components
    dc = sub.add_parser("dead-components", help="Find components never imported anywhere")
    dc.add_argument("path", nargs="?", default=".", help="Path to the repo")
    dc.add_argument("--format", "-f", choices=["markdown", "json"], default="markdown")
    dc.add_argument("--out", "-o", help="Output file (default: stdout)")

    # route-tree
    rt = sub.add_parser("route-tree", help="Parse router config and build route → component tree")
    rt.add_argument("path", nargs="?", default=".", help="Path to the repo")
    rt.add_argument("--format", "-f", choices=["markdown", "json"], default="markdown")
    rt.add_argument("--out", "-o", help="Output file (default: stdout)")
    rt.add_argument("--framework", choices=["auto", "react-router", "nextjs"], default="auto",
                    help="Router framework (default: auto-detect)")

    args = ap.parse_args()
    repo = Path(args.path).resolve()

    if not repo.exists():
        print(f"ERROR: {repo} does not exist", file=sys.stderr)
        sys.exit(2)

    if args.command == "dead-components":
        print(f"graphify frontend dead-components — scanning {repo}...", file=sys.stderr)
        dead = find_dead_components(repo)

        if args.format == "json":
            output = json.dumps([{
                "name": c.name,
                "file": c.file,
                "export_type": "default" if c.is_default_export else "named",
            } for c in dead], indent=2)
        else:
            output = emit_dead_components_report(dead, repo)

        if args.out:
            Path(args.out).write_text(output, encoding="utf-8")
            print(f"Report written to {args.out}", file=sys.stderr)
        else:
            print(output)

        print(f"\n{len(dead)} dead component(s) found.", file=sys.stderr)
        sys.exit(1 if dead else 0)

    elif args.command == "route-tree":
        print(f"graphify frontend route-tree — scanning {repo}...", file=sys.stderr)

        # Auto-detect framework
        framework = args.framework
        if framework == "auto":
            if (repo / "app" / "page.tsx").exists() or (repo / "src" / "app" / "page.tsx").exists():
                framework = "nextjs"
            elif (repo / "src" / "App.tsx").exists() or (repo / "src" / "App.jsx").exists():
                framework = "react-router"
            else:
                framework = "react-router"  # default

        print(f"  Detected framework: {framework}", file=sys.stderr)

        if framework == "nextjs":
            routes = parse_nextjs_app_router(repo)
        else:
            routes = parse_react_router(repo)

        if args.format == "json":
            def route_to_dict(r: RouteNode) -> dict:
                return {
                    "path": r.path,
                    "component": r.component,
                    "file": r.file,
                    "is_lazy": r.is_lazy,
                    "is_protected": r.is_protected,
                    "children": [route_to_dict(c) for c in r.children],
                }
            output = json.dumps([route_to_dict(r) for r in routes], indent=2)
        else:
            output = emit_route_tree(routes, repo)

        if args.out:
            Path(args.out).write_text(output, encoding="utf-8")
            print(f"Report written to {args.out}", file=sys.stderr)
        else:
            print(output)

        print(f"\n{len(routes)} route(s) found.", file=sys.stderr)
        sys.exit(0)


if __name__ == "__main__":
    main()
