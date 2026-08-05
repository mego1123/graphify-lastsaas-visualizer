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
# Feature 3: Bundle Impact Analyzer
# ============================================================

@dataclass
class BundleImpactResult:
    component: str
    file: str
    affected_routes: list[dict]  # [{path, component, is_lazy, file}]
    affected_chunks: list[str]   # chunk names (e.g., "settings", "admin-dashboard")
    shared_components: list[dict]  # components that import this one and are themselves imported by routes
    risk_level: str  # LOW, MEDIUM, HIGH


def build_import_graph(repo: Path) -> dict[str, list[str]]:
    """Build a reverse import graph: file → list of files that import it.

    For each .tsx/.ts file, parse its import statements and record
    which files it imports. Then reverse the graph so we can look up
    "who imports this file?" efficiently.
    """
    src_dirs = detect_src_dirs(repo)
    # Forward graph: importer → [imported files]
    forward: dict[str, list[str]] = {}
    # All source files
    all_files: list[Path] = []

    for src_dir in src_dirs:
        full_src = repo / src_dir
        if not full_src.exists():
            continue
        for ext in ["*.tsx", "*.ts", "*.jsx", "*.js"]:
            for f in full_src.rglob(ext):
                if "node_modules" in str(f) or ".next" in str(f):
                    continue
                all_files.append(f)
                rel = str(f.relative_to(repo))
                forward[rel] = []
                try:
                    content = f.read_text(encoding="utf-8", errors="ignore")
                except Exception:
                    continue
                # Parse import paths: import X from './path' or import('./path')
                for m in re.finditer(r'(?:import\s+[^;]+from\s+|import\s*\(\s*)[\'"`]([^\'"`]+)[\'"`]', content):
                    import_path = m.group(1)
                    if import_path.startswith(".") or import_path.startswith("/"):
                        # Resolve relative path
                        resolved = (f.parent / import_path).resolve()
                        # Try with extensions
                        for ext2 in [".tsx", ".ts", ".jsx", ".js", "/index.tsx", "/index.ts"]:
                            candidate = resolved.with_suffix(ext2) if not ext2.startswith("/") else resolved.parent / f"index{ext2}"
                            if candidate.exists():
                                try:
                                    rel2 = str(candidate.relative_to(repo))
                                    forward[rel].append(rel2)
                                except ValueError:
                                    pass
                                break

    # Reverse graph: imported → [importers]
    reverse: dict[str, list[str]] = defaultdict(list)
    for importer, imported_list in forward.items():
        for imported in imported_list:
            reverse[imported].append(importer)

    return dict(reverse)


def analyze_bundle_impact(repo: Path, component_name: str) -> Optional[BundleImpactResult]:
    """Analyze the bundle impact of changing a component.

    Traces: component → importers → routes (lazy or eager)
    Shows which routes' bundles would be affected by a change.
    """
    # Find the component's file
    components = find_components(repo)
    comp = next((c for c in components if c.name == component_name), None)
    if not comp:
        return None

    # Build reverse import graph
    reverse_graph = build_import_graph(repo)

    # Parse routes to know which files are route entry points
    routes = parse_react_router(repo)
    if not routes:
        routes = parse_nextjs_app_router(repo)

    # Flatten routes to {file → route_path}
    route_files: dict[str, list[dict]] = defaultdict(list)
    def collect_route_files(route: RouteNode):
        if route.file:
            # Resolve the import path to a real file
            # route.file is like './pages/auth/LoginPage'
            app_file = None
            for candidate in ["src/App.tsx", "frontend/src/App.tsx"]:
                if (repo / candidate).exists():
                    app_file = repo / candidate
                    break
            if app_file:
                resolved = (app_file.parent / route.file).resolve()
                for ext in [".tsx", ".ts", ".jsx", ".js"]:
                    candidate = resolved.with_suffix(ext)
                    if candidate.exists():
                        try:
                            rel = str(candidate.relative_to(repo))
                            route_files[rel].append({
                                "path": route.path,
                                "component": route.component,
                                "is_lazy": route.is_lazy,
                                "file": rel,
                            })
                        except ValueError:
                            pass
                        break
        for child in route.children:
            collect_route_files(child)

    for r in routes:
        collect_route_files(r)

    # BFS: find all files that transitively import this component's file
    # Start from the component's file, walk up the reverse import graph
    affected_routes: list[dict] = []
    affected_chunks: set[str] = set()
    visited: set[str] = set()
    queue: list[str] = [comp.file]

    while queue:
        current = queue.pop(0)
        if current in visited:
            continue
        visited.add(current)

        # Is this file a route entry point?
        if current in route_files:
            for r in route_files[current]:
                if r not in affected_routes:
                    affected_routes.append(r)
                    # Determine chunk name
                    if r["is_lazy"]:
                        chunk_name = r["path"].strip("/").replace("/", "-") or "root"
                        affected_chunks.add(f"chunk:{chunk_name}")
                    else:
                        affected_chunks.add("main bundle")

        # Walk up: who imports this file?
        importers = reverse_graph.get(current, [])
        for imp in importers:
            if imp not in visited:
                queue.append(imp)

    # Find shared components (components imported by multiple routes)
    shared: list[dict] = []
    if len(affected_routes) > 1:
        shared.append({
            "component": component_name,
            "file": comp.file,
            "route_count": len(affected_routes),
            "note": "This component is imported by multiple routes — changes affect all of them",
        })

    # Risk assessment
    if len(affected_routes) >= 5:
        risk = "HIGH"
    elif len(affected_routes) >= 2:
        risk = "MEDIUM"
    else:
        risk = "LOW"

    return BundleImpactResult(
        component=component_name,
        file=comp.file,
        affected_routes=affected_routes,
        affected_chunks=list(affected_chunks),
        shared_components=shared,
        risk_level=risk,
    )


def emit_bundle_impact_report(result: BundleImpactResult, repo: Path) -> str:
    """Emit markdown report for bundle impact analysis."""
    risk_icon = {"LOW": "🟢", "MEDIUM": "🟡", "HIGH": "🟠"}[result.risk_level]

    lines = [
        f"# {risk_icon} Bundle Impact: `{result.component}`",
        "",
        f"**File:** `{result.file}`",
        f"**Risk Level:** {result.risk_level}",
        f"**Affected routes:** {len(result.affected_routes)}",
        f"**Affected bundles:** {len(result.affected_chunks)}",
        "",
    ]

    if result.affected_routes:
        lines.append("## Affected Routes")
        lines.append("")
        lines.append("| Route | Component | Lazy? | Bundle |")
        lines.append("|-------|-----------|-------|--------|")
        for r in result.affected_routes:
            lazy = "✓ lazy" if r["is_lazy"] else "eager"
            chunk = f"chunk:{r['path'].strip('/').replace('/', '-')}" if r["is_lazy"] else "main bundle"
            lines.append(f"| `{r['path']}` | `{r['component']}` | {lazy} | `{chunk}` |")
        lines.append("")

    if result.affected_chunks:
        lines.append("## Affected Bundles")
        lines.append("")
        for chunk in result.affected_chunks:
            lines.append(f"- `{chunk}`")
        lines.append("")

    if result.shared_components:
        lines.append("## ⚠️ Shared Component Warning")
        lines.append("")
        for s in result.shared_components:
            lines.append(f"- `{s['component']}` is imported by **{s['route_count']} routes** — changes ripple across all of them")
        lines.append("")

    lines.append("## Recommendations")
    lines.append("")
    if result.risk_level == "HIGH":
        lines.append("- 🔴 **High impact** — this component is used by many routes")
        lines.append("- Consider whether the change is necessary")
        lines.append("- If changing, test all affected routes")
        lines.append("- Consider extracting shared logic to avoid coupling")
    elif result.risk_level == "MEDIUM":
        lines.append("- 🟡 **Medium impact** — changes affect a few routes")
        lines.append("- Test the affected routes after changes")
    else:
        lines.append("- 🟢 **Low impact** — only one route is affected")
        lines.append("- Standard testing is sufficient")

    lines.append("")
    lines.append("---")
    lines.append(f"_Generated by `graphify frontend bundle-impact` — "
                 f"{len(result.affected_routes)} route(s), {len(result.affected_chunks)} bundle(s)_")

    return "\n".join(lines)


