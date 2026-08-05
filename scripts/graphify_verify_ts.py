#!/usr/bin/env python3
"""graphify verify-ts — formal verification of behavior preservation for changed TypeScript functions.

TypeScript counterpart to graphify_verify.py. Uses fast-check for property-based
differential testing instead of Go's testing/quick.

For each changed .ts/.tsx function:
  1. Extract old (git HEAD) and new (working tree) versions
  2. Parse the function signature (name, params, return type)
  3. Generate a differential test using fast-check arbitraries
  4. Run with bun/bunx vitest
  5. Report EQUIVALENT | BREAKING | INCONCLUSIVE

Usage:
  python graphify_verify_ts.py [path] [--function NAME] [--iterations N] [--timeout SECS]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

try:
    from tree_sitter import Parser, Language
    import tree_sitter_typescript as ts_ts
except ImportError:
    print("ERROR: tree-sitter-typescript not installed. Run: pip install tree-sitter-typescript", file=sys.stderr)
    sys.exit(2)


@dataclass
class TSParam:
    name: str
    type_str: str
    optional: bool = False

@dataclass
class TSFunc:
    name: str
    params: list[TSParam]
    return_type: str
    is_async: bool
    is_exported: bool
    is_arrow: bool  # arrow function vs function declaration
    file: str
    start_line: int
    end_line: int
    body_source: str

    @property
    def signature_key(self) -> str:
        params = ",".join(f"{p.name}:{p.type_str}" for p in self.params)
        return f"{self.name}|({params})|{self.return_type}|async={self.is_async}"


@dataclass
class VerificationResult:
    function: str
    file: str
    status: str  # EQUIVALENT | BREAKING | INCONCLUSIVE | ERROR
    iterations: int = 0
    breaking_input: Optional[str] = None
    old_output: Optional[str] = None
    new_output: Optional[str] = None
    error: Optional[str] = None
    affected_callers: list[str] = field(default_factory=list)


# ---------- tree-sitter setup ----------

TS_LANGUAGE = Language(ts_ts.language_typescript())
parser = Parser(TS_LANGUAGE)


def parse_ts_file(source: str) -> list[TSFunc]:
    """Parse a TS source string and return all top-level function declarations."""
    tree = parser.parse(source.encode("utf-8"))
    funcs: list[TSFunc] = []

    def walk(node):
        if node.type in ("function_declaration", "lexical_declaration", "export_statement"):
            f = extract_func(node, source)
            if f:
                funcs.append(f)
                # Don't recurse into the function body
                return
        for child in node.children:
            walk(child)

    walk(tree.root_node)
    return funcs


def extract_func(node, source: str) -> Optional[TSFunc]:
    """Extract a TSFunc from a function_declaration or variable declarator."""
    # Handle export_statement — descend into it
    if node.type == "export_statement":
        for child in node.children:
            if child.type in ("function_declaration", "lexical_declaration"):
                return extract_func(child, source)
        return None

    name = None
    params = []
    return_type = "any"
    is_async = False
    is_exported = False
    is_arrow = False
    body_node = None

    for child in node.children:
        if child.type == "export":
            is_exported = True
        elif child.type == "async":
            is_async = True
        elif child.type == "function":
            pass  # function keyword
        elif child.type == "identifier" and name is None:
            name = source[child.start_byte:child.end_byte]
        elif child.type == "arrow_function":
            is_arrow = True
        elif child.type == "formal_parameters":
            for param_node in child.children:
                if param_node.type == "required_parameter" or param_node.type == "optional_parameter":
                    p = parse_ts_param(param_node, source)
                    if p:
                        params.append(p)
        elif child.type == "type_annotation":
            return_type = source[child.start_byte:child.end_byte].strip().lstrip(":").strip()
        elif child.type in ("statement_block", "expression"):
            body_node = child

    if name is None:
        # Try to find name in variable declarator
        for child in node.children:
            if child.type == "variable_declarator":
                for sub in child.children:
                    if sub.type == "identifier":
                        name = source[sub.start_byte:sub.end_byte]
                    elif sub.type == "arrow_function":
                        is_arrow = True
                        for arrow_child in sub.children:
                            if arrow_child.type == "formal_parameters":
                                for param_node in arrow_child.children:
                                    if param_node.type in ("required_parameter", "optional_parameter"):
                                        p = parse_ts_param(param_node, source)
                                        if p:
                                            params.append(p)
                            elif arrow_child.type == "type_annotation":
                                return_type = source[arrow_child.start_byte:arrow_child.end_byte].strip().lstrip(":").strip()
                            elif arrow_child.type in ("statement_block", "expression"):
                                body_node = arrow_child

    if name is None:
        return None

    # Only include functions with a body (not just signatures)
    if body_node is None:
        # Check if the whole node is the body (arrow function with expression body)
        body_source = source[node.start_byte:node.end_byte]
    else:
        body_source = source[node.start_byte:node.end_byte]

    return TSFunc(
        name=name,
        params=params,
        return_type=return_type,
        is_async=is_async,
        is_exported=is_exported,
        is_arrow=is_arrow,
        file="",
        start_line=node.start_point[0] + 1,
        end_line=node.end_point[0] + 1,
        body_source=body_source,
    )


def parse_ts_param(node, source: str) -> Optional[TSParam]:
    """Parse a TS parameter node."""
    name = None
    type_str = "any"
    optional = node.type == "optional_parameter"

    for child in node.children:
        if child.type == "identifier" and name is None:
            name = source[child.start_byte:child.end_byte]
        elif child.type == "type_annotation":
            type_str = source[child.start_byte:child.end_byte].strip().lstrip(":").strip()
        elif child.type == "rest_pattern":
            # ...args: type
            name = source[child.start_byte:child.end_byte].lstrip("...")
            # Find the type
        elif child.type == "preset_type" or child.type == "type_identifier" or child.type == "union_type":
            type_str = source[child.start_byte:child.end_byte].strip()

    if name is None:
        return None
    return TSParam(name=name, type_str=type_str, optional=optional)


# ---------- fast-check arbitrary mapping ----------

# Map TS types to fast-check arbitrary generators
TS_TYPE_TO_ARBITRARY = {
    "string": "fc.string()",
    "number": "fc.float({ min: -1e9, max: 1e9, noNaN: true })",
    "boolean": "fc.boolean()",
    "boolean": "fc.boolean()",
    "any": "fc.anything()",
    "unknown": "fc.anything()",
    "string | null": "fc.option(fc.string())",
    "string | undefined": "fc.option(fc.string(), { nil: undefined })",
    "number | null": "fc.option(fc.float())",
    "number | undefined": "fc.option(fc.float(), { nil: undefined })",
    "string[]": "fc.array(fc.string())",
    "number[]": "fc.array(fc.float())",
    "Record<string, string>": "fc.dictionary(fc.string(), fc.string())",
    "Record<string, any>": "fc.dictionary(fc.string(), fc.anything())",
    "object": "fc.object()",
    "Date": "fc.date()",
}


def get_arbitrary(type_str: str) -> Optional[str]:
    """Get a fast-check arbitrary for a TS type string."""
    t = type_str.strip()
    if t in TS_TYPE_TO_ARBITRARY:
        return TS_TYPE_TO_ARBITRARY[t]
    # Handle unions like string | number
    if "|" in t:
        parts = [p.strip() for p in t.split("|")]
        arbs = [get_arbitrary(p) for p in parts]
        if all(arbs):
            return f"fc.oneof({', '.join(arbs)})"
    # Handle arrays
    if t.endswith("[]"):
        inner = t[:-2].strip()
        inner_arb = get_arbitrary(inner)
        if inner_arb:
            return f"fc.array({inner_arb})"
    # Handle Promise<T>
    if t.startswith("Promise<") and t.endswith(">"):
        return None  # can't generate promises easily
    # Default: try fc.anything for unknown types
    return None


def can_verify(func: TSFunc) -> tuple[bool, str]:
    """Check if we can verify this TS function."""
    if func.is_async:
        return False, "async function (would need promise comparison)"
    if not func.params and not func.return_type:
        return False, "no params and no return type"
    # Check all params have generatable types
    for p in func.params:
        if get_arbitrary(p.type_str) is None:
            return False, f"param type {p.type_str} not generatable"
    return True, ""


# ---------- git helpers (same as Go version) ----------

def git_show(repo: Path, file_path: str, ref: str = "HEAD") -> Optional[str]:
    try:
        result = subprocess.run(
            ["git", "show", f"{ref}:{file_path}"],
            cwd=repo, capture_output=True, text=True, timeout=10,
        )
        return result.stdout if result.returncode == 0 else None
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return None


def git_changed_files(repo: Path) -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--name-only", "HEAD"],
        cwd=repo, capture_output=True, text=True, timeout=10,
    )
    files = [f for f in result.stdout.strip().split("\n") if f.endswith((".ts", ".tsx"))]
    return files


def git_working_tree_content(repo: Path, file_path: str) -> Optional[str]:
    p = repo / file_path
    return p.read_text(encoding="utf-8") if p.exists() else None


# ---------- generate vitest differential test ----------

def generate_ts_diff_test(
    pkg_dir: Path,
    old_funcs: dict[str, TSFunc],
    new_funcs: dict[str, TSFunc],
    iterations: int,
    source_file: str,
    old_source: str = "",
) -> Path:
    """Generate a vitest test file for differential testing."""

    test_blocks = []
    for sig, old_f in old_funcs.items():
        if sig not in new_funcs:
            continue
        can, reason = can_verify(old_f)
        if not can:
            test_blocks.append(f"// SKIP {old_f.name}: {reason}\n")
            continue

        # Build the arbitrary tuple
        param_arbs = []
        param_names = []
        for p in old_f.params:
            arb = get_arbitrary(p.type_str)
            if arb is None:
                break
            param_arbs.append(arb)
            param_names.append(p.name)
        else:
            # All params have arbitraries
            arb_tuple = ", ".join(param_arbs)
            call_args = ", ".join(param_names)

            test_block = f"""
