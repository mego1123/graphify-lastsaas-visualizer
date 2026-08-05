# Tenant Isolation Audit

MongoDB query audit for **cross-tenant data leakage** risks. Every query that touches a tenant-scoped collection without a `tenantId` filter is flagged as a violation.

Repo: `/home/z/my-project/repos/lastsaas/backend`

## Summary

| Metric | Value |
|--------|-------|
| Total MongoDB queries | **544** |
| Queries with `tenantId` filter | **77** (14.15%) |
| Queries without `tenantId` filter | **467** |
| Global-collection queries (MEDIUM) | 241 |
| **Total violations** | **226** |
| → CRITICAL (write ops, no tenantId) | **106** |
| → HIGH (read ops, no tenantId) | **120** |
| Violations with safe unique key (likely false positive) | 92 |
| **Real violations needing review** | **134** |

### Risk levels

- **CRITICAL** — write operation (`InsertOne`, `UpdateOne`, `DeleteOne`, `FindOneAndUpdate`, ...) on a tenant-scoped collection without a `tenantId` filter. Can modify or delete data belonging to other tenants.
- **HIGH** — read operation (`Find`, `FindOne`, `Aggregate`, `CountDocuments`) on a tenant-scoped collection without a `tenantId` filter. Can leak data across tenants.
- **MEDIUM** — query on a global collection (`tenants`, `plans`, `system_config`, `system_logs`, `users`) that legitimately doesn't need tenant filtering, or where tenant filtering is applied differently. Not a strict violation but reviewed for appropriate scoping.
- **OK** — query has a `tenantId` filter.

The `safe_key_filter` flag marks violations whose filter contains a globally-unique key (e.g. `_id`, `tokenHash`, `slug`). These are likely false positives because the unique key already constrains the query to a single document — but they are still listed for manual confirmation.

## Top Files by Violations

| File | Violations | Total queries |
|------|------------|---------------|
| `internal/api/handlers/auth.go` | 39 | 94 |
| `internal/telemetry/service.go` | 18 | 30 |
| `internal/api/handlers/branding.go` | 17 | 17 |
| `internal/api/handlers/event_definitions.go` | 16 | 16 |
| `internal/api/handlers/admin.go` | 14 | 70 |
| `cmd/lastsaas/main.go` | 13 | 42 |
| `internal/api/handlers/webhooks.go` | 12 | 12 |
| `internal/api/handlers/bundles.go` | 11 | 11 |
| `cmd/lastsaas/cmd_financial.go` | 6 | 8 |
| `internal/api/handlers/promotions.go` | 6 | 9 |
| `internal/health/query.go` | 6 | 6 |
| `internal/testutil/testutil.go` | 6 | 14 |
| `internal/api/handlers/announcements.go` | 5 | 5 |
| `internal/api/handlers/webhook.go` | 5 | 34 |
| `internal/metrics/metrics.go` | 5 | 7 |
| `cmd/lastsaas/cmd_health.go` | 4 | 4 |
| `internal/api/handlers/apikeys.go` | 4 | 4 |
| `cmd/lastsaas/cmd_users.go` | 3 | 9 |
| `internal/api/handlers/billing.go` | 3 | 19 |
| `internal/api/handlers/config.go` | 3 | 3 |

## Violations by Collection

| Collection | Violations |
|------------|------------|
| `tenant_memberships` | 21 |
| `refresh_tokens` | 19 |
| `credit_bundles` | 16 |
| `telemetry_events` | 15 |
| `config_vars` | 14 |
| `event_definitions` | 14 |
| `webhooks` | 11 |
| `financial_transactions` | 10 |
| `messages` | 10 |
| `branding_assets` | 9 |
| `system_nodes` | 7 |
| `system_metrics` | 7 |
| `api_keys` | 7 |
| `verification_tokens` | 7 |
| `daily_metrics` | 6 |
| `oauth_states` | 6 |
| `custom_pages` | 6 |
| `stripe_mappings` | 6 |
| `<unknown>` | 6 |
| `announcements` | 5 |
| `webhook_deliveries` | 5 |
| `branding_config` | 3 |
| `invitations` | 3 |
| `webhook_events` | 3 |
| `leader_locks` | 3 |
| `revoked_tokens` | 2 |
| `auth_codes` | 2 |
| `impersonation_logs` | 1 |
| `counters` | 1 |
| `usage_events` | 1 |

## CRITICAL Violations — Write Ops without tenantId (45 real)

| Line | Function | Operation | Collection | Filter fields | Risk | Safe key | Filter source | Note |
|------|----------|-----------|------------|---------------|------|----------|---------------|------|
| 314 | `cmdUsersSetActive` | `DeleteMany` | `refresh_tokens` | `userId` | CRITICAL |  | `inline` | DeleteMany on a tenant-scoped collection without tenantId in the filter. CRITICAL: this can modify/delete data belong... |
| 347 | `cmdUsersRevokeSessions` | `DeleteMany` | `refresh_tokens` | `userId` | CRITICAL |  | `inline` | DeleteMany on a tenant-scoped collection without tenantId in the filter. CRITICAL: this can modify/delete data belong... |
| 379 | `cmdSetup` | `InsertOne` | `messages` | `body`, `createdAt`, `isSystem`, `read`, `subject`, `userId` | CRITICAL |  | `struct-var:welcomeMsg:Message` | InsertOne with welcomeMsg (a Message struct); the struct definition does NOT declare a tenantId bson field. CRITICAL:... |
| 460 | `cmdChangePassword` | `DeleteMany` | `refresh_tokens` | `userId` | CRITICAL |  | `inline` | DeleteMany on a tenant-scoped collection without tenantId in the filter. CRITICAL: this can modify/delete data belong... |
| 531 | `cmdSendMessage` | `InsertOne` | `messages` | `body`, `createdAt`, `isSystem`, `read`, `subject`, `userId` | CRITICAL |  | `struct-var:msg:Message` | InsertOne with msg (a Message struct); the struct definition does NOT declare a tenantId bson field. CRITICAL: insert... |
| 1479 | `DeleteUser` | `DeleteMany` | `tenant_memberships` | `userId` | CRITICAL |  | `inline` | DeleteMany on a tenant-scoped collection without tenantId in the filter. CRITICAL: this can modify/delete data belong... |
| 1482 | `DeleteUser` | `DeleteMany` | `refresh_tokens` | `userId` | CRITICAL |  | `inline` | DeleteMany on a tenant-scoped collection without tenantId in the filter. CRITICAL: this can modify/delete data belong... |
| 1485 | `DeleteUser` | `DeleteMany` | `messages` | `userId` | CRITICAL |  | `inline` | DeleteMany on a tenant-scoped collection without tenantId in the filter. CRITICAL: this can modify/delete data belong... |
| 1656 | `ImpersonateUser` | `InsertOne` | `impersonation_logs` | `adminId`, `adminEmail`, `targetId`, `targetEmail`, `ipAddress`, `startedAt`, `expiresAt` | CRITICAL |  | `inline-document` | InsertOne inserts a document with no tenantId field. CRITICAL: the inserted document will be orphaned — readable/modi... |
| 105 | `Create` | `InsertOne` | `announcements` | `body`, `createdAt`, `isPublished`, `publishedAt`, `title`, `updatedAt` | CRITICAL |  | `struct-var:ann:Announcement` | InsertOne with ann (a Announcement struct); the struct definition does NOT declare a tenantId bson field. CRITICAL: i... |
| 696 | `ForgotPassword` | `UpdateMany` | `verification_tokens` | `userId`, `type`, `usedAt` | CRITICAL |  | `inline` | UpdateMany on a tenant-scoped collection without tenantId in the filter. CRITICAL: this can modify/delete data belong... |
| 777 | `ResetPassword` | `UpdateMany` | `refresh_tokens` | `userId`, `isRevoked` | CRITICAL |  | `inline` | UpdateMany on a tenant-scoped collection without tenantId in the filter. CRITICAL: this can modify/delete data belong... |
| 844 | `ChangePassword` | `UpdateMany` | `refresh_tokens` | `userId`, `isRevoked` | CRITICAL |  | `inline` | UpdateMany on a tenant-scoped collection without tenantId in the filter. CRITICAL: this can modify/delete data belong... |
| 1374 | `GoogleOAuth` | `InsertOne` | `oauth_states` | `createdAt`, `expiresAt`, `state` | CRITICAL |  | `struct-var:oauthState:OAuthState` | InsertOne with oauthState (a OAuthState struct); the struct definition does NOT declare a tenantId bson field. CRITIC... |
| 1398 | `GoogleOAuthCallback` | `FindOneAndDelete` | `oauth_states` | `state`, `expiresAt` | CRITICAL |  | `inline` | FindOneAndDelete on a tenant-scoped collection without tenantId in the filter. CRITICAL: this can modify/delete data ... |
| 1507 | `GitHubOAuth` | `InsertOne` | `oauth_states` | `createdAt`, `expiresAt`, `state` | CRITICAL |  | `struct-var:oauthState:OAuthState` | InsertOne with oauthState (a OAuthState struct); the struct definition does NOT declare a tenantId bson field. CRITIC... |
| 1531 | `GitHubOAuthCallback` | `FindOneAndDelete` | `oauth_states` | `state`, `expiresAt` | CRITICAL |  | `inline` | FindOneAndDelete on a tenant-scoped collection without tenantId in the filter. CRITICAL: this can modify/delete data ... |
| 1649 | `MicrosoftOAuth` | `InsertOne` | `oauth_states` | `createdAt`, `expiresAt`, `state` | CRITICAL |  | `struct-var:oauthState:OAuthState` | InsertOne with oauthState (a OAuthState struct); the struct definition does NOT declare a tenantId bson field. CRITIC... |
| 1673 | `MicrosoftOAuthCallback` | `FindOneAndDelete` | `oauth_states` | `state`, `expiresAt` | CRITICAL |  | `inline` | FindOneAndDelete on a tenant-scoped collection without tenantId in the filter. CRITICAL: this can modify/delete data ... |
| 1881 | `RevokeAllSessions` | `UpdateMany` | `refresh_tokens` | `userId`, `isRevoked` | CRITICAL |  | `inline` | UpdateMany on a tenant-scoped collection without tenantId in the filter. CRITICAL: this can modify/delete data belong... |
| 2302 | `DeleteAccount` | `DeleteMany` | `tenant_memberships` | `userId` | CRITICAL |  | `inline` | DeleteMany on a tenant-scoped collection without tenantId in the filter. CRITICAL: this can modify/delete data belong... |
| 2305 | `DeleteAccount` | `DeleteMany` | `refresh_tokens` | `userId` | CRITICAL |  | `inline` | DeleteMany on a tenant-scoped collection without tenantId in the filter. CRITICAL: this can modify/delete data belong... |
| 2308 | `DeleteAccount` | `DeleteMany` | `messages` | `userId` | CRITICAL |  | `inline` | DeleteMany on a tenant-scoped collection without tenantId in the filter. CRITICAL: this can modify/delete data belong... |
| 262 | `UpdateBranding` | `UpdateOne` | `branding_config` | — | CRITICAL |  | `inline` | UpdateOne with an empty filter — affects ALL documents. CRITICAL: cross-tenant data corruption risk. |
| 324 | `UploadAsset` | `UpdateOne` | `branding_assets` | `key` | CRITICAL |  | `inline` | UpdateOne on a tenant-scoped collection without tenantId in the filter. CRITICAL: this can modify/delete data belongi... |
| 348 | `DeleteAsset` | `DeleteOne` | `branding_assets` | `key` | CRITICAL |  | `inline` | DeleteOne on a tenant-scoped collection without tenantId in the filter. CRITICAL: this can modify/delete data belongi... |
| 460 | `UploadMedia` | `InsertOne` | `branding_assets` | `contentType`, `createdAt`, `data`, `filename`, `key`, `size` | CRITICAL |  | `struct-var:asset:BrandingAsset` | InsertOne with asset (a BrandingAsset struct); the struct definition does NOT declare a tenantId bson field. CRITICAL... |
| 487 | `DeleteMedia` | `DeleteOne` | `branding_assets` | `key` | CRITICAL |  | `inline` | DeleteOne on a tenant-scoped collection without tenantId in the filter. CRITICAL: this can modify/delete data belongi... |
| 543 | `CreatePage` | `InsertOne` | `custom_pages` | — | CRITICAL |  | `struct:unknown` | InsertOne with an unrecognised struct value; could not statically verify tenantId presence. Manual review required. |
| 302 | `DeleteEventDefinition` | `UpdateMany` | `event_definitions` | `parentId` | CRITICAL |  | `inline` | UpdateMany on a tenant-scoped collection without tenantId in the filter. CRITICAL: this can modify/delete data belong... |
| 368 | `UpdatePlan` | `DeleteMany` | `stripe_mappings` | `entityType` | CRITICAL |  | `inline` | DeleteMany on a tenant-scoped collection without tenantId in the filter. CRITICAL: this can modify/delete data belong... |
| 519 | `handleInvoicePaymentFailed` | `InsertOne` | `messages` | `body`, `createdAt`, `isSystem`, `read`, `subject`, `userId` | CRITICAL |  | `struct:Message` | InsertOne with a Message struct value; tenantId presence inferred from the struct definition — verify the value is ac... |
| 384 | `Seed` | `InsertOne` | `config_vars` | — | CRITICAL |  | `struct:unknown` | InsertOne with an unrecognised struct value; could not statically verify tenantId presence. Manual review required. |
| 300 | `collectAndStore` | `InsertOne` | `system_metrics` | `cpu`, `disk`, `goRuntime`, `http`, `integrations`, `memory`, `mongo`, `network`, `nodeId`, `timestamp` | CRITICAL |  | `struct-var:metric:SystemMetric` | InsertOne with metric (a SystemMetric struct); the struct definition does NOT declare a tenantId bson field. CRITICAL... |
| 28 | `ListNodes` | `UpdateMany` | `system_nodes` | `lastSeen` | CRITICAL |  | `inline` | UpdateMany on a tenant-scoped collection without tenantId in the filter. CRITICAL: this can modify/delete data belong... |
| 280 | `collectDaily` | `UpdateOne` | `daily_metrics` | `date` | CRITICAL |  | `inline` | UpdateOne on a tenant-scoped collection without tenantId in the filter. CRITICAL: this can modify/delete data belongi... |
| 143 | `GetOrCreatePrice` | `InsertOne` | `stripe_mappings` | `createdAt`, `entityId`, `entityType`, `stripePriceId`, `stripeProductId` | CRITICAL |  | `struct:StripeMapping` | InsertOne with a StripeMapping struct value; tenantId presence inferred from the struct definition — verify the value... |
| 82 | `flushLoop` | `InsertMany` | `telemetry_events` | — | CRITICAL |  | `inline-document-slice` | InsertMany inserts a document with no tenantId field. CRITICAL: the inserted document will be orphaned — readable/mod... |
| 188 | `TrackBatch` | `InsertMany` | `telemetry_events` | — | CRITICAL |  | `inline-document-slice` | InsertMany inserts a document with no tenantId field. CRITICAL: the inserted document will be orphaned — readable/mod... |
| 98 | `MustConnectTestDB` | `DeleteMany` | `<unknown>` | — | CRITICAL |  | `inline` | DeleteMany with an empty filter — affects ALL documents. CRITICAL: cross-tenant data corruption risk. |
| 144 | `ConnectTestDB` | `DeleteMany` | `<unknown>` | — | CRITICAL |  | `inline` | DeleteMany with an empty filter — affects ALL documents. CRITICAL: cross-tenant data corruption risk. |
| 227 | `CleanupCollections` | `DeleteMany` | `<unknown>` | — | CRITICAL |  | `inline` | DeleteMany with an empty filter — affects ALL documents. CRITICAL: cross-tenant data corruption risk. |
| 91 | `sendUpgradeMessage` | `InsertOne` | `messages` | `body`, `createdAt`, `isSystem`, `read`, `subject`, `userId` | CRITICAL |  | `struct-var:msg:Message` | InsertOne with msg (a Message struct); the struct definition does NOT declare a tenantId bson field. CRITICAL: insert... |
| 287 | `deliverWithRetry` | `InsertOne` | `webhook_deliveries` | `createdAt`, `durationMs`, `eventType`, `maxRetries`, `payload`, `responseBody`, `responseCode`, `retryCount`, `success`, `webhookId` | CRITICAL |  | `struct-var:delivery:WebhookDelivery` | InsertOne with delivery (a WebhookDelivery struct); the struct definition does NOT declare a tenantId bson field. CRI... |
| 421 | `DeliverTest` | `InsertOne` | `webhook_deliveries` | `createdAt`, `durationMs`, `eventType`, `maxRetries`, `payload`, `responseBody`, `responseCode`, `retryCount`, `success`, `webhookId` | CRITICAL |  | `struct-var:delivery:WebhookDelivery` | InsertOne with delivery (a WebhookDelivery struct); the struct definition does NOT declare a tenantId bson field. CRI... |

## HIGH Violations — Read Ops without tenantId (89 real)

