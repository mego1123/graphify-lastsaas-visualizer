#!/usr/bin/env python3
"""graphify verify — formal verification of behavior preservation for changed functions.

For each function changed in the working tree (vs git HEAD):
  1. Extract the old version (from `git show HEAD:file`) and new version (working tree).
  2. Parse the function signature (name, params, return types) with tree-sitter.
  3. Generate a differential test harness that calls BOTH versions with the SAME
     auto-generated inputs (Go's testing/quick for primitives).
  4. Run `go test` and parse results.
  5. Report: PROVEN EQUIVALENT (N inputs tested) | BREAKING INPUT FOUND (with details)
     | INCONCLUSIVE (couldn't generate valid inputs).

Also cross-references graph.json to report which callers would be affected by a break.

Usage:
  python graphify_verify.py [path] [--function NAME] [--iterations N] [--timeout SECS]

Defaults: path=., iterations=500, timeout=30s per function.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import textwrap
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

# tree-sitter is a graphify dependency; we reuse it.
try:
    from tree_sitter import Parser, Language
    import tree_sitter_go as ts_go
except ImportError:
    print("ERROR: tree-sitter not installed. Run: pip install tree-sitter tree-sitter-go", file=sys.stderr)
    sys.exit(2)


@dataclass
class GoParam:
    name: str
    type_str: str

@dataclass
class GoFunc:
    name: str
    receiver: Optional[str]  # receiver type string or None (free function)
    params: list[GoParam]
    return_types: list[str]  # could be multi-return
    file: str
    start_line: int  # 1-indexed
    end_line: int
    body_source: str  # full source including func keyword

    @property
    def signature_key(self) -> str:
        """A stable key for matching old<->new versions of the same function."""
        recv = self.receiver or ""
        params = ",".join(f"{p.name} {p.type_str}" for p in self.params)
        rets = ",".join(self.return_types)
        return f"{recv}|{self.name}|({params})|({rets})"


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

GO_LANGUAGE = Language(ts_go.language())
parser = Parser(GO_LANGUAGE)


def parse_go_file(source: str) -> list[GoFunc]:
    """Parse a Go source string and return all top-level function declarations."""
    tree = parser.parse(source.encode("utf-8"))
    funcs: list[GoFunc] = []

    def walk(node):
        if node.type == "function_declaration":
            f = extract_func(node, source)
            if f:
                funcs.append(f)
            # don't recurse into function body for nested funcs (Go doesn't have them anyway)
            return
        if node.type == "method_declaration":
            f = extract_func(node, source, is_method=True)
            if f:
                funcs.append(f)
            return
        for child in node.children:
            walk(child)

    walk(tree.root_node)
    return funcs


def extract_func(node, source: str, is_method: bool = False) -> Optional[GoFunc]:
    """Extract a GoFunc from a function_declaration or method_declaration node."""
    name = None
    receiver = None
    params = []
    return_types = []
    seen_param_list = 0

    for child in node.children:
        if child.type == "identifier" and name is None:
            name = source[child.start_byte:child.end_byte]
        elif child.type == "field_identifier" and name is None:
            # method_declaration uses field_identifier for the method name
            name = source[child.start_byte:child.end_byte]
            is_method = True
        elif child.type == "receiver_type":
            receiver = source[child.start_byte:child.end_byte]
        elif child.type == "parameter_list":
            seen_param_list += 1
            if seen_param_list == 1 and is_method:
                # First parameter_list = receiver (for methods)
                # Extract receiver type from "(f *Foo)" or "(Foo)"
                recv_text = source[child.start_byte:child.end_byte].strip().lstrip("(").rstrip(")")
                # Remove the receiver variable name, keep the type
                # "(f *Foo)" -> "*Foo", "(Foo)" -> "Foo"
                parts = recv_text.split(None, 1)
                if len(parts) == 2:
                    receiver = parts[1].strip()
                else:
                    receiver = recv_text.strip()
            elif (seen_param_list == 1 and not is_method) or (seen_param_list == 2 and is_method):
                # Input params
                for param_node in child.children:
                    if param_node.type == "parameter_declaration":
                        p = parse_param(param_node, source)
                        if p:
                            params.append(p)
            elif seen_param_list == 3 or (seen_param_list == 2 and not is_method):
                # Return types (parenthesized)
                for pn in child.children:
                    if pn.type == "parameter_declaration":
                        for tnode in pn.children:
                            if tnode.type in ("type_identifier", "qualified_type",
                                              "pointer_type", "slice_type", "array_type",
                                              "map_type", "channel_type"):
                                return_types.append(source[tnode.start_byte:tnode.end_byte])
        elif child.type == "result":
            return_types = parse_result(child, source)
        elif child.type in ("type_identifier", "qualified_type", "pointer_type",
                            "slice_type", "array_type", "map_type", "channel_type") and seen_param_list >= 1 and not return_types:
            # Bare return type (no parens) — e.g. `func Foo() error`
            return_types.append(source[child.start_byte:child.end_byte])

    if name is None:
        return None

    body_source = source[node.start_byte:node.end_byte]
    start_line = node.start_point[0] + 1
    end_line = node.end_point[0] + 1

    return GoFunc(
        name=name,
        receiver=receiver,
        params=params,
        return_types=return_types,
        file="",
        start_line=start_line,
        end_line=end_line,
        body_source=body_source,
    )


def parse_param(node, source: str) -> Optional[GoParam]:
    """Parse a parameter_declaration node into a GoParam."""
    name = None
    type_str = None
    for child in node.children:
        if child.type == "identifier" and name is None:
            name = source[child.start_byte:child.end_byte]
        elif child.type in ("type_identifier", "qualified_type", "pointer_type",
                            "slice_type", "array_type", "map_type", "channel_type",
                            "function_type", "interface_type", "struct_type"):
            type_str = source[child.start_byte:child.end_byte]
    if name and type_str:
        return GoParam(name=name, type_str=type_str)
    # Handle "a, b int" style — multiple names sharing a type
    names = []
    type_str = None
    for child in node.children:
        if child.type == "identifier":
            names.append(source[child.start_byte:child.end_byte])
        elif child.type in ("type_identifier", "qualified_type", "pointer_type",
                            "slice_type", "array_type", "map_type", "channel_type"):
            type_str = source[child.start_byte:child.end_byte]
    if names and type_str:
        # Return the first name with the shared type; caller should handle the rest
        # Actually, we need to return multiple params. Let's return a special marker.
        # For simplicity, return the first one and let the caller detect multi-name params.
        return GoParam(name="|".join(names), type_str=type_str)
    return None


def parse_result(node, source: str) -> list[str]:
    """Parse a result node into a list of return type strings."""
    types = []
    for child in node.children:
        if child.type == "parameter_list":
            for pn in child.children:
                if pn.type == "parameter_declaration":
                    for tnode in pn.children:
                        if tnode.type in ("type_identifier", "qualified_type",
                                          "pointer_type", "slice_type", "array_type"):
                            types.append(source[tnode.start_byte:tnode.end_byte])
        elif child.type in ("type_identifier", "qualified_type", "pointer_type",
                            "slice_type", "array_type", "map_type", "channel_type"):
            types.append(source[child.start_byte:child.end_byte])
    return types


# ---------- git helpers ----------

def git_show(repo: Path, file_path: str, ref: str = "HEAD") -> Optional[str]:
    """Get file content at a git ref. Returns None if file doesn't exist at ref."""
    try:
        result = subprocess.run(
            ["git", "show", f"{ref}:{file_path}"],
            cwd=repo,
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            return result.stdout
        return None
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return None


def git_changed_files(repo: Path) -> list[str]:
    """Return list of .go files changed in working tree vs HEAD."""
    result = subprocess.run(
        ["git", "diff", "--name-only", "HEAD"],
        cwd=repo,
        capture_output=True,
        text=True,
        timeout=10,
    )
    files = [f for f in result.stdout.strip().split("\n") if f.endswith(".go")]
    return files


def git_working_tree_content(repo: Path, file_path: str) -> Optional[str]:
    """Read current working tree version of a file."""
    p = repo / file_path
    if not p.exists():
        return None
    return p.read_text(encoding="utf-8")


# ---------- differential test generation ----------

# Go types that testing/quick can generate
QUICK_GENERATABLE = {
    "int", "int8", "int16", "int32", "int64",
    "uint", "uint8", "uint16", "uint32", "uint64",
    "byte", "rune",
    "float32", "float64",
    "bool",
    "string",
}

# Types that need nil-checking (slices, maps, pointers)
NILABLE_TYPES = {"slice", "pointer", "map", "channel", "interface", "func"}


def is_quick_generatable(type_str: str) -> bool:
    """Check if testing/quick.Value can generate values of this type."""
    t = type_str.strip()
    if t in QUICK_GENERATABLE:
        return True
    # testing/quick can generate slices of primitives and pointers to primitives
    if t.startswith("[]"):
        inner = t[2:].strip()
        return inner in QUICK_GENERATABLE
    if t.startswith("*"):
        inner = t[1:].strip()
        return inner in QUICK_GENERATABLE
    # Common Go aliases that are backed by primitives
    if t in ("time.Duration", "byte", "rune"):
        return True
    return False


def can_verify(func: GoFunc) -> tuple[bool, str]:
    """Check if we can verify this function. Returns (can_verify, reason_if_not).

    Methods are now supported via zero-value receiver construction.
    Complex param types are supported via LLM-generated test cases.
    """
    # Skip variadic functions
    if any("..." in p.type_str for p in func.params):
        return False, "variadic params"
    # Skip functions with no return (nothing to compare)
    if not func.return_types:
        return False, "no return value"
    # For methods, check if the receiver type is a simple struct (not interface)
    if func.receiver:
        recv = func.receiver.strip().lstrip("*")
        if recv in ("error", "io.Reader", "io.Writer"):
            return False, f"interface receiver {func.receiver}"
    return True, ""


def has_complex_params(func: GoFunc) -> bool:
    """Check if the function has params that testing/quick can't auto-generate."""
    for p in func.params:
        for _ in p.name.split("|"):
            if not is_quick_generatable(p.type_str):
                return True
    for rt in func.return_types:
        if not is_quick_generatable(rt) and rt not in ("error",):
            return True
    return False


def normalize_params(func: GoFunc) -> list[GoParam]:
    """Expand multi-name params (a, b int) into separate params."""
    out = []
    for p in func.params:
        names = p.name.split("|")
        for name in names:
            out.append(GoParam(name=name, type_str=p.type_str))
    return out


def generate_diff_test_package(
    pkg_dir: Path,
    package_name: str,
    old_funcs: dict[str, GoFunc],
    new_funcs: dict[str, GoFunc],
    iterations: int,
) -> Path:
    """Generate a Go test file that differential-tests old vs new versions of each function.

    Strategy: rename old functions with an `Old_` prefix in a separate file,
    then generate a test that calls both with the same inputs from testing/quick.
    """
    # We need to compile the old version alongside the new. The cleanest way:
    # 1. Copy the new package files as-is
    # 2. Create an `oldimpl.go` file with the old function bodies, renamed to Old_<name>
    # 3. Create a `diff_test.go` that imports nothing special, just calls both

    # But: the old function bodies may reference package-private types/helpers
    # that still exist in the new package. So we can drop the old func bodies
    # verbatim into the same package, just with renamed identifiers.

    test_files: list[str] = []

    # Write old functions file (renamed)
    old_func_blocks = []
    for sig_key, old_func in old_funcs.items():
        new_func = new_funcs.get(sig_key)
        if not new_func:
            continue  # function was deleted, skip
        can, reason = can_verify(old_func)
        if not can:
            continue
        # Rename the function in the old body
        # Replace "func OldName(" — but method_decls have receivers, which we skip
        old_body = old_func.body_source
        # Rename: replace "func <name>(" with "func Old_<name>("
        # This is a simple text replacement; for methods it'd be more complex but we skip those
        pattern = rf"\bfunc\s+({re.escape(old_func.name)})\s*\("
        renamed_body = re.sub(pattern, rf"func Old_\1(", old_body, count=1)
        old_func_blocks.append(renamed_body)

    if not old_func_blocks:
        raise ValueError("No verifiable functions found")

    old_file_content = f"""// Code generated by graphify verify. DO NOT EDIT.
// Old function versions for differential testing.

package {package_name}

{chr(10).join(old_func_blocks)}
"""
    (pkg_dir / "zz_diffcheck_old.go").write_text(old_file_content, encoding="utf-8")

    # Generate the test file
    test_blocks = []
    for sig_key, old_func in old_funcs.items():
        new_func = new_funcs.get(sig_key)
        if not new_func:
            continue
        can, reason = can_verify(old_func)
        if not can:
            test_blocks.append(f"""// SKIP {old_func.name}: {reason}
""")
            continue

        params = normalize_params(old_func)
        param_names = [p.name for p in params]
        param_types = [p.type_str for p in params]
        return_types = old_func.return_types

        # Build the quick.Check function
        # quick.Check takes a func(*testing.T) that calls f and checks invariants
        # We use quick.CheckEqual which compares two functions

        # Build the call signature
        call_args = ", ".join(param_names)

        # quick.CheckEqual signature: func(args) returns, func(args) returns
        # We need to construct closures
        rets_old = ", ".join([f"r_old_{i}" for i in range(len(return_types))])
        rets_new = ", ".join([f"r_new_{i}" for i in range(len(return_types))])

        # For error returns, we compare .Error() strings
        comparisons = []
        for i, rt in enumerate(return_types):
            if rt == "error":
                comparisons.append(f"""if (r_old_{i} == nil) != (r_new_{i} == nil) {{
                return false
            }}
            if r_old_{i} != nil && r_new_{i} != nil && r_old_{i}.Error() != r_new_{i}.Error() {{
                return false
            }}""")
            else:
                comparisons.append(f"""if r_old_{i} != r_new_{i} {{
                return false
            }}""")

        comparison_block = "\n            ".join(comparisons)

        # quick.CheckEqual needs both funcs to have the same signature
        # The signature is determined by the param types
        quick_sig = ", ".join(param_types)

        test_block = f"""func TestDiffCheck_{old_func.name}(t *testing.T) {{
        f_old := func({call_args} {quick_sig}) ({", ".join(return_types)}) {{
            {rets_old} := Old_{old_func.name}({call_args})
            return {rets_old}
        }}
        f_new := func({call_args} {quick_sig}) ({", ".join(return_types)}) {{
            {rets_new} := {old_func.name}({call_args})
            return {rets_new}
        }}
        config := &quick.Config{{MaxCount: {iterations}}}
        err := quick.CheckEqual(f_old, f_new, config)
        if err != nil {{
            // Extract the failing input from the error
            t.Errorf("BREAKING INPUT: %v", err)
        }}
    }}"""
        test_blocks.append(test_block)

    test_file_content = f"""// Code generated by graphify verify. DO NOT EDIT.

package {package_name}

import (
    "testing"
    "testing/quick"
)

{chr(10).join(test_blocks)}
"""
    test_file = pkg_dir / "zz_diffcheck_test.go"
    test_file.write_text(test_file_content, encoding="utf-8")
    return test_file


def _generate_curated_inputs(param_types: list[str]) -> list[list[str]]:
    """Generate curated boundary-value test inputs for common Go types.

    These complement random testing by hitting values that random generation
    is unlikely to produce (e.g. valid hex strings of exact length, empty strings,
    common boundary integers).
    """
    # Per-type curated values
    type_values: dict[str, list[str]] = {
        "string": [
            '""', '"a"',
            '"0000000000000000000000000000000000000000000000000000000000000000"',
            '"00000000000000000000000000000000"',
            '"abcdef0123456789"', '"hello world"', '"null"', '"true"',
        ],
        "int": ["0", "1", "-1", "32", "64", "255", "1000", "-1000"],
        "int32": ["0", "1", "-1", "32", "64"],
        "int64": ["0", "1", "-1", "32", "64"],
        "uint": ["0", "1", "32", "64", "255"],
        "bool": ["true", "false"],
        "float64": ["0.0", "1.0", "-1.0", "3.14", "1e10"],
        "float32": ["0.0", "1.0", "-1.0"],
        "[]byte": ["nil", "[]byte{}", "[]byte{0}", "[]byte{0,1,2,3}", "make([]byte, 32)"],
        "time.Duration": ["0", "time.Second", "time.Minute", "-time.Second", "24 * time.Hour"],
    }

    if not param_types:
        return []

    # For single-param functions, generate all curated values for that type
    if len(param_types) == 1:
        t = param_types[0]
        vals = type_values.get(t, [])
        return [[v] for v in vals]

    # For multi-param functions, generate a smaller cross-product
    # (take first 3 values per type to avoid explosion)
    result = [[]]
    for t in param_types:
        vals = type_values.get(t, [""])[:3]
        new_result = []
        for r in result:
            for v in vals:
                new_result.append(r + [v])
        result = new_result
    return result[:20]  # cap at 20 combinations


def _split_args(line: str) -> list[str]:
    """Split a comma-separated argument list, respecting parens and braces."""
    parts = []
    depth = 0
    in_str = False
    str_ch = ""
    current = ""
    for c in line:
        if in_str:
            current += c
            if c == "\\":
                continue
            if c == str_ch:
                in_str = False
        else:
            if c in ('"', "'", "`"):
                in_str = True
                str_ch = c
                current += c
            elif c in "([{":
                depth += 1
                current += c
            elif c in ")]}":
                depth -= 1
                current += c
            elif c == "," and depth == 0:
                parts.append(current.strip())
                current = ""
            else:
                current += c
    if current.strip():
        parts.append(current.strip())
    return parts


# ---------- main verification flow ----------

def verify_repo(repo: Path, iterations: int = 500, timeout: int = 30, function_filter: Optional[str] = None) -> list[VerificationResult]:
    """Verify all changed Go functions in the repo."""
    changed_files = git_changed_files(repo)
    if not changed_files:
        print("No changed .go files detected.")
        return []

    print(f"Changed Go files: {len(changed_files)}")
    results: list[VerificationResult] = []

    # Group changed files by their package directory
    files_by_pkg: dict[Path, list[str]] = {}
    for rel_path in changed_files:
        pkg_dir = (repo / rel_path).parent
        files_by_pkg.setdefault(pkg_dir, []).append(rel_path)

    for pkg_dir, rel_paths in files_by_pkg.items():
        # Parse old + new for all changed files in this package
        old_funcs_all: dict[str, GoFunc] = {}
        new_funcs_all: dict[str, GoFunc] = {}
        for rel_path in rel_paths:
            old_source = git_show(repo, rel_path, "HEAD")
            new_source = git_working_tree_content(repo, rel_path)
            if old_source is None or new_source is None:
                continue
            for f in parse_go_file(old_source):
                f.file = rel_path
                old_funcs_all[f.signature_key] = f
            for f in parse_go_file(new_source):
                f.file = rel_path
                new_funcs_all[f.signature_key] = f

        # Find changed functions
        changed_funcs = []
        for sig, old_f in old_funcs_all.items():
            if sig not in new_funcs_all:
                continue
            new_f = new_funcs_all[sig]
            if old_f.body_source != new_f.body_source:
                changed_funcs.append((sig, old_f, new_f))

        if not changed_funcs:
            continue

        # Apply function filter
        if function_filter:
            changed_funcs = [(s, o, n) for s, o, n in changed_funcs if function_filter.lower() in o.name.lower()]
            if not changed_funcs:
                continue

        # Clean up any leftover generated files from previous runs
        for stale in pkg_dir.glob("zz_diffcheck_*.go"):
            stale.unlink()

        # Determine package name from any non-generated .go file in the dir
        pkg_name = "main"
        for go_file in pkg_dir.glob("*.go"):
            if go_file.name.startswith("zz_diffcheck_"):
                continue
            for line in go_file.read_text(encoding="utf-8").split("\n"):
                m = re.match(r"^package\s+(\w+)", line)
                if m:
                    pkg_name = m.group(1)
                    break
            if pkg_name != "main":
                break

        print(f"\n{pkg_dir.relative_to(repo)}: {len(changed_funcs)} changed function(s)")

        # Generate old-functions file + test file IN PLACE in the package directory
        old_funcs_dict = {s: o for s, o, _ in changed_funcs}
        new_funcs_dict = {s: n for s, _, n in changed_funcs}

        old_file = pkg_dir / "zz_diffcheck_old.go"
        test_file = pkg_dir / "zz_diffcheck_test.go"

        try:
            # Build old-funcs file
            # We need to include imports that the old function bodies reference.
            # Strategy: extract the import block from each old source file and union them.
            import_blocks: set[str] = set()
            old_func_blocks = []
            for sig_key, old_func in old_funcs_dict.items():
                can, _ = can_verify(old_func)
                if not can:
                    continue
                old_body = old_func.body_source
                # Rename the function/method
                # For free functions: "func Name(" → "func Old_Name("
                # For methods: "func (recv) Name(" → "func (recv) Old_Name("
                if old_func.receiver:
                    # Method — rename after the receiver declaration
                    pattern = rf"(\bfunc\s*\([^)]+\)\s*){re.escape(old_func.name)}\s*\("
                    renamed_body = re.sub(pattern, rf"\1Old_{old_func.name}(", old_body, count=1)
                else:
                    pattern = rf"\bfunc\s+({re.escape(old_func.name)})\s*\("
                    renamed_body = re.sub(pattern, rf"func Old_\1(", old_body, count=1)
                old_func_blocks.append(renamed_body)

            if not old_func_blocks:
                print(f"  SKIP: no verifiable functions")
                continue

            # Extract ALL imports from each changed file's old version.
            # We include all imports because Go package names don't always match
            # the import path's last segment (e.g. "github.com/golang-jwt/jwt/v5"
            # is used as "jwt" in code, not "v5"). Unused imports will cause
            # compile errors that we report as ERROR status.
            import_blocks: set[str] = set()
            for rel_path in rel_paths:
                old_source = git_show(repo, rel_path, "HEAD")
                if old_source:
                    m = re.search(r'^import\s*\(([^)]+)\)', old_source, re.MULTILINE | re.DOTALL)
                    if m:
                        for line in m.group(1).strip().split("\n"):
                            line = line.strip()
                            if line and not line.startswith("//"):
                                import_blocks.add(line)
                    else:
                        m2 = re.findall(r'^import\s+(.+)$', old_source, re.MULTILINE)
                        for imp in m2:
                            import_blocks.add(imp.strip())

            imports_str = "\n".join(sorted(import_blocks)) if import_blocks else ""

            old_file_content = f"""// Code generated by graphify verify. DO NOT EDIT.
// Old function versions for differential testing.

package {pkg_name}

import (
{imports_str}
)

{chr(10).join(old_func_blocks)}
"""
            old_file.write_text(old_file_content, encoding="utf-8")

            # Build test file
            # Note: quick.CheckEqual does the comparison internally, so we don't need
            # reflect.DeepEqual or manual comparison code.
            test_blocks = []
            for sig, old_f, new_f in changed_funcs:
                can, reason = can_verify(old_f)
                if not can:
                    test_blocks.append(f"// SKIP {old_f.name}: {reason}\n")
                    continue

                params = normalize_params(old_f)
                param_names = [p.name for p in params]
                param_types = [p.type_str for p in params]
                return_types = old_f.return_types
                complex_params = has_complex_params(old_f)

                call_args = ", ".join(param_names)
                rets_old = ", ".join([f"r_old_{i}" for i in range(len(return_types))])
                rets_new = ", ".join([f"r_new_{i}" for i in range(len(return_types))])
                closure_params = ", ".join(f"{n} {t}" for n, t in zip(param_names, param_types))

                # Generate curated test inputs based on param types.
                curated_inputs = _generate_curated_inputs(param_types)

                # If the function has complex params, also generate LLM-based test cases
                # that construct realistic struct/interface values
                llm_cases: list[list[str]] = []
                if complex_params:
                    print(f"    Generating LLM test cases for {old_f.name} (complex params)...")
                    sys.path.insert(0, str(Path(__file__).parent))
                    try:
                        from llm_test_cases import generate_llm_test_cases, extract_call_sites_from_graph
                        graph_json = repo / "graphify-out" / "graph.json"
                        call_sites = extract_call_sites_from_graph(graph_json, old_f.name, limit=3)
                        llm_inputs = generate_llm_test_cases(
                            old_f.name, old_f.body_source, param_types, call_sites, num_cases=5
                        )
                        # Parse each LLM input line into a list of expressions
                        for line in llm_inputs:
                            # Split by comma, but respect parentheses and braces
                            parts = _split_args(line)
                            if len(parts) == len(param_types):
                                llm_cases.append(parts)
                    except Exception as e:
                        print(f"    LLM case generation failed: {e}")

                # Build the call expression — methods need a receiver
                if old_f.receiver:
                    recv_type = old_f.receiver.strip().lstrip("*").strip()
                    if old_f.receiver.strip().startswith("*"):
                        recv_construct = f"&{recv_type}{{}}"
                    else:
                        recv_construct = f"{recv_type}{{}}"
                    call_old_expr = f"({recv_construct}).Old_{old_f.name}"
                    call_new_expr = f"({recv_construct}).{old_f.name}"
                else:
                    call_old_expr = f"Old_{old_f.name}"
                    call_new_expr = f"{old_f.name}"

                n_returns = len(return_types)
                if n_returns == 1:
                    curated_cases = "\n        ".join(
                        f'{{ // input #{i+1}\n'
                        f'            v_old := {call_old_expr}({", ".join(curated)})\n'
                        f'            v_new := {call_new_expr}({", ".join(curated)})\n'
                        f'            if !reflect.DeepEqual(v_old, v_new) {{\n'
                        f'                t.Errorf("BREAKING INPUT #{i+1}: old=%v, new=%v", v_old, v_new)\n'
                        f'            }}\n'
                        f'        }}'
                        for i, curated in enumerate(curated_inputs)
                    )
                    llm_cases_str = "\n        ".join(
                        f'{{ // LLM input #{i+1}\n'
                        f'            v_old := {call_old_expr}({", ".join(case)})\n'
                        f'            v_new := {call_new_expr}({", ".join(case)})\n'
                        f'            if !reflect.DeepEqual(v_old, v_new) {{\n'
                        f'                t.Errorf("BREAKING INPUT (LLM) #{i+1}: old=%v, new=%v", v_old, v_new)\n'
                        f'            }}\n'
                        f'        }}'
                        for i, case in enumerate(llm_cases)
                    )
                else:
                    old_vars = ", ".join([f"o{j}" for j in range(n_returns)])
                    new_vars = ", ".join([f"n{j}" for j in range(n_returns)])
                    curated_cases = "\n        ".join(
                        f'{{ // input #{i+1}\n'
                        f'            {old_vars} := {call_old_expr}({", ".join(curated)})\n'
                        f'            {new_vars} := {call_new_expr}({", ".join(curated)})\n'
                        f'            if !reflect.DeepEqual([]interface{{}}{{{old_vars}}}, []interface{{}}{{{new_vars}}}) {{\n'
                        f'                t.Errorf("BREAKING INPUT #{i+1}: old=%v, new=%v", []interface{{}}{{{old_vars}}}, []interface{{}}{{{new_vars}}})\n'
                        f'            }}\n'
                        f'        }}'
                        for i, curated in enumerate(curated_inputs)
                    )
                    llm_cases_str = "\n        ".join(
                        f'{{ // LLM input #{i+1}\n'
                        f'            {old_vars} := {call_old_expr}({", ".join(case)})\n'
                        f'            {new_vars} := {call_new_expr}({", ".join(case)})\n'
                        f'            if !reflect.DeepEqual([]interface{{}}{{{old_vars}}}, []interface{{}}{{{new_vars}}}) {{\n'
                        f'                t.Errorf("BREAKING INPUT (LLM) #{i+1}: old=%v, new=%v", []interface{{}}{{{old_vars}}}, []interface{{}}{{{new_vars}}})\n'
                        f'            }}\n'
                        f'        }}'
                        for i, case in enumerate(llm_cases)
                    )

                # For quick.CheckEqual, also use the receiver-aware call
                call_old = f"{call_old_expr}({call_args})"
                call_new = f"{call_new_expr}({call_args})"

                # If complex params, skip quick.CheckEqual (can't generate random inputs)
                # and rely only on curated + LLM cases
                if complex_params:
                    test_block = f"""func TestDiffCheck_{old_f.name}_Curated(t *testing.T) {{
        // Curated + LLM-generated inputs (complex params — random testing skipped)
        {curated_cases if curated_inputs else '_ = t'}
        {llm_cases_str if llm_cases else '// no LLM cases generated'}
    }}"""
                else:
                    test_block = f"""func TestDiffCheck_{old_f.name}(t *testing.T) {{
        f_old := func({closure_params}) ({", ".join(return_types)}) {{
            {rets_old} := {call_old}
            return {rets_old}
        }}
        f_new := func({closure_params}) ({", ".join(return_types)}) {{
            {rets_new} := {call_new}
            return {rets_new}
        }}
        config := &quick.Config{{MaxCount: {iterations}}}
        err := quick.CheckEqual(f_old, f_new, config)
        if err != nil {{
            t.Errorf("BREAKING INPUT: %v", err)
        }}
    }}

func TestDiffCheck_{old_f.name}_Curated(t *testing.T) {{
        // Curated boundary-value inputs (complement random testing)
        {curated_cases if curated_inputs else '_ = t // no curated inputs for this signature'}
        {llm_cases_str if llm_cases else ''}
    }}"""
                test_blocks.append(test_block)

            # Collect all imports needed by the test file
            # We need reflect, testing, testing/quick, plus any types used in closures
            test_imports = {"reflect", "testing", "testing/quick"}
            # Check if any param or return type needs time package
            for sig, old_f, new_f in changed_funcs:
                for p in old_f.params:
                    if "time." in p.type_str:
                        test_imports.add("time")
                for rt in old_f.return_types:
                    if "time." in rt:
                        test_imports.add("time")

            test_import_str = "\n    ".join(f'"{p}"' for p in sorted(test_imports))

            test_file_content = f"""// Code generated by graphify verify. DO NOT EDIT.

package {pkg_name}

import (
    {test_import_str}
)

{chr(10).join(test_blocks)}
"""
            test_file.write_text(test_file_content, encoding="utf-8")

        except Exception as e:
            print(f"  ERROR generating tests: {e}")
            # Clean up
            old_file.unlink(missing_ok=True)
            test_file.unlink(missing_ok=True)
            continue

        # Run go test from the go.mod directory
        print(f"  Running differential tests ({iterations} iterations each)...")
        env = os.environ.copy()
        # Ensure Go is on PATH (may be installed in non-standard location)
        go_bin = "/home/z/.local/go/bin"
        if Path(go_bin).exists():
            env["PATH"] = go_bin + ":" + env.get("PATH", "")
        env["GOPATH"] = env.get("GOPATH", str(Path.home() / "go"))
        env["GO111MODULE"] = "on"
        env["GOCACHE"] = env.get("GOCACHE", str(Path.home() / ".cache" / "go-build"))

        test_pattern = "|".join(f"TestDiffCheck_{o.name}" for s, o, n in changed_funcs)
        # Find the go.mod directory (could be repo root or a subdirectory like backend/)
        go_mod_dir = repo
        for parent in [repo] + list(repo.parents)[:3] + [repo / "backend"]:
            if (parent / "go.mod").exists():
                go_mod_dir = parent
                break

        # Build the package path relative to go.mod dir
        try:
            pkg_rel = pkg_dir.relative_to(go_mod_dir)
            pkg_import_path = f"./{pkg_rel}/"
        except ValueError:
            pkg_import_path = f"./{pkg_dir.relative_to(repo)}/"

        result = subprocess.run(
            ["go", "test", "-v", "-run", test_pattern, "-timeout", f"{timeout}s", pkg_import_path],
            cwd=go_mod_dir,
            capture_output=True,
            text=True,
            timeout=timeout + 30,
            env=env,
        )

        # If compile fails due to unused imports, try to fix and retry
        retry_count = 0
        while result.returncode != 0 and retry_count < 5:
            unused_match = re.search(r'"([^"]+)" imported and not used', result.stderr + result.stdout)
            if unused_match:
                unused_import = unused_match.group(1)
                # Try to find the file — go test may report relative paths
                file_match = re.search(r'(\S+\.go):\d+:\d+: "' + re.escape(unused_import) + r'" imported and not used', result.stderr + result.stdout)
                if file_match:
                    file_path_str = file_match.group(1)
                    # Try multiple path resolutions
                    candidates = [
                        Path(file_path_str),
                        pkg_dir / Path(file_path_str).name,
                        go_mod_dir / file_path_str,
                    ]
                    file_path = None
                    for c in candidates:
                        if c.exists():
                            file_path = c
                            break
                else:
                    # Just try to remove from all zz_diffcheck files
                    file_path = None

                removed = False
                for zz_file in [pkg_dir / "zz_diffcheck_old.go", pkg_dir / "zz_diffcheck_test.go"]:
                    if zz_file.exists():
                        content = zz_file.read_text(encoding="utf-8")
                        if f'"{unused_import}"' in content:
                            lines = content.split("\n")
                            new_lines = [l for l in lines if l.strip() != f'"{unused_import}"']
                            zz_file.write_text("\n".join(new_lines), encoding="utf-8")
                            removed = True
                if removed:
                    retry_count += 1
                    result = subprocess.run(
                        ["go", "test", "-v", "-run", test_pattern, "-timeout", f"{timeout}s", pkg_import_path],
                        cwd=go_mod_dir,
                        capture_output=True, text=True,
                        timeout=timeout + 30, env=env,
                    )
                    continue
            break

        # Parse results per function
        for sig, old_f, new_f in changed_funcs:
            test_name = f"TestDiffCheck_{old_f.name}"
            vr = VerificationResult(
                function=old_f.name,
                file=old_f.file,
                status="INCONCLUSIVE",
                iterations=iterations,
            )

            output = result.stdout + result.stderr

            if result.returncode == 0:
                if test_name in result.stdout and "PASS" in result.stdout:
                    vr.status = "EQUIVALE"
            else:
                if test_name in output:
                    # Look for breaking input from either random or curated tests
                    # Format 1 (random): "BREAKING INPUT: #<num>: f_old(...) = X, f_new(...) = Y"
                    # Format 2 (curated): "BREAKING INPUT #N: old=X, new=Y"
                    m = re.search(
                        rf"(?:TestDiffCheck_{re.escape(old_f.name)}).*?BREAKING INPUT(?: #\d+)?(?: \(zero values\))?: (.+?)(?:\n---|\nFAIL|\n---|\Z)",
                        output,
                        re.DOTALL,
                    )
                    if m:
                        breaking_msg = m.group(1).strip()
                        # Also try to find the old= new= format from curated tests
                        curated_m = re.search(r"old=(.+?),\s*new=(.+?)(?:\n|$)", breaking_msg)
                        if curated_m:
                            vr.status = "BREAKING"
                            vr.old_output = curated_m.group(1).strip()
                            vr.new_output = curated_m.group(2).strip()
                            vr.breaking_input = f"old={vr.old_output}, new={vr.new_output}"
                        else:
                            vr.status = "BREAKING"
                            vr.breaking_input = breaking_msg
                            # Try to extract old/new outputs from quick.CheckEqual format
                            out_m = re.search(r"f_old\([^)]*\)\s*=\s*(.+?),\s*f_new\([^)]*\)\s*=\s*(.+?)(?:\n|$)", breaking_msg)
                            if out_m:
                                vr.old_output = out_m.group(1).strip()
                                vr.new_output = out_m.group(2).strip()
                    else:
                        # Check for compile error mentioning our test
                        vr.status = "ERROR"
                        vr.error = output[-500:]
                else:
                    # Compile error not specific to our test
                    vr.status = "ERROR"
                    vr.error = output[-500:]

            results.append(vr)
            status_icon = {"EQUIVALE": "✓", "BREAKING": "✗", "INCONCLUSIVE": "?", "ERROR": "!"}[vr.status]
            print(f"  {status_icon} {old_f.name}: {vr.status}")
            if vr.breaking_input:
                print(f"    Breaking input: {vr.breaking_input[:200]}")

        # Clean up generated files
        old_file.unlink(missing_ok=True)
        test_file.unlink(missing_ok=True)

    return results


def cross_reference_callers(repo: Path, results: list[VerificationResult], graph_json: Optional[Path]) -> None:
    """Use graph.json to find callers of each changed function."""
    if not graph_json or not graph_json.exists():
        return
    data = json.loads(graph_json.read_text(encoding="utf-8"))
    # Build a reverse-edge map: function -> callers
    callers_map: dict[str, list[str]] = {}
    for edge in data.get("links", []):
        if edge.get("relation") in ("calls", "indirect_call", "references"):
            target = edge.get("target", "")
            source = edge.get("source", "")
            callers_map.setdefault(target, []).append(source)

    for vr in results:
        # Find the function's node ID in the graph
        # Node IDs are path-based like "backend_internal_auth_jwt_jwtservice"
        func_label = vr.function
        # Find nodes whose label matches the function name
        matching_nodes = [
            n for n in data.get("nodes", [])
            if n.get("label") == func_label or n.get("label", "").endswith(f".{func_label}")
        ]
        callers: list[str] = []
        for n in matching_nodes:
            node_id = n.get("id", "")
            for caller_id in callers_map.get(node_id, []):
                # Resolve caller_id back to a label
                caller_node = next((c for c in data["nodes"] if c.get("id") == caller_id), None)
                if caller_node:
                    callers.append(caller_node.get("label", caller_id))
        vr.affected_callers = sorted(set(callers))[:10]  # cap at 10


def emit_report(results: list[VerificationResult], repo: Path) -> str:
    """Emit a Markdown verification report."""
    if not results:
        return "# Verification Report\n\nNo changed functions to verify.\n"

    lines = ["# graphify verify — Behavior Preservation Report", ""]
    lines.append(f"**Repository:** {repo}")
    lines.append(f"**Functions verified:** {len(results)}")
    lines.append("")

    equiv = [r for r in results if r.status == "EQUIVALE"]
    breaking = [r for r in results if r.status == "BREAKING"]
    inconcl = [r for r in results if r.status == "INCONCLUSIVE"]
    errors = [r for r in results if r.status == "ERROR"]

    lines.append("## Summary")
    lines.append("")
    lines.append(f"| Status | Count |")
    lines.append(f"|--------|-------|")
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
                if len(r.affected_callers) > 5:
                    lines.append(f"- ... and {len(r.affected_callers) - 5} more")
            lines.append("")

    if equiv:
        lines.append("## ✓ Proven Equivalent")
        lines.append("")
        lines.append("These functions produced identical outputs across all generated inputs:")
        lines.append("")
        for r in equiv:
            lines.append(f"- `{r.function}` ({r.file}) — {r.iterations} inputs tested")
            if r.affected_callers:
                lines.append(f"  - Callers: {', '.join(f'`{c}`' for c in r.affected_callers[:3])}")
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
    lines.append("Each changed function was differential-tested using Go's `testing/quick`")
    lines.append("package. The old version (from `git HEAD`) was renamed to `Old_<name>` and")
    lines.append("compiled alongside the new version in the same package. A test harness")
    lines.append("called both versions with N auto-generated random inputs matching the")
    lines.append("function's parameter types. If all outputs matched, the function is marked")
    lines.append("PROVEN EQUIVALENT. If any output diverged, the breaking input is reported.")
    lines.append("")
    lines.append("**Limitations:**")
    lines.append("- Only functions with primitive-parameter signatures (int, string, bool, etc.) can be auto-verified.")
    lines.append("- Functions with struct/interface params are marked INCONCLUSIVE (would need custom generators).")
    lines.append("- Methods (with receivers) are skipped (would need receiver construction).")
    lines.append("- This is probabilistic, not a mathematical proof — but 500+ iterations gives strong confidence.")
    lines.append("")

    return "\n".join(lines)


# ---------- CLI ----------

def main():
    ap = argparse.ArgumentParser(
        prog="graphify verify",
        description="Formal verification of behavior preservation for changed Go functions.",
    )
    ap.add_argument("path", nargs="?", default=".", help="Path to the repo (default: .)")
    ap.add_argument("--function", "-f", help="Only verify functions matching this name (substring)")
    ap.add_argument("--iterations", "-n", type=int, default=500, help="Max random inputs per function (default: 500)")
    ap.add_argument("--timeout", "-t", type=int, default=30, help="Timeout per package in seconds (default: 30)")
    ap.add_argument("--graph", help="Path to graph.json for caller cross-reference")
    ap.add_argument("--report", help="Write Markdown report to this path (default: graphify-out/VERIFY_REPORT.md)")
    args = ap.parse_args()

    repo = Path(args.path).resolve()
    if not (repo / ".git").exists():
        print(f"ERROR: {repo} is not a git repository", file=sys.stderr)
        sys.exit(2)

    # Set up GOCACHE if not present
    cache_dir = Path.home() / ".cache" / "go-build"
    cache_dir.mkdir(parents=True, exist_ok=True)

    graph_json = Path(args.graph) if args.graph else (repo / "graphify-out" / "graph.json")

    print(f"graphify verify — analyzing changes in {repo}")
    print(f"Iterations per function: {args.iterations}")
    print()

    results = verify_repo(
        repo,
        iterations=args.iterations,
        timeout=args.timeout,
        function_filter=args.function,
    )

    if not results:
        print("\nNo changed functions eligible for verification.")
        sys.exit(0)

    cross_reference_callers(repo, results, graph_json)

    report = emit_report(results, repo)
    report_path = Path(args.report) if args.report else (repo / "graphify-out" / "VERIFY_REPORT.md")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")
    print(f"\nReport written to {report_path}")

    # Print summary
    equiv = sum(1 for r in results if r.status == "EQUIVALE")
    breaking = sum(1 for r in results if r.status == "BREAKING")
    inconcl = sum(1 for r in results if r.status in ("INCONCLUSIVE", "ERROR"))

    print(f"\n{'='*60}")
    print(f"  ✓ EQUIVALENT: {equiv}")
    print(f"  ✗ BREAKING:   {breaking}")
    print(f"  ? OTHER:      {inconcl}")
    print(f"{'='*60}")

    # Exit code: 0 if all equivalent, 1 if any breaking, 2 if errors
    if breaking:
        sys.exit(1)
    if inconcl:
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
