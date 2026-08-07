# Debugging Notes for graphify

This document captures gotchas and lessons learned from debugging the
graphify enrichment pipeline. It's meant to save the next person from
rediscovering these the hard way.

## Known Gotchas

### 1. `git stash` can corrupt Go file whitespace

**Symptom**: After `git stash pop`, Go files that used tabs for indentation
now use spaces. `gofmt -l .` reports every file as needing formatting.

**Cause**: The `git stash` mechanism doesn't always preserve whitespace
correctly when the stashed content and the working tree have different
line endings or indentation styles. This is especially likely when:
- The repo uses tabs but an editor/config introduces spaces
- The stash includes changes to files with mixed indentation
- A git hook (like graphify's pre-commit rebuild) touches files during
  the stash operation

**Fix**: Don't use `git stash` for temporary reverts of Go files. Instead,
use the patch-based approach:

```bash
# Save the current state as a patch
git diff -- scripts/graphify_enrich.py > /tmp/fix.patch

# Revert to HEAD
git checkout -- scripts/graphify_enrich.py

# ... do your work ...

# Restore the fix
git apply /tmp/fix.patch
```

Or even simpler: commit the fix first, then `git checkout HEAD~1 -- file`
to temporarily revert, and `git checkout HEAD -- file` to restore.

### 2. Method-receiver label mismatch (enrich_with_ssa)

**Symptom**: `filter_writes_field` edge count is suspiciously low (e.g., 8
`map_update` edges when the tracer found 68).

**Root cause**: The Go SSA tracer reports function names as
`(*AdminHandler).ListTenants`, but the tree-sitter graph stores the same
function node with label `.ListTenants()` (leading dot, no receiver type,
trailing `()`). The enrich script's lookup tried `func_name`,
`func_name + "()"`, and `func_name.lower()` — none of which matched.

**Fix**: `_normalize_go_method_name()` in `graphify_enrich.py` generates
all candidate label forms for a tracer function name, including
`.MethodName()` for method-receiver functions. The lookup uses a 3-strategy
approach: candidate labels → file-scoped index → linear scan.

**How to verify**: Run `python scripts/graphify_enrich.py . --all` and
check the `SSA lookup` stats line. It should show `miss: 0` and
`file_scoped: 0` (all functions matched via strategy 1).

### 3. Duplicate method names and over-matching

**Symptom**: Two structs with the same method name (e.g.,
`(*AdminHandler).List` and `(*TenantHandler).List`) both return the same
filter fields when queried via `get_function_filter_fields_with_confidence()`.

**Root cause**: The graph stores both method nodes with the same label
(`.List()`). When the query helper finds multiple matches, it picks the
first one without considering which receiver type the caller asked for.

**Fix**: `_find_function_node()` in `graph_query.py` extracts the receiver
type from the function name (e.g., `AdminHandler` from
`(*AdminHandler).List`) and prefers nodes whose `id` or `source_file`
contains the receiver type (case-insensitive).

**How to verify**: The test suite (`scripts/test_enrich.py`) includes a
test for `ExchangeCode` on 4 different receivers — AuthHandler should
return 9 fields (it calls MongoDB), while the OAuth service implementations
should return 0 (they don't call MongoDB directly).

### 4. Dict-collision on stable_id (verification scripts only)

**Symptom**: When diffing finding IDs between two runs, 11 findings
collapse to 8 because the stable_id omits the line number.

**Root cause**: Two findings in the same function with the same
`filter_fields` (e.g., `ListLogs` has two `Find` calls on `system_logs`
with empty filter) produce the same stable_id
(`file:function:collection:filter_fields`). A dict comprehension
`{stable_id(f): f for f in findings}` collapses them.

**Fix**: Include the line number in the stable_id:
`file:line:function:collection:filter_fields`. This is only needed in
verification/comparison scripts — the actual tools use lists
(`[asdict(f) for f in findings]`), not dicts, so they're not affected.

### 5. Graphify pre-commit hook rebuilds the graph

**Symptom**: After committing changes to Go files, `graphify-out/graph.json`
gets overwritten with a non-enriched graph.

**Cause**: The lastsaas repo has a pre-commit hook that triggers a
background graph rebuild. This rebuild runs `graphify extract` (which
produces a non-enriched graph) but NOT `graphify enrich`.

**Fix**: After any commit that touches Go files, re-run enrichment:
```bash
python scripts/graphify_enrich.py repos/lastsaas --all
cp repos/lastsaas/graphify-out/graph.json public/graph.json
```

## Standard Workflow

The supported way to regenerate the enriched graph:

```bash
# 1. Extract the base graph (tree-sitter)
cd repos/lastsaas
graphify extract .                    # produces graphify-out/graph.json

# 2. Enrich with go/types + go/ssa
python /home/z/my-project/scripts/graphify_enrich.py . --all

# 3. Sync to public/ (for the web UI)
cp graphify-out/graph.json /home/z/my-project/public/graph.json

# 4. Verify (optional but recommended)
python /home/z/my-project/scripts/test_enrich.py
python /home/z/my-project/scripts/regression_check.py
```

Do NOT use `git stash` to temporarily revert Go files — use the
patch-based approach described in gotcha #1.

## Test Suite

Run `python scripts/test_enrich.py` to verify:
- Method-receiver label matching (`(*Foo).Bar` → `.Bar()`)
- Duplicate method name disambiguation (no over-matching)
- Dict-collision not present in tool output (list, not dict)
- Embedded struct flattening (value, pointer, multi-level)
- Enrich lookup stats on the real graph (literal=1758, map_update=68, struct_type=631)
- Query helpers return correct results on real graph
