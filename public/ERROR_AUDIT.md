# Error Handling Audit

**Target:** `/home/z/my-project/repos/lastsaas`

## Summary (non-test files)

| Metric | Value |
| --- | --- |
| Files scanned | 101 |
| Total lines | 29,012 |
| Total error-handling sites | **932** |
| Properly handled | 707 |
| Logged only (no return) | 206 |
| Swallowed errors | 0 |
| Ignored errors (`_`) | 7 |
| Missing error checks | 11 |
| Panic on error | 1 |
| % properly handled | **75.86%** |

## Pattern Breakdown (non-test files)

| Pattern | Count | Severity |
| --- | ---: | --- |
| Proper handling | 707 | LOW |
| Logged only (no return) | 206 | MEDIUM |
| Swallowed error | 0 | HIGH |
| Ignored error (`_`) | 7 | HIGH |
| Missing error check | 11 | HIGH |
| Panic on error | 1 | MEDIUM |

## Severity Breakdown (non-test files)

| Severity | Count |
| --- | ---: |
| HIGH | 18 |
| MEDIUM | 207 |
| LOW | 707 |

## Most Problematic Files (non-test)

| File | Issues | Sites | Swallowed | Ignored | Missing | Logged | Panic |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `backend/internal/api/handlers/auth.go` | 15 | 130 | 0 | 7 | 8 | 13 | 0 |
| `backend/internal/api/handlers/admin.go` | 2 | 84 | 0 | 0 | 2 | 17 | 0 |
| `backend/internal/api/handlers/logs.go` | 1 | 11 | 0 | 0 | 1 | 1 | 0 |

## Detailed Findings (non-test files)

### `backend/cmd/lastsaas/cmd_db.go`

- **[LOW] Proper handling** — `backend/cmd/lastsaas/cmd_db.go:41` in `cmdDBStats`
  ```go
          if err != nil {
                  fmt.Fprintf(os.Stderr, "Failed to get database stats: %v\n", err)
                  os.Exit(1)
          }
  ```
- **[LOW] Proper handling** — `backend/cmd/lastsaas/cmd_db.go:48` in `cmdDBStats`
  ```go
          if err != nil {
                  fmt.Fprintf(os.Stderr, "Failed to list collections: %v\n", err)
                  os.Exit(1)
          }
  ```
- **[LOW] Proper handling** — `backend/cmd/lastsaas/cmd_db.go:65` in `cmdDBStats`
  ```go
                  if err != nil {
                          fmt.Fprintf(os.Stderr, "warning: failed to get stats for %s: %v\n", cName, err)
                          continue
                  }
  ```

### `backend/cmd/lastsaas/cmd_doctor.go`

- **[MEDIUM] Logged only (no return)** — `backend/cmd/lastsaas/cmd_doctor.go:57` in `cmdDoctor`
  ```go
                  if err := database.Close(ctx); err != nil {
                          fmt.Fprintf(os.Stderr, "warning: failed to close database: %v\n", err)
                  }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/cmd/lastsaas/cmd_doctor.go:107` in `cmdDoctor`
  ```go
                          if err != nil {
                                  fmt.Fprintf(os.Stderr, "warning: failed to count root tenant owners: %v\n", err)
                          }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/cmd/lastsaas/cmd_doctor.go:118` in `cmdDoctor`
  ```go
          if err != nil {
                  fmt.Fprintf(os.Stderr, "warning: failed to count active nodes: %v\n", err)
          }
  ```
- **[LOW] Proper handling** — `backend/cmd/lastsaas/cmd_doctor.go:42` in `cmdDoctor`
  ```go
          if err != nil {
                  fmt.Printf("\n  Results: %d passed, %d warnings, %d failed\n", passes, warnings, failures)
                  os.Exit(1)
          }
  ```
- **[LOW] Proper handling** — `backend/cmd/lastsaas/cmd_doctor.go:50` in `cmdDoctor`
  ```go
          if err != nil {
                  fmt.Printf("\n  Results: %d passed, %d warnings, %d failed\n", passes, warnings, failures)
                  os.Exit(1)
          }
  ```

### `backend/cmd/lastsaas/cmd_financial.go`

- **[MEDIUM] Logged only (no return)** — `backend/cmd/lastsaas/cmd_financial.go:59` in `cmdFinancialSummary`
  ```go
          if err != nil {
                  fmt.Fprintf(os.Stderr, "warning: failed to aggregate revenue: %v\n", err)
          }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/cmd/lastsaas/cmd_financial.go:85` in `cmdFinancialSummary`
  ```go
          if err != nil {
                  fmt.Fprintf(os.Stderr, "warning: failed to aggregate refunds: %v\n", err)
          }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/cmd/lastsaas/cmd_financial.go:112` in `cmdFinancialSummary`
  ```go
          if err != nil {
                  fmt.Fprintf(os.Stderr, "warning: failed to aggregate revenue by type: %v\n", err)
          }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/cmd/lastsaas/cmd_financial.go:132` in `cmdFinancialSummary`
  ```go
          if err != nil {
                  fmt.Fprintf(os.Stderr, "warning: failed to count active subscriptions: %v\n", err)
          }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/cmd/lastsaas/cmd_financial.go:148` in `cmdFinancialSummary`
  ```go
          if err != nil {
                  fmt.Fprintf(os.Stderr, "warning: failed to aggregate 30d revenue: %v\n", err)
          }
  ```
- **[LOW] Proper handling** — `backend/cmd/lastsaas/cmd_financial.go:214` in `cmdFinancialTransactions`
  ```go
          if err := fs.Parse(os.Args[3:]); err != nil {
                  fmt.Fprintf(os.Stderr, "error: %v\n", err)
                  os.Exit(1)
          }
  ```
- **[LOW] Proper handling** — `backend/cmd/lastsaas/cmd_financial.go:255` in `cmdFinancialTransactions`
  ```go
          if err != nil {
                  fmt.Fprintf(os.Stderr, "Failed to query transactions: %v\n", err)
                  os.Exit(1)
          }
  ```
- **[LOW] Proper handling** — `backend/cmd/lastsaas/cmd_financial.go:262` in `cmdFinancialTransactions`
  ```go
          if err := cursor.All(ctx, &txns); err != nil {
                  fmt.Fprintf(os.Stderr, "Failed to read transactions: %v\n", err)
                  os.Exit(1)
          }
  ```
- **[LOW] Proper handling** — `backend/cmd/lastsaas/cmd_financial.go:335` in `cmdFinancialMetrics`
  ```go
          if err := fs.Parse(os.Args[3:]); err != nil {
                  fmt.Fprintf(os.Stderr, "error: %v\n", err)
                  os.Exit(1)
          }
  ```
- **[LOW] Proper handling** — `backend/cmd/lastsaas/cmd_financial.go:351` in `cmdFinancialMetrics`
  ```go
          if err != nil {
                  fmt.Fprintf(os.Stderr, "Failed to query daily metrics: %v\n", err)
                  os.Exit(1)
          }
  ```
- **[LOW] Proper handling** — `backend/cmd/lastsaas/cmd_financial.go:358` in `cmdFinancialMetrics`
  ```go
          if err := cursor.All(ctx, &metrics); err != nil {
                  fmt.Fprintf(os.Stderr, "Failed to read metrics: %v\n", err)
                  os.Exit(1)
          }
  ```

### `backend/cmd/lastsaas/cmd_health.go`

- **[MEDIUM] Logged only (no return)** — `backend/cmd/lastsaas/cmd_health.go:53` in `cmdHealth`
  ```go
                  if err != nil {
                          fmt.Fprintf(os.Stderr, "warning: failed to query nodes: %v\n", err)
                  }
  ```

### `backend/cmd/lastsaas/cmd_logs.go`

- **[LOW] Proper handling** — `backend/cmd/lastsaas/cmd_logs.go:27` in `cmdLogs`
  ```go
          if err := fs.Parse(os.Args[2:]); err != nil {
                  fmt.Fprintf(os.Stderr, "error: %v\n", err)
                  os.Exit(1)
          }
  ```
- **[LOW] Proper handling** — `backend/cmd/lastsaas/cmd_logs.go:141` in `queryLogs`
  ```go
          if err != nil {
                  fmt.Fprintf(os.Stderr, "Failed to query logs: %v\n", err)
                  os.Exit(1)
          }
  ```
- **[LOW] Proper handling** — `backend/cmd/lastsaas/cmd_logs.go:148` in `queryLogs`
  ```go
          if err := cursor.All(ctx, &logs); err != nil {
                  fmt.Fprintf(os.Stderr, "Failed to read logs: %v\n", err)
                  os.Exit(1)
          }
  ```
- **[LOW] Proper handling** — `backend/cmd/lastsaas/cmd_logs.go:194` in `logsFollow`
  ```go
                  if err != nil {
                          fmt.Fprintf(os.Stderr, "warning: failed to query logs: %v\n", err)
                          continue
                  }
  ```

### `backend/cmd/lastsaas/cmd_mcp.go`

- **[MEDIUM] Logged only (no return)** — `backend/cmd/lastsaas/cmd_mcp.go:70` in `prettyJSON`
  ```go
          if err := json.Indent(&buf, data, "", "  "); err != nil {
                  fmt.Fprintf(os.Stderr, "warning: failed to pretty-print JSON: %v\n", err)
                  return string(data)
          }
  ```
- **[LOW] Proper handling** — `backend/cmd/lastsaas/cmd_mcp.go:42` in `get`
  ```go
          if err != nil {
                  return nil, fmt.Errorf("failed to create request: %w", err)
          }
  ```
- **[LOW] Proper handling** — `backend/cmd/lastsaas/cmd_mcp.go:48` in `get`
  ```go
          if err != nil {
                  return nil, fmt.Errorf("request failed: %w", err)
          }
  ```
- **[LOW] Proper handling** — `backend/cmd/lastsaas/cmd_mcp.go:54` in `get`
  ```go
          if err != nil {
                  return nil, fmt.Errorf("failed to read response: %w", err)
          }
  ```
- **[LOW] Proper handling** — `backend/cmd/lastsaas/cmd_mcp.go:133` in `cmdMCP`
  ```go
          if err := server.ServeStdio(s); err != nil {
                  fmt.Fprintf(os.Stderr, "MCP server error: %v\n", err)
                  os.Exit(1)
          }
  ```
- **[LOW] Proper handling** — `backend/cmd/lastsaas/cmd_mcp.go:151` in `registerAboutTools`
  ```go
                          if err != nil {
                                  return mcp.NewToolResultError(err.Error()), nil
                          }
  ```
- **[LOW] Proper handling** — `backend/cmd/lastsaas/cmd_mcp.go:171` in `registerDashboardTools`
  ```go
                          if err != nil {
                                  return mcp.NewToolResultError(err.Error()), nil
                          }
  ```
- **[LOW] Proper handling** — `backend/cmd/lastsaas/cmd_mcp.go:210` in `registerTenantTools`
  ```go
                          if err != nil {
                                  return mcp.NewToolResultError(err.Error()), nil
                          }
  ```
- **[LOW] Proper handling** — `backend/cmd/lastsaas/cmd_mcp.go:226` in `registerTenantTools`
  ```go
                          if err != nil {
                                  return mcp.NewToolResultError("id is required: " + err.Error()), nil
                          }
  ```
- **[LOW] Proper handling** — `backend/cmd/lastsaas/cmd_mcp.go:230` in `registerTenantTools`
  ```go
                          if err != nil {
                                  return mcp.NewToolResultError(err.Error()), nil
                          }
  ```
- **[LOW] Proper handling** — `backend/cmd/lastsaas/cmd_mcp.go:267` in `registerUserTools`
  ```go
                          if err != nil {
                                  return mcp.NewToolResultError(err.Error()), nil
                          }
  ```
- **[LOW] Proper handling** — `backend/cmd/lastsaas/cmd_mcp.go:283` in `registerUserTools`
  ```go
                          if err != nil {
                                  return mcp.NewToolResultError("id is required: " + err.Error()), nil
                          }
  ```
- **[LOW] Proper handling** — `backend/cmd/lastsaas/cmd_mcp.go:287` in `registerUserTools`
  ```go
                          if err != nil {
                                  return mcp.NewToolResultError(err.Error()), nil
                          }
  ```
- **[LOW] Proper handling** — `backend/cmd/lastsaas/cmd_mcp.go:322` in `registerFinancialTools`
  ```go
                          if err != nil {
                                  return mcp.NewToolResultError(err.Error()), nil
                          }
  ```
- **[LOW] Proper handling** — `backend/cmd/lastsaas/cmd_mcp.go:343` in `registerFinancialTools`
  ```go
                          if err != nil {
                                  return mcp.NewToolResultError(err.Error()), nil
                          }
  ```
- **[LOW] Proper handling** — `backend/cmd/lastsaas/cmd_mcp.go:384` in `registerLogTools`
  ```go
                          if err != nil {
                                  return mcp.NewToolResultError(err.Error()), nil
                          }
  ```
- **[LOW] Proper handling** — `backend/cmd/lastsaas/cmd_mcp.go:399` in `registerLogTools`
  ```go
                          if err != nil {
                                  return mcp.NewToolResultError(err.Error()), nil
                          }
  ```
- **[LOW] Proper handling** — `backend/cmd/lastsaas/cmd_mcp.go:420` in `registerHealthTools`
  ```go
                          if err != nil {
                                  return mcp.NewToolResultError(err.Error()), nil
                          }
  ```
- **[LOW] Proper handling** — `backend/cmd/lastsaas/cmd_mcp.go:441` in `registerHealthTools`
  ```go
                          if err != nil {
                                  return mcp.NewToolResultError(err.Error()), nil
                          }
  ```
- **[LOW] Proper handling** — `backend/cmd/lastsaas/cmd_mcp.go:456` in `registerHealthTools`
  ```go
                          if err != nil {
                                  return mcp.NewToolResultError(err.Error()), nil
                          }
  ```
- **[LOW] Proper handling** — `backend/cmd/lastsaas/cmd_mcp.go:471` in `registerHealthTools`
  ```go
                          if err != nil {
                                  return mcp.NewToolResultError(err.Error()), nil
                          }
  ```
- **[LOW] Proper handling** — `backend/cmd/lastsaas/cmd_mcp.go:492` in `registerConfigTools`
  ```go
                          if err != nil {
                                  return mcp.NewToolResultError(err.Error()), nil
                          }
  ```
- **[LOW] Proper handling** — `backend/cmd/lastsaas/cmd_mcp.go:508` in `registerConfigTools`
  ```go
                          if err != nil {
                                  return mcp.NewToolResultError("name is required: " + err.Error()), nil
                          }
  ```
- **[LOW] Proper handling** — `backend/cmd/lastsaas/cmd_mcp.go:512` in `registerConfigTools`
  ```go
                          if err != nil {
                                  return mcp.NewToolResultError(err.Error()), nil
                          }
  ```
- **[LOW] Proper handling** — `backend/cmd/lastsaas/cmd_mcp.go:533` in `registerPlanTools`
  ```go
                          if err != nil {
                                  return mcp.NewToolResultError(err.Error()), nil
                          }
  ```
- **[LOW] Proper handling** — `backend/cmd/lastsaas/cmd_mcp.go:549` in `registerPlanTools`
  ```go
                          if err != nil {
                                  return mcp.NewToolResultError("id is required: " + err.Error()), nil
                          }
  ```
- **[LOW] Proper handling** — `backend/cmd/lastsaas/cmd_mcp.go:553` in `registerPlanTools`
  ```go
                          if err != nil {
                                  return mcp.NewToolResultError(err.Error()), nil
                          }
  ```
- **[LOW] Proper handling** — `backend/cmd/lastsaas/cmd_mcp.go:568` in `registerPlanTools`
  ```go
                          if err != nil {
                                  return mcp.NewToolResultError(err.Error()), nil
                          }
  ```
- **[LOW] Proper handling** — `backend/cmd/lastsaas/cmd_mcp.go:583` in `registerPlanTools`
  ```go
                          if err != nil {
                                  return mcp.NewToolResultError(err.Error()), nil
                          }
  ```
- **[LOW] Proper handling** — `backend/cmd/lastsaas/cmd_mcp.go:604` in `registerAnnouncementTools`
  ```go
                          if err != nil {
                                  return mcp.NewToolResultError(err.Error()), nil
                          }
  ```
- **[LOW] Proper handling** — `backend/cmd/lastsaas/cmd_mcp.go:625` in `registerPromotionTools`
  ```go
                          if err != nil {
                                  return mcp.NewToolResultError(err.Error()), nil
                          }
  ```
- **[LOW] Proper handling** — `backend/cmd/lastsaas/cmd_mcp.go:646` in `registerSecurityTools`
  ```go
                          if err != nil {
                                  return mcp.NewToolResultError(err.Error()), nil
                          }
  ```
- **[LOW] Proper handling** — `backend/cmd/lastsaas/cmd_mcp.go:661` in `registerSecurityTools`
  ```go
                          if err != nil {
                                  return mcp.NewToolResultError(err.Error()), nil
                          }
  ```
- **[LOW] Proper handling** — `backend/cmd/lastsaas/cmd_mcp.go:682` in `registerWebhookTools`
  ```go
                          if err != nil {
                                  return mcp.NewToolResultError(err.Error()), nil
                          }
  ```
- **[LOW] Proper handling** — `backend/cmd/lastsaas/cmd_mcp.go:697` in `registerWebhookTools`
  ```go
                          if err != nil {
                                  return mcp.NewToolResultError(err.Error()), nil
                          }
  ```
- **[LOW] Proper handling** — `backend/cmd/lastsaas/cmd_mcp.go:713` in `registerWebhookTools`
  ```go
                          if err != nil {
                                  return mcp.NewToolResultError("id is required: " + err.Error()), nil
                          }
  ```
- **[LOW] Proper handling** — `backend/cmd/lastsaas/cmd_mcp.go:717` in `registerWebhookTools`
  ```go
                          if err != nil {
                                  return mcp.NewToolResultError(err.Error()), nil
                          }
  ```
- **[LOW] Proper handling** — `backend/cmd/lastsaas/cmd_mcp.go:742` in `registerPMTools`
  ```go
                          if err != nil {
                                  return mcp.NewToolResultError(err.Error()), nil
                          }
  ```
- **[LOW] Proper handling** — `backend/cmd/lastsaas/cmd_mcp.go:757` in `registerPMTools`
  ```go
                          if err != nil {
                                  return mcp.NewToolResultError(err.Error()), nil
                          }
  ```
- **[LOW] Proper handling** — `backend/cmd/lastsaas/cmd_mcp.go:780` in `registerPMTools`
  ```go
                          if err != nil {
                                  return mcp.NewToolResultError(err.Error()), nil
                          }
  ```
- **[LOW] Proper handling** — `backend/cmd/lastsaas/cmd_mcp.go:799` in `registerPMTools`
  ```go
                          if err != nil {
                                  return mcp.NewToolResultError(err.Error()), nil
                          }
  ```
- **[LOW] Proper handling** — `backend/cmd/lastsaas/cmd_mcp.go:816` in `registerPMTools`
  ```go
                          if err != nil {
                                  return mcp.NewToolResultError("name is required: " + err.Error()), nil
                          }
  ```
- **[LOW] Proper handling** — `backend/cmd/lastsaas/cmd_mcp.go:824` in `registerPMTools`
  ```go
                          if err != nil {
                                  return mcp.NewToolResultError(err.Error()), nil
                          }
  ```
- **[LOW] Proper handling** — `backend/cmd/lastsaas/cmd_mcp.go:839` in `registerPMTools`
  ```go
                          if err != nil {
                                  return mcp.NewToolResultError(err.Error()), nil
                          }
  ```
- **[LOW] Proper handling** — `backend/cmd/lastsaas/cmd_mcp.go:862` in `registerResources`
  ```go
                          if err != nil {
                                  return nil, fmt.Errorf("failed to fetch dashboard: %w", err)
                          }
  ```
- **[LOW] Proper handling** — `backend/cmd/lastsaas/cmd_mcp.go:885` in `registerResources`
  ```go
                          if err != nil {
                                  return nil, fmt.Errorf("failed to fetch health: %w", err)
                          }
  ```

### `backend/cmd/lastsaas/cmd_stats.go`

- **[MEDIUM] Logged only (no return)** — `backend/cmd/lastsaas/cmd_stats.go:24` in `cmdStats`
  ```go
          if err != nil {
                  fmt.Fprintf(os.Stderr, "warning: failed to count users: %v\n", err)
          }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/cmd/lastsaas/cmd_stats.go:28` in `cmdStats`
  ```go
          if err != nil {
                  fmt.Fprintf(os.Stderr, "warning: failed to count tenants: %v\n", err)
          }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/cmd/lastsaas/cmd_stats.go:34` in `cmdStats`
  ```go
          if err != nil {
                  fmt.Fprintf(os.Stderr, "warning: failed to count active users: %v\n", err)
          }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/cmd/lastsaas/cmd_stats.go:42` in `cmdStats`
  ```go
          if err != nil {
                  fmt.Fprintf(os.Stderr, "warning: failed to count active subscriptions: %v\n", err)
          }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/cmd/lastsaas/cmd_stats.go:54` in `cmdStats`
  ```go
          if err != nil {
                  fmt.Fprintf(os.Stderr, "warning: failed to aggregate log counts: %v\n", err)
          }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/cmd/lastsaas/cmd_stats.go:82` in `cmdStats`
  ```go
          if err != nil {
                  fmt.Fprintf(os.Stderr, "warning: failed to aggregate revenue: %v\n", err)
          }
  ```

### `backend/cmd/lastsaas/cmd_tenants.go`

- **[MEDIUM] Logged only (no return)** — `backend/cmd/lastsaas/cmd_tenants.go:290` in `resolveUserNames`
  ```go
          if err != nil {
                  fmt.Fprintf(os.Stderr, "warning: failed to query users: %v\n", err)
                  return result
          }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/cmd/lastsaas/cmd_tenants.go:318` in `resolvePlanNames`
  ```go
          if err != nil {
                  fmt.Fprintf(os.Stderr, "warning: failed to query plans: %v\n", err)
                  return names
          }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/cmd/lastsaas/cmd_tenants.go:356` in `countMembersPerTenant`
  ```go
          if err != nil {
                  fmt.Fprintf(os.Stderr, "warning: failed to aggregate member counts: %v\n", err)
                  return counts
          }
  ```
- **[LOW] Proper handling** — `backend/cmd/lastsaas/cmd_tenants.go:46` in `cmdTenantsList`
  ```go
          if err := fs.Parse(os.Args[3:]); err != nil {
                  fmt.Fprintf(os.Stderr, "error: %v\n", err)
                  os.Exit(1)
          }
  ```
- **[LOW] Proper handling** — `backend/cmd/lastsaas/cmd_tenants.go:62` in `cmdTenantsList`
  ```go
          if err != nil {
                  fmt.Fprintf(os.Stderr, "Failed to query tenants: %v\n", err)
                  os.Exit(1)
          }
  ```
- **[LOW] Proper handling** — `backend/cmd/lastsaas/cmd_tenants.go:69` in `cmdTenantsList`
  ```go
          if err := cursor.All(ctx, &tenants); err != nil {
                  fmt.Fprintf(os.Stderr, "Failed to read tenants: %v\n", err)
                  os.Exit(1)
          }
  ```
- **[LOW] Proper handling** — `backend/cmd/lastsaas/cmd_tenants.go:174` in `cmdTenantsGet`
  ```go
          if err != nil {
                  fmt.Fprintf(os.Stderr, "Failed to query memberships: %v\n", err)
                  os.Exit(1)
          }
  ```

### `backend/cmd/lastsaas/cmd_users.go`

- **[MEDIUM] Logged only (no return)** — `backend/cmd/lastsaas/cmd_users.go:366` in `lookupUserWithMemberships`
  ```go
          if err != nil {
                  fmt.Fprintf(os.Stderr, "warning: failed to query memberships: %v\n", err)
                  return user, nil
          }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/cmd/lastsaas/cmd_users.go:384` in `resolveTenantNames`
  ```go
          if err != nil {
                  fmt.Fprintf(os.Stderr, "warning: failed to query tenants: %v\n", err)
                  return names
          }
  ```
- **[LOW] Proper handling** — `backend/cmd/lastsaas/cmd_users.go:53` in `cmdUsersList`
  ```go
          if err := fs.Parse(os.Args[3:]); err != nil {
                  fmt.Fprintf(os.Stderr, "error: %v\n", err)
                  os.Exit(1)
          }
  ```
- **[LOW] Proper handling** — `backend/cmd/lastsaas/cmd_users.go:74` in `cmdUsersList`
  ```go
          if err != nil {
                  fmt.Fprintf(os.Stderr, "Failed to query users: %v\n", err)
                  os.Exit(1)
          }
  ```
