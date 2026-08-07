# MongoDB Query Map

Scanned **41** files, found **515** MongoDB queries across **34** collections.

Repo: `/home/z/my-project/repos/lastsaas/backend`

## Collections by Access Count

| Rank | Collection | Queries | Model | Model File | Files | Operations |
|------|------------|---------|-------|------------|-------|------------|
| 1 | `tenants` | 89 | Tenant | `internal/models/tenant.go` | 20 | FindOne×32, UpdateOne×23, CountDocuments×12, Find×7, DeleteOne×7, Aggregate×5, InsertOne×3 |
| 2 | `users` | 88 | User | `internal/models/user.go` | 12 | FindOne×34, UpdateOne×26, Find×8, CountDocuments×7, InsertOne×6, DeleteOne×5, Aggregate×2 |
| 3 | `tenant_memberships` | 68 | TenantMembership | `internal/models/membership.go` | 14 | Find×15, CountDocuments×14, FindOne×12, UpdateOne×10, Aggregate×5, InsertOne×5, DeleteMany×4, DeleteOne×3 |
| 4 | `plans` | 39 | Plan | `internal/models/plan.go` | 10 | FindOne×23, Find×9, CountDocuments×3, InsertOne×3, DeleteOne×1 |
| 5 | `financial_transactions` | 18 | FinancialTransaction | `internal/models/billing.go` | 6 | Aggregate×9, Find×3, CountDocuments×3, FindOne×2, InsertOne×1 |
| 6 | `refresh_tokens` | 18 | RefreshToken | `internal/models/tokens.go` | 4 | DeleteMany×5, UpdateMany×5, UpdateOne×3, Find×2, FindOne×1, CountDocuments×1, InsertOne×1 |
| 7 | `system_logs` | 16 | SystemLog | `internal/models/system_log.go` | 7 | InsertOne×7, Find×5, Aggregate×2, CountDocuments×2 |
| 8 | `credit_bundles` | 15 | CreditBundle | `internal/models/credit_bundle.go` | 4 | FindOne×6, Find×4, CountDocuments×3, InsertOne×1, DeleteOne×1 |
| 9 | `telemetry_events` | 15 | TelemetryEvent | `internal/models/telemetry.go` | 2 | Aggregate×9, CountDocuments×4, InsertMany×2 |
| 10 | `config_vars` | 14 | ConfigVar | `internal/models/config_var.go` | 4 | FindOne×5, UpdateOne×4, Find×2, InsertOne×2, DeleteOne×1 |
| 11 | `event_definitions` | 14 | EventDefinition | `internal/models/event_definition.go` | 1 | CountDocuments×4, FindOne×4, Find×2, InsertOne×1, UpdateOne×1, UpdateMany×1, DeleteOne×1 |
| 12 | `invitations` | 13 | Invitation | `internal/models/invitation.go` | 4 | InsertOne×4, CountDocuments×3, DeleteMany×2, DeleteOne×2, Find×1, FindOne×1 |
| 13 | `system_config` | 10 | SystemConfig | `internal/models/system.go` | 5 | FindOne×7, InsertOne×2, UpdateOne×1 |
| 14 | `messages` | 10 | Message | `internal/models/message.go` | 6 | InsertOne×4, DeleteMany×2, Find×2, CountDocuments×1, UpdateOne×1 |
| 15 | `branding_assets` | 9 | BrandingAsset | `internal/models/branding.go` | 1 | FindOne×4, DeleteOne×2, UpdateOne×1, Find×1, InsertOne×1 |
| 16 | `webhooks` | 8 | Webhook | `internal/models/webhook.go` | 3 | FindOne×3, Find×2, InsertOne×2, CountDocuments×1 |
| 17 | `system_nodes` | 7 | SystemNode | `internal/models/health.go` | 4 | Find×3, UpdateOne×2, CountDocuments×1, UpdateMany×1 |
| 18 | `system_metrics` | 7 | SystemMetric | `internal/models/health.go` | 3 | FindOne×3, Find×2, InsertOne×1, Aggregate×1 |
| 19 | `daily_metrics` | 6 | DailyMetric | `internal/models/billing.go` | 5 | Find×3, FindOne×2, UpdateOne×1 |
| 20 | `stripe_mappings` | 6 | StripeMapping | `internal/models/billing.go` | 3 | FindOne×3, DeleteMany×1, Find×1, InsertOne×1 |
| 21 | `announcements` | 5 | Announcement | `internal/models/announcement.go` | 1 | Find×2, InsertOne×1, UpdateOne×1, DeleteOne×1 |
| 22 | `api_keys` | 5 | APIKey | `internal/models/api_key.go` | 3 | InsertOne×2, Find×1, CountDocuments×1, FindOne×1 |
| 23 | `custom_pages` | 5 | CustomPage | `internal/models/branding.go` | 1 | Find×2, FindOne×1, InsertOne×1, DeleteOne×1 |
| 24 | `webhook_deliveries` | 5 | WebhookDelivery | `internal/models/webhook.go` | 2 | InsertOne×2, CountDocuments×1, FindOne×1, Find×1 |
| 25 | `verification_tokens` | 4 | VerificationToken | `internal/models/tokens.go` | 1 | InsertOne×3, UpdateMany×1 |
| 26 | `<unknown>` | 4 | <unknown> | — | 1 | DeleteMany×3, CountDocuments×1 |
| 27 | `branding_config` | 3 | BrandingConfig | `internal/models/branding.go` | 2 | FindOne×2, UpdateOne×1 |
| 28 | `oauth_states` | 3 | OAuthState | `internal/models/tokens.go` | 1 | InsertOne×3 |
| 29 | `usage_events` | 3 | UsageEvent | `internal/models/usage_event.go` | 2 | Aggregate×2, InsertOne×1 |
| 30 | `revoked_tokens` | 2 | RevokedToken | `internal/models/tokens.go` | 2 | InsertOne×1, CountDocuments×1 |
| 31 | `webhook_events` | 2 | WebhookEvent | — | 1 | DeleteOne×1, UpdateOne×1 |
| 32 | `leader_locks` | 2 | LeaderLock | — | 1 | FindOne×1, DeleteOne×1 |
| 33 | `impersonation_logs` | 1 | SystemLog | `internal/models/system_log.go` | 1 | InsertOne×1 |
| 34 | `auth_codes` | 1 | AuthCode | `internal/models/tokens.go` | 1 | InsertOne×1 |

## Operations by Usage

| Operation | Count |
|-----------|-------|
| `FindOne` | 148 |
| `Find` | 78 |
| `UpdateOne` | 76 |
| `CountDocuments` | 63 |
| `InsertOne` | 61 |
| `Aggregate` | 35 |
| `DeleteOne` | 27 |
| `DeleteMany` | 17 |
| `UpdateMany` | 8 |
| `InsertMany` | 2 |

## Models by Query Activity

| Rank | Model struct | Queries | Primary collection |
|------|--------------|---------|--------------------|
| 1 | `Tenant` | 89 | `tenants` |
| 2 | `User` | 88 | `users` |
| 3 | `TenantMembership` | 68 | `tenant_memberships` |
| 4 | `Plan` | 39 | `plans` |
| 5 | `FinancialTransaction` | 18 | `financial_transactions` |
| 6 | `RefreshToken` | 18 | `refresh_tokens` |
| 7 | `SystemLog` | 17 | `system_logs` |
| 8 | `CreditBundle` | 15 | `credit_bundles` |
| 9 | `TelemetryEvent` | 15 | `telemetry_events` |
| 10 | `ConfigVar` | 14 | `config_vars` |
| 11 | `EventDefinition` | 14 | `event_definitions` |
| 12 | `Invitation` | 13 | `invitations` |
| 13 | `SystemConfig` | 10 | `system_config` |
| 14 | `Message` | 10 | `messages` |
| 15 | `BrandingAsset` | 9 | `branding_assets` |
| 16 | `Webhook` | 8 | `webhooks` |
| 17 | `SystemNode` | 7 | `system_nodes` |
| 18 | `SystemMetric` | 7 | `system_metrics` |
| 19 | `DailyMetric` | 6 | `daily_metrics` |
| 20 | `StripeMapping` | 6 | `stripe_mappings` |
| 21 | `Announcement` | 5 | `announcements` |
| 22 | `APIKey` | 5 | `api_keys` |
| 23 | `CustomPage` | 5 | `custom_pages` |
| 24 | `WebhookDelivery` | 5 | `webhook_deliveries` |
| 25 | `VerificationToken` | 4 | `verification_tokens` |
| 26 | `<unknown>` | 4 | `<unknown>` |
| 27 | `BrandingConfig` | 3 | `branding_config` |
| 28 | `OAuthState` | 3 | `oauth_states` |
| 29 | `UsageEvent` | 3 | `usage_events` |
| 30 | `RevokedToken` | 2 | `revoked_tokens` |
| 31 | `WebhookEvent` | 2 | `webhook_events` |
| 32 | `LeaderLock` | 2 | `leader_locks` |
| 33 | `AuthCode` | 1 | `auth_codes` |

## Files with Most Queries