| Line | Function | Operation | Collection | Filter fields | Risk | Safe key | Filter source | Note |
|------|----------|-----------|------------|---------------|------|----------|---------------|------|
| 115 | `cmdDoctor` | `CountDocuments` | `system_nodes` | `lastSeen` | HIGH |  | `inline` | Read operation on a tenant-scoped collection without tenantId in the filter. HIGH: cross-tenant data leakage risk. |
| 58 | `cmdFinancialSummary` | `Aggregate` | `financial_transactions` | `type` | HIGH |  | `variable-pipeline:revPipeline` | Read operation on a tenant-scoped collection without tenantId in the filter. HIGH: cross-tenant data leakage risk. |
| 84 | `cmdFinancialSummary` | `Aggregate` | `financial_transactions` | `type` | HIGH |  | `variable-pipeline:refundPipeline` | Read operation on a tenant-scoped collection without tenantId in the filter. HIGH: cross-tenant data leakage risk. |
| 111 | `cmdFinancialSummary` | `Aggregate` | `financial_transactions` | — | HIGH |  | `variable-pipeline:typePipeline` | Read operation with an empty filter — returns ALL documents. HIGH: cross-tenant data leakage risk. |
| 138 | `cmdFinancialSummary` | `FindOne` | `daily_metrics` | — | HIGH |  | `inline` | Read operation with an empty filter — returns ALL documents. HIGH: cross-tenant data leakage risk. |
| 147 | `cmdFinancialSummary` | `Aggregate` | `financial_transactions` | `type` | HIGH |  | `variable-pipeline:rev30Pipeline` | Read operation on a tenant-scoped collection without tenantId in the filter. HIGH: cross-tenant data leakage risk. |
| 350 | `cmdFinancialMetrics` | `Find` | `daily_metrics` | — | HIGH |  | `inline` | Read operation with an empty filter — returns ALL documents. HIGH: cross-tenant data leakage risk. |
| 51 | `cmdHealth` | `Find` | `system_nodes` | — | HIGH |  | `inline` | Read operation with an empty filter — returns ALL documents. HIGH: cross-tenant data leakage risk. |
| 77 | `cmdHealth` | `FindOne` | `system_metrics` | — | HIGH |  | `inline` | Read operation with an empty filter — returns ALL documents. HIGH: cross-tenant data leakage risk. |
| 100 | `cmdHealth` | `Find` | `system_nodes` | — | HIGH |  | `inline` | Read operation with an empty filter — returns ALL documents. HIGH: cross-tenant data leakage risk. |
| 124 | `cmdHealth` | `FindOne` | `system_metrics` | — | HIGH |  | `inline` | Read operation with an empty filter — returns ALL documents. HIGH: cross-tenant data leakage risk. |
| 71 | `cmdStats` | `FindOne` | `daily_metrics` | — | HIGH |  | `inline` | Read operation with an empty filter — returns ALL documents. HIGH: cross-tenant data leakage risk. |
| 79 | `cmdStats` | `Aggregate` | `financial_transactions` | `type` | HIGH |  | `variable-pipeline:revPipeline` | Read operation on a tenant-scoped collection without tenantId in the filter. HIGH: cross-tenant data leakage risk. |
| 365 | `lookupUserWithMemberships` | `Find` | `tenant_memberships` | `userId` | HIGH |  | `inline` | Read operation on a tenant-scoped collection without tenantId in the filter. HIGH: cross-tenant data leakage risk. |
| 587 | `cmdConfigList` | `Find` | `config_vars` | — | HIGH |  | `inline` | Read operation with an empty filter — returns ALL documents. HIGH: cross-tenant data leakage risk. |
| 801 | `main` | `FindOne` | `branding_config` | — | HIGH |  | `inline` | Read operation with an empty filter — returns ALL documents. HIGH: cross-tenant data leakage risk. |
| 51 | `isRootTenantOwner` | `CountDocuments` | `tenant_memberships` | `userId`, `role` | HIGH |  | `inline` | Read operation on a tenant-scoped collection without tenantId in the filter. HIGH: cross-tenant data leakage risk. |
| 64 | `isRootTenantOwner` | `FindOne` | `tenant_memberships` | `userId`, `role` | HIGH |  | `inline` | Read operation on a tenant-scoped collection without tenantId in the filter. HIGH: cross-tenant data leakage risk. |
| 616 | `ListUsers` | `Aggregate` | `tenant_memberships` | `userId` | HIGH |  | `variable-pipeline:pipeline` | Read operation on a tenant-scoped collection without tenantId in the filter. HIGH: cross-tenant data leakage risk. |
| 702 | `ExportUsersCSV` | `Aggregate` | `tenant_memberships` | `userId` | HIGH |  | `variable-pipeline:pipeline` | Read operation on a tenant-scoped collection without tenantId in the filter. HIGH: cross-tenant data leakage risk. |
| 948 | `GetUser` | `Find` | `tenant_memberships` | `userId` | HIGH |  | `inline` | Read operation on a tenant-scoped collection without tenantId in the filter. HIGH: cross-tenant data leakage risk. |
| 1243 | `PreflightDeleteUser` | `Find` | `tenant_memberships` | `userId`, `role` | HIGH |  | `inline` | Read operation on a tenant-scoped collection without tenantId in the filter. HIGH: cross-tenant data leakage risk. |
| 1378 | `DeleteUser` | `Find` | `tenant_memberships` | `userId` | HIGH |  | `inline` | Read operation on a tenant-scoped collection without tenantId in the filter. HIGH: cross-tenant data leakage risk. |
| 1667 | `ImpersonateUser` | `Find` | `tenant_memberships` | `userId` | HIGH |  | `inline` | Read operation on a tenant-scoped collection without tenantId in the filter. HIGH: cross-tenant data leakage risk. |
| 33 | `ListPublic` | `Find` | `announcements` | `isPublished` | HIGH |  | `inline` | Read operation on a tenant-scoped collection without tenantId in the filter. HIGH: cross-tenant data leakage risk. |
| 54 | `ListAll` | `Find` | `announcements` | — | HIGH |  | `inline` | Read operation with an empty filter — returns ALL documents. HIGH: cross-tenant data leakage risk. |
| 45 | `ListAPIKeys` | `Find` | `api_keys` | `isActive` | HIGH |  | `inline` | Read operation on a tenant-scoped collection without tenantId in the filter. HIGH: cross-tenant data leakage risk. |
| 60 | `ListAPIKeys` | `CountDocuments` | `api_keys` | `isActive` | HIGH |  | `inline` | Read operation on a tenant-scoped collection without tenantId in the filter. HIGH: cross-tenant data leakage risk. |
| 1790 | `ListSessions` | `Find` | `refresh_tokens` | `userId`, `isRevoked`, `expiresAt` | HIGH |  | `inline` | Read operation on a tenant-scoped collection without tenantId in the filter. HIGH: cross-tenant data leakage risk. |
| 2048 | `getUserMemberships` | `Find` | `tenant_memberships` | `userId` | HIGH |  | `inline` | Read operation on a tenant-scoped collection without tenantId in the filter. HIGH: cross-tenant data leakage risk. |
| 2166 | `storeRefreshToken` | `CountDocuments` | `refresh_tokens` | `userId`, `isRevoked`, `expiresAt` | HIGH |  | `inline` | Read operation on a tenant-scoped collection without tenantId in the filter. HIGH: cross-tenant data leakage risk. |
| 2174 | `storeRefreshToken` | `Find` | `refresh_tokens` | `userId`, `isRevoked`, `expiresAt` | HIGH |  | `inline` | Read operation on a tenant-scoped collection without tenantId in the filter. HIGH: cross-tenant data leakage risk. |
| 2241 | `DeleteAccount` | `Find` | `tenant_memberships` | `userId` | HIGH |  | `inline` | Read operation on a tenant-scoped collection without tenantId in the filter. HIGH: cross-tenant data leakage risk. |
| 2341 | `ExportData` | `Find` | `tenant_memberships` | `userId` | HIGH |  | `inline` | Read operation on a tenant-scoped collection without tenantId in the filter. HIGH: cross-tenant data leakage risk. |
| 2363 | `ExportData` | `Find` | `messages` | `userId` | HIGH |  | `inline` | Read operation on a tenant-scoped collection without tenantId in the filter. HIGH: cross-tenant data leakage risk. |
| 801 | `AdminGetMetrics` | `Find` | `daily_metrics` | `date` | HIGH |  | `variable:filter` | Read operation on a tenant-scoped collection without tenantId in the filter. HIGH: cross-tenant data leakage risk. |
| 893 | `computeLiveRevenue` | `Aggregate` | `financial_transactions` | `createdAt` | HIGH |  | `variable-pipeline:pipeline` | Read operation on a tenant-scoped collection without tenantId in the filter. HIGH: cross-tenant data leakage risk. |
| 45 | `GetBranding` | `FindOne` | `branding_config` | — | HIGH |  | `inline` | Read operation with an empty filter — returns ALL documents. HIGH: cross-tenant data leakage risk. |
| 60 | `GetBranding` | `FindOne` | `branding_assets` | `key` | HIGH |  | `inline` | Read operation on a tenant-scoped collection without tenantId in the filter. HIGH: cross-tenant data leakage risk. |
| 64 | `GetBranding` | `FindOne` | `branding_assets` | `key` | HIGH |  | `inline` | Read operation on a tenant-scoped collection without tenantId in the filter. HIGH: cross-tenant data leakage risk. |
| 119 | `ServeAsset` | `FindOne` | `branding_assets` | `key` | HIGH |  | `inline` | Read operation on a tenant-scoped collection without tenantId in the filter. HIGH: cross-tenant data leakage risk. |
| 141 | `ServeMedia` | `FindOne` | `branding_assets` | `key` | HIGH |  | `inline` | Read operation on a tenant-scoped collection without tenantId in the filter. HIGH: cross-tenant data leakage risk. |
| 182 | `ListPublicPages` | `Find` | `custom_pages` | `isPublished` | HIGH |  | `inline` | Read operation on a tenant-scoped collection without tenantId in the filter. HIGH: cross-tenant data leakage risk. |
| 368 | `ListMedia` | `Find` | `branding_assets` | `key` | HIGH |  | `variable:filter` | Read operation on a tenant-scoped collection without tenantId in the filter. HIGH: cross-tenant data leakage risk. |
| 505 | `AdminListPages` | `Find` | `custom_pages` | — | HIGH |  | `inline` | Read operation with an empty filter — returns ALL documents. HIGH: cross-tenant data leakage risk. |
| 60 | `ListBundles` | `Find` | `credit_bundles` | — | HIGH |  | `inline` | Read operation with an empty filter — returns ALL documents. HIGH: cross-tenant data leakage risk. |
| 75 | `ListBundles` | `CountDocuments` | `credit_bundles` | — | HIGH |  | `inline` | Read operation with an empty filter — returns ALL documents. HIGH: cross-tenant data leakage risk. |
| 236 | `ListBundlesPublic` | `Find` | `credit_bundles` | `isActive` | HIGH |  | `inline` | Read operation on a tenant-scoped collection without tenantId in the filter. HIGH: cross-tenant data leakage risk. |
| 50 | `ListEventDefinitions` | `Find` | `event_definitions` | — | HIGH |  | `inline` | Read operation with an empty filter — returns ALL documents. HIGH: cross-tenant data leakage risk. |
| 85 | `ListEventDefinitions` | `Aggregate` | `telemetry_events` | — | HIGH |  | `variable-pipeline:pipeline` | Read operation with an empty filter — returns ALL documents. HIGH: cross-tenant data leakage risk. |
| 321 | `GetSankeyData` | `Find` | `event_definitions` | — | HIGH |  | `inline` | Read operation with an empty filter — returns ALL documents. HIGH: cross-tenant data leakage risk. |
| 399 | `GetSankeyData` | `Aggregate` | `telemetry_events` | — | HIGH |  | `variable-pipeline:pipeline` | Read operation with an empty filter — returns ALL documents. HIGH: cross-tenant data leakage risk. |
| 36 | `ListMessages` | `Find` | `messages` | `userId` | HIGH |  | `inline` | Read operation on a tenant-scoped collection without tenantId in the filter. HIGH: cross-tenant data leakage risk. |
| 64 | `UnreadCount` | `CountDocuments` | `messages` | `userId`, `read` | HIGH |  | `inline` | Read operation on a tenant-scoped collection without tenantId in the filter. HIGH: cross-tenant data leakage risk. |
| 115 | `buildProductNameMap` | `Find` | `stripe_mappings` | — | HIGH |  | `inline` | Read operation with an empty filter — returns ALL documents. HIGH: cross-tenant data leakage risk. |
| 226 | `ListEligibleProducts` | `Find` | `credit_bundles` | `isActive` | HIGH |  | `inline` | Read operation on a tenant-scoped collection without tenantId in the filter. HIGH: cross-tenant data leakage risk. |
| 418 | `resolveStripeProducts` | `FindOne` | `stripe_mappings` | `entityType`, `entityId` | HIGH |  | `inline` | Read operation on a tenant-scoped collection without tenantId in the filter. HIGH: cross-tenant data leakage risk. |
| 438 | `resolveStripeProducts` | `FindOne` | `stripe_mappings` | `entityType`, `entityId` | HIGH |  | `inline` | Read operation on a tenant-scoped collection without tenantId in the filter. HIGH: cross-tenant data leakage risk. |
| 45 | `ListWebhooks` | `Find` | `webhooks` | `isActive` | HIGH |  | `inline` | Read operation on a tenant-scoped collection without tenantId in the filter. HIGH: cross-tenant data leakage risk. |
| 71 | `ListWebhooks` | `CountDocuments` | `webhook_deliveries` | `webhookId`, `createdAt` | HIGH |  | `inline` | Read operation on a tenant-scoped collection without tenantId in the filter. HIGH: cross-tenant data leakage risk. |
| 83 | `ListWebhooks` | `FindOne` | `webhook_deliveries` | `webhookId` | HIGH |  | `inline` | Read operation on a tenant-scoped collection without tenantId in the filter. HIGH: cross-tenant data leakage risk. |
| 88 | `ListWebhooks` | `CountDocuments` | `webhooks` | `isActive` | HIGH |  | `inline` | Read operation on a tenant-scoped collection without tenantId in the filter. HIGH: cross-tenant data leakage risk. |
| 111 | `GetWebhook` | `Find` | `webhook_deliveries` | `webhookId` | HIGH |  | `inline` | Read operation on a tenant-scoped collection without tenantId in the filter. HIGH: cross-tenant data leakage risk. |
| 34 | `Load` | `Find` | `config_vars` | — | HIGH |  | `inline` | Read operation with an empty filter — returns ALL documents. HIGH: cross-tenant data leakage risk. |
| 35 | `ListNodes` | `Find` | `system_nodes` | — | HIGH |  | `inline` | Read operation with an empty filter — returns ALL documents. HIGH: cross-tenant data leakage risk. |
| 55 | `GetMetrics` | `Find` | `system_metrics` | `nodeId`, `timestamp` | HIGH |  | `variable:filter` | Read operation on a tenant-scoped collection without tenantId in the filter. HIGH: cross-tenant data leakage risk. |
| 74 | `GetAggregateMetrics` | `Find` | `system_metrics` | `timestamp` | HIGH |  | `variable:filter` | Read operation on a tenant-scoped collection without tenantId in the filter. HIGH: cross-tenant data leakage risk. |
| 98 | `GetCurrentMetrics` | `FindOne` | `system_metrics` | `nodeId` | HIGH |  | `inline` | Read operation on a tenant-scoped collection without tenantId in the filter. HIGH: cross-tenant data leakage risk. |
| 120 | `GetIntegrationCounts24h` | `Aggregate` | `system_metrics` | — | HIGH |  | `variable-pipeline:pipeline` | Read operation with an empty filter — returns ALL documents. HIGH: cross-tenant data leakage risk. |
| 227 | `collectDaily` | `Aggregate` | `financial_transactions` | `createdAt` | HIGH |  | `variable-pipeline:revPipeline` | Read operation on a tenant-scoped collection without tenantId in the filter. HIGH: cross-tenant data leakage risk. |
| 100 | `GetOrCreatePrice` | `FindOne` | `stripe_mappings` | `entityType`, `entityId` | HIGH |  | `inline` | Read operation on a tenant-scoped collection without tenantId in the filter. HIGH: cross-tenant data leakage risk. |
| 338 | `FunnelMetrics` | `CountDocuments` | `telemetry_events` | `eventName`, `createdAt` | HIGH |  | `inline` | Read operation on a tenant-scoped collection without tenantId in the filter. HIGH: cross-tenant data leakage risk. |
| 347 | `FunnelMetrics` | `CountDocuments` | `financial_transactions` | `type`, `createdAt` | HIGH |  | `inline` | Read operation on a tenant-scoped collection without tenantId in the filter. HIGH: cross-tenant data leakage risk. |
| 356 | `FunnelMetrics` | `CountDocuments` | `telemetry_events` | — | HIGH |  | `variable:unknown:mergeBson(dateFilter, bson.M{
          ` | Read operation with an empty filter — returns ALL documents. HIGH: cross-tenant data leakage risk. |
| 531 | `EngagementMetrics` | `CountDocuments` | `telemetry_events` | `eventName`, `userId` | HIGH |  | `inline` | Read operation on a tenant-scoped collection without tenantId in the filter. HIGH: cross-tenant data leakage risk. |
| 703 | `CustomEventSummary` | `CountDocuments` | `telemetry_events` | `createdAt`, `eventName` | HIGH |  | `variable:filter` | Read operation on a tenant-scoped collection without tenantId in the filter. HIGH: cross-tenant data leakage risk. |
| 719 | `CustomEventSummary` | `Aggregate` | `telemetry_events` | — | HIGH |  | `variable-pipeline:pipeline` | Read operation with an empty filter — returns ALL documents. HIGH: cross-tenant data leakage risk. |
| 756 | `ListEventTypes` | `Aggregate` | `telemetry_events` | — | HIGH |  | `variable-pipeline:pipeline` | Read operation with an empty filter — returns ALL documents. HIGH: cross-tenant data leakage risk. |
| 795 | `countDistinct` | `Aggregate` | `telemetry_events` | — | HIGH |  | `variable-pipeline:pipeline` | Read operation with an empty filter — returns ALL documents. HIGH: cross-tenant data leakage risk. |
| 905 | `weeklyActiveUsers` | `Aggregate` | `telemetry_events` | — | HIGH |  | `variable-pipeline:pipeline` | Read operation with an empty filter — returns ALL documents. HIGH: cross-tenant data leakage risk. |
| 953 | `monthlyActiveUsers` | `Aggregate` | `telemetry_events` | — | HIGH |  | `variable-pipeline:pipeline` | Read operation with an empty filter — returns ALL documents. HIGH: cross-tenant data leakage risk. |
| 991 | `topCustomEvents` | `Aggregate` | `telemetry_events` | — | HIGH |  | `variable-pipeline:pipeline` | Read operation with an empty filter — returns ALL documents. HIGH: cross-tenant data leakage risk. |
| 1022 | `creditConsumptionTrend` | `Aggregate` | `usage_events` | — | HIGH |  | `variable-pipeline:pipeline` | Read operation with an empty filter — returns ALL documents. HIGH: cross-tenant data leakage risk. |
| 1142 | `medianTimeToFirstPurchase` | `Aggregate` | `financial_transactions` | — | HIGH |  | `variable-pipeline:pipeline` | Read operation with an empty filter — returns ALL documents. HIGH: cross-tenant data leakage risk. |
| 1228 | `mrrTrend` | `Find` | `daily_metrics` | `date` | HIGH |  | `inline` | Read operation on a tenant-scoped collection without tenantId in the filter. HIGH: cross-tenant data leakage risk. |
| 1264 | `subscriberTrend` | `Aggregate` | `financial_transactions` | — | HIGH |  | `variable-pipeline:pipeline` | Read operation with an empty filter — returns ALL documents. HIGH: cross-tenant data leakage risk. |
| 1285 | `aggregateDailyPoints` | `Aggregate` | `telemetry_events` | — | HIGH |  | `variable-pipeline:unknown` | Read operation with an empty filter — returns ALL documents. HIGH: cross-tenant data leakage risk. |
| 352 | `CountDocuments` | `CountDocuments` | `<unknown>` | — | HIGH |  | `variable:unknown:filter` | Read operation with an empty filter — returns ALL documents. HIGH: cross-tenant data leakage risk. |
| 194 | `dispatch` | `Find` | `webhooks` | `events`, `isActive` | HIGH |  | `inline` | Read operation on a tenant-scoped collection without tenantId in the filter. HIGH: cross-tenant data leakage risk. |

## Safe-Key Violations — Likely False Positives (92)

These queries lack a `tenantId` filter but constrain on a globally-unique key. Listed for completeness — manual confirmation recommended.

| Line | Function | Operation | Collection | Filter fields | Risk | Safe key | Filter source | Note |
|------|----------|-----------|------------|---------------|------|----------|---------------|------|
| 362 | `cmdSetup` | `DeleteOne` | `tenant_memberships` | `_id` | CRITICAL | ✓ | `inline` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 635 | `cmdConfigGet` | `FindOne` | `config_vars` | `name` | HIGH | ✓ | `inline` | Read operation without tenantId, but the filter contains a globally-unique key — likely safe, manual review recommended. |
| 665 | `cmdConfigSet` | `FindOne` | `config_vars` | `name` | HIGH | ✓ | `inline` | Read operation without tenantId, but the filter contains a globally-unique key — likely safe, manual review recommended. |
| 676 | `cmdConfigSet` | `UpdateOne` | `config_vars` | `name` | CRITICAL | ✓ | `inline` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 713 | `cmdConfigReset` | `FindOne` | `config_vars` | `name` | HIGH | ✓ | `inline` | Read operation without tenantId, but the filter contains a globally-unique key — likely safe, manual review recommended. |
| 724 | `cmdConfigReset` | `UpdateOne` | `config_vars` | `name` | CRITICAL | ✓ | `inline` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 831 | `cmdTransferRootOwner` | `UpdateOne` | `tenant_memberships` | `_id` | CRITICAL | ✓ | `inline` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 841 | `cmdTransferRootOwner` | `UpdateOne` | `tenant_memberships` | `_id` | CRITICAL | ✓ | `inline` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 847 | `cmdTransferRootOwner` | `UpdateOne` | `tenant_memberships` | `_id` | CRITICAL | ✓ | `inline` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 1186 | `UpdateUserRole` | `UpdateOne` | `tenant_memberships` | `_id` | CRITICAL | ✓ | `inline` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 1964 | `RemoveRootMember` | `DeleteOne` | `tenant_memberships` | `_id` | CRITICAL | ✓ | `inline` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 152 | `Update` | `UpdateOne` | `announcements` | `_id` | CRITICAL | ✓ | `inline` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 168 | `Delete` | `DeleteOne` | `announcements` | `_id` | CRITICAL | ✓ | `inline` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 127 | `CreateAPIKey` | `InsertOne` | `api_keys` | `authority`, `createdAt`, `createdBy`, `isActive`, `keyHash`, `keyPreview`, `lastUsedAt`, `name` | CRITICAL | ✓ | `struct-var:apiKey:APIKey` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 166 | `DeleteAPIKey` | `UpdateByID` | `api_keys` | `_id` | CRITICAL | ✓ | `by-id` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 453 | `Logout` | `InsertOne` | `revoked_tokens` | `createdAt`, `expiresAt`, `tokenHash` | CRITICAL | ✓ | `struct:RevokedToken` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 470 | `Logout` | `UpdateMany` | `refresh_tokens` | `tokenHash`, `userId` | CRITICAL | ✓ | `inline` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 503 | `Refresh` | `FindOne` | `refresh_tokens` | `tokenHash` | HIGH | ✓ | `inline` | Read operation without tenantId, but the filter contains a globally-unique key — likely safe, manual review recommended. |
| 514 | `Refresh` | `UpdateMany` | `refresh_tokens` | `familyId` | CRITICAL | ✓ | `inline` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 525 | `Refresh` | `UpdateOne` | `refresh_tokens` | `_id` | CRITICAL | ✓ | `inline` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 555 | `Refresh` | `UpdateOne` | `refresh_tokens` | `tokenHash` | CRITICAL | ✓ | `inline` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 601 | `VerifyEmail` | `FindOneAndUpdate` | `verification_tokens` | `token`, `type`, `usedAt`, `expiresAt` | CRITICAL | ✓ | `inline` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 711 | `ForgotPassword` | `InsertOne` | `verification_tokens` | `createdAt`, `expiresAt`, `token`, `type`, `usedAt`, `userId` | CRITICAL | ✓ | `struct-var:verification:VerificationToken` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 746 | `ResetPassword` | `FindOneAndUpdate` | `verification_tokens` | `token`, `type`, `usedAt`, `expiresAt` | CRITICAL | ✓ | `inline` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 1204 | `MagicLinkRequest` | `InsertOne` | `verification_tokens` | `createdAt`, `expiresAt`, `token`, `type`, `usedAt`, `userId` | CRITICAL | ✓ | `struct-var:verification:VerificationToken` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 1236 | `MagicLinkVerify` | `FindOneAndUpdate` | `verification_tokens` | `token`, `type`, `usedAt`, `expiresAt` | CRITICAL | ✓ | `inline` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 1315 | `createAuthCodeRedirect` | `InsertOne` | `auth_codes` | `code`, `createdAt`, `expiresAt`, `tokenData`, `usedAt`, `userId` | CRITICAL | ✓ | `struct-var:authCode:AuthCode` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 1336 | `ExchangeCode` | `FindOneAndUpdate` | `auth_codes` | `code`, `usedAt`, `expiresAt` | CRITICAL | ✓ | `inline` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 1861 | `RevokeSession` | `UpdateOne` | `refresh_tokens` | `_id`, `userId` | CRITICAL | ✓ | `inline` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 2026 | `sendVerificationEmail` | `InsertOne` | `verification_tokens` | `createdAt`, `expiresAt`, `token`, `type`, `usedAt`, `userId` | CRITICAL | ✓ | `struct-var:verification:VerificationToken` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 2082 | `acceptInvitationForUser` | `FindOne` | `invitations` | `token`, `status`, `expiresAt` | HIGH | ✓ | `inline` | Read operation without tenantId, but the filter contains a globally-unique key — likely safe, manual review recommended. |
| 2101 | `acceptInvitationForUser` | `FindOneAndUpdate` | `invitations` | `_id`, `status` | CRITICAL | ✓ | `inline` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 2183 | `storeRefreshToken` | `UpdateByID` | `refresh_tokens` | `_id` | CRITICAL | ✓ | `by-id` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 2204 | `storeRefreshToken` | `InsertOne` | `refresh_tokens` | `createdAt`, `deviceInfo`, `expiresAt`, `familyId`, `ipAddress`, `isRevoked`, `lastActiveAt`, `tokenHash`, `userAgent`, `userId` | CRITICAL | ✓ | `struct-var:rt:RefreshToken` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 313 | `Checkout` | `FindOne` | `credit_bundles` | `_id`, `isActive` | HIGH | ✓ | `inline` | Read operation without tenantId, but the filter contains a globally-unique key — likely safe, manual review recommended. |
| 163 | `GetPublicPage` | `FindOne` | `custom_pages` | `slug`, `isPublished` | HIGH | ✓ | `inline` | Read operation without tenantId, but the filter contains a globally-unique key — likely safe, manual review recommended. |
| 590 | `UpdatePage` | `UpdateByID` | `custom_pages` | `_id` | CRITICAL | ✓ | `by-id` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 616 | `DeletePage` | `DeleteOne` | `custom_pages` | `_id` | CRITICAL | ✓ | `inline` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 96 | `CreateBundle` | `CountDocuments` | `credit_bundles` | `name` | HIGH | ✓ | `inline` | Read operation without tenantId, but the filter contains a globally-unique key — likely safe, manual review recommended. |
| 117 | `CreateBundle` | `InsertOne` | `credit_bundles` | `createdAt`, `credits`, `isActive`, `name`, `priceCents`, `sortOrder`, `updatedAt` | CRITICAL | ✓ | `struct-var:bundle:CreditBundle` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 145 | `UpdateBundle` | `FindOne` | `credit_bundles` | `_id` | HIGH | ✓ | `inline` | Read operation without tenantId, but the filter contains a globally-unique key — likely safe, manual review recommended. |
| 166 | `UpdateBundle` | `CountDocuments` | `credit_bundles` | `name`, `_id` | HIGH | ✓ | `inline` | Read operation without tenantId, but the filter contains a globally-unique key — likely safe, manual review recommended. |
| 186 | `UpdateBundle` | `UpdateByID` | `credit_bundles` | `_id` | CRITICAL | ✓ | `by-id` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 196 | `UpdateBundle` | `FindOne` | `credit_bundles` | `_id` | HIGH | ✓ | `inline` | Read operation without tenantId, but the filter contains a globally-unique key — likely safe, manual review recommended. |
| 212 | `DeleteBundle` | `FindOne` | `credit_bundles` | `_id` | HIGH | ✓ | `inline` | Read operation without tenantId, but the filter contains a globally-unique key — likely safe, manual review recommended. |
| 221 | `DeleteBundle` | `DeleteOne` | `credit_bundles` | `_id` | CRITICAL | ✓ | `inline` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 94 | `UpdateConfig` | `UpdateOne` | `config_vars` | `name` | CRITICAL | ✓ | `inline` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 162 | `CreateConfig` | `InsertOne` | `config_vars` | `createdAt`, `description`, `isSystem`, `name`, `options`, `type`, `updatedAt`, `value` | CRITICAL | ✓ | `struct-var:v:ConfigVar` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 192 | `DeleteConfig` | `DeleteOne` | `config_vars` | `name` | CRITICAL | ✓ | `inline` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 135 | `CreateEventDefinition` | `CountDocuments` | `event_definitions` | `name` | HIGH | ✓ | `inline` | Read operation without tenantId, but the filter contains a globally-unique key — likely safe, manual review recommended. |
| 161 | `CreateEventDefinition` | `CountDocuments` | `event_definitions` | `_id` | HIGH | ✓ | `inline` | Read operation without tenantId, but the filter contains a globally-unique key — likely safe, manual review recommended. |
| 173 | `CreateEventDefinition` | `InsertOne` | `event_definitions` | `createdAt`, `description`, `name`, `parentId`, `updatedAt` | CRITICAL | ✓ | `struct-var:def:EventDefinition` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 212 | `UpdateEventDefinition` | `FindOne` | `event_definitions` | `_id` | HIGH | ✓ | `inline` | Read operation without tenantId, but the filter contains a globally-unique key — likely safe, manual review recommended. |
| 219 | `UpdateEventDefinition` | `CountDocuments` | `event_definitions` | `name`, `_id` | HIGH | ✓ | `inline` | Read operation without tenantId, but the filter contains a globally-unique key — likely safe, manual review recommended. |
| 249 | `UpdateEventDefinition` | `CountDocuments` | `event_definitions` | `_id` | HIGH | ✓ | `inline` | Read operation without tenantId, but the filter contains a globally-unique key — likely safe, manual review recommended. |
| 269 | `UpdateEventDefinition` | `UpdateOne` | `event_definitions` | `_id` | CRITICAL | ✓ | `inline` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 278 | `UpdateEventDefinition` | `FindOne` | `event_definitions` | `_id` | HIGH | ✓ | `inline` | Read operation without tenantId, but the filter contains a globally-unique key — likely safe, manual review recommended. |
| 296 | `DeleteEventDefinition` | `FindOne` | `event_definitions` | `_id` | HIGH | ✓ | `inline` | Read operation without tenantId, but the filter contains a globally-unique key — likely safe, manual review recommended. |
| 307 | `DeleteEventDefinition` | `DeleteOne` | `event_definitions` | `_id` | CRITICAL | ✓ | `inline` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 463 | `wouldCreateCycle` | `FindOne` | `event_definitions` | `_id` | HIGH | ✓ | `inline` | Read operation without tenantId, but the filter contains a globally-unique key — likely safe, manual review recommended. |
| 88 | `MarkRead` | `UpdateOne` | `messages` | `_id`, `userId` | CRITICAL | ✓ | `inline` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 166 | `buildProductNameMap` | `Find` | `credit_bundles` | `_id` | HIGH | ✓ | `inline` | Read operation without tenantId, but the filter contains a globally-unique key — likely safe, manual review recommended. |
| 428 | `resolveStripeProducts` | `FindOne` | `credit_bundles` | `_id` | HIGH | ✓ | `inline` | Read operation without tenantId, but the filter contains a globally-unique key — likely safe, manual review recommended. |
| 252 | `InviteMember` | `DeleteOne` | `invitations` | `_id` | CRITICAL | ✓ | `inline` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 364 | `RemoveMember` | `DeleteOne` | `tenant_memberships` | `_id` | CRITICAL | ✓ | `inline` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 71 | `HandleWebhook` | `FindOneAndUpdate` | `webhook_events` | `eventId` | CRITICAL | ✓ | `inline` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 132 | `HandleWebhook` | `DeleteOne` | `webhook_events` | `eventId` | CRITICAL | ✓ | `inline` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 138 | `HandleWebhook` | `UpdateOne` | `webhook_events` | `eventId` | CRITICAL | ✓ | `inline` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 322 | `handleCheckoutCompleted` | `FindOne` | `credit_bundles` | `_id` | HIGH | ✓ | `inline` | Read operation without tenantId, but the filter contains a globally-unique key — likely safe, manual review recommended. |
| 105 | `GetWebhook` | `FindOne` | `webhooks` | `_id`, `isActive` | HIGH | ✓ | `inline` | Read operation without tenantId, but the filter contains a globally-unique key — likely safe, manual review recommended. |
| 279 | `CreateWebhook` | `InsertOne` | `webhooks` | `createdAt`, `createdBy`, `description`, `events`, `isActive`, `name`, `secret`, `secretPreview`, `updatedAt`, `url` | CRITICAL | ✓ | `struct-var:hook:Webhook` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 320 | `UpdateWebhook` | `UpdateByID` | `webhooks` | `_id` | CRITICAL | ✓ | `by-id` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 340 | `UpdateWebhook` | `FindOne` | `webhooks` | `_id` | HIGH | ✓ | `inline` | Read operation without tenantId, but the filter contains a globally-unique key — likely safe, manual review recommended. |
| 356 | `DeleteWebhook` | `UpdateByID` | `webhooks` | `_id` | CRITICAL | ✓ | `by-id` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 393 | `RegenerateSecret` | `UpdateByID` | `webhooks` | `_id` | CRITICAL | ✓ | `by-id` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 421 | `TestWebhook` | `FindOne` | `webhooks` | `_id`, `isActive` | HIGH | ✓ | `inline` | Read operation without tenantId, but the filter contains a globally-unique key — likely safe, manual review recommended. |
| 380 | `Seed` | `FindOne` | `config_vars` | `name` | HIGH | ✓ | `inline` | Read operation without tenantId, but the filter contains a globally-unique key — likely safe, manual review recommended. |
| 90 | `Set` | `UpdateOne` | `config_vars` | `name` | CRITICAL | ✓ | `inline` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 106 | `Reload` | `FindOne` | `config_vars` | `name` | HIGH | ✓ | `inline` | Read operation without tenantId, but the filter contains a globally-unique key — likely safe, manual review recommended. |
| 138 | `registerNode` | `UpdateOne` | `system_nodes` | `machineId` | CRITICAL | ✓ | `inline` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 165 | `heartbeat` | `UpdateOne` | `system_nodes` | `machineId` | CRITICAL | ✓ | `inline` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 112 | `tryAcquireOrRenew` | `FindOneAndUpdate` | `leader_locks` | `_id`, `expiresAt`, `holderId` | CRITICAL | ✓ | `variable:filter` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 148 | `isLeader` | `FindOne` | `leader_locks` | `_id` | HIGH | ✓ | `inline` | Read operation without tenantId, but the filter contains a globally-unique key — likely safe, manual review recommended. |
| 158 | `releaseLock` | `DeleteOne` | `leader_locks` | `_id`, `holderId` | CRITICAL | ✓ | `inline` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 113 | `authenticateAPIKey` | `FindOne` | `api_keys` | `keyHash`, `isActive` | HIGH | ✓ | `inline` | Read operation without tenantId, but the filter contains a globally-unique key — likely safe, manual review recommended. |
| 155 | `authenticateAPIKey` | `UpdateByID` | `api_keys` | `_id` | CRITICAL | ✓ | `by-id` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 168 | `isTokenRevoked` | `CountDocuments` | `revoked_tokens` | `tokenHash` | HIGH | ✓ | `inline` | Read operation without tenantId, but the filter contains a globally-unique key — likely safe, manual review recommended. |
| 156 | `allowDistributed` | `FindOneAndUpdate` | `<unknown>` | `_id`, `windowEnd` | CRITICAL | ✓ | `inline` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 165 | `allowDistributed` | `FindOneAndUpdate` | `<unknown>` | `_id` | CRITICAL | ✓ | `inline` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 352 | `NextInvoiceNumber` | `FindOneAndUpdate` | `counters` | `_id` | CRITICAL | ✓ | `inline` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 438 | `CreateTestAPIKey` | `InsertOne` | `api_keys` | `authority`, `createdAt`, `createdBy`, `isActive`, `keyHash`, `keyPreview`, `lastUsedAt`, `name` | CRITICAL | ✓ | `struct-var:apiKey:APIKey` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 462 | `CreateTestWebhook` | `InsertOne` | `webhooks` | `createdAt`, `createdBy`, `description`, `events`, `isActive`, `name`, `secret`, `secretPreview`, `updatedAt`, `url` | CRITICAL | ✓ | `struct-var:webhook:Webhook` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |

## MEDIUM — Global-Collection Queries (241)

| Line | Function | Operation | Collection | Filter fields | Risk | Safe key | Filter source | Note |
|------|----------|-----------|------------|---------------|------|----------|---------------|------|
| 67 | `cmdDoctor` | `FindOne` | `system_config` | — | MEDIUM |  | `inline` | Collection 'system_config' is in the exempt (global) list; tenant filtering is not strictly required, but queries sho... |
| 102 | `cmdDoctor` | `FindOne` | `tenants` | `isRoot` | MEDIUM |  | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 131 | `cmdFinancialSummary` | `CountDocuments` | `tenants` | `billingStatus` | MEDIUM |  | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 140 | `queryLogs` | `Find` | `system_logs` | — | MEDIUM |  | `variable:unknown:filter` | Collection 'system_logs' is in the exempt (global) list; tenant filtering is not strictly required, but queries shoul... |
| 193 | `logsFollow` | `Find` | `system_logs` | `createdAt` | MEDIUM |  | `variable:followFilter` | Collection 'system_logs' is in the exempt (global) list; tenant filtering is not strictly required, but queries shoul... |
| 23 | `cmdStats` | `EstimatedDocumentCount` | `users` | — | MEDIUM |  | `no-filter` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 27 | `cmdStats` | `EstimatedDocumentCount` | `tenants` | — | MEDIUM |  | `no-filter` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 31 | `cmdStats` | `CountDocuments` | `users` | `isActive` | MEDIUM |  | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 37 | `cmdStats` | `CountDocuments` | `tenants` | `billingStatus` | MEDIUM |  | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 51 | `cmdStats` | `Aggregate` | `system_logs` | — | MEDIUM |  | `variable-pipeline:pipeline` | Collection 'system_logs' is in the exempt (global) list; tenant filtering is not strictly required, but queries shoul... |
| 61 | `cmdTenantsList` | `Find` | `tenants` | — | MEDIUM |  | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 160 | `cmdTenantsGet` | `FindOne` | `tenants` | `_id` | MEDIUM | ✓ | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 166 | `cmdTenantsGet` | `FindOne` | `tenants` | `slug` | MEDIUM | ✓ | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 193 | `cmdTenantsGet` | `FindOne` | `plans` | `_id` | MEDIUM | ✓ | `inline` | Collection 'plans' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 289 | `resolveUserNames` | `Find` | `users` | `_id` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 317 | `resolvePlanNames` | `Find` | `plans` | `_id` | MEDIUM | ✓ | `inline` | Collection 'plans' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 73 | `cmdUsersList` | `Find` | `users` | `isActive` | MEDIUM |  | `variable:filter` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 287 | `cmdUsersSetActive` | `FindOne` | `users` | `email` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 301 | `cmdUsersSetActive` | `UpdateOne` | `users` | `_id` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 342 | `cmdUsersRevokeSessions` | `FindOne` | `users` | `email` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 360 | `lookupUserWithMemberships` | `FindOne` | `users` | `email` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 383 | `resolveTenantNames` | `Find` | `tenants` | `_id` | MEDIUM | ✓ | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 227 | `cmdSetup` | `FindOne` | `system_config` | — | MEDIUM |  | `inline` | Collection 'system_config' is in the exempt (global) list; tenant filtering is not strictly required, but queries sho... |
| 235 | `cmdSetup` | `FindOne` | `tenants` | `isRoot` | MEDIUM |  | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 239 | `cmdSetup` | `FindOne` | `users` | `_id` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 303 | `cmdSetup` | `InsertOne` | `tenants` | `billingInterval`, `billingStatus`, `billingWaived`, `canceledAt`, `createdAt`, `currentPeriodEnd`, `isActive`, `isRoot`, `name`, `planId`, `purchasedCredits`, `seatQuantity`, `slug`, `stripeCustomerId`, `stripeSubscriptionId`, `subscriptionCredits`, `trialUsedAt`, `updatedAt` | MEDIUM | ✓ | `struct-var:tenant:Tenant` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 321 | `cmdSetup` | `DeleteOne` | `tenants` | `_id` | MEDIUM | ✓ | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 325 | `cmdSetup` | `InsertOne` | `users` | `accountLockedUntil`, `authMethods`, `createdAt`, `displayName`, `email`, `emailVerified`, `failedLoginAttempts`, `githubId`, `googleId`, `isActive`, `lastLoginAt`, `lastVerificationSent`, `microsoftId`, `onboardingCompletedAt`, `passwordHash`, `recoveryCodes`, `themePreference`, `totpEnabled`, `totpSecret`, `totpVerifiedAt`, `trialUsedAt`, `updatedAt` | MEDIUM | ✓ | `struct-var:user:User` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 326 | `cmdSetup` | `DeleteOne` | `tenants` | `_id` | MEDIUM | ✓ | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 341 | `cmdSetup` | `DeleteOne` | `users` | `_id` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 342 | `cmdSetup` | `DeleteOne` | `tenants` | `_id` | MEDIUM | ✓ | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 347 | `cmdSetup` | `DeleteOne` | `users` | `_id` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 348 | `cmdSetup` | `DeleteOne` | `tenants` | `_id` | MEDIUM | ✓ | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 361 | `cmdSetup` | `InsertOne` | `system_config` | `initialized`, `initializedAt`, `initializedBy`, `version` | MEDIUM |  | `struct-var:sysConfig:SystemConfig` | Collection 'system_config' is in the exempt (global) list; tenant filtering is not strictly required, but queries sho... |
| 363 | `cmdSetup` | `DeleteOne` | `users` | `_id` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 364 | `cmdSetup` | `DeleteOne` | `tenants` | `_id` | MEDIUM | ✓ | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 417 | `cmdChangePassword` | `FindOne` | `users` | `email` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 447 | `cmdChangePassword` | `UpdateOne` | `users` | `_id` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 515 | `cmdSendMessage` | `FindOne` | `users` | `email` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 760 | `cmdTransferRootOwner` | `FindOne` | `tenants` | `isRoot` | MEDIUM |  | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 768 | `cmdTransferRootOwner` | `FindOne` | `users` | `email` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 800 | `cmdTransferRootOwner` | `FindOne` | `users` | `_id` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 885 | `cmdVersion` | `FindOne` | `system_config` | — | MEDIUM |  | `inline` | Collection 'system_config' is in the exempt (global) list; tenant filtering is not strictly required, but queries sho... |
| 931 | `cmdStatus` | `FindOne` | `system_config` | — | MEDIUM |  | `inline` | Collection 'system_config' is in the exempt (global) list; tenant filtering is not strictly required, but queries sho... |
| 946 | `cmdStatus` | `CountDocuments` | `users` | — | MEDIUM |  | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 950 | `cmdStatus` | `CountDocuments` | `tenants` | — | MEDIUM |  | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 68 | `isRootTenantOwner` | `FindOne` | `tenants` | `_id` | MEDIUM | ✓ | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 176 | `ListTenants` | `CountDocuments` | `tenants` | `$or`, `billingStatus`, `isActive` | MEDIUM |  | `variable:filter` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 187 | `ListTenants` | `Find` | `tenants` | `$or`, `billingStatus`, `isActive` | MEDIUM |  | `variable:filter` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 228 | `ListTenants` | `Find` | `plans` | — | MEDIUM |  | `inline` | Collection 'plans' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 312 | `ExportTenantsCSV` | `Find` | `tenants` | `$or`, `billingStatus`, `isActive` | MEDIUM |  | `variable:filter` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 353 | `ExportTenantsCSV` | `Find` | `plans` | — | MEDIUM |  | `inline` | Collection 'plans' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 418 | `GetTenant` | `FindOne` | `tenants` | `_id` | MEDIUM | ✓ | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 441 | `GetTenant` | `Find` | `users` | `_id` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 483 | `UpdateTenantStatus` | `FindOne` | `tenants` | `_id` | MEDIUM | ✓ | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 502 | `UpdateTenantStatus` | `UpdateOne` | `tenants` | `_id` | MEDIUM | ✓ | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 581 | `ListUsers` | `CountDocuments` | `users` | `$or`, `isActive` | MEDIUM |  | `variable:filter` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 592 | `ListUsers` | `Find` | `users` | `$or`, `isActive` | MEDIUM |  | `variable:filter` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 678 | `ExportUsersCSV` | `Find` | `users` | `$or`, `isActive` | MEDIUM |  | `variable:filter` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 774 | `UpdateUserStatus` | `UpdateOne` | `users` | `_id` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 817 | `GetDashboard` | `CountDocuments` | `users` | — | MEDIUM |  | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 822 | `GetDashboard` | `CountDocuments` | `tenants` | — | MEDIUM |  | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 943 | `GetUser` | `FindOne` | `users` | `_id` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 963 | `GetUser` | `Find` | `plans` | — | MEDIUM |  | `inline` | Collection 'plans' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 992 | `GetUser` | `Find` | `tenants` | `_id` | MEDIUM | ✓ | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 1079 | `UpdateUser` | `FindOne` | `users` | `_id` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 1098 | `UpdateUser` | `CountDocuments` | `users` | `email`, `_id` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 1121 | `UpdateUser` | `UpdateOne` | `users` | `_id` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 1165 | `UpdateUserRole` | `FindOne` | `tenants` | `_id` | MEDIUM | ✓ | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 1264 | `PreflightDeleteUser` | `Find` | `tenants` | `_id` | MEDIUM | ✓ | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 1301 | `PreflightDeleteUser` | `Find` | `users` | `_id` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 1358 | `DeleteUser` | `FindOne` | `users` | `_id` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 1398 | `DeleteUser` | `FindOne` | `tenants` | `_id` | MEDIUM | ✓ | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 1457 | `DeleteUser` | `DeleteOne` | `tenants` | `_id` | MEDIUM | ✓ | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 1488 | `DeleteUser` | `DeleteOne` | `users` | `_id` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 1529 | `UpdateTenant` | `FindOne` | `tenants` | `_id` | MEDIUM | ✓ | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 1587 | `UpdateTenant` | `UpdateOne` | `tenants` | `_id` | MEDIUM | ✓ | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 1619 | `ImpersonateUser` | `FindOne` | `users` | `_id` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 1626 | `ImpersonateUser` | `FindOne` | `tenants` | `isRoot` | MEDIUM |  | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 1680 | `ImpersonateUser` | `FindOne` | `tenants` | `_id` | MEDIUM | ✓ | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 1703 | `getRootTenant` | `FindOne` | `tenants` | `isRoot` | MEDIUM |  | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 1739 | `ListRootMembers` | `Find` | `users` | `_id` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 1837 | `InviteRootMember` | `FindOne` | `users` | `email` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 223 | `Register` | `FindOne` | `users` | `email` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 252 | `Register` | `InsertOne` | `users` | `accountLockedUntil`, `authMethods`, `createdAt`, `displayName`, `email`, `emailVerified`, `failedLoginAttempts`, `githubId`, `googleId`, `isActive`, `lastLoginAt`, `lastVerificationSent`, `microsoftId`, `onboardingCompletedAt`, `passwordHash`, `recoveryCodes`, `themePreference`, `totpEnabled`, `totpSecret`, `totpVerifiedAt`, `trialUsedAt`, `updatedAt` | MEDIUM | ✓ | `struct-var:user:User` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 330 | `Login` | `FindOne` | `users` | `email` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 359 | `Login` | `FindOneAndUpdate` | `users` | `_id`, `accountLockedUntil` | MEDIUM | ✓ | `variable:filter` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 367 | `Login` | `UpdateOne` | `users` | `_id` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 387 | `Login` | `UpdateOne` | `users` | `_id` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 537 | `Refresh` | `FindOne` | `users` | `_id`, `isActive` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 616 | `VerifyEmail` | `UpdateOne` | `users` | `_id` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 651 | `ResendVerification` | `FindOne` | `users` | `email` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 691 | `ForgotPassword` | `FindOne` | `users` | `email` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 767 | `ResetPassword` | `UpdateOne` | `users` | `_id` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 837 | `ChangePassword` | `UpdateOne` | `users` | `_id` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 889 | `MFASetup` | `UpdateOne` | `users` | `_id` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 920 | `MFAVerifySetup` | `FindOne` | `users` | `_id` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 944 | `MFAVerifySetup` | `UpdateOne` | `users` | `_id` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 981 | `MFADisable` | `FindOne` | `users` | `_id` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 1001 | `MFADisable` | `UpdateOne` | `users` | `_id` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 1051 | `MFAChallenge` | `FindOne` | `users` | `_id` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 1071 | `MFAChallenge` | `UpdateOne` | `users` | `_id` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 1127 | `MFARegenerateRecoveryCodes` | `FindOne` | `users` | `_id` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 1148 | `MFARegenerateRecoveryCodes` | `UpdateOne` | `users` | `_id` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 1190 | `MagicLinkRequest` | `FindOne` | `users` | `email` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 1252 | `MagicLinkVerify` | `FindOne` | `users` | `_id`, `isActive` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 1258 | `MagicLinkVerify` | `UpdateOne` | `users` | `_id` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 1423 | `GoogleOAuthCallback` | `FindOne` | `users` | `googleId` | MEDIUM |  | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 1425 | `GoogleOAuthCallback` | `FindOne` | `users` | `email` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 1440 | `GoogleOAuthCallback` | `InsertOne` | `users` | `accountLockedUntil`, `authMethods`, `createdAt`, `displayName`, `email`, `emailVerified`, `failedLoginAttempts`, `githubId`, `googleId`, `isActive`, `lastLoginAt`, `lastVerificationSent`, `microsoftId`, `onboardingCompletedAt`, `passwordHash`, `recoveryCodes`, `themePreference`, `totpEnabled`, `totpSecret`, `totpVerifiedAt`, `trialUsedAt`, `updatedAt` | MEDIUM | ✓ | `struct-var:user:User` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 1448 | `GoogleOAuthCallback` | `UpdateOne` | `users` | `_id` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 1454 | `GoogleOAuthCallback` | `UpdateOne` | `users` | `_id` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 1557 | `GitHubOAuthCallback` | `FindOne` | `users` | `githubId` | MEDIUM |  | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 1559 | `GitHubOAuthCallback` | `FindOne` | `users` | `email` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 1578 | `GitHubOAuthCallback` | `InsertOne` | `users` | `accountLockedUntil`, `authMethods`, `createdAt`, `displayName`, `email`, `emailVerified`, `failedLoginAttempts`, `githubId`, `googleId`, `isActive`, `lastLoginAt`, `lastVerificationSent`, `microsoftId`, `onboardingCompletedAt`, `passwordHash`, `recoveryCodes`, `themePreference`, `totpEnabled`, `totpSecret`, `totpVerifiedAt`, `trialUsedAt`, `updatedAt` | MEDIUM | ✓ | `struct-var:user:User` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 1591 | `GitHubOAuthCallback` | `UpdateOne` | `users` | `_id` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 1597 | `GitHubOAuthCallback` | `UpdateOne` | `users` | `_id` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 1704 | `MicrosoftOAuthCallback` | `FindOne` | `users` | `microsoftId` | MEDIUM |  | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 1706 | `MicrosoftOAuthCallback` | `FindOne` | `users` | `email` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 1725 | `MicrosoftOAuthCallback` | `InsertOne` | `users` | `accountLockedUntil`, `authMethods`, `createdAt`, `displayName`, `email`, `emailVerified`, `failedLoginAttempts`, `githubId`, `googleId`, `isActive`, `lastLoginAt`, `lastVerificationSent`, `microsoftId`, `onboardingCompletedAt`, `passwordHash`, `recoveryCodes`, `themePreference`, `totpEnabled`, `totpSecret`, `totpVerifiedAt`, `trialUsedAt`, `updatedAt` | MEDIUM | ✓ | `struct-var:user:User` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 1738 | `MicrosoftOAuthCallback` | `UpdateOne` | `users` | `_id` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 1744 | `MicrosoftOAuthCallback` | `UpdateOne` | `users` | `_id` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 1922 | `UpdatePreferences` | `UpdateOne` | `users` | `_id` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 1937 | `CompleteOnboarding` | `UpdateOne` | `users` | `_id` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 1991 | `createPersonalTenant` | `InsertOne` | `tenants` | `billingInterval`, `billingStatus`, `billingWaived`, `canceledAt`, `createdAt`, `currentPeriodEnd`, `isActive`, `isRoot`, `name`, `planId`, `purchasedCredits`, `seatQuantity`, `slug`, `stripeCustomerId`, `stripeSubscriptionId`, `subscriptionCredits`, `trialUsedAt`, `updatedAt` | MEDIUM | ✓ | `struct-var:tenant:Tenant` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 2029 | `sendVerificationEmail` | `UpdateOne` | `users` | `_id` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 2062 | `getUserMemberships` | `FindOne` | `tenants` | `_id` | MEDIUM | ✓ | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 2093 | `acceptInvitationForUser` | `FindOne` | `users` | `_id` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 2135 | `acceptInvitationForUser` | `UpdateOne` | `users` | `_id` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 2261 | `DeleteAccount` | `FindOne` | `tenants` | `_id` | MEDIUM | ✓ | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 2283 | `DeleteAccount` | `DeleteOne` | `tenants` | `_id` | MEDIUM | ✓ | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 2311 | `DeleteAccount` | `DeleteOne` | `users` | `_id` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 94 | `Checkout` | `FindOne` | `plans` | `_id` | MEDIUM | ✓ | `inline` | Collection 'plans' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 122 | `Checkout` | `UpdateOne` | `tenants` | `_id` | MEDIUM | ✓ | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 152 | `Checkout` | `UpdateOne` | `tenants` | `_id` | MEDIUM | ✓ | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 654 | `CancelSubscription` | `UpdateOne` | `tenants` | `_id` | MEDIUM | ✓ | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 929 | `computeLiveARR` | `Aggregate` | `tenants` | `billingStatus`, `planId` | MEDIUM |  | `variable-pipeline:pipeline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 955 | `AdminCancelSubscription` | `FindOne` | `tenants` | `_id` | MEDIUM | ✓ | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 1001 | `AdminCancelSubscription` | `UpdateOne` | `tenants` | `_id` | MEDIUM | ✓ | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 1034 | `AdminUpdateSubscription` | `UpdateOne` | `tenants` | `_id` | MEDIUM | ✓ | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 36 | `refreshInitialized` | `FindOne` | `system_config` | — | MEDIUM |  | `inline` | Collection 'system_config' is in the exempt (global) list; tenant filtering is not strictly required, but queries sho... |
| 66 | `refreshInitializedFromContext` | `FindOne` | `system_config` | — | MEDIUM |  | `inline` | Collection 'system_config' is in the exempt (global) list; tenant filtering is not strictly required, but queries sho... |
| 111 | `ListLogs` | `EstimatedDocumentCount` | `system_logs` | — | MEDIUM |  | `no-filter` | Collection 'system_logs' is in the exempt (global) list; tenant filtering is not strictly required, but queries shoul... |
| 113 | `ListLogs` | `CountDocuments` | `system_logs` | — | MEDIUM |  | `variable:unknown:filter` | Collection 'system_logs' is in the exempt (global) list; tenant filtering is not strictly required, but queries shoul... |
| 125 | `ListLogs` | `Find` | `system_logs` | — | MEDIUM |  | `variable:unknown:filter` | Collection 'system_logs' is in the exempt (global) list; tenant filtering is not strictly required, but queries shoul... |
| 156 | `SeverityCounts` | `Aggregate` | `system_logs` | — | MEDIUM |  | `variable-pipeline:pipeline` | Collection 'system_logs' is in the exempt (global) list; tenant filtering is not strictly required, but queries shoul... |
| 196 | `ExportCSV` | `Find` | `system_logs` | — | MEDIUM |  | `variable:unknown:filter` | Collection 'system_logs' is in the exempt (global) list; tenant filtering is not strictly required, but queries shoul... |
| 48 | `ListPlans` | `Find` | `plans` | — | MEDIUM |  | `inline` | Collection 'plans' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 66 | `ListPlans` | `Aggregate` | `tenants` | — | MEDIUM |  | `inline-pipeline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 93 | `ListPlans` | `CountDocuments` | `plans` | — | MEDIUM |  | `inline` | Collection 'plans' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 110 | `GetPlan` | `FindOne` | `plans` | `_id` | MEDIUM | ✓ | `inline` | Collection 'plans' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 123 | `ListEntitlementKeys` | `Find` | `plans` | — | MEDIUM |  | `inline` | Collection 'plans' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 253 | `CreatePlan` | `CountDocuments` | `plans` | `name` | MEDIUM | ✓ | `inline` | Collection 'plans' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 295 | `CreatePlan` | `InsertOne` | `plans` | `annualDiscountPct`, `bonusCredits`, `createdAt`, `creditResetPolicy`, `description`, `entitlements`, `includedSeats`, `isArchived`, `isSystem`, `maxSeats`, `minSeats`, `monthlyPriceCents`, `name`, `perSeatPriceCents`, `pricingModel`, `trialDays`, `updatedAt`, `usageCreditsPerMonth`, `userLimit` | MEDIUM | ✓ | `struct-var:plan:Plan` | Collection 'plans' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 323 | `UpdatePlan` | `FindOne` | `plans` | `_id` | MEDIUM | ✓ | `inline` | Collection 'plans' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 350 | `UpdatePlan` | `CountDocuments` | `plans` | `name`, `_id` | MEDIUM | ✓ | `inline` | Collection 'plans' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 393 | `UpdatePlan` | `UpdateByID` | `plans` | `_id` | MEDIUM | ✓ | `by-id` | Collection 'plans' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 404 | `UpdatePlan` | `FindOne` | `plans` | `_id` | MEDIUM | ✓ | `inline` | Collection 'plans' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 408 | `UpdatePlan` | `CountDocuments` | `tenants` | `planId` | MEDIUM |  | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 446 | `DeletePlan` | `FindOne` | `plans` | `_id` | MEDIUM | ✓ | `inline` | Collection 'plans' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 460 | `DeletePlan` | `CountDocuments` | `tenants` | `planId` | MEDIUM |  | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 470 | `DeletePlan` | `DeleteOne` | `plans` | `_id` | MEDIUM | ✓ | `inline` | Collection 'plans' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 491 | `ArchivePlan` | `FindOne` | `plans` | `_id` | MEDIUM | ✓ | `inline` | Collection 'plans' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 505 | `ArchivePlan` | `UpdateByID` | `plans` | `_id` | MEDIUM | ✓ | `by-id` | Collection 'plans' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 526 | `UnarchivePlan` | `FindOne` | `plans` | `_id` | MEDIUM | ✓ | `inline` | Collection 'plans' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 540 | `UnarchivePlan` | `UpdateByID` | `plans` | `_id` | MEDIUM | ✓ | `by-id` | Collection 'plans' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 576 | `AssignPlan` | `FindOne` | `tenants` | `_id` | MEDIUM | ✓ | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 598 | `AssignPlan` | `FindOne` | `plans` | `_id` | MEDIUM | ✓ | `inline` | Collection 'plans' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 627 | `AssignPlan` | `FindOne` | `plans` | `_id` | MEDIUM | ✓ | `inline` | Collection 'plans' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 671 | `AssignPlan` | `UpdateByID` | `tenants` | `_id` | MEDIUM | ✓ | `by-id` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 703 | `ListPlansPublic` | `FindOne` | `tenants` | `_id` | MEDIUM | ✓ | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 737 | `ListPlansPublic` | `Find` | `plans` | `isArchived` | MEDIUM |  | `variable:filter` | Collection 'plans' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 817 | `lookupPlanForTenant` | `FindOne` | `plans` | `_id` | MEDIUM | ✓ | `inline` | Collection 'plans' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 820 | `lookupPlanForTenant` | `FindOne` | `plans` | `isSystem` | MEDIUM |  | `inline` | Collection 'plans' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 146 | `buildProductNameMap` | `Find` | `plans` | `_id` | MEDIUM | ✓ | `inline` | Collection 'plans' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 200 | `ListEligibleProducts` | `Find` | `plans` | `isArchived` | MEDIUM |  | `inline` | Collection 'plans' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 380 | `resolveStripeProducts` | `FindOne` | `plans` | `_id` | MEDIUM | ✓ | `inline` | Collection 'plans' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 94 | `ListMembers` | `Find` | `users` | `_id` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 171 | `InviteMember` | `FindOne` | `users` | `email` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 205 | `InviteMember` | `FindOne` | `plans` | `_id` | MEDIUM | ✓ | `inline` | Collection 'plans' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 209 | `InviteMember` | `FindOne` | `plans` | `isSystem` | MEDIUM |  | `inline` | Collection 'plans' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 283 | `InviteMember` | `UpdateOne` | `tenants` | `_id` | MEDIUM | ✓ | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 372 | `RemoveMember` | `FindOne` | `plans` | `_id` | MEDIUM | ✓ | `inline` | Collection 'plans' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 388 | `RemoveMember` | `UpdateOne` | `tenants` | `_id` | MEDIUM | ✓ | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 642 | `UpdateTenantSettings` | `UpdateOne` | `tenants` | `_id` | MEDIUM | ✓ | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 90 | `RecordUsage` | `UpdateOne` | `tenants` | `_id`, `subscriptionCredits` | MEDIUM | ✓ | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 100 | `RecordUsage` | `UpdateOne` | `tenants` | `_id`, `purchasedCredits` | MEDIUM | ✓ | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 196 | `GetSummary` | `FindOne` | `tenants` | `_id` | MEDIUM | ✓ | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 170 | `handleCheckoutCompleted` | `FindOne` | `tenants` | `_id` | MEDIUM | ✓ | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 182 | `handleCheckoutCompleted` | `FindOne` | `tenants` | `stripeCustomerId`, `_id` | MEDIUM | ✓ | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 205 | `handleCheckoutCompleted` | `FindOne` | `plans` | `_id` | MEDIUM | ✓ | `inline` | Collection 'plans' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 239 | `handleCheckoutCompleted` | `UpdateOne` | `users` | `_id` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 255 | `handleCheckoutCompleted` | `UpdateOne` | `tenants` | `_id` | MEDIUM | ✓ | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 328 | `handleCheckoutCompleted` | `UpdateOne` | `tenants` | `_id` | MEDIUM | ✓ | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 391 | `handleInvoicePaid` | `FindOne` | `tenants` | `stripeSubscriptionId` | MEDIUM |  | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 397 | `handleInvoicePaid` | `UpdateOne` | `tenants` | `_id` | MEDIUM | ✓ | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 407 | `handleInvoicePaid` | `FindOne` | `plans` | `_id` | MEDIUM | ✓ | `inline` | Collection 'plans' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 409 | `handleInvoicePaid` | `UpdateOne` | `tenants` | `_id` | MEDIUM | ✓ | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 415 | `handleInvoicePaid` | `UpdateOne` | `tenants` | `_id` | MEDIUM | ✓ | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 443 | `handleInvoicePaid` | `FindOne` | `plans` | `_id` | MEDIUM | ✓ | `inline` | Collection 'plans' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 482 | `handleInvoicePaymentFailed` | `FindOne` | `tenants` | `stripeSubscriptionId` | MEDIUM |  | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 488 | `handleInvoicePaymentFailed` | `UpdateOne` | `tenants` | `_id` | MEDIUM | ✓ | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 551 | `handleSubscriptionUpdated` | `FindOne` | `tenants` | `stripeSubscriptionId` | MEDIUM |  | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 583 | `handleSubscriptionUpdated` | `FindOne` | `plans` | `_id` | MEDIUM | ✓ | `inline` | Collection 'plans' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 598 | `handleSubscriptionUpdated` | `UpdateOne` | `tenants` | `_id` | MEDIUM | ✓ | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 613 | `handleSubscriptionDeleted` | `FindOne` | `tenants` | `stripeSubscriptionId` | MEDIUM |  | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 619 | `handleSubscriptionDeleted` | `FindOne` | `plans` | `isSystem` | MEDIUM |  | `inline` | Collection 'plans' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 635 | `handleSubscriptionDeleted` | `UpdateOne` | `tenants` | `_id` | MEDIUM | ✓ | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 675 | `handleChargeRefunded` | `FindOne` | `tenants` | `stripeCustomerId` | MEDIUM |  | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 726 | `handleDisputeCreated` | `FindOne` | `tenants` | `stripeCustomerId` | MEDIUM |  | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 732 | `handleDisputeCreated` | `UpdateOne` | `tenants` | `_id` | MEDIUM | ✓ | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 771 | `handleDisputeClosed` | `FindOne` | `tenants` | `stripeCustomerId` | MEDIUM |  | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 779 | `handleDisputeClosed` | `UpdateOne` | `tenants` | `_id` | MEDIUM | ✓ | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 192 | `collectDaily` | `Aggregate` | `users` | `lastLoginAt` | MEDIUM |  | `variable-pipeline:dauWauMauPipeline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 263 | `collectDaily` | `Aggregate` | `tenants` | `billingStatus`, `planId` | MEDIUM |  | `variable-pipeline:arrPipeline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 90 | `authenticateJWT` | `FindOne` | `users` | `_id` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 124 | `authenticateAPIKey` | `FindOne` | `users` | `_id` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 135 | `authenticateAPIKey` | `FindOne` | `tenants` | `isRoot` | MEDIUM |  | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 51 | `RequireTenant` | `FindOne` | `tenants` | `_id`, `isActive` | MEDIUM | ✓ | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 141 | `RequireEntitlement` | `FindOne` | `plans` | `_id` | MEDIUM | ✓ | `inline` | Collection 'plans' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 19 | `Seed` | `FindOne` | `plans` | `isSystem` | MEDIUM |  | `inline` | Collection 'plans' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 36 | `Seed` | `InsertOne` | `plans` | `annualDiscountPct`, `bonusCredits`, `createdAt`, `creditResetPolicy`, `description`, `entitlements`, `includedSeats`, `isArchived`, `isSystem`, `maxSeats`, `minSeats`, `monthlyPriceCents`, `name`, `perSeatPriceCents`, `pricingModel`, `trialDays`, `updatedAt`, `usageCreditsPerMonth`, `userLimit` | MEDIUM | ✓ | `struct-var:plan:Plan` | Collection 'plans' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 82 | `GetOrCreateCustomer` | `UpdateOne` | `tenants` | `_id` | MEDIUM | ✓ | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 320 | `FunnelMetrics` | `CountDocuments` | `users` | `createdAt` | MEDIUM |  | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 447 | `RetentionCohorts` | `Aggregate` | `users` | — | MEDIUM |  | `variable-pipeline:pipeline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 596 | `computeKPIs` | `CountDocuments` | `tenants` | `billingStatus`, `isActive` | MEDIUM |  | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 605 | `computeKPIs` | `CountDocuments` | `users` | — | MEDIUM |  | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 621 | `computeKPIs` | `CountDocuments` | `tenants` | `canceledAt` | MEDIUM |  | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 627 | `computeKPIs` | `CountDocuments` | `tenants` | `billingStatus` | MEDIUM |  | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 640 | `computeKPIs` | `CountDocuments` | `tenants` | `trialUsedAt` | MEDIUM |  | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 646 | `computeKPIs` | `CountDocuments` | `tenants` | `trialUsedAt` | MEDIUM |  | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 813 | `getActiveTenantIDs` | `Find` | `tenants` | `billingStatus`, `isActive` | MEDIUM |  | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 1098 | `calculateMRR` | `Aggregate` | `tenants` | — | MEDIUM |  | `variable-pipeline:pipeline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 1192 | `planDistribution` | `Aggregate` | `tenants` | — | MEDIUM |  | `variable-pipeline:pipeline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 270 | `CreateTestUser` | `InsertOne` | `users` | `accountLockedUntil`, `authMethods`, `createdAt`, `displayName`, `email`, `emailVerified`, `failedLoginAttempts`, `githubId`, `googleId`, `isActive`, `lastLoginAt`, `lastVerificationSent`, `microsoftId`, `onboardingCompletedAt`, `passwordHash`, `recoveryCodes`, `themePreference`, `totpEnabled`, `totpSecret`, `totpVerifiedAt`, `trialUsedAt`, `updatedAt` | MEDIUM | ✓ | `struct-var:user:User` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 292 | `CreateTestTenant` | `InsertOne` | `tenants` | `billingInterval`, `billingStatus`, `billingWaived`, `canceledAt`, `createdAt`, `currentPeriodEnd`, `isActive`, `isRoot`, `name`, `planId`, `purchasedCredits`, `seatQuantity`, `slug`, `stripeCustomerId`, `stripeSubscriptionId`, `subscriptionCredits`, `trialUsedAt`, `updatedAt` | MEDIUM | ✓ | `struct-var:tenant:Tenant` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 318 | `MarkSystemInitialized` | `InsertOne` | `system_config` | `initialized`, `initializedAt`, `initializedBy`, `version` | MEDIUM |  | `struct:SystemConfig` | Collection 'system_config' is in the exempt (global) list; tenant filtering is not strictly required, but queries sho... |
| 416 | `CreateTestPlan` | `InsertOne` | `plans` | `annualDiscountPct`, `bonusCredits`, `createdAt`, `creditResetPolicy`, `description`, `entitlements`, `includedSeats`, `isArchived`, `isSystem`, `maxSeats`, `minSeats`, `monthlyPriceCents`, `name`, `perSeatPriceCents`, `pricingModel`, `trialDays`, `updatedAt`, `usageCreditsPerMonth`, `userLimit` | MEDIUM | ✓ | `struct-var:plan:Plan` | Collection 'plans' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 28 | `CheckAndMigrate` | `FindOne` | `system_config` | — | MEDIUM |  | `inline` | Collection 'system_config' is in the exempt (global) list; tenant filtering is not strictly required, but queries sho... |
| 50 | `CheckAndMigrate` | `UpdateOne` | `system_config` | `_id` | MEDIUM | ✓ | `inline` | Collection 'system_config' is in the exempt (global) list; tenant filtering is not strictly required, but queries sho... |
| 65 | `sendUpgradeMessage` | `FindOne` | `tenants` | `isRoot` | MEDIUM |  | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |

## All Queries by File

### `cmd/lastsaas/cmd_doctor.go`

| Line | Function | Operation | Collection | Filter fields | Risk | Safe key | Filter source | Note |
|------|----------|-----------|------------|---------------|------|----------|---------------|------|
| 67 | `cmdDoctor` | `FindOne` | `system_config` | — | MEDIUM |  | `inline` | Collection 'system_config' is in the exempt (global) list; tenant filtering is not strictly required, but queries sho... |
| 102 | `cmdDoctor` | `FindOne` | `tenants` | `isRoot` | MEDIUM |  | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 103 | `cmdDoctor` | `CountDocuments` | `tenant_memberships` | `tenantId`, `role` | OK |  | `inline` | Filter contains tenantId. |
| 115 | `cmdDoctor` | `CountDocuments` | `system_nodes` | `lastSeen` | HIGH |  | `inline` | Read operation on a tenant-scoped collection without tenantId in the filter. HIGH: cross-tenant data leakage risk. |


### `cmd/lastsaas/cmd_financial.go`

| Line | Function | Operation | Collection | Filter fields | Risk | Safe key | Filter source | Note |
|------|----------|-----------|------------|---------------|------|----------|---------------|------|
| 58 | `cmdFinancialSummary` | `Aggregate` | `financial_transactions` | `type` | HIGH |  | `variable-pipeline:revPipeline` | Read operation on a tenant-scoped collection without tenantId in the filter. HIGH: cross-tenant data leakage risk. |
| 84 | `cmdFinancialSummary` | `Aggregate` | `financial_transactions` | `type` | HIGH |  | `variable-pipeline:refundPipeline` | Read operation on a tenant-scoped collection without tenantId in the filter. HIGH: cross-tenant data leakage risk. |
| 111 | `cmdFinancialSummary` | `Aggregate` | `financial_transactions` | — | HIGH |  | `variable-pipeline:typePipeline` | Read operation with an empty filter — returns ALL documents. HIGH: cross-tenant data leakage risk. |
| 131 | `cmdFinancialSummary` | `CountDocuments` | `tenants` | `billingStatus` | MEDIUM |  | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 138 | `cmdFinancialSummary` | `FindOne` | `daily_metrics` | — | HIGH |  | `inline` | Read operation with an empty filter — returns ALL documents. HIGH: cross-tenant data leakage risk. |
| 147 | `cmdFinancialSummary` | `Aggregate` | `financial_transactions` | `type` | HIGH |  | `variable-pipeline:rev30Pipeline` | Read operation on a tenant-scoped collection without tenantId in the filter. HIGH: cross-tenant data leakage risk. |
| 254 | `cmdFinancialTransactions` | `Find` | `financial_transactions` | `createdAt`, `tenantId`, `type` | OK |  | `variable:filter` | Filter contains tenantId. |
| 350 | `cmdFinancialMetrics` | `Find` | `daily_metrics` | — | HIGH |  | `inline` | Read operation with an empty filter — returns ALL documents. HIGH: cross-tenant data leakage risk. |


### `cmd/lastsaas/cmd_health.go`

| Line | Function | Operation | Collection | Filter fields | Risk | Safe key | Filter source | Note |
|------|----------|-----------|------------|---------------|------|----------|---------------|------|
| 51 | `cmdHealth` | `Find` | `system_nodes` | — | HIGH |  | `inline` | Read operation with an empty filter — returns ALL documents. HIGH: cross-tenant data leakage risk. |
| 77 | `cmdHealth` | `FindOne` | `system_metrics` | — | HIGH |  | `inline` | Read operation with an empty filter — returns ALL documents. HIGH: cross-tenant data leakage risk. |
| 100 | `cmdHealth` | `Find` | `system_nodes` | — | HIGH |  | `inline` | Read operation with an empty filter — returns ALL documents. HIGH: cross-tenant data leakage risk. |
| 124 | `cmdHealth` | `FindOne` | `system_metrics` | — | HIGH |  | `inline` | Read operation with an empty filter — returns ALL documents. HIGH: cross-tenant data leakage risk. |


### `cmd/lastsaas/cmd_logs.go`

| Line | Function | Operation | Collection | Filter fields | Risk | Safe key | Filter source | Note |
|------|----------|-----------|------------|---------------|------|----------|---------------|------|
| 140 | `queryLogs` | `Find` | `system_logs` | — | MEDIUM |  | `variable:unknown:filter` | Collection 'system_logs' is in the exempt (global) list; tenant filtering is not strictly required, but queries shoul... |
| 193 | `logsFollow` | `Find` | `system_logs` | `createdAt` | MEDIUM |  | `variable:followFilter` | Collection 'system_logs' is in the exempt (global) list; tenant filtering is not strictly required, but queries shoul... |


### `cmd/lastsaas/cmd_stats.go`

| Line | Function | Operation | Collection | Filter fields | Risk | Safe key | Filter source | Note |
|------|----------|-----------|------------|---------------|------|----------|---------------|------|
| 23 | `cmdStats` | `EstimatedDocumentCount` | `users` | — | MEDIUM |  | `no-filter` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 27 | `cmdStats` | `EstimatedDocumentCount` | `tenants` | — | MEDIUM |  | `no-filter` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 31 | `cmdStats` | `CountDocuments` | `users` | `isActive` | MEDIUM |  | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 37 | `cmdStats` | `CountDocuments` | `tenants` | `billingStatus` | MEDIUM |  | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 51 | `cmdStats` | `Aggregate` | `system_logs` | — | MEDIUM |  | `variable-pipeline:pipeline` | Collection 'system_logs' is in the exempt (global) list; tenant filtering is not strictly required, but queries shoul... |
| 71 | `cmdStats` | `FindOne` | `daily_metrics` | — | HIGH |  | `inline` | Read operation with an empty filter — returns ALL documents. HIGH: cross-tenant data leakage risk. |
| 79 | `cmdStats` | `Aggregate` | `financial_transactions` | `type` | HIGH |  | `variable-pipeline:revPipeline` | Read operation on a tenant-scoped collection without tenantId in the filter. HIGH: cross-tenant data leakage risk. |


### `cmd/lastsaas/cmd_tenants.go`

| Line | Function | Operation | Collection | Filter fields | Risk | Safe key | Filter source | Note |
|------|----------|-----------|------------|---------------|------|----------|---------------|------|
| 61 | `cmdTenantsList` | `Find` | `tenants` | — | MEDIUM |  | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 160 | `cmdTenantsGet` | `FindOne` | `tenants` | `_id` | MEDIUM | ✓ | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 166 | `cmdTenantsGet` | `FindOne` | `tenants` | `slug` | MEDIUM | ✓ | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 173 | `cmdTenantsGet` | `Find` | `tenant_memberships` | `tenantId` | OK |  | `inline` | Filter contains tenantId. |
| 193 | `cmdTenantsGet` | `FindOne` | `plans` | `_id` | MEDIUM | ✓ | `inline` | Collection 'plans' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 289 | `resolveUserNames` | `Find` | `users` | `_id` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 317 | `resolvePlanNames` | `Find` | `plans` | `_id` | MEDIUM | ✓ | `inline` | Collection 'plans' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 355 | `countMembersPerTenant` | `Aggregate` | `tenant_memberships` | `tenantId` | OK |  | `variable-pipeline:pipeline` | Filter contains tenantId. |


### `cmd/lastsaas/cmd_users.go`

| Line | Function | Operation | Collection | Filter fields | Risk | Safe key | Filter source | Note |
|------|----------|-----------|------------|---------------|------|----------|---------------|------|
| 73 | `cmdUsersList` | `Find` | `users` | `isActive` | MEDIUM |  | `variable:filter` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 287 | `cmdUsersSetActive` | `FindOne` | `users` | `email` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 301 | `cmdUsersSetActive` | `UpdateOne` | `users` | `_id` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 314 | `cmdUsersSetActive` | `DeleteMany` | `refresh_tokens` | `userId` | CRITICAL |  | `inline` | DeleteMany on a tenant-scoped collection without tenantId in the filter. CRITICAL: this can modify/delete data belong... |
| 342 | `cmdUsersRevokeSessions` | `FindOne` | `users` | `email` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 347 | `cmdUsersRevokeSessions` | `DeleteMany` | `refresh_tokens` | `userId` | CRITICAL |  | `inline` | DeleteMany on a tenant-scoped collection without tenantId in the filter. CRITICAL: this can modify/delete data belong... |
| 360 | `lookupUserWithMemberships` | `FindOne` | `users` | `email` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 365 | `lookupUserWithMemberships` | `Find` | `tenant_memberships` | `userId` | HIGH |  | `inline` | Read operation on a tenant-scoped collection without tenantId in the filter. HIGH: cross-tenant data leakage risk. |
| 383 | `resolveTenantNames` | `Find` | `tenants` | `_id` | MEDIUM | ✓ | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |


### `cmd/lastsaas/main.go`

| Line | Function | Operation | Collection | Filter fields | Risk | Safe key | Filter source | Note |
|------|----------|-----------|------------|---------------|------|----------|---------------|------|
| 227 | `cmdSetup` | `FindOne` | `system_config` | — | MEDIUM |  | `inline` | Collection 'system_config' is in the exempt (global) list; tenant filtering is not strictly required, but queries sho... |
| 235 | `cmdSetup` | `FindOne` | `tenants` | `isRoot` | MEDIUM |  | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 237 | `cmdSetup` | `FindOne` | `tenant_memberships` | `tenantId`, `role` | OK |  | `inline` | Filter contains tenantId. |
| 239 | `cmdSetup` | `FindOne` | `users` | `_id` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 303 | `cmdSetup` | `InsertOne` | `tenants` | `billingInterval`, `billingStatus`, `billingWaived`, `canceledAt`, `createdAt`, `currentPeriodEnd`, `isActive`, `isRoot`, `name`, `planId`, `purchasedCredits`, `seatQuantity`, `slug`, `stripeCustomerId`, `stripeSubscriptionId`, `subscriptionCredits`, `trialUsedAt`, `updatedAt` | MEDIUM | ✓ | `struct-var:tenant:Tenant` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 321 | `cmdSetup` | `DeleteOne` | `tenants` | `_id` | MEDIUM | ✓ | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 325 | `cmdSetup` | `InsertOne` | `users` | `accountLockedUntil`, `authMethods`, `createdAt`, `displayName`, `email`, `emailVerified`, `failedLoginAttempts`, `githubId`, `googleId`, `isActive`, `lastLoginAt`, `lastVerificationSent`, `microsoftId`, `onboardingCompletedAt`, `passwordHash`, `recoveryCodes`, `themePreference`, `totpEnabled`, `totpSecret`, `totpVerifiedAt`, `trialUsedAt`, `updatedAt` | MEDIUM | ✓ | `struct-var:user:User` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 326 | `cmdSetup` | `DeleteOne` | `tenants` | `_id` | MEDIUM | ✓ | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 341 | `cmdSetup` | `DeleteOne` | `users` | `_id` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 342 | `cmdSetup` | `DeleteOne` | `tenants` | `_id` | MEDIUM | ✓ | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 346 | `cmdSetup` | `InsertOne` | `tenant_memberships` | `joinedAt`, `role`, `tenantId`, `updatedAt`, `userId` | OK |  | `struct-var:membership:TenantMembership` | Filter contains tenantId. |
| 347 | `cmdSetup` | `DeleteOne` | `users` | `_id` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 348 | `cmdSetup` | `DeleteOne` | `tenants` | `_id` | MEDIUM | ✓ | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 361 | `cmdSetup` | `InsertOne` | `system_config` | `initialized`, `initializedAt`, `initializedBy`, `version` | MEDIUM |  | `struct-var:sysConfig:SystemConfig` | Collection 'system_config' is in the exempt (global) list; tenant filtering is not strictly required, but queries sho... |
| 362 | `cmdSetup` | `DeleteOne` | `tenant_memberships` | `_id` | CRITICAL | ✓ | `inline` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 363 | `cmdSetup` | `DeleteOne` | `users` | `_id` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 364 | `cmdSetup` | `DeleteOne` | `tenants` | `_id` | MEDIUM | ✓ | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 379 | `cmdSetup` | `InsertOne` | `messages` | `body`, `createdAt`, `isSystem`, `read`, `subject`, `userId` | CRITICAL |  | `struct-var:welcomeMsg:Message` | InsertOne with welcomeMsg (a Message struct); the struct definition does NOT declare a tenantId bson field. CRITICAL:... |
| 417 | `cmdChangePassword` | `FindOne` | `users` | `email` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 447 | `cmdChangePassword` | `UpdateOne` | `users` | `_id` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 460 | `cmdChangePassword` | `DeleteMany` | `refresh_tokens` | `userId` | CRITICAL |  | `inline` | DeleteMany on a tenant-scoped collection without tenantId in the filter. CRITICAL: this can modify/delete data belong... |
| 515 | `cmdSendMessage` | `FindOne` | `users` | `email` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 531 | `cmdSendMessage` | `InsertOne` | `messages` | `body`, `createdAt`, `isSystem`, `read`, `subject`, `userId` | CRITICAL |  | `struct-var:msg:Message` | InsertOne with msg (a Message struct); the struct definition does NOT declare a tenantId bson field. CRITICAL: insert... |
| 587 | `cmdConfigList` | `Find` | `config_vars` | — | HIGH |  | `inline` | Read operation with an empty filter — returns ALL documents. HIGH: cross-tenant data leakage risk. |
| 635 | `cmdConfigGet` | `FindOne` | `config_vars` | `name` | HIGH | ✓ | `inline` | Read operation without tenantId, but the filter contains a globally-unique key — likely safe, manual review recommended. |
| 665 | `cmdConfigSet` | `FindOne` | `config_vars` | `name` | HIGH | ✓ | `inline` | Read operation without tenantId, but the filter contains a globally-unique key — likely safe, manual review recommended. |
| 676 | `cmdConfigSet` | `UpdateOne` | `config_vars` | `name` | CRITICAL | ✓ | `inline` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 713 | `cmdConfigReset` | `FindOne` | `config_vars` | `name` | HIGH | ✓ | `inline` | Read operation without tenantId, but the filter contains a globally-unique key — likely safe, manual review recommended. |
| 724 | `cmdConfigReset` | `UpdateOne` | `config_vars` | `name` | CRITICAL | ✓ | `inline` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 760 | `cmdTransferRootOwner` | `FindOne` | `tenants` | `isRoot` | MEDIUM |  | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 768 | `cmdTransferRootOwner` | `FindOne` | `users` | `email` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 775 | `cmdTransferRootOwner` | `FindOne` | `tenant_memberships` | `userId`, `tenantId` | OK |  | `inline` | Filter contains tenantId. |
| 791 | `cmdTransferRootOwner` | `FindOne` | `tenant_memberships` | `tenantId`, `role` | OK |  | `inline` | Filter contains tenantId. |
| 800 | `cmdTransferRootOwner` | `FindOne` | `users` | `_id` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 831 | `cmdTransferRootOwner` | `UpdateOne` | `tenant_memberships` | `_id` | CRITICAL | ✓ | `inline` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 841 | `cmdTransferRootOwner` | `UpdateOne` | `tenant_memberships` | `_id` | CRITICAL | ✓ | `inline` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 847 | `cmdTransferRootOwner` | `UpdateOne` | `tenant_memberships` | `_id` | CRITICAL | ✓ | `inline` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 862 | `cmdTransferRootOwner` | `InsertOne` | `system_logs` | `action`, `category`, `createdAt`, `message`, `metadata`, `severity`, `tenantId`, `userId` | OK |  | `struct-var:logEntry:SystemLog` | Filter contains tenantId. |
| 885 | `cmdVersion` | `FindOne` | `system_config` | — | MEDIUM |  | `inline` | Collection 'system_config' is in the exempt (global) list; tenant filtering is not strictly required, but queries sho... |
| 931 | `cmdStatus` | `FindOne` | `system_config` | — | MEDIUM |  | `inline` | Collection 'system_config' is in the exempt (global) list; tenant filtering is not strictly required, but queries sho... |
| 946 | `cmdStatus` | `CountDocuments` | `users` | — | MEDIUM |  | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 950 | `cmdStatus` | `CountDocuments` | `tenants` | — | MEDIUM |  | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |


### `cmd/server/main.go`

| Line | Function | Operation | Collection | Filter fields | Risk | Safe key | Filter source | Note |
|------|----------|-----------|------------|---------------|------|----------|---------------|------|
| 801 | `main` | `FindOne` | `branding_config` | — | HIGH |  | `inline` | Read operation with an empty filter — returns ALL documents. HIGH: cross-tenant data leakage risk. |


### `internal/api/handlers/admin.go`

| Line | Function | Operation | Collection | Filter fields | Risk | Safe key | Filter source | Note |
|------|----------|-----------|------------|---------------|------|----------|---------------|------|
| 51 | `isRootTenantOwner` | `CountDocuments` | `tenant_memberships` | `userId`, `role` | HIGH |  | `inline` | Read operation on a tenant-scoped collection without tenantId in the filter. HIGH: cross-tenant data leakage risk. |
| 64 | `isRootTenantOwner` | `FindOne` | `tenant_memberships` | `userId`, `role` | HIGH |  | `inline` | Read operation on a tenant-scoped collection without tenantId in the filter. HIGH: cross-tenant data leakage risk. |
| 68 | `isRootTenantOwner` | `FindOne` | `tenants` | `_id` | MEDIUM | ✓ | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 176 | `ListTenants` | `CountDocuments` | `tenants` | `$or`, `billingStatus`, `isActive` | MEDIUM |  | `variable:filter` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 187 | `ListTenants` | `Find` | `tenants` | `$or`, `billingStatus`, `isActive` | MEDIUM |  | `variable:filter` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 211 | `ListTenants` | `Aggregate` | `tenant_memberships` | `tenantId` | OK |  | `variable-pipeline:pipeline` | Filter contains tenantId. |
| 228 | `ListTenants` | `Find` | `plans` | — | MEDIUM |  | `inline` | Collection 'plans' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 312 | `ExportTenantsCSV` | `Find` | `tenants` | `$or`, `billingStatus`, `isActive` | MEDIUM |  | `variable:filter` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 336 | `ExportTenantsCSV` | `Aggregate` | `tenant_memberships` | `tenantId` | OK |  | `variable-pipeline:pipeline` | Filter contains tenantId. |
| 353 | `ExportTenantsCSV` | `Find` | `plans` | — | MEDIUM |  | `inline` | Collection 'plans' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 418 | `GetTenant` | `FindOne` | `tenants` | `_id` | MEDIUM | ✓ | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 424 | `GetTenant` | `Find` | `tenant_memberships` | `tenantId` | OK |  | `inline` | Filter contains tenantId. |
| 441 | `GetTenant` | `Find` | `users` | `_id` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 483 | `UpdateTenantStatus` | `FindOne` | `tenants` | `_id` | MEDIUM | ✓ | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 502 | `UpdateTenantStatus` | `UpdateOne` | `tenants` | `_id` | MEDIUM | ✓ | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 581 | `ListUsers` | `CountDocuments` | `users` | `$or`, `isActive` | MEDIUM |  | `variable:filter` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 592 | `ListUsers` | `Find` | `users` | `$or`, `isActive` | MEDIUM |  | `variable:filter` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 616 | `ListUsers` | `Aggregate` | `tenant_memberships` | `userId` | HIGH |  | `variable-pipeline:pipeline` | Read operation on a tenant-scoped collection without tenantId in the filter. HIGH: cross-tenant data leakage risk. |
| 678 | `ExportUsersCSV` | `Find` | `users` | `$or`, `isActive` | MEDIUM |  | `variable:filter` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 702 | `ExportUsersCSV` | `Aggregate` | `tenant_memberships` | `userId` | HIGH |  | `variable-pipeline:pipeline` | Read operation on a tenant-scoped collection without tenantId in the filter. HIGH: cross-tenant data leakage risk. |
| 774 | `UpdateUserStatus` | `UpdateOne` | `users` | `_id` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 817 | `GetDashboard` | `CountDocuments` | `users` | — | MEDIUM |  | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 822 | `GetDashboard` | `CountDocuments` | `tenants` | — | MEDIUM |  | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 943 | `GetUser` | `FindOne` | `users` | `_id` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 948 | `GetUser` | `Find` | `tenant_memberships` | `userId` | HIGH |  | `inline` | Read operation on a tenant-scoped collection without tenantId in the filter. HIGH: cross-tenant data leakage risk. |
| 963 | `GetUser` | `Find` | `plans` | — | MEDIUM |  | `inline` | Collection 'plans' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 992 | `GetUser` | `Find` | `tenants` | `_id` | MEDIUM | ✓ | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 1079 | `UpdateUser` | `FindOne` | `users` | `_id` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 1098 | `UpdateUser` | `CountDocuments` | `users` | `email`, `_id` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 1121 | `UpdateUser` | `UpdateOne` | `users` | `_id` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 1165 | `UpdateUserRole` | `FindOne` | `tenants` | `_id` | MEDIUM | ✓ | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 1182 | `UpdateUserRole` | `FindOne` | `tenant_memberships` | `tenantId`, `role` | OK |  | `inline` | Filter contains tenantId. |
| 1186 | `UpdateUserRole` | `UpdateOne` | `tenant_memberships` | `_id` | CRITICAL | ✓ | `inline` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 1193 | `UpdateUserRole` | `UpdateOne` | `tenant_memberships` | `userId`, `tenantId` | OK |  | `inline` | Filter contains tenantId. |
| 1243 | `PreflightDeleteUser` | `Find` | `tenant_memberships` | `userId`, `role` | HIGH |  | `inline` | Read operation on a tenant-scoped collection without tenantId in the filter. HIGH: cross-tenant data leakage risk. |
| 1264 | `PreflightDeleteUser` | `Find` | `tenants` | `_id` | MEDIUM | ✓ | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 1280 | `PreflightDeleteUser` | `Find` | `tenant_memberships` | `tenantId`, `userId` | OK |  | `inline` | Filter contains tenantId. |
| 1301 | `PreflightDeleteUser` | `Find` | `users` | `_id` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 1358 | `DeleteUser` | `FindOne` | `users` | `_id` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 1378 | `DeleteUser` | `Find` | `tenant_memberships` | `userId` | HIGH |  | `inline` | Read operation on a tenant-scoped collection without tenantId in the filter. HIGH: cross-tenant data leakage risk. |
| 1398 | `DeleteUser` | `FindOne` | `tenants` | `_id` | MEDIUM | ✓ | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 1414 | `DeleteUser` | `UpdateOne` | `tenant_memberships` | `userId`, `tenantId` | OK |  | `inline` | Filter contains tenantId. |
| 1430 | `DeleteUser` | `CountDocuments` | `tenant_memberships` | `tenantId`, `userId` | OK |  | `inline` | Filter contains tenantId. |
| 1454 | `DeleteUser` | `DeleteMany` | `tenant_memberships` | `tenantId` | OK |  | `inline` | Filter contains tenantId. |
| 1457 | `DeleteUser` | `DeleteOne` | `tenants` | `_id` | MEDIUM | ✓ | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 1460 | `DeleteUser` | `DeleteMany` | `invitations` | `tenantId` | OK |  | `inline` | Filter contains tenantId. |
| 1479 | `DeleteUser` | `DeleteMany` | `tenant_memberships` | `userId` | CRITICAL |  | `inline` | DeleteMany on a tenant-scoped collection without tenantId in the filter. CRITICAL: this can modify/delete data belong... |
| 1482 | `DeleteUser` | `DeleteMany` | `refresh_tokens` | `userId` | CRITICAL |  | `inline` | DeleteMany on a tenant-scoped collection without tenantId in the filter. CRITICAL: this can modify/delete data belong... |
| 1485 | `DeleteUser` | `DeleteMany` | `messages` | `userId` | CRITICAL |  | `inline` | DeleteMany on a tenant-scoped collection without tenantId in the filter. CRITICAL: this can modify/delete data belong... |
| 1488 | `DeleteUser` | `DeleteOne` | `users` | `_id` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 1529 | `UpdateTenant` | `FindOne` | `tenants` | `_id` | MEDIUM | ✓ | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 1587 | `UpdateTenant` | `UpdateOne` | `tenants` | `_id` | MEDIUM | ✓ | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 1619 | `ImpersonateUser` | `FindOne` | `users` | `_id` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 1626 | `ImpersonateUser` | `FindOne` | `tenants` | `isRoot` | MEDIUM |  | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 1628 | `ImpersonateUser` | `FindOne` | `tenant_memberships` | `userId`, `tenantId`, `role` | OK |  | `inline` | Filter contains tenantId. |
| 1656 | `ImpersonateUser` | `InsertOne` | `impersonation_logs` | `adminId`, `adminEmail`, `targetId`, `targetEmail`, `ipAddress`, `startedAt`, `expiresAt` | CRITICAL |  | `inline-document` | InsertOne inserts a document with no tenantId field. CRITICAL: the inserted document will be orphaned — readable/modi... |
| 1667 | `ImpersonateUser` | `Find` | `tenant_memberships` | `userId` | HIGH |  | `inline` | Read operation on a tenant-scoped collection without tenantId in the filter. HIGH: cross-tenant data leakage risk. |
| 1680 | `ImpersonateUser` | `FindOne` | `tenants` | `_id` | MEDIUM | ✓ | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 1703 | `getRootTenant` | `FindOne` | `tenants` | `isRoot` | MEDIUM |  | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 1719 | `ListRootMembers` | `Find` | `tenant_memberships` | `tenantId` | OK |  | `inline` | Filter contains tenantId. |
| 1739 | `ListRootMembers` | `Find` | `users` | `_id` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 1770 | `ListRootMembers` | `Find` | `invitations` | `tenantId`, `status`, `expiresAt` | OK |  | `inline` | Filter contains tenantId. |
| 1837 | `InviteRootMember` | `FindOne` | `users` | `email` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 1838 | `InviteRootMember` | `CountDocuments` | `tenant_memberships` | `userId`, `tenantId` | OK |  | `inline` | Filter contains tenantId. |
| 1853 | `InviteRootMember` | `CountDocuments` | `invitations` | `tenantId`, `email`, `status`, `expiresAt` | OK | ✓ | `inline` | Filter contains tenantId. |
| 1885 | `InviteRootMember` | `InsertOne` | `invitations` | `createdAt`, `email`, `expiresAt`, `invitedBy`, `role`, `status`, `tenantId`, `token` | OK | ✓ | `struct-var:invitation:Invitation` | Filter contains tenantId. |
| 1946 | `RemoveRootMember` | `FindOne` | `tenant_memberships` | `userId`, `tenantId` | OK |  | `inline` | Filter contains tenantId. |
| 1964 | `RemoveRootMember` | `DeleteOne` | `tenant_memberships` | `_id` | CRITICAL | ✓ | `inline` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 2032 | `ChangeRootMemberRole` | `UpdateOne` | `tenant_memberships` | `userId`, `tenantId` | OK |  | `inline` | Filter contains tenantId. |
| 2074 | `CancelRootInvitation` | `DeleteOne` | `invitations` | `_id`, `tenantId`, `status` | OK | ✓ | `inline` | Filter contains tenantId. |


### `internal/api/handlers/announcements.go`

| Line | Function | Operation | Collection | Filter fields | Risk | Safe key | Filter source | Note |
|------|----------|-----------|------------|---------------|------|----------|---------------|------|
| 33 | `ListPublic` | `Find` | `announcements` | `isPublished` | HIGH |  | `inline` | Read operation on a tenant-scoped collection without tenantId in the filter. HIGH: cross-tenant data leakage risk. |
| 54 | `ListAll` | `Find` | `announcements` | — | HIGH |  | `inline` | Read operation with an empty filter — returns ALL documents. HIGH: cross-tenant data leakage risk. |
| 105 | `Create` | `InsertOne` | `announcements` | `body`, `createdAt`, `isPublished`, `publishedAt`, `title`, `updatedAt` | CRITICAL |  | `struct-var:ann:Announcement` | InsertOne with ann (a Announcement struct); the struct definition does NOT declare a tenantId bson field. CRITICAL: i... |
| 152 | `Update` | `UpdateOne` | `announcements` | `_id` | CRITICAL | ✓ | `inline` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 168 | `Delete` | `DeleteOne` | `announcements` | `_id` | CRITICAL | ✓ | `inline` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |


### `internal/api/handlers/apikeys.go`

| Line | Function | Operation | Collection | Filter fields | Risk | Safe key | Filter source | Note |
|------|----------|-----------|------------|---------------|------|----------|---------------|------|
| 45 | `ListAPIKeys` | `Find` | `api_keys` | `isActive` | HIGH |  | `inline` | Read operation on a tenant-scoped collection without tenantId in the filter. HIGH: cross-tenant data leakage risk. |
| 60 | `ListAPIKeys` | `CountDocuments` | `api_keys` | `isActive` | HIGH |  | `inline` | Read operation on a tenant-scoped collection without tenantId in the filter. HIGH: cross-tenant data leakage risk. |
| 127 | `CreateAPIKey` | `InsertOne` | `api_keys` | `authority`, `createdAt`, `createdBy`, `isActive`, `keyHash`, `keyPreview`, `lastUsedAt`, `name` | CRITICAL | ✓ | `struct-var:apiKey:APIKey` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 166 | `DeleteAPIKey` | `UpdateByID` | `api_keys` | `_id` | CRITICAL | ✓ | `by-id` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |


### `internal/api/handlers/auth.go`

| Line | Function | Operation | Collection | Filter fields | Risk | Safe key | Filter source | Note |
|------|----------|-----------|------------|---------------|------|----------|---------------|------|
| 223 | `Register` | `FindOne` | `users` | `email` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 252 | `Register` | `InsertOne` | `users` | `accountLockedUntil`, `authMethods`, `createdAt`, `displayName`, `email`, `emailVerified`, `failedLoginAttempts`, `githubId`, `googleId`, `isActive`, `lastLoginAt`, `lastVerificationSent`, `microsoftId`, `onboardingCompletedAt`, `passwordHash`, `recoveryCodes`, `themePreference`, `totpEnabled`, `totpSecret`, `totpVerifiedAt`, `trialUsedAt`, `updatedAt` | MEDIUM | ✓ | `struct-var:user:User` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 330 | `Login` | `FindOne` | `users` | `email` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 359 | `Login` | `FindOneAndUpdate` | `users` | `_id`, `accountLockedUntil` | MEDIUM | ✓ | `variable:filter` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 367 | `Login` | `UpdateOne` | `users` | `_id` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 387 | `Login` | `UpdateOne` | `users` | `_id` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 453 | `Logout` | `InsertOne` | `revoked_tokens` | `createdAt`, `expiresAt`, `tokenHash` | CRITICAL | ✓ | `struct:RevokedToken` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 470 | `Logout` | `UpdateMany` | `refresh_tokens` | `tokenHash`, `userId` | CRITICAL | ✓ | `inline` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 503 | `Refresh` | `FindOne` | `refresh_tokens` | `tokenHash` | HIGH | ✓ | `inline` | Read operation without tenantId, but the filter contains a globally-unique key — likely safe, manual review recommended. |
| 514 | `Refresh` | `UpdateMany` | `refresh_tokens` | `familyId` | CRITICAL | ✓ | `inline` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 525 | `Refresh` | `UpdateOne` | `refresh_tokens` | `_id` | CRITICAL | ✓ | `inline` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 537 | `Refresh` | `FindOne` | `users` | `_id`, `isActive` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 555 | `Refresh` | `UpdateOne` | `refresh_tokens` | `tokenHash` | CRITICAL | ✓ | `inline` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 601 | `VerifyEmail` | `FindOneAndUpdate` | `verification_tokens` | `token`, `type`, `usedAt`, `expiresAt` | CRITICAL | ✓ | `inline` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 616 | `VerifyEmail` | `UpdateOne` | `users` | `_id` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 651 | `ResendVerification` | `FindOne` | `users` | `email` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 691 | `ForgotPassword` | `FindOne` | `users` | `email` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 696 | `ForgotPassword` | `UpdateMany` | `verification_tokens` | `userId`, `type`, `usedAt` | CRITICAL |  | `inline` | UpdateMany on a tenant-scoped collection without tenantId in the filter. CRITICAL: this can modify/delete data belong... |
| 711 | `ForgotPassword` | `InsertOne` | `verification_tokens` | `createdAt`, `expiresAt`, `token`, `type`, `usedAt`, `userId` | CRITICAL | ✓ | `struct-var:verification:VerificationToken` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 746 | `ResetPassword` | `FindOneAndUpdate` | `verification_tokens` | `token`, `type`, `usedAt`, `expiresAt` | CRITICAL | ✓ | `inline` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 767 | `ResetPassword` | `UpdateOne` | `users` | `_id` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 777 | `ResetPassword` | `UpdateMany` | `refresh_tokens` | `userId`, `isRevoked` | CRITICAL |  | `inline` | UpdateMany on a tenant-scoped collection without tenantId in the filter. CRITICAL: this can modify/delete data belong... |
| 837 | `ChangePassword` | `UpdateOne` | `users` | `_id` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 844 | `ChangePassword` | `UpdateMany` | `refresh_tokens` | `userId`, `isRevoked` | CRITICAL |  | `inline` | UpdateMany on a tenant-scoped collection without tenantId in the filter. CRITICAL: this can modify/delete data belong... |
| 889 | `MFASetup` | `UpdateOne` | `users` | `_id` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 920 | `MFAVerifySetup` | `FindOne` | `users` | `_id` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 944 | `MFAVerifySetup` | `UpdateOne` | `users` | `_id` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 981 | `MFADisable` | `FindOne` | `users` | `_id` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 1001 | `MFADisable` | `UpdateOne` | `users` | `_id` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 1051 | `MFAChallenge` | `FindOne` | `users` | `_id` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 1071 | `MFAChallenge` | `UpdateOne` | `users` | `_id` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 1127 | `MFARegenerateRecoveryCodes` | `FindOne` | `users` | `_id` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 1148 | `MFARegenerateRecoveryCodes` | `UpdateOne` | `users` | `_id` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 1190 | `MagicLinkRequest` | `FindOne` | `users` | `email` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 1204 | `MagicLinkRequest` | `InsertOne` | `verification_tokens` | `createdAt`, `expiresAt`, `token`, `type`, `usedAt`, `userId` | CRITICAL | ✓ | `struct-var:verification:VerificationToken` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 1236 | `MagicLinkVerify` | `FindOneAndUpdate` | `verification_tokens` | `token`, `type`, `usedAt`, `expiresAt` | CRITICAL | ✓ | `inline` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 1252 | `MagicLinkVerify` | `FindOne` | `users` | `_id`, `isActive` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 1258 | `MagicLinkVerify` | `UpdateOne` | `users` | `_id` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 1315 | `createAuthCodeRedirect` | `InsertOne` | `auth_codes` | `code`, `createdAt`, `expiresAt`, `tokenData`, `usedAt`, `userId` | CRITICAL | ✓ | `struct-var:authCode:AuthCode` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 1336 | `ExchangeCode` | `FindOneAndUpdate` | `auth_codes` | `code`, `usedAt`, `expiresAt` | CRITICAL | ✓ | `inline` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 1374 | `GoogleOAuth` | `InsertOne` | `oauth_states` | `createdAt`, `expiresAt`, `state` | CRITICAL |  | `struct-var:oauthState:OAuthState` | InsertOne with oauthState (a OAuthState struct); the struct definition does NOT declare a tenantId bson field. CRITIC... |
| 1398 | `GoogleOAuthCallback` | `FindOneAndDelete` | `oauth_states` | `state`, `expiresAt` | CRITICAL |  | `inline` | FindOneAndDelete on a tenant-scoped collection without tenantId in the filter. CRITICAL: this can modify/delete data ... |
| 1423 | `GoogleOAuthCallback` | `FindOne` | `users` | `googleId` | MEDIUM |  | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 1425 | `GoogleOAuthCallback` | `FindOne` | `users` | `email` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 1440 | `GoogleOAuthCallback` | `InsertOne` | `users` | `accountLockedUntil`, `authMethods`, `createdAt`, `displayName`, `email`, `emailVerified`, `failedLoginAttempts`, `githubId`, `googleId`, `isActive`, `lastLoginAt`, `lastVerificationSent`, `microsoftId`, `onboardingCompletedAt`, `passwordHash`, `recoveryCodes`, `themePreference`, `totpEnabled`, `totpSecret`, `totpVerifiedAt`, `trialUsedAt`, `updatedAt` | MEDIUM | ✓ | `struct-var:user:User` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 1448 | `GoogleOAuthCallback` | `UpdateOne` | `users` | `_id` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 1454 | `GoogleOAuthCallback` | `UpdateOne` | `users` | `_id` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 1507 | `GitHubOAuth` | `InsertOne` | `oauth_states` | `createdAt`, `expiresAt`, `state` | CRITICAL |  | `struct-var:oauthState:OAuthState` | InsertOne with oauthState (a OAuthState struct); the struct definition does NOT declare a tenantId bson field. CRITIC... |
| 1531 | `GitHubOAuthCallback` | `FindOneAndDelete` | `oauth_states` | `state`, `expiresAt` | CRITICAL |  | `inline` | FindOneAndDelete on a tenant-scoped collection without tenantId in the filter. CRITICAL: this can modify/delete data ... |
| 1557 | `GitHubOAuthCallback` | `FindOne` | `users` | `githubId` | MEDIUM |  | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 1559 | `GitHubOAuthCallback` | `FindOne` | `users` | `email` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 1578 | `GitHubOAuthCallback` | `InsertOne` | `users` | `accountLockedUntil`, `authMethods`, `createdAt`, `displayName`, `email`, `emailVerified`, `failedLoginAttempts`, `githubId`, `googleId`, `isActive`, `lastLoginAt`, `lastVerificationSent`, `microsoftId`, `onboardingCompletedAt`, `passwordHash`, `recoveryCodes`, `themePreference`, `totpEnabled`, `totpSecret`, `totpVerifiedAt`, `trialUsedAt`, `updatedAt` | MEDIUM | ✓ | `struct-var:user:User` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 1591 | `GitHubOAuthCallback` | `UpdateOne` | `users` | `_id` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 1597 | `GitHubOAuthCallback` | `UpdateOne` | `users` | `_id` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 1649 | `MicrosoftOAuth` | `InsertOne` | `oauth_states` | `createdAt`, `expiresAt`, `state` | CRITICAL |  | `struct-var:oauthState:OAuthState` | InsertOne with oauthState (a OAuthState struct); the struct definition does NOT declare a tenantId bson field. CRITIC... |
| 1673 | `MicrosoftOAuthCallback` | `FindOneAndDelete` | `oauth_states` | `state`, `expiresAt` | CRITICAL |  | `inline` | FindOneAndDelete on a tenant-scoped collection without tenantId in the filter. CRITICAL: this can modify/delete data ... |
| 1704 | `MicrosoftOAuthCallback` | `FindOne` | `users` | `microsoftId` | MEDIUM |  | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 1706 | `MicrosoftOAuthCallback` | `FindOne` | `users` | `email` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 1725 | `MicrosoftOAuthCallback` | `InsertOne` | `users` | `accountLockedUntil`, `authMethods`, `createdAt`, `displayName`, `email`, `emailVerified`, `failedLoginAttempts`, `githubId`, `googleId`, `isActive`, `lastLoginAt`, `lastVerificationSent`, `microsoftId`, `onboardingCompletedAt`, `passwordHash`, `recoveryCodes`, `themePreference`, `totpEnabled`, `totpSecret`, `totpVerifiedAt`, `trialUsedAt`, `updatedAt` | MEDIUM | ✓ | `struct-var:user:User` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 1738 | `MicrosoftOAuthCallback` | `UpdateOne` | `users` | `_id` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 1744 | `MicrosoftOAuthCallback` | `UpdateOne` | `users` | `_id` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 1790 | `ListSessions` | `Find` | `refresh_tokens` | `userId`, `isRevoked`, `expiresAt` | HIGH |  | `inline` | Read operation on a tenant-scoped collection without tenantId in the filter. HIGH: cross-tenant data leakage risk. |
| 1861 | `RevokeSession` | `UpdateOne` | `refresh_tokens` | `_id`, `userId` | CRITICAL | ✓ | `inline` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 1881 | `RevokeAllSessions` | `UpdateMany` | `refresh_tokens` | `userId`, `isRevoked` | CRITICAL |  | `inline` | UpdateMany on a tenant-scoped collection without tenantId in the filter. CRITICAL: this can modify/delete data belong... |
| 1922 | `UpdatePreferences` | `UpdateOne` | `users` | `_id` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 1937 | `CompleteOnboarding` | `UpdateOne` | `users` | `_id` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 1991 | `createPersonalTenant` | `InsertOne` | `tenants` | `billingInterval`, `billingStatus`, `billingWaived`, `canceledAt`, `createdAt`, `currentPeriodEnd`, `isActive`, `isRoot`, `name`, `planId`, `purchasedCredits`, `seatQuantity`, `slug`, `stripeCustomerId`, `stripeSubscriptionId`, `subscriptionCredits`, `trialUsedAt`, `updatedAt` | MEDIUM | ✓ | `struct-var:tenant:Tenant` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 2004 | `createPersonalTenant` | `InsertOne` | `tenant_memberships` | `joinedAt`, `role`, `tenantId`, `updatedAt`, `userId` | OK |  | `struct-var:membership:TenantMembership` | Filter contains tenantId. |
| 2026 | `sendVerificationEmail` | `InsertOne` | `verification_tokens` | `createdAt`, `expiresAt`, `token`, `type`, `usedAt`, `userId` | CRITICAL | ✓ | `struct-var:verification:VerificationToken` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 2029 | `sendVerificationEmail` | `UpdateOne` | `users` | `_id` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 2048 | `getUserMemberships` | `Find` | `tenant_memberships` | `userId` | HIGH |  | `inline` | Read operation on a tenant-scoped collection without tenantId in the filter. HIGH: cross-tenant data leakage risk. |
| 2062 | `getUserMemberships` | `FindOne` | `tenants` | `_id` | MEDIUM | ✓ | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 2082 | `acceptInvitationForUser` | `FindOne` | `invitations` | `token`, `status`, `expiresAt` | HIGH | ✓ | `inline` | Read operation without tenantId, but the filter contains a globally-unique key — likely safe, manual review recommended. |
| 2093 | `acceptInvitationForUser` | `FindOne` | `users` | `_id` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 2101 | `acceptInvitationForUser` | `FindOneAndUpdate` | `invitations` | `_id`, `status` | CRITICAL | ✓ | `inline` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 2113 | `acceptInvitationForUser` | `CountDocuments` | `tenant_memberships` | `userId`, `tenantId` | OK |  | `inline` | Filter contains tenantId. |
| 2129 | `acceptInvitationForUser` | `InsertOne` | `tenant_memberships` | `joinedAt`, `role`, `tenantId`, `updatedAt`, `userId` | OK |  | `struct-var:membership:TenantMembership` | Filter contains tenantId. |
| 2135 | `acceptInvitationForUser` | `UpdateOne` | `users` | `_id` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 2166 | `storeRefreshToken` | `CountDocuments` | `refresh_tokens` | `userId`, `isRevoked`, `expiresAt` | HIGH |  | `inline` | Read operation on a tenant-scoped collection without tenantId in the filter. HIGH: cross-tenant data leakage risk. |
| 2174 | `storeRefreshToken` | `Find` | `refresh_tokens` | `userId`, `isRevoked`, `expiresAt` | HIGH |  | `inline` | Read operation on a tenant-scoped collection without tenantId in the filter. HIGH: cross-tenant data leakage risk. |
| 2183 | `storeRefreshToken` | `UpdateByID` | `refresh_tokens` | `_id` | CRITICAL | ✓ | `by-id` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 2204 | `storeRefreshToken` | `InsertOne` | `refresh_tokens` | `createdAt`, `deviceInfo`, `expiresAt`, `familyId`, `ipAddress`, `isRevoked`, `lastActiveAt`, `tokenHash`, `userAgent`, `userId` | CRITICAL | ✓ | `struct-var:rt:RefreshToken` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 2241 | `DeleteAccount` | `Find` | `tenant_memberships` | `userId` | HIGH |  | `inline` | Read operation on a tenant-scoped collection without tenantId in the filter. HIGH: cross-tenant data leakage risk. |
| 2261 | `DeleteAccount` | `FindOne` | `tenants` | `_id` | MEDIUM | ✓ | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 2270 | `DeleteAccount` | `CountDocuments` | `tenant_memberships` | `tenantId`, `userId` | OK |  | `inline` | Filter contains tenantId. |
| 2280 | `DeleteAccount` | `DeleteMany` | `tenant_memberships` | `tenantId` | OK |  | `inline` | Filter contains tenantId. |
| 2283 | `DeleteAccount` | `DeleteOne` | `tenants` | `_id` | MEDIUM | ✓ | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 2286 | `DeleteAccount` | `DeleteMany` | `invitations` | `tenantId` | OK |  | `inline` | Filter contains tenantId. |
| 2302 | `DeleteAccount` | `DeleteMany` | `tenant_memberships` | `userId` | CRITICAL |  | `inline` | DeleteMany on a tenant-scoped collection without tenantId in the filter. CRITICAL: this can modify/delete data belong... |
| 2305 | `DeleteAccount` | `DeleteMany` | `refresh_tokens` | `userId` | CRITICAL |  | `inline` | DeleteMany on a tenant-scoped collection without tenantId in the filter. CRITICAL: this can modify/delete data belong... |
| 2308 | `DeleteAccount` | `DeleteMany` | `messages` | `userId` | CRITICAL |  | `inline` | DeleteMany on a tenant-scoped collection without tenantId in the filter. CRITICAL: this can modify/delete data belong... |
| 2311 | `DeleteAccount` | `DeleteOne` | `users` | `_id` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 2341 | `ExportData` | `Find` | `tenant_memberships` | `userId` | HIGH |  | `inline` | Read operation on a tenant-scoped collection without tenantId in the filter. HIGH: cross-tenant data leakage risk. |
| 2363 | `ExportData` | `Find` | `messages` | `userId` | HIGH |  | `inline` | Read operation on a tenant-scoped collection without tenantId in the filter. HIGH: cross-tenant data leakage risk. |


### `internal/api/handlers/billing.go`

| Line | Function | Operation | Collection | Filter fields | Risk | Safe key | Filter source | Note |
|------|----------|-----------|------------|---------------|------|----------|---------------|------|
| 94 | `Checkout` | `FindOne` | `plans` | `_id` | MEDIUM | ✓ | `inline` | Collection 'plans' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 122 | `Checkout` | `UpdateOne` | `tenants` | `_id` | MEDIUM | ✓ | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 138 | `Checkout` | `CountDocuments` | `tenant_memberships` | `tenantId` | OK |  | `inline` | Filter contains tenantId. |
| 152 | `Checkout` | `UpdateOne` | `tenants` | `_id` | MEDIUM | ✓ | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 162 | `Checkout` | `CountDocuments` | `tenant_memberships` | `tenantId` | OK |  | `inline` | Filter contains tenantId. |
| 313 | `Checkout` | `FindOne` | `credit_bundles` | `_id`, `isActive` | HIGH | ✓ | `inline` | Read operation without tenantId, but the filter contains a globally-unique key — likely safe, manual review recommended. |
| 403 | `ListTransactions` | `CountDocuments` | `financial_transactions` | `tenantId` | OK |  | `variable:filter` | Filter contains tenantId. |
| 414 | `ListTransactions` | `Find` | `financial_transactions` | `tenantId` | OK |  | `variable:filter` | Filter contains tenantId. |
| 454 | `GetInvoice` | `FindOne` | `financial_transactions` | `_id`, `tenantId` | OK | ✓ | `inline` | Filter contains tenantId. |
| 483 | `GetInvoicePDF` | `FindOne` | `financial_transactions` | `_id`, `tenantId` | OK | ✓ | `inline` | Filter contains tenantId. |
| 654 | `CancelSubscription` | `UpdateOne` | `tenants` | `_id` | MEDIUM | ✓ | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 733 | `AdminListTransactions` | `CountDocuments` | `financial_transactions` | `$or`, `tenantId` | OK |  | `variable:filter` | Filter contains tenantId. |
| 744 | `AdminListTransactions` | `Find` | `financial_transactions` | `$or`, `tenantId` | OK |  | `variable:filter` | Filter contains tenantId. |
| 801 | `AdminGetMetrics` | `Find` | `daily_metrics` | `date` | HIGH |  | `variable:filter` | Read operation on a tenant-scoped collection without tenantId in the filter. HIGH: cross-tenant data leakage risk. |
| 893 | `computeLiveRevenue` | `Aggregate` | `financial_transactions` | `createdAt` | HIGH |  | `variable-pipeline:pipeline` | Read operation on a tenant-scoped collection without tenantId in the filter. HIGH: cross-tenant data leakage risk. |
| 929 | `computeLiveARR` | `Aggregate` | `tenants` | `billingStatus`, `planId` | MEDIUM |  | `variable-pipeline:pipeline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 955 | `AdminCancelSubscription` | `FindOne` | `tenants` | `_id` | MEDIUM | ✓ | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 1001 | `AdminCancelSubscription` | `UpdateOne` | `tenants` | `_id` | MEDIUM | ✓ | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 1034 | `AdminUpdateSubscription` | `UpdateOne` | `tenants` | `_id` | MEDIUM | ✓ | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |


### `internal/api/handlers/bootstrap.go`

| Line | Function | Operation | Collection | Filter fields | Risk | Safe key | Filter source | Note |
|------|----------|-----------|------------|---------------|------|----------|---------------|------|
| 36 | `refreshInitialized` | `FindOne` | `system_config` | — | MEDIUM |  | `inline` | Collection 'system_config' is in the exempt (global) list; tenant filtering is not strictly required, but queries sho... |
| 66 | `refreshInitializedFromContext` | `FindOne` | `system_config` | — | MEDIUM |  | `inline` | Collection 'system_config' is in the exempt (global) list; tenant filtering is not strictly required, but queries sho... |


### `internal/api/handlers/branding.go`

| Line | Function | Operation | Collection | Filter fields | Risk | Safe key | Filter source | Note |
|------|----------|-----------|------------|---------------|------|----------|---------------|------|
| 45 | `GetBranding` | `FindOne` | `branding_config` | — | HIGH |  | `inline` | Read operation with an empty filter — returns ALL documents. HIGH: cross-tenant data leakage risk. |
| 60 | `GetBranding` | `FindOne` | `branding_assets` | `key` | HIGH |  | `inline` | Read operation on a tenant-scoped collection without tenantId in the filter. HIGH: cross-tenant data leakage risk. |
| 64 | `GetBranding` | `FindOne` | `branding_assets` | `key` | HIGH |  | `inline` | Read operation on a tenant-scoped collection without tenantId in the filter. HIGH: cross-tenant data leakage risk. |
| 119 | `ServeAsset` | `FindOne` | `branding_assets` | `key` | HIGH |  | `inline` | Read operation on a tenant-scoped collection without tenantId in the filter. HIGH: cross-tenant data leakage risk. |
| 141 | `ServeMedia` | `FindOne` | `branding_assets` | `key` | HIGH |  | `inline` | Read operation on a tenant-scoped collection without tenantId in the filter. HIGH: cross-tenant data leakage risk. |
| 163 | `GetPublicPage` | `FindOne` | `custom_pages` | `slug`, `isPublished` | HIGH | ✓ | `inline` | Read operation without tenantId, but the filter contains a globally-unique key — likely safe, manual review recommended. |
| 182 | `ListPublicPages` | `Find` | `custom_pages` | `isPublished` | HIGH |  | `inline` | Read operation on a tenant-scoped collection without tenantId in the filter. HIGH: cross-tenant data leakage risk. |
| 262 | `UpdateBranding` | `UpdateOne` | `branding_config` | — | CRITICAL |  | `inline` | UpdateOne with an empty filter — affects ALL documents. CRITICAL: cross-tenant data corruption risk. |
| 324 | `UploadAsset` | `UpdateOne` | `branding_assets` | `key` | CRITICAL |  | `inline` | UpdateOne on a tenant-scoped collection without tenantId in the filter. CRITICAL: this can modify/delete data belongi... |
| 348 | `DeleteAsset` | `DeleteOne` | `branding_assets` | `key` | CRITICAL |  | `inline` | DeleteOne on a tenant-scoped collection without tenantId in the filter. CRITICAL: this can modify/delete data belongi... |
| 368 | `ListMedia` | `Find` | `branding_assets` | `key` | HIGH |  | `variable:filter` | Read operation on a tenant-scoped collection without tenantId in the filter. HIGH: cross-tenant data leakage risk. |
| 460 | `UploadMedia` | `InsertOne` | `branding_assets` | `contentType`, `createdAt`, `data`, `filename`, `key`, `size` | CRITICAL |  | `struct-var:asset:BrandingAsset` | InsertOne with asset (a BrandingAsset struct); the struct definition does NOT declare a tenantId bson field. CRITICAL... |
| 487 | `DeleteMedia` | `DeleteOne` | `branding_assets` | `key` | CRITICAL |  | `inline` | DeleteOne on a tenant-scoped collection without tenantId in the filter. CRITICAL: this can modify/delete data belongi... |
| 505 | `AdminListPages` | `Find` | `custom_pages` | — | HIGH |  | `inline` | Read operation with an empty filter — returns ALL documents. HIGH: cross-tenant data leakage risk. |
| 543 | `CreatePage` | `InsertOne` | `custom_pages` | — | CRITICAL |  | `struct:unknown` | InsertOne with an unrecognised struct value; could not statically verify tenantId presence. Manual review required. |
| 590 | `UpdatePage` | `UpdateByID` | `custom_pages` | `_id` | CRITICAL | ✓ | `by-id` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 616 | `DeletePage` | `DeleteOne` | `custom_pages` | `_id` | CRITICAL | ✓ | `inline` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |


### `internal/api/handlers/bundles.go`

| Line | Function | Operation | Collection | Filter fields | Risk | Safe key | Filter source | Note |
|------|----------|-----------|------------|---------------|------|----------|---------------|------|
| 60 | `ListBundles` | `Find` | `credit_bundles` | — | HIGH |  | `inline` | Read operation with an empty filter — returns ALL documents. HIGH: cross-tenant data leakage risk. |
| 75 | `ListBundles` | `CountDocuments` | `credit_bundles` | — | HIGH |  | `inline` | Read operation with an empty filter — returns ALL documents. HIGH: cross-tenant data leakage risk. |
| 96 | `CreateBundle` | `CountDocuments` | `credit_bundles` | `name` | HIGH | ✓ | `inline` | Read operation without tenantId, but the filter contains a globally-unique key — likely safe, manual review recommended. |
| 117 | `CreateBundle` | `InsertOne` | `credit_bundles` | `createdAt`, `credits`, `isActive`, `name`, `priceCents`, `sortOrder`, `updatedAt` | CRITICAL | ✓ | `struct-var:bundle:CreditBundle` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 145 | `UpdateBundle` | `FindOne` | `credit_bundles` | `_id` | HIGH | ✓ | `inline` | Read operation without tenantId, but the filter contains a globally-unique key — likely safe, manual review recommended. |
| 166 | `UpdateBundle` | `CountDocuments` | `credit_bundles` | `name`, `_id` | HIGH | ✓ | `inline` | Read operation without tenantId, but the filter contains a globally-unique key — likely safe, manual review recommended. |
| 186 | `UpdateBundle` | `UpdateByID` | `credit_bundles` | `_id` | CRITICAL | ✓ | `by-id` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 196 | `UpdateBundle` | `FindOne` | `credit_bundles` | `_id` | HIGH | ✓ | `inline` | Read operation without tenantId, but the filter contains a globally-unique key — likely safe, manual review recommended. |
| 212 | `DeleteBundle` | `FindOne` | `credit_bundles` | `_id` | HIGH | ✓ | `inline` | Read operation without tenantId, but the filter contains a globally-unique key — likely safe, manual review recommended. |
| 221 | `DeleteBundle` | `DeleteOne` | `credit_bundles` | `_id` | CRITICAL | ✓ | `inline` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 236 | `ListBundlesPublic` | `Find` | `credit_bundles` | `isActive` | HIGH |  | `inline` | Read operation on a tenant-scoped collection without tenantId in the filter. HIGH: cross-tenant data leakage risk. |


### `internal/api/handlers/config.go`

| Line | Function | Operation | Collection | Filter fields | Risk | Safe key | Filter source | Note |
|------|----------|-----------|------------|---------------|------|----------|---------------|------|
| 94 | `UpdateConfig` | `UpdateOne` | `config_vars` | `name` | CRITICAL | ✓ | `inline` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 162 | `CreateConfig` | `InsertOne` | `config_vars` | `createdAt`, `description`, `isSystem`, `name`, `options`, `type`, `updatedAt`, `value` | CRITICAL | ✓ | `struct-var:v:ConfigVar` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 192 | `DeleteConfig` | `DeleteOne` | `config_vars` | `name` | CRITICAL | ✓ | `inline` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |


### `internal/api/handlers/event_definitions.go`

| Line | Function | Operation | Collection | Filter fields | Risk | Safe key | Filter source | Note |
|------|----------|-----------|------------|---------------|------|----------|---------------|------|
| 50 | `ListEventDefinitions` | `Find` | `event_definitions` | — | HIGH |  | `inline` | Read operation with an empty filter — returns ALL documents. HIGH: cross-tenant data leakage risk. |
| 85 | `ListEventDefinitions` | `Aggregate` | `telemetry_events` | — | HIGH |  | `variable-pipeline:pipeline` | Read operation with an empty filter — returns ALL documents. HIGH: cross-tenant data leakage risk. |
| 135 | `CreateEventDefinition` | `CountDocuments` | `event_definitions` | `name` | HIGH | ✓ | `inline` | Read operation without tenantId, but the filter contains a globally-unique key — likely safe, manual review recommended. |
| 161 | `CreateEventDefinition` | `CountDocuments` | `event_definitions` | `_id` | HIGH | ✓ | `inline` | Read operation without tenantId, but the filter contains a globally-unique key — likely safe, manual review recommended. |
| 173 | `CreateEventDefinition` | `InsertOne` | `event_definitions` | `createdAt`, `description`, `name`, `parentId`, `updatedAt` | CRITICAL | ✓ | `struct-var:def:EventDefinition` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 212 | `UpdateEventDefinition` | `FindOne` | `event_definitions` | `_id` | HIGH | ✓ | `inline` | Read operation without tenantId, but the filter contains a globally-unique key — likely safe, manual review recommended. |
| 219 | `UpdateEventDefinition` | `CountDocuments` | `event_definitions` | `name`, `_id` | HIGH | ✓ | `inline` | Read operation without tenantId, but the filter contains a globally-unique key — likely safe, manual review recommended. |
| 249 | `UpdateEventDefinition` | `CountDocuments` | `event_definitions` | `_id` | HIGH | ✓ | `inline` | Read operation without tenantId, but the filter contains a globally-unique key — likely safe, manual review recommended. |
| 269 | `UpdateEventDefinition` | `UpdateOne` | `event_definitions` | `_id` | CRITICAL | ✓ | `inline` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 278 | `UpdateEventDefinition` | `FindOne` | `event_definitions` | `_id` | HIGH | ✓ | `inline` | Read operation without tenantId, but the filter contains a globally-unique key — likely safe, manual review recommended. |
| 296 | `DeleteEventDefinition` | `FindOne` | `event_definitions` | `_id` | HIGH | ✓ | `inline` | Read operation without tenantId, but the filter contains a globally-unique key — likely safe, manual review recommended. |
| 302 | `DeleteEventDefinition` | `UpdateMany` | `event_definitions` | `parentId` | CRITICAL |  | `inline` | UpdateMany on a tenant-scoped collection without tenantId in the filter. CRITICAL: this can modify/delete data belong... |
| 307 | `DeleteEventDefinition` | `DeleteOne` | `event_definitions` | `_id` | CRITICAL | ✓ | `inline` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 321 | `GetSankeyData` | `Find` | `event_definitions` | — | HIGH |  | `inline` | Read operation with an empty filter — returns ALL documents. HIGH: cross-tenant data leakage risk. |
| 399 | `GetSankeyData` | `Aggregate` | `telemetry_events` | — | HIGH |  | `variable-pipeline:pipeline` | Read operation with an empty filter — returns ALL documents. HIGH: cross-tenant data leakage risk. |
| 463 | `wouldCreateCycle` | `FindOne` | `event_definitions` | `_id` | HIGH | ✓ | `inline` | Read operation without tenantId, but the filter contains a globally-unique key — likely safe, manual review recommended. |


### `internal/api/handlers/logs.go`

| Line | Function | Operation | Collection | Filter fields | Risk | Safe key | Filter source | Note |
|------|----------|-----------|------------|---------------|------|----------|---------------|------|
| 111 | `ListLogs` | `EstimatedDocumentCount` | `system_logs` | — | MEDIUM |  | `no-filter` | Collection 'system_logs' is in the exempt (global) list; tenant filtering is not strictly required, but queries shoul... |
| 113 | `ListLogs` | `CountDocuments` | `system_logs` | — | MEDIUM |  | `variable:unknown:filter` | Collection 'system_logs' is in the exempt (global) list; tenant filtering is not strictly required, but queries shoul... |
| 125 | `ListLogs` | `Find` | `system_logs` | — | MEDIUM |  | `variable:unknown:filter` | Collection 'system_logs' is in the exempt (global) list; tenant filtering is not strictly required, but queries shoul... |
| 156 | `SeverityCounts` | `Aggregate` | `system_logs` | — | MEDIUM |  | `variable-pipeline:pipeline` | Collection 'system_logs' is in the exempt (global) list; tenant filtering is not strictly required, but queries shoul... |
| 196 | `ExportCSV` | `Find` | `system_logs` | — | MEDIUM |  | `variable:unknown:filter` | Collection 'system_logs' is in the exempt (global) list; tenant filtering is not strictly required, but queries shoul... |


### `internal/api/handlers/messages.go`

| Line | Function | Operation | Collection | Filter fields | Risk | Safe key | Filter source | Note |
|------|----------|-----------|------------|---------------|------|----------|---------------|------|
| 36 | `ListMessages` | `Find` | `messages` | `userId` | HIGH |  | `inline` | Read operation on a tenant-scoped collection without tenantId in the filter. HIGH: cross-tenant data leakage risk. |
| 64 | `UnreadCount` | `CountDocuments` | `messages` | `userId`, `read` | HIGH |  | `inline` | Read operation on a tenant-scoped collection without tenantId in the filter. HIGH: cross-tenant data leakage risk. |
| 88 | `MarkRead` | `UpdateOne` | `messages` | `_id`, `userId` | CRITICAL | ✓ | `inline` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |


### `internal/api/handlers/plans.go`