- **[LOW] Proper handling** — `backend/cmd/lastsaas/cmd_users.go:81` in `cmdUsersList`
  ```go
          if err := cursor.All(ctx, &users); err != nil {
                  fmt.Fprintf(os.Stderr, "Failed to read users: %v\n", err)
                  os.Exit(1)
          }
  ```
- **[LOW] Proper handling** — `backend/cmd/lastsaas/cmd_users.go:155` in `cmdUsersGet`
  ```go
          if err := fs.Parse(os.Args[3:]); err != nil {
                  fmt.Fprintf(os.Stderr, "error: %v\n", err)
                  os.Exit(1)
          }
  ```
- **[LOW] Proper handling** — `backend/cmd/lastsaas/cmd_users.go:269` in `cmdUsersSetActive`
  ```go
          if err := fs.Parse(os.Args[3:]); err != nil {
                  fmt.Fprintf(os.Stderr, "error: %v\n", err)
                  os.Exit(1)
          }
  ```
- **[LOW] Proper handling** — `backend/cmd/lastsaas/cmd_users.go:305` in `cmdUsersSetActive`
  ```go
          if err != nil {
                  fmt.Fprintf(os.Stderr, "Failed to update user: %v\n", err)
                  os.Exit(1)
          }
  ```
- **[LOW] Proper handling** — `backend/cmd/lastsaas/cmd_users.go:324` in `cmdUsersRevokeSessions`
  ```go
          if err := fs.Parse(os.Args[3:]); err != nil {
                  fmt.Fprintf(os.Stderr, "error: %v\n", err)
                  os.Exit(1)
          }
  ```
- **[LOW] Proper handling** — `backend/cmd/lastsaas/cmd_users.go:348` in `cmdUsersRevokeSessions`
  ```go
          if err != nil {
                  fmt.Fprintf(os.Stderr, "Failed to revoke sessions: %v\n", err)
                  os.Exit(1)
          }
  ```

### `backend/cmd/lastsaas/main.go`

- **[MEDIUM] Logged only (no return)** — `backend/cmd/lastsaas/main.go:169` in `connectDB`
  ```go
                  if err := database.Close(ctx); err != nil {
                          fmt.Fprintf(os.Stderr, "warning: failed to close database: %v\n", err)
                  }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/cmd/lastsaas/main.go:379` in `cmdSetup`
  ```go
          if _, err := database.Messages().InsertOne(ctx, welcomeMsg); err != nil {
                  fmt.Fprintf(os.Stderr, "warning: failed to insert welcome message: %v\n", err)
          }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/cmd/lastsaas/main.go:818` in `cmdTransferRootOwner`
  ```go
          if err != nil {
                  fmt.Fprintf(os.Stderr, "warning: failed to read input: %v\n", err)
          }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/cmd/lastsaas/main.go:862` in `cmdTransferRootOwner`
  ```go
          if _, err := database.SystemLogs().InsertOne(ctx, logEntry); err != nil {
                  fmt.Fprintf(os.Stderr, "warning: failed to write system log: %v\n", err)
          }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/cmd/lastsaas/main.go:886` in `cmdVersion`
  ```go
          if err != nil {
                  fmt.Fprintf(os.Stderr, "warning: failed to read system config: %v\n", err)
          }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/cmd/lastsaas/main.go:889` in `cmdVersion`
  ```go
          if err != nil || !sys.Initialized {
                  fmt.Println("DB version:  (not initialized)")
                  return
          }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/cmd/lastsaas/main.go:907` in `cmdStatus`
  ```go
          if err != nil {
                  fmt.Printf("Config:      ERROR - %v\n", err)
                  return
          }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/cmd/lastsaas/main.go:914` in `cmdStatus`
  ```go
          if err != nil {
                  fmt.Printf("MongoDB:     ERROR - %v\n", err)
                  return
          }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/cmd/lastsaas/main.go:921` in `cmdStatus`
  ```go
                  if err := database.Close(ctx); err != nil {
                          fmt.Fprintf(os.Stderr, "warning: failed to close database: %v\n", err)
                  }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/cmd/lastsaas/main.go:932` in `cmdStatus`
  ```go
          if err != nil {
                  fmt.Fprintf(os.Stderr, "warning: failed to read system config: %v\n", err)
          }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/cmd/lastsaas/main.go:935` in `cmdStatus`
  ```go
          if err != nil || !sys.Initialized {
                  fmt.Println("Initialized: No")
                  fmt.Println()
                  fmt.Println("Run 'lastsaas setup' to initialize the system.")
                  return
          }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/cmd/lastsaas/main.go:947` in `cmdStatus`
  ```go
          if err != nil {
                  fmt.Fprintf(os.Stderr, "warning: failed to count users: %v\n", err)
          }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/cmd/lastsaas/main.go:951` in `cmdStatus`
  ```go
          if err != nil {
                  fmt.Fprintf(os.Stderr, "warning: failed to count tenants: %v\n", err)
          }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/cmd/lastsaas/main.go:963` in `prompt`
  ```go
          if err != nil {
                  fmt.Fprintf(os.Stderr, "warning: failed to read input: %v\n", err)
          }
  ```
- **[LOW] Proper handling** — `backend/cmd/lastsaas/main.go:153` in `connectDB`
  ```go
          if err != nil {
                  fmt.Fprintf(os.Stderr, "Error loading config: %v\n\n", err)
                  printConfigHelp(env)
                  os.Exit(1)
          }
  ```
- **[LOW] Proper handling** — `backend/cmd/lastsaas/main.go:160` in `connectDB`
  ```go
          if err != nil {
                  fmt.Fprintf(os.Stderr, "Error connecting to MongoDB: %v\n\n", err)
                  printMongoHelp(env)
                  os.Exit(1)
          }
  ```
- **[LOW] Proper handling** — `backend/cmd/lastsaas/main.go:275` in `cmdSetup`
  ```go
          if err := passwordService.ValidatePasswordStrength(password); err != nil {
                  fmt.Fprintf(os.Stderr, "Password too weak: %v\n", err)
                  fmt.Fprintln(os.Stderr, "Requirements: 10+ characters, uppercase, lowercase, number, special character")
                  os.Exit(1)
          }
  ```
- **[LOW] Proper handling** — `backend/cmd/lastsaas/main.go:282` in `cmdSetup`
  ```go
          if err != nil {
                  fmt.Fprintf(os.Stderr, "Failed to hash password: %v\n", err)
                  os.Exit(1)
          }
  ```
- **[LOW] Proper handling** — `backend/cmd/lastsaas/main.go:299` in `cmdSetup`
  ```go
          if err := validation.Validate(&tenant); err != nil {
                  fmt.Fprintf(os.Stderr, "Tenant validation failed: %v\n", err)
                  os.Exit(1)
          }
  ```
- **[LOW] Proper handling** — `backend/cmd/lastsaas/main.go:303` in `cmdSetup`
  ```go
          if _, err := database.Tenants().InsertOne(ctx, tenant); err != nil {
                  fmt.Fprintf(os.Stderr, "Failed to create root tenant: %v\n", err)
                  os.Exit(1)
          }
  ```
- **[LOW] Proper handling** — `backend/cmd/lastsaas/main.go:320` in `cmdSetup`
  ```go
          if err := validation.Validate(&user); err != nil {
                  database.Tenants().DeleteOne(ctx, bson.M{"_id": tenant.ID})
                  fmt.Fprintf(os.Stderr, "User validation failed: %v\n", err)
                  os.Exit(1)
          }
  ```
- **[LOW] Proper handling** — `backend/cmd/lastsaas/main.go:325` in `cmdSetup`
  ```go
          if _, err := database.Users().InsertOne(ctx, user); err != nil {
                  database.Tenants().DeleteOne(ctx, bson.M{"_id": tenant.ID})
                  fmt.Fprintf(os.Stderr, "Failed to create user: %v\n", err)
                  os.Exit(1)
          }
  ```
- **[LOW] Proper handling** — `backend/cmd/lastsaas/main.go:340` in `cmdSetup`
  ```go
          if err := validation.Validate(&membership); err != nil {
                  database.Users().DeleteOne(ctx, bson.M{"_id": user.ID})
                  database.Tenants().DeleteOne(ctx, bson.M{"_id": tenant.ID})
                  fmt.Fprintf(os.Stderr, "Membership validation failed: %v\n", err)
                  os.Exit(1)
          }
  ```
- **[LOW] Proper handling** — `backend/cmd/lastsaas/main.go:346` in `cmdSetup`
  ```go
          if _, err := database.TenantMemberships().InsertOne(ctx, membership); err != nil {
                  database.Users().DeleteOne(ctx, bson.M{"_id": user.ID})
                  database.Tenants().DeleteOne(ctx, bson.M{"_id": tenant.ID})
                  fmt.Fprintf(os.Stderr, "Failed to create membership: %v\n", err)
                  os.Exit(1)
          }
  ```
- **[LOW] Proper handling** — `backend/cmd/lastsaas/main.go:361` in `cmdSetup`
  ```go
          if _, err := database.SystemConfig().InsertOne(ctx, sysConfig); err != nil {
                  database.TenantMemberships().DeleteOne(ctx, bson.M{"_id": membership.ID})
                  database.Users().DeleteOne(ctx, bson.M{"_id": user.ID})
                  database.Tenants().DeleteOne(ctx, bson.M{"_id": tenant.ID})
                  fmt.Fprintf(os.Stderr, "Failed to mark system as initialized: %v\n", err)
                  os.Exit(1)
  ... (1 more lines)
  ```
- **[LOW] Proper handling** — `backend/cmd/lastsaas/main.go:398` in `cmdChangePassword`
  ```go
          if err := fs.Parse(os.Args[2:]); err != nil {
                  fmt.Fprintf(os.Stderr, "error: %v\n", err)
                  os.Exit(1)
          }
  ```
- **[LOW] Proper handling** — `backend/cmd/lastsaas/main.go:418` in `cmdChangePassword`
  ```go
          if err != nil {
                  fmt.Fprintf(os.Stderr, "User not found: %s\n", email)
                  os.Exit(1)
          }
  ```
- **[LOW] Proper handling** — `backend/cmd/lastsaas/main.go:435` in `cmdChangePassword`
  ```go
          if err := passwordService.ValidatePasswordStrength(password); err != nil {
                  fmt.Fprintf(os.Stderr, "Password too weak: %v\n", err)
                  fmt.Fprintln(os.Stderr, "Requirements: 10+ characters, uppercase, lowercase, number, special character")
                  os.Exit(1)
          }
  ```
- **[LOW] Proper handling** — `backend/cmd/lastsaas/main.go:442` in `cmdChangePassword`
  ```go
          if err != nil {
                  fmt.Fprintf(os.Stderr, "Failed to hash password: %v\n", err)
                  os.Exit(1)
          }
  ```
- **[LOW] Proper handling** — `backend/cmd/lastsaas/main.go:454` in `cmdChangePassword`
  ```go
          if err != nil {
                  fmt.Fprintf(os.Stderr, "Failed to update password: %v\n", err)
                  os.Exit(1)
          }
  ```
- **[LOW] Proper handling** — `backend/cmd/lastsaas/main.go:474` in `cmdSendMessage`
  ```go
          if err := fs.Parse(os.Args[2:]); err != nil {
                  fmt.Fprintf(os.Stderr, "error: %v\n", err)
                  os.Exit(1)
          }
  ```
- **[LOW] Proper handling** — `backend/cmd/lastsaas/main.go:516` in `cmdSendMessage`
  ```go
          if err != nil {
                  fmt.Fprintf(os.Stderr, "User not found: %s\n", email)
                  os.Exit(1)
          }
  ```
- **[LOW] Proper handling** — `backend/cmd/lastsaas/main.go:531` in `cmdSendMessage`
  ```go
          if _, err := database.Messages().InsertOne(ctx, msg); err != nil {
                  fmt.Fprintf(os.Stderr, "Failed to send message: %v\n", err)
                  os.Exit(1)
          }
  ```
- **[LOW] Proper handling** — `backend/cmd/lastsaas/main.go:588` in `cmdConfigList`
  ```go
          if err != nil {
                  fmt.Fprintf(os.Stderr, "Failed to query config vars: %v\n", err)
                  os.Exit(1)
          }
  ```
- **[LOW] Proper handling** — `backend/cmd/lastsaas/main.go:595` in `cmdConfigList`
  ```go
          if err := cursor.All(ctx, &vars); err != nil {
                  fmt.Fprintf(os.Stderr, "Failed to read config vars: %v\n", err)
                  os.Exit(1)
          }
  ```
- **[LOW] Proper handling** — `backend/cmd/lastsaas/main.go:636` in `cmdConfigGet`
  ```go
          if err != nil {
                  fmt.Fprintf(os.Stderr, "Config variable not found: %s\n", name)
                  os.Exit(1)
          }
  ```
- **[LOW] Proper handling** — `backend/cmd/lastsaas/main.go:666` in `cmdConfigSet`
  ```go
          if err != nil {
                  fmt.Fprintf(os.Stderr, "Config variable not found: %s\n", name)
                  os.Exit(1)
          }
  ```
- **[LOW] Proper handling** — `backend/cmd/lastsaas/main.go:671` in `cmdConfigSet`
  ```go
          if err := configstore.ValidateValue(v.Type, value, v.Options); err != nil {
                  fmt.Fprintf(os.Stderr, "Invalid value: %v\n", err)
                  os.Exit(1)
          }
  ```
- **[LOW] Proper handling** — `backend/cmd/lastsaas/main.go:680` in `cmdConfigSet`
  ```go
          if err != nil {
                  fmt.Fprintf(os.Stderr, "Failed to update config variable: %v\n", err)
                  os.Exit(1)
          }
  ```
- **[LOW] Proper handling** — `backend/cmd/lastsaas/main.go:714` in `cmdConfigReset`
  ```go
          if err != nil {
                  fmt.Fprintf(os.Stderr, "Config variable not found in database: %s\n", name)
                  os.Exit(1)
          }
  ```
- **[LOW] Proper handling** — `backend/cmd/lastsaas/main.go:728` in `cmdConfigReset`
  ```go
          if err != nil {
                  fmt.Fprintf(os.Stderr, "Failed to reset config variable: %v\n", err)
                  os.Exit(1)
          }
  ```
- **[LOW] Proper handling** — `backend/cmd/lastsaas/main.go:742` in `cmdTransferRootOwner`
  ```go
          if err := fs.Parse(os.Args[2:]); err != nil {
                  fmt.Fprintf(os.Stderr, "error: %v\n", err)
                  os.Exit(1)
          }
  ```
- **[LOW] Proper handling** — `backend/cmd/lastsaas/main.go:835` in `cmdTransferRootOwner`
  ```go
          if err != nil {
                  fmt.Fprintf(os.Stderr, "Failed to demote current owner: %v\n", err)
                  os.Exit(1)
          }
  ```
- **[LOW] Proper handling** — `backend/cmd/lastsaas/main.go:845` in `cmdTransferRootOwner`
  ```go
          if err != nil {
                  // Try to rollback
                  database.TenantMemberships().UpdateOne(ctx,
                          bson.M{"_id": currentOwnerMembership.ID},
                          bson.M{"$set": bson.M{"role": "owner", "updatedAt": now}},
                  )
  ... (3 more lines)
  ```
- **[LOW] Proper handling** — `backend/cmd/lastsaas/main.go:973` in `promptPassword`
  ```go
          if err != nil {
                  fmt.Fprintf(os.Stderr, "Error reading password: %v\n", err)
                  os.Exit(1)
          }
  ```

### `backend/cmd/lastsaas/output.go`

- **[MEDIUM] Logged only (no return)** — `backend/cmd/lastsaas/output.go:84` in `printJSON`
  ```go
          if err := enc.Encode(v); err != nil {
                  fmt.Fprintf(os.Stderr, "warning: failed to encode JSON output: %v\n", err)
          }
  ```

### `backend/cmd/lastsaas/process.go`

- **[MEDIUM] Logged only (no return)** — `backend/cmd/lastsaas/process.go:148` in `startBackend`
  ```go
          if err := os.WriteFile(pidFile, []byte(strconv.Itoa(pid)), 0644); err != nil {
                  fmt.Fprintf(os.Stderr, "warning: failed to write backend PID file: %v\n", err)
          }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/cmd/lastsaas/process.go:152` in `startBackend`
  ```go
          if err := lf.Close(); err != nil {
                  fmt.Fprintf(os.Stderr, "warning: failed to close backend log file: %v\n", err)
          }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/cmd/lastsaas/process.go:160` in `startBackend`
  ```go
                  if err := os.Remove(pidFile); err != nil {
                          fmt.Fprintf(os.Stderr, "warning: failed to remove backend PID file: %v\n", err)
                  }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/cmd/lastsaas/process.go:207` in `startFrontend`
  ```go
          if err := os.WriteFile(pidFile, []byte(strconv.Itoa(pid)), 0644); err != nil {
                  fmt.Fprintf(os.Stderr, "warning: failed to write frontend PID file: %v\n", err)
          }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/cmd/lastsaas/process.go:211` in `startFrontend`
  ```go
          if err := lf.Close(); err != nil {
                  fmt.Fprintf(os.Stderr, "warning: failed to close frontend log file: %v\n", err)
          }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/cmd/lastsaas/process.go:219` in `startFrontend`
  ```go
                  if err := os.Remove(pidFile); err != nil {
                          fmt.Fprintf(os.Stderr, "warning: failed to remove frontend PID file: %v\n", err)
                  }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/cmd/lastsaas/process.go:235` in `stopService`
  ```go
                  if err := os.Remove(pidFile); err != nil {
                          fmt.Fprintf(os.Stderr, "warning: failed to remove PID file: %v\n", err)
                  }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/cmd/lastsaas/process.go:260` in `stopService`
  ```go
          if err := os.Remove(pidFile); err != nil {
                  fmt.Fprintf(os.Stderr, "warning: failed to remove PID file: %v\n", err)
          }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/cmd/lastsaas/process.go:318` in `ensurePIDDir`
  ```go
          if err := os.MkdirAll(pd, 0755); err != nil {
                  fmt.Fprintf(os.Stderr, "warning: failed to create PID directory: %v\n", err)
          }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/cmd/lastsaas/process.go:331` in `readPID`
  ```go
          if err != nil {
                  fmt.Fprintf(os.Stderr, "warning: failed to read PID file %s: %v\n", file, err)
                  return 0
          }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/cmd/lastsaas/process.go:336` in `readPID`
  ```go
          if err != nil {
                  fmt.Fprintf(os.Stderr, "warning: failed to parse PID file %s: %v\n", file, err)
                  return 0
          }
  ```
- **[LOW] Proper handling** — `backend/cmd/lastsaas/process.go:29` in `cmdStart`
  ```go
          if err := fs.Parse(os.Args[2:]); err != nil {
                  fmt.Fprintf(os.Stderr, "error: %v\n", err)
                  os.Exit(1)
          }
  ```
- **[LOW] Proper handling** — `backend/cmd/lastsaas/process.go:52` in `cmdStop`
  ```go
          if err := fs.Parse(os.Args[2:]); err != nil {
                  fmt.Fprintf(os.Stderr, "error: %v\n", err)
                  os.Exit(1)
          }
  ```
- **[LOW] Proper handling** — `backend/cmd/lastsaas/process.go:76` in `cmdRestart`
  ```go
          if err := fs.Parse(os.Args[2:]); err != nil {
                  fmt.Fprintf(os.Stderr, "error: %v\n", err)
                  os.Exit(1)
          }
  ```
- **[LOW] Proper handling** — `backend/cmd/lastsaas/process.go:121` in `startBackend`
  ```go
          if out, err := buildCmd.CombinedOutput(); err != nil {
                  fmt.Printf("FAILED\n%s\n", string(out))
                  os.Exit(1)
          }
  ```
- **[LOW] Proper handling** — `backend/cmd/lastsaas/process.go:129` in `startBackend`
  ```go
          if err != nil {
                  fmt.Fprintf(os.Stderr, "Failed to create log file: %v\n", err)
                  os.Exit(1)
          }
  ```
- **[LOW] Proper handling** — `backend/cmd/lastsaas/process.go:141` in `startBackend`
  ```go
          if err := cmd.Start(); err != nil {
                  lf.Close()
                  fmt.Fprintf(os.Stderr, "Failed to start backend: %v\n", err)
                  os.Exit(1)
          }
  ```
- **[LOW] Proper handling** — `backend/cmd/lastsaas/process.go:183` in `startFrontend`
  ```go
          if _, err := os.Stat(viteBin); err != nil {
                  fmt.Fprintf(os.Stderr, "Vite not found. Run 'npm install' in the frontend directory first.\n")
                  os.Exit(1)
          }
  ```
- **[LOW] Proper handling** — `backend/cmd/lastsaas/process.go:189` in `startFrontend`
  ```go
          if err != nil {
                  fmt.Fprintf(os.Stderr, "Failed to create log file: %v\n", err)
                  os.Exit(1)
          }
  ```
- **[LOW] Proper handling** — `backend/cmd/lastsaas/process.go:200` in `startFrontend`
  ```go
          if err := cmd.Start(); err != nil {
                  lf.Close()
                  fmt.Fprintf(os.Stderr, "Failed to start frontend: %v\n", err)
                  os.Exit(1)
          }
  ```
- **[LOW] Proper handling** — `backend/cmd/lastsaas/process.go:283` in `findProjectRoot`
  ```go
          if err != nil {
                  return "", err
          }
  ```
- **[LOW] Proper handling** — `backend/cmd/lastsaas/process.go:309` in `mustFindProjectRoot`
  ```go
          if err != nil {
                  fmt.Fprintf(os.Stderr, "%v\n", err)
                  os.Exit(1)
          }
  ```

### `backend/cmd/server/main.go`

- **[MEDIUM] Logged only (no return)** — `backend/cmd/server/main.go:79` in `ServeHTTP`
  ```go
                  if _, err := w.Write([]byte(html)); err != nil {
                          slog.Warn("server: failed to write index.html", "error", err)
                  }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/cmd/server/main.go:113` in `main`
  ```go
                  if err := database.Close(ctx); err != nil {
                          slog.Error("Failed to close database connection", "error", err)
                  }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/cmd/server/main.go:159` in `main`
  ```go
                  if err := ddClient.Startup(context.Background(), version.Current); err != nil {
                          slog.Warn("DataDog startup verification failed (integration will retry in background)", "error", err)
                  }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/cmd/server/main.go:385` in `main`
  ```go
                  if err := database.Client.Ping(ctx, nil); err != nil {
                          slog.Warn("server: health check DB ping failed", "error", err)
                          w.WriteHeader(http.StatusServiceUnavailable)
                          if _, err := w.Write([]byte(`{"status":"unhealthy","error":"database unreachable"}`)); err != nil {
                                  slog.Warn("server: failed to write health response", "error", err)
                          }
  ... (2 more lines)
  ```
- **[MEDIUM] Logged only (no return)** — `backend/cmd/server/main.go:388` in `main`
  ```go
                          if _, err := w.Write([]byte(`{"status":"unhealthy","error":"database unreachable"}`)); err != nil {
                                  slog.Warn("server: failed to write health response", "error", err)
                          }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/cmd/server/main.go:394` in `main`
  ```go
                  if _, err := w.Write([]byte(`{"status":"ok"}`)); err != nil {
                          slog.Warn("server: failed to write health response", "error", err)
                  }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/cmd/server/main.go:407` in `main`
  ```go
                  if _, err := w.Write([]byte(fmt.Sprintf(`{"version":%q}`, version.Current))); err != nil {
                          slog.Warn("server: failed to write version response", "error", err)
                  }
  ```
- **[LOW] Proper handling** — `backend/cmd/server/main.go:67` in `ServeHTTP`
  ```go
                  if readErr != nil {
                          http.Error(w, "Internal Server Error", http.StatusInternalServerError)
                          return
                  }
  ```
- **[LOW] Proper handling** — `backend/cmd/server/main.go:84` in `ServeHTTP`
  ```go
          if err != nil {
                  http.Error(w, "Internal Server Error", http.StatusInternalServerError)
                  return
          }
  ```
- **[LOW] Proper handling** — `backend/cmd/server/main.go:98` in `main`
  ```go
          if err != nil {
                  slog.Error("Failed to load config", "error", err)
                  os.Exit(1)
          }
  ```
- **[LOW] Proper handling** — `backend/cmd/server/main.go:106` in `main`
  ```go
          if err != nil {
                  slog.Error("Failed to connect to MongoDB", "error", err)
                  os.Exit(1)
          }
  ```
