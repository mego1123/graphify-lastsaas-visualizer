# Middleware Chain Report

Repository: `/home/z/my-project/repos/lastsaas/backend`

- **Middleware definitions**: 13
- **Chain sites**: 38
- **Short-circuiting**: 7 / 13
- **Run before handler**: 13 / 13
- **Run after handler**: 12 / 13

## Middleware Definitions

| Name | File | Method? | Factory? | Before | After | Short-circuits | Description |
|------|------|---------|----------|--------|-------|----------------|-------------|
| `BootstrapGuard` | `internal/api/handlers/bootstrap.go:75` | `BootstrapHandler` | — | ✓ | ✓ | ✋ yes | BootstrapGuard — BootstrapGuard returns middleware that blocks non-bootstrap routes when system is not initialized |
| `APIVersion` | `internal/middleware/apiversion.go:10` | — | — | ✓ | ✓ | — | APIVersion — APIVersion sets the X-API-Version response header on all API responses |
| `RequireAuth` | `internal/middleware/auth.go:40` | `AuthMiddleware` | — | ✓ | — | ✋ yes | RequireAuth — validates JWT or API key, blocks anonymous requests |
| `BodySizeLimit` | `internal/middleware/bodylimit.go:7` | — | — | ✓ | ✓ | — | BodySizeLimit — limits request body size to 1MB |
| `Middleware` | `internal/middleware/metrics.go:93` | `MetricsCollector` | — | ✓ | ✓ | — | Middleware — Middleware returns an http |
| `RequireRole` | `internal/middleware/rbac.go:9` | — | ✓ | ✓ | ✓ | ✋ yes | RequireRole — blocks requests below a minimum tenant role |
| `RequireRootTenant` | `internal/middleware/rbac.go:26` | — | ✓ | ✓ | ✓ | ✋ yes | RequireRootTenant — blocks requests to non-root tenants |
| `Recovery` | `internal/middleware/recovery.go:11` | — | — | ✓ | ✓ | — | Recovery — Recovery returns middleware that recovers from panics in HTTP handlers, logs the stack trace, and returns a 500 response instead of crashing the process |
| `RequestID` | `internal/middleware/requestid.go:15` | — | — | ✓ | ✓ | — | RequestID — RequestID generates a unique ID for each request, sets it as a response header, and stores it in the request context for downstream logging |
| `SecurityHeaders` | `internal/middleware/security.go:8` | — | — | ✓ | ✓ | — | SecurityHeaders — sets CSP, HSTS, X-Frame-Options and related headers |
| `RequireActiveBilling` | `internal/middleware/tenant.go:92` | — | ✓ | ✓ | ✓ | ✋ yes | RequireActiveBilling — RequireActiveBilling returns middleware that blocks requests when the tenant's billing status is not active (and not waived/root) |
| `RequireEntitlement` | `internal/middleware/tenant.go:120` | — | ✓ | ✓ | ✓ | ✋ yes | RequireEntitlement — RequireEntitlement returns middleware that checks whether the tenant's plan grants a specific boolean entitlement |
| `RequireTenant` | `internal/middleware/tenant.go:28` | `TenantMiddleware` | — | ✓ | ✓ | ✋ yes | RequireTenant — resolves X-Tenant-ID and loads tenant membership |

## Chain Sites

### `api` — `cmd/server/main.go:393` (use)

```go
api.Use(middleware.RequestID) ; api.Use(middleware.APIVersion)
```

**Execution order** (outer → inner):

1. `RequestID` — _wraps (before+after)_
2. `APIVersion` — _wraps (before+after)_

**Visual chain:**

```
Request → RequestID → APIVersion → Response
```

### `guarded` — `cmd/server/main.go:420` (use)

```go
guarded.Use(bootstrapHandler.BootstrapGuard)
```

**Execution order** (outer → inner):

1. `BootstrapGuard` — _✋ short-circuits; wraps (before+after)_

**Visual chain:**

```
Request → BootstrapGuard ✋ → Response
```

### `(ratelimit)` — `cmd/server/main.go:423` (ratelimit)

```go
rateLimiter.RateLimitHandler(
```

**Execution order** (outer → inner):

1. `RateLimitHandler`

**Visual chain:**

```
Request → RateLimit (Handler) → Response
```

### `(ratelimit)` — `cmd/server/main.go:429` (ratelimit)

```go
rateLimiter.RateLimitHandler(
```

**Execution order** (outer → inner):

