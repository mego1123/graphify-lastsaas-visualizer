# Missing Index Report

**Target:** `/home/z/my-project/repos/lastsaas`

For every MongoDB query in the codebase, checks whether the filter fields are covered by a declared index. Indexes are parsed from `Indexes().CreateMany(...)` / `CreateOne(...)` calls in the codebase (`internal/db/mongodb.go::ensureIndexes`, `internal/middleware/ratelimit.go`, etc.).

## Summary

| Metric | Value |
| --- | --- |
| Queries scanned | 413 |
| Total findings | **22** |
| HIGH severity | 0 |
| MEDIUM severity | 22 |
| LOW severity | 0 |
| Suppressed by `// graphify:no-index-check` | 11 |

## Findings by Type

| Type | Count |
| --- | ---: |
| No covering index | 14 |
| Multi-tenant query without tenantId filter | 7 |
| Collection has no declared indexes | 1 |

## Collections Affected

| Collection | Findings |
| --- | ---: |
| `tenants` | 8 |
| `system_logs` | 3 |
| `financial_transactions` | 3 |
| `announcements` | 2 |
| `webhooks` | 2 |
| `api_keys` | 2 |
| `plans` | 1 |
| `credit_bundles` | 1 |

## Collections Queried But With No Declared Indexes

These collections are queried in the codebase but have no `Indexes().CreateMany/CreateOne` call anywhere — every query will be a full collection scan (modulo the default `_id` index).

- `announcements`
- `branding_config`
- `system_config`

## Files With Most Findings

| File | Findings |
| --- | ---: |
| `backend/internal/api/handlers/webhook.go` | 7 |
| `backend/cmd/lastsaas/cmd_logs.go` | 2 |
| `backend/internal/api/handlers/announcements.go` | 2 |
| `backend/internal/api/handlers/billing.go` | 2 |
| `backend/internal/api/handlers/promotions.go` | 2 |
| `backend/internal/api/handlers/webhooks.go` | 2 |
| `backend/internal/api/handlers/apikeys.go` | 2 |
| `backend/cmd/lastsaas/cmd_financial.go` | 1 |
| `backend/internal/telemetry/service.go` | 1 |
| `backend/internal/api/handlers/logs.go` | 1 |

## Detailed Findings

### `backend/cmd/lastsaas/cmd_financial.go`

- **[MEDIUM] Multi-tenant query without tenantId filter** — `backend/cmd/lastsaas/cmd_financial.go:254` `Find` on `financial_transactions` in `cmdFinancialTransactions`
  - Filter fields: —
  - _empty-filter query on multi-tenant collection `financial_transactions` — full collection scan, risks cross-tenant data leak_
  - Suggestion: Add a `tenantId` filter (or scope the collection accessor to the current tenant) to avoid a full collection scan.
  ```go
  cursor, err := database.FinancialTransactions().Find(ctx, filter, opts)
  ```

### `backend/cmd/lastsaas/cmd_logs.go`

- **[MEDIUM] Multi-tenant query without tenantId filter** — `backend/cmd/lastsaas/cmd_logs.go:140` `Find` on `system_logs` in `queryLogs`
  - Filter fields: —
  - _empty-filter query on multi-tenant collection `system_logs` — full collection scan, risks cross-tenant data leak_
  - Suggestion: Add a `tenantId` filter (or scope the collection accessor to the current tenant) to avoid a full collection scan.
  ```go
  cursor, err := database.SystemLogs().Find(ctx, filter, opts)
  ```
- **[MEDIUM] Multi-tenant query without tenantId filter** — `backend/cmd/lastsaas/cmd_logs.go:193` `Find` on `system_logs` in `logsFollow`
  - Filter fields: —
  - _empty-filter query on multi-tenant collection `system_logs` — full collection scan, risks cross-tenant data leak_
  - Suggestion: Add a `tenantId` filter (or scope the collection accessor to the current tenant) to avoid a full collection scan.
  ```go
  cursor, err := database.SystemLogs().Find(ctx, followFilter, opts)
  ```

### `backend/internal/api/handlers/announcements.go`

