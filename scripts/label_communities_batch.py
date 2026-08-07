"""Batch-label graphify communities with z-ai LLM (one call covers ~20 communities).

Instead of 157 separate API calls (which hit rate limits), we batch ~20
communities into a single prompt and ask the LLM to return a JSON object
mapping community_id -> short_label. Far fewer requests, same result.
"""
import json
import subprocess
import time
import re
from pathlib import Path
from collections import defaultdict, Counter

GRAPH = Path("/home/z/my-project/repos/lastsaas/graphify-out/graph.json")
LABELS_OUT = Path("/home/z/my-project/repos/lastsaas/graphify-out/community_labels.json")

data = json.loads(GRAPH.read_text(encoding="utf-8"))
nodes = data["nodes"]
edges = data["links"]

comm_members: dict[int, list[dict]] = defaultdict(list)
for n in nodes:
    cid = n.get("community")
    if cid is None: continue
    comm_members[cid].append(n)

degree = Counter()
for e in edges:
    degree[e["source"]] += 1
    degree[e["target"]] += 1

GENERIC = {"T", "Context", "Request", "ResponseWriter", "ObjectID", "Time",
           "MongoDB", "Collection", "Service", "Client", "Handler", "M",
           "Mutex", "RWMutex", "WaitGroup", "Server", "Database", "Duration",
           "HandlerFunc", "default", "description", "required", "title", "type",
           "name", "version", "url", "private", "author", "maintainers", "$schema",
           "repository", "platforms", "darwin", "linux", "compatibility",
           "dependencies", "devDependencies", "compilerOptions"}

def is_generic(label: str) -> bool:
    if not label: return True
    if label in GENERIC: return True
    if len(label) <= 2: return True
    return False

# Build a compact description per community
comm_descs: list[tuple[int, str]] = []
for cid, members in comm_members.items():
    members_sorted = sorted(members, key=lambda m: degree.get(m["id"], 0), reverse=True)
    symbols = [m["label"] for m in members_sorted if not is_generic(m.get("label", ""))][:10]
    src_files = sorted({m.get("source_file", "") for m in members if m.get("source_file")})[:4]
    src_basenames = [Path(s).name for s in src_files]
    n_count = len(members)
    desc = f"#{cid} ({n_count} nodes): symbols=[{', '.join(symbols)}] files=[{', '.join(src_basenames)}]"
    comm_descs.append((cid, desc))

# Load any existing real labels (non-fallback)
labels: dict[str, str] = {}
if LABELS_OUT.exists():
    raw = json.loads(LABELS_OUT.read_text(encoding="utf-8"))
    for k, v in raw.items():
        if not v.startswith("Community "):
            labels[k] = v
print(f"Loaded {len(labels)} existing real labels")

# Find communities still needing labels
need_label = [cid for cid, _ in comm_descs if str(cid) not in labels]
print(f"Need labels: {len(need_label)}")

BATCH_SIZE = 10

def call_llm_batch(batch: list[tuple[int, str]]) -> dict[str, str]:
    """Ask the LLM to label a batch of communities, return {cid_str: label}."""
    desc_block = "\n".join(desc for _, desc in batch)
    prompt = f"""You are analyzing a multi-tenant SaaS codebase called "lastsaas" (Go backend + React/TypeScript frontend).
Below are {len(batch)} communities (tightly-coupled modules detected by graph clustering).
For each, output a JSON object mapping the community ID (as a string) to a 2-5 word descriptive name.

Rules:
- Names should be specific and descriptive (e.g. "Stripe Checkout Integration", "JWT Token Service", "OAuth GitHub Provider", "Rate Limiter Middleware", "TOTP MFA Service", "Frontend API Client")
- Use Title Case
- No quotes around the name in the JSON value, just the name as a string
- Output ONLY the JSON object, no other text

Communities:
{desc_block}

Output JSON like:
{{"0": "Frontend API Client", "1": "MongoDB Aggregations", ...}}
"""
    result = subprocess.run(
        ["z-ai", "chat", "-p", prompt],
        capture_output=True, text=True, timeout=120
    )
    if result.returncode != 0:
        raise RuntimeError(f"z-ai failed: {result.stderr[:300]}")

    out = result.stdout
    # The z-ai CLI emits its own JSON wrapper. Extract message.content from it.
    # Strategy: find the OUTER JSON object (the SDK wrapper), parse it, extract .choices[0].message.content
    # The content string may itself contain a JSON object wrapped in ```json ... ``` fences.
    try:
        # Find outermost JSON object — scan from start, find last '}'
        first_brace = out.index("{")
        last_brace = out.rindex("}")
        outer = json.loads(out[first_brace:last_brace+1])
        content = outer["choices"][0]["message"]["content"].strip()
        # Strip markdown code fences if present
        if content.startswith("```"):
            # Remove first line (```json or ```) and last line (```)
            lines = content.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            content = "\n".join(lines).strip()
        # Now content should be a JSON object string
        # If it's wrapped in extra quotes, strip them
        if content.startswith('"') and content.endswith('"'):
            content = json.loads(content)  # unwraps one level of string-quoting
        # Parse the inner JSON
        obj = json.loads(content)
        if not isinstance(obj, dict):
            raise RuntimeError(f"Inner content is not a JSON object: {type(obj)}")
        # Validate keys look like community IDs
        if all(k.lstrip('-').isdigit() for k in obj.keys()):
            return obj
        raise RuntimeError(f"Keys not all numeric: {list(obj.keys())[:5]}")
    except (json.JSONDecodeError, KeyError, IndexError) as e:
        raise RuntimeError(f"Failed to parse LLM output: {e}\nOutput:\n{out[:1500]}")


# Process in batches
for i in range(0, len(need_label), BATCH_SIZE):
    batch = [(cid, next(d for c, d in comm_descs if c == cid)) for cid in need_label[i:i+BATCH_SIZE]]
    batch_ids = [cid for cid, _ in batch]
    print(f"\nBatch {i//BATCH_SIZE + 1}: labeling communities {batch_ids[0]}..{batch_ids[-1]} ({len(batch)} communities)")

    success = False
    for attempt in range(3):
        try:
            result = call_llm_batch(batch)
            for k, v in result.items():
                # Clean up the label
                v = v.strip().strip('"').strip("'").strip()
                if len(v) > 80:
                    v = v[:80]
                labels[k] = v
            print(f"  Got {len(result)} labels")
            for k, v in result.items():
                print(f"    #{k} -> {v}")
            success = True
            break
        except Exception as e:
            print(f"  Attempt {attempt+1} FAILED: {str(e)[:200]}")
            if attempt < 2:
                time.sleep(10 * (attempt + 1))

    if not success:
        # Mark as fallback so we don't retry next run
        for cid, _ in batch:
            key = str(cid)
            if key not in labels:
                labels[key] = f"Community {cid}"

    # Save after each batch
    LABELS_OUT.write_text(json.dumps(labels, indent=2), encoding="utf-8")
    # Polite delay between batches
    time.sleep(3)

# Final save
LABELS_OUT.write_text(json.dumps(labels, indent=2), encoding="utf-8")
real_count = sum(1 for v in labels.values() if not v.startswith("Community "))
print(f"\nDone. {real_count}/{len(labels)} communities have real labels.")
print(f"Wrote {LABELS_OUT}")