# ============================================================
# Feature 4: Prop Drilling Detector
# ============================================================

@dataclass
class PropFlow:
    prop_name: str
    source_file: str       # where the prop originates (Context/state)
    source_component: str  # component that provides the prop
    chain: list[dict]      # [{component, file, uses_prop (bool)}]
    depth: int


def find_prop_sources(repo: Path) -> list[dict]:
    """Find where props originate — Context providers, useState, props from API calls.

    Returns a list of {prop_name, component, file, source_type} where source_type
    is one of: context, useState, useReducer, props (from parent).
    """
    src_dirs = detect_src_dirs(repo)
    sources: list[dict] = []

    for src_dir in src_dirs:
        full_src = repo / src_dir
        if not full_src.exists():
            continue

        for ext in ["*.tsx", "*.jsx"]:
            for f in full_src.rglob(ext):
                if "node_modules" in str(f):
                    continue
                try:
                    content = f.read_text(encoding="utf-8", errors="ignore")
                except Exception:
                    continue

                rel = str(f.relative_to(repo))

                # Find Context usage: const { prop } = useSomeContext()
                for m in re.finditer(r'(?:const|let)\s*\{\s*([^}]+)\s*\}\s*=\s*(use\w+)\s*\(', content):
                    props = [p.strip() for p in m.group(1).split(",")]
                    hook = m.group(2)
                    for prop in props:
                        # Skip destructured renames: "prop: alias"
                        prop = prop.split(":")[0].strip()
                        if prop and prop[0].islower():
                            sources.append({
                                "prop_name": prop,
                                "component": "",  # will be filled later
                                "file": rel,
                                "source_type": "context",
                                "hook": hook,
                            })

                # Find useState: const [prop, setProp] = useState(...)
                for m in re.finditer(r'(?:const|let)\s*\[\s*(\w+)\s*,\s*(\w+)\s*\]\s*=\s*useState', content):
                    prop = m.group(1)
                    if prop[0].islower():
                        sources.append({
                            "prop_name": prop,
                            "component": "",
                            "file": rel,
                            "source_type": "useState",
                            "hook": "useState",
                        })

    return sources


def find_prop_passing(repo: Path) -> list[dict]:
    """Find places where props are passed to child components.

    Looks for: <ChildComponent propName={propName} ... />
    Returns: [{prop_name, from_component, from_file, to_component, to_file}]
    """
    src_dirs = detect_src_dirs(repo)
    passes: list[dict] = []

    for src_dir in src_dirs:
        full_src = repo / src_dir
        if not full_src.exists():
            continue

        for ext in ["*.tsx", "*.jsx"]:
            for f in full_src.rglob(ext):
                if "node_modules" in str(f):
                    continue
                try:
                    content = f.read_text(encoding="utf-8", errors="ignore")
                except Exception:
                    continue

                rel = str(f.relative_to(repo))

                # Find JSX elements with prop passing: <Component propName={propName}
                # Match: <CapitalWord ... propName={propName} ... >
                for m in re.finditer(r'<([A-Z]\w+)[^>]*?\s(\w+)=\{(\w+)\}', content):
                    child_component = m.group(1)
                    attr_name = m.group(2)
                    prop_value = m.group(3)

                    # Only track if the attribute name matches the prop value
                    # (i.e., passing a prop through unchanged: prop={prop})
                    if attr_name == prop_value and prop_value[0].islower():
                        passes.append({
                            "prop_name": prop_value,
                            "attr_name": attr_name,
                            "from_file": rel,
                            "to_component": child_component,
                        })

    return passes


def detect_prop_drilling(repo: Path, min_depth: int = 3) -> list[PropFlow]:
    """Detect props that are drilled through multiple layers.

    A prop is "drilled" when:
    1. It originates from a Context/useState in component A
    2. A passes it to B as a prop
    3. B passes it to C as a prop (without using it itself)
    4. C passes it to D as a prop
    5. Depth >= min_depth (default 3)

    We trace each prop through the component tree.
    """
    sources = find_prop_sources(repo)
    passes = find_prop_passing(repo)

    # Build a map: prop_name → list of passes
    passes_by_prop: dict[str, list[dict]] = defaultdict(list)
    for p in passes:
        passes_by_prop[p["prop_name"]].append(p)

    # Build a map: file → component name (for resolving "from_file" to component)
    file_to_component: dict[str, str] = {}
    components = find_components(repo)
    for c in components:
        file_to_component[c.file] = c.name

    # For each source, trace the prop through passes
    drilling: list[PropFlow] = []

    for source in sources:
        prop_name = source["prop_name"]
        source_component = file_to_component.get(source["file"], "")
        if not source_component:
            continue

        # BFS through passes
        chain: list[dict] = [{
            "component": source_component,
            "file": source["file"],
            "uses_prop": True,  # source uses it (from Context/useState)
        }]

        current_file = source["file"]
        visited: set[str] = {current_file}
        depth = 0

        # Find all passes of this prop from the current file
        queue: list[tuple[str, int]] = [(current_file, 0)]
        chains_found: list[list[dict]] = []

        def trace_chain(start_file: str, prop: str, visited_set: set[str]) -> list[dict]:
            """Recursively trace prop passing from a file."""
            result = []
            for p in passes_by_prop.get(prop, []):
                if p["from_file"] == start_file and p["from_file"] not in visited_set:
                    to_comp = p["to_component"]
                    # Find the file of the child component
                    to_file = next((c.file for c in components if c.name == to_comp), "")
                    if to_file and to_file not in visited_set:
                        # Check if this component uses the prop (not just passes it)
                        try:
                            child_content = (repo / to_file).read_text(encoding="utf-8", errors="ignore")
                            uses_prop = bool(re.search(rf'\b{re.escape(prop)}\b', child_content))
                        except Exception:
                            uses_prop = False

                        result.append({
                            "component": to_comp,
                            "file": to_file,
                            "uses_prop": uses_prop,
                        })
                        # Recurse
                        new_visited = visited_set | {to_file}
                        result.extend(trace_chain(to_file, prop, new_visited))
            return result

        chain_extension = trace_chain(current_file, prop_name, visited)
        if chain_extension:
            full_chain = chain + chain_extension
            depth = len(full_chain)
            if depth >= min_depth:
                drilling.append(PropFlow(
                    prop_name=prop_name,
                    source_file=source["file"],
                    source_component=source_component,
                    chain=full_chain,
                    depth=depth,
                ))

    # Deduplicate by prop_name + source_component (keep longest chain)
    seen: dict[str, PropFlow] = {}
    for pf in drilling:
        key = f"{pf.prop_name}@{pf.source_component}"
        if key not in seen or pf.depth > seen[key].depth:
            seen[key] = pf

    return sorted(seen.values(), key=lambda x: -x.depth)


def emit_prop_drilling_report(drilling: list[PropFlow], repo: Path) -> str:
    """Emit markdown report for prop drilling."""
    lines = [
        f"# 🔗 Prop Drilling Report — {repo.name}",
        "",
        f"**Found {len(drilling)} prop(s) drilled through 3+ layers.**",
        "",
        "Props that are passed through multiple components without being used by intermediates",
        "are candidates for Context or a state management solution.",
        "",
    ]

    if not drilling:
        lines.append("✅ No significant prop drilling detected (depth ≥ 3).")
        return "\n".join(lines)

    lines.append("| Prop | Source | Depth | Chain | Pass-through (unused by) |")
    lines.append("|------|--------|-------|-------|-------------------------|")

    for pf in drilling:
        chain_str = " → ".join(f"`{c['component']}`" for c in pf.chain)
        # Find intermediate components that don't use the prop
        pass_through = [c["component"] for c in pf.chain if not c["uses_prop"]]
        pt_str = ", ".join(f"`{c}`" for c in pass_through) if pass_through else "—"
        lines.append(f"| `{pf.prop_name}` | `{pf.source_component}` | {pf.depth} | {chain_str} | {pt_str} |")

    lines.append("")

    # Detailed chains
    lines.append("## Detailed Chains")
    lines.append("")

    for pf in drilling[:10]:  # top 10
        lines.append(f"### `{pf.prop_name}` (depth {pf.depth})")
        lines.append("")
        lines.append(f"**Source:** `{pf.source_component}` in `{pf.source_file}`")
        lines.append("")
        lines.append("```")
        for i, c in enumerate(pf.chain):
            indent = "  " * i
            icon = "✅" if c["uses_prop"] else "➡️"
            lines.append(f"{indent}{icon} {c['component']} [{c['file']}]")
        lines.append("```")
        lines.append("")

        # Recommendation
        pass_through_count = sum(1 for c in pf.chain if not c["uses_prop"])
        if pass_through_count >= 2:
            lines.append(f"⚠️ **{pass_through_count} intermediate components** receive this prop but don't use it — consider Context.")
        lines.append("")

    lines.append("## Recommendations")
    lines.append("")
    lines.append("- **Props with depth ≥ 4:** Strong candidates for Context API or a state manager (Zustand, Jotai)")
    lines.append("- **Props with depth 3:** Consider Context if the prop is used by leaf components only")
    lines.append("- **Pass-through components:** Components that receive a prop but don't use it are coupling smells")
    lines.append("")

    return "\n".join(lines)


