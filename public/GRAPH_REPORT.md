# Graph Report - /home/z/my-project/repos/lastsaas  (2026-08-04)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 2507 nodes · 6423 edges · 157 communities (139 shown, 18 thin omitted)
- Extraction: 78% EXTRACTED · 22% INFERRED · 0% AMBIGUOUS · INFERRED: 1411 edges (avg confidence: 0.8)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `1ce9858c`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Community 0
- Community 1
- Community 2
- Community 3
- Community 4
- Community 5
- Community 6
- Community 7
- Community 8
- Community 9
- Community 10
- Community 11
- Community 12
- Community 13
- Community 14
- Community 15
- Community 16
- Community 17
- Community 18
- Community 19
- Community 20
- Community 21
- Community 22
- Community 23
- Community 24
- Community 25
- Community 26
- Community 27
- Community 28
- Community 29
- Community 30
- Community 31
- Community 32
- Community 33
- Community 34
- Community 35
- Community 36
- Community 37
- Community 38
- Community 39
- Community 40
- Community 41
- Community 42
- Community 43
- Community 44
- Community 45
- Community 46
- Community 47
- Community 48
- Community 49
- Community 50
- Community 51
- Community 52
- Community 53
- Community 54
- Community 55
- Community 56
- Community 57
- Community 58
- Community 59
- Community 60
- Community 61
- Community 62
- Community 63
- Community 64
- Community 65
- Community 66
- Community 67
- Community 68
- Community 69
- Community 70
- Community 71
- Community 72
- Community 73
- Community 74
- Community 75
- Community 76
- Community 77
- Community 78
- Community 79
- Community 80
- Community 82
- Community 83
- Community 84
- Community 85
- Community 86
- Community 87
- Community 88
- Community 89
- Community 90
- Community 91
- Community 92
- Community 93
- Community 94
- Community 95
- Community 96
- Community 97
- Community 98
- Community 99
- Community 100
- Community 101
- Community 102
- Community 103
- Community 104
- Community 105
- Community 106
- Community 107
- Community 108
- Community 109
- Community 110
- Community 111
- Community 112
- Community 113
- Community 114
- Community 115
- Community 116
- Community 117
- Community 118
- Community 119
- Community 120
- Community 121
- Community 122
- Community 123
- Community 124
- Community 125
- Community 126
- Community 127
- Community 128
- Community 129
- Community 130
- Community 131
- Community 132
- Community 133
- Community 134
- Community 135
- Community 136
- Community 137
- Community 138
- Community 139
- Community 140
- Community 141
- Community 142
- Community 143
- Community 144
- Community 145
- Community 157

## God Nodes (most connected - your core abstractions)
1. `setupTestServer()` - 152 edges
2. `respondWithError()` - 146 edges
3. `respondWithJSON()` - 144 edges
4. `CreateTestUser()` - 81 edges
5. `createAdminEnv()` - 76 edges
6. `MarkSystemInitialized()` - 64 edges
7. `AuthHandler` - 60 edges
8. `GetUserFromContext()` - 58 edges
9. `CreateTestTenant()` - 56 edges
10. `getErrorMessage()` - 56 edges

## Surprising Connections (you probably didn't know these)
- `main()` --calls--> `parseGlobalFlags()`  [INFERRED]
  backend/cmd/lastsaas/main.go → backend/cmd/lastsaas/output.go
- `main()` --calls--> `cmdDB()`  [INFERRED]
  backend/cmd/lastsaas/main.go → backend/cmd/lastsaas/cmd_db.go
- `cmdDBStats()` --calls--> `connectDB()`  [INFERRED]
  backend/cmd/lastsaas/cmd_db.go → backend/cmd/lastsaas/main.go
- `cmdDBStats()` --calls--> `bold()`  [INFERRED]
  backend/cmd/lastsaas/cmd_db.go → backend/cmd/lastsaas/output.go
- `cmdDBStats()` --calls--> `formatBytes()`  [INFERRED]
  backend/cmd/lastsaas/cmd_db.go → backend/cmd/lastsaas/output.go

## Import Cycles
- None detected.

## Communities (157 total, 18 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.04
Nodes (65): api, brandingAdminApi, brandingApi, refreshSubscribers, usageApi, Card(), BrandingContextValue, BrandingPage() (+57 more)

### Community 1 - "Community 1"
Cohesion: 0.08
Nodes (29): ObjectID, Time, buildFunnelSteps(), Context, M, MongoDB, Mutex, ObjectID (+21 more)

