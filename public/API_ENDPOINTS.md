# API Endpoints Map

- **Repo scanned:** `/home/z/my-project/repos/lastsaas`
- **Graph reference:** `/home/z/my-project/public/graph.json` (loaded)
- **Files scanned:** 134
- **Files with route registrations:** 1
- **Total endpoints:** 162

## Summary by prefix

| Prefix | Label | Endpoints |
| --- | --- | ---: |
| `/api/auth` | Auth | 33 |
| `/api/tenant` | Tenant | 7 |
| `/api/messages` | Messages | 3 |
| `/api/plans` | Plans | 1 |
| `/api/credit-bundles` | Credit Bundles | 1 |
| `/api/announcements` | Announcements | 1 |
| `/api/usage` | Usage | 2 |
| `/api/telemetry` | Telemetry | 3 |
| `/api/billing` | Billing | 8 |
| `/api/admin` | Admin | 92 |
| `/api/branding` | Branding | 5 |
| `/api/bootstrap` | Bootstrap | 1 |
| `/api/docs` | Docs | 3 |
| `/api` | API (other) | 1 |
| `/health` | Health | 1 |

## Auth  (`/api/auth`)

| Method | Path | Handler | Struct | Method | Community | Degree | Handler File | Route File:Line |
| --- | --- | --- | --- | --- | --- | ---: | --- | --- |
| `POST` | `/api/auth/accept-invitation` | `AuthHandler.AcceptInvitation` | AuthHandler | AcceptInvitation | Community 2 | 9 | `backend/internal/api/handlers/auth.go` | `backend/cmd/server/main.go:526` |
| `POST` | `/api/auth/change-password` | `AuthHandler.ChangePassword` | AuthHandler | ChangePassword | Community 2 | 7 | `backend/internal/api/handlers/auth.go` | `backend/cmd/server/main.go:525` |
| `POST` | `/api/auth/complete-onboarding` | `AuthHandler.CompleteOnboarding` | AuthHandler | CompleteOnboarding | Community 2 | 7 | `backend/internal/api/handlers/auth.go` | `backend/cmd/server/main.go:535` |
| `POST` | `/api/auth/delete-account` | `AuthHandler.DeleteAccount` | AuthHandler | DeleteAccount | Community 2 | 7 | `backend/internal/api/handlers/auth.go` | `backend/cmd/server/main.go:536` |
| `POST` | `/api/auth/exchange-code` | `AuthHandler.ExchangeCode` | AuthHandler | ExchangeCode | Community 2 | 9 | `backend/internal/api/handlers/auth.go` | `backend/cmd/server/main.go:466` |
| `GET` | `/api/auth/export-data` | `AuthHandler.ExportData` | AuthHandler | ExportData | Community 2 | 6 | `backend/internal/api/handlers/auth.go` | `backend/cmd/server/main.go:537` |
| `POST` | `/api/auth/forgot-password` | `AuthHandler.ForgotPassword` `<RateLimitHandler>` | AuthHandler | ForgotPassword | Community 2 | 8 | `backend/internal/api/handlers/auth.go` | `backend/cmd/server/main.go:453` |
| `GET` | `/api/auth/github` | `AuthHandler.GitHubOAuth` `<RateLimitHandler>` | AuthHandler | GitHubOAuth | Community 2 | 6 | `backend/internal/api/handlers/auth.go` | `backend/cmd/server/main.go:502` |
| `GET` | `/api/auth/github/callback` | `AuthHandler.GitHubOAuthCallback` | AuthHandler | GitHubOAuthCallback | Community 2 | 10 | `backend/internal/api/handlers/auth.go` | `backend/cmd/server/main.go:507` |
| `GET` | `/api/auth/google` | `AuthHandler.GoogleOAuth` `<RateLimitHandler>` | AuthHandler | GoogleOAuth | Community 2 | 6 | `backend/internal/api/handlers/auth.go` | `backend/cmd/server/main.go:492` |
| `GET` | `/api/auth/google/callback` | `AuthHandler.GoogleOAuthCallback` | AuthHandler | GoogleOAuthCallback | Community 2 | 10 | `backend/internal/api/handlers/auth.go` | `backend/cmd/server/main.go:497` |
| `POST` | `/api/auth/login` | `AuthHandler.Login` `<RateLimitHandler>` | AuthHandler | Login | Community 2 | 9 | `backend/internal/api/handlers/auth.go` | `backend/cmd/server/main.go:429` |
| `POST` | `/api/auth/logout` | `AuthHandler.Logout` | AuthHandler | Logout | Community 2 | 7 | `backend/internal/api/handlers/auth.go` | `backend/cmd/server/main.go:524` |
| `POST` | `/api/auth/magic-link` | `AuthHandler.MagicLinkRequest` `<RateLimitHandler>` | AuthHandler | MagicLinkRequest | Community 2 | 8 | `backend/internal/api/handlers/auth.go` | `backend/cmd/server/main.go:479` |
| `POST` | `/api/auth/magic-link/verify` | `AuthHandler.MagicLinkVerify` `<RateLimitHandler>` | AuthHandler | MagicLinkVerify | Community 2 | 10 | `backend/internal/api/handlers/auth.go` | `backend/cmd/server/main.go:484` |
| `GET` | `/api/auth/me` | `AuthHandler.GetMe` | AuthHandler | GetMe | Community 2 | 8 | `backend/internal/api/handlers/auth.go` | `backend/cmd/server/main.go:523` |
| `POST` | `/api/auth/mfa/challenge` | `AuthHandler.MFAChallenge` `<RateLimitHandler>` | AuthHandler | MFAChallenge | Community 2 | 9 | `backend/internal/api/handlers/auth.go` | `backend/cmd/server/main.go:472` |
| `POST` | `/api/auth/mfa/disable` | `AuthHandler.MFADisable` | AuthHandler | MFADisable | Community 2 | 7 | `backend/internal/api/handlers/auth.go` | `backend/cmd/server/main.go:529` |
| `POST` | `/api/auth/mfa/regenerate-codes` | `AuthHandler.MFARegenerateRecoveryCodes` | AuthHandler | MFARegenerateRecoveryCodes | Community 2 | 7 | `backend/internal/api/handlers/auth.go` | `backend/cmd/server/main.go:530` |
| `POST` | `/api/auth/mfa/setup` | `AuthHandler.MFASetup` | AuthHandler | MFASetup | Community 2 | 7 | `backend/internal/api/handlers/auth.go` | `backend/cmd/server/main.go:527` |
| `POST` | `/api/auth/mfa/verify-setup` | `AuthHandler.MFAVerifySetup` | AuthHandler | MFAVerifySetup | Community 2 | 7 | `backend/internal/api/handlers/auth.go` | `backend/cmd/server/main.go:528` |
| `GET` | `/api/auth/microsoft` | `AuthHandler.MicrosoftOAuth` `<RateLimitHandler>` | AuthHandler | MicrosoftOAuth | Community 2 | 6 | `backend/internal/api/handlers/auth.go` | `backend/cmd/server/main.go:512` |
| `GET` | `/api/auth/microsoft/callback` | `AuthHandler.MicrosoftOAuthCallback` | AuthHandler | MicrosoftOAuthCallback | Community 2 | 10 | `backend/internal/api/handlers/auth.go` | `backend/cmd/server/main.go:517` |
| `PATCH` | `/api/auth/preferences` | `AuthHandler.UpdatePreferences` | AuthHandler | UpdatePreferences | Community 2 | 7 | `backend/internal/api/handlers/auth.go` | `backend/cmd/server/main.go:534` |
| `GET` | `/api/auth/providers` | `AuthHandler.GetProviders` | AuthHandler | GetProviders | Community 2 | 4 | `backend/internal/api/handlers/auth.go` | `backend/cmd/server/main.go:469` |
| `POST` | `/api/auth/refresh` | `AuthHandler.Refresh` `<RateLimitHandler>` | AuthHandler | Refresh | Community 2 | 10 | `backend/internal/api/handlers/auth.go` | `backend/cmd/server/main.go:435` |
| `POST` | `/api/auth/register` | `AuthHandler.Register` `<RateLimitHandler>` | AuthHandler | Register | Community 2 | 13 | `backend/internal/api/handlers/auth.go` | `backend/cmd/server/main.go:423` |
| `POST` | `/api/auth/resend-verification` | `AuthHandler.ResendVerification` `<RateLimitHandler>` | AuthHandler | ResendVerification | Community 2 | 7 | `backend/internal/api/handlers/auth.go` | `backend/cmd/server/main.go:447` |
| `POST` | `/api/auth/reset-password` | `AuthHandler.ResetPassword` `<RateLimitHandler>` | AuthHandler | ResetPassword | Community 2 | 7 | `backend/internal/api/handlers/auth.go` | `backend/cmd/server/main.go:459` |
| `DELETE` | `/api/auth/sessions` | `AuthHandler.RevokeAllSessions` | AuthHandler | RevokeAllSessions | Community 2 | 7 | `backend/internal/api/handlers/auth.go` | `backend/cmd/server/main.go:533` |
| `GET` | `/api/auth/sessions` | `AuthHandler.ListSessions` | AuthHandler | ListSessions | Community 2 | 7 | `backend/internal/api/handlers/auth.go` | `backend/cmd/server/main.go:531` |
| `DELETE` | `/api/auth/sessions/{id}` | `AuthHandler.RevokeSession` | AuthHandler | RevokeSession | Community 2 | 7 | `backend/internal/api/handlers/auth.go` | `backend/cmd/server/main.go:532` |
| `POST` | `/api/auth/verify-email` | `AuthHandler.VerifyEmail` `<RateLimitHandler>` | AuthHandler | VerifyEmail | Community 2 | 7 | `backend/internal/api/handlers/auth.go` | `backend/cmd/server/main.go:441` |

