# 🌳 Route Tree — lastsaas

**43 top-level route(s) found.**

| Metric | Value |
|--------|-------|
| Total routes | 43 |
| Lazy-loaded | 27 |
| Protected (behind auth guard) | 0 |

## Route Hierarchy

```

📄 /setup → BootstrapPage [./pages/BootstrapPage]
📄 * → Navigate
📄 / → LandingPage [./pages/public/LandingPage]
📄 /p/:slug → CustomPage [./pages/public/CustomPage]
📄 /login → LoginPage (lazy) [./pages/auth/LoginPage]
📄 /signup → SignupPage (lazy) [./pages/auth/SignupPage]
📄 /verify-email → VerifyEmailPage (lazy) [./pages/auth/VerifyEmailPage]
📄 /forgot-password → ForgotPasswordPage (lazy) [./pages/auth/ForgotPasswordPage]
📄 /reset-password → ResetPasswordPage (lazy) [./pages/auth/ResetPasswordPage]
📄 /auth/callback → AuthCallbackPage (lazy) [./pages/auth/AuthCallbackPage]
📄 /auth/mfa → MFAChallengePage (lazy) [./pages/auth/MFAChallengePage]
📄 /auth/magic-link → MagicLinkVerifyPage (lazy) [./pages/auth/MagicLinkVerifyPage]
📄 /onboarding → OnboardingPage [./pages/app/OnboardingPage]
📄 /dashboard → DashboardPage [./pages/app/DashboardPage]
📄 /team → TeamPage [./pages/app/TeamPage]
📄 /plan → PlanPage [./pages/app/PlanPage]
📄 /buy-credits → BuyCreditsPage [./pages/app/BuyCreditsPage]
📄 /billing/success → BillingSuccessPage [./pages/app/BillingSuccessPage]
📄 /billing/cancel → BillingCancelPage [./pages/app/BillingCancelPage]
📄 /settings → SettingsPage [./pages/app/SettingsPage]
📄 /activity → ActivityPage [./pages/app/ActivityPage]
📄 /test-entitlements → TestEntitlementsPage [./pages/app/TestEntitlementsPage]
📄 /messages → AdminMessagesPage (lazy) [./pages/admin/MessagesPage]
📄 /last → AdminLayout [./components/AdminLayout]
📄 (index) → AdminDashboardPage (lazy) [./pages/admin/DashboardPage]
📄 messages → AdminMessagesPage (lazy) [./pages/admin/MessagesPage]
📄 users → AdminUsersPage (lazy) [./pages/admin/UsersPage]
📄 users/:userId → AdminUserProfilePage (lazy) [./pages/admin/UserProfilePage]
📄 tenants → AdminTenantsPage (lazy) [./pages/admin/TenantsPage]
📄 tenants/:tenantId → AdminTenantProfilePage (lazy) [./pages/admin/TenantProfilePage]
📄 members → AdminRootMembersPage (lazy) [./pages/admin/RootMembersPage]
📄 plans → AdminPlansPage (lazy) [./pages/admin/PlansPage]
📄 financial → AdminFinancialPage (lazy) [./pages/admin/FinancialPage]
📄 pm → AdminPMPage (lazy) [./pages/admin/PMPage]
📄 promotions → AdminPromotionsPage (lazy) [./pages/admin/PromotionsPage]
📄 announcements → AdminAnnouncementsPage (lazy) [./pages/admin/AnnouncementsPage]
📄 health → AdminHealthPage (lazy) [./pages/admin/HealthPage]
📄 logs → AdminLogsPage (lazy) [./pages/admin/LogsPage]
📄 config → AdminConfigPage (lazy) [./pages/admin/ConfigPage]
📄 api → AdminAPIPage (lazy) [./pages/admin/APIPage]
📄 branding → AdminBrandingPage (lazy) [./pages/admin/BrandingPage]
📄 about → AdminAboutPage (lazy) [./pages/admin/AboutPage]
📄 * → Navigate

```

## Route → Component Mapping

