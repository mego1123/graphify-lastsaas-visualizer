# API Shapes — Backend ↔ Frontend Response Audit

**Repository**: `/home/z/my-project/repos/lastsaas`

Compares Go backend API response shapes against the
TypeScript frontend's expected response types. Each
matched endpoint is checked for:

- **Missing in Go** — the frontend expects a field the
  backend doesn't send (frontend bug waiting to happen).
- **Extra in Go** — the backend sends a field the frontend
  doesn't read (wasted bandwidth / accidental info leak).
- **Type mismatch** — both sides have the field but the
  types disagree (e.g. Go `int64` vs TS `string` for an
  ID — the classic JS precision bug).

## Summary

- TS endpoints scanned: **153**
- Go endpoints scanned: **163**
- Matched endpoints: **122**
- ✅ OK: **59**
- ⚪ Unknown Go shape: **12**
- ⚫ No Go handler: **0**
- 🔴 Missing-in-Go fields: **0**
- 🟡 Extra-in-Go fields: **58**
- 🟠 Type mismatches: **4**
- Unmatched TS endpoints: **31**
- Unmatched Go endpoints: **41**

## Comparison Table

| Endpoint | Go handler | Go struct | TS type | Missing in Go | Extra in Go | Mismatches | Status |
|----------|------------|-----------|---------|---------------|-------------|------------|--------|
| `GET /api/admin/about` | `AdminHandler.GetAbout` | (map) | `AboutInfo` | — | — | — | ✅ ok |
| `GET /api/admin/announcements` | `AnnouncementsHandler.ListAll` | (map) | `{ announcements: Announcement[] }` | — | — | — | ✅ ok |
| `POST /api/admin/announcements` | `AnnouncementsHandler.Create` | `Announcement` | `Announcement` | — | — | — | ✅ ok |
| `DELETE /api/admin/announcements/{id}` | `AnnouncementsHandler.Delete` | (map) | `(unknown)` | — | `message` | — | 🟡 extra in Go |
| `PUT /api/admin/announcements/{id}` | `AnnouncementsHandler.Update` | (map) | `(unknown)` | — | `message` | — | 🟡 extra in Go |
| `GET /api/admin/api-keys` | `APIKeysHandler.ListAPIKeys` | (map) | `{ apiKeys: APIKey[] }` | — | `total` | — | 🟡 extra in Go |
| `POST /api/admin/api-keys` | `APIKeysHandler.CreateAPIKey` | (map) | `{ apiKey: APIKey; rawKey: string }` | — | — | — | ✅ ok |
| `PUT /api/admin/branding` | `BrandingHandler.UpdateBranding` | (map) | `(unknown)` | — | `status` | — | 🟡 extra in Go |
| `POST /api/admin/branding/asset` | `BrandingHandler.UploadAsset` | (map) | `(unknown)` | — | `key`, `filename`, `contentType`, `size`, `url` | — | 🟡 extra in Go |
| `DELETE /api/admin/branding/asset/{key}` | `BrandingHandler.DeleteAsset` | (map) | `(unknown)` | — | `status` | — | 🟡 extra in Go |
| `GET /api/admin/branding/media` | `BrandingHandler.ListMedia` | (map) | `{ media: MediaItem[] }` | — | — | — | ✅ ok |
| `POST /api/admin/branding/media` | `BrandingHandler.UploadMedia` | (map) | `MediaItem` | — | — | — | ✅ ok |
| `GET /api/admin/branding/pages` | `BrandingHandler.AdminListPages` | (map) | `{ pages: CustomPage[] }` | — | — | — | ✅ ok |
| `POST /api/admin/branding/pages` | `BrandingHandler.CreatePage` | `CustomPage` | `CustomPage` | — | — | — | ✅ ok |
| `DELETE /api/admin/branding/pages/{id}` | `BrandingHandler.DeletePage` | (map) | `(unknown)` | — | `status` | — | 🟡 extra in Go |
| `PUT /api/admin/branding/pages/{id}` | `BrandingHandler.UpdatePage` | (map) | `(unknown)` | — | `status` | — | 🟡 extra in Go |
| `GET /api/admin/config` | `ConfigHandler.ListConfig` | (map) | `{ configs: ConfigVar[] }` | — | — | — | ✅ ok |
| `POST /api/admin/config` | `ConfigHandler.CreateConfig` | `ConfigVar` | `ConfigVar` | — | — | — | ✅ ok |
| `DELETE /api/admin/config/{name}` | `ConfigHandler.DeleteConfig` | (map) | `(unknown)` | — | `message` | — | 🟡 extra in Go |
| `GET /api/admin/config/{name}` | `ConfigHandler.GetConfig` | — | `ConfigVar` | — | — | — | ⚪ Go shape unknown |
| `PUT /api/admin/config/{name}` | `ConfigHandler.UpdateConfig` | — | `ConfigVar` | — | — | — | ⚪ Go shape unknown |
| `GET /api/admin/credit-bundles` | `BundlesHandler.ListBundles` | (map) | `{ bundles: CreditBundle[] }` | — | `total` | — | 🟡 extra in Go |
| `POST /api/admin/credit-bundles` | `BundlesHandler.CreateBundle` | `CreditBundle` | `CreditBundle` | — | — | — | ✅ ok |
| `GET /api/admin/dashboard` | `AdminHandler.GetDashboard` | (map) | `{ users: number; tenants: number; health: { he…` | — | `health` | — | 🟡 extra in Go |
| `GET /api/admin/entitlement-keys` | `PlansHandler.ListEntitlementKeys` | (map) | `{ keys: EntitlementKeyInfo[] }` | — | — | — | ✅ ok |
| `GET /api/admin/financial/metrics` | `BillingHandler.AdminGetMetrics` | (map) | `{ data: DailyMetricPoint[] }` | — | — | 1 | 🟠 type mismatch |
| `GET /api/admin/financial/transactions` | `BillingHandler.AdminListTransactions` | (map) | `{ transactions: FinancialTransaction[]; total:…` | — | — | — | ✅ ok |
| `GET /api/admin/health/current` | `HealthHandler.GetCurrent` | (map) | `{ metrics: SystemMetric[] }` | — | — | — | ✅ ok |
| `GET /api/admin/health/integrations` | `HealthHandler.GetIntegrations` | (map) | `{ integrations: IntegrationCheck[] }` | — | — | — | ✅ ok |
| `GET /api/admin/health/metrics` | `HealthHandler.GetMetrics` | (map) | `{ metrics: SystemMetric[]; from: string; to: s…` | — | — | — | ✅ ok |
| `GET /api/admin/health/nodes` | `HealthHandler.ListNodes` | (map) | `{ nodes: SystemNode[] }` | — | — | — | ✅ ok |
| `POST /api/admin/health/test-email` | `HealthHandler.SendTestEmail` | (map) | `{ success?: boolean; error?: string }` | — | — | — | ✅ ok |
| `GET /api/admin/logs` | `LogHandler.ListLogs` | `logListResponse` | `{ logs: SystemLog[]; total: number }` | — | — | — | ✅ ok |
| `GET /api/admin/logs/export` | `LogHandler.ExportCSV` | — | `(unknown)` | — | — | — | ⚪ Go shape unknown |
| `GET /api/admin/members` | `AdminHandler.ListRootMembers` | (map) | `{ members: TenantMember[]; invitations: Invita…` | — | — | — | ✅ ok |
| `DELETE /api/admin/members/invitations/{invitationId}` | `AdminHandler.CancelRootInvitation` | (map) | `(unknown)` | — | `message` | — | 🟡 extra in Go |
| `POST /api/admin/members/invite` | `AdminHandler.InviteRootMember` | (map) | `(unknown)` | — | `message` | — | 🟡 extra in Go |
| `DELETE /api/admin/members/{userId}` | `AdminHandler.RemoveRootMember` | (map) | `(unknown)` | — | `message` | — | 🟡 extra in Go |
| `PATCH /api/admin/members/{userId}/role` | `AdminHandler.ChangeRootMemberRole` | (map) | `(unknown)` | — | `message` | — | 🟡 extra in Go |
| `GET /api/admin/plans` | `PlansHandler.ListPlans` | (map) | `{ plans: Plan[] }` | — | `total` | — | 🟡 extra in Go |
| `POST /api/admin/plans` | `PlansHandler.CreatePlan` | `Plan` | `Plan` | — | — | — | ✅ ok |
| `GET /api/admin/pm/engagement` | `PMHandler.GetEngagement` | — | `EngagementData` | — | — | — | ⚪ Go shape unknown |
| `GET /api/admin/pm/event-definitions` | `EventDefinitionsHandler.ListEventDefinitions` | (map) | `{ definitions: EventDefinition[] }` | — | — | — | ✅ ok |
| `POST /api/admin/pm/event-definitions` | `EventDefinitionsHandler.CreateEventDefinition` | `EventDefinition` | `EventDefinition` | — | — | — | ✅ ok |
| `GET /api/admin/pm/event-definitions/sankey` | `EventDefinitionsHandler.GetSankeyData` | (map) | `SankeyData` | — | `nodes`, `links` | — | 🟡 extra in Go |
| `GET /api/admin/pm/events` | `PMHandler.GetCustomEvents` | — | `CustomEventData` | — | — | — | ⚪ Go shape unknown |
| `GET /api/admin/pm/events/types` | `PMHandler.ListEventTypes` | (map) | `{ eventTypes: EventTypeSummary[] }` | — | — | — | ✅ ok |
| `GET /api/admin/pm/funnel` | `PMHandler.GetFunnel` | — | `FunnelData` | — | — | — | ⚪ Go shape unknown |
| `GET /api/admin/pm/kpis` | `PMHandler.GetKPIs` | — | `KPIData` | — | — | — | ⚪ Go shape unknown |
| `GET /api/admin/pm/retention` | `PMHandler.GetRetention` | (map) | `{ granularity: string; periods: number; cohort…` | — | — | — | ✅ ok |
| `POST /api/admin/promotions` | `PromotionsHandler.CreatePromotion` | (map) | `{ id: string; code: string }` | — | — | — | ✅ ok |
| `POST /api/admin/promotions/deactivate` | `PromotionsHandler.DeactivatePromotion` | (map) | `(unknown)` | — | `status` | — | 🟡 extra in Go |
| `GET /api/admin/promotions/eligible-products` | `PromotionsHandler.ListEligibleProducts` | (map) | `{ items: EligibleProduct[] }` | — | — | 1 | 🟠 type mismatch |
| `POST /api/admin/promotions/update` | `PromotionsHandler.UpdatePromotion` | (map) | `(unknown)` | — | `status` | — | 🟡 extra in Go |
| `GET /api/admin/tenants` | `AdminHandler.ListTenants` | (map) | `{ tenants: TenantListItem[]; total: number; pa…` | — | — | — | ✅ ok |
| `GET /api/admin/tenants/export` | `AdminHandler.ExportTenantsCSV` | — | `(unknown)` | — | — | — | ⚪ Go shape unknown |
| `POST /api/admin/tenants/{tenantId}/cancel-subscription` | `BillingHandler.AdminCancelSubscription` | (map) | `(unknown)` | — | `message` | — | 🟡 extra in Go |
| `PATCH /api/admin/tenants/{tenantId}/plan` | `PlansHandler.AssignPlan` | (map) | `(unknown)` | — | `status` | — | 🟡 extra in Go |
| `PATCH /api/admin/tenants/{tenantId}/subscription` | `BillingHandler.AdminUpdateSubscription` | (map) | `(unknown)` | — | `message` | — | 🟡 extra in Go |
| `GET /api/admin/users` | `AdminHandler.ListUsers` | (map) | `{ users: UserListItem[]; total: number; page: …` | — | — | — | ✅ ok |
| `GET /api/admin/users/export` | `AdminHandler.ExportUsersCSV` | — | `(unknown)` | — | — | — | ⚪ Go shape unknown |
| `POST /api/admin/users/{userId}/impersonate` | `AdminHandler.ImpersonateUser` | (map) | `ImpersonationResponse` | — | — | — | ✅ ok |
| `PATCH /api/admin/users/{userId}/role/{tenantId}` | `AdminHandler.UpdateUserRole` | (map) | `(unknown)` | — | `message` | — | 🟡 extra in Go |
| `GET /api/admin/webhooks` | `WebhooksHandler.ListWebhooks` | (map) | `{ webhooks: Webhook[] }` | — | `total` | — | 🟡 extra in Go |
| `POST /api/admin/webhooks` | `WebhooksHandler.CreateWebhook` | (map) | `{ webhook: Webhook; secret: string }` | — | — | — | ✅ ok |
| `GET /api/admin/webhooks/event-types` | `WebhooksHandler.ListEventTypes` | (map) | `{ eventTypes: WebhookEventTypeInfo[] }` | — | — | — | ✅ ok |
| `GET /api/announcements` | `AnnouncementsHandler.ListPublic` | (map) | `{ announcements: Announcement[] }` | — | — | — | ✅ ok |
| `POST /api/auth/accept-invitation` | `AuthHandler.AcceptInvitation` | (map) | `(unknown)` | — | `message`, `memberships` | — | 🟡 extra in Go |
| `POST /api/auth/change-password` | `AuthHandler.ChangePassword` | (map) | `(unknown)` | — | `message` | — | 🟡 extra in Go |
| `POST /api/auth/complete-onboarding` | `AuthHandler.CompleteOnboarding` | (map) | `(unknown)` | — | `message` | — | 🟡 extra in Go |
| `POST /api/auth/delete-account` | `AuthHandler.DeleteAccount` | (map) | `(unknown)` | — | `message` | — | 🟡 extra in Go |
| `POST /api/auth/exchange-code` | `AuthHandler.ExchangeCode` | (map) | `{ accessToken?: string; refreshToken?: string;…` | — | — | — | ✅ ok |
| `GET /api/auth/export-data` | `AuthHandler.ExportData` | — | `(unknown)` | — | — | — | ⚪ Go shape unknown |
| `POST /api/auth/forgot-password` | `AuthHandler.ForgotPassword` | (map) | `(unknown)` | — | `message` | — | 🟡 extra in Go |
| `POST /api/auth/login` | `AuthHandler.Login` | `MFARequiredResponse` | `AuthResponse | MFARequiredResponse` | — | — | — | ✅ ok |
| `POST /api/auth/logout` | `AuthHandler.Logout` | (map) | `(unknown)` | — | `message` | — | 🟡 extra in Go |
| `POST /api/auth/magic-link` | `AuthHandler.MagicLinkRequest` | (map) | `(unknown)` | — | `message` | — | 🟡 extra in Go |
| `POST /api/auth/magic-link/verify` | `AuthHandler.MagicLinkVerify` | `MFARequiredResponse` | `AuthResponse | MFARequiredResponse` | — | — | — | ✅ ok |
| `GET /api/auth/me` | `AuthHandler.GetMe` | (map) | `{ user: import('../types').User; memberships: …` | — | — | — | ✅ ok |
| `POST /api/auth/mfa/challenge` | `AuthHandler.MFAChallenge` | `AuthResponse` | `AuthResponse` | — | — | — | ✅ ok |
| `POST /api/auth/mfa/disable` | `AuthHandler.MFADisable` | (map) | `(unknown)` | — | `message` | — | 🟡 extra in Go |
| `POST /api/auth/mfa/regenerate-codes` | `AuthHandler.MFARegenerateRecoveryCodes` | (map) | `{ recoveryCodes: string[] }` | — | — | — | ✅ ok |
| `POST /api/auth/mfa/setup` | `AuthHandler.MFASetup` | (map) | `{ secret: string; qrCodeUrl: string }` | — | — | — | ✅ ok |
| `POST /api/auth/mfa/verify-setup` | `AuthHandler.MFAVerifySetup` | (map) | `{ recoveryCodes: string[] }` | — | `message` | — | 🟡 extra in Go |
| `PATCH /api/auth/preferences` | `AuthHandler.UpdatePreferences` | (map) | `(unknown)` | — | `message` | — | 🟡 extra in Go |
| `GET /api/auth/providers` | `AuthHandler.GetProviders` | — | `AuthProviders` | — | — | — | ⚪ Go shape unknown |
| `POST /api/auth/refresh` | `AuthHandler.Refresh` | `AuthResponse` | `AuthResponse` | — | — | — | ✅ ok |
| `POST /api/auth/refresh` | `AuthHandler.Refresh` | `AuthResponse` | `AuthResponse` | — | — | — | ✅ ok |
| `POST /api/auth/register` | `AuthHandler.Register` | `AuthResponse` | `AuthResponse` | — | — | — | ✅ ok |
| `POST /api/auth/resend-verification` | `AuthHandler.ResendVerification` | (map) | `(unknown)` | — | `message` | — | 🟡 extra in Go |
| `POST /api/auth/reset-password` | `AuthHandler.ResetPassword` | (map) | `(unknown)` | — | `message` | — | 🟡 extra in Go |
| `DELETE /api/auth/sessions` | `AuthHandler.RevokeAllSessions` | (map) | `(unknown)` | — | `message` | — | 🟡 extra in Go |
| `GET /api/auth/sessions` | `AuthHandler.ListSessions` | (map) | `{ sessions: ActiveSession[] }` | — | — | — | ✅ ok |
| `DELETE /api/auth/sessions/{id}` | `AuthHandler.RevokeSession` | (map) | `(unknown)` | — | `message` | — | 🟡 extra in Go |
| `POST /api/auth/verify-email` | `AuthHandler.VerifyEmail` | (map) | `(unknown)` | — | `message` | — | 🟡 extra in Go |
| `POST /api/billing/cancel` | `BillingHandler.CancelSubscription` | (map) | `{ message: string; currentPeriodEnd?: string }` | — | — | — | ✅ ok |
| `POST /api/billing/checkout` | `BillingHandler.Checkout` | (map) | `{ checkoutUrl?: string; waived?: boolean }` | — | — | — | ✅ ok |
| `GET /api/billing/config` | `BillingHandler.GetConfig` | (map) | `{ publishableKey: string }` | — | — | — | ✅ ok |
| `POST /api/billing/portal` | `BillingHandler.Portal` | (map) | `{ portalUrl: string }` | — | — | — | ✅ ok |
| `GET /api/billing/transactions` | `BillingHandler.ListTransactions` | (map) | `{ transactions: FinancialTransaction[]; total:…` | — | — | — | ✅ ok |
| `GET /api/billing/transactions/{id}/invoice` | `BillingHandler.GetInvoice` | (map) | `{ transaction: FinancialTransaction; tenant: {…` | — | — | — | ✅ ok |
| `GET /api/billing/transactions/{id}/invoice/pdf` | `BillingHandler.GetInvoicePDF` | — | `(unknown)` | — | — | — | ⚪ Go shape unknown |
| `GET /api/bootstrap/status` | `BootstrapHandler.Status` | `bootstrapStatusResponse` | `{ initialized: boolean }` | — | — | — | ✅ ok |
| `GET /api/branding` | `BrandingHandler.GetBranding` | (map) | `BrandingConfig` | — | — | — | ✅ ok |
| `GET /api/branding/page/{slug}` | `BrandingHandler.GetPublicPage` | `CustomPage` | `CustomPage` | — | — | — | ✅ ok |
| `GET /api/branding/pages` | `BrandingHandler.ListPublicPages` | (map) | `{ pages: CustomPage[] }` | — | — | — | ✅ ok |
| `GET /api/credit-bundles` | `BundlesHandler.ListBundlesPublic` | (map) | `{ bundles: CreditBundle[] }` | — | — | — | ✅ ok |
| `GET /api/messages` | `MessageHandler.ListMessages` | (map) | `{ messages: Message[] }` | — | — | — | ✅ ok |
| `GET /api/messages/unread-count` | `MessageHandler.UnreadCount` | (map) | `{ count: number }` | — | — | — | ✅ ok |
| `GET /api/plans` | `PlansHandler.ListPlansPublic` | (map) | `PublicPlansResponse` | — | — | — | ✅ ok |
| `POST /api/telemetry/events` | `TelemetryHandler.TrackAuthenticated` | (map) | `(unknown)` | — | `status` | — | 🟡 extra in Go |
| `POST /api/telemetry/events/batch` | `TelemetryHandler.TrackBatch` | (map) | `(unknown)` | — | `status`, `tracked` | — | 🟡 extra in Go |
| `POST /api/telemetry/track` | `TelemetryHandler.TrackAnonymous` | (map) | `(unknown)` | — | `status` | — | 🟡 extra in Go |
| `GET /api/tenant/activity` | `TenantHandler.GetActivity` | (map) | `{ logs: ActivityLogEntry[]; total: number }` | — | `page`, `limit` | 1 | 🟠 type mismatch |
| `GET /api/tenant/members` | `TenantHandler.ListMembers` | (map) | `{ members: TenantMember[] }` | — | — | — | ✅ ok |
| `POST /api/tenant/members/invite` | `TenantHandler.InviteMember` | (map) | `(unknown)` | — | `error`, `code`, `userLimit` | — | 🟡 extra in Go |
| `DELETE /api/tenant/members/{userId}` | `TenantHandler.RemoveMember` | (map) | `(unknown)` | — | `message` | — | 🟡 extra in Go |
| `PATCH /api/tenant/members/{userId}/role` | `TenantHandler.ChangeRole` | (map) | `(unknown)` | — | `message` | — | 🟡 extra in Go |
| `POST /api/tenant/members/{userId}/transfer-ownership` | `TenantHandler.TransferOwnership` | (map) | `(unknown)` | — | `message` | — | 🟡 extra in Go |
| `PATCH /api/tenant/settings` | `TenantHandler.UpdateTenantSettings` | (map) | `(unknown)` | — | `message` | — | 🟡 extra in Go |
| `POST /api/usage/record` | `UsageHandler.RecordUsage` | (map) | `{ id: string; type: string; quantity: number }` | — | — | — | ✅ ok |
| `GET /api/usage/summary` | `UsageHandler.GetSummary` | (map) | `UsageSummary` | — | — | 1 | 🟠 type mismatch |