### Community 2 - "Community 2"
Cohesion: 0.14
Nodes (14): GoogleOAuthService, Context, Duration, MongoDB, ObjectID, Request, ResponseWriter, Service (+6 more)

### Community 3 - "Community 3"
Cohesion: 0.07
Nodes (38): dompurify, dompurify, announcementsApi, bundlesApi, setAuthToken(), BrandingThemeInjector(), generatePalette(), isValidHex() (+30 more)

### Community 4 - "Community 4"
Cohesion: 0.10
Nodes (23): Context, MongoDB, ObjectID, Request, ResponseWriter, NewEventDefinitionsHandler(), MongoDB, Request (+15 more)

### Community 5 - "Community 5"
Cohesion: 0.05
Nodes (40): bootstrapApi, tenantApi, AdminAboutPage, AdminAnnouncementsPage, AdminAPIPage, AdminBrandingPage, AdminConfigPage, AdminDashboardPage (+32 more)

### Community 6 - "Community 6"
Cohesion: 0.08
Nodes (39): GoogleUserInfo, MicrosoftOAuthService, MicrosoftUserInfo, mockTransport, NewGitHubOAuthService(), Context, Token, NewGoogleOAuthService() (+31 more)

### Community 7 - "Community 7"
Cohesion: 0.07
Nodes (28): Context, Service, IntegrationCheck, MongoDB, MongoMetrics, RWMutex, SystemMetric, WaitGroup (+20 more)

### Community 8 - "Community 8"
Cohesion: 0.08
Nodes (5): Collection, Context, Database, MongoDB, NewMongoDB()

### Community 9 - "Community 9"
Cohesion: 0.09
Nodes (22): GitHubEmail, GitHubOAuthService, GitHubUserInfo, Context, Token, Context, IntegrationCheck, LogSeverity (+14 more)

### Community 10 - "Community 10"
Cohesion: 0.11
Nodes (42): expandEnvVars(), Load(), LoadEnvFile(), findConfigDir(), T, hasYAMLFiles(), setupTestEnv(), TestEnvVarExpansion() (+34 more)

### Community 11 - "Community 11"
Cohesion: 0.09
Nodes (34): ChartCard(), ChartCardProps, avg(), CurrentStatusPanel(), CurrentStatusPanelProps, formatBytes(), formatMs(), formatPercent() (+26 more)

### Community 12 - "Community 12"
Cohesion: 0.09
Nodes (32): adminApi, TableSkeleton(), TableSkeletonProps, AboutPage(), AnnouncementFormData, AnnouncementFormModal(), announcementSchema, AnnouncementsPage() (+24 more)

### Community 13 - "Community 13"
Cohesion: 0.11
Nodes (30): PasswordService, T, User, setupIsolationEnv(), TestIntegration_Admin_CanInviteUsers_NotAdmins(), TestIntegration_NonRootAdmin_CannotAccessDashboard(), TestIntegration_NonRootAdmin_CannotListAPIKeys(), TestIntegration_NonRootAdmin_CannotListLogs() (+22 more)

### Community 14 - "Community 14"
Cohesion: 0.10
Nodes (32): GetAPIKeyFromContext(), GetImpersonatedBy(), APIKey, Context, Handler, MongoDB, Request, ResponseWriter (+24 more)

### Community 15 - "Community 15"
Cohesion: 0.18
Nodes (12): decodeJSON(), Context, ObjectID, Request, ResponseWriter, Service, escapeRegexInput(), sanitizeCSVField() (+4 more)

### Community 16 - "Community 16"
Cohesion: 0.15
Nodes (13): MongoDB, Request, ResponseWriter, NewAnnouncementsHandler(), defaultBrandingConfig(), MongoDB, Request, ResponseWriter (+5 more)

### Community 17 - "Community 17"
Cohesion: 0.26
Nodes (35): TestIntegration_AdminCannotAssignPlan(), TestIntegration_AdminCannotCreatePlan(), T, TestIntegration_ChangeRole_AdminCannotChangeRoles(), TestIntegration_ChangeRole_CannotChangeOwnRole(), TestIntegration_ChangeRole_CannotSetToOwner(), TestIntegration_ChangeRole_OwnerChangesAdminToUser(), TestIntegration_ChangeRole_OwnerChangesUserToAdmin() (+27 more)

### Community 18 - "Community 18"
Cohesion: 0.10
Nodes (20): Context, MongoDB, ObjectID, Request, ResponseWriter, Service, NewPromotionsHandler(), Context (+12 more)

