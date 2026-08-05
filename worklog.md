# Worklog

A running log of work performed in the graphify workspace. New entries are
appended at the bottom.

---

## Task ID: backend-5-6 — Interface + Middleware analyzers

**Date**: 2026-08-05
**Scope**: Build two Python analyzers for the `lastsaas` Go backend and
persist their reports to `/home/z/my-project/public/`.

### Files created

- `scripts/graphify_interfaces.py` — Go interface satisfaction checker
- `scripts/graphify_middleware.py` — Go HTTP middleware chain visualizer

### Outputs written to `public/`

- `interfaces.json` (101 KB) — full machine-readable interface/struct report
- `INTERFACES.md` (3.4 KB) — human-readable interface summary
- `middleware.json` (19 KB) — full machine-readable middleware chain report
- `MIDDLEWARE.md` (19 KB) — human-readable middleware summary

### What the interface analyzer does

1. Walks every `.go` file (excluding `*_test.go` by default) under the
   target path.
2. Parses every `type X interface { ... }` declaration — including embedded
   interfaces (same-package embeddings are flattened) and multi-line method
   signatures.
3. Parses every `type Y struct { ... }` declaration and every method bound
   to it (both value receivers `func (s Y) M()` and pointer receivers
   `func (s *Y) M()`).
4. For each interface, checks every struct's method set and decides whether
   the struct (value form `T` or pointer form `*T`) satisfies the interface.
5. Reports:
   - All interfaces with method count, file, and package
   - Which structs implement each interface, with value vs pointer receiver
   - Interfaces with 0 implementors (dead) — flagged for removal
   - Interfaces with exactly 1 implementor (over-designed candidates)
   - Top structs by method count (a structural complexity signal)
6. Emits both Markdown (`INTERFACES.md`) and JSON (`interfaces.json`).

CLI:
```
python scripts/graphify_interfaces.py [path] [--out report.md] [--json]
                                       [--include-tests]
```

### What the middleware analyzer does

1. Walks every `.go` file and detects middleware usage patterns:
   - `router.Use(...)` / `api.Use(...)` / `r.Use(...)` — gorilla/mux style
   - `middleware.Func(...)` factory calls (e.g. `middleware.RequireRole(role)`)
   - Method-style middleware: `authMiddleware.RequireAuth`, `metricsCollector.Middleware(...)`
   - Manual nesting: `handler := m1(m2(m3(finalHandler)))`
   - `http.Handler` wrapping (`c.Handler(...)`, `http.HandlerFunc(...)`)
   - `rateLimiter.RateLimitHandler(config, keyFunc, handler)` — per-route
     rate-limit pattern
2. Reconstructs execution order: outermost wrapper runs first; innermost is
   the terminal handler.
3. For each middleware definition, inspects the function body and decides:
   - **runs_before** — does work before calling `next.ServeHTTP`
   - **runs_after** — does work after `next.ServeHTTP` (or via `defer`)
   - **short_circuits** — may return without calling `next.ServeHTTP`
     (proactive request rejection). Detection uses `http.Error(...)` /
     `WriteHeader(http.StatusXXX)` calls that are NOT inside a `defer`
     block, so panic-recovery middleware like `Recovery` is correctly
     classified as *not* short-circuiting.
4. Emits a visual chain for every router, e.g.:
   ```
   Request → Recovery → BodySizeLimit → SecurityHeaders → CORS → Metrics → Router (Handler) → Response
   ```
   with ✋ markers on short-circuiting middleware.
5. Per-router stacks (combining multiple `.Use(...)` calls on the same
   router in declaration order).
6. Rate-limit site inventory — every endpoint wrapped with
   `RateLimitHandler` is listed.
7. Emits both Markdown (`MIDDLEWARE.md`) and JSON (`middleware.json`).

CLI:
```
python scripts/graphify_middleware.py [path] [--out report.md] [--json]
                                       [--include-tests]
```

### Key findings on the `lastsaas` backend

#### Interfaces
- **1 interface declared** in production code: `events.Emitter` with a
  single method `Emit(event Event)`.
- **2 implementors**: `NoopEmitter` (in-package) and `Dispatcher` (webhook
  dispatcher) — both pointer-only.
- **0 dead**, **0 single-implementor** interfaces. The `Emitter` abstraction
  is well-justified: it has two real implementations and is consumed by
  6+ handlers as a constructor parameter, making the indirection valuable
  for testing (handlers receive `NoopEmitter` in tests).
