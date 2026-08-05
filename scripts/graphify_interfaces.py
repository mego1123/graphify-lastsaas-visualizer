#!/usr/bin/env python3
"""graphify interfaces — Go interface satisfaction checker.

Scans all .go files in a repository and:

  1. Collects every `type X interface { ... }` declaration and the methods
     it requires (including embedded interfaces by name).
  2. Collects every `type Y struct { ... }` declaration and every method
     bound to it (both value receivers `func (s Y) M()` and pointer
     receivers `func (s *Y) M()`).
  3. For each interface, walks every struct and decides whether that struct
     (or its pointer) satisfies the interface — Go has *implicit* interface
     implementation, so this is the only way to discover the relationship.
  4. Reports:
       - all interfaces with their method count
       - which structs implement each interface
       - interfaces with only one implementor (likely over-designed)
       - interfaces with zero implementors (dead interfaces)

Usage:
  python graphify_interfaces.py [path] [--out report.md] [--json]

Defaults: writes JSON to public/interfaces.json and markdown to
public/INTERFACES.md if `--out` is omitted and the script is run from the
graphify workspace root.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

# ---------------------------------------------------------------------------
# Regexes
# ---------------------------------------------------------------------------

# `type Name interface {` — open brace may be at end of line.
RE_INTERFACE_OPEN = re.compile(
    r"type\s+(?P<name>[A-Z]\w*)\s+interface\s*\{"
)

# `type Name struct {` — same shape; also catches `type Name struct{}` on
# one line because we tolerate zero-or-more whitespace before `{`.
RE_STRUCT_OPEN = re.compile(
    r"type\s+(?P<name>[A-Z]\w*)\s+struct\s*\{"
)

# Method declaration on a struct:
#   func (recv Type) Method(params) returns
#   func (recv *Type) Method(params) returns
# We capture receiver name, whether it is a pointer, the type name, and the
# method name.
RE_METHOD = re.compile(
    r"func\s+\(\s*(?P<recv>\w+)\s+(?P<ptr>\*?)(?P<type>[A-Z]\w*)\s*\)\s+"
    r"(?P<method>[A-Z]\w*)\s*\("
)

# Identifier inside an interface body that is followed by `(` — that's a
# method declaration. Anything else (e.g. another `type X interface {}`
# on the same line, or an embedded interface name with no parens) is not a
# method of this interface.
RE_IFACE_METHOD = re.compile(r"\b(?P<name>[A-Z]\w*)\s*\(")

# Embedded interface inside an interface body: a bare identifier on its own
# line (no parens). Could be `io.Reader` or `error` or `Foo`.
RE_IFACE_EMBED = re.compile(r"^\s*(?P<name>(?:[a-z]\w*\.)?[A-Z]\w*|error)\s*$")

# Comment line so we can extract docstrings for interface methods.
RE_COMMENT = re.compile(r"^\s*//\s*(?P<text>.*)$")


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class InterfaceMethod:
    name: str
    signature: str  # raw text after the name, e.g. "(ctx context.Context) error"


@dataclass
class InterfaceDecl:
    name: str
    file: str
    package: str
    methods: List[InterfaceMethod] = field(default_factory=list)
    embedded: List[str] = field(default_factory=list)
    doc: str = ""
    implementors: List[str] = field(default_factory=list)  # struct names
    pointer_only_implementors: List[str] = field(default_factory=list)


@dataclass
class StructMethod:
    name: str
    pointer_receiver: bool
    signature: str


@dataclass
class StructDecl:
    name: str
    file: str
    package: str
    methods: List[StructMethod] = field(default_factory=list)
    doc: str = ""

    @property
    def value_method_set(self) -> Set[str]:
        return {m.name for m in self.methods if not m.pointer_receiver}

    @property
    def pointer_method_set(self) -> Set[str]:
        # `*T` has access to both value and pointer receiver methods.
        return {m.name for m in self.methods}

    @property
    def total_method_count(self) -> int:
        return len(self.methods)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def find_go_files(repo: Path, include_tests: bool = False) -> List[Path]:
    """Return every .go file in repo, skipping vendor / generated / test dirs."""
    skip_dirs = {"vendor", "node_modules", ".git", "graphify-out", "dist", "build"}
    out: List[Path] = []
    for p in repo.rglob("*.go"):
        if any(part in skip_dirs for part in p.parts):
            continue
        if not include_tests and p.name.endswith("_test.go"):
            continue
        out.append(p)
    return sorted(out)


def extract_package(content: str) -> str:
    m = re.search(r"^\s*package\s+(\w+)", content, re.MULTILINE)
    return m.group(1) if m else ""


def brace_block(content: str, start: int) -> Tuple[str, int]:
    """Return the text inside the brace block starting at index `start`,
    where `start` is the position of the opening `{`. Returns (body, end)
    where `end` is the index just after the closing `}`.
    """
    depth = 0
    i = start
    while i < len(content):
        ch = content[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return content[start + 1 : i], i + 1
        i += 1
    # Unbalanced — return everything from start to end.
    return content[start + 1 :], len(content)


def preceding_doc_comment(content: str, idx: int) -> str:
    """Walk backwards from `idx` collecting consecutive `//` comment lines."""
    lines = content[:idx].splitlines()
    out: List[str] = []
    for line in reversed(lines):
        m = RE_COMMENT.match(line)
        if m:
            out.append(m.group("text").strip())
        elif line.strip() == "":
            continue
        else:
            break
    return " ".join(reversed(out)).strip()


# ---------------------------------------------------------------------------
# Parsers
# ---------------------------------------------------------------------------

def parse_interfaces(content: str, file: str, package: str) -> List[InterfaceDecl]:
    out: List[InterfaceDecl] = []
    for m in RE_INTERFACE_OPEN.finditer(content):
        name = m.group("name")
        # Find the open brace index from the match object.
        brace_idx = content.index("{", m.start())
        body, _end = brace_block(content, brace_idx)
        doc = preceding_doc_comment(content, m.start())
        decl = InterfaceDecl(name=name, file=file, package=package, doc=doc)

        # Walk the body line-by-line so we can distinguish methods from
        # embedded interfaces cleanly.
        for raw_line in body.splitlines():
            line = raw_line.strip()
            if not line or line.startswith("//"):
                # Inline comment — pull the method name out if any.
                if "//" in line:
                    before = line.split("//", 1)[0].strip()
                    if before:
                        mm = RE_IFACE_METHOD.search(before)
                        if mm:
                            decl.methods.append(
                                InterfaceMethod(name=mm.group("name"), signature=before)
                            )
                continue
            # Embedded interface? (bare identifier on its own line)
            em = RE_IFACE_EMBED.match(line)
            method_match = RE_IFACE_METHOD.search(line)
            if method_match:
                decl.methods.append(
                    InterfaceMethod(name=method_match.group("name"), signature=line)
                )
            elif em:
                decl.embedded.append(em.group("name"))
            # Anything else is ignored — it might be a multi-line method
            # signature split across lines, which we handle below.
        # Try to recover multi-line method signatures: re-join lines that
        # contain an identifier followed by `(` but no closing `)` on the
        # same line.
        joined = re.sub(r"\s+", " ", body).strip()
        if joined:
            # Find every identifier immediately followed by `(`.
            for mm in RE_IFACE_METHOD.finditer(joined):
                # Avoid duplicates with what we already captured.
                if any(existing.name == mm.group("name") for existing in decl.methods):
                    continue
                # Slice from the identifier to the matching close paren on
                # the joined string, then store as signature.
                start = mm.start()
                depth = 0
                end = start
                for i in range(start, len(joined)):
                    if joined[i] == "(":
                        depth += 1
                    elif joined[i] == ")":
                        depth -= 1
                        if depth == 0:
                            end = i + 1
                            break
                sig = joined[start:end]
                decl.methods.append(InterfaceMethod(name=mm.group("name"), signature=sig))
        out.append(decl)
    return out


def parse_structs(content: str, file: str, package: str) -> List[StructDecl]:
    out: List[StructDecl] = []
    for m in RE_STRUCT_OPEN.finditer(content):
        name = m.group("name")
        brace_idx = content.index("{", m.start())
        _body, _end = brace_block(content, brace_idx)
        doc = preceding_doc_comment(content, m.start())
        out.append(StructDecl(name=name, file=file, package=package, doc=doc))
    return out


def parse_methods(content: str, file: str, package: str) -> List[Tuple[str, StructMethod]]:
    """Return [(struct_name, StructMethod), ...] for every method declared
    in this file. The struct_name is the bare type name (Go method receivers
    never include a package qualifier — methods live in the same package as
    the type). The `package` arg is attached to the StructMethod via the
    caller so cross-package name collisions can be resolved later.
    """
    out: List[Tuple[str, StructMethod]] = []
    for m in RE_METHOD.finditer(content):
        struct_name = m.group("type")
        pointer = bool(m.group("ptr"))
        method_name = m.group("method")
        # Capture the signature text: from method name to end of line (rough).
        line_end = content.find("\n", m.end())
        if line_end == -1:
            line_end = len(content)
        # Also include continuation lines if the closing paren of the params
        # hasn't appeared yet.
        chunk = content[m.start() : line_end]
        # If params close paren is not yet in chunk, extend.
        if chunk.count("(") < chunk.count(")") or chunk.count("(") > chunk.count(")"):
            # Find balanced close paren starting at the method name's `(`.
            paren_open = content.index("(", m.end() - 1)
            depth = 0
            i = paren_open
            while i < len(content):
                if content[i] == "(":
                    depth += 1
                elif content[i] == ")":
                    depth -= 1
                    if depth == 0:
                        chunk = content[m.start() : i + 1]
                        break
                i += 1
        out.append(
            (struct_name, StructMethod(name=method_name, pointer_receiver=pointer, signature=chunk))
        )
    return out


# ---------------------------------------------------------------------------
# Resolution
# ---------------------------------------------------------------------------

def resolve_embeddings(
    interfaces: Dict[str, InterfaceDecl],
) -> None:
    """Flatten embedded interface methods into each interface's method list.

    Embedding is by name; cross-package embeddings (with a `.`) are kept as
    references but their methods are not pulled in (we don't have stdlib
    signatures here).
    """
    # Build a lookup by name (last-seen wins if duplicates exist).
    by_name: Dict[str, InterfaceDecl] = {i.name: i for i in interfaces.values()}

    def collect(name: str, seen: Set[str]) -> List[InterfaceMethod]:
        if name in seen:
            return []
        seen.add(name)
        decl = by_name.get(name)
        if decl is None:
            return []
        methods = list(decl.methods)
        for emb in decl.embedded:
            if "." in emb:
                # Cross-package embedding — we can't resolve.
                continue
            methods.extend(collect(emb, seen))
        return methods

    for decl in interfaces.values():
        full: List[InterfaceMethod] = []
        seen_names: Set[str] = set()
        for m in collect(decl.name, set()):
            if m.name not in seen_names:
                full.append(m)
                seen_names.add(m.name)
        decl.methods = full


def assign_methods_to_structs(
    structs: Dict[str, StructDecl],
    raw_methods: List[Tuple[str, StructMethod]],
) -> None:
    """Attach each parsed method to its struct.

    The struct is looked up by bare name (Go methods are always defined in
    the same package as the type, so the receiver name is unambiguous within
    that package). If the struct declaration wasn't seen — sometimes methods
    live in a different file from the `type X struct` line — we create a
    synthetic struct entry so the method still gets tracked.
    """
    # Build a name -> StructDecl index. If the same name appears in two
    # packages we keep both; the bare-name lookup below will pick the first
    # one. That's an acceptable trade-off for static analysis.
    by_name: Dict[str, StructDecl] = {}
    for key, s in structs.items():
        # `key` may be "pkg.Name" or just "Name". Prefer the bare name.
        bare = key.rsplit(".", 1)[-1]
        if bare not in by_name:
            by_name[bare] = s
        else:
            # If we already have one with the same bare name, keep whichever
            # is the "real" declaration (i.e. not synthetic).
            existing = by_name[bare]
            if existing.file == "(synthetic)" and s.file != "(synthetic)":
                by_name[bare] = s

    for struct_name, method in raw_methods:
        s = by_name.get(struct_name)
        if s is None:
            s = StructDecl(name=struct_name, file="(synthetic)", package="")
            by_name[struct_name] = s
            structs[struct_name] = s  # also register in the main dict
        # Avoid double-counting: a method declared twice (e.g. build tag
        # variants) should be deduped by (name, pointer_receiver).
        dup = any(
            m.name == method.name and m.pointer_receiver == method.pointer_receiver
            for m in s.methods
        )
        if not dup:
            s.methods.append(method)

    # Make sure every struct in `structs` is also referenced by bare name
    # so downstream lookups (find_implementors) work consistently.
    for key, s in list(structs.items()):
        bare = key.rsplit(".", 1)[-1]
        if bare not in by_name:
            by_name[bare] = s
        # If the dict was keyed by "pkg.Name", also add a bare alias.
        if "." in key and bare not in structs:
            structs[bare] = s


def find_implementors(
    interface: InterfaceDecl,
    structs: Dict[str, StructDecl],
) -> Tuple[List[str], List[str]]:
    """Return (value_implementors, pointer_only_implementors)."""
    required = {m.name for m in interface.methods}
    if not required:
        # Empty interface — satisfied by everything (skip in practice).
        return [], []
    # Deduplicate structs by name so the same struct registered under both
    # "pkg.Name" and "Name" keys is not reported twice.
    seen: Set[str] = set()
    value_impls: List[str] = []
    ptr_impls: List[str] = []
    for name, s in structs.items():
        bare = name.rsplit(".", 1)[-1]
        if bare in seen:
            continue
        seen.add(bare)
        if required.issubset(s.value_method_set):
            value_impls.append(bare)
        elif required.issubset(s.pointer_method_set):
            ptr_impls.append(bare)
    return value_impls, ptr_impls


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def emit_markdown(
    interfaces: List[InterfaceDecl],
    structs: List[StructDecl],
    repo: Path,
) -> str:
    lines: List[str] = []
    lines.append("# Interface Satisfaction Report")
    lines.append("")
    lines.append(f"Repository: `{repo}`")
    lines.append("")
    total_ifaces = len(interfaces)
    total_structs = len(structs)
    total_methods = sum(len(i.methods) for i in interfaces)
    lines.append(f"- **Interfaces scanned**: {total_ifaces}")
    lines.append(f"- **Structs scanned**: {total_structs}")
    lines.append(f"- **Interface methods total**: {total_methods}")
    lines.append("")

    # --- Summary table -----------------------------------------------------
    lines.append("## Summary — Interfaces")
    lines.append("")
    lines.append("| Interface | Package | Methods | Implementors | Pointer-only | Status |")
    lines.append("|-----------|---------|---------|--------------|--------------|--------|")
    for i in sorted(interfaces, key=lambda x: (-len(x.implementors), x.name)):
        status = "✅ healthy"
        if len(i.implementors) == 0 and len(i.pointer_only_implementors) == 0:
            status = "💀 dead (no implementors)"
        elif len(i.implementors) + len(i.pointer_only_implementors) == 1:
            status = "⚠️ single implementor (over-designed?)"
        lines.append(
            f"| `{i.name}` | `{i.package}` | {len(i.methods)} | "
            f"{len(i.implementors)} | {len(i.pointer_only_implementors)} | {status} |"
        )
    lines.append("")

    # --- Per-interface detail ---------------------------------------------
    lines.append("## Per-Interface Detail")
    lines.append("")
    for i in sorted(interfaces, key=lambda x: x.name):
        lines.append(f"### `{i.name}`")
        lines.append("")
        lines.append(f"- **File**: `{i.file}`")
        lines.append(f"- **Package**: `{i.package}`")
        if i.doc:
            lines.append(f"- **Doc**: {i.doc}")
        if i.embedded:
            lines.append(f"- **Embeds**: {', '.join(f'`{e}`' for e in i.embedded)}")
        lines.append(f"- **Method count**: {len(i.methods)}")
        lines.append("")
        if i.methods:
            lines.append("| Method | Signature |")
            lines.append("|--------|-----------|")
            for m in i.methods:
                lines.append(f"| `{m.name}` | `{m.signature}` |")
            lines.append("")
        all_impls = i.implementors + i.pointer_only_implementors
        if not all_impls:
            lines.append("> 💀 **No struct in the codebase satisfies this interface.**")
            lines.append("")
        else:
            lines.append("#### Implementors")
            lines.append("")
            lines.append("| Struct | Receiver | File |")
            lines.append("|--------|----------|------|")
            for name in sorted(i.implementors):
                # Find the struct file.
                s = next((x for x in structs if x.name == name), None)
                f = s.file if s else "?"
                lines.append(f"| `{name}` | value (`T`) | `{f}` |")
            for name in sorted(i.pointer_only_implementors):
                s = next((x for x in structs if x.name == name), None)
                f = s.file if s else "?"
                lines.append(f"| `{name}` | pointer (`*T`) | `{f}` |")
            lines.append("")

    # --- Dead interfaces ---------------------------------------------------
    dead = [i for i in interfaces if not (i.implementors or i.pointer_only_implementors)]
    lines.append("## Dead Interfaces (0 implementors)")
    lines.append("")
    if dead:
        for i in dead:
            lines.append(f"- `{i.name}` — `{i.file}` — {len(i.methods)} methods")
        lines.append("")
        lines.append(
            "These interfaces have no struct that satisfies them. Either remove "
            "them, or add a production implementation. (Note: stdlib interface "
            "embeddings like `io.Reader` cannot be checked here — see the "
            "Embeds column above.)"
        )
    else:
        lines.append("_None — every declared interface has at least one implementor._")
    lines.append("")

    # --- Single-implementor interfaces ------------------------------------
    single = [
        i
        for i in interfaces
        if len(i.implementors) + len(i.pointer_only_implementors) == 1
    ]
    lines.append("## Single-Implementor Interfaces (may be over-designed)")
    lines.append("")
    if single:
        for i in single:
            impl = (i.implementors + i.pointer_only_implementors)[0]
            lines.append(
                f"- `{i.name}` — only implemented by `{impl}` — `{i.file}`"
            )
        lines.append("")
        lines.append(
            "An interface with a single implementor is a candidate for removal "
            "unless the indirection is needed for testing (mocks) or future "
            "extensibility."
        )
    else:
        lines.append("_None._")
    lines.append("")

    # --- Top structs by method count --------------------------------------
    lines.append("## Top Structs by Method Count")
    lines.append("")
    lines.append("| Struct | File | Methods (value) | Methods (pointer) | Total |")
    lines.append("|--------|------|------------------|--------------------|-------|")
    sorted_structs = sorted(structs, key=lambda s: -s.total_method_count)
    for s in sorted_structs[:25]:
        v = len([m for m in s.methods if not m.pointer_receiver])
        p = len([m for m in s.methods if m.pointer_receiver])
        lines.append(
            f"| `{s.name}` | `{s.file}` | {v} | {p} | {s.total_method_count} |"
        )
    lines.append("")

    # --- Notes -------------------------------------------------------------
    lines.append("## Notes")
    lines.append("")
    lines.append(
        "- Go interfaces are satisfied *implicitly* — there is no `implements` "
        "keyword. This tool inspects every struct's method set and checks "
        "whether it is a superset of each interface's required methods."
    )
    lines.append(
        "- Pointer-receiver methods are only available on `*T`, so a struct "
        "that satisfies an interface purely through pointer methods is listed "
        "as a *pointer-only* implementor."
    )
    lines.append(
        "- Cross-package interface embeddings (e.g. `io.Reader`) cannot be "
        "resolved by static scan — those methods are not counted."
    )
    lines.append(
        "- Test files (`*_test.go`) are excluded by default to keep the "
        "report focused on production code."
    )
    lines.append("")
    return "\n".join(lines)


def emit_json(
    interfaces: List[InterfaceDecl],
    structs: List[StructDecl],
    repo: Path,
) -> str:
    payload = {
        "repository": str(repo),
        "summary": {
            "interfaces": len(interfaces),
            "structs": len(structs),
            "total_interface_methods": sum(len(i.methods) for i in interfaces),
            "dead_interfaces": [
                i.name for i in interfaces
                if not (i.implementors or i.pointer_only_implementors)
            ],
            "single_implementor_interfaces": [
                i.name for i in interfaces
                if len(i.implementors) + len(i.pointer_only_implementors) == 1
            ],
        },
        "interfaces": [
            {
                **asdict(i),
                "implementor_count": len(i.implementors) + len(i.pointer_only_implementors),
            }
            for i in interfaces
        ],
        "structs": [
            {
                "name": s.name,
                "file": s.file,
                "package": s.package,
                "doc": s.doc,
                "method_count": s.total_method_count,
                "value_method_count": len([m for m in s.methods if not m.pointer_receiver]),
                "pointer_method_count": len([m for m in s.methods if m.pointer_receiver]),
                "methods": [asdict(m) for m in s.methods],
            }
            for s in structs
        ],
    }
    return json.dumps(payload, indent=2)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def analyze(repo: Path, include_tests: bool = False) -> Tuple[List[InterfaceDecl], List[StructDecl]]:
    files = find_go_files(repo, include_tests=include_tests)
    print(f"  Scanning {len(files)} .go files", file=sys.stderr)

    interfaces: Dict[str, InterfaceDecl] = {}
    structs: Dict[str, StructDecl] = {}
    raw_methods: List[Tuple[str, StructMethod]] = []

    for f in files:
        try:
            content = f.read_text(encoding="utf-8", errors="replace")
        except Exception as exc:
            print(f"  ! could not read {f}: {exc}", file=sys.stderr)
            continue
        package = extract_package(content)
        rel = str(f.relative_to(repo))

        for i in parse_interfaces(content, rel, package):
            # Key on (package, name) so duplicates across packages don't
            # clobber each other.
            key = f"{package}.{i.name}" if package else i.name
            interfaces[key] = i
        for s in parse_structs(content, rel, package):
            key = f"{package}.{s.name}" if package else s.name
            # If a struct with the same package.name exists already, prefer
            # the one with the doc comment, but keep both files for the
            # method attachment step.
            if key not in structs:
                structs[key] = s
            else:
                # Merge — keep doc from whichever has one.
                if not structs[key].doc and s.doc:
                    structs[key].doc = s.doc
        raw_methods.extend(parse_methods(content, rel, package))

    resolve_embeddings(interfaces)
    assign_methods_to_structs(structs, raw_methods)

    # Find implementors.
    for i in interfaces.values():
        v, p = find_implementors(i, structs)
        i.implementors = sorted(v)
        i.pointer_only_implementors = sorted(p)

    # Deduplicate structs: we may have both "pkg.Name" and bare "Name" keys
    # pointing at the same StructDecl. Pick unique entries by (name, file).
    seen_structs: Set[Tuple[str, str]] = set()
    unique_structs: List[StructDecl] = []
    for s in structs.values():
        sig = (s.name, s.file)
        if sig in seen_structs:
            continue
        seen_structs.add(sig)
        unique_structs.append(s)

    iface_list = list(interfaces.values())
    struct_list = unique_structs
    return iface_list, struct_list


def main():
    ap = argparse.ArgumentParser(
        prog="graphify interfaces",
        description="Go interface satisfaction checker.",
    )
    ap.add_argument("path", nargs="?", default=".", help="Path to the Go project (or a subdir).")
    ap.add_argument("--out", "-o", help="Output markdown file (default: stdout).")
    ap.add_argument("--json", action="store_true", help="Emit JSON instead of markdown.")
    ap.add_argument(
        "--include-tests",
        action="store_true",
        help="Include *_test.go files (default: skip).",
    )
    args = ap.parse_args()

    repo = Path(args.path).resolve()
    print(f"graphify interfaces — scanning {repo}", file=sys.stderr)
    if not repo.exists():
        print(f"error: path does not exist: {repo}", file=sys.stderr)
        sys.exit(1)

    interfaces, structs = analyze(repo, include_tests=args.include_tests)

    print(
        f"  Found {len(interfaces)} interfaces, {len(structs)} structs",
        file=sys.stderr,
    )
    dead = [i for i in interfaces if not (i.implementors or i.pointer_only_implementors)]
    single = [
        i for i in interfaces
        if len(i.implementors) + len(i.pointer_only_implementors) == 1
    ]
    print(
        f"  {len(dead)} dead, {len(single)} single-implementor",
        file=sys.stderr,
    )

    if args.json:
        output = emit_json(interfaces, structs, repo)
    else:
        output = emit_markdown(interfaces, structs, repo)

    if args.out:
        Path(args.out).write_text(output, encoding="utf-8")
        print(f"Report written to {args.out}", file=sys.stderr)
    else:
        # When no --out is provided, also write the canonical workspace
        # outputs so the graphify UI picks them up.
        workspace_root = Path(os.environ.get("GRAPHIFY_ROOT", "/home/z/my-project"))
        public_dir = workspace_root / "public"
        if public_dir.exists():
            (public_dir / "interfaces.json").write_text(
                emit_json(interfaces, structs, repo), encoding="utf-8"
            )
            (public_dir / "INTERFACES.md").write_text(
                emit_markdown(interfaces, structs, repo), encoding="utf-8"
            )
            print(
                f"  Wrote public/interfaces.json and public/INTERFACES.md",
                file=sys.stderr,
            )
        print(output)


if __name__ == "__main__":
    main()
