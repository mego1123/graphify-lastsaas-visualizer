# Interface Satisfaction Report

Repository: `/home/z/my-project/repos/lastsaas/backend`

- **Interfaces scanned**: 1
- **Structs scanned**: 144
- **Interface methods total**: 1

## Summary — Interfaces

| Interface | Package | Methods | Implementors | Pointer-only | Status |
|-----------|---------|---------|--------------|--------------|--------|
| `Emitter` | `events` | 1 | 0 | 2 | ✅ healthy |

## Per-Interface Detail

### `Emitter`

- **File**: `internal/events/emitter.go`
- **Package**: `events`
- **Method count**: 1

| Method | Signature |
|--------|-----------|
| `Emit` | `Emit(event Event)` |

#### Implementors

| Struct | Receiver | File |
|--------|----------|------|
| `Dispatcher` | pointer (`*T`) | `internal/webhooks/dispatcher.go` |
| `NoopEmitter` | pointer (`*T`) | `internal/events/emitter.go` |

## Dead Interfaces (0 implementors)

_None — every declared interface has at least one implementor._

## Single-Implementor Interfaces (may be over-designed)

_None._

## Top Structs by Method Count

| Struct | File | Methods (value) | Methods (pointer) | Total |
|--------|------|------------------|--------------------|-------|
| `MongoDB` | `internal/db/mongodb.go` | 0 | 40 | 40 |
| `AuthHandler` | `internal/api/handlers/auth.go` | 0 | 39 | 39 |
| `Service` | `internal/health/health.go` | 0 | 36 | 36 |
| `AdminHandler` | `internal/api/handlers/admin.go` | 0 | 24 | 24 |
| `BrandingHandler` | `internal/api/handlers/branding.go` | 0 | 16 | 16 |
| `Logger` | `internal/syslog/syslog.go` | 0 | 13 | 13 |
| `BillingHandler` | `internal/api/handlers/billing.go` | 0 | 12 | 12 |
| `PlansHandler` | `internal/api/handlers/plans.go` | 0 | 10 | 10 |
| `JWTService` | `internal/auth/jwt.go` | 0 | 10 | 10 |
| `TenantHandler` | `internal/api/handlers/tenant.go` | 0 | 8 | 8 |
| `WebhooksHandler` | `internal/api/handlers/webhooks.go` | 0 | 8 | 8 |
| `TOTPService` | `internal/auth/totp.go` | 0 | 7 | 7 |
| `Store` | `internal/configstore/store.go` | 0 | 7 | 7 |
| `Client` | `internal/datadog/client.go` | 0 | 7 | 7 |
| `HealthHandler` | `internal/api/handlers/health.go` | 0 | 6 | 6 |
| `PMHandler` | `internal/api/handlers/pm.go` | 0 | 6 | 6 |
| `AnnouncementsHandler` | `internal/api/handlers/announcements.go` | 0 | 5 | 5 |
| `BundlesHandler` | `internal/api/handlers/bundles.go` | 0 | 5 | 5 |
| `ConfigHandler` | `internal/api/handlers/config.go` | 0 | 5 | 5 |
| `EventDefinitionsHandler` | `internal/api/handlers/event_definitions.go` | 0 | 5 | 5 |
| `PromotionsHandler` | `internal/api/handlers/promotions.go` | 0 | 5 | 5 |
| `ResendService` | `internal/email/resend.go` | 0 | 5 | 5 |
| `PasswordService` | `internal/auth/password.go` | 0 | 4 | 4 |
| `Dispatcher` | `internal/webhooks/dispatcher.go` | 0 | 4 | 4 |
| `APIKeysHandler` | `internal/api/handlers/apikeys.go` | 0 | 3 | 3 |

## Notes

- Go interfaces are satisfied *implicitly* — there is no `implements` keyword. This tool inspects every struct's method set and checks whether it is a superset of each interface's required methods.
- Pointer-receiver methods are only available on `*T`, so a struct that satisfies an interface purely through pointer methods is listed as a *pointer-only* implementor.
- Cross-package interface embeddings (e.g. `io.Reader`) cannot be resolved by static scan — those methods are not counted.
- Test files (`*_test.go`) are excluded by default to keep the report focused on production code.