- **[LOW] Proper handling** — `backend/cmd/server/main.go:124` in `main`
  ```go
          if err := configstore.Seed(context.Background(), database); err != nil {
                  slog.Error("Failed to seed config variables", "error", err)
                  os.Exit(1)
          }
  ```
- **[LOW] Proper handling** — `backend/cmd/server/main.go:129` in `main`
  ```go
          if err := cfgStore.Load(context.Background()); err != nil {
                  slog.Error("Failed to load config store", "error", err)
                  os.Exit(1)
          }
  ```
- **[LOW] Proper handling** — `backend/cmd/server/main.go:139` in `main`
  ```go
          if err := planstore.Seed(context.Background(), database); err != nil {
                  slog.Error("Failed to seed plans", "error", err)
                  os.Exit(1)
          }
  ```
- **[LOW] Proper handling** — `backend/cmd/server/main.go:244` in `main`
  ```go
          if err != nil {
                  slog.Error("Invalid webhook encryption key", "error", err)
                  os.Exit(1)
          }
  ```
- **[LOW] Proper handling** — `backend/cmd/server/main.go:837` in `main`
  ```go
                  if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
                          slog.Error("Server failed", "error", err)
                          os.Exit(1)
                  }
  ```
- **[LOW] Proper handling** — `backend/cmd/server/main.go:854` in `main`
  ```go
          if err := srv.Shutdown(shutdownCtx); err != nil {
                  slog.Error("Server forced shutdown", "error", err)
                  os.Exit(1)
          }
  ```

### `backend/internal/api/handlers/admin.go`

- **[HIGH] Missing error check** — `backend/internal/api/handlers/admin.go:403` in `ExportTenantsCSV`
  - _statement-form call to known error-returning 'writer.Flush()'_
  ```go
  	writer.Flush()
  ```
- **[HIGH] Missing error check** — `backend/internal/api/handlers/admin.go:741` in `ExportUsersCSV`
  - _statement-form call to known error-returning 'writer.Flush()'_
  ```go
  	writer.Flush()
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/api/handlers/admin.go:55` in `isRootTenantOwner`
  ```go
  	if err != nil {
  		slog.Warn("isRootTenantOwner: failed to count owner memberships", "userId", userID.Hex(), "error", err)
  		return false
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/api/handlers/admin.go:229` in `ListTenants`
  ```go
  	if planErr != nil {
  		slog.Warn("ListTenants: failed to load plans for name lookup", "error", planErr)
  	} else {
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/api/handlers/admin.go:234` in `ListTenants`
  ```go
  		if err := planCursor.All(ctx, &plans); err != nil {
  			slog.Warn("ListTenants: failed to decode plans", "error", err)
  		}
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/api/handlers/admin.go:354` in `ExportTenantsCSV`
  ```go
  	if planErr != nil {
  		slog.Warn("ExportTenantsCSV: failed to load plans for name lookup", "error", planErr)
  	} else {
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/api/handlers/admin.go:359` in `ExportTenantsCSV`
  ```go
  		if err := planCursor.All(ctx, &plans); err != nil {
  			slog.Warn("ExportTenantsCSV: failed to decode plans", "error", err)
  		}
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/api/handlers/admin.go:404` in `ExportTenantsCSV`
  ```go
  	if err := writer.Error(); err != nil {
  		slog.Error("ExportTenantsCSV: CSV writer error", "error", err)
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/api/handlers/admin.go:742` in `ExportUsersCSV`
  ```go
  	if err := writer.Error(); err != nil {
  		slog.Error("ExportUsersCSV: CSV writer error", "error", err)
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/api/handlers/admin.go:836` in `GetDashboard`
  ```go
  			if cpuWarnErr != nil {
  				slog.Warn("GetDashboard: invalid health.cpu.warning_threshold", "error", cpuWarnErr)
  			}
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/api/handlers/admin.go:840` in `GetDashboard`
  ```go
  			if cpuCritErr != nil {
  				slog.Warn("GetDashboard: invalid health.cpu.critical_threshold", "error", cpuCritErr)
  			}
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/api/handlers/admin.go:844` in `GetDashboard`
  ```go
  			if memWarnErr != nil {
  				slog.Warn("GetDashboard: invalid health.memory.warning_threshold", "error", memWarnErr)
  			}
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/api/handlers/admin.go:848` in `GetDashboard`
  ```go
  			if memCritErr != nil {
  				slog.Warn("GetDashboard: invalid health.memory.critical_threshold", "error", memCritErr)
  			}
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/api/handlers/admin.go:852` in `GetDashboard`
  ```go
  			if diskWarnErr != nil {
  				slog.Warn("GetDashboard: invalid health.disk.warning_threshold", "error", diskWarnErr)
  			}
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/api/handlers/admin.go:856` in `GetDashboard`
  ```go
  			if diskCritErr != nil {
  				slog.Warn("GetDashboard: invalid health.disk.critical_threshold", "error", diskCritErr)
  			}
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/api/handlers/admin.go:964` in `GetUser`
  ```go
  	if planErr != nil {
  		slog.Warn("GetUser: failed to load plans for name lookup", "error", planErr)
  	} else {
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/api/handlers/admin.go:969` in `GetUser`
  ```go
  		if err := planCursor.All(r.Context(), &allPlans); err != nil {
  			slog.Warn("GetUser: failed to decode plans", "error", err)
  		}
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/api/handlers/admin.go:1290` in `PreflightDeleteUser`
  ```go
  		if err := memberCursor.All(ctx, &otherMemberships); err != nil {
  			slog.Warn("PreflightDeleteUser: failed to decode tenant members", "tenantId", m.TenantID.Hex(), "error", err)
  		}
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/api/handlers/admin.go:1895` in `InviteRootMember`
  ```go
  			if err := h.emailService.SendInvitationEmail(req.Email, user.DisplayName, rootTenant.Name, token); err != nil {
  				slog.Error("Failed to send root member invitation email", "to", req.Email, "error", err)
  			}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/admin.go:120` in `ListTenants`
  ```go
  	if pageErr != nil || page < 1 {
  		page = 1
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/admin.go:124` in `ListTenants`
  ```go
  	if limitErr != nil || limit < 1 || limit > 100 {
  		limit = 25
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/admin.go:177` in `ListTenants`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to count tenants")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/admin.go:188` in `ListTenants`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to fetch tenants")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/admin.go:195` in `ListTenants`
  ```go
  	if err := cursor.All(ctx, &tenants); err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to decode tenants")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/admin.go:313` in `ExportTenantsCSV`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to query tenants")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/admin.go:320` in `ExportTenantsCSV`
  ```go
  	if err := cursor.All(ctx, &tenants); err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to decode tenants")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/admin.go:412` in `GetTenant`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid tenant ID")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/admin.go:425` in `GetTenant`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to fetch members")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/admin.go:477` in `UpdateTenantStatus`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid tenant ID")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/admin.go:497` in `UpdateTenantStatus`
  ```go
  	if err := decodeJSON(r, &req); err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid request body")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/admin.go:527` in `ListUsers`
  ```go
  	if pageErr != nil || page < 1 {
  		page = 1
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/admin.go:531` in `ListUsers`
  ```go
  	if limitErr != nil || limit < 1 || limit > 100 {
  		limit = 25
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/admin.go:582` in `ListUsers`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to count users")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/admin.go:593` in `ListUsers`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to fetch users")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/admin.go:600` in `ListUsers`
  ```go
  	if err := cursor.All(ctx, &users); err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to decode users")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/admin.go:679` in `ExportUsersCSV`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to query users")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/admin.go:686` in `ExportUsersCSV`
  ```go
  	if err := cursor.All(ctx, &users); err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to decode users")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/admin.go:750` in `UpdateUserStatus`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid user ID")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/admin.go:769` in `UpdateUserStatus`
  ```go
  	if err := decodeJSON(r, &req); err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid request body")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/admin.go:778` in `UpdateUserStatus`
  ```go
  	if err != nil || result.MatchedCount == 0 {
  		respondWithError(w, http.StatusNotFound, "User not found")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/admin.go:818` in `GetDashboard`
  ```go
  	if err != nil {
  		slog.Warn("GetDashboard: failed to count users", "error", err)
  		userCount = 0
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/admin.go:823` in `GetDashboard`
  ```go
  	if err != nil {
  		slog.Warn("GetDashboard: failed to count tenants", "error", err)
  		tenantCount = 0
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/admin.go:937` in `GetUser`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid user ID")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/admin.go:949` in `GetUser`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to fetch memberships")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/admin.go:1053` in `UpdateUser`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid user ID")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/admin.go:1073` in `UpdateUser`
  ```go
  	if err := decodeJSON(r, &req); err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid request body")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/admin.go:1099` in `UpdateUser`
  ```go
  			if err != nil {
  				respondWithError(w, http.StatusInternalServerError, "Failed to check email uniqueness")
  				return
  			}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/admin.go:1131` in `UpdateUserRole`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid user ID")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/admin.go:1136` in `UpdateUserRole`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid tenant ID")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/admin.go:1155` in `UpdateUserRole`
  ```go
  	if err := decodeJSON(r, &req); err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid request body")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/admin.go:1197` in `UpdateUserRole`
  ```go
  	if err != nil || result.MatchedCount == 0 {
  		respondWithError(w, http.StatusNotFound, "Membership not found")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/admin.go:1223` in `PreflightDeleteUser`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid user ID")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/admin.go:1244` in `PreflightDeleteUser`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to query memberships")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/admin.go:1249` in `PreflightDeleteUser`
  ```go
  	if err := cursor.All(ctx, &ownerships); err != nil {
  		_ = cursor.Close(ctx)
  		respondWithError(w, http.StatusInternalServerError, "Failed to read memberships")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/admin.go:1284` in `PreflightDeleteUser`
  ```go
  		if err != nil {
  			slog.Warn("PreflightDeleteUser: failed to find tenant members", "tenantId", m.TenantID.Hex(), "error", err)
  			continue
  		}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/admin.go:1342` in `DeleteUser`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid user ID")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/admin.go:1367` in `DeleteUser`
  ```go
  	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid request body")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/admin.go:1379` in `DeleteUser`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to query memberships")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/admin.go:1384` in `DeleteUser`
  ```go
  	if err := cursor.All(ctx, &memberships); err != nil {
  		_ = cursor.Close(ctx)
  		respondWithError(w, http.StatusInternalServerError, "Failed to read memberships")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/admin.go:1410` in `DeleteUser`
  ```go
  			if err != nil {
  				respondWithError(w, http.StatusBadRequest, "Invalid replacement owner ID")
  				return
  			}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/admin.go:1418` in `DeleteUser`
  ```go
  			if err != nil {
  				respondWithError(w, http.StatusInternalServerError, "Failed to transfer ownership to replacement owner")
  				return
  			}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/admin.go:1434` in `DeleteUser`
  ```go
  			if err != nil {
  				respondWithError(w, http.StatusInternalServerError, "Failed to count tenant members")
  				return
  			}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/admin.go:1512` in `UpdateTenant`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid tenant ID")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/admin.go:1523` in `UpdateTenant`
  ```go
  	if err := decodeJSON(r, &req); err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid request body")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/admin.go:1607` in `ImpersonateUser`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid user ID")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/admin.go:1645` in `ImpersonateUser`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to generate impersonation token")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/admin.go:1668` in `ImpersonateUser`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to fetch memberships")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/admin.go:1713` in `ListRootMembers`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Root tenant not found")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/admin.go:1720` in `ListRootMembers`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to fetch members")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/admin.go:1727` in `ListRootMembers`
  ```go
  	if err := cursor.All(ctx, &memberships); err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to decode members")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/admin.go:1795` in `InviteRootMember`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Root tenant not found")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/admin.go:1812` in `InviteRootMember`
  ```go
  	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid request body")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/admin.go:1842` in `InviteRootMember`
  ```go
  		if err != nil {
  			respondWithError(w, http.StatusInternalServerError, "Failed to check existing root tenant membership")
  			return
  		}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/admin.go:1859` in `InviteRootMember`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to check existing root tenant invitations")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/admin.go:1885` in `InviteRootMember`
  ```go
  	if _, err := h.db.Invitations().InsertOne(ctx, invitation); err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to create invitation")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/admin.go:1923` in `RemoveRootMember`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Root tenant not found")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/admin.go:1935` in `RemoveRootMember`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid user ID")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/admin.go:1990` in `ChangeRootMemberRole`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Root tenant not found")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/admin.go:2007` in `ChangeRootMemberRole`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid user ID")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/admin.go:2018` in `ChangeRootMemberRole`
  ```go
  	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid request body")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/admin.go:2036` in `ChangeRootMemberRole`
  ```go
  	if err != nil || result.MatchedCount == 0 {
  		respondWithError(w, http.StatusNotFound, "Member not found")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/admin.go:2063` in `CancelRootInvitation`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Root tenant not found")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/admin.go:2069` in `CancelRootInvitation`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid invitation ID")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/admin.go:2079` in `CancelRootInvitation`
  ```go
  	if err != nil || result.DeletedCount == 0 {
  		respondWithError(w, http.StatusNotFound, "Invitation not found")
  		return
  	}
  ```

### `backend/internal/api/handlers/announcements.go`

- **[LOW] Proper handling** — `backend/internal/api/handlers/announcements.go:34` in `ListPublic`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to list announcements")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/announcements.go:41` in `ListPublic`
  ```go
  	if err := cursor.All(r.Context(), &announcements); err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to decode announcements")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/announcements.go:55` in `ListAll`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to list announcements")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/announcements.go:62` in `ListAll`
  ```go
  	if err := cursor.All(r.Context(), &announcements); err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to decode announcements")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/announcements.go:79` in `Create`
  ```go
  	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid request body")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/announcements.go:100` in `Create`
  ```go
  	if err := validation.Validate(&ann); err != nil {
  		respondWithError(w, http.StatusBadRequest, err.Error())
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/announcements.go:106` in `Create`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to create announcement")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/announcements.go:122` in `Update`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid announcement ID")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/announcements.go:132` in `Update`
  ```go
  	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid request body")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/announcements.go:153` in `Update`
  ```go
  	if err != nil || result.MatchedCount == 0 {
  		respondWithError(w, http.StatusNotFound, "Announcement not found")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/announcements.go:163` in `Delete`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid announcement ID")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/announcements.go:169` in `Delete`
  ```go
  	if err != nil || result.DeletedCount == 0 {
  		respondWithError(w, http.StatusNotFound, "Announcement not found")
  		return
  	}
  ```

### `backend/internal/api/handlers/apikeys.go`