| File | Queries |
|------|---------|
| `internal/api/handlers/auth.go` | 84 |
| `internal/api/handlers/admin.go` | 70 |
| `cmd/lastsaas/main.go` | 42 |
| `internal/api/handlers/webhook.go` | 33 |
| `internal/telemetry/service.go` | 30 |
| `internal/api/handlers/tenant.go` | 26 |
| `internal/api/handlers/plans.go` | 25 |
| `internal/api/handlers/billing.go` | 19 |
| `internal/api/handlers/branding.go` | 16 |
| `internal/api/handlers/event_definitions.go` | 16 |
| `internal/testutil/testutil.go` | 14 |
| `internal/api/handlers/bundles.go` | 10 |
| `cmd/lastsaas/cmd_users.go` | 9 |
| `internal/api/handlers/promotions.go` | 9 |
| `internal/api/handlers/webhooks.go` | 9 |

## Collection → Model Map

| Collection | Model struct |
|------------|--------------|
| `<unknown>` | `<unknown>` |
| `announcements` | `Announcement` |
| `api_keys` | `APIKey` |
| `auth_codes` | `AuthCode` |
| `branding_assets` | `BrandingAsset` |
| `branding_config` | `BrandingConfig` |
| `config_vars` | `ConfigVar` |
| `credit_bundles` | `CreditBundle` |
| `custom_pages` | `CustomPage` |
| `daily_metrics` | `DailyMetric` |
| `event_definitions` | `EventDefinition` |
| `financial_transactions` | `FinancialTransaction` |
| `impersonation_logs` | `SystemLog` |
| `invitations` | `Invitation` |
| `leader_locks` | `LeaderLock` |
| `messages` | `Message` |
| `oauth_states` | `OAuthState` |
| `plans` | `Plan` |
| `refresh_tokens` | `RefreshToken` |
| `revoked_tokens` | `RevokedToken` |
| `stripe_mappings` | `StripeMapping` |
| `system_config` | `SystemConfig` |
| `system_logs` | `SystemLog` |
| `system_metrics` | `SystemMetric` |
| `system_nodes` | `SystemNode` |
| `telemetry_events` | `TelemetryEvent` |
| `tenant_memberships` | `TenantMembership` |
| `tenants` | `Tenant` |
| `usage_events` | `UsageEvent` |
| `users` | `User` |
| `verification_tokens` | `VerificationToken` |
| `webhook_deliveries` | `WebhookDelivery` |
| `webhook_events` | `WebhookEvent` |
| `webhooks` | `Webhook` |

## All Queries

### `cmd/lastsaas/cmd_doctor.go`

| Line | Function | Operation | Collection | Model | Filter fields |
|------|----------|-----------|------------|-------|---------------|
| 65 | `cmdDoctor` | `FindOne` | `system_config` | `SystemConfig` | — |
| 100 | `cmdDoctor` | `FindOne` | `tenants` | `Tenant` | `isRoot` |
| 101 | `cmdDoctor` | `CountDocuments` | `tenant_memberships` | `TenantMembership` | `tenantId`, `role` |
| 110 | `cmdDoctor` | `CountDocuments` | `system_nodes` | `SystemNode` | `lastSeen` |

### `cmd/lastsaas/cmd_financial.go`

| Line | Function | Operation | Collection | Model | Filter fields |
|------|----------|-----------|------------|-------|---------------|
| 58 | `cmdFinancialSummary` | `Aggregate` | `financial_transactions` | `FinancialTransaction` | — |
| 81 | `cmdFinancialSummary` | `Aggregate` | `financial_transactions` | `FinancialTransaction` | — |
| 105 | `cmdFinancialSummary` | `Aggregate` | `financial_transactions` | `FinancialTransaction` | — |
| 122 | `cmdFinancialSummary` | `CountDocuments` | `tenants` | `Tenant` | `billingStatus` |
| 126 | `cmdFinancialSummary` | `FindOne` | `daily_metrics` | `DailyMetric` | — |
| 135 | `cmdFinancialSummary` | `Aggregate` | `financial_transactions` | `FinancialTransaction` | — |
| 236 | `cmdFinancialTransactions` | `Find` | `financial_transactions` | `FinancialTransaction` | — |
| 329 | `cmdFinancialMetrics` | `Find` | `daily_metrics` | `DailyMetric` | — |

### `cmd/lastsaas/cmd_health.go`

| Line | Function | Operation | Collection | Model | Filter fields |
|------|----------|-----------|------------|-------|---------------|
| 50 | `cmdHealth` | `Find` | `system_nodes` | `SystemNode` | — |
| 73 | `cmdHealth` | `FindOne` | `system_metrics` | `SystemMetric` | — |
| 96 | `cmdHealth` | `Find` | `system_nodes` | `SystemNode` | — |
| 120 | `cmdHealth` | `FindOne` | `system_metrics` | `SystemMetric` | — |

### `cmd/lastsaas/cmd_logs.go`

| Line | Function | Operation | Collection | Model | Filter fields |
|------|----------|-----------|------------|-------|---------------|
| 137 | `queryLogs` | `Find` | `system_logs` | `SystemLog` | — |
| 190 | `logsFollow` | `Find` | `system_logs` | `SystemLog` | — |

### `cmd/lastsaas/cmd_stats.go`

| Line | Function | Operation | Collection | Model | Filter fields |
|------|----------|-----------|------------|-------|---------------|
| 24 | `cmdStats` | `CountDocuments` | `users` | `User` | `isActive` |
| 27 | `cmdStats` | `CountDocuments` | `tenants` | `Tenant` | `billingStatus` |
| 38 | `cmdStats` | `Aggregate` | `system_logs` | `SystemLog` | — |
| 55 | `cmdStats` | `FindOne` | `daily_metrics` | `DailyMetric` | — |
| 63 | `cmdStats` | `Aggregate` | `financial_transactions` | `FinancialTransaction` | — |

### `cmd/lastsaas/cmd_tenants.go`

| Line | Function | Operation | Collection | Model | Filter fields |
|------|----------|-----------|------------|-------|---------------|
| 58 | `cmdTenantsList` | `Find` | `tenants` | `Tenant` | — |
| 157 | `cmdTenantsGet` | `FindOne` | `tenants` | `Tenant` | `_id` |
| 161 | `cmdTenantsGet` | `FindOne` | `tenants` | `Tenant` | `slug` |
| 168 | `cmdTenantsGet` | `Find` | `tenant_memberships` | `TenantMembership` | `tenantId` |
| 188 | `cmdTenantsGet` | `FindOne` | `plans` | `Plan` | `_id` |
| 284 | `resolveUserNames` | `Find` | `users` | `User` | `_id` |
| 311 | `resolvePlanNames` | `Find` | `plans` | `Plan` | `_id` |
| 348 | `countMembersPerTenant` | `Aggregate` | `tenant_memberships` | `TenantMembership` | — |

### `cmd/lastsaas/cmd_users.go`

| Line | Function | Operation | Collection | Model | Filter fields |
|------|----------|-----------|------------|-------|---------------|
| 70 | `cmdUsersList` | `Find` | `users` | `User` | — |
| 278 | `cmdUsersSetActive` | `FindOne` | `users` | `User` | `email` |
| 292 | `cmdUsersSetActive` | `UpdateOne` | `users` | `User` | — |
| 305 | `cmdUsersSetActive` | `DeleteMany` | `refresh_tokens` | `RefreshToken` | `userId` |
| 328 | `cmdUsersRevokeSessions` | `FindOne` | `users` | `User` | `email` |
| 333 | `cmdUsersRevokeSessions` | `DeleteMany` | `refresh_tokens` | `RefreshToken` | `userId` |
| 346 | `lookupUserWithMemberships` | `FindOne` | `users` | `User` | `email` |
| 351 | `lookupUserWithMemberships` | `Find` | `tenant_memberships` | `TenantMembership` | `userId` |
| 368 | `resolveTenantNames` | `Find` | `tenants` | `Tenant` | `_id` |

### `cmd/lastsaas/main.go`

