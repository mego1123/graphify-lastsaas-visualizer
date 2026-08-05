# Dead Code Report (Go)

**Target:** `/home/z/my-project/repos/lastsaas/backend`

Lists functions that have no references anywhere in the codebase outside their own definition. These are candidates for removal — review each finding before deleting (some may be invoked via reflection, interface dispatch, or external callers not in this repo).

## Summary

| Metric | Value |
| --- | --- |
| Functions scanned | 709 |
| Dead code findings | **21** |
| exported | 18 |
| unexported | 3 |

## Files With Most Dead Code

| File | Dead functions |
| --- | ---: |
| `internal/apierror/apierror.go` | 7 |
| `internal/db/mongodb.go` | 4 |
| `cmd/lastsaas/output.go` | 2 |
| `internal/testutil/testutil.go` | 2 |
| `internal/configstore/validate.go` | 1 |
| `internal/telemetry/service.go` | 1 |
| `internal/db/schema.go` | 1 |
| `internal/syslog/syslog.go` | 1 |
| `internal/api/handlers/bootstrap.go` | 1 |
| `internal/api/handlers/plans.go` | 1 |

## Detailed Findings

### `cmd/lastsaas/output.go`

- **[LOW] unexported function `statusClr`** — `cmd/lastsaas/output.go:72` (external_refs=0, same_file_refs=0)
  - _unexported function with no references anywhere in the codebase — safe to remove_
  ```go
  func statusClr(ok bool) string {
          if ok {
                  return clr(cGreen, "OK")
  ```
- **[LOW] unexported function `warnClr`** — `cmd/lastsaas/output.go:79` (external_refs=0, same_file_refs=0)
  - _unexported function with no references anywhere in the codebase — safe to remove_
  ```go
  func warnClr(text string) string { return clr(cYellow, text) }
  
  func printJSON(v interface{}) {
  ```

### `internal/api/handlers/bootstrap.go`

- **[LOW] exported function `IsInitialized` on `*BootstrapHandler`** — `internal/api/handlers/bootstrap.go:44` (external_refs=0, same_file_refs=4)
  - _exported function with no references outside its own file — candidate for removal (verify no reflect / interface dispatch usage)_
  ```go
  func (h *BootstrapHandler) IsInitialized() bool {
  	h.mu.RLock()
  	defer h.mu.RUnlock()
  ```

### `internal/api/handlers/plans.go`

- **[LOW] unexported function `lookupPlanForTenant` on `*PlansHandler`** — `internal/api/handlers/plans.go:814` (external_refs=0, same_file_refs=0)
  - _unexported function with no references anywhere in the codebase — safe to remove_
  ```go
  func (h *PlansHandler) lookupPlanForTenant(ctx context.Context, tenant *models.Tenant) (*models.Plan, error) {
  	var plan models.Plan
  	if tenant.PlanID != nil {
  ```

### `internal/apierror/apierror.go`

- **[LOW] exported function `BadRequest`** — `internal/apierror/apierror.go:65` (external_refs=0, same_file_refs=0)
  - _exported function with no references outside its own file — candidate for removal (verify no reflect / interface dispatch usage)_
  ```go
  func BadRequest(w http.ResponseWriter, r *http.Request, message string) {
          Write(w, http.StatusBadRequest, CodeBadRequest, message, r)
  }
  ```
- **[LOW] exported function `Unauthorized`** — `internal/apierror/apierror.go:70` (external_refs=0, same_file_refs=0)
  - _exported function with no references outside its own file — candidate for removal (verify no reflect / interface dispatch usage)_
  ```go
  func Unauthorized(w http.ResponseWriter, r *http.Request, message string) {
          Write(w, http.StatusUnauthorized, CodeUnauthorized, message, r)
  }
  ```
- **[LOW] exported function `Forbidden`** — `internal/apierror/apierror.go:75` (external_refs=0, same_file_refs=0)
  - _exported function with no references outside its own file — candidate for removal (verify no reflect / interface dispatch usage)_
  ```go
  func Forbidden(w http.ResponseWriter, r *http.Request, message string) {
          Write(w, http.StatusForbidden, CodeForbidden, message, r)
  }
  ```