- **[LOW] Proper handling** — `backend/internal/api/handlers/apikeys.go:46` in `ListAPIKeys`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to list API keys")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/apikeys.go:53` in `ListAPIKeys`
  ```go
  	if err := cursor.All(r.Context(), &keys); err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to decode API keys")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/apikeys.go:61` in `ListAPIKeys`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to count API keys")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/apikeys.go:74` in `CreateAPIKey`
  ```go
  	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid request body")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/apikeys.go:122` in `CreateAPIKey`
  ```go
  	if err := validation.Validate(&apiKey); err != nil {
  		respondWithError(w, http.StatusBadRequest, err.Error())
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/apikeys.go:128` in `CreateAPIKey`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to create API key")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/apikeys.go:161` in `DeleteAPIKey`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid key ID")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/apikeys.go:169` in `DeleteAPIKey`
  ```go
  	if err != nil || result.MatchedCount == 0 {
  		respondWithError(w, http.StatusNotFound, "API key not found")
  		return
  	}
  ```

### `backend/internal/api/handlers/auth.go`

- **[HIGH] Ignored error (`_`)** — `backend/internal/api/handlers/auth.go:682` in `ForgotPassword`
  - _error explicitly discarded with `_`_
  ```go
                  if allowed, _, _ := h.rateLimiter.Allow("email:pwreset:"+req.Email, middleware.EmailPasswordResetLimit); !allowed {
  ```
- **[HIGH] Missing error check** — `backend/internal/api/handlers/auth.go:711` in `ForgotPassword`
  - _statement-form call to known error-returning 'h.db.VerificationTokens().InsertOne()'_
  ```go
          h.db.VerificationTokens().InsertOne(r.Context(), verification)
  ```
- **[HIGH] Ignored error (`_`)** — `backend/internal/api/handlers/auth.go:1180` in `MagicLinkRequest`
  - _error explicitly discarded with `_`_
  ```go
                  if allowed, _, _ := h.rateLimiter.Allow("email:magiclink:"+req.Email, middleware.EmailMagicLinkLimit); !allowed {
  ```
- **[HIGH] Missing error check** — `backend/internal/api/handlers/auth.go:1204` in `MagicLinkRequest`
  - _statement-form call to known error-returning 'h.db.VerificationTokens().InsertOne()'_
  ```go
          h.db.VerificationTokens().InsertOne(r.Context(), verification)
  ```
- **[HIGH] Missing error check** — `backend/internal/api/handlers/auth.go:1922` in `UpdatePreferences`
  - _statement-form call to known error-returning 'h.db.Users().UpdateOne()'_
  ```go
          h.db.Users().UpdateOne(r.Context(), bson.M{"_id": user.ID}, bson.M{"$set": update})
  ```
- **[HIGH] Missing error check** — `backend/internal/api/handlers/auth.go:2026` in `sendVerificationEmail`
  - _statement-form call to known error-returning 'h.db.VerificationTokens().InsertOne()'_
  ```go
          h.db.VerificationTokens().InsertOne(ctx, verification)
  ```
- **[HIGH] Ignored error (`_`)** — `backend/internal/api/handlers/auth.go:2138` in `acceptInvitationForUser`
  - _error explicitly discarded with `_`_
  ```go
          count, _ := h.db.TenantMemberships().CountDocuments(ctx, bson.M{
  ```
- **[HIGH] Ignored error (`_`)** — `backend/internal/api/handlers/auth.go:2191` in `storeRefreshToken`
  - _error explicitly discarded with `_`_
  ```go
          activeCount, _ := database.RefreshTokens().CountDocuments(r.Context(), bson.M{
  ```
- **[HIGH] Missing error check** — `backend/internal/api/handlers/auth.go:2278` in `DeleteAccount`
  - _statement-form call to known error-returning 'cursor.Close()'_
  ```go
          cursor.Close(ctx)
  ```
- **[HIGH] Ignored error (`_`)** — `backend/internal/api/handlers/auth.go:2295` in `DeleteAccount`
  - _error explicitly discarded with `_`_
  ```go
                  otherCount, _ := h.db.TenantMemberships().CountDocuments(ctx, bson.M{
  ```
- **[HIGH] Ignored error (`_`)** — `backend/internal/api/handlers/auth.go:2366` in `ExportData`
  - _error explicitly discarded with `_`_
  ```go
          cursor, _ := h.db.TenantMemberships().Find(ctx, bson.M{"userId": user.ID})
  ```
- **[HIGH] Missing error check** — `backend/internal/api/handlers/auth.go:2370` in `ExportData`
  - _statement-form call to known error-returning 'cursor.Close()'_
  ```go
                  cursor.Close(ctx)
  ```
- **[HIGH] Ignored error (`_`)** — `backend/internal/api/handlers/auth.go:2388` in `ExportData`
  - _error explicitly discarded with `_`_
  ```go
          msgCursor, _ := h.db.Messages().Find(ctx, bson.M{"userId": user.ID})
  ```
- **[HIGH] Missing error check** — `backend/internal/api/handlers/auth.go:2392` in `ExportData`
  - _statement-form call to known error-returning 'msgCursor.Close()'_
  ```go
                  msgCursor.Close(ctx)
  ```
- **[HIGH] Missing error check** — `backend/internal/api/handlers/auth.go:2431` in `ExportData`
  - _statement-form call to known error-returning 'json.NewEncoder(w).Encode()'_
  ```go
          json.NewEncoder(w).Encode(export)
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/api/handlers/auth.go:262` in `Register`
  ```go
                  if err := h.acceptInvitationForUser(r.Context(), user.ID, req.InvitationToken); err != nil {
                          slog.Error("Failed to accept invitation during registration", "error", err)
                  } else {
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/api/handlers/auth.go:289` in `Register`
  ```go
          if err != nil {
                  slog.Error("Failed to get user memberships", "userId", user.ID.Hex(), "error", err)
          }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/api/handlers/auth.go:422` in `Login`
  ```go
          if err != nil {
                  slog.Error("Failed to get user memberships", "userId", user.ID.Hex(), "error", err)
          }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/api/handlers/auth.go:561` in `Refresh`
  ```go
          if err != nil {
                  slog.Error("Failed to get user memberships", "userId", user.ID.Hex(), "error", err)
          }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/api/handlers/auth.go:581` in `GetMe`
  ```go
          if err != nil {
                  slog.Error("Failed to get user memberships", "userId", user.ID.Hex(), "error", err)
          }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/api/handlers/auth.go:718` in `ForgotPassword`
  ```go
                          if err := h.emailService.SendPasswordResetEmail(user.Email, user.DisplayName, resetToken); err != nil {
                                  slog.Error("Failed to send password reset email", "error", err)
                          }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/api/handlers/auth.go:1089` in `MFAChallenge`
  ```go
          if err != nil {
                  slog.Error("Failed to get user memberships", "userId", user.ID.Hex(), "error", err)
          }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/api/handlers/auth.go:1211` in `MagicLinkRequest`
  ```go
                          if err := h.emailService.SendMagicLinkEmail(user.Email, user.DisplayName, magicToken); err != nil {
                                  slog.Error("Failed to send magic link email", "error", err)
                          }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/api/handlers/auth.go:1289` in `MagicLinkVerify`
  ```go
          if err != nil {
                  slog.Error("Failed to get user memberships", "userId", user.ID.Hex(), "error", err)
          }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/api/handlers/auth.go:1968` in `AcceptInvitation`
  ```go
          if err != nil {
                  slog.Error("Failed to get user memberships", "userId", user.ID.Hex(), "error", err)
          }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/api/handlers/auth.go:1991` in `createPersonalTenant`
  ```go
          if _, err := h.db.Tenants().InsertOne(ctx, tenant); err != nil {
                  slog.Error("Failed to create personal tenant", "userId", userID.Hex(), "error", err)
                  return
          }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/api/handlers/auth.go:2004` in `createPersonalTenant`
  ```go
          if _, err := h.db.TenantMemberships().InsertOne(ctx, membership); err != nil {
                  slog.Error("Failed to create membership for personal tenant", "error", err)
          }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/api/handlers/auth.go:2038` in `sendVerificationEmail`
  ```go
                          if err := h.emailService.SendVerificationEmail(userEmail, displayName, verificationToken); err != nil {
                                  slog.Error("Failed to send verification email", "to", userEmail, "error", err)
                          }
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/auth.go:105` in `generateTokenPair`
  ```go
          if err != nil {
                  return "", "", 0, fmt.Errorf("failed to generate access token: %w", err)
          }
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/auth.go:109` in `generateTokenPair`
  ```go
          if err != nil {
                  return "", "", 0, fmt.Errorf("failed to generate refresh token: %w", err)
          }
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/auth.go:198` in `Register`
  ```go
          if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
                  respondWithError(w, http.StatusBadRequest, "Invalid request body")
                  return
          }
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/auth.go:216` in `Register`
  ```go
          if err := h.passwordService.ValidatePasswordStrength(req.Password); err != nil {
                  respondWithError(w, http.StatusBadRequest, err.Error())
                  return
          }
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/auth.go:229` in `Register`
  ```go
          if err != nil {
                  respondWithError(w, http.StatusInternalServerError, "Failed to process password")
                  return
          }
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/auth.go:247` in `Register`
  ```go
          if err := validation.Validate(&user); err != nil {
                  respondWithError(w, http.StatusBadRequest, err.Error())
                  return
          }
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/auth.go:252` in `Register`
  ```go
          if _, err := h.db.Users().InsertOne(r.Context(), user); err != nil {
                  respondWithError(w, http.StatusInternalServerError, "Failed to create user")
                  return
          }
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/auth.go:278` in `Register`
  ```go
          if err != nil {
                  respondWithError(w, http.StatusInternalServerError, "Failed to generate token")
                  return
          }
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/auth.go:282` in `Register`
  ```go
          if err := storeRefreshToken(r, h.db, user.ID, refreshToken, refreshTTL); err != nil {
                  slog.Error("Failed to store refresh token", "error", err)
                  respondWithError(w, http.StatusInternalServerError, "Failed to create session")
                  return
          }
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/auth.go:317` in `Login`
  ```go
          if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
                  respondWithError(w, http.StatusBadRequest, "Invalid request body")
                  return
          }
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/auth.go:348` in `Login`
  ```go
          if err := h.passwordService.ComparePassword(user.PasswordHash, req.Password); err != nil {
                  // Atomic increment of failed attempts + conditional lock
                  now := time.Now()
                  filter := bson.M{
                          "_id": user.ID,
                          "$or": []bson.M{
  ... (25 more lines)
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/auth.go:399` in `Login`
  ```go
                  if err != nil {
                          respondWithError(w, http.StatusInternalServerError, "Failed to generate token")
                          return
                  }
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/auth.go:411` in `Login`
  ```go
          if err != nil {
                  respondWithError(w, http.StatusInternalServerError, "Failed to generate token")
                  return
          }
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/auth.go:415` in `Login`
  ```go
          if err := storeRefreshToken(r, h.db, user.ID, refreshToken, refreshTTL); err != nil {
                  slog.Error("Failed to store refresh token", "error", err)
                  respondWithError(w, http.StatusInternalServerError, "Failed to create session")
                  return
          }
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/auth.go:489` in `Refresh`
  ```go
          if err := json.NewDecoder(r.Body).Decode(&req); err != nil || req.RefreshToken == "" {
                  respondWithError(w, http.StatusBadRequest, "Refresh token is required")
                  return
          }
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/auth.go:495` in `Refresh`
  ```go
          if err != nil {
                  respondWithError(w, http.StatusUnauthorized, "Invalid refresh token")
                  return
          }
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/auth.go:506` in `Refresh`
  ```go
          if err != nil {
                  respondWithError(w, http.StatusUnauthorized, "Refresh token not found")
                  return
          }
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/auth.go:531` in `Refresh`
  ```go
          if err != nil {
                  respondWithError(w, http.StatusUnauthorized, "Invalid user ID")
                  return
          }
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/auth.go:543` in `Refresh`
  ```go
          if err != nil {
                  respondWithError(w, http.StatusInternalServerError, "Failed to generate token")
                  return
          }
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/auth.go:547` in `Refresh`
  ```go
          if err := storeRefreshToken(r, h.db, user.ID, refreshToken, refreshTTL, storedToken.FamilyID); err != nil {
                  slog.Error("Failed to store refresh token", "error", err)
                  respondWithError(w, http.StatusInternalServerError, "Failed to create session")
                  return
          }
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/auth.go:593` in `VerifyEmail`
  ```go
          if err := json.NewDecoder(r.Body).Decode(&req); err != nil || req.Token == "" {
                  respondWithError(w, http.StatusBadRequest, "Token is required")
                  return
          }
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/auth.go:611` in `VerifyEmail`
  ```go
          if err != nil {
                  respondWithError(w, http.StatusBadRequest, "Invalid or expired verification token")
                  return
          }
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/auth.go:643` in `ResendVerification`
  ```go
          if err := json.NewDecoder(r.Body).Decode(&req); err != nil || req.Email == "" {
                  respondWithError(w, http.StatusBadRequest, "Email is required")
                  return
          }
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/auth.go:673` in `ForgotPassword`
  ```go
          if err := json.NewDecoder(r.Body).Decode(&req); err != nil || req.Email == "" {
                  respondWithError(w, http.StatusBadRequest, "Email is required")
                  return
          }
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/auth.go:727` in `ResetPassword`
  ```go
          if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
                  respondWithError(w, http.StatusBadRequest, "Invalid request body")
                  return
          }
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/auth.go:737` in `ResetPassword`
  ```go
          if err := h.passwordService.ValidatePasswordStrength(req.NewPassword); err != nil {
                  respondWithError(w, http.StatusBadRequest, err.Error())
                  return
          }
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/auth.go:756` in `ResetPassword`
  ```go
          if err != nil {
                  respondWithError(w, http.StatusBadRequest, "Invalid or expired reset token")
                  return
          }
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/auth.go:762` in `ResetPassword`
  ```go
          if err != nil {
                  respondWithError(w, http.StatusInternalServerError, "Failed to process password")
                  return
          }
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/auth.go:795` in `ChangePassword`
  ```go
          if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
                  respondWithError(w, http.StatusBadRequest, "Invalid request body")
                  return
          }
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/auth.go:805` in `ChangePassword`
  ```go
          if err := h.passwordService.ValidatePasswordStrength(req.NewPassword); err != nil {
                  respondWithError(w, http.StatusBadRequest, err.Error())
                  return
          }
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/auth.go:815` in `ChangePassword`
  ```go
                  if err := h.passwordService.ComparePassword(user.PasswordHash, req.CurrentPassword); err != nil {
                          respondWithError(w, http.StatusUnauthorized, "Current password is incorrect")
                          return
                  }
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/auth.go:822` in `ChangePassword`
  ```go
          if err != nil {
                  respondWithError(w, http.StatusInternalServerError, "Failed to process password")
                  return
          }
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/auth.go:878` in `MFASetup`
  ```go
          if err != nil {
                  respondWithError(w, http.StatusInternalServerError, "Failed to generate MFA secret")
                  return
          }
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/auth.go:885` in `MFASetup`
  ```go
          if err != nil {
                  respondWithError(w, http.StatusInternalServerError, "Failed to secure MFA secret")
                  return
          }
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/auth.go:913` in `MFAVerifySetup`
  ```go
          if err := json.NewDecoder(r.Body).Decode(&req); err != nil || req.Code == "" {
                  respondWithError(w, http.StatusBadRequest, "Code is required")
                  return
          }
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/auth.go:938` in `MFAVerifySetup`
  ```go
          if err != nil {
                  respondWithError(w, http.StatusInternalServerError, "Failed to generate recovery codes")
                  return
          }
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/auth.go:975` in `MFADisable`
  ```go
          if err := json.NewDecoder(r.Body).Decode(&req); err != nil || req.Code == "" {
                  respondWithError(w, http.StatusBadRequest, "Code is required")
                  return
          }
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/auth.go:1025` in `MFAChallenge`
  ```go
          if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
                  respondWithError(w, http.StatusBadRequest, "Invalid request body")
                  return
          }
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/auth.go:1035` in `MFAChallenge`
  ```go
          if err != nil {
                  respondWithError(w, http.StatusUnauthorized, "Invalid or expired MFA token")
                  return
          }
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/auth.go:1045` in `MFAChallenge`
  ```go
          if err != nil {
                  respondWithError(w, http.StatusUnauthorized, "Invalid user")
                  return
          }
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/auth.go:1078` in `MFAChallenge`
  ```go
          if err != nil {
                  respondWithError(w, http.StatusInternalServerError, "Failed to generate token")
                  return
          }
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/auth.go:1082` in `MFAChallenge`
  ```go
          if err := storeRefreshToken(r, h.db, user.ID, refreshToken, refreshTTL); err != nil {
                  slog.Error("Failed to store refresh token", "error", err)
                  respondWithError(w, http.StatusInternalServerError, "Failed to create session")
                  return
          }
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/auth.go:1121` in `MFARegenerateRecoveryCodes`
  ```go
          if err := json.NewDecoder(r.Body).Decode(&req); err != nil || req.Code == "" {
                  respondWithError(w, http.StatusBadRequest, "Code is required")
                  return
          }
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/auth.go:1143` in `MFARegenerateRecoveryCodes`
  ```go
          if err != nil {
                  respondWithError(w, http.StatusInternalServerError, "Failed to generate recovery codes")
                  return
          }
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/auth.go:1172` in `MagicLinkRequest`
  ```go
          if err := json.NewDecoder(r.Body).Decode(&req); err != nil || req.Email == "" {
                  respondWithError(w, http.StatusBadRequest, "Email is required")
                  return
          }
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/auth.go:1227` in `MagicLinkVerify`
  ```go
          if err := json.NewDecoder(r.Body).Decode(&req); err != nil || req.Token == "" {
                  respondWithError(w, http.StatusBadRequest, "Token is required")
                  return
          }
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/auth.go:1246` in `MagicLinkVerify`
  ```go
          if err != nil {
                  respondWithError(w, http.StatusBadRequest, "Invalid or expired magic link token")
                  return
          }
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/auth.go:1266` in `MagicLinkVerify`
  ```go
                  if err != nil {
                          respondWithError(w, http.StatusInternalServerError, "Failed to generate token")
                          return
                  }
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/auth.go:1278` in `MagicLinkVerify`
  ```go
          if err != nil {
                  respondWithError(w, http.StatusInternalServerError, "Failed to generate token")
                  return
          }
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/auth.go:1282` in `MagicLinkVerify`
  ```go
          if err := storeRefreshToken(r, h.db, user.ID, refreshToken, refreshTTL); err != nil {
                  slog.Error("Failed to store refresh token", "error", err)
                  respondWithError(w, http.StatusInternalServerError, "Failed to create session")
                  return
          }
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/auth.go:1315` in `createAuthCodeRedirect`
  ```go
          if _, err := h.db.AuthCodes().InsertOne(r.Context(), authCode); err != nil {
                  http.Redirect(w, r, h.frontendURL+"/login?error=code_generation_failed", http.StatusTemporaryRedirect)
                  return
          }
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/auth.go:1328` in `ExchangeCode`
  ```go
          if err := json.NewDecoder(r.Body).Decode(&req); err != nil || req.Code == "" {
                  respondWithError(w, http.StatusBadRequest, "Code is required")
                  return
          }
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/auth.go:1340` in `ExchangeCode`
  ```go
          if err != nil {
                  respondWithError(w, http.StatusUnauthorized, "Invalid or expired code")
                  return
          }
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/auth.go:1374` in `GoogleOAuth`
  ```go
          if _, err := h.db.OAuthStates().InsertOne(r.Context(), oauthState); err != nil {
                  slog.Error("Failed to store OAuth state", "error", err)
                  respondWithError(w, http.StatusInternalServerError, "Failed to initiate OAuth")
                  return
          }
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/auth.go:1402` in `GoogleOAuthCallback`
  ```go
          if result.Err() != nil {
                  http.Redirect(w, r, h.frontendURL+"/login?error=invalid_state", http.StatusTemporaryRedirect)
                  return
          }
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/auth.go:1408` in `GoogleOAuthCallback`
  ```go
          if err != nil {
                  http.Redirect(w, r, h.frontendURL+"/login?error=oauth_exchange_failed", http.StatusTemporaryRedirect)
                  return
          }
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/auth.go:1414` in `GoogleOAuthCallback`
  ```go
          if err != nil || !googleUser.VerifiedEmail {
                  http.Redirect(w, r, h.frontendURL+"/login?error=oauth_user_info_failed", http.StatusTemporaryRedirect)
                  return
          }
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/auth.go:1424` in `GoogleOAuthCallback`
  ```go
          if err != nil {
                  err = h.db.Users().FindOne(r.Context(), bson.M{"email": strings.ToLower(googleUser.Email)}).Decode(&user)
                  if err != nil {
                          isNewUser = true
                          user = models.User{
                                  ID:            primitive.NewObjectID(),
  ... (24 more lines)
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/auth.go:1426` in `GoogleOAuthCallback`
  ```go
                  if err != nil {
                          isNewUser = true
                          user = models.User{
                                  ID:            primitive.NewObjectID(),
                                  Email:         strings.ToLower(googleUser.Email),
                                  DisplayName:   googleUser.GivenName,
  ... (16 more lines)
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/auth.go:1440` in `GoogleOAuthCallback`
  ```go
                          if _, err := h.db.Users().InsertOne(r.Context(), user); err != nil {
                                  slog.Error("OAuth: failed to create user", "error", err)
                                  http.Redirect(w, r, h.frontendURL+"/login?error=account_creation_failed", http.StatusTemporaryRedirect)
                                  return
                          }
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/auth.go:1462` in `GoogleOAuthCallback`
  ```go
                  if err != nil {
                          http.Redirect(w, r, h.frontendURL+"/login?error=token_generation_failed", http.StatusTemporaryRedirect)
                          return
                  }
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/auth.go:1471` in `GoogleOAuthCallback`
  ```go
          if err != nil {
                  http.Redirect(w, r, h.frontendURL+"/login?error=token_generation_failed", http.StatusTemporaryRedirect)
                  return
          }
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/auth.go:1475` in `GoogleOAuthCallback`
  ```go
          if err := storeRefreshToken(r, h.db, user.ID, refreshToken, refreshTTL); err != nil {
                  slog.Error("Failed to store refresh token", "error", err)
                  http.Redirect(w, r, h.frontendURL+"/login?error=session_creation_failed", http.StatusTemporaryRedirect)
                  return
          }
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/auth.go:1507` in `GitHubOAuth`
  ```go
          if _, err := h.db.OAuthStates().InsertOne(r.Context(), oauthState); err != nil {
                  slog.Error("Failed to store OAuth state", "error", err)
                  respondWithError(w, http.StatusInternalServerError, "Failed to initiate OAuth")
                  return
          }
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/auth.go:1535` in `GitHubOAuthCallback`
  ```go
          if result.Err() != nil {
                  http.Redirect(w, r, h.frontendURL+"/login?error=invalid_state", http.StatusTemporaryRedirect)
                  return
          }
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/auth.go:1541` in `GitHubOAuthCallback`
  ```go
          if err != nil {
                  http.Redirect(w, r, h.frontendURL+"/login?error=oauth_exchange_failed", http.StatusTemporaryRedirect)
                  return
          }
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/auth.go:1547` in `GitHubOAuthCallback`
  ```go
          if err != nil {
                  http.Redirect(w, r, h.frontendURL+"/login?error=oauth_user_info_failed", http.StatusTemporaryRedirect)
                  return
          }
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/auth.go:1558` in `GitHubOAuthCallback`
  ```go
          if err != nil {
                  err = h.db.Users().FindOne(r.Context(), bson.M{"email": strings.ToLower(ghUser.Email)}).Decode(&user)
                  if err != nil {
                          isNewUser = true
                          displayName := ghUser.Name
                          if displayName == "" {
  ... (33 more lines)
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/auth.go:1560` in `GitHubOAuthCallback`
  ```go
                  if err != nil {
                          isNewUser = true
                          displayName := ghUser.Name
                          if displayName == "" {
                                  displayName = ghUser.Login
                          }
  ... (20 more lines)
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/auth.go:1578` in `GitHubOAuthCallback`
  ```go
                          if _, err := h.db.Users().InsertOne(r.Context(), user); err != nil {
                                  slog.Error("OAuth: failed to create user", "error", err)
                                  http.Redirect(w, r, h.frontendURL+"/login?error=account_creation_failed", http.StatusTemporaryRedirect)
                                  return
                          }
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/auth.go:1604` in `GitHubOAuthCallback`
  ```go
                  if err != nil {
                          http.Redirect(w, r, h.frontendURL+"/login?error=token_generation_failed", http.StatusTemporaryRedirect)
                          return
                  }
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/auth.go:1613` in `GitHubOAuthCallback`
  ```go
          if err != nil {
                  http.Redirect(w, r, h.frontendURL+"/login?error=token_generation_failed", http.StatusTemporaryRedirect)
                  return
          }
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/auth.go:1617` in `GitHubOAuthCallback`
  ```go
          if err := storeRefreshToken(r, h.db, user.ID, refreshToken, refreshTTL); err != nil {
                  slog.Error("Failed to store refresh token", "error", err)
                  http.Redirect(w, r, h.frontendURL+"/login?error=session_creation_failed", http.StatusTemporaryRedirect)
                  return
          }
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/auth.go:1649` in `MicrosoftOAuth`
  ```go
          if _, err := h.db.OAuthStates().InsertOne(r.Context(), oauthState); err != nil {
                  slog.Error("Failed to store OAuth state", "error", err)
                  respondWithError(w, http.StatusInternalServerError, "Failed to initiate OAuth")
                  return
          }
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/auth.go:1677` in `MicrosoftOAuthCallback`
  ```go
          if result.Err() != nil {
                  http.Redirect(w, r, h.frontendURL+"/login?error=invalid_state", http.StatusTemporaryRedirect)
                  return
          }
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/auth.go:1683` in `MicrosoftOAuthCallback`
  ```go
          if err != nil {
                  http.Redirect(w, r, h.frontendURL+"/login?error=oauth_exchange_failed", http.StatusTemporaryRedirect)
                  return
          }
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/auth.go:1689` in `MicrosoftOAuthCallback`
  ```go
          if err != nil {
                  http.Redirect(w, r, h.frontendURL+"/login?error=oauth_user_info_failed", http.StatusTemporaryRedirect)
                  return
          }
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/auth.go:1705` in `MicrosoftOAuthCallback`
  ```go
          if err != nil {
                  err = h.db.Users().FindOne(r.Context(), bson.M{"email": strings.ToLower(userEmail)}).Decode(&user)
                  if err != nil {
                          isNewUser = true
                          displayName := msUser.DisplayName
                          if displayName == "" {
  ... (33 more lines)
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/auth.go:1707` in `MicrosoftOAuthCallback`
  ```go
                  if err != nil {
                          isNewUser = true
                          displayName := msUser.DisplayName
                          if displayName == "" {
                                  displayName = msUser.GivenName
                          }
  ... (20 more lines)
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/auth.go:1725` in `MicrosoftOAuthCallback`
  ```go
                          if _, err := h.db.Users().InsertOne(r.Context(), user); err != nil {
                                  slog.Error("OAuth: failed to create user", "error", err)
                                  http.Redirect(w, r, h.frontendURL+"/login?error=account_creation_failed", http.StatusTemporaryRedirect)
                                  return
                          }
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/auth.go:1751` in `MicrosoftOAuthCallback`
  ```go
                  if err != nil {
                          http.Redirect(w, r, h.frontendURL+"/login?error=token_generation_failed", http.StatusTemporaryRedirect)
                          return
                  }
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/auth.go:1760` in `MicrosoftOAuthCallback`
  ```go
          if err != nil {
                  http.Redirect(w, r, h.frontendURL+"/login?error=token_generation_failed", http.StatusTemporaryRedirect)
                  return
          }
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/auth.go:1764` in `MicrosoftOAuthCallback`
  ```go
          if err := storeRefreshToken(r, h.db, user.ID, refreshToken, refreshTTL); err != nil {
                  slog.Error("Failed to store refresh token", "error", err)
                  http.Redirect(w, r, h.frontendURL+"/login?error=session_creation_failed", http.StatusTemporaryRedirect)
                  return
          }
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/auth.go:1795` in `ListSessions`
  ```go
          if err != nil {
                  respondWithError(w, http.StatusInternalServerError, "Failed to fetch sessions")
                  return
          }
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/auth.go:1802` in `ListSessions`
  ```go
          if err := cursor.All(r.Context(), &tokens); err != nil {
                  respondWithError(w, http.StatusInternalServerError, "Failed to fetch sessions")
                  return
          }
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/auth.go:1856` in `RevokeSession`
  ```go
          if err != nil {
                  respondWithError(w, http.StatusBadRequest, "Invalid session ID")
                  return
          }
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/auth.go:1865` in `RevokeSession`
  ```go
          if err != nil || result.ModifiedCount == 0 {
                  respondWithError(w, http.StatusNotFound, "Session not found")
                  return
          }
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/auth.go:1908` in `UpdatePreferences`
  ```go
          if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
                  respondWithError(w, http.StatusBadRequest, "Invalid request body")
                  return
          }
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/auth.go:1957` in `AcceptInvitation`
  ```go
          if err := json.NewDecoder(r.Body).Decode(&req); err != nil || req.Token == "" {
                  respondWithError(w, http.StatusBadRequest, "Invitation token is required")
                  return
          }
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/auth.go:1962` in `AcceptInvitation`
  ```go
          if err := h.acceptInvitationForUser(r.Context(), user.ID, req.Token); err != nil {
                  respondWithError(w, http.StatusBadRequest, err.Error())
                  return
          }
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/auth.go:2049` in `getUserMemberships`
  ```go
          if err != nil {
                  return nil, fmt.Errorf("failed to query memberships: %w", err)
          }
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/auth.go:2055` in `getUserMemberships`
  ```go
          if err := cursor.All(ctx, &memberships); err != nil {
                  return nil, fmt.Errorf("failed to decode memberships: %w", err)
          }
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/auth.go:2069` in `getUserMemberships`
  ```go
          if err != nil {
                  return nil, fmt.Errorf("failed to batch-query tenants: %w", err)
          }
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/auth.go:2075` in `getUserMemberships`
  ```go
          if err := tenantCursor.All(ctx, &tenants); err != nil {
                  return nil, fmt.Errorf("failed to decode tenants: %w", err)
          }
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/auth.go:2112` in `acceptInvitationForUser`
  ```go
          if err != nil {
                  return fmt.Errorf("invalid or expired invitation: %w", err)
          }
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/auth.go:2134` in `acceptInvitationForUser`
  ```go
          if res.Err() != nil {
                  return fmt.Errorf("invitation already accepted or modified: %w", res.Err())
          }
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/auth.go:2154` in `acceptInvitationForUser`
  ```go
          if _, err := h.db.TenantMemberships().InsertOne(ctx, membership); err != nil {
                  return fmt.Errorf("failed to create membership: %w", err)
          }
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/auth.go:2229` in `storeRefreshToken`
  ```go
          if _, err := database.RefreshTokens().InsertOne(r.Context(), rt); err != nil {
                  return fmt.Errorf("failed to store refresh token: %w", err)
          }
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/auth.go:2246` in `DeleteAccount`
  ```go
          if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
                  respondWithError(w, http.StatusBadRequest, "Invalid request body")
                  return
          }
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/auth.go:2257` in `DeleteAccount`
  ```go
                  if err := h.passwordService.ComparePassword(user.PasswordHash, req.Password); err != nil {
                          respondWithError(w, http.StatusUnauthorized, "Incorrect password")
                          return
                  }
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/auth.go:2267` in `DeleteAccount`
  ```go
          if err != nil {
                  respondWithError(w, http.StatusInternalServerError, "Failed to check memberships")
                  return
          }
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/auth.go:2272` in `DeleteAccount`
  ```go
          if err := cursor.All(ctx, &memberships); err != nil {
                  cursor.Close(ctx)
                  slog.Error("Failed to decode memberships during account deletion", "userId", user.ID.Hex(), "error", err)
                  respondWithError(w, http.StatusInternalServerError, "Failed to check memberships")
                  return
          }
  ```

### `backend/internal/api/handlers/billing.go`

- **[MEDIUM] Logged only (no return)** — `backend/internal/api/handlers/billing.go:616` in `GetInvoicePDF`
  ```go
  	if _, err := w.Write(buf.Bytes()); err != nil {
  		slog.Error("failed to write invoice PDF response", "transactionId", tx.ID.Hex(), "error", err)
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/api/handlers/billing.go:880` in `computeLiveRevenue`
  ```go
  	if err != nil {
  		slog.Warn("computeLiveRevenue: failed to parse date string", "dateStr", dateStr, "error", err)
  		return 0
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/api/handlers/billing.go:897` in `computeLiveRevenue`
  ```go
  	if err != nil {
  		slog.Warn("computeLiveRevenue: failed to aggregate financial transactions", "dateStr", dateStr, "error", err)
  		return 0
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/api/handlers/billing.go:933` in `computeLiveARR`
  ```go
  	if err != nil {
  		slog.Warn("computeLiveARR: failed to aggregate active tenant subscriptions", "error", err)
  		return 0
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/billing.go:72` in `Checkout`
  ```go
  	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid request body")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/billing.go:88` in `Checkout`
  ```go
  		if err != nil {
  			respondWithError(w, http.StatusBadRequest, "Invalid plan ID")
  			return
  		}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/billing.go:139` in `Checkout`
  ```go
  				if memberErr != nil {
  					slog.Warn("Billing: failed to count tenant members for seat calculation", "tenantId", tenant.ID.Hex(), "error", memberErr)
  					memberCount = 0
  				}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/billing.go:163` in `Checkout`
  ```go
  			if memberErr != nil {
  				slog.Warn("Billing: failed to count tenant members for per-seat checkout", "tenantId", tenant.ID.Hex(), "error", memberErr)
  				memberCount = 0
  			}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/billing.go:185` in `Checkout`
  ```go
  			if err != nil {
  				slog.Error("Billing: failed to get/create customer", "error", err)
  				respondWithError(w, http.StatusInternalServerError, "Failed to create billing session")
  				return
  			}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/billing.go:218` in `Checkout`
  ```go
  				if err != nil {
  					slog.Error("Billing: failed to create base price", "error", err)
  					respondWithError(w, http.StatusInternalServerError, "Failed to create billing session")
  					return
  				}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/billing.go:231` in `Checkout`
  ```go
  					if err != nil {
  						slog.Error("Billing: failed to create seat price", "error", err)
  						respondWithError(w, http.StatusInternalServerError, "Failed to create billing session")
  						return
  					}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/billing.go:253` in `Checkout`
  ```go
  			if err != nil {
  				slog.Error("Billing: failed to create checkout session", "error", err)
  				respondWithError(w, http.StatusInternalServerError, "Failed to create billing session")
  				return
  			}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/billing.go:277` in `Checkout`
  ```go
  		if err != nil {
  			slog.Error("Billing: failed to get/create customer", "error", err)
  			respondWithError(w, http.StatusInternalServerError, "Failed to create billing session")
  			return
  		}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/billing.go:295` in `Checkout`
  ```go
  		if err != nil {
  			slog.Error("Billing: failed to create checkout session", "error", err)
  			respondWithError(w, http.StatusInternalServerError, "Failed to create billing session")
  			return
  		}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/billing.go:307` in `Checkout`
  ```go
  		if err != nil {
  			respondWithError(w, http.StatusBadRequest, "Invalid bundle ID")
  			return
  		}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/billing.go:324` in `Checkout`
  ```go
  		if err != nil {
  			slog.Error("Billing: failed to get/create customer", "error", err)
  			respondWithError(w, http.StatusInternalServerError, "Failed to create billing session")
  			return
  		}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/billing.go:340` in `Checkout`
  ```go
  		if err != nil {
  			slog.Error("Billing: failed to create checkout session", "error", err)
  			respondWithError(w, http.StatusInternalServerError, "Failed to create billing session")
  			return
  		}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/billing.go:373` in `Portal`
  ```go
  	if err != nil {
  		slog.Error("Billing: failed to create portal session", "error", err)
  		respondWithError(w, http.StatusInternalServerError, "Failed to create portal session")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/billing.go:396` in `ListTransactions`
  ```go
  	if pageErr != nil || page < 1 {
  		page = 1
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/billing.go:400` in `ListTransactions`
  ```go
  	if perPageErr != nil || perPage < 1 || perPage > 100 {
  		perPage = 20
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/billing.go:407` in `ListTransactions`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to count transactions")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/billing.go:418` in `ListTransactions`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to fetch transactions")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/billing.go:425` in `ListTransactions`
  ```go
  	if err := cursor.All(ctx, &transactions); err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to decode transactions")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/billing.go:451` in `GetInvoice`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid transaction ID")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/billing.go:480` in `GetInvoicePDF`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid transaction ID")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/billing.go:608` in `GetInvoicePDF`
  ```go
  	if err := pdf.Output(&buf); err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to generate PDF")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/billing.go:642` in `CancelSubscription`
  ```go
  	if err != nil {
  		slog.Error("Billing: failed to cancel subscription", "error", err)
  		respondWithError(w, http.StatusInternalServerError, "Failed to cancel subscription")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/billing.go:712` in `AdminListTransactions`
  ```go
  	if pageErr != nil || page < 1 {
  		page = 1
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/billing.go:716` in `AdminListTransactions`
  ```go
  	if perPageErr != nil || perPage < 1 || perPage > 100 {
  		perPage = 50
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/billing.go:737` in `AdminListTransactions`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to count transactions")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/billing.go:748` in `AdminListTransactions`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to fetch transactions")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/billing.go:755` in `AdminListTransactions`
  ```go
  	if err := cursor.All(ctx, &transactions); err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to decode transactions")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/billing.go:805` in `AdminGetMetrics`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to fetch metrics")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/billing.go:812` in `AdminGetMetrics`
  ```go
  	if err := cursor.All(ctx, &metrics); err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to decode metrics")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/billing.go:952` in `AdminCancelSubscription`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid tenant ID")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/billing.go:971` in `AdminCancelSubscription`
  ```go
  	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid request body")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/billing.go:983` in `AdminCancelSubscription`
  ```go
  		if err := h.stripe.CancelSubscriptionImmediately(ctx, tenant.StripeSubscriptionID); err != nil {
  			slog.Error("Admin: failed to cancel subscription immediately", "error", err)
  			respondWithError(w, http.StatusInternalServerError, "Failed to cancel subscription")
  			return
  		}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/billing.go:991` in `AdminCancelSubscription`
  ```go
  		if err != nil {
  			slog.Error("Admin: failed to cancel subscription", "error", err)
  			respondWithError(w, http.StatusInternalServerError, "Failed to cancel subscription")
  			return
  		}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/billing.go:1019` in `AdminUpdateSubscription`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid tenant ID")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/billing.go:1027` in `AdminUpdateSubscription`
  ```go
  	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid request body")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/billing.go:1038` in `AdminUpdateSubscription`
  ```go
  	if err != nil || result.MatchedCount == 0 {
  		respondWithError(w, http.StatusNotFound, "Tenant not found")
  		return
  	}
  ```

### `backend/internal/api/handlers/branding.go`

- **[MEDIUM] Logged only (no return)** — `backend/internal/api/handlers/branding.go:130` in `ServeAsset`
  ```go
  	if _, err := w.Write(asset.Data); err != nil {
  		slog.Error("failed to write branding asset", "key", key, "error", err)
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/api/handlers/branding.go:152` in `ServeMedia`
  ```go
  	if _, err := w.Write(asset.Data); err != nil {
  		slog.Error("failed to write media asset", "id", key, "error", err)
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/branding.go:49` in `GetBranding`
  ```go
  	} else if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to load branding config")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/branding.go:123` in `ServeAsset`
  ```go
  	} else if err != nil {
  		http.Error(w, "Internal Server Error", http.StatusInternalServerError)
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/branding.go:145` in `ServeMedia`
  ```go
  	} else if err != nil {
  		http.Error(w, "Internal Server Error", http.StatusInternalServerError)
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/branding.go:167` in `GetPublicPage`
  ```go
  	} else if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to load page")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/branding.go:183` in `ListPublicPages`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to list pages")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/branding.go:188` in `ListPublicPages`
  ```go
  	if err := cursor.All(r.Context(), &pages); err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to decode pages")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/branding.go:203` in `UpdateBranding`
  ```go
  	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid JSON")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/branding.go:263` in `UpdateBranding`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to update branding config")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/branding.go:274` in `UploadAsset`
  ```go
  	if err := r.ParseMultipartForm(maxAssetSize); err != nil {
  		respondWithError(w, http.StatusBadRequest, "File too large (max 5MB)")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/branding.go:286` in `UploadAsset`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusBadRequest, "Missing file upload")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/branding.go:293` in `UploadAsset`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to read file")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/branding.go:325` in `UploadAsset`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to save asset")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/branding.go:349` in `DeleteAsset`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to delete asset")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/branding.go:369` in `ListMedia`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to list media")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/branding.go:374` in `ListMedia`
  ```go
  	if err := cursor.All(r.Context(), &assets); err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to decode media")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/branding.go:409` in `UploadMedia`
  ```go
  	if err := r.ParseMultipartForm(maxMediaSize); err != nil {
  		respondWithError(w, http.StatusBadRequest, "File too large (max 10MB)")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/branding.go:415` in `UploadMedia`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusBadRequest, "Missing file upload")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/branding.go:422` in `UploadMedia`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to read file")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/branding.go:461` in `UploadMedia`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to save media")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/branding.go:488` in `DeleteMedia`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to delete media")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/branding.go:506` in `AdminListPages`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to list pages")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/branding.go:511` in `AdminListPages`
  ```go
  	if err := cursor.All(r.Context(), &pages); err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to decode pages")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/branding.go:524` in `CreatePage`
  ```go
  	if err := json.NewDecoder(r.Body).Decode(&page); err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid JSON")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/branding.go:544` in `CreatePage`
  ```go
  	if err != nil {
  		if mongo.IsDuplicateKeyError(err) {
  			respondWithError(w, http.StatusConflict, "A page with this slug already exists")
  			return
  		}
  		respondWithError(w, http.StatusInternalServerError, "Failed to create page")
  ... (2 more lines)
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/branding.go:560` in `UpdatePage`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid page ID")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/branding.go:566` in `UpdatePage`
  ```go
  	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid JSON")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/branding.go:591` in `UpdatePage`
  ```go
  	if err != nil {
  		if mongo.IsDuplicateKeyError(err) {
  			respondWithError(w, http.StatusConflict, "A page with this slug already exists")
  			return
  		}
  		respondWithError(w, http.StatusInternalServerError, "Failed to update page")
  ... (2 more lines)
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/branding.go:611` in `DeletePage`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid page ID")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/branding.go:617` in `DeletePage`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to delete page")
  		return
  	}
  ```

### `backend/internal/api/handlers/bundles.go`

- **[LOW] Proper handling** — `backend/internal/api/handlers/bundles.go:61` in `ListBundles`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to list credit bundles")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/bundles.go:68` in `ListBundles`
  ```go
  	if err := cursor.All(r.Context(), &bundles); err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to decode credit bundles")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/bundles.go:76` in `ListBundles`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to count credit bundles")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/bundles.go:86` in `CreateBundle`
  ```go
  	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid request body")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/bundles.go:90` in `CreateBundle`
  ```go
  	if err := validateBundleRequest(&req); err != nil {
  		respondWithError(w, http.StatusBadRequest, err.Error())
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/bundles.go:97` in `CreateBundle`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to check credit bundle name uniqueness")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/bundles.go:118` in `CreateBundle`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to create credit bundle")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/bundles.go:139` in `UpdateBundle`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid bundle ID")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/bundles.go:155` in `UpdateBundle`
  ```go
  	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid request body")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/bundles.go:159` in `UpdateBundle`
  ```go
  	if err := validateBundleRequest(&req); err != nil {
  		respondWithError(w, http.StatusBadRequest, err.Error())
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/bundles.go:167` in `UpdateBundle`
  ```go
  		if err != nil {
  			respondWithError(w, http.StatusInternalServerError, "Failed to check credit bundle name uniqueness")
  			return
  		}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/bundles.go:186` in `UpdateBundle`
  ```go
  	if _, err := h.db.CreditBundles().UpdateByID(r.Context(), bundleID, update); err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to update credit bundle")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/bundles.go:206` in `DeleteBundle`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid bundle ID")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/bundles.go:238` in `ListBundlesPublic`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to list credit bundles")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/bundles.go:245` in `ListBundlesPublic`
  ```go
  	if err := cursor.All(r.Context(), &bundles); err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to decode credit bundles")
  		return
  	}
  ```

### `backend/internal/api/handlers/config.go`

- **[LOW] Proper handling** — `backend/internal/api/handlers/config.go:66` in `UpdateConfig`
  ```go
  	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid request body")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/config.go:77` in `UpdateConfig`
  ```go
  	if err := configstore.ValidateValue(v.Type, req.Value, effectiveOptions); err != nil {
  		respondWithError(w, http.StatusBadRequest, err.Error())
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/config.go:95` in `UpdateConfig`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to update config variable")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/config.go:100` in `UpdateConfig`
  ```go
  	if err := h.store.Reload(r.Context(), name); err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Updated but failed to reload cache")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/config.go:124` in `CreateConfig`
  ```go
  	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid request body")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/config.go:138` in `CreateConfig`
  ```go
  	if err := configstore.ValidateValue(req.Type, req.Value, req.Options); err != nil {
  		respondWithError(w, http.StatusBadRequest, err.Error())
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/config.go:162` in `CreateConfig`
  ```go
  	if _, err := h.db.ConfigVars().InsertOne(r.Context(), v); err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to create config variable")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/config.go:167` in `CreateConfig`
  ```go
  	if err := h.store.Reload(r.Context(), req.Name); err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Created but failed to reload cache")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/config.go:198` in `DeleteConfig`
  ```go
  	if err := h.store.Load(r.Context()); err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Deleted but failed to reload cache")
  		return
  	}
  ```

### `backend/internal/api/handlers/docs.go`

- **[MEDIUM] Logged only (no return)** — `backend/internal/api/handlers/docs.go:1103` in `DocsHTML`
  ```go
  	if _, err := w.Write([]byte(sb.String())); err != nil {
  		slog.Error("failed to write HTML docs response", "error", err)
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/api/handlers/docs.go:1181` in `DocsMarkdown`
  ```go
  	if _, err := w.Write([]byte(sb.String())); err != nil {
  		slog.Error("failed to write markdown docs response", "error", err)
  		return
  	}
  ```

### `backend/internal/api/handlers/event_definitions.go`

- **[MEDIUM] Logged only (no return)** — `backend/internal/api/handlers/event_definitions.go:464` in `wouldCreateCycle`
  ```go
  		if err != nil {
  			slog.Warn("failed to look up parent during cycle check", "id", current, "error", err)
  			return false
  		}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/event_definitions.go:51` in `ListEventDefinitions`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to list event definitions")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/event_definitions.go:58` in `ListEventDefinitions`
  ```go
  	if err := cursor.All(ctx, &defs); err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to decode event definitions")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/event_definitions.go:115` in `CreateEventDefinition`
  ```go
  	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid request body")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/event_definitions.go:136` in `CreateEventDefinition`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to check event definition name uniqueness")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/event_definitions.go:156` in `CreateEventDefinition`
  ```go
  		if err != nil {
  			respondWithError(w, http.StatusBadRequest, "Invalid parent ID")
  			return
  		}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/event_definitions.go:162` in `CreateEventDefinition`
  ```go
  		if pErr != nil {
  			respondWithError(w, http.StatusInternalServerError, "Failed to verify parent event definition")
  			return
  		}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/event_definitions.go:173` in `CreateEventDefinition`
  ```go
  	if _, err := h.db.EventDefinitions().InsertOne(ctx, def); err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to create event definition")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/event_definitions.go:185` in `UpdateEventDefinition`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid definition ID")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/event_definitions.go:191` in `UpdateEventDefinition`
  ```go
  	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid request body")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/event_definitions.go:220` in `UpdateEventDefinition`
  ```go
  		if err != nil {
  			respondWithError(w, http.StatusInternalServerError, "Failed to check event definition name uniqueness")
  			return
  		}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/event_definitions.go:240` in `UpdateEventDefinition`
  ```go
  		if err != nil {
  			respondWithError(w, http.StatusBadRequest, "Invalid parent ID")
  			return
  		}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/event_definitions.go:250` in `UpdateEventDefinition`
  ```go
  		if pErr != nil {
  			respondWithError(w, http.StatusInternalServerError, "Failed to verify parent event definition")
  			return
  		}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/event_definitions.go:288` in `DeleteEventDefinition`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid definition ID")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/event_definitions.go:322` in `GetSankeyData`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to load event definitions")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/event_definitions.go:329` in `GetSankeyData`
  ```go
  	if err := cursor.All(ctx, &allDefs); err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to decode event definitions")
  		return
  	}
  ```

### `backend/internal/api/handlers/health.go`

- **[MEDIUM] Logged only (no return)** — `backend/internal/api/handlers/health.go:136` in `SendTestEmail`
  ```go
  	if err := h.emailService.SendEmail(req.To, subject, body); err != nil {
  		slog.Error("failed to send test email", "to", req.To, "error", err)
  		respondWithJSON(w, http.StatusOK, map[string]interface{}{
  			"success": false,
  			"error":   err.Error(),
  		})
  ... (2 more lines)
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/health.go:31` in `ListNodes`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to list nodes")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/health.go:59` in `GetMetrics`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to query metrics")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/health.go:76` in `GetCurrent`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to get current metrics")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/health.go:117` in `SendTestEmail`
  ```go
  	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid request body")
  		return
  	}
  ```

### `backend/internal/api/handlers/helpers.go`

- **[MEDIUM] Logged only (no return)** — `backend/internal/api/handlers/helpers.go:26` in `respondWithJSON`
  ```go
  	if err := json.NewEncoder(w).Encode(payload); err != nil {
  		slog.Error("failed to encode JSON response", "error", err)
  	}
  ```
- **[MEDIUM] Panic on error** — `backend/internal/api/handlers/helpers.go:37` in `generateRandomToken`
  ```go
  	if _, err := rand.Read(b); err != nil {
  		panic("crypto/rand failed: " + err.Error())
  	}
  ```

### `backend/internal/api/handlers/logs.go`

- **[HIGH] Missing error check** — `backend/internal/api/handlers/logs.go:238` in `ExportCSV`
  - _statement-form call to known error-returning 'writer.Flush()'_
  ```go
  	writer.Flush()
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/api/handlers/logs.go:239` in `ExportCSV`
  ```go
  	if err := writer.Error(); err != nil {
  		slog.Error("CSV writer error during log export", "error", err)
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/logs.go:97` in `ListLogs`
  ```go
  	if pageErr != nil || page < 1 {
  		page = 1
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/logs.go:101` in `ListLogs`
  ```go
  	if perPageErr != nil || perPage < 1 || perPage > 100 {
  		perPage = 50
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/logs.go:117` in `ListLogs`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to count logs")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/logs.go:128` in `ListLogs`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to query logs")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/logs.go:135` in `ListLogs`
  ```go
  	if err := cursor.All(ctx, &logs); err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to read logs")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/logs.go:159` in `SeverityCounts`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to aggregate severity counts")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/logs.go:170` in `SeverityCounts`
  ```go
  	if err := cursor.All(r.Context(), &results); err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to read severity counts")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/logs.go:199` in `ExportCSV`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to query logs")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/logs.go:216` in `ExportCSV`
  ```go
  		if err := cursor.Decode(&log); err != nil {
  			slog.Warn("failed to decode log row during CSV export", "error", err)
  			continue
  		}
  ```

### `backend/internal/api/handlers/messages.go`

- **[LOW] Proper handling** — `backend/internal/api/handlers/messages.go:38` in `ListMessages`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to fetch messages")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/messages.go:45` in `ListMessages`
  ```go
  	if err := cursor.All(r.Context(), &messages); err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to decode messages")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/messages.go:66` in `UnreadCount`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to count messages")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/messages.go:83` in `MarkRead`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid message ID")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/messages.go:91` in `MarkRead`
  ```go
  	if err != nil || result.MatchedCount == 0 {
  		respondWithError(w, http.StatusNotFound, "Message not found")
  		return
  	}
  ```

### `backend/internal/api/handlers/openapi.go`

- **[MEDIUM] Logged only (no return)** — `backend/internal/api/handlers/openapi.go:167` in `DocsOpenAPI`
  ```go
  				if err := json.Unmarshal([]byte(ep.Body), &bodyExample); err != nil {
  					slog.Warn("OpenAPI: failed to parse body example", "path", path, "method", method, "error", err)
  				}
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/api/handlers/openapi.go:183` in `DocsOpenAPI`
  ```go
  				if err := json.Unmarshal([]byte(ep.Response), &respExample); err != nil {
  					slog.Warn("OpenAPI: failed to parse response example", "path", path, "method", method, "error", err)
  				}
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/api/handlers/openapi.go:216` in `DocsOpenAPI`
  ```go
  	if err := enc.Encode(spec); err != nil {
  		slog.Error("failed to encode OpenAPI spec response", "error", err)
  		return
  	}
  ```

### `backend/internal/api/handlers/plans.go`

- **[LOW] Proper handling** — `backend/internal/api/handlers/plans.go:49` in `ListPlans`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to list plans")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/plans.go:56` in `ListPlans`
  ```go
  	if err := cursor.All(ctx, &plans); err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to decode plans")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/plans.go:94` in `ListPlans`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to count plans")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/plans.go:104` in `GetPlan`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid plan ID")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/plans.go:124` in `ListEntitlementKeys`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to list plans")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/plans.go:143` in `ListEntitlementKeys`
  ```go
  		if err := cursor.Decode(&plan); err != nil {
  			slog.Warn("failed to decode plan during entitlement key scan", "error", err)
  			continue
  		}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/plans.go:243` in `CreatePlan`
  ```go
  	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid request body")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/plans.go:247` in `CreatePlan`
  ```go
  	if err := validatePlanRequest(&req); err != nil {
  		respondWithError(w, http.StatusBadRequest, err.Error())
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/plans.go:254` in `CreatePlan`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to check plan name uniqueness")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/plans.go:290` in `CreatePlan`
  ```go
  	if err := validation.Validate(&plan); err != nil {
  		respondWithError(w, http.StatusBadRequest, err.Error())
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/plans.go:296` in `CreatePlan`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to create plan")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/plans.go:317` in `UpdatePlan`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid plan ID")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/plans.go:333` in `UpdatePlan`
  ```go
  	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid request body")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/plans.go:337` in `UpdatePlan`
  ```go
  	if err := validatePlanRequest(&req); err != nil {
  		respondWithError(w, http.StatusBadRequest, err.Error())
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/plans.go:351` in `UpdatePlan`
  ```go
  		if err != nil {
  			respondWithError(w, http.StatusInternalServerError, "Failed to check plan name uniqueness")
  			return
  		}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/plans.go:393` in `UpdatePlan`
  ```go
  	if _, err := h.db.Plans().UpdateByID(r.Context(), planID, update); err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to update plan")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/plans.go:409` in `UpdatePlan`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to count plan subscribers")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/plans.go:440` in `DeletePlan`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid plan ID")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/plans.go:461` in `DeletePlan`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to count tenants using plan")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/plans.go:485` in `ArchivePlan`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid plan ID")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/plans.go:520` in `UnarchivePlan`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid plan ID")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/plans.go:560` in `AssignPlan`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid tenant ID")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/plans.go:569` in `AssignPlan`
  ```go
  	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid request body")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/plans.go:593` in `AssignPlan`
  ```go
  			if err != nil {
  				respondWithError(w, http.StatusBadRequest, "Invalid plan ID")
  				return
  			}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/plans.go:652` in `AssignPlan`
  ```go
  				if err := h.stripe.CancelSubscriptionImmediately(ctx, tenant.StripeSubscriptionID); err != nil {
  					slog.Error("AssignPlan: failed to cancel subscription", "tenant", tenant.Name, "error", err)
  					respondWithError(w, http.StatusInternalServerError, "Failed to cancel existing subscription")
  					return
  				}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/plans.go:671` in `AssignPlan`
  ```go
  	if _, err := h.db.Tenants().UpdateByID(ctx, tenantID, update); err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to assign plan")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/plans.go:697` in `ListPlansPublic`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid tenant ID")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/plans.go:718` in `ListPlansPublic`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to verify tenant membership")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/plans.go:738` in `ListPlansPublic`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to list plans")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/plans.go:745` in `ListPlansPublic`
  ```go
  	if err := cursor.All(r.Context(), &plans); err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to decode plans")
  		return
  	}
  ```

### `backend/internal/api/handlers/pm.go`

- **[LOW] Proper handling** — `backend/internal/api/handlers/pm.go:50` in `GetFunnel`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to compute funnel metrics")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/pm.go:70` in `GetRetention`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to compute retention data")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/pm.go:85` in `GetEngagement`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to compute engagement metrics")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/pm.go:95` in `GetKPIs`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to compute KPIs")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/pm.go:107` in `GetCustomEvents`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to compute custom event data")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/pm.go:117` in `ListEventTypes`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to list event types")
  		return
  	}
  ```