## Problematic Endpoints — Detail

### `DELETE /api/admin/announcements/{id}`

- **Status**: 🟡 extra in Go
- **Go handler**: `AnnouncementsHandler.Delete` (`backend/internal/api/handlers/announcements.go`)
- **Go response**: anonymous `map[string]interface{}` literal
- **TS response type**: `(unknown)`

| Field | Go type | TS type | Notes |
|------|---------|---------|-------|
| `message` | `string` | `_(missing)_` | 🟡 extra in Go |

### `PUT /api/admin/announcements/{id}`

- **Status**: 🟡 extra in Go
- **Go handler**: `AnnouncementsHandler.Update` (`backend/internal/api/handlers/announcements.go`)
- **Go response**: anonymous `map[string]interface{}` literal
- **TS response type**: `(unknown)`

| Field | Go type | TS type | Notes |
|------|---------|---------|-------|
| `message` | `string` | `_(missing)_` | 🟡 extra in Go |

### `GET /api/admin/api-keys`

- **Status**: 🟡 extra in Go
- **Go handler**: `APIKeysHandler.ListAPIKeys` (`backend/internal/api/handlers/apikeys.go`)
- **Go response**: anonymous `map[string]interface{}` literal
- **TS response type**: `{ apiKeys: APIKey[] }`