# ============================================================
# Feature 5: Hook Dependency Analyzer
# ============================================================

@dataclass
class HookIssue:
    file: str
    component: str
    hook_type: str       # useEffect, useMemo, useCallback
    line: int
    issue_type: str      # missing_dep, unnecessary_dep, empty_deps, no_deps_array
    description: str
    missing_vars: list[str] = field(default_factory=list)
    unnecessary_vars: list[str] = field(default_factory=list)


def analyze_hook_dependencies(repo: Path) -> list[HookIssue]:
    """Analyze React hook dependency arrays for common bugs.

    Checks:
    1. Missing dependencies — variables used in the hook body but not in the dep array
    2. Unnecessary dependencies — variables in the dep array but not used in the body
    3. Empty dep array — hook runs once, but uses variables that may change
    4. No dep array — hook runs on every render (usually a bug)
    """
    src_dirs = detect_src_dirs(repo)
    issues: list[HookIssue] = []

    # Regex to find hooks: useEffect(() => { ... }, [deps]) or useEffect(callback, [deps])
    # We need to match the hook call, the body, and the dependency array
    hook_pattern = re.compile(
        r'(use(Effect|Memo|Callback|LayoutEffect))\s*\(\s*'  # hook name
        r'(?:'                                                    # callback can be:
        r'\(\s*\)\s*=>\s*\{'                                      #   () => {
        r'|'                                                      # or
        r'\([^)]*\)\s*=>\s*\{'                                    #   (args) => {
        r'|'                                                      # or
        r'(?:async\s+)?\([^)]*\)\s*=>\s*\{'                       #   async (args) => {
        r')',
        re.DOTALL,
    )

    for src_dir in src_dirs:
        full_src = repo / src_dir
        if not full_src.exists():
            continue

        for ext in ["*.tsx", "*.jsx"]:
            for f in full_src.rglob(ext):
                if "node_modules" in str(f):
                    continue
                try:
                    content = f.read_text(encoding="utf-8", errors="ignore")
                except Exception:
                    continue

                rel = str(f.relative_to(repo))
                lines = content.split("\n")

                # Find component name (for reporting)
                comp_name = ""
                for line in lines:
                    m = re.match(r'(?:export\s+)?(?:default\s+)?function\s+(\w+)', line)
                    if m:
                        comp_name = m.group(1)
                        break

                # Find each hook call
                for m in hook_pattern.finditer(content):
                    hook_name = m.group(1)
                    hook_type = m.group(2)  # Effect, Memo, Callback, LayoutEffect

                    # Get line number
                    line_num = content[:m.start()].count("\n") + 1

                    # Find the hook body (from the { after the arrow to the matching })
                    body_start = m.end() - 1  # position of {
                    depth = 0
                    body_end = body_start
                    for i in range(body_start, len(content)):
                        if content[i] == '{':
                            depth += 1
                        elif content[i] == '}':
                            depth -= 1
                            if depth == 0:
                                body_end = i
                                break
                    body = content[body_start:body_end+1]

                    # Find the dependency array after the body
                    after_body = content[body_end+1:]
                    # Skip whitespace, then look for , [deps]
                    deps_match = re.match(r'\s*,\s*\[([^\]]*)\]', after_body)
                    deps_str = ""
                    if deps_match:
                        deps_str = deps_match.group(1)
                        deps = [d.strip() for d in deps_str.split(",") if d.strip()]
                    else:
                        # Check if there's no deps array at all
                        # (just a closing paren after the body)
                        deps = None  # no dependency array

                    # Extract variables referenced in the hook body
                    # Look for identifiers that are likely variables (not keywords, not strings)
                    body_vars: set[str] = set()
                    # Match identifiers that aren't in strings or comments
                    # Simple heuristic: find all word-boundary identifiers
                    for var_match in re.finditer(r'\b([a-zA-Z_$][a-zA-Z0-9_$]*)\b', body):
                        var = var_match.group(1)
                        # Skip JavaScript/React keywords and built-ins
                        if var in ("if", "else", "return", "const", "let", "var", "function",
                                   "true", "false", "null", "undefined", "new", "typeof",
                                   "await", "async", "try", "catch", "finally", "throw",
                                   "for", "while", "do", "switch", "case", "break", "continue",
                                   "this", "class", "extends", "import", "export", "default",
                                   "from", "as", "in", "of", "instanceof", "void", "delete",
                                   "yield", "debugger", "with", "implements", "interface",
                                   "package", "private", "protected", "public", "static",
                                   "console", "window", "document", "Math", "JSON", "Object",
                                   "Array", "String", "Number", "Boolean", "Date", "Promise",
                                   "Set", "Map", "Symbol", "Error", "RegExp", "Number",
                                   "parseInt", "parseFloat", "isNaN", "isFinite",
                                   "setTimeout", "setInterval", "clearTimeout", "clearInterval",
                                   "fetch", "alert", "confirm", "prompt",
                                   # DOM globals that aren't variables
                                   "scrollTo", "scrollIntoView", "querySelector", "querySelectorAll",
                                   "getElementById", "getElementsByClassName", "getElementsByTagName",
                                   "createElement", "createTextNode", "appendChild", "removeChild",
                                   "addEventListener", "removeEventListener", "dispatchEvent",
                                   "requestAnimationFrame", "cancelAnimationFrame",
                                   "localStorage", "sessionStorage", "indexedDB",
                                   "history", "location", "navigator", "screen",
                                   "innerWidth", "innerHeight", "outerWidth", "outerHeight",
                                   "HTMLLinkElement", "HTMLElement", "HTMLInputElement",
                                   "HTMLButtonElement", "HTMLFormElement", "HTMLSelectElement",
                                   "HTMLTextAreaElement", "HTMLAnchorElement", "HTMLImageElement",
                                   "Node", "Element", "Event", "MouseEvent", "KeyboardEvent",
                                   "TouchEvent", "WheelEvent", "CustomEvent",
                                   "Headers", "Request", "Response", "FormData", "Blob", "File",
                                   "FileReader", "URL", "URLSearchParams",
                                   "WebSocket", "EventSource", "AbortController",
                                   "crypto", "performance", "IntersectionObserver",
                                   "MutationObserver", "ResizeObserver",
                                   "Promise", "Proxy", "Reflect",
                                   "allSettled", "resolve", "reject", "all", "race",
                                   "then", "catch", "finally",
                                   ):
                            continue
                        # Skip function parameter names (common patterns)
                        if var.startswith("set"):  # setState functions
                            body_vars.add(var)
                        elif var[0].isupper():  # component names
                            body_vars.add(var)
                        elif var[0].islower():
                            body_vars.add(var)

                    # Determine issues
                    if deps is None:
                        # No dependency array
                        issues.append(HookIssue(
                            file=rel,
                            component=comp_name,
                            hook_type=hook_name,
                            line=line_num,
                            issue_type="no_deps_array",
                            description=f"{hook_name} has no dependency array — runs on every render",
                        ))
                    elif len(deps) == 0:
                        # Empty dependency array
                        # Check if the body uses external variables
                        external_vars = {v for v in body_vars if not v.startswith("set")}
                        if external_vars:
                            issues.append(HookIssue(
                                file=rel,
                                component=comp_name,
                                hook_type=hook_name,
                                line=line_num,
                                issue_type="empty_deps",
                                description=f"{hook_name} has empty deps [] but uses external variables: {', '.join(sorted(external_vars)[:5])}",
                                missing_vars=sorted(external_vars)[:5],
                            ))
                    else:
                        # Check for missing deps
                        dep_set = set(deps)
                        missing = body_vars - dep_set
                        # Filter out likely-false-positives: setState functions are usually safe to omit
                        missing = {v for v in missing if not v.startswith("set")}
                        # Filter out variables that are likely defined inside the hook body
                        # (we'd need proper scope analysis for this, but as a heuristic,
                        # skip single-letter vars and common loop variables)
                        missing = {v for v in missing if len(v) > 1}

                        if missing:
                            issues.append(HookIssue(
                                file=rel,
                                component=comp_name,
                                hook_type=hook_name,
                                line=line_num,
                                issue_type="missing_dep",
                                description=f"{hook_name} uses variables not in dependency array: {', '.join(sorted(missing)[:5])}",
                                missing_vars=sorted(missing)[:5],
                            ))

                        # Check for unnecessary deps
                        # NOTE: This check is disabled because dependency arrays control
                        # WHEN the effect runs, not just what variables the body uses.
                        # A dep like [pathname] in useEffect(() => { window.scrollTo(0,0) }, [pathname])
                        # is CORRECT — it makes the effect run on route change, even though
                        # pathname isn't referenced in the body. This is a common, valid pattern.
                        # Reporting these as "unnecessary" produces 100% false positives.
                        unnecessary: set[str] = set()  # always empty — check disabled
                        if unnecessary:
                            issues.append(HookIssue(
                                file=rel,
                                component=comp_name,
                                hook_type=hook_name,
                                line=line_num,
                                issue_type="unnecessary_dep",
                                description=f"{hook_name} has dependencies not used in the body: {', '.join(sorted(unnecessary)[:5])}",
                                unnecessary_vars=sorted(unnecessary)[:5],
                            ))

    return issues