| Line | Function | Operation | Collection | Model | Filter fields |
|------|----------|-----------|------------|-------|---------------|
| 225 | `cmdSetup` | `FindOne` | `system_config` | `SystemConfig` | — |
| 233 | `cmdSetup` | `FindOne` | `tenants` | `Tenant` | `isRoot` |
| 235 | `cmdSetup` | `FindOne` | `tenant_memberships` | `TenantMembership` | `tenantId`, `role` |
| 237 | `cmdSetup` | `FindOne` | `users` | `User` | `_id` |
| 301 | `cmdSetup` | `InsertOne` | `tenants` | `Tenant` | — |
| 319 | `cmdSetup` | `DeleteOne` | `tenants` | `Tenant` | `_id` |
| 323 | `cmdSetup` | `InsertOne` | `users` | `User` | — |
| 324 | `cmdSetup` | `DeleteOne` | `tenants` | `Tenant` | `_id` |
| 339 | `cmdSetup` | `DeleteOne` | `users` | `User` | `_id` |
| 340 | `cmdSetup` | `DeleteOne` | `tenants` | `Tenant` | `_id` |
| 344 | `cmdSetup` | `InsertOne` | `tenant_memberships` | `TenantMembership` | — |
| 345 | `cmdSetup` | `DeleteOne` | `users` | `User` | `_id` |
| 346 | `cmdSetup` | `DeleteOne` | `tenants` | `Tenant` | `_id` |
| 359 | `cmdSetup` | `InsertOne` | `system_config` | `SystemConfig` | — |
| 360 | `cmdSetup` | `DeleteOne` | `tenant_memberships` | `TenantMembership` | `_id` |
| 361 | `cmdSetup` | `DeleteOne` | `users` | `User` | `_id` |
| 362 | `cmdSetup` | `DeleteOne` | `tenants` | `Tenant` | `_id` |
| 377 | `cmdSetup` | `InsertOne` | `messages` | `Message` | — |
| 410 | `cmdChangePassword` | `FindOne` | `users` | `User` | `email` |
| 440 | `cmdChangePassword` | `UpdateOne` | `users` | `User` | — |
| 453 | `cmdChangePassword` | `DeleteMany` | `refresh_tokens` | `RefreshToken` | `userId` |
| 503 | `cmdSendMessage` | `FindOne` | `users` | `User` | `email` |
| 519 | `cmdSendMessage` | `InsertOne` | `messages` | `Message` | — |
| 575 | `cmdConfigList` | `Find` | `config_vars` | `ConfigVar` | — |
| 623 | `cmdConfigGet` | `FindOne` | `config_vars` | `ConfigVar` | `name` |
| 653 | `cmdConfigSet` | `FindOne` | `config_vars` | `ConfigVar` | `name` |
| 664 | `cmdConfigSet` | `UpdateOne` | `config_vars` | `ConfigVar` | — |
| 701 | `cmdConfigReset` | `FindOne` | `config_vars` | `ConfigVar` | `name` |
| 712 | `cmdConfigReset` | `UpdateOne` | `config_vars` | `ConfigVar` | — |
| 745 | `cmdTransferRootOwner` | `FindOne` | `tenants` | `Tenant` | `isRoot` |
| 753 | `cmdTransferRootOwner` | `FindOne` | `users` | `User` | `email` |
| 760 | `cmdTransferRootOwner` | `FindOne` | `tenant_memberships` | `TenantMembership` | `userId`, `tenantId` |
| 776 | `cmdTransferRootOwner` | `FindOne` | `tenant_memberships` | `TenantMembership` | `tenantId`, `role` |
| 785 | `cmdTransferRootOwner` | `FindOne` | `users` | `User` | `_id` |
| 813 | `cmdTransferRootOwner` | `UpdateOne` | `tenant_memberships` | `TenantMembership` | — |
| 823 | `cmdTransferRootOwner` | `UpdateOne` | `tenant_memberships` | `TenantMembership` | — |
| 829 | `cmdTransferRootOwner` | `UpdateOne` | `tenant_memberships` | `TenantMembership` | — |
| 844 | `cmdTransferRootOwner` | `InsertOne` | `system_logs` | `SystemLog` | — |
| 865 | `cmdVersion` | `FindOne` | `system_config` | `SystemConfig` | — |
| 906 | `cmdStatus` | `FindOne` | `system_config` | `SystemConfig` | — |
| 918 | `cmdStatus` | `CountDocuments` | `users` | `User` | — |
| 919 | `cmdStatus` | `CountDocuments` | `tenants` | `Tenant` | — |

### `cmd/server/main.go`

| Line | Function | Operation | Collection | Model | Filter fields |
|------|----------|-----------|------------|-------|---------------|
| 786 | `main` | `FindOne` | `branding_config` | `BrandingConfig` | — |

### `internal/api/handlers/admin.go`

| Line | Function | Operation | Collection | Model | Filter fields |
|------|----------|-----------|------------|-------|---------------|
| 51 | `isRootTenantOwner` | `CountDocuments` | `tenant_memberships` | `TenantMembership` | `userId`, `role` |
| 60 | `isRootTenantOwner` | `FindOne` | `tenant_memberships` | `TenantMembership` | `userId`, `role` |
| 64 | `isRootTenantOwner` | `FindOne` | `tenants` | `Tenant` | `_id` |
| 172 | `ListTenants` | `CountDocuments` | `tenants` | `Tenant` | — |
| 183 | `ListTenants` | `Find` | `tenants` | `Tenant` | — |
| 207 | `ListTenants` | `Aggregate` | `tenant_memberships` | `TenantMembership` | — |
| 222 | `ListTenants` | `Find` | `plans` | `Plan` | — |
| 303 | `ExportTenantsCSV` | `Find` | `tenants` | `Tenant` | — |
| 327 | `ExportTenantsCSV` | `Aggregate` | `tenant_memberships` | `TenantMembership` | — |
| 342 | `ExportTenantsCSV` | `Find` | `plans` | `Plan` | — |
| 399 | `GetTenant` | `FindOne` | `tenants` | `Tenant` | `_id` |
| 405 | `GetTenant` | `Find` | `tenant_memberships` | `TenantMembership` | `tenantId` |
| 422 | `GetTenant` | `Find` | `users` | `User` | `_id` |
| 464 | `UpdateTenantStatus` | `FindOne` | `tenants` | `Tenant` | `_id` |
| 483 | `UpdateTenantStatus` | `UpdateOne` | `tenants` | `Tenant` | — |
| 562 | `ListUsers` | `CountDocuments` | `users` | `User` | — |
| 573 | `ListUsers` | `Find` | `users` | `User` | — |
| 597 | `ListUsers` | `Aggregate` | `tenant_memberships` | `TenantMembership` | — |
| 659 | `ExportUsersCSV` | `Find` | `users` | `User` | — |
| 683 | `ExportUsersCSV` | `Aggregate` | `tenant_memberships` | `TenantMembership` | — |
| 745 | `UpdateUserStatus` | `UpdateOne` | `users` | `User` | — |
| 784 | `GetDashboard` | `CountDocuments` | `users` | `User` | — |
| 785 | `GetDashboard` | `CountDocuments` | `tenants` | `Tenant` | — |
| 884 | `GetUser` | `FindOne` | `users` | `User` | `_id` |
| 889 | `GetUser` | `Find` | `tenant_memberships` | `TenantMembership` | `userId` |
| 900 | `GetUser` | `Find` | `plans` | `Plan` | — |
| 928 | `GetUser` | `Find` | `tenants` | `Tenant` | `_id` |
| 1011 | `UpdateUser` | `FindOne` | `users` | `User` | `_id` |
| 1026 | `UpdateUser` | `CountDocuments` | `users` | `User` | `email`, `_id` |
| 1045 | `UpdateUser` | `UpdateOne` | `users` | `User` | `_id` |
| 1082 | `UpdateUserRole` | `FindOne` | `tenants` | `Tenant` | `_id` |
| 1099 | `UpdateUserRole` | `FindOne` | `tenant_memberships` | `TenantMembership` | `tenantId`, `role` |
| 1103 | `UpdateUserRole` | `UpdateOne` | `tenant_memberships` | `TenantMembership` | — |
| 1110 | `UpdateUserRole` | `UpdateOne` | `tenant_memberships` | `TenantMembership` | — |
| 1152 | `PreflightDeleteUser` | `Find` | `tenant_memberships` | `TenantMembership` | `userId`, `role` |
| 1173 | `PreflightDeleteUser` | `Find` | `tenants` | `Tenant` | `_id` |
| 1189 | `PreflightDeleteUser` | `Find` | `tenant_memberships` | `TenantMembership` | `tenantId`, `userId` |
| 1207 | `PreflightDeleteUser` | `Find` | `users` | `User` | `_id` |
| 1260 | `DeleteUser` | `FindOne` | `users` | `User` | `_id` |
| 1280 | `DeleteUser` | `Find` | `tenant_memberships` | `TenantMembership` | `userId` |
| 1300 | `DeleteUser` | `FindOne` | `tenants` | `Tenant` | `_id` |
| 1316 | `DeleteUser` | `UpdateOne` | `tenant_memberships` | `TenantMembership` | — |
| 1328 | `DeleteUser` | `CountDocuments` | `tenant_memberships` | `TenantMembership` | `tenantId`, `userId` |
| 1348 | `DeleteUser` | `DeleteMany` | `tenant_memberships` | `TenantMembership` | `tenantId` |
| 1349 | `DeleteUser` | `DeleteOne` | `tenants` | `Tenant` | `_id` |
| 1350 | `DeleteUser` | `DeleteMany` | `invitations` | `Invitation` | `tenantId` |
| 1367 | `DeleteUser` | `DeleteMany` | `tenant_memberships` | `TenantMembership` | `userId` |
| 1368 | `DeleteUser` | `DeleteMany` | `refresh_tokens` | `RefreshToken` | `userId` |
| 1369 | `DeleteUser` | `DeleteMany` | `messages` | `Message` | `userId` |
| 1370 | `DeleteUser` | `DeleteOne` | `users` | `User` | `_id` |
| 1407 | `UpdateTenant` | `FindOne` | `tenants` | `Tenant` | `_id` |
| 1461 | `UpdateTenant` | `UpdateOne` | `tenants` | `Tenant` | `_id` |
| 1490 | `ImpersonateUser` | `FindOne` | `users` | `User` | `_id` |
| 1497 | `ImpersonateUser` | `FindOne` | `tenants` | `Tenant` | `isRoot` |
| 1499 | `ImpersonateUser` | `FindOne` | `tenant_memberships` | `TenantMembership` | `userId`, `tenantId`, `role` |
| 1527 | `ImpersonateUser` | `InsertOne` | `impersonation_logs` | `SystemLog` | — |
| 1538 | `ImpersonateUser` | `Find` | `tenant_memberships` | `TenantMembership` | `userId` |
| 1551 | `ImpersonateUser` | `FindOne` | `tenants` | `Tenant` | `_id` |
| 1574 | `getRootTenant` | `FindOne` | `tenants` | `Tenant` | `isRoot` |
| 1590 | `ListRootMembers` | `Find` | `tenant_memberships` | `TenantMembership` | `tenantId` |
| 1610 | `ListRootMembers` | `Find` | `users` | `User` | `_id` |
| 1641 | `ListRootMembers` | `Find` | `invitations` | `Invitation` | `createdAt`, `tenantId`, `status`, `expiresAt` |
| 1708 | `InviteRootMember` | `FindOne` | `users` | `User` | `email` |
| 1709 | `InviteRootMember` | `CountDocuments` | `tenant_memberships` | `TenantMembership` | `userId`, `tenantId` |
| 1720 | `InviteRootMember` | `CountDocuments` | `invitations` | `Invitation` | `tenantId`, `email`, `status`, `expiresAt` |
| 1748 | `InviteRootMember` | `InsertOne` | `invitations` | `Invitation` | — |
| 1809 | `RemoveRootMember` | `FindOne` | `tenant_memberships` | `TenantMembership` | `userId`, `tenantId` |
| 1827 | `RemoveRootMember` | `DeleteOne` | `tenant_memberships` | `TenantMembership` | `_id` |
| 1895 | `ChangeRootMemberRole` | `UpdateOne` | `tenant_memberships` | `TenantMembership` | — |
| 1937 | `CancelRootInvitation` | `DeleteOne` | `invitations` | `Invitation` | `_id`, `tenantId`, `status` |