| Field | Go type | TS type | Notes |
|------|---------|---------|-------|
| `apiKeys` | `[]models.APIKey` | `APIKey[]` |  |
| `total` | `unknown` | `_(missing)_` | 🟡 extra in Go |

### `PUT /api/admin/branding`

- **Status**: 🟡 extra in Go
- **Go handler**: `BrandingHandler.UpdateBranding` (`backend/internal/api/handlers/branding.go`)
- **Go response**: anonymous `map[string]interface{}` literal
- **TS response type**: `(unknown)`

| Field | Go type | TS type | Notes |
|------|---------|---------|-------|
| `status` | `string` | `_(missing)_` | 🟡 extra in Go |

### `POST /api/admin/branding/asset`

- **Status**: 🟡 extra in Go
- **Go handler**: `BrandingHandler.UploadAsset` (`backend/internal/api/handlers/branding.go`)
- **Go response**: anonymous `map[string]interface{}` literal
- **TS response type**: `(unknown)`

| Field | Go type | TS type | Notes |
|------|---------|---------|-------|
| `contentType` | `unknown` | `_(missing)_` | 🟡 extra in Go |
| `filename` | `unknown` | `_(missing)_` | 🟡 extra in Go |
| `key` | `unknown` | `_(missing)_` | 🟡 extra in Go |
| `size` | `unknown` | `_(missing)_` | 🟡 extra in Go |
| `url` | `unknown` | `_(missing)_` | 🟡 extra in Go |

### `DELETE /api/admin/branding/asset/{key}`

- **Status**: 🟡 extra in Go
- **Go handler**: `BrandingHandler.DeleteAsset` (`backend/internal/api/handlers/branding.go`)
- **Go response**: anonymous `map[string]interface{}` literal
- **TS response type**: `(unknown)`

| Field | Go type | TS type | Notes |
|------|---------|---------|-------|
| `status` | `string` | `_(missing)_` | 🟡 extra in Go |

### `DELETE /api/admin/branding/pages/{id}`