- **[MEDIUM] Collection has no declared indexes** — `backend/internal/api/handlers/announcements.go:33` `Find` on `announcements` in `ListPublic`
  - Filter fields: `isPublished``
  - _collection `announcements` has no declared indexes — every query scans the full collection_
  - Suggestion: Add an index on the most-filtered field(s) of `announcements` (e.g. `isPublished` based on this query).
  ```go
  cursor, err := h.db.Announcements().Find(r.Context(), bson.M{"isPublished": true}, opts)
  ```
- **[MEDIUM] Multi-tenant query without tenantId filter** — `backend/internal/api/handlers/announcements.go:54` `Find` on `announcements` in `ListAll`
  - Filter fields: —
  - _empty-filter query on multi-tenant collection `announcements` — full collection scan, risks cross-tenant data leak_
  - Suggestion: Add a `tenantId` filter (or scope the collection accessor to the current tenant) to avoid a full collection scan.
  ```go
  cursor, err := h.db.Announcements().Find(r.Context(), bson.M{}, opts)
  ```

### `backend/internal/api/handlers/apikeys.go`

- **[MEDIUM] No covering index** — `backend/internal/api/handlers/apikeys.go:45` `Find` on `api_keys` in `ListAPIKeys`
  - Filter fields: `isActive``
  - _filter fields ['isActive'] are not covered by any index on `api_keys` (indexed leading fields: ['createdBy', 'keyHash'])_
  - Suggestion: Add an index on `isActive` (or a compound index starting with it) on `api_keys`.
  ```go
  cursor, err := h.db.APIKeys().Find(r.Context(), bson.M{"isActive": true}, opts)
  ```
- **[MEDIUM] No covering index** — `backend/internal/api/handlers/apikeys.go:60` `CountDocuments` on `api_keys` in `ListAPIKeys`
  - Filter fields: `isActive``
  - _filter fields ['isActive'] are not covered by any index on `api_keys` (indexed leading fields: ['createdBy', 'keyHash'])_
  - Suggestion: Add an index on `isActive` (or a compound index starting with it) on `api_keys`.
  ```go
  total, err := h.db.APIKeys().CountDocuments(r.Context(), bson.M{"isActive": true})
  ```

### `backend/internal/api/handlers/billing.go`

- **[MEDIUM] Multi-tenant query without tenantId filter** — `backend/internal/api/handlers/billing.go:736` `CountDocuments` on `financial_transactions` in `AdminListTransactions`
  - Filter fields: —
  - _empty-filter query on multi-tenant collection `financial_transactions` — full collection scan, risks cross-tenant data leak_
  - Suggestion: Add a `tenantId` filter (or scope the collection accessor to the current tenant) to avoid a full collection scan.
  ```go
  total, err := h.db.FinancialTransactions().CountDocuments(ctx, filter)
  ```
- **[MEDIUM] Multi-tenant query without tenantId filter** — `backend/internal/api/handlers/billing.go:747` `Find` on `financial_transactions` in `AdminListTransactions`
  - Filter fields: —
  - _empty-filter query on multi-tenant collection `financial_transactions` — full collection scan, risks cross-tenant data leak_
  - Suggestion: Add a `tenantId` filter (or scope the collection accessor to the current tenant) to avoid a full collection scan.
  ```go
  cursor, err := h.db.FinancialTransactions().Find(ctx, filter, opts)
  ```

### `backend/internal/api/handlers/logs.go`

- **[MEDIUM] Multi-tenant query without tenantId filter** — `backend/internal/api/handlers/logs.go:198` `Find` on `system_logs` in `ExportCSV`
  - Filter fields: —
  - _empty-filter query on multi-tenant collection `system_logs` — full collection scan, risks cross-tenant data leak_
  - Suggestion: Add a `tenantId` filter (or scope the collection accessor to the current tenant) to avoid a full collection scan.
  ```go
  cursor, err := h.db.SystemLogs().Find(ctx, filter, opts)
  ```

### `backend/internal/api/handlers/promotions.go`

- **[MEDIUM] No covering index** — `backend/internal/api/handlers/promotions.go:200` `Find` on `plans` in `ListEligibleProducts`
  - Filter fields: `isArchived``
  - _filter fields ['isArchived'] are not covered by any index on `plans` (indexed leading fields: ['isSystem', 'name'])_
  - Suggestion: Add an index on `isArchived` (or a compound index starting with it) on `plans`.
  ```go
  planCursor, err := h.db.Plans().Find(ctx, bson.M{"isArchived": bson.M{"$ne": true}})
  ```