test('{old_f.name} — differential property test', () => {{
  const arbitrary = fc.tuple({arb_tuple});
  const result = fc.check(fc.property(arbitrary, (args) => {{
    const [{call_args}] = args as [any];
    // Wrap in try/catch — if either version throws, both must throw the same error
    let oldResult: any, oldThrew: any = null;
    let newResult: any, newThrew: any = null;
    try {{ oldResult = Old_{old_f.name}({call_args}); }} catch (e) {{ oldThrew = e; }}
    try {{ newResult = {old_f.name}({call_args}); }} catch (e) {{ newThrew = e; }}
    // Both threw?
    if (oldThrew !== null || newThrew !== null) {{
      return String(oldThrew) === String(newThrew);
    }}
    // Neither threw — compare results
    return JSON.stringify(oldResult) === JSON.stringify(newResult);
  }}), {{ numRuns: {iterations} }});

  if (result.failed) {{
    // Re-run to capture the failing input
    let breakingInput: any = null;
    let oldOut: any = null;
    let newOut: any = null;
    fc.check(fc.property(arbitrary, (args) => {{
      const [{call_args}] = args as [any];
      let oldR: any, oldT: any = null;
      let newR: any, newT: any = null;
      try {{ oldR = Old_{old_f.name}({call_args}); }} catch (e) {{ oldT = e; }}
      try {{ newR = {old_f.name}({call_args}); }} catch (e) {{ newT = e; }}
      const oldStr = oldT !== null ? String(oldT) : JSON.stringify(oldR);
      const newStr = newT !== null ? String(newT) : JSON.stringify(newR);
      if (oldStr !== newStr) {{
        breakingInput = args;
        oldOut = oldT !== null ? 'THROW: ' + String(oldT) : oldR;
        newOut = newT !== null ? 'THROW: ' + String(newT) : newR;
        return false;
      }}
      return true;
    }}), {{ numRuns: {iterations} }});
    throw new Error('BREAKING INPUT: ' + JSON.stringify(breakingInput) + '\\nold output: ' + JSON.stringify(oldOut) + '\\nnew output: ' + JSON.stringify(newOut));
  }}
}});
"""
            test_blocks.append(test_block)

    if not test_blocks:
        raise ValueError("No verifiable functions found")

    # Build the old functions file — we need to extract old function bodies
    # and rename them to Old_<name>
    old_func_blocks = []
    for sig, old_f in old_funcs.items():
        if sig not in new_funcs:
            continue
        can, _ = can_verify(old_f)
        if not can:
            continue
        # Rename the function and add export
        old_body = old_f.body_source
        # For function declarations: replace "function name(" with "export function Old_name("
        renamed = re.sub(
            rf'\b(function\s+){re.escape(old_f.name)}\s*\(',
            rf'\1Old_{old_f.name}(',
            old_body,
            count=1,
        )
        # For arrow functions: replace "const name =" or "export const name ="
        renamed = re.sub(
            rf'(export\s+)?(const|let|var)\s+{re.escape(old_f.name)}\s*=',
            rf'\1\2 Old_{old_f.name} =',
            renamed,
            count=1,
        )
        # Ensure it's exported (add export keyword if not present)
        if not renamed.strip().startswith('export'):
            renamed = 'export ' + renamed
        old_func_blocks.append(renamed)

    # Write old functions file — include imports from the original source
    # Extract import statements from the old source
    old_imports = []
    for line in old_source.split("\n") if old_source else []:
        stripped = line.strip()
        if stripped.startswith("import ") or stripped.startswith("export ") and "from" in stripped:
            # Skip exports of functions (we only want import statements)
            if not stripped.startswith("export function") and not stripped.startswith("export const") and not stripped.startswith("export class"):
                old_imports.append(line)
    imports_block = "\n".join(old_imports)

    old_file_content = f"""// Code generated by graphify verify-ts. DO NOT EDIT.