- **Status**: 🟡 extra in Go
- **Go handler**: `BrandingHandler.DeletePage` (`backend/internal/api/handlers/branding.go`)
- **Go response**: anonymous `map[string]interface{}` literal
- **TS response type**: `(unknown)`

| Field | Go type | TS type | Notes |
|------|---------|---------|-------|
| `status` | `string` | `_(missing)_` | 🟡 extra in Go |

### `PUT /api/admin/branding/pages/{id}`

- **Status**: 🟡 extra in Go
- **Go handler**: `BrandingHandler.UpdatePage` (`backend/internal/api/handlers/branding.go`)
- **Go response**: anonymous `map[string]interface{}` literal
- **TS response type**: `(unknown)`

| Field | Go type | TS type | Notes |
|------|---------|---------|-------|
| `status` | `string` | `_(missing)_` | 🟡 extra in Go |

### `DELETE /api/admin/config/{name}`

- **Status**: 🟡 extra in Go
- **Go handler**: `ConfigHandler.DeleteConfig` (`backend/internal/api/handlers/config.go`)
- **Go response**: anonymous `map[string]interface{}` literal
- **TS response type**: `(unknown)`

| Field | Go type | TS type | Notes |
|------|---------|---------|-------|
| `message` | `string` | `_(missing)_` | 🟡 extra in Go |

### `GET /api/admin/credit-bundles`

- **Status**: 🟡 extra in Go
- **Go handler**: `BundlesHandler.ListBundles` (`backend/internal/api/handlers/bundles.go`)
- **Go response**: anonymous `map[string]interface{}` literal
- **TS response type**: `{ bundles: CreditBundle[] }`

| Field | Go type | TS type | Notes |
|------|---------|---------|-------|
| `bundles` | `[]models.CreditBundle` | `CreditBundle[]` |  |
| `total` | `unknown` | `_(missing)_` | 🟡 extra in Go |

### `GET /api/admin/dashboard`

- **Status**: 🟡 extra in Go
- **Go handler**: `AdminHandler.GetDashboard` (`backend/internal/api/handlers/admin.go`)
- **Go response**: anonymous `map[string]interface{}` literal
- **TS response type**: `{ users: number; tenants: number; health: { healthy: boolean; issues: string[] } }`

| Field | Go type | TS type | Notes |
|------|---------|---------|-------|
| `health` | `unknown` | `_(missing)_` | 🟡 extra in Go |
| `tenants` | `unknown` | `number` |  |
| `users` | `unknown` | `number` |  |

### `DELETE /api/admin/members/invitations/{invitationId}`

- **Status**: 🟡 extra in Go
- **Go handler**: `AdminHandler.CancelRootInvitation` (`backend/internal/api/handlers/admin.go`)
- **Go response**: anonymous `map[string]interface{}` literal
- **TS response type**: `(unknown)`

| Field | Go type | TS type | Notes |
|------|---------|---------|-------|
| `message` | `string` | `_(missing)_` | 🟡 extra in Go |

### `POST /api/admin/members/invite`

- **Status**: 🟡 extra in Go
- **Go handler**: `AdminHandler.InviteRootMember` (`backend/internal/api/handlers/admin.go`)
- **Go response**: anonymous `map[string]interface{}` literal
- **TS response type**: `(unknown)`

| Field | Go type | TS type | Notes |
|------|---------|---------|-------|
| `message` | `string` | `_(missing)_` | 🟡 extra in Go |

### `DELETE /api/admin/members/{userId}`

- **Status**: 🟡 extra in Go
- **Go handler**: `AdminHandler.RemoveRootMember` (`backend/internal/api/handlers/admin.go`)
- **Go response**: anonymous `map[string]interface{}` literal
- **TS response type**: `(unknown)`

| Field | Go type | TS type | Notes |
|------|---------|---------|-------|
| `message` | `string` | `_(missing)_` | 🟡 extra in Go |

### `PATCH /api/admin/members/{userId}/role`

- **Status**: 🟡 extra in Go
- **Go handler**: `AdminHandler.ChangeRootMemberRole` (`backend/internal/api/handlers/admin.go`)
- **Go response**: anonymous `map[string]interface{}` literal
- **TS response type**: `(unknown)`

| Field | Go type | TS type | Notes |
|------|---------|---------|-------|
| `message` | `string` | `_(missing)_` | 🟡 extra in Go |

### `GET /api/admin/plans`

- **Status**: 🟡 extra in Go
- **Go handler**: `PlansHandler.ListPlans` (`backend/internal/api/handlers/plans.go`)
- **Go response**: anonymous `map[string]interface{}` literal
- **TS response type**: `{ plans: Plan[] }`

| Field | Go type | TS type | Notes |
|------|---------|---------|-------|
| `plans` | `unknown` | `Plan[]` |  |
| `total` | `unknown` | `_(missing)_` | 🟡 extra in Go |

### `GET /api/admin/pm/event-definitions/sankey`

- **Status**: 🟡 extra in Go
- **Go handler**: `EventDefinitionsHandler.GetSankeyData` (`backend/internal/api/handlers/event_definitions.go`)
- **Go response**: anonymous `map[string]interface{}` literal
- **TS response type**: `SankeyData`

| Field | Go type | TS type | Notes |
|------|---------|---------|-------|
| `hasDependencies` | `unknown` | `boolean` |  |
| `links` | `[]interface` | `_(missing)_` | 🟡 extra in Go |
| `nodes` | `[]interface` | `_(missing)_` | 🟡 extra in Go |

### `POST /api/admin/promotions/deactivate`

- **Status**: 🟡 extra in Go
- **Go handler**: `PromotionsHandler.DeactivatePromotion` (`backend/internal/api/handlers/promotions.go`)
- **Go response**: anonymous `map[string]interface{}` literal
- **TS response type**: `(unknown)`

| Field | Go type | TS type | Notes |
|------|---------|---------|-------|
| `status` | `string` | `_(missing)_` | 🟡 extra in Go |

### `POST /api/admin/promotions/update`

- **Status**: 🟡 extra in Go
- **Go handler**: `PromotionsHandler.UpdatePromotion` (`backend/internal/api/handlers/promotions.go`)
- **Go response**: anonymous `map[string]interface{}` literal
- **TS response type**: `(unknown)`

| Field | Go type | TS type | Notes |
|------|---------|---------|-------|
| `status` | `string` | `_(missing)_` | 🟡 extra in Go |

### `POST /api/admin/tenants/{tenantId}/cancel-subscription`

- **Status**: 🟡 extra in Go
- **Go handler**: `BillingHandler.AdminCancelSubscription` (`backend/internal/api/handlers/billing.go`)
- **Go response**: anonymous `map[string]interface{}` literal
- **TS response type**: `(unknown)`

| Field | Go type | TS type | Notes |
|------|---------|---------|-------|
| `message` | `string` | `_(missing)_` | 🟡 extra in Go |

### `PATCH /api/admin/tenants/{tenantId}/plan`

- **Status**: 🟡 extra in Go
- **Go handler**: `PlansHandler.AssignPlan` (`backend/internal/api/handlers/plans.go`)
- **Go response**: anonymous `map[string]interface{}` literal
- **TS response type**: `(unknown)`

| Field | Go type | TS type | Notes |
|------|---------|---------|-------|
| `status` | `string` | `_(missing)_` | 🟡 extra in Go |

### `PATCH /api/admin/tenants/{tenantId}/subscription`

- **Status**: 🟡 extra in Go
- **Go handler**: `BillingHandler.AdminUpdateSubscription` (`backend/internal/api/handlers/billing.go`)
- **Go response**: anonymous `map[string]interface{}` literal
- **TS response type**: `(unknown)`

| Field | Go type | TS type | Notes |
|------|---------|---------|-------|
| `message` | `string` | `_(missing)_` | 🟡 extra in Go |

### `PATCH /api/admin/users/{userId}/role/{tenantId}`

- **Status**: 🟡 extra in Go
- **Go handler**: `AdminHandler.UpdateUserRole` (`backend/internal/api/handlers/admin.go`)
- **Go response**: anonymous `map[string]interface{}` literal
- **TS response type**: `(unknown)`

| Field | Go type | TS type | Notes |
|------|---------|---------|-------|
| `message` | `string` | `_(missing)_` | 🟡 extra in Go |

### `GET /api/admin/webhooks`

- **Status**: 🟡 extra in Go
- **Go handler**: `WebhooksHandler.ListWebhooks` (`backend/internal/api/handlers/webhooks.go`)
- **Go response**: anonymous `map[string]interface{}` literal
- **TS response type**: `{ webhooks: Webhook[] }`