## Tenant  (`/api/tenant`)

| Method | Path | Handler | Struct | Method | Community | Degree | Handler File | Route File:Line |
| --- | --- | --- | --- | --- | --- | ---: | --- | --- |
| `GET` | `/api/tenant/activity` | `TenantHandler.GetActivity` | TenantHandler | GetActivity | Community 59 | 7 | `backend/internal/api/handlers/tenant.go` | `backend/cmd/server/main.go:545` |
| `GET` | `/api/tenant/members` | `TenantHandler.ListMembers` | TenantHandler | ListMembers | Community 59 | 6 | `backend/internal/api/handlers/tenant.go` | `backend/cmd/server/main.go:544` |
| `POST` | `/api/tenant/members/invite` | `TenantHandler.InviteMember` `<RateLimitHandler>` | TenantHandler | InviteMember | Community 59 | 11 | `backend/internal/api/handlers/tenant.go` | `backend/cmd/server/main.go:555` |
| `DELETE` | `/api/tenant/members/{userId}` | `TenantHandler.RemoveMember` | TenantHandler | RemoveMember | Community 59 | 7 | `backend/internal/api/handlers/tenant.go` | `backend/cmd/server/main.go:564` |
| `PATCH` | `/api/tenant/members/{userId}/role` | `TenantHandler.ChangeRole` | TenantHandler | ChangeRole | Community 59 | 8 | `backend/internal/api/handlers/tenant.go` | `backend/cmd/server/main.go:569` |
| `POST` | `/api/tenant/members/{userId}/transfer-ownership` | `TenantHandler.TransferOwnership` | TenantHandler | TransferOwnership | Community 59 | 7 | `backend/internal/api/handlers/tenant.go` | `backend/cmd/server/main.go:570` |
| `PATCH` | `/api/tenant/settings` | `TenantHandler.UpdateTenantSettings` | TenantHandler | UpdateTenantSettings | Community 59 | 7 | `backend/internal/api/handlers/tenant.go` | `backend/cmd/server/main.go:550` |

