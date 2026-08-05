# Missing Index Report

**Target:** `/home/z/my-project/repos/lastsaas/backend`

For every MongoDB query in the codebase, checks whether the filter fields are covered by a declared index. Indexes are parsed from `Indexes().CreateMany(...)` / `CreateOne(...)` calls in the codebase (`internal/db/mongodb.go::ensureIndexes`, `internal/middleware/ratelimit.go`, etc.).

## Summary

| Metric | Value |
| --- | --- |
| Queries scanned | 413 |
| Total findings | **48** |
| HIGH severity | 21 |
| MEDIUM severity | 27 |
| LOW severity | 0 |

## Findings by Type

| Type | Count |
| --- | ---: |
| Multi-tenant query without tenantId filter | 28 |
| No covering index | 19 |
| Collection has no declared indexes | 1 |

## Collections Affected

| Collection | Findings |
| --- | ---: |
| `tenant_memberships` | 10 |
| `tenants` | 8 |
| `system_logs` | 7 |
| `financial_transactions` | 6 |
| `messages` | 3 |
| `users` | 2 |
| `announcements` | 2 |
| `credit_bundles` | 2 |
| `webhooks` | 2 |
| `api_keys` | 2 |
| `telemetry_events` | 1 |
| `plans` | 1 |
| `webhook_deliveries` | 1 |
| `refresh_tokens` | 1 |

## Collections Queried But With No Declared Indexes

These collections are queried in the codebase but have no `Indexes().CreateMany/CreateOne` call anywhere — every query will be a full collection scan (modulo the default `_id` index).

- `announcements`
- `branding_config`
- `system_config`

## Files With Most Findings

| File | Findings |
| --- | ---: |
| `internal/api/handlers/webhook.go` | 7 |
| `internal/api/handlers/tenant.go` | 5 |
| `internal/telemetry/service.go` | 4 |
| `internal/api/handlers/billing.go` | 4 |
| `internal/api/handlers/admin.go` | 4 |
| `cmd/lastsaas/main.go` | 3 |
| `internal/api/handlers/logs.go` | 3 |
| `internal/api/handlers/messages.go` | 3 |
| `internal/api/handlers/webhooks.go` | 3 |
| `cmd/lastsaas/cmd_logs.go` | 2 |
| `internal/api/handlers/announcements.go` | 2 |
| `internal/api/handlers/promotions.go` | 2 |
| `internal/api/handlers/apikeys.go` | 2 |
| `cmd/lastsaas/cmd_stats.go` | 1 |
| `cmd/lastsaas/cmd_financial.go` | 1 |
| `internal/api/handlers/bundles.go` | 1 |
| `internal/api/handlers/auth.go` | 1 |

## Detailed Findings

### `cmd/lastsaas/cmd_financial.go`

- **[HIGH] Multi-tenant query without tenantId filter** — `cmd/lastsaas/cmd_financial.go:254` `Find` on `financial_transactions` in `cmdFinancialTransactions`
  - Filter fields: —
  - _empty-filter query on multi-tenant collection `financial_transactions` — full collection scan, risks cross-tenant data leak_
  - Suggestion: Add a `tenantId` filter (or scope the collection accessor to the current tenant) to avoid a full collection scan.
  ```go
  cursor, err := database.FinancialTransactions().Find(ctx, filter, opts)
  ```

### `cmd/lastsaas/cmd_logs.go`

- **[HIGH] Multi-tenant query without tenantId filter** — `cmd/lastsaas/cmd_logs.go:140` `Find` on `system_logs` in `queryLogs`
  - Filter fields: —
  - _empty-filter query on multi-tenant collection `system_logs` — full collection scan, risks cross-tenant data leak_
  - Suggestion: Add a `tenantId` filter (or scope the collection accessor to the current tenant) to avoid a full collection scan.
  ```go
  cursor, err := database.SystemLogs().Find(ctx, filter, opts)
  ```
- **[HIGH] Multi-tenant query without tenantId filter** — `cmd/lastsaas/cmd_logs.go:193` `Find` on `system_logs` in `logsFollow`
  - Filter fields: —
  - _empty-filter query on multi-tenant collection `system_logs` — full collection scan, risks cross-tenant data leak_
  - Suggestion: Add a `tenantId` filter (or scope the collection accessor to the current tenant) to avoid a full collection scan.
  ```go
  cursor, err := database.SystemLogs().Find(ctx, followFilter, opts)
  ```