def emit_hook_report(issues: list[HookIssue], repo: Path) -> str:
    """Emit markdown report for hook dependency issues."""
    lines = [
        f"# 🪝 Hook Dependency Report — {repo.name}",
        "",
        f"**Found {len(issues)} potential hook dependency issue(s).**",
        "",
    ]

    if not issues:
        lines.append("✅ No hook dependency issues found. All hooks have correct dependency arrays.")
        return "\n".join(lines)

    # Summary by issue type
    by_type: dict[str, int] = defaultdict(int)
    for issue in issues:
        by_type[issue.issue_type] += 1

    lines.append("## Summary")
    lines.append("")
    lines.append("| Issue Type | Count | Severity |")
    lines.append("|-----------|-------|----------|")
    severity = {
        "missing_dep": "🔴 High — can cause stale closures and bugs",
        "no_deps_array": "🟡 Medium — hook runs on every render (performance)",
        "empty_deps": "🟡 Medium — may miss needed re-runs",
        "unnecessary_dep": "🟢 Low — unnecessary re-runs (minor perf)",
    }
    for itype, count in sorted(by_type.items(), key=lambda x: -x[1]):
        lines.append(f"| {itype} | {count} | {severity.get(itype, '?')} |")
    lines.append("")

    # Detailed issues
    lines.append("## Issues")
    lines.append("")

    # Sort by severity (missing_dep first)
    severity_order = {"missing_dep": 0, "no_deps_array": 1, "empty_deps": 2, "unnecessary_dep": 3}
    issues_sorted = sorted(issues, key=lambda x: severity_order.get(x.issue_type, 99))

    for issue in issues_sorted[:30]:  # cap at 30
        icon = {"missing_dep": "🔴", "no_deps_array": "🟡", "empty_deps": "🟡", "unnecessary_dep": "🟢"}[issue.issue_type]
        lines.append(f"### {icon} {issue.hook_type} — {issue.issue_type}")
        lines.append("")
        lines.append(f"- **File:** `{issue.file}:{issue.line}`")
        lines.append(f"- **Component:** `{issue.component}`")
        lines.append(f"- **Issue:** {issue.description}")
        if issue.missing_vars:
            lines.append(f"- **Missing:** `{', '.join(issue.missing_vars)}`")
        if issue.unnecessary_vars:
            lines.append(f"- **Unnecessary:** `{', '.join(issue.unnecessary_vars)}`")
        lines.append("")

    if len(issues_sorted) > 30:
        lines.append(f"_... and {len(issues_sorted) - 30} more issues_")
        lines.append("")

    lines.append("## How to Fix")
    lines.append("")
    lines.append("- **Missing deps:** Add the variable to the dependency array, or wrap it in a `useRef` if it shouldn't trigger re-runs")
    lines.append("- **No deps array:** Add `[]` for run-once, or `[dep1, dep2]` for specific triggers")
    lines.append("- **Empty deps:** If the hook uses external variables, add them to the array")
    lines.append("- **Unnecessary deps:** Remove unused entries from the dependency array")
    lines.append("")
    lines.append("> ⚠️ These are heuristic checks. Some missing deps are intentional (e.g., `eslint-disable` comments). Always review context.")

    return "\n".join(lines)


# ============================================================
# Feature 6: Context Usage Map
# ============================================================

@dataclass
class ContextInfo:
    name: str              # e.g., "AuthContext"
    file: str              # where the Context is defined
    provider_component: str  # component that wraps children in <Provider>
    consumers: list[dict]  # [{component, file, hook: useAuth}]
    consumer_count: int
    risk_level: str        # LOW, MEDIUM, HIGH


def find_contexts(repo: Path) -> list[ContextInfo]:
    """Find all React Context definitions and their consumers.

    Looks for:
    1. Context creation: const XContext = createContext(...)
    2. Provider usage: <XContext.Provider> or <Provider>
    3. Consumer hooks: const { ... } = useContext(XContext) or custom hooks like useAuth()
    """
    src_dirs = detect_src_dirs(repo)
    contexts: list[ContextInfo] = []

    # Map: context_name → {file, provider_component}
    context_defs: dict[str, dict] = {}
    # Map: hook_name → context_name (e.g., useAuth → AuthContext)
    hook_to_context: dict[str, str] = {}

    for src_dir in src_dirs:
        full_src = repo / src_dir
        if not full_src.exists():
            continue

        for ext in ["*.tsx", "*.ts", "*.jsx", "*.js"]:
            for f in full_src.rglob(ext):
                if "node_modules" in str(f):
                    continue
                try:
                    content = f.read_text(encoding="utf-8", errors="ignore")
                except Exception:
                    continue

                rel = str(f.relative_to(repo))

                # Find Context creation: const XContext = createContext(...)
                for m in re.finditer(r'(?:const|let)\s+(\w+Context)\s*=\s*createContext', content):
                    ctx_name = m.group(1)
                    context_defs[ctx_name] = {"file": rel, "provider_component": ""}

                # Find custom hooks that wrap useContext: const useX = () => useContext(XContext)
                # or: export function useX() { return useContext(XContext) }
                for m in re.finditer(r'(?:const|let)\s+(use\w+)\s*=\s*\(\s*\)\s*=>\s*useContext\s*\(\s*(\w+Context)\s*\)', content):
                    hook_name = m.group(1)
                    ctx_name = m.group(2)
                    hook_to_context[hook_name] = ctx_name

                for m in re.finditer(r'(?:export\s+)?function\s+(use\w+)\s*\(\s*\)\s*\{[^}]*useContext\s*\(\s*(\w+Context)\s*\)', content, re.DOTALL):
                    hook_name = m.group(1)
                    ctx_name = m.group(2)
                    hook_to_context[hook_name] = ctx_name

    # Now find consumers of each context
    for ctx_name, info in context_defs.items():
        consumers: list[dict] = []

        # Find direct useContext calls
        for src_dir in src_dirs:
            full_src = repo / src_dir
            if not full_src.exists():
                continue

            for ext in ["*.tsx", "*.ts", "*.jsx"]:
                for f in full_src.rglob(ext):
                    if "node_modules" in str(f) or str(f) == info["file"]:
                        continue
                    try:
                        content = f.read_text(encoding="utf-8", errors="ignore")
                    except Exception:
                        continue

                    rel = str(f.relative_to(repo))

                    # Check for useContext(XContext)
                    if re.search(rf'useContext\s*\(\s*{re.escape(ctx_name)}\s*\)', content):
                        # Find component name
                        comp_name = ""
                        for line in content.split("\n"):
                            m2 = re.match(r'(?:export\s+)?(?:default\s+)?function\s+(\w+)', line)
                            if m2:
                                comp_name = m2.group(1)
                                break
                        consumers.append({
                            "component": comp_name or f.stem,
                            "file": rel,
                            "hook": "useContext",
                        })

                    # Check for custom hook usage (useAuth, useTenant, etc.)
                    for hook_name, ctx in hook_to_context.items():
                        if ctx == ctx_name and re.search(rf'\b{re.escape(hook_name)}\s*\(', content):
                            comp_name = ""
                            for line in content.split("\n"):
                                m2 = re.match(r'(?:export\s+)?(?:default\s+)?function\s+(\w+)', line)
                                if m2:
                                    comp_name = m2.group(1)
                                    break
                            # Avoid duplicate entries
                            if not any(c["file"] == rel for c in consumers):
                                consumers.append({
                                    "component": comp_name or f.stem,
                                    "file": rel,
                                    "hook": hook_name,
                                })

        # Risk assessment
        count = len(consumers)
        if count >= 30:
            risk = "HIGH"
        elif count >= 10:
            risk = "MEDIUM"
        else:
            risk = "LOW"

        contexts.append(ContextInfo(
            name=ctx_name,
            file=info["file"],
            provider_component=info["provider_component"],
            consumers=consumers,
            consumer_count=count,
            risk_level=risk,
        ))

    return contexts