## Messages  (`/api/messages`)

| Method | Path | Handler | Struct | Method | Community | Degree | Handler File | Route File:Line |
| --- | --- | --- | --- | --- | --- | ---: | --- | --- |
| `GET` | `/api/messages` | `MessageHandler.ListMessages` | MessageHandler | ListMessages | Community 23 | 6 | `backend/internal/api/handlers/messages.go` | `backend/cmd/server/main.go:575` |
| `GET` | `/api/messages/unread-count` | `MessageHandler.UnreadCount` | MessageHandler | UnreadCount | Community 23 | 6 | `backend/internal/api/handlers/messages.go` | `backend/cmd/server/main.go:576` |
| `PATCH` | `/api/messages/{messageId}/read` | `MessageHandler.MarkRead` | MessageHandler | MarkRead | Community 23 | 6 | `backend/internal/api/handlers/messages.go` | `backend/cmd/server/main.go:577` |

## Plans  (`/api/plans`)

| Method | Path | Handler | Struct | Method | Community | Degree | Handler File | Route File:Line |
| --- | --- | --- | --- | --- | --- | ---: | --- | --- |
| `GET` | `/api/plans` | `PlansHandler.ListPlansPublic` `<HandlerFunc, RequireAuth>` | PlansHandler | ListPlansPublic | Community 23 | 7 | `backend/internal/api/handlers/plans.go` | `backend/cmd/server/main.go:580` |

## Credit Bundles  (`/api/credit-bundles`)

| Method | Path | Handler | Struct | Method | Community | Degree | Handler File | Route File:Line |
| --- | --- | --- | --- | --- | --- | ---: | --- | --- |
| `GET` | `/api/credit-bundles` | `BundlesHandler.ListBundlesPublic` `<HandlerFunc, RequireAuth>` | BundlesHandler | ListBundlesPublic | Community 70 | 5 | `backend/internal/api/handlers/bundles.go` | `backend/cmd/server/main.go:583` |

## Announcements  (`/api/announcements`)

| Method | Path | Handler | Struct | Method | Community | Degree | Handler File | Route File:Line |
| --- | --- | --- | --- | --- | --- | ---: | --- | --- |
| `GET` | `/api/announcements` | `AnnouncementsHandler.ListPublic` `<HandlerFunc, RequireAuth>` | AnnouncementsHandler | ListPublic | Community 16 | 5 | `backend/internal/api/handlers/announcements.go` | `backend/cmd/server/main.go:586` |

## Usage  (`/api/usage`)

| Method | Path | Handler | Struct | Method | Community | Degree | Handler File | Route File:Line |
| --- | --- | --- | --- | --- | --- | ---: | --- | --- |
| `POST` | `/api/usage/record` | `UsageHandler.RecordUsage` `<RateLimitHandler>` | UsageHandler | RecordUsage | Community 92 | 5 | `backend/internal/api/handlers/usage.go` | `backend/cmd/server/main.go:593` |
| `GET` | `/api/usage/summary` | `UsageHandler.GetSummary` | UsageHandler | GetSummary | Community 92 | 4 | `backend/internal/api/handlers/usage.go` | `backend/cmd/server/main.go:598` |

## Telemetry  (`/api/telemetry`)

| Method | Path | Handler | Struct | Method | Community | Degree | Handler File | Route File:Line |
| --- | --- | --- | --- | --- | --- | ---: | --- | --- |
| `POST` | `/api/telemetry/events` | `TelemetryHandler.TrackAuthenticated` `<RateLimitHandler>` | TelemetryHandler | TrackAuthenticated | Community 83 | 8 | `backend/internal/api/handlers/telemetry.go` | `backend/cmd/server/main.go:611` |
| `POST` | `/api/telemetry/events/batch` | `TelemetryHandler.TrackBatch` `<RateLimitHandler>` | TelemetryHandler | TrackBatch | Community 83 | 8 | `backend/internal/api/handlers/telemetry.go` | `backend/cmd/server/main.go:622` |
| `POST` | `/api/telemetry/track` | `TelemetryHandler.TrackAnonymous` `<RateLimitHandler>` | TelemetryHandler | TrackAnonymous | Community 83 | 6 | `backend/internal/api/handlers/telemetry.go` | `backend/cmd/server/main.go:601` |

## Billing  (`/api/billing`)

| Method | Path | Handler | Struct | Method | Community | Degree | Handler File | Route File:Line |
| --- | --- | --- | --- | --- | --- | ---: | --- | --- |
| `POST` | `/api/billing/cancel` | `BillingHandler.CancelSubscription` | BillingHandler | CancelSubscription | Community 39 | 8 | `backend/internal/api/handlers/billing.go` | `backend/cmd/server/main.go:651` |
| `POST` | `/api/billing/checkout` | `BillingHandler.Checkout` | BillingHandler | Checkout | Community 39 | 8 | `backend/internal/api/handlers/billing.go` | `backend/cmd/server/main.go:649` |
| `GET` | `/api/billing/config` | `BillingHandler.GetConfig` | BillingHandler | GetConfig | Community 39 | 4 | `backend/internal/api/handlers/billing.go` | `backend/cmd/server/main.go:644` |
| `POST` | `/api/billing/portal` | `BillingHandler.Portal` | BillingHandler | Portal | Community 39 | 7 | `backend/internal/api/handlers/billing.go` | `backend/cmd/server/main.go:650` |
| `GET` | `/api/billing/transactions` | `BillingHandler.ListTransactions` | BillingHandler | ListTransactions | Community 39 | 7 | `backend/internal/api/handlers/billing.go` | `backend/cmd/server/main.go:641` |
| `GET` | `/api/billing/transactions/{id}/invoice` | `BillingHandler.GetInvoice` | BillingHandler | GetInvoice | Community 39 | 7 | `backend/internal/api/handlers/billing.go` | `backend/cmd/server/main.go:642` |
| `GET` | `/api/billing/transactions/{id}/invoice/pdf` | `BillingHandler.GetInvoicePDF` | BillingHandler | GetInvoicePDF | Community 39 | 6 | `backend/internal/api/handlers/billing.go` | `backend/cmd/server/main.go:643` |
| `POST` | `/api/billing/webhook` | `WebhookHandler.HandleWebhook` | WebhookHandler | HandleWebhook | Community 45 | 13 | `backend/internal/api/handlers/webhook.go` | `backend/cmd/server/main.go:635` |