### `internal/api/handlers/announcements.go`

| Line | Function | Operation | Collection | Model | Filter fields |
|------|----------|-----------|------------|-------|---------------|
| 33 | `ListPublic` | `Find` | `announcements` | `Announcement` | `isPublished` |
| 54 | `ListAll` | `Find` | `announcements` | `Announcement` | — |
| 105 | `Create` | `InsertOne` | `announcements` | `Announcement` | — |
| 152 | `Update` | `UpdateOne` | `announcements` | `Announcement` | `_id` |
| 168 | `Delete` | `DeleteOne` | `announcements` | `Announcement` | `_id` |

### `internal/api/handlers/apikeys.go`

| Line | Function | Operation | Collection | Model | Filter fields |
|------|----------|-----------|------------|-------|---------------|
| 45 | `ListAPIKeys` | `Find` | `api_keys` | `APIKey` | `isActive` |
| 60 | `ListAPIKeys` | `CountDocuments` | `api_keys` | `APIKey` | `isActive` |
| 123 | `CreateAPIKey` | `InsertOne` | `api_keys` | `APIKey` | — |

### `internal/api/handlers/auth.go`

| Line | Function | Operation | Collection | Model | Filter fields |
|------|----------|-----------|------------|-------|---------------|
| 220 | `Register` | `FindOne` | `users` | `User` | `email` |
| 249 | `Register` | `InsertOne` | `users` | `User` | — |
| 324 | `Login` | `FindOne` | `users` | `User` | `email` |
| 361 | `Login` | `UpdateOne` | `users` | `User` | `_id`, `accountLockedUntil` |
| 381 | `Login` | `UpdateOne` | `users` | `User` | `_id`, `failedLoginAttempts`, `accountLockedUntil`, `lastLoginAt`, `updatedAt` |
| 444 | `Logout` | `InsertOne` | `revoked_tokens` | `RevokedToken` | — |
| 461 | `Logout` | `UpdateMany` | `refresh_tokens` | `RefreshToken` | — |
| 494 | `Refresh` | `FindOne` | `refresh_tokens` | `RefreshToken` | `tokenHash` |
| 505 | `Refresh` | `UpdateMany` | `refresh_tokens` | `RefreshToken` | — |
| 516 | `Refresh` | `UpdateOne` | `refresh_tokens` | `RefreshToken` | — |
| 528 | `Refresh` | `FindOne` | `users` | `User` | `_id`, `isActive` |
| 546 | `Refresh` | `UpdateOne` | `refresh_tokens` | `RefreshToken` | — |
| 601 | `VerifyEmail` | `UpdateOne` | `users` | `User` | `_id`, `emailVerified`, `updatedAt` |
| 636 | `ResendVerification` | `FindOne` | `users` | `User` | `email` |
| 676 | `ForgotPassword` | `FindOne` | `users` | `User` | `email` |
| 681 | `ForgotPassword` | `UpdateMany` | `verification_tokens` | `VerificationToken` | — |
| 696 | `ForgotPassword` | `InsertOne` | `verification_tokens` | `VerificationToken` | — |
| 752 | `ResetPassword` | `UpdateOne` | `users` | `User` | `_id`, `passwordHash`, `updatedAt`, `authMethods` |
| 762 | `ResetPassword` | `UpdateMany` | `refresh_tokens` | `RefreshToken` | — |
| 822 | `ChangePassword` | `UpdateOne` | `users` | `User` | `_id` |
| 829 | `ChangePassword` | `UpdateMany` | `refresh_tokens` | `RefreshToken` | — |
| 874 | `MFASetup` | `UpdateOne` | `users` | `User` | `_id`, `totpSecret`, `updatedAt` |
| 905 | `MFAVerifySetup` | `FindOne` | `users` | `User` | `_id` |
| 929 | `MFAVerifySetup` | `UpdateOne` | `users` | `User` | `_id`, `totpEnabled`, `totpVerifiedAt`, `recoveryCodes`, `updatedAt` |
| 966 | `MFADisable` | `FindOne` | `users` | `User` | `_id` |
| 986 | `MFADisable` | `UpdateOne` | `users` | `User` | `_id`, `totpEnabled`, `totpSecret`, `totpVerifiedAt`, `recoveryCodes`, `updatedAt` |
| 1036 | `MFAChallenge` | `FindOne` | `users` | `User` | `_id` |
| 1056 | `MFAChallenge` | `UpdateOne` | `users` | `User` | `_id`, `recoveryCodes` |
| 1109 | `MFARegenerateRecoveryCodes` | `FindOne` | `users` | `User` | `_id` |
| 1130 | `MFARegenerateRecoveryCodes` | `UpdateOne` | `users` | `User` | `_id`, `recoveryCodes`, `updatedAt` |
| 1172 | `MagicLinkRequest` | `FindOne` | `users` | `User` | `email` |
| 1186 | `MagicLinkRequest` | `InsertOne` | `verification_tokens` | `VerificationToken` | — |
| 1234 | `MagicLinkVerify` | `FindOne` | `users` | `User` | `_id`, `isActive` |
| 1240 | `MagicLinkVerify` | `UpdateOne` | `users` | `User` | `_id`, `emailVerified`, `lastLoginAt`, `updatedAt`, `authMethods` |
| 1294 | `createAuthCodeRedirect` | `InsertOne` | `auth_codes` | `AuthCode` | — |
| 1353 | `GoogleOAuth` | `InsertOne` | `oauth_states` | `OAuthState` | — |
| 1402 | `GoogleOAuthCallback` | `FindOne` | `users` | `User` | `googleId` |
| 1404 | `GoogleOAuthCallback` | `FindOne` | `users` | `User` | `email` |
| 1419 | `GoogleOAuthCallback` | `InsertOne` | `users` | `User` | — |
| 1427 | `GoogleOAuthCallback` | `UpdateOne` | `users` | `User` | `_id`, `googleId`, `lastLoginAt`, `updatedAt`, `authMethods` |
| 1433 | `GoogleOAuthCallback` | `UpdateOne` | `users` | `User` | `_id`, `lastLoginAt`, `updatedAt` |
| 1486 | `GitHubOAuth` | `InsertOne` | `oauth_states` | `OAuthState` | — |
| 1536 | `GitHubOAuthCallback` | `FindOne` | `users` | `User` | `githubId` |
| 1538 | `GitHubOAuthCallback` | `FindOne` | `users` | `User` | `email` |
| 1557 | `GitHubOAuthCallback` | `InsertOne` | `users` | `User` | — |
| 1570 | `GitHubOAuthCallback` | `UpdateOne` | `users` | `User` | `_id`, `githubId`, `lastLoginAt`, `updatedAt`, `authMethods` |
| 1576 | `GitHubOAuthCallback` | `UpdateOne` | `users` | `User` | `_id`, `lastLoginAt`, `updatedAt` |
| 1628 | `MicrosoftOAuth` | `InsertOne` | `oauth_states` | `OAuthState` | — |
| 1683 | `MicrosoftOAuthCallback` | `FindOne` | `users` | `User` | `microsoftId` |
| 1685 | `MicrosoftOAuthCallback` | `FindOne` | `users` | `User` | `email` |
| 1704 | `MicrosoftOAuthCallback` | `InsertOne` | `users` | `User` | — |
| 1717 | `MicrosoftOAuthCallback` | `UpdateOne` | `users` | `User` | `_id`, `microsoftId`, `lastLoginAt`, `updatedAt`, `authMethods` |
| 1723 | `MicrosoftOAuthCallback` | `UpdateOne` | `users` | `User` | `_id`, `lastLoginAt`, `updatedAt` |
| 1769 | `ListSessions` | `Find` | `refresh_tokens` | `RefreshToken` | `createdAt`, `userId`, `isRevoked`, `expiresAt` |
| 1840 | `RevokeSession` | `UpdateOne` | `refresh_tokens` | `RefreshToken` | — |
| 1860 | `RevokeAllSessions` | `UpdateMany` | `refresh_tokens` | `RefreshToken` | — |
| 1901 | `UpdatePreferences` | `UpdateOne` | `users` | `User` | `_id` |
| 1916 | `CompleteOnboarding` | `UpdateOne` | `users` | `User` | `_id`, `onboardingCompletedAt`, `updatedAt` |
| 1967 | `createPersonalTenant` | `InsertOne` | `tenants` | `Tenant` | — |
| 1980 | `createPersonalTenant` | `InsertOne` | `tenant_memberships` | `TenantMembership` | — |
| 2002 | `sendVerificationEmail` | `InsertOne` | `verification_tokens` | `VerificationToken` | — |
| 2005 | `sendVerificationEmail` | `UpdateOne` | `users` | `User` | `_id`, `lastVerificationSent` |
| 2024 | `getUserMemberships` | `Find` | `tenant_memberships` | `TenantMembership` | `userId` |
| 2038 | `getUserMemberships` | `FindOne` | `tenants` | `Tenant` | `_id` |
| 2058 | `acceptInvitationForUser` | `FindOne` | `invitations` | `Invitation` | `token`, `status`, `expiresAt` |
| 2069 | `acceptInvitationForUser` | `FindOne` | `users` | `User` | `_id` |
| 2089 | `acceptInvitationForUser` | `CountDocuments` | `tenant_memberships` | `TenantMembership` | `userId`, `tenantId` |
| 2105 | `acceptInvitationForUser` | `InsertOne` | `tenant_memberships` | `TenantMembership` | — |
| 2111 | `acceptInvitationForUser` | `UpdateOne` | `users` | `User` | `_id`, `emailVerified`, `updatedAt` |
| 2142 | `storeRefreshToken` | `CountDocuments` | `refresh_tokens` | `RefreshToken` | `userId`, `isRevoked`, `expiresAt` |
| 2150 | `storeRefreshToken` | `Find` | `refresh_tokens` | `RefreshToken` | — |
| 2180 | `storeRefreshToken` | `InsertOne` | `refresh_tokens` | `RefreshToken` | — |
| 2217 | `DeleteAccount` | `Find` | `tenant_memberships` | `TenantMembership` | `userId` |
| 2237 | `DeleteAccount` | `FindOne` | `tenants` | `Tenant` | `_id` |
| 2246 | `DeleteAccount` | `CountDocuments` | `tenant_memberships` | `TenantMembership` | `tenantId`, `userId` |
| 2256 | `DeleteAccount` | `DeleteMany` | `tenant_memberships` | `TenantMembership` | `tenantId` |
| 2259 | `DeleteAccount` | `DeleteOne` | `tenants` | `Tenant` | `_id` |
| 2262 | `DeleteAccount` | `DeleteMany` | `invitations` | `Invitation` | `tenantId` |
| 2278 | `DeleteAccount` | `DeleteMany` | `tenant_memberships` | `TenantMembership` | `userId` |
| 2281 | `DeleteAccount` | `DeleteMany` | `refresh_tokens` | `RefreshToken` | `userId` |
| 2284 | `DeleteAccount` | `DeleteMany` | `messages` | `Message` | `userId` |
| 2287 | `DeleteAccount` | `DeleteOne` | `users` | `User` | `_id` |
| 2317 | `ExportData` | `Find` | `tenant_memberships` | `TenantMembership` | `userId` |
| 2339 | `ExportData` | `Find` | `messages` | `Message` | `userId` |