### Community 19 - "Community 19"
Cohesion: 0.16
Nodes (34): formatFieldError(), T, User, TestValidate_APIKeyInvalidAuthority(), TestValidate_ConfigVarInvalidType(), TestValidate_CreditBundleZeroCredits(), TestValidate_ErrorFormatting(), TestValidate_InvitationInvalidStatus() (+26 more)

### Community 20 - "Community 20"
Cohesion: 0.13
Nodes (24): TOTPService, NewTOTPService(), NewTOTPServiceWithEncryption(), T, TestGenerateRecoveryCodes_Count(), TestGenerateRecoveryCodes_Format(), TestGenerateRecoveryCodes_HashesMatchPlain(), TestGenerateRecoveryCodes_Uniqueness() (+16 more)

### Community 21 - "Community 21"
Cohesion: 0.11
Nodes (32): apiReference(), authBadge(), authLabel(), DocsHTML(), DocsMarkdown(), Request, ResponseWriter, stripHTML() (+24 more)

### Community 22 - "Community 22"
Cohesion: 0.12
Nodes (22): GetClientIP(), Collection, Database, Duration, HandlerFunc, Request, RWMutex, Time (+14 more)

### Community 23 - "Community 23"
Cohesion: 0.17
Nodes (15): Request, ResponseWriter, Context, MongoDB, Plan, Request, ResponseWriter, Service (+7 more)

### Community 24 - "Community 24"
Cohesion: 0.18
Nodes (28): detectInjection(), New(), sanitize(), T, TestDetectInjectionCleanString(), TestDetectInjectionEmbed(), TestDetectInjectionIframe(), TestDetectInjectionJavascript() (+20 more)

### Community 25 - "Community 25"
Cohesion: 0.12
Nodes (23): messagesApi, setTenantHeader(), AdminLayout(), AdminRoute(), TenantContext, TenantContextType, TenantProvider(), useTenant() (+15 more)

### Community 26 - "Community 26"
Cohesion: 0.14
Nodes (11): Request, ResponseWriter, Service, Time, NewHealthHandler(), parseTimeRange(), isValidEmail(), NewResendService() (+3 more)

### Community 27 - "Community 27"
Cohesion: 0.15
Nodes (22): Code, Response, Request, ResponseWriter, BadRequest(), Conflict(), Forbidden(), Request (+14 more)

### Community 28 - "Community 28"
Cohesion: 0.16
Nodes (25): cmdChangePassword(), cmdConfig(), cmdConfigGet(), cmdConfigList(), cmdConfigReset(), cmdConfigSet(), cmdSendMessage(), cmdSetup() (+17 more)

### Community 29 - "Community 29"
Cohesion: 0.23
Nodes (26): New(), HandlerFunc, Server, T, setupMockStripe(), TestCancelSubscriptionAtPeriodEnd(), TestCancelSubscriptionAtPeriodEndNoItems(), TestCancelSubscriptionImmediately() (+18 more)

### Community 30 - "Community 30"
Cohesion: 0.07
Nodes (26): compilerOptions, allowImportingTsExtensions, erasableSyntaxOnly, jsx, lib, module, moduleDetection, moduleResolution (+18 more)

### Community 31 - "Community 31"
Cohesion: 0.26
Nodes (25): NewJWTService(), NewAuthMiddleware(), T, setupAuthMiddleware(), TestGetClientIPFlyClientIP(), TestGetClientIPFlyClientIPInvalid(), TestRateLimiterCleanupExpired(), TestRequireAuthAdminAPIKey() (+17 more)

### Community 32 - "Community 32"
Cohesion: 0.14
Nodes (11): authApi, ConfirmModal(), ConfirmModalProps, LoadingSpinner(), LoadingSpinnerProps, roleIcons, RootMembersPage(), MFASetupModal() (+3 more)

### Community 33 - "Community 33"
Cohesion: 0.38
Nodes (22): buildQuery(), cmdMCP(), Context, newMCPClient(), prettyJSON(), registerAboutTools(), registerAnnouncementTools(), registerConfigTools() (+14 more)

### Community 34 - "Community 34"
Cohesion: 0.10
Nodes (23): MongoMetrics, ObjectID, Time, CPUMetrics, DiskMetrics, GoRuntimeMetrics, HTTPMetrics, IntegrationCountMetrics (+15 more)

### Community 35 - "Community 35"
Cohesion: 0.14
Nodes (19): billingApi, plansApi, telemetryApi, getSessionId(), useTelemetry(), BuyCreditsPage(), formatPrice(), annualPrice() (+11 more)