- **144 structs** scanned; the largest is `MongoDB` (40 methods), followed
  by `AuthHandler` (39) and `Service` (36, health service).

#### Middleware
- **13 middleware definitions** across 8 files.
- **38 chain sites** — places where middleware is wired onto a router or
  used to wrap a handler.
- **7 short-circuiting middleware**: `BootstrapGuard`, `RequireAuth`,
  `RequireRole`, `RequireRootTenant`, `RequireActiveBilling`,
  `RequireEntitlement`, `RequireTenant`. All use `http.Error` with an
  appropriate 4xx/5xx status to reject requests proactively.
- **6 non-short-circuiting middleware**: `Recovery`, `BodySizeLimit`,
  `SecurityHeaders`, `RequestID`, `APIVersion`, `Metrics` — these always
  call `next.ServeHTTP` and either wrap the response or augment the context.
- **Global request pipeline** (the outermost `http.Handler` in `main.go`):
  ```
  Request → Recovery → BodySizeLimit → SecurityHeaders → CORS → Metrics → Router → Response
  ```
- **Per-router stacks** are layered correctly:
  - `api` (public routes): `RequestID → APIVersion`
  - `protectedAuth`: `RequireAuth ✋`
  - `tenantAPI` / `billingAPI` / `telemetryAPI`: `RequireAuth ✋ → RequireTenant ✋`
  - `usageAPI`: `RequireAuth ✋ → RequireTenant ✋ → RequireActiveBilling ✋`
  - `adminAPI`: `RequireAuth ✋ → RequireTenant ✋ → RequireRootTenant ✋ → RequireRole ✋`
  - `adminWrite` / `adminOwner` / `tenantSettingsRouter` / `inviteRouter` /
    `removeRouter` / `ownerRouter` / `billingOwner`: `RequireRole ✋`
- **21 rate-limited endpoints** wrapped with `rateLimiter.RateLimitHandler`
  — each uses a `RateLimitConfig` constant (e.g. `LoginAttemptLimit`,
  `MFAChallengeLimit`) for per-route quota tuning.

### Implementation notes

- Both scripts follow the existing `graphify_*` conventions in
  `scripts/` (argparse with `[path]`, `--out`, `--json`; stderr for
  progress, stdout for the report when no `--out` is supplied).
- The interface parser handles single-line and multi-line interface
  bodies, embedded interfaces (same-package only — stdlib embeddings
  like `io.Reader` are noted but not flattened), and multi-line method
  signatures (re-joined before extraction).
- The middleware parser uses a two-pass approach: pass 1 collects every
  middleware definition so the manual-wrap detector can filter out
  constructor calls (`handler := NewFoo(db)`) from real middleware wraps
  (`handler := Recovery(BodySizeLimit(...))`).
- The chain unwrapper (`_unwrap_chain`) handles arbitrarily deep call
  nesting by recursively descending into single-argument calls. It
  stops at terminal handlers (bare identifiers, closures, or multi-arg
  calls).
- Short-circuit detection excludes `http.Error` calls inside `defer`
  blocks so panic-recovery middleware isn't misclassified.
- Both scripts write to `public/{interfaces,middleware}.json` and
  `public/{INTERFACES,MIDDLEWARE}.md` automatically when run without
  `--out`, matching the workspace convention.

### Next actions

- Run both analyzers as part of the graphify pipeline so the reports
  stay in sync with the repo state.
- Consider adding the analyzers to a `Makefile` target (`make analyze`)
  in the `lastsaas` backend so contributors can regenerate the reports
  locally.
- The interface analyzer is currently name-based for implementation
  matching — a future enhancement could compare full method signatures
  (parameters and return types) to catch drift between interface
  declarations and implementors.
- The middleware analyzer could be extended to render an interactive
  HTML diagram (similar to `lastsaas-callflow.html`) showing the request
  pipeline as a node graph.

---

## Task ID: backend-4 — Go error handling audit

**Date**: 2026-08-05
**Scope**: Build a Python analyzer that audits Go source code for error
handling patterns and persist its reports to `/home/z/my-project/public/`.

### Files created

- `scripts/graphify_errors.py` — Go error handling pattern auditor

### Outputs written to `public/`

- `error-audit.json` (≈ 320 KB) — full machine-readable audit report
- `ERROR_AUDIT.md` (≈ 230 KB) — human-readable audit summary

### What the analyzer does