### `internal/api/handlers/billing.go`

| Line | Function | Operation | Collection | Model | Filter fields |
|------|----------|-----------|------------|-------|---------------|
| 94 | `Checkout` | `FindOne` | `plans` | `Plan` | `_id` |
| 122 | `Checkout` | `UpdateOne` | `tenants` | `Tenant` | `_id`, `billingWaived`, `updatedAt` |
| 138 | `Checkout` | `CountDocuments` | `tenant_memberships` | `TenantMembership` | `tenantId` |
| 148 | `Checkout` | `UpdateOne` | `tenants` | `Tenant` | `_id`, `purchasedCredits` |
| 158 | `Checkout` | `CountDocuments` | `tenant_memberships` | `TenantMembership` | `tenantId` |
| 305 | `Checkout` | `FindOne` | `credit_bundles` | `CreditBundle` | `_id`, `isActive` |
| 395 | `ListTransactions` | `CountDocuments` | `financial_transactions` | `FinancialTransaction` | — |
| 402 | `ListTransactions` | `Find` | `financial_transactions` | `FinancialTransaction` | — |
| 442 | `GetInvoice` | `FindOne` | `financial_transactions` | `FinancialTransaction` | `_id`, `tenantId` |
| 471 | `GetInvoicePDF` | `FindOne` | `financial_transactions` | `FinancialTransaction` | `_id`, `tenantId` |
| 639 | `CancelSubscription` | `UpdateOne` | `tenants` | `Tenant` | `_id` |
| 714 | `AdminListTransactions` | `CountDocuments` | `financial_transactions` | `FinancialTransaction` | — |
| 721 | `AdminListTransactions` | `Find` | `financial_transactions` | `FinancialTransaction` | — |
| 778 | `AdminGetMetrics` | `Find` | `daily_metrics` | `DailyMetric` | — |
| 866 | `computeLiveRevenue` | `Aggregate` | `financial_transactions` | `FinancialTransaction` | — |
| 901 | `computeLiveARR` | `Aggregate` | `tenants` | `Tenant` | — |
| 926 | `AdminCancelSubscription` | `FindOne` | `tenants` | `Tenant` | `_id` |
| 972 | `AdminCancelSubscription` | `UpdateOne` | `tenants` | `Tenant` | `_id` |
| 1001 | `AdminUpdateSubscription` | `UpdateOne` | `tenants` | `Tenant` | `_id` |

### `internal/api/handlers/bootstrap.go`

| Line | Function | Operation | Collection | Model | Filter fields |
|------|----------|-----------|------------|-------|---------------|
| 36 | `refreshInitialized` | `FindOne` | `system_config` | `SystemConfig` | — |
| 66 | `refreshInitializedFromContext` | `FindOne` | `system_config` | `SystemConfig` | — |

### `internal/api/handlers/branding.go`

| Line | Function | Operation | Collection | Model | Filter fields |
|------|----------|-----------|------------|-------|---------------|
| 44 | `GetBranding` | `FindOne` | `branding_config` | `BrandingConfig` | — |
| 59 | `GetBranding` | `FindOne` | `branding_assets` | `BrandingAsset` | `key` |
| 63 | `GetBranding` | `FindOne` | `branding_assets` | `BrandingAsset` | `key` |
| 118 | `ServeAsset` | `FindOne` | `branding_assets` | `BrandingAsset` | `key` |
| 137 | `ServeMedia` | `FindOne` | `branding_assets` | `BrandingAsset` | `key` |
| 156 | `GetPublicPage` | `FindOne` | `custom_pages` | `CustomPage` | `slug`, `isPublished` |
| 175 | `ListPublicPages` | `Find` | `custom_pages` | `CustomPage` | `isPublished` |
| 255 | `UpdateBranding` | `UpdateOne` | `branding_config` | `BrandingConfig` | — |
| 317 | `UploadAsset` | `UpdateOne` | `branding_assets` | `BrandingAsset` | `key` |
| 341 | `DeleteAsset` | `DeleteOne` | `branding_assets` | `BrandingAsset` | `key` |
| 361 | `ListMedia` | `Find` | `branding_assets` | `BrandingAsset` | — |
| 453 | `UploadMedia` | `InsertOne` | `branding_assets` | `BrandingAsset` | — |
| 480 | `DeleteMedia` | `DeleteOne` | `branding_assets` | `BrandingAsset` | `key` |
| 498 | `AdminListPages` | `Find` | `custom_pages` | `CustomPage` | — |
| 536 | `CreatePage` | `InsertOne` | `custom_pages` | `CustomPage` | — |
| 609 | `DeletePage` | `DeleteOne` | `custom_pages` | `CustomPage` | `_id` |

### `internal/api/handlers/bundles.go`

| Line | Function | Operation | Collection | Model | Filter fields |
|------|----------|-----------|------------|-------|---------------|
| 60 | `ListBundles` | `Find` | `credit_bundles` | `CreditBundle` | — |
| 75 | `ListBundles` | `CountDocuments` | `credit_bundles` | `CreditBundle` | — |
| 92 | `CreateBundle` | `CountDocuments` | `credit_bundles` | `CreditBundle` | `name` |
| 109 | `CreateBundle` | `InsertOne` | `credit_bundles` | `CreditBundle` | — |
| 137 | `UpdateBundle` | `FindOne` | `credit_bundles` | `CreditBundle` | `_id` |
| 158 | `UpdateBundle` | `CountDocuments` | `credit_bundles` | `CreditBundle` | `name`, `_id` |
| 184 | `UpdateBundle` | `FindOne` | `credit_bundles` | `CreditBundle` | `_id` |
| 197 | `DeleteBundle` | `FindOne` | `credit_bundles` | `CreditBundle` | `_id` |
| 206 | `DeleteBundle` | `DeleteOne` | `credit_bundles` | `CreditBundle` | `_id` |
| 221 | `ListBundlesPublic` | `Find` | `credit_bundles` | `CreditBundle` | `isActive` |

### `internal/api/handlers/config.go`

| Line | Function | Operation | Collection | Model | Filter fields |
|------|----------|-----------|------------|-------|---------------|
| 94 | `UpdateConfig` | `UpdateOne` | `config_vars` | `ConfigVar` | `name` |
| 158 | `CreateConfig` | `InsertOne` | `config_vars` | `ConfigVar` | — |
| 188 | `DeleteConfig` | `DeleteOne` | `config_vars` | `ConfigVar` | `name` |