### Community 36 - "Community 36"
Cohesion: 0.09
Nodes (23): axios, dependencies, axios, @hookform/resolvers, lucide-react, react, react-dom, react-hook-form (+15 more)

### Community 37 - "Community 37"
Cohesion: 0.22
Nodes (22): T, TestIntegration_AdminCancelRootInvitation(), TestIntegration_AdminChangeRootMemberRole(), TestIntegration_AdminDashboard(), TestIntegration_AdminGetTenant(), TestIntegration_AdminGetTenantNotFound(), TestIntegration_AdminGetUser(), TestIntegration_AdminGetUserNotFound() (+14 more)

### Community 38 - "Community 38"
Cohesion: 0.23
Nodes (22): T, TestIntegration_BootstrapStatus(), TestIntegration_BootstrapStatusAfterInit(), TestIntegration_ChangePassword(), TestIntegration_ChangePasswordWrongCurrent(), TestIntegration_GetMe(), TestIntegration_GetMeNoToken(), TestIntegration_LoginNonexistentUser() (+14 more)

### Community 39 - "Community 39"
Cohesion: 0.24
Nodes (7): Context, MongoDB, Request, ResponseWriter, Service, NewBillingHandler(), BillingHandler

### Community 40 - "Community 40"
Cohesion: 0.26
Nodes (22): T, TestIntegration_AdminCannotDeletePlan(), TestIntegration_ArchivePlan_Success(), TestIntegration_ArchiveSystemPlan_Forbidden(), TestIntegration_AssignPlan_Success(), TestIntegration_CreatePlan_DuplicateName(), TestIntegration_CreatePlan_MissingName(), TestIntegration_CreatePlan_Success() (+14 more)

### Community 41 - "Community 41"
Cohesion: 0.15
Nodes (9): Context, MongoDB, ObjectID, Time, CheckoutSession, CheckoutLineItem, CheckoutRequest, Service (+1 more)

### Community 42 - "Community 42"
Cohesion: 0.09
Nodes (23): eslint, eslint-plugin-react-refresh, devDependencies, eslint, eslint-plugin-react-refresh, jsdom, tailwindcss, @tailwindcss/vite (+15 more)

### Community 43 - "Community 43"
Cohesion: 0.13
Nodes (18): pmApi, binChartData(), EngagementTab(), EventSubTab, FlowSubTab(), formatCents(), formatNum(), formatPct() (+10 more)

### Community 44 - "Community 44"
Cohesion: 0.09
Nodes (22): compilerOptions, allowImportingTsExtensions, erasableSyntaxOnly, lib, module, moduleDetection, moduleResolution, noEmit (+14 more)

### Community 45 - "Community 45"
Cohesion: 0.23
Nodes (11): extractInstanceFromEvent(), Context, MongoDB, ObjectID, Request, ResponseWriter, Service, NewWebhookHandler() (+3 more)

### Community 46 - "Community 46"
Cohesion: 0.18
Nodes (12): MongoDB, NewWebhooksHandler(), computeSignature(), Context, MongoDB, Time, Webhook, WebhookEventType (+4 more)

### Community 47 - "Community 47"
Cohesion: 0.23
Nodes (20): AllSchemas(), announcementsSchema(), apiKeysSchema(), configVarsSchema(), creditBundlesSchema(), customPagesSchema(), eventDefinitionsSchema(), financialTransactionsSchema() (+12 more)

### Community 48 - "Community 48"
Cohesion: 0.20
Nodes (20): DecryptSecret(), EncryptSecret(), ParseEncryptionKey(), T, TestDecryptInvalidBase64(), TestDecryptInvalidKeyLength(), TestDecryptTooShortCiphertext(), TestEncryptDecryptRoundTrip() (+12 more)

### Community 49 - "Community 49"
Cohesion: 0.19
Nodes (20): T, TestIntegration_CreateWebhook_InvalidURL(), TestIntegration_CreateWebhook_MissingEvents(), TestIntegration_CreateWebhook_MissingName(), TestIntegration_CreateWebhook_MissingURL(), TestIntegration_CreateWebhook_Success(), TestIntegration_DeleteWebhook_NotFound(), TestIntegration_DeleteWebhook_Success() (+12 more)

### Community 50 - "Community 50"
Cohesion: 0.23
Nodes (16): cmdFinancial(), cmdFinancialMetrics(), cmdFinancialSummary(), cmdFinancialTransactions(), cmdHealth(), cmdStats(), bold(), clr() (+8 more)

