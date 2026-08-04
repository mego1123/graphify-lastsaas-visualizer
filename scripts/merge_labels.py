"""Merge LLM-generated community labels into graph.json and graph.html.

Patches graph.json's nodes' `community_name` field with the new labels,
also updates the LEGEND array in graph.html, and re-extracts the slim
JSON files used by the Next.js web app.
"""
import json
import re
from pathlib import Path

GRAPH_JSON = Path("/home/z/my-project/repos/lastsaas/graphify-out/graph.json")
GRAPH_HTML = Path("/home/z/my-project/repos/lastsaas/graphify-out/graph.html")
LABELS = Path("/home/z/my-project/repos/lastsaas/graphify-out/community_labels.json")

labels = json.loads(LABELS.read_text(encoding="utf-8"))
print(f"Loaded {len(labels)} labels")

# --- 1. Patch graph.json ---
data = json.loads(GRAPH_JSON.read_text(encoding="utf-8"))
patched = 0
for n in data["nodes"]:
    cid = n.get("community")
    if cid is None: continue
    new_name = labels.get(str(cid))
    if new_name and new_name != n.get("community_name"):
        n["community_name"] = new_name
        patched += 1
# Also update community_label in graph metadata if present
if "communities" in data.get("graph", {}):
    for c in data["graph"]["communities"]:
        cid = c.get("cid", c.get("id"))
        if cid is not None and str(cid) in labels:
            c["label"] = labels[str(cid)]

GRAPH_JSON.write_text(json.dumps(data), encoding="utf-8")
print(f"Patched {patched} nodes in graph.json")

# --- 2. Patch graph.html (LEGEND + node titles) ---
html = GRAPH_HTML.read_text(encoding="utf-8")

# Replace LEGEND array
def replace_legend(html: str, labels: dict) -> str:
    m = re.search(r'const\s+LEGEND\s*=\s*\[', html)
    if not m:
        print("WARN: LEGEND not found in graph.html")
        return html
    start = m.end() - 1  # position of '['
    depth = 0
    i = start
    in_str = False
    str_ch = ""
    while i < len(html):
        c = html[i]
        if in_str:
            if c == '\\':
                i += 2; continue
            if c == str_ch:
                in_str = False
        else:
            if c in ('"', "'", '`'):
                in_str = True; str_ch = c
            elif c == '[': depth += 1
            elif c == ']':
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        i += 1
    old_legend = html[start:end]
    try:
        old_legend_parsed = json.loads(old_legend)
    except json.JSONDecodeError:
        old_legend_parsed = []
    new_legend = []
    for c in old_legend_parsed:
        cid = c.get("cid")
        new_c = dict(c)
        if str(cid) in labels:
            new_c["label"] = labels[str(cid)]
        new_legend.append(new_c)
    new_legend_str = json.dumps(new_legend)
    return html[:start] + new_legend_str + html[end:]

html = replace_legend(html, labels)

# Patch community_name in RAW_NODES (each node has community_name field)
def patch_raw_nodes(html: str, labels: dict) -> str:
    m = re.search(r'const\s+RAW_NODES\s*=\s*\[', html)
    if not m:
        print("WARN: RAW_NODES not found")
        return html
    start = m.end() - 1
    depth = 0
    i = start
    in_str = False
    str_ch = ""
    while i < len(html):
        c = html[i]
        if in_str:
            if c == '\\':
                i += 2; continue
            if c == str_ch:
                in_str = False
        else:
            if c in ('"', "'", '`'):
                in_str = True; str_ch = c
            elif c == '[': depth += 1
            elif c == ']':
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        i += 1
    old_nodes_str = html[start:end]
    try:
        old_nodes = json.loads(old_nodes_str)
    except json.JSONDecodeError as e:
        print(f"WARN: failed to parse RAW_NODES: {e}")
        return html
    patched = 0
    for n in old_nodes:
        cid = n.get("community")
        if cid is not None and str(cid) in labels:
            n["community_name"] = labels[str(cid)]
            # also update the title (used as tooltip) to include the label
            n["title"] = f"{n.get('label', '')} [{labels[str(cid)]}]"
            patched += 1
    new_nodes_str = json.dumps(old_nodes)
    print(f"Patched {patched} nodes in graph.html RAW_NODES")
    return html[:start] + new_nodes_str + html[end:]

html = patch_raw_nodes(html, labels)

GRAPH_HTML.write_text(html, encoding="utf-8")
print(f"Wrote patched graph.html ({len(html):,} bytes)")

# --- 3. Copy patched outputs to download/ ---
import shutil
download_dir = Path("/home/z/my-project/download/graphify-lastsaas")
shutil.copy(GRAPH_HTML, download_dir / "graph.html")
shutil.copy(GRAPH_JSON, download_dir / "graph.json")
print(f"Copied to {download_dir}")