- **[LOW] exported function `Conflict`** — `internal/apierror/apierror.go:85` (external_refs=0, same_file_refs=0)
  - _exported function with no references outside its own file — candidate for removal (verify no reflect / interface dispatch usage)_
  ```go
  func Conflict(w http.ResponseWriter, r *http.Request, message string) {
          Write(w, http.StatusConflict, CodeConflict, message, r)
  }
  ```
- **[LOW] exported function `Validation`** — `internal/apierror/apierror.go:90` (external_refs=0, same_file_refs=0)
  - _exported function with no references outside its own file — candidate for removal (verify no reflect / interface dispatch usage)_
  ```go
  func Validation(w http.ResponseWriter, r *http.Request, message string) {
          Write(w, http.StatusBadRequest, CodeValidation, message, r)
  }
  ```
- **[LOW] exported function `Internal`** — `internal/apierror/apierror.go:95` (external_refs=0, same_file_refs=0)
  - _exported function with no references outside its own file — candidate for removal (verify no reflect / interface dispatch usage)_
  ```go
  func Internal(w http.ResponseWriter, r *http.Request, message string) {
          Write(w, http.StatusInternalServerError, CodeInternal, message, r)
  }
  ```
- **[LOW] exported function `RateLimited`** — `internal/apierror/apierror.go:100` (external_refs=0, same_file_refs=0)
  - _exported function with no references outside its own file — candidate for removal (verify no reflect / interface dispatch usage)_
  ```go
  func RateLimited(w http.ResponseWriter, r *http.Request, message string) {
          Write(w, http.StatusTooManyRequests, CodeRateLimited, message, r)
  }
  ```

### `internal/configstore/validate.go`

- **[LOW] exported function `ValidateEnumValue`** — `internal/configstore/validate.go:51` (external_refs=0, same_file_refs=1)
  - _exported function with no references outside its own file — candidate for removal (verify no reflect / interface dispatch usage)_
  ```go
  func ValidateEnumValue(value, optionsJSON string) error {
  	if optionsJSON == "" {
  		return fmt.Errorf("enum type requires options")
  ```

### `internal/db/mongodb.go`

- **[LOW] exported function `AuditLog` on `*MongoDB`** — `internal/db/mongodb.go:369` (external_refs=0, same_file_refs=0)
  - _exported function with no references outside its own file — candidate for removal (verify no reflect / interface dispatch usage)_
  ```go
  func (m *MongoDB) AuditLog() *mongo.Collection {
  	return m.Database.Collection("audit_log")
  }
  ```
- **[LOW] exported function `WebAuthnCredentials` on `*MongoDB`** — `internal/db/mongodb.go:449` (external_refs=0, same_file_refs=0)
  - _exported function with no references outside its own file — candidate for removal (verify no reflect / interface dispatch usage)_
  ```go
  func (m *MongoDB) WebAuthnCredentials() *mongo.Collection {
  	return m.Database.Collection("webauthn_credentials")
  }
  ```
- **[LOW] exported function `WebAuthnSessions` on `*MongoDB`** — `internal/db/mongodb.go:453` (external_refs=0, same_file_refs=0)
  - _exported function with no references outside its own file — candidate for removal (verify no reflect / interface dispatch usage)_
  ```go
  func (m *MongoDB) WebAuthnSessions() *mongo.Collection {
  	return m.Database.Collection("webauthn_sessions")
  }
  ```
- **[LOW] exported function `SSOConnections` on `*MongoDB`** — `internal/db/mongodb.go:457` (external_refs=0, same_file_refs=0)
  - _exported function with no references outside its own file — candidate for removal (verify no reflect / interface dispatch usage)_
  ```go
  func (m *MongoDB) SSOConnections() *mongo.Collection {
  	return m.Database.Collection("sso_connections")
  }
  ```