### Community 51 - "Community 51"
Cohesion: 0.25
Nodes (19): T, newTestJWTService(), TestAccessTokenCantValidateAsRefresh(), TestDefaultTTLValues(), TestEmptyToken(), TestExpiredAccessToken(), TestExpiredRefreshToken(), TestGenerateAccessToken() (+11 more)

### Community 52 - "Community 52"
Cohesion: 0.26
Nodes (17): parseBrowser(), parseOS(), ParseUserAgent(), T, TestParseUserAgentAndroid(), TestParseUserAgentBrowserOnly(), TestParseUserAgentChrome(), TestParseUserAgentChromeOS() (+9 more)

### Community 53 - "Community 53"
Cohesion: 0.18
Nodes (16): APIKeyAuthority, M, TestMain(), ConnectTestDB(), CreateTestAPIKey(), CreateTestInvitation(), findAndSetConfigDir(), APIKey (+8 more)

### Community 54 - "Community 54"
Cohesion: 0.17
Nodes (12): Request, ResponseWriter, MongoDB, Request, ResponseWriter, NewConfigHandler(), ResponseWriter, respondWithJSON() (+4 more)

### Community 55 - "Community 55"
Cohesion: 0.18
Nodes (5): AccessTokenClaims, JWTService, RefreshTokenClaims, Duration, RegisteredClaims

### Community 56 - "Community 56"
Cohesion: 0.21
Nodes (15): cmdTenants(), cmdTenantsGet(), cmdTenantsList(), countMembersPerTenant(), Context, MongoDB, ObjectID, resolvePlanNames() (+7 more)

### Community 57 - "Community 57"
Cohesion: 0.19
Nodes (12): MongoDB, NewAPIKeysHandler(), NewNoopEmitter(), T, TestEventStruct(), TestEventTypeConstants(), TestNoopEmitterEmit(), TestNoopEmitterImplementsInterface() (+4 more)

### Community 58 - "Community 58"
Cohesion: 0.16
Nodes (13): MongoDB, Time, NewTenantHandler(), ObjectID, Time, RoleHasPermission(), ChangeRoleRequest, InviteMemberRequest (+5 more)

### Community 59 - "Community 59"
Cohesion: 0.33
Nodes (7): Request, ResponseWriter, Service, GetMembershipFromContext(), GetTenantFromContext(), Context, TenantHandler

### Community 60 - "Community 60"
Cohesion: 0.35
Nodes (14): capitalizeStr(), cmdRestart(), cmdStart(), cmdStop(), ensurePIDDir(), findProjectRoot(), isDirAt(), mustFindProjectRoot() (+6 more)

### Community 61 - "Community 61"
Cohesion: 0.18
Nodes (11): APIKeysSection(), CreateKeyModal(), formatDate(), timeAgo(), WebhookDetailModal(), WebhookFormModal(), WebhooksSection(), APIKey (+3 more)

### Community 62 - "Community 62"
Cohesion: 0.24
Nodes (13): cmdUsers(), cmdUsersGet(), cmdUsersList(), cmdUsersRevokeSessions(), cmdUsersSetActive(), Context, MongoDB, ObjectID (+5 more)

### Community 63 - "Community 63"
Cohesion: 0.34
Nodes (13): main(), Context, NewDataDogChecker(), NewGitHubOAuthChecker(), NewGoogleOAuthChecker(), NewMicrosoftOAuthChecker(), NewMongoChecker(), NewResendChecker() (+5 more)

### Community 64 - "Community 64"
Cohesion: 0.14
Nodes (13): User, AcceptInvitationRequest, AuthResponse, ChangePasswordRequest, ForgotPasswordRequest, LoginRequest, MFARequiredResponse, RefreshRequest (+5 more)

### Community 65 - "Community 65"
Cohesion: 0.23
Nodes (8): Handler, MongoDB, Request, ResponseWriter, RWMutex, NewBootstrapHandler(), BootstrapHandler, bootstrapStatusResponse

### Community 66 - "Community 66"
Cohesion: 0.25
Nodes (9): getFirst(), M, MongoDB, Request, ResponseWriter, SystemLog, NewLogHandler(), LogHandler (+1 more)

### Community 67 - "Community 67"
Cohesion: 0.22
Nodes (11): T, TestContextHelpers(), TestRequireRole(), TestRequireRoleMissingContext(), TestRequireRootTenant(), TestSecurityHeaders(), Handler, RequireRole() (+3 more)

### Community 68 - "Community 68"
Cohesion: 0.14
Nodes (13): description, display_name, documentation, homepage, license, long_description, manifest_version, name (+5 more)