def emit_context_report(contexts: list[ContextInfo], repo: Path) -> str:
    """Emit markdown report for Context usage."""
    lines = [
        f"# 🌐 Context Usage Map — {repo.name}",
        "",
        f"**Found {len(contexts)} Context(s).**",
        "",
    ]

    if not contexts:
        lines.append("No React Contexts found. The app may be using prop drilling instead.")
        return "\n".join(lines)

    # Summary
    lines.append("## Summary")
    lines.append("")
    lines.append("| Context | Consumers | Risk | File |")
    lines.append("|---------|-----------|------|------|")
    for ctx in sorted(contexts, key=lambda x: -x.consumer_count):
        risk_icon = {"LOW": "🟢", "MEDIUM": "🟡", "HIGH": "🟠"}[ctx.risk_level]
        lines.append(f"| `{ctx.name}` | {ctx.consumer_count} | {risk_icon} {ctx.risk_level} | `{ctx.file}` |")
    lines.append("")

    # Detailed consumers
    lines.append("## Consumer Details")
    lines.append("")

    for ctx in sorted(contexts, key=lambda x: -x.consumer_count):
        risk_icon = {"LOW": "🟢", "MEDIUM": "🟡", "HIGH": "🟠"}[ctx.risk_level]
        lines.append(f"### {risk_icon} `{ctx.name}` — {ctx.consumer_count} consumer(s)")
        lines.append("")
        lines.append(f"**Defined in:** `{ctx.file}`")
        lines.append("")

        if ctx.consumers:
            lines.append("| Component | File | Hook |")
            lines.append("|-----------|------|------|")
            for c in ctx.consumers[:20]:
                lines.append(f"| `{c['component']}` | `{c['file']}` | `{c['hook']}` |")
            if len(ctx.consumers) > 20:
                lines.append(f"| _... and {len(ctx.consumers) - 20} more_ | | |")
            lines.append("")

        if ctx.risk_level == "HIGH":
            lines.append(f"⚠️ **HIGH risk:** {ctx.consumer_count} components consume this Context. ")
            lines.append(f"Any state change causes ALL of them to re-render. Consider splitting into smaller Contexts.")
            lines.append("")
        elif ctx.risk_level == "MEDIUM":
            lines.append(f"💡 **MEDIUM:** {ctx.consumer_count} consumers — monitor for performance if state changes frequently.")
            lines.append("")

    # Insights
    lines.append("## Insights")
    lines.append("")
    total_consumers = sum(c.consumer_count for c in contexts)
    if contexts:
        avg = total_consumers / len(contexts)
        lines.append(f"- **Average consumers per Context:** {avg:.0f}")
    high_risk = [c for c in contexts if c.risk_level == "HIGH"]
    if high_risk:
        lines.append(f"- 🔴 **{len(high_risk)} HIGH-risk Context(s)** — consider splitting:")
        for c in high_risk:
            lines.append(f"  - `{c.name}` ({c.consumer_count} consumers)")
    low_consumers = [c for c in contexts if c.consumer_count <= 1]
    if low_consumers:
        lines.append(f"- 🟢 **{len(low_consumers)} Context(s) with ≤1 consumer** — may be over-engineered:")
        for c in low_consumers:
            lines.append(f"  - `{c.name}` ({c.consumer_count} consumer)")
    lines.append("")

    return "\n".join(lines)


# ============================================================
# Feature 7: Component Complexity Report
# ============================================================

@dataclass
class ComponentComplexity:
    name: str
    file: str
    lines: int
    prop_count: int
    hook_count: int
    nesting_depth: int
    complexity_score: int
    flags: list[str] = field(default_factory=list)


def analyze_complexity(repo: Path) -> list[ComponentComplexity]:
    """Analyze component complexity metrics.

    Metrics per component:
    - Lines of code
    - Number of props (from function signature destructuring)
    - Number of hooks (useState, useEffect, useMemo, useCallback, useRef, useContext)
    - Nesting depth (max depth of JSX elements)
    - Complexity score (weighted combination)
    """
    src_dirs = detect_src_dirs(repo)
    results: list[ComponentComplexity] = []

    for src_dir in src_dirs:
        full_src = repo / src_dir
        if not full_src.exists():
            continue

        for ext in ["*.tsx", "*.jsx"]:
            for f in full_src.rglob(ext):
                if "node_modules" in str(f):
                    continue
                try:
                    content = f.read_text(encoding="utf-8", errors="ignore")
                except Exception:
                    continue

                rel = str(f.relative_to(repo))

                # Find component definitions
                for m in re.finditer(r'(?:export\s+)?(?:default\s+)?function\s+(\w+)\s*(\([^)]*\))?\s*(?:<[^>]*>)?\s*\{', content):
                    name = m.group(1)
                    params = m.group(2) or "()"

                    # Count props (from destructured params: { prop1, prop2, ... })
                    prop_count = 0
                    prop_match = re.search(r'\{\s*([^}]+)\s*\}', params)
                    if prop_match:
                        prop_count = len([p for p in prop_match.group(1).split(",") if p.strip() and not p.strip().startswith("...")])

                    # Find the component body
                    body_start = m.end() - 1
                    depth = 0
                    body_end = body_start
                    for i in range(body_start, len(content)):
                        if content[i] == '{':
                            depth += 1
                        elif content[i] == '}':
                            depth -= 1
                            if depth == 0:
                                body_end = i
                                break
                    body = content[body_start:body_end+1]
                    body_lines = body.count("\n")

                    # Count hooks
                    hook_count = len(re.findall(r'\buse(State|Effect|Memo|Callback|Ref|Context|Reducer|LayoutEffect)\b', body))

                    # Estimate nesting depth (max depth of JSX elements)
                    max_depth = 0
                    current_depth = 0
                    for char in body:
                        if char == '<' and not body[max(0, body.index(char)-1):body.index(char)].endswith('!'):
                            current_depth += 1
                            max_depth = max(max_depth, current_depth)
                        elif char == '>' and current_depth > 0:
                            # Don't decrement for self-closing tags
                            pass
                    # Simpler approach: count indentation levels in JSX
                    jsx_depth = 0
                    for line in body.split("\n"):
                        stripped = line.lstrip()
                        if stripped.startswith("<") and not stripped.startswith("</"):
                            jsx_depth += 1
                        elif stripped.startswith("</"):
                            jsx_depth = max(0, jsx_depth - 1)
                        max_depth = max(max_depth, jsx_depth)

                    # Complexity score
                    score = body_lines + (prop_count * 3) + (hook_count * 5) + (max_depth * 2)

                    flags = []
                    if body_lines > 300:
                        flags.append("📏 Too long (>300 lines)")
                    if prop_count > 10:
                        flags.append(f"📎 Too many props ({prop_count})")
                    if hook_count > 7:
                        flags.append(f"🪝 Too many hooks ({hook_count})")
                    if max_depth > 8:
                        flags.append(f" nested too deeply ({max_depth} levels)")

                    results.append(ComponentComplexity(
                        name=name,
                        file=rel,
                        lines=body_lines,
                        prop_count=prop_count,
                        hook_count=hook_count,
                        nesting_depth=max_depth,
                        complexity_score=score,
                        flags=flags,
                    ))

    # Sort by complexity score descending
    results.sort(key=lambda x: -x.complexity_score)
    return results