### `internal/api/handlers/event_definitions.go`

| Line | Function | Operation | Collection | Model | Filter fields |
|------|----------|-----------|------------|-------|---------------|
| 49 | `ListEventDefinitions` | `Find` | `event_definitions` | `EventDefinition` | `name` |
| 84 | `ListEventDefinitions` | `Aggregate` | `telemetry_events` | `TelemetryEvent` | — |
| 134 | `CreateEventDefinition` | `CountDocuments` | `event_definitions` | `EventDefinition` | `name` |
| 156 | `CreateEventDefinition` | `CountDocuments` | `event_definitions` | `EventDefinition` | `_id` |
| 164 | `CreateEventDefinition` | `InsertOne` | `event_definitions` | `EventDefinition` | — |
| 203 | `UpdateEventDefinition` | `FindOne` | `event_definitions` | `EventDefinition` | `_id` |
| 210 | `UpdateEventDefinition` | `CountDocuments` | `event_definitions` | `EventDefinition` | `name`, `_id` |
| 236 | `UpdateEventDefinition` | `CountDocuments` | `event_definitions` | `EventDefinition` | `_id` |
| 252 | `UpdateEventDefinition` | `UpdateOne` | `event_definitions` | `EventDefinition` | `_id` |
| 261 | `UpdateEventDefinition` | `FindOne` | `event_definitions` | `EventDefinition` | `_id` |
| 276 | `DeleteEventDefinition` | `FindOne` | `event_definitions` | `EventDefinition` | `_id` |
| 282 | `DeleteEventDefinition` | `UpdateMany` | `event_definitions` | `EventDefinition` | `parentId`, `updatedAt` |
| 287 | `DeleteEventDefinition` | `DeleteOne` | `event_definitions` | `EventDefinition` | `_id` |
| 301 | `GetSankeyData` | `Find` | `event_definitions` | `EventDefinition` | — |
| 379 | `GetSankeyData` | `Aggregate` | `telemetry_events` | `TelemetryEvent` | — |
| 443 | `wouldCreateCycle` | `FindOne` | `event_definitions` | `EventDefinition` | `_id` |

### `internal/api/handlers/logs.go`

| Line | Function | Operation | Collection | Model | Filter fields |
|------|----------|-----------|------------|-------|---------------|
| 112 | `ListLogs` | `CountDocuments` | `system_logs` | `SystemLog` | — |
| 124 | `ListLogs` | `Find` | `system_logs` | `SystemLog` | — |
| 155 | `SeverityCounts` | `Aggregate` | `system_logs` | `SystemLog` | — |
| 195 | `ExportCSV` | `Find` | `system_logs` | `SystemLog` | — |

### `internal/api/handlers/messages.go`

| Line | Function | Operation | Collection | Model | Filter fields |
|------|----------|-----------|------------|-------|---------------|
| 36 | `ListMessages` | `Find` | `messages` | `Message` | — |
| 64 | `UnreadCount` | `CountDocuments` | `messages` | `Message` | — |
| 88 | `MarkRead` | `UpdateOne` | `messages` | `Message` | — |

### `internal/api/handlers/plans.go`

| Line | Function | Operation | Collection | Model | Filter fields |
|------|----------|-----------|------------|-------|---------------|
| 48 | `ListPlans` | `Find` | `plans` | `Plan` | — |
| 66 | `ListPlans` | `Aggregate` | `tenants` | `Tenant` | — |
| 93 | `ListPlans` | `CountDocuments` | `plans` | `Plan` | — |
| 106 | `GetPlan` | `FindOne` | `plans` | `Plan` | `_id` |
| 119 | `ListEntitlementKeys` | `Find` | `plans` | `Plan` | — |
| 248 | `CreatePlan` | `CountDocuments` | `plans` | `Plan` | `name` |
| 286 | `CreatePlan` | `InsertOne` | `plans` | `Plan` | — |
| 314 | `UpdatePlan` | `FindOne` | `plans` | `Plan` | `_id` |
| 341 | `UpdatePlan` | `CountDocuments` | `plans` | `Plan` | `name`, `_id` |
| 355 | `UpdatePlan` | `DeleteMany` | `stripe_mappings` | `StripeMapping` | `entityType` |
| 391 | `UpdatePlan` | `FindOne` | `plans` | `Plan` | `_id` |
| 392 | `UpdatePlan` | `CountDocuments` | `tenants` | `Tenant` | `planId` |
| 426 | `DeletePlan` | `FindOne` | `plans` | `Plan` | `_id` |
| 440 | `DeletePlan` | `CountDocuments` | `tenants` | `Tenant` | `planId` |
| 446 | `DeletePlan` | `DeleteOne` | `plans` | `Plan` | `_id` |
| 467 | `ArchivePlan` | `FindOne` | `plans` | `Plan` | `_id` |
| 499 | `UnarchivePlan` | `FindOne` | `plans` | `Plan` | `_id` |
| 546 | `AssignPlan` | `FindOne` | `tenants` | `Tenant` | `_id` |
| 568 | `AssignPlan` | `FindOne` | `plans` | `Plan` | `_id` |
| 597 | `AssignPlan` | `FindOne` | `plans` | `Plan` | `_id` |
| 673 | `ListPlansPublic` | `FindOne` | `tenants` | `Tenant` | `_id` |
| 684 | `ListPlansPublic` | `CountDocuments` | `tenant_memberships` | `TenantMembership` | `userId`, `tenantId` |
| 703 | `ListPlansPublic` | `Find` | `plans` | `Plan` | — |
| 783 | `lookupPlanForTenant` | `FindOne` | `plans` | `Plan` | `_id` |
| 786 | `lookupPlanForTenant` | `FindOne` | `plans` | `Plan` | `isSystem` |

### `internal/api/handlers/promotions.go`

| Line | Function | Operation | Collection | Model | Filter fields |
|------|----------|-----------|------------|-------|---------------|
| 115 | `buildProductNameMap` | `Find` | `stripe_mappings` | `StripeMapping` | — |
| 144 | `buildProductNameMap` | `Find` | `plans` | `Plan` | `_id` |
| 162 | `buildProductNameMap` | `Find` | `credit_bundles` | `CreditBundle` | `_id` |
| 194 | `ListEligibleProducts` | `Find` | `plans` | `Plan` | `isArchived` |
| 220 | `ListEligibleProducts` | `Find` | `credit_bundles` | `CreditBundle` | `isActive` |
| 374 | `resolveStripeProducts` | `FindOne` | `plans` | `Plan` | `_id` |
| 412 | `resolveStripeProducts` | `FindOne` | `stripe_mappings` | `StripeMapping` | `entityType`, `entityId` |
| 422 | `resolveStripeProducts` | `FindOne` | `credit_bundles` | `CreditBundle` | `_id` |
| 432 | `resolveStripeProducts` | `FindOne` | `stripe_mappings` | `StripeMapping` | `entityType`, `entityId` |

### `internal/api/handlers/tenant.go`

| Line | Function | Operation | Collection | Model | Filter fields |
|------|----------|-----------|------------|-------|---------------|
| 74 | `ListMembers` | `Find` | `tenant_memberships` | `TenantMembership` | `tenantId` |
| 94 | `ListMembers` | `Find` | `users` | `User` | `_id` |
| 171 | `InviteMember` | `FindOne` | `users` | `User` | `email` |
| 172 | `InviteMember` | `CountDocuments` | `tenant_memberships` | `TenantMembership` | `userId`, `tenantId` |
| 183 | `InviteMember` | `CountDocuments` | `invitations` | `Invitation` | `tenantId`, `email`, `status`, `expiresAt` |
| 197 | `InviteMember` | `FindOne` | `plans` | `Plan` | `_id` |
| 199 | `InviteMember` | `FindOne` | `plans` | `Plan` | `isSystem` |
| 219 | `InviteMember` | `InsertOne` | `invitations` | `Invitation` | — |
| 224 | `InviteMember` | `CountDocuments` | `tenant_memberships` | `TenantMembership` | `tenantId` |
| 225 | `InviteMember` | `CountDocuments` | `invitations` | `Invitation` | `tenantId`, `status`, `expiresAt` |
| 232 | `InviteMember` | `DeleteOne` | `invitations` | `Invitation` | `_id` |
| 241 | `InviteMember` | `InsertOne` | `invitations` | `Invitation` | — |
| 249 | `InviteMember` | `CountDocuments` | `tenant_memberships` | `TenantMembership` | `tenantId` |
| 257 | `InviteMember` | `UpdateOne` | `tenants` | `Tenant` | `_id`, `seatQuantity`, `updatedAt` |
| 316 | `RemoveMember` | `FindOne` | `tenant_memberships` | `TenantMembership` | `userId`, `tenantId` |
| 336 | `RemoveMember` | `DeleteOne` | `tenant_memberships` | `TenantMembership` | `_id` |
| 344 | `RemoveMember` | `FindOne` | `plans` | `Plan` | `_id` |
| 345 | `RemoveMember` | `CountDocuments` | `tenant_memberships` | `TenantMembership` | `tenantId` |
| 356 | `RemoveMember` | `UpdateOne` | `tenants` | `Tenant` | `_id`, `seatQuantity`, `updatedAt` |
| 422 | `ChangeRole` | `UpdateOne` | `tenant_memberships` | `TenantMembership` | — |
| 474 | `TransferOwnership` | `CountDocuments` | `tenant_memberships` | `TenantMembership` | `userId`, `tenantId` |
| 486 | `TransferOwnership` | `UpdateOne` | `tenant_memberships` | `TenantMembership` | — |
| 496 | `TransferOwnership` | `UpdateOne` | `tenant_memberships` | `TenantMembership` | — |
| 555 | `GetActivity` | `Find` | `system_logs` | `SystemLog` | — |
| 568 | `GetActivity` | `CountDocuments` | `system_logs` | `SystemLog` | — |
| 600 | `UpdateTenantSettings` | `UpdateOne` | `tenants` | `Tenant` | `_id` |