## Admin  (`/api/admin`)

| Method | Path | Handler | Struct | Method | Community | Degree | Handler File | Route File:Line |
| --- | --- | --- | --- | --- | --- | ---: | --- | --- |
| `GET` | `/api/admin/about` | `AdminHandler.GetAbout` | AdminHandler | GetAbout | Community 15 | 4 | `backend/internal/api/handlers/admin.go` | `backend/cmd/server/main.go:664` |
| `GET` | `/api/admin/announcements` | `AnnouncementsHandler.ListAll` | AnnouncementsHandler | ListAll | Community 16 | 5 | `backend/internal/api/handlers/announcements.go` | `backend/cmd/server/main.go:693` |
| `POST` | `/api/admin/announcements` | `AnnouncementsHandler.Create` | AnnouncementsHandler | Create | Community 16 | 5 | `backend/internal/api/handlers/announcements.go` | `backend/cmd/server/main.go:742` |
| `DELETE` | `/api/admin/announcements/{id}` | `AnnouncementsHandler.Delete` | AnnouncementsHandler | Delete | Community 16 | 5 | `backend/internal/api/handlers/announcements.go` | `backend/cmd/server/main.go:744` |
| `PUT` | `/api/admin/announcements/{id}` | `AnnouncementsHandler.Update` | AnnouncementsHandler | Update | Community 16 | 13 | `backend/internal/api/handlers/announcements.go` | `backend/cmd/server/main.go:743` |
| `GET` | `/api/admin/api-keys` | `APIKeysHandler.ListAPIKeys` | APIKeysHandler | ListAPIKeys | Community 54 | 5 | `backend/internal/api/handlers/apikeys.go` | `backend/cmd/server/main.go:696` |
| `POST` | `/api/admin/api-keys` | `APIKeysHandler.CreateAPIKey` | APIKeysHandler | CreateAPIKey | Community 54 | 9 | `backend/internal/api/handlers/apikeys.go` | `backend/cmd/server/main.go:745` |
| `DELETE` | `/api/admin/api-keys/{keyId}` | `APIKeysHandler.DeleteAPIKey` | APIKeysHandler | DeleteAPIKey | Community 54 | 6 | `backend/internal/api/handlers/apikeys.go` | `backend/cmd/server/main.go:746` |
| `PUT` | `/api/admin/branding` | `BrandingHandler.UpdateBranding` | BrandingHandler | UpdateBranding | Community 16 | 7 | `backend/internal/api/handlers/branding.go` | `backend/cmd/server/main.go:768` |
| `POST` | `/api/admin/branding/asset` | `BrandingHandler.UploadAsset` | BrandingHandler | UploadAsset | Community 16 | 6 | `backend/internal/api/handlers/branding.go` | `backend/cmd/server/main.go:769` |
| `DELETE` | `/api/admin/branding/asset/{key}` | `BrandingHandler.DeleteAsset` | BrandingHandler | DeleteAsset | Community 16 | 5 | `backend/internal/api/handlers/branding.go` | `backend/cmd/server/main.go:770` |
| `GET` | `/api/admin/branding/media` | `BrandingHandler.ListMedia` | BrandingHandler | ListMedia | Community 16 | 5 | `backend/internal/api/handlers/branding.go` | `backend/cmd/server/main.go:708` |
| `POST` | `/api/admin/branding/media` | `BrandingHandler.UploadMedia` | BrandingHandler | UploadMedia | Community 16 | 5 | `backend/internal/api/handlers/branding.go` | `backend/cmd/server/main.go:771` |
| `DELETE` | `/api/admin/branding/media/{id}` | `BrandingHandler.DeleteMedia` | BrandingHandler | DeleteMedia | Community 16 | 5 | `backend/internal/api/handlers/branding.go` | `backend/cmd/server/main.go:772` |
| `GET` | `/api/admin/branding/pages` | `BrandingHandler.AdminListPages` | BrandingHandler | AdminListPages | Community 16 | 5 | `backend/internal/api/handlers/branding.go` | `backend/cmd/server/main.go:709` |
| `POST` | `/api/admin/branding/pages` | `BrandingHandler.CreatePage` | BrandingHandler | CreatePage | Community 16 | 5 | `backend/internal/api/handlers/branding.go` | `backend/cmd/server/main.go:773` |
| `DELETE` | `/api/admin/branding/pages/{id}` | `BrandingHandler.DeletePage` | BrandingHandler | DeletePage | Community 16 | 5 | `backend/internal/api/handlers/branding.go` | `backend/cmd/server/main.go:775` |
| `PUT` | `/api/admin/branding/pages/{id}` | `BrandingHandler.UpdatePage` | BrandingHandler | UpdatePage | Community 16 | 5 | `backend/internal/api/handlers/branding.go` | `backend/cmd/server/main.go:774` |
| `GET` | `/api/admin/config` | `ConfigHandler.ListConfig` | ConfigHandler | ListConfig | Community 54 | 4 | `backend/internal/api/handlers/config.go` | `backend/cmd/server/main.go:673` |
| `POST` | `/api/admin/config` | `ConfigHandler.CreateConfig` | ConfigHandler | CreateConfig | Community 54 | 7 | `backend/internal/api/handlers/config.go` | `backend/cmd/server/main.go:722` |
| `DELETE` | `/api/admin/config/{name}` | `ConfigHandler.DeleteConfig` | ConfigHandler | DeleteConfig | Community 54 | 5 | `backend/internal/api/handlers/config.go` | `backend/cmd/server/main.go:724` |
| `GET` | `/api/admin/config/{name}` | `ConfigHandler.GetConfig` | ConfigHandler | GetConfig | Community 54 | 5 | `backend/internal/api/handlers/config.go` | `backend/cmd/server/main.go:674` |
| `PUT` | `/api/admin/config/{name}` | `ConfigHandler.UpdateConfig` | ConfigHandler | UpdateConfig | Community 54 | 6 | `backend/internal/api/handlers/config.go` | `backend/cmd/server/main.go:723` |
| `GET` | `/api/admin/credit-bundles` | `BundlesHandler.ListBundles` | BundlesHandler | ListBundles | Community 70 | 5 | `backend/internal/api/handlers/bundles.go` | `backend/cmd/server/main.go:685` |
| `POST` | `/api/admin/credit-bundles` | `BundlesHandler.CreateBundle` | BundlesHandler | CreateBundle | Community 70 | 7 | `backend/internal/api/handlers/bundles.go` | `backend/cmd/server/main.go:736` |
| `DELETE` | `/api/admin/credit-bundles/{bundleId}` | `BundlesHandler.DeleteBundle` | BundlesHandler | DeleteBundle | Community 70 | 6 | `backend/internal/api/handlers/bundles.go` | `backend/cmd/server/main.go:738` |
| `PUT` | `/api/admin/credit-bundles/{bundleId}` | `BundlesHandler.UpdateBundle` | BundlesHandler | UpdateBundle | Community 70 | 7 | `backend/internal/api/handlers/bundles.go` | `backend/cmd/server/main.go:737` |
| `GET` | `/api/admin/dashboard` | `AdminHandler.GetDashboard` | AdminHandler | GetDashboard | Community 15 | 5 | `backend/internal/api/handlers/admin.go` | `backend/cmd/server/main.go:665` |
| `GET` | `/api/admin/entitlement-keys` | `PlansHandler.ListEntitlementKeys` | PlansHandler | ListEntitlementKeys | Community 23 | 6 | `backend/internal/api/handlers/plans.go` | `backend/cmd/server/main.go:684` |
| `GET` | `/api/admin/financial/metrics` | `BillingHandler.AdminGetMetrics` | BillingHandler | AdminGetMetrics | Community 39 | 7 | `backend/internal/api/handlers/billing.go` | `backend/cmd/server/main.go:695` |
| `GET` | `/api/admin/financial/transactions` | `BillingHandler.AdminListTransactions` | BillingHandler | AdminListTransactions | Community 39 | 7 | `backend/internal/api/handlers/billing.go` | `backend/cmd/server/main.go:694` |
| `GET` | `/api/admin/health/current` | `HealthHandler.GetCurrent` | HealthHandler | GetCurrent | Community 26 | 5 | `backend/internal/api/handlers/health.go` | `backend/cmd/server/main.go:688` |
| `GET` | `/api/admin/health/integrations` | `HealthHandler.GetIntegrations` | HealthHandler | GetIntegrations | Community 26 | 4 | `backend/internal/api/handlers/health.go` | `backend/cmd/server/main.go:689` |
| `GET` | `/api/admin/health/metrics` | `HealthHandler.GetMetrics` | HealthHandler | GetMetrics | Community 26 | 6 | `backend/internal/api/handlers/health.go` | `backend/cmd/server/main.go:687` |
| `GET` | `/api/admin/health/nodes` | `HealthHandler.ListNodes` | HealthHandler | ListNodes | Community 26 | 5 | `backend/internal/api/handlers/health.go` | `backend/cmd/server/main.go:686` |
| `POST` | `/api/admin/health/test-email` | `HealthHandler.SendTestEmail` | HealthHandler | SendTestEmail | Community 26 | 6 | `backend/internal/api/handlers/health.go` | `backend/cmd/server/main.go:690` |
| `GET` | `/api/admin/logs` | `LogHandler.ListLogs` | LogHandler | ListLogs | Community 66 | 6 | `backend/internal/api/handlers/logs.go` | `backend/cmd/server/main.go:666` |
| `GET` | `/api/admin/logs/export` | `LogHandler.ExportCSV` `<RateLimitHandler>` | LogHandler | ExportCSV | Community 66 | 6 | `backend/internal/api/handlers/logs.go` | `backend/cmd/server/main.go:668` |
| `GET` | `/api/admin/logs/severity-counts` | `LogHandler.SeverityCounts` | LogHandler | SeverityCounts | Community 66 | 6 | `backend/internal/api/handlers/logs.go` | `backend/cmd/server/main.go:667` |
| `GET` | `/api/admin/members` | `AdminHandler.ListRootMembers` | AdminHandler | ListRootMembers | Community 15 | 7 | `backend/internal/api/handlers/admin.go` | `backend/cmd/server/main.go:697` |
| `DELETE` | `/api/admin/members/invitations/{invitationId}` | `AdminHandler.CancelRootInvitation` | AdminHandler | CancelRootInvitation | Community 15 | 8 | `backend/internal/api/handlers/admin.go` | `backend/cmd/server/main.go:748` |
| `POST` | `/api/admin/members/invite` | `AdminHandler.InviteRootMember` | AdminHandler | InviteRootMember | Community 15 | 12 | `backend/internal/api/handlers/admin.go` | `backend/cmd/server/main.go:747` |
| `DELETE` | `/api/admin/members/{userId}` | `AdminHandler.RemoveRootMember` | AdminHandler | RemoveRootMember | Community 15 | 8 | `backend/internal/api/handlers/admin.go` | `backend/cmd/server/main.go:749` |
| `PATCH` | `/api/admin/members/{userId}/role` | `AdminHandler.ChangeRootMemberRole` | AdminHandler | ChangeRootMemberRole | Community 15 | 9 | `backend/internal/api/handlers/admin.go` | `backend/cmd/server/main.go:762` |
| `GET` | `/api/admin/plans` | `PlansHandler.ListPlans` | PlansHandler | ListPlans | Community 23 | 6 | `backend/internal/api/handlers/plans.go` | `backend/cmd/server/main.go:682` |
| `POST` | `/api/admin/plans` | `PlansHandler.CreatePlan` | PlansHandler | CreatePlan | Community 23 | 10 | `backend/internal/api/handlers/plans.go` | `backend/cmd/server/main.go:730` |
| `DELETE` | `/api/admin/plans/{planId}` | `PlansHandler.DeletePlan` | PlansHandler | DeletePlan | Community 23 | 7 | `backend/internal/api/handlers/plans.go` | `backend/cmd/server/main.go:732` |
| `GET` | `/api/admin/plans/{planId}` | `PlansHandler.GetPlan` | PlansHandler | GetPlan | Community 23 | 6 | `backend/internal/api/handlers/plans.go` | `backend/cmd/server/main.go:683` |
| `PUT` | `/api/admin/plans/{planId}` | `PlansHandler.UpdatePlan` | PlansHandler | UpdatePlan | Community 23 | 8 | `backend/internal/api/handlers/plans.go` | `backend/cmd/server/main.go:731` |
| `POST` | `/api/admin/plans/{planId}/archive` | `PlansHandler.ArchivePlan` | PlansHandler | ArchivePlan | Community 23 | 7 | `backend/internal/api/handlers/plans.go` | `backend/cmd/server/main.go:733` |
| `POST` | `/api/admin/plans/{planId}/unarchive` | `PlansHandler.UnarchivePlan` | PlansHandler | UnarchivePlan | Community 23 | 7 | `backend/internal/api/handlers/plans.go` | `backend/cmd/server/main.go:734` |
| `GET` | `/api/admin/pm/engagement` | `PMHandler.GetEngagement` | PMHandler | GetEngagement | Community 4 | 6 | `backend/internal/api/handlers/pm.go` | `backend/cmd/server/main.go:712` |
| `GET` | `/api/admin/pm/event-definitions` | `EventDefinitionsHandler.ListEventDefinitions` | EventDefinitionsHandler | ListEventDefinitions | Community 4 | 7 | `backend/internal/api/handlers/event_definitions.go` | `backend/cmd/server/main.go:716` |
| `POST` | `/api/admin/pm/event-definitions` | `EventDefinitionsHandler.CreateEventDefinition` | EventDefinitionsHandler | CreateEventDefinition | Community 4 | 6 | `backend/internal/api/handlers/event_definitions.go` | `backend/cmd/server/main.go:755` |
| `GET` | `/api/admin/pm/event-definitions/sankey` | `EventDefinitionsHandler.GetSankeyData` | EventDefinitionsHandler | GetSankeyData | Community 4 | 7 | `backend/internal/api/handlers/event_definitions.go` | `backend/cmd/server/main.go:717` |
| `DELETE` | `/api/admin/pm/event-definitions/{defId}` | `EventDefinitionsHandler.DeleteEventDefinition` | EventDefinitionsHandler | DeleteEventDefinition | Community 4 | 6 | `backend/internal/api/handlers/event_definitions.go` | `backend/cmd/server/main.go:757` |
| `PUT` | `/api/admin/pm/event-definitions/{defId}` | `EventDefinitionsHandler.UpdateEventDefinition` | EventDefinitionsHandler | UpdateEventDefinition | Community 4 | 7 | `backend/internal/api/handlers/event_definitions.go` | `backend/cmd/server/main.go:756` |
| `GET` | `/api/admin/pm/events` | `PMHandler.GetCustomEvents` | PMHandler | GetCustomEvents | Community 4 | 6 | `backend/internal/api/handlers/pm.go` | `backend/cmd/server/main.go:714` |
| `GET` | `/api/admin/pm/events/types` | `PMHandler.ListEventTypes` | PMHandler | ListEventTypes | Community 4 | 5 | `backend/internal/api/handlers/pm.go` | `backend/cmd/server/main.go:715` |
| `GET` | `/api/admin/pm/funnel` | `PMHandler.GetFunnel` | PMHandler | GetFunnel | Community 4 | 6 | `backend/internal/api/handlers/pm.go` | `backend/cmd/server/main.go:710` |
| `GET` | `/api/admin/pm/kpis` | `PMHandler.GetKPIs` | PMHandler | GetKPIs | Community 4 | 5 | `backend/internal/api/handlers/pm.go` | `backend/cmd/server/main.go:713` |
| `GET` | `/api/admin/pm/retention` | `PMHandler.GetRetention` | PMHandler | GetRetention | Community 4 | 5 | `backend/internal/api/handlers/pm.go` | `backend/cmd/server/main.go:711` |
| `GET` | `/api/admin/promotions` | `PromotionsHandler.ListPromotions` | PromotionsHandler | ListPromotions | Community 18 | 7 | `backend/internal/api/handlers/promotions.go` | `backend/cmd/server/main.go:691` |
| `POST` | `/api/admin/promotions` | `PromotionsHandler.CreatePromotion` | PromotionsHandler | CreatePromotion | Community 18 | 7 | `backend/internal/api/handlers/promotions.go` | `backend/cmd/server/main.go:739` |
| `POST` | `/api/admin/promotions/deactivate` | `PromotionsHandler.DeactivatePromotion` | PromotionsHandler | DeactivatePromotion | Community 18 | 6 | `backend/internal/api/handlers/promotions.go` | `backend/cmd/server/main.go:741` |
| `GET` | `/api/admin/promotions/eligible-products` | `PromotionsHandler.ListEligibleProducts` | PromotionsHandler | ListEligibleProducts | Community 18 | 6 | `backend/internal/api/handlers/promotions.go` | `backend/cmd/server/main.go:692` |
| `POST` | `/api/admin/promotions/update` | `PromotionsHandler.UpdatePromotion` | PromotionsHandler | UpdatePromotion | Community 18 | 6 | `backend/internal/api/handlers/promotions.go` | `backend/cmd/server/main.go:740` |
| `GET` | `/api/admin/tenants` | `AdminHandler.ListTenants` | AdminHandler | ListTenants | Community 15 | 8 | `backend/internal/api/handlers/admin.go` | `backend/cmd/server/main.go:675` |
| `GET` | `/api/admin/tenants/export` | `AdminHandler.ExportTenantsCSV` `<RateLimitHandler>` | AdminHandler | ExportTenantsCSV | Community 15 | 8 | `backend/internal/api/handlers/admin.go` | `backend/cmd/server/main.go:676` |
| `GET` | `/api/admin/tenants/{tenantId}` | `AdminHandler.GetTenant` | AdminHandler | GetTenant | Community 15 | 6 | `backend/internal/api/handlers/admin.go` | `backend/cmd/server/main.go:681` |
| `PUT` | `/api/admin/tenants/{tenantId}` | `AdminHandler.UpdateTenant` | AdminHandler | UpdateTenant | Community 15 | 8 | `backend/internal/api/handlers/admin.go` | `backend/cmd/server/main.go:728` |
| `POST` | `/api/admin/tenants/{tenantId}/cancel-subscription` | `BillingHandler.AdminCancelSubscription` | BillingHandler | AdminCancelSubscription | Community 39 | 6 | `backend/internal/api/handlers/billing.go` | `backend/cmd/server/main.go:766` |
| `PATCH` | `/api/admin/tenants/{tenantId}/plan` | `PlansHandler.AssignPlan` | PlansHandler | AssignPlan | Community 23 | 7 | `backend/internal/api/handlers/plans.go` | `backend/cmd/server/main.go:735` |
| `PATCH` | `/api/admin/tenants/{tenantId}/status` | `AdminHandler.UpdateTenantStatus` | AdminHandler | UpdateTenantStatus | Community 15 | 7 | `backend/internal/api/handlers/admin.go` | `backend/cmd/server/main.go:729` |
| `PATCH` | `/api/admin/tenants/{tenantId}/subscription` | `BillingHandler.AdminUpdateSubscription` | BillingHandler | AdminUpdateSubscription | Community 39 | 6 | `backend/internal/api/handlers/billing.go` | `backend/cmd/server/main.go:767` |
| `GET` | `/api/admin/users` | `AdminHandler.ListUsers` | AdminHandler | ListUsers | Community 15 | 7 | `backend/internal/api/handlers/admin.go` | `backend/cmd/server/main.go:698` |
| `GET` | `/api/admin/users/export` | `AdminHandler.ExportUsersCSV` `<RateLimitHandler>` | AdminHandler | ExportUsersCSV | Community 15 | 7 | `backend/internal/api/handlers/admin.go` | `backend/cmd/server/main.go:699` |
| `DELETE` | `/api/admin/users/{userId}` | `AdminHandler.DeleteUser` | AdminHandler | DeleteUser | Community 15 | 7 | `backend/internal/api/handlers/admin.go` | `backend/cmd/server/main.go:765` |
| `GET` | `/api/admin/users/{userId}` | `AdminHandler.GetUser` | AdminHandler | GetUser | Community 15 | 6 | `backend/internal/api/handlers/admin.go` | `backend/cmd/server/main.go:704` |
| `PUT` | `/api/admin/users/{userId}` | `AdminHandler.UpdateUser` | AdminHandler | UpdateUser | Community 15 | 10 | `backend/internal/api/handlers/admin.go` | `backend/cmd/server/main.go:725` |
| `POST` | `/api/admin/users/{userId}/impersonate` | `AdminHandler.ImpersonateUser` | AdminHandler | ImpersonateUser | Community 15 | 8 | `backend/internal/api/handlers/admin.go` | `backend/cmd/server/main.go:764` |
| `GET` | `/api/admin/users/{userId}/preflight-delete` | `AdminHandler.PreflightDeleteUser` | AdminHandler | PreflightDeleteUser | Community 15 | 7 | `backend/internal/api/handlers/admin.go` | `backend/cmd/server/main.go:763` |
| `PATCH` | `/api/admin/users/{userId}/role/{tenantId}` | `AdminHandler.UpdateUserRole` | AdminHandler | UpdateUserRole | Community 15 | 11 | `backend/internal/api/handlers/admin.go` | `backend/cmd/server/main.go:727` |
| `PATCH` | `/api/admin/users/{userId}/status` | `AdminHandler.UpdateUserStatus` | AdminHandler | UpdateUserStatus | Community 15 | 10 | `backend/internal/api/handlers/admin.go` | `backend/cmd/server/main.go:726` |
| `GET` | `/api/admin/webhooks` | `WebhooksHandler.ListWebhooks` | WebhooksHandler | ListWebhooks | Community 54 | 5 | `backend/internal/api/handlers/webhooks.go` | `backend/cmd/server/main.go:705` |
| `POST` | `/api/admin/webhooks` | `WebhooksHandler.CreateWebhook` | WebhooksHandler | CreateWebhook | Community 54 | 9 | `backend/internal/api/handlers/webhooks.go` | `backend/cmd/server/main.go:750` |
| `GET` | `/api/admin/webhooks/event-types` | `WebhooksHandler.ListEventTypes` | WebhooksHandler | ListEventTypes | Community 54 | 4 | `backend/internal/api/handlers/webhooks.go` | `backend/cmd/server/main.go:706` |
| `DELETE` | `/api/admin/webhooks/{webhookId}` | `WebhooksHandler.DeleteWebhook` | WebhooksHandler | DeleteWebhook | Community 54 | 6 | `backend/internal/api/handlers/webhooks.go` | `backend/cmd/server/main.go:752` |
| `GET` | `/api/admin/webhooks/{webhookId}` | `WebhooksHandler.GetWebhook` | WebhooksHandler | GetWebhook | Community 54 | 5 | `backend/internal/api/handlers/webhooks.go` | `backend/cmd/server/main.go:707` |
| `PUT` | `/api/admin/webhooks/{webhookId}` | `WebhooksHandler.UpdateWebhook` | WebhooksHandler | UpdateWebhook | Community 54 | 8 | `backend/internal/api/handlers/webhooks.go` | `backend/cmd/server/main.go:751` |
| `POST` | `/api/admin/webhooks/{webhookId}/regenerate-secret` | `WebhooksHandler.RegenerateSecret` | WebhooksHandler | RegenerateSecret | Community 54 | 7 | `backend/internal/api/handlers/webhooks.go` | `backend/cmd/server/main.go:754` |
| `POST` | `/api/admin/webhooks/{webhookId}/test` | `WebhooksHandler.TestWebhook` | WebhooksHandler | TestWebhook | Community 54 | 5 | `backend/internal/api/handlers/webhooks.go` | `backend/cmd/server/main.go:753` |

