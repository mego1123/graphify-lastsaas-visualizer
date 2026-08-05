# Context Propagation Audit

**Target:** `/home/z/my-project/repos/lastsaas`

## Summary (non-test files)

| Metric | Value |
| --- | ---: |
| Files scanned | 101 |
| Total lines | 28,969 |
| MongoDB operations scanned | **1023** |
| Proper context (ctx / r.Context() / WithTimeout) | 1022 |
| Improper context (context.Background / TODO) | **1** |
| Total findings | 1 |
| HIGH risk (in HTTP handlers) | **0** |
| LOW risk (background / CLI / goroutine) | 1 |

### Findings by risk

| Risk | Count | Meaning |
| --- | ---: | --- |
| HIGH | 0 | `context.Background()`/`TODO()` in HTTP handler — op can't be cancelled on client disconnect |
| LOW | 1 | `context.Background()`/`TODO()` in non-HTTP code (CLI, startup, goroutine) — acceptable |

### Improper-context calls by operation

| Operation | Count |
| --- | ---: |
| `FindOne` | 1 |

### Improper context expressions used

| Expression | Count |
| --- | ---: |
| `context.Background()` | 1 |

## Top Files by Improper Context Usage

| File | Operations | Proper | Improper | HIGH | LOW |
| --- | ---: | ---: | ---: | ---: | ---: |
| `backend/cmd/server/main.go` | 4 | 3 | 1 | 0 | 1 |
| `backend/cmd/lastsaas/cmd_db.go` | 2 | 2 | 0 | 0 | 0 |
| `backend/cmd/lastsaas/cmd_doctor.go` | 7 | 7 | 0 | 0 | 0 |
| `backend/cmd/lastsaas/cmd_financial.go` | 21 | 21 | 0 | 0 | 0 |
| `backend/cmd/lastsaas/cmd_health.go` | 10 | 10 | 0 | 0 | 0 |
| `backend/cmd/lastsaas/cmd_logs.go` | 6 | 6 | 0 | 0 | 0 |
| `backend/cmd/lastsaas/cmd_mcp.go` | 0 | 0 | 0 | 0 | 0 |
| `backend/cmd/lastsaas/cmd_stats.go` | 12 | 12 | 0 | 0 | 0 |
| `backend/cmd/lastsaas/cmd_tenants.go` | 21 | 21 | 0 | 0 | 0 |
| `backend/cmd/lastsaas/cmd_users.go` | 18 | 18 | 0 | 0 | 0 |
| `backend/cmd/lastsaas/main.go` | 62 | 62 | 0 | 0 | 0 |
| `backend/cmd/lastsaas/output.go` | 0 | 0 | 0 | 0 | 0 |
| `backend/cmd/lastsaas/process.go` | 0 | 0 | 0 | 0 | 0 |
| `backend/internal/api/handlers/admin.go` | 142 | 142 | 0 | 0 | 0 |
| `backend/internal/api/handlers/announcements.go` | 11 | 11 | 0 | 0 | 0 |
| `backend/internal/api/handlers/apikeys.go` | 7 | 7 | 0 | 0 | 0 |
| `backend/internal/api/handlers/auth.go` | 154 | 154 | 0 | 0 | 0 |
| `backend/internal/api/handlers/billing.go` | 37 | 37 | 0 | 0 | 0 |
| `backend/internal/api/handlers/bootstrap.go` | 4 | 4 | 0 | 0 | 0 |
| `backend/internal/api/handlers/branding.go` | 29 | 29 | 0 | 0 | 0 |
| `backend/internal/api/handlers/bundles.go` | 20 | 20 | 0 | 0 | 0 |
| `backend/internal/api/handlers/config.go` | 5 | 5 | 0 | 0 | 0 |
| `backend/internal/api/handlers/docs.go` | 0 | 0 | 0 | 0 | 0 |
| `backend/internal/api/handlers/event_definitions.go` | 32 | 32 | 0 | 0 | 0 |
| `backend/internal/api/handlers/health.go` | 1 | 1 | 0 | 0 | 0 |

## Detailed Findings

### `backend/cmd/server/main.go`

- **[LOW] FindOne** — `backend/cmd/server/main.go:801` in `main`
  - **Context used:** `context.Background()`
  - _DB operation in non-HTTP function 'main' uses context.Background(). Acceptable for CLI commands, startup code, and constructors._
  ```go
                                  if err := database.BrandingConfig().FindOne(context.Background(), bson.M{}).Decode(&bc); err == nil && bc.AppName != "" {
  ```

## Test File Context Usage (summary)

| Metric | Value |
| --- | --- |
| Test files scanned | 33 |
| Total lines | 8,984 |
| MongoDB operations scanned | 56 |
| Proper context | 47 |
| Improper context | 9 |

_Test files are scanned for completeness but their findings are not included in the detailed list — `context.Background()` in a test is appropriate (no real HTTP request to cancel)._

## Methodology

The scanner walks every `.go` file (excluding `vendor/`, `node_modules/`, `.git/`, `graphify-out/`, `testdata/`) and applies these heuristics:

1. **Function detection.** Each top-level function/method is located via brace matching on a masked source (strings/comments blanked). The function signature (the ``(...)`` parameter list) is extracted and checked for the ``http.ResponseWriter`` + ``*http.Request`` pair — if both are present, the function is classified as an HTTP handler.
2. **MongoDB operation detection.** Every call to a known mongo-driver method (``Find``, ``FindOne``, ``InsertOne``, ``UpdateOne``, ``DeleteOne``, ``Aggregate``, ``CountDocuments``, ``UpdateByID``, cursor ops like ``Close`` / ``All`` / ``Next``, session ops like ``WithTransaction``, etc.) is located via paren matching.
3. **First-arg inspection.** The first positional argument (the ``context.Context`` parameter) is extracted. It is classified as **proper** if it matches ``ctx``, ``r.Context()``, ``context.WithTimeout(ctx, ...)``, ``context.WithCancel(ctx, ...)``, ``context.WithDeadline(ctx, ...)``, ``context.WithValue(ctx, ...)``, ``sc`` (session context), or ``txnCtx``. It is **improper** if it contains ``context.Background()`` or ``context.TODO()``.
4. **Goroutine detection.** For each improper-context call, the scanner walks backward to check whether the call is inside a ``go func() { ... }()`` block. If so, the call is treated as a background operation (LOW risk) regardless of the containing function's signature.
5. **Risk classification.** ``HIGH`` for ``context.Background()`` or ``context.TODO()`` in an HTTP handler function (not in a goroutine) — the DB operation will run to completion even if the client disconnects. ``LOW`` for the same patterns in non-handler functions (CLI commands, startup code, constructors, background goroutines) where ``context.Background()`` is appropriate.

**Why this matters:** when a client cancels an HTTP request, Go's ``net/http`` package cancels the request's context. Any DB operation that receives ``r.Context()`` (or a derivative) will be cancelled, freeing the DB connection promptly. Operations that receive ``context.Background()`` are *not* cancelled — they run to completion, consuming a connection and CPU until the DB returns. In high-load scenarios, this can exhaust the connection pool.