1. Walks every `.go` file (excluding `vendor/`, `node_modules/`, `.git/`,
   `graphify-out/`, `testdata/`) under the target path. Single-file and
   directory paths are both supported.
2. For each file, masks out string literals and comments (preserving
   length and newlines) so brace/paren matching is robust against
   braces appearing inside strings or comments.
3. Locates every named top-level function and method declaration via
   regex + brace matching, building per-function `(start_line, end_line)`
   ranges so each finding can be attributed to its containing function.
4. Detects four classes of error-handling constructs:
   - **`if X != nil { ... }` blocks** — located via `IF_NIL_RE`, body
     extracted via brace matching, then classified into one of:
       - `proper_handling` (LOW) — body returns `err` (directly or via
         `fmt.Errorf("...: %w", err)` / `errors.Wrap(err, ...)`), OR
         terminates with `os.Exit(non-zero)` / `log.Fatal*` / `t.Fatal*`
         after reporting the error.
       - `panic_on_error` (MEDIUM) — body calls `panic(...)`.
       - `logged_only` (MEDIUM) — body has no `return`, but reports the
         error via `log.*` / `slog.*` / `fmt.Print*` / `respondWithError`
         / `http.Error` / `t.Error*` (i.e. error is acknowledged but not
         propagated).
       - `swallowed` (HIGH) — empty body, or body that returns without
         `err` (dropping the error info), or body that does anything else
         without propagating/reporting.
   - **Ignored errors** — `result, _ := someFunc(...)` patterns where the
     last return value is discarded with `_`. `for k, _ := range m` is
     excluded (map iteration idiom).
   - **Missing error checks** — statement-form method calls (not
     assigned, not preceded by `defer`/`go`) to a known error-returning
     method such as `Close`, `Write`, `Read`, `InsertOne`, `UpdateOne`,
     `DeleteOne`, `BulkWrite`, `Marshal`, `Unmarshal`, `Encode`, `Decode`,
     `Parse`, `Exec`, `Commit`, `Ping`, etc. The **outermost** call in a
     chain is examined (e.g. `collection.FindOne(...).Decode(&x)` is
     attributed to `Decode`, not `FindOne`). Free-function calls (no `.`
     receiver) are skipped to avoid noise from custom helpers.
   - **Panic on error** — flagged separately so non-`init()` panics can
     be reviewed (per the spec, panicking is acceptable in `init()` but
     risky elsewhere).
5. Skips lines inside `if X != nil { ... }` blocks for the missing-check
   scan so the same error site isn't double-counted.
6. For each finding, records: file (relative to project root), line,
   end_line, containing function, pattern type, severity, code snippet
   (capped at 6 lines), and a note explaining the heuristic that fired.
7. Test files (`*_test.go`) are scanned separately; only their aggregate
   statistics appear in the report (test-file findings are not included
   in the detailed findings list, per the spec).

### CLI

```
python graphify_errors.py [path] [--out report.md] [--json] [--include-tests]
```

- `path` — file or directory to audit (default: `.`).
- `--out report.md` — write markdown report to this path in addition to
  the default `public/ERROR_AUDIT.md`.
- `--json` — print the JSON report to stdout.
- `--include-tests` — reserved (test-file findings always excluded from
  the detailed list; their stats are always reported in the summary).

The script always writes `public/error-audit.json` and
`public/ERROR_AUDIT.md` (best effort) when run, matching the workspace
convention used by the other `graphify_*` analyzers.

### Key findings on the `lastsaas` backend

Audited **101 non-test Go files** (28,236 lines) plus **33 test files**
(8,982 lines). Totals across non-test code:

| Pattern | Count | Severity |
| --- | ---: | --- |
| Proper handling | 224 | LOW |
| Logged only (no return) | 373 | MEDIUM |
| Swallowed error | 133 | HIGH |
| Ignored error (`_`) | 143 | HIGH |
| Missing error check | 124 | HIGH |
| Panic on error | 1 | MEDIUM |
| **Total** | **998** | |
| % properly handled | **22.44%** | |

- **HIGH severity: 400** (swallowed + ignored + missing-check).
- **MEDIUM severity: 374** (logged-only + panic).
- **LOW severity: 224** (proper handling).

The relatively low "proper handling" percentage reflects the codebase's
HTTP-handler heavy style: most error sites use the
`if err != nil { respondWithError(w, status, msg); return }` pattern,
which is classified as `logged_only` (MEDIUM) — the error is reported to
the client via the response, but the original `err` is not propagated.
This is a defensible production pattern, but the audit treats it
strictly per the spec (only `return err` counts as "proper").