| Field | Go type | TS type | Notes |
|------|---------|---------|-------|
| `total` | `unknown` | `_(missing)_` | 🟡 extra in Go |
| `webhooks` | `unknown` | `Webhook[]` |  |

### `POST /api/auth/accept-invitation`

- **Status**: 🟡 extra in Go
- **Go handler**: `AuthHandler.AcceptInvitation` (`backend/internal/api/handlers/auth.go`)
- **Go response**: anonymous `map[string]interface{}` literal
- **TS response type**: `(unknown)`

| Field | Go type | TS type | Notes |
|------|---------|---------|-------|
| `memberships` | `unknown` | `_(missing)_` | 🟡 extra in Go |
| `message` | `string` | `_(missing)_` | 🟡 extra in Go |

### `POST /api/auth/change-password`

- **Status**: 🟡 extra in Go
- **Go handler**: `AuthHandler.ChangePassword` (`backend/internal/api/handlers/auth.go`)
- **Go response**: anonymous `map[string]interface{}` literal
- **TS response type**: `(unknown)`

| Field | Go type | TS type | Notes |
|------|---------|---------|-------|
| `message` | `string` | `_(missing)_` | 🟡 extra in Go |

### `POST /api/auth/complete-onboarding`

- **Status**: 🟡 extra in Go
- **Go handler**: `AuthHandler.CompleteOnboarding` (`backend/internal/api/handlers/auth.go`)
- **Go response**: anonymous `map[string]interface{}` literal
- **TS response type**: `(unknown)`

| Field | Go type | TS type | Notes |
|------|---------|---------|-------|
| `message` | `string` | `_(missing)_` | 🟡 extra in Go |

### `POST /api/auth/delete-account`

- **Status**: 🟡 extra in Go
- **Go handler**: `AuthHandler.DeleteAccount` (`backend/internal/api/handlers/auth.go`)
- **Go response**: anonymous `map[string]interface{}` literal
- **TS response type**: `(unknown)`

| Field | Go type | TS type | Notes |
|------|---------|---------|-------|
| `message` | `string` | `_(missing)_` | 🟡 extra in Go |

### `POST /api/auth/forgot-password`

- **Status**: 🟡 extra in Go
- **Go handler**: `AuthHandler.ForgotPassword` (`backend/internal/api/handlers/auth.go`)
- **Go response**: anonymous `map[string]interface{}` literal
- **TS response type**: `(unknown)`

| Field | Go type | TS type | Notes |
|------|---------|---------|-------|
| `message` | `string` | `_(missing)_` | 🟡 extra in Go |

### `POST /api/auth/logout`

- **Status**: 🟡 extra in Go
- **Go handler**: `AuthHandler.Logout` (`backend/internal/api/handlers/auth.go`)
- **Go response**: anonymous `map[string]interface{}` literal
- **TS response type**: `(unknown)`

| Field | Go type | TS type | Notes |
|------|---------|---------|-------|
| `message` | `string` | `_(missing)_` | 🟡 extra in Go |

### `POST /api/auth/magic-link`

- **Status**: 🟡 extra in Go
- **Go handler**: `AuthHandler.MagicLinkRequest` (`backend/internal/api/handlers/auth.go`)
- **Go response**: anonymous `map[string]interface{}` literal
- **TS response type**: `(unknown)`

| Field | Go type | TS type | Notes |
|------|---------|---------|-------|
| `message` | `string` | `_(missing)_` | 🟡 extra in Go |

### `POST /api/auth/mfa/disable`

- **Status**: 🟡 extra in Go
- **Go handler**: `AuthHandler.MFADisable` (`backend/internal/api/handlers/auth.go`)
- **Go response**: anonymous `map[string]interface{}` literal
- **TS response type**: `(unknown)`

| Field | Go type | TS type | Notes |
|------|---------|---------|-------|
| `message` | `string` | `_(missing)_` | 🟡 extra in Go |

### `POST /api/auth/mfa/verify-setup`

- **Status**: 🟡 extra in Go
- **Go handler**: `AuthHandler.MFAVerifySetup` (`backend/internal/api/handlers/auth.go`)
- **Go response**: anonymous `map[string]interface{}` literal
- **TS response type**: `{ recoveryCodes: string[] }`

| Field | Go type | TS type | Notes |
|------|---------|---------|-------|
| `message` | `string` | `_(missing)_` | 🟡 extra in Go |
| `recoveryCodes` | `unknown` | `string[]` |  |

### `PATCH /api/auth/preferences`

- **Status**: 🟡 extra in Go
- **Go handler**: `AuthHandler.UpdatePreferences` (`backend/internal/api/handlers/auth.go`)
- **Go response**: anonymous `map[string]interface{}` literal
- **TS response type**: `(unknown)`

| Field | Go type | TS type | Notes |
|------|---------|---------|-------|
| `message` | `string` | `_(missing)_` | 🟡 extra in Go |

### `POST /api/auth/resend-verification`

- **Status**: 🟡 extra in Go
- **Go handler**: `AuthHandler.ResendVerification` (`backend/internal/api/handlers/auth.go`)
- **Go response**: anonymous `map[string]interface{}` literal
- **TS response type**: `(unknown)`

| Field | Go type | TS type | Notes |
|------|---------|---------|-------|
| `message` | `string` | `_(missing)_` | 🟡 extra in Go |

### `POST /api/auth/reset-password`

- **Status**: 🟡 extra in Go
- **Go handler**: `AuthHandler.ResetPassword` (`backend/internal/api/handlers/auth.go`)
- **Go response**: anonymous `map[string]interface{}` literal
- **TS response type**: `(unknown)`

| Field | Go type | TS type | Notes |
|------|---------|---------|-------|
| `message` | `string` | `_(missing)_` | 🟡 extra in Go |

### `DELETE /api/auth/sessions`

- **Status**: 🟡 extra in Go
- **Go handler**: `AuthHandler.RevokeAllSessions` (`backend/internal/api/handlers/auth.go`)
- **Go response**: anonymous `map[string]interface{}` literal
- **TS response type**: `(unknown)`

| Field | Go type | TS type | Notes |
|------|---------|---------|-------|
| `message` | `string` | `_(missing)_` | 🟡 extra in Go |

### `DELETE /api/auth/sessions/{id}`

- **Status**: 🟡 extra in Go
- **Go handler**: `AuthHandler.RevokeSession` (`backend/internal/api/handlers/auth.go`)
- **Go response**: anonymous `map[string]interface{}` literal
- **TS response type**: `(unknown)`

| Field | Go type | TS type | Notes |
|------|---------|---------|-------|
| `message` | `string` | `_(missing)_` | 🟡 extra in Go |

### `POST /api/auth/verify-email`

- **Status**: 🟡 extra in Go
- **Go handler**: `AuthHandler.VerifyEmail` (`backend/internal/api/handlers/auth.go`)
- **Go response**: anonymous `map[string]interface{}` literal
- **TS response type**: `(unknown)`

| Field | Go type | TS type | Notes |
|------|---------|---------|-------|
| `message` | `string` | `_(missing)_` | 🟡 extra in Go |

### `POST /api/telemetry/events`

- **Status**: 🟡 extra in Go
- **Go handler**: `TelemetryHandler.TrackAuthenticated` (`backend/internal/api/handlers/telemetry.go`)
- **Go response**: anonymous `map[string]interface{}` literal
- **TS response type**: `(unknown)`

| Field | Go type | TS type | Notes |
|------|---------|---------|-------|
| `status` | `string` | `_(missing)_` | 🟡 extra in Go |

### `POST /api/telemetry/events/batch`

- **Status**: 🟡 extra in Go
- **Go handler**: `TelemetryHandler.TrackBatch` (`backend/internal/api/handlers/telemetry.go`)
- **Go response**: anonymous `map[string]interface{}` literal
- **TS response type**: `(unknown)`

| Field | Go type | TS type | Notes |
|------|---------|---------|-------|
| `status` | `string` | `_(missing)_` | 🟡 extra in Go |
| `tracked` | `unknown` | `_(missing)_` | 🟡 extra in Go |

### `POST /api/telemetry/track`

- **Status**: 🟡 extra in Go
- **Go handler**: `TelemetryHandler.TrackAnonymous` (`backend/internal/api/handlers/telemetry.go`)
- **Go response**: anonymous `map[string]interface{}` literal
- **TS response type**: `(unknown)`

| Field | Go type | TS type | Notes |
|------|---------|---------|-------|
| `status` | `string` | `_(missing)_` | 🟡 extra in Go |

### `POST /api/tenant/members/invite`