### `backend/internal/api/handlers/promotions.go`

- **[MEDIUM] Logged only (no return)** — `backend/internal/api/handlers/promotions.go:116` in `buildProductNameMap`
  ```go
  	if err != nil {
  		slog.Warn("failed to find stripe mappings for product name map", "error", err)
  		return nameMap
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/api/handlers/promotions.go:123` in `buildProductNameMap`
  ```go
  	if err := cursor.All(ctx, &mappings); err != nil {
  		slog.Warn("failed to decode stripe mappings for product name map", "error", err)
  		return nameMap
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/api/handlers/promotions.go:147` in `buildProductNameMap`
  ```go
  		if err != nil {
  			slog.Warn("failed to find plans for product name map", "error", err)
  		} else {
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/api/handlers/promotions.go:167` in `buildProductNameMap`
  ```go
  		if err != nil {
  			slog.Warn("failed to find bundles for product name map", "error", err)
  		} else {
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/promotions.go:91` in `ListPromotions`
  ```go
  	if err := iter.Err(); err != nil {
  		slog.Error("Promotions: list error", "error", err)
  		respondWithError(w, http.StatusInternalServerError, "Failed to list promotion codes")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/promotions.go:201` in `ListEligibleProducts`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to list plans")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/promotions.go:215` in `ListEligibleProducts`
  ```go
  	if err := planCursor.All(ctx, &plans); err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to read plans")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/promotions.go:227` in `ListEligibleProducts`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to list bundles")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/promotions.go:234` in `ListEligibleProducts`
  ```go
  	if err := bundleCursor.All(ctx, &bundles); err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to read bundles")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/promotions.go:264` in `CreatePromotion`
  ```go
  	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid request body")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/promotions.go:289` in `CreatePromotion`
  ```go
  			if err != nil {
  				respondWithError(w, http.StatusBadRequest, "Invalid product ID: "+item.ID)
  				return
  			}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/promotions.go:295` in `CreatePromotion`
  ```go
  			if err != nil {
  				slog.Warn("Failed to resolve Stripe product", "type", item.Type, "id", item.ID, "error", err)
  			respondWithError(w, http.StatusInternalServerError, "Failed to resolve Stripe product")
  				return
  			}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/promotions.go:331` in `CreatePromotion`
  ```go
  	if err != nil {
  		slog.Error("Promotions: coupon create error", "error", err)
  		respondWithError(w, http.StatusInternalServerError, "Failed to create coupon")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/promotions.go:349` in `CreatePromotion`
  ```go
  		if err != nil {
  			respondWithError(w, http.StatusBadRequest, "Invalid expiration date format (use YYYY-MM-DD)")
  			return
  		}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/promotions.go:360` in `CreatePromotion`
  ```go
  	if err != nil {
  		slog.Error("Promotions: promo code create error", "error", err)
  		respondWithError(w, http.StatusInternalServerError, "Failed to create promotion code")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/promotions.go:412` in `resolveStripeProducts`
  ```go
  			if err != nil {
  				return nil, err
  			}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/promotions.go:433` in `resolveStripeProducts`
  ```go
  		if err != nil {
  			return nil, err
  		}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/promotions.go:459` in `UpdatePromotion`
  ```go
  	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid request body")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/promotions.go:474` in `UpdatePromotion`
  ```go
  		if err != nil {
  			slog.Error("Promotions: coupon update error", "error", err)
  			respondWithError(w, http.StatusInternalServerError, "Failed to update coupon name")
  			return
  		}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/promotions.go:487` in `UpdatePromotion`
  ```go
  		if err != nil {
  			slog.Error("Promotions: promo code update error", "error", err)
  			respondWithError(w, http.StatusInternalServerError, "Failed to update promotion code")
  			return
  		}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/promotions.go:502` in `DeactivatePromotion`
  ```go
  	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid request body")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/promotions.go:515` in `DeactivatePromotion`
  ```go
  	if err != nil {
  		slog.Error("Promotions: deactivate error", "error", err)
  		respondWithError(w, http.StatusInternalServerError, "Failed to deactivate promotion code")
  		return
  	}
  ```