def emit_complexity_report(results: list[ComponentComplexity], repo: Path) -> str:
    lines = [
        f"# 📊 Component Complexity Report — {repo.name}",
        "",
        f"**Analyzed {len(results)} component(s).**",
        "",
    ]

    flagged = [r for r in results if r.flags]
    lines.append(f"**{len(flagged)} component(s) flagged** for high complexity.")
    lines.append("")

    # Top 20 most complex
    lines.append("## Top 20 Most Complex Components")
    lines.append("")
    lines.append("| # | Component | Lines | Props | Hooks | Depth | Score | Flags |")
    lines.append("|---|-----------|-------|-------|-------|-------|-------|-------|")
    for i, r in enumerate(results[:20], 1):
        flags_str = ", ".join(r.flags) if r.flags else "—"
        lines.append(f"| {i} | `{r.name}` | {r.lines} | {r.prop_count} | {r.hook_count} | {r.nesting_depth} | {r.complexity_score} | {flags_str} |")
    lines.append("")

    # Flagged components
    if flagged:
        lines.append("## ⚠️ Flagged Components")
        lines.append("")
        for r in flagged[:15]:
            lines.append(f"### `{r.name}` — score {r.complexity_score}")
            lines.append(f"- **File:** `{r.file}`")
            lines.append(f"- **Lines:** {r.lines} | **Props:** {r.prop_count} | **Hooks:** {r.hook_count} | **Depth:** {r.nesting_depth}")
            if r.flags:
                lines.append(f"- **Flags:** {' '.join(r.flags)}")
            lines.append("")

    lines.append("## Recommendations")
    lines.append("")
    lines.append("- **>300 lines:** Consider splitting into smaller components")
    lines.append("- **>10 props:** Consider using Context or composing smaller components")
    lines.append("- **>7 hooks:** Extract custom hooks to reduce complexity")
    lines.append("- **>8 nesting:** Flatten the JSX structure with intermediate components")

    return "\n".join(lines)


# ============================================================
# Feature 8: i18n Coverage Checker
# ============================================================

def analyze_i18n(repo: Path) -> dict:
    """Check i18n coverage by scanning for hardcoded strings in JSX.

    Looks for:
    - Hardcoded text in JSX: <p>Hello</p> vs <p>{t('hello')}</p>
    - Hardcoded attributes: placeholder="Email" vs placeholder={t('email')}
    - Reports percentage of text that's internationalized
    """
    src_dirs = detect_src_dirs(repo)
    hardcoded: list[dict] = []
    translated: list[dict] = []

    # Check if i18n is used at all
    has_i18n = False

    for src_dir in src_dirs:
        full_src = repo / src_dir
        if not full_src.exists():
            continue

        for ext in ["*.tsx", "*.jsx"]:
            for f in full_src.rglob(ext):
                if "node_modules" in str(f):
                    continue
                try:
                    content = f.read_text(encoding="utf-8", errors="ignore")
                except Exception:
                    continue

                if re.search(r'\b(useTranslation|i18n|t\(|useIntl|formatMessage)\b', content):
                    has_i18n = True

                rel = str(f.relative_to(repo))

                # Find JSX text content: >Some text here<
                for m in re.finditer(r'>([A-Z][a-zA-Z\s]{3,})<', content):
                    text = m.group(1).strip()
                    if text and not text.startswith("{"):
                        hardcoded.append({"file": rel, "text": text, "type": "JSX text"})

                # Find hardcoded placeholder/title/label attributes
                for m in re.finditer(r'(placeholder|title|aria-label|label)\s*=\s*"([^"]{3,})"', content):
                    text = m.group(2)
                    if not text.startswith("{"):
                        hardcoded.append({"file": rel, "text": text, "type": m.group(1) + " attribute"})

                # Find translated text: {t('key')} or {formatMessage(...)}
                for m in re.finditer(r'\{(?:t|translate|intl\.formatMessage)\s*\(\s*[\'"`]([^\'"`]+)[\'"`]', content):
                    translated.append({"file": rel, "key": m.group(1)})

    return {
        "has_i18n": has_i18n,
        "hardcoded_count": len(hardcoded),
        "translated_count": len(translated),
        "coverage_pct": 100 * len(translated) / max(len(translated) + len(hardcoded), 1),
        "hardcoded_samples": hardcoded[:15],
        "translated_samples": translated[:10],
    }


def emit_i18n_report(data: dict, repo: Path) -> str:
    lines = [
        f"# 🌍 i18n Coverage Report — {repo.name}",
        "",
    ]

    if not data["has_i18n"]:
        lines.append("⚠️ **No i18n library detected.** The app uses hardcoded strings throughout.")
        lines.append("")
        lines.append("To add i18n:")
        lines.append("- Install `react-i18next` or `react-intl`")
        lines.append("- Wrap text in `{t('key')}` instead of hardcoded strings")
        lines.append("")
        lines.append(f"**{data['hardcoded_count']} hardcoded strings found.**")
        lines.append("")
        if data["hardcoded_samples"]:
            lines.append("## Sample Hardcoded Strings")
            lines.append("")
            lines.append("| Text | Type | File |")
            lines.append("|------|------|------|")
            for s in data["hardcoded_samples"][:15]:
                lines.append(f"| `{s['text'][:40]}` | {s['type']} | `{s['file']}` |")
        return "\n".join(lines)

    lines.append(f"**i18n library detected.** Coverage: {data['coverage_pct']:.0f}%")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append(f"| Translated strings | {data['translated_count']} |")
    lines.append(f"| Hardcoded strings | {data['hardcoded_count']} |")
    lines.append(f"| Coverage | {data['coverage_pct']:.0f}% |")
    lines.append("")

    if data["hardcoded_samples"]:
        lines.append("## Hardcoded Strings (need translation)")
        lines.append("")
        lines.append("| Text | Type | File |")
        lines.append("|------|------|------|")
        for s in data["hardcoded_samples"][:15]:
            lines.append(f"| `{s['text'][:40]}` | {s['type']} | `{s['file']}` |")
        lines.append("")

    return "\n".join(lines)


# ============================================================
# Feature 9: Accessibility Audit
# ============================================================

