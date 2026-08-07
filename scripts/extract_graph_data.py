"""Extract RAW_NODES, RAW_EDGES, COMMUNITIES from graph.html into JSON files
that the Next.js page can import."""
import json
import re
import sys
from pathlib import Path

SRC = Path("/home/z/my-project/repos/lastsaas/graphify-out/graph.html")
OUT_DIR = Path("/home/z/my-project/src/app/api/graph-data")
OUT_DIR.mkdir(parents=True, exist_ok=True)

text = SRC.read_text(encoding="utf-8")

def extract_var(name: str):
    m = re.search(rf"const\s+{name}\s*=\s*(\[|\{{)", text)
    if not m:
        print(f"WARN: {name} not found", file=sys.stderr)
        return None
    start = m.start(1)
    open_ch = m.group(1)
    close_ch = "]" if open_ch == "[" else "}"
    depth = 0
    i = start
    in_str = False
    str_ch = ""
    while i < len(text):
        c = text[i]
        if in_str:
            if c == "\\":
                i += 2
                continue
            if c == str_ch:
                in_str = False
        else:
            if c in ('"', "'", "`"):
                in_str = True
                str_ch = c
            elif c == open_ch:
                depth += 1
            elif c == close_ch:
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        i += 1
    raw = text[start:end]
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"ERROR parsing {name}: {e}", file=sys.stderr)
        return None

nodes = extract_var("RAW_NODES")
edges = extract_var("RAW_EDGES")
communities = extract_var("LEGEND")

print(f"nodes: {len(nodes) if nodes else 0}")
print(f"edges: {len(edges) if edges else 0}")
print(f"communities: {len(communities) if communities else 0}")

slim_nodes = []
if nodes:
    for n in nodes:
        c = n.get("color")
        bg = c.get("background") if isinstance(c, dict) else c
        slim_nodes.append({
            "id": n.get("id"),
            "label": n.get("label"),
            "community": n.get("community"),
            "community_name": n.get("community_name"),
            "color": bg,
            "size": n.get("size", 10),
            "source_file": n.get("source_file"),
            "file_type": n.get("file_type"),
            "degree": n.get("degree", 0),
        })

slim_edges = []
if edges:
    for e in edges:
        slim_edges.append({
            "from": e.get("from"),
            "to": e.get("to"),
            "label": e.get("label"),
            "context": e.get("context"),
            "confidence": e.get("confidence"),
        })

slim_communities = []
if communities:
    for c in communities:
        slim_communities.append({
            "id": c.get("cid", c.get("id")),
            "label": c.get("label") or c.get("name"),
            "color": c.get("color"),
            "count": c.get("count"),
        })

pub = Path("/home/z/my-project/public")
pub.mkdir(exist_ok=True)
(pub / "graph-nodes.json").write_text(json.dumps(slim_nodes), encoding="utf-8")
(pub / "graph-edges.json").write_text(json.dumps(slim_edges), encoding="utf-8")
(pub / "graph-communities.json").write_text(json.dumps(slim_communities), encoding="utf-8")

print(f"wrote {pub/'graph-nodes.json'} ({len(slim_nodes)} nodes)")
print(f"wrote {pub/'graph-edges.json'} ({len(slim_edges)} edges)")
print(f"wrote {pub/'graph-communities.json'} ({len(slim_communities)} communities)")