- **[MEDIUM] No covering index** — `backend/internal/api/handlers/promotions.go:226` `Find` on `credit_bundles` in `ListEligibleProducts`
  - Filter fields: `isActive``
  - _filter fields ['isActive'] are not covered by any index on `credit_bundles` (indexed leading fields: ['name', 'sortOrder'])_
  - Suggestion: Add an index on `isActive` (or a compound index starting with it) on `credit_bundles`.
  ```go
  bundleCursor, err := h.db.CreditBundles().Find(ctx, bson.M{"isActive": true})
  ```

### `backend/internal/api/handlers/webhook.go`

- **[MEDIUM] No covering index** — `backend/internal/api/handlers/webhook.go:391` `FindOne` on `tenants` in `handleInvoicePaid`
  - Filter fields: `stripeSubscriptionId``
  - _filter fields ['stripeSubscriptionId'] are not covered by any index on `tenants` (indexed leading fields: ['billingStatus', 'isRoot', 'name', 'planId', 'slug', 'trialUsedAt'])_
  - Suggestion: Add an index on `stripeSubscriptionId` (or a compound index starting with it) on `tenants`.
  ```go
  if err := h.db.Tenants().FindOne(ctx, bson.M{"stripeSubscriptionId": subscriptionID}).Decode(&tenant); err != nil {
  ```