def audit_accessibility(repo: Path) -> list[dict]:
    """Static accessibility audit of JSX components.

    Checks for:
    - <img> without alt attribute
    - <button> without text or aria-label
    - <input> without associated <label> or aria-label
    - <a> without text or aria-label
    - <div onClick> without role="button" and tabIndex
    """
    src_dirs = detect_src_dirs(repo)
    issues: list[dict] = []

    for src_dir in src_dirs:
        full_src = repo / src_dir
        if not full_src.exists():
            continue

        for ext in ["*.tsx", "*.jsx"]:
            for f in full_src.rglob(ext):
                if "node_modules" in str(f):
                    continue
                try:
                    content = f.read_text(encoding="utf-8", errors="ignore")
                except Exception:
                    continue

                rel = str(f.relative_to(repo))

                # <img> without alt
                for m in re.finditer(r'<img\s+([^>]*?)/?>', content, re.DOTALL):
                    attrs = m.group(1)
                    if 'alt=' not in attrs:
                        line = content[:m.start()].count("\n") + 1
                        issues.append({
                            "file": rel, "line": line, "severity": "high",
                            "rule": "img-alt",
                            "message": "<img> missing alt attribute",
                        })

                # <button> without text or aria-label
                for m in re.finditer(r'<button\s+([^>]*?)>([^<]*)(?:</button>)?', content, re.DOTALL):
                    attrs = m.group(1)
                    text = m.group(2).strip()
                    if not text and 'aria-label' not in attrs:
                        line = content[:m.start()].count("\n") + 1
                        issues.append({
                            "file": rel, "line": line, "severity": "high",
                            "rule": "button-text",
                            "message": "<button> has no text or aria-label",
                        })

                # <input> without label or aria-label
                for m in re.finditer(r'<input\s+([^>]*?)/?>', content, re.DOTALL):
                    attrs = m.group(1)
                    if 'aria-label' not in attrs and 'id=' not in attrs:
                        line = content[:m.start()].count("\n") + 1
                        issues.append({
                            "file": rel, "line": line, "severity": "medium",
                            "rule": "input-label",
                            "message": "<input> has no aria-label or id for label association",
                        })

                # <div onClick> without role="button"
                for m in re.finditer(r'<div\s+([^>]*?onClick[^>]*?)>', content):
                    attrs = m.group(1)
                    if 'role="button"' not in attrs and 'role={\'button\'}' not in attrs:
                        line = content[:m.start()].count("\n") + 1
                        issues.append({
                            "file": rel, "line": line, "severity": "medium",
                            "rule": "clickable-div-role",
                            "message": "<div onClick> without role='button' — not keyboard accessible",
                        })

    return issues


def emit_a11y_report(issues: list[dict], repo: Path) -> str:
    lines = [
        f"# ♿ Accessibility Audit — {repo.name}",
        "",
        f"**Found {len(issues)} accessibility issue(s).**",
        "",
    ]

    if not issues:
        lines.append("✅ No accessibility issues found.")
        return "\n".join(lines)

    by_rule: dict[str, int] = defaultdict(int)
    by_severity: dict[str, int] = defaultdict(int)
    for i in issues:
        by_rule[i["rule"]] += 1
        by_severity[i["severity"]] += 1

    lines.append("## Summary")
    lines.append("")
    lines.append("| Severity | Count |")
    lines.append("|----------|-------|")
    for sev in ["high", "medium", "low"]:
        if by_severity.get(sev):
            icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}[sev]
            lines.append(f"| {icon} {sev} | {by_severity[sev]} |")
    lines.append("")

    lines.append("| Rule | Count |")
    lines.append("|------|-------|")
    rule_names = {
        "img-alt": "Images without alt text",
        "button-text": "Buttons without text/aria-label",
        "input-label": "Inputs without labels",
        "clickable-div-role": "Clickable divs without role",
    }
    for rule, count in sorted(by_rule.items(), key=lambda x: -x[1]):
        lines.append(f"| {rule_names.get(rule, rule)} | {count} |")
    lines.append("")

    lines.append("## Issues")
    lines.append("")
    for i in issues[:20]:
        icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}[i["severity"]]
        lines.append(f"- {icon} `{i['file']}:{i['line']}` — {i['message']}")
    if len(issues) > 20:
        lines.append(f"- _... and {len(issues) - 20} more_")
    lines.append("")

    lines.append("## How to Fix")
    lines.append("")
    lines.append("- **img-alt:** Add `alt=\"description\"` to all `<img>` tags")
    lines.append("- **button-text:** Add text content or `aria-label` to `<button>` tags")
    lines.append("- **input-label:** Add `aria-label` or an associated `<label htmlFor>`")
    lines.append("- **clickable-div-role:** Use `<button>` instead of `<div onClick>`, or add `role=\"button\" tabIndex={0}`")

    return "\n".join(lines)


# ============================================================
# Feature 10: Test Coverage Mapper
# ============================================================

def map_test_coverage(repo: Path) -> dict:
    """Map which components have co-located test files.

    Checks for:
    - Component.tsx → Component.test.tsx or Component.spec.tsx
    - Component.tsx → __tests__/Component.test.tsx
    - Component.tsx → Component.test.ts
    """
    src_dirs = detect_src_dirs(repo)
    components_with_tests: list[dict] = []
    components_without_tests: list[dict] = []
    total_components = 0

    for src_dir in src_dirs:
        full_src = repo / src_dir
        if not full_src.exists():
            continue

        for ext in ["*.tsx", "*.jsx"]:
            for f in full_src.rglob(ext):
                if "node_modules" in str(f) or ".test." in f.name or ".spec." in f.name:
                    continue
                try:
                    content = f.read_text(encoding="utf-8", errors="ignore")
                except Exception:
                    continue

                # Only count files that export components
                if not re.search(r'export\s+(?:default\s+)?(?:function|const)\s+\w+', content):
                    continue

                total_components += 1
                rel = str(f.relative_to(repo))
                stem = f.stem

                # Check for test files
                test_patterns = [
                    f.parent / f"{stem}.test.tsx",
                    f.parent / f"{stem}.test.ts",
                    f.parent / f"{stem}.spec.tsx",
                    f.parent / f"{stem}.spec.ts",
                    f.parent / "__tests__" / f"{stem}.test.tsx",
                    f.parent / "__tests__" / f"{stem}.test.ts",
                ]

                has_test = any(p.exists() for p in test_patterns)

                if has_test:
                    components_with_tests.append({"file": rel, "name": stem})
                else:
                    components_without_tests.append({"file": rel, "name": stem})

    coverage_pct = 100 * len(components_with_tests) / max(total_components, 1)

    return {
        "total_components": total_components,
        "with_tests": len(components_with_tests),
        "without_tests": len(components_without_tests),
        "coverage_pct": coverage_pct,
        "untested": components_without_tests[:20],
    }