1. `RateLimitHandler`

**Visual chain:**

```
Request → RateLimit (Handler) → Response
```

### `(ratelimit)` — `cmd/server/main.go:435` (ratelimit)

```go
rateLimiter.RateLimitHandler(
```

**Execution order** (outer → inner):

1. `RateLimitHandler`

**Visual chain:**

```
Request → RateLimit (Handler) → Response
```

### `(ratelimit)` — `cmd/server/main.go:441` (ratelimit)

```go
rateLimiter.RateLimitHandler(
```

**Execution order** (outer → inner):

1. `RateLimitHandler`

**Visual chain:**

```
Request → RateLimit (Handler) → Response
```

### `(ratelimit)` — `cmd/server/main.go:447` (ratelimit)

```go
rateLimiter.RateLimitHandler(
```

**Execution order** (outer → inner):

1. `RateLimitHandler`

**Visual chain:**

```
Request → RateLimit (Handler) → Response
```

### `(ratelimit)` — `cmd/server/main.go:453` (ratelimit)

```go
rateLimiter.RateLimitHandler(
```

**Execution order** (outer → inner):

1. `RateLimitHandler`

**Visual chain:**

```
Request → RateLimit (Handler) → Response
```

### `(ratelimit)` — `cmd/server/main.go:459` (ratelimit)

```go
rateLimiter.RateLimitHandler(
```

**Execution order** (outer → inner):

1. `RateLimitHandler`

**Visual chain:**

```
Request → RateLimit (Handler) → Response
```

### `(ratelimit)` — `cmd/server/main.go:472` (ratelimit)

```go
rateLimiter.RateLimitHandler(
```

**Execution order** (outer → inner):

1. `RateLimitHandler`

**Visual chain:**

```
Request → RateLimit (Handler) → Response
```

### `(ratelimit)` — `cmd/server/main.go:479` (ratelimit)

```go
rateLimiter.RateLimitHandler(
```

**Execution order** (outer → inner):

1. `RateLimitHandler`

**Visual chain:**

```
Request → RateLimit (Handler) → Response
```

### `(ratelimit)` — `cmd/server/main.go:484` (ratelimit)

```go
rateLimiter.RateLimitHandler(
```

**Execution order** (outer → inner):

1. `RateLimitHandler`

**Visual chain:**

```
Request → RateLimit (Handler) → Response
```

### `(ratelimit)` — `cmd/server/main.go:492` (ratelimit)

```go
rateLimiter.RateLimitHandler(
```

**Execution order** (outer → inner):

1. `RateLimitHandler`

**Visual chain:**

```
Request → RateLimit (Handler) → Response
```

### `(ratelimit)` — `cmd/server/main.go:502` (ratelimit)

```go
rateLimiter.RateLimitHandler(
```

**Execution order** (outer → inner):

1. `RateLimitHandler`

**Visual chain:**

```
Request → RateLimit (Handler) → Response
```

### `(ratelimit)` — `cmd/server/main.go:512` (ratelimit)

```go
rateLimiter.RateLimitHandler(
```

**Execution order** (outer → inner):

1. `RateLimitHandler`

**Visual chain:**

```
Request → RateLimit (Handler) → Response
```

### `protectedAuth` — `cmd/server/main.go:522` (use)

```go
protectedAuth.Use(authMiddleware.RequireAuth)
```

**Execution order** (outer → inner):

1. `RequireAuth` — _✋ short-circuits; runs before handler_

**Visual chain:**

```
Request → RequireAuth ✋ → Response
```

### `tenantAPI` — `cmd/server/main.go:541` (use)

```go
tenantAPI.Use(authMiddleware.RequireAuth) ; tenantAPI.Use(tenantMiddleware.RequireTenant)
```

**Execution order** (outer → inner):

1. `RequireAuth` — _✋ short-circuits; runs before handler_
2. `RequireTenant` — _✋ short-circuits; wraps (before+after)_

**Visual chain:**

```
Request → RequireAuth ✋ → RequireTenant ✋ → Response
```

### `tenantSettingsRouter` — `cmd/server/main.go:549` (use)

```go
tenantSettingsRouter.Use(middleware.RequireRole(models.RoleOwner))
```

**Execution order** (outer → inner):

1. `RequireRole` — _✋ short-circuits; wraps (before+after)_

**Visual chain:**

```
Request → RequireRole ✋ → Response
```

### `inviteRouter` — `cmd/server/main.go:554` (use)