### `internal/db/schema.go`

- **[LOW] exported function `AllSchemas`** — `internal/db/schema.go:18` (external_refs=0, same_file_refs=1)
  - _exported function with no references outside its own file — candidate for removal (verify no reflect / interface dispatch usage)_
  ```go
  func AllSchemas() []CollectionSchema {
  	return []CollectionSchema{
  		usersSchema(),
  ```

### `internal/syslog/syslog.go`

- **[LOW] exported function `CriticalWithUser` on `*Logger`** — `internal/syslog/syslog.go:206` (external_refs=0, same_file_refs=0)
  - _exported function with no references outside its own file — candidate for removal (verify no reflect / interface dispatch usage)_
  ```go
  func (l *Logger) CriticalWithUser(ctx context.Context, message string, userID primitive.ObjectID) {
  	l.log(ctx, models.LogCritical, message, &userID)
  }
  ```

### `internal/telemetry/service.go`

- **[LOW] exported function `TrackPageView` on `*Service`** — `internal/telemetry/service.go:196` (external_refs=0, same_file_refs=0)
  - _exported function with no references outside its own file — candidate for removal (verify no reflect / interface dispatch usage)_
  ```go
  func (s *Service) TrackPageView(ctx context.Context, sessionID, page string, userID *primitive.ObjectID) error {
          return s.Track(ctx, models.TelemetryEvent{
                  EventName:  models.TelemetryPageView,
  ```

### `internal/testutil/testutil.go`

- **[LOW] exported function `SetConfigDir`** — `internal/testutil/testutil.go:185` (external_refs=0, same_file_refs=2)
  - _exported function with no references outside its own file — candidate for removal (verify no reflect / interface dispatch usage)_
  ```go
  func SetConfigDir(t *testing.T) {
          t.Helper()
          findAndSetConfigDir()
  ```
- **[LOW] exported function `ParseJSON`** — `internal/testutil/testutil.go:360` (external_refs=0, same_file_refs=0)
  - _exported function with no references outside its own file — candidate for removal (verify no reflect / interface dispatch usage)_
  ```go
  func ParseJSON(t *testing.T, resp *http.Response, target interface{}) {
          t.Helper()
          defer resp.Body.Close()
  ```

## Methodology

1. Every `.go` file under the target path is scanned for `func [recv] Name(...)` declarations. Each declaration's body extent is found via brace matching (strings and comments are masked out first).
2. Special-cased exclusions: `main`, `init`, `Test*`, `Benchmark*`, `Fuzz*`, `Example*` (Go entry points), well-known interface-satisfying methods (`String`, `Error`, `MarshalJSON`, `ServeHTTP`, `Len`/`Less`/`Swap`, `Read`/`Write`/`Close`, etc.) which may be invoked via interface dispatch, and stub functions whose body is just `panic("not implemented")` / `panic("TODO")`.
3. For every remaining function, the codebase is searched for whole-word references to the function name across ALL `.go` files (including `*_test.go` — tests are legitimate external callers).
4. **Unexported function** (lowercase): reported as dead if it has zero references anywhere outside its own definition line.
5. **Exported function** (capitalised): reported as dead if no OTHER file references it. Same-file references don't count because removing the function would also remove those callers — they're part of the same dead subtree.
6. Each finding is verified by counting references; the `external_refs` and `same_file_refs` fields record the count so the reviewer can confirm there are genuinely no callers.
7. Severity is **LOW** for every finding — dead code is safe to remove but not urgent.

### Caveats

- Name-based analysis: if two functions in different packages share a name, the second one's references count for the first. This can mask a dead function. Review each finding before deletion.
- Functions invoked only via reflection (e.g. `reflect.ValueOf(x).MethodByName("Foo")`) will appear dead. The well-known-method exclusion list mitigates the common cases.
- Functions whose only caller is in `*_test.go` are reported as dead for unexported functions (the test should be removed too). For exported functions, test-file references count as external use and the function is NOT reported as dead.

---
_Generated by `graphify dead-code`._