### `backend/internal/api/handlers/telemetry.go`

- **[LOW] Proper handling** — `backend/internal/api/handlers/telemetry.go:68` in `TrackAnonymous`
  ```go
  	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid request body")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/telemetry.go:97` in `TrackAnonymous`
  ```go
  	if err := h.telemetry.Track(r.Context(), event); err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to track event")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/telemetry.go:119` in `TrackAuthenticated`
  ```go
  	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid request body")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/telemetry.go:151` in `TrackAuthenticated`
  ```go
  	if err := h.telemetry.Track(r.Context(), event); err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to track event")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/telemetry.go:175` in `TrackBatch`
  ```go
  	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid request body")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/telemetry.go:220` in `TrackBatch`
  ```go
  	if err := h.telemetry.TrackBatch(r.Context(), events); err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to track events")
  		return
  	}
  ```

### `backend/internal/api/handlers/tenant.go`

- **[MEDIUM] Logged only (no return)** — `backend/internal/api/handlers/tenant.go:280` in `InviteMember`
  ```go
  		if err := h.stripe.UpdateSubscriptionQuantity(r.Context(), tenant.StripeSubscriptionID, int64(newSeats)); err != nil {
  			slog.Error("Failed to update seat quantity", "tenantId", tenant.ID.Hex(), "error", err)
  		} else {
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/api/handlers/tenant.go:295` in `InviteMember`
  ```go
  			if err := h.emailService.SendInvitationEmail(req.Email, user.DisplayName, tenant.Name, token); err != nil {
  				slog.Error("Failed to send invitation email", "to", req.Email, "error", err)
  			}
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/api/handlers/tenant.go:385` in `RemoveMember`
  ```go
  			if err := h.stripe.UpdateSubscriptionQuantity(r.Context(), tenant.StripeSubscriptionID, int64(newSeats)); err != nil {
  				slog.Error("Failed to update seat quantity", "tenant", tenant.ID.Hex(), "error", err)
  			} else {
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/tenant.go:75` in `ListMembers`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to fetch members")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/tenant.go:82` in `ListMembers`
  ```go
  	if err := cursor.All(r.Context(), &memberships); err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to decode members")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/tenant.go:142` in `InviteMember`
  ```go
  	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid request body")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/tenant.go:176` in `InviteMember`
  ```go
  		if err != nil {
  			respondWithError(w, http.StatusInternalServerError, "Failed to check existing membership")
  			return
  		}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/tenant.go:193` in `InviteMember`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to check existing invitations")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/tenant.go:231` in `InviteMember`
  ```go
  		if _, err := h.db.Invitations().InsertOne(r.Context(), invitation); err != nil {
  			respondWithError(w, http.StatusInternalServerError, "Failed to create invitation")
  			return
  		}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/tenant.go:237` in `InviteMember`
  ```go
  		if err != nil {
  			respondWithError(w, http.StatusInternalServerError, "Failed to count tenant members")
  			return
  		}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/tenant.go:246` in `InviteMember`
  ```go
  		if err != nil {
  			respondWithError(w, http.StatusInternalServerError, "Failed to count pending invitations")
  			return
  		}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/tenant.go:263` in `InviteMember`
  ```go
  		if _, err := h.db.Invitations().InsertOne(r.Context(), invitation); err != nil {
  			respondWithError(w, http.StatusInternalServerError, "Failed to create invitation")
  			return
  		}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/tenant.go:272` in `InviteMember`
  ```go
  		if err != nil {
  			slog.Warn("InviteMember: failed to count tenant members for seat calculation", "tenantId", tenant.ID.Hex(), "error", err)
  			memberCount = 0
  		}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/tenant.go:331` in `RemoveMember`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid user ID")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/tenant.go:374` in `RemoveMember`
  ```go
  			if err != nil {
  				slog.Warn("RemoveMember: failed to count tenant members for seat calculation", "tenantId", tenant.ID.Hex(), "error", err)
  				memberCount = 0
  			}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/tenant.go:430` in `ChangeRole`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid user ID")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/tenant.go:442` in `ChangeRole`
  ```go
  	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid request body")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/tenant.go:460` in `ChangeRole`
  ```go
  	if err != nil || result.MatchedCount == 0 {
  		respondWithError(w, http.StatusNotFound, "Member not found")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/tenant.go:497` in `TransferOwnership`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid user ID")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/tenant.go:512` in `TransferOwnership`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to verify target membership")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/tenant.go:597` in `GetActivity`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to fetch activity")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/tenant.go:604` in `GetActivity`
  ```go
  	if err := cursor.All(r.Context(), &logs); err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to decode activity")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/tenant.go:610` in `GetActivity`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to count activity logs")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/tenant.go:635` in `UpdateTenantSettings`
  ```go
  	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid request body")
  		return
  	}
  ```

### `backend/internal/api/handlers/usage.go`

- **[LOW] Proper handling** — `backend/internal/api/handlers/usage.go:46` in `RecordUsage`
  ```go
  	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
  		http.Error(w, `{"error":"Invalid request body"}`, http.StatusBadRequest)
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/usage.go:75` in `RecordUsage`
  ```go
  	if err := validation.Validate(&event); err != nil {
  		http.Error(w, fmt.Sprintf(`{"error":%q}`, err.Error()), http.StatusBadRequest)
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/usage.go:81` in `RecordUsage`
  ```go
  	if err != nil {
  		http.Error(w, `{"error":"Failed to start session"}`, http.StatusInternalServerError)
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/usage.go:94` in `RecordUsage`
  ```go
  		if err != nil {
  			return nil, err
  		}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/usage.go:104` in `RecordUsage`
  ```go
  			if err != nil {
  				return nil, err
  			}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/usage.go:114` in `RecordUsage`
  ```go
  		if _, err := h.db.UsageEvents().InsertOne(sc, event); err != nil {
  			return nil, err
  		}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/usage.go:124` in `RecordUsage`
  ```go
  	if txErr != nil {
  		http.Error(w, `{"error":"Failed to deduct credits"}`, http.StatusInternalServerError)
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/usage.go:170` in `GetSummary`
  ```go
  	if err != nil {
  		http.Error(w, `{"error":"Failed to aggregate usage"}`, http.StatusInternalServerError)
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/usage.go:183` in `GetSummary`
  ```go
  	if err := cursor.All(ctx, &items); err != nil {
  		http.Error(w, `{"error":"Failed to read usage data"}`, http.StatusInternalServerError)
  		return
  	}
  ```

### `backend/internal/api/handlers/webhook.go`

- **[MEDIUM] Logged only (no return)** — `backend/internal/api/handlers/webhook.go:498` in `handleInvoicePaymentFailed`
  ```go
  	if cursorErr != nil {
  		slog.Warn("Webhook: failed to find tenant memberships for failed-payment notification", "tenantId", tenant.ID.Hex(), "error", cursorErr)
  	} else {
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/api/handlers/webhook.go:502` in `handleInvoicePaymentFailed`
  ```go
  		if err := cursor.All(ctx, &memberships); err != nil {
  			slog.Warn("Webhook: failed to decode tenant memberships for failed-payment notification", "tenantId", tenant.ID.Hex(), "error", err)
  		}
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/api/handlers/webhook.go:841` in `recordTransaction`
  ```go
  	if _, err := h.db.FinancialTransactions().InsertOne(ctx, tx); err != nil {
  		slog.Error("Failed to record transaction", "error", err)
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/api/handlers/webhook.go:880` in `extractInstanceFromEvent`
  ```go
  	if err := json.Unmarshal(event.Data.Raw, &obj); err != nil {
  		slog.Warn("Webhook: failed to unmarshal event data for instance extraction", "error", err)
  	} else if obj.Metadata != nil {
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/webhook.go:53` in `HandleWebhook`
  ```go
  	if err != nil {
  		http.Error(w, "read error", http.StatusBadRequest)
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/webhook.go:59` in `HandleWebhook`
  ```go
  	if err != nil {
  		slog.Error("Webhook signature verification failed", "error", err)
  		http.Error(w, "invalid signature", http.StatusBadRequest)
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/webhook.go:130` in `HandleWebhook`
  ```go
  	if processingErr != nil {
  		slog.Error("Webhook: processing failed, removing idempotency record for retry", "eventId", event.ID, "error", processingErr)
  		h.db.WebhookEvents().DeleteOne(ctx, bson.M{"eventId": event.ID})
  		http.Error(w, "processing failed", http.StatusInternalServerError)
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/webhook.go:147` in `handleCheckoutCompleted`
  ```go
  	if err := json.Unmarshal(event.Data.Raw, &session); err != nil {
  		slog.Error("Webhook: failed to unmarshal checkout session", "error", err)
  		return fmt.Errorf("unmarshal checkout session: %w", err)
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/webhook.go:153` in `handleCheckoutCompleted`
  ```go
  	if err != nil {
  		slog.Error("Webhook: invalid tenantId in session metadata", "raw", session.Metadata["tenantId"], "error", err)
  		return fmt.Errorf("invalid tenantId in session metadata: %w", err)
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/webhook.go:158` in `handleCheckoutCompleted`
  ```go
  	if err != nil {
  		slog.Error("Webhook: invalid userId in session metadata", "raw", session.Metadata["userId"], "error", err)
  		return fmt.Errorf("invalid userId in session metadata: %w", err)
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/webhook.go:200` in `handleCheckoutCompleted`
  ```go
  		if err != nil {
  			slog.Error("Webhook: invalid planId in session metadata", "raw", planIDStr, "error", err)
  			return fmt.Errorf("invalid planId in session metadata: %w", err)
  		}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/webhook.go:317` in `handleCheckoutCompleted`
  ```go
  		if err != nil {
  			slog.Error("Webhook: invalid bundleId in session metadata", "raw", bundleIDStr, "error", err)
  			return fmt.Errorf("invalid bundleId in session metadata: %w", err)
  		}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/webhook.go:368` in `handleInvoicePaid`
  ```go
  	if err := json.Unmarshal(event.Data.Raw, &invoice); err != nil {
  		slog.Error("Webhook: failed to unmarshal invoice", "error", err)
  		return fmt.Errorf("unmarshal invoice: %w", err)
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/webhook.go:468` in `handleInvoicePaymentFailed`
  ```go
  	if err := json.Unmarshal(event.Data.Raw, &invoice); err != nil {
  		slog.Error("Webhook: failed to unmarshal invoice", "error", err)
  		return fmt.Errorf("unmarshal invoice: %w", err)
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/webhook.go:545` in `handleSubscriptionUpdated`
  ```go
  	if err := json.Unmarshal(event.Data.Raw, &sub); err != nil {
  		slog.Error("Webhook: failed to unmarshal subscription", "error", err)
  		return fmt.Errorf("unmarshal subscription: %w", err)
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/webhook.go:607` in `handleSubscriptionDeleted`
  ```go
  	if err := json.Unmarshal(event.Data.Raw, &sub); err != nil {
  		slog.Error("Webhook: failed to unmarshal subscription", "error", err)
  		return fmt.Errorf("unmarshal subscription: %w", err)
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/webhook.go:665` in `handleChargeRefunded`
  ```go
  	if err := json.Unmarshal(event.Data.Raw, &charge); err != nil {
  		slog.Error("Webhook: failed to unmarshal charge", "error", err)
  		return fmt.Errorf("unmarshal charge: %w", err)
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/webhook.go:711` in `handleDisputeCreated`
  ```go
  	if err := json.Unmarshal(event.Data.Raw, &dispute); err != nil {
  		slog.Error("Webhook: failed to unmarshal dispute", "error", err)
  		return fmt.Errorf("unmarshal dispute: %w", err)
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/webhook.go:757` in `handleDisputeClosed`
  ```go
  	if err := json.Unmarshal(event.Data.Raw, &dispute); err != nil {
  		slog.Error("Webhook: failed to unmarshal dispute", "error", err)
  		return fmt.Errorf("unmarshal dispute: %w", err)
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/webhook.go:805` in `recordTransaction`
  ```go
  	if err != nil {
  		slog.Error("Failed to generate invoice number", "error", err)
  		randBytes := make([]byte, 4)
  		rand.Read(randBytes)
  		invoiceNum = fmt.Sprintf("INV-ERR-%d-%s", time.Now().UnixNano(), hex.EncodeToString(randBytes))
  	}
  ```

### `backend/internal/api/handlers/webhooks.go`