- **Status**: 🟡 extra in Go
- **Go handler**: `TenantHandler.InviteMember` (`backend/internal/api/handlers/tenant.go`)
- **Go response**: anonymous `map[string]interface{}` literal
- **TS response type**: `(unknown)`

| Field | Go type | TS type | Notes |
|------|---------|---------|-------|
| `code` | `string` | `_(missing)_` | 🟡 extra in Go |
| `error` | `unknown` | `_(missing)_` | 🟡 extra in Go |
| `userLimit` | `unknown` | `_(missing)_` | 🟡 extra in Go |

### `DELETE /api/tenant/members/{userId}`

- **Status**: 🟡 extra in Go
- **Go handler**: `TenantHandler.RemoveMember` (`backend/internal/api/handlers/tenant.go`)
- **Go response**: anonymous `map[string]interface{}` literal
- **TS response type**: `(unknown)`

| Field | Go type | TS type | Notes |
|------|---------|---------|-------|
| `message` | `string` | `_(missing)_` | 🟡 extra in Go |

### `PATCH /api/tenant/members/{userId}/role`

- **Status**: 🟡 extra in Go
- **Go handler**: `TenantHandler.ChangeRole` (`backend/internal/api/handlers/tenant.go`)
- **Go response**: anonymous `map[string]interface{}` literal
- **TS response type**: `(unknown)`

| Field | Go type | TS type | Notes |
|------|---------|---------|-------|
| `message` | `string` | `_(missing)_` | 🟡 extra in Go |

### `POST /api/tenant/members/{userId}/transfer-ownership`

- **Status**: 🟡 extra in Go
- **Go handler**: `TenantHandler.TransferOwnership` (`backend/internal/api/handlers/tenant.go`)
- **Go response**: anonymous `map[string]interface{}` literal
- **TS response type**: `(unknown)`

| Field | Go type | TS type | Notes |
|------|---------|---------|-------|
| `message` | `string` | `_(missing)_` | 🟡 extra in Go |

### `PATCH /api/tenant/settings`

- **Status**: 🟡 extra in Go
- **Go handler**: `TenantHandler.UpdateTenantSettings` (`backend/internal/api/handlers/tenant.go`)
- **Go response**: anonymous `map[string]interface{}` literal
- **TS response type**: `(unknown)`

| Field | Go type | TS type | Notes |
|------|---------|---------|-------|
| `message` | `string` | `_(missing)_` | 🟡 extra in Go |

### `GET /api/admin/financial/metrics`

- **Status**: 🟠 type mismatch
- **Go handler**: `BillingHandler.AdminGetMetrics` (`backend/internal/api/handlers/billing.go`)
- **Go response**: anonymous `map[string]interface{}` literal
- **TS response type**: `{ data: DailyMetricPoint[] }`

| Field | Go type | TS type | Notes |
|------|---------|---------|-------|
| `data` | `[]point` | `DailyMetricPoint[]` | 🟠 Go point[] vs TS DailyMetricPoint[] |

**Type mismatches:**

- `data`: Go `[]point` vs TS `DailyMetricPoint[]` — Go point[] vs TS DailyMetricPoint[]

### `GET /api/admin/promotions/eligible-products`

- **Status**: 🟠 type mismatch
- **Go handler**: `PromotionsHandler.ListEligibleProducts` (`backend/internal/api/handlers/promotions.go`)
- **Go response**: anonymous `map[string]interface{}` literal
- **TS response type**: `{ items: EligibleProduct[] }`

| Field | Go type | TS type | Notes |
|------|---------|---------|-------|
| `items` | `[]eligibleItem` | `EligibleProduct[]` | 🟠 Go eligibleItem[] vs TS EligibleProduct[] |

**Type mismatches:**

- `items`: Go `[]eligibleItem` vs TS `EligibleProduct[]` — Go eligibleItem[] vs TS EligibleProduct[]

### `GET /api/tenant/activity`

- **Status**: 🟠 type mismatch
- **Go handler**: `TenantHandler.GetActivity` (`backend/internal/api/handlers/tenant.go`)
- **Go response**: anonymous `map[string]interface{}` literal
- **TS response type**: `{ logs: ActivityLogEntry[]; total: number }`

| Field | Go type | TS type | Notes |
|------|---------|---------|-------|
| `limit` | `unknown` | `_(missing)_` | 🟡 extra in Go |
| `logs` | `[]models.SystemLog` | `ActivityLogEntry[]` | 🟠 struct name mismatch: Go SystemLog[] vs TS ActivityLogEntry[] |
| `page` | `unknown` | `_(missing)_` | 🟡 extra in Go |
| `total` | `unknown` | `number` |  |

**Type mismatches:**

- `logs`: Go `[]models.SystemLog` vs TS `ActivityLogEntry[]` — struct name mismatch: Go SystemLog[] vs TS ActivityLogEntry[]

### `GET /api/usage/summary`

- **Status**: 🟠 type mismatch
- **Go handler**: `UsageHandler.GetSummary` (`backend/internal/api/handlers/usage.go`)
- **Go response**: anonymous `map[string]interface{}` literal
- **TS response type**: `UsageSummary`

| Field | Go type | TS type | Notes |
|------|---------|---------|-------|
| `periodStart` | `unknown` | `string` |  |
| `purchasedCredits` | `unknown` | `number` |  |
| `subscriptionCredits` | `unknown` | `number` |  |
| `totalCreditsUsed` | `unknown` | `number` |  |
| `usage` | `[]usageSummaryItem` | `UsageSummaryItem[]` | 🟠 Go usageSummaryItem[] vs TS UsageSummaryItem[] |

**Type mismatches:**

- `usage`: Go `[]usageSummaryItem` vs TS `UsageSummaryItem[]` — Go usageSummaryItem[] vs TS UsageSummaryItem[]

### `GET /api/admin/config/{name}`

- **Status**: ⚪ Go shape unknown
- **Go handler**: `ConfigHandler.GetConfig` (`backend/internal/api/handlers/config.go`)
- **Go response**: _unparseable (function call or complex expression)_
- **TS response type**: `ConfigVar`

| Field | Go type | TS type | Notes |
|------|---------|---------|-------|
| `createdAt` | `_(missing)_` | `string` | 🔴 missing in Go |
| `description` | `_(missing)_` | `string` | 🔴 missing in Go |
| `id` | `_(missing)_` | `string` | 🔴 missing in Go |
| `isSystem` | `_(missing)_` | `boolean` | 🔴 missing in Go |
| `name` | `_(missing)_` | `string` | 🔴 missing in Go |
| `options` | `_(missing)_` | `string` | 🔴 missing in Go |
| `type` | `_(missing)_` | `ConfigVarType` | 🔴 missing in Go |
| `updatedAt` | `_(missing)_` | `string` | 🔴 missing in Go |
| `value` | `_(missing)_` | `string` | 🔴 missing in Go |

### `PUT /api/admin/config/{name}`

- **Status**: ⚪ Go shape unknown
- **Go handler**: `ConfigHandler.UpdateConfig` (`backend/internal/api/handlers/config.go`)
- **Go response**: _unparseable (function call or complex expression)_
- **TS response type**: `ConfigVar`

| Field | Go type | TS type | Notes |
|------|---------|---------|-------|
| `createdAt` | `_(missing)_` | `string` | 🔴 missing in Go |
| `description` | `_(missing)_` | `string` | 🔴 missing in Go |
| `id` | `_(missing)_` | `string` | 🔴 missing in Go |
| `isSystem` | `_(missing)_` | `boolean` | 🔴 missing in Go |
| `name` | `_(missing)_` | `string` | 🔴 missing in Go |
| `options` | `_(missing)_` | `string` | 🔴 missing in Go |
| `type` | `_(missing)_` | `ConfigVarType` | 🔴 missing in Go |
| `updatedAt` | `_(missing)_` | `string` | 🔴 missing in Go |
| `value` | `_(missing)_` | `string` | 🔴 missing in Go |

### `GET /api/admin/logs/export`

- **Status**: ⚪ Go shape unknown
- **Go handler**: `LogHandler.ExportCSV` (`backend/internal/api/handlers/logs.go`)
- **Go response**: _unparseable (function call or complex expression)_
- **TS response type**: `(unknown)`

### `GET /api/admin/pm/engagement`

- **Status**: ⚪ Go shape unknown
- **Go handler**: `PMHandler.GetEngagement` (`backend/internal/api/handlers/pm.go`)
- **Go response**: _unparseable (function call or complex expression)_
- **TS response type**: `EngagementData`