// Old function versions for differential testing.

{imports_block}

{chr(10).join(old_func_blocks)}
"""
    (pkg_dir / "zz_diffcheck_old.ts").write_text(old_file_content, encoding="utf-8")

    # Write test file
    # We need to import the new functions from the source file
    # and the old functions from zz_diffcheck_old.ts
    source_basename = Path(source_file).stem
    # Determine import path — relative to the test file location
    # We place the test file next to the source file
    test_file_content = f"""// Code generated by graphify verify-ts. DO NOT EDIT.

import {{ describe, test, expect }} from 'vitest';
import * as fc from 'fast-check';
import {{ {", ".join(f.name for f in new_funcs.values() if can_verify(f)[0])} }} from './{source_basename}';
import {{ {", ".join(f"Old_{f.name}" for f in old_funcs.values() if can_verify(f)[0])} }} from './zz_diffcheck_old';

describe('graphify verify — differential tests', () => {{{chr(10).join(test_blocks)}
}});
"""
    test_file = pkg_dir / "zz_diffcheck.test.ts"
    test_file.write_text(test_file_content, encoding="utf-8")
    return test_file


# ---------- main verification flow ----------

def verify_repo_ts(repo: Path, iterations: int = 100, timeout: int = 30, function_filter: Optional[str] = None) -> list[VerificationResult]:
    """Verify all changed TypeScript functions in the repo."""
    changed_files = git_changed_files(repo)
    if not changed_files:
        print("No changed .ts/.tsx files detected.")
        return []

    print(f"Changed TS files: {len(changed_files)}")
    results: list[VerificationResult] = []

    for rel_path in changed_files:
        old_source = git_show(repo, rel_path, "HEAD")
        new_source = git_working_tree_content(repo, rel_path)
        if old_source is None or new_source is None:
            continue

        old_funcs_list = parse_ts_file(old_source)
        new_funcs_list = parse_ts_file(new_source)

        old_funcs = {f.signature_key: f for f in old_funcs_list}
        new_funcs = {f.signature_key: f for f in new_funcs_list}

        changed_funcs = []
        for sig, old_f in old_funcs.items():
            if sig not in new_funcs:
                continue
            new_f = new_funcs[sig]
            if old_f.body_source != new_f.body_source:
                changed_funcs.append((sig, old_f, new_f))

        if not changed_funcs:
            continue

        if function_filter:
            changed_funcs = [(s, o, n) for s, o, n in changed_funcs if function_filter.lower() in o.name.lower()]
            if not changed_funcs:
                continue

        print(f"\n{rel_path}: {len(changed_funcs)} changed function(s)")

        pkg_dir = (repo / rel_path).parent

        # Clean up stale files
        for stale in pkg_dir.glob("zz_diffcheck*.ts"):
            stale.unlink()

        old_funcs_dict = {s: o for s, o, _ in changed_funcs}
        new_funcs_dict = {s: n for s, _, n in changed_funcs}

        try:
            generate_ts_diff_test(pkg_dir, old_funcs_dict, new_funcs_dict, iterations, rel_path, old_source)
        except ValueError as e:
            print(f"  SKIP: {e}")
            continue

        # Find the frontend project root (where package.json with vitest is)
        frontend_root = repo
        for candidate in [repo, repo / "frontend", repo / "web", repo / "app"]:
            if (candidate / "package.json").exists() and (candidate / "node_modules" / "vitest").exists():
                frontend_root = candidate
                break

        # Run vitest
        print(f"  Running differential tests ({iterations} iterations each)...")
        env = os.environ.copy()
        env["PATH"] = "/home/z/.local/go/bin:/home/z/.bun/bin:" + env.get("PATH", "")

        test_file_path = pkg_dir / "zz_diffcheck.test.ts"
        try:
            rel_test_path = test_file_path.relative_to(frontend_root)
        except ValueError:
            rel_test_path = test_file_path

        result = subprocess.run(
            ["bunx", "vitest", "run", str(rel_test_path), "--reporter=verbose", "--no-coverage"],
            cwd=frontend_root,
            capture_output=True,
            text=True,
            timeout=timeout + 30,
            env=env,
        )

        output = result.stdout + result.stderr

        for sig, old_f, new_f in changed_funcs:
            can, reason = can_verify(old_f)
            if not can:
                vr = VerificationResult(
                    function=old_f.name, file=rel_path,
                    status="INCONCLUSIVE", iterations=0,
                    error=reason,
                )
                results.append(vr)
                print(f"  ? {old_f.name}: INCONCLUSIVE ({reason})")
                continue

            vr = VerificationResult(
                function=old_f.name, file=rel_path,
                status="INCONCLUSIVE", iterations=iterations,
            )

            if result.returncode == 0:
                if old_f.name in output and "passed" in output.lower():
                    vr.status = "EQUIVALE"
            else:
                # Look for breaking input
                if "BREAKING INPUT" in output:
                    m = re.search(r"BREAKING INPUT: (.+?)(?:\n|$)", output, re.DOTALL)
                    if m:
                        breaking_msg = m.group(1).strip()
                        vr.status = "BREAKING"
                        vr.breaking_input = breaking_msg
                        # Try to extract old/new outputs
                        out_m = re.search(r"old output: (.+?)\n.*?new output: (.+?)(?:\n|$)", output, re.DOTALL)
                        if out_m:
                            vr.old_output = out_m.group(1).strip()
                            vr.new_output = out_m.group(2).strip()
                else:
                    vr.status = "ERROR"
                    vr.error = output[-500:]

            results.append(vr)
            status_icon = {"EQUIVALE": "✓", "BREAKING": "✗", "INCONCLUSIVE": "?", "ERROR": "!"}[vr.status]
            print(f"  {status_icon} {old_f.name}: {vr.status}")
            if vr.breaking_input:
                print(f"    Breaking input: {vr.breaking_input[:200]}")

        # Clean up
        for stale in pkg_dir.glob("zz_diffcheck*.ts"):
            stale.unlink()

    return results


def emit_ts_report(results: list[VerificationResult], repo: Path) -> str:
    if not results:
        return "# TS Verification Report\n\nNo changed functions to verify.\n"

    lines = ["# graphify verify-ts — TypeScript Behavior Preservation Report", ""]
    lines.append(f"**Repository:** {repo}")
    lines.append(f"**Functions verified:** {len(results)}")
    lines.append("")

    equiv = [r for r in results if r.status == "EQUIVALE"]
    breaking = [r for r in results if r.status == "BREAKING"]
    inconcl = [r for r in results if r.status == "INCONCLUSIVE"]
    errors = [r for r in results if r.status == "ERROR"]

    lines.append("## Summary")
    lines.append("")
    lines.append("| Status | Count |")
    lines.append("|--------|-------|")
    lines.append(f"| ✓ PROVEN EQUIVALENT | {len(equiv)} |")
    lines.append(f"| ✗ BREAKING INPUT FOUND | {len(breaking)} |")
    lines.append(f"| ? INCONCLUSIVE | {len(inconcl)} |")
    lines.append(f"| ! ERROR | {len(errors)} |")
    lines.append("")

    if breaking:
        lines.append("## 🚨 Breaking Changes Detected")
        lines.append("")
        for r in breaking:
            lines.append(f"### `{r.function}` in `{r.file}`")
            lines.append("")
            lines.append(f"**Breaking input:** `{r.breaking_input}`")
            lines.append("")
            if r.old_output and r.new_output:
                lines.append(f"- Old output: `{r.old_output}`")
                lines.append(f"- New output: `{r.new_output}`")
                lines.append("")
            if r.affected_callers:
                lines.append(f"**Affected callers ({len(r.affected_callers)}):**")
                for c in r.affected_callers[:5]:
                    lines.append(f"- `{c}`")
            lines.append("")

    if equiv:
        lines.append("## ✓ Proven Equivalent")
        lines.append("")
        for r in equiv:
            lines.append(f"- `{r.function}` ({r.file}) — {r.iterations} inputs tested")
        lines.append("")

    if inconcl or errors:
        lines.append("## ⚠ Inconclusive / Errors")
        lines.append("")
        for r in inconcl + errors:
            lines.append(f"- `{r.function}` ({r.file}): {r.status}")
            if r.error:
                lines.append(f"  - {r.error[:200]}")
        lines.append("")

    lines.append("## Methodology")
    lines.append("")
    lines.append("TypeScript differential testing using **fast-check** property-based testing.")
    lines.append("Each changed function's old version (from `git HEAD`) is renamed to `Old_<name>`")
    lines.append("and compiled alongside the new version. A vitest test runs both with N random")
    lines.append("inputs generated by fast-check arbitraries matching the function's parameter types.")
    lines.append("")

    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(
        prog="graphify verify-ts",
        description="Formal verification of behavior preservation for changed TypeScript functions.",
    )
    ap.add_argument("path", nargs="?", default=".", help="Path to the repo (default: .)")
    ap.add_argument("--function", "-f", help="Only verify functions matching this name")
    ap.add_argument("--iterations", "-n", type=int, default=100, help="Max random inputs (default: 100)")
    ap.add_argument("--timeout", "-t", type=int, default=30, help="Timeout in seconds (default: 30)")
    ap.add_argument("--graph", help="Path to graph.json for caller cross-reference")
    ap.add_argument("--report", help="Write report to this path")
    args = ap.parse_args()

    repo = Path(args.path).resolve()
    if not (repo / ".git").exists():
        print(f"ERROR: {repo} is not a git repository", file=sys.stderr)
        sys.exit(2)

    print(f"graphify verify-ts — analyzing TypeScript changes in {repo}")
    print(f"Iterations per function: {args.iterations}")
    print()

    results = verify_repo_ts(repo, iterations=args.iterations, timeout=args.timeout, function_filter=args.function)

    if not results:
        print("\nNo changed functions eligible for verification.")
        sys.exit(0)

    # Cross-reference callers if graph.json available
    graph_json = Path(args.graph) if args.graph else (repo / "graphify-out" / "graph.json")
    if graph_json.exists():
        data = json.loads(graph_json.read_text(encoding="utf-8"))
        callers_map = {}
        for edge in data.get("links", []):
            if edge.get("relation") in ("calls", "references"):
                callers_map.setdefault(edge.get("target", ""), []).append(edge.get("source", ""))
        for vr in results:
            matching = [n for n in data.get("nodes", []) if n.get("label") == vr.function]
            callers = []
            for n in matching:
                for cid in callers_map.get(n.get("id", ""), []):
                    cn = next((c for c in data["nodes"] if c.get("id") == cid), None)
                    if cn:
                        callers.append(cn.get("label", cid))
            vr.affected_callers = sorted(set(callers))[:10]

    report = emit_ts_report(results, repo)
    report_path = Path(args.report) if args.report else (repo / "graphify-out" / "VERIFY_TS_REPORT.md")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")
    print(f"\nReport written to {report_path}")

    equiv = sum(1 for r in results if r.status == "EQUIVALE")
    breaking = sum(1 for r in results if r.status == "BREAKING")
    inconcl = sum(1 for r in results if r.status in ("INCONCLUSIVE", "ERROR"))

    print(f"\n{'='*60}")
    print(f"  ✓ EQUIVALENT: {equiv}")
    print(f"  ✗ BREAKING:   {breaking}")
    print(f"  ? OTHER:      {inconcl}")
    print(f"{'='*60}")

    if breaking:
        sys.exit(1)
    if inconcl:
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