## Branding  (`/api/branding`)

| Method | Path | Handler | Struct | Method | Community | Degree | Handler File | Route File:Line |
| --- | --- | --- | --- | --- | --- | ---: | --- | --- |
| `GET` | `/api/branding` | `BrandingHandler.GetBranding` | BrandingHandler | GetBranding | Community 16 | 7 | `backend/internal/api/handlers/branding.go` | `backend/cmd/server/main.go:412` |
| `GET` | `/api/branding/asset/{key}` | `BrandingHandler.ServeAsset` | BrandingHandler | ServeAsset | Community 16 | 4 | `backend/internal/api/handlers/branding.go` | `backend/cmd/server/main.go:413` |
| `GET` | `/api/branding/media/{id}` | `BrandingHandler.ServeMedia` | BrandingHandler | ServeMedia | Community 16 | 4 | `backend/internal/api/handlers/branding.go` | `backend/cmd/server/main.go:414` |
| `GET` | `/api/branding/page/{slug}` | `BrandingHandler.GetPublicPage` | BrandingHandler | GetPublicPage | Community 16 | 6 | `backend/internal/api/handlers/branding.go` | `backend/cmd/server/main.go:415` |
| `GET` | `/api/branding/pages` | `BrandingHandler.ListPublicPages` | BrandingHandler | ListPublicPages | Community 16 | 5 | `backend/internal/api/handlers/branding.go` | `backend/cmd/server/main.go:416` |