def emit_test_coverage_report(data: dict, repo: Path) -> str:
    lines = [
        f"# 🧪 Test Coverage Map — {repo.name}",
        "",
        f"**Coverage: {data['coverage_pct']:.0f}%** ({data['with_tests']}/{data['total_components']} components tested)",
        "",
    ]

    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append(f"| Total components | {data['total_components']} |")
    lines.append(f"| With tests | {data['with_tests']} |")
    lines.append(f"| Without tests | {data['without_tests']} |")
    lines.append(f"| Coverage | {data['coverage_pct']:.0f}% |")
    lines.append("")

    if data["untested"]:
        lines.append("## Untested Components")
        lines.append("")
        lines.append("Priority: test high-complexity and high-traffic components first.")
        lines.append("")
        lines.append("| Component | File |")
        lines.append("|-----------|------|")
        for c in data["untested"]:
            lines.append(f"| `{c['name']}` | `{c['file']}` |")
        if data["without_tests"] > 20:
            lines.append(f"| _... and {data['without_tests'] - 20} more_ | |")
        lines.append("")

    lines.append("## Recommendations")
    lines.append("")
    if data["coverage_pct"] < 50:
        lines.append("- 🔴 **Low coverage** — prioritize testing core components")
    elif data["coverage_pct"] < 80:
        lines.append("- 🟡 **Moderate coverage** — focus on untested admin/critical-path components")
    else:
        lines.append("- 🟢 **Good coverage** — maintain test discipline for new components")
    lines.append("- Co-locate tests: `Component.tsx` → `Component.test.tsx`")
    lines.append("- Test behavior, not implementation details")

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

    # bundle-impact
    bi = sub.add_parser("bundle-impact", help="Analyze which routes/bundles are affected by changing a component")
    bi.add_argument("path", nargs="?", default=".", help="Path to the repo")
    bi.add_argument("--component", "-c", required=True, help="Component name to analyze")
    bi.add_argument("--format", "-f", choices=["markdown", "json"], default="markdown")
    bi.add_argument("--out", "-o", help="Output file (default: stdout)")

    # prop-drilling
    pd = sub.add_parser("prop-drilling", help="Detect props drilled through 3+ component layers")
    pd.add_argument("path", nargs="?", default=".", help="Path to the repo")
    pd.add_argument("--min-depth", "-d", type=int, default=3, help="Minimum depth to report (default: 3)")
    pd.add_argument("--format", "-f", choices=["markdown", "json"], default="markdown")
    pd.add_argument("--out", "-o", help="Output file (default: stdout)")

    # hook-dependencies
    hd = sub.add_parser("hook-deps", help="Analyze React hook dependency arrays for bugs")
    hd.add_argument("path", nargs="?", default=".", help="Path to the repo")
    hd.add_argument("--format", "-f", choices=["markdown", "json"], default="markdown")
    hd.add_argument("--out", "-o", help="Output file (default: stdout)")

    # context-usage
    cu = sub.add_parser("context-usage", help="Map React Context consumers and flag performance risks")
    cu.add_argument("path", nargs="?", default=".", help="Path to the repo")
    cu.add_argument("--format", "-f", choices=["markdown", "json"], default="markdown")
    cu.add_argument("--out", "-o", help="Output file (default: stdout)")

    # complexity
    cx = sub.add_parser("complexity", help="Component complexity metrics (lines, props, hooks, nesting)")
    cx.add_argument("path", nargs="?", default=".", help="Path to the repo")
    cx.add_argument("--format", "-f", choices=["markdown", "json"], default="markdown")
    cx.add_argument("--out", "-o", help="Output file (default: stdout)")

    # i18n
    i18n = sub.add_parser("i18n", help="Check i18n coverage — find hardcoded strings")
    i18n.add_argument("path", nargs="?", default=".", help="Path to the repo")
    i18n.add_argument("--format", "-f", choices=["markdown", "json"], default="markdown")
    i18n.add_argument("--out", "-o", help="Output file (default: stdout)")

    # a11y
    a11y = sub.add_parser("a11y", help="Accessibility audit — find missing alt, labels, roles")
    a11y.add_argument("path", nargs="?", default=".", help="Path to the repo")
    a11y.add_argument("--format", "-f", choices=["markdown", "json"], default="markdown")
    a11y.add_argument("--out", "-o", help="Output file (default: stdout)")

    # test-coverage
    tc = sub.add_parser("test-coverage", help="Map which components have co-located test files")
    tc.add_argument("path", nargs="?", default=".", help="Path to the repo")
    tc.add_argument("--format", "-f", choices=["markdown", "json"], default="markdown")
    tc.add_argument("--out", "-o", help="Output file (default: stdout)")

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

    elif args.command == "bundle-impact":
        print(f"graphify frontend bundle-impact — analyzing `{args.component}`...", file=sys.stderr)
        result = analyze_bundle_impact(repo, args.component)

        if not result:
            print(f"ERROR: Component '{args.component}' not found.", file=sys.stderr)
            sys.exit(2)

        if args.format == "json":
            output = json.dumps({
                "component": result.component,
                "file": result.file,
                "risk_level": result.risk_level,
                "affected_routes": result.affected_routes,
                "affected_chunks": result.affected_chunks,
                "shared_components": result.shared_components,
            }, indent=2)
        else:
            output = emit_bundle_impact_report(result, repo)

        if args.out:
            Path(args.out).write_text(output, encoding="utf-8")
            print(f"Report written to {args.out}", file=sys.stderr)
        else:
            print(output)

        print(f"\nRisk: {result.risk_level}, {len(result.affected_routes)} route(s) affected.", file=sys.stderr)
        sys.exit(0)

    elif args.command == "prop-drilling":
        print(f"graphify frontend prop-drilling — scanning {repo}...", file=sys.stderr)
        drilling = detect_prop_drilling(repo, min_depth=args.min_depth)

        if args.format == "json":
            output = json.dumps([{
                "prop_name": pf.prop_name,
                "source_component": pf.source_component,
                "source_file": pf.source_file,
                "depth": pf.depth,
                "chain": pf.chain,
            } for pf in drilling], indent=2)
        else:
            output = emit_prop_drilling_report(drilling, repo)

        if args.out:
            Path(args.out).write_text(output, encoding="utf-8")
            print(f"Report written to {args.out}", file=sys.stderr)
        else:
            print(output)

        print(f"\n{len(drilling)} prop(s) drilled through {args.min_depth}+ layers.", file=sys.stderr)
        sys.exit(1 if drilling else 0)

    elif args.command == "hook-deps":
        print(f"graphify frontend hook-deps — scanning {repo}...", file=sys.stderr)
        issues = analyze_hook_dependencies(repo)

        if args.format == "json":
            output = json.dumps([{
                "file": i.file,
                "component": i.component,
                "hook_type": i.hook_type,
                "line": i.line,
                "issue_type": i.issue_type,
                "description": i.description,
                "missing_vars": i.missing_vars,
                "unnecessary_vars": i.unnecessary_vars,
            } for i in issues], indent=2)
        else:
            output = emit_hook_report(issues, repo)

        if args.out:
            Path(args.out).write_text(output, encoding="utf-8")
            print(f"Report written to {args.out}", file=sys.stderr)
        else:
            print(output)

        print(f"\n{len(issues)} hook dependency issue(s) found.", file=sys.stderr)
        sys.exit(1 if issues else 0)

    elif args.command == "context-usage":
        print(f"graphify frontend context-usage — scanning {repo}...", file=sys.stderr)
        contexts = find_contexts(repo)

        if args.format == "json":
            output = json.dumps([{
                "name": c.name,
                "file": c.file,
                "consumer_count": c.consumer_count,
                "risk_level": c.risk_level,
                "consumers": c.consumers[:20],
            } for c in contexts], indent=2)
        else:
            output = emit_context_report(contexts, repo)

        if args.out:
            Path(args.out).write_text(output, encoding="utf-8")
            print(f"Report written to {args.out}", file=sys.stderr)
        else:
            print(output)

        print(f"\n{len(contexts)} Context(s) found.", file=sys.stderr)
        sys.exit(0)

    elif args.command == "complexity":
        print(f"graphify frontend complexity — scanning {repo}...", file=sys.stderr)
        results = analyze_complexity(repo)

        if args.format == "json":
            output = json.dumps([{
                "name": r.name, "file": r.file, "lines": r.lines,
                "prop_count": r.prop_count, "hook_count": r.hook_count,
                "nesting_depth": r.nesting_depth, "complexity_score": r.complexity_score,
                "flags": r.flags,
            } for r in results], indent=2)
        else:
            output = emit_complexity_report(results, repo)

        if args.out:
            Path(args.out).write_text(output, encoding="utf-8")
            print(f"Report written to {args.out}", file=sys.stderr)
        else:
            print(output)

        flagged = sum(1 for r in results if r.flags)
        print(f"\n{len(results)} components analyzed, {flagged} flagged.", file=sys.stderr)
        sys.exit(0)

    elif args.command == "i18n":
        print(f"graphify frontend i18n — scanning {repo}...", file=sys.stderr)
        data = analyze_i18n(repo)

        if args.format == "json":
            output = json.dumps(data, indent=2)
        else:
            output = emit_i18n_report(data, repo)

        if args.out:
            Path(args.out).write_text(output, encoding="utf-8")
            print(f"Report written to {args.out}", file=sys.stderr)
        else:
            print(output)

        print(f"\ni18n: {data['coverage_pct']:.0f}% coverage, {data['hardcoded_count']} hardcoded strings.", file=sys.stderr)
        sys.exit(0)

    elif args.command == "a11y":
        print(f"graphify frontend a11y — scanning {repo}...", file=sys.stderr)
        issues = audit_accessibility(repo)

        if args.format == "json":
            output = json.dumps(issues, indent=2)
        else:
            output = emit_a11y_report(issues, repo)

        if args.out:
            Path(args.out).write_text(output, encoding="utf-8")
            print(f"Report written to {args.out}", file=sys.stderr)
        else:
            print(output)

        print(f"\n{len(issues)} accessibility issue(s) found.", file=sys.stderr)
        sys.exit(1 if issues else 0)

    elif args.command == "test-coverage":
        print(f"graphify frontend test-coverage — scanning {repo}...", file=sys.stderr)
        data = map_test_coverage(repo)

        if args.format == "json":
            output = json.dumps(data, indent=2)
        else:
            output = emit_test_coverage_report(data, repo)

        if args.out:
            Path(args.out).write_text(output, encoding="utf-8")
            print(f"Report written to {args.out}", file=sys.stderr)
        else:
            print(output)

        print(f"\n{data['coverage_pct']:.0f}% coverage ({data['with_tests']}/{data['total_components']}).", file=sys.stderr)
        sys.exit(0)


if __name__ == "__main__":
    main()