```go
inviteRouter.Use(middleware.RequireRole(models.RoleAdmin))
```

**Execution order** (outer → inner):

1. `RequireRole` — _✋ short-circuits; wraps (before+after)_

**Visual chain:**

```
Request → RequireRole ✋ → Response
```

### `(ratelimit)` — `cmd/server/main.go:555` (ratelimit)

```go
rateLimiter.RateLimitHandler(
```

**Execution order** (outer → inner):

1. `RateLimitHandler`

**Visual chain:**

```
Request → RateLimit (Handler) → Response
```

### `removeRouter` — `cmd/server/main.go:563` (use)

```go
removeRouter.Use(middleware.RequireRole(models.RoleAdmin))
```

**Execution order** (outer → inner):

1. `RequireRole` — _✋ short-circuits; wraps (before+after)_

**Visual chain:**

```
Request → RequireRole ✋ → Response
```

### `ownerRouter` — `cmd/server/main.go:568` (use)

```go
ownerRouter.Use(middleware.RequireRole(models.RoleOwner))
```

**Execution order** (outer → inner):

1. `RequireRole` — _✋ short-circuits; wraps (before+after)_

**Visual chain:**

```
Request → RequireRole ✋ → Response
```

### `messageAPI` — `cmd/server/main.go:574` (use)

```go
messageAPI.Use(authMiddleware.RequireAuth)
```

**Execution order** (outer → inner):

1. `RequireAuth` — _✋ short-circuits; runs before handler_

**Visual chain:**

```
Request → RequireAuth ✋ → Response
```

### `usageAPI` — `cmd/server/main.go:590` (use)

```go
usageAPI.Use(authMiddleware.RequireAuth) ; usageAPI.Use(tenantMiddleware.RequireTenant) ; usageAPI.Use(middleware.RequireActiveBilling())
```

**Execution order** (outer → inner):

1. `RequireAuth` — _✋ short-circuits; runs before handler_
2. `RequireTenant` — _✋ short-circuits; wraps (before+after)_
3. `RequireActiveBilling` — _✋ short-circuits; wraps (before+after)_

**Visual chain:**

```
Request → RequireAuth ✋ → RequireTenant ✋ → RequireActiveBilling ✋ → Response
```

### `(ratelimit)` — `cmd/server/main.go:593` (ratelimit)

```go
rateLimiter.RateLimitHandler(
```

**Execution order** (outer → inner):

1. `RateLimitHandler`

**Visual chain:**

```
Request → RateLimit (Handler) → Response
```

### `(ratelimit)` — `cmd/server/main.go:601` (ratelimit)

```go
rateLimiter.RateLimitHandler(
```

**Execution order** (outer → inner):

1. `RateLimitHandler`

**Visual chain:**

```
Request → RateLimit (Handler) → Response
```

### `telemetryAPI` — `cmd/server/main.go:609` (use)

```go
telemetryAPI.Use(authMiddleware.RequireAuth) ; telemetryAPI.Use(tenantMiddleware.RequireTenant)
```

**Execution order** (outer → inner):

1. `RequireAuth` — _✋ short-circuits; runs before handler_
2. `RequireTenant` — _✋ short-circuits; wraps (before+after)_

**Visual chain:**

```
Request → RequireAuth ✋ → RequireTenant ✋ → Response
```

### `(ratelimit)` — `cmd/server/main.go:611` (ratelimit)

```go
rateLimiter.RateLimitHandler(
```

**Execution order** (outer → inner):

1. `RateLimitHandler`

**Visual chain:**

```
Request → RateLimit (Handler) → Response
```

### `(ratelimit)` — `cmd/server/main.go:622` (ratelimit)

```go
rateLimiter.RateLimitHandler(
```

**Execution order** (outer → inner):

1. `RateLimitHandler`

**Visual chain:**

```
Request → RateLimit (Handler) → Response
```

### `billingAPI` — `cmd/server/main.go:639` (use)

```go
billingAPI.Use(authMiddleware.RequireAuth) ; billingAPI.Use(tenantMiddleware.RequireTenant)
```

**Execution order** (outer → inner):

1. `RequireAuth` — _✋ short-circuits; runs before handler_
2. `RequireTenant` — _✋ short-circuits; wraps (before+after)_

**Visual chain:**

```
Request → RequireAuth ✋ → RequireTenant ✋ → Response
```

### `billingOwner` — `cmd/server/main.go:648` (use)

