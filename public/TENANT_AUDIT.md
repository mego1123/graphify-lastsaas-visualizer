# Tenant Isolation Audit

MongoDB query audit for **cross-tenant data leakage** risks. The auditor flags queries on tenant-scoped collections that lack a `tenantId` filter — but first applies a series of context-aware heuristics to suppress known false positives (global-by-design collections, admin handlers, background tasks, public endpoints, user-scoped filters, globally-unique keys, and CLI tools).

Repo: `/home/z/my-project/repos/lastsaas`

## Summary

| Metric | Value |
|--------|-------|
| Total MongoDB queries | **544** |
| Queries with `tenantId` filter | **77** (14.15%) |
| Queries without `tenantId` filter | **467** |
| OK (suppressed: user-scoped, has tenantId, etc.) | 83 |
| MEDIUM (suppressed: global/admin/CLI/background/public) | 461 |
| **Total violations** | **0** |
| → CRITICAL (write ops, no tenantId) | **0** |
| → HIGH (read ops, no tenantId) | **0** |
| **Real violations needing review** | **0** |

### False-positive suppressions applied

The following heuristics downgraded potential violations to MEDIUM informational notes:

| Suppression reason | Queries affected |
|--------------------|-----------------|
| Admin handler (/api/admin/*) — sees all tenants by design | 179 |
| Collection's struct has no tenantId field — global by design | 147 |
| CLI tool (cmd/lastsaas/) — no request context | 76 |
| Background system task (no request context) | 28 |
| Public endpoint (no auth) — published content | 14 |
| Test utility (internal/testutil/) — not production code | 10 |
| User-scoped collection with userId filter — valid scope | 6 |
| Filter uses a globally-unique key — single-doc query | 4 |
| Auth-flow handler — user hasn't selected a tenant yet | 2 |
| Inserted struct declares tenantId — caller responsibility | 1 |

### Route scope breakdown

| Scope | Queries |
|-------|---------|
| `admin` | 200 |
| `auth` | 100 |
| `cli` | 85 |
| `unknown` | 57 |
| `tenant` | 43 |
| `background` | 30 |
| `public` | 15 |
| `testutil` | 14 |

### Risk levels

- **CRITICAL** — write operation (`InsertOne`, `UpdateOne`, `DeleteOne`, `FindOneAndUpdate`, ...) on a tenant-scoped collection without a `tenantId` filter. Can modify or delete data belonging to other tenants.
- **HIGH** — read operation (`Find`, `FindOne`, `Aggregate`, `CountDocuments`) on a tenant-scoped collection without a `tenantId` filter. Can leak data across tenants.
- **MEDIUM** — query that was *suppressed* by a false-positive heuristic (global-by-design collection, admin handler, background task, public endpoint, user-scoped filter, globally-unique key, or CLI tool). Not a strict violation but listed for review.
- **OK** — query has a `tenantId` filter, or is on a user-scoped collection filtered by `userId` (a valid scope since a user's data spans tenants).

The `safe_key_filter` flag marks queries whose filter contains a globally-unique key (e.g. `_id`, `tokenHash`, `slug`, `webhookId`). Such queries are downgraded to MEDIUM because the unique key already constrains the query to a single document regardless of tenant.

## CRITICAL Violations — Write Ops without tenantId (0 real)

_None — all write operations include a `tenantId` filter or were suppressed by a context heuristic._

## HIGH Violations — Read Ops without tenantId (0 real)

_None — all read operations include a `tenantId` filter or were suppressed by a context heuristic._

## Safe-Key Queries — Globally-Unique Filter (268)

These queries lack a `tenantId` filter but constrain on a globally-unique key (`_id`, `tokenHash`, `slug`, `webhookId`, etc.). The unique key already constrains the query to a single document regardless of tenant — downgraded to MEDIUM.

| Line | Function | Op | Collection | Filter | Scope | Risk | Suppression | Note |
|------|----------|----|------------|--------|-------|------|-------------|------|
| 160 | `cmdTenantsGet` | `FindOne` | `tenants` | `_id` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 166 | `cmdTenantsGet` | `FindOne` | `tenants` | `slug` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 193 | `cmdTenantsGet` | `FindOne` | `plans` | `_id` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 289 | `resolveUserNames` | `Find` | `users` | `_id` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 317 | `resolvePlanNames` | `Find` | `plans` | `_id` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 287 | `cmdUsersSetActive` | `FindOne` | `users` | `email` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 301 | `cmdUsersSetActive` | `UpdateOne` | `users` | `_id` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 342 | `cmdUsersRevokeSessions` | `FindOne` | `users` | `email` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 360 | `lookupUserWithMemberships` | `FindOne` | `users` | `email` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 383 | `resolveTenantNames` | `Find` | `tenants` | `_id` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 239 | `cmdSetup` | `FindOne` | `users` | `_id` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 303 | `cmdSetup` | `InsertOne` | `tenants` | `billingInterval`, `billingStatus`, `billingWaived`, `canceledAt`, `createdAt`, `currentPeriodEnd`, `isActive`, `isRoot`, `name`, `planId`, `purchasedCredits`, `seatQuantity`, `slug`, `stripeCustomerId`, `stripeSubscriptionId`, `subscriptionCredits`, `trialUsedAt`, `updatedAt` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 321 | `cmdSetup` | `DeleteOne` | `tenants` | `_id` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 325 | `cmdSetup` | `InsertOne` | `users` | `accountLockedUntil`, `authMethods`, `createdAt`, `displayName`, `email`, `emailVerified`, `failedLoginAttempts`, `githubId`, `googleId`, `isActive`, `lastLoginAt`, `lastVerificationSent`, `microsoftId`, `onboardingCompletedAt`, `passwordHash`, `recoveryCodes`, `themePreference`, `totpEnabled`, `totpSecret`, `totpVerifiedAt`, `trialUsedAt`, `updatedAt` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 326 | `cmdSetup` | `DeleteOne` | `tenants` | `_id` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 341 | `cmdSetup` | `DeleteOne` | `users` | `_id` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 342 | `cmdSetup` | `DeleteOne` | `tenants` | `_id` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 347 | `cmdSetup` | `DeleteOne` | `users` | `_id` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 348 | `cmdSetup` | `DeleteOne` | `tenants` | `_id` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 362 | `cmdSetup` | `DeleteOne` | `tenant_memberships` | `_id` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 363 | `cmdSetup` | `DeleteOne` | `users` | `_id` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 364 | `cmdSetup` | `DeleteOne` | `tenants` | `_id` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 417 | `cmdChangePassword` | `FindOne` | `users` | `email` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 447 | `cmdChangePassword` | `UpdateOne` | `users` | `_id` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 515 | `cmdSendMessage` | `FindOne` | `users` | `email` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 635 | `cmdConfigGet` | `FindOne` | `config_vars` | `name` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 665 | `cmdConfigSet` | `FindOne` | `config_vars` | `name` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 676 | `cmdConfigSet` | `UpdateOne` | `config_vars` | `name` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 713 | `cmdConfigReset` | `FindOne` | `config_vars` | `name` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 724 | `cmdConfigReset` | `UpdateOne` | `config_vars` | `name` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 768 | `cmdTransferRootOwner` | `FindOne` | `users` | `email` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 800 | `cmdTransferRootOwner` | `FindOne` | `users` | `_id` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 831 | `cmdTransferRootOwner` | `UpdateOne` | `tenant_memberships` | `_id` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 841 | `cmdTransferRootOwner` | `UpdateOne` | `tenant_memberships` | `_id` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 847 | `cmdTransferRootOwner` | `UpdateOne` | `tenant_memberships` | `_id` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 68 | `isRootTenantOwner` | `FindOne` | `tenants` | `_id` | `unknown` | MEDIUM | global-by-design | Collection 'tenants' maps to struct 'Tenant' which does NOT declare a tenantId bson fie... |
| 418 | `GetTenant` | `FindOne` | `tenants` | `_id` | `admin` | MEDIUM | admin-handler | Function 'GetTenant' is an admin handler (registered on /api/admin/*). Admin handlers s... |
| 441 | `GetTenant` | `Find` | `users` | `_id` | `admin` | MEDIUM | admin-handler | Function 'GetTenant' is an admin handler (registered on /api/admin/*). Admin handlers s... |
| 483 | `UpdateTenantStatus` | `FindOne` | `tenants` | `_id` | `admin` | MEDIUM | admin-handler | Function 'UpdateTenantStatus' is an admin handler (registered on /api/admin/*). Admin h... |
| 502 | `UpdateTenantStatus` | `UpdateOne` | `tenants` | `_id` | `admin` | MEDIUM | admin-handler | Function 'UpdateTenantStatus' is an admin handler (registered on /api/admin/*). Admin h... |
| 774 | `UpdateUserStatus` | `UpdateOne` | `users` | `_id` | `admin` | MEDIUM | admin-handler | Function 'UpdateUserStatus' is an admin handler (registered on /api/admin/*). Admin han... |
| 943 | `GetUser` | `FindOne` | `users` | `_id` | `admin` | MEDIUM | admin-handler | Function 'GetUser' is an admin handler (registered on /api/admin/*). Admin handlers see... |
| 992 | `GetUser` | `Find` | `tenants` | `_id` | `admin` | MEDIUM | admin-handler | Function 'GetUser' is an admin handler (registered on /api/admin/*). Admin handlers see... |
| 1079 | `UpdateUser` | `FindOne` | `users` | `_id` | `admin` | MEDIUM | admin-handler | Function 'UpdateUser' is an admin handler (registered on /api/admin/*). Admin handlers ... |
| 1098 | `UpdateUser` | `CountDocuments` | `users` | `email`, `_id` | `admin` | MEDIUM | admin-handler | Function 'UpdateUser' is an admin handler (registered on /api/admin/*). Admin handlers ... |
| 1121 | `UpdateUser` | `UpdateOne` | `users` | `_id` | `admin` | MEDIUM | admin-handler | Function 'UpdateUser' is an admin handler (registered on /api/admin/*). Admin handlers ... |
| 1165 | `UpdateUserRole` | `FindOne` | `tenants` | `_id` | `admin` | MEDIUM | admin-handler | Function 'UpdateUserRole' is an admin handler (registered on /api/admin/*). Admin handl... |
| 1186 | `UpdateUserRole` | `UpdateOne` | `tenant_memberships` | `_id` | `admin` | MEDIUM | admin-handler | Function 'UpdateUserRole' is an admin handler (registered on /api/admin/*). Admin handl... |
| 1264 | `PreflightDeleteUser` | `Find` | `tenants` | `_id` | `admin` | MEDIUM | admin-handler | Function 'PreflightDeleteUser' is an admin handler (registered on /api/admin/*). Admin ... |
| 1301 | `PreflightDeleteUser` | `Find` | `users` | `_id` | `admin` | MEDIUM | admin-handler | Function 'PreflightDeleteUser' is an admin handler (registered on /api/admin/*). Admin ... |


_…and 218 more (see JSON)._

## MEDIUM — Suppressed Queries (461)

| Line | Function | Op | Collection | Filter | Scope | Risk | Suppression | Note |
|------|----------|----|------------|--------|-------|------|-------------|------|
| 67 | `cmdDoctor` | `FindOne` | `system_config` | — | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 102 | `cmdDoctor` | `FindOne` | `tenants` | `isRoot` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 115 | `cmdDoctor` | `CountDocuments` | `system_nodes` | `lastSeen` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 58 | `cmdFinancialSummary` | `Aggregate` | `financial_transactions` | `type` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 84 | `cmdFinancialSummary` | `Aggregate` | `financial_transactions` | `type` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 111 | `cmdFinancialSummary` | `Aggregate` | `financial_transactions` | — | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 131 | `cmdFinancialSummary` | `CountDocuments` | `tenants` | `billingStatus` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 138 | `cmdFinancialSummary` | `FindOne` | `daily_metrics` | — | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 147 | `cmdFinancialSummary` | `Aggregate` | `financial_transactions` | `type` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 350 | `cmdFinancialMetrics` | `Find` | `daily_metrics` | — | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 51 | `cmdHealth` | `Find` | `system_nodes` | — | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 77 | `cmdHealth` | `FindOne` | `system_metrics` | — | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 100 | `cmdHealth` | `Find` | `system_nodes` | — | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 124 | `cmdHealth` | `FindOne` | `system_metrics` | — | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 140 | `queryLogs` | `Find` | `system_logs` | — | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 193 | `logsFollow` | `Find` | `system_logs` | `createdAt` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 23 | `cmdStats` | `EstimatedDocumentCount` | `users` | — | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 27 | `cmdStats` | `EstimatedDocumentCount` | `tenants` | — | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 33 | `cmdStats` | `CountDocuments` | `users` | `isActive` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 39 | `cmdStats` | `CountDocuments` | `tenants` | `billingStatus` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 53 | `cmdStats` | `Aggregate` | `system_logs` | — | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 73 | `cmdStats` | `FindOne` | `daily_metrics` | — | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 81 | `cmdStats` | `Aggregate` | `financial_transactions` | `type` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 61 | `cmdTenantsList` | `Find` | `tenants` | — | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 160 | `cmdTenantsGet` | `FindOne` | `tenants` | `_id` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 166 | `cmdTenantsGet` | `FindOne` | `tenants` | `slug` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 193 | `cmdTenantsGet` | `FindOne` | `plans` | `_id` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 289 | `resolveUserNames` | `Find` | `users` | `_id` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 317 | `resolvePlanNames` | `Find` | `plans` | `_id` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 73 | `cmdUsersList` | `Find` | `users` | `isActive` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 287 | `cmdUsersSetActive` | `FindOne` | `users` | `email` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 301 | `cmdUsersSetActive` | `UpdateOne` | `users` | `_id` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 314 | `cmdUsersSetActive` | `DeleteMany` | `refresh_tokens` | `userId` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 342 | `cmdUsersRevokeSessions` | `FindOne` | `users` | `email` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 347 | `cmdUsersRevokeSessions` | `DeleteMany` | `refresh_tokens` | `userId` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 360 | `lookupUserWithMemberships` | `FindOne` | `users` | `email` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 365 | `lookupUserWithMemberships` | `Find` | `tenant_memberships` | `userId` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 383 | `resolveTenantNames` | `Find` | `tenants` | `_id` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 227 | `cmdSetup` | `FindOne` | `system_config` | — | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 235 | `cmdSetup` | `FindOne` | `tenants` | `isRoot` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 239 | `cmdSetup` | `FindOne` | `users` | `_id` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 303 | `cmdSetup` | `InsertOne` | `tenants` | `billingInterval`, `billingStatus`, `billingWaived`, `canceledAt`, `createdAt`, `currentPeriodEnd`, `isActive`, `isRoot`, `name`, `planId`, `purchasedCredits`, `seatQuantity`, `slug`, `stripeCustomerId`, `stripeSubscriptionId`, `subscriptionCredits`, `trialUsedAt`, `updatedAt` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 321 | `cmdSetup` | `DeleteOne` | `tenants` | `_id` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 325 | `cmdSetup` | `InsertOne` | `users` | `accountLockedUntil`, `authMethods`, `createdAt`, `displayName`, `email`, `emailVerified`, `failedLoginAttempts`, `githubId`, `googleId`, `isActive`, `lastLoginAt`, `lastVerificationSent`, `microsoftId`, `onboardingCompletedAt`, `passwordHash`, `recoveryCodes`, `themePreference`, `totpEnabled`, `totpSecret`, `totpVerifiedAt`, `trialUsedAt`, `updatedAt` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 326 | `cmdSetup` | `DeleteOne` | `tenants` | `_id` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 341 | `cmdSetup` | `DeleteOne` | `users` | `_id` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 342 | `cmdSetup` | `DeleteOne` | `tenants` | `_id` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 347 | `cmdSetup` | `DeleteOne` | `users` | `_id` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 348 | `cmdSetup` | `DeleteOne` | `tenants` | `_id` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 361 | `cmdSetup` | `InsertOne` | `system_config` | `initialized`, `initializedAt`, `initializedBy`, `version` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |


_…and 411 more (see JSON and All Queries by File below)._

## All Queries by File

### `backend/cmd/lastsaas/cmd_doctor.go`

| Line | Function | Op | Collection | Filter | Scope | Risk | Suppression | Note |
|------|----------|----|------------|--------|-------|------|-------------|------|
| 67 | `cmdDoctor` | `FindOne` | `system_config` | — | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 102 | `cmdDoctor` | `FindOne` | `tenants` | `isRoot` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 103 | `cmdDoctor` | `CountDocuments` | `tenant_memberships` | `tenantId`, `role` | `cli` | OK |  | Filter contains tenantId. |
| 115 | `cmdDoctor` | `CountDocuments` | `system_nodes` | `lastSeen` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |


### `backend/cmd/lastsaas/cmd_financial.go`

| Line | Function | Op | Collection | Filter | Scope | Risk | Suppression | Note |
|------|----------|----|------------|--------|-------|------|-------------|------|
| 58 | `cmdFinancialSummary` | `Aggregate` | `financial_transactions` | `type` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 84 | `cmdFinancialSummary` | `Aggregate` | `financial_transactions` | `type` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 111 | `cmdFinancialSummary` | `Aggregate` | `financial_transactions` | — | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 131 | `cmdFinancialSummary` | `CountDocuments` | `tenants` | `billingStatus` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 138 | `cmdFinancialSummary` | `FindOne` | `daily_metrics` | — | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 147 | `cmdFinancialSummary` | `Aggregate` | `financial_transactions` | `type` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 254 | `cmdFinancialTransactions` | `Find` | `financial_transactions` | `createdAt`, `tenantId`, `type` | `cli` | OK |  | Filter contains tenantId. |
| 350 | `cmdFinancialMetrics` | `Find` | `daily_metrics` | — | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |


### `backend/cmd/lastsaas/cmd_health.go`

| Line | Function | Op | Collection | Filter | Scope | Risk | Suppression | Note |
|------|----------|----|------------|--------|-------|------|-------------|------|
| 51 | `cmdHealth` | `Find` | `system_nodes` | — | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 77 | `cmdHealth` | `FindOne` | `system_metrics` | — | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 100 | `cmdHealth` | `Find` | `system_nodes` | — | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 124 | `cmdHealth` | `FindOne` | `system_metrics` | — | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |


### `backend/cmd/lastsaas/cmd_logs.go`

| Line | Function | Op | Collection | Filter | Scope | Risk | Suppression | Note |
|------|----------|----|------------|--------|-------|------|-------------|------|
| 140 | `queryLogs` | `Find` | `system_logs` | — | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 193 | `logsFollow` | `Find` | `system_logs` | `createdAt` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |


### `backend/cmd/lastsaas/cmd_stats.go`

| Line | Function | Op | Collection | Filter | Scope | Risk | Suppression | Note |
|------|----------|----|------------|--------|-------|------|-------------|------|
| 23 | `cmdStats` | `EstimatedDocumentCount` | `users` | — | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 27 | `cmdStats` | `EstimatedDocumentCount` | `tenants` | — | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 33 | `cmdStats` | `CountDocuments` | `users` | `isActive` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 39 | `cmdStats` | `CountDocuments` | `tenants` | `billingStatus` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 53 | `cmdStats` | `Aggregate` | `system_logs` | — | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 73 | `cmdStats` | `FindOne` | `daily_metrics` | — | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 81 | `cmdStats` | `Aggregate` | `financial_transactions` | `type` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |


### `backend/cmd/lastsaas/cmd_tenants.go`

| Line | Function | Op | Collection | Filter | Scope | Risk | Suppression | Note |
|------|----------|----|------------|--------|-------|------|-------------|------|
| 61 | `cmdTenantsList` | `Find` | `tenants` | — | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 160 | `cmdTenantsGet` | `FindOne` | `tenants` | `_id` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 166 | `cmdTenantsGet` | `FindOne` | `tenants` | `slug` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 173 | `cmdTenantsGet` | `Find` | `tenant_memberships` | `tenantId` | `cli` | OK |  | Filter contains tenantId. |
| 193 | `cmdTenantsGet` | `FindOne` | `plans` | `_id` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 289 | `resolveUserNames` | `Find` | `users` | `_id` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 317 | `resolvePlanNames` | `Find` | `plans` | `_id` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 355 | `countMembersPerTenant` | `Aggregate` | `tenant_memberships` | `tenantId` | `cli` | OK |  | Filter contains tenantId. |


### `backend/cmd/lastsaas/cmd_users.go`

| Line | Function | Op | Collection | Filter | Scope | Risk | Suppression | Note |
|------|----------|----|------------|--------|-------|------|-------------|------|
| 73 | `cmdUsersList` | `Find` | `users` | `isActive` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 287 | `cmdUsersSetActive` | `FindOne` | `users` | `email` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 301 | `cmdUsersSetActive` | `UpdateOne` | `users` | `_id` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 314 | `cmdUsersSetActive` | `DeleteMany` | `refresh_tokens` | `userId` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 342 | `cmdUsersRevokeSessions` | `FindOne` | `users` | `email` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 347 | `cmdUsersRevokeSessions` | `DeleteMany` | `refresh_tokens` | `userId` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 360 | `lookupUserWithMemberships` | `FindOne` | `users` | `email` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 365 | `lookupUserWithMemberships` | `Find` | `tenant_memberships` | `userId` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 383 | `resolveTenantNames` | `Find` | `tenants` | `_id` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |


### `backend/cmd/lastsaas/main.go`

| Line | Function | Op | Collection | Filter | Scope | Risk | Suppression | Note |
|------|----------|----|------------|--------|-------|------|-------------|------|
| 227 | `cmdSetup` | `FindOne` | `system_config` | — | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 235 | `cmdSetup` | `FindOne` | `tenants` | `isRoot` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 237 | `cmdSetup` | `FindOne` | `tenant_memberships` | `tenantId`, `role` | `cli` | OK |  | Filter contains tenantId. |
| 239 | `cmdSetup` | `FindOne` | `users` | `_id` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 303 | `cmdSetup` | `InsertOne` | `tenants` | `billingInterval`, `billingStatus`, `billingWaived`, `canceledAt`, `createdAt`, `currentPeriodEnd`, `isActive`, `isRoot`, `name`, `planId`, `purchasedCredits`, `seatQuantity`, `slug`, `stripeCustomerId`, `stripeSubscriptionId`, `subscriptionCredits`, `trialUsedAt`, `updatedAt` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 321 | `cmdSetup` | `DeleteOne` | `tenants` | `_id` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 325 | `cmdSetup` | `InsertOne` | `users` | `accountLockedUntil`, `authMethods`, `createdAt`, `displayName`, `email`, `emailVerified`, `failedLoginAttempts`, `githubId`, `googleId`, `isActive`, `lastLoginAt`, `lastVerificationSent`, `microsoftId`, `onboardingCompletedAt`, `passwordHash`, `recoveryCodes`, `themePreference`, `totpEnabled`, `totpSecret`, `totpVerifiedAt`, `trialUsedAt`, `updatedAt` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 326 | `cmdSetup` | `DeleteOne` | `tenants` | `_id` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 341 | `cmdSetup` | `DeleteOne` | `users` | `_id` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 342 | `cmdSetup` | `DeleteOne` | `tenants` | `_id` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 346 | `cmdSetup` | `InsertOne` | `tenant_memberships` | `joinedAt`, `role`, `tenantId`, `updatedAt`, `userId` | `cli` | OK |  | Filter contains tenantId. |
| 347 | `cmdSetup` | `DeleteOne` | `users` | `_id` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 348 | `cmdSetup` | `DeleteOne` | `tenants` | `_id` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 361 | `cmdSetup` | `InsertOne` | `system_config` | `initialized`, `initializedAt`, `initializedBy`, `version` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 362 | `cmdSetup` | `DeleteOne` | `tenant_memberships` | `_id` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 363 | `cmdSetup` | `DeleteOne` | `users` | `_id` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 364 | `cmdSetup` | `DeleteOne` | `tenants` | `_id` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 379 | `cmdSetup` | `InsertOne` | `messages` | `body`, `createdAt`, `isSystem`, `read`, `subject`, `userId` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 417 | `cmdChangePassword` | `FindOne` | `users` | `email` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 447 | `cmdChangePassword` | `UpdateOne` | `users` | `_id` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 460 | `cmdChangePassword` | `DeleteMany` | `refresh_tokens` | `userId` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 515 | `cmdSendMessage` | `FindOne` | `users` | `email` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 531 | `cmdSendMessage` | `InsertOne` | `messages` | `body`, `createdAt`, `isSystem`, `read`, `subject`, `userId` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 587 | `cmdConfigList` | `Find` | `config_vars` | — | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 635 | `cmdConfigGet` | `FindOne` | `config_vars` | `name` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 665 | `cmdConfigSet` | `FindOne` | `config_vars` | `name` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 676 | `cmdConfigSet` | `UpdateOne` | `config_vars` | `name` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 713 | `cmdConfigReset` | `FindOne` | `config_vars` | `name` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 724 | `cmdConfigReset` | `UpdateOne` | `config_vars` | `name` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 760 | `cmdTransferRootOwner` | `FindOne` | `tenants` | `isRoot` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 768 | `cmdTransferRootOwner` | `FindOne` | `users` | `email` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 775 | `cmdTransferRootOwner` | `FindOne` | `tenant_memberships` | `userId`, `tenantId` | `cli` | OK |  | Filter contains tenantId. |
| 791 | `cmdTransferRootOwner` | `FindOne` | `tenant_memberships` | `tenantId`, `role` | `cli` | OK |  | Filter contains tenantId. |
| 800 | `cmdTransferRootOwner` | `FindOne` | `users` | `_id` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 831 | `cmdTransferRootOwner` | `UpdateOne` | `tenant_memberships` | `_id` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 841 | `cmdTransferRootOwner` | `UpdateOne` | `tenant_memberships` | `_id` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 847 | `cmdTransferRootOwner` | `UpdateOne` | `tenant_memberships` | `_id` | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 862 | `cmdTransferRootOwner` | `InsertOne` | `system_logs` | `action`, `category`, `createdAt`, `message`, `metadata`, `severity`, `tenantId`, `userId` | `cli` | OK |  | Filter contains tenantId. |
| 885 | `cmdVersion` | `FindOne` | `system_config` | — | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 931 | `cmdStatus` | `FindOne` | `system_config` | — | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 946 | `cmdStatus` | `CountDocuments` | `users` | — | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |
| 950 | `cmdStatus` | `CountDocuments` | `tenants` | — | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |


### `backend/cmd/server/main.go`

| Line | Function | Op | Collection | Filter | Scope | Risk | Suppression | Note |
|------|----------|----|------------|--------|-------|------|-------------|------|
| 801 | `main` | `FindOne` | `branding_config` | — | `cli` | MEDIUM | cli-tool | Query is in a CLI tool (cmd/lastsaas/) — CLI tools have no HTTP request context and ope... |


### `backend/internal/api/handlers/admin.go`

| Line | Function | Op | Collection | Filter | Scope | Risk | Suppression | Note |
|------|----------|----|------------|--------|-------|------|-------------|------|
| 51 | `isRootTenantOwner` | `CountDocuments` | `tenant_memberships` | `userId`, `role` | `unknown` | OK | user-scoped | Collection 'tenant_memberships' is user-scoped (has userId field) and the filter contai... |
| 64 | `isRootTenantOwner` | `FindOne` | `tenant_memberships` | `userId`, `role` | `unknown` | OK | user-scoped | Collection 'tenant_memberships' is user-scoped (has userId field) and the filter contai... |
| 68 | `isRootTenantOwner` | `FindOne` | `tenants` | `_id` | `unknown` | MEDIUM | global-by-design | Collection 'tenants' maps to struct 'Tenant' which does NOT declare a tenantId bson fie... |
| 176 | `ListTenants` | `CountDocuments` | `tenants` | `$or`, `billingStatus`, `isActive` | `admin` | MEDIUM | admin-handler | Function 'ListTenants' is an admin handler (registered on /api/admin/*). Admin handlers... |
| 187 | `ListTenants` | `Find` | `tenants` | `$or`, `billingStatus`, `isActive` | `admin` | MEDIUM | admin-handler | Function 'ListTenants' is an admin handler (registered on /api/admin/*). Admin handlers... |
| 211 | `ListTenants` | `Aggregate` | `tenant_memberships` | `tenantId` | `admin` | OK |  | Filter contains tenantId. |
| 228 | `ListTenants` | `Find` | `plans` | — | `admin` | MEDIUM | admin-handler | Function 'ListTenants' is an admin handler (registered on /api/admin/*). Admin handlers... |
| 312 | `ExportTenantsCSV` | `Find` | `tenants` | `$or`, `billingStatus`, `isActive` | `admin` | MEDIUM | admin-handler | Function 'ExportTenantsCSV' is an admin handler (registered on /api/admin/*). Admin han... |
| 336 | `ExportTenantsCSV` | `Aggregate` | `tenant_memberships` | `tenantId` | `admin` | OK |  | Filter contains tenantId. |
| 353 | `ExportTenantsCSV` | `Find` | `plans` | — | `admin` | MEDIUM | admin-handler | Function 'ExportTenantsCSV' is an admin handler (registered on /api/admin/*). Admin han... |
| 418 | `GetTenant` | `FindOne` | `tenants` | `_id` | `admin` | MEDIUM | admin-handler | Function 'GetTenant' is an admin handler (registered on /api/admin/*). Admin handlers s... |
| 424 | `GetTenant` | `Find` | `tenant_memberships` | `tenantId` | `admin` | OK |  | Filter contains tenantId. |
| 441 | `GetTenant` | `Find` | `users` | `_id` | `admin` | MEDIUM | admin-handler | Function 'GetTenant' is an admin handler (registered on /api/admin/*). Admin handlers s... |
| 483 | `UpdateTenantStatus` | `FindOne` | `tenants` | `_id` | `admin` | MEDIUM | admin-handler | Function 'UpdateTenantStatus' is an admin handler (registered on /api/admin/*). Admin h... |
| 502 | `UpdateTenantStatus` | `UpdateOne` | `tenants` | `_id` | `admin` | MEDIUM | admin-handler | Function 'UpdateTenantStatus' is an admin handler (registered on /api/admin/*). Admin h... |
| 581 | `ListUsers` | `CountDocuments` | `users` | `$or`, `isActive` | `admin` | MEDIUM | admin-handler | Function 'ListUsers' is an admin handler (registered on /api/admin/*). Admin handlers s... |
| 592 | `ListUsers` | `Find` | `users` | `$or`, `isActive` | `admin` | MEDIUM | admin-handler | Function 'ListUsers' is an admin handler (registered on /api/admin/*). Admin handlers s... |
| 616 | `ListUsers` | `Aggregate` | `tenant_memberships` | `userId` | `admin` | MEDIUM | admin-handler | Function 'ListUsers' is an admin handler (registered on /api/admin/*). Admin handlers s... |
| 678 | `ExportUsersCSV` | `Find` | `users` | `$or`, `isActive` | `admin` | MEDIUM | admin-handler | Function 'ExportUsersCSV' is an admin handler (registered on /api/admin/*). Admin handl... |
| 702 | `ExportUsersCSV` | `Aggregate` | `tenant_memberships` | `userId` | `admin` | MEDIUM | admin-handler | Function 'ExportUsersCSV' is an admin handler (registered on /api/admin/*). Admin handl... |
| 774 | `UpdateUserStatus` | `UpdateOne` | `users` | `_id` | `admin` | MEDIUM | admin-handler | Function 'UpdateUserStatus' is an admin handler (registered on /api/admin/*). Admin han... |
| 817 | `GetDashboard` | `CountDocuments` | `users` | — | `admin` | MEDIUM | admin-handler | Function 'GetDashboard' is an admin handler (registered on /api/admin/*). Admin handler... |
| 822 | `GetDashboard` | `CountDocuments` | `tenants` | — | `admin` | MEDIUM | admin-handler | Function 'GetDashboard' is an admin handler (registered on /api/admin/*). Admin handler... |
| 943 | `GetUser` | `FindOne` | `users` | `_id` | `admin` | MEDIUM | admin-handler | Function 'GetUser' is an admin handler (registered on /api/admin/*). Admin handlers see... |
| 948 | `GetUser` | `Find` | `tenant_memberships` | `userId` | `admin` | MEDIUM | admin-handler | Function 'GetUser' is an admin handler (registered on /api/admin/*). Admin handlers see... |
| 963 | `GetUser` | `Find` | `plans` | — | `admin` | MEDIUM | admin-handler | Function 'GetUser' is an admin handler (registered on /api/admin/*). Admin handlers see... |
| 992 | `GetUser` | `Find` | `tenants` | `_id` | `admin` | MEDIUM | admin-handler | Function 'GetUser' is an admin handler (registered on /api/admin/*). Admin handlers see... |
| 1079 | `UpdateUser` | `FindOne` | `users` | `_id` | `admin` | MEDIUM | admin-handler | Function 'UpdateUser' is an admin handler (registered on /api/admin/*). Admin handlers ... |
| 1098 | `UpdateUser` | `CountDocuments` | `users` | `email`, `_id` | `admin` | MEDIUM | admin-handler | Function 'UpdateUser' is an admin handler (registered on /api/admin/*). Admin handlers ... |
| 1121 | `UpdateUser` | `UpdateOne` | `users` | `_id` | `admin` | MEDIUM | admin-handler | Function 'UpdateUser' is an admin handler (registered on /api/admin/*). Admin handlers ... |
| 1165 | `UpdateUserRole` | `FindOne` | `tenants` | `_id` | `admin` | MEDIUM | admin-handler | Function 'UpdateUserRole' is an admin handler (registered on /api/admin/*). Admin handl... |
| 1182 | `UpdateUserRole` | `FindOne` | `tenant_memberships` | `tenantId`, `role` | `admin` | OK |  | Filter contains tenantId. |
| 1186 | `UpdateUserRole` | `UpdateOne` | `tenant_memberships` | `_id` | `admin` | MEDIUM | admin-handler | Function 'UpdateUserRole' is an admin handler (registered on /api/admin/*). Admin handl... |
| 1193 | `UpdateUserRole` | `UpdateOne` | `tenant_memberships` | `userId`, `tenantId` | `admin` | OK |  | Filter contains tenantId. |
| 1243 | `PreflightDeleteUser` | `Find` | `tenant_memberships` | `userId`, `role` | `admin` | MEDIUM | admin-handler | Function 'PreflightDeleteUser' is an admin handler (registered on /api/admin/*). Admin ... |
| 1264 | `PreflightDeleteUser` | `Find` | `tenants` | `_id` | `admin` | MEDIUM | admin-handler | Function 'PreflightDeleteUser' is an admin handler (registered on /api/admin/*). Admin ... |
| 1280 | `PreflightDeleteUser` | `Find` | `tenant_memberships` | `tenantId`, `userId` | `admin` | OK |  | Filter contains tenantId. |
| 1301 | `PreflightDeleteUser` | `Find` | `users` | `_id` | `admin` | MEDIUM | admin-handler | Function 'PreflightDeleteUser' is an admin handler (registered on /api/admin/*). Admin ... |
| 1358 | `DeleteUser` | `FindOne` | `users` | `_id` | `admin` | MEDIUM | admin-handler | Function 'DeleteUser' is an admin handler (registered on /api/admin/*). Admin handlers ... |
| 1378 | `DeleteUser` | `Find` | `tenant_memberships` | `userId` | `admin` | MEDIUM | admin-handler | Function 'DeleteUser' is an admin handler (registered on /api/admin/*). Admin handlers ... |
| 1398 | `DeleteUser` | `FindOne` | `tenants` | `_id` | `admin` | MEDIUM | admin-handler | Function 'DeleteUser' is an admin handler (registered on /api/admin/*). Admin handlers ... |
| 1414 | `DeleteUser` | `UpdateOne` | `tenant_memberships` | `userId`, `tenantId` | `admin` | OK |  | Filter contains tenantId. |
| 1430 | `DeleteUser` | `CountDocuments` | `tenant_memberships` | `tenantId`, `userId` | `admin` | OK |  | Filter contains tenantId. |
| 1454 | `DeleteUser` | `DeleteMany` | `tenant_memberships` | `tenantId` | `admin` | OK |  | Filter contains tenantId. |
| 1457 | `DeleteUser` | `DeleteOne` | `tenants` | `_id` | `admin` | MEDIUM | admin-handler | Function 'DeleteUser' is an admin handler (registered on /api/admin/*). Admin handlers ... |
| 1460 | `DeleteUser` | `DeleteMany` | `invitations` | `tenantId` | `admin` | OK |  | Filter contains tenantId. |
| 1479 | `DeleteUser` | `DeleteMany` | `tenant_memberships` | `userId` | `admin` | MEDIUM | admin-handler | Function 'DeleteUser' is an admin handler (registered on /api/admin/*). Admin handlers ... |
| 1482 | `DeleteUser` | `DeleteMany` | `refresh_tokens` | `userId` | `admin` | MEDIUM | admin-handler | Function 'DeleteUser' is an admin handler (registered on /api/admin/*). Admin handlers ... |
| 1485 | `DeleteUser` | `DeleteMany` | `messages` | `userId` | `admin` | MEDIUM | admin-handler | Function 'DeleteUser' is an admin handler (registered on /api/admin/*). Admin handlers ... |
| 1488 | `DeleteUser` | `DeleteOne` | `users` | `_id` | `admin` | MEDIUM | admin-handler | Function 'DeleteUser' is an admin handler (registered on /api/admin/*). Admin handlers ... |
| 1529 | `UpdateTenant` | `FindOne` | `tenants` | `_id` | `admin` | MEDIUM | admin-handler | Function 'UpdateTenant' is an admin handler (registered on /api/admin/*). Admin handler... |
| 1587 | `UpdateTenant` | `UpdateOne` | `tenants` | `_id` | `admin` | MEDIUM | admin-handler | Function 'UpdateTenant' is an admin handler (registered on /api/admin/*). Admin handler... |
| 1619 | `ImpersonateUser` | `FindOne` | `users` | `_id` | `admin` | MEDIUM | admin-handler | Function 'ImpersonateUser' is an admin handler (registered on /api/admin/*). Admin hand... |
| 1626 | `ImpersonateUser` | `FindOne` | `tenants` | `isRoot` | `admin` | MEDIUM | admin-handler | Function 'ImpersonateUser' is an admin handler (registered on /api/admin/*). Admin hand... |
| 1628 | `ImpersonateUser` | `FindOne` | `tenant_memberships` | `userId`, `tenantId`, `role` | `admin` | OK |  | Filter contains tenantId. |
| 1656 | `ImpersonateUser` | `InsertOne` | `impersonation_logs` | `adminId`, `adminEmail`, `targetId`, `targetEmail`, `ipAddress`, `startedAt`, `expiresAt` | `admin` | MEDIUM | admin-handler | Function 'ImpersonateUser' is an admin handler (registered on /api/admin/*). Admin hand... |
| 1667 | `ImpersonateUser` | `Find` | `tenant_memberships` | `userId` | `admin` | MEDIUM | admin-handler | Function 'ImpersonateUser' is an admin handler (registered on /api/admin/*). Admin hand... |
| 1680 | `ImpersonateUser` | `FindOne` | `tenants` | `_id` | `admin` | MEDIUM | admin-handler | Function 'ImpersonateUser' is an admin handler (registered on /api/admin/*). Admin hand... |
| 1703 | `getRootTenant` | `FindOne` | `tenants` | `isRoot` | `unknown` | MEDIUM | global-by-design | Collection 'tenants' maps to struct 'Tenant' which does NOT declare a tenantId bson fie... |
| 1719 | `ListRootMembers` | `Find` | `tenant_memberships` | `tenantId` | `admin` | OK |  | Filter contains tenantId. |
| 1739 | `ListRootMembers` | `Find` | `users` | `_id` | `admin` | MEDIUM | admin-handler | Function 'ListRootMembers' is an admin handler (registered on /api/admin/*). Admin hand... |
| 1770 | `ListRootMembers` | `Find` | `invitations` | `tenantId`, `status`, `expiresAt` | `admin` | OK |  | Filter contains tenantId. |
| 1837 | `InviteRootMember` | `FindOne` | `users` | `email` | `admin` | MEDIUM | admin-handler | Function 'InviteRootMember' is an admin handler (registered on /api/admin/*). Admin han... |
| 1838 | `InviteRootMember` | `CountDocuments` | `tenant_memberships` | `userId`, `tenantId` | `admin` | OK |  | Filter contains tenantId. |
| 1853 | `InviteRootMember` | `CountDocuments` | `invitations` | `tenantId`, `email`, `status`, `expiresAt` | `admin` | OK |  | Filter contains tenantId. |
| 1885 | `InviteRootMember` | `InsertOne` | `invitations` | `createdAt`, `email`, `expiresAt`, `invitedBy`, `role`, `status`, `tenantId`, `token` | `admin` | OK |  | Filter contains tenantId. |
| 1946 | `RemoveRootMember` | `FindOne` | `tenant_memberships` | `userId`, `tenantId` | `admin` | OK |  | Filter contains tenantId. |
| 1964 | `RemoveRootMember` | `DeleteOne` | `tenant_memberships` | `_id` | `admin` | MEDIUM | admin-handler | Function 'RemoveRootMember' is an admin handler (registered on /api/admin/*). Admin han... |
| 2032 | `ChangeRootMemberRole` | `UpdateOne` | `tenant_memberships` | `userId`, `tenantId` | `admin` | OK |  | Filter contains tenantId. |
| 2074 | `CancelRootInvitation` | `DeleteOne` | `invitations` | `_id`, `tenantId`, `status` | `admin` | OK |  | Filter contains tenantId. |


### `backend/internal/api/handlers/announcements.go`

| Line | Function | Op | Collection | Filter | Scope | Risk | Suppression | Note |
|------|----------|----|------------|--------|-------|------|-------------|------|
| 33 | `ListPublic` | `Find` | `announcements` | `isPublished` | `public` | MEDIUM | public-endpoint | Function 'ListPublic' is a public endpoint (no auth) — returns published/global content... |
| 54 | `ListAll` | `Find` | `announcements` | — | `admin` | MEDIUM | admin-handler | Function 'ListAll' is an admin handler (registered on /api/admin/*). Admin handlers see... |
| 105 | `Create` | `InsertOne` | `announcements` | `body`, `createdAt`, `isPublished`, `publishedAt`, `title`, `updatedAt` | `admin` | MEDIUM | admin-handler | Function 'Create' is an admin handler (registered on /api/admin/*). Admin handlers see ... |
| 152 | `Update` | `UpdateOne` | `announcements` | `_id` | `admin` | MEDIUM | admin-handler | Function 'Update' is an admin handler (registered on /api/admin/*). Admin handlers see ... |
| 168 | `Delete` | `DeleteOne` | `announcements` | `_id` | `admin` | MEDIUM | admin-handler | Function 'Delete' is an admin handler (registered on /api/admin/*). Admin handlers see ... |


### `backend/internal/api/handlers/apikeys.go`

| Line | Function | Op | Collection | Filter | Scope | Risk | Suppression | Note |
|------|----------|----|------------|--------|-------|------|-------------|------|
| 45 | `ListAPIKeys` | `Find` | `api_keys` | `isActive` | `admin` | MEDIUM | admin-handler | Function 'ListAPIKeys' is an admin handler (registered on /api/admin/*). Admin handlers... |
| 60 | `ListAPIKeys` | `CountDocuments` | `api_keys` | `isActive` | `admin` | MEDIUM | admin-handler | Function 'ListAPIKeys' is an admin handler (registered on /api/admin/*). Admin handlers... |
| 127 | `CreateAPIKey` | `InsertOne` | `api_keys` | `authority`, `createdAt`, `createdBy`, `isActive`, `keyHash`, `keyPreview`, `lastUsedAt`, `name` | `admin` | MEDIUM | admin-handler | Function 'CreateAPIKey' is an admin handler (registered on /api/admin/*). Admin handler... |
| 166 | `DeleteAPIKey` | `UpdateByID` | `api_keys` | `_id` | `admin` | MEDIUM | admin-handler | Function 'DeleteAPIKey' is an admin handler (registered on /api/admin/*). Admin handler... |


### `backend/internal/api/handlers/auth.go`

| Line | Function | Op | Collection | Filter | Scope | Risk | Suppression | Note |
|------|----------|----|------------|--------|-------|------|-------------|------|
| 223 | `Register` | `FindOne` | `users` | `email` | `auth` | MEDIUM | global-by-design | Collection 'users' maps to struct 'User' which does NOT declare a tenantId bson field —... |
| 252 | `Register` | `InsertOne` | `users` | `accountLockedUntil`, `authMethods`, `createdAt`, `displayName`, `email`, `emailVerified`, `failedLoginAttempts`, `githubId`, `googleId`, `isActive`, `lastLoginAt`, `lastVerificationSent`, `microsoftId`, `onboardingCompletedAt`, `passwordHash`, `recoveryCodes`, `themePreference`, `totpEnabled`, `totpSecret`, `totpVerifiedAt`, `trialUsedAt`, `updatedAt` | `auth` | MEDIUM | global-by-design | Collection 'users' maps to struct 'User' which does NOT declare a tenantId bson field —... |
| 330 | `Login` | `FindOne` | `users` | `email` | `auth` | MEDIUM | global-by-design | Collection 'users' maps to struct 'User' which does NOT declare a tenantId bson field —... |
| 359 | `Login` | `FindOneAndUpdate` | `users` | `_id`, `accountLockedUntil` | `auth` | MEDIUM | global-by-design | Collection 'users' maps to struct 'User' which does NOT declare a tenantId bson field —... |
| 367 | `Login` | `UpdateOne` | `users` | `_id` | `auth` | MEDIUM | global-by-design | Collection 'users' maps to struct 'User' which does NOT declare a tenantId bson field —... |
| 387 | `Login` | `UpdateOne` | `users` | `_id` | `auth` | MEDIUM | global-by-design | Collection 'users' maps to struct 'User' which does NOT declare a tenantId bson field —... |
| 453 | `Logout` | `InsertOne` | `revoked_tokens` | `createdAt`, `expiresAt`, `tokenHash` | `auth` | MEDIUM | global-by-design | Collection 'revoked_tokens' maps to struct 'RevokedToken' which does NOT declare a tena... |
| 470 | `Logout` | `UpdateMany` | `refresh_tokens` | `tokenHash`, `userId` | `auth` | MEDIUM | global-by-design | Collection 'refresh_tokens' maps to struct 'RefreshToken' which does NOT declare a tena... |
| 503 | `Refresh` | `FindOne` | `refresh_tokens` | `tokenHash` | `auth` | MEDIUM | global-by-design | Collection 'refresh_tokens' maps to struct 'RefreshToken' which does NOT declare a tena... |
| 514 | `Refresh` | `UpdateMany` | `refresh_tokens` | `familyId` | `auth` | MEDIUM | global-by-design | Collection 'refresh_tokens' maps to struct 'RefreshToken' which does NOT declare a tena... |
| 525 | `Refresh` | `UpdateOne` | `refresh_tokens` | `_id` | `auth` | MEDIUM | global-by-design | Collection 'refresh_tokens' maps to struct 'RefreshToken' which does NOT declare a tena... |
| 537 | `Refresh` | `FindOne` | `users` | `_id`, `isActive` | `auth` | MEDIUM | global-by-design | Collection 'users' maps to struct 'User' which does NOT declare a tenantId bson field —... |
| 555 | `Refresh` | `UpdateOne` | `refresh_tokens` | `tokenHash` | `auth` | MEDIUM | global-by-design | Collection 'refresh_tokens' maps to struct 'RefreshToken' which does NOT declare a tena... |
| 601 | `VerifyEmail` | `FindOneAndUpdate` | `verification_tokens` | `token`, `type`, `usedAt`, `expiresAt` | `auth` | MEDIUM | global-by-design | Collection 'verification_tokens' maps to struct 'VerificationToken' which does NOT decl... |
| 616 | `VerifyEmail` | `UpdateOne` | `users` | `_id` | `auth` | MEDIUM | global-by-design | Collection 'users' maps to struct 'User' which does NOT declare a tenantId bson field —... |
| 651 | `ResendVerification` | `FindOne` | `users` | `email` | `auth` | MEDIUM | global-by-design | Collection 'users' maps to struct 'User' which does NOT declare a tenantId bson field —... |
| 691 | `ForgotPassword` | `FindOne` | `users` | `email` | `auth` | MEDIUM | global-by-design | Collection 'users' maps to struct 'User' which does NOT declare a tenantId bson field —... |
| 696 | `ForgotPassword` | `UpdateMany` | `verification_tokens` | `userId`, `type`, `usedAt` | `auth` | MEDIUM | global-by-design | Collection 'verification_tokens' maps to struct 'VerificationToken' which does NOT decl... |
| 711 | `ForgotPassword` | `InsertOne` | `verification_tokens` | `createdAt`, `expiresAt`, `token`, `type`, `usedAt`, `userId` | `auth` | MEDIUM | global-by-design | Collection 'verification_tokens' maps to struct 'VerificationToken' which does NOT decl... |
| 746 | `ResetPassword` | `FindOneAndUpdate` | `verification_tokens` | `token`, `type`, `usedAt`, `expiresAt` | `auth` | MEDIUM | global-by-design | Collection 'verification_tokens' maps to struct 'VerificationToken' which does NOT decl... |
| 767 | `ResetPassword` | `UpdateOne` | `users` | `_id` | `auth` | MEDIUM | global-by-design | Collection 'users' maps to struct 'User' which does NOT declare a tenantId bson field —... |
| 777 | `ResetPassword` | `UpdateMany` | `refresh_tokens` | `userId`, `isRevoked` | `auth` | MEDIUM | global-by-design | Collection 'refresh_tokens' maps to struct 'RefreshToken' which does NOT declare a tena... |
| 837 | `ChangePassword` | `UpdateOne` | `users` | `_id` | `auth` | MEDIUM | global-by-design | Collection 'users' maps to struct 'User' which does NOT declare a tenantId bson field —... |
| 844 | `ChangePassword` | `UpdateMany` | `refresh_tokens` | `userId`, `isRevoked` | `auth` | MEDIUM | global-by-design | Collection 'refresh_tokens' maps to struct 'RefreshToken' which does NOT declare a tena... |
| 889 | `MFASetup` | `UpdateOne` | `users` | `_id` | `auth` | MEDIUM | global-by-design | Collection 'users' maps to struct 'User' which does NOT declare a tenantId bson field —... |
| 920 | `MFAVerifySetup` | `FindOne` | `users` | `_id` | `auth` | MEDIUM | global-by-design | Collection 'users' maps to struct 'User' which does NOT declare a tenantId bson field —... |
| 944 | `MFAVerifySetup` | `UpdateOne` | `users` | `_id` | `auth` | MEDIUM | global-by-design | Collection 'users' maps to struct 'User' which does NOT declare a tenantId bson field —... |
| 981 | `MFADisable` | `FindOne` | `users` | `_id` | `auth` | MEDIUM | global-by-design | Collection 'users' maps to struct 'User' which does NOT declare a tenantId bson field —... |
| 1001 | `MFADisable` | `UpdateOne` | `users` | `_id` | `auth` | MEDIUM | global-by-design | Collection 'users' maps to struct 'User' which does NOT declare a tenantId bson field —... |
| 1051 | `MFAChallenge` | `FindOne` | `users` | `_id` | `auth` | MEDIUM | global-by-design | Collection 'users' maps to struct 'User' which does NOT declare a tenantId bson field —... |
| 1071 | `MFAChallenge` | `UpdateOne` | `users` | `_id` | `auth` | MEDIUM | global-by-design | Collection 'users' maps to struct 'User' which does NOT declare a tenantId bson field —... |
| 1127 | `MFARegenerateRecoveryCodes` | `FindOne` | `users` | `_id` | `auth` | MEDIUM | global-by-design | Collection 'users' maps to struct 'User' which does NOT declare a tenantId bson field —... |
| 1148 | `MFARegenerateRecoveryCodes` | `UpdateOne` | `users` | `_id` | `auth` | MEDIUM | global-by-design | Collection 'users' maps to struct 'User' which does NOT declare a tenantId bson field —... |
| 1190 | `MagicLinkRequest` | `FindOne` | `users` | `email` | `auth` | MEDIUM | global-by-design | Collection 'users' maps to struct 'User' which does NOT declare a tenantId bson field —... |
| 1204 | `MagicLinkRequest` | `InsertOne` | `verification_tokens` | `createdAt`, `expiresAt`, `token`, `type`, `usedAt`, `userId` | `auth` | MEDIUM | global-by-design | Collection 'verification_tokens' maps to struct 'VerificationToken' which does NOT decl... |
| 1236 | `MagicLinkVerify` | `FindOneAndUpdate` | `verification_tokens` | `token`, `type`, `usedAt`, `expiresAt` | `auth` | MEDIUM | global-by-design | Collection 'verification_tokens' maps to struct 'VerificationToken' which does NOT decl... |
| 1252 | `MagicLinkVerify` | `FindOne` | `users` | `_id`, `isActive` | `auth` | MEDIUM | global-by-design | Collection 'users' maps to struct 'User' which does NOT declare a tenantId bson field —... |
| 1258 | `MagicLinkVerify` | `UpdateOne` | `users` | `_id` | `auth` | MEDIUM | global-by-design | Collection 'users' maps to struct 'User' which does NOT declare a tenantId bson field —... |
| 1315 | `createAuthCodeRedirect` | `InsertOne` | `auth_codes` | `code`, `createdAt`, `expiresAt`, `tokenData`, `usedAt`, `userId` | `auth` | MEDIUM | global-by-design | Collection 'auth_codes' maps to struct 'AuthCode' which does NOT declare a tenantId bso... |
| 1336 | `ExchangeCode` | `FindOneAndUpdate` | `auth_codes` | `code`, `usedAt`, `expiresAt` | `auth` | MEDIUM | global-by-design | Collection 'auth_codes' maps to struct 'AuthCode' which does NOT declare a tenantId bso... |
| 1374 | `GoogleOAuth` | `InsertOne` | `oauth_states` | `createdAt`, `expiresAt`, `state` | `auth` | MEDIUM | global-by-design | Collection 'oauth_states' maps to struct 'OAuthState' which does NOT declare a tenantId... |
| 1398 | `GoogleOAuthCallback` | `FindOneAndDelete` | `oauth_states` | `state`, `expiresAt` | `auth` | MEDIUM | global-by-design | Collection 'oauth_states' maps to struct 'OAuthState' which does NOT declare a tenantId... |
| 1423 | `GoogleOAuthCallback` | `FindOne` | `users` | `googleId` | `auth` | MEDIUM | global-by-design | Collection 'users' maps to struct 'User' which does NOT declare a tenantId bson field —... |
| 1425 | `GoogleOAuthCallback` | `FindOne` | `users` | `email` | `auth` | MEDIUM | global-by-design | Collection 'users' maps to struct 'User' which does NOT declare a tenantId bson field —... |
| 1440 | `GoogleOAuthCallback` | `InsertOne` | `users` | `accountLockedUntil`, `authMethods`, `createdAt`, `displayName`, `email`, `emailVerified`, `failedLoginAttempts`, `githubId`, `googleId`, `isActive`, `lastLoginAt`, `lastVerificationSent`, `microsoftId`, `onboardingCompletedAt`, `passwordHash`, `recoveryCodes`, `themePreference`, `totpEnabled`, `totpSecret`, `totpVerifiedAt`, `trialUsedAt`, `updatedAt` | `auth` | MEDIUM | global-by-design | Collection 'users' maps to struct 'User' which does NOT declare a tenantId bson field —... |
| 1448 | `GoogleOAuthCallback` | `UpdateOne` | `users` | `_id` | `auth` | MEDIUM | global-by-design | Collection 'users' maps to struct 'User' which does NOT declare a tenantId bson field —... |
| 1454 | `GoogleOAuthCallback` | `UpdateOne` | `users` | `_id` | `auth` | MEDIUM | global-by-design | Collection 'users' maps to struct 'User' which does NOT declare a tenantId bson field —... |
| 1507 | `GitHubOAuth` | `InsertOne` | `oauth_states` | `createdAt`, `expiresAt`, `state` | `auth` | MEDIUM | global-by-design | Collection 'oauth_states' maps to struct 'OAuthState' which does NOT declare a tenantId... |
| 1531 | `GitHubOAuthCallback` | `FindOneAndDelete` | `oauth_states` | `state`, `expiresAt` | `auth` | MEDIUM | global-by-design | Collection 'oauth_states' maps to struct 'OAuthState' which does NOT declare a tenantId... |
| 1557 | `GitHubOAuthCallback` | `FindOne` | `users` | `githubId` | `auth` | MEDIUM | global-by-design | Collection 'users' maps to struct 'User' which does NOT declare a tenantId bson field —... |
| 1559 | `GitHubOAuthCallback` | `FindOne` | `users` | `email` | `auth` | MEDIUM | global-by-design | Collection 'users' maps to struct 'User' which does NOT declare a tenantId bson field —... |
| 1578 | `GitHubOAuthCallback` | `InsertOne` | `users` | `accountLockedUntil`, `authMethods`, `createdAt`, `displayName`, `email`, `emailVerified`, `failedLoginAttempts`, `githubId`, `googleId`, `isActive`, `lastLoginAt`, `lastVerificationSent`, `microsoftId`, `onboardingCompletedAt`, `passwordHash`, `recoveryCodes`, `themePreference`, `totpEnabled`, `totpSecret`, `totpVerifiedAt`, `trialUsedAt`, `updatedAt` | `auth` | MEDIUM | global-by-design | Collection 'users' maps to struct 'User' which does NOT declare a tenantId bson field —... |
| 1591 | `GitHubOAuthCallback` | `UpdateOne` | `users` | `_id` | `auth` | MEDIUM | global-by-design | Collection 'users' maps to struct 'User' which does NOT declare a tenantId bson field —... |
| 1597 | `GitHubOAuthCallback` | `UpdateOne` | `users` | `_id` | `auth` | MEDIUM | global-by-design | Collection 'users' maps to struct 'User' which does NOT declare a tenantId bson field —... |
| 1649 | `MicrosoftOAuth` | `InsertOne` | `oauth_states` | `createdAt`, `expiresAt`, `state` | `auth` | MEDIUM | global-by-design | Collection 'oauth_states' maps to struct 'OAuthState' which does NOT declare a tenantId... |
| 1673 | `MicrosoftOAuthCallback` | `FindOneAndDelete` | `oauth_states` | `state`, `expiresAt` | `auth` | MEDIUM | global-by-design | Collection 'oauth_states' maps to struct 'OAuthState' which does NOT declare a tenantId... |
| 1704 | `MicrosoftOAuthCallback` | `FindOne` | `users` | `microsoftId` | `auth` | MEDIUM | global-by-design | Collection 'users' maps to struct 'User' which does NOT declare a tenantId bson field —... |
| 1706 | `MicrosoftOAuthCallback` | `FindOne` | `users` | `email` | `auth` | MEDIUM | global-by-design | Collection 'users' maps to struct 'User' which does NOT declare a tenantId bson field —... |
| 1725 | `MicrosoftOAuthCallback` | `InsertOne` | `users` | `accountLockedUntil`, `authMethods`, `createdAt`, `displayName`, `email`, `emailVerified`, `failedLoginAttempts`, `githubId`, `googleId`, `isActive`, `lastLoginAt`, `lastVerificationSent`, `microsoftId`, `onboardingCompletedAt`, `passwordHash`, `recoveryCodes`, `themePreference`, `totpEnabled`, `totpSecret`, `totpVerifiedAt`, `trialUsedAt`, `updatedAt` | `auth` | MEDIUM | global-by-design | Collection 'users' maps to struct 'User' which does NOT declare a tenantId bson field —... |
| 1738 | `MicrosoftOAuthCallback` | `UpdateOne` | `users` | `_id` | `auth` | MEDIUM | global-by-design | Collection 'users' maps to struct 'User' which does NOT declare a tenantId bson field —... |
| 1744 | `MicrosoftOAuthCallback` | `UpdateOne` | `users` | `_id` | `auth` | MEDIUM | global-by-design | Collection 'users' maps to struct 'User' which does NOT declare a tenantId bson field —... |
| 1790 | `ListSessions` | `Find` | `refresh_tokens` | `userId`, `isRevoked`, `expiresAt` | `auth` | MEDIUM | global-by-design | Collection 'refresh_tokens' maps to struct 'RefreshToken' which does NOT declare a tena... |
| 1861 | `RevokeSession` | `UpdateOne` | `refresh_tokens` | `_id`, `userId` | `auth` | MEDIUM | global-by-design | Collection 'refresh_tokens' maps to struct 'RefreshToken' which does NOT declare a tena... |
| 1881 | `RevokeAllSessions` | `UpdateMany` | `refresh_tokens` | `userId`, `isRevoked` | `auth` | MEDIUM | global-by-design | Collection 'refresh_tokens' maps to struct 'RefreshToken' which does NOT declare a tena... |
| 1922 | `UpdatePreferences` | `UpdateOne` | `users` | `_id` | `auth` | MEDIUM | global-by-design | Collection 'users' maps to struct 'User' which does NOT declare a tenantId bson field —... |
| 1937 | `CompleteOnboarding` | `UpdateOne` | `users` | `_id` | `auth` | MEDIUM | global-by-design | Collection 'users' maps to struct 'User' which does NOT declare a tenantId bson field —... |
| 1991 | `createPersonalTenant` | `InsertOne` | `tenants` | `billingInterval`, `billingStatus`, `billingWaived`, `canceledAt`, `createdAt`, `currentPeriodEnd`, `isActive`, `isRoot`, `name`, `planId`, `purchasedCredits`, `seatQuantity`, `slug`, `stripeCustomerId`, `stripeSubscriptionId`, `subscriptionCredits`, `trialUsedAt`, `updatedAt` | `unknown` | MEDIUM | global-by-design | Collection 'tenants' maps to struct 'Tenant' which does NOT declare a tenantId bson fie... |
| 2004 | `createPersonalTenant` | `InsertOne` | `tenant_memberships` | `joinedAt`, `role`, `tenantId`, `updatedAt`, `userId` | `unknown` | OK |  | Filter contains tenantId. |
| 2026 | `sendVerificationEmail` | `InsertOne` | `verification_tokens` | `createdAt`, `expiresAt`, `token`, `type`, `usedAt`, `userId` | `auth` | MEDIUM | global-by-design | Collection 'verification_tokens' maps to struct 'VerificationToken' which does NOT decl... |
| 2029 | `sendVerificationEmail` | `UpdateOne` | `users` | `_id` | `auth` | MEDIUM | global-by-design | Collection 'users' maps to struct 'User' which does NOT declare a tenantId bson field —... |
| 2048 | `getUserMemberships` | `Find` | `tenant_memberships` | `userId` | `auth` | OK | user-scoped | Collection 'tenant_memberships' is user-scoped (has userId field) and the filter contai... |
| 2068 | `getUserMemberships` | `Find` | `tenants` | `_id` | `auth` | MEDIUM | global-by-design | Collection 'tenants' maps to struct 'Tenant' which does NOT declare a tenantId bson fie... |
| 2107 | `acceptInvitationForUser` | `FindOne` | `invitations` | `token`, `status`, `expiresAt` | `auth` | MEDIUM | auth-flow | Auth-flow handler 'acceptInvitationForUser' operates on user-scoped collections (the us... |
| 2118 | `acceptInvitationForUser` | `FindOne` | `users` | `_id` | `auth` | MEDIUM | global-by-design | Collection 'users' maps to struct 'User' which does NOT declare a tenantId bson field —... |
| 2126 | `acceptInvitationForUser` | `FindOneAndUpdate` | `invitations` | `_id`, `status` | `auth` | MEDIUM | auth-flow | Auth-flow handler 'acceptInvitationForUser' operates on user-scoped collections (the us... |
| 2138 | `acceptInvitationForUser` | `CountDocuments` | `tenant_memberships` | `userId`, `tenantId` | `auth` | OK |  | Filter contains tenantId. |
| 2154 | `acceptInvitationForUser` | `InsertOne` | `tenant_memberships` | `joinedAt`, `role`, `tenantId`, `updatedAt`, `userId` | `auth` | OK |  | Filter contains tenantId. |
| 2160 | `acceptInvitationForUser` | `UpdateOne` | `users` | `_id` | `auth` | MEDIUM | global-by-design | Collection 'users' maps to struct 'User' which does NOT declare a tenantId bson field —... |
| 2191 | `storeRefreshToken` | `CountDocuments` | `refresh_tokens` | `userId`, `isRevoked`, `expiresAt` | `auth` | MEDIUM | global-by-design | Collection 'refresh_tokens' maps to struct 'RefreshToken' which does NOT declare a tena... |
| 2199 | `storeRefreshToken` | `Find` | `refresh_tokens` | `userId`, `isRevoked`, `expiresAt` | `auth` | MEDIUM | global-by-design | Collection 'refresh_tokens' maps to struct 'RefreshToken' which does NOT declare a tena... |
| 2208 | `storeRefreshToken` | `UpdateByID` | `refresh_tokens` | `_id` | `auth` | MEDIUM | global-by-design | Collection 'refresh_tokens' maps to struct 'RefreshToken' which does NOT declare a tena... |
| 2229 | `storeRefreshToken` | `InsertOne` | `refresh_tokens` | `createdAt`, `deviceInfo`, `expiresAt`, `familyId`, `ipAddress`, `isRevoked`, `lastActiveAt`, `tokenHash`, `userAgent`, `userId` | `auth` | MEDIUM | global-by-design | Collection 'refresh_tokens' maps to struct 'RefreshToken' which does NOT declare a tena... |
| 2266 | `DeleteAccount` | `Find` | `tenant_memberships` | `userId` | `auth` | OK | user-scoped | Collection 'tenant_memberships' is user-scoped (has userId field) and the filter contai... |
| 2286 | `DeleteAccount` | `FindOne` | `tenants` | `_id` | `auth` | MEDIUM | global-by-design | Collection 'tenants' maps to struct 'Tenant' which does NOT declare a tenantId bson fie... |
| 2295 | `DeleteAccount` | `CountDocuments` | `tenant_memberships` | `tenantId`, `userId` | `auth` | OK |  | Filter contains tenantId. |
| 2305 | `DeleteAccount` | `DeleteMany` | `tenant_memberships` | `tenantId` | `auth` | OK |  | Filter contains tenantId. |
| 2308 | `DeleteAccount` | `DeleteOne` | `tenants` | `_id` | `auth` | MEDIUM | global-by-design | Collection 'tenants' maps to struct 'Tenant' which does NOT declare a tenantId bson fie... |
| 2311 | `DeleteAccount` | `DeleteMany` | `invitations` | `tenantId` | `auth` | OK |  | Filter contains tenantId. |
| 2327 | `DeleteAccount` | `DeleteMany` | `tenant_memberships` | `userId` | `auth` | OK | user-scoped | Collection 'tenant_memberships' is user-scoped (has userId field) and the filter contai... |
| 2330 | `DeleteAccount` | `DeleteMany` | `refresh_tokens` | `userId` | `auth` | MEDIUM | global-by-design | Collection 'refresh_tokens' maps to struct 'RefreshToken' which does NOT declare a tena... |
| 2333 | `DeleteAccount` | `DeleteMany` | `messages` | `userId` | `auth` | MEDIUM | global-by-design | Collection 'messages' maps to struct 'Message' which does NOT declare a tenantId bson f... |
| 2336 | `DeleteAccount` | `DeleteOne` | `users` | `_id` | `auth` | MEDIUM | global-by-design | Collection 'users' maps to struct 'User' which does NOT declare a tenantId bson field —... |
| 2366 | `ExportData` | `Find` | `tenant_memberships` | `userId` | `auth` | OK | user-scoped | Collection 'tenant_memberships' is user-scoped (has userId field) and the filter contai... |
| 2388 | `ExportData` | `Find` | `messages` | `userId` | `auth` | MEDIUM | global-by-design | Collection 'messages' maps to struct 'Message' which does NOT declare a tenantId bson f... |


### `backend/internal/api/handlers/billing.go`

| Line | Function | Op | Collection | Filter | Scope | Risk | Suppression | Note |
|------|----------|----|------------|--------|-------|------|-------------|------|
| 94 | `Checkout` | `FindOne` | `plans` | `_id` | `tenant` | MEDIUM | global-by-design | Collection 'plans' maps to struct 'Plan' which does NOT declare a tenantId bson field —... |
| 122 | `Checkout` | `UpdateOne` | `tenants` | `_id` | `tenant` | MEDIUM | global-by-design | Collection 'tenants' maps to struct 'Tenant' which does NOT declare a tenantId bson fie... |
| 138 | `Checkout` | `CountDocuments` | `tenant_memberships` | `tenantId` | `tenant` | OK |  | Filter contains tenantId. |
| 152 | `Checkout` | `UpdateOne` | `tenants` | `_id` | `tenant` | MEDIUM | global-by-design | Collection 'tenants' maps to struct 'Tenant' which does NOT declare a tenantId bson fie... |
| 162 | `Checkout` | `CountDocuments` | `tenant_memberships` | `tenantId` | `tenant` | OK |  | Filter contains tenantId. |
| 313 | `Checkout` | `FindOne` | `credit_bundles` | `_id`, `isActive` | `tenant` | MEDIUM | global-by-design | Collection 'credit_bundles' maps to struct 'CreditBundle' which does NOT declare a tena... |
| 406 | `ListTransactions` | `CountDocuments` | `financial_transactions` | `tenantId` | `tenant` | OK |  | Filter contains tenantId. |
| 417 | `ListTransactions` | `Find` | `financial_transactions` | `tenantId` | `tenant` | OK |  | Filter contains tenantId. |
| 457 | `GetInvoice` | `FindOne` | `financial_transactions` | `_id`, `tenantId` | `tenant` | OK |  | Filter contains tenantId. |
| 486 | `GetInvoicePDF` | `FindOne` | `financial_transactions` | `_id`, `tenantId` | `tenant` | OK |  | Filter contains tenantId. |
| 657 | `CancelSubscription` | `UpdateOne` | `tenants` | `_id` | `tenant` | MEDIUM | global-by-design | Collection 'tenants' maps to struct 'Tenant' which does NOT declare a tenantId bson fie... |
| 736 | `AdminListTransactions` | `CountDocuments` | `financial_transactions` | `$or`, `tenantId` | `admin` | OK |  | Filter contains tenantId. |
| 747 | `AdminListTransactions` | `Find` | `financial_transactions` | `$or`, `tenantId` | `admin` | OK |  | Filter contains tenantId. |
| 804 | `AdminGetMetrics` | `Find` | `daily_metrics` | `date` | `admin` | MEDIUM | admin-handler | Function 'AdminGetMetrics' is an admin handler (registered on /api/admin/*). Admin hand... |
| 896 | `computeLiveRevenue` | `Aggregate` | `financial_transactions` | `createdAt` | `background` | MEDIUM | background-task | Function 'computeLiveRevenue' is a background system task (no request context, no tenan... |
| 932 | `computeLiveARR` | `Aggregate` | `tenants` | `billingStatus`, `planId` | `unknown` | MEDIUM | global-by-design | Collection 'tenants' maps to struct 'Tenant' which does NOT declare a tenantId bson fie... |
| 958 | `AdminCancelSubscription` | `FindOne` | `tenants` | `_id` | `admin` | MEDIUM | admin-handler | Function 'AdminCancelSubscription' is an admin handler (registered on /api/admin/*). Ad... |
| 1004 | `AdminCancelSubscription` | `UpdateOne` | `tenants` | `_id` | `admin` | MEDIUM | admin-handler | Function 'AdminCancelSubscription' is an admin handler (registered on /api/admin/*). Ad... |
| 1037 | `AdminUpdateSubscription` | `UpdateOne` | `tenants` | `_id` | `admin` | MEDIUM | admin-handler | Function 'AdminUpdateSubscription' is an admin handler (registered on /api/admin/*). Ad... |


### `backend/internal/api/handlers/bootstrap.go`

| Line | Function | Op | Collection | Filter | Scope | Risk | Suppression | Note |
|------|----------|----|------------|--------|-------|------|-------------|------|
| 36 | `refreshInitialized` | `FindOne` | `system_config` | — | `unknown` | MEDIUM | global-by-design | Collection 'system_config' maps to struct 'SystemConfig' which does NOT declare a tenan... |
| 66 | `refreshInitializedFromContext` | `FindOne` | `system_config` | — | `unknown` | MEDIUM | global-by-design | Collection 'system_config' maps to struct 'SystemConfig' which does NOT declare a tenan... |


### `backend/internal/api/handlers/branding.go`

| Line | Function | Op | Collection | Filter | Scope | Risk | Suppression | Note |
|------|----------|----|------------|--------|-------|------|-------------|------|
| 45 | `GetBranding` | `FindOne` | `branding_config` | — | `public` | MEDIUM | public-endpoint | Function 'GetBranding' is a public endpoint (no auth) — returns published/global conten... |
| 60 | `GetBranding` | `FindOne` | `branding_assets` | `key` | `public` | MEDIUM | public-endpoint | Function 'GetBranding' is a public endpoint (no auth) — returns published/global conten... |
| 64 | `GetBranding` | `FindOne` | `branding_assets` | `key` | `public` | MEDIUM | public-endpoint | Function 'GetBranding' is a public endpoint (no auth) — returns published/global conten... |
| 119 | `ServeAsset` | `FindOne` | `branding_assets` | `key` | `public` | MEDIUM | public-endpoint | Function 'ServeAsset' is a public endpoint (no auth) — returns published/global content... |
| 141 | `ServeMedia` | `FindOne` | `branding_assets` | `key` | `public` | MEDIUM | public-endpoint | Function 'ServeMedia' is a public endpoint (no auth) — returns published/global content... |
| 163 | `GetPublicPage` | `FindOne` | `custom_pages` | `slug`, `isPublished` | `public` | MEDIUM | public-endpoint | Function 'GetPublicPage' is a public endpoint (no auth) — returns published/global cont... |
| 182 | `ListPublicPages` | `Find` | `custom_pages` | `isPublished` | `public` | MEDIUM | public-endpoint | Function 'ListPublicPages' is a public endpoint (no auth) — returns published/global co... |
| 262 | `UpdateBranding` | `UpdateOne` | `branding_config` | — | `admin` | MEDIUM | admin-handler | Function 'UpdateBranding' is an admin handler (registered on /api/admin/*). Admin handl... |
| 324 | `UploadAsset` | `UpdateOne` | `branding_assets` | `key` | `admin` | MEDIUM | admin-handler | Function 'UploadAsset' is an admin handler (registered on /api/admin/*). Admin handlers... |
| 348 | `DeleteAsset` | `DeleteOne` | `branding_assets` | `key` | `admin` | MEDIUM | admin-handler | Function 'DeleteAsset' is an admin handler (registered on /api/admin/*). Admin handlers... |
| 368 | `ListMedia` | `Find` | `branding_assets` | `key` | `admin` | MEDIUM | admin-handler | Function 'ListMedia' is an admin handler (registered on /api/admin/*). Admin handlers s... |
| 460 | `UploadMedia` | `InsertOne` | `branding_assets` | `contentType`, `createdAt`, `data`, `filename`, `key`, `size` | `admin` | MEDIUM | admin-handler | Function 'UploadMedia' is an admin handler (registered on /api/admin/*). Admin handlers... |
| 487 | `DeleteMedia` | `DeleteOne` | `branding_assets` | `key` | `admin` | MEDIUM | admin-handler | Function 'DeleteMedia' is an admin handler (registered on /api/admin/*). Admin handlers... |
| 505 | `AdminListPages` | `Find` | `custom_pages` | — | `admin` | MEDIUM | admin-handler | Function 'AdminListPages' is an admin handler (registered on /api/admin/*). Admin handl... |
| 543 | `CreatePage` | `InsertOne` | `custom_pages` | — | `admin` | MEDIUM | admin-handler | Function 'CreatePage' is an admin handler (registered on /api/admin/*). Admin handlers ... |
| 590 | `UpdatePage` | `UpdateByID` | `custom_pages` | `_id` | `admin` | MEDIUM | admin-handler | Function 'UpdatePage' is an admin handler (registered on /api/admin/*). Admin handlers ... |
| 616 | `DeletePage` | `DeleteOne` | `custom_pages` | `_id` | `admin` | MEDIUM | admin-handler | Function 'DeletePage' is an admin handler (registered on /api/admin/*). Admin handlers ... |


### `backend/internal/api/handlers/bundles.go`

| Line | Function | Op | Collection | Filter | Scope | Risk | Suppression | Note |
|------|----------|----|------------|--------|-------|------|-------------|------|
| 60 | `ListBundles` | `Find` | `credit_bundles` | — | `admin` | MEDIUM | admin-handler | Function 'ListBundles' is an admin handler (registered on /api/admin/*). Admin handlers... |
| 75 | `ListBundles` | `CountDocuments` | `credit_bundles` | — | `admin` | MEDIUM | admin-handler | Function 'ListBundles' is an admin handler (registered on /api/admin/*). Admin handlers... |
| 96 | `CreateBundle` | `CountDocuments` | `credit_bundles` | `name` | `admin` | MEDIUM | admin-handler | Function 'CreateBundle' is an admin handler (registered on /api/admin/*). Admin handler... |
| 117 | `CreateBundle` | `InsertOne` | `credit_bundles` | `createdAt`, `credits`, `isActive`, `name`, `priceCents`, `sortOrder`, `updatedAt` | `admin` | MEDIUM | admin-handler | Function 'CreateBundle' is an admin handler (registered on /api/admin/*). Admin handler... |
| 145 | `UpdateBundle` | `FindOne` | `credit_bundles` | `_id` | `admin` | MEDIUM | admin-handler | Function 'UpdateBundle' is an admin handler (registered on /api/admin/*). Admin handler... |
| 166 | `UpdateBundle` | `CountDocuments` | `credit_bundles` | `name`, `_id` | `admin` | MEDIUM | admin-handler | Function 'UpdateBundle' is an admin handler (registered on /api/admin/*). Admin handler... |
| 186 | `UpdateBundle` | `UpdateByID` | `credit_bundles` | `_id` | `admin` | MEDIUM | admin-handler | Function 'UpdateBundle' is an admin handler (registered on /api/admin/*). Admin handler... |
| 196 | `UpdateBundle` | `FindOne` | `credit_bundles` | `_id` | `admin` | MEDIUM | admin-handler | Function 'UpdateBundle' is an admin handler (registered on /api/admin/*). Admin handler... |
| 212 | `DeleteBundle` | `FindOne` | `credit_bundles` | `_id` | `admin` | MEDIUM | admin-handler | Function 'DeleteBundle' is an admin handler (registered on /api/admin/*). Admin handler... |
| 221 | `DeleteBundle` | `DeleteOne` | `credit_bundles` | `_id` | `admin` | MEDIUM | admin-handler | Function 'DeleteBundle' is an admin handler (registered on /api/admin/*). Admin handler... |
| 237 | `ListBundlesPublic` | `Find` | `credit_bundles` | `isActive` | `public` | MEDIUM | public-endpoint | Function 'ListBundlesPublic' is a public endpoint (no auth) — returns published/global ... |


### `backend/internal/api/handlers/config.go`

| Line | Function | Op | Collection | Filter | Scope | Risk | Suppression | Note |
|------|----------|----|------------|--------|-------|------|-------------|------|
| 94 | `UpdateConfig` | `UpdateOne` | `config_vars` | `name` | `admin` | MEDIUM | admin-handler | Function 'UpdateConfig' is an admin handler (registered on /api/admin/*). Admin handler... |
| 162 | `CreateConfig` | `InsertOne` | `config_vars` | `createdAt`, `description`, `isSystem`, `name`, `options`, `type`, `updatedAt`, `value` | `admin` | MEDIUM | admin-handler | Function 'CreateConfig' is an admin handler (registered on /api/admin/*). Admin handler... |
| 192 | `DeleteConfig` | `DeleteOne` | `config_vars` | `name` | `admin` | MEDIUM | admin-handler | Function 'DeleteConfig' is an admin handler (registered on /api/admin/*). Admin handler... |


### `backend/internal/api/handlers/event_definitions.go`

| Line | Function | Op | Collection | Filter | Scope | Risk | Suppression | Note |
|------|----------|----|------------|--------|-------|------|-------------|------|
| 50 | `ListEventDefinitions` | `Find` | `event_definitions` | — | `admin` | MEDIUM | admin-handler | Function 'ListEventDefinitions' is an admin handler (registered on /api/admin/*). Admin... |
| 85 | `ListEventDefinitions` | `Aggregate` | `telemetry_events` | — | `admin` | MEDIUM | admin-handler | Function 'ListEventDefinitions' is an admin handler (registered on /api/admin/*). Admin... |
| 135 | `CreateEventDefinition` | `CountDocuments` | `event_definitions` | `name` | `admin` | MEDIUM | admin-handler | Function 'CreateEventDefinition' is an admin handler (registered on /api/admin/*). Admi... |
| 161 | `CreateEventDefinition` | `CountDocuments` | `event_definitions` | `_id` | `admin` | MEDIUM | admin-handler | Function 'CreateEventDefinition' is an admin handler (registered on /api/admin/*). Admi... |
| 173 | `CreateEventDefinition` | `InsertOne` | `event_definitions` | `createdAt`, `description`, `name`, `parentId`, `updatedAt` | `admin` | MEDIUM | admin-handler | Function 'CreateEventDefinition' is an admin handler (registered on /api/admin/*). Admi... |
| 212 | `UpdateEventDefinition` | `FindOne` | `event_definitions` | `_id` | `admin` | MEDIUM | admin-handler | Function 'UpdateEventDefinition' is an admin handler (registered on /api/admin/*). Admi... |
| 219 | `UpdateEventDefinition` | `CountDocuments` | `event_definitions` | `name`, `_id` | `admin` | MEDIUM | admin-handler | Function 'UpdateEventDefinition' is an admin handler (registered on /api/admin/*). Admi... |
| 249 | `UpdateEventDefinition` | `CountDocuments` | `event_definitions` | `_id` | `admin` | MEDIUM | admin-handler | Function 'UpdateEventDefinition' is an admin handler (registered on /api/admin/*). Admi... |
| 269 | `UpdateEventDefinition` | `UpdateOne` | `event_definitions` | `_id` | `admin` | MEDIUM | admin-handler | Function 'UpdateEventDefinition' is an admin handler (registered on /api/admin/*). Admi... |
| 278 | `UpdateEventDefinition` | `FindOne` | `event_definitions` | `_id` | `admin` | MEDIUM | admin-handler | Function 'UpdateEventDefinition' is an admin handler (registered on /api/admin/*). Admi... |
| 296 | `DeleteEventDefinition` | `FindOne` | `event_definitions` | `_id` | `admin` | MEDIUM | admin-handler | Function 'DeleteEventDefinition' is an admin handler (registered on /api/admin/*). Admi... |
| 302 | `DeleteEventDefinition` | `UpdateMany` | `event_definitions` | `parentId` | `admin` | MEDIUM | admin-handler | Function 'DeleteEventDefinition' is an admin handler (registered on /api/admin/*). Admi... |
| 307 | `DeleteEventDefinition` | `DeleteOne` | `event_definitions` | `_id` | `admin` | MEDIUM | admin-handler | Function 'DeleteEventDefinition' is an admin handler (registered on /api/admin/*). Admi... |
| 321 | `GetSankeyData` | `Find` | `event_definitions` | — | `admin` | MEDIUM | admin-handler | Function 'GetSankeyData' is an admin handler (registered on /api/admin/*). Admin handle... |
| 399 | `GetSankeyData` | `Aggregate` | `telemetry_events` | — | `admin` | MEDIUM | admin-handler | Function 'GetSankeyData' is an admin handler (registered on /api/admin/*). Admin handle... |
| 463 | `wouldCreateCycle` | `FindOne` | `event_definitions` | `_id` | `unknown` | MEDIUM | global-by-design | Collection 'event_definitions' maps to struct 'EventDefinition' which does NOT declare ... |


### `backend/internal/api/handlers/logs.go`

| Line | Function | Op | Collection | Filter | Scope | Risk | Suppression | Note |
|------|----------|----|------------|--------|-------|------|-------------|------|
| 113 | `ListLogs` | `EstimatedDocumentCount` | `system_logs` | — | `admin` | MEDIUM | admin-handler | Function 'ListLogs' is an admin handler (registered on /api/admin/*). Admin handlers se... |
| 115 | `ListLogs` | `CountDocuments` | `system_logs` | — | `admin` | MEDIUM | admin-handler | Function 'ListLogs' is an admin handler (registered on /api/admin/*). Admin handlers se... |
| 127 | `ListLogs` | `Find` | `system_logs` | — | `admin` | MEDIUM | admin-handler | Function 'ListLogs' is an admin handler (registered on /api/admin/*). Admin handlers se... |
| 158 | `SeverityCounts` | `Aggregate` | `system_logs` | — | `admin` | MEDIUM | admin-handler | Function 'SeverityCounts' is an admin handler (registered on /api/admin/*). Admin handl... |
| 198 | `ExportCSV` | `Find` | `system_logs` | — | `admin` | MEDIUM | admin-handler | Function 'ExportCSV' is an admin handler (registered on /api/admin/*). Admin handlers s... |


### `backend/internal/api/handlers/messages.go`

| Line | Function | Op | Collection | Filter | Scope | Risk | Suppression | Note |
|------|----------|----|------------|--------|-------|------|-------------|------|
| 36 | `ListMessages` | `Find` | `messages` | `userId` | `auth` | MEDIUM | global-by-design | Collection 'messages' maps to struct 'Message' which does NOT declare a tenantId bson f... |
| 64 | `UnreadCount` | `CountDocuments` | `messages` | `userId`, `read` | `auth` | MEDIUM | global-by-design | Collection 'messages' maps to struct 'Message' which does NOT declare a tenantId bson f... |
| 88 | `MarkRead` | `UpdateOne` | `messages` | `_id`, `userId` | `auth` | MEDIUM | global-by-design | Collection 'messages' maps to struct 'Message' which does NOT declare a tenantId bson f... |


### `backend/internal/api/handlers/plans.go`

| Line | Function | Op | Collection | Filter | Scope | Risk | Suppression | Note |
|------|----------|----|------------|--------|-------|------|-------------|------|
| 48 | `ListPlans` | `Find` | `plans` | — | `admin` | MEDIUM | admin-handler | Function 'ListPlans' is an admin handler (registered on /api/admin/*). Admin handlers s... |
| 66 | `ListPlans` | `Aggregate` | `tenants` | — | `admin` | MEDIUM | admin-handler | Function 'ListPlans' is an admin handler (registered on /api/admin/*). Admin handlers s... |
| 93 | `ListPlans` | `CountDocuments` | `plans` | — | `admin` | MEDIUM | admin-handler | Function 'ListPlans' is an admin handler (registered on /api/admin/*). Admin handlers s... |
| 110 | `GetPlan` | `FindOne` | `plans` | `_id` | `admin` | MEDIUM | admin-handler | Function 'GetPlan' is an admin handler (registered on /api/admin/*). Admin handlers see... |
| 123 | `ListEntitlementKeys` | `Find` | `plans` | — | `admin` | MEDIUM | admin-handler | Function 'ListEntitlementKeys' is an admin handler (registered on /api/admin/*). Admin ... |
| 253 | `CreatePlan` | `CountDocuments` | `plans` | `name` | `admin` | MEDIUM | admin-handler | Function 'CreatePlan' is an admin handler (registered on /api/admin/*). Admin handlers ... |
| 295 | `CreatePlan` | `InsertOne` | `plans` | `annualDiscountPct`, `bonusCredits`, `createdAt`, `creditResetPolicy`, `description`, `entitlements`, `includedSeats`, `isArchived`, `isSystem`, `maxSeats`, `minSeats`, `monthlyPriceCents`, `name`, `perSeatPriceCents`, `pricingModel`, `trialDays`, `updatedAt`, `usageCreditsPerMonth`, `userLimit` | `admin` | MEDIUM | admin-handler | Function 'CreatePlan' is an admin handler (registered on /api/admin/*). Admin handlers ... |
| 323 | `UpdatePlan` | `FindOne` | `plans` | `_id` | `admin` | MEDIUM | admin-handler | Function 'UpdatePlan' is an admin handler (registered on /api/admin/*). Admin handlers ... |
| 350 | `UpdatePlan` | `CountDocuments` | `plans` | `name`, `_id` | `admin` | MEDIUM | admin-handler | Function 'UpdatePlan' is an admin handler (registered on /api/admin/*). Admin handlers ... |
| 368 | `UpdatePlan` | `DeleteMany` | `stripe_mappings` | `entityType` | `admin` | MEDIUM | admin-handler | Function 'UpdatePlan' is an admin handler (registered on /api/admin/*). Admin handlers ... |
| 393 | `UpdatePlan` | `UpdateByID` | `plans` | `_id` | `admin` | MEDIUM | admin-handler | Function 'UpdatePlan' is an admin handler (registered on /api/admin/*). Admin handlers ... |
| 404 | `UpdatePlan` | `FindOne` | `plans` | `_id` | `admin` | MEDIUM | admin-handler | Function 'UpdatePlan' is an admin handler (registered on /api/admin/*). Admin handlers ... |
| 408 | `UpdatePlan` | `CountDocuments` | `tenants` | `planId` | `admin` | MEDIUM | admin-handler | Function 'UpdatePlan' is an admin handler (registered on /api/admin/*). Admin handlers ... |
| 446 | `DeletePlan` | `FindOne` | `plans` | `_id` | `admin` | MEDIUM | admin-handler | Function 'DeletePlan' is an admin handler (registered on /api/admin/*). Admin handlers ... |
| 460 | `DeletePlan` | `CountDocuments` | `tenants` | `planId` | `admin` | MEDIUM | admin-handler | Function 'DeletePlan' is an admin handler (registered on /api/admin/*). Admin handlers ... |
| 470 | `DeletePlan` | `DeleteOne` | `plans` | `_id` | `admin` | MEDIUM | admin-handler | Function 'DeletePlan' is an admin handler (registered on /api/admin/*). Admin handlers ... |
| 491 | `ArchivePlan` | `FindOne` | `plans` | `_id` | `admin` | MEDIUM | admin-handler | Function 'ArchivePlan' is an admin handler (registered on /api/admin/*). Admin handlers... |
| 505 | `ArchivePlan` | `UpdateByID` | `plans` | `_id` | `admin` | MEDIUM | admin-handler | Function 'ArchivePlan' is an admin handler (registered on /api/admin/*). Admin handlers... |
| 526 | `UnarchivePlan` | `FindOne` | `plans` | `_id` | `admin` | MEDIUM | admin-handler | Function 'UnarchivePlan' is an admin handler (registered on /api/admin/*). Admin handle... |
| 540 | `UnarchivePlan` | `UpdateByID` | `plans` | `_id` | `admin` | MEDIUM | admin-handler | Function 'UnarchivePlan' is an admin handler (registered on /api/admin/*). Admin handle... |
| 576 | `AssignPlan` | `FindOne` | `tenants` | `_id` | `admin` | MEDIUM | admin-handler | Function 'AssignPlan' is an admin handler (registered on /api/admin/*). Admin handlers ... |
| 598 | `AssignPlan` | `FindOne` | `plans` | `_id` | `admin` | MEDIUM | admin-handler | Function 'AssignPlan' is an admin handler (registered on /api/admin/*). Admin handlers ... |
| 627 | `AssignPlan` | `FindOne` | `plans` | `_id` | `admin` | MEDIUM | admin-handler | Function 'AssignPlan' is an admin handler (registered on /api/admin/*). Admin handlers ... |
| 671 | `AssignPlan` | `UpdateByID` | `tenants` | `_id` | `admin` | MEDIUM | admin-handler | Function 'AssignPlan' is an admin handler (registered on /api/admin/*). Admin handlers ... |
| 703 | `ListPlansPublic` | `FindOne` | `tenants` | `_id` | `public` | MEDIUM | public-endpoint | Function 'ListPlansPublic' is a public endpoint (no auth) — returns published/global co... |
| 714 | `ListPlansPublic` | `CountDocuments` | `tenant_memberships` | `userId`, `tenantId` | `public` | OK |  | Filter contains tenantId. |
| 737 | `ListPlansPublic` | `Find` | `plans` | `isArchived` | `public` | MEDIUM | public-endpoint | Function 'ListPlansPublic' is a public endpoint (no auth) — returns published/global co... |
| 817 | `lookupPlanForTenant` | `FindOne` | `plans` | `_id` | `unknown` | MEDIUM | global-by-design | Collection 'plans' maps to struct 'Plan' which does NOT declare a tenantId bson field —... |
| 820 | `lookupPlanForTenant` | `FindOne` | `plans` | `isSystem` | `unknown` | MEDIUM | global-by-design | Collection 'plans' maps to struct 'Plan' which does NOT declare a tenantId bson field —... |


### `backend/internal/api/handlers/promotions.go`

| Line | Function | Op | Collection | Filter | Scope | Risk | Suppression | Note |
|------|----------|----|------------|--------|-------|------|-------------|------|
| 115 | `buildProductNameMap` | `Find` | `stripe_mappings` | — | `admin` | MEDIUM | admin-handler | Function 'buildProductNameMap' is an admin handler (registered on /api/admin/*). Admin ... |
| 146 | `buildProductNameMap` | `Find` | `plans` | `_id` | `admin` | MEDIUM | admin-handler | Function 'buildProductNameMap' is an admin handler (registered on /api/admin/*). Admin ... |
| 166 | `buildProductNameMap` | `Find` | `credit_bundles` | `_id` | `admin` | MEDIUM | admin-handler | Function 'buildProductNameMap' is an admin handler (registered on /api/admin/*). Admin ... |
| 200 | `ListEligibleProducts` | `Find` | `plans` | `isArchived` | `admin` | MEDIUM | admin-handler | Function 'ListEligibleProducts' is an admin handler (registered on /api/admin/*). Admin... |
| 226 | `ListEligibleProducts` | `Find` | `credit_bundles` | `isActive` | `admin` | MEDIUM | admin-handler | Function 'ListEligibleProducts' is an admin handler (registered on /api/admin/*). Admin... |
| 380 | `resolveStripeProducts` | `FindOne` | `plans` | `_id` | `admin` | MEDIUM | admin-handler | Function 'resolveStripeProducts' is an admin handler (registered on /api/admin/*). Admi... |
| 418 | `resolveStripeProducts` | `FindOne` | `stripe_mappings` | `entityType`, `entityId` | `admin` | MEDIUM | admin-handler | Function 'resolveStripeProducts' is an admin handler (registered on /api/admin/*). Admi... |
| 428 | `resolveStripeProducts` | `FindOne` | `credit_bundles` | `_id` | `admin` | MEDIUM | admin-handler | Function 'resolveStripeProducts' is an admin handler (registered on /api/admin/*). Admi... |
| 438 | `resolveStripeProducts` | `FindOne` | `stripe_mappings` | `entityType`, `entityId` | `admin` | MEDIUM | admin-handler | Function 'resolveStripeProducts' is an admin handler (registered on /api/admin/*). Admi... |


### `backend/internal/api/handlers/tenant.go`

| Line | Function | Op | Collection | Filter | Scope | Risk | Suppression | Note |
|------|----------|----|------------|--------|-------|------|-------------|------|
| 74 | `ListMembers` | `Find` | `tenant_memberships` | `tenantId` | `tenant` | OK |  | Filter contains tenantId. |
| 94 | `ListMembers` | `Find` | `users` | `_id` | `tenant` | MEDIUM | global-by-design | Collection 'users' maps to struct 'User' which does NOT declare a tenantId bson field —... |
| 171 | `InviteMember` | `FindOne` | `users` | `email` | `tenant` | MEDIUM | global-by-design | Collection 'users' maps to struct 'User' which does NOT declare a tenantId bson field —... |
| 172 | `InviteMember` | `CountDocuments` | `tenant_memberships` | `userId`, `tenantId` | `tenant` | OK |  | Filter contains tenantId. |
| 187 | `InviteMember` | `CountDocuments` | `invitations` | `tenantId`, `email`, `status`, `expiresAt` | `tenant` | OK |  | Filter contains tenantId. |
| 205 | `InviteMember` | `FindOne` | `plans` | `_id` | `tenant` | MEDIUM | global-by-design | Collection 'plans' maps to struct 'Plan' which does NOT declare a tenantId bson field —... |
| 209 | `InviteMember` | `FindOne` | `plans` | `isSystem` | `tenant` | MEDIUM | global-by-design | Collection 'plans' maps to struct 'Plan' which does NOT declare a tenantId bson field —... |
| 231 | `InviteMember` | `InsertOne` | `invitations` | `createdAt`, `email`, `expiresAt`, `invitedBy`, `role`, `status`, `tenantId`, `token` | `tenant` | OK |  | Filter contains tenantId. |
| 236 | `InviteMember` | `CountDocuments` | `tenant_memberships` | `tenantId` | `tenant` | OK |  | Filter contains tenantId. |
| 241 | `InviteMember` | `CountDocuments` | `invitations` | `tenantId`, `status`, `expiresAt` | `tenant` | OK |  | Filter contains tenantId. |
| 252 | `InviteMember` | `DeleteOne` | `invitations` | `_id` | `tenant` | MEDIUM | safe-unique-key | Filter contains a globally-unique key (_id) — the query will only ever return one docum... |
| 263 | `InviteMember` | `InsertOne` | `invitations` | `createdAt`, `email`, `expiresAt`, `invitedBy`, `role`, `status`, `tenantId`, `token` | `tenant` | OK |  | Filter contains tenantId. |
| 271 | `InviteMember` | `CountDocuments` | `tenant_memberships` | `tenantId` | `tenant` | OK |  | Filter contains tenantId. |
| 283 | `InviteMember` | `UpdateOne` | `tenants` | `_id` | `tenant` | MEDIUM | global-by-design | Collection 'tenants' maps to struct 'Tenant' which does NOT declare a tenantId bson fie... |
| 344 | `RemoveMember` | `FindOne` | `tenant_memberships` | `userId`, `tenantId` | `tenant` | OK |  | Filter contains tenantId. |
| 364 | `RemoveMember` | `DeleteOne` | `tenant_memberships` | `_id` | `tenant` | MEDIUM | safe-unique-key | Filter contains a globally-unique key (_id) — the query will only ever return one docum... |
| 372 | `RemoveMember` | `FindOne` | `plans` | `_id` | `tenant` | MEDIUM | global-by-design | Collection 'plans' maps to struct 'Plan' which does NOT declare a tenantId bson field —... |
| 373 | `RemoveMember` | `CountDocuments` | `tenant_memberships` | `tenantId` | `tenant` | OK |  | Filter contains tenantId. |
| 388 | `RemoveMember` | `UpdateOne` | `tenants` | `_id` | `tenant` | MEDIUM | global-by-design | Collection 'tenants' maps to struct 'Tenant' which does NOT declare a tenantId bson fie... |
| 456 | `ChangeRole` | `UpdateOne` | `tenant_memberships` | `userId`, `tenantId` | `tenant` | OK |  | Filter contains tenantId. |
| 508 | `TransferOwnership` | `CountDocuments` | `tenant_memberships` | `userId`, `tenantId` | `tenant` | OK |  | Filter contains tenantId. |
| 524 | `TransferOwnership` | `UpdateOne` | `tenant_memberships` | `userId`, `tenantId` | `tenant` | OK |  | Filter contains tenantId. |
| 534 | `TransferOwnership` | `UpdateOne` | `tenant_memberships` | `userId`, `tenantId` | `tenant` | OK |  | Filter contains tenantId. |
| 596 | `GetActivity` | `Find` | `system_logs` | `action`, `message`, `tenantId` | `tenant` | OK |  | Filter contains tenantId. |
| 609 | `GetActivity` | `CountDocuments` | `system_logs` | `action`, `message`, `tenantId` | `tenant` | OK |  | Filter contains tenantId. |
| 645 | `UpdateTenantSettings` | `UpdateOne` | `tenants` | `_id` | `tenant` | MEDIUM | global-by-design | Collection 'tenants' maps to struct 'Tenant' which does NOT declare a tenantId bson fie... |


### `backend/internal/api/handlers/usage.go`

| Line | Function | Op | Collection | Filter | Scope | Risk | Suppression | Note |
|------|----------|----|------------|--------|-------|------|-------------|------|
| 90 | `RecordUsage` | `UpdateOne` | `tenants` | `_id`, `subscriptionCredits` | `tenant` | MEDIUM | global-by-design | Collection 'tenants' maps to struct 'Tenant' which does NOT declare a tenantId bson fie... |
| 100 | `RecordUsage` | `UpdateOne` | `tenants` | `_id`, `purchasedCredits` | `tenant` | MEDIUM | global-by-design | Collection 'tenants' maps to struct 'Tenant' which does NOT declare a tenantId bson fie... |
| 114 | `RecordUsage` | `InsertOne` | `usage_events` | `createdAt`, `metadata`, `quantity`, `tenantId`, `type`, `userId` | `tenant` | OK |  | Filter contains tenantId. |
| 169 | `GetSummary` | `Aggregate` | `usage_events` | `createdAt`, `tenantId` | `tenant` | OK |  | Filter contains tenantId. |
| 196 | `GetSummary` | `FindOne` | `tenants` | `_id` | `tenant` | MEDIUM | global-by-design | Collection 'tenants' maps to struct 'Tenant' which does NOT declare a tenantId bson fie... |


### `backend/internal/api/handlers/webhook.go`

| Line | Function | Op | Collection | Filter | Scope | Risk | Suppression | Note |
|------|----------|----|------------|--------|-------|------|-------------|------|
| 71 | `HandleWebhook` | `FindOneAndUpdate` | `webhook_events` | `eventId` | `public` | MEDIUM | public-endpoint | Function 'HandleWebhook' is a public endpoint (no auth) — returns published/global cont... |
| 132 | `HandleWebhook` | `DeleteOne` | `webhook_events` | `eventId` | `public` | MEDIUM | public-endpoint | Function 'HandleWebhook' is a public endpoint (no auth) — returns published/global cont... |
| 138 | `HandleWebhook` | `UpdateOne` | `webhook_events` | `eventId` | `public` | MEDIUM | public-endpoint | Function 'HandleWebhook' is a public endpoint (no auth) — returns published/global cont... |
| 170 | `handleCheckoutCompleted` | `FindOne` | `tenants` | `_id` | `background` | MEDIUM | background-task | Function 'handleCheckoutCompleted' is a background system task (no request context, no ... |
| 182 | `handleCheckoutCompleted` | `FindOne` | `tenants` | `stripeCustomerId`, `_id` | `background` | MEDIUM | background-task | Function 'handleCheckoutCompleted' is a background system task (no request context, no ... |
| 205 | `handleCheckoutCompleted` | `FindOne` | `plans` | `_id` | `background` | MEDIUM | background-task | Function 'handleCheckoutCompleted' is a background system task (no request context, no ... |
| 239 | `handleCheckoutCompleted` | `UpdateOne` | `users` | `_id` | `background` | MEDIUM | background-task | Function 'handleCheckoutCompleted' is a background system task (no request context, no ... |
| 255 | `handleCheckoutCompleted` | `UpdateOne` | `tenants` | `_id` | `background` | MEDIUM | background-task | Function 'handleCheckoutCompleted' is a background system task (no request context, no ... |
| 322 | `handleCheckoutCompleted` | `FindOne` | `credit_bundles` | `_id` | `background` | MEDIUM | background-task | Function 'handleCheckoutCompleted' is a background system task (no request context, no ... |
| 328 | `handleCheckoutCompleted` | `UpdateOne` | `tenants` | `_id` | `background` | MEDIUM | background-task | Function 'handleCheckoutCompleted' is a background system task (no request context, no ... |
| 391 | `handleInvoicePaid` | `FindOne` | `tenants` | `stripeSubscriptionId` | `unknown` | MEDIUM | global-by-design | Collection 'tenants' maps to struct 'Tenant' which does NOT declare a tenantId bson fie... |
| 397 | `handleInvoicePaid` | `UpdateOne` | `tenants` | `_id` | `unknown` | MEDIUM | global-by-design | Collection 'tenants' maps to struct 'Tenant' which does NOT declare a tenantId bson fie... |
| 407 | `handleInvoicePaid` | `FindOne` | `plans` | `_id` | `unknown` | MEDIUM | global-by-design | Collection 'plans' maps to struct 'Plan' which does NOT declare a tenantId bson field —... |
| 409 | `handleInvoicePaid` | `UpdateOne` | `tenants` | `_id` | `unknown` | MEDIUM | global-by-design | Collection 'tenants' maps to struct 'Tenant' which does NOT declare a tenantId bson fie... |
| 415 | `handleInvoicePaid` | `UpdateOne` | `tenants` | `_id` | `unknown` | MEDIUM | global-by-design | Collection 'tenants' maps to struct 'Tenant' which does NOT declare a tenantId bson fie... |
| 436 | `handleInvoicePaid` | `FindOne` | `tenant_memberships` | `tenantId`, `role` | `unknown` | OK |  | Filter contains tenantId. |
| 443 | `handleInvoicePaid` | `FindOne` | `plans` | `_id` | `unknown` | MEDIUM | global-by-design | Collection 'plans' maps to struct 'Plan' which does NOT declare a tenantId bson field —... |
| 482 | `handleInvoicePaymentFailed` | `FindOne` | `tenants` | `stripeSubscriptionId` | `background` | MEDIUM | background-task | Function 'handleInvoicePaymentFailed' is a background system task (no request context, ... |
| 488 | `handleInvoicePaymentFailed` | `UpdateOne` | `tenants` | `_id` | `background` | MEDIUM | background-task | Function 'handleInvoicePaymentFailed' is a background system task (no request context, ... |
| 497 | `handleInvoicePaymentFailed` | `Find` | `tenant_memberships` | `tenantId` | `background` | OK |  | Filter contains tenantId. |
| 519 | `handleInvoicePaymentFailed` | `InsertOne` | `messages` | `body`, `createdAt`, `isSystem`, `read`, `subject`, `userId` | `background` | MEDIUM | background-task | Function 'handleInvoicePaymentFailed' is a background system task (no request context, ... |
| 551 | `handleSubscriptionUpdated` | `FindOne` | `tenants` | `stripeSubscriptionId` | `unknown` | MEDIUM | global-by-design | Collection 'tenants' maps to struct 'Tenant' which does NOT declare a tenantId bson fie... |
| 583 | `handleSubscriptionUpdated` | `FindOne` | `plans` | `_id` | `unknown` | MEDIUM | global-by-design | Collection 'plans' maps to struct 'Plan' which does NOT declare a tenantId bson field —... |
| 598 | `handleSubscriptionUpdated` | `UpdateOne` | `tenants` | `_id` | `unknown` | MEDIUM | global-by-design | Collection 'tenants' maps to struct 'Tenant' which does NOT declare a tenantId bson fie... |
| 613 | `handleSubscriptionDeleted` | `FindOne` | `tenants` | `stripeSubscriptionId` | `unknown` | MEDIUM | global-by-design | Collection 'tenants' maps to struct 'Tenant' which does NOT declare a tenantId bson fie... |
| 619 | `handleSubscriptionDeleted` | `FindOne` | `plans` | `isSystem` | `unknown` | MEDIUM | global-by-design | Collection 'plans' maps to struct 'Plan' which does NOT declare a tenantId bson field —... |
| 635 | `handleSubscriptionDeleted` | `UpdateOne` | `tenants` | `_id` | `unknown` | MEDIUM | global-by-design | Collection 'tenants' maps to struct 'Tenant' which does NOT declare a tenantId bson fie... |
| 675 | `handleChargeRefunded` | `FindOne` | `tenants` | `stripeCustomerId` | `unknown` | MEDIUM | global-by-design | Collection 'tenants' maps to struct 'Tenant' which does NOT declare a tenantId bson fie... |
| 688 | `handleChargeRefunded` | `FindOne` | `tenant_memberships` | `tenantId`, `role` | `unknown` | OK |  | Filter contains tenantId. |
| 726 | `handleDisputeCreated` | `FindOne` | `tenants` | `stripeCustomerId` | `unknown` | MEDIUM | global-by-design | Collection 'tenants' maps to struct 'Tenant' which does NOT declare a tenantId bson fie... |
| 732 | `handleDisputeCreated` | `UpdateOne` | `tenants` | `_id` | `unknown` | MEDIUM | global-by-design | Collection 'tenants' maps to struct 'Tenant' which does NOT declare a tenantId bson fie... |
| 771 | `handleDisputeClosed` | `FindOne` | `tenants` | `stripeCustomerId` | `unknown` | MEDIUM | global-by-design | Collection 'tenants' maps to struct 'Tenant' which does NOT declare a tenantId bson fie... |
| 779 | `handleDisputeClosed` | `UpdateOne` | `tenants` | `_id` | `unknown` | MEDIUM | global-by-design | Collection 'tenants' maps to struct 'Tenant' which does NOT declare a tenantId bson fie... |
| 841 | `recordTransaction` | `InsertOne` | `financial_transactions` | `amountCents`, `billingInterval`, `bundleId`, `bundleName`, `createdAt`, `currency`, `description`, `invoiceNumber`, `planId`, `planName`, `stripeInvoiceId`, `stripeSessionId`, `stripeSubscriptionId`, `subtotalCents`, `taxAmountCents`, `tenantId`, `type`, `userId` | `unknown` | OK |  | Filter contains tenantId. |


### `backend/internal/api/handlers/webhooks.go`

| Line | Function | Op | Collection | Filter | Scope | Risk | Suppression | Note |
|------|----------|----|------------|--------|-------|------|-------------|------|
| 45 | `ListWebhooks` | `Find` | `webhooks` | `isActive` | `admin` | MEDIUM | admin-handler | Function 'ListWebhooks' is an admin handler (registered on /api/admin/*). Admin handler... |
| 71 | `ListWebhooks` | `CountDocuments` | `webhook_deliveries` | `webhookId`, `createdAt` | `admin` | MEDIUM | admin-handler | Function 'ListWebhooks' is an admin handler (registered on /api/admin/*). Admin handler... |
| 83 | `ListWebhooks` | `FindOne` | `webhook_deliveries` | `webhookId` | `admin` | MEDIUM | admin-handler | Function 'ListWebhooks' is an admin handler (registered on /api/admin/*). Admin handler... |
| 88 | `ListWebhooks` | `CountDocuments` | `webhooks` | `isActive` | `admin` | MEDIUM | admin-handler | Function 'ListWebhooks' is an admin handler (registered on /api/admin/*). Admin handler... |
| 105 | `GetWebhook` | `FindOne` | `webhooks` | `_id`, `isActive` | `admin` | MEDIUM | admin-handler | Function 'GetWebhook' is an admin handler (registered on /api/admin/*). Admin handlers ... |
| 111 | `GetWebhook` | `Find` | `webhook_deliveries` | `webhookId` | `admin` | MEDIUM | admin-handler | Function 'GetWebhook' is an admin handler (registered on /api/admin/*). Admin handlers ... |
| 279 | `CreateWebhook` | `InsertOne` | `webhooks` | `createdAt`, `createdBy`, `description`, `events`, `isActive`, `name`, `secret`, `secretPreview`, `updatedAt`, `url` | `admin` | MEDIUM | admin-handler | Function 'CreateWebhook' is an admin handler (registered on /api/admin/*). Admin handle... |
| 320 | `UpdateWebhook` | `UpdateByID` | `webhooks` | `_id` | `admin` | MEDIUM | admin-handler | Function 'UpdateWebhook' is an admin handler (registered on /api/admin/*). Admin handle... |
| 340 | `UpdateWebhook` | `FindOne` | `webhooks` | `_id` | `admin` | MEDIUM | admin-handler | Function 'UpdateWebhook' is an admin handler (registered on /api/admin/*). Admin handle... |
| 356 | `DeleteWebhook` | `UpdateByID` | `webhooks` | `_id` | `admin` | MEDIUM | admin-handler | Function 'DeleteWebhook' is an admin handler (registered on /api/admin/*). Admin handle... |
| 393 | `RegenerateSecret` | `UpdateByID` | `webhooks` | `_id` | `admin` | MEDIUM | admin-handler | Function 'RegenerateSecret' is an admin handler (registered on /api/admin/*). Admin han... |
| 421 | `TestWebhook` | `FindOne` | `webhooks` | `_id`, `isActive` | `admin` | MEDIUM | admin-handler | Function 'TestWebhook' is an admin handler (registered on /api/admin/*). Admin handlers... |


### `backend/internal/configstore/seed.go`

| Line | Function | Op | Collection | Filter | Scope | Risk | Suppression | Note |
|------|----------|----|------------|--------|-------|------|-------------|------|
| 380 | `Seed` | `FindOne` | `config_vars` | `name` | `admin` | MEDIUM | admin-handler | Function 'Seed' is an admin handler (registered on /api/admin/*). Admin handlers see AL... |
| 384 | `Seed` | `InsertOne` | `config_vars` | — | `admin` | MEDIUM | admin-handler | Function 'Seed' is an admin handler (registered on /api/admin/*). Admin handlers see AL... |


### `backend/internal/configstore/store.go`

| Line | Function | Op | Collection | Filter | Scope | Risk | Suppression | Note |
|------|----------|----|------------|--------|-------|------|-------------|------|
| 34 | `Load` | `Find` | `config_vars` | — | `admin` | MEDIUM | admin-handler | Function 'Load' is an admin handler (registered on /api/admin/*). Admin handlers see AL... |
| 90 | `Set` | `UpdateOne` | `config_vars` | `name` | `admin` | MEDIUM | admin-handler | Function 'Set' is an admin handler (registered on /api/admin/*). Admin handlers see ALL... |
| 106 | `Reload` | `FindOne` | `config_vars` | `name` | `admin` | MEDIUM | admin-handler | Function 'Reload' is an admin handler (registered on /api/admin/*). Admin handlers see ... |


### `backend/internal/health/health.go`

| Line | Function | Op | Collection | Filter | Scope | Risk | Suppression | Note |
|------|----------|----|------------|--------|-------|------|-------------|------|
| 138 | `registerNode` | `UpdateOne` | `system_nodes` | `machineId` | `background` | MEDIUM | background-task | Function 'registerNode' is a background system task (no request context, no tenantId av... |
| 165 | `heartbeat` | `UpdateOne` | `system_nodes` | `machineId` | `background` | MEDIUM | background-task | Function 'heartbeat' is a background system task (no request context, no tenantId avail... |
| 300 | `collectAndStore` | `InsertOne` | `system_metrics` | `cpu`, `disk`, `goRuntime`, `http`, `integrations`, `memory`, `mongo`, `network`, `nodeId`, `timestamp` | `background` | MEDIUM | background-task | Function 'collectAndStore' is a background system task (no request context, no tenantId... |


### `backend/internal/health/query.go`

| Line | Function | Op | Collection | Filter | Scope | Risk | Suppression | Note |
|------|----------|----|------------|--------|-------|------|-------------|------|
| 28 | `ListNodes` | `UpdateMany` | `system_nodes` | `lastSeen` | `admin` | MEDIUM | admin-handler | Function 'ListNodes' is an admin handler (registered on /api/admin/*). Admin handlers s... |
| 35 | `ListNodes` | `Find` | `system_nodes` | — | `admin` | MEDIUM | admin-handler | Function 'ListNodes' is an admin handler (registered on /api/admin/*). Admin handlers s... |
| 55 | `GetMetrics` | `Find` | `system_metrics` | `nodeId`, `timestamp` | `admin` | MEDIUM | admin-handler | Function 'GetMetrics' is an admin handler (registered on /api/admin/*). Admin handlers ... |
| 74 | `GetAggregateMetrics` | `Find` | `system_metrics` | `timestamp` | `admin` | MEDIUM | admin-handler | Function 'GetAggregateMetrics' is an admin handler (registered on /api/admin/*). Admin ... |
| 98 | `GetCurrentMetrics` | `FindOne` | `system_metrics` | `nodeId` | `admin` | MEDIUM | admin-handler | Function 'GetCurrentMetrics' is an admin handler (registered on /api/admin/*). Admin ha... |
| 120 | `GetIntegrationCounts24h` | `Aggregate` | `system_metrics` | — | `admin` | MEDIUM | admin-handler | Function 'GetIntegrationCounts24h' is an admin handler (registered on /api/admin/*). Ad... |


### `backend/internal/metrics/metrics.go`

| Line | Function | Op | Collection | Filter | Scope | Risk | Suppression | Note |
|------|----------|----|------------|--------|-------|------|-------------|------|
| 112 | `tryAcquireOrRenew` | `FindOneAndUpdate` | `leader_locks` | `_id`, `expiresAt`, `holderId` | `background` | MEDIUM | background-task | Function 'tryAcquireOrRenew' is a background system task (no request context, no tenant... |
| 148 | `isLeader` | `FindOne` | `leader_locks` | `_id` | `background` | MEDIUM | background-task | Function 'isLeader' is a background system task (no request context, no tenantId availa... |
| 158 | `releaseLock` | `DeleteOne` | `leader_locks` | `_id`, `holderId` | `background` | MEDIUM | background-task | Function 'releaseLock' is a background system task (no request context, no tenantId ava... |
| 192 | `collectDaily` | `Aggregate` | `users` | `lastLoginAt` | `background` | MEDIUM | background-task | Function 'collectDaily' is a background system task (no request context, no tenantId av... |
| 227 | `collectDaily` | `Aggregate` | `financial_transactions` | `createdAt` | `background` | MEDIUM | background-task | Function 'collectDaily' is a background system task (no request context, no tenantId av... |
| 263 | `collectDaily` | `Aggregate` | `tenants` | `billingStatus`, `planId` | `background` | MEDIUM | background-task | Function 'collectDaily' is a background system task (no request context, no tenantId av... |
| 280 | `collectDaily` | `UpdateOne` | `daily_metrics` | `date` | `background` | MEDIUM | background-task | Function 'collectDaily' is a background system task (no request context, no tenantId av... |


### `backend/internal/middleware/auth.go`

| Line | Function | Op | Collection | Filter | Scope | Risk | Suppression | Note |
|------|----------|----|------------|--------|-------|------|-------------|------|
| 90 | `authenticateJWT` | `FindOne` | `users` | `_id` | `unknown` | MEDIUM | global-by-design | Collection 'users' maps to struct 'User' which does NOT declare a tenantId bson field —... |
| 113 | `authenticateAPIKey` | `FindOne` | `api_keys` | `keyHash`, `isActive` | `auth` | MEDIUM | global-by-design | Collection 'api_keys' maps to struct 'APIKey' which does NOT declare a tenantId bson fi... |
| 124 | `authenticateAPIKey` | `FindOne` | `users` | `_id` | `auth` | MEDIUM | global-by-design | Collection 'users' maps to struct 'User' which does NOT declare a tenantId bson field —... |
| 135 | `authenticateAPIKey` | `FindOne` | `tenants` | `isRoot` | `auth` | MEDIUM | global-by-design | Collection 'tenants' maps to struct 'Tenant' which does NOT declare a tenantId bson fie... |
| 155 | `authenticateAPIKey` | `UpdateByID` | `api_keys` | `_id` | `auth` | MEDIUM | global-by-design | Collection 'api_keys' maps to struct 'APIKey' which does NOT declare a tenantId bson fi... |
| 168 | `isTokenRevoked` | `CountDocuments` | `revoked_tokens` | `tokenHash` | `auth` | MEDIUM | global-by-design | Collection 'revoked_tokens' maps to struct 'RevokedToken' which does NOT declare a tena... |


### `backend/internal/middleware/ratelimit.go`

| Line | Function | Op | Collection | Filter | Scope | Risk | Suppression | Note |
|------|----------|----|------------|--------|-------|------|-------------|------|
| 156 | `allowDistributed` | `FindOneAndUpdate` | `<unknown>` | `_id`, `windowEnd` | `unknown` | MEDIUM | safe-unique-key | Filter contains a globally-unique key (_id) — the query will only ever return one docum... |
| 165 | `allowDistributed` | `FindOneAndUpdate` | `<unknown>` | `_id` | `unknown` | MEDIUM | safe-unique-key | Filter contains a globally-unique key (_id) — the query will only ever return one docum... |


### `backend/internal/middleware/tenant.go`

| Line | Function | Op | Collection | Filter | Scope | Risk | Suppression | Note |
|------|----------|----|------------|--------|-------|------|-------------|------|
| 51 | `RequireTenant` | `FindOne` | `tenants` | `_id`, `isActive` | `unknown` | MEDIUM | global-by-design | Collection 'tenants' maps to struct 'Tenant' which does NOT declare a tenantId bson fie... |
| 64 | `RequireTenant` | `FindOne` | `tenant_memberships` | `userId`, `tenantId` | `unknown` | OK |  | Filter contains tenantId. |
| 141 | `RequireEntitlement` | `FindOne` | `plans` | `_id` | `unknown` | MEDIUM | global-by-design | Collection 'plans' maps to struct 'Plan' which does NOT declare a tenantId bson field —... |


### `backend/internal/planstore/seed.go`

| Line | Function | Op | Collection | Filter | Scope | Risk | Suppression | Note |
|------|----------|----|------------|--------|-------|------|-------------|------|
| 19 | `Seed` | `FindOne` | `plans` | `isSystem` | `admin` | MEDIUM | admin-handler | Function 'Seed' is an admin handler (registered on /api/admin/*). Admin handlers see AL... |
| 36 | `Seed` | `InsertOne` | `plans` | `annualDiscountPct`, `bonusCredits`, `createdAt`, `creditResetPolicy`, `description`, `entitlements`, `includedSeats`, `isArchived`, `isSystem`, `maxSeats`, `minSeats`, `monthlyPriceCents`, `name`, `perSeatPriceCents`, `pricingModel`, `trialDays`, `updatedAt`, `usageCreditsPerMonth`, `userLimit` | `admin` | MEDIUM | admin-handler | Function 'Seed' is an admin handler (registered on /api/admin/*). Admin handlers see AL... |


### `backend/internal/stripe/stripe.go`

| Line | Function | Op | Collection | Filter | Scope | Risk | Suppression | Note |
|------|----------|----|------------|--------|-------|------|-------------|------|
| 82 | `GetOrCreateCustomer` | `UpdateOne` | `tenants` | `_id` | `unknown` | MEDIUM | global-by-design | Collection 'tenants' maps to struct 'Tenant' which does NOT declare a tenantId bson fie... |
| 100 | `GetOrCreatePrice` | `FindOne` | `stripe_mappings` | `entityType`, `entityId` | `admin` | MEDIUM | admin-handler | Function 'GetOrCreatePrice' is an admin handler (registered on /api/admin/*). Admin han... |
| 143 | `GetOrCreatePrice` | `InsertOne` | `stripe_mappings` | `createdAt`, `entityId`, `entityType`, `stripePriceId`, `stripeProductId` | `admin` | MEDIUM | admin-handler | Function 'GetOrCreatePrice' is an admin handler (registered on /api/admin/*). Admin han... |
| 352 | `NextInvoiceNumber` | `FindOneAndUpdate` | `counters` | `_id` | `background` | MEDIUM | background-task | Function 'NextInvoiceNumber' is a background system task (no request context, no tenant... |


### `backend/internal/syslog/syslog.go`

| Line | Function | Op | Collection | Filter | Scope | Risk | Suppression | Note |
|------|----------|----|------------|--------|-------|------|-------------|------|
| 97 | `log` | `InsertOne` | `system_logs` | `action`, `category`, `createdAt`, `message`, `metadata`, `severity`, `tenantId`, `userId` | `unknown` | OK |  | Filter contains tenantId. |
| 114 | `log` | `InsertOne` | `system_logs` | `action`, `category`, `createdAt`, `message`, `metadata`, `severity`, `tenantId`, `userId` | `unknown` | OK |  | Filter contains tenantId. |
| 137 | `logCategorized` | `InsertOne` | `system_logs` | `action`, `category`, `createdAt`, `message`, `metadata`, `severity`, `tenantId`, `userId` | `unknown` | OK |  | Filter contains tenantId. |
| 154 | `logCategorized` | `InsertOne` | `system_logs` | `action`, `category`, `createdAt`, `message`, `metadata`, `severity`, `tenantId`, `userId` | `unknown` | OK |  | Filter contains tenantId. |
| 234 | `LogTenantActivity` | `InsertOne` | `system_logs` | `action`, `category`, `createdAt`, `message`, `metadata`, `severity`, `tenantId`, `userId` | `unknown` | OK |  | Filter contains tenantId. |


### `backend/internal/telemetry/service.go`

| Line | Function | Op | Collection | Filter | Scope | Risk | Suppression | Note |
|------|----------|----|------------|--------|-------|------|-------------|------|
| 82 | `flushLoop` | `InsertMany` | `telemetry_events` | — | `background` | MEDIUM | background-task | Function 'flushLoop' is a background system task (no request context, no tenantId avail... |
| 188 | `TrackBatch` | `InsertMany` | `telemetry_events` | — | `tenant` | MEDIUM | struct-supports-tenant-id | InsertMany inserts a document (or slice of documents) whose struct 'TelemetryEvent' dec... |
| 323 | `FunnelMetrics` | `CountDocuments` | `users` | `createdAt` | `admin` | MEDIUM | admin-handler | Function 'FunnelMetrics' is an admin handler (registered on /api/admin/*). Admin handle... |
| 341 | `FunnelMetrics` | `CountDocuments` | `telemetry_events` | `eventName`, `createdAt` | `admin` | MEDIUM | admin-handler | Function 'FunnelMetrics' is an admin handler (registered on /api/admin/*). Admin handle... |
| 350 | `FunnelMetrics` | `CountDocuments` | `financial_transactions` | `type`, `createdAt` | `admin` | MEDIUM | admin-handler | Function 'FunnelMetrics' is an admin handler (registered on /api/admin/*). Admin handle... |
| 359 | `FunnelMetrics` | `CountDocuments` | `telemetry_events` | `eventName` | `admin` | MEDIUM | admin-handler | Function 'FunnelMetrics' is an admin handler (registered on /api/admin/*). Admin handle... |
| 450 | `RetentionCohorts` | `Aggregate` | `users` | — | `admin` | MEDIUM | admin-handler | Function 'RetentionCohorts' is an admin handler (registered on /api/admin/*). Admin han... |
| 534 | `EngagementMetrics` | `CountDocuments` | `telemetry_events` | `eventName`, `userId` | `admin` | MEDIUM | admin-handler | Function 'EngagementMetrics' is an admin handler (registered on /api/admin/*). Admin ha... |
| 599 | `computeKPIs` | `CountDocuments` | `tenants` | `billingStatus`, `isActive` | `unknown` | MEDIUM | global-by-design | Collection 'tenants' maps to struct 'Tenant' which does NOT declare a tenantId bson fie... |
| 608 | `computeKPIs` | `CountDocuments` | `users` | — | `unknown` | MEDIUM | global-by-design | Collection 'users' maps to struct 'User' which does NOT declare a tenantId bson field —... |
| 624 | `computeKPIs` | `CountDocuments` | `tenants` | `canceledAt` | `unknown` | MEDIUM | global-by-design | Collection 'tenants' maps to struct 'Tenant' which does NOT declare a tenantId bson fie... |
| 630 | `computeKPIs` | `CountDocuments` | `tenants` | `billingStatus` | `unknown` | MEDIUM | global-by-design | Collection 'tenants' maps to struct 'Tenant' which does NOT declare a tenantId bson fie... |
| 643 | `computeKPIs` | `CountDocuments` | `tenants` | `trialUsedAt` | `unknown` | MEDIUM | global-by-design | Collection 'tenants' maps to struct 'Tenant' which does NOT declare a tenantId bson fie... |
| 649 | `computeKPIs` | `CountDocuments` | `tenants` | `trialUsedAt` | `unknown` | MEDIUM | global-by-design | Collection 'tenants' maps to struct 'Tenant' which does NOT declare a tenantId bson fie... |
| 708 | `CustomEventSummary` | `CountDocuments` | `telemetry_events` | `createdAt`, `eventName` | `admin` | MEDIUM | admin-handler | Function 'CustomEventSummary' is an admin handler (registered on /api/admin/*). Admin h... |
| 724 | `CustomEventSummary` | `Aggregate` | `telemetry_events` | — | `admin` | MEDIUM | admin-handler | Function 'CustomEventSummary' is an admin handler (registered on /api/admin/*). Admin h... |
| 761 | `ListEventTypes` | `Aggregate` | `telemetry_events` | — | `admin` | MEDIUM | admin-handler | Function 'ListEventTypes' is an admin handler (registered on /api/admin/*). Admin handl... |
| 800 | `countDistinct` | `Aggregate` | `telemetry_events` | — | `admin` | MEDIUM | admin-handler | Function 'countDistinct' is an admin handler (registered on /api/admin/*). Admin handle... |
| 818 | `getActiveTenantIDs` | `Find` | `tenants` | `billingStatus`, `isActive` | `unknown` | MEDIUM | global-by-design | Collection 'tenants' maps to struct 'Tenant' which does NOT declare a tenantId bson fie... |
| 843 | `getUserIDsForTenants` | `Find` | `tenant_memberships` | `tenantId` | `unknown` | OK |  | Filter contains tenantId. |
| 910 | `weeklyActiveUsers` | `Aggregate` | `telemetry_events` | — | `admin` | MEDIUM | admin-handler | Function 'weeklyActiveUsers' is an admin handler (registered on /api/admin/*). Admin ha... |
| 958 | `monthlyActiveUsers` | `Aggregate` | `telemetry_events` | — | `admin` | MEDIUM | admin-handler | Function 'monthlyActiveUsers' is an admin handler (registered on /api/admin/*). Admin h... |
| 996 | `topCustomEvents` | `Aggregate` | `telemetry_events` | — | `admin` | MEDIUM | admin-handler | Function 'topCustomEvents' is an admin handler (registered on /api/admin/*). Admin hand... |
| 1027 | `creditConsumptionTrend` | `Aggregate` | `usage_events` | — | `admin` | MEDIUM | admin-handler | Function 'creditConsumptionTrend' is an admin handler (registered on /api/admin/*). Adm... |
| 1103 | `calculateMRR` | `Aggregate` | `tenants` | — | `unknown` | MEDIUM | global-by-design | Collection 'tenants' maps to struct 'Tenant' which does NOT declare a tenantId bson fie... |
| 1147 | `medianTimeToFirstPurchase` | `Aggregate` | `financial_transactions` | — | `admin` | MEDIUM | admin-handler | Function 'medianTimeToFirstPurchase' is an admin handler (registered on /api/admin/*). ... |
| 1197 | `planDistribution` | `Aggregate` | `tenants` | — | `unknown` | MEDIUM | global-by-design | Collection 'tenants' maps to struct 'Tenant' which does NOT declare a tenantId bson fie... |
| 1233 | `mrrTrend` | `Find` | `daily_metrics` | `date` | `admin` | MEDIUM | admin-handler | Function 'mrrTrend' is an admin handler (registered on /api/admin/*). Admin handlers se... |
| 1269 | `subscriberTrend` | `Aggregate` | `financial_transactions` | — | `admin` | MEDIUM | admin-handler | Function 'subscriberTrend' is an admin handler (registered on /api/admin/*). Admin hand... |
| 1290 | `aggregateDailyPoints` | `Aggregate` | `telemetry_events` | — | `background` | MEDIUM | background-task | Function 'aggregateDailyPoints' is a background system task (no request context, no ten... |


### `backend/internal/testutil/testutil.go`

| Line | Function | Op | Collection | Filter | Scope | Risk | Suppression | Note |
|------|----------|----|------------|--------|-------|------|-------------|------|
| 98 | `MustConnectTestDB` | `DeleteMany` | `<unknown>` | — | `testutil` | MEDIUM | test-util | Query is in a test-utility file (internal/testutil/) — test helpers reset/clean test da... |
| 144 | `ConnectTestDB` | `DeleteMany` | `<unknown>` | — | `testutil` | MEDIUM | test-util | Query is in a test-utility file (internal/testutil/) — test helpers reset/clean test da... |
| 227 | `CleanupCollections` | `DeleteMany` | `<unknown>` | — | `testutil` | MEDIUM | test-util | Query is in a test-utility file (internal/testutil/) — test helpers reset/clean test da... |
| 270 | `CreateTestUser` | `InsertOne` | `users` | `accountLockedUntil`, `authMethods`, `createdAt`, `displayName`, `email`, `emailVerified`, `failedLoginAttempts`, `githubId`, `googleId`, `isActive`, `lastLoginAt`, `lastVerificationSent`, `microsoftId`, `onboardingCompletedAt`, `passwordHash`, `recoveryCodes`, `themePreference`, `totpEnabled`, `totpSecret`, `totpVerifiedAt`, `trialUsedAt`, `updatedAt` | `testutil` | MEDIUM | test-util | Query is in a test-utility file (internal/testutil/) — test helpers reset/clean test da... |
| 292 | `CreateTestTenant` | `InsertOne` | `tenants` | `billingInterval`, `billingStatus`, `billingWaived`, `canceledAt`, `createdAt`, `currentPeriodEnd`, `isActive`, `isRoot`, `name`, `planId`, `purchasedCredits`, `seatQuantity`, `slug`, `stripeCustomerId`, `stripeSubscriptionId`, `subscriptionCredits`, `trialUsedAt`, `updatedAt` | `testutil` | MEDIUM | test-util | Query is in a test-utility file (internal/testutil/) — test helpers reset/clean test da... |
| 305 | `CreateTestTenant` | `InsertOne` | `tenant_memberships` | `joinedAt`, `role`, `tenantId`, `updatedAt`, `userId` | `testutil` | OK |  | Filter contains tenantId. |
| 318 | `MarkSystemInitialized` | `InsertOne` | `system_config` | `initialized`, `initializedAt`, `initializedBy`, `version` | `testutil` | MEDIUM | test-util | Query is in a test-utility file (internal/testutil/) — test helpers reset/clean test da... |
| 341 | `InsertTestLogs` | `InsertOne` | `system_logs` | `action`, `category`, `createdAt`, `message`, `metadata`, `severity`, `tenantId`, `userId` | `testutil` | OK |  | Filter contains tenantId. |
| 352 | `CountDocuments` | `CountDocuments` | `<unknown>` | — | `testutil` | MEDIUM | test-util | Query is in a test-utility file (internal/testutil/) — test helpers reset/clean test da... |
| 392 | `CreateTestMembership` | `InsertOne` | `tenant_memberships` | `joinedAt`, `role`, `tenantId`, `updatedAt`, `userId` | `testutil` | OK |  | Filter contains tenantId. |
| 416 | `CreateTestPlan` | `InsertOne` | `plans` | `annualDiscountPct`, `bonusCredits`, `createdAt`, `creditResetPolicy`, `description`, `entitlements`, `includedSeats`, `isArchived`, `isSystem`, `maxSeats`, `minSeats`, `monthlyPriceCents`, `name`, `perSeatPriceCents`, `pricingModel`, `trialDays`, `updatedAt`, `usageCreditsPerMonth`, `userLimit` | `testutil` | MEDIUM | test-util | Query is in a test-utility file (internal/testutil/) — test helpers reset/clean test da... |
| 438 | `CreateTestAPIKey` | `InsertOne` | `api_keys` | `authority`, `createdAt`, `createdBy`, `isActive`, `keyHash`, `keyPreview`, `lastUsedAt`, `name` | `testutil` | MEDIUM | test-util | Query is in a test-utility file (internal/testutil/) — test helpers reset/clean test da... |
| 462 | `CreateTestWebhook` | `InsertOne` | `webhooks` | `createdAt`, `createdBy`, `description`, `events`, `isActive`, `name`, `secret`, `secretPreview`, `updatedAt`, `url` | `testutil` | MEDIUM | test-util | Query is in a test-utility file (internal/testutil/) — test helpers reset/clean test da... |
| 485 | `CreateTestInvitation` | `InsertOne` | `invitations` | `createdAt`, `email`, `expiresAt`, `invitedBy`, `role`, `status`, `tenantId`, `token` | `testutil` | OK |  | Filter contains tenantId. |


### `backend/internal/version/check.go`

| Line | Function | Op | Collection | Filter | Scope | Risk | Suppression | Note |
|------|----------|----|------------|--------|-------|------|-------------|------|
| 28 | `CheckAndMigrate` | `FindOne` | `system_config` | — | `unknown` | MEDIUM | global-by-design | Collection 'system_config' maps to struct 'SystemConfig' which does NOT declare a tenan... |
| 50 | `CheckAndMigrate` | `UpdateOne` | `system_config` | `_id` | `unknown` | MEDIUM | global-by-design | Collection 'system_config' maps to struct 'SystemConfig' which does NOT declare a tenan... |
| 65 | `sendUpgradeMessage` | `FindOne` | `tenants` | `isRoot` | `background` | MEDIUM | background-task | Function 'sendUpgradeMessage' is a background system task (no request context, no tenan... |
| 72 | `sendUpgradeMessage` | `FindOne` | `tenant_memberships` | `tenantId`, `role` | `background` | OK |  | Filter contains tenantId. |
| 91 | `sendUpgradeMessage` | `InsertOne` | `messages` | `body`, `createdAt`, `isSystem`, `read`, `subject`, `userId` | `background` | MEDIUM | background-task | Function 'sendUpgradeMessage' is a background system task (no request context, no tenan... |


### `backend/internal/webhooks/dispatcher.go`

| Line | Function | Op | Collection | Filter | Scope | Risk | Suppression | Note |
|------|----------|----|------------|--------|-------|------|-------------|------|
| 194 | `dispatch` | `Find` | `webhooks` | `events`, `isActive` | `background` | MEDIUM | background-task | Function 'dispatch' is a background system task (no request context, no tenantId availa... |
| 287 | `deliverWithRetry` | `InsertOne` | `webhook_deliveries` | `createdAt`, `durationMs`, `eventType`, `maxRetries`, `payload`, `responseBody`, `responseCode`, `retryCount`, `success`, `webhookId` | `background` | MEDIUM | background-task | Function 'deliverWithRetry' is a background system task (no request context, no tenantI... |
| 421 | `DeliverTest` | `InsertOne` | `webhook_deliveries` | `createdAt`, `durationMs`, `eventType`, `maxRetries`, `payload`, `responseBody`, `responseCode`, `retryCount`, `success`, `webhookId` | `unknown` | MEDIUM | global-by-design | Collection 'webhook_deliveries' maps to struct 'WebhookDelivery' which does NOT declare... |


---
_Generated by `graphify_tenant_audit.py`._