## Bootstrap  (`/api/bootstrap`)

| Method | Path | Handler | Struct | Method | Community | Degree | Handler File | Route File:Line |
| --- | --- | --- | --- | --- | --- | ---: | --- | --- |
| `GET` | `/api/bootstrap/status` | `BootstrapHandler.Status` | BootstrapHandler | Status | Community 65 | 6 | `backend/internal/api/handlers/bootstrap.go` | `backend/cmd/server/main.go:404` |

## Docs  (`/api/docs`)

| Method | Path | Handler | Struct | Method | Community | Degree | Handler File | Route File:Line |
| --- | --- | --- | --- | --- | --- | ---: | --- | --- |
| `GET` | `/api/docs` | `handlers.DocsHTML` | — | DocsHTML | Community 21 | 6 | `backend/internal/api/handlers/docs.go` | `backend/cmd/server/main.go:407` |
| `GET` | `/api/docs/markdown` | `handlers.DocsMarkdown` | — | DocsMarkdown | Community 21 | 7 | `backend/internal/api/handlers/docs.go` | `backend/cmd/server/main.go:408` |
| `GET` | `/api/docs/openapi.json` | `handlers.DocsOpenAPI` | — | DocsOpenAPI | Community 21 | 6 | `backend/internal/api/handlers/openapi.go` | `backend/cmd/server/main.go:409` |