```go
billingOwner.Use(middleware.RequireRole(models.RoleOwner))
```

**Execution order** (outer → inner):

1. `RequireRole` — _✋ short-circuits; wraps (before+after)_

**Visual chain:**

```
Request → RequireRole ✋ → Response
```

### `adminAPI` — `cmd/server/main.go:658` (use)

```go
adminAPI.Use(authMiddleware.RequireAuth) ; adminAPI.Use(tenantMiddleware.RequireTenant) ; adminAPI.Use(middleware.RequireRootTenant()) ; adminAPI.Use(middleware.RequireRole(models.RoleUser))
```

**Execution order** (outer → inner):

1. `RequireAuth` — _✋ short-circuits; runs before handler_
2. `RequireTenant` — _✋ short-circuits; wraps (before+after)_
3. `RequireRootTenant` — _✋ short-circuits; wraps (before+after)_
4. `RequireRole` — _✋ short-circuits; wraps (before+after)_

**Visual chain:**

```
Request → RequireAuth ✋ → RequireTenant ✋ → RequireRootTenant ✋ → RequireRole ✋ → Response
```

### `(ratelimit)` — `cmd/server/main.go:668` (ratelimit)

```go
rateLimiter.RateLimitHandler(
```

**Execution order** (outer → inner):

1. `RateLimitHandler`

**Visual chain:**

```
Request → RateLimit (Handler) → Response
```

### `(ratelimit)` — `cmd/server/main.go:676` (ratelimit)

```go
rateLimiter.RateLimitHandler(
```

**Execution order** (outer → inner):

1. `RateLimitHandler`

**Visual chain:**

```
Request → RateLimit (Handler) → Response
```

### `(ratelimit)` — `cmd/server/main.go:699` (ratelimit)

```go
rateLimiter.RateLimitHandler(
```

**Execution order** (outer → inner):

1. `RateLimitHandler`

**Visual chain:**

```
Request → RateLimit (Handler) → Response
```

### `adminWrite` — `cmd/server/main.go:721` (use)

```go
adminWrite.Use(middleware.RequireRole(models.RoleAdmin))
```

**Execution order** (outer → inner):

1. `RequireRole` — _✋ short-circuits; wraps (before+after)_

**Visual chain:**

```
Request → RequireRole ✋ → Response
```

### `adminOwner` — `cmd/server/main.go:761` (use)

```go
adminOwner.Use(middleware.RequireRole(models.RoleOwner))
```

**Execution order** (outer → inner):

1. `RequireRole` — _✋ short-circuits; wraps (before+after)_

**Visual chain:**

```
Request → RequireRole ✋ → Response
```

### `(global)` — `cmd/server/main.go:806` (manual-wrap)

```go
handler := middleware.Recovery(middleware.BodySizeLimit(middleware.SecurityHeaders(c.Handler(metricsCollector.Middleware(router)))))
```

**Execution order** (outer → inner):

1. `Recovery` — _wraps (before+after)_
2. `BodySizeLimit` — _wraps (before+after)_
3. `SecurityHeaders` — _wraps (before+after)_
4. `Handler`
5. `Middleware` — _wraps (before+after)_
6. `router`

**Visual chain:**

```
Request → Recovery → BodySizeLimit → SecurityHeaders → CORS → Metrics → Router (Handler) → Response
```

## Global Handler Chain

The outermost HTTP handler in `main.go` wraps the router with cross-cutting middleware. This is the request pipeline every API call traverses, in order:

```
Request → Recovery → BodySizeLimit → SecurityHeaders → CORS → Metrics → Router (Handler) → Response
```

## Per-Router Middleware Stacks

### `adminAPI`

Applied at 1 site(s); merged middleware order:

```
Request → RequireAuth ✋ → RequireTenant ✋ → RequireRootTenant ✋ → RequireRole ✋ → Response
```

### `adminOwner`

Applied at 1 site(s); merged middleware order:

```
Request → RequireRole ✋ → Response
```

### `adminWrite`

Applied at 1 site(s); merged middleware order:

```
Request → RequireRole ✋ → Response
```

### `api`

Applied at 1 site(s); merged middleware order:

```
Request → RequestID → APIVersion → Response
```

### `billingAPI`

Applied at 1 site(s); merged middleware order:

```
Request → RequireAuth ✋ → RequireTenant ✋ → Response
```

### `billingOwner`

Applied at 1 site(s); merged middleware order:

```
Request → RequireRole ✋ → Response
```

### `guarded`

Applied at 1 site(s); merged middleware order:

```
Request → BootstrapGuard ✋ → Response
```

### `inviteRouter`

Applied at 1 site(s); merged middleware order:

```
Request → RequireRole ✋ → Response
```

### `messageAPI`

Applied at 1 site(s); merged middleware order:

```
Request → RequireAuth ✋ → Response
```

### `ownerRouter`

Applied at 1 site(s); merged middleware order:

```
Request → RequireRole ✋ → Response
```

### `protectedAuth`

Applied at 1 site(s); merged middleware order:

```
Request → RequireAuth ✋ → Response
```

### `removeRouter`

Applied at 1 site(s); merged middleware order:

```
Request → RequireRole ✋ → Response
```

### `telemetryAPI`

Applied at 1 site(s); merged middleware order:

```
Request → RequireAuth ✋ → RequireTenant ✋ → Response
```

### `tenantAPI`

Applied at 1 site(s); merged middleware order:

```
Request → RequireAuth ✋ → RequireTenant ✋ → Response
```

### `tenantSettingsRouter`

Applied at 1 site(s); merged middleware order:

```
Request → RequireRole ✋ → Response
```

### `usageAPI`

Applied at 1 site(s); merged middleware order:

```
Request → RequireAuth ✋ → RequireTenant ✋ → RequireActiveBilling ✋ → Response
```

## Rate-Limited Endpoints

These endpoints are wrapped with `RateLimitHandler` — requests exceeding the configured quota are rejected with HTTP 429 before the handler runs.

| File | Line | Call |
|------|------|------|
| `cmd/server/main.go` | 423 | `rateLimiter.RateLimitHandler(` |
| `cmd/server/main.go` | 429 | `rateLimiter.RateLimitHandler(` |
| `cmd/server/main.go` | 435 | `rateLimiter.RateLimitHandler(` |
| `cmd/server/main.go` | 441 | `rateLimiter.RateLimitHandler(` |
| `cmd/server/main.go` | 447 | `rateLimiter.RateLimitHandler(` |
| `cmd/server/main.go` | 453 | `rateLimiter.RateLimitHandler(` |
| `cmd/server/main.go` | 459 | `rateLimiter.RateLimitHandler(` |
| `cmd/server/main.go` | 472 | `rateLimiter.RateLimitHandler(` |
| `cmd/server/main.go` | 479 | `rateLimiter.RateLimitHandler(` |
| `cmd/server/main.go` | 484 | `rateLimiter.RateLimitHandler(` |
| `cmd/server/main.go` | 492 | `rateLimiter.RateLimitHandler(` |
| `cmd/server/main.go` | 502 | `rateLimiter.RateLimitHandler(` |
| `cmd/server/main.go` | 512 | `rateLimiter.RateLimitHandler(` |
| `cmd/server/main.go` | 555 | `rateLimiter.RateLimitHandler(` |
| `cmd/server/main.go` | 593 | `rateLimiter.RateLimitHandler(` |
| `cmd/server/main.go` | 601 | `rateLimiter.RateLimitHandler(` |
| `cmd/server/main.go` | 611 | `rateLimiter.RateLimitHandler(` |
| `cmd/server/main.go` | 622 | `rateLimiter.RateLimitHandler(` |
| `cmd/server/main.go` | 668 | `rateLimiter.RateLimitHandler(` |
| `cmd/server/main.go` | 676 | `rateLimiter.RateLimitHandler(` |
| `cmd/server/main.go` | 699 | `rateLimiter.RateLimitHandler(` |

## Recommendations

- ✋ **7 middleware short-circuit.** Make sure logs / metrics are emitted *before* the short-circuit so rejected requests are still observable. Short-circuiting middleware:
    - `BootstrapGuard` (`internal/api/handlers/bootstrap.go:75`)
    - `RequireAuth` (`internal/middleware/auth.go:40`)
    - `RequireRole` (`internal/middleware/rbac.go:9`)
    - `RequireRootTenant` (`internal/middleware/rbac.go:26`)
    - `RequireTenant` (`internal/middleware/tenant.go:28`)
    - `RequireActiveBilling` (`internal/middleware/tenant.go:92`)
    - `RequireEntitlement` (`internal/middleware/tenant.go:120`)

- Run `go vet ./...` and consider `go tool pprof` to validate that the middleware stack isn't a hotspot under load.