| Field | Go type | TS type | Notes |
|------|---------|---------|-------|
| `avgSessions` | `_(missing)_` | `number` | 🔴 missing in Go |
| `creditTrend` | `_(missing)_` | `DailyMetricPoint[]` | 🔴 missing in Go |
| `dau` | `_(missing)_` | `DailyMetricPoint[]` | 🔴 missing in Go |
| `mau` | `_(missing)_` | `DailyMetricPoint[]` | 🔴 missing in Go |
| `topFeatures` | `_(missing)_` | `FeatureUse[]` | 🔴 missing in Go |
| `wau` | `_(missing)_` | `DailyMetricPoint[]` | 🔴 missing in Go |

### `GET /api/admin/pm/events`

- **Status**: ⚪ Go shape unknown
- **Go handler**: `PMHandler.GetCustomEvents` (`backend/internal/api/handlers/pm.go`)
- **Go response**: _unparseable (function call or complex expression)_
- **TS response type**: `CustomEventData`

| Field | Go type | TS type | Notes |
|------|---------|---------|-------|
| `eventName` | `_(missing)_` | `string` | 🔴 missing in Go |
| `totalCount` | `_(missing)_` | `number` | 🔴 missing in Go |
| `trend` | `_(missing)_` | `DailyMetricPoint[]` | 🔴 missing in Go |

### `GET /api/admin/pm/funnel`

- **Status**: ⚪ Go shape unknown
- **Go handler**: `PMHandler.GetFunnel` (`backend/internal/api/handlers/pm.go`)
- **Go response**: _unparseable (function call or complex expression)_
- **TS response type**: `FunnelData`

| Field | Go type | TS type | Notes |
|------|---------|---------|-------|
| `checkoutsStarted` | `_(missing)_` | `number` | 🔴 missing in Go |
| `paidConversions` | `_(missing)_` | `number` | 🔴 missing in Go |
| `planPageViews` | `_(missing)_` | `number` | 🔴 missing in Go |
| `registrations` | `_(missing)_` | `number` | 🔴 missing in Go |
| `steps` | `_(missing)_` | `FunnelStep[]` | 🔴 missing in Go |
| `uniqueVisitors` | `_(missing)_` | `number` | 🔴 missing in Go |
| `upgrades` | `_(missing)_` | `number` | 🔴 missing in Go |

### `GET /api/admin/pm/kpis`

- **Status**: ⚪ Go shape unknown
- **Go handler**: `PMHandler.GetKPIs` (`backend/internal/api/handlers/pm.go`)
- **Go response**: _unparseable (function call or complex expression)_
- **TS response type**: `KPIData`

| Field | Go type | TS type | Notes |
|------|---------|---------|-------|
| `activeSubscribers` | `_(missing)_` | `number` | 🔴 missing in Go |
| `arpu` | `_(missing)_` | `number` | 🔴 missing in Go |
| `arr` | `_(missing)_` | `number` | 🔴 missing in Go |
| `churnRate` | `_(missing)_` | `number` | 🔴 missing in Go |
| `ltv` | `_(missing)_` | `number` | 🔴 missing in Go |
| `mrr` | `_(missing)_` | `number` | 🔴 missing in Go |
| `mrrTrend` | `_(missing)_` | `DailyMetricPoint[]` | 🔴 missing in Go |
| `planDistribution` | `_(missing)_` | `PlanShare[]` | 🔴 missing in Go |
| `subscriberTrend` | `_(missing)_` | `DailyMetricPoint[]` | 🔴 missing in Go |
| `timeToFirstPurchase` | `_(missing)_` | `number` | 🔴 missing in Go |
| `totalRegistrations` | `_(missing)_` | `number` | 🔴 missing in Go |
| `trialConversionRate` | `_(missing)_` | `number` | 🔴 missing in Go |

### `GET /api/admin/tenants/export`

- **Status**: ⚪ Go shape unknown
- **Go handler**: `AdminHandler.ExportTenantsCSV` (`backend/internal/api/handlers/admin.go`)
- **Go response**: _unparseable (function call or complex expression)_
- **TS response type**: `(unknown)`

### `GET /api/admin/users/export`

- **Status**: ⚪ Go shape unknown
- **Go handler**: `AdminHandler.ExportUsersCSV` (`backend/internal/api/handlers/admin.go`)
- **Go response**: _unparseable (function call or complex expression)_
- **TS response type**: `(unknown)`

### `GET /api/auth/export-data`

- **Status**: ⚪ Go shape unknown
- **Go handler**: `AuthHandler.ExportData` (`backend/internal/api/handlers/auth.go`)
- **Go response**: _unparseable (function call or complex expression)_
- **TS response type**: `(unknown)`

### `GET /api/auth/providers`

- **Status**: ⚪ Go shape unknown
- **Go handler**: `AuthHandler.GetProviders` (`backend/internal/api/handlers/auth.go`)
- **Go response**: _unparseable (function call or complex expression)_
- **TS response type**: `AuthProviders`

| Field | Go type | TS type | Notes |
|------|---------|---------|-------|
| `github` | `_(missing)_` | `boolean` | 🔴 missing in Go |
| `google` | `_(missing)_` | `boolean` | 🔴 missing in Go |
| `magicLink` | `_(missing)_` | `boolean` | 🔴 missing in Go |
| `mfa` | `_(missing)_` | `boolean` | 🔴 missing in Go |
| `microsoft` | `_(missing)_` | `boolean` | 🔴 missing in Go |
| `passkeys` | `_(missing)_` | `boolean` | 🔴 missing in Go |
| `password` | `_(missing)_` | `boolean` | 🔴 missing in Go |

### `GET /api/billing/transactions/{id}/invoice/pdf`

- **Status**: ⚪ Go shape unknown
- **Go handler**: `BillingHandler.GetInvoicePDF` (`backend/internal/api/handlers/billing.go`)
- **Go response**: _unparseable (function call or complex expression)_
- **TS response type**: `(unknown)`

## Unmatched TS Endpoints

These frontend API calls have no matching Go route. The
backend may not implement them, or the URL/method may
differ from what the frontend expects.

| Method | Path | TS type | File |
|--------|------|---------|------|
| `DELETE` | `/api/admin/api-keys/{id}` | `(unknown)` | `frontend/src/api/client.ts:355` |
| `DELETE` | `/api/admin/branding/media/{key}` | `(unknown)` | `frontend/src/api/client.ts:466` |
| `DELETE` | `/api/admin/credit-bundles/{id}` | `(unknown)` | `frontend/src/api/client.ts:307` |
| `PUT` | `/api/admin/credit-bundles/{id}` | `CreditBundle` | `frontend/src/api/client.ts:305` |
| `DELETE` | `/api/admin/plans/{id}` | `(unknown)` | `frontend/src/api/client.ts:287` |
| `GET` | `/api/admin/plans/{id}` | `Plan` | `frontend/src/api/client.ts:281` |
| `PUT` | `/api/admin/plans/{id}` | `Plan` | `frontend/src/api/client.ts:285` |
| `POST` | `/api/admin/plans/{id}/archive` | `(unknown)` | `frontend/src/api/client.ts:289` |
| `POST` | `/api/admin/plans/{id}/unarchive` | `(unknown)` | `frontend/src/api/client.ts:291` |
| `DELETE` | `/api/admin/pm/event-definitions/{id}` | `(unknown)` | `frontend/src/api/client.ts:498` |
| `PUT` | `/api/admin/pm/event-definitions/{id}` | `EventDefinition` | `frontend/src/api/client.ts:496` |
| `GET` | `/api/admin/tenants/{id}` | `{ tenant: TenantDetail; members: TenantMember[…` | `frontend/src/api/client.ts:239` |
| `PUT` | `/api/admin/tenants/{id}` | `(unknown)` | `frontend/src/api/client.ts:241` |
| `PATCH` | `/api/admin/tenants/{id}/status` | `(unknown)` | `frontend/src/api/client.ts:243` |
| `DELETE` | `/api/admin/users/{id}` | `(unknown)` | `frontend/src/api/client.ts:277` |
| `GET` | `/api/admin/users/{id}` | `{ user: UserDetail; memberships: UserMembershi…` | `frontend/src/api/client.ts:269` |
| `PUT` | `/api/admin/users/{id}` | `(unknown)` | `frontend/src/api/client.ts:271` |
| `GET` | `/api/admin/users/{id}/preflight-delete` | `DeletePreflightResponse` | `frontend/src/api/client.ts:275` |
| `PATCH` | `/api/admin/users/{id}/status` | `(unknown)` | `frontend/src/api/client.ts:247` |
| `DELETE` | `/api/admin/webhooks/{id}` | `(unknown)` | `frontend/src/api/client.ts:367` |
| `GET` | `/api/admin/webhooks/{id}` | `{ webhook: Webhook; deliveries: WebhookDeliver…` | `frontend/src/api/client.ts:361` |
| `PUT` | `/api/admin/webhooks/{id}` | `{ webhook: Webhook }` | `frontend/src/api/client.ts:365` |
| `POST` | `/api/admin/webhooks/{id}/regenerate-secret` | `{ secret: string; secretPreview: string }` | `frontend/src/api/client.ts:371` |
| `POST` | `/api/admin/webhooks/{id}/test` | `{ delivery: WebhookDelivery }` | `frontend/src/api/client.ts:369` |
| `GET` | `/api/auth/passkeys` | `{ passkeys: PasskeyCredential[] }` | `frontend/src/api/client.ts:175` |
| `POST` | `/api/auth/passkeys/login/begin` | `(unknown)` | `frontend/src/api/client.ts:171` |
| `POST` | `/api/auth/passkeys/login/finish` | `AuthResponse` | `frontend/src/api/client.ts:173` |
| `POST` | `/api/auth/passkeys/register/begin` | `(unknown)` | `frontend/src/api/client.ts:167` |
| `POST` | `/api/auth/passkeys/register/finish` | `(unknown)` | `frontend/src/api/client.ts:169` |
| `DELETE` | `/api/auth/passkeys/{id}` | `(unknown)` | `frontend/src/api/client.ts:177` |
| `PATCH` | `/api/messages/{id}/read` | `(unknown)` | `frontend/src/api/client.ts:227` |