- **[MEDIUM] Logged only (no return)** — `backend/internal/api/handlers/webhooks.go:115` in `GetWebhook`
  ```go
  	if err != nil {
  		slog.Error("failed to query webhook deliveries", "webhookId", whID, "error", err)
  		respondWithJSON(w, http.StatusOK, map[string]interface{}{
  			"webhook":    hook,
  			"deliveries": []models.WebhookDelivery{},
  		})
  ... (2 more lines)
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/webhooks.go:46` in `ListWebhooks`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to list webhooks")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/webhooks.go:53` in `ListWebhooks`
  ```go
  	if err := cursor.All(ctx, &hooks); err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to decode webhooks")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/webhooks.go:75` in `ListWebhooks`
  ```go
  		if err != nil {
  			slog.Warn("failed to count webhook deliveries", "webhookId", hook.ID, "error", err)
  			count = 0
  		}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/webhooks.go:89` in `ListWebhooks`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to count webhooks")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/webhooks.go:99` in `GetWebhook`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid webhook ID")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/webhooks.go:126` in `GetWebhook`
  ```go
  	if err := cursor.All(r.Context(), &deliveries); err != nil {
  		slog.Warn("failed to decode webhook deliveries", "webhookId", whID, "error", err)
  		deliveries = []models.WebhookDelivery{}
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/webhooks.go:149` in `validateWebhookURL`
  ```go
  	if err != nil {
  		return fmt.Errorf("invalid URL format: %w", err)
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/webhooks.go:165` in `validateWebhookURL`
  ```go
  	if err != nil {
  		// If DNS fails, check if host is already an IP
  		ip := net.ParseIP(host)
  		if ip == nil {
  			return fmt.Errorf("cannot resolve hostname: %w", err)
  		}
  ... (2 more lines)
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/webhooks.go:208` in `validateWebhookRequest`
  ```go
  	if err := validateWebhookURL(req.URL); err != nil {
  		return err
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/webhooks.go:225` in `CreateWebhook`
  ```go
  	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid request body")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/webhooks.go:230` in `CreateWebhook`
  ```go
  	if err := validateWebhookRequest(&req); err != nil {
  		respondWithError(w, http.StatusBadRequest, err.Error())
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/webhooks.go:252` in `CreateWebhook`
  ```go
  			if err != nil {
  				respondWithError(w, http.StatusInternalServerError, "Failed to secure webhook secret")
  				return
  			}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/webhooks.go:274` in `CreateWebhook`
  ```go
  	if err := validation.Validate(&hook); err != nil {
  		respondWithError(w, http.StatusBadRequest, err.Error())
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/webhooks.go:280` in `CreateWebhook`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to create webhook")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/webhooks.go:299` in `UpdateWebhook`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid webhook ID")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/webhooks.go:305` in `UpdateWebhook`
  ```go
  	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid request body")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/webhooks.go:310` in `UpdateWebhook`
  ```go
  	if err := validateWebhookRequest(&req); err != nil {
  		respondWithError(w, http.StatusBadRequest, err.Error())
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/webhooks.go:329` in `UpdateWebhook`
  ```go
  	if err != nil || result.MatchedCount == 0 {
  		respondWithError(w, http.StatusNotFound, "Webhook not found")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/webhooks.go:351` in `DeleteWebhook`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid webhook ID")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/webhooks.go:359` in `DeleteWebhook`
  ```go
  	if err != nil || result.MatchedCount == 0 {
  		respondWithError(w, http.StatusNotFound, "Webhook not found")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/webhooks.go:374` in `RegenerateSecret`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid webhook ID")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/webhooks.go:385` in `RegenerateSecret`
  ```go
  			if err != nil {
  				respondWithError(w, http.StatusInternalServerError, "Failed to secure webhook secret")
  				return
  			}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/webhooks.go:400` in `RegenerateSecret`
  ```go
  	if err != nil || result.MatchedCount == 0 {
  		respondWithError(w, http.StatusNotFound, "Webhook not found")
  		return
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/api/handlers/webhooks.go:415` in `TestWebhook`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid webhook ID")
  		return
  	}
  ```

### `backend/internal/apierror/apierror.go`

- **[MEDIUM] Logged only (no return)** — `backend/internal/apierror/apierror.go:59` in `Write`
  ```go
          if err := json.NewEncoder(w).Encode(resp); err != nil {
                  slog.Warn("apierror: failed to encode error response", "code", code, "error", err)
          }
  ```

### `backend/internal/auth/github_oauth.go`

- **[LOW] Proper handling** — `backend/internal/auth/github_oauth.go:48` in `ExchangeCode`
  ```go
          if err != nil {
                  return nil, fmt.Errorf("%w: %v", ErrOAuthCodeExchange, err)
          }
  ```
- **[LOW] Proper handling** — `backend/internal/auth/github_oauth.go:58` in `GetUserInfo`
  ```go
          if err != nil {
                  return nil, fmt.Errorf("%w: %v", ErrOAuthUserInfo, err)
          }
  ```
- **[LOW] Proper handling** — `backend/internal/auth/github_oauth.go:64` in `GetUserInfo`
  ```go
          if err != nil {
                  return nil, fmt.Errorf("%w: %v", ErrOAuthUserInfo, err)
          }
  ```
- **[LOW] Proper handling** — `backend/internal/auth/github_oauth.go:69` in `GetUserInfo`
  ```go
          if err := json.Unmarshal(data, &userInfo); err != nil {
                  return nil, fmt.Errorf("%w: %v", ErrOAuthUserInfo, err)
          }
  ```
- **[LOW] Proper handling** — `backend/internal/auth/github_oauth.go:90` in `getPrimaryEmail`
  ```go
          if err != nil {
                  return "", err
          }
  ```
- **[LOW] Proper handling** — `backend/internal/auth/github_oauth.go:96` in `getPrimaryEmail`
  ```go
          if err != nil {
                  return "", err
          }
  ```
- **[LOW] Proper handling** — `backend/internal/auth/github_oauth.go:101` in `getPrimaryEmail`
  ```go
          if err := json.Unmarshal(data, &emails); err != nil {
                  return "", err
          }
  ```

### `backend/internal/auth/google_oauth.go`

- **[LOW] Proper handling** — `backend/internal/auth/google_oauth.go:54` in `ExchangeCode`
  ```go
          if err != nil {
                  return nil, fmt.Errorf("%w: %v", ErrOAuthCodeExchange, err)
          }
  ```
- **[LOW] Proper handling** — `backend/internal/auth/google_oauth.go:63` in `GetUserInfo`
  ```go
          if err != nil {
                  return nil, fmt.Errorf("%w: %v", ErrOAuthUserInfo, err)
          }
  ```
- **[LOW] Proper handling** — `backend/internal/auth/google_oauth.go:69` in `GetUserInfo`
  ```go
          if err != nil {
                  return nil, fmt.Errorf("%w: %v", ErrOAuthUserInfo, err)
          }
  ```
- **[LOW] Proper handling** — `backend/internal/auth/google_oauth.go:74` in `GetUserInfo`
  ```go
          if err := json.Unmarshal(data, &userInfo); err != nil {
                  return nil, fmt.Errorf("%w: %v", ErrOAuthUserInfo, err)
          }
  ```

### `backend/internal/auth/jwt.go`

- **[LOW] Proper handling** — `backend/internal/auth/jwt.go:138` in `ValidateAccessToken`
  ```go
          if err != nil {
                  if errors.Is(err, jwt.ErrTokenExpired) {
                          return nil, fmt.Errorf("%w: %v", ErrExpiredToken, err)
                  }
                  return nil, fmt.Errorf("%w: %v", ErrInvalidToken, err)
          }
  ```
- **[LOW] Proper handling** — `backend/internal/auth/jwt.go:158` in `ValidateRefreshToken`
  ```go
          if err != nil {
                  if errors.Is(err, jwt.ErrTokenExpired) {
                          return nil, fmt.Errorf("%w: %v", ErrExpiredToken, err)
                  }
                  return nil, fmt.Errorf("%w: %v", ErrInvalidToken, err)
          }
  ```

### `backend/internal/auth/microsoft_oauth.go`

- **[LOW] Proper handling** — `backend/internal/auth/microsoft_oauth.go:49` in `ExchangeCode`
  ```go
          if err != nil {
                  return nil, fmt.Errorf("%w: %v", ErrOAuthCodeExchange, err)
          }
  ```
- **[LOW] Proper handling** — `backend/internal/auth/microsoft_oauth.go:58` in `GetUserInfo`
  ```go
          if err != nil {
                  return nil, fmt.Errorf("%w: %v", ErrOAuthUserInfo, err)
          }
  ```
- **[LOW] Proper handling** — `backend/internal/auth/microsoft_oauth.go:64` in `GetUserInfo`
  ```go
          if err != nil {
                  return nil, fmt.Errorf("%w: %v", ErrOAuthUserInfo, err)
          }
  ```
- **[LOW] Proper handling** — `backend/internal/auth/microsoft_oauth.go:69` in `GetUserInfo`
  ```go
          if err := json.Unmarshal(data, &userInfo); err != nil {
                  return nil, fmt.Errorf("%w: %v", ErrOAuthUserInfo, err)
          }
  ```

### `backend/internal/auth/password.go`

- **[LOW] Proper handling** — `backend/internal/auth/password.go:46` in `init`
  ```go
          if err != nil {
                  log.Fatalf("failed to generate dummy bcrypt hash: %v", err)
          }
  ```
- **[LOW] Proper handling** — `backend/internal/auth/password.go:67` in `HashPassword`
  ```go
          if err != nil {
                  return "", err
          }
  ```

### `backend/internal/auth/totp.go`

- **[MEDIUM] Logged only (no return)** — `backend/internal/auth/totp.go:68` in `DecryptSecret`
  ```go
          if err != nil {
                  slog.Warn("totp: failed to base64-decode secret", "error", err)
                  return stored
          }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/auth/totp.go:73` in `DecryptSecret`
  ```go
          if err != nil {
                  slog.Warn("totp: failed to create AES cipher", "error", err)
                  return stored
          }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/auth/totp.go:78` in `DecryptSecret`
  ```go
          if err != nil {
                  slog.Warn("totp: failed to create GCM", "error", err)
                  return stored
          }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/auth/totp.go:88` in `DecryptSecret`
  ```go
          if err != nil {
                  slog.Warn("totp: failed to decrypt secret (may be corrupted)", "error", err)
                  return stored // decryption failed — may be corrupted
          }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/auth/totp.go:145` in `ValidateCodeWithWindow`
  ```go
          if err != nil {
                  slog.Warn("totp: ValidateCustom failed", "error", err)
          }
  ```
- **[LOW] Proper handling** — `backend/internal/auth/totp.go:43` in `EncryptSecret`
  ```go
          if err != nil {
                  return "", fmt.Errorf("create cipher: %w", err)
          }
  ```
- **[LOW] Proper handling** — `backend/internal/auth/totp.go:47` in `EncryptSecret`
  ```go
          if err != nil {
                  return "", fmt.Errorf("create GCM: %w", err)
          }
  ```
- **[LOW] Proper handling** — `backend/internal/auth/totp.go:51` in `EncryptSecret`
  ```go
          if _, err := io.ReadFull(rand.Reader, nonce); err != nil {
                  return "", fmt.Errorf("generate nonce: %w", err)
          }
  ```
- **[LOW] Proper handling** — `backend/internal/auth/totp.go:115` in `GenerateRecoveryCodes`
  ```go
                  if _, err := rand.Read(b); err != nil {
                          return nil, nil, fmt.Errorf("failed to generate recovery code: %w", err)
                  }
  ```

### `backend/internal/config/config.go`

- **[MEDIUM] Logged only (no return)** — `backend/internal/config/config.go:99` in `LoadEnvFile`
  ```go
          if err != nil {
                  slog.Warn("config: failed to get cwd, will not search for .env file", "error", err)
          }
  ```
- **[LOW] Proper handling** — `backend/internal/config/config.go:140` in `Load`
  ```go
          if err != nil {
                  return nil, fmt.Errorf("failed to read config file %s: %w", configPath, err)
          }
  ```
- **[LOW] Proper handling** — `backend/internal/config/config.go:147` in `Load`
  ```go
          if err := yaml.Unmarshal([]byte(configStr), &cfg); err != nil {
                  return nil, fmt.Errorf("failed to parse config file: %w", err)
          }
  ```
- **[LOW] Proper handling** — `backend/internal/config/config.go:153` in `Load`
  ```go
          if err := cfg.validate(); err != nil {
                  return nil, fmt.Errorf("config validation failed: %w", err)
          }
  ```
- **[LOW] Proper handling** — `backend/internal/config/config.go:187` in `validate`
  ```go
          if _, err := url.Parse(c.Frontend.URL); err != nil {
                  return fmt.Errorf("frontend.url is not a valid URL: %w", err)
          }
  ```

### `backend/internal/configstore/seed.go`

- **[LOW] Proper handling** — `backend/internal/configstore/seed.go:384` in `Seed`
  ```go
                          if _, err := col.InsertOne(ctx, def); err != nil {
                                  return err
                          }
  ```
- **[LOW] Proper handling** — `backend/internal/configstore/seed.go:388` in `Seed`
  ```go
                  } else if err != nil {
                          return err
                  }
  ```

### `backend/internal/configstore/store.go`

- **[MEDIUM] Logged only (no return)** — `backend/internal/configstore/store.go:128` in `StartAutoReload`
  ```go
  				if err := s.Load(ctx); err != nil {
  					slog.Warn("configstore: auto-reload failed", "error", err)
  				}
  ```
- **[LOW] Proper handling** — `backend/internal/configstore/store.go:35` in `Load`
  ```go
  	if err != nil {
  		return err
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/configstore/store.go:41` in `Load`
  ```go
  	if err := cursor.All(ctx, &vars); err != nil {
  		return err
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/configstore/store.go:94` in `Set`
  ```go
  	if err != nil {
  		return err
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/configstore/store.go:107` in `Reload`
  ```go
  	if err != nil {
  		return err
  	}
  ```

### `backend/internal/configstore/validate.go`

- **[LOW] Proper handling** — `backend/internal/configstore/validate.go:30` in `ValidateValue`
  ```go
  		if _, err := strconv.ParseFloat(value, 64); err != nil {
  			return fmt.Errorf("invalid numeric value: %w", err)
  		}
  ```
- **[LOW] Proper handling** — `backend/internal/configstore/validate.go:73` in `ValidateEnumValue`
  ```go
  	if err := json.Unmarshal([]byte(optionsJSON), &strOpts); err != nil {
  		return fmt.Errorf("invalid options JSON: %w", err)
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/configstore/validate.go:86` in `validateTemplate`
  ```go
  	if _, err := template.New("check").Parse(value); err != nil {
  		return fmt.Errorf("invalid template syntax: %w", err)
  	}
  ```

### `backend/internal/datadog/client.go`

- **[MEDIUM] Logged only (no return)** — `backend/internal/datadog/client.go:140` in `resolveHostname`
  ```go
          if err != nil {
                  slog.Warn("datadog: failed to get hostname", "error", err)
                  return "unknown"
          }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/datadog/client.go:409` in `Validate`
  ```go
          if _, err := io.Copy(io.Discard, resp.Body); err != nil {
                  slog.Warn("datadog: failed to drain validate response body", "error", err)
          }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/datadog/client.go:434` in `metricsFlushLoop`
  ```go
                  if err := c.submitMetrics(buf); err != nil {
                          slog.Warn("datadog: metrics flush failed, will retry", "count", len(buf), "error", err)
                          return false
                  }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/datadog/client.go:486` in `eventsFlushLoop`
  ```go
                          if err := c.submitEvent(evt); err != nil {
                                  slog.Warn("datadog: event submission failed", "title", evt.Title, "error", err)
                          }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/datadog/client.go:493` in `eventsFlushLoop`
  ```go
                                          if err := c.submitEvent(evt); err != nil {
                                                  slog.Warn("datadog: event submission failed during shutdown", "error", err)
                                          }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/datadog/client.go:515` in `logsFlushLoop`
  ```go
                  if err := c.submitLogs(buf); err != nil {
                          slog.Warn("datadog: logs flush failed, will retry", "count", len(buf), "error", err)
                          return false
                  }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/datadog/client.go:567` in `checksFlushLoop`
  ```go
                          if err := c.submitServiceCheck(check); err != nil {
                                  slog.Warn("datadog: service check submission failed", "check", check.Check, "error", err)
                          }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/datadog/client.go:574` in `checksFlushLoop`
  ```go
                                          if err := c.submitServiceCheck(check); err != nil {
                                                  slog.Warn("datadog: service check submission failed during shutdown", "error", err)
                                          }
  ```
- **[LOW] Proper handling** — `backend/internal/datadog/client.go:161` in `Startup`
  ```go
          if err := c.Validate(ctx); err != nil {
                  return fmt.Errorf("API key validation failed: %w", err)
          }
  ```
- **[LOW] Proper handling** — `backend/internal/datadog/client.go:174` in `Startup`
  ```go
          if err := c.submitEvent(evt); err != nil {
                  return fmt.Errorf("startup event submission failed: %w", err)
          }
  ```
- **[LOW] Proper handling** — `backend/internal/datadog/client.go:186` in `Startup`
  ```go
          if err := c.submitMetrics(heartbeat); err != nil {
                  return fmt.Errorf("startup metric submission failed: %w", err)
          }
  ```
- **[LOW] Proper handling** — `backend/internal/datadog/client.go:399` in `Validate`
  ```go
          if err != nil {
                  return err
          }
  ```
- **[LOW] Proper handling** — `backend/internal/datadog/client.go:405` in `Validate`
  ```go
          if err != nil {
                  return fmt.Errorf("datadog validate request failed: %w", err)
          }
  ```
- **[LOW] Proper handling** — `backend/internal/datadog/client.go:642` in `submitMetrics`
  ```go
          if err != nil {
                  return err
          }
  ```
- **[LOW] Proper handling** — `backend/internal/datadog/client.go:648` in `submitMetrics`
  ```go
          if err != nil {
                  return err
          }
  ```
- **[LOW] Proper handling** — `backend/internal/datadog/client.go:659` in `submitMetrics`
  ```go
          if err != nil {
                  return err
          }
  ```
- **[LOW] Proper handling** — `backend/internal/datadog/client.go:664` in `submitMetrics`
  ```go
          if err != nil {
                  return fmt.Errorf("datadog: read metrics response body: %w", err)
          }
  ```
- **[LOW] Proper handling** — `backend/internal/datadog/client.go:679` in `submitEvent`
  ```go
          if err != nil {
                  return err
          }
  ```
- **[LOW] Proper handling** — `backend/internal/datadog/client.go:685` in `submitEvent`
  ```go
          if err != nil {
                  return err
          }
  ```
- **[LOW] Proper handling** — `backend/internal/datadog/client.go:696` in `submitEvent`
  ```go
          if err != nil {
                  return err
          }
  ```
- **[LOW] Proper handling** — `backend/internal/datadog/client.go:701` in `submitEvent`
  ```go
          if err != nil {
                  return fmt.Errorf("datadog: read events response body: %w", err)
          }
  ```
- **[LOW] Proper handling** — `backend/internal/datadog/client.go:715` in `submitLogs`
  ```go
          if err != nil {
                  return err
          }
  ```
- **[LOW] Proper handling** — `backend/internal/datadog/client.go:721` in `submitLogs`
  ```go
          if err != nil {
                  return err
          }
  ```
- **[LOW] Proper handling** — `backend/internal/datadog/client.go:732` in `submitLogs`
  ```go
          if err != nil {
                  return err
          }
  ```
- **[LOW] Proper handling** — `backend/internal/datadog/client.go:737` in `submitLogs`
  ```go
          if err != nil {
                  return fmt.Errorf("datadog: read logs response body: %w", err)
          }
  ```
- **[LOW] Proper handling** — `backend/internal/datadog/client.go:751` in `submitServiceCheck`
  ```go
          if err != nil {
                  return err
          }
  ```
- **[LOW] Proper handling** — `backend/internal/datadog/client.go:757` in `submitServiceCheck`
  ```go
          if err != nil {
                  return err
          }
  ```
- **[LOW] Proper handling** — `backend/internal/datadog/client.go:768` in `submitServiceCheck`
  ```go
          if err != nil {
                  return err
          }
  ```
- **[LOW] Proper handling** — `backend/internal/datadog/client.go:773` in `submitServiceCheck`
  ```go
          if err != nil {
                  return fmt.Errorf("datadog: read service check response body: %w", err)
          }
  ```

### `backend/internal/db/mongodb.go`

- **[LOW] Proper handling** — `backend/internal/db/mongodb.go:31` in `NewMongoDB`
  ```go
          if err != nil {
                  return nil, fmt.Errorf("failed to connect to MongoDB: %w", err)
          }
  ```
- **[LOW] Proper handling** — `backend/internal/db/mongodb.go:35` in `NewMongoDB`
  ```go
          if err := client.Ping(ctx, nil); err != nil {
                  return nil, fmt.Errorf("failed to ping MongoDB: %w", err)
          }
  ```
- **[LOW] Proper handling** — `backend/internal/db/mongodb.go:321` in `ensureIndexes`
  ```go
                  if err != nil {
                          if criticalCollections[idx.collection] {
                                  slog.Error("FATAL: failed to create indexes on critical collection", "collection", idx.collection, "error", err)
                                  os.Exit(1)
                          }
                          slog.Warn("failed to create indexes", "collection", idx.collection, "error", err)
  ... (1 more lines)
  ```

### `backend/internal/db/schema.go`

- **[MEDIUM] Logged only (no return)** — `backend/internal/db/schema.go:56` in `EnsureSchemaValidation`
  ```go
  		if err := m.Database.RunCommand(ctx, cmd).Err(); err != nil {
  			slog.Warn("failed to apply schema validation", "collection", cs.Collection, "error", err)
  		}
  ```

### `backend/internal/email/resend.go`

- **[MEDIUM] Logged only (no return)** — `backend/internal/email/resend.go:101` in `SendEmail`
  ```go
                  if err != nil {
                          slog.Warn("email: failed to read error response body", "status", resp.StatusCode, "error", err)
                  }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/email/resend.go:139` in `executeTemplate`
  ```go
          if err != nil {
                  slog.Error("email: failed to parse template, using fallback", "template", configKey, "error", err)
                  return fallback
          }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/email/resend.go:145` in `executeTemplate`
  ```go
          if err := t.Execute(&buf, data); err != nil {
                  slog.Error("email: failed to execute template, using fallback", "template", configKey, "error", err)
                  return fallback
          }
  ```
- **[LOW] Proper handling** — `backend/internal/email/resend.go:64` in `SendEmail`
  ```go
          if err != nil {
                  return fmt.Errorf("failed to marshal email request: %w", err)
          }
  ```
- **[LOW] Proper handling** — `backend/internal/email/resend.go:77` in `SendEmail`
  ```go
                  if err != nil {
                          return fmt.Errorf("failed to create request: %w", err)
                  }
  ```
- **[LOW] Proper handling** — `backend/internal/email/resend.go:85` in `SendEmail`
  ```go
                  if err != nil {
                          if attempt < maxRetries-1 {
                                  slog.Warn("email network error, will retry", "error", err)
                                  continue
                          }
                          return fmt.Errorf("failed to send email after %d attempts: %w", maxRetries, err)
  ... (1 more lines)
  ```

### `backend/internal/health/health.go`

- **[MEDIUM] Logged only (no return)** — `backend/internal/health/health.go:156` in `registerNode`
  ```go
          if err != nil {
                  slog.Error("health: failed to register node", "error", err)
          }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/health/health.go:169` in `heartbeat`
  ```go
          if err != nil {
                  slog.Warn("health: heartbeat failed", "error", err)
          }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/health/health.go:213` in `collectAndStore`
  ```go
          } else if err != nil {
                  slog.Warn("health: cpu collect error", "error", err)
          }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/health/health.go:245` in `collectAndStore`
  ```go
          } else if err != nil {
                  slog.Warn("health: network collect error", "error", err)
          }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/health/health.go:300` in `collectAndStore`
  ```go
          if _, err := s.db.SystemMetrics().InsertOne(ctx, metric); err != nil {
                  slog.Error("health: failed to store metrics", "error", err)
          }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/health/health.go:372` in `hostname`
  ```go
          if err != nil {
                  slog.Warn("health: failed to get hostname", "error", err)
                  return ""
          }
  ```

### `backend/internal/health/integrations.go`

- **[MEDIUM] Logged only (no return)** — `backend/internal/health/integrations.go:180` in `NewResendChecker`
  ```go
                  if _, err := io.Copy(io.Discard, resp.Body); err != nil {
                          slog.Warn("health: failed to drain resend response body", "error", err)
                  }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/health/integrations.go:203` in `NewGoogleOAuthChecker`
  ```go
                  if _, err := io.Copy(io.Discard, resp.Body); err != nil {
                          slog.Warn("health: failed to drain google oauth response body", "error", err)
                  }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/health/integrations.go:225` in `NewGitHubOAuthChecker`
  ```go
                  if _, err := io.Copy(io.Discard, resp.Body); err != nil {
                          slog.Warn("health: failed to drain github oauth response body", "error", err)
                  }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/health/integrations.go:247` in `NewMicrosoftOAuthChecker`
  ```go
                  if _, err := io.Copy(io.Discard, resp.Body); err != nil {
                          slog.Warn("health: failed to drain microsoft oauth response body", "error", err)
                  }
  ```
- **[LOW] Proper handling** — `backend/internal/health/integrations.go:124` in `runIntegrationChecks`
  ```go
                  if err != nil {
                          result.Status = models.IntegrationUnhealthy
                          result.Message = err.Error()
                          slog.Warn("health: integration unhealthy", "integration", entry.name, "error", err)
                  } else {
  ```
- **[LOW] Proper handling** — `backend/internal/health/integrations.go:171` in `NewResendChecker`
  ```go
                  if err != nil {
                          return err
                  }
  ```
- **[LOW] Proper handling** — `backend/internal/health/integrations.go:176` in `NewResendChecker`
  ```go
                  if err != nil {
                          return err
                  }
  ```
- **[LOW] Proper handling** — `backend/internal/health/integrations.go:195` in `NewGoogleOAuthChecker`
  ```go
                  if err != nil {
                          return err
                  }
  ```
- **[LOW] Proper handling** — `backend/internal/health/integrations.go:199` in `NewGoogleOAuthChecker`
  ```go
                  if err != nil {
                          return err
                  }
  ```
- **[LOW] Proper handling** — `backend/internal/health/integrations.go:217` in `NewGitHubOAuthChecker`
  ```go
                  if err != nil {
                          return err
                  }
  ```
- **[LOW] Proper handling** — `backend/internal/health/integrations.go:221` in `NewGitHubOAuthChecker`
  ```go
                  if err != nil {
                          return err
                  }
  ```
- **[LOW] Proper handling** — `backend/internal/health/integrations.go:239` in `NewMicrosoftOAuthChecker`
  ```go
                  if err != nil {
                          return err
                  }
  ```
- **[LOW] Proper handling** — `backend/internal/health/integrations.go:243` in `NewMicrosoftOAuthChecker`
  ```go
                  if err != nil {
                          return err
                  }
  ```

### `backend/internal/health/query.go`

- **[MEDIUM] Logged only (no return)** — `backend/internal/health/query.go:19` in `ListNodes`
  ```go
          if err != nil {
                  slog.Warn("health: invalid stale_timeout_seconds config, using default", "error", err)
          }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/health/query.go:121` in `GetIntegrationCounts24h`
  ```go
          if err != nil {
                  slog.Warn("health: GetIntegrationCounts24h aggregation failed", "error", err)
                  return 0, 0
          }
  ```
- **[LOW] Proper handling** — `backend/internal/health/query.go:37` in `ListNodes`
  ```go
          if err != nil {
                  return nil, err
          }
  ```
- **[LOW] Proper handling** — `backend/internal/health/query.go:43` in `ListNodes`
  ```go
          if err := cursor.All(ctx, &nodes); err != nil {
                  return nil, err
          }
  ```
- **[LOW] Proper handling** — `backend/internal/health/query.go:57` in `GetMetrics`
  ```go
          if err != nil {
                  return nil, err
          }
  ```
- **[LOW] Proper handling** — `backend/internal/health/query.go:63` in `GetMetrics`
  ```go
          if err := cursor.All(ctx, &metrics); err != nil {
                  return nil, err
          }
  ```
- **[LOW] Proper handling** — `backend/internal/health/query.go:76` in `GetAggregateMetrics`
  ```go
          if err != nil {
                  return nil, err
          }
  ```
- **[LOW] Proper handling** — `backend/internal/health/query.go:82` in `GetAggregateMetrics`
  ```go
          if err := cursor.All(ctx, &metrics); err != nil {
                  return nil, err
          }
  ```
- **[LOW] Proper handling** — `backend/internal/health/query.go:91` in `GetCurrentMetrics`
  ```go
          if err != nil {
                  return nil, err
          }
  ```

### `backend/internal/metrics/metrics.go`

- **[MEDIUM] Logged only (no return)** — `backend/internal/metrics/metrics.go:33` in `New`
  ```go
          if err != nil {
                  slog.Warn("metrics: failed to get hostname", "error", err)
          }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/metrics/metrics.go:132` in `tryAcquireOrRenew`
  ```go
          if err := result.Decode(&doc); err != nil {
                  slog.Warn("metrics: failed to decode leader lock document", "error", err)
                  return false
          }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/metrics/metrics.go:149` in `isLeader`
  ```go
          if err != nil {
                  slog.Warn("metrics: failed to read leader lock for isLeader check", "error", err)
                  return false
          }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/metrics/metrics.go:193` in `collectDaily`
  ```go
                  if err != nil {
                          slog.Error("Metrics DAU/WAU/MAU aggregation error", "error", err)
                          return
                  }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/metrics/metrics.go:228` in `collectDaily`
  ```go
                  if err != nil {
                          slog.Error("Metrics revenue aggregation error", "error", err)
                          return
                  }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/metrics/metrics.go:264` in `collectDaily`
  ```go
                  if err != nil {
                          slog.Error("Metrics ARR aggregation error", "error", err)
                          return
                  }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/metrics/metrics.go:292` in `collectDaily`
  ```go
          if err != nil {
                  slog.Error("Metrics upsert daily metric error", "error", err)
          }
  ```
- **[LOW] Proper handling** — `backend/internal/metrics/metrics.go:116` in `tryAcquireOrRenew`
  ```go
          if result.Err() != nil {
                  if result.Err() == mongo.ErrNoDocuments {
                          // Another holder has the lock and it hasn't expired
                          return false
                  }
                  // On upsert conflict (duplicate key during race), the other machine won
  ... (6 more lines)
  ```

### `backend/internal/middleware/auth.go`

- **[MEDIUM] Logged only (no return)** — `backend/internal/middleware/auth.go:169` in `isTokenRevoked`
  ```go
          if err != nil {
                  slog.Warn("revoked-token lookup failed, denying access", "error", err)
                  return true
          }
  ```
- **[LOW] Proper handling** — `backend/internal/middleware/auth.go:69` in `authenticateJWT`
  ```go
          if err != nil {
                  if err == auth.ErrExpiredToken {
                          http.Error(w, `{"error":"Token has expired"}`, http.StatusUnauthorized)
                          return
                  }
                  http.Error(w, `{"error":"Invalid token"}`, http.StatusUnauthorized)
  ... (2 more lines)
  ```
- **[LOW] Proper handling** — `backend/internal/middleware/auth.go:84` in `authenticateJWT`
  ```go
          if err != nil {
                  http.Error(w, `{"error":"Invalid user ID"}`, http.StatusUnauthorized)
                  return
          }
  ```
- **[LOW] Proper handling** — `backend/internal/middleware/auth.go:91` in `authenticateJWT`
  ```go
          if err != nil {
                  http.Error(w, `{"error":"User not found"}`, http.StatusUnauthorized)
                  return
          }
  ```
- **[LOW] Proper handling** — `backend/internal/middleware/auth.go:117` in `authenticateAPIKey`
  ```go
          if err != nil {
                  http.Error(w, `{"error":"Invalid API key"}`, http.StatusUnauthorized)
                  return
          }
  ```
- **[LOW] Proper handling** — `backend/internal/middleware/auth.go:125` in `authenticateAPIKey`
  ```go
          if err != nil || !user.IsActive {
                  http.Error(w, `{"error":"API key owner account is inactive"}`, http.StatusUnauthorized)
                  return
          }
  ```
- **[LOW] Proper handling** — `backend/internal/middleware/auth.go:136` in `authenticateAPIKey`
  ```go
                  if err != nil {
                          http.Error(w, `{"error":"System configuration error"}`, http.StatusInternalServerError)
                          return
                  }
  ```

### `backend/internal/middleware/ratelimit.go`

- **[MEDIUM] Logged only (no return)** — `backend/internal/middleware/ratelimit.go:238` in `GetClientIP`
  ```go
          if err != nil {
                  slog.Debug("middleware: failed to split host:port, using raw RemoteAddr", "remoteAddr", r.RemoteAddr, "error", err)
                  return r.RemoteAddr
          }
  ```
- **[LOW] Proper handling** — `backend/internal/middleware/ratelimit.go:162` in `allowDistributed`
  ```go
          if err != nil {
                  if err == mongo.ErrNoDocuments {
                          // No valid window exists — reset/create with count=1.
                          err = rl.collection.FindOneAndUpdate(ctx,
                                  bson.M{"_id": key},
                                  bson.M{"$set": bson.M{
  ... (13 more lines)
  ```
- **[LOW] Proper handling** — `backend/internal/middleware/ratelimit.go:174` in `allowDistributed`
  ```go
                          if err != nil {
                                  return false, 0, now, err
                          }
  ```

### `backend/internal/middleware/requestid.go`

- **[MEDIUM] Logged only (no return)** — `backend/internal/middleware/requestid.go:36` in `generateRequestID`
  ```go
          if _, err := rand.Read(b); err != nil {
                  // Fallback to timestamp-based ID on catastrophic rand failure
                  slog.Warn("middleware: crypto/rand failed, using timestamp-based request ID", "error", err)
                  return fmt.Sprintf("%x", time.Now().UnixNano())
          }
  ```

### `backend/internal/middleware/tenant.go`

- **[LOW] Proper handling** — `backend/internal/middleware/tenant.go:45` in `RequireTenant`
  ```go
  		if err != nil {
  			http.Error(w, `{"error":"Invalid tenant ID"}`, http.StatusBadRequest)
  			return
  		}
  ```
- **[LOW] Proper handling** — `backend/internal/middleware/tenant.go:52` in `RequireTenant`
  ```go
  		if err != nil {
  			http.Error(w, `{"error":"Tenant not found"}`, http.StatusNotFound)
  			return
  		}
  ```
- **[LOW] Proper handling** — `backend/internal/middleware/tenant.go:68` in `RequireTenant`
  ```go
  		if err != nil {
  			http.Error(w, `{"error":"Not a member of this tenant"}`, http.StatusForbidden)
  			return
  		}
  ```

### `backend/internal/planstore/seed.go`

- **[LOW] Proper handling** — `backend/internal/planstore/seed.go:36` in `Seed`
  ```go
                  if _, err := col.InsertOne(ctx, plan); err != nil {
                          return err
                  }
  ```
- **[LOW] Proper handling** — `backend/internal/planstore/seed.go:40` in `Seed`
  ```go
          } else if err != nil {
                  return err
          }
  ```

### `backend/internal/stripe/stripe.go`

- **[LOW] Proper handling** — `backend/internal/stripe/stripe.go:78` in `GetOrCreateCustomer`
  ```go
  	if err != nil {
  		return "", fmt.Errorf("stripe customer create: %w", err)
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/stripe/stripe.go:86` in `GetOrCreateCustomer`
  ```go
  	if err != nil {
  		return "", fmt.Errorf("save stripe customer id: %w", err)
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/stripe/stripe.go:121` in `GetOrCreatePrice`
  ```go
  	if err != nil {
  		return "", fmt.Errorf("stripe product create: %w", err)
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/stripe/stripe.go:138` in `GetOrCreatePrice`
  ```go
  	if err != nil {
  		return "", fmt.Errorf("stripe price create: %w", err)
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/stripe/stripe.go:228` in `CreateCheckoutSession`
  ```go
  		if err != nil {
  			return "", err
  		}
  ```
- **[LOW] Proper handling** — `backend/internal/stripe/stripe.go:284` in `CreateCheckoutSession`
  ```go
  	if err != nil {
  		return "", fmt.Errorf("stripe checkout create: %w", err)
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/stripe/stripe.go:299` in `CreateBillingPortalSession`
  ```go
  	if err != nil {
  		return "", fmt.Errorf("stripe portal create: %w", err)
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/stripe/stripe.go:313` in `CancelSubscriptionAtPeriodEnd`
  ```go
  	if err != nil {
  		return nil, fmt.Errorf("stripe cancel subscription: %w", err)
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/stripe/stripe.go:333` in `CancelSubscriptionImmediately`
  ```go
  	if err != nil {
  		return fmt.Errorf("stripe cancel subscription: %w", err)
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/stripe/stripe.go:357` in `NextInvoiceNumber`
  ```go
  	if err != nil {
  		return "", fmt.Errorf("generate invoice number: %w", err)
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/stripe/stripe.go:379` in `UpdateSubscriptionQuantity`
  ```go
  	if err != nil {
  		return fmt.Errorf("stripe get subscription: %w", err)
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/stripe/stripe.go:399` in `UpdateSubscriptionQuantity`
  ```go
  	if err != nil {
  		return fmt.Errorf("stripe update subscription quantity: %w", err)
  	}
  ```

### `backend/internal/syslog/syslog.go`

- **[MEDIUM] Logged only (no return)** — `backend/internal/syslog/syslog.go:97` in `log`
  ```go
  	if _, err := l.db.SystemLogs().InsertOne(ctx, entry); err != nil {
  		slog.Error("syslog: failed to write log", "error", err)
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/syslog/syslog.go:114` in `log`
  ```go
  		if _, err := l.db.SystemLogs().InsertOne(ctx, alert); err != nil {
  			slog.Error("syslog: failed to write injection alert", "error", err)
  		}
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/syslog/syslog.go:137` in `logCategorized`
  ```go
  	if _, err := l.db.SystemLogs().InsertOne(ctx, entry); err != nil {
  		slog.Error("syslog: failed to write log", "error", err)
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/syslog/syslog.go:154` in `logCategorized`
  ```go
  		if _, err := l.db.SystemLogs().InsertOne(ctx, alert); err != nil {
  			slog.Error("syslog: failed to write injection alert", "error", err)
  		}
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/syslog/syslog.go:234` in `LogTenantActivity`
  ```go
  	if _, err := l.db.SystemLogs().InsertOne(ctx, entry); err != nil {
  		slog.Error("syslog: failed to write tenant activity log", "error", err)
  	}
  ```

### `backend/internal/telemetry/service.go`

- **[MEDIUM] Logged only (no return)** — `backend/internal/telemetry/service.go:84` in `flushLoop`
  ```go
                  if err != nil {
                          slog.Warn("telemetry: flush failed, will retry", "count", len(buf), "error", err)
                          return false // retain buffer for next attempt
                  }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/telemetry/service.go:189` in `TrackBatch`
  ```go
          if err != nil {
                  slog.Warn("telemetry: failed to track batch", "count", len(events), "error", err)
          }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/telemetry/service.go:318` in `FunnelMetrics`
  ```go
          if err != nil {
                  slog.Warn("telemetry: failed to count unique visitors", "error", err)
          }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/telemetry/service.go:326` in `FunnelMetrics`
  ```go
          if err != nil {
                  slog.Warn("telemetry: failed to count registrations", "error", err)
          }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/telemetry/service.go:336` in `FunnelMetrics`
  ```go
          if err != nil {
                  slog.Warn("telemetry: failed to count plan page views", "error", err)
          }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/telemetry/service.go:345` in `FunnelMetrics`
  ```go
          if err != nil {
                  slog.Warn("telemetry: failed to count checkouts", "error", err)
          }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/telemetry/service.go:354` in `FunnelMetrics`
  ```go
          if err != nil {
                  slog.Warn("telemetry: failed to count conversions", "error", err)
          }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/telemetry/service.go:362` in `FunnelMetrics`
  ```go
          if err != nil {
                  slog.Warn("telemetry: failed to count upgrades", "error", err)
          }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/telemetry/service.go:507` in `EngagementMetrics`
  ```go
          if err != nil {
                  slog.Warn("telemetry: failed to get active tenant IDs", "error", err)
                  return &EngagementData{}, nil
          }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/telemetry/service.go:514` in `EngagementMetrics`
  ```go
          if err != nil {
                  slog.Warn("telemetry: failed to get user IDs for tenants", "error", err)
                  return &EngagementData{}, nil
          }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/telemetry/service.go:539` in `EngagementMetrics`
  ```go
          if err != nil {
                  slog.Warn("telemetry: failed to count total logins", "error", err)
          }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/telemetry/service.go:603` in `computeKPIs`
  ```go
          if err != nil {
                  slog.Warn("telemetry: failed to count active subscribers", "error", err)
          }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/telemetry/service.go:609` in `computeKPIs`
  ```go
          if err != nil {
                  slog.Warn("telemetry: failed to count total registrations", "error", err)
          }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/telemetry/service.go:627` in `computeKPIs`
  ```go
          if err != nil {
                  slog.Warn("telemetry: failed to count cancellations this month", "error", err)
          }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/telemetry/service.go:634` in `computeKPIs`
  ```go
          if err != nil {
                  slog.Warn("telemetry: failed to count active at month start", "error", err)
          }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/telemetry/service.go:646` in `computeKPIs`
  ```go
          if err != nil {
                  slog.Warn("telemetry: failed to count total trials", "error", err)
          }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/telemetry/service.go:653` in `computeKPIs`
  ```go
          if err != nil {
                  slog.Warn("telemetry: failed to count converted trials", "error", err)
          }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/telemetry/service.go:709` in `CustomEventSummary`
  ```go
          if err != nil {
                  slog.Warn("telemetry: failed to count custom events", "event", eventName, "error", err)
          }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/telemetry/service.go:725` in `CustomEventSummary`
  ```go
          if err != nil {
                  slog.Warn("telemetry: failed to query custom event trend", "event", eventName, "error", err)
                  return &CustomEventData{EventName: eventName, TotalCount: totalCount}, nil
          }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/telemetry/service.go:911` in `weeklyActiveUsers`
  ```go
          if err != nil {
                  slog.Warn("telemetry: weeklyActiveUsers aggregation failed", "error", err)
                  return nil
          }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/telemetry/service.go:959` in `monthlyActiveUsers`
  ```go
          if err != nil {
                  slog.Warn("telemetry: monthlyActiveUsers aggregation failed", "error", err)
                  return nil
          }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/telemetry/service.go:997` in `topCustomEvents`
  ```go
          if err != nil {
                  slog.Warn("telemetry: topCustomEvents aggregation failed", "error", err)
                  return nil
          }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/telemetry/service.go:1028` in `creditConsumptionTrend`
  ```go
          if err != nil {
                  slog.Warn("telemetry: creditConsumptionTrend aggregation failed", "error", err)
                  return nil
          }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/telemetry/service.go:1104` in `calculateMRR`
  ```go
          if err != nil {
                  slog.Warn("telemetry: calculateMRR aggregation failed", "error", err)
                  return 0
          }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/telemetry/service.go:1148` in `medianTimeToFirstPurchase`
  ```go
          if err != nil {
                  slog.Warn("telemetry: medianTimeToFirstPurchase aggregation failed", "error", err)
                  return 0
          }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/telemetry/service.go:1198` in `planDistribution`
  ```go
          if err != nil {
                  slog.Warn("telemetry: planDistribution aggregation failed", "error", err)
                  return nil
          }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/telemetry/service.go:1239` in `mrrTrend`
  ```go
          if err != nil {
                  slog.Warn("telemetry: mrrTrend query failed", "error", err)
                  return nil
          }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/telemetry/service.go:1270` in `subscriberTrend`
  ```go
          if err != nil {
                  slog.Warn("telemetry: subscriberTrend aggregation failed", "error", err)
                  return nil
          }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/telemetry/service.go:1291` in `aggregateDailyPoints`
  ```go
          if err != nil {
                  slog.Warn("telemetry: aggregateDailyPoints aggregation failed", "error", err)
                  return nil
          }
  ```
- **[LOW] Proper handling** — `backend/internal/telemetry/service.go:451` in `RetentionCohorts`
  ```go
          if err != nil {
                  return nil, err
          }
  ```
- **[LOW] Proper handling** — `backend/internal/telemetry/service.go:577` in `KPIs`
  ```go
                  if err != nil {
                          return nil, err
                  }
  ```
- **[LOW] Proper handling** — `backend/internal/telemetry/service.go:587` in `KPIs`
  ```go
          if err != nil {
                  return nil, err
          }
  ```
- **[LOW] Proper handling** — `backend/internal/telemetry/service.go:762` in `ListEventTypes`
  ```go
          if err != nil {
                  return nil, err
          }
  ```
- **[LOW] Proper handling** — `backend/internal/telemetry/service.go:801` in `countDistinct`
  ```go
          if err != nil {
                  return 0, err
          }
  ```
- **[LOW] Proper handling** — `backend/internal/telemetry/service.go:822` in `getActiveTenantIDs`
  ```go
          if err != nil {
                  return nil, err
          }
  ```
- **[LOW] Proper handling** — `backend/internal/telemetry/service.go:846` in `getUserIDsForTenants`
  ```go
          if err != nil {
                  return nil, err
          }
  ```

### `backend/internal/testutil/testutil.go`

- **[MEDIUM] Logged only (no return)** — `backend/internal/testutil/testutil.go:28` in `loadEnvTest`
  ```go
          if err != nil {
                  log.Printf("testutil: warning: failed to get cwd: %v", err)
          }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/testutil/testutil.go:94` in `MustConnectTestDB`
  ```go
                  if err != nil {
                          log.Printf("testutil: warning: failed to list collections: %v", err)
                  }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/testutil/testutil.go:102` in `MustConnectTestDB`
  ```go
                  if err := database.Close(ctx); err != nil {
                          log.Printf("testutil: warning: failed to close database: %v", err)
                  }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/testutil/testutil.go:140` in `ConnectTestDB`
  ```go
                  if err != nil {
                          log.Printf("testutil: warning: failed to list collections: %v", err)
                  }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/testutil/testutil.go:148` in `ConnectTestDB`
  ```go
                  if err := database.Close(ctx); err != nil {
                          log.Printf("testutil: warning: failed to close database: %v", err)
                  }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/testutil/testutil.go:162` in `findAndSetConfigDir`
  ```go
          if err != nil {
                  log.Printf("testutil: warning: failed to get cwd: %v", err)
          }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/testutil/testutil.go:195` in `hasYAMLConfigs`
  ```go
          if err != nil {
                  log.Printf("testutil: warning: failed to read config dir %s: %v", dir, err)
                  return false
          }
  ```
- **[LOW] Proper handling** — `backend/internal/testutil/testutil.go:73` in `MustConnectTestDB`
  ```go
          if err != nil {
                  t.Fatalf("testutil: failed to load test config: %v", err)
          }
  ```
- **[LOW] Proper handling** — `backend/internal/testutil/testutil.go:83` in `MustConnectTestDB`
  ```go
          if err != nil {
                  t.Fatalf("testutil: failed to connect to test database: %v", err)
          }
  ```
- **[LOW] Proper handling** — `backend/internal/testutil/testutil.go:123` in `ConnectTestDB`
  ```go
          if err != nil {
                  log.Fatalf("testutil: failed to load test config: %v", err)
          }
  ```
- **[LOW] Proper handling** — `backend/internal/testutil/testutil.go:132` in `ConnectTestDB`
  ```go
          if err != nil {
                  log.Fatalf("testutil: failed to connect to test database: %v", err)
          }
  ```
- **[LOW] Proper handling** — `backend/internal/testutil/testutil.go:241` in `TestConfig`
  ```go
          if err != nil {
                  t.Fatalf("testutil: failed to load test config: %v", err)
          }
  ```
- **[LOW] Proper handling** — `backend/internal/testutil/testutil.go:254` in `CreateTestUser`
  ```go
          if err != nil {
                  t.Fatalf("testutil: failed to hash password: %v", err)
          }
  ```
- **[LOW] Proper handling** — `backend/internal/testutil/testutil.go:271` in `CreateTestUser`
  ```go
          if err != nil {
                  t.Fatalf("testutil: failed to create test user: %v", err)
          }
  ```
- **[LOW] Proper handling** — `backend/internal/testutil/testutil.go:293` in `CreateTestTenant`
  ```go
          if err != nil {
                  t.Fatalf("testutil: failed to create test tenant: %v", err)
          }
  ```
- **[LOW] Proper handling** — `backend/internal/testutil/testutil.go:306` in `CreateTestTenant`
  ```go
          if err != nil {
                  t.Fatalf("testutil: failed to create test membership: %v", err)
          }
  ```
- **[LOW] Proper handling** — `backend/internal/testutil/testutil.go:324` in `MarkSystemInitialized`
  ```go
          if err != nil {
                  t.Fatalf("testutil: failed to mark system initialized: %v", err)
          }
  ```
- **[LOW] Proper handling** — `backend/internal/testutil/testutil.go:342` in `InsertTestLogs`
  ```go
                  if err != nil {
                          t.Fatalf("testutil: failed to insert test log: %v", err)
                  }
  ```
- **[LOW] Proper handling** — `backend/internal/testutil/testutil.go:353` in `CountDocuments`
  ```go
          if err != nil {
                  t.Fatalf("testutil: failed to count documents: %v", err)
          }
  ```
- **[LOW] Proper handling** — `backend/internal/testutil/testutil.go:363` in `ParseJSON`
  ```go
          if err := json.NewDecoder(resp.Body).Decode(target); err != nil {
                  t.Fatalf("testutil: failed to parse JSON response: %v", err)
          }
  ```
- **[LOW] Proper handling** — `backend/internal/testutil/testutil.go:393` in `CreateTestMembership`
  ```go
          if err != nil {
                  t.Fatalf("testutil: failed to create test membership: %v", err)
          }
  ```
- **[LOW] Proper handling** — `backend/internal/testutil/testutil.go:417` in `CreateTestPlan`
  ```go
          if err != nil {
                  t.Fatalf("testutil: failed to create test plan: %v", err)
          }
  ```
- **[LOW] Proper handling** — `backend/internal/testutil/testutil.go:439` in `CreateTestAPIKey`
  ```go
          if err != nil {
                  t.Fatalf("testutil: failed to create test API key: %v", err)
          }
  ```
- **[LOW] Proper handling** — `backend/internal/testutil/testutil.go:463` in `CreateTestWebhook`
  ```go
          if err != nil {
                  t.Fatalf("testutil: failed to create test webhook: %v", err)
          }
  ```
- **[LOW] Proper handling** — `backend/internal/testutil/testutil.go:486` in `CreateTestInvitation`
  ```go
          if err != nil {
                  t.Fatalf("testutil: failed to create test invitation: %v", err)
          }
  ```

### `backend/internal/version/check.go`

- **[MEDIUM] Logged only (no return)** — `backend/internal/version/check.go:29` in `CheckAndMigrate`
  ```go
          if err != nil {
                  // System not initialized yet — nothing to check
                  slog.Debug("version: system config not available, skipping migration check", "error", err)
                  return
          }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/version/check.go:66` in `sendUpgradeMessage`
  ```go
          if err != nil {
                  slog.Warn("Could not find root tenant for upgrade message", "error", err)
                  return
          }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/version/check.go:76` in `sendUpgradeMessage`
  ```go
          if err != nil {
                  slog.Warn("Could not find root tenant owner for upgrade message", "error", err)
                  return
          }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/version/check.go:91` in `sendUpgradeMessage`
  ```go
          if _, err := database.Messages().InsertOne(ctx, msg); err != nil {
                  slog.Warn("Failed to send upgrade message", "error", err)
          }
  ```

### `backend/internal/version/version.go`

- **[MEDIUM] Logged only (no return)** — `backend/internal/version/version.go:32` in `Load`
  ```go
          if err != nil {
                  slog.Warn("version: failed to get cwd, will not search for VERSION file", "error", err)
          }
  ```

### `backend/internal/webhooks/crypto.go`

- **[LOW] Proper handling** — `backend/internal/webhooks/crypto.go:21` in `EncryptSecret`
  ```go
  	if err != nil {
  		return "", fmt.Errorf("create cipher: %w", err)
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/webhooks/crypto.go:26` in `EncryptSecret`
  ```go
  	if err != nil {
  		return "", fmt.Errorf("create GCM: %w", err)
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/webhooks/crypto.go:31` in `EncryptSecret`
  ```go
  	if _, err := io.ReadFull(rand.Reader, nonce); err != nil {
  		return "", fmt.Errorf("generate nonce: %w", err)
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/webhooks/crypto.go:46` in `DecryptSecret`
  ```go
  	if err != nil {
  		return "", fmt.Errorf("decode base64: %w", err)
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/webhooks/crypto.go:51` in `DecryptSecret`
  ```go
  	if err != nil {
  		return "", fmt.Errorf("create cipher: %w", err)
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/webhooks/crypto.go:56` in `DecryptSecret`
  ```go
  	if err != nil {
  		return "", fmt.Errorf("create GCM: %w", err)
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/webhooks/crypto.go:67` in `DecryptSecret`
  ```go
  	if err != nil {
  		return "", fmt.Errorf("decrypt: %w", err)
  	}
  ```
- **[LOW] Proper handling** — `backend/internal/webhooks/crypto.go:81` in `ParseEncryptionKey`
  ```go
  	if err != nil {
  		return nil, fmt.Errorf("invalid hex key: %w", err)
  	}
  ```

### `backend/internal/webhooks/dispatcher.go`

- **[MEDIUM] Logged only (no return)** — `backend/internal/webhooks/dispatcher.go:198` in `dispatch`
  ```go
          if err != nil {
                  slog.Error("webhooks: failed to query webhooks", "event_type", eventType, "error", err)
                  return
          }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/webhooks/dispatcher.go:205` in `dispatch`
  ```go
          if err := cursor.All(ctx, &hooks); err != nil {
                  slog.Error("webhooks: failed to decode webhooks", "error", err)
                  return
          }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/webhooks/dispatcher.go:232` in `deliverWithRetry`
  ```go
          if err != nil {
                  slog.Error("webhooks: failed to marshal payload", "error", err)
                  return
          }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/webhooks/dispatcher.go:241` in `deliverWithRetry`
  ```go
          if err != nil {
                  slog.Error("webhooks: failed to create request", "webhook", hook.Name, "error", err)
                  return
          }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/webhooks/dispatcher.go:287` in `deliverWithRetry`
  ```go
          if _, err := d.db.WebhookDeliveries().InsertOne(deliverCtx, delivery); err != nil {
                  slog.Error("webhooks: failed to record delivery", "webhook", hook.Name, "error", err)
          }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/webhooks/dispatcher.go:331` in `computeSignature`
  ```go
          if _, err := mac.Write(payload); err != nil {
                  slog.Warn("webhooks: failed to write payload to HMAC", "error", err)
          }
  ```
- **[MEDIUM] Logged only (no return)** — `backend/internal/webhooks/dispatcher.go:421` in `DeliverTest`
  ```go
          if _, err := d.db.WebhookDeliveries().InsertOne(ctx, delivery); err != nil {
                  slog.Error("webhooks: failed to record test delivery", "webhook", hook.Name, "error", err)
          }
  ```
- **[LOW] Proper handling** — `backend/internal/webhooks/dispatcher.go:273` in `deliverWithRetry`
  ```go
          if err != nil {
                  delivery.Success = false
                  delivery.ResponseCode = 0
                  delivery.ResponseBody = err.Error()
          } else {
  ```
- **[LOW] Proper handling** — `backend/internal/webhooks/dispatcher.go:317` in `resolveSecret`
  ```go
          if err != nil {
                  // Fallback: may be a legacy plaintext secret not yet migrated
                  if len(stored) > 0 && stored[0] != 0 {
                          return stored
                  }
                  slog.Error("webhooks: failed to decrypt secret", "error", err)
  ... (2 more lines)
  ```
- **[LOW] Proper handling** — `backend/internal/webhooks/dispatcher.go:356` in `DeliverTest`
  ```go
          if err != nil {
                  slog.Error("webhooks: failed to marshal test payload", "error", err)
                  return models.WebhookDelivery{
                          ID:           primitive.NewObjectID(),
                          WebhookID:    hook.ID,
                          EventType:    models.WebhookEventTenantCreated,
  ... (6 more lines)
  ```
- **[LOW] Proper handling** — `backend/internal/webhooks/dispatcher.go:370` in `DeliverTest`
  ```go
          if err != nil {
                  return models.WebhookDelivery{
                          ID:           primitive.NewObjectID(),
                          WebhookID:    hook.ID,
                          EventType:    models.WebhookEventTenantCreated,
                          Payload:      string(body),
  ... (6 more lines)
  ```
- **[LOW] Proper handling** — `backend/internal/webhooks/dispatcher.go:408` in `DeliverTest`
  ```go
          if err != nil {
                  delivery.Success = false
                  delivery.ResponseCode = 0
                  delivery.ResponseBody = err.Error()
          } else {
  ```

## Test File Error Handling (summary)

| Metric | Value |
| --- | --- |
| Test files scanned | 33 |
| Total lines | 8,984 |
| Total error-handling sites | 349 |
| Properly handled | 207 |
| Logged only | 10 |
| Swallowed | 1 |
| Ignored (`_`) | 70 |
| Missing checks | 61 |
| Panic on error | 0 |
| % properly handled | 59.31% |

## Methodology

The audit scans every `.go` file (excluding `vendor/`, `node_modules/`, `.git/`, `graphify-out/`, `testdata/`) and applies these heuristics:

1. **`if X != nil { ... }` blocks** are located via brace matching (strings and comments are masked out first). The **full** block body is then classified in priority order:
    - **`proper_handling`** (LOW) — body returns the error directly (`return err`, `return fmt.Errorf("...: %w", err)`, `return res.Err()`), OR terminates the process / test (`os.Exit(non-zero)`, `log.Fatal*`, `t.Fatal*`), OR contains a recognised proper-handler pattern: `http.Redirect`, `respondWithError`/`http.Error`/`writeError`/etc., an `ErrNoDocuments`/`mongo.ErrNoDocuments` check, a `continue` statement (batch processing), or an assignment to a variable / struct field (`page = 1`, `delivery.Success = false`, …).
    - **`panic_on_error`** (MEDIUM) — body calls `panic(...)`.
    - **`logged_only`** (MEDIUM) — body acknowledges the error via `slog.Warn/Error/Info/Debug`, `log.Print*`/`Fatal*`/`Panic*`, `fmt.Print*`/`Fprint*`/`Sprint*`, or `fmt.Fprint*(os.Stderr, ...)`, without propagating the original `err`. (`fmt.Errorf` is excluded — that's error construction, not logging.)
    - **`swallowed`** (HIGH) — body is empty, or only contains a bare `return` / `return nil` / `return <non-err>` (including `return errors.New("...")` which drops the original error), and matches none of the proper-handler or logging patterns above.
2. **Ignored errors** are detected as `result, _ := someFunc(...)` patterns where the last return value is discarded with `_`. `for k, _ := range m` is excluded.
3. **Missing error checks** are detected as statement-form calls (not assigned, not preceded by `defer`/`go`) to a known error-returning method such as `Close`, `Write`, `InsertOne`, `UpdateOne`, `Marshal`, etc. This is heuristic and may produce false positives — review each finding.

Severity: **HIGH** for swallowed/ignored/missing, **MEDIUM** for logged-only and panic-on-error, **LOW** for proper handling.