| Route | Component | File | Lazy? | Protected? |
|-------|-----------|------|-------|-----------|
| `/setup` | `BootstrapPage` | `./pages/BootstrapPage` | — | — |
| `*` | `Navigate` | `—` | — | — |
| `/` | `LandingPage` | `./pages/public/LandingPage` | — | — |
| `/p/:slug` | `CustomPage` | `./pages/public/CustomPage` | — | — |
| `/login` | `LoginPage` | `./pages/auth/LoginPage` | ✓ | — |
| `/signup` | `SignupPage` | `./pages/auth/SignupPage` | ✓ | — |
| `/verify-email` | `VerifyEmailPage` | `./pages/auth/VerifyEmailPage` | ✓ | — |
| `/forgot-password` | `ForgotPasswordPage` | `./pages/auth/ForgotPasswordPage` | ✓ | — |
| `/reset-password` | `ResetPasswordPage` | `./pages/auth/ResetPasswordPage` | ✓ | — |
| `/auth/callback` | `AuthCallbackPage` | `./pages/auth/AuthCallbackPage` | ✓ | — |
| `/auth/mfa` | `MFAChallengePage` | `./pages/auth/MFAChallengePage` | ✓ | — |
| `/auth/magic-link` | `MagicLinkVerifyPage` | `./pages/auth/MagicLinkVerifyPage` | ✓ | — |
| `/onboarding` | `OnboardingPage` | `./pages/app/OnboardingPage` | — | — |
| `/dashboard` | `DashboardPage` | `./pages/app/DashboardPage` | — | — |
| `/team` | `TeamPage` | `./pages/app/TeamPage` | — | — |
| `/plan` | `PlanPage` | `./pages/app/PlanPage` | — | — |
| `/buy-credits` | `BuyCreditsPage` | `./pages/app/BuyCreditsPage` | — | — |
| `/billing/success` | `BillingSuccessPage` | `./pages/app/BillingSuccessPage` | — | — |
| `/billing/cancel` | `BillingCancelPage` | `./pages/app/BillingCancelPage` | — | — |
| `/settings` | `SettingsPage` | `./pages/app/SettingsPage` | — | — |
| `/activity` | `ActivityPage` | `./pages/app/ActivityPage` | — | — |
| `/test-entitlements` | `TestEntitlementsPage` | `./pages/app/TestEntitlementsPage` | — | — |
| `/messages` | `AdminMessagesPage` | `./pages/admin/MessagesPage` | ✓ | — |
| `/last` | `AdminLayout` | `./components/AdminLayout` | — | — |
| `/` | `AdminDashboardPage` | `./pages/admin/DashboardPage` | ✓ | — |
| `messages` | `AdminMessagesPage` | `./pages/admin/MessagesPage` | ✓ | — |
| `users` | `AdminUsersPage` | `./pages/admin/UsersPage` | ✓ | — |
| `users/:userId` | `AdminUserProfilePage` | `./pages/admin/UserProfilePage` | ✓ | — |
| `tenants` | `AdminTenantsPage` | `./pages/admin/TenantsPage` | ✓ | — |
| `tenants/:tenantId` | `AdminTenantProfilePage` | `./pages/admin/TenantProfilePage` | ✓ | — |
| `members` | `AdminRootMembersPage` | `./pages/admin/RootMembersPage` | ✓ | — |
| `plans` | `AdminPlansPage` | `./pages/admin/PlansPage` | ✓ | — |
| `financial` | `AdminFinancialPage` | `./pages/admin/FinancialPage` | ✓ | — |
| `pm` | `AdminPMPage` | `./pages/admin/PMPage` | ✓ | — |
| `promotions` | `AdminPromotionsPage` | `./pages/admin/PromotionsPage` | ✓ | — |
| `announcements` | `AdminAnnouncementsPage` | `./pages/admin/AnnouncementsPage` | ✓ | — |
| `health` | `AdminHealthPage` | `./pages/admin/HealthPage` | ✓ | — |
| `logs` | `AdminLogsPage` | `./pages/admin/LogsPage` | ✓ | — |
| `config` | `AdminConfigPage` | `./pages/admin/ConfigPage` | ✓ | — |
| `api` | `AdminAPIPage` | `./pages/admin/APIPage` | ✓ | — |
| `branding` | `AdminBrandingPage` | `./pages/admin/BrandingPage` | ✓ | — |
| `about` | `AdminAboutPage` | `./pages/admin/AboutPage` | ✓ | — |
| `*` | `Navigate` | `—` | — | — |

## 💡 Bundle Impact

- **27 route(s) are lazy-loaded** — they're in separate chunks and won't affect initial bundle size
- **16 route(s) are eagerly loaded** — their components are in the main bundle
- Changing a lazy-loaded component only affects that route's chunk
- Changing a shared component (imported by multiple routes) affects ALL chunks that include it