### `cmd/lastsaas/cmd_stats.go`

- **[MEDIUM] No covering index** — `cmd/lastsaas/cmd_stats.go:31` `CountDocuments` on `users` in `cmdStats`
  - Filter fields: `isActive``
  - _filter fields ['isActive'] are not covered by any index on `users` (indexed leading fields: ['displayName', 'email', 'githubId', 'googleId', 'microsoftId'])_
  - Suggestion: Add an index on `isActive` (or a compound index starting with it) on `users`.
  ```go
  activeUsers, err := database.Users().CountDocuments(ctx, bson.M{"isActive": true})
  ```

### `cmd/lastsaas/main.go`

- **[MEDIUM] Multi-tenant query without tenantId filter** — `cmd/lastsaas/main.go:831` `UpdateOne` on `tenant_memberships` in `cmdTransferRootOwner`
  - Filter fields: —
  - _empty-filter query on multi-tenant collection `tenant_memberships` — full collection scan, risks cross-tenant data leak_
  - Suggestion: Add a `tenantId` filter (or scope the collection accessor to the current tenant) to avoid a full collection scan.
  ```go
  _, err = database.TenantMemberships().UpdateOne(ctx,
  ```
- **[MEDIUM] Multi-tenant query without tenantId filter** — `cmd/lastsaas/main.go:841` `UpdateOne` on `tenant_memberships` in `cmdTransferRootOwner`
  - Filter fields: —
  - _empty-filter query on multi-tenant collection `tenant_memberships` — full collection scan, risks cross-tenant data leak_
  - Suggestion: Add a `tenantId` filter (or scope the collection accessor to the current tenant) to avoid a full collection scan.
  ```go
  _, err = database.TenantMemberships().UpdateOne(ctx,
  ```
- **[MEDIUM] Multi-tenant query without tenantId filter** — `cmd/lastsaas/main.go:847` `UpdateOne` on `tenant_memberships` in `cmdTransferRootOwner`
  - Filter fields: —
  - _empty-filter query on multi-tenant collection `tenant_memberships` — full collection scan, risks cross-tenant data leak_
  - Suggestion: Add a `tenantId` filter (or scope the collection accessor to the current tenant) to avoid a full collection scan.
  ```go
  database.TenantMemberships().UpdateOne(ctx,
  ```

### `internal/api/handlers/admin.go`

- **[MEDIUM] Multi-tenant query without tenantId filter** — `internal/api/handlers/admin.go:1186` `UpdateOne` on `tenant_memberships` in `UpdateUserRole`
  - Filter fields: —
  - _empty-filter query on multi-tenant collection `tenant_memberships` — full collection scan, risks cross-tenant data leak_
  - Suggestion: Add a `tenantId` filter (or scope the collection accessor to the current tenant) to avoid a full collection scan.
  ```go
  h.db.TenantMemberships().UpdateOne(ctx,
  ```
- **[MEDIUM] Multi-tenant query without tenantId filter** — `internal/api/handlers/admin.go:1193` `UpdateOne` on `tenant_memberships` in `UpdateUserRole`
  - Filter fields: —
  - _empty-filter query on multi-tenant collection `tenant_memberships` — full collection scan, risks cross-tenant data leak_
  - Suggestion: Add a `tenantId` filter (or scope the collection accessor to the current tenant) to avoid a full collection scan.
  ```go
  result, err := h.db.TenantMemberships().UpdateOne(ctx,
  ```
- **[MEDIUM] Multi-tenant query without tenantId filter** — `internal/api/handlers/admin.go:1414` `UpdateOne` on `tenant_memberships` in `DeleteUser`
  - Filter fields: —
  - _empty-filter query on multi-tenant collection `tenant_memberships` — full collection scan, risks cross-tenant data leak_
  - Suggestion: Add a `tenantId` filter (or scope the collection accessor to the current tenant) to avoid a full collection scan.
  ```go
  result, err := h.db.TenantMemberships().UpdateOne(ctx,
  ```
- **[MEDIUM] Multi-tenant query without tenantId filter** — `internal/api/handlers/admin.go:2032` `UpdateOne` on `tenant_memberships` in `ChangeRootMemberRole`
  - Filter fields: —
  - _empty-filter query on multi-tenant collection `tenant_memberships` — full collection scan, risks cross-tenant data leak_
  - Suggestion: Add a `tenantId` filter (or scope the collection accessor to the current tenant) to avoid a full collection scan.
  ```go
  result, err := h.db.TenantMemberships().UpdateOne(ctx,
  ```

### `internal/api/handlers/announcements.go`

- **[HIGH] Collection has no declared indexes** — `internal/api/handlers/announcements.go:33` `Find` on `announcements` in `ListPublic`
  - Filter fields: `isPublished``
  - _collection `announcements` has no declared indexes — every query scans the full collection_
  - Suggestion: Add an index on the most-filtered field(s) of `announcements` (e.g. `isPublished` based on this query).
  ```go
  cursor, err := h.db.Announcements().Find(r.Context(), bson.M{"isPublished": true}, opts)
  ```
- **[HIGH] Multi-tenant query without tenantId filter** — `internal/api/handlers/announcements.go:54` `Find` on `announcements` in `ListAll`
  - Filter fields: —
  - _empty-filter query on multi-tenant collection `announcements` — full collection scan, risks cross-tenant data leak_
  - Suggestion: Add a `tenantId` filter (or scope the collection accessor to the current tenant) to avoid a full collection scan.
  ```go
  cursor, err := h.db.Announcements().Find(r.Context(), bson.M{}, opts)
  ```

### `internal/api/handlers/apikeys.go`

- **[MEDIUM] No covering index** — `internal/api/handlers/apikeys.go:45` `Find` on `api_keys` in `ListAPIKeys`
  - Filter fields: `isActive``
  - _filter fields ['isActive'] are not covered by any index on `api_keys` (indexed leading fields: ['createdBy', 'keyHash'])_
  - Suggestion: Add an index on `isActive` (or a compound index starting with it) on `api_keys`.
  ```go
  cursor, err := h.db.APIKeys().Find(r.Context(), bson.M{"isActive": true}, opts)
  ```
- **[MEDIUM] No covering index** — `internal/api/handlers/apikeys.go:60` `CountDocuments` on `api_keys` in `ListAPIKeys`
  - Filter fields: `isActive``
  - _filter fields ['isActive'] are not covered by any index on `api_keys` (indexed leading fields: ['createdBy', 'keyHash'])_
  - Suggestion: Add an index on `isActive` (or a compound index starting with it) on `api_keys`.
  ```go
  total, err := h.db.APIKeys().CountDocuments(r.Context(), bson.M{"isActive": true})
  ```

### `internal/api/handlers/auth.go`

- **[HIGH] No covering index** — `internal/api/handlers/auth.go:503` `FindOne` on `refresh_tokens` in `Refresh`
  - Filter fields: `tokenHash``
  - _filter fields ['tokenHash'] are not covered by any index on `refresh_tokens` (indexed leading fields: ['expiresAt', 'userId'])_
  - Suggestion: Add an index on `tokenHash` (or a compound index starting with it) on `refresh_tokens`.
  ```go
  err = h.db.RefreshTokens().FindOne(r.Context(), bson.M{
  ```

### `internal/api/handlers/billing.go`

- **[HIGH] Multi-tenant query without tenantId filter** — `internal/api/handlers/billing.go:403` `CountDocuments` on `financial_transactions` in `ListTransactions`
  - Filter fields: —
  - _empty-filter query on multi-tenant collection `financial_transactions` — full collection scan, risks cross-tenant data leak_
  - Suggestion: Add a `tenantId` filter (or scope the collection accessor to the current tenant) to avoid a full collection scan.
  ```go
  total, err := h.db.FinancialTransactions().CountDocuments(ctx, filter)
  ```
- **[HIGH] Multi-tenant query without tenantId filter** — `internal/api/handlers/billing.go:414` `Find` on `financial_transactions` in `ListTransactions`
  - Filter fields: —
  - _empty-filter query on multi-tenant collection `financial_transactions` — full collection scan, risks cross-tenant data leak_
  - Suggestion: Add a `tenantId` filter (or scope the collection accessor to the current tenant) to avoid a full collection scan.
  ```go
  cursor, err := h.db.FinancialTransactions().Find(ctx, filter, opts)
  ```
- **[HIGH] Multi-tenant query without tenantId filter** — `internal/api/handlers/billing.go:733` `CountDocuments` on `financial_transactions` in `AdminListTransactions`
  - Filter fields: —
  - _empty-filter query on multi-tenant collection `financial_transactions` — full collection scan, risks cross-tenant data leak_
  - Suggestion: Add a `tenantId` filter (or scope the collection accessor to the current tenant) to avoid a full collection scan.
  ```go
  total, err := h.db.FinancialTransactions().CountDocuments(ctx, filter)
  ```
- **[HIGH] Multi-tenant query without tenantId filter** — `internal/api/handlers/billing.go:744` `Find` on `financial_transactions` in `AdminListTransactions`
  - Filter fields: —
  - _empty-filter query on multi-tenant collection `financial_transactions` — full collection scan, risks cross-tenant data leak_
  - Suggestion: Add a `tenantId` filter (or scope the collection accessor to the current tenant) to avoid a full collection scan.
  ```go
  cursor, err := h.db.FinancialTransactions().Find(ctx, filter, opts)
  ```

### `internal/api/handlers/bundles.go`

- **[MEDIUM] No covering index** — `internal/api/handlers/bundles.go:236` `Find` on `credit_bundles` in `ListBundlesPublic`
  - Filter fields: `isActive``
  - _filter fields ['isActive'] are not covered by any index on `credit_bundles` (indexed leading fields: ['name', 'sortOrder'])_
  - Suggestion: Add an index on `isActive` (or a compound index starting with it) on `credit_bundles`.
  ```go
  cursor, err := h.db.CreditBundles().Find(r.Context(), bson.M{"isActive": true}, opts)
  ```

### `internal/api/handlers/logs.go`

- **[HIGH] Multi-tenant query without tenantId filter** — `internal/api/handlers/logs.go:113` `CountDocuments` on `system_logs` in `ListLogs`
  - Filter fields: —
  - _empty-filter query on multi-tenant collection `system_logs` — full collection scan, risks cross-tenant data leak_
  - Suggestion: Add a `tenantId` filter (or scope the collection accessor to the current tenant) to avoid a full collection scan.
  ```go
  total, err = h.db.SystemLogs().CountDocuments(ctx, filter)
  ```
- **[HIGH] Multi-tenant query without tenantId filter** — `internal/api/handlers/logs.go:125` `Find` on `system_logs` in `ListLogs`
  - Filter fields: —
  - _empty-filter query on multi-tenant collection `system_logs` — full collection scan, risks cross-tenant data leak_
  - Suggestion: Add a `tenantId` filter (or scope the collection accessor to the current tenant) to avoid a full collection scan.
  ```go
  cursor, err := h.db.SystemLogs().Find(ctx, filter, opts)
  ```
- **[HIGH] Multi-tenant query without tenantId filter** — `internal/api/handlers/logs.go:196` `Find` on `system_logs` in `ExportCSV`
  - Filter fields: —
  - _empty-filter query on multi-tenant collection `system_logs` — full collection scan, risks cross-tenant data leak_
  - Suggestion: Add a `tenantId` filter (or scope the collection accessor to the current tenant) to avoid a full collection scan.
  ```go
  cursor, err := h.db.SystemLogs().Find(ctx, filter, opts)
  ```

### `internal/api/handlers/messages.go`

- **[HIGH] Multi-tenant query without tenantId filter** — `internal/api/handlers/messages.go:36` `Find` on `messages` in `ListMessages`
  - Filter fields: —
  - _empty-filter query on multi-tenant collection `messages` — full collection scan, risks cross-tenant data leak_
  - Suggestion: Add a `tenantId` filter (or scope the collection accessor to the current tenant) to avoid a full collection scan.
  ```go
  cursor, err := h.db.Messages().Find(r.Context(),
  ```
- **[HIGH] Multi-tenant query without tenantId filter** — `internal/api/handlers/messages.go:64` `CountDocuments` on `messages` in `UnreadCount`
  - Filter fields: —
  - _empty-filter query on multi-tenant collection `messages` — full collection scan, risks cross-tenant data leak_
  - Suggestion: Add a `tenantId` filter (or scope the collection accessor to the current tenant) to avoid a full collection scan.
  ```go
  count, err := h.db.Messages().CountDocuments(r.Context(),
  ```
- **[HIGH] Multi-tenant query without tenantId filter** — `internal/api/handlers/messages.go:88` `UpdateOne` on `messages` in `MarkRead`
  - Filter fields: —
  - _empty-filter query on multi-tenant collection `messages` — full collection scan, risks cross-tenant data leak_
  - Suggestion: Add a `tenantId` filter (or scope the collection accessor to the current tenant) to avoid a full collection scan.
  ```go
  result, err := h.db.Messages().UpdateOne(r.Context(),
  ```

### `internal/api/handlers/promotions.go`

- **[MEDIUM] No covering index** — `internal/api/handlers/promotions.go:200` `Find` on `plans` in `ListEligibleProducts`
  - Filter fields: `isArchived``
  - _filter fields ['isArchived'] are not covered by any index on `plans` (indexed leading fields: ['isSystem', 'name'])_
  - Suggestion: Add an index on `isArchived` (or a compound index starting with it) on `plans`.
  ```go
  planCursor, err := h.db.Plans().Find(ctx, bson.M{"isArchived": bson.M{"$ne": true}})
  ```
- **[MEDIUM] No covering index** — `internal/api/handlers/promotions.go:226` `Find` on `credit_bundles` in `ListEligibleProducts`
  - Filter fields: `isActive``
  - _filter fields ['isActive'] are not covered by any index on `credit_bundles` (indexed leading fields: ['name', 'sortOrder'])_
  - Suggestion: Add an index on `isActive` (or a compound index starting with it) on `credit_bundles`.
  ```go
  bundleCursor, err := h.db.CreditBundles().Find(ctx, bson.M{"isActive": true})
  ```

### `internal/api/handlers/tenant.go`

- **[HIGH] Multi-tenant query without tenantId filter** — `internal/api/handlers/tenant.go:593` `Find` on `system_logs` in `GetActivity`
  - Filter fields: —
  - _empty-filter query on multi-tenant collection `system_logs` — full collection scan, risks cross-tenant data leak_
  - Suggestion: Add a `tenantId` filter (or scope the collection accessor to the current tenant) to avoid a full collection scan.
  ```go
  cursor, err := h.db.SystemLogs().Find(r.Context(), filter, opts)
  ```
- **[HIGH] Multi-tenant query without tenantId filter** — `internal/api/handlers/tenant.go:606` `CountDocuments` on `system_logs` in `GetActivity`
  - Filter fields: —
  - _empty-filter query on multi-tenant collection `system_logs` — full collection scan, risks cross-tenant data leak_
  - Suggestion: Add a `tenantId` filter (or scope the collection accessor to the current tenant) to avoid a full collection scan.
  ```go
  total, err := h.db.SystemLogs().CountDocuments(r.Context(), filter)
  ```
- **[MEDIUM] Multi-tenant query without tenantId filter** — `internal/api/handlers/tenant.go:456` `UpdateOne` on `tenant_memberships` in `ChangeRole`
  - Filter fields: —
  - _empty-filter query on multi-tenant collection `tenant_memberships` — full collection scan, risks cross-tenant data leak_
  - Suggestion: Add a `tenantId` filter (or scope the collection accessor to the current tenant) to avoid a full collection scan.
  ```go
  result, err := h.db.TenantMemberships().UpdateOne(r.Context(),
  ```
- **[MEDIUM] Multi-tenant query without tenantId filter** — `internal/api/handlers/tenant.go:524` `UpdateOne` on `tenant_memberships` in `TransferOwnership`
  - Filter fields: —
  - _empty-filter query on multi-tenant collection `tenant_memberships` — full collection scan, risks cross-tenant data leak_
  - Suggestion: Add a `tenantId` filter (or scope the collection accessor to the current tenant) to avoid a full collection scan.
  ```go
  if _, err := h.db.TenantMemberships().UpdateOne(r.Context(),
  ```
- **[MEDIUM] Multi-tenant query without tenantId filter** — `internal/api/handlers/tenant.go:534` `UpdateOne` on `tenant_memberships` in `TransferOwnership`
  - Filter fields: —
  - _empty-filter query on multi-tenant collection `tenant_memberships` — full collection scan, risks cross-tenant data leak_
  - Suggestion: Add a `tenantId` filter (or scope the collection accessor to the current tenant) to avoid a full collection scan.
  ```go
  if _, err := h.db.TenantMemberships().UpdateOne(r.Context(),
  ```

### `internal/api/handlers/webhook.go`

- **[MEDIUM] No covering index** — `internal/api/handlers/webhook.go:391` `FindOne` on `tenants` in `handleInvoicePaid`
  - Filter fields: `stripeSubscriptionId``
  - _filter fields ['stripeSubscriptionId'] are not covered by any index on `tenants` (indexed leading fields: ['billingStatus', 'isRoot', 'name', 'planId', 'slug', 'trialUsedAt'])_
  - Suggestion: Add an index on `stripeSubscriptionId` (or a compound index starting with it) on `tenants`.
  ```go
  if err := h.db.Tenants().FindOne(ctx, bson.M{"stripeSubscriptionId": subscriptionID}).Decode(&tenant); err != nil {
  ```
- **[MEDIUM] No covering index** — `internal/api/handlers/webhook.go:482` `FindOne` on `tenants` in `handleInvoicePaymentFailed`
  - Filter fields: `stripeSubscriptionId``
  - _filter fields ['stripeSubscriptionId'] are not covered by any index on `tenants` (indexed leading fields: ['billingStatus', 'isRoot', 'name', 'planId', 'slug', 'trialUsedAt'])_
  - Suggestion: Add an index on `stripeSubscriptionId` (or a compound index starting with it) on `tenants`.
  ```go
  if err := h.db.Tenants().FindOne(ctx, bson.M{"stripeSubscriptionId": subscriptionID}).Decode(&tenant); err != nil {
  ```
- **[MEDIUM] No covering index** — `internal/api/handlers/webhook.go:551` `FindOne` on `tenants` in `handleSubscriptionUpdated`
  - Filter fields: `stripeSubscriptionId``
  - _filter fields ['stripeSubscriptionId'] are not covered by any index on `tenants` (indexed leading fields: ['billingStatus', 'isRoot', 'name', 'planId', 'slug', 'trialUsedAt'])_
  - Suggestion: Add an index on `stripeSubscriptionId` (or a compound index starting with it) on `tenants`.
  ```go
  if err := h.db.Tenants().FindOne(ctx, bson.M{"stripeSubscriptionId": sub.ID}).Decode(&tenant); err != nil {
  ```
- **[MEDIUM] No covering index** — `internal/api/handlers/webhook.go:613` `FindOne` on `tenants` in `handleSubscriptionDeleted`
  - Filter fields: `stripeSubscriptionId``
  - _filter fields ['stripeSubscriptionId'] are not covered by any index on `tenants` (indexed leading fields: ['billingStatus', 'isRoot', 'name', 'planId', 'slug', 'trialUsedAt'])_
  - Suggestion: Add an index on `stripeSubscriptionId` (or a compound index starting with it) on `tenants`.
  ```go
  if err := h.db.Tenants().FindOne(ctx, bson.M{"stripeSubscriptionId": sub.ID}).Decode(&tenant); err != nil {
  ```
- **[MEDIUM] No covering index** — `internal/api/handlers/webhook.go:675` `FindOne` on `tenants` in `handleChargeRefunded`
  - Filter fields: `stripeCustomerId``
  - _filter fields ['stripeCustomerId'] are not covered by any index on `tenants` (indexed leading fields: ['billingStatus', 'isRoot', 'name', 'planId', 'slug', 'trialUsedAt'])_
  - Suggestion: Add an index on `stripeCustomerId` (or a compound index starting with it) on `tenants`.
  ```go
  if err := h.db.Tenants().FindOne(ctx, bson.M{"stripeCustomerId": charge.Customer.ID}).Decode(&tenant); err != nil {
  ```
- **[MEDIUM] No covering index** — `internal/api/handlers/webhook.go:726` `FindOne` on `tenants` in `handleDisputeCreated`
  - Filter fields: `stripeCustomerId``
  - _filter fields ['stripeCustomerId'] are not covered by any index on `tenants` (indexed leading fields: ['billingStatus', 'isRoot', 'name', 'planId', 'slug', 'trialUsedAt'])_
  - Suggestion: Add an index on `stripeCustomerId` (or a compound index starting with it) on `tenants`.
  ```go
  if err := h.db.Tenants().FindOne(ctx, bson.M{"stripeCustomerId": customerID}).Decode(&tenant); err != nil {
  ```
- **[MEDIUM] No covering index** — `internal/api/handlers/webhook.go:771` `FindOne` on `tenants` in `handleDisputeClosed`
  - Filter fields: `stripeCustomerId``
  - _filter fields ['stripeCustomerId'] are not covered by any index on `tenants` (indexed leading fields: ['billingStatus', 'isRoot', 'name', 'planId', 'slug', 'trialUsedAt'])_
  - Suggestion: Add an index on `stripeCustomerId` (or a compound index starting with it) on `tenants`.
  ```go
  if err := h.db.Tenants().FindOne(ctx, bson.M{"stripeCustomerId": customerID}).Decode(&tenant); err != nil {
  ```

### `internal/api/handlers/webhooks.go`

- **[HIGH] Multi-tenant query without tenantId filter** — `internal/api/handlers/webhooks.go:111` `Find` on `webhook_deliveries` in `GetWebhook`
  - Filter fields: —
  - _empty-filter query on multi-tenant collection `webhook_deliveries` — full collection scan, risks cross-tenant data leak_
  - Suggestion: Add a `tenantId` filter (or scope the collection accessor to the current tenant) to avoid a full collection scan.
  ```go
  cursor, err := h.db.WebhookDeliveries().Find(r.Context(),
  ```
- **[MEDIUM] No covering index** — `internal/api/handlers/webhooks.go:45` `Find` on `webhooks` in `ListWebhooks`
  - Filter fields: `isActive``
  - _filter fields ['isActive'] are not covered by any index on `webhooks` (indexed leading fields: ['createdBy', 'events'])_
  - Suggestion: Add an index on `isActive` (or a compound index starting with it) on `webhooks`.
  ```go
  cursor, err := h.db.Webhooks().Find(ctx, bson.M{"isActive": true}, opts)
  ```
- **[MEDIUM] No covering index** — `internal/api/handlers/webhooks.go:88` `CountDocuments` on `webhooks` in `ListWebhooks`
  - Filter fields: `isActive``
  - _filter fields ['isActive'] are not covered by any index on `webhooks` (indexed leading fields: ['createdBy', 'events'])_
  - Suggestion: Add an index on `isActive` (or a compound index starting with it) on `webhooks`.
  ```go
  total, err := h.db.Webhooks().CountDocuments(ctx, bson.M{"isActive": true})
  ```

### `internal/telemetry/service.go`

- **[HIGH] No covering index** — `internal/telemetry/service.go:347` `CountDocuments` on `financial_transactions` in `FunnelMetrics`
  - Filter fields: `type``, `createdAt``
  - _filter fields ['type', 'createdAt'] are not covered by any index on `financial_transactions` (indexed leading fields: ['invoiceNumber', 'tenantId', 'userId'])_
  - Suggestion: Add an index on `type` (or a compound index starting with it) on `financial_transactions`.
  ```go
  conversions, err := s.db.FinancialTransactions().CountDocuments(ctx, bson.M{
  ```
- **[HIGH] Multi-tenant query without tenantId filter** — `internal/telemetry/service.go:703` `CountDocuments` on `telemetry_events` in `CustomEventSummary`
  - Filter fields: —
  - _empty-filter query on multi-tenant collection `telemetry_events` — full collection scan, risks cross-tenant data leak_
  - Suggestion: Add a `tenantId` filter (or scope the collection accessor to the current tenant) to avoid a full collection scan.
  ```go
  totalCount, err := s.db.TelemetryEvents().CountDocuments(ctx, filter)
  ```
- **[MEDIUM] No covering index** — `internal/telemetry/service.go:320` `CountDocuments` on `users` in `FunnelMetrics`
  - Filter fields: `createdAt``
  - _filter fields ['createdAt'] are not covered by any index on `users` (indexed leading fields: ['displayName', 'email', 'githubId', 'googleId', 'microsoftId'])_
  - Suggestion: Add an index on `createdAt` (or a compound index starting with it) on `users`.
  ```go
  registrations, err := s.db.Users().CountDocuments(ctx, bson.M{
  ```
- **[MEDIUM] No covering index** — `internal/telemetry/service.go:621` `CountDocuments` on `tenants` in `computeKPIs`
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
| `refresh_tokens` | 2 | no | `expiresAt`, `userId` | `expiresAt`, `userId` |
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
6. **Risk.** HIGH for queries on large collections (logs, events, telemetry, audit, deliveries, metrics) without a covering index, and for any query on a spec-required field that is missing the index. MEDIUM for small/static-data collections without coverage and for multi-tenant queries without a tenantId filter.

---
_Generated by `graphify missing-indexes`._