### `internal/api/handlers/usage.go`

| Line | Function | Operation | Collection | Model | Filter fields |
|------|----------|-----------|------------|-------|---------------|
| 90 | `RecordUsage` | `UpdateOne` | `tenants` | `Tenant` | — |
| 100 | `RecordUsage` | `UpdateOne` | `tenants` | `Tenant` | — |
| 114 | `RecordUsage` | `InsertOne` | `usage_events` | `UsageEvent` | — |
| 169 | `GetSummary` | `Aggregate` | `usage_events` | `UsageEvent` | — |
| 196 | `GetSummary` | `FindOne` | `tenants` | `Tenant` | `_id` |

### `internal/api/handlers/webhook.go`

| Line | Function | Operation | Collection | Model | Filter fields |
|------|----------|-----------|------------|-------|---------------|
| 132 | `HandleWebhook` | `DeleteOne` | `webhook_events` | `WebhookEvent` | `eventId` |
| 138 | `HandleWebhook` | `UpdateOne` | `webhook_events` | `WebhookEvent` | `eventId`, `status` |
| 162 | `handleCheckoutCompleted` | `FindOne` | `tenants` | `Tenant` | `_id` |
| 174 | `handleCheckoutCompleted` | `FindOne` | `tenants` | `Tenant` | `stripeCustomerId`, `_id` |
| 193 | `handleCheckoutCompleted` | `FindOne` | `plans` | `Plan` | `_id` |
| 227 | `handleCheckoutCompleted` | `UpdateOne` | `users` | `User` | `_id`, `trialUsedAt` |
| 243 | `handleCheckoutCompleted` | `UpdateOne` | `tenants` | `Tenant` | `_id` |
| 306 | `handleCheckoutCompleted` | `FindOne` | `credit_bundles` | `CreditBundle` | `_id` |
| 312 | `handleCheckoutCompleted` | `UpdateOne` | `tenants` | `Tenant` | `_id`, `purchasedCredits`, `updatedAt` |
| 375 | `handleInvoicePaid` | `FindOne` | `tenants` | `Tenant` | `stripeSubscriptionId` |
| 381 | `handleInvoicePaid` | `UpdateOne` | `tenants` | `Tenant` | `_id`, `billingStatus`, `updatedAt` |
| 391 | `handleInvoicePaid` | `FindOne` | `plans` | `Plan` | `_id` |
| 393 | `handleInvoicePaid` | `UpdateOne` | `tenants` | `Tenant` | `_id`, `subscriptionCredits` |
| 399 | `handleInvoicePaid` | `UpdateOne` | `tenants` | `Tenant` | `_id`, `subscriptionCredits` |
| 420 | `handleInvoicePaid` | `FindOne` | `tenant_memberships` | `TenantMembership` | `tenantId`, `role` |
| 427 | `handleInvoicePaid` | `FindOne` | `plans` | `Plan` | `_id` |
| 466 | `handleInvoicePaymentFailed` | `FindOne` | `tenants` | `Tenant` | `stripeSubscriptionId` |
| 472 | `handleInvoicePaymentFailed` | `UpdateOne` | `tenants` | `Tenant` | `_id`, `billingStatus`, `updatedAt` |
| 480 | `handleInvoicePaymentFailed` | `Find` | `tenant_memberships` | `TenantMembership` | `tenantId` |
| 499 | `handleInvoicePaymentFailed` | `InsertOne` | `messages` | `Message` | — |
| 531 | `handleSubscriptionUpdated` | `FindOne` | `tenants` | `Tenant` | `stripeSubscriptionId` |
| 563 | `handleSubscriptionUpdated` | `FindOne` | `plans` | `Plan` | `_id` |
| 578 | `handleSubscriptionUpdated` | `UpdateOne` | `tenants` | `Tenant` | `_id` |
| 593 | `handleSubscriptionDeleted` | `FindOne` | `tenants` | `Tenant` | `stripeSubscriptionId` |
| 599 | `handleSubscriptionDeleted` | `FindOne` | `plans` | `Plan` | `isSystem` |
| 615 | `handleSubscriptionDeleted` | `UpdateOne` | `tenants` | `Tenant` | `_id` |
| 655 | `handleChargeRefunded` | `FindOne` | `tenants` | `Tenant` | `stripeCustomerId` |
| 668 | `handleChargeRefunded` | `FindOne` | `tenant_memberships` | `TenantMembership` | `tenantId`, `role` |
| 706 | `handleDisputeCreated` | `FindOne` | `tenants` | `Tenant` | `stripeCustomerId` |
| 712 | `handleDisputeCreated` | `UpdateOne` | `tenants` | `Tenant` | `_id`, `billingStatus`, `updatedAt` |
| 751 | `handleDisputeClosed` | `FindOne` | `tenants` | `Tenant` | `stripeCustomerId` |
| 759 | `handleDisputeClosed` | `UpdateOne` | `tenants` | `Tenant` | `_id`, `billingStatus`, `updatedAt` |
| 821 | `recordTransaction` | `InsertOne` | `financial_transactions` | `FinancialTransaction` | — |

### `internal/api/handlers/webhooks.go`

| Line | Function | Operation | Collection | Model | Filter fields |
|------|----------|-----------|------------|-------|---------------|
| 44 | `ListWebhooks` | `Find` | `webhooks` | `Webhook` | `isActive` |
| 70 | `ListWebhooks` | `CountDocuments` | `webhook_deliveries` | `WebhookDelivery` | `webhookId`, `createdAt` |
| 78 | `ListWebhooks` | `FindOne` | `webhook_deliveries` | `WebhookDelivery` | `webhookId` |
| 83 | `ListWebhooks` | `CountDocuments` | `webhooks` | `Webhook` | `isActive` |
| 96 | `GetWebhook` | `FindOne` | `webhooks` | `Webhook` | `_id`, `isActive` |
| 102 | `GetWebhook` | `Find` | `webhook_deliveries` | `WebhookDelivery` | — |
| 268 | `CreateWebhook` | `InsertOne` | `webhooks` | `Webhook` | — |
| 329 | `UpdateWebhook` | `FindOne` | `webhooks` | `Webhook` | `_id` |
| 410 | `TestWebhook` | `FindOne` | `webhooks` | `Webhook` | `_id`, `isActive` |

### `internal/configstore/seed.go`

| Line | Function | Operation | Collection | Model | Filter fields |
|------|----------|-----------|------------|-------|---------------|
| 380 | `Seed` | `FindOne` | `config_vars` | `ConfigVar` | `name` |
| 384 | `Seed` | `InsertOne` | `config_vars` | `ConfigVar` | — |

### `internal/configstore/store.go`

| Line | Function | Operation | Collection | Model | Filter fields |
|------|----------|-----------|------------|-------|---------------|
| 34 | `Load` | `Find` | `config_vars` | `ConfigVar` | — |
| 90 | `Set` | `UpdateOne` | `config_vars` | `ConfigVar` | — |
| 106 | `Reload` | `FindOne` | `config_vars` | `ConfigVar` | `name` |

### `internal/health/health.go`

| Line | Function | Operation | Collection | Model | Filter fields |
|------|----------|-----------|------------|-------|---------------|
| 135 | `registerNode` | `UpdateOne` | `system_nodes` | `SystemNode` | — |
| 162 | `heartbeat` | `UpdateOne` | `system_nodes` | `SystemNode` | — |
| 297 | `collectAndStore` | `InsertOne` | `system_metrics` | `SystemMetric` | — |

### `internal/health/query.go`

| Line | Function | Operation | Collection | Model | Filter fields |
|------|----------|-----------|------------|-------|---------------|
| 24 | `ListNodes` | `UpdateMany` | `system_nodes` | `SystemNode` | — |
| 29 | `ListNodes` | `Find` | `system_nodes` | `SystemNode` | — |
| 49 | `GetMetrics` | `Find` | `system_metrics` | `SystemMetric` | — |
| 68 | `GetAggregateMetrics` | `Find` | `system_metrics` | `SystemMetric` | — |
| 92 | `GetCurrentMetrics` | `FindOne` | `system_metrics` | `SystemMetric` | — |
| 114 | `GetIntegrationCounts24h` | `Aggregate` | `system_metrics` | `SystemMetric` | — |

### `internal/metrics/metrics.go`

| Line | Function | Operation | Collection | Model | Filter fields |
|------|----------|-----------|------------|-------|---------------|
| 144 | `isLeader` | `FindOne` | `leader_locks` | `LeaderLock` | `_id` |
| 153 | `releaseLock` | `DeleteOne` | `leader_locks` | `LeaderLock` | `_id`, `holderId` |
| 185 | `collectDaily` | `Aggregate` | `users` | `User` | — |
| 220 | `collectDaily` | `Aggregate` | `financial_transactions` | `FinancialTransaction` | — |
| 256 | `collectDaily` | `Aggregate` | `tenants` | `Tenant` | — |
| 273 | `collectDaily` | `UpdateOne` | `daily_metrics` | `DailyMetric` | — |