| Line | Function | Operation | Collection | Filter fields | Risk | Safe key | Filter source | Note |
|------|----------|-----------|------------|---------------|------|----------|---------------|------|
| 48 | `ListPlans` | `Find` | `plans` | — | MEDIUM |  | `inline` | Collection 'plans' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 66 | `ListPlans` | `Aggregate` | `tenants` | — | MEDIUM |  | `inline-pipeline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 93 | `ListPlans` | `CountDocuments` | `plans` | — | MEDIUM |  | `inline` | Collection 'plans' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 110 | `GetPlan` | `FindOne` | `plans` | `_id` | MEDIUM | ✓ | `inline` | Collection 'plans' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 123 | `ListEntitlementKeys` | `Find` | `plans` | — | MEDIUM |  | `inline` | Collection 'plans' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 253 | `CreatePlan` | `CountDocuments` | `plans` | `name` | MEDIUM | ✓ | `inline` | Collection 'plans' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 295 | `CreatePlan` | `InsertOne` | `plans` | `annualDiscountPct`, `bonusCredits`, `createdAt`, `creditResetPolicy`, `description`, `entitlements`, `includedSeats`, `isArchived`, `isSystem`, `maxSeats`, `minSeats`, `monthlyPriceCents`, `name`, `perSeatPriceCents`, `pricingModel`, `trialDays`, `updatedAt`, `usageCreditsPerMonth`, `userLimit` | MEDIUM | ✓ | `struct-var:plan:Plan` | Collection 'plans' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 323 | `UpdatePlan` | `FindOne` | `plans` | `_id` | MEDIUM | ✓ | `inline` | Collection 'plans' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 350 | `UpdatePlan` | `CountDocuments` | `plans` | `name`, `_id` | MEDIUM | ✓ | `inline` | Collection 'plans' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 368 | `UpdatePlan` | `DeleteMany` | `stripe_mappings` | `entityType` | CRITICAL |  | `inline` | DeleteMany on a tenant-scoped collection without tenantId in the filter. CRITICAL: this can modify/delete data belong... |
| 393 | `UpdatePlan` | `UpdateByID` | `plans` | `_id` | MEDIUM | ✓ | `by-id` | Collection 'plans' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 404 | `UpdatePlan` | `FindOne` | `plans` | `_id` | MEDIUM | ✓ | `inline` | Collection 'plans' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 408 | `UpdatePlan` | `CountDocuments` | `tenants` | `planId` | MEDIUM |  | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 446 | `DeletePlan` | `FindOne` | `plans` | `_id` | MEDIUM | ✓ | `inline` | Collection 'plans' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 460 | `DeletePlan` | `CountDocuments` | `tenants` | `planId` | MEDIUM |  | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 470 | `DeletePlan` | `DeleteOne` | `plans` | `_id` | MEDIUM | ✓ | `inline` | Collection 'plans' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 491 | `ArchivePlan` | `FindOne` | `plans` | `_id` | MEDIUM | ✓ | `inline` | Collection 'plans' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 505 | `ArchivePlan` | `UpdateByID` | `plans` | `_id` | MEDIUM | ✓ | `by-id` | Collection 'plans' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 526 | `UnarchivePlan` | `FindOne` | `plans` | `_id` | MEDIUM | ✓ | `inline` | Collection 'plans' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 540 | `UnarchivePlan` | `UpdateByID` | `plans` | `_id` | MEDIUM | ✓ | `by-id` | Collection 'plans' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 576 | `AssignPlan` | `FindOne` | `tenants` | `_id` | MEDIUM | ✓ | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 598 | `AssignPlan` | `FindOne` | `plans` | `_id` | MEDIUM | ✓ | `inline` | Collection 'plans' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 627 | `AssignPlan` | `FindOne` | `plans` | `_id` | MEDIUM | ✓ | `inline` | Collection 'plans' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 671 | `AssignPlan` | `UpdateByID` | `tenants` | `_id` | MEDIUM | ✓ | `by-id` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 703 | `ListPlansPublic` | `FindOne` | `tenants` | `_id` | MEDIUM | ✓ | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 714 | `ListPlansPublic` | `CountDocuments` | `tenant_memberships` | `userId`, `tenantId` | OK |  | `inline` | Filter contains tenantId. |
| 737 | `ListPlansPublic` | `Find` | `plans` | `isArchived` | MEDIUM |  | `variable:filter` | Collection 'plans' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 817 | `lookupPlanForTenant` | `FindOne` | `plans` | `_id` | MEDIUM | ✓ | `inline` | Collection 'plans' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 820 | `lookupPlanForTenant` | `FindOne` | `plans` | `isSystem` | MEDIUM |  | `inline` | Collection 'plans' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |


### `internal/api/handlers/promotions.go`

| Line | Function | Operation | Collection | Filter fields | Risk | Safe key | Filter source | Note |
|------|----------|-----------|------------|---------------|------|----------|---------------|------|
| 115 | `buildProductNameMap` | `Find` | `stripe_mappings` | — | HIGH |  | `inline` | Read operation with an empty filter — returns ALL documents. HIGH: cross-tenant data leakage risk. |
| 146 | `buildProductNameMap` | `Find` | `plans` | `_id` | MEDIUM | ✓ | `inline` | Collection 'plans' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 166 | `buildProductNameMap` | `Find` | `credit_bundles` | `_id` | HIGH | ✓ | `inline` | Read operation without tenantId, but the filter contains a globally-unique key — likely safe, manual review recommended. |
| 200 | `ListEligibleProducts` | `Find` | `plans` | `isArchived` | MEDIUM |  | `inline` | Collection 'plans' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 226 | `ListEligibleProducts` | `Find` | `credit_bundles` | `isActive` | HIGH |  | `inline` | Read operation on a tenant-scoped collection without tenantId in the filter. HIGH: cross-tenant data leakage risk. |
| 380 | `resolveStripeProducts` | `FindOne` | `plans` | `_id` | MEDIUM | ✓ | `inline` | Collection 'plans' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 418 | `resolveStripeProducts` | `FindOne` | `stripe_mappings` | `entityType`, `entityId` | HIGH |  | `inline` | Read operation on a tenant-scoped collection without tenantId in the filter. HIGH: cross-tenant data leakage risk. |
| 428 | `resolveStripeProducts` | `FindOne` | `credit_bundles` | `_id` | HIGH | ✓ | `inline` | Read operation without tenantId, but the filter contains a globally-unique key — likely safe, manual review recommended. |
| 438 | `resolveStripeProducts` | `FindOne` | `stripe_mappings` | `entityType`, `entityId` | HIGH |  | `inline` | Read operation on a tenant-scoped collection without tenantId in the filter. HIGH: cross-tenant data leakage risk. |


### `internal/api/handlers/tenant.go`

| Line | Function | Operation | Collection | Filter fields | Risk | Safe key | Filter source | Note |
|------|----------|-----------|------------|---------------|------|----------|---------------|------|
| 74 | `ListMembers` | `Find` | `tenant_memberships` | `tenantId` | OK |  | `inline` | Filter contains tenantId. |
| 94 | `ListMembers` | `Find` | `users` | `_id` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 171 | `InviteMember` | `FindOne` | `users` | `email` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 172 | `InviteMember` | `CountDocuments` | `tenant_memberships` | `userId`, `tenantId` | OK |  | `inline` | Filter contains tenantId. |
| 187 | `InviteMember` | `CountDocuments` | `invitations` | `tenantId`, `email`, `status`, `expiresAt` | OK | ✓ | `inline` | Filter contains tenantId. |
| 205 | `InviteMember` | `FindOne` | `plans` | `_id` | MEDIUM | ✓ | `inline` | Collection 'plans' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 209 | `InviteMember` | `FindOne` | `plans` | `isSystem` | MEDIUM |  | `inline` | Collection 'plans' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 231 | `InviteMember` | `InsertOne` | `invitations` | `createdAt`, `email`, `expiresAt`, `invitedBy`, `role`, `status`, `tenantId`, `token` | OK | ✓ | `struct-var:invitation:Invitation` | Filter contains tenantId. |
| 236 | `InviteMember` | `CountDocuments` | `tenant_memberships` | `tenantId` | OK |  | `inline` | Filter contains tenantId. |
| 241 | `InviteMember` | `CountDocuments` | `invitations` | `tenantId`, `status`, `expiresAt` | OK |  | `inline` | Filter contains tenantId. |
| 252 | `InviteMember` | `DeleteOne` | `invitations` | `_id` | CRITICAL | ✓ | `inline` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 263 | `InviteMember` | `InsertOne` | `invitations` | `createdAt`, `email`, `expiresAt`, `invitedBy`, `role`, `status`, `tenantId`, `token` | OK | ✓ | `struct-var:invitation:Invitation` | Filter contains tenantId. |
| 271 | `InviteMember` | `CountDocuments` | `tenant_memberships` | `tenantId` | OK |  | `inline` | Filter contains tenantId. |
| 283 | `InviteMember` | `UpdateOne` | `tenants` | `_id` | MEDIUM | ✓ | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 344 | `RemoveMember` | `FindOne` | `tenant_memberships` | `userId`, `tenantId` | OK |  | `inline` | Filter contains tenantId. |
| 364 | `RemoveMember` | `DeleteOne` | `tenant_memberships` | `_id` | CRITICAL | ✓ | `inline` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 372 | `RemoveMember` | `FindOne` | `plans` | `_id` | MEDIUM | ✓ | `inline` | Collection 'plans' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 373 | `RemoveMember` | `CountDocuments` | `tenant_memberships` | `tenantId` | OK |  | `inline` | Filter contains tenantId. |
| 388 | `RemoveMember` | `UpdateOne` | `tenants` | `_id` | MEDIUM | ✓ | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 456 | `ChangeRole` | `UpdateOne` | `tenant_memberships` | `userId`, `tenantId` | OK |  | `inline` | Filter contains tenantId. |
| 508 | `TransferOwnership` | `CountDocuments` | `tenant_memberships` | `userId`, `tenantId` | OK |  | `inline` | Filter contains tenantId. |
| 524 | `TransferOwnership` | `UpdateOne` | `tenant_memberships` | `userId`, `tenantId` | OK |  | `inline` | Filter contains tenantId. |
| 534 | `TransferOwnership` | `UpdateOne` | `tenant_memberships` | `userId`, `tenantId` | OK |  | `inline` | Filter contains tenantId. |
| 593 | `GetActivity` | `Find` | `system_logs` | `action`, `message`, `tenantId` | OK |  | `variable:filter` | Filter contains tenantId. |
| 606 | `GetActivity` | `CountDocuments` | `system_logs` | `action`, `message`, `tenantId` | OK |  | `variable:filter` | Filter contains tenantId. |
| 642 | `UpdateTenantSettings` | `UpdateOne` | `tenants` | `_id` | MEDIUM | ✓ | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |


### `internal/api/handlers/usage.go`

| Line | Function | Operation | Collection | Filter fields | Risk | Safe key | Filter source | Note |
|------|----------|-----------|------------|---------------|------|----------|---------------|------|
| 90 | `RecordUsage` | `UpdateOne` | `tenants` | `_id`, `subscriptionCredits` | MEDIUM | ✓ | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 100 | `RecordUsage` | `UpdateOne` | `tenants` | `_id`, `purchasedCredits` | MEDIUM | ✓ | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 114 | `RecordUsage` | `InsertOne` | `usage_events` | `createdAt`, `metadata`, `quantity`, `tenantId`, `type`, `userId` | OK |  | `struct-var:event:UsageEvent` | Filter contains tenantId. |
| 169 | `GetSummary` | `Aggregate` | `usage_events` | `createdAt`, `tenantId` | OK |  | `variable-pipeline:pipeline` | Filter contains tenantId. |
| 196 | `GetSummary` | `FindOne` | `tenants` | `_id` | MEDIUM | ✓ | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |


### `internal/api/handlers/webhook.go`

| Line | Function | Operation | Collection | Filter fields | Risk | Safe key | Filter source | Note |
|------|----------|-----------|------------|---------------|------|----------|---------------|------|
| 71 | `HandleWebhook` | `FindOneAndUpdate` | `webhook_events` | `eventId` | CRITICAL | ✓ | `inline` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 132 | `HandleWebhook` | `DeleteOne` | `webhook_events` | `eventId` | CRITICAL | ✓ | `inline` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 138 | `HandleWebhook` | `UpdateOne` | `webhook_events` | `eventId` | CRITICAL | ✓ | `inline` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 170 | `handleCheckoutCompleted` | `FindOne` | `tenants` | `_id` | MEDIUM | ✓ | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 182 | `handleCheckoutCompleted` | `FindOne` | `tenants` | `stripeCustomerId`, `_id` | MEDIUM | ✓ | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 205 | `handleCheckoutCompleted` | `FindOne` | `plans` | `_id` | MEDIUM | ✓ | `inline` | Collection 'plans' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 239 | `handleCheckoutCompleted` | `UpdateOne` | `users` | `_id` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 255 | `handleCheckoutCompleted` | `UpdateOne` | `tenants` | `_id` | MEDIUM | ✓ | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 322 | `handleCheckoutCompleted` | `FindOne` | `credit_bundles` | `_id` | HIGH | ✓ | `inline` | Read operation without tenantId, but the filter contains a globally-unique key — likely safe, manual review recommended. |
| 328 | `handleCheckoutCompleted` | `UpdateOne` | `tenants` | `_id` | MEDIUM | ✓ | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 391 | `handleInvoicePaid` | `FindOne` | `tenants` | `stripeSubscriptionId` | MEDIUM |  | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 397 | `handleInvoicePaid` | `UpdateOne` | `tenants` | `_id` | MEDIUM | ✓ | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 407 | `handleInvoicePaid` | `FindOne` | `plans` | `_id` | MEDIUM | ✓ | `inline` | Collection 'plans' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 409 | `handleInvoicePaid` | `UpdateOne` | `tenants` | `_id` | MEDIUM | ✓ | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 415 | `handleInvoicePaid` | `UpdateOne` | `tenants` | `_id` | MEDIUM | ✓ | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 436 | `handleInvoicePaid` | `FindOne` | `tenant_memberships` | `tenantId`, `role` | OK |  | `inline` | Filter contains tenantId. |
| 443 | `handleInvoicePaid` | `FindOne` | `plans` | `_id` | MEDIUM | ✓ | `inline` | Collection 'plans' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 482 | `handleInvoicePaymentFailed` | `FindOne` | `tenants` | `stripeSubscriptionId` | MEDIUM |  | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 488 | `handleInvoicePaymentFailed` | `UpdateOne` | `tenants` | `_id` | MEDIUM | ✓ | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 497 | `handleInvoicePaymentFailed` | `Find` | `tenant_memberships` | `tenantId` | OK |  | `inline` | Filter contains tenantId. |
| 519 | `handleInvoicePaymentFailed` | `InsertOne` | `messages` | `body`, `createdAt`, `isSystem`, `read`, `subject`, `userId` | CRITICAL |  | `struct:Message` | InsertOne with a Message struct value; tenantId presence inferred from the struct definition — verify the value is ac... |
| 551 | `handleSubscriptionUpdated` | `FindOne` | `tenants` | `stripeSubscriptionId` | MEDIUM |  | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 583 | `handleSubscriptionUpdated` | `FindOne` | `plans` | `_id` | MEDIUM | ✓ | `inline` | Collection 'plans' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 598 | `handleSubscriptionUpdated` | `UpdateOne` | `tenants` | `_id` | MEDIUM | ✓ | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 613 | `handleSubscriptionDeleted` | `FindOne` | `tenants` | `stripeSubscriptionId` | MEDIUM |  | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 619 | `handleSubscriptionDeleted` | `FindOne` | `plans` | `isSystem` | MEDIUM |  | `inline` | Collection 'plans' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 635 | `handleSubscriptionDeleted` | `UpdateOne` | `tenants` | `_id` | MEDIUM | ✓ | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 675 | `handleChargeRefunded` | `FindOne` | `tenants` | `stripeCustomerId` | MEDIUM |  | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 688 | `handleChargeRefunded` | `FindOne` | `tenant_memberships` | `tenantId`, `role` | OK |  | `inline` | Filter contains tenantId. |
| 726 | `handleDisputeCreated` | `FindOne` | `tenants` | `stripeCustomerId` | MEDIUM |  | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 732 | `handleDisputeCreated` | `UpdateOne` | `tenants` | `_id` | MEDIUM | ✓ | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 771 | `handleDisputeClosed` | `FindOne` | `tenants` | `stripeCustomerId` | MEDIUM |  | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 779 | `handleDisputeClosed` | `UpdateOne` | `tenants` | `_id` | MEDIUM | ✓ | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 841 | `recordTransaction` | `InsertOne` | `financial_transactions` | `amountCents`, `billingInterval`, `bundleId`, `bundleName`, `createdAt`, `currency`, `description`, `invoiceNumber`, `planId`, `planName`, `stripeInvoiceId`, `stripeSessionId`, `stripeSubscriptionId`, `subtotalCents`, `taxAmountCents`, `tenantId`, `type`, `userId` | OK | ✓ | `struct-var:tx:FinancialTransaction` | Filter contains tenantId. |


### `internal/api/handlers/webhooks.go`

| Line | Function | Operation | Collection | Filter fields | Risk | Safe key | Filter source | Note |
|------|----------|-----------|------------|---------------|------|----------|---------------|------|
| 45 | `ListWebhooks` | `Find` | `webhooks` | `isActive` | HIGH |  | `inline` | Read operation on a tenant-scoped collection without tenantId in the filter. HIGH: cross-tenant data leakage risk. |
| 71 | `ListWebhooks` | `CountDocuments` | `webhook_deliveries` | `webhookId`, `createdAt` | HIGH |  | `inline` | Read operation on a tenant-scoped collection without tenantId in the filter. HIGH: cross-tenant data leakage risk. |
| 83 | `ListWebhooks` | `FindOne` | `webhook_deliveries` | `webhookId` | HIGH |  | `inline` | Read operation on a tenant-scoped collection without tenantId in the filter. HIGH: cross-tenant data leakage risk. |
| 88 | `ListWebhooks` | `CountDocuments` | `webhooks` | `isActive` | HIGH |  | `inline` | Read operation on a tenant-scoped collection without tenantId in the filter. HIGH: cross-tenant data leakage risk. |
| 105 | `GetWebhook` | `FindOne` | `webhooks` | `_id`, `isActive` | HIGH | ✓ | `inline` | Read operation without tenantId, but the filter contains a globally-unique key — likely safe, manual review recommended. |
| 111 | `GetWebhook` | `Find` | `webhook_deliveries` | `webhookId` | HIGH |  | `inline` | Read operation on a tenant-scoped collection without tenantId in the filter. HIGH: cross-tenant data leakage risk. |
| 279 | `CreateWebhook` | `InsertOne` | `webhooks` | `createdAt`, `createdBy`, `description`, `events`, `isActive`, `name`, `secret`, `secretPreview`, `updatedAt`, `url` | CRITICAL | ✓ | `struct-var:hook:Webhook` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 320 | `UpdateWebhook` | `UpdateByID` | `webhooks` | `_id` | CRITICAL | ✓ | `by-id` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 340 | `UpdateWebhook` | `FindOne` | `webhooks` | `_id` | HIGH | ✓ | `inline` | Read operation without tenantId, but the filter contains a globally-unique key — likely safe, manual review recommended. |
| 356 | `DeleteWebhook` | `UpdateByID` | `webhooks` | `_id` | CRITICAL | ✓ | `by-id` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 393 | `RegenerateSecret` | `UpdateByID` | `webhooks` | `_id` | CRITICAL | ✓ | `by-id` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 421 | `TestWebhook` | `FindOne` | `webhooks` | `_id`, `isActive` | HIGH | ✓ | `inline` | Read operation without tenantId, but the filter contains a globally-unique key — likely safe, manual review recommended. |


### `internal/configstore/seed.go`

| Line | Function | Operation | Collection | Filter fields | Risk | Safe key | Filter source | Note |
|------|----------|-----------|------------|---------------|------|----------|---------------|------|
| 380 | `Seed` | `FindOne` | `config_vars` | `name` | HIGH | ✓ | `inline` | Read operation without tenantId, but the filter contains a globally-unique key — likely safe, manual review recommended. |
| 384 | `Seed` | `InsertOne` | `config_vars` | — | CRITICAL |  | `struct:unknown` | InsertOne with an unrecognised struct value; could not statically verify tenantId presence. Manual review required. |


### `internal/configstore/store.go`

| Line | Function | Operation | Collection | Filter fields | Risk | Safe key | Filter source | Note |
|------|----------|-----------|------------|---------------|------|----------|---------------|------|
| 34 | `Load` | `Find` | `config_vars` | — | HIGH |  | `inline` | Read operation with an empty filter — returns ALL documents. HIGH: cross-tenant data leakage risk. |
| 90 | `Set` | `UpdateOne` | `config_vars` | `name` | CRITICAL | ✓ | `inline` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 106 | `Reload` | `FindOne` | `config_vars` | `name` | HIGH | ✓ | `inline` | Read operation without tenantId, but the filter contains a globally-unique key — likely safe, manual review recommended. |


### `internal/health/health.go`

| Line | Function | Operation | Collection | Filter fields | Risk | Safe key | Filter source | Note |
|------|----------|-----------|------------|---------------|------|----------|---------------|------|
| 138 | `registerNode` | `UpdateOne` | `system_nodes` | `machineId` | CRITICAL | ✓ | `inline` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 165 | `heartbeat` | `UpdateOne` | `system_nodes` | `machineId` | CRITICAL | ✓ | `inline` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 300 | `collectAndStore` | `InsertOne` | `system_metrics` | `cpu`, `disk`, `goRuntime`, `http`, `integrations`, `memory`, `mongo`, `network`, `nodeId`, `timestamp` | CRITICAL |  | `struct-var:metric:SystemMetric` | InsertOne with metric (a SystemMetric struct); the struct definition does NOT declare a tenantId bson field. CRITICAL... |


### `internal/health/query.go`

| Line | Function | Operation | Collection | Filter fields | Risk | Safe key | Filter source | Note |
|------|----------|-----------|------------|---------------|------|----------|---------------|------|
| 28 | `ListNodes` | `UpdateMany` | `system_nodes` | `lastSeen` | CRITICAL |  | `inline` | UpdateMany on a tenant-scoped collection without tenantId in the filter. CRITICAL: this can modify/delete data belong... |
| 35 | `ListNodes` | `Find` | `system_nodes` | — | HIGH |  | `inline` | Read operation with an empty filter — returns ALL documents. HIGH: cross-tenant data leakage risk. |
| 55 | `GetMetrics` | `Find` | `system_metrics` | `nodeId`, `timestamp` | HIGH |  | `variable:filter` | Read operation on a tenant-scoped collection without tenantId in the filter. HIGH: cross-tenant data leakage risk. |
| 74 | `GetAggregateMetrics` | `Find` | `system_metrics` | `timestamp` | HIGH |  | `variable:filter` | Read operation on a tenant-scoped collection without tenantId in the filter. HIGH: cross-tenant data leakage risk. |
| 98 | `GetCurrentMetrics` | `FindOne` | `system_metrics` | `nodeId` | HIGH |  | `inline` | Read operation on a tenant-scoped collection without tenantId in the filter. HIGH: cross-tenant data leakage risk. |
| 120 | `GetIntegrationCounts24h` | `Aggregate` | `system_metrics` | — | HIGH |  | `variable-pipeline:pipeline` | Read operation with an empty filter — returns ALL documents. HIGH: cross-tenant data leakage risk. |


### `internal/metrics/metrics.go`

| Line | Function | Operation | Collection | Filter fields | Risk | Safe key | Filter source | Note |
|------|----------|-----------|------------|---------------|------|----------|---------------|------|
| 112 | `tryAcquireOrRenew` | `FindOneAndUpdate` | `leader_locks` | `_id`, `expiresAt`, `holderId` | CRITICAL | ✓ | `variable:filter` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 148 | `isLeader` | `FindOne` | `leader_locks` | `_id` | HIGH | ✓ | `inline` | Read operation without tenantId, but the filter contains a globally-unique key — likely safe, manual review recommended. |
| 158 | `releaseLock` | `DeleteOne` | `leader_locks` | `_id`, `holderId` | CRITICAL | ✓ | `inline` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 192 | `collectDaily` | `Aggregate` | `users` | `lastLoginAt` | MEDIUM |  | `variable-pipeline:dauWauMauPipeline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 227 | `collectDaily` | `Aggregate` | `financial_transactions` | `createdAt` | HIGH |  | `variable-pipeline:revPipeline` | Read operation on a tenant-scoped collection without tenantId in the filter. HIGH: cross-tenant data leakage risk. |
| 263 | `collectDaily` | `Aggregate` | `tenants` | `billingStatus`, `planId` | MEDIUM |  | `variable-pipeline:arrPipeline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 280 | `collectDaily` | `UpdateOne` | `daily_metrics` | `date` | CRITICAL |  | `inline` | UpdateOne on a tenant-scoped collection without tenantId in the filter. CRITICAL: this can modify/delete data belongi... |


### `internal/middleware/auth.go`

| Line | Function | Operation | Collection | Filter fields | Risk | Safe key | Filter source | Note |
|------|----------|-----------|------------|---------------|------|----------|---------------|------|
| 90 | `authenticateJWT` | `FindOne` | `users` | `_id` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 113 | `authenticateAPIKey` | `FindOne` | `api_keys` | `keyHash`, `isActive` | HIGH | ✓ | `inline` | Read operation without tenantId, but the filter contains a globally-unique key — likely safe, manual review recommended. |
| 124 | `authenticateAPIKey` | `FindOne` | `users` | `_id` | MEDIUM | ✓ | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 135 | `authenticateAPIKey` | `FindOne` | `tenants` | `isRoot` | MEDIUM |  | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 155 | `authenticateAPIKey` | `UpdateByID` | `api_keys` | `_id` | CRITICAL | ✓ | `by-id` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 168 | `isTokenRevoked` | `CountDocuments` | `revoked_tokens` | `tokenHash` | HIGH | ✓ | `inline` | Read operation without tenantId, but the filter contains a globally-unique key — likely safe, manual review recommended. |


### `internal/middleware/ratelimit.go`

| Line | Function | Operation | Collection | Filter fields | Risk | Safe key | Filter source | Note |
|------|----------|-----------|------------|---------------|------|----------|---------------|------|
| 156 | `allowDistributed` | `FindOneAndUpdate` | `<unknown>` | `_id`, `windowEnd` | CRITICAL | ✓ | `inline` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 165 | `allowDistributed` | `FindOneAndUpdate` | `<unknown>` | `_id` | CRITICAL | ✓ | `inline` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |


### `internal/middleware/tenant.go`

| Line | Function | Operation | Collection | Filter fields | Risk | Safe key | Filter source | Note |
|------|----------|-----------|------------|---------------|------|----------|---------------|------|
| 51 | `RequireTenant` | `FindOne` | `tenants` | `_id`, `isActive` | MEDIUM | ✓ | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 64 | `RequireTenant` | `FindOne` | `tenant_memberships` | `userId`, `tenantId` | OK |  | `inline` | Filter contains tenantId. |
| 141 | `RequireEntitlement` | `FindOne` | `plans` | `_id` | MEDIUM | ✓ | `inline` | Collection 'plans' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |


### `internal/planstore/seed.go`

| Line | Function | Operation | Collection | Filter fields | Risk | Safe key | Filter source | Note |
|------|----------|-----------|------------|---------------|------|----------|---------------|------|
| 19 | `Seed` | `FindOne` | `plans` | `isSystem` | MEDIUM |  | `inline` | Collection 'plans' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 36 | `Seed` | `InsertOne` | `plans` | `annualDiscountPct`, `bonusCredits`, `createdAt`, `creditResetPolicy`, `description`, `entitlements`, `includedSeats`, `isArchived`, `isSystem`, `maxSeats`, `minSeats`, `monthlyPriceCents`, `name`, `perSeatPriceCents`, `pricingModel`, `trialDays`, `updatedAt`, `usageCreditsPerMonth`, `userLimit` | MEDIUM | ✓ | `struct-var:plan:Plan` | Collection 'plans' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |


### `internal/stripe/stripe.go`

| Line | Function | Operation | Collection | Filter fields | Risk | Safe key | Filter source | Note |
|------|----------|-----------|------------|---------------|------|----------|---------------|------|
| 82 | `GetOrCreateCustomer` | `UpdateOne` | `tenants` | `_id` | MEDIUM | ✓ | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 100 | `GetOrCreatePrice` | `FindOne` | `stripe_mappings` | `entityType`, `entityId` | HIGH |  | `inline` | Read operation on a tenant-scoped collection without tenantId in the filter. HIGH: cross-tenant data leakage risk. |
| 143 | `GetOrCreatePrice` | `InsertOne` | `stripe_mappings` | `createdAt`, `entityId`, `entityType`, `stripePriceId`, `stripeProductId` | CRITICAL |  | `struct:StripeMapping` | InsertOne with a StripeMapping struct value; tenantId presence inferred from the struct definition — verify the value... |
| 352 | `NextInvoiceNumber` | `FindOneAndUpdate` | `counters` | `_id` | CRITICAL | ✓ | `inline` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |


### `internal/syslog/syslog.go`

| Line | Function | Operation | Collection | Filter fields | Risk | Safe key | Filter source | Note |
|------|----------|-----------|------------|---------------|------|----------|---------------|------|
| 97 | `log` | `InsertOne` | `system_logs` | `action`, `category`, `createdAt`, `message`, `metadata`, `severity`, `tenantId`, `userId` | OK |  | `struct-var:entry:SystemLog` | Filter contains tenantId. |
| 114 | `log` | `InsertOne` | `system_logs` | `action`, `category`, `createdAt`, `message`, `metadata`, `severity`, `tenantId`, `userId` | OK |  | `struct-var:alert:SystemLog` | Filter contains tenantId. |
| 137 | `logCategorized` | `InsertOne` | `system_logs` | `action`, `category`, `createdAt`, `message`, `metadata`, `severity`, `tenantId`, `userId` | OK |  | `struct-var:entry:SystemLog` | Filter contains tenantId. |
| 154 | `logCategorized` | `InsertOne` | `system_logs` | `action`, `category`, `createdAt`, `message`, `metadata`, `severity`, `tenantId`, `userId` | OK |  | `struct-var:alert:SystemLog` | Filter contains tenantId. |
| 234 | `LogTenantActivity` | `InsertOne` | `system_logs` | `action`, `category`, `createdAt`, `message`, `metadata`, `severity`, `tenantId`, `userId` | OK |  | `struct-var:entry:SystemLog` | Filter contains tenantId. |


### `internal/telemetry/service.go`

| Line | Function | Operation | Collection | Filter fields | Risk | Safe key | Filter source | Note |
|------|----------|-----------|------------|---------------|------|----------|---------------|------|
| 82 | `flushLoop` | `InsertMany` | `telemetry_events` | — | CRITICAL |  | `inline-document-slice` | InsertMany inserts a document with no tenantId field. CRITICAL: the inserted document will be orphaned — readable/mod... |
| 188 | `TrackBatch` | `InsertMany` | `telemetry_events` | — | CRITICAL |  | `inline-document-slice` | InsertMany inserts a document with no tenantId field. CRITICAL: the inserted document will be orphaned — readable/mod... |
| 320 | `FunnelMetrics` | `CountDocuments` | `users` | `createdAt` | MEDIUM |  | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 338 | `FunnelMetrics` | `CountDocuments` | `telemetry_events` | `eventName`, `createdAt` | HIGH |  | `inline` | Read operation on a tenant-scoped collection without tenantId in the filter. HIGH: cross-tenant data leakage risk. |
| 347 | `FunnelMetrics` | `CountDocuments` | `financial_transactions` | `type`, `createdAt` | HIGH |  | `inline` | Read operation on a tenant-scoped collection without tenantId in the filter. HIGH: cross-tenant data leakage risk. |
| 356 | `FunnelMetrics` | `CountDocuments` | `telemetry_events` | — | HIGH |  | `variable:unknown:mergeBson(dateFilter, bson.M{
          ` | Read operation with an empty filter — returns ALL documents. HIGH: cross-tenant data leakage risk. |
| 447 | `RetentionCohorts` | `Aggregate` | `users` | — | MEDIUM |  | `variable-pipeline:pipeline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 531 | `EngagementMetrics` | `CountDocuments` | `telemetry_events` | `eventName`, `userId` | HIGH |  | `inline` | Read operation on a tenant-scoped collection without tenantId in the filter. HIGH: cross-tenant data leakage risk. |
| 596 | `computeKPIs` | `CountDocuments` | `tenants` | `billingStatus`, `isActive` | MEDIUM |  | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 605 | `computeKPIs` | `CountDocuments` | `users` | — | MEDIUM |  | `inline` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 621 | `computeKPIs` | `CountDocuments` | `tenants` | `canceledAt` | MEDIUM |  | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 627 | `computeKPIs` | `CountDocuments` | `tenants` | `billingStatus` | MEDIUM |  | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 640 | `computeKPIs` | `CountDocuments` | `tenants` | `trialUsedAt` | MEDIUM |  | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 646 | `computeKPIs` | `CountDocuments` | `tenants` | `trialUsedAt` | MEDIUM |  | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 703 | `CustomEventSummary` | `CountDocuments` | `telemetry_events` | `createdAt`, `eventName` | HIGH |  | `variable:filter` | Read operation on a tenant-scoped collection without tenantId in the filter. HIGH: cross-tenant data leakage risk. |
| 719 | `CustomEventSummary` | `Aggregate` | `telemetry_events` | — | HIGH |  | `variable-pipeline:pipeline` | Read operation with an empty filter — returns ALL documents. HIGH: cross-tenant data leakage risk. |
| 756 | `ListEventTypes` | `Aggregate` | `telemetry_events` | — | HIGH |  | `variable-pipeline:pipeline` | Read operation with an empty filter — returns ALL documents. HIGH: cross-tenant data leakage risk. |
| 795 | `countDistinct` | `Aggregate` | `telemetry_events` | — | HIGH |  | `variable-pipeline:pipeline` | Read operation with an empty filter — returns ALL documents. HIGH: cross-tenant data leakage risk. |
| 813 | `getActiveTenantIDs` | `Find` | `tenants` | `billingStatus`, `isActive` | MEDIUM |  | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 838 | `getUserIDsForTenants` | `Find` | `tenant_memberships` | `tenantId` | OK |  | `inline` | Filter contains tenantId. |
| 905 | `weeklyActiveUsers` | `Aggregate` | `telemetry_events` | — | HIGH |  | `variable-pipeline:pipeline` | Read operation with an empty filter — returns ALL documents. HIGH: cross-tenant data leakage risk. |
| 953 | `monthlyActiveUsers` | `Aggregate` | `telemetry_events` | — | HIGH |  | `variable-pipeline:pipeline` | Read operation with an empty filter — returns ALL documents. HIGH: cross-tenant data leakage risk. |
| 991 | `topCustomEvents` | `Aggregate` | `telemetry_events` | — | HIGH |  | `variable-pipeline:pipeline` | Read operation with an empty filter — returns ALL documents. HIGH: cross-tenant data leakage risk. |
| 1022 | `creditConsumptionTrend` | `Aggregate` | `usage_events` | — | HIGH |  | `variable-pipeline:pipeline` | Read operation with an empty filter — returns ALL documents. HIGH: cross-tenant data leakage risk. |
| 1098 | `calculateMRR` | `Aggregate` | `tenants` | — | MEDIUM |  | `variable-pipeline:pipeline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 1142 | `medianTimeToFirstPurchase` | `Aggregate` | `financial_transactions` | — | HIGH |  | `variable-pipeline:pipeline` | Read operation with an empty filter — returns ALL documents. HIGH: cross-tenant data leakage risk. |
| 1192 | `planDistribution` | `Aggregate` | `tenants` | — | MEDIUM |  | `variable-pipeline:pipeline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 1228 | `mrrTrend` | `Find` | `daily_metrics` | `date` | HIGH |  | `inline` | Read operation on a tenant-scoped collection without tenantId in the filter. HIGH: cross-tenant data leakage risk. |
| 1264 | `subscriberTrend` | `Aggregate` | `financial_transactions` | — | HIGH |  | `variable-pipeline:pipeline` | Read operation with an empty filter — returns ALL documents. HIGH: cross-tenant data leakage risk. |
| 1285 | `aggregateDailyPoints` | `Aggregate` | `telemetry_events` | — | HIGH |  | `variable-pipeline:unknown` | Read operation with an empty filter — returns ALL documents. HIGH: cross-tenant data leakage risk. |


### `internal/testutil/testutil.go`

| Line | Function | Operation | Collection | Filter fields | Risk | Safe key | Filter source | Note |
|------|----------|-----------|------------|---------------|------|----------|---------------|------|
| 98 | `MustConnectTestDB` | `DeleteMany` | `<unknown>` | — | CRITICAL |  | `inline` | DeleteMany with an empty filter — affects ALL documents. CRITICAL: cross-tenant data corruption risk. |
| 144 | `ConnectTestDB` | `DeleteMany` | `<unknown>` | — | CRITICAL |  | `inline` | DeleteMany with an empty filter — affects ALL documents. CRITICAL: cross-tenant data corruption risk. |
| 227 | `CleanupCollections` | `DeleteMany` | `<unknown>` | — | CRITICAL |  | `inline` | DeleteMany with an empty filter — affects ALL documents. CRITICAL: cross-tenant data corruption risk. |
| 270 | `CreateTestUser` | `InsertOne` | `users` | `accountLockedUntil`, `authMethods`, `createdAt`, `displayName`, `email`, `emailVerified`, `failedLoginAttempts`, `githubId`, `googleId`, `isActive`, `lastLoginAt`, `lastVerificationSent`, `microsoftId`, `onboardingCompletedAt`, `passwordHash`, `recoveryCodes`, `themePreference`, `totpEnabled`, `totpSecret`, `totpVerifiedAt`, `trialUsedAt`, `updatedAt` | MEDIUM | ✓ | `struct-var:user:User` | Collection 'users' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 292 | `CreateTestTenant` | `InsertOne` | `tenants` | `billingInterval`, `billingStatus`, `billingWaived`, `canceledAt`, `createdAt`, `currentPeriodEnd`, `isActive`, `isRoot`, `name`, `planId`, `purchasedCredits`, `seatQuantity`, `slug`, `stripeCustomerId`, `stripeSubscriptionId`, `subscriptionCredits`, `trialUsedAt`, `updatedAt` | MEDIUM | ✓ | `struct-var:tenant:Tenant` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 305 | `CreateTestTenant` | `InsertOne` | `tenant_memberships` | `joinedAt`, `role`, `tenantId`, `updatedAt`, `userId` | OK |  | `struct-var:membership:TenantMembership` | Filter contains tenantId. |
| 318 | `MarkSystemInitialized` | `InsertOne` | `system_config` | `initialized`, `initializedAt`, `initializedBy`, `version` | MEDIUM |  | `struct:SystemConfig` | Collection 'system_config' is in the exempt (global) list; tenant filtering is not strictly required, but queries sho... |
| 341 | `InsertTestLogs` | `InsertOne` | `system_logs` | `action`, `category`, `createdAt`, `message`, `metadata`, `severity`, `tenantId`, `userId` | OK |  | `struct-var:entry:SystemLog` | Filter contains tenantId. |
| 352 | `CountDocuments` | `CountDocuments` | `<unknown>` | — | HIGH |  | `variable:unknown:filter` | Read operation with an empty filter — returns ALL documents. HIGH: cross-tenant data leakage risk. |
| 392 | `CreateTestMembership` | `InsertOne` | `tenant_memberships` | `joinedAt`, `role`, `tenantId`, `updatedAt`, `userId` | OK |  | `struct-var:membership:TenantMembership` | Filter contains tenantId. |
| 416 | `CreateTestPlan` | `InsertOne` | `plans` | `annualDiscountPct`, `bonusCredits`, `createdAt`, `creditResetPolicy`, `description`, `entitlements`, `includedSeats`, `isArchived`, `isSystem`, `maxSeats`, `minSeats`, `monthlyPriceCents`, `name`, `perSeatPriceCents`, `pricingModel`, `trialDays`, `updatedAt`, `usageCreditsPerMonth`, `userLimit` | MEDIUM | ✓ | `struct-var:plan:Plan` | Collection 'plans' is in the exempt (global) list; tenant filtering is not strictly required, but queries should stil... |
| 438 | `CreateTestAPIKey` | `InsertOne` | `api_keys` | `authority`, `createdAt`, `createdBy`, `isActive`, `keyHash`, `keyPreview`, `lastUsedAt`, `name` | CRITICAL | ✓ | `struct-var:apiKey:APIKey` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 462 | `CreateTestWebhook` | `InsertOne` | `webhooks` | `createdAt`, `createdBy`, `description`, `events`, `isActive`, `name`, `secret`, `secretPreview`, `updatedAt`, `url` | CRITICAL | ✓ | `struct-var:webhook:Webhook` | Write operation on a tenant-scoped collection without tenantId in the filter, but the filter contains a globally-uniq... |
| 485 | `CreateTestInvitation` | `InsertOne` | `invitations` | `createdAt`, `email`, `expiresAt`, `invitedBy`, `role`, `status`, `tenantId`, `token` | OK | ✓ | `struct-var:invitation:Invitation` | Filter contains tenantId. |


### `internal/version/check.go`

| Line | Function | Operation | Collection | Filter fields | Risk | Safe key | Filter source | Note |
|------|----------|-----------|------------|---------------|------|----------|---------------|------|
| 28 | `CheckAndMigrate` | `FindOne` | `system_config` | — | MEDIUM |  | `inline` | Collection 'system_config' is in the exempt (global) list; tenant filtering is not strictly required, but queries sho... |
| 50 | `CheckAndMigrate` | `UpdateOne` | `system_config` | `_id` | MEDIUM | ✓ | `inline` | Collection 'system_config' is in the exempt (global) list; tenant filtering is not strictly required, but queries sho... |
| 65 | `sendUpgradeMessage` | `FindOne` | `tenants` | `isRoot` | MEDIUM |  | `inline` | Collection 'tenants' is in the exempt (global) list; tenant filtering is not strictly required, but queries should st... |
| 72 | `sendUpgradeMessage` | `FindOne` | `tenant_memberships` | `tenantId`, `role` | OK |  | `inline` | Filter contains tenantId. |
| 91 | `sendUpgradeMessage` | `InsertOne` | `messages` | `body`, `createdAt`, `isSystem`, `read`, `subject`, `userId` | CRITICAL |  | `struct-var:msg:Message` | InsertOne with msg (a Message struct); the struct definition does NOT declare a tenantId bson field. CRITICAL: insert... |


### `internal/webhooks/dispatcher.go`

| Line | Function | Operation | Collection | Filter fields | Risk | Safe key | Filter source | Note |
|------|----------|-----------|------------|---------------|------|----------|---------------|------|
| 194 | `dispatch` | `Find` | `webhooks` | `events`, `isActive` | HIGH |  | `inline` | Read operation on a tenant-scoped collection without tenantId in the filter. HIGH: cross-tenant data leakage risk. |
| 287 | `deliverWithRetry` | `InsertOne` | `webhook_deliveries` | `createdAt`, `durationMs`, `eventType`, `maxRetries`, `payload`, `responseBody`, `responseCode`, `retryCount`, `success`, `webhookId` | CRITICAL |  | `struct-var:delivery:WebhookDelivery` | InsertOne with delivery (a WebhookDelivery struct); the struct definition does NOT declare a tenantId bson field. CRI... |
| 421 | `DeliverTest` | `InsertOne` | `webhook_deliveries` | `createdAt`, `durationMs`, `eventType`, `maxRetries`, `payload`, `responseBody`, `responseCode`, `retryCount`, `success`, `webhookId` | CRITICAL |  | `struct-var:delivery:WebhookDelivery` | InsertOne with delivery (a WebhookDelivery struct); the struct definition does NOT declare a tenantId bson field. CRI... |


---
_Generated by `graphify_tenant_audit.py`._