### Community 69 - "Community 69"
Cohesion: 0.28
Nodes (12): T, TestIntegration_AdminBilling_NonRootTenantForbidden(), TestIntegration_AdminGetMetrics_Returns(), TestIntegration_AdminListTransactions_Empty(), TestIntegration_Billing_NonRootTenantCanAccess(), TestIntegration_Billing_UnauthenticatedForbidden(), TestIntegration_BillingConfig_NilStripe_ReturnsEmptyKey(), TestIntegration_CancelSubscription_NoSubscription() (+4 more)

### Community 70 - "Community 70"
Cohesion: 0.32
Nodes (7): MongoDB, Request, ResponseWriter, NewBundlesHandler(), validateBundleRequest(), bundleRequest, BundlesHandler

### Community 71 - "Community 71"
Cohesion: 0.32
Nodes (12): T, TestIntegration_LogsDateRange(), TestIntegration_LogsEmptyResults(), TestIntegration_LogsFilterByCategory(), TestIntegration_LogsFilterBySeverity(), TestIntegration_LogsListDefault(), TestIntegration_LogsMultiSeverityFilter(), TestIntegration_LogsPagination() (+4 more)

### Community 72 - "Community 72"
Cohesion: 0.23
Nodes (11): ObjectID, Time, ValidAPIKeyAuthority(), ObjectID, Time, ValidConfigVarType(), init(), APIKey (+3 more)

### Community 73 - "Community 73"
Cohesion: 0.28
Nodes (12): T, TestAllWebhookEventTypesNoDuplicates(), TestAuthMethodConstants(), TestBillingStatusConstants(), TestUserHasAuthMethod(), TestUserHasAuthMethodEmpty(), TestUserIsLockedFuture(), TestUserIsLockedNil() (+4 more)

### Community 74 - "Community 74"
Cohesion: 0.15
Nodes (8): CardProps, paddingClasses, Input, InputProps, Select, SelectProps, Textarea, TextareaProps

### Community 75 - "Community 75"
Cohesion: 0.35
Nodes (11): buildLogFilter(), cmdLogs(), Context, M, MongoDB, SystemLog, Time, logsFollow() (+3 more)

### Community 76 - "Community 76"
Cohesion: 0.29
Nodes (4): Context, MongoDB, New(), Service

### Community 77 - "Community 77"
Cohesion: 0.41
Nodes (11): T, TestDispatcherDeliverTest(), TestDispatcherDeliverTestBadURL(), TestDispatcherEmitAndDeliver(), TestDispatcherEmitUnmappedEvent(), TestDispatcherEncryptedSecret(), TestDispatcherNoMatchingWebhooks(), TestDispatcherRetryOnFailure() (+3 more)

### Community 78 - "Community 78"
Cohesion: 0.21
Nodes (9): ConfigPage(), CreateConfigModal(), EditConfigModal(), parseEnumOptions(), serializeEnumOptions(), typeLabels, ConfigVar, ConfigVarType (+1 more)

### Community 79 - "Community 79"
Cohesion: 0.17
Nodes (12): keywords, admin, ai-native, billing, dashboard, go, health, monitoring (+4 more)

### Community 80 - "Community 80"
Cohesion: 0.33
Nodes (10): T, TestIntegration_APIKeys_NonRootTenantForbidden(), TestIntegration_CreateAPIKey_InvalidAuthority(), TestIntegration_CreateAPIKey_MissingName(), TestIntegration_CreateAPIKey_Success(), TestIntegration_CreateAPIKey_UserAuthority(), TestIntegration_DeleteAPIKey_NotFound(), TestIntegration_DeleteAPIKey_Success() (+2 more)

### Community 82 - "Community 82"
Cohesion: 0.33
Nodes (9): validateWebhookRequest(), validateWebhookURL(), ObjectID, Time, ValidWebhookEventType(), webhookRequest, Webhook, WebhookDelivery (+1 more)

### Community 83 - "Community 83"
Cohesion: 0.40
Nodes (6): Request, ResponseWriter, Service, NewTelemetryHandler(), sanitizeProperties(), TelemetryHandler

### Community 84 - "Community 84"
Cohesion: 0.38
Nodes (5): Context, Service, SystemMetric, Time, SystemNode

### Community 85 - "Community 85"
Cohesion: 0.42
Nodes (9): ObjectID, Time, AuthCode, AuthCodeTokenData, OAuthState, RefreshToken, RevokedToken, TokenType (+1 more)

### Community 86 - "Community 86"
Cohesion: 0.42
Nodes (8): Load(), T, TestBuildVersionTakesPrecedence(), TestLoadFallbackToUnknown(), TestLoadFromBuildVersion(), TestLoadFromVersionFile(), TestLoadTrimsWhitespace(), TestLoadWalksUpDirectories()