### `internal/middleware/auth.go`

| Line | Function | Operation | Collection | Model | Filter fields |
|------|----------|-----------|------------|-------|---------------|
| 90 | `authenticateJWT` | `FindOne` | `users` | `User` | `_id` |
| 113 | `authenticateAPIKey` | `FindOne` | `api_keys` | `APIKey` | `keyHash`, `isActive` |
| 124 | `authenticateAPIKey` | `FindOne` | `users` | `User` | `_id` |
| 135 | `authenticateAPIKey` | `FindOne` | `tenants` | `Tenant` | `isRoot` |
| 166 | `isTokenRevoked` | `CountDocuments` | `revoked_tokens` | `RevokedToken` | `tokenHash` |

### `internal/middleware/tenant.go`

| Line | Function | Operation | Collection | Model | Filter fields |
|------|----------|-----------|------------|-------|---------------|
| 51 | `RequireTenant` | `FindOne` | `tenants` | `Tenant` | `_id`, `isActive` |
| 64 | `RequireTenant` | `FindOne` | `tenant_memberships` | `TenantMembership` | `userId`, `tenantId` |
| 141 | `RequireEntitlement` | `FindOne` | `plans` | `Plan` | `_id` |

### `internal/planstore/seed.go`

| Line | Function | Operation | Collection | Model | Filter fields |
|------|----------|-----------|------------|-------|---------------|
| 19 | `Seed` | `FindOne` | `plans` | `Plan` | `isSystem` |
| 36 | `Seed` | `InsertOne` | `plans` | `Plan` | — |

### `internal/stripe/stripe.go`

| Line | Function | Operation | Collection | Model | Filter fields |
|------|----------|-----------|------------|-------|---------------|
| 82 | `GetOrCreateCustomer` | `UpdateOne` | `tenants` | `Tenant` | — |
| 100 | `GetOrCreatePrice` | `FindOne` | `stripe_mappings` | `StripeMapping` | `entityType`, `entityId` |
| 143 | `GetOrCreatePrice` | `InsertOne` | `stripe_mappings` | `StripeMapping` | — |

### `internal/syslog/syslog.go`

| Line | Function | Operation | Collection | Model | Filter fields |
|------|----------|-----------|------------|-------|---------------|
| 97 | `log` | `InsertOne` | `system_logs` | `SystemLog` | — |
| 114 | `log` | `InsertOne` | `system_logs` | `SystemLog` | — |
| 137 | `logCategorized` | `InsertOne` | `system_logs` | `SystemLog` | — |
| 154 | `logCategorized` | `InsertOne` | `system_logs` | `SystemLog` | — |
| 234 | `LogTenantActivity` | `InsertOne` | `system_logs` | `SystemLog` | — |

### `internal/telemetry/service.go`

| Line | Function | Operation | Collection | Model | Filter fields |
|------|----------|-----------|------------|-------|---------------|
| 82 | `flushLoop` | `InsertMany` | `telemetry_events` | `TelemetryEvent` | — |
| 188 | `TrackBatch` | `InsertMany` | `telemetry_events` | `TelemetryEvent` | — |
| 317 | `FunnelMetrics` | `CountDocuments` | `users` | `User` | `createdAt` |
| 329 | `FunnelMetrics` | `CountDocuments` | `telemetry_events` | `TelemetryEvent` | `eventName`, `createdAt` |
| 335 | `FunnelMetrics` | `CountDocuments` | `financial_transactions` | `FinancialTransaction` | `type`, `createdAt` |
| 341 | `FunnelMetrics` | `CountDocuments` | `telemetry_events` | `TelemetryEvent` | `eventName` |
| 429 | `RetentionCohorts` | `Aggregate` | `users` | `User` | — |
| 511 | `EngagementMetrics` | `CountDocuments` | `telemetry_events` | `TelemetryEvent` | `eventName`, `userId` |
| 572 | `computeKPIs` | `CountDocuments` | `tenants` | `Tenant` | `billingStatus`, `isActive` |
| 578 | `computeKPIs` | `CountDocuments` | `users` | `User` | — |
| 591 | `computeKPIs` | `CountDocuments` | `tenants` | `Tenant` | `canceledAt` |
| 594 | `computeKPIs` | `CountDocuments` | `tenants` | `Tenant` | `billingStatus` |
| 604 | `computeKPIs` | `CountDocuments` | `tenants` | `Tenant` | `trialUsedAt` |
| 607 | `computeKPIs` | `CountDocuments` | `tenants` | `Tenant` | `trialUsedAt` |
| 661 | `CustomEventSummary` | `CountDocuments` | `telemetry_events` | `TelemetryEvent` | — |
| 674 | `CustomEventSummary` | `Aggregate` | `telemetry_events` | `TelemetryEvent` | — |
| 710 | `ListEventTypes` | `Aggregate` | `telemetry_events` | `TelemetryEvent` | — |
| 749 | `countDistinct` | `Aggregate` | `telemetry_events` | `TelemetryEvent` | — |
| 767 | `getActiveTenantIDs` | `Find` | `tenants` | `Tenant` | `billingStatus`, `isActive`, `_id` |
| 792 | `getUserIDsForTenants` | `Find` | `tenant_memberships` | `TenantMembership` | `tenantId`, `userId` |
| 859 | `weeklyActiveUsers` | `Aggregate` | `telemetry_events` | `TelemetryEvent` | — |
| 906 | `monthlyActiveUsers` | `Aggregate` | `telemetry_events` | `TelemetryEvent` | — |
| 943 | `topCustomEvents` | `Aggregate` | `telemetry_events` | `TelemetryEvent` | — |
| 973 | `creditConsumptionTrend` | `Aggregate` | `usage_events` | `UsageEvent` | — |
| 1048 | `calculateMRR` | `Aggregate` | `tenants` | `Tenant` | — |
| 1091 | `medianTimeToFirstPurchase` | `Aggregate` | `financial_transactions` | `FinancialTransaction` | — |
| 1140 | `planDistribution` | `Aggregate` | `tenants` | `Tenant` | — |
| 1175 | `mrrTrend` | `Find` | `daily_metrics` | `DailyMetric` | `date` |
| 1210 | `subscriberTrend` | `Aggregate` | `financial_transactions` | `FinancialTransaction` | — |
| 1230 | `aggregateDailyPoints` | `Aggregate` | `telemetry_events` | `TelemetryEvent` | — |

### `internal/testutil/testutil.go`

| Line | Function | Operation | Collection | Model | Filter fields |
|------|----------|-----------|------------|-------|---------------|
| 92 | `MustConnectTestDB` | `DeleteMany` | `<unknown>` | `<unknown>` | — |
| 131 | `ConnectTestDB` | `DeleteMany` | `<unknown>` | `<unknown>` | — |
| 206 | `CleanupCollections` | `DeleteMany` | `<unknown>` | `<unknown>` | — |
| 247 | `CreateTestUser` | `InsertOne` | `users` | `User` | — |
| 269 | `CreateTestTenant` | `InsertOne` | `tenants` | `Tenant` | — |
| 282 | `CreateTestTenant` | `InsertOne` | `tenant_memberships` | `TenantMembership` | — |
| 295 | `MarkSystemInitialized` | `InsertOne` | `system_config` | `SystemConfig` | — |
| 318 | `InsertTestLogs` | `InsertOne` | `system_logs` | `SystemLog` | — |
| 329 | `CountDocuments` | `CountDocuments` | `<unknown>` | `<unknown>` | — |
| 369 | `CreateTestMembership` | `InsertOne` | `tenant_memberships` | `TenantMembership` | — |
| 393 | `CreateTestPlan` | `InsertOne` | `plans` | `Plan` | — |
| 415 | `CreateTestAPIKey` | `InsertOne` | `api_keys` | `APIKey` | — |
| 439 | `CreateTestWebhook` | `InsertOne` | `webhooks` | `Webhook` | — |
| 462 | `CreateTestInvitation` | `InsertOne` | `invitations` | `Invitation` | — |

### `internal/version/check.go`

| Line | Function | Operation | Collection | Model | Filter fields |
|------|----------|-----------|------------|-------|---------------|
| 28 | `CheckAndMigrate` | `FindOne` | `system_config` | `SystemConfig` | — |
| 49 | `CheckAndMigrate` | `UpdateOne` | `system_config` | `SystemConfig` | — |
| 64 | `sendUpgradeMessage` | `FindOne` | `tenants` | `Tenant` | `isRoot` |
| 71 | `sendUpgradeMessage` | `FindOne` | `tenant_memberships` | `TenantMembership` | `tenantId`, `role` |
| 90 | `sendUpgradeMessage` | `InsertOne` | `messages` | `Message` | — |

### `internal/webhooks/dispatcher.go`

| Line | Function | Operation | Collection | Model | Filter fields |
|------|----------|-----------|------------|-------|---------------|
| 194 | `dispatch` | `Find` | `webhooks` | `Webhook` | `events`, `isActive` |
| 287 | `deliverWithRetry` | `InsertOne` | `webhook_deliveries` | `WebhookDelivery` | — |
| 419 | `DeliverTest` | `InsertOne` | `webhook_deliveries` | `WebhookDelivery` | — |

---
_Generated by `graphify db-queries`._