Most problematic files (top 5 by HIGH-severity count):

1. `internal/api/handlers/auth.go` — 50 problematic sites (35 swallowed,
   7 ignored, 8 missing-check)
2. `internal/api/handlers/admin.go` — 50 problematic sites (1 swallowed,
   30 ignored, 19 missing-check)
3. `internal/telemetry/service.go` — 30 problematic sites (15 swallowed,
   15 ignored)
4. `internal/testutil/testutil.go` — 26 problematic sites
5. `cmd/lastsaas/main.go` — 17 problematic sites

The single `panic_on_error` finding is in
`internal/api/handlers/helpers.go:34` (`generateRandomToken`) — panicking
on a `crypto/rand.Read` failure. This is defensible (the system is
unusable without crypto randomness) but worth flagging per the spec.

Test files (33 files, 349 error sites) are markedly better-behaved:
**59.31% properly handled**, thanks to the standard
`if err != nil { t.Fatalf("...: %v", err) }` test idiom being
recognized as `proper_handling` (test termination).

### Implementation notes

- The script is pure-Python (no `tree-sitter` dependency, unlike
  `graphify_verify.py`); it relies on a custom string/comment masker
  plus brace matching, which is sufficient for Go's relatively regular
  syntax.
- The `extract_outermost_method` helper walks a single source line,
  tracks `()` / `[]` / `{}` depth, and returns the **last** top-level
  call's method name — this correctly handles chained calls like
  `client.Database("x").Collection("y").InsertOne(ctx, doc)` by
  attributing the call to `InsertOne` (the actual error-returning call),
  not `Database` or `Collection` (which return builder types).
- Free-function calls are skipped from the missing-check scan because
  the auditor cannot infer their signatures without type information.
  This avoids false positives like `apierror.Write(w, status, ...)` —
  a void package-level helper that happens to share a name with
  `io.Writer.Write`.
- `WriteString` is deliberately **not** in the error-returning set:
  `strings.Builder.WriteString` and `bytes.Buffer.WriteString` always
  return a nil error, and including it produced 64 false positives in
  `internal/api/handlers/docs.go` alone (the OpenAPI HTML generator
  uses `sb.WriteString(...)` extensively).
- The classifier recognizes several legitimate "non-propagating but
  acceptable" patterns and treats them as `proper_handling`:
  - `os.Exit(non-zero)` after printing the error (CLI termination).
  - `log.Fatal*` (calls `os.Exit(1)` internally).
  - `t.Fatal*` (test termination — fails the test immediately).
  - `return fmt.Errorf("...: %w", err)` / `errors.Wrap(err, ...)`
    (error wrapping).
  Returning a *new* error without the original (e.g.
  `return errors.New("oops")`) is classified as `swallowed` because
  the original error info is dropped.
- The HTTP-handler pattern
  `if err != nil { respondWithError(w, status, msg); return }` is
  classified as `logged_only` (MEDIUM) rather than `swallowed` (HIGH)
  because the error IS acknowledged (it triggers the error response)
  even though the original `err` value isn't propagated. The
  `ERROR_REPORT_RE` regex covers `respondWithError`, `http.Error`,
  `writeError`, `sendError`, `c.JSON`, and similar response helpers.

### Next actions

- Run the auditor as part of the graphify pipeline so the report stays
  in sync with the repo state.
- Review the 400 HIGH-severity findings file-by-file, starting with the
  top offenders (`auth.go`, `admin.go`, `telemetry/service.go`).
- Consider tightening the 143 `ignored` findings — many are
  `result, _ := collection.Find(...).Decode(&x)` patterns where the
  decode error is intentionally discarded (often because the code path
  handles "not found" via a zero-value check). These warrant a
  `//nolint:errcheck` comment or an explicit `if err != nil` check.
- The 124 `missing_check` findings are the highest-priority review
  target — most are real `Close()` / `Decode()` / `Parse()` calls whose
  errors are silently dropped. Start with the MongoDB cursor
  `Close(ctx)` calls in `cmd/lastsaas/cmd_financial.go` and the
  `Decode` calls in `cmd/lastsaas/cmd_doctor.go`.
- A future enhancement could integrate with `errcheck` (Go's official
  error-check linter) to cross-validate the heuristic findings against
  ground-truth type information.