## Unmatched Go Endpoints

These backend routes have no matching frontend API call.
They may be unused by the current frontend, or the
frontend may call them with a different URL/method.

| Method | Path | Handler | File |
|--------|------|---------|------|
| `DELETE` | `/api/admin/api-keys/{keyId}` | `APIKeysHandler.DeleteAPIKey` | `backend/cmd/server/main.go:761` |
| `DELETE` | `/api/admin/branding/media/{id}` | `BrandingHandler.DeleteMedia` | `backend/cmd/server/main.go:787` |
| `DELETE` | `/api/admin/credit-bundles/{bundleId}` | `BundlesHandler.DeleteBundle` | `backend/cmd/server/main.go:753` |
| `PUT` | `/api/admin/credit-bundles/{bundleId}` | `BundlesHandler.UpdateBundle` | `backend/cmd/server/main.go:752` |
| `GET` | `/api/admin/logs/severity-counts` | `LogHandler.SeverityCounts` | `backend/cmd/server/main.go:682` |
| `DELETE` | `/api/admin/plans/{planId}` | `PlansHandler.DeletePlan` | `backend/cmd/server/main.go:747` |
| `GET` | `/api/admin/plans/{planId}` | `PlansHandler.GetPlan` | `backend/cmd/server/main.go:698` |
| `PUT` | `/api/admin/plans/{planId}` | `PlansHandler.UpdatePlan` | `backend/cmd/server/main.go:746` |
| `POST` | `/api/admin/plans/{planId}/archive` | `PlansHandler.ArchivePlan` | `backend/cmd/server/main.go:748` |
| `POST` | `/api/admin/plans/{planId}/unarchive` | `PlansHandler.UnarchivePlan` | `backend/cmd/server/main.go:749` |
| `DELETE` | `/api/admin/pm/event-definitions/{defId}` | `EventDefinitionsHandler.DeleteEventDefinition` | `backend/cmd/server/main.go:772` |
| `PUT` | `/api/admin/pm/event-definitions/{defId}` | `EventDefinitionsHandler.UpdateEventDefinition` | `backend/cmd/server/main.go:771` |
| `GET` | `/api/admin/promotions` | `PromotionsHandler.ListPromotions` | `backend/cmd/server/main.go:706` |
| `GET` | `/api/admin/tenants/{tenantId}` | `AdminHandler.GetTenant` | `backend/cmd/server/main.go:696` |
| `PUT` | `/api/admin/tenants/{tenantId}` | `AdminHandler.UpdateTenant` | `backend/cmd/server/main.go:743` |
| `PATCH` | `/api/admin/tenants/{tenantId}/status` | `AdminHandler.UpdateTenantStatus` | `backend/cmd/server/main.go:744` |
| `DELETE` | `/api/admin/users/{userId}` | `AdminHandler.DeleteUser` | `backend/cmd/server/main.go:780` |
| `GET` | `/api/admin/users/{userId}` | `AdminHandler.GetUser` | `backend/cmd/server/main.go:719` |
| `PUT` | `/api/admin/users/{userId}` | `AdminHandler.UpdateUser` | `backend/cmd/server/main.go:740` |
| `GET` | `/api/admin/users/{userId}/preflight-delete` | `AdminHandler.PreflightDeleteUser` | `backend/cmd/server/main.go:778` |
| `PATCH` | `/api/admin/users/{userId}/status` | `AdminHandler.UpdateUserStatus` | `backend/cmd/server/main.go:741` |
| `DELETE` | `/api/admin/webhooks/{webhookId}` | `WebhooksHandler.DeleteWebhook` | `backend/cmd/server/main.go:767` |
| `GET` | `/api/admin/webhooks/{webhookId}` | `WebhooksHandler.GetWebhook` | `backend/cmd/server/main.go:722` |
| `PUT` | `/api/admin/webhooks/{webhookId}` | `WebhooksHandler.UpdateWebhook` | `backend/cmd/server/main.go:766` |
| `POST` | `/api/admin/webhooks/{webhookId}/regenerate-secret` | `WebhooksHandler.RegenerateSecret` | `backend/cmd/server/main.go:769` |
| `POST` | `/api/admin/webhooks/{webhookId}/test` | `WebhooksHandler.TestWebhook` | `backend/cmd/server/main.go:768` |
| `GET` | `/api/auth/github` | `AuthHandler.GitHubOAuth` | `backend/cmd/server/main.go:511` |
| `GET` | `/api/auth/github/callback` | `AuthHandler.GitHubOAuthCallback` | `backend/cmd/server/main.go:516` |
| `GET` | `/api/auth/google` | `AuthHandler.GoogleOAuth` | `backend/cmd/server/main.go:501` |
| `GET` | `/api/auth/google/callback` | `AuthHandler.GoogleOAuthCallback` | `backend/cmd/server/main.go:506` |
| `GET` | `/api/auth/microsoft` | `AuthHandler.MicrosoftOAuth` | `backend/cmd/server/main.go:521` |
| `GET` | `/api/auth/microsoft/callback` | `AuthHandler.MicrosoftOAuthCallback` | `backend/cmd/server/main.go:526` |
| `POST` | `/api/billing/webhook` | `WebhookHandler.HandleWebhook` | `backend/cmd/server/main.go:650` |
| `GET` | `/api/branding/asset/{key}` | `BrandingHandler.ServeAsset` | `backend/cmd/server/main.go:422` |
| `GET` | `/api/branding/media/{id}` | `BrandingHandler.ServeMedia` | `backend/cmd/server/main.go:423` |
| `GET` | `/api/docs` | `Handlers.DocsHTML` | `backend/cmd/server/main.go:416` |
| `GET` | `/api/docs/markdown` | `Handlers.DocsMarkdown` | `backend/cmd/server/main.go:417` |
| `GET` | `/api/docs/openapi.json` | `Handlers.DocsOpenAPI` | `backend/cmd/server/main.go:418` |
| `PATCH` | `/api/messages/{messageId}/read` | `MessageHandler.MarkRead` | `backend/cmd/server/main.go:586` |
| `GET` | `/api/version` | `W.Write` | `backend/cmd/server/main.go:405` |
| `GET` | `/health` | `W.Write` | `backend/cmd/server/main.go:381` |

## Recommendations

- 🟡 **58 extra-in-Go field(s)** — the backend sends data the frontend ignores. Consider trimming the Go response struct to reduce payload size and avoid leaking internal fields. Note that some extra fields (e.g. audit metadata) may be intentional.
- 🟠 **4 type mismatch(es)** — pay special attention to `int64` vs `string` mismatches on ID fields: JavaScript cannot represent integers > 2^53 precisely, so any ObjectID or 64-bit ID must be serialised as a string on the Go side (which `primitive.ObjectID.Hex()` does correctly).
- ⚪ **12 endpoint(s) with unparseable Go response** — the handler returns a value via a function call or complex expression the auditor can't statically resolve. Review these manually.

Run this auditor as part of the CI pipeline so shape
drift is caught before it reaches production.