- **[MEDIUM] No covering index** — `backend/internal/api/handlers/webhook.go:482` `FindOne` on `tenants` in `handleInvoicePaymentFailed`
  - Filter fields: `stripeSubscriptionId``
  - _filter fields ['stripeSubscriptionId'] are not covered by any index on `tenants` (indexed leading fields: ['billingStatus', 'isRoot', 'name', 'planId', 'slug', 'trialUsedAt'])_
  - Suggestion: Add an index on `stripeSubscriptionId` (or a compound index starting with it) on `tenants`.
  ```go
  if err := h.db.Tenants().FindOne(ctx, bson.M{"stripeSubscriptionId": subscriptionID}).Decode(&tenant); err != nil {
  ```
- **[MEDIUM] No covering index** — `backend/internal/api/handlers/webhook.go:551` `FindOne` on `tenants` in `handleSubscriptionUpdated`
  - Filter fields: `stripeSubscriptionId``
  - _filter fields ['stripeSubscriptionId'] are not covered by any index on `tenants` (indexed leading fields: ['billingStatus', 'isRoot', 'name', 'planId', 'slug', 'trialUsedAt'])_
  - Suggestion: Add an index on `stripeSubscriptionId` (or a compound index starting with it) on `tenants`.
  ```go
  if err := h.db.Tenants().FindOne(ctx, bson.M{"stripeSubscriptionId": sub.ID}).Decode(&tenant); err != nil {
  ```
- **[MEDIUM] No covering index** — `backend/internal/api/handlers/webhook.go:613` `FindOne` on `tenants` in `handleSubscriptionDeleted`
  - Filter fields: `stripeSubscriptionId``
  - _filter fields ['stripeSubscriptionId'] are not covered by any index on `tenants` (indexed leading fields: ['billingStatus', 'isRoot', 'name', 'planId', 'slug', 'trialUsedAt'])_
  - Suggestion: Add an index on `stripeSubscriptionId` (or a compound index starting with it) on `tenants`.
  ```go
  if err := h.db.Tenants().FindOne(ctx, bson.M{"stripeSubscriptionId": sub.ID}).Decode(&tenant); err != nil {
  ```
- **[MEDIUM] No covering index** — `backend/internal/api/handlers/webhook.go:675` `FindOne` on `tenants` in `handleChargeRefunded`
  - Filter fields: `stripeCustomerId``
  - _filter fields ['stripeCustomerId'] are not covered by any index on `tenants` (indexed leading fields: ['billingStatus', 'isRoot', 'name', 'planId', 'slug', 'trialUsedAt'])_
  - Suggestion: Add an index on `stripeCustomerId` (or a compound index starting with it) on `tenants`.
  ```go
  if err := h.db.Tenants().FindOne(ctx, bson.M{"stripeCustomerId": charge.Customer.ID}).Decode(&tenant); err != nil {
  ```
- **[MEDIUM] No covering index** — `backend/internal/api/handlers/webhook.go:726` `FindOne` on `tenants` in `handleDisputeCreated`
  - Filter fields: `stripeCustomerId``
  - _filter fields ['stripeCustomerId'] are not covered by any index on `tenants` (indexed leading fields: ['billingStatus', 'isRoot', 'name', 'planId', 'slug', 'trialUsedAt'])_
  - Suggestion: Add an index on `stripeCustomerId` (or a compound index starting with it) on `tenants`.
  ```go
  if err := h.db.Tenants().FindOne(ctx, bson.M{"stripeCustomerId": customerID}).Decode(&tenant); err != nil {
  ```
- **[MEDIUM] No covering index** — `backend/internal/api/handlers/webhook.go:771` `FindOne` on `tenants` in `handleDisputeClosed`
  - Filter fields: `stripeCustomerId``
  - _filter fields ['stripeCustomerId'] are not covered by any index on `tenants` (indexed leading fields: ['billingStatus', 'isRoot', 'name', 'planId', 'slug', 'trialUsedAt'])_
  - Suggestion: Add an index on `stripeCustomerId` (or a compound index starting with it) on `tenants`.
  ```go
  if err := h.db.Tenants().FindOne(ctx, bson.M{"stripeCustomerId": customerID}).Decode(&tenant); err != nil {
  ```

### `backend/internal/api/handlers/webhooks.go`

- **[MEDIUM] No covering index** — `backend/internal/api/handlers/webhooks.go:45` `Find` on `webhooks` in `ListWebhooks`
  - Filter fields: `isActive``
  - _filter fields ['isActive'] are not covered by any index on `webhooks` (indexed leading fields: ['createdBy', 'events'])_
  - Suggestion: Add an index on `isActive` (or a compound index starting with it) on `webhooks`.
  ```go
  cursor, err := h.db.Webhooks().Find(ctx, bson.M{"isActive": true}, opts)
  ```
- **[MEDIUM] No covering index** — `backend/internal/api/handlers/webhooks.go:88` `CountDocuments` on `webhooks` in `ListWebhooks`
  - Filter fields: `isActive``
  - _filter fields ['isActive'] are not covered by any index on `webhooks` (indexed leading fields: ['createdBy', 'events'])_
  - Suggestion: Add an index on `isActive` (or a compound index starting with it) on `webhooks`.
  ```go
  total, err := h.db.Webhooks().CountDocuments(ctx, bson.M{"isActive": true})
  ```

### `backend/internal/telemetry/service.go`

- **[MEDIUM] No covering index** — `backend/internal/telemetry/service.go:624` `CountDocuments` on `tenants` in `computeKPIs`
  - Filter fields: `canceledAt``
  - _filter fields ['canceledAt'] are not covered by any index on `tenants` (indexed leading fields: ['billingStatus', 'isRoot', 'name', 'planId', 'slug', 'trialUsedAt'])_
  - Suggestion: Add an index on `canceledAt` (or a compound index starting with it) on `tenants`.
  ```go
  canceledThisMonth, err := s.db.Tenants().CountDocuments(ctx, bson.M{
  ```

## Index Inventory (parsed from source)

The following indexes were detected by scanning the codebase for `mongo.IndexModel{...}` declarations inside `Indexes().CreateMany` / `CreateOne` calls.

| Collection | Indexes | Unique | Indexed fields (any) | Leading fields |
| --- | ---: | --- | --- | --- |
| `api_keys` | 2 | yes | `createdAt`, `createdBy`, `keyHash` | `createdBy`, `keyHash` |
| `audit_log` | 3 | no | `createdAt`, `tenantId`, `userId` | `createdAt`, `tenantId`, `userId` |
| `auth_codes` | 2 | yes | `code`, `expiresAt` | `code`, `expiresAt` |
| `branding_assets` | 1 | yes | `key` | `key` |
| `config_vars` | 1 | yes | `name` | `name` |
| `credit_bundles` | 2 | yes | `name`, `sortOrder` | `name`, `sortOrder` |
| `custom_pages` | 2 | yes | `isPublished`, `slug`, `sortOrder` | `isPublished`, `slug` |
| `daily_metrics` | 2 | yes | `createdAt`, `date` | `createdAt`, `date` |
| `event_definitions` | 2 | yes | `name`, `parentId` | `name`, `parentId` |
| `financial_transactions` | 3 | yes | `createdAt`, `invoiceNumber`, `tenantId`, `userId` | `invoiceNumber`, `tenantId`, `userId` |
| `invitations` | 3 | yes | `email`, `expiresAt`, `tenantId`, `token` | `expiresAt`, `tenantId`, `token` |
| `leader_locks` | 1 | no | `expiresAt` | `expiresAt` |
| `messages` | 2 | no | `createdAt`, `read`, `userId` | `userId` |
| `oauth_states` | 1 | no | `expiresAt` | `expiresAt` |
| `plans` | 2 | yes | `isSystem`, `name` | `isSystem`, `name` |
| `rate_limits` | 1 | no | `expiresAt` | `expiresAt` |
| `refresh_tokens` | 4 | yes | `expiresAt`, `familyId`, `tokenHash`, `userId` | `expiresAt`, `familyId`, `tokenHash`, `userId` |
| `revoked_tokens` | 2 | yes | `expiresAt`, `tokenHash` | `expiresAt`, `tokenHash` |
| `sso_connections` | 1 | yes | `tenantId` | `tenantId` |
| `stripe_mappings` | 1 | yes | `entityId`, `entityType` | `entityType` |
| `system_logs` | 6 | no | `category`, `createdAt`, `message`, `severity`, `tenantId`, `userId` | `category`, `createdAt`, `message`, `severity`, `tenantId`, `userId` |
| `system_metrics` | 2 | no | `nodeId`, `timestamp` | `nodeId`, `timestamp` |
| `system_nodes` | 3 | yes | `lastSeen`, `machineId`, `startedAt` | `lastSeen`, `machineId`, `startedAt` |
| `telemetry_events` | 6 | no | `category`, `createdAt`, `eventName`, `properties`, `sessionId`, `userId` | `category`, `createdAt`, `eventName`, `properties`, `sessionId`, `userId` |
| `tenant_memberships` | 3 | yes | `role`, `tenantId`, `userId` | `tenantId`, `userId` |
| `tenants` | 6 | yes | `billingStatus`, `isActive`, `isRoot`, `name`, `planId`, `slug`, `trialUsedAt` | `billingStatus`, `isRoot`, `name`, `planId`, `slug`, `trialUsedAt` |
| `usage_events` | 3 | no | `createdAt`, `tenantId`, `type` | `createdAt`, `tenantId` |
| `users` | 5 | yes | `displayName`, `email`, `githubId`, `googleId`, `microsoftId` | `displayName`, `email`, `githubId`, `googleId`, `microsoftId` |
| `verification_tokens` | 3 | no | `expiresAt`, `token`, `type`, `userId` | `expiresAt`, `token`, `userId` |
| `webauthn_credentials` | 2 | yes | `credentialId`, `userId` | `credentialId`, `userId` |
| `webauthn_sessions` | 1 | no | `expiresAt` | `expiresAt` |
| `webhook_deliveries` | 2 | no | `createdAt`, `webhookId` | `createdAt`, `webhookId` |
| `webhook_events` | 2 | yes | `createdAt`, `eventId` | `createdAt`, `eventId` |
| `webhooks` | 2 | no | `createdAt`, `createdBy`, `events`, `isActive` | `createdBy`, `events` |

## Methodology

1. **Index inventory.** Every `.go` file is scanned for `mongo.IndexModel{ Keys: bson.D{...}, Options: ... }` literals. Each IndexModel's collection is resolved by walking *backwards* to find the nearest preceding collection-binding site (`db.Collection("name")` literal, alias variable, or a `Collection("name").Indexes()` call on the same expression). Single-field and compound indexes are recorded; for compound indexes only the leading field is treated as a 'covering' field for queries.
2. **Query scan.** Every MongoDB collection method call (Find, FindOne, UpdateOne, DeleteOne, CountDocuments, ...) is located and its first-argument filter is parsed from the `bson.M{}` / `bson.D{}` literal. Multi-line literals are captured via a small look-ahead window. Option-builder calls like `options.Find()` are skipped.
3. **Coverage check.** For each query the filter fields are compared against the collection's index inventory. A query is covered if any of its filter fields is the leading field of any index (single-field or compound). Queries with no covering index are flagged.
4. **Spec check.** Each query is also checked against a small set of SaaS-domain index rules: `tenantId` on multi-tenant collections, `email` on `users`, `slug` on `tenants`, `token` on invitation/token collections, etc. Queries that filter on a spec-required field that is not indexed are flagged.
5. **Multi-tenant hygiene.** Queries on multi-tenant collections that do not filter by `tenantId` are flagged separately — these risk cross-tenant data leaks and force full-collection scans.
6. **Risk.** HIGH for queries on large collections (logs, events, telemetry, audit, deliveries, metrics) without a covering index, and for any query on a spec-required field that is missing the index. MEDIUM for small/static-data collections without coverage (announcements, plans, webhooks, api_keys, etc. — full scan is sub-millisecond on <100 docs) and for multi-tenant queries without a tenantId filter. Admin/CLI scopes (admin.go, cmd/lastsaas/) are downgraded to MEDIUM — they legitimately scan across tenants. Single-document collections (branding_config, system_config) are suppressed entirely.

---
_Generated by `graphify missing-indexes`._