### Community 87 - "Community 87"
Cohesion: 0.20
Nodes (10): LASTSAAS_API_KEY, LASTSAAS_URL, args, command, env, server, entry_point, mcp_config (+2 more)

### Community 88 - "Community 88"
Cohesion: 0.36
Nodes (7): BodySizeLimit(), Handler, T, TestBodySizeLimitAllowsSmallBody(), TestBodySizeLimitBlocksOversizedBody(), TestBodySizeLimitNilBody(), TestMaxBodySizeConstant()

### Community 89 - "Community 89"
Cohesion: 0.28
Nodes (7): Modal(), ModalProps, EventDefinitionModal(), FormData, Props, schema, EventDefinition

### Community 90 - "Community 90"
Cohesion: 0.22
Nodes (8): description, name, packages, repository, source, url, $schema, version

### Community 91 - "Community 91"
Cohesion: 0.36
Nodes (7): MongoDB, Time, NewAdminHandler(), TenantListItem, UserDetail, UserListItem, UserMembershipDetail

### Community 92 - "Community 92"
Cohesion: 0.39
Nodes (5): MongoDB, Request, ResponseWriter, NewUsageHandler(), UsageHandler

### Community 94 - "Community 94"
Cohesion: 0.43
Nodes (7): ObjectID, Time, DailyMetric, FinancialTransaction, InvoiceCounter, StripeMapping, TransactionType

### Community 95 - "Community 95"
Cohesion: 0.39
Nodes (7): ObjectID, Time, CreditResetPolicy, EntitlementType, EntitlementValue, Plan, PricingModel

### Community 96 - "Community 96"
Cohesion: 0.25
Nodes (8): scripts, build, dev, lint, preview, test, test:coverage, test:watch

### Community 97 - "Community 97"
Cohesion: 0.25
Nodes (3): ErrorBoundary, Props, State

### Community 98 - "Community 98"
Cohesion: 0.52
Nodes (6): ObjectID, Time, BrandingAsset, BrandingConfig, CustomPage, NavItem

### Community 99 - "Community 99"
Cohesion: 0.38
Nodes (4): ObjectID, Time, AuthMethod, User

### Community 100 - "Community 100"
Cohesion: 0.29
Nodes (6): Button(), ButtonProps, ButtonSize, ButtonVariant, sizeClasses, variantClasses

### Community 101 - "Community 101"
Cohesion: 0.33
Nodes (6): description, required, sensitive, title, type, api_key

### Community 102 - "Community 102"
Cohesion: 0.53
Nodes (5): T, TestConcurrentIncrements(), TestResendEmailsIncrement(), TestStripeAPICallsIncrement(), TestSwapResets()

### Community 103 - "Community 103"
Cohesion: 0.47
Nodes (5): ObjectID, Time, LogCategory, LogSeverity, SystemLog

### Community 104 - "Community 104"
Cohesion: 0.60
Nodes (5): CheckAndMigrate(), Context, MongoDB, runMigrations(), sendUpgradeMessage()

### Community 105 - "Community 105"
Cohesion: 0.29
Nodes (7): default, description, required, title, type, user_config, server_url

### Community 106 - "Community 106"
Cohesion: 0.50
Nodes (4): checkConfigIntegration(), cmdDoctor(), Context, MongoDB

### Community 107 - "Community 107"
Cohesion: 0.40
Nodes (3): Context, MongoDB, Seed()

### Community 108 - "Community 108"
Cohesion: 0.50
Nodes (4): ObjectID, Time, Invitation, InvitationStatus

### Community 109 - "Community 109"
Cohesion: 0.50
Nodes (4): ObjectID, Time, SSOAttributeMap, SSOConnection

### Community 110 - "Community 110"
Cohesion: 0.60
Nodes (4): T, TestComputeSignature(), TestComputeSignatureDifferentSecrets(), TestMapEventType()

### Community 111 - "Community 111"
Cohesion: 0.40
Nodes (4): name, private, type, version

### Community 112 - "Community 112"
Cohesion: 0.40
Nodes (3): AlertProps, AlertVariant, variantClasses

### Community 113 - "Community 113"
Cohesion: 0.40
Nodes (4): Badge(), BadgeProps, BadgeVariant, variantClasses

### Community 114 - "Community 114"
Cohesion: 0.83
Nodes (3): cmdDB(), cmdDBStats(), toInt64()

