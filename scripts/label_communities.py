"""Label every graphify community with a real name using z-ai LLM.

For each of the 157 communities, sends its top symbols to the LLM and asks
for a 2-4 word subsystem name (e.g. "Stripe Checkout Integration").
Writes a labels.json file that we'll then merge into graph.json, the
architecture map, and the web app's data files."""
import json
import subprocess
import time
from pathlib import Path
from collections import defaultdict, Counter

GRAPH = Path("/home/z/my-project/repos/lastsaas/graphify-out/graph.json")
LABELS_OUT = Path("/home/z/my-project/repos/lastsaas/graphify-out/community_labels.json")

data = json.loads(GRAPH.read_text(encoding="utf-8"))
nodes = data["nodes"]
edges = data["links"]

# Group nodes by community
comm_members: dict[int, list[dict]] = defaultdict(list)
for n in nodes:
    cid = n.get("community")
    if cid is None: continue
    comm_members[cid].append(n)

# Compute degree per node
degree = Counter()
for e in edges:
    degree[e["source"]] += 1
    degree[e["target"]] += 1

# For each community, gather:
#   - top 12 symbols by degree (excluding generic ones)
#   - all source files (deduped, basename only)
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

prompts: list[tuple[int, str]] = []
for cid, members in comm_members.items():
    # Sort by degree desc
    members_sorted = sorted(members, key=lambda m: degree.get(m["id"], 0), reverse=True)
    symbols = [m["label"] for m in members_sorted if not is_generic(m.get("label", ""))][:15]
    src_files = sorted({m.get("source_file", "") for m in members if m.get("source_file")})[:6]
    src_basenames = [Path(s).name for s in src_files]
    n_count = len(members)
    prompt = f"""Community #{cid} (a tightly-coupled module of {n_count} symbols from a multi-tenant SaaS codebase called lastsaas).

Top symbols (by connection count): {', '.join(symbols)}
Source files: {', '.join(src_basenames)}

Based on these symbols, what does this community implement? Reply with ONLY a 2-5 word descriptive name (no quotes, no explanation, no period at end). Examples: "Stripe Checkout Integration", "JWT Token Service", "Tenant Isolation Tests", "OAuth GitHub Provider", "Rate Limiter Middleware", "Frontend API Client", "TOTP MFA Service"."""
    prompts.append((cid, prompt))

print(f"Total communities to label: {len(prompts)}")
print(f"Estimated time: {len(prompts) * 3}s = {len(prompts) * 3 / 60:.1f} min")

# Load existing labels if present (for resume)
labels: dict[str, str] = {}
if LABELS_OUT.exists():
    labels = json.loads(LABELS_OUT.read_text(encoding="utf-8"))
    print(f"Loaded {len(labels)} existing labels (will skip)")

def call_llm(prompt: str) -> str:
    result = subprocess.run(
        ["z-ai", "chat", "-p", prompt],
        capture_output=True, text=True, timeout=60
    )
    if result.returncode != 0:
        raise RuntimeError(f"z-ai failed: {result.stderr[:200]}")
    # Parse JSON from stdout — the CLI emits JSON to stdout
    out = result.stdout
    # Find the JSON portion
    try:
        # The CLI prefixes emoji/log lines, so find the first { and parse from there
        start = out.index("{")
        data = json.loads(out[start:])
        content = data["choices"][0]["message"]["content"].strip()
        # Strip surrounding quotes if present
        content = content.strip('"').strip("'").strip()
        # Cap at 60 chars
        if len(content) > 60:
            content = content[:60]
        return content
    except (json.JSONDecodeError, KeyError, IndexError) as e:
        raise RuntimeError(f"Failed to parse z-ai output: {e}\nOutput was: {out[:500]}")

# Process in batches with progress
for i, (cid, prompt) in enumerate(prompts):
    key = str(cid)
    if key in labels:
        continue
    try:
        label = call_llm(prompt)
        labels[key] = label
        print(f"[{i+1}/{len(prompts)}] Community {cid} -> \"{label}\"")
    except Exception as e:
        print(f"[{i+1}/{len(prompts)}] Community {cid} FAILED: {e}")
        # Retry once after 10s
        try:
            time.sleep(15)
            label = call_llm(prompt)
            labels[key] = label
            print(f"  RETRY OK -> \"{label}\"")
        except Exception as e2:
            print(f"  RETRY FAILED: {e2}")
            labels[key] = f"Community {cid}"  # fallback

    # Save every 10 to allow resume
    if (i + 1) % 10 == 0:
        LABELS_OUT.write_text(json.dumps(labels, indent=2), encoding="utf-8")
        print(f"  (saved progress: {len(labels)} labels)")

# Final save
LABELS_OUT.write_text(json.dumps(labels, indent=2), encoding="utf-8")
print(f"\nDone. Wrote {len(labels)} labels to {LABELS_OUT}")