## API (other)  (`/api`)

| Method | Path | Handler | Struct | Method | Community | Degree | Handler File | Route File:Line |
| --- | --- | --- | --- | --- | --- | ---: | --- | --- |
| `GET` | `/api/version` | `<inline>` | — | — | — | — | `—` | `backend/cmd/server/main.go:398` |

## Health  (`/health`)

| Method | Path | Handler | Struct | Method | Community | Degree | Handler File | Route File:Line |
| --- | --- | --- | --- | --- | --- | ---: | --- | --- |
| `GET` | `/health` | `<inline>` | — | — | — | — | `—` | `backend/cmd/server/main.go:379` |

## Handler structs referenced

| Struct | Endpoints |
| --- | ---: |
| `AuthHandler` | 33 |
| `AdminHandler` | 21 |
| `BrandingHandler` | 15 |
| `BillingHandler` | 11 |
| `PlansHandler` | 10 |
| `WebhooksHandler` | 8 |
| `TenantHandler` | 7 |
| `PMHandler` | 6 |
| `BundlesHandler` | 5 |
| `AnnouncementsHandler` | 5 |
| `ConfigHandler` | 5 |
| `HealthHandler` | 5 |
| `PromotionsHandler` | 5 |
| `EventDefinitionsHandler` | 5 |
| `MessageHandler` | 3 |
| `TelemetryHandler` | 3 |
| `LogHandler` | 3 |
| `APIKeysHandler` | 3 |
| `UsageHandler` | 2 |
| `BootstrapHandler` | 1 |
| `WebhookHandler` | 1 |

## Notes

- `degree` = number of graph edges (in + out) touching the handler node.
- `<inline>` = anonymous `func(w, r)` literal registered as the handler.
- Middleware column lists wrappers peeled to find the real handler (e.g. `RateLimitHandler`, `RequireAuth`, `RequireRole`).
- Sub-router prefixes (e.g. `/api`, `/api/auth`, `/api/admin`) are resolved by tracking `PathPrefix("…").Subrouter()` assignments.
- `_test.go` files are skipped by default; pass `--no-skip-tests` to include them (will produce duplicate routes from test helpers).