### Community 115 - "Community 115"
Cohesion: 0.83
Nodes (3): MongoDB, NewMessageHandler(), MessageHandler

### Community 116 - "Community 116"
Cohesion: 0.83
Nodes (3): indexOf(), replaceAll(), templateReplace()

### Community 117 - "Community 117"
Cohesion: 0.50
Nodes (3): ObjectID, Time, Announcement

### Community 118 - "Community 118"
Cohesion: 0.50
Nodes (3): ObjectID, Time, CreditBundle

### Community 119 - "Community 119"
Cohesion: 0.50
Nodes (3): ObjectID, Time, EventDefinition

### Community 120 - "Community 120"
Cohesion: 0.67
Nodes (3): T, TestRoleHasPermission(), TestValidRole()

### Community 121 - "Community 121"
Cohesion: 0.50
Nodes (3): ObjectID, Time, Message

### Community 122 - "Community 122"
Cohesion: 0.50
Nodes (3): ObjectID, Time, SystemConfig

### Community 123 - "Community 123"
Cohesion: 0.50
Nodes (3): ObjectID, Time, UsageEvent

### Community 124 - "Community 124"
Cohesion: 0.50
Nodes (3): ObjectID, Time, WebAuthnCredential

### Community 125 - "Community 125"
Cohesion: 0.50
Nodes (3): Context, MongoDB, Seed()

### Community 126 - "Community 126"
Cohesion: 0.50
Nodes (3): maintainers, $schema, jonradoff

### Community 127 - "Community 127"
Cohesion: 0.50
Nodes (4): compatibility, platforms, darwin, linux

### Community 131 - "Community 131"
Cohesion: 0.67
Nodes (3): author, name, url

### Community 132 - "Community 132"
Cohesion: 0.67
Nodes (3): repository, type, url

## Knowledge Gaps
- **284 isolated node(s):** `lastsaas`, `RegisterRequest`, `LoginRequest`, `RefreshRequest`, `MFARequiredResponse` (+279 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **18 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `main()` connect `Community 63` to `Community 129`, `Community 2`, `Community 4`, `Community 6`, `Community 7`, `Community 8`, `Community 10`, `Community 14`, `Community 16`, `Community 18`, `Community 22`, `Community 23`, `Community 26`, `Community 27`, `Community 28`, `Community 31`, `Community 39`, `Community 45`, `Community 46`, `Community 48`, `Community 54`, `Community 57`, `Community 58`, `Community 65`, `Community 66`, `Community 67`, `Community 70`, `Community 77`, `Community 83`, `Community 88`, `Community 91`, `Community 92`, `Community 104`, `Community 115`?**
  _High betweenness centrality (0.129) - this node is a cross-community bridge._
- **Why does `setupTestServer()` connect `Community 38` to `Community 2`, `Community 9`, `Community 13`, `Community 17`, `Community 23`, `Community 31`, `Community 37`, `Community 39`, `Community 40`, `Community 46`, `Community 49`, `Community 53`, `Community 57`, `Community 58`, `Community 65`, `Community 66`, `Community 67`, `Community 69`, `Community 71`, `Community 80`, `Community 91`?**
  _High betweenness centrality (0.104) - this node is a cross-community bridge._
- **Why does `Client` connect `Community 9` to `Community 33`, `Community 38`, `Community 8`, `Community 13`, `Community 46`, `Community 26`, `Community 63`?**
  _High betweenness centrality (0.073) - this node is a cross-community bridge._
- **Are the 148 inferred relationships involving `setupTestServer()` (e.g. with `TestIntegration_AdminCancelRootInvitation()` and `TestIntegration_AdminChangeRootMemberRole()`) actually correct?**
  _`setupTestServer()` has 148 INFERRED edges - model-reasoned connections that need verification._
- **Are the 143 inferred relationships involving `respondWithError()` (e.g. with `.CancelRootInvitation()` and `.ChangeRootMemberRole()`) actually correct?**
  _`respondWithError()` has 143 INFERRED edges - model-reasoned connections that need verification._
- **Are the 141 inferred relationships involving `respondWithJSON()` (e.g. with `.CancelRootInvitation()` and `.ChangeRootMemberRole()`) actually correct?**
  _`respondWithJSON()` has 141 INFERRED edges - model-reasoned connections that need verification._
- **Are the 77 inferred relationships involving `CreateTestUser()` (e.g. with `TestIntegration_AdminChangeRootMemberRole()` and `TestIntegration_AdminGetUser()`) actually correct?**
  _`CreateTestUser()` has 77 INFERRED edges - model-reasoned connections that need verification._