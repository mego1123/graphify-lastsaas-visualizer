# lastsaas — Architecture Map

> Auto-generated from `graph.json` by grouping graphify's 157 detected communities
> into thematic SaaS subsystems. Each community is a Leiden-clustered module
> of tightly-coupled symbols; the subsystem grouping below is a higher-level view.

## Top-level: 12 SaaS subsystems

| Subsystem | Communities | Nodes | Coverage |
|---|---:|---:|---|
| **Observability & Health** | 12 | 271 | 10.8% |
| **Configuration & Branding** | 22 | 259 | 10.3% |
| **Authentication & Identity** | 10 | 242 | 9.7% |
| **Public Site (marketing / custom pages)** | 5 | 210 | 8.4% |
| **Storage & Data Layer** | 20 | 204 | 8.1% |
| **Webhooks** | 11 | 197 | 7.9% |
| **Billing & Plans** | 11 | 176 | 7.0% |
| **Auth UI (login / signup / MFA flows)** | 4 | 147 | 5.9% |
| **Middleware & API Gateway** | 6 | 135 | 5.4% |
| **CLI Tooling** | 7 | 126 | 5.0% |
| **Multi-tenancy & RBAC** | 7 | 115 | 4.6% |
| **Admin UI (operator console)** | 5 | 104 | 4.1% |
| **End-User Dashboard (tenant app)** | 3 | 95 | 3.8% |
| **Test Suite** | 12 | 55 | 2.2% |
| **Messaging & Announcements** | 4 | 40 | 1.6% |
| **Build & Config Files** | 7 | 35 | 1.4% |
| **API Docs & OpenAPI** | 1 | 34 | 1.4% |
| **UI Component Library** | 4 | 30 | 1.2% |
| **Deployment & Manifests** | 2 | 20 | 0.8% |
| **Misc / Cross-cutting** | 4 | 12 | 0.5% |
| _Total_ | _157_ | _2507_ | _100%_ |

## God Nodes — architectural pillars

These 20 symbols have the highest degree (most connections). They are the
load-bearing abstractions of the entire codebase.

| Rank | Symbol | Degree | Source |
|---:|---|---:|---|
| 1 | `setupTestServer()` | 152 | `backend/internal/api/handlers/testhelpers_test.go` |
| 2 | `respondWithError()` | 146 | `backend/internal/api/handlers/helpers.go` |
| 3 | `respondWithJSON()` | 144 | `backend/internal/api/handlers/helpers.go` |
| 4 | `types/index.ts` | 118 | `frontend/src/types/index.ts` |
| 5 | `client.ts` | 117 | `frontend/src/api/client.ts` |
| 6 | `CreateTestUser()` | 81 | `backend/internal/testutil/testutil.go` |
| 7 | `App.tsx` | 80 | `frontend/src/App.tsx` |
| 8 | `createAdminEnv()` | 76 | `backend/internal/api/handlers/testhelpers_test.go` |
| 9 | `MarkSystemInitialized()` | 64 | `backend/internal/testutil/testutil.go` |
| 10 | `AuthHandler` | 60 | `backend/internal/api/handlers/auth.go` |
| 11 | `GetUserFromContext()` | 58 | `backend/internal/middleware/auth.go` |
| 12 | `CreateTestTenant()` | 56 | `backend/internal/testutil/testutil.go` |
| 13 | `getErrorMessage()` | 56 | `frontend/src/utils/errors.ts` |
| 14 | `main()` | 55 | `backend/cmd/server/main.go` |
| 15 | `Logger` | 48 | `backend/internal/syslog/syslog.go` |
| 16 | `MongoDB` | 44 | `backend/internal/db/mongodb.go` |
| 17 | `MustConnectTestDB()` | 43 | `backend/internal/testutil/testutil.go` |
| 18 | `CleanupCollections()` | 41 | `backend/internal/testutil/testutil.go` |
| 19 | `useAuth()` | 41 | `frontend/src/contexts/AuthContext.tsx` |
| 20 | `Collection` | 39 | `` |

## Cross-subsystem bridges

Nodes that touch 3+ communities — these are the integration points where
subsystems talk to each other. Refactoring them is high-leverage but high-risk.

| Symbol | Home Community | Communities Touched | Source |
|---|---:|---:|---|
| `main()` | 63 | 35 | `backend/cmd/server/main.go` |
| `setupTestServer()` | 38 | 22 | `backend/internal/api/handlers/testhelpers_test.go` |
| `Logger` | 4 | 16 | `backend/internal/syslog/syslog.go` |
| `respondWithJSON()` | 54 | 14 | `backend/internal/api/handlers/helpers.go` |
| `devDependencies` | 42 | 14 | `frontend/package.json` |
| `respondWithError()` | 16 | 13 | `backend/internal/api/handlers/helpers.go` |
| `GetUserFromContext()` | 23 | 13 | `backend/internal/middleware/auth.go` |
| `CreateTestUser()` | 17 | 12 | `backend/internal/testutil/testutil.go` |
| `client.ts` | 0 | 12 | `frontend/src/api/client.ts` |
| `types/index.ts` | 0 | 12 | `frontend/src/types/index.ts` |
| `AuthHandler` | 2 | 11 | `backend/internal/api/handlers/auth.go` |
| `CreateTestTenant()` | 17 | 11 | `backend/internal/testutil/testutil.go` |
| `main()` | 28 | 10 | `backend/cmd/lastsaas/main.go` |
| `NewAuthHandler()` | 2 | 10 | `backend/internal/api/handlers/auth.go` |
| `testEnv` | 13 | 10 | `backend/internal/api/handlers/testhelpers_test.go` |

## Subsystem Breakdown

### Observability & Health — 271 nodes across 12 communities

- **Community 1** (60 nodes): `Service`, `Context`, `service.go`, `Time`, `DailyPoint`, `.EngagementMetrics()` +54 more
- **Community 7** (47 nodes): `Service`, `MetricsCollector`, `NewMetricsCollector()`, `.collectMongoMetrics()`, `metrics_test.go`, `T` +41 more
- **Community 24** (30 nodes): `syslog_test.go`, `T`, `CountDocuments()`, `New()`, `detectInjection()`, `sanitize()` +24 more
- **Community 34** (24 nodes): `models/health.go`, `SystemMetric`, `SystemNode`, `Time`, `IntegrationCheck`, `NodeStatus` +18 more
- **Community 37** (23 nodes): `ReadResponseBody()`, `admin_test.go`, `T`, `TestIntegration_AdminListTenants()`, `TestIntegration_AdminUpdateTenantStatus()`, `TestIntegration_AdminSearchTenants()` +17 more
- **Community 40** (23 nodes): `createAdminEnv()`, `plans_test.go`, `T`, `CreateTestPlan()`, `TestIntegration_AdminCannotDeletePlan()`, `TestIntegration_AssignPlan_Success()` +17 more
- **Community 71** (13 nodes): `InsertTestLogs()`, `logs_test.go`, `T`, `TestIntegration_LogsListDefault()`, `TestIntegration_LogsSeverityCounts()`, `TestIntegration_LogsFilterBySeverity()` +7 more
- **Community 76** (12 nodes): `Service`, `.run()`, `New()`, `.Stop()`, `.releaseLock()`, `.collectDaily()` +6 more
- **Community 80** (11 nodes): `apikeys_test.go`, `T`, `TestIntegration_APIKeys_NonRootTenantForbidden()`, `TestIntegration_ListAPIKeys_ReturnsKeys()`, `TestIntegration_DeleteAPIKey_Success()`, `TestIntegration_ListAPIKeys_EmptyReturnsArray()` +5 more
- **Community 83** (10 nodes): `.TrackAuthenticated()`, `.TrackBatch()`, `TelemetryHandler`, `.TrackAnonymous()`, `sanitizeProperties()`, `NewTelemetryHandler()` +4 more
- **Community 84** (10 nodes): `Service`, `Context`, `.ListNodes()`, `.GetMetrics()`, `.GetAggregateMetrics()`, `.GetCurrentMetrics()` +4 more
- **Community 93** (8 nodes): `Service`, `.safeRunIntegrationChecks()`, `.RegisterIntegration()`, `.GetIntegrationStatus()`, `.integrationCheckLoop()`, `.runIntegrationChecks()` +2 more

### Configuration & Branding — 259 nodes across 22 communities

- **Community 10** (45 nodes): `config_test.go`, `T`, `Config`, `config/config.go`, `Load()`, `setupTestEnv()` +39 more
- **Community 13** (40 nodes): `setupIsolationEnv()`, `isolation_test.go`, `T`, `testEnv`, `PasswordService`, `.adminRequest()` +34 more
- **Community 16** (36 nodes): `respondWithError()`, `BrandingHandler`, `ResponseWriter`, `Request`, `.Update()`, `AnnouncementsHandler` +30 more
- **Community 30** (27 nodes): `compilerOptions`, `lib`, `tsconfig.app.json`, `types`, `include`, `tsBuildInfoFile` +21 more
- **Community 44** (23 nodes): `compilerOptions`, `tsconfig.node.json`, `lib`, `types`, `include`, `tsBuildInfoFile` +17 more
- **Community 53** (18 nodes): `testutil.go`, `T`, `CreateTestAPIKey()`, `CreateTestInvitation()`, `ConnectTestDB()`, `TestConfig()` +12 more
- **Community 72** (13 nodes): `init()`, `APIKeyAuthority`, `ValidAPIKeyAuthority()`, `ValidConfigVarType()`, `APIKey`, `ConfigVarType` +7 more
- **Community 87** (10 nodes): `server`, `mcp_config`, `env`, `args`, `mcp`, `type` +4 more
- **Community 90** (9 nodes): `server.json`, `repository`, `$schema`, `name`, `description`, `url` +3 more
- **Community 105** (7 nodes): `server_url`, `user_config`, `type`, `title`, `description`, `required` +1 more
- **Community 111** (5 nodes): `package.json`, `name`, `private`, `version`, `type`
- **Community 122** (4 nodes): `SystemConfig`, `system.go`, `ObjectID`, `Time`
- **Community 127** (4 nodes): `platforms`, `compatibility`, `darwin`, `linux`
- **Community 128** (3 nodes): `APIVersion()`, `apiversion.go`, `Handler`
- **Community 130** (3 nodes): `tsconfig.json`, `files`, `references`
- **Community 131** (3 nodes): `author`, `name`, `url`
- **Community 132** (3 nodes): `repository`, `type`, `url`
- **Community 133** (2 nodes): `@eslint/js`, `@eslint/js`
- **Community 152** (1 nodes): `eslint.config.js`
- **Community 153** (1 nodes): `playwright.config.ts`
- **Community 155** (1 nodes): `vite.config.ts`
- **Community 156** (1 nodes): `vitest.config.ts`

### Authentication & Identity — 242 nodes across 10 communities

- **Community 6** (49 nodes): `oauth_test.go`, `T`, `mockToken()`, `MicrosoftOAuthService`, `HandlerFunc`, `NewGitHubOAuthService()` +43 more
- **Community 9** (45 nodes): `Client`, `client.go`, `GitHubOAuthService`, `New()`, `.GetUserInfo()`, `.Startup()` +39 more
- **Community 20** (34 nodes): `NewTOTPService()`, `totp_test.go`, `T`, `TOTPService`, `totp.go`, `NewTOTPServiceWithEncryption()` +28 more
- **Community 28** (27 nodes): `connectDB()`, `main()`, `lastsaas/main.go`, `GetEnv()`, `cmdSetup()`, `cmdConfig()` +21 more
- **Community 38** (23 nodes): `setupTestServer()`, `handlers/auth_test.go`, `T`, `TestIntegration_LoginSuccess()`, `TestIntegration_ChangePassword()`, `TestIntegration_RegisterSuccess()` +17 more
- **Community 51** (20 nodes): `jwt_test.go`, `T`, `newTestJWTService()`, `TestInvalidAccessTokenSignature()`, `TestInvalidRefreshTokenSignature()`, `TestGenerateAccessToken()` +14 more
- **Community 52** (19 nodes): `ParseUserAgent()`, `ua_parser_test.go`, `T`, `ua_parser.go`, `TestParseUserAgentEmpty()`, `TestParseUserAgentChrome()` +13 more
- **Community 55** (17 nodes): `JWTService`, `Duration`, `jwt.go`, `AccessTokenClaims`, `RefreshTokenClaims`, `.GenerateAccessTokenWithTTL()` +11 more
- **Community 99** (7 nodes): `User`, `AuthMethod`, `user.go`, `.HasAuthMethod()`, `ObjectID`, `Time` +1 more
- **Community 149** (1 nodes): `auth.spec.ts`

### Public Site (marketing / custom pages) — 210 nodes across 5 communities

- **Community 0** (79 nodes): `types/index.ts`, `client.ts`, `BrandingPage.tsx`, `UserProfilePage.tsx`, `LogsPage.tsx`, `admin/DashboardPage.tsx` +73 more
- **Community 3** (56 nodes): `useAuth()`, `AuthContext.tsx`, `BrandingContext.tsx`, `useBranding()`, `Layout.tsx`, `ThemeContext.tsx` +50 more
- **Community 8** (46 nodes): `MongoDB`, `Collection`, `NewMongoDB()`, `.ensureIndexes()`, `mongodb.go`, `Database` +40 more
- **Community 47** (22 nodes): `CollectionSchema`, `AllSchemas()`, `schema.go`, `usersSchema()`, `tenantsSchema()`, `tenantMembershipsSchema()` +16 more
- **Community 98** (7 nodes): `models/branding.go`, `BrandingConfig`, `ObjectID`, `Time`, `BrandingAsset`, `CustomPage` +1 more

### Storage & Data Layer — 204 nodes across 20 communities

- **Community 4** (52 nodes): `Logger`, `.log()`, `Context`, `PMHandler`, `EventDefinitionsHandler`, `.logCategorized()` +46 more
- **Community 23** (30 nodes): `GetUserFromContext()`, `PlansHandler`, `Context`, `ResponseWriter`, `Request`, `.CreatePlan()` +24 more
- **Community 57** (16 nodes): `Emitter`, `APIKeysHandler`, `NewAPIKeysHandler()`, `emitter.go`, `NewNoopEmitter()`, `emitter_test.go` +10 more
- **Community 65** (14 nodes): `BootstrapHandler`, `NewBootstrapHandler()`, `.Status()`, `.refreshInitializedFromContext()`, `.BootstrapGuard()`, `bootstrap.go` +8 more
- **Community 66** (14 nodes): `LogHandler`, `.buildFilter()`, `.ListLogs()`, `.SeverityCounts()`, `.ExportCSV()`, `NewLogHandler()` +8 more
- **Community 85** (10 nodes): `tokens.go`, `ObjectID`, `Time`, `VerificationToken`, `AuthCode`, `RefreshToken` +4 more
- **Community 91** (8 nodes): `admin.go`, `NewAdminHandler()`, `Time`, `UserDetail`, `UserMembershipDetail`, `MongoDB` +2 more
- **Community 92** (8 nodes): `UsageHandler`, `.RecordUsage()`, `NewUsageHandler()`, `.GetSummary()`, `usage.go`, `MongoDB` +2 more
- **Community 103** (6 nodes): `SystemLog`, `LogSeverity`, `system_log.go`, `LogCategory`, `ObjectID`, `Time`
- **Community 104** (6 nodes): `CheckAndMigrate()`, `sendUpgradeMessage()`, `check.go`, `MongoDB`, `runMigrations()`, `Context`
- **Community 107** (5 nodes): `Seed()`, `configstore/seed.go`, `appNameDefault()`, `Context`, `MongoDB`
- **Community 108** (5 nodes): `Invitation`, `InvitationStatus`, `invitation.go`, `ObjectID`, `Time`
- **Community 109** (5 nodes): `SSOConnection`, `sso_connection.go`, `SSOAttributeMap`, `ObjectID`, `Time`
- **Community 114** (4 nodes): `cmdDBStats()`, `cmd_db.go`, `cmdDB()`, `toInt64()`
- **Community 119** (4 nodes): `EventDefinition`, `event_definition.go`, `ObjectID`, `Time`
- **Community 123** (4 nodes): `UsageEvent`, `usage_event.go`, `ObjectID`, `Time`
- **Community 124** (4 nodes): `WebAuthnCredential`, `webauthn_credential.go`, `ObjectID`, `Time`
- **Community 125** (4 nodes): `Seed()`, `planstore/seed.go`, `Context`, `MongoDB`
- **Community 126** (4 nodes): `glama.json`, `maintainers`, `$schema`, `jonradoff`
- **Community 147** (1 nodes): `query.go`

### Webhooks — 197 nodes across 11 communities

- **Community 19** (36 nodes): `Validate()`, `validate_test.go`, `T`, `validUser()`, `TestValidate_ValidUser()`, `TestValidate_UserMissingEmail()` +30 more
- **Community 54** (29 nodes): `respondWithJSON()`, `WebhooksHandler`, `ConfigHandler`, `.CreateAPIKey()`, `.CreateWebhook()`, `ResponseWriter` +23 more
- **Community 45** (22 nodes): `Event`, `WebhookHandler`, `.HandleWebhook()`, `Context`, `NewWebhookHandler()`, `.recordTransaction()` +16 more
- **Community 46** (22 nodes): `Dispatcher`, `.deliverWithRetry()`, `NewWebhooksHandler()`, `.deliver()`, `retryJob`, `mapEventType()` +16 more
- **Community 48** (22 nodes): `crypto_test.go`, `T`, `EncryptSecret()`, `DecryptSecret()`, `ParseEncryptionKey()`, `TestEncryptDecryptRoundTrip()` +16 more
- **Community 49** (21 nodes): `CreateTestWebhook()`, `webhooks_test.go`, `T`, `TestIntegration_Webhooks_NonRootTenantForbidden()`, `TestIntegration_ListWebhooks_ReturnsWebhooks()`, `TestIntegration_GetWebhook_Success()` +15 more
- **Community 73** (13 nodes): `models_test.go`, `T`, `TestValidAPIKeyAuthority()`, `TestValidConfigVarType()`, `TestValidWebhookEventType()`, `TestUserHasAuthMethod()` +7 more
- **Community 77** (12 nodes): `NewDispatcher()`, `dispatcher_integration_test.go`, `T`, `TestDispatcherEmitAndDeliver()`, `TestDispatcherEncryptedSecret()`, `TestDispatcherRetryOnFailure()` +6 more
- **Community 82** (11 nodes): `WebhookEventType`, `validateWebhookRequest()`, `webhooks.go`, `ValidWebhookEventType()`, `models/webhook.go`, `Webhook` +5 more
- **Community 110** (5 nodes): `dispatcher_test.go`, `TestComputeSignature()`, `T`, `TestComputeSignatureDifferentSecrets()`, `TestMapEventType()`
- **Community 116** (4 nodes): `handlers/webhook.go`, `templateReplace()`, `replaceAll()`, `indexOf()`

### Billing & Plans — 176 nodes across 11 communities

- **Community 15** (37 nodes): `AdminHandler`, `Context`, `Request`, `ResponseWriter`, `.InviteRootMember()`, `.UpdateUserRole()` +31 more
- **Community 29** (27 nodes): `New()`, `stripe_test.go`, `T`, `setupMockStripe()`, `TestGetOrCreateCustomerNew()`, `TestCreateCheckoutSessionSubscription()` +21 more
- **Community 39** (23 nodes): `BillingHandler`, `Context`, `ResponseWriter`, `Request`, `NewBillingHandler()`, `.Checkout()` +17 more
- **Community 41** (23 nodes): `Service`, `Context`, `.Get()`, `.GetOrCreatePrice()`, `.CreateCheckoutSession()`, `stripe.go` +17 more
- **Community 63** (14 nodes): `main()`, `IntegrationChecker`, `integrations.go`, `NewMongoChecker()`, `NewStripeChecker()`, `NewDataDogChecker()` +8 more
- **Community 69** (13 nodes): `billing_test.go`, `T`, `TestIntegration_Checkout_NilStripe()`, `TestIntegration_Checkout_BillingWaiver_FreePlan()`, `TestIntegration_BillingConfig_NilStripe_ReturnsEmptyKey()`, `TestIntegration_ListTransactions_Empty()` +7 more
- **Community 70** (13 nodes): `BundlesHandler`, `.CreateBundle()`, `.UpdateBundle()`, `.DeleteBundle()`, `NewBundlesHandler()`, `.ListBundles()` +7 more
- **Community 94** (8 nodes): `models/billing.go`, `FinancialTransaction`, `TransactionType`, `ObjectID`, `Time`, `StripeMapping` +2 more
- **Community 95** (8 nodes): `Plan`, `plan.go`, `CreditResetPolicy`, `PricingModel`, `EntitlementValue`, `EntitlementType` +2 more
- **Community 102** (6 nodes): `counter_test.go`, `T`, `TestStripeAPICallsIncrement()`, `TestResendEmailsIncrement()`, `TestSwapResets()`, `TestConcurrentIncrements()`
- **Community 118** (4 nodes): `CreditBundle`, `credit_bundle.go`, `ObjectID`, `Time`

### Auth UI (login / signup / MFA flows) — 147 nodes across 4 communities

- **Community 2** (57 nodes): `AuthHandler`, `Context`, `Request`, `ResponseWriter`, `storeRefreshToken()`, `generateRandomToken()` +51 more
- **Community 5** (51 nodes): `App.tsx`, `ActivityPage.tsx`, `OnboardingPage.tsx`, `ProtectedRoute.tsx`, `tenantApi`, `BootstrapPage.tsx` +45 more
- **Community 32** (25 nodes): `LoadingSpinner.tsx`, `LoadingSpinner()`, `SecurityTab.tsx`, `RootMembersPage.tsx`, `authApi`, `ConfirmModal.tsx` +19 more
- **Community 64** (14 nodes): `handlers/auth.go`, `AuthResponse`, `RegisterRequest`, `LoginRequest`, `RefreshRequest`, `User` +8 more

### Middleware & API Gateway — 135 nodes across 6 communities

- **Community 14** (39 nodes): `middleware/tenant_test.go`, `T`, `RequireActiveBilling()`, `AuthMiddleware`, `RequireEntitlement()`, `.authenticateJWT()` +33 more
- **Community 22** (31 nodes): `RateLimiter`, `NewRateLimiter()`, `GetClientIP()`, `ratelimit.go`, `RateLimitConfig`, `NewDistributedRateLimiter()` +25 more
- **Community 27** (27 nodes): `Write()`, `apierror.go`, `ResponseWriter`, `Request`, `NotFound()`, `Response` +21 more
- **Community 31** (26 nodes): `MustConnectTestDB()`, `CleanupCollections()`, `middleware/auth_test.go`, `T`, `NewJWTService()`, `NewAuthMiddleware()` +20 more
- **Community 88** (9 nodes): `BodySizeLimit()`, `bodylimit_test.go`, `T`, `TestBodySizeLimitAllowsSmallBody()`, `TestBodySizeLimitBlocksOversizedBody()`, `TestBodySizeLimitNilBody()` +3 more
- **Community 129** (3 nodes): `Recovery()`, `recovery.go`, `Handler`

### CLI Tooling — 126 nodes across 7 communities

- **Community 18** (36 nodes): `Store`, `PromotionsHandler`, `.ListPromotions()`, `.CreatePromotion()`, `ValidateValue()`, `NewPromotionsHandler()` +30 more
- **Community 33** (24 nodes): `cmd_mcp.go`, `mcpClient`, `cmdMCP()`, `.get()`, `prettyJSON()`, `MCPServer` +18 more
- **Community 50** (20 nodes): `clr()`, `printJSON()`, `bold()`, `output.go`, `cmdFinancialTransactions()`, `cmdHealth()` +14 more
- **Community 60** (15 nodes): `process.go`, `cmdRestart()`, `cmdStart()`, `stopService()`, `cmdStop()`, `startBackend()` +9 more
- **Community 62** (14 nodes): `cmdUsersGet()`, `cmdUsersList()`, `cmd_users.go`, `timeAgo()`, `cmdUsers()`, `lookupUserWithMemberships()` +8 more
- **Community 75** (12 nodes): `cmdLogs()`, `logsFollow()`, `queryLogs()`, `printLogEntry()`, `cmd_logs.go`, `buildLogFilter()` +6 more
- **Community 106** (5 nodes): `cmdDoctor()`, `checkConfigIntegration()`, `cmd_doctor.go`, `Context`, `MongoDB`

### Multi-tenancy & RBAC — 115 nodes across 7 communities

- **Community 17** (36 nodes): `CreateTestUser()`, `MarkSystemInitialized()`, `CreateTestTenant()`, `CreateTestMembership()`, `handlers/tenant_test.go`, `T` +30 more
- **Community 56** (17 nodes): `Tenant`, `cmdTenantsList()`, `cmdTenantsGet()`, `cmd_tenants.go`, `resolveUserNames()`, `resolvePlanNames()` +11 more
- **Community 58** (16 nodes): `MemberRole`, `NewTenantHandler()`, `TenantMembership`, `handlers/tenant.go`, `MemberResponse`, `membership.go` +10 more
- **Community 59** (16 nodes): `GetTenantFromContext()`, `GetMembershipFromContext()`, `TenantHandler`, `.InviteMember()`, `.ChangeRole()`, `ResponseWriter` +10 more
- **Community 67** (14 nodes): `RequireRole()`, `RequireRootTenant()`, `middleware_test.go`, `T`, `TestContextHelpers()`, `SecurityHeaders()` +8 more
- **Community 79** (12 nodes): `keywords`, `saas`, `admin`, `multi-tenant`, `billing`, `stripe` +6 more
- **Community 120** (4 nodes): `TestRoleHasPermission()`, `TestValidRole()`, `membership_test.go`, `T`

### Admin UI (operator console) — 104 nodes across 5 communities

- **Community 11** (45 nodes): `HealthPage.tsx`, `MetricsCharts.tsx`, `IntegrationsPanel.tsx`, `CurrentStatusPanel.tsx`, `TimeRangeSelector.tsx`, `MetricsCharts()` +39 more
- **Community 43** (23 nodes): `PMPage.tsx`, `formatNum()`, `formatPct()`, `KPIsTab()`, `binChartData()`, `FunnelTab()` +17 more
- **Community 61** (15 nodes): `APIPage.tsx`, `timeAgo()`, `APIKeysSection()`, `formatDate()`, `WebhookDetailModal()`, `WebhooksSection()` +9 more
- **Community 78** (12 nodes): `ConfigPage.tsx`, `EditConfigModal()`, `serializeEnumOptions()`, `ConfigPage()`, `CreateConfigModal()`, `ConfigVar` +6 more
- **Community 89** (9 nodes): `EventDefinitionModal.tsx`, `EventDefinition`, `Modal.tsx`, `Modal()`, `Props`, `EventDefinitionModal()` +3 more

### End-User Dashboard (tenant app) — 95 nodes across 3 communities

- **Community 12** (42 nodes): `getErrorMessage()`, `errors.ts`, `AnnouncementsPage.tsx`, `PlansPage.tsx`, `adminApi`, `PromotionsPage.tsx` +36 more
- **Community 25** (29 nodes): `useTenant()`, `TenantContext.tsx`, `TeamPage.tsx`, `TestEntitlementsPage.tsx`, `TenantProfilePage.tsx`, `Plan` +23 more
- **Community 35** (24 nodes): `PlanPage.tsx`, `BillingTab.tsx`, `BuyCreditsPage.tsx`, `InvoiceModal.tsx`, `PlanPage()`, `plansApi` +18 more

### Test Suite — 55 nodes across 12 communities

- **Community 42** (23 nodes): `devDependencies`, `@testing-library/react`, `jsdom`, `@tailwindcss/vite`, `@types/node`, `@types/react-dom` +17 more
- **Community 86** (10 nodes): `Load()`, `version_test.go`, `T`, `TestLoadFromVersionFile()`, `TestLoadFromBuildVersion()`, `TestBuildVersionTakesPrecedence()` +4 more
- **Community 96** (8 nodes): `scripts`, `dev`, `build`, `lint`, `preview`, `test` +2 more
- **Community 138** (2 nodes): `@testing-library/jest-dom`, `@testing-library/jest-dom`
- **Community 139** (2 nodes): `@testing-library/user-event`, `@testing-library/user-event`
- **Community 144** (2 nodes): `@vitest/coverage-v8`, `@vitest/coverage-v8`
- **Community 143** (2 nodes): `vitest`, `vitest`
- **Community 137** (2 nodes): `@playwright/test`, `@playwright/test`
- **Community 148** (1 nodes): `admin.spec.ts`
- **Community 150** (1 nodes): `navigation.spec.ts`
- **Community 151** (1 nodes): `smoke.spec.ts`
- **Community 154** (1 nodes): `setup.ts`

### Messaging & Announcements — 40 nodes across 4 communities

- **Community 26** (28 nodes): `ResendService`, `HealthHandler`, `.GetMetrics()`, `.SendTestEmail()`, `.SendEmail()`, `.ListNodes()` +22 more
- **Community 115** (4 nodes): `MessageHandler`, `NewMessageHandler()`, `messages.go`, `MongoDB`
- **Community 117** (4 nodes): `Announcement`, `announcement.go`, `ObjectID`, `Time`
- **Community 121** (4 nodes): `Message`, `message.go`, `ObjectID`, `Time`

### Build & Config Files — 35 nodes across 7 communities

- **Community 36** (23 nodes): `dependencies`, `@hookform/resolvers`, `@tanstack/react-query`, `axios`, `lucide-react`, `react` +17 more
- **Community 136** (2 nodes): `msw`, `msw`
- **Community 140** (2 nodes): `@types/dompurify`, `@types/dompurify`
- **Community 141** (2 nodes): `@types/react`, `@types/react`
- **Community 142** (2 nodes): `@vitejs/plugin-react`, `@vitejs/plugin-react`
- **Community 134** (2 nodes): `eslint-plugin-react-hooks`, `eslint-plugin-react-hooks`
- **Community 135** (2 nodes): `globals`, `globals`

### API Docs & OpenAPI — 34 nodes across 1 communities

- **Community 21** (34 nodes): `openapi.go`, `docs.go`, `DocsMarkdown()`, `DocsHTML()`, `DocsOpenAPI()`, `apiReference()` +28 more

### UI Component Library — 30 nodes across 4 communities

- **Community 74** (13 nodes): `ui/index.ts`, `Card.tsx`, `Input.tsx`, `Select.tsx`, `Textarea.tsx`, `Input` +7 more
- **Community 100** (7 nodes): `Button.tsx`, `Button()`, `ButtonVariant`, `ButtonSize`, `ButtonProps`, `variantClasses` +1 more
- **Community 112** (5 nodes): `Alert.tsx`, `AlertVariant`, `AlertProps`, `variantClasses`, `Alert()`
- **Community 113** (5 nodes): `Badge.tsx`, `Badge()`, `BadgeVariant`, `BadgeProps`, `variantClasses`

### Deployment & Manifests — 20 nodes across 2 communities

- **Community 68** (14 nodes): `manifest.json`, `privacy_policies`, `manifest_version`, `name`, `display_name`, `version` +8 more
- **Community 101** (6 nodes): `api_key`, `type`, `title`, `description`, `sensitive`, `required`

### Misc / Cross-cutting — 12 nodes across 4 communities

- **Community 97** (8 nodes): `ErrorBoundary`, `ErrorBoundary.tsx`, `Props`, `State`, `.constructor()`, `.getDerivedStateFromError()` +2 more
- **Community 145** (2 nodes): `setup.sh`, `setup.sh script`
- **Community 157** (1 nodes): `lastsaas`
- **Community 146** (1 nodes): `counter.go`

## SaaS Capability Checklist

Cross-referencing the subsystems above against what a typical SaaS needs:

- [x] User authentication (password + OAuth + MFA) — _Authentication & Identity_
- [x] Auth UI (login / signup / MFA flows) — _Auth UI (login / signup / MFA flows)_
- [x] Authorization / RBAC — _Multi-tenancy & RBAC_
- [x] Multi-tenancy isolation — _Multi-tenancy & RBAC_
- [x] Subscription billing — _Billing & Plans_
- [x] Metered usage / credits — _Billing & Plans_
- [x] Database layer — _Storage & Data Layer_
- [x] Webhook delivery — _Webhooks_
- [x] Rate limiting / security headers — _Middleware & API Gateway_
- [x] Health checks & metrics — _Observability & Health_
- [x] Transactional email — _Messaging & Announcements_
- [x] Per-tenant configuration — _Configuration & Branding_
- [x] Admin dashboard (operator console) — _Admin UI (operator console)_
- [x] End-user dashboard (tenant app) — _End-User Dashboard (tenant app)_
- [x] Public marketing site — _Public Site (marketing / custom pages)_
- [x] API documentation (OpenAPI) — _API Docs & OpenAPI_
- [x] CLI for ops — _CLI Tooling_
- [x] Test coverage — _Test Suite_
- [x] Deployment config (Docker/Fly) — _Deployment & Manifests_
