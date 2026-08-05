# Error Handling Audit

**Target:** `/home/z/my-project/repos/lastsaas/backend`

## Summary (non-test files)

| Metric | Value |
| --- | --- |
| Files scanned | 101 |
| Total lines | 28,236 |
| Total error-handling sites | **998** |
| Properly handled | 224 |
| Logged only (no return) | 373 |
| Swallowed errors | 133 |
| Ignored errors (`_`) | 143 |
| Missing error checks | 124 |
| Panic on error | 1 |
| % properly handled | **22.44%** |

## Pattern Breakdown (non-test files)

| Pattern | Count | Severity |
| --- | ---: | --- |
| Proper handling | 224 | LOW |
| Logged only (no return) | 373 | MEDIUM |
| Swallowed error | 133 | HIGH |
| Ignored error (`_`) | 143 | HIGH |
| Missing error check | 124 | HIGH |
| Panic on error | 1 | MEDIUM |

## Severity Breakdown (non-test files)

| Severity | Count |
| --- | ---: |
| HIGH | 400 |
| MEDIUM | 374 |
| LOW | 224 |

## Most Problematic Files (non-test)

| File | Issues | Sites | Swallowed | Ignored | Missing | Logged | Panic |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `internal/api/handlers/auth.go` | 50 | 120 | 35 | 7 | 8 | 69 | 0 |
| `internal/api/handlers/admin.go` | 50 | 104 | 1 | 30 | 19 | 54 | 0 |
| `internal/telemetry/service.go` | 30 | 37 | 15 | 15 | 0 | 0 | 0 |
| `cmd/lastsaas/main.go` | 17 | 45 | 4 | 4 | 9 | 0 | 0 |
| `internal/api/handlers/tenant.go` | 16 | 30 | 2 | 8 | 6 | 14 | 0 |
| `internal/api/handlers/billing.go` | 15 | 44 | 2 | 10 | 3 | 29 | 0 |
| `internal/datadog/client.go` | 14 | 35 | 2 | 6 | 6 | 4 | 0 |
| `cmd/lastsaas/process.go` | 14 | 22 | 2 | 0 | 12 | 0 | 0 |
| `cmd/lastsaas/cmd_financial.go` | 11 | 15 | 0 | 5 | 6 | 0 | 0 |
| `internal/api/handlers/plans.go` | 10 | 33 | 1 | 6 | 3 | 23 | 0 |
| `internal/testutil/testutil.go` | 10 | 28 | 1 | 4 | 5 | 0 | 0 |
| `internal/health/integrations.go` | 9 | 17 | 1 | 0 | 8 | 0 | 0 |
| `internal/api/handlers/webhook.go` | 8 | 20 | 2 | 5 | 1 | 4 | 0 |
| `internal/metrics/metrics.go` | 8 | 9 | 6 | 2 | 0 | 1 | 0 |
| `cmd/lastsaas/cmd_stats.go` | 8 | 8 | 0 | 6 | 2 | 0 | 0 |

## Detailed Findings (non-test files)

### `cmd/lastsaas/cmd_db.go`

- **[HIGH] Swallowed error** — `cmd/lastsaas/cmd_db.go:65` in `cmdDBStats`
  ```go
  		if err != nil {
  			continue
  		}
  ```
- **[LOW] Proper handling** — `cmd/lastsaas/cmd_db.go:41` in `cmdDBStats`
  ```go
  	if err != nil {
  		fmt.Fprintf(os.Stderr, "Failed to get database stats: %v\n", err)
  		os.Exit(1)
  	}
  ```
- **[LOW] Proper handling** — `cmd/lastsaas/cmd_db.go:48` in `cmdDBStats`
  ```go
  	if err != nil {
  		fmt.Fprintf(os.Stderr, "Failed to list collections: %v\n", err)
  		os.Exit(1)
  	}
  ```

### `cmd/lastsaas/cmd_doctor.go`

- **[HIGH] Missing error check** — `cmd/lastsaas/cmd_doctor.go:57` in `cmdDoctor`
  - _statement-form call to known error-returning 'database.Close()'_
  ```go
  		database.Close(ctx)
  ```
- **[HIGH] Ignored error (`_`)** — `cmd/lastsaas/cmd_doctor.go:101` in `cmdDoctor`
  - _error explicitly discarded with `_`_
  ```go
  			ownerCount, _ := database.TenantMemberships().CountDocuments(ctx, bson.M{
  ```
- **[HIGH] Ignored error (`_`)** — `cmd/lastsaas/cmd_doctor.go:110` in `cmdDoctor`
  - _error explicitly discarded with `_`_
  ```go
  	nodeCount, _ := database.SystemNodes().CountDocuments(ctx, bson.M{
  ```
- **[LOW] Proper handling** — `cmd/lastsaas/cmd_doctor.go:42` in `cmdDoctor`
  ```go
  	if err != nil {
  		fmt.Printf("\n  Results: %d passed, %d warnings, %d failed\n", passes, warnings, failures)
  		os.Exit(1)
  	}
  ```
- **[LOW] Proper handling** — `cmd/lastsaas/cmd_doctor.go:50` in `cmdDoctor`
  ```go
  	if err != nil {
  		fmt.Printf("\n  Results: %d passed, %d warnings, %d failed\n", passes, warnings, failures)
  		os.Exit(1)
  	}
  ```

### `cmd/lastsaas/cmd_financial.go`

- **[HIGH] Ignored error (`_`)** — `cmd/lastsaas/cmd_financial.go:58` in `cmdFinancialSummary`
  - _error explicitly discarded with `_`_
  ```go
  	revCursor, _ := database.FinancialTransactions().Aggregate(ctx, revPipeline)
  ```
- **[HIGH] Missing error check** — `cmd/lastsaas/cmd_financial.go:68` in `cmdFinancialSummary`
  - _statement-form call to known error-returning 'revCursor.Close()'_
  ```go
  		revCursor.Close(ctx)
  ```
- **[HIGH] Ignored error (`_`)** — `cmd/lastsaas/cmd_financial.go:81` in `cmdFinancialSummary`
  - _error explicitly discarded with `_`_
  ```go
  	refCursor, _ := database.FinancialTransactions().Aggregate(ctx, refundPipeline)
  ```
- **[HIGH] Missing error check** — `cmd/lastsaas/cmd_financial.go:90` in `cmdFinancialSummary`
  - _statement-form call to known error-returning 'refCursor.Close()'_
  ```go
  		refCursor.Close(ctx)
  ```
- **[HIGH] Ignored error (`_`)** — `cmd/lastsaas/cmd_financial.go:105` in `cmdFinancialSummary`
  - _error explicitly discarded with `_`_
  ```go
  	typeCursor, _ := database.FinancialTransactions().Aggregate(ctx, typePipeline)
  ```
- **[HIGH] Missing error check** — `cmd/lastsaas/cmd_financial.go:115` in `cmdFinancialSummary`
  - _statement-form call to known error-returning 'typeCursor.Close()'_
  ```go
  		typeCursor.Close(ctx)
  ```
- **[HIGH] Ignored error (`_`)** — `cmd/lastsaas/cmd_financial.go:122` in `cmdFinancialSummary`
  - _error explicitly discarded with `_`_
  ```go
  	activeSubs, _ := database.Tenants().CountDocuments(ctx, bson.M{"billingStatus": "active"})
  ```
- **[HIGH] Ignored error (`_`)** — `cmd/lastsaas/cmd_financial.go:135` in `cmdFinancialSummary`
  - _error explicitly discarded with `_`_
  ```go
  	rev30Cursor, _ := database.FinancialTransactions().Aggregate(ctx, rev30Pipeline)
  ```
- **[HIGH] Missing error check** — `cmd/lastsaas/cmd_financial.go:143` in `cmdFinancialSummary`
  - _statement-form call to known error-returning 'rev30Cursor.Close()'_
  ```go
  		rev30Cursor.Close(ctx)
  ```
- **[HIGH] Missing error check** — `cmd/lastsaas/cmd_financial.go:199` in `cmdFinancialTransactions`
  - _statement-form call to known error-returning 'fs.Parse()'_
  ```go
  	fs.Parse(os.Args[3:])
  ```
- **[HIGH] Missing error check** — `cmd/lastsaas/cmd_financial.go:317` in `cmdFinancialMetrics`
  - _statement-form call to known error-returning 'fs.Parse()'_
  ```go
  	fs.Parse(os.Args[3:])
  ```
- **[LOW] Proper handling** — `cmd/lastsaas/cmd_financial.go:237` in `cmdFinancialTransactions`
  ```go
  	if err != nil {
  		fmt.Fprintf(os.Stderr, "Failed to query transactions: %v\n", err)
  		os.Exit(1)
  	}
  ```
- **[LOW] Proper handling** — `cmd/lastsaas/cmd_financial.go:244` in `cmdFinancialTransactions`
  ```go
  	if err := cursor.All(ctx, &txns); err != nil {
  		fmt.Fprintf(os.Stderr, "Failed to read transactions: %v\n", err)
  		os.Exit(1)
  	}
  ```
- **[LOW] Proper handling** — `cmd/lastsaas/cmd_financial.go:330` in `cmdFinancialMetrics`
  ```go
  	if err != nil {
  		fmt.Fprintf(os.Stderr, "Failed to query daily metrics: %v\n", err)
  		os.Exit(1)
  	}
  ```
- **[LOW] Proper handling** — `cmd/lastsaas/cmd_financial.go:337` in `cmdFinancialMetrics`
  ```go
  	if err := cursor.All(ctx, &metrics); err != nil {
  		fmt.Fprintf(os.Stderr, "Failed to read metrics: %v\n", err)
  		os.Exit(1)
  	}
  ```

### `cmd/lastsaas/cmd_health.go`

- **[HIGH] Ignored error (`_`)** — `cmd/lastsaas/cmd_health.go:50` in `cmdHealth`
  - _error explicitly discarded with `_`_
  ```go
  		cursor, _ := database.SystemNodes().Find(ctx, bson.M{},
  ```
- **[HIGH] Missing error check** — `cmd/lastsaas/cmd_health.go:55` in `cmdHealth`
  - _statement-form call to known error-returning 'cursor.Close()'_
  ```go
  			cursor.Close(ctx)
  ```
- **[HIGH] Missing error check** — `cmd/lastsaas/cmd_health.go:101` in `cmdHealth`
  - _statement-form call to known error-returning 'cursor.Close()'_
  ```go
  		cursor.Close(ctx)
  ```

### `cmd/lastsaas/cmd_logs.go`

- **[HIGH] Missing error check** — `cmd/lastsaas/cmd_logs.go:27` in `cmdLogs`
  - _statement-form call to known error-returning 'fs.Parse()'_
  ```go
  	fs.Parse(os.Args[2:])
  ```
- **[HIGH] Swallowed error** — `cmd/lastsaas/cmd_logs.go:191` in `logsFollow`
  ```go
  		if err != nil {
  			continue
  		}
  ```
- **[HIGH] Missing error check** — `cmd/lastsaas/cmd_logs.go:197` in `logsFollow`
  - _statement-form call to known error-returning 'cursor.Close()'_
  ```go
  		cursor.Close(ctx)
  ```
- **[LOW] Proper handling** — `cmd/lastsaas/cmd_logs.go:138` in `queryLogs`
  ```go
  	if err != nil {
  		fmt.Fprintf(os.Stderr, "Failed to query logs: %v\n", err)
  		os.Exit(1)
  	}
  ```
- **[LOW] Proper handling** — `cmd/lastsaas/cmd_logs.go:145` in `queryLogs`
  ```go
  	if err := cursor.All(ctx, &logs); err != nil {
  		fmt.Fprintf(os.Stderr, "Failed to read logs: %v\n", err)
  		os.Exit(1)
  	}
  ```

### `cmd/lastsaas/cmd_mcp.go`

- **[HIGH] Swallowed error** — `cmd/lastsaas/cmd_mcp.go:70` in `prettyJSON`
  ```go
  	if err := json.Indent(&buf, data, "", "  "); err != nil {
  		return string(data)
  	}
  ```
- **[HIGH] Swallowed error** — `cmd/lastsaas/cmd_mcp.go:225` in `registerTenantTools`
  ```go
  			if err != nil {
  				return mcp.NewToolResultError("id is required"), nil
  			}
  ```
- **[HIGH] Swallowed error** — `cmd/lastsaas/cmd_mcp.go:282` in `registerUserTools`
  ```go
  			if err != nil {
  				return mcp.NewToolResultError("id is required"), nil
  			}
  ```
- **[HIGH] Swallowed error** — `cmd/lastsaas/cmd_mcp.go:507` in `registerConfigTools`
  ```go
  			if err != nil {
  				return mcp.NewToolResultError("name is required"), nil
  			}
  ```
- **[HIGH] Swallowed error** — `cmd/lastsaas/cmd_mcp.go:548` in `registerPlanTools`
  ```go
  			if err != nil {
  				return mcp.NewToolResultError("id is required"), nil
  			}
  ```
- **[HIGH] Swallowed error** — `cmd/lastsaas/cmd_mcp.go:712` in `registerWebhookTools`
  ```go
  			if err != nil {
  				return mcp.NewToolResultError("id is required"), nil
  			}
  ```
- **[HIGH] Swallowed error** — `cmd/lastsaas/cmd_mcp.go:815` in `registerPMTools`
  ```go
  			if err != nil {
  				return mcp.NewToolResultError("name is required"), nil
  			}
  ```
- **[LOW] Proper handling** — `cmd/lastsaas/cmd_mcp.go:42` in `get`
  ```go
  	if err != nil {
  		return nil, fmt.Errorf("failed to create request: %w", err)
  	}
  ```
- **[LOW] Proper handling** — `cmd/lastsaas/cmd_mcp.go:48` in `get`
  ```go
  	if err != nil {
  		return nil, fmt.Errorf("request failed: %w", err)
  	}
  ```
- **[LOW] Proper handling** — `cmd/lastsaas/cmd_mcp.go:54` in `get`
  ```go
  	if err != nil {
  		return nil, fmt.Errorf("failed to read response: %w", err)
  	}
  ```
- **[LOW] Proper handling** — `cmd/lastsaas/cmd_mcp.go:132` in `cmdMCP`
  ```go
  	if err := server.ServeStdio(s); err != nil {
  		fmt.Fprintf(os.Stderr, "MCP server error: %v\n", err)
  		os.Exit(1)
  	}
  ```
- **[LOW] Proper handling** — `cmd/lastsaas/cmd_mcp.go:150` in `registerAboutTools`
  ```go
  			if err != nil {
  				return mcp.NewToolResultError(err.Error()), nil
  			}
  ```
- **[LOW] Proper handling** — `cmd/lastsaas/cmd_mcp.go:170` in `registerDashboardTools`
  ```go
  			if err != nil {
  				return mcp.NewToolResultError(err.Error()), nil
  			}
  ```
- **[LOW] Proper handling** — `cmd/lastsaas/cmd_mcp.go:209` in `registerTenantTools`
  ```go
  			if err != nil {
  				return mcp.NewToolResultError(err.Error()), nil
  			}
  ```
- **[LOW] Proper handling** — `cmd/lastsaas/cmd_mcp.go:229` in `registerTenantTools`
  ```go
  			if err != nil {
  				return mcp.NewToolResultError(err.Error()), nil
  			}
  ```
- **[LOW] Proper handling** — `cmd/lastsaas/cmd_mcp.go:266` in `registerUserTools`
  ```go
  			if err != nil {
  				return mcp.NewToolResultError(err.Error()), nil
  			}
  ```
- **[LOW] Proper handling** — `cmd/lastsaas/cmd_mcp.go:286` in `registerUserTools`
  ```go
  			if err != nil {
  				return mcp.NewToolResultError(err.Error()), nil
  			}
  ```
- **[LOW] Proper handling** — `cmd/lastsaas/cmd_mcp.go:321` in `registerFinancialTools`
  ```go
  			if err != nil {
  				return mcp.NewToolResultError(err.Error()), nil
  			}
  ```
- **[LOW] Proper handling** — `cmd/lastsaas/cmd_mcp.go:342` in `registerFinancialTools`
  ```go
  			if err != nil {
  				return mcp.NewToolResultError(err.Error()), nil
  			}
  ```
- **[LOW] Proper handling** — `cmd/lastsaas/cmd_mcp.go:383` in `registerLogTools`
  ```go
  			if err != nil {
  				return mcp.NewToolResultError(err.Error()), nil
  			}
  ```
- **[LOW] Proper handling** — `cmd/lastsaas/cmd_mcp.go:398` in `registerLogTools`
  ```go
  			if err != nil {
  				return mcp.NewToolResultError(err.Error()), nil
  			}
  ```
- **[LOW] Proper handling** — `cmd/lastsaas/cmd_mcp.go:419` in `registerHealthTools`
  ```go
  			if err != nil {
  				return mcp.NewToolResultError(err.Error()), nil
  			}
  ```
- **[LOW] Proper handling** — `cmd/lastsaas/cmd_mcp.go:440` in `registerHealthTools`
  ```go
  			if err != nil {
  				return mcp.NewToolResultError(err.Error()), nil
  			}
  ```
- **[LOW] Proper handling** — `cmd/lastsaas/cmd_mcp.go:455` in `registerHealthTools`
  ```go
  			if err != nil {
  				return mcp.NewToolResultError(err.Error()), nil
  			}
  ```
- **[LOW] Proper handling** — `cmd/lastsaas/cmd_mcp.go:470` in `registerHealthTools`
  ```go
  			if err != nil {
  				return mcp.NewToolResultError(err.Error()), nil
  			}
  ```
- **[LOW] Proper handling** — `cmd/lastsaas/cmd_mcp.go:491` in `registerConfigTools`
  ```go
  			if err != nil {
  				return mcp.NewToolResultError(err.Error()), nil
  			}
  ```
- **[LOW] Proper handling** — `cmd/lastsaas/cmd_mcp.go:511` in `registerConfigTools`
  ```go
  			if err != nil {
  				return mcp.NewToolResultError(err.Error()), nil
  			}
  ```
- **[LOW] Proper handling** — `cmd/lastsaas/cmd_mcp.go:532` in `registerPlanTools`
  ```go
  			if err != nil {
  				return mcp.NewToolResultError(err.Error()), nil
  			}
  ```
- **[LOW] Proper handling** — `cmd/lastsaas/cmd_mcp.go:552` in `registerPlanTools`
  ```go
  			if err != nil {
  				return mcp.NewToolResultError(err.Error()), nil
  			}
  ```
- **[LOW] Proper handling** — `cmd/lastsaas/cmd_mcp.go:567` in `registerPlanTools`
  ```go
  			if err != nil {
  				return mcp.NewToolResultError(err.Error()), nil
  			}
  ```
- **[LOW] Proper handling** — `cmd/lastsaas/cmd_mcp.go:582` in `registerPlanTools`
  ```go
  			if err != nil {
  				return mcp.NewToolResultError(err.Error()), nil
  			}
  ```
- **[LOW] Proper handling** — `cmd/lastsaas/cmd_mcp.go:603` in `registerAnnouncementTools`
  ```go
  			if err != nil {
  				return mcp.NewToolResultError(err.Error()), nil
  			}
  ```
- **[LOW] Proper handling** — `cmd/lastsaas/cmd_mcp.go:624` in `registerPromotionTools`
  ```go
  			if err != nil {
  				return mcp.NewToolResultError(err.Error()), nil
  			}
  ```
- **[LOW] Proper handling** — `cmd/lastsaas/cmd_mcp.go:645` in `registerSecurityTools`
  ```go
  			if err != nil {
  				return mcp.NewToolResultError(err.Error()), nil
  			}
  ```
- **[LOW] Proper handling** — `cmd/lastsaas/cmd_mcp.go:660` in `registerSecurityTools`
  ```go
  			if err != nil {
  				return mcp.NewToolResultError(err.Error()), nil
  			}
  ```
- **[LOW] Proper handling** — `cmd/lastsaas/cmd_mcp.go:681` in `registerWebhookTools`
  ```go
  			if err != nil {
  				return mcp.NewToolResultError(err.Error()), nil
  			}
  ```
- **[LOW] Proper handling** — `cmd/lastsaas/cmd_mcp.go:696` in `registerWebhookTools`
  ```go
  			if err != nil {
  				return mcp.NewToolResultError(err.Error()), nil
  			}
  ```
- **[LOW] Proper handling** — `cmd/lastsaas/cmd_mcp.go:716` in `registerWebhookTools`
  ```go
  			if err != nil {
  				return mcp.NewToolResultError(err.Error()), nil
  			}
  ```
- **[LOW] Proper handling** — `cmd/lastsaas/cmd_mcp.go:741` in `registerPMTools`
  ```go
  			if err != nil {
  				return mcp.NewToolResultError(err.Error()), nil
  			}
  ```
- **[LOW] Proper handling** — `cmd/lastsaas/cmd_mcp.go:756` in `registerPMTools`
  ```go
  			if err != nil {
  				return mcp.NewToolResultError(err.Error()), nil
  			}
  ```
- **[LOW] Proper handling** — `cmd/lastsaas/cmd_mcp.go:779` in `registerPMTools`
  ```go
  			if err != nil {
  				return mcp.NewToolResultError(err.Error()), nil
  			}
  ```
- **[LOW] Proper handling** — `cmd/lastsaas/cmd_mcp.go:798` in `registerPMTools`
  ```go
  			if err != nil {
  				return mcp.NewToolResultError(err.Error()), nil
  			}
  ```
- **[LOW] Proper handling** — `cmd/lastsaas/cmd_mcp.go:823` in `registerPMTools`
  ```go
  			if err != nil {
  				return mcp.NewToolResultError(err.Error()), nil
  			}
  ```
- **[LOW] Proper handling** — `cmd/lastsaas/cmd_mcp.go:838` in `registerPMTools`
  ```go
  			if err != nil {
  				return mcp.NewToolResultError(err.Error()), nil
  			}
  ```
- **[LOW] Proper handling** — `cmd/lastsaas/cmd_mcp.go:861` in `registerResources`
  ```go
  			if err != nil {
  				return nil, fmt.Errorf("failed to fetch dashboard: %w", err)
  			}
  ```
- **[LOW] Proper handling** — `cmd/lastsaas/cmd_mcp.go:884` in `registerResources`
  ```go
  			if err != nil {
  				return nil, fmt.Errorf("failed to fetch health: %w", err)
  			}
  ```

### `cmd/lastsaas/cmd_stats.go`

- **[HIGH] Ignored error (`_`)** — `cmd/lastsaas/cmd_stats.go:22` in `cmdStats`
  - _error explicitly discarded with `_`_
  ```go
  	userCount, _ := database.Users().EstimatedDocumentCount(ctx)
  ```
- **[HIGH] Ignored error (`_`)** — `cmd/lastsaas/cmd_stats.go:23` in `cmdStats`
  - _error explicitly discarded with `_`_
  ```go
  	tenantCount, _ := database.Tenants().EstimatedDocumentCount(ctx)
  ```
- **[HIGH] Ignored error (`_`)** — `cmd/lastsaas/cmd_stats.go:24` in `cmdStats`
  - _error explicitly discarded with `_`_
  ```go
  	activeUsers, _ := database.Users().CountDocuments(ctx, bson.M{"isActive": true})
  ```
- **[HIGH] Ignored error (`_`)** — `cmd/lastsaas/cmd_stats.go:27` in `cmdStats`
  - _error explicitly discarded with `_`_
  ```go
  	activeSubs, _ := database.Tenants().CountDocuments(ctx, bson.M{
  ```
- **[HIGH] Ignored error (`_`)** — `cmd/lastsaas/cmd_stats.go:38` in `cmdStats`
  - _error explicitly discarded with `_`_
  ```go
  	logCursor, _ := database.SystemLogs().Aggregate(ctx, pipeline)
  ```
- **[HIGH] Missing error check** — `cmd/lastsaas/cmd_stats.go:47` in `cmdStats`
  - _statement-form call to known error-returning 'logCursor.Close()'_
  ```go
  		logCursor.Close(ctx)
  ```
- **[HIGH] Ignored error (`_`)** — `cmd/lastsaas/cmd_stats.go:63` in `cmdStats`
  - _error explicitly discarded with `_`_
  ```go
  	revCursor, _ := database.FinancialTransactions().Aggregate(ctx, revPipeline)
  ```
- **[HIGH] Missing error check** — `cmd/lastsaas/cmd_stats.go:71` in `cmdStats`
  - _statement-form call to known error-returning 'revCursor.Close()'_
  ```go
  		revCursor.Close(ctx)
  ```

### `cmd/lastsaas/cmd_tenants.go`

- **[HIGH] Missing error check** — `cmd/lastsaas/cmd_tenants.go:46` in `cmdTenantsList`
  - _statement-form call to known error-returning 'fs.Parse()'_
  ```go
  	fs.Parse(os.Args[3:])
  ```
- **[HIGH] Missing error check** — `cmd/lastsaas/cmd_tenants.go:157` in `cmdTenantsGet`
  - _statement-form call to known error-returning 'database.Tenants().FindOne(ctx, bson.M{"_id": oid}).Decode()'_
  ```go
  		database.Tenants().FindOne(ctx, bson.M{"_id": oid}).Decode(&tenant)
  ```
- **[HIGH] Swallowed error** — `cmd/lastsaas/cmd_tenants.go:285` in `resolveUserNames`
  ```go
  	if err != nil {
  		return result
  	}
  ```
- **[HIGH] Swallowed error** — `cmd/lastsaas/cmd_tenants.go:312` in `resolvePlanNames`
  ```go
  	if err != nil {
  		return names
  	}
  ```
- **[HIGH] Swallowed error** — `cmd/lastsaas/cmd_tenants.go:349` in `countMembersPerTenant`
  ```go
  	if err != nil {
  		return counts
  	}
  ```
- **[LOW] Proper handling** — `cmd/lastsaas/cmd_tenants.go:59` in `cmdTenantsList`
  ```go
  	if err != nil {
  		fmt.Fprintf(os.Stderr, "Failed to query tenants: %v\n", err)
  		os.Exit(1)
  	}
  ```
- **[LOW] Proper handling** — `cmd/lastsaas/cmd_tenants.go:66` in `cmdTenantsList`
  ```go
  	if err := cursor.All(ctx, &tenants); err != nil {
  		fmt.Fprintf(os.Stderr, "Failed to read tenants: %v\n", err)
  		os.Exit(1)
  	}
  ```
- **[LOW] Proper handling** — `cmd/lastsaas/cmd_tenants.go:169` in `cmdTenantsGet`
  ```go
  	if err != nil {
  		fmt.Fprintf(os.Stderr, "Failed to query memberships: %v\n", err)
  		os.Exit(1)
  	}
  ```

### `cmd/lastsaas/cmd_users.go`

- **[HIGH] Missing error check** — `cmd/lastsaas/cmd_users.go:53` in `cmdUsersList`
  - _statement-form call to known error-returning 'fs.Parse()'_
  ```go
  	fs.Parse(os.Args[3:])
  ```
- **[HIGH] Missing error check** — `cmd/lastsaas/cmd_users.go:152` in `cmdUsersGet`
  - _statement-form call to known error-returning 'fs.Parse()'_
  ```go
  	fs.Parse(os.Args[3:])
  ```
- **[HIGH] Missing error check** — `cmd/lastsaas/cmd_users.go:263` in `cmdUsersSetActive`
  - _statement-form call to known error-returning 'fs.Parse()'_
  ```go
  	fs.Parse(os.Args[3:])
  ```
- **[HIGH] Missing error check** — `cmd/lastsaas/cmd_users.go:305` in `cmdUsersSetActive`
  - _statement-form call to known error-returning 'database.RefreshTokens().DeleteMany()'_
  ```go
  		database.RefreshTokens().DeleteMany(ctx, bson.M{"userId": user.ID})
  ```
- **[HIGH] Missing error check** — `cmd/lastsaas/cmd_users.go:313` in `cmdUsersRevokeSessions`
  - _statement-form call to known error-returning 'fs.Parse()'_
  ```go
  	fs.Parse(os.Args[3:])
  ```
- **[HIGH] Swallowed error** — `cmd/lastsaas/cmd_users.go:352` in `lookupUserWithMemberships`
  ```go
  	if err != nil {
  		return user, nil
  	}
  ```
- **[HIGH] Swallowed error** — `cmd/lastsaas/cmd_users.go:369` in `resolveTenantNames`
  ```go
  	if err != nil {
  		return names
  	}
  ```
- **[LOW] Proper handling** — `cmd/lastsaas/cmd_users.go:71` in `cmdUsersList`
  ```go
  	if err != nil {
  		fmt.Fprintf(os.Stderr, "Failed to query users: %v\n", err)
  		os.Exit(1)
  	}
  ```
- **[LOW] Proper handling** — `cmd/lastsaas/cmd_users.go:78` in `cmdUsersList`
  ```go
  	if err := cursor.All(ctx, &users); err != nil {
  		fmt.Fprintf(os.Stderr, "Failed to read users: %v\n", err)
  		os.Exit(1)
  	}
  ```
- **[LOW] Proper handling** — `cmd/lastsaas/cmd_users.go:296` in `cmdUsersSetActive`
  ```go
  	if err != nil {
  		fmt.Fprintf(os.Stderr, "Failed to update user: %v\n", err)
  		os.Exit(1)
  	}
  ```
- **[LOW] Proper handling** — `cmd/lastsaas/cmd_users.go:334` in `cmdUsersRevokeSessions`
  ```go
  	if err != nil {
  		fmt.Fprintf(os.Stderr, "Failed to revoke sessions: %v\n", err)
  		os.Exit(1)
  	}
  ```

### `cmd/lastsaas/main.go`

- **[HIGH] Missing error check** — `cmd/lastsaas/main.go:29` in `main`
  - _statement-form call to known error-returning 'version.Load()'_
  ```go
  	version.Load()
  ```
- **[HIGH] Missing error check** — `cmd/lastsaas/main.go:169` in `connectDB`
  - _statement-form call to known error-returning 'database.Close()'_
  ```go
  		database.Close(ctx)
  ```
- **[HIGH] Missing error check** — `cmd/lastsaas/main.go:377` in `cmdSetup`
  - _statement-form call to known error-returning 'database.Messages().InsertOne()'_
  ```go
  	database.Messages().InsertOne(ctx, welcomeMsg)
  ```
- **[HIGH] Missing error check** — `cmd/lastsaas/main.go:394` in `cmdChangePassword`
  - _statement-form call to known error-returning 'fs.Parse()'_
  ```go
  	fs.Parse(os.Args[2:])
  ```
- **[HIGH] Missing error check** — `cmd/lastsaas/main.go:453` in `cmdChangePassword`
  - _statement-form call to known error-returning 'database.RefreshTokens().DeleteMany()'_
  ```go
  	database.RefreshTokens().DeleteMany(ctx, bson.M{"userId": user.ID})
  ```
- **[HIGH] Missing error check** — `cmd/lastsaas/main.go:465` in `cmdSendMessage`
  - _statement-form call to known error-returning 'fs.Parse()'_
  ```go
  	fs.Parse(os.Args[2:])
  ```
- **[HIGH] Missing error check** — `cmd/lastsaas/main.go:730` in `cmdTransferRootOwner`
  - _statement-form call to known error-returning 'fs.Parse()'_
  ```go
  	fs.Parse(os.Args[2:])
  ```
- **[HIGH] Ignored error (`_`)** — `cmd/lastsaas/main.go:802` in `cmdTransferRootOwner`
  - _error explicitly discarded with `_`_
  ```go
  	answer, _ := reader.ReadString('\n')
  ```
- **[HIGH] Missing error check** — `cmd/lastsaas/main.go:844` in `cmdTransferRootOwner`
  - _statement-form call to known error-returning 'database.SystemLogs().InsertOne()'_
  ```go
  	database.SystemLogs().InsertOne(ctx, logEntry)
  ```
- **[HIGH] Swallowed error** — `cmd/lastsaas/main.go:866` in `cmdVersion`
  ```go
  	if err != nil || !sys.Initialized {
  		fmt.Println("DB version:  (not initialized)")
  		return
  	}
  ```
- **[HIGH] Swallowed error** — `cmd/lastsaas/main.go:884` in `cmdStatus`
  ```go
  	if err != nil {
  		fmt.Printf("Config:      ERROR - %v\n", err)
  		return
  	}
  ```
- **[HIGH] Swallowed error** — `cmd/lastsaas/main.go:891` in `cmdStatus`
  ```go
  	if err != nil {
  		fmt.Printf("MongoDB:     ERROR - %v\n", err)
  		return
  	}
  ```
- **[HIGH] Missing error check** — `cmd/lastsaas/main.go:898` in `cmdStatus`
  - _statement-form call to known error-returning 'database.Close()'_
  ```go
  		database.Close(ctx)
  ```
- **[HIGH] Swallowed error** — `cmd/lastsaas/main.go:907` in `cmdStatus`
  ```go
  	if err != nil || !sys.Initialized {
  		fmt.Println("Initialized: No")
  		fmt.Println()
  		fmt.Println("Run 'lastsaas setup' to initialize the system.")
  		return
  	}
  ```
- **[HIGH] Ignored error (`_`)** — `cmd/lastsaas/main.go:918` in `cmdStatus`
  - _error explicitly discarded with `_`_
  ```go
  	userCount, _ := database.Users().CountDocuments(ctx, bson.M{})
  ```
- **[HIGH] Ignored error (`_`)** — `cmd/lastsaas/main.go:919` in `cmdStatus`
  - _error explicitly discarded with `_`_
  ```go
  	tenantCount, _ := database.Tenants().CountDocuments(ctx, bson.M{})
  ```
- **[HIGH] Ignored error (`_`)** — `cmd/lastsaas/main.go:928` in `prompt`
  - _error explicitly discarded with `_`_
  ```go
  	text, _ := reader.ReadString('\n')
  ```
- **[LOW] Proper handling** — `cmd/lastsaas/main.go:153` in `connectDB`
  ```go
  	if err != nil {
  		fmt.Fprintf(os.Stderr, "Error loading config: %v\n\n", err)
  		printConfigHelp(env)
  		os.Exit(1)
  	}
  ```
- **[LOW] Proper handling** — `cmd/lastsaas/main.go:160` in `connectDB`
  ```go
  	if err != nil {
  		fmt.Fprintf(os.Stderr, "Error connecting to MongoDB: %v\n\n", err)
  		printMongoHelp(env)
  		os.Exit(1)
  	}
  ```
- **[LOW] Proper handling** — `cmd/lastsaas/main.go:273` in `cmdSetup`
  ```go
  	if err := passwordService.ValidatePasswordStrength(password); err != nil {
  		fmt.Fprintf(os.Stderr, "Password too weak: %v\n", err)
  		fmt.Fprintln(os.Stderr, "Requirements: 10+ characters, uppercase, lowercase, number, special character")
  		os.Exit(1)
  	}
  ```
- **[LOW] Proper handling** — `cmd/lastsaas/main.go:280` in `cmdSetup`
  ```go
  	if err != nil {
  		fmt.Fprintf(os.Stderr, "Failed to hash password: %v\n", err)
  		os.Exit(1)
  	}
  ```
- **[LOW] Proper handling** — `cmd/lastsaas/main.go:297` in `cmdSetup`
  ```go
  	if err := validation.Validate(&tenant); err != nil {
  		fmt.Fprintf(os.Stderr, "Tenant validation failed: %v\n", err)
  		os.Exit(1)
  	}
  ```
- **[LOW] Proper handling** — `cmd/lastsaas/main.go:301` in `cmdSetup`
  ```go
  	if _, err := database.Tenants().InsertOne(ctx, tenant); err != nil {
  		fmt.Fprintf(os.Stderr, "Failed to create root tenant: %v\n", err)
  		os.Exit(1)
  	}
  ```
- **[LOW] Proper handling** — `cmd/lastsaas/main.go:318` in `cmdSetup`
  ```go
  	if err := validation.Validate(&user); err != nil {
  		database.Tenants().DeleteOne(ctx, bson.M{"_id": tenant.ID})
  		fmt.Fprintf(os.Stderr, "User validation failed: %v\n", err)
  		os.Exit(1)
  	}
  ```
- **[LOW] Proper handling** — `cmd/lastsaas/main.go:323` in `cmdSetup`
  ```go
  	if _, err := database.Users().InsertOne(ctx, user); err != nil {
  		database.Tenants().DeleteOne(ctx, bson.M{"_id": tenant.ID})
  		fmt.Fprintf(os.Stderr, "Failed to create user: %v\n", err)
  		os.Exit(1)
  	}
  ```
- **[LOW] Proper handling** — `cmd/lastsaas/main.go:338` in `cmdSetup`
  ```go
  	if err := validation.Validate(&membership); err != nil {
  		database.Users().DeleteOne(ctx, bson.M{"_id": user.ID})
  		database.Tenants().DeleteOne(ctx, bson.M{"_id": tenant.ID})
  		fmt.Fprintf(os.Stderr, "Membership validation failed: %v\n", err)
  		os.Exit(1)
  	}
  ```
- **[LOW] Proper handling** — `cmd/lastsaas/main.go:344` in `cmdSetup`
  ```go
  	if _, err := database.TenantMemberships().InsertOne(ctx, membership); err != nil {
  		database.Users().DeleteOne(ctx, bson.M{"_id": user.ID})
  		database.Tenants().DeleteOne(ctx, bson.M{"_id": tenant.ID})
  		fmt.Fprintf(os.Stderr, "Failed to create membership: %v\n", err)
  		os.Exit(1)
  	}
  ```
- **[LOW] Proper handling** — `cmd/lastsaas/main.go:359` in `cmdSetup`
  ```go
  	if _, err := database.SystemConfig().InsertOne(ctx, sysConfig); err != nil {
  		database.TenantMemberships().DeleteOne(ctx, bson.M{"_id": membership.ID})
  		database.Users().DeleteOne(ctx, bson.M{"_id": user.ID})
  		database.Tenants().DeleteOne(ctx, bson.M{"_id": tenant.ID})
  		fmt.Fprintf(os.Stderr, "Failed to mark system as initialized: %v\n", err)
  		os.Exit(1)
  ... (1 more lines)
  ```
- **[LOW] Proper handling** — `cmd/lastsaas/main.go:411` in `cmdChangePassword`
  ```go
  	if err != nil {
  		fmt.Fprintf(os.Stderr, "User not found: %s\n", email)
  		os.Exit(1)
  	}
  ```
- **[LOW] Proper handling** — `cmd/lastsaas/main.go:428` in `cmdChangePassword`
  ```go
  	if err := passwordService.ValidatePasswordStrength(password); err != nil {
  		fmt.Fprintf(os.Stderr, "Password too weak: %v\n", err)
  		fmt.Fprintln(os.Stderr, "Requirements: 10+ characters, uppercase, lowercase, number, special character")
  		os.Exit(1)
  	}
  ```
- **[LOW] Proper handling** — `cmd/lastsaas/main.go:435` in `cmdChangePassword`
  ```go
  	if err != nil {
  		fmt.Fprintf(os.Stderr, "Failed to hash password: %v\n", err)
  		os.Exit(1)
  	}
  ```
- **[LOW] Proper handling** — `cmd/lastsaas/main.go:447` in `cmdChangePassword`
  ```go
  	if err != nil {
  		fmt.Fprintf(os.Stderr, "Failed to update password: %v\n", err)
  		os.Exit(1)
  	}
  ```
- **[LOW] Proper handling** — `cmd/lastsaas/main.go:504` in `cmdSendMessage`
  ```go
  	if err != nil {
  		fmt.Fprintf(os.Stderr, "User not found: %s\n", email)
  		os.Exit(1)
  	}
  ```
- **[LOW] Proper handling** — `cmd/lastsaas/main.go:519` in `cmdSendMessage`
  ```go
  	if _, err := database.Messages().InsertOne(ctx, msg); err != nil {
  		fmt.Fprintf(os.Stderr, "Failed to send message: %v\n", err)
  		os.Exit(1)
  	}
  ```
- **[LOW] Proper handling** — `cmd/lastsaas/main.go:576` in `cmdConfigList`
  ```go
  	if err != nil {
  		fmt.Fprintf(os.Stderr, "Failed to query config vars: %v\n", err)
  		os.Exit(1)
  	}
  ```
- **[LOW] Proper handling** — `cmd/lastsaas/main.go:583` in `cmdConfigList`
  ```go
  	if err := cursor.All(ctx, &vars); err != nil {
  		fmt.Fprintf(os.Stderr, "Failed to read config vars: %v\n", err)
  		os.Exit(1)
  	}
  ```
- **[LOW] Proper handling** — `cmd/lastsaas/main.go:624` in `cmdConfigGet`
  ```go
  	if err != nil {
  		fmt.Fprintf(os.Stderr, "Config variable not found: %s\n", name)
  		os.Exit(1)
  	}
  ```
- **[LOW] Proper handling** — `cmd/lastsaas/main.go:654` in `cmdConfigSet`
  ```go
  	if err != nil {
  		fmt.Fprintf(os.Stderr, "Config variable not found: %s\n", name)
  		os.Exit(1)
  	}
  ```
- **[LOW] Proper handling** — `cmd/lastsaas/main.go:659` in `cmdConfigSet`
  ```go
  	if err := configstore.ValidateValue(v.Type, value, v.Options); err != nil {
  		fmt.Fprintf(os.Stderr, "Invalid value: %v\n", err)
  		os.Exit(1)
  	}
  ```
- **[LOW] Proper handling** — `cmd/lastsaas/main.go:668` in `cmdConfigSet`
  ```go
  	if err != nil {
  		fmt.Fprintf(os.Stderr, "Failed to update config variable: %v\n", err)
  		os.Exit(1)
  	}
  ```
- **[LOW] Proper handling** — `cmd/lastsaas/main.go:702` in `cmdConfigReset`
  ```go
  	if err != nil {
  		fmt.Fprintf(os.Stderr, "Config variable not found in database: %s\n", name)
  		os.Exit(1)
  	}
  ```
- **[LOW] Proper handling** — `cmd/lastsaas/main.go:716` in `cmdConfigReset`
  ```go
  	if err != nil {
  		fmt.Fprintf(os.Stderr, "Failed to reset config variable: %v\n", err)
  		os.Exit(1)
  	}
  ```
- **[LOW] Proper handling** — `cmd/lastsaas/main.go:817` in `cmdTransferRootOwner`
  ```go
  	if err != nil {
  		fmt.Fprintf(os.Stderr, "Failed to demote current owner: %v\n", err)
  		os.Exit(1)
  	}
  ```
- **[LOW] Proper handling** — `cmd/lastsaas/main.go:827` in `cmdTransferRootOwner`
  ```go
  	if err != nil {
  		// Try to rollback
  		database.TenantMemberships().UpdateOne(ctx,
  			bson.M{"_id": currentOwnerMembership.ID},
  			bson.M{"$set": bson.M{"role": "owner", "updatedAt": now}},
  		)
  ... (3 more lines)
  ```
- **[LOW] Proper handling** — `cmd/lastsaas/main.go:936` in `promptPassword`
  ```go
  	if err != nil {
  		fmt.Fprintf(os.Stderr, "Error reading password: %v\n", err)
  		os.Exit(1)
  	}
  ```

### `cmd/lastsaas/output.go`

- **[HIGH] Missing error check** — `cmd/lastsaas/output.go:84` in `printJSON`
  - _statement-form call to known error-returning 'enc.Encode()'_
  ```go
  	enc.Encode(v)
  ```

### `cmd/lastsaas/process.go`

- **[HIGH] Missing error check** — `cmd/lastsaas/process.go:29` in `cmdStart`
  - _statement-form call to known error-returning 'fs.Parse()'_
  ```go
  	fs.Parse(os.Args[2:])
  ```
- **[HIGH] Missing error check** — `cmd/lastsaas/process.go:49` in `cmdStop`
  - _statement-form call to known error-returning 'fs.Parse()'_
  ```go
  	fs.Parse(os.Args[2:])
  ```
- **[HIGH] Missing error check** — `cmd/lastsaas/process.go:70` in `cmdRestart`
  - _statement-form call to known error-returning 'fs.Parse()'_
  ```go
  	fs.Parse(os.Args[2:])
  ```
- **[HIGH] Missing error check** — `cmd/lastsaas/process.go:139` in `startBackend`
  - _statement-form call to known error-returning 'os.WriteFile()'_
  ```go
  	os.WriteFile(pidFile, []byte(strconv.Itoa(pid)), 0644)
  ```
- **[HIGH] Missing error check** — `cmd/lastsaas/process.go:141` in `startBackend`
  - _statement-form call to known error-returning 'lf.Close()'_
  ```go
  	lf.Close()
  ```
- **[HIGH] Missing error check** — `cmd/lastsaas/process.go:147` in `startBackend`
  - _statement-form call to known error-returning 'os.Remove()'_
  ```go
  		os.Remove(pidFile)
  ```
- **[HIGH] Missing error check** — `cmd/lastsaas/process.go:192` in `startFrontend`
  - _statement-form call to known error-returning 'os.WriteFile()'_
  ```go
  	os.WriteFile(pidFile, []byte(strconv.Itoa(pid)), 0644)
  ```
- **[HIGH] Missing error check** — `cmd/lastsaas/process.go:194` in `startFrontend`
  - _statement-form call to known error-returning 'lf.Close()'_
  ```go
  	lf.Close()
  ```
- **[HIGH] Missing error check** — `cmd/lastsaas/process.go:200` in `startFrontend`
  - _statement-form call to known error-returning 'os.Remove()'_
  ```go
  		os.Remove(pidFile)
  ```
- **[HIGH] Missing error check** — `cmd/lastsaas/process.go:214` in `stopService`
  - _statement-form call to known error-returning 'os.Remove()'_
  ```go
  		os.Remove(pidFile)
  ```
- **[HIGH] Missing error check** — `cmd/lastsaas/process.go:237` in `stopService`
  - _statement-form call to known error-returning 'os.Remove()'_
  ```go
  	os.Remove(pidFile)
  ```
- **[HIGH] Missing error check** — `cmd/lastsaas/process.go:293` in `ensurePIDDir`
  - _statement-form call to known error-returning 'os.MkdirAll()'_
  ```go
  	os.MkdirAll(pd, 0755)
  ```
- **[HIGH] Swallowed error** — `cmd/lastsaas/process.go:304` in `readPID`
  ```go
  	if err != nil {
  		return 0
  	}
  ```
- **[HIGH] Swallowed error** — `cmd/lastsaas/process.go:308` in `readPID`
  ```go
  	if err != nil {
  		return 0
  	}
  ```
- **[LOW] Proper handling** — `cmd/lastsaas/process.go:112` in `startBackend`
  ```go
  	if out, err := buildCmd.CombinedOutput(); err != nil {
  		fmt.Printf("FAILED\n%s\n", string(out))
  		os.Exit(1)
  	}
  ```
- **[LOW] Proper handling** — `cmd/lastsaas/process.go:120` in `startBackend`
  ```go
  	if err != nil {
  		fmt.Fprintf(os.Stderr, "Failed to create log file: %v\n", err)
  		os.Exit(1)
  	}
  ```
- **[LOW] Proper handling** — `cmd/lastsaas/process.go:132` in `startBackend`
  ```go
  	if err := cmd.Start(); err != nil {
  		lf.Close()
  		fmt.Fprintf(os.Stderr, "Failed to start backend: %v\n", err)
  		os.Exit(1)
  	}
  ```
- **[LOW] Proper handling** — `cmd/lastsaas/process.go:168` in `startFrontend`
  ```go
  	if _, err := os.Stat(viteBin); err != nil {
  		fmt.Fprintf(os.Stderr, "Vite not found. Run 'npm install' in the frontend directory first.\n")
  		os.Exit(1)
  	}
  ```
- **[LOW] Proper handling** — `cmd/lastsaas/process.go:174` in `startFrontend`
  ```go
  	if err != nil {
  		fmt.Fprintf(os.Stderr, "Failed to create log file: %v\n", err)
  		os.Exit(1)
  	}
  ```
- **[LOW] Proper handling** — `cmd/lastsaas/process.go:185` in `startFrontend`
  ```go
  	if err := cmd.Start(); err != nil {
  		lf.Close()
  		fmt.Fprintf(os.Stderr, "Failed to start frontend: %v\n", err)
  		os.Exit(1)
  	}
  ```
- **[LOW] Proper handling** — `cmd/lastsaas/process.go:258` in `findProjectRoot`
  ```go
  	if err != nil {
  		return "", err
  	}
  ```
- **[LOW] Proper handling** — `cmd/lastsaas/process.go:284` in `mustFindProjectRoot`
  ```go
  	if err != nil {
  		fmt.Fprintf(os.Stderr, "%v\n", err)
  		os.Exit(1)
  	}
  ```

### `cmd/server/main.go`

- **[HIGH] Missing error check** — `cmd/server/main.go:79` in `ServeHTTP`
  - _statement-form call to known error-returning 'w.Write()'_
  ```go
  		w.Write([]byte(html))
  ```
- **[HIGH] Missing error check** — `cmd/server/main.go:118` in `main`
  - _statement-form call to known error-returning 'version.Load()'_
  ```go
  	version.Load()
  ```
- **[HIGH] Swallowed error** — `cmd/server/main.go:383` in `main`
  ```go
  		if err := database.Client.Ping(ctx, nil); err != nil {
  			w.WriteHeader(http.StatusServiceUnavailable)
  			w.Write([]byte(`{"status":"unhealthy","error":"database unreachable"}`))
  			return
  		}
  ```
- **[HIGH] Missing error check** — `cmd/server/main.go:389` in `main`
  - _statement-form call to known error-returning 'w.Write()'_
  ```go
  		w.Write([]byte(`{"status":"ok"}`))
  ```
- **[HIGH] Missing error check** — `cmd/server/main.go:400` in `main`
  - _statement-form call to known error-returning 'w.Write()'_
  ```go
  		w.Write([]byte(fmt.Sprintf(`{"version":%q}`, version.Current)))
  ```
- **[HIGH] Ignored error (`_`)** — `cmd/server/main.go:614` in `main`
  - _error explicitly discarded with `_`_
  ```go
  			user, _ := middleware.GetUserFromContext(r.Context())
  ```
- **[HIGH] Ignored error (`_`)** — `cmd/server/main.go:625` in `main`
  - _error explicitly discarded with `_`_
  ```go
  			user, _ := middleware.GetUserFromContext(r.Context())
  ```
- **[MEDIUM] Logged only (no return)** — `cmd/server/main.go:67` in `ServeHTTP`
  ```go
  		if readErr != nil {
  			http.Error(w, "Internal Server Error", http.StatusInternalServerError)
  			return
  		}
  ```
- **[MEDIUM] Logged only (no return)** — `cmd/server/main.go:82` in `ServeHTTP`
  ```go
  	if err != nil {
  		http.Error(w, "Internal Server Error", http.StatusInternalServerError)
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `cmd/server/main.go:111` in `main`
  ```go
  		if err := database.Close(ctx); err != nil {
  			slog.Error("Failed to close database connection", "error", err)
  		}
  ```
- **[MEDIUM] Logged only (no return)** — `cmd/server/main.go:157` in `main`
  ```go
  		if err := ddClient.Startup(context.Background(), version.Current); err != nil {
  			slog.Warn("DataDog startup verification failed (integration will retry in background)", "error", err)
  		}
  ```
- **[LOW] Proper handling** — `cmd/server/main.go:96` in `main`
  ```go
  	if err != nil {
  		slog.Error("Failed to load config", "error", err)
  		os.Exit(1)
  	}
  ```
- **[LOW] Proper handling** — `cmd/server/main.go:104` in `main`
  ```go
  	if err != nil {
  		slog.Error("Failed to connect to MongoDB", "error", err)
  		os.Exit(1)
  	}
  ```
- **[LOW] Proper handling** — `cmd/server/main.go:122` in `main`
  ```go
  	if err := configstore.Seed(context.Background(), database); err != nil {
  		slog.Error("Failed to seed config variables", "error", err)
  		os.Exit(1)
  	}
  ```
- **[LOW] Proper handling** — `cmd/server/main.go:127` in `main`
  ```go
  	if err := cfgStore.Load(context.Background()); err != nil {
  		slog.Error("Failed to load config store", "error", err)
  		os.Exit(1)
  	}
  ```
- **[LOW] Proper handling** — `cmd/server/main.go:137` in `main`
  ```go
  	if err := planstore.Seed(context.Background(), database); err != nil {
  		slog.Error("Failed to seed plans", "error", err)
  		os.Exit(1)
  	}
  ```
- **[LOW] Proper handling** — `cmd/server/main.go:242` in `main`
  ```go
  	if err != nil {
  		slog.Error("Invalid webhook encryption key", "error", err)
  		os.Exit(1)
  	}
  ```
- **[LOW] Proper handling** — `cmd/server/main.go:822` in `main`
  ```go
  		if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
  			slog.Error("Server failed", "error", err)
  			os.Exit(1)
  		}
  ```
- **[LOW] Proper handling** — `cmd/server/main.go:839` in `main`
  ```go
  	if err := srv.Shutdown(shutdownCtx); err != nil {
  		slog.Error("Server forced shutdown", "error", err)
  		os.Exit(1)
  	}
  ```

### `internal/api/handlers/admin.go`

- **[HIGH] Ignored error (`_`)** — `internal/api/handlers/admin.go:51` in `isRootTenantOwner`
  - _error explicitly discarded with `_`_
  ```go
  	count, _ := h.db.TenantMemberships().CountDocuments(ctx, bson.M{
  ```
- **[HIGH] Ignored error (`_`)** — `internal/api/handlers/admin.go:115` in `ListTenants`
  - _error explicitly discarded with `_`_
  ```go
  	page, _ := strconv.Atoi(q.Get("page"))
  ```
- **[HIGH] Ignored error (`_`)** — `internal/api/handlers/admin.go:119` in `ListTenants`
  - _error explicitly discarded with `_`_
  ```go
  	limit, _ := strconv.Atoi(q.Get("limit"))
  ```
- **[HIGH] Ignored error (`_`)** — `internal/api/handlers/admin.go:222` in `ListTenants`
  - _error explicitly discarded with `_`_
  ```go
  	planCursor, _ := h.db.Plans().Find(ctx, bson.M{}, options.Find().SetLimit(500))
  ```
- **[HIGH] Ignored error (`_`)** — `internal/api/handlers/admin.go:342` in `ExportTenantsCSV`
  - _error explicitly discarded with `_`_
  ```go
  	planCursor, _ := h.db.Plans().Find(ctx, bson.M{}, options.Find().SetLimit(500))
  ```
- **[HIGH] Missing error check** — `internal/api/handlers/admin.go:348` in `ExportTenantsCSV`
  - _statement-form call to known error-returning 'planCursor.Close()'_
  ```go
  		planCursor.Close(ctx)
  ```
- **[HIGH] Missing error check** — `internal/api/handlers/admin.go:364` in `ExportTenantsCSV`
  - _statement-form call to known error-returning 'writer.Write()'_
  ```go
  	writer.Write([]string{"ID", "Name", "Slug", "IsRoot", "IsActive", "MemberCount", "PlanName", "BillingStatus", "Credits", "CreatedAt"})
  ```
- **[HIGH] Missing error check** — `internal/api/handlers/admin.go:387` in `ExportTenantsCSV`
  - _statement-form call to known error-returning 'writer.Flush()'_
  ```go
  	writer.Flush()
  ```
- **[HIGH] Ignored error (`_`)** — `internal/api/handlers/admin.go:507` in `ListUsers`
  - _error explicitly discarded with `_`_
  ```go
  	page, _ := strconv.Atoi(q.Get("page"))
  ```
- **[HIGH] Ignored error (`_`)** — `internal/api/handlers/admin.go:511` in `ListUsers`
  - _error explicitly discarded with `_`_
  ```go
  	limit, _ := strconv.Atoi(q.Get("limit"))
  ```
- **[HIGH] Missing error check** — `internal/api/handlers/admin.go:701` in `ExportUsersCSV`
  - _statement-form call to known error-returning 'writer.Write()'_
  ```go
  	writer.Write([]string{"ID", "Email", "DisplayName", "EmailVerified", "IsActive", "TenantCount", "CreatedAt", "LastLoginAt"})
  ```
- **[HIGH] Missing error check** — `internal/api/handlers/admin.go:719` in `ExportUsersCSV`
  - _statement-form call to known error-returning 'writer.Flush()'_
  ```go
  	writer.Flush()
  ```
- **[HIGH] Ignored error (`_`)** — `internal/api/handlers/admin.go:731` in `UpdateUserStatus`
  - _error explicitly discarded with `_`_
  ```go
  	actingMembership, _ := middleware.GetMembershipFromContext(r.Context())
  ```
- **[HIGH] Ignored error (`_`)** — `internal/api/handlers/admin.go:754` in `UpdateUserStatus`
  - _error explicitly discarded with `_`_
  ```go
  	actingUser, _ := middleware.GetUserFromContext(r.Context())
  ```
- **[HIGH] Ignored error (`_`)** — `internal/api/handlers/admin.go:784` in `GetDashboard`
  - _error explicitly discarded with `_`_
  ```go
  	userCount, _ := h.db.Users().CountDocuments(ctx, bson.M{})
  ```
- **[HIGH] Ignored error (`_`)** — `internal/api/handlers/admin.go:785` in `GetDashboard`
  - _error explicitly discarded with `_`_
  ```go
  	tenantCount, _ := h.db.Tenants().CountDocuments(ctx, bson.M{})
  ```
- **[HIGH] Ignored error (`_`)** — `internal/api/handlers/admin.go:794` in `GetDashboard`
  - _error explicitly discarded with `_`_
  ```go
  			cpuWarn, _ := strconv.ParseFloat(h.getConfig("health.cpu.warning_threshold"), 64)
  ```
- **[HIGH] Ignored error (`_`)** — `internal/api/handlers/admin.go:795` in `GetDashboard`
  - _error explicitly discarded with `_`_
  ```go
  			cpuCrit, _ := strconv.ParseFloat(h.getConfig("health.cpu.critical_threshold"), 64)
  ```
- **[HIGH] Ignored error (`_`)** — `internal/api/handlers/admin.go:796` in `GetDashboard`
  - _error explicitly discarded with `_`_
  ```go
  			memWarn, _ := strconv.ParseFloat(h.getConfig("health.memory.warning_threshold"), 64)
  ```
- **[HIGH] Ignored error (`_`)** — `internal/api/handlers/admin.go:797` in `GetDashboard`
  - _error explicitly discarded with `_`_
  ```go
  			memCrit, _ := strconv.ParseFloat(h.getConfig("health.memory.critical_threshold"), 64)
  ```
- **[HIGH] Ignored error (`_`)** — `internal/api/handlers/admin.go:798` in `GetDashboard`
  - _error explicitly discarded with `_`_
  ```go
  			diskWarn, _ := strconv.ParseFloat(h.getConfig("health.disk.warning_threshold"), 64)
  ```
- **[HIGH] Ignored error (`_`)** — `internal/api/handlers/admin.go:799` in `GetDashboard`
  - _error explicitly discarded with `_`_
  ```go
  			diskCrit, _ := strconv.ParseFloat(h.getConfig("health.disk.critical_threshold"), 64)
  ```
- **[HIGH] Ignored error (`_`)** — `internal/api/handlers/admin.go:900` in `GetUser`
  - _error explicitly discarded with `_`_
  ```go
  	planCursor, _ := h.db.Plans().Find(r.Context(), bson.M{}, options.Find().SetLimit(500))
  ```
- **[HIGH] Ignored error (`_`)** — `internal/api/handlers/admin.go:995` in `UpdateUser`
  - _error explicitly discarded with `_`_
  ```go
  	actingMembership, _ := middleware.GetMembershipFromContext(r.Context())
  ```
- **[HIGH] Ignored error (`_`)** — `internal/api/handlers/admin.go:1016` in `UpdateUser`
  - _error explicitly discarded with `_`_
  ```go
  	actingUser, _ := middleware.GetUserFromContext(r.Context())
  ```
- **[HIGH] Ignored error (`_`)** — `internal/api/handlers/admin.go:1026` in `UpdateUser`
  - _error explicitly discarded with `_`_
  ```go
  			count, _ := h.db.Users().CountDocuments(r.Context(), bson.M{"email": newEmail, "_id": bson.M{"$ne": userID}})
  ```
- **[HIGH] Missing error check** — `internal/api/handlers/admin.go:1045` in `UpdateUser`
  - _statement-form call to known error-returning 'h.db.Users().UpdateOne()'_
  ```go
  	h.db.Users().UpdateOne(r.Context(), bson.M{"_id": userID}, bson.M{"$set": updates})
  ```
- **[HIGH] Ignored error (`_`)** — `internal/api/handlers/admin.go:1063` in `UpdateUserRole`
  - _error explicitly discarded with `_`_
  ```go
  	actingMembership, _ := middleware.GetMembershipFromContext(r.Context())
  ```
- **[HIGH] Ignored error (`_`)** — `internal/api/handlers/admin.go:1119` in `UpdateUserRole`
  - _error explicitly discarded with `_`_
  ```go
  	actingUser, _ := middleware.GetUserFromContext(ctx)
  ```
- **[HIGH] Ignored error (`_`)** — `internal/api/handlers/admin.go:1142` in `PreflightDeleteUser`
  - _error explicitly discarded with `_`_
  ```go
  	actingUser, _ := middleware.GetUserFromContext(ctx)
  ```
- **[HIGH] Missing error check** — `internal/api/handlers/admin.go:1163` in `PreflightDeleteUser`
  - _statement-form call to known error-returning 'cursor.Close()'_
  ```go
  	cursor.Close(ctx)
  ```
- **[HIGH] Missing error check** — `internal/api/handlers/admin.go:1181` in `PreflightDeleteUser`
  - _statement-form call to known error-returning 'tCursor.Close()'_
  ```go
  			tCursor.Close(ctx)
  ```
- **[HIGH] Swallowed error** — `internal/api/handlers/admin.go:1193` in `PreflightDeleteUser`
  ```go
  		if err != nil {
  			continue
  		}
  ```
- **[HIGH] Missing error check** — `internal/api/handlers/admin.go:1198` in `PreflightDeleteUser`
  - _statement-form call to known error-returning 'memberCursor.Close()'_
  ```go
  		memberCursor.Close(ctx)
  ```
- **[HIGH] Missing error check** — `internal/api/handlers/admin.go:1215` in `PreflightDeleteUser`
  - _statement-form call to known error-returning 'uCursor.Close()'_
  ```go
  				uCursor.Close(ctx)
  ```
- **[HIGH] Ignored error (`_`)** — `internal/api/handlers/admin.go:1253` in `DeleteUser`
  - _error explicitly discarded with `_`_
  ```go
  	actingUser, _ := middleware.GetUserFromContext(r.Context())
  ```
- **[HIGH] Missing error check** — `internal/api/handlers/admin.go:1291` in `DeleteUser`
  - _statement-form call to known error-returning 'cursor.Close()'_
  ```go
  	cursor.Close(ctx)
  ```
- **[HIGH] Ignored error (`_`)** — `internal/api/handlers/admin.go:1316` in `DeleteUser`
  - _error explicitly discarded with `_`_
  ```go
  			result, _ := h.db.TenantMemberships().UpdateOne(ctx,
  ```
- **[HIGH] Ignored error (`_`)** — `internal/api/handlers/admin.go:1328` in `DeleteUser`
  - _error explicitly discarded with `_`_
  ```go
  			otherCount, _ := h.db.TenantMemberships().CountDocuments(ctx, bson.M{
  ```
- **[HIGH] Missing error check** — `internal/api/handlers/admin.go:1348` in `DeleteUser`
  - _statement-form call to known error-returning 'h.db.TenantMemberships().DeleteMany()'_
  ```go
  			h.db.TenantMemberships().DeleteMany(ctx, bson.M{"tenantId": m.TenantID})
  ```
- **[HIGH] Missing error check** — `internal/api/handlers/admin.go:1349` in `DeleteUser`
  - _statement-form call to known error-returning 'h.db.Tenants().DeleteOne()'_
  ```go
  			h.db.Tenants().DeleteOne(ctx, bson.M{"_id": m.TenantID})
  ```
- **[HIGH] Missing error check** — `internal/api/handlers/admin.go:1350` in `DeleteUser`
  - _statement-form call to known error-returning 'h.db.Invitations().DeleteMany()'_
  ```go
  			h.db.Invitations().DeleteMany(ctx, bson.M{"tenantId": m.TenantID})
  ```
- **[HIGH] Missing error check** — `internal/api/handlers/admin.go:1367` in `DeleteUser`
  - _statement-form call to known error-returning 'h.db.TenantMemberships().DeleteMany()'_
  ```go
  	h.db.TenantMemberships().DeleteMany(ctx, bson.M{"userId": userID})
  ```
- **[HIGH] Missing error check** — `internal/api/handlers/admin.go:1368` in `DeleteUser`
  - _statement-form call to known error-returning 'h.db.RefreshTokens().DeleteMany()'_
  ```go
  	h.db.RefreshTokens().DeleteMany(ctx, bson.M{"userId": userID})
  ```
- **[HIGH] Missing error check** — `internal/api/handlers/admin.go:1369` in `DeleteUser`
  - _statement-form call to known error-returning 'h.db.Messages().DeleteMany()'_
  ```go
  	h.db.Messages().DeleteMany(ctx, bson.M{"userId": userID})
  ```
- **[HIGH] Missing error check** — `internal/api/handlers/admin.go:1370` in `DeleteUser`
  - _statement-form call to known error-returning 'h.db.Users().DeleteOne()'_
  ```go
  	h.db.Users().DeleteOne(ctx, bson.M{"_id": userID})
  ```
- **[HIGH] Ignored error (`_`)** — `internal/api/handlers/admin.go:1412` in `UpdateTenant`
  - _error explicitly discarded with `_`_
  ```go
  	actingUser, _ := middleware.GetUserFromContext(r.Context())
  ```
- **[HIGH] Missing error check** — `internal/api/handlers/admin.go:1461` in `UpdateTenant`
  - _statement-form call to known error-returning 'h.db.Tenants().UpdateOne()'_
  ```go
  	h.db.Tenants().UpdateOne(r.Context(), bson.M{"_id": tenantID}, bson.M{"$set": updates})
  ```
- **[HIGH] Ignored error (`_`)** — `internal/api/handlers/admin.go:1709` in `InviteRootMember`
  - _error explicitly discarded with `_`_
  ```go
  		count, _ := h.db.TenantMemberships().CountDocuments(ctx, bson.M{
  ```
- **[HIGH] Ignored error (`_`)** — `internal/api/handlers/admin.go:1720` in `InviteRootMember`
  - _error explicitly discarded with `_`_
  ```go
  	count, _ := h.db.Invitations().CountDocuments(ctx, bson.M{
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/admin.go:173` in `ListTenants`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to count tenants")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/admin.go:184` in `ListTenants`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to fetch tenants")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/admin.go:191` in `ListTenants`
  ```go
  	if err := cursor.All(ctx, &tenants); err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to decode tenants")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/admin.go:304` in `ExportTenantsCSV`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to query tenants")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/admin.go:311` in `ExportTenantsCSV`
  ```go
  	if err := cursor.All(ctx, &tenants); err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to decode tenants")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/admin.go:393` in `GetTenant`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid tenant ID")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/admin.go:406` in `GetTenant`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to fetch members")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/admin.go:458` in `UpdateTenantStatus`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid tenant ID")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/admin.go:478` in `UpdateTenantStatus`
  ```go
  	if err := decodeJSON(r, &req); err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid request body")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/admin.go:563` in `ListUsers`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to count users")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/admin.go:574` in `ListUsers`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to fetch users")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/admin.go:581` in `ListUsers`
  ```go
  	if err := cursor.All(ctx, &users); err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to decode users")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/admin.go:660` in `ExportUsersCSV`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to query users")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/admin.go:667` in `ExportUsersCSV`
  ```go
  	if err := cursor.All(ctx, &users); err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to decode users")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/admin.go:725` in `UpdateUserStatus`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid user ID")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/admin.go:740` in `UpdateUserStatus`
  ```go
  	if err := decodeJSON(r, &req); err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid request body")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/admin.go:749` in `UpdateUserStatus`
  ```go
  	if err != nil || result.MatchedCount == 0 {
  		respondWithError(w, http.StatusNotFound, "User not found")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/admin.go:878` in `GetUser`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid user ID")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/admin.go:890` in `GetUser`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to fetch memberships")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/admin.go:989` in `UpdateUser`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid user ID")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/admin.go:1005` in `UpdateUser`
  ```go
  	if err := decodeJSON(r, &req); err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid request body")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/admin.go:1052` in `UpdateUserRole`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid user ID")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/admin.go:1057` in `UpdateUserRole`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid tenant ID")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/admin.go:1072` in `UpdateUserRole`
  ```go
  	if err := decodeJSON(r, &req); err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid request body")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/admin.go:1114` in `UpdateUserRole`
  ```go
  	if err != nil || result.MatchedCount == 0 {
  		respondWithError(w, http.StatusNotFound, "Membership not found")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/admin.go:1136` in `PreflightDeleteUser`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid user ID")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/admin.go:1153` in `PreflightDeleteUser`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to query memberships")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/admin.go:1158` in `PreflightDeleteUser`
  ```go
  	if err := cursor.All(ctx, &ownerships); err != nil {
  		cursor.Close(ctx)
  		respondWithError(w, http.StatusInternalServerError, "Failed to read memberships")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/admin.go:1248` in `DeleteUser`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid user ID")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/admin.go:1269` in `DeleteUser`
  ```go
  	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid request body")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/admin.go:1281` in `DeleteUser`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to query memberships")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/admin.go:1286` in `DeleteUser`
  ```go
  	if err := cursor.All(ctx, &memberships); err != nil {
  		cursor.Close(ctx)
  		respondWithError(w, http.StatusInternalServerError, "Failed to read memberships")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/admin.go:1312` in `DeleteUser`
  ```go
  			if err != nil {
  				respondWithError(w, http.StatusBadRequest, "Invalid replacement owner ID")
  				return
  			}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/admin.go:1390` in `UpdateTenant`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid tenant ID")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/admin.go:1401` in `UpdateTenant`
  ```go
  	if err := decodeJSON(r, &req); err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid request body")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/admin.go:1478` in `ImpersonateUser`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid user ID")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/admin.go:1516` in `ImpersonateUser`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to generate impersonation token")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/admin.go:1539` in `ImpersonateUser`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to fetch memberships")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/admin.go:1584` in `ListRootMembers`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Root tenant not found")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/admin.go:1591` in `ListRootMembers`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to fetch members")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/admin.go:1598` in `ListRootMembers`
  ```go
  	if err := cursor.All(ctx, &memberships); err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to decode members")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/admin.go:1666` in `InviteRootMember`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Root tenant not found")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/admin.go:1683` in `InviteRootMember`
  ```go
  	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid request body")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/admin.go:1748` in `InviteRootMember`
  ```go
  	if _, err := h.db.Invitations().InsertOne(ctx, invitation); err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to create invitation")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/admin.go:1758` in `InviteRootMember`
  ```go
  			if err := h.emailService.SendInvitationEmail(req.Email, user.DisplayName, rootTenant.Name, token); err != nil {
  				slog.Error("Failed to send root member invitation email", "to", req.Email, "error", err)
  			}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/admin.go:1786` in `RemoveRootMember`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Root tenant not found")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/admin.go:1798` in `RemoveRootMember`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid user ID")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/admin.go:1853` in `ChangeRootMemberRole`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Root tenant not found")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/admin.go:1870` in `ChangeRootMemberRole`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid user ID")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/admin.go:1881` in `ChangeRootMemberRole`
  ```go
  	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid request body")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/admin.go:1899` in `ChangeRootMemberRole`
  ```go
  	if err != nil || result.MatchedCount == 0 {
  		respondWithError(w, http.StatusNotFound, "Member not found")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/admin.go:1926` in `CancelRootInvitation`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Root tenant not found")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/admin.go:1932` in `CancelRootInvitation`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid invitation ID")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/admin.go:1942` in `CancelRootInvitation`
  ```go
  	if err != nil || result.DeletedCount == 0 {
  		respondWithError(w, http.StatusNotFound, "Invitation not found")
  		return
  	}
  ```

### `internal/api/handlers/announcements.go`

- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/announcements.go:34` in `ListPublic`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to list announcements")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/announcements.go:41` in `ListPublic`
  ```go
  	if err := cursor.All(r.Context(), &announcements); err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to decode announcements")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/announcements.go:55` in `ListAll`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to list announcements")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/announcements.go:62` in `ListAll`
  ```go
  	if err := cursor.All(r.Context(), &announcements); err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to decode announcements")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/announcements.go:79` in `Create`
  ```go
  	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid request body")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/announcements.go:100` in `Create`
  ```go
  	if err := validation.Validate(&ann); err != nil {
  		respondWithError(w, http.StatusBadRequest, err.Error())
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/announcements.go:106` in `Create`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to create announcement")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/announcements.go:122` in `Update`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid announcement ID")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/announcements.go:132` in `Update`
  ```go
  	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid request body")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/announcements.go:153` in `Update`
  ```go
  	if err != nil || result.MatchedCount == 0 {
  		respondWithError(w, http.StatusNotFound, "Announcement not found")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/announcements.go:163` in `Delete`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid announcement ID")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/announcements.go:169` in `Delete`
  ```go
  	if err != nil || result.DeletedCount == 0 {
  		respondWithError(w, http.StatusNotFound, "Announcement not found")
  		return
  	}
  ```

### `internal/api/handlers/apikeys.go`

- **[HIGH] Ignored error (`_`)** — `internal/api/handlers/apikeys.go:60` in `ListAPIKeys`
  - _error explicitly discarded with `_`_
  ```go
  	total, _ := h.db.APIKeys().CountDocuments(r.Context(), bson.M{"isActive": true})
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/apikeys.go:46` in `ListAPIKeys`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to list API keys")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/apikeys.go:53` in `ListAPIKeys`
  ```go
  	if err := cursor.All(r.Context(), &keys); err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to decode API keys")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/apikeys.go:70` in `CreateAPIKey`
  ```go
  	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid request body")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/apikeys.go:118` in `CreateAPIKey`
  ```go
  	if err := validation.Validate(&apiKey); err != nil {
  		respondWithError(w, http.StatusBadRequest, err.Error())
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/apikeys.go:124` in `CreateAPIKey`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to create API key")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/apikeys.go:157` in `DeleteAPIKey`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid key ID")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/apikeys.go:165` in `DeleteAPIKey`
  ```go
  	if err != nil || result.MatchedCount == 0 {
  		respondWithError(w, http.StatusNotFound, "API key not found")
  		return
  	}
  ```

### `internal/api/handlers/auth.go`

- **[HIGH] Swallowed error** — `internal/api/handlers/auth.go:105` in `generateTokenPair`
  ```go
  	if err != nil {
  		return
  	}
  ```
- **[HIGH] Ignored error (`_`)** — `internal/api/handlers/auth.go:667` in `ForgotPassword`
  - _error explicitly discarded with `_`_
  ```go
  		if allowed, _, _ := h.rateLimiter.Allow("email:pwreset:"+req.Email, middleware.EmailPasswordResetLimit); !allowed {
  ```
- **[HIGH] Missing error check** — `internal/api/handlers/auth.go:696` in `ForgotPassword`
  - _statement-form call to known error-returning 'h.db.VerificationTokens().InsertOne()'_
  ```go
  	h.db.VerificationTokens().InsertOne(r.Context(), verification)
  ```
- **[HIGH] Ignored error (`_`)** — `internal/api/handlers/auth.go:1162` in `MagicLinkRequest`
  - _error explicitly discarded with `_`_
  ```go
  		if allowed, _, _ := h.rateLimiter.Allow("email:magiclink:"+req.Email, middleware.EmailMagicLinkLimit); !allowed {
  ```
- **[HIGH] Missing error check** — `internal/api/handlers/auth.go:1186` in `MagicLinkRequest`
  - _statement-form call to known error-returning 'h.db.VerificationTokens().InsertOne()'_
  ```go
  	h.db.VerificationTokens().InsertOne(r.Context(), verification)
  ```
- **[HIGH] Swallowed error** — `internal/api/handlers/auth.go:1294` in `createAuthCodeRedirect`
  ```go
  	if _, err := h.db.AuthCodes().InsertOne(r.Context(), authCode); err != nil {
  		http.Redirect(w, r, h.frontendURL+"/login?error=code_generation_failed", http.StatusTemporaryRedirect)
  		return
  	}
  ```
- **[HIGH] Swallowed error** — `internal/api/handlers/auth.go:1381` in `GoogleOAuthCallback`
  ```go
  	if result.Err() != nil {
  		http.Redirect(w, r, h.frontendURL+"/login?error=invalid_state", http.StatusTemporaryRedirect)
  		return
  	}
  ```
- **[HIGH] Swallowed error** — `internal/api/handlers/auth.go:1387` in `GoogleOAuthCallback`
  ```go
  	if err != nil {
  		http.Redirect(w, r, h.frontendURL+"/login?error=oauth_exchange_failed", http.StatusTemporaryRedirect)
  		return
  	}
  ```
- **[HIGH] Swallowed error** — `internal/api/handlers/auth.go:1393` in `GoogleOAuthCallback`
  ```go
  	if err != nil || !googleUser.VerifiedEmail {
  		http.Redirect(w, r, h.frontendURL+"/login?error=oauth_user_info_failed", http.StatusTemporaryRedirect)
  		return
  	}
  ```
- **[HIGH] Swallowed error** — `internal/api/handlers/auth.go:1403` in `GoogleOAuthCallback`
  ```go
  	if err != nil {
  		err = h.db.Users().FindOne(r.Context(), bson.M{"email": strings.ToLower(googleUser.Email)}).Decode(&user)
  		if err != nil {
  			isNewUser = true
  			user = models.User{
  				ID:            primitive.NewObjectID(),
  ... (24 more lines)
  ```
- **[HIGH] Swallowed error** — `internal/api/handlers/auth.go:1405` in `GoogleOAuthCallback`
  ```go
  		if err != nil {
  			isNewUser = true
  			user = models.User{
  				ID:            primitive.NewObjectID(),
  				Email:         strings.ToLower(googleUser.Email),
  				DisplayName:   googleUser.GivenName,
  ... (16 more lines)
  ```
- **[HIGH] Swallowed error** — `internal/api/handlers/auth.go:1419` in `GoogleOAuthCallback`
  ```go
  			if _, err := h.db.Users().InsertOne(r.Context(), user); err != nil {
  				slog.Error("OAuth: failed to create user", "error", err)
  				http.Redirect(w, r, h.frontendURL+"/login?error=account_creation_failed", http.StatusTemporaryRedirect)
  				return
  			}
  ```
- **[HIGH] Swallowed error** — `internal/api/handlers/auth.go:1441` in `GoogleOAuthCallback`
  ```go
  		if err != nil {
  			http.Redirect(w, r, h.frontendURL+"/login?error=token_generation_failed", http.StatusTemporaryRedirect)
  			return
  		}
  ```
- **[HIGH] Swallowed error** — `internal/api/handlers/auth.go:1450` in `GoogleOAuthCallback`
  ```go
  	if err != nil {
  		http.Redirect(w, r, h.frontendURL+"/login?error=token_generation_failed", http.StatusTemporaryRedirect)
  		return
  	}
  ```
- **[HIGH] Swallowed error** — `internal/api/handlers/auth.go:1454` in `GoogleOAuthCallback`
  ```go
  	if err := storeRefreshToken(r, h.db, user.ID, refreshToken, refreshTTL); err != nil {
  		slog.Error("Failed to store refresh token", "error", err)
  		http.Redirect(w, r, h.frontendURL+"/login?error=session_creation_failed", http.StatusTemporaryRedirect)
  		return
  	}
  ```
- **[HIGH] Swallowed error** — `internal/api/handlers/auth.go:1514` in `GitHubOAuthCallback`
  ```go
  	if result.Err() != nil {
  		http.Redirect(w, r, h.frontendURL+"/login?error=invalid_state", http.StatusTemporaryRedirect)
  		return
  	}
  ```
- **[HIGH] Swallowed error** — `internal/api/handlers/auth.go:1520` in `GitHubOAuthCallback`
  ```go
  	if err != nil {
  		http.Redirect(w, r, h.frontendURL+"/login?error=oauth_exchange_failed", http.StatusTemporaryRedirect)
  		return
  	}
  ```
- **[HIGH] Swallowed error** — `internal/api/handlers/auth.go:1526` in `GitHubOAuthCallback`
  ```go
  	if err != nil {
  		http.Redirect(w, r, h.frontendURL+"/login?error=oauth_user_info_failed", http.StatusTemporaryRedirect)
  		return
  	}
  ```
- **[HIGH] Swallowed error** — `internal/api/handlers/auth.go:1537` in `GitHubOAuthCallback`
  ```go
  	if err != nil {
  		err = h.db.Users().FindOne(r.Context(), bson.M{"email": strings.ToLower(ghUser.Email)}).Decode(&user)
  		if err != nil {
  			isNewUser = true
  			displayName := ghUser.Name
  			if displayName == "" {
  ... (33 more lines)
  ```
- **[HIGH] Swallowed error** — `internal/api/handlers/auth.go:1539` in `GitHubOAuthCallback`
  ```go
  		if err != nil {
  			isNewUser = true
  			displayName := ghUser.Name
  			if displayName == "" {
  				displayName = ghUser.Login
  			}
  ... (20 more lines)
  ```
- **[HIGH] Swallowed error** — `internal/api/handlers/auth.go:1557` in `GitHubOAuthCallback`
  ```go
  			if _, err := h.db.Users().InsertOne(r.Context(), user); err != nil {
  				slog.Error("OAuth: failed to create user", "error", err)
  				http.Redirect(w, r, h.frontendURL+"/login?error=account_creation_failed", http.StatusTemporaryRedirect)
  				return
  			}
  ```
- **[HIGH] Swallowed error** — `internal/api/handlers/auth.go:1583` in `GitHubOAuthCallback`
  ```go
  		if err != nil {
  			http.Redirect(w, r, h.frontendURL+"/login?error=token_generation_failed", http.StatusTemporaryRedirect)
  			return
  		}
  ```
- **[HIGH] Swallowed error** — `internal/api/handlers/auth.go:1592` in `GitHubOAuthCallback`
  ```go
  	if err != nil {
  		http.Redirect(w, r, h.frontendURL+"/login?error=token_generation_failed", http.StatusTemporaryRedirect)
  		return
  	}
  ```
- **[HIGH] Swallowed error** — `internal/api/handlers/auth.go:1596` in `GitHubOAuthCallback`
  ```go
  	if err := storeRefreshToken(r, h.db, user.ID, refreshToken, refreshTTL); err != nil {
  		slog.Error("Failed to store refresh token", "error", err)
  		http.Redirect(w, r, h.frontendURL+"/login?error=session_creation_failed", http.StatusTemporaryRedirect)
  		return
  	}
  ```
- **[HIGH] Swallowed error** — `internal/api/handlers/auth.go:1656` in `MicrosoftOAuthCallback`
  ```go
  	if result.Err() != nil {
  		http.Redirect(w, r, h.frontendURL+"/login?error=invalid_state", http.StatusTemporaryRedirect)
  		return
  	}
  ```
- **[HIGH] Swallowed error** — `internal/api/handlers/auth.go:1662` in `MicrosoftOAuthCallback`
  ```go
  	if err != nil {
  		http.Redirect(w, r, h.frontendURL+"/login?error=oauth_exchange_failed", http.StatusTemporaryRedirect)
  		return
  	}
  ```
- **[HIGH] Swallowed error** — `internal/api/handlers/auth.go:1668` in `MicrosoftOAuthCallback`
  ```go
  	if err != nil {
  		http.Redirect(w, r, h.frontendURL+"/login?error=oauth_user_info_failed", http.StatusTemporaryRedirect)
  		return
  	}
  ```
- **[HIGH] Swallowed error** — `internal/api/handlers/auth.go:1684` in `MicrosoftOAuthCallback`
  ```go
  	if err != nil {
  		err = h.db.Users().FindOne(r.Context(), bson.M{"email": strings.ToLower(userEmail)}).Decode(&user)
  		if err != nil {
  			isNewUser = true
  			displayName := msUser.DisplayName
  			if displayName == "" {
  ... (33 more lines)
  ```
- **[HIGH] Swallowed error** — `internal/api/handlers/auth.go:1686` in `MicrosoftOAuthCallback`
  ```go
  		if err != nil {
  			isNewUser = true
  			displayName := msUser.DisplayName
  			if displayName == "" {
  				displayName = msUser.GivenName
  			}
  ... (20 more lines)
  ```
- **[HIGH] Swallowed error** — `internal/api/handlers/auth.go:1704` in `MicrosoftOAuthCallback`
  ```go
  			if _, err := h.db.Users().InsertOne(r.Context(), user); err != nil {
  				slog.Error("OAuth: failed to create user", "error", err)
  				http.Redirect(w, r, h.frontendURL+"/login?error=account_creation_failed", http.StatusTemporaryRedirect)
  				return
  			}
  ```
- **[HIGH] Swallowed error** — `internal/api/handlers/auth.go:1730` in `MicrosoftOAuthCallback`
  ```go
  		if err != nil {
  			http.Redirect(w, r, h.frontendURL+"/login?error=token_generation_failed", http.StatusTemporaryRedirect)
  			return
  		}
  ```
- **[HIGH] Swallowed error** — `internal/api/handlers/auth.go:1739` in `MicrosoftOAuthCallback`
  ```go
  	if err != nil {
  		http.Redirect(w, r, h.frontendURL+"/login?error=token_generation_failed", http.StatusTemporaryRedirect)
  		return
  	}
  ```
- **[HIGH] Swallowed error** — `internal/api/handlers/auth.go:1743` in `MicrosoftOAuthCallback`
  ```go
  	if err := storeRefreshToken(r, h.db, user.ID, refreshToken, refreshTTL); err != nil {
  		slog.Error("Failed to store refresh token", "error", err)
  		http.Redirect(w, r, h.frontendURL+"/login?error=session_creation_failed", http.StatusTemporaryRedirect)
  		return
  	}
  ```
- **[HIGH] Missing error check** — `internal/api/handlers/auth.go:1901` in `UpdatePreferences`
  - _statement-form call to known error-returning 'h.db.Users().UpdateOne()'_
  ```go
  	h.db.Users().UpdateOne(r.Context(), bson.M{"_id": user.ID}, bson.M{"$set": update})
  ```
- **[HIGH] Swallowed error** — `internal/api/handlers/auth.go:1967` in `createPersonalTenant`
  ```go
  	if _, err := h.db.Tenants().InsertOne(ctx, tenant); err != nil {
  		slog.Error("Failed to create personal tenant", "userId", userID.Hex(), "error", err)
  		return
  	}
  ```
- **[HIGH] Missing error check** — `internal/api/handlers/auth.go:2002` in `sendVerificationEmail`
  - _statement-form call to known error-returning 'h.db.VerificationTokens().InsertOne()'_
  ```go
  	h.db.VerificationTokens().InsertOne(ctx, verification)
  ```
- **[HIGH] Swallowed error** — `internal/api/handlers/auth.go:2025` in `getUserMemberships`
  ```go
  	if err != nil {
  		return nil
  	}
  ```
- **[HIGH] Swallowed error** — `internal/api/handlers/auth.go:2031` in `getUserMemberships`
  ```go
  	if err := cursor.All(ctx, &memberships); err != nil {
  		return nil
  	}
  ```
- **[HIGH] Swallowed error** — `internal/api/handlers/auth.go:2063` in `acceptInvitationForUser`
  ```go
  	if err != nil {
  		return fmt.Errorf("invalid or expired invitation")
  	}
  ```
- **[HIGH] Swallowed error** — `internal/api/handlers/auth.go:2085` in `acceptInvitationForUser`
  ```go
  	if res.Err() != nil {
  		return fmt.Errorf("invitation already accepted")
  	}
  ```
- **[HIGH] Ignored error (`_`)** — `internal/api/handlers/auth.go:2089` in `acceptInvitationForUser`
  - _error explicitly discarded with `_`_
  ```go
  	count, _ := h.db.TenantMemberships().CountDocuments(ctx, bson.M{
  ```
- **[HIGH] Swallowed error** — `internal/api/handlers/auth.go:2105` in `acceptInvitationForUser`
  ```go
  	if _, err := h.db.TenantMemberships().InsertOne(ctx, membership); err != nil {
  		return fmt.Errorf("failed to create membership")
  	}
  ```
- **[HIGH] Ignored error (`_`)** — `internal/api/handlers/auth.go:2142` in `storeRefreshToken`
  - _error explicitly discarded with `_`_
  ```go
  	activeCount, _ := database.RefreshTokens().CountDocuments(r.Context(), bson.M{
  ```
- **[HIGH] Missing error check** — `internal/api/handlers/auth.go:2229` in `DeleteAccount`
  - _statement-form call to known error-returning 'cursor.Close()'_
  ```go
  	cursor.Close(ctx)
  ```
- **[HIGH] Ignored error (`_`)** — `internal/api/handlers/auth.go:2246` in `DeleteAccount`
  - _error explicitly discarded with `_`_
  ```go
  		otherCount, _ := h.db.TenantMemberships().CountDocuments(ctx, bson.M{
  ```
- **[HIGH] Ignored error (`_`)** — `internal/api/handlers/auth.go:2317` in `ExportData`
  - _error explicitly discarded with `_`_
  ```go
  	cursor, _ := h.db.TenantMemberships().Find(ctx, bson.M{"userId": user.ID})
  ```
- **[HIGH] Missing error check** — `internal/api/handlers/auth.go:2321` in `ExportData`
  - _statement-form call to known error-returning 'cursor.Close()'_
  ```go
  		cursor.Close(ctx)
  ```
- **[HIGH] Ignored error (`_`)** — `internal/api/handlers/auth.go:2339` in `ExportData`
  - _error explicitly discarded with `_`_
  ```go
  	msgCursor, _ := h.db.Messages().Find(ctx, bson.M{"userId": user.ID})
  ```
- **[HIGH] Missing error check** — `internal/api/handlers/auth.go:2343` in `ExportData`
  - _statement-form call to known error-returning 'msgCursor.Close()'_
  ```go
  		msgCursor.Close(ctx)
  ```
- **[HIGH] Missing error check** — `internal/api/handlers/auth.go:2382` in `ExportData`
  - _statement-form call to known error-returning 'json.NewEncoder(w).Encode()'_
  ```go
  	json.NewEncoder(w).Encode(export)
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/auth.go:195` in `Register`
  ```go
  	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid request body")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/auth.go:213` in `Register`
  ```go
  	if err := h.passwordService.ValidatePasswordStrength(req.Password); err != nil {
  		respondWithError(w, http.StatusBadRequest, err.Error())
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/auth.go:226` in `Register`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to process password")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/auth.go:244` in `Register`
  ```go
  	if err := validation.Validate(&user); err != nil {
  		respondWithError(w, http.StatusBadRequest, err.Error())
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/auth.go:249` in `Register`
  ```go
  	if _, err := h.db.Users().InsertOne(r.Context(), user); err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to create user")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/auth.go:259` in `Register`
  ```go
  		if err := h.acceptInvitationForUser(r.Context(), user.ID, req.InvitationToken); err != nil {
  			slog.Error("Failed to accept invitation during registration", "error", err)
  		} else {
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/auth.go:275` in `Register`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to generate token")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/auth.go:279` in `Register`
  ```go
  	if err := storeRefreshToken(r, h.db, user.ID, refreshToken, refreshTTL); err != nil {
  		slog.Error("Failed to store refresh token", "error", err)
  		respondWithError(w, http.StatusInternalServerError, "Failed to create session")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/auth.go:311` in `Login`
  ```go
  	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid request body")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/auth.go:342` in `Login`
  ```go
  	if err := h.passwordService.ComparePassword(user.PasswordHash, req.Password); err != nil {
  		// Atomic increment of failed attempts + conditional lock
  		now := time.Now()
  		filter := bson.M{
  			"_id": user.ID,
  			"$or": []bson.M{
  ... (25 more lines)
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/auth.go:393` in `Login`
  ```go
  		if err != nil {
  			respondWithError(w, http.StatusInternalServerError, "Failed to generate token")
  			return
  		}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/auth.go:405` in `Login`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to generate token")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/auth.go:409` in `Login`
  ```go
  	if err := storeRefreshToken(r, h.db, user.ID, refreshToken, refreshTTL); err != nil {
  		slog.Error("Failed to store refresh token", "error", err)
  		respondWithError(w, http.StatusInternalServerError, "Failed to create session")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/auth.go:480` in `Refresh`
  ```go
  	if err := json.NewDecoder(r.Body).Decode(&req); err != nil || req.RefreshToken == "" {
  		respondWithError(w, http.StatusBadRequest, "Refresh token is required")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/auth.go:486` in `Refresh`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusUnauthorized, "Invalid refresh token")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/auth.go:497` in `Refresh`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusUnauthorized, "Refresh token not found")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/auth.go:522` in `Refresh`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusUnauthorized, "Invalid user ID")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/auth.go:534` in `Refresh`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to generate token")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/auth.go:538` in `Refresh`
  ```go
  	if err := storeRefreshToken(r, h.db, user.ID, refreshToken, refreshTTL, storedToken.FamilyID); err != nil {
  		slog.Error("Failed to store refresh token", "error", err)
  		respondWithError(w, http.StatusInternalServerError, "Failed to create session")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/auth.go:578` in `VerifyEmail`
  ```go
  	if err := json.NewDecoder(r.Body).Decode(&req); err != nil || req.Token == "" {
  		respondWithError(w, http.StatusBadRequest, "Token is required")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/auth.go:596` in `VerifyEmail`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid or expired verification token")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/auth.go:628` in `ResendVerification`
  ```go
  	if err := json.NewDecoder(r.Body).Decode(&req); err != nil || req.Email == "" {
  		respondWithError(w, http.StatusBadRequest, "Email is required")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/auth.go:658` in `ForgotPassword`
  ```go
  	if err := json.NewDecoder(r.Body).Decode(&req); err != nil || req.Email == "" {
  		respondWithError(w, http.StatusBadRequest, "Email is required")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/auth.go:703` in `ForgotPassword`
  ```go
  			if err := h.emailService.SendPasswordResetEmail(user.Email, user.DisplayName, resetToken); err != nil {
  				slog.Error("Failed to send password reset email", "error", err)
  			}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/auth.go:712` in `ResetPassword`
  ```go
  	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid request body")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/auth.go:722` in `ResetPassword`
  ```go
  	if err := h.passwordService.ValidatePasswordStrength(req.NewPassword); err != nil {
  		respondWithError(w, http.StatusBadRequest, err.Error())
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/auth.go:741` in `ResetPassword`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid or expired reset token")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/auth.go:747` in `ResetPassword`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to process password")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/auth.go:780` in `ChangePassword`
  ```go
  	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid request body")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/auth.go:790` in `ChangePassword`
  ```go
  	if err := h.passwordService.ValidatePasswordStrength(req.NewPassword); err != nil {
  		respondWithError(w, http.StatusBadRequest, err.Error())
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/auth.go:800` in `ChangePassword`
  ```go
  		if err := h.passwordService.ComparePassword(user.PasswordHash, req.CurrentPassword); err != nil {
  			respondWithError(w, http.StatusUnauthorized, "Current password is incorrect")
  			return
  		}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/auth.go:807` in `ChangePassword`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to process password")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/auth.go:863` in `MFASetup`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to generate MFA secret")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/auth.go:870` in `MFASetup`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to secure MFA secret")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/auth.go:898` in `MFAVerifySetup`
  ```go
  	if err := json.NewDecoder(r.Body).Decode(&req); err != nil || req.Code == "" {
  		respondWithError(w, http.StatusBadRequest, "Code is required")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/auth.go:923` in `MFAVerifySetup`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to generate recovery codes")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/auth.go:960` in `MFADisable`
  ```go
  	if err := json.NewDecoder(r.Body).Decode(&req); err != nil || req.Code == "" {
  		respondWithError(w, http.StatusBadRequest, "Code is required")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/auth.go:1010` in `MFAChallenge`
  ```go
  	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid request body")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/auth.go:1020` in `MFAChallenge`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusUnauthorized, "Invalid or expired MFA token")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/auth.go:1030` in `MFAChallenge`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusUnauthorized, "Invalid user")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/auth.go:1063` in `MFAChallenge`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to generate token")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/auth.go:1067` in `MFAChallenge`
  ```go
  	if err := storeRefreshToken(r, h.db, user.ID, refreshToken, refreshTTL); err != nil {
  		slog.Error("Failed to store refresh token", "error", err)
  		respondWithError(w, http.StatusInternalServerError, "Failed to create session")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/auth.go:1103` in `MFARegenerateRecoveryCodes`
  ```go
  	if err := json.NewDecoder(r.Body).Decode(&req); err != nil || req.Code == "" {
  		respondWithError(w, http.StatusBadRequest, "Code is required")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/auth.go:1125` in `MFARegenerateRecoveryCodes`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to generate recovery codes")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/auth.go:1154` in `MagicLinkRequest`
  ```go
  	if err := json.NewDecoder(r.Body).Decode(&req); err != nil || req.Email == "" {
  		respondWithError(w, http.StatusBadRequest, "Email is required")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/auth.go:1193` in `MagicLinkRequest`
  ```go
  			if err := h.emailService.SendMagicLinkEmail(user.Email, user.DisplayName, magicToken); err != nil {
  				slog.Error("Failed to send magic link email", "error", err)
  			}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/auth.go:1209` in `MagicLinkVerify`
  ```go
  	if err := json.NewDecoder(r.Body).Decode(&req); err != nil || req.Token == "" {
  		respondWithError(w, http.StatusBadRequest, "Token is required")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/auth.go:1228` in `MagicLinkVerify`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid or expired magic link token")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/auth.go:1248` in `MagicLinkVerify`
  ```go
  		if err != nil {
  			respondWithError(w, http.StatusInternalServerError, "Failed to generate token")
  			return
  		}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/auth.go:1260` in `MagicLinkVerify`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to generate token")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/auth.go:1264` in `MagicLinkVerify`
  ```go
  	if err := storeRefreshToken(r, h.db, user.ID, refreshToken, refreshTTL); err != nil {
  		slog.Error("Failed to store refresh token", "error", err)
  		respondWithError(w, http.StatusInternalServerError, "Failed to create session")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/auth.go:1307` in `ExchangeCode`
  ```go
  	if err := json.NewDecoder(r.Body).Decode(&req); err != nil || req.Code == "" {
  		respondWithError(w, http.StatusBadRequest, "Code is required")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/auth.go:1319` in `ExchangeCode`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusUnauthorized, "Invalid or expired code")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/auth.go:1353` in `GoogleOAuth`
  ```go
  	if _, err := h.db.OAuthStates().InsertOne(r.Context(), oauthState); err != nil {
  		slog.Error("Failed to store OAuth state", "error", err)
  		respondWithError(w, http.StatusInternalServerError, "Failed to initiate OAuth")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/auth.go:1486` in `GitHubOAuth`
  ```go
  	if _, err := h.db.OAuthStates().InsertOne(r.Context(), oauthState); err != nil {
  		slog.Error("Failed to store OAuth state", "error", err)
  		respondWithError(w, http.StatusInternalServerError, "Failed to initiate OAuth")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/auth.go:1628` in `MicrosoftOAuth`
  ```go
  	if _, err := h.db.OAuthStates().InsertOne(r.Context(), oauthState); err != nil {
  		slog.Error("Failed to store OAuth state", "error", err)
  		respondWithError(w, http.StatusInternalServerError, "Failed to initiate OAuth")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/auth.go:1774` in `ListSessions`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to fetch sessions")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/auth.go:1781` in `ListSessions`
  ```go
  	if err := cursor.All(r.Context(), &tokens); err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to fetch sessions")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/auth.go:1835` in `RevokeSession`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid session ID")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/auth.go:1844` in `RevokeSession`
  ```go
  	if err != nil || result.ModifiedCount == 0 {
  		respondWithError(w, http.StatusNotFound, "Session not found")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/auth.go:1887` in `UpdatePreferences`
  ```go
  	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid request body")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/auth.go:1936` in `AcceptInvitation`
  ```go
  	if err := json.NewDecoder(r.Body).Decode(&req); err != nil || req.Token == "" {
  		respondWithError(w, http.StatusBadRequest, "Invitation token is required")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/auth.go:1941` in `AcceptInvitation`
  ```go
  	if err := h.acceptInvitationForUser(r.Context(), user.ID, req.Token); err != nil {
  		respondWithError(w, http.StatusBadRequest, err.Error())
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/auth.go:1980` in `createPersonalTenant`
  ```go
  	if _, err := h.db.TenantMemberships().InsertOne(ctx, membership); err != nil {
  		slog.Error("Failed to create membership for personal tenant", "error", err)
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/auth.go:2014` in `sendVerificationEmail`
  ```go
  			if err := h.emailService.SendVerificationEmail(userEmail, displayName, verificationToken); err != nil {
  				slog.Error("Failed to send verification email", "to", userEmail, "error", err)
  			}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/auth.go:2197` in `DeleteAccount`
  ```go
  	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid request body")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/auth.go:2208` in `DeleteAccount`
  ```go
  		if err := h.passwordService.ComparePassword(user.PasswordHash, req.Password); err != nil {
  			respondWithError(w, http.StatusUnauthorized, "Incorrect password")
  			return
  		}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/auth.go:2218` in `DeleteAccount`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to check memberships")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/auth.go:2223` in `DeleteAccount`
  ```go
  	if err := cursor.All(ctx, &memberships); err != nil {
  		cursor.Close(ctx)
  		slog.Error("Failed to decode memberships during account deletion", "userId", user.ID.Hex(), "error", err)
  		respondWithError(w, http.StatusInternalServerError, "Failed to check memberships")
  		return
  	}
  ```
- **[LOW] Proper handling** — `internal/api/handlers/auth.go:2180` in `storeRefreshToken`
  ```go
  	if _, err := database.RefreshTokens().InsertOne(r.Context(), rt); err != nil {
  		return fmt.Errorf("failed to store refresh token: %w", err)
  	}
  ```

### `internal/api/handlers/billing.go`

- **[HIGH] Ignored error (`_`)** — `internal/api/handlers/billing.go:138` in `Checkout`
  - _error explicitly discarded with `_`_
  ```go
  				memberCount, _ := h.db.TenantMemberships().CountDocuments(ctx, bson.M{"tenantId": tenant.ID})
  ```
- **[HIGH] Ignored error (`_`)** — `internal/api/handlers/billing.go:158` in `Checkout`
  - _error explicitly discarded with `_`_
  ```go
  			memberCount, _ := h.db.TenantMemberships().CountDocuments(ctx, bson.M{"tenantId": tenant.ID})
  ```
- **[HIGH] Ignored error (`_`)** — `internal/api/handlers/billing.go:384` in `ListTransactions`
  - _error explicitly discarded with `_`_
  ```go
  	page, _ := strconv.Atoi(q.Get("page"))
  ```
- **[HIGH] Ignored error (`_`)** — `internal/api/handlers/billing.go:388` in `ListTransactions`
  - _error explicitly discarded with `_`_
  ```go
  	perPage, _ := strconv.Atoi(q.Get("perPage"))
  ```
- **[HIGH] Ignored error (`_`)** — `internal/api/handlers/billing.go:395` in `ListTransactions`
  - _error explicitly discarded with `_`_
  ```go
  	total, _ := h.db.FinancialTransactions().CountDocuments(ctx, filter)
  ```
- **[HIGH] Missing error check** — `internal/api/handlers/billing.go:601` in `GetInvoicePDF`
  - _statement-form call to known error-returning 'w.Write()'_
  ```go
  	w.Write(buf.Bytes())
  ```
- **[HIGH] Missing error check** — `internal/api/handlers/billing.go:639` in `CancelSubscription`
  - _statement-form call to known error-returning 'h.db.Tenants().UpdateOne()'_
  ```go
  	h.db.Tenants().UpdateOne(ctx, bson.M{"_id": tenant.ID}, bson.M{"$set": updates})
  ```
- **[HIGH] Ignored error (`_`)** — `internal/api/handlers/billing.go:654` in `CancelSubscription`
  - _error explicitly discarded with `_`_
  ```go
  		user, _ := middleware.GetUserFromContext(ctx)
  ```
- **[HIGH] Ignored error (`_`)** — `internal/api/handlers/billing.go:689` in `AdminListTransactions`
  - _error explicitly discarded with `_`_
  ```go
  	page, _ := strconv.Atoi(q.Get("page"))
  ```
- **[HIGH] Ignored error (`_`)** — `internal/api/handlers/billing.go:693` in `AdminListTransactions`
  - _error explicitly discarded with `_`_
  ```go
  	perPage, _ := strconv.Atoi(q.Get("perPage"))
  ```
- **[HIGH] Ignored error (`_`)** — `internal/api/handlers/billing.go:714` in `AdminListTransactions`
  - _error explicitly discarded with `_`_
  ```go
  	total, _ := h.db.FinancialTransactions().CountDocuments(ctx, filter)
  ```
- **[HIGH] Ignored error (`_`)** — `internal/api/handlers/billing.go:853` in `computeLiveRevenue`
  - _error explicitly discarded with `_`_
  ```go
  	dayStart, _ := time.Parse("2006-01-02", dateStr)
  ```
- **[HIGH] Swallowed error** — `internal/api/handlers/billing.go:867` in `computeLiveRevenue`
  ```go
  	if err != nil {
  		return 0
  	}
  ```
- **[HIGH] Swallowed error** — `internal/api/handlers/billing.go:902` in `computeLiveARR`
  ```go
  	if err != nil {
  		return 0
  	}
  ```
- **[HIGH] Missing error check** — `internal/api/handlers/billing.go:972` in `AdminCancelSubscription`
  - _statement-form call to known error-returning 'h.db.Tenants().UpdateOne()'_
  ```go
  		h.db.Tenants().UpdateOne(ctx, bson.M{"_id": tenantID}, bson.M{"$set": updates})
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/billing.go:72` in `Checkout`
  ```go
  	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid request body")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/billing.go:88` in `Checkout`
  ```go
  		if err != nil {
  			respondWithError(w, http.StatusBadRequest, "Invalid plan ID")
  			return
  		}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/billing.go:177` in `Checkout`
  ```go
  			if err != nil {
  				slog.Error("Billing: failed to get/create customer", "error", err)
  				respondWithError(w, http.StatusInternalServerError, "Failed to create billing session")
  				return
  			}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/billing.go:210` in `Checkout`
  ```go
  				if err != nil {
  					slog.Error("Billing: failed to create base price", "error", err)
  					respondWithError(w, http.StatusInternalServerError, "Failed to create billing session")
  					return
  				}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/billing.go:223` in `Checkout`
  ```go
  					if err != nil {
  						slog.Error("Billing: failed to create seat price", "error", err)
  						respondWithError(w, http.StatusInternalServerError, "Failed to create billing session")
  						return
  					}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/billing.go:245` in `Checkout`
  ```go
  			if err != nil {
  				slog.Error("Billing: failed to create checkout session", "error", err)
  				respondWithError(w, http.StatusInternalServerError, "Failed to create billing session")
  				return
  			}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/billing.go:269` in `Checkout`
  ```go
  		if err != nil {
  			slog.Error("Billing: failed to get/create customer", "error", err)
  			respondWithError(w, http.StatusInternalServerError, "Failed to create billing session")
  			return
  		}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/billing.go:287` in `Checkout`
  ```go
  		if err != nil {
  			slog.Error("Billing: failed to create checkout session", "error", err)
  			respondWithError(w, http.StatusInternalServerError, "Failed to create billing session")
  			return
  		}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/billing.go:299` in `Checkout`
  ```go
  		if err != nil {
  			respondWithError(w, http.StatusBadRequest, "Invalid bundle ID")
  			return
  		}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/billing.go:316` in `Checkout`
  ```go
  		if err != nil {
  			slog.Error("Billing: failed to get/create customer", "error", err)
  			respondWithError(w, http.StatusInternalServerError, "Failed to create billing session")
  			return
  		}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/billing.go:332` in `Checkout`
  ```go
  		if err != nil {
  			slog.Error("Billing: failed to create checkout session", "error", err)
  			respondWithError(w, http.StatusInternalServerError, "Failed to create billing session")
  			return
  		}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/billing.go:365` in `Portal`
  ```go
  	if err != nil {
  		slog.Error("Billing: failed to create portal session", "error", err)
  		respondWithError(w, http.StatusInternalServerError, "Failed to create portal session")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/billing.go:403` in `ListTransactions`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to fetch transactions")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/billing.go:410` in `ListTransactions`
  ```go
  	if err := cursor.All(ctx, &transactions); err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to decode transactions")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/billing.go:436` in `GetInvoice`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid transaction ID")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/billing.go:465` in `GetInvoicePDF`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid transaction ID")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/billing.go:593` in `GetInvoicePDF`
  ```go
  	if err := pdf.Output(&buf); err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to generate PDF")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/billing.go:624` in `CancelSubscription`
  ```go
  	if err != nil {
  		slog.Error("Billing: failed to cancel subscription", "error", err)
  		respondWithError(w, http.StatusInternalServerError, "Failed to cancel subscription")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/billing.go:722` in `AdminListTransactions`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to fetch transactions")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/billing.go:729` in `AdminListTransactions`
  ```go
  	if err := cursor.All(ctx, &transactions); err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to decode transactions")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/billing.go:779` in `AdminGetMetrics`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to fetch metrics")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/billing.go:786` in `AdminGetMetrics`
  ```go
  	if err := cursor.All(ctx, &metrics); err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to decode metrics")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/billing.go:920` in `AdminCancelSubscription`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid tenant ID")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/billing.go:939` in `AdminCancelSubscription`
  ```go
  	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid request body")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/billing.go:951` in `AdminCancelSubscription`
  ```go
  		if err := h.stripe.CancelSubscriptionImmediately(ctx, tenant.StripeSubscriptionID); err != nil {
  			slog.Error("Admin: failed to cancel subscription immediately", "error", err)
  			respondWithError(w, http.StatusInternalServerError, "Failed to cancel subscription")
  			return
  		}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/billing.go:959` in `AdminCancelSubscription`
  ```go
  		if err != nil {
  			slog.Error("Admin: failed to cancel subscription", "error", err)
  			respondWithError(w, http.StatusInternalServerError, "Failed to cancel subscription")
  			return
  		}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/billing.go:983` in `AdminUpdateSubscription`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid tenant ID")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/billing.go:991` in `AdminUpdateSubscription`
  ```go
  	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid request body")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/billing.go:1002` in `AdminUpdateSubscription`
  ```go
  	if err != nil || result.MatchedCount == 0 {
  		respondWithError(w, http.StatusNotFound, "Tenant not found")
  		return
  	}
  ```

### `internal/api/handlers/branding.go`

- **[HIGH] Missing error check** — `internal/api/handlers/branding.go:129` in `ServeAsset`
  - _statement-form call to known error-returning 'w.Write()'_
  ```go
  	w.Write(asset.Data)
  ```
- **[HIGH] Missing error check** — `internal/api/handlers/branding.go:148` in `ServeMedia`
  - _statement-form call to known error-returning 'w.Write()'_
  ```go
  	w.Write(asset.Data)
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/branding.go:48` in `GetBranding`
  ```go
  	} else if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to load branding config")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/branding.go:122` in `ServeAsset`
  ```go
  	} else if err != nil {
  		http.Error(w, "Internal Server Error", http.StatusInternalServerError)
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/branding.go:141` in `ServeMedia`
  ```go
  	} else if err != nil {
  		http.Error(w, "Internal Server Error", http.StatusInternalServerError)
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/branding.go:160` in `GetPublicPage`
  ```go
  	} else if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to load page")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/branding.go:176` in `ListPublicPages`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to list pages")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/branding.go:181` in `ListPublicPages`
  ```go
  	if err := cursor.All(r.Context(), &pages); err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to decode pages")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/branding.go:196` in `UpdateBranding`
  ```go
  	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid JSON")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/branding.go:256` in `UpdateBranding`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to update branding config")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/branding.go:267` in `UploadAsset`
  ```go
  	if err := r.ParseMultipartForm(maxAssetSize); err != nil {
  		respondWithError(w, http.StatusBadRequest, "File too large (max 5MB)")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/branding.go:279` in `UploadAsset`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusBadRequest, "Missing file upload")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/branding.go:286` in `UploadAsset`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to read file")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/branding.go:318` in `UploadAsset`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to save asset")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/branding.go:342` in `DeleteAsset`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to delete asset")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/branding.go:362` in `ListMedia`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to list media")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/branding.go:367` in `ListMedia`
  ```go
  	if err := cursor.All(r.Context(), &assets); err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to decode media")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/branding.go:402` in `UploadMedia`
  ```go
  	if err := r.ParseMultipartForm(maxMediaSize); err != nil {
  		respondWithError(w, http.StatusBadRequest, "File too large (max 10MB)")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/branding.go:408` in `UploadMedia`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusBadRequest, "Missing file upload")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/branding.go:415` in `UploadMedia`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to read file")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/branding.go:454` in `UploadMedia`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to save media")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/branding.go:481` in `DeleteMedia`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to delete media")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/branding.go:499` in `AdminListPages`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to list pages")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/branding.go:504` in `AdminListPages`
  ```go
  	if err := cursor.All(r.Context(), &pages); err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to decode pages")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/branding.go:517` in `CreatePage`
  ```go
  	if err := json.NewDecoder(r.Body).Decode(&page); err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid JSON")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/branding.go:537` in `CreatePage`
  ```go
  	if err != nil {
  		if mongo.IsDuplicateKeyError(err) {
  			respondWithError(w, http.StatusConflict, "A page with this slug already exists")
  			return
  		}
  		respondWithError(w, http.StatusInternalServerError, "Failed to create page")
  ... (2 more lines)
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/branding.go:553` in `UpdatePage`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid page ID")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/branding.go:559` in `UpdatePage`
  ```go
  	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid JSON")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/branding.go:584` in `UpdatePage`
  ```go
  	if err != nil {
  		if mongo.IsDuplicateKeyError(err) {
  			respondWithError(w, http.StatusConflict, "A page with this slug already exists")
  			return
  		}
  		respondWithError(w, http.StatusInternalServerError, "Failed to update page")
  ... (2 more lines)
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/branding.go:604` in `DeletePage`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid page ID")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/branding.go:610` in `DeletePage`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to delete page")
  		return
  	}
  ```

### `internal/api/handlers/bundles.go`

- **[HIGH] Ignored error (`_`)** — `internal/api/handlers/bundles.go:75` in `ListBundles`
  - _error explicitly discarded with `_`_
  ```go
  	total, _ := h.db.CreditBundles().CountDocuments(r.Context(), bson.M{})
  ```
- **[HIGH] Ignored error (`_`)** — `internal/api/handlers/bundles.go:92` in `CreateBundle`
  - _error explicitly discarded with `_`_
  ```go
  	count, _ := h.db.CreditBundles().CountDocuments(r.Context(), bson.M{"name": req.Name})
  ```
- **[HIGH] Ignored error (`_`)** — `internal/api/handlers/bundles.go:158` in `UpdateBundle`
  - _error explicitly discarded with `_`_
  ```go
  		count, _ := h.db.CreditBundles().CountDocuments(r.Context(), bson.M{"name": req.Name, "_id": bson.M{"$ne": bundleID}})
  ```
- **[HIGH] Missing error check** — `internal/api/handlers/bundles.go:184` in `UpdateBundle`
  - _statement-form call to known error-returning 'h.db.CreditBundles().FindOne(r.Context(), bson.M{"_id": bundleID}).Decode()'_
  ```go
  	h.db.CreditBundles().FindOne(r.Context(), bson.M{"_id": bundleID}).Decode(&updated)
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/bundles.go:61` in `ListBundles`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to list credit bundles")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/bundles.go:68` in `ListBundles`
  ```go
  	if err := cursor.All(r.Context(), &bundles); err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to decode credit bundles")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/bundles.go:82` in `CreateBundle`
  ```go
  	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid request body")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/bundles.go:86` in `CreateBundle`
  ```go
  	if err := validateBundleRequest(&req); err != nil {
  		respondWithError(w, http.StatusBadRequest, err.Error())
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/bundles.go:110` in `CreateBundle`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to create credit bundle")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/bundles.go:131` in `UpdateBundle`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid bundle ID")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/bundles.go:147` in `UpdateBundle`
  ```go
  	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid request body")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/bundles.go:151` in `UpdateBundle`
  ```go
  	if err := validateBundleRequest(&req); err != nil {
  		respondWithError(w, http.StatusBadRequest, err.Error())
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/bundles.go:174` in `UpdateBundle`
  ```go
  	if _, err := h.db.CreditBundles().UpdateByID(r.Context(), bundleID, update); err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to update credit bundle")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/bundles.go:191` in `DeleteBundle`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid bundle ID")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/bundles.go:222` in `ListBundlesPublic`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to list credit bundles")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/bundles.go:229` in `ListBundlesPublic`
  ```go
  	if err := cursor.All(r.Context(), &bundles); err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to decode credit bundles")
  		return
  	}
  ```

### `internal/api/handlers/config.go`

- **[HIGH] Ignored error (`_`)** — `internal/api/handlers/config.go:107` in `UpdateConfig`
  - _error explicitly discarded with `_`_
  ```go
  	updated, _ := h.store.GetVar(name)
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/config.go:66` in `UpdateConfig`
  ```go
  	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid request body")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/config.go:77` in `UpdateConfig`
  ```go
  	if err := configstore.ValidateValue(v.Type, req.Value, effectiveOptions); err != nil {
  		respondWithError(w, http.StatusBadRequest, err.Error())
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/config.go:95` in `UpdateConfig`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to update config variable")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/config.go:100` in `UpdateConfig`
  ```go
  	if err := h.store.Reload(r.Context(), name); err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Updated but failed to reload cache")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/config.go:120` in `CreateConfig`
  ```go
  	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid request body")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/config.go:134` in `CreateConfig`
  ```go
  	if err := configstore.ValidateValue(req.Type, req.Value, req.Options); err != nil {
  		respondWithError(w, http.StatusBadRequest, err.Error())
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/config.go:158` in `CreateConfig`
  ```go
  	if _, err := h.db.ConfigVars().InsertOne(r.Context(), v); err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to create config variable")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/config.go:163` in `CreateConfig`
  ```go
  	if err := h.store.Reload(r.Context(), req.Name); err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Created but failed to reload cache")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/config.go:194` in `DeleteConfig`
  ```go
  	if err := h.store.Load(r.Context()); err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Deleted but failed to reload cache")
  		return
  	}
  ```

### `internal/api/handlers/docs.go`

- **[HIGH] Missing error check** — `internal/api/handlers/docs.go:1102` in `DocsHTML`
  - _statement-form call to known error-returning 'w.Write()'_
  ```go
  	w.Write([]byte(sb.String()))
  ```
- **[HIGH] Missing error check** — `internal/api/handlers/docs.go:1177` in `DocsMarkdown`
  - _statement-form call to known error-returning 'w.Write()'_
  ```go
  	w.Write([]byte(sb.String()))
  ```

### `internal/api/handlers/event_definitions.go`

- **[HIGH] Ignored error (`_`)** — `internal/api/handlers/event_definitions.go:134` in `CreateEventDefinition`
  - _error explicitly discarded with `_`_
  ```go
  	count, _ := h.db.EventDefinitions().CountDocuments(ctx, bson.M{"name": req.Name})
  ```
- **[HIGH] Ignored error (`_`)** — `internal/api/handlers/event_definitions.go:156` in `CreateEventDefinition`
  - _error explicitly discarded with `_`_
  ```go
  		count, _ := h.db.EventDefinitions().CountDocuments(ctx, bson.M{"_id": parentID})
  ```
- **[HIGH] Ignored error (`_`)** — `internal/api/handlers/event_definitions.go:210` in `UpdateEventDefinition`
  - _error explicitly discarded with `_`_
  ```go
  		count, _ := h.db.EventDefinitions().CountDocuments(ctx, bson.M{"name": req.Name, "_id": bson.M{"$ne": defID}})
  ```
- **[HIGH] Ignored error (`_`)** — `internal/api/handlers/event_definitions.go:236` in `UpdateEventDefinition`
  - _error explicitly discarded with `_`_
  ```go
  		count, _ := h.db.EventDefinitions().CountDocuments(ctx, bson.M{"_id": parentID})
  ```
- **[HIGH] Missing error check** — `internal/api/handlers/event_definitions.go:261` in `UpdateEventDefinition`
  - _statement-form call to known error-returning 'h.db.EventDefinitions().FindOne(ctx, bson.M{"_id": defID}).Decode()'_
  ```go
  	h.db.EventDefinitions().FindOne(ctx, bson.M{"_id": defID}).Decode(&updated)
  ```
- **[HIGH] Swallowed error** — `internal/api/handlers/event_definitions.go:444` in `wouldCreateCycle`
  ```go
  		if err != nil || parent.ParentID == nil {
  			return false
  		}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/event_definitions.go:50` in `ListEventDefinitions`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to list event definitions")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/event_definitions.go:57` in `ListEventDefinitions`
  ```go
  	if err := cursor.All(ctx, &defs); err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to decode event definitions")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/event_definitions.go:114` in `CreateEventDefinition`
  ```go
  	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid request body")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/event_definitions.go:151` in `CreateEventDefinition`
  ```go
  		if err != nil {
  			respondWithError(w, http.StatusBadRequest, "Invalid parent ID")
  			return
  		}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/event_definitions.go:164` in `CreateEventDefinition`
  ```go
  	if _, err := h.db.EventDefinitions().InsertOne(ctx, def); err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to create event definition")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/event_definitions.go:176` in `UpdateEventDefinition`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid definition ID")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/event_definitions.go:182` in `UpdateEventDefinition`
  ```go
  	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid request body")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/event_definitions.go:227` in `UpdateEventDefinition`
  ```go
  		if err != nil {
  			respondWithError(w, http.StatusBadRequest, "Invalid parent ID")
  			return
  		}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/event_definitions.go:268` in `DeleteEventDefinition`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid definition ID")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/event_definitions.go:302` in `GetSankeyData`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to load event definitions")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/event_definitions.go:309` in `GetSankeyData`
  ```go
  	if err := cursor.All(ctx, &allDefs); err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to decode event definitions")
  		return
  	}
  ```

### `internal/api/handlers/health.go`

- **[HIGH] Swallowed error** — `internal/api/handlers/health.go:135` in `SendTestEmail`
  ```go
  	if err := h.emailService.SendEmail(req.To, subject, body); err != nil {
  		respondWithJSON(w, http.StatusOK, map[string]interface{}{
  			"success": false,
  			"error":   err.Error(),
  		})
  		return
  ... (1 more lines)
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/health.go:30` in `ListNodes`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to list nodes")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/health.go:58` in `GetMetrics`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to query metrics")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/health.go:75` in `GetCurrent`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to get current metrics")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/health.go:116` in `SendTestEmail`
  ```go
  	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid request body")
  		return
  	}
  ```

### `internal/api/handlers/helpers.go`

- **[HIGH] Missing error check** — `internal/api/handlers/helpers.go:25` in `respondWithJSON`
  - _statement-form call to known error-returning 'json.NewEncoder(w).Encode()'_
  ```go
  	json.NewEncoder(w).Encode(payload)
  ```
- **[MEDIUM] Panic on error** — `internal/api/handlers/helpers.go:34` in `generateRandomToken`
  ```go
  	if _, err := rand.Read(b); err != nil {
  		panic("crypto/rand failed: " + err.Error())
  	}
  ```

### `internal/api/handlers/logs.go`

- **[HIGH] Ignored error (`_`)** — `internal/api/handlers/logs.go:93` in `ListLogs`
  - _error explicitly discarded with `_`_
  ```go
  	page, _ := strconv.Atoi(q.Get("page"))
  ```
- **[HIGH] Ignored error (`_`)** — `internal/api/handlers/logs.go:97` in `ListLogs`
  - _error explicitly discarded with `_`_
  ```go
  	perPage, _ := strconv.Atoi(q.Get("perPage"))
  ```
- **[HIGH] Missing error check** — `internal/api/handlers/logs.go:206` in `ExportCSV`
  - _statement-form call to known error-returning 'writer.Write()'_
  ```go
  	writer.Write([]string{"Timestamp", "Severity", "Category", "Message", "UserID", "TenantID", "Action"})
  ```
- **[HIGH] Swallowed error** — `internal/api/handlers/logs.go:210` in `ExportCSV`
  ```go
  		if err := cursor.Decode(&log); err != nil {
  			continue
  		}
  ```
- **[HIGH] Missing error check** — `internal/api/handlers/logs.go:231` in `ExportCSV`
  - _statement-form call to known error-returning 'writer.Flush()'_
  ```go
  	writer.Flush()
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/logs.go:114` in `ListLogs`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to count logs")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/logs.go:125` in `ListLogs`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to query logs")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/logs.go:132` in `ListLogs`
  ```go
  	if err := cursor.All(ctx, &logs); err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to read logs")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/logs.go:156` in `SeverityCounts`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to aggregate severity counts")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/logs.go:167` in `SeverityCounts`
  ```go
  	if err := cursor.All(r.Context(), &results); err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to read severity counts")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/logs.go:196` in `ExportCSV`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to query logs")
  		return
  	}
  ```

### `internal/api/handlers/messages.go`

- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/messages.go:38` in `ListMessages`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to fetch messages")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/messages.go:45` in `ListMessages`
  ```go
  	if err := cursor.All(r.Context(), &messages); err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to decode messages")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/messages.go:66` in `UnreadCount`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to count messages")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/messages.go:83` in `MarkRead`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid message ID")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/messages.go:91` in `MarkRead`
  ```go
  	if err != nil || result.MatchedCount == 0 {
  		respondWithError(w, http.StatusNotFound, "Message not found")
  		return
  	}
  ```

### `internal/api/handlers/openapi.go`

- **[HIGH] Missing error check** — `internal/api/handlers/openapi.go:166` in `DocsOpenAPI`
  - _statement-form call to known error-returning 'json.Unmarshal()'_
  ```go
  				json.Unmarshal([]byte(ep.Body), &bodyExample)
  ```
- **[HIGH] Missing error check** — `internal/api/handlers/openapi.go:180` in `DocsOpenAPI`
  - _statement-form call to known error-returning 'json.Unmarshal()'_
  ```go
  				json.Unmarshal([]byte(ep.Response), &respExample)
  ```
- **[HIGH] Missing error check** — `internal/api/handlers/openapi.go:211` in `DocsOpenAPI`
  - _statement-form call to known error-returning 'enc.Encode()'_
  ```go
  	enc.Encode(spec)
  ```

### `internal/api/handlers/plans.go`

- **[HIGH] Ignored error (`_`)** — `internal/api/handlers/plans.go:93` in `ListPlans`
  - _error explicitly discarded with `_`_
  ```go
  	total, _ := h.db.Plans().CountDocuments(ctx, bson.M{})
  ```
- **[HIGH] Swallowed error** — `internal/api/handlers/plans.go:139` in `ListEntitlementKeys`
  ```go
  		if err := cursor.Decode(&plan); err != nil {
  			continue
  		}
  ```
- **[HIGH] Ignored error (`_`)** — `internal/api/handlers/plans.go:248` in `CreatePlan`
  - _error explicitly discarded with `_`_
  ```go
  	count, _ := h.db.Plans().CountDocuments(r.Context(), bson.M{"name": req.Name})
  ```
- **[HIGH] Ignored error (`_`)** — `internal/api/handlers/plans.go:341` in `UpdatePlan`
  - _error explicitly discarded with `_`_
  ```go
  		count, _ := h.db.Plans().CountDocuments(r.Context(), bson.M{"name": req.Name, "_id": bson.M{"$ne": planID}})
  ```
- **[HIGH] Missing error check** — `internal/api/handlers/plans.go:391` in `UpdatePlan`
  - _statement-form call to known error-returning 'h.db.Plans().FindOne(r.Context(), bson.M{"_id": planID}).Decode()'_
  ```go
  	h.db.Plans().FindOne(r.Context(), bson.M{"_id": planID}).Decode(&updated)
  ```
- **[HIGH] Ignored error (`_`)** — `internal/api/handlers/plans.go:392` in `UpdatePlan`
  - _error explicitly discarded with `_`_
  ```go
  	subCount, _ := h.db.Tenants().CountDocuments(r.Context(), bson.M{"planId": planID})
  ```
- **[HIGH] Ignored error (`_`)** — `internal/api/handlers/plans.go:440` in `DeletePlan`
  - _error explicitly discarded with `_`_
  ```go
  	tenantCount, _ := h.db.Tenants().CountDocuments(r.Context(), bson.M{"planId": planID})
  ```
- **[HIGH] Missing error check** — `internal/api/handlers/plans.go:481` in `ArchivePlan`
  - _statement-form call to known error-returning 'h.db.Plans().UpdateByID()'_
  ```go
  	h.db.Plans().UpdateByID(r.Context(), planID, bson.M{"$set": bson.M{"isArchived": true, "updatedAt": time.Now()}})
  ```
- **[HIGH] Missing error check** — `internal/api/handlers/plans.go:513` in `UnarchivePlan`
  - _statement-form call to known error-returning 'h.db.Plans().UpdateByID()'_
  ```go
  	h.db.Plans().UpdateByID(r.Context(), planID, bson.M{"$set": bson.M{"isArchived": false, "updatedAt": time.Now()}})
  ```
- **[HIGH] Ignored error (`_`)** — `internal/api/handlers/plans.go:684` in `ListPlansPublic`
  - _error explicitly discarded with `_`_
  ```go
  	memberCount, _ := h.db.TenantMemberships().CountDocuments(r.Context(), bson.M{
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/plans.go:49` in `ListPlans`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to list plans")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/plans.go:56` in `ListPlans`
  ```go
  	if err := cursor.All(ctx, &plans); err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to decode plans")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/plans.go:100` in `GetPlan`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid plan ID")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/plans.go:120` in `ListEntitlementKeys`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to list plans")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/plans.go:238` in `CreatePlan`
  ```go
  	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid request body")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/plans.go:242` in `CreatePlan`
  ```go
  	if err := validatePlanRequest(&req); err != nil {
  		respondWithError(w, http.StatusBadRequest, err.Error())
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/plans.go:281` in `CreatePlan`
  ```go
  	if err := validation.Validate(&plan); err != nil {
  		respondWithError(w, http.StatusBadRequest, err.Error())
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/plans.go:287` in `CreatePlan`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to create plan")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/plans.go:308` in `UpdatePlan`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid plan ID")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/plans.go:324` in `UpdatePlan`
  ```go
  	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid request body")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/plans.go:328` in `UpdatePlan`
  ```go
  	if err := validatePlanRequest(&req); err != nil {
  		respondWithError(w, http.StatusBadRequest, err.Error())
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/plans.go:380` in `UpdatePlan`
  ```go
  	if _, err := h.db.Plans().UpdateByID(r.Context(), planID, update); err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to update plan")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/plans.go:420` in `DeletePlan`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid plan ID")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/plans.go:461` in `ArchivePlan`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid plan ID")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/plans.go:493` in `UnarchivePlan`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid plan ID")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/plans.go:530` in `AssignPlan`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid tenant ID")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/plans.go:539` in `AssignPlan`
  ```go
  	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid request body")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/plans.go:563` in `AssignPlan`
  ```go
  			if err != nil {
  				respondWithError(w, http.StatusBadRequest, "Invalid plan ID")
  				return
  			}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/plans.go:622` in `AssignPlan`
  ```go
  				if err := h.stripe.CancelSubscriptionImmediately(ctx, tenant.StripeSubscriptionID); err != nil {
  					slog.Error("AssignPlan: failed to cancel subscription", "tenant", tenant.Name, "error", err)
  					respondWithError(w, http.StatusInternalServerError, "Failed to cancel existing subscription")
  					return
  				}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/plans.go:641` in `AssignPlan`
  ```go
  	if _, err := h.db.Tenants().UpdateByID(ctx, tenantID, update); err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to assign plan")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/plans.go:667` in `ListPlansPublic`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid tenant ID")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/plans.go:704` in `ListPlansPublic`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to list plans")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/plans.go:711` in `ListPlansPublic`
  ```go
  	if err := cursor.All(r.Context(), &plans); err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to decode plans")
  		return
  	}
  ```

### `internal/api/handlers/pm.go`

- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/pm.go:50` in `GetFunnel`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to compute funnel metrics")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/pm.go:70` in `GetRetention`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to compute retention data")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/pm.go:85` in `GetEngagement`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to compute engagement metrics")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/pm.go:95` in `GetKPIs`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to compute KPIs")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/pm.go:107` in `GetCustomEvents`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to compute custom event data")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/pm.go:117` in `ListEventTypes`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to list event types")
  		return
  	}
  ```

### `internal/api/handlers/promotions.go`

- **[HIGH] Swallowed error** — `internal/api/handlers/promotions.go:116` in `buildProductNameMap`
  ```go
  	if err != nil {
  		return nameMap
  	}
  ```
- **[HIGH] Swallowed error** — `internal/api/handlers/promotions.go:122` in `buildProductNameMap`
  ```go
  	if err := cursor.All(ctx, &mappings); err != nil {
  		return nameMap
  	}
  ```
- **[HIGH] Ignored error (`_`)** — `internal/api/handlers/promotions.go:144` in `buildProductNameMap`
  - _error explicitly discarded with `_`_
  ```go
  		cur, _ := h.db.Plans().Find(ctx, bson.M{"_id": bson.M{"$in": ids}})
  ```
- **[HIGH] Missing error check** — `internal/api/handlers/promotions.go:151` in `buildProductNameMap`
  - _statement-form call to known error-returning 'cur.Close()'_
  ```go
  			cur.Close(ctx)
  ```
- **[HIGH] Ignored error (`_`)** — `internal/api/handlers/promotions.go:162` in `buildProductNameMap`
  - _error explicitly discarded with `_`_
  ```go
  		cur, _ := h.db.CreditBundles().Find(ctx, bson.M{"_id": bson.M{"$in": ids}})
  ```
- **[HIGH] Missing error check** — `internal/api/handlers/promotions.go:169` in `buildProductNameMap`
  - _statement-form call to known error-returning 'cur.Close()'_
  ```go
  			cur.Close(ctx)
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/promotions.go:91` in `ListPromotions`
  ```go
  	if err := iter.Err(); err != nil {
  		slog.Error("Promotions: list error", "error", err)
  		respondWithError(w, http.StatusInternalServerError, "Failed to list promotion codes")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/promotions.go:195` in `ListEligibleProducts`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to list plans")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/promotions.go:209` in `ListEligibleProducts`
  ```go
  	if err := planCursor.All(ctx, &plans); err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to read plans")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/promotions.go:221` in `ListEligibleProducts`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to list bundles")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/promotions.go:228` in `ListEligibleProducts`
  ```go
  	if err := bundleCursor.All(ctx, &bundles); err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to read bundles")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/promotions.go:258` in `CreatePromotion`
  ```go
  	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid request body")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/promotions.go:283` in `CreatePromotion`
  ```go
  			if err != nil {
  				respondWithError(w, http.StatusBadRequest, "Invalid product ID: "+item.ID)
  				return
  			}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/promotions.go:289` in `CreatePromotion`
  ```go
  			if err != nil {
  				slog.Warn("Failed to resolve Stripe product", "type", item.Type, "id", item.ID, "error", err)
  			respondWithError(w, http.StatusInternalServerError, "Failed to resolve Stripe product")
  				return
  			}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/promotions.go:325` in `CreatePromotion`
  ```go
  	if err != nil {
  		slog.Error("Promotions: coupon create error", "error", err)
  		respondWithError(w, http.StatusInternalServerError, "Failed to create coupon")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/promotions.go:343` in `CreatePromotion`
  ```go
  		if err != nil {
  			respondWithError(w, http.StatusBadRequest, "Invalid expiration date format (use YYYY-MM-DD)")
  			return
  		}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/promotions.go:354` in `CreatePromotion`
  ```go
  	if err != nil {
  		slog.Error("Promotions: promo code create error", "error", err)
  		respondWithError(w, http.StatusInternalServerError, "Failed to create promotion code")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/promotions.go:453` in `UpdatePromotion`
  ```go
  	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid request body")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/promotions.go:468` in `UpdatePromotion`
  ```go
  		if err != nil {
  			slog.Error("Promotions: coupon update error", "error", err)
  			respondWithError(w, http.StatusInternalServerError, "Failed to update coupon name")
  			return
  		}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/promotions.go:481` in `UpdatePromotion`
  ```go
  		if err != nil {
  			slog.Error("Promotions: promo code update error", "error", err)
  			respondWithError(w, http.StatusInternalServerError, "Failed to update promotion code")
  			return
  		}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/promotions.go:496` in `DeactivatePromotion`
  ```go
  	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid request body")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/promotions.go:509` in `DeactivatePromotion`
  ```go
  	if err != nil {
  		slog.Error("Promotions: deactivate error", "error", err)
  		respondWithError(w, http.StatusInternalServerError, "Failed to deactivate promotion code")
  		return
  	}
  ```
- **[LOW] Proper handling** — `internal/api/handlers/promotions.go:406` in `resolveStripeProducts`
  ```go
  			if err != nil {
  				return nil, err
  			}
  ```
- **[LOW] Proper handling** — `internal/api/handlers/promotions.go:427` in `resolveStripeProducts`
  ```go
  		if err != nil {
  			return nil, err
  		}
  ```

### `internal/api/handlers/telemetry.go`

- **[HIGH] Ignored error (`_`)** — `internal/api/handlers/telemetry.go:113` in `TrackAuthenticated`
  - _error explicitly discarded with `_`_
  ```go
  	tenant, _ := middleware.GetTenantFromContext(r.Context())
  ```
- **[HIGH] Ignored error (`_`)** — `internal/api/handlers/telemetry.go:167` in `TrackBatch`
  - _error explicitly discarded with `_`_
  ```go
  	tenant, _ := middleware.GetTenantFromContext(r.Context())
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/telemetry.go:68` in `TrackAnonymous`
  ```go
  	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid request body")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/telemetry.go:97` in `TrackAnonymous`
  ```go
  	if err := h.telemetry.Track(r.Context(), event); err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to track event")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/telemetry.go:119` in `TrackAuthenticated`
  ```go
  	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid request body")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/telemetry.go:151` in `TrackAuthenticated`
  ```go
  	if err := h.telemetry.Track(r.Context(), event); err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to track event")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/telemetry.go:175` in `TrackBatch`
  ```go
  	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid request body")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/telemetry.go:220` in `TrackBatch`
  ```go
  	if err := h.telemetry.TrackBatch(r.Context(), events); err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to track events")
  		return
  	}
  ```

### `internal/api/handlers/tenant.go`

- **[HIGH] Ignored error (`_`)** — `internal/api/handlers/tenant.go:172` in `InviteMember`
  - _error explicitly discarded with `_`_
  ```go
  		count, _ := h.db.TenantMemberships().CountDocuments(r.Context(), bson.M{
  ```
- **[HIGH] Ignored error (`_`)** — `internal/api/handlers/tenant.go:183` in `InviteMember`
  - _error explicitly discarded with `_`_
  ```go
  	count, _ := h.db.Invitations().CountDocuments(r.Context(), bson.M{
  ```
- **[HIGH] Missing error check** — `internal/api/handlers/tenant.go:197` in `InviteMember`
  - _statement-form call to known error-returning 'h.db.Plans().FindOne(r.Context(), bson.M{"_id": *tenant.PlanID}).Decode()'_
  ```go
  		h.db.Plans().FindOne(r.Context(), bson.M{"_id": *tenant.PlanID}).Decode(&tenantPlan)
  ```
- **[HIGH] Missing error check** — `internal/api/handlers/tenant.go:199` in `InviteMember`
  - _statement-form call to known error-returning 'h.db.Plans().FindOne(r.Context(), bson.M{"isSystem": true}).Decode()'_
  ```go
  		h.db.Plans().FindOne(r.Context(), bson.M{"isSystem": true}).Decode(&tenantPlan)
  ```
- **[HIGH] Ignored error (`_`)** — `internal/api/handlers/tenant.go:224` in `InviteMember`
  - _error explicitly discarded with `_`_
  ```go
  		memberCount, _ := h.db.TenantMemberships().CountDocuments(r.Context(), bson.M{"tenantId": tenant.ID})
  ```
- **[HIGH] Ignored error (`_`)** — `internal/api/handlers/tenant.go:225` in `InviteMember`
  - _error explicitly discarded with `_`_
  ```go
  		pendingCount, _ := h.db.Invitations().CountDocuments(r.Context(), bson.M{
  ```
- **[HIGH] Missing error check** — `internal/api/handlers/tenant.go:232` in `InviteMember`
  - _statement-form call to known error-returning 'h.db.Invitations().DeleteOne()'_
  ```go
  			h.db.Invitations().DeleteOne(r.Context(), bson.M{"_id": invitation.ID})
  ```
- **[HIGH] Ignored error (`_`)** — `internal/api/handlers/tenant.go:249` in `InviteMember`
  - _error explicitly discarded with `_`_
  ```go
  		memberCount, _ := h.db.TenantMemberships().CountDocuments(r.Context(), bson.M{"tenantId": tenant.ID})
  ```
- **[HIGH] Swallowed error** — `internal/api/handlers/tenant.go:254` in `InviteMember`
  ```go
  		if err := h.stripe.UpdateSubscriptionQuantity(r.Context(), tenant.StripeSubscriptionID, int64(newSeats)); err != nil {
  			slog.Error("Failed to update seat quantity", "tenantId", tenant.ID.Hex(), "error", err)
  		} else {
  ```
- **[HIGH] Missing error check** — `internal/api/handlers/tenant.go:257` in `InviteMember`
  - _statement-form call to known error-returning 'h.db.Tenants().UpdateOne()'_
  ```go
  			h.db.Tenants().UpdateOne(r.Context(), bson.M{"_id": tenant.ID}, bson.M{"$set": bson.M{"seatQuantity": newSeats, "updatedAt": time.Now()}})
  ```
- **[HIGH] Ignored error (`_`)** — `internal/api/handlers/tenant.go:345` in `RemoveMember`
  - _error explicitly discarded with `_`_
  ```go
  			memberCount, _ := h.db.TenantMemberships().CountDocuments(r.Context(), bson.M{"tenantId": tenant.ID})
  ```
- **[HIGH] Swallowed error** — `internal/api/handlers/tenant.go:353` in `RemoveMember`
  ```go
  			if err := h.stripe.UpdateSubscriptionQuantity(r.Context(), tenant.StripeSubscriptionID, int64(newSeats)); err != nil {
  				slog.Error("Failed to update seat quantity", "tenant", tenant.ID.Hex(), "error", err)
  			} else {
  ```
- **[HIGH] Missing error check** — `internal/api/handlers/tenant.go:356` in `RemoveMember`
  - _statement-form call to known error-returning 'h.db.Tenants().UpdateOne()'_
  ```go
  				h.db.Tenants().UpdateOne(r.Context(), bson.M{"_id": tenant.ID}, bson.M{"$set": bson.M{"seatQuantity": newSeats, "updatedAt": time.Now()}})
  ```
- **[HIGH] Ignored error (`_`)** — `internal/api/handlers/tenant.go:474` in `TransferOwnership`
  - _error explicitly discarded with `_`_
  ```go
  	count, _ := h.db.TenantMemberships().CountDocuments(r.Context(), bson.M{
  ```
- **[HIGH] Ignored error (`_`)** — `internal/api/handlers/tenant.go:568` in `GetActivity`
  - _error explicitly discarded with `_`_
  ```go
  	total, _ := h.db.SystemLogs().CountDocuments(r.Context(), filter)
  ```
- **[HIGH] Missing error check** — `internal/api/handlers/tenant.go:600` in `UpdateTenantSettings`
  - _statement-form call to known error-returning 'h.db.Tenants().UpdateOne()'_
  ```go
  	h.db.Tenants().UpdateOne(r.Context(), bson.M{"_id": tenant.ID}, bson.M{"$set": updates})
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/tenant.go:75` in `ListMembers`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to fetch members")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/tenant.go:82` in `ListMembers`
  ```go
  	if err := cursor.All(r.Context(), &memberships); err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to decode members")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/tenant.go:142` in `InviteMember`
  ```go
  	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid request body")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/tenant.go:219` in `InviteMember`
  ```go
  		if _, err := h.db.Invitations().InsertOne(r.Context(), invitation); err != nil {
  			respondWithError(w, http.StatusInternalServerError, "Failed to create invitation")
  			return
  		}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/tenant.go:241` in `InviteMember`
  ```go
  		if _, err := h.db.Invitations().InsertOne(r.Context(), invitation); err != nil {
  			respondWithError(w, http.StatusInternalServerError, "Failed to create invitation")
  			return
  		}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/tenant.go:267` in `InviteMember`
  ```go
  			if err := h.emailService.SendInvitationEmail(req.Email, user.DisplayName, tenant.Name, token); err != nil {
  				slog.Error("Failed to send invitation email", "to", req.Email, "error", err)
  			}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/tenant.go:303` in `RemoveMember`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid user ID")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/tenant.go:396` in `ChangeRole`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid user ID")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/tenant.go:408` in `ChangeRole`
  ```go
  	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid request body")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/tenant.go:426` in `ChangeRole`
  ```go
  	if err != nil || result.MatchedCount == 0 {
  		respondWithError(w, http.StatusNotFound, "Member not found")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/tenant.go:463` in `TransferOwnership`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid user ID")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/tenant.go:556` in `GetActivity`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to fetch activity")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/tenant.go:563` in `GetActivity`
  ```go
  	if err := cursor.All(r.Context(), &logs); err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to decode activity")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/tenant.go:590` in `UpdateTenantSettings`
  ```go
  	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid request body")
  		return
  	}
  ```

### `internal/api/handlers/usage.go`

- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/usage.go:46` in `RecordUsage`
  ```go
  	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
  		http.Error(w, `{"error":"Invalid request body"}`, http.StatusBadRequest)
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/usage.go:75` in `RecordUsage`
  ```go
  	if err := validation.Validate(&event); err != nil {
  		http.Error(w, fmt.Sprintf(`{"error":%q}`, err.Error()), http.StatusBadRequest)
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/usage.go:81` in `RecordUsage`
  ```go
  	if err != nil {
  		http.Error(w, `{"error":"Failed to start session"}`, http.StatusInternalServerError)
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/usage.go:124` in `RecordUsage`
  ```go
  	if txErr != nil {
  		http.Error(w, `{"error":"Failed to deduct credits"}`, http.StatusInternalServerError)
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/usage.go:170` in `GetSummary`
  ```go
  	if err != nil {
  		http.Error(w, `{"error":"Failed to aggregate usage"}`, http.StatusInternalServerError)
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/usage.go:183` in `GetSummary`
  ```go
  	if err := cursor.All(ctx, &items); err != nil {
  		http.Error(w, `{"error":"Failed to read usage data"}`, http.StatusInternalServerError)
  		return
  	}
  ```
- **[LOW] Proper handling** — `internal/api/handlers/usage.go:94` in `RecordUsage`
  ```go
  		if err != nil {
  			return nil, err
  		}
  ```
- **[LOW] Proper handling** — `internal/api/handlers/usage.go:104` in `RecordUsage`
  ```go
  			if err != nil {
  				return nil, err
  			}
  ```
- **[LOW] Proper handling** — `internal/api/handlers/usage.go:114` in `RecordUsage`
  ```go
  		if _, err := h.db.UsageEvents().InsertOne(sc, event); err != nil {
  			return nil, err
  		}
  ```

### `internal/api/handlers/webhook.go`

- **[HIGH] Ignored error (`_`)** — `internal/api/handlers/webhook.go:152` in `handleCheckoutCompleted`
  - _error explicitly discarded with `_`_
  ```go
  	tenantID, _ := primitive.ObjectIDFromHex(session.Metadata["tenantId"])
  ```
- **[HIGH] Ignored error (`_`)** — `internal/api/handlers/webhook.go:153` in `handleCheckoutCompleted`
  - _error explicitly discarded with `_`_
  ```go
  	userID, _ := primitive.ObjectIDFromHex(session.Metadata["userId"])
  ```
- **[HIGH] Ignored error (`_`)** — `internal/api/handlers/webhook.go:191` in `handleCheckoutCompleted`
  - _error explicitly discarded with `_`_
  ```go
  		planID, _ := primitive.ObjectIDFromHex(planIDStr)
  ```
- **[HIGH] Ignored error (`_`)** — `internal/api/handlers/webhook.go:304` in `handleCheckoutCompleted`
  - _error explicitly discarded with `_`_
  ```go
  		bundleID, _ := primitive.ObjectIDFromHex(bundleIDStr)
  ```
- **[HIGH] Ignored error (`_`)** — `internal/api/handlers/webhook.go:480` in `handleInvoicePaymentFailed`
  - _error explicitly discarded with `_`_
  ```go
  	cursor, _ := h.db.TenantMemberships().Find(ctx, bson.M{"tenantId": tenant.ID})
  ```
- **[HIGH] Missing error check** — `internal/api/handlers/webhook.go:484` in `handleInvoicePaymentFailed`
  - _statement-form call to known error-returning 'cursor.Close()'_
  ```go
  		cursor.Close(ctx)
  ```
- **[HIGH] Swallowed error** — `internal/api/handlers/webhook.go:785` in `recordTransaction`
  ```go
  	if err != nil {
  		slog.Error("Failed to generate invoice number", "error", err)
  		randBytes := make([]byte, 4)
  		rand.Read(randBytes)
  		invoiceNum = fmt.Sprintf("INV-ERR-%d-%s", time.Now().UnixNano(), hex.EncodeToString(randBytes))
  	}
  ```
- **[HIGH] Swallowed error** — `internal/api/handlers/webhook.go:860` in `extractInstanceFromEvent`
  ```go
  	if err := json.Unmarshal(event.Data.Raw, &obj); err == nil && obj.Metadata != nil {
  		if inst, ok := obj.Metadata["instance"]; ok {
  			return inst, true
  		}
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/webhook.go:53` in `HandleWebhook`
  ```go
  	if err != nil {
  		http.Error(w, "read error", http.StatusBadRequest)
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/webhook.go:59` in `HandleWebhook`
  ```go
  	if err != nil {
  		slog.Error("Webhook signature verification failed", "error", err)
  		http.Error(w, "invalid signature", http.StatusBadRequest)
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/webhook.go:130` in `HandleWebhook`
  ```go
  	if processingErr != nil {
  		slog.Error("Webhook: processing failed, removing idempotency record for retry", "eventId", event.ID, "error", processingErr)
  		h.db.WebhookEvents().DeleteOne(ctx, bson.M{"eventId": event.ID})
  		http.Error(w, "processing failed", http.StatusInternalServerError)
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/webhook.go:821` in `recordTransaction`
  ```go
  	if _, err := h.db.FinancialTransactions().InsertOne(ctx, tx); err != nil {
  		slog.Error("Failed to record transaction", "error", err)
  	}
  ```
- **[LOW] Proper handling** — `internal/api/handlers/webhook.go:147` in `handleCheckoutCompleted`
  ```go
  	if err := json.Unmarshal(event.Data.Raw, &session); err != nil {
  		slog.Error("Webhook: failed to unmarshal checkout session", "error", err)
  		return fmt.Errorf("unmarshal checkout session: %w", err)
  	}
  ```
- **[LOW] Proper handling** — `internal/api/handlers/webhook.go:352` in `handleInvoicePaid`
  ```go
  	if err := json.Unmarshal(event.Data.Raw, &invoice); err != nil {
  		slog.Error("Webhook: failed to unmarshal invoice", "error", err)
  		return fmt.Errorf("unmarshal invoice: %w", err)
  	}
  ```
- **[LOW] Proper handling** — `internal/api/handlers/webhook.go:452` in `handleInvoicePaymentFailed`
  ```go
  	if err := json.Unmarshal(event.Data.Raw, &invoice); err != nil {
  		slog.Error("Webhook: failed to unmarshal invoice", "error", err)
  		return fmt.Errorf("unmarshal invoice: %w", err)
  	}
  ```
- **[LOW] Proper handling** — `internal/api/handlers/webhook.go:525` in `handleSubscriptionUpdated`
  ```go
  	if err := json.Unmarshal(event.Data.Raw, &sub); err != nil {
  		slog.Error("Webhook: failed to unmarshal subscription", "error", err)
  		return fmt.Errorf("unmarshal subscription: %w", err)
  	}
  ```
- **[LOW] Proper handling** — `internal/api/handlers/webhook.go:587` in `handleSubscriptionDeleted`
  ```go
  	if err := json.Unmarshal(event.Data.Raw, &sub); err != nil {
  		slog.Error("Webhook: failed to unmarshal subscription", "error", err)
  		return fmt.Errorf("unmarshal subscription: %w", err)
  	}
  ```
- **[LOW] Proper handling** — `internal/api/handlers/webhook.go:645` in `handleChargeRefunded`
  ```go
  	if err := json.Unmarshal(event.Data.Raw, &charge); err != nil {
  		slog.Error("Webhook: failed to unmarshal charge", "error", err)
  		return fmt.Errorf("unmarshal charge: %w", err)
  	}
  ```
- **[LOW] Proper handling** — `internal/api/handlers/webhook.go:691` in `handleDisputeCreated`
  ```go
  	if err := json.Unmarshal(event.Data.Raw, &dispute); err != nil {
  		slog.Error("Webhook: failed to unmarshal dispute", "error", err)
  		return fmt.Errorf("unmarshal dispute: %w", err)
  	}
  ```
- **[LOW] Proper handling** — `internal/api/handlers/webhook.go:737` in `handleDisputeClosed`
  ```go
  	if err := json.Unmarshal(event.Data.Raw, &dispute); err != nil {
  		slog.Error("Webhook: failed to unmarshal dispute", "error", err)
  		return fmt.Errorf("unmarshal dispute: %w", err)
  	}
  ```

### `internal/api/handlers/webhooks.go`

- **[HIGH] Ignored error (`_`)** — `internal/api/handlers/webhooks.go:70` in `ListWebhooks`
  - _error explicitly discarded with `_`_
  ```go
  		count, _ := h.db.WebhookDeliveries().CountDocuments(ctx, bson.M{
  ```
- **[HIGH] Ignored error (`_`)** — `internal/api/handlers/webhooks.go:83` in `ListWebhooks`
  - _error explicitly discarded with `_`_
  ```go
  	total, _ := h.db.Webhooks().CountDocuments(ctx, bson.M{"isActive": true})
  ```
- **[HIGH] Swallowed error** — `internal/api/handlers/webhooks.go:106` in `GetWebhook`
  ```go
  	if err != nil {
  		respondWithJSON(w, http.StatusOK, map[string]interface{}{
  			"webhook":    hook,
  			"deliveries": []models.WebhookDelivery{},
  		})
  		return
  ... (1 more lines)
  ```
- **[HIGH] Swallowed error** — `internal/api/handlers/webhooks.go:116` in `GetWebhook`
  ```go
  	if err := cursor.All(r.Context(), &deliveries); err != nil {
  		deliveries = []models.WebhookDelivery{}
  	}
  ```
- **[HIGH] Swallowed error** — `internal/api/handlers/webhooks.go:138` in `validateWebhookURL`
  ```go
  	if err != nil {
  		return fmt.Errorf("invalid URL format")
  	}
  ```
- **[HIGH] Swallowed error** — `internal/api/handlers/webhooks.go:154` in `validateWebhookURL`
  ```go
  	if err != nil {
  		// If DNS fails, check if host is already an IP
  		ip := net.ParseIP(host)
  		if ip == nil {
  			return fmt.Errorf("cannot resolve hostname")
  		}
  ... (2 more lines)
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/webhooks.go:45` in `ListWebhooks`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to list webhooks")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/webhooks.go:52` in `ListWebhooks`
  ```go
  	if err := cursor.All(ctx, &hooks); err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to decode webhooks")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/webhooks.go:90` in `GetWebhook`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid webhook ID")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/webhooks.go:214` in `CreateWebhook`
  ```go
  	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid request body")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/webhooks.go:219` in `CreateWebhook`
  ```go
  	if err := validateWebhookRequest(&req); err != nil {
  		respondWithError(w, http.StatusBadRequest, err.Error())
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/webhooks.go:241` in `CreateWebhook`
  ```go
  			if err != nil {
  				respondWithError(w, http.StatusInternalServerError, "Failed to secure webhook secret")
  				return
  			}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/webhooks.go:263` in `CreateWebhook`
  ```go
  	if err := validation.Validate(&hook); err != nil {
  		respondWithError(w, http.StatusBadRequest, err.Error())
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/webhooks.go:269` in `CreateWebhook`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusInternalServerError, "Failed to create webhook")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/webhooks.go:288` in `UpdateWebhook`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid webhook ID")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/webhooks.go:294` in `UpdateWebhook`
  ```go
  	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid request body")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/webhooks.go:299` in `UpdateWebhook`
  ```go
  	if err := validateWebhookRequest(&req); err != nil {
  		respondWithError(w, http.StatusBadRequest, err.Error())
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/webhooks.go:318` in `UpdateWebhook`
  ```go
  	if err != nil || result.MatchedCount == 0 {
  		respondWithError(w, http.StatusNotFound, "Webhook not found")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/webhooks.go:340` in `DeleteWebhook`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid webhook ID")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/webhooks.go:348` in `DeleteWebhook`
  ```go
  	if err != nil || result.MatchedCount == 0 {
  		respondWithError(w, http.StatusNotFound, "Webhook not found")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/webhooks.go:363` in `RegenerateSecret`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid webhook ID")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/webhooks.go:374` in `RegenerateSecret`
  ```go
  			if err != nil {
  				respondWithError(w, http.StatusInternalServerError, "Failed to secure webhook secret")
  				return
  			}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/webhooks.go:389` in `RegenerateSecret`
  ```go
  	if err != nil || result.MatchedCount == 0 {
  		respondWithError(w, http.StatusNotFound, "Webhook not found")
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/api/handlers/webhooks.go:404` in `TestWebhook`
  ```go
  	if err != nil {
  		respondWithError(w, http.StatusBadRequest, "Invalid webhook ID")
  		return
  	}
  ```
- **[LOW] Proper handling** — `internal/api/handlers/webhooks.go:197` in `validateWebhookRequest`
  ```go
  	if err := validateWebhookURL(req.URL); err != nil {
  		return err
  	}
  ```

### `internal/apierror/apierror.go`

- **[HIGH] Missing error check** — `internal/apierror/apierror.go:58` in `Write`
  - _statement-form call to known error-returning 'json.NewEncoder(w).Encode()'_
  ```go
  	json.NewEncoder(w).Encode(resp)
  ```

### `internal/auth/github_oauth.go`

- **[HIGH] Swallowed error** — `internal/auth/github_oauth.go:48` in `ExchangeCode`
  ```go
  	if err != nil {
  		return nil, ErrOAuthCodeExchange
  	}
  ```
- **[HIGH] Swallowed error** — `internal/auth/github_oauth.go:58` in `GetUserInfo`
  ```go
  	if err != nil {
  		return nil, ErrOAuthUserInfo
  	}
  ```
- **[HIGH] Swallowed error** — `internal/auth/github_oauth.go:64` in `GetUserInfo`
  ```go
  	if err != nil {
  		return nil, ErrOAuthUserInfo
  	}
  ```
- **[HIGH] Swallowed error** — `internal/auth/github_oauth.go:69` in `GetUserInfo`
  ```go
  	if err := json.Unmarshal(data, &userInfo); err != nil {
  		return nil, ErrOAuthUserInfo
  	}
  ```
- **[LOW] Proper handling** — `internal/auth/github_oauth.go:90` in `getPrimaryEmail`
  ```go
  	if err != nil {
  		return "", err
  	}
  ```
- **[LOW] Proper handling** — `internal/auth/github_oauth.go:96` in `getPrimaryEmail`
  ```go
  	if err != nil {
  		return "", err
  	}
  ```
- **[LOW] Proper handling** — `internal/auth/github_oauth.go:101` in `getPrimaryEmail`
  ```go
  	if err := json.Unmarshal(data, &emails); err != nil {
  		return "", err
  	}
  ```

### `internal/auth/google_oauth.go`

- **[HIGH] Swallowed error** — `internal/auth/google_oauth.go:53` in `ExchangeCode`
  ```go
  	if err != nil {
  		return nil, ErrOAuthCodeExchange
  	}
  ```
- **[HIGH] Swallowed error** — `internal/auth/google_oauth.go:62` in `GetUserInfo`
  ```go
  	if err != nil {
  		return nil, ErrOAuthUserInfo
  	}
  ```
- **[HIGH] Swallowed error** — `internal/auth/google_oauth.go:68` in `GetUserInfo`
  ```go
  	if err != nil {
  		return nil, ErrOAuthUserInfo
  	}
  ```
- **[HIGH] Swallowed error** — `internal/auth/google_oauth.go:73` in `GetUserInfo`
  ```go
  	if err := json.Unmarshal(data, &userInfo); err != nil {
  		return nil, ErrOAuthUserInfo
  	}
  ```

### `internal/auth/jwt.go`

- **[HIGH] Swallowed error** — `internal/auth/jwt.go:137` in `ValidateAccessToken`
  ```go
  	if err != nil {
  		if errors.Is(err, jwt.ErrTokenExpired) {
  			return nil, ErrExpiredToken
  		}
  		return nil, ErrInvalidToken
  	}
  ```
- **[HIGH] Swallowed error** — `internal/auth/jwt.go:157` in `ValidateRefreshToken`
  ```go
  	if err != nil {
  		if errors.Is(err, jwt.ErrTokenExpired) {
  			return nil, ErrExpiredToken
  		}
  		return nil, ErrInvalidToken
  	}
  ```

### `internal/auth/microsoft_oauth.go`

- **[HIGH] Swallowed error** — `internal/auth/microsoft_oauth.go:48` in `ExchangeCode`
  ```go
  	if err != nil {
  		return nil, ErrOAuthCodeExchange
  	}
  ```
- **[HIGH] Swallowed error** — `internal/auth/microsoft_oauth.go:57` in `GetUserInfo`
  ```go
  	if err != nil {
  		return nil, ErrOAuthUserInfo
  	}
  ```
- **[HIGH] Swallowed error** — `internal/auth/microsoft_oauth.go:63` in `GetUserInfo`
  ```go
  	if err != nil {
  		return nil, ErrOAuthUserInfo
  	}
  ```
- **[HIGH] Swallowed error** — `internal/auth/microsoft_oauth.go:68` in `GetUserInfo`
  ```go
  	if err := json.Unmarshal(data, &userInfo); err != nil {
  		return nil, ErrOAuthUserInfo
  	}
  ```

### `internal/auth/password.go`

- **[HIGH] Ignored error (`_`)** — `internal/auth/password.go:44` in `init`
  - _error explicitly discarded with `_`_
  ```go
  	h, _ := bcrypt.GenerateFromPassword([]byte("dummy-timing-safe"), bcryptCost)
  ```
- **[LOW] Proper handling** — `internal/auth/password.go:63` in `HashPassword`
  ```go
  	if err != nil {
  		return "", err
  	}
  ```

### `internal/auth/totp.go`

- **[HIGH] Swallowed error** — `internal/auth/totp.go:67` in `DecryptSecret`
  ```go
  	if err != nil {
  		return stored
  	}
  ```
- **[HIGH] Swallowed error** — `internal/auth/totp.go:71` in `DecryptSecret`
  ```go
  	if err != nil {
  		return stored
  	}
  ```
- **[HIGH] Swallowed error** — `internal/auth/totp.go:75` in `DecryptSecret`
  ```go
  	if err != nil {
  		return stored
  	}
  ```
- **[HIGH] Swallowed error** — `internal/auth/totp.go:84` in `DecryptSecret`
  ```go
  	if err != nil {
  		return stored // decryption failed — may be corrupted
  	}
  ```
- **[HIGH] Ignored error (`_`)** — `internal/auth/totp.go:134` in `ValidateCodeWithWindow`
  - _error explicitly discarded with `_`_
  ```go
  	valid, _ := totp.ValidateCustom(code, secret, time.Now(), totp.ValidateOpts{
  ```
- **[LOW] Proper handling** — `internal/auth/totp.go:42` in `EncryptSecret`
  ```go
  	if err != nil {
  		return "", fmt.Errorf("create cipher: %w", err)
  	}
  ```
- **[LOW] Proper handling** — `internal/auth/totp.go:46` in `EncryptSecret`
  ```go
  	if err != nil {
  		return "", fmt.Errorf("create GCM: %w", err)
  	}
  ```
- **[LOW] Proper handling** — `internal/auth/totp.go:50` in `EncryptSecret`
  ```go
  	if _, err := io.ReadFull(rand.Reader, nonce); err != nil {
  		return "", fmt.Errorf("generate nonce: %w", err)
  	}
  ```
- **[LOW] Proper handling** — `internal/auth/totp.go:110` in `GenerateRecoveryCodes`
  ```go
  		if _, err := rand.Read(b); err != nil {
  			return nil, nil, fmt.Errorf("failed to generate recovery code: %w", err)
  		}
  ```

### `internal/config/config.go`

- **[HIGH] Ignored error (`_`)** — `internal/config/config.go:97` in `LoadEnvFile`
  - _error explicitly discarded with `_`_
  ```go
  	dir, _ := os.Getwd()
  ```
- **[LOW] Proper handling** — `internal/config/config.go:136` in `Load`
  ```go
  	if err != nil {
  		return nil, fmt.Errorf("failed to read config file %s: %w", configPath, err)
  	}
  ```
- **[LOW] Proper handling** — `internal/config/config.go:143` in `Load`
  ```go
  	if err := yaml.Unmarshal([]byte(configStr), &cfg); err != nil {
  		return nil, fmt.Errorf("failed to parse config file: %w", err)
  	}
  ```
- **[LOW] Proper handling** — `internal/config/config.go:149` in `Load`
  ```go
  	if err := cfg.validate(); err != nil {
  		return nil, fmt.Errorf("config validation failed: %w", err)
  	}
  ```
- **[LOW] Proper handling** — `internal/config/config.go:183` in `validate`
  ```go
  	if _, err := url.Parse(c.Frontend.URL); err != nil {
  		return fmt.Errorf("frontend.url is not a valid URL: %w", err)
  	}
  ```

### `internal/configstore/seed.go`

- **[HIGH] Swallowed error** — `internal/configstore/seed.go:384` in `Seed`
  ```go
  			if _, insertErr := col.InsertOne(ctx, def); insertErr != nil {
  				return insertErr
  			}
  ```
- **[LOW] Proper handling** — `internal/configstore/seed.go:388` in `Seed`
  ```go
  		} else if err != nil {
  			return err
  		}
  ```

### `internal/configstore/store.go`

- **[MEDIUM] Logged only (no return)** — `internal/configstore/store.go:128` in `StartAutoReload`
  ```go
  				if err := s.Load(ctx); err != nil {
  					slog.Warn("configstore: auto-reload failed", "error", err)
  				}
  ```
- **[LOW] Proper handling** — `internal/configstore/store.go:35` in `Load`
  ```go
  	if err != nil {
  		return err
  	}
  ```
- **[LOW] Proper handling** — `internal/configstore/store.go:41` in `Load`
  ```go
  	if err := cursor.All(ctx, &vars); err != nil {
  		return err
  	}
  ```
- **[LOW] Proper handling** — `internal/configstore/store.go:94` in `Set`
  ```go
  	if err != nil {
  		return err
  	}
  ```
- **[LOW] Proper handling** — `internal/configstore/store.go:107` in `Reload`
  ```go
  	if err != nil {
  		return err
  	}
  ```

### `internal/configstore/validate.go`

- **[LOW] Proper handling** — `internal/configstore/validate.go:30` in `ValidateValue`
  ```go
  		if _, err := strconv.ParseFloat(value, 64); err != nil {
  			return fmt.Errorf("invalid numeric value: %w", err)
  		}
  ```
- **[LOW] Proper handling** — `internal/configstore/validate.go:73` in `ValidateEnumValue`
  ```go
  	if err := json.Unmarshal([]byte(optionsJSON), &strOpts); err != nil {
  		return fmt.Errorf("invalid options JSON: %w", err)
  	}
  ```
- **[LOW] Proper handling** — `internal/configstore/validate.go:86` in `validateTemplate`
  ```go
  	if _, err := template.New("check").Parse(value); err != nil {
  		return fmt.Errorf("invalid template syntax: %w", err)
  	}
  ```

### `internal/datadog/client.go`

- **[HIGH] Ignored error (`_`)** — `internal/datadog/client.go:98` in `New`
  - _error explicitly discarded with `_`_
  ```go
  		machineID, _ = os.Hostname()
  ```
- **[HIGH] Ignored error (`_`)** — `internal/datadog/client.go:135` in `resolveHostname`
  - _error explicitly discarded with `_`_
  ```go
  	h, _ := os.Hostname()
  ```
- **[HIGH] Missing error check** — `internal/datadog/client.go:400` in `Validate`
  - _statement-form call to known error-returning 'io.Copy()'_
  ```go
  	io.Copy(io.Discard, resp.Body)
  ```
- **[HIGH] Missing error check** — `internal/datadog/client.go:401` in `Validate`
  - _statement-form call to known error-returning 'resp.Body.Close()'_
  ```go
  	resp.Body.Close()
  ```
- **[HIGH] Swallowed error** — `internal/datadog/client.go:424` in `metricsFlushLoop`
  ```go
  		if err := c.submitMetrics(buf); err != nil {
  			slog.Warn("datadog: metrics flush failed, will retry", "count", len(buf), "error", err)
  			return false
  		}
  ```
- **[HIGH] Swallowed error** — `internal/datadog/client.go:505` in `logsFlushLoop`
  ```go
  		if err := c.submitLogs(buf); err != nil {
  			slog.Warn("datadog: logs flush failed, will retry", "count", len(buf), "error", err)
  			return false
  		}
  ```
- **[HIGH] Ignored error (`_`)** — `internal/datadog/client.go:652` in `submitMetrics`
  - _error explicitly discarded with `_`_
  ```go
  	respBody, _ := io.ReadAll(resp.Body)
  ```
- **[HIGH] Missing error check** — `internal/datadog/client.go:653` in `submitMetrics`
  - _statement-form call to known error-returning 'resp.Body.Close()'_
  ```go
  	resp.Body.Close()
  ```
- **[HIGH] Ignored error (`_`)** — `internal/datadog/client.go:686` in `submitEvent`
  - _error explicitly discarded with `_`_
  ```go
  	respBody, _ := io.ReadAll(resp.Body)
  ```
- **[HIGH] Missing error check** — `internal/datadog/client.go:687` in `submitEvent`
  - _statement-form call to known error-returning 'resp.Body.Close()'_
  ```go
  	resp.Body.Close()
  ```
- **[HIGH] Ignored error (`_`)** — `internal/datadog/client.go:719` in `submitLogs`
  - _error explicitly discarded with `_`_
  ```go
  	respBody, _ := io.ReadAll(resp.Body)
  ```
- **[HIGH] Missing error check** — `internal/datadog/client.go:720` in `submitLogs`
  - _statement-form call to known error-returning 'resp.Body.Close()'_
  ```go
  	resp.Body.Close()
  ```
- **[HIGH] Ignored error (`_`)** — `internal/datadog/client.go:752` in `submitServiceCheck`
  - _error explicitly discarded with `_`_
  ```go
  	respBody, _ := io.ReadAll(resp.Body)
  ```
- **[HIGH] Missing error check** — `internal/datadog/client.go:753` in `submitServiceCheck`
  - _statement-form call to known error-returning 'resp.Body.Close()'_
  ```go
  	resp.Body.Close()
  ```
- **[MEDIUM] Logged only (no return)** — `internal/datadog/client.go:476` in `eventsFlushLoop`
  ```go
  			if err := c.submitEvent(evt); err != nil {
  				slog.Warn("datadog: event submission failed", "title", evt.Title, "error", err)
  			}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/datadog/client.go:483` in `eventsFlushLoop`
  ```go
  					if err := c.submitEvent(evt); err != nil {
  						slog.Warn("datadog: event submission failed during shutdown", "error", err)
  					}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/datadog/client.go:557` in `checksFlushLoop`
  ```go
  			if err := c.submitServiceCheck(check); err != nil {
  				slog.Warn("datadog: service check submission failed", "check", check.Check, "error", err)
  			}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/datadog/client.go:564` in `checksFlushLoop`
  ```go
  					if err := c.submitServiceCheck(check); err != nil {
  						slog.Warn("datadog: service check submission failed during shutdown", "error", err)
  					}
  ```
- **[LOW] Proper handling** — `internal/datadog/client.go:153` in `Startup`
  ```go
  	if err := c.Validate(ctx); err != nil {
  		return fmt.Errorf("API key validation failed: %w", err)
  	}
  ```
- **[LOW] Proper handling** — `internal/datadog/client.go:166` in `Startup`
  ```go
  	if err := c.submitEvent(evt); err != nil {
  		return fmt.Errorf("startup event submission failed: %w", err)
  	}
  ```
- **[LOW] Proper handling** — `internal/datadog/client.go:178` in `Startup`
  ```go
  	if err := c.submitMetrics(heartbeat); err != nil {
  		return fmt.Errorf("startup metric submission failed: %w", err)
  	}
  ```
- **[LOW] Proper handling** — `internal/datadog/client.go:391` in `Validate`
  ```go
  	if err != nil {
  		return err
  	}
  ```
- **[LOW] Proper handling** — `internal/datadog/client.go:397` in `Validate`
  ```go
  	if err != nil {
  		return fmt.Errorf("datadog validate request failed: %w", err)
  	}
  ```
- **[LOW] Proper handling** — `internal/datadog/client.go:632` in `submitMetrics`
  ```go
  	if err != nil {
  		return err
  	}
  ```
- **[LOW] Proper handling** — `internal/datadog/client.go:638` in `submitMetrics`
  ```go
  	if err != nil {
  		return err
  	}
  ```
- **[LOW] Proper handling** — `internal/datadog/client.go:649` in `submitMetrics`
  ```go
  	if err != nil {
  		return err
  	}
  ```
- **[LOW] Proper handling** — `internal/datadog/client.go:666` in `submitEvent`
  ```go
  	if err != nil {
  		return err
  	}
  ```
- **[LOW] Proper handling** — `internal/datadog/client.go:672` in `submitEvent`
  ```go
  	if err != nil {
  		return err
  	}
  ```
- **[LOW] Proper handling** — `internal/datadog/client.go:683` in `submitEvent`
  ```go
  	if err != nil {
  		return err
  	}
  ```
- **[LOW] Proper handling** — `internal/datadog/client.go:699` in `submitLogs`
  ```go
  	if err != nil {
  		return err
  	}
  ```
- **[LOW] Proper handling** — `internal/datadog/client.go:705` in `submitLogs`
  ```go
  	if err != nil {
  		return err
  	}
  ```
- **[LOW] Proper handling** — `internal/datadog/client.go:716` in `submitLogs`
  ```go
  	if err != nil {
  		return err
  	}
  ```
- **[LOW] Proper handling** — `internal/datadog/client.go:732` in `submitServiceCheck`
  ```go
  	if err != nil {
  		return err
  	}
  ```
- **[LOW] Proper handling** — `internal/datadog/client.go:738` in `submitServiceCheck`
  ```go
  	if err != nil {
  		return err
  	}
  ```
- **[LOW] Proper handling** — `internal/datadog/client.go:749` in `submitServiceCheck`
  ```go
  	if err != nil {
  		return err
  	}
  ```

### `internal/db/mongodb.go`

- **[LOW] Proper handling** — `internal/db/mongodb.go:31` in `NewMongoDB`
  ```go
  	if err != nil {
  		return nil, fmt.Errorf("failed to connect to MongoDB: %w", err)
  	}
  ```
- **[LOW] Proper handling** — `internal/db/mongodb.go:35` in `NewMongoDB`
  ```go
  	if err := client.Ping(ctx, nil); err != nil {
  		return nil, fmt.Errorf("failed to ping MongoDB: %w", err)
  	}
  ```
- **[LOW] Proper handling** — `internal/db/mongodb.go:319` in `ensureIndexes`
  ```go
  		if err != nil {
  			if criticalCollections[idx.collection] {
  				slog.Error("FATAL: failed to create indexes on critical collection", "collection", idx.collection, "error", err)
  				os.Exit(1)
  			}
  			slog.Warn("failed to create indexes", "collection", idx.collection, "error", err)
  ... (1 more lines)
  ```

### `internal/db/schema.go`

- **[MEDIUM] Logged only (no return)** — `internal/db/schema.go:56` in `EnsureSchemaValidation`
  ```go
  		if err := m.Database.RunCommand(ctx, cmd).Err(); err != nil {
  			slog.Warn("failed to apply schema validation", "collection", cs.Collection, "error", err)
  		}
  ```

### `internal/email/resend.go`

- **[HIGH] Missing error check** — `internal/email/resend.go:94` in `SendEmail`
  - _statement-form call to known error-returning 'resp.Body.Close()'_
  ```go
  			resp.Body.Close()
  ```
- **[HIGH] Ignored error (`_`)** — `internal/email/resend.go:100` in `SendEmail`
  - _error explicitly discarded with `_`_
  ```go
  		body, _ := io.ReadAll(resp.Body)
  ```
- **[HIGH] Missing error check** — `internal/email/resend.go:101` in `SendEmail`
  - _statement-form call to known error-returning 'resp.Body.Close()'_
  ```go
  		resp.Body.Close()
  ```
- **[HIGH] Swallowed error** — `internal/email/resend.go:137` in `executeTemplate`
  ```go
  	if err != nil {
  		slog.Error("email: failed to parse template, using fallback", "template", configKey, "error", err)
  		return fallback
  	}
  ```
- **[HIGH] Swallowed error** — `internal/email/resend.go:143` in `executeTemplate`
  ```go
  	if err := t.Execute(&buf, data); err != nil {
  		slog.Error("email: failed to execute template, using fallback", "template", configKey, "error", err)
  		return fallback
  	}
  ```
- **[LOW] Proper handling** — `internal/email/resend.go:64` in `SendEmail`
  ```go
  	if err != nil {
  		return fmt.Errorf("failed to marshal email request: %w", err)
  	}
  ```
- **[LOW] Proper handling** — `internal/email/resend.go:77` in `SendEmail`
  ```go
  		if err != nil {
  			return fmt.Errorf("failed to create request: %w", err)
  		}
  ```
- **[LOW] Proper handling** — `internal/email/resend.go:85` in `SendEmail`
  ```go
  		if err != nil {
  			if attempt < maxRetries-1 {
  				slog.Warn("email network error, will retry", "error", err)
  				continue
  			}
  			return fmt.Errorf("failed to send email after %d attempts: %w", maxRetries, err)
  ... (1 more lines)
  ```

### `internal/health/health.go`

- **[HIGH] Ignored error (`_`)** — `internal/health/health.go:50` in `New`
  - _error explicitly discarded with `_`_
  ```go
  		h, _ := os.Hostname()
  ```
- **[HIGH] Ignored error (`_`)** — `internal/health/health.go:368` in `hostname`
  - _error explicitly discarded with `_`_
  ```go
  	h, _ := os.Hostname()
  ```
- **[MEDIUM] Logged only (no return)** — `internal/health/health.go:153` in `registerNode`
  ```go
  	if err != nil {
  		slog.Error("health: failed to register node", "error", err)
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/health/health.go:166` in `heartbeat`
  ```go
  	if err != nil {
  		slog.Warn("health: heartbeat failed", "error", err)
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/health/health.go:210` in `collectAndStore`
  ```go
  	} else if err != nil {
  		slog.Warn("health: cpu collect error", "error", err)
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/health/health.go:242` in `collectAndStore`
  ```go
  	} else if err != nil {
  		slog.Warn("health: network collect error", "error", err)
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/health/health.go:297` in `collectAndStore`
  ```go
  	if _, err := s.db.SystemMetrics().InsertOne(ctx, metric); err != nil {
  		slog.Error("health: failed to store metrics", "error", err)
  	}
  ```

### `internal/health/integrations.go`

- **[HIGH] Swallowed error** — `internal/health/integrations.go:124` in `runIntegrationChecks`
  ```go
  		if err != nil {
  			result.Status = models.IntegrationUnhealthy
  			result.Message = err.Error()
  			slog.Warn("health: integration unhealthy", "integration", entry.name, "error", err)
  		} else {
  ```
- **[HIGH] Missing error check** — `internal/health/integrations.go:179` in `NewResendChecker`
  - _statement-form call to known error-returning 'io.Copy()'_
  ```go
  		io.Copy(io.Discard, resp.Body)
  ```
- **[HIGH] Missing error check** — `internal/health/integrations.go:180` in `NewResendChecker`
  - _statement-form call to known error-returning 'resp.Body.Close()'_
  ```go
  		resp.Body.Close()
  ```
- **[HIGH] Missing error check** — `internal/health/integrations.go:200` in `NewGoogleOAuthChecker`
  - _statement-form call to known error-returning 'io.Copy()'_
  ```go
  		io.Copy(io.Discard, resp.Body)
  ```
- **[HIGH] Missing error check** — `internal/health/integrations.go:201` in `NewGoogleOAuthChecker`
  - _statement-form call to known error-returning 'resp.Body.Close()'_
  ```go
  		resp.Body.Close()
  ```
- **[HIGH] Missing error check** — `internal/health/integrations.go:220` in `NewGitHubOAuthChecker`
  - _statement-form call to known error-returning 'io.Copy()'_
  ```go
  		io.Copy(io.Discard, resp.Body)
  ```
- **[HIGH] Missing error check** — `internal/health/integrations.go:221` in `NewGitHubOAuthChecker`
  - _statement-form call to known error-returning 'resp.Body.Close()'_
  ```go
  		resp.Body.Close()
  ```
- **[HIGH] Missing error check** — `internal/health/integrations.go:240` in `NewMicrosoftOAuthChecker`
  - _statement-form call to known error-returning 'io.Copy()'_
  ```go
  		io.Copy(io.Discard, resp.Body)
  ```
- **[HIGH] Missing error check** — `internal/health/integrations.go:241` in `NewMicrosoftOAuthChecker`
  - _statement-form call to known error-returning 'resp.Body.Close()'_
  ```go
  		resp.Body.Close()
  ```
- **[LOW] Proper handling** — `internal/health/integrations.go:171` in `NewResendChecker`
  ```go
  		if err != nil {
  			return err
  		}
  ```
- **[LOW] Proper handling** — `internal/health/integrations.go:176` in `NewResendChecker`
  ```go
  		if err != nil {
  			return err
  		}
  ```
- **[LOW] Proper handling** — `internal/health/integrations.go:193` in `NewGoogleOAuthChecker`
  ```go
  		if err != nil {
  			return err
  		}
  ```
- **[LOW] Proper handling** — `internal/health/integrations.go:197` in `NewGoogleOAuthChecker`
  ```go
  		if err != nil {
  			return err
  		}
  ```
- **[LOW] Proper handling** — `internal/health/integrations.go:213` in `NewGitHubOAuthChecker`
  ```go
  		if err != nil {
  			return err
  		}
  ```
- **[LOW] Proper handling** — `internal/health/integrations.go:217` in `NewGitHubOAuthChecker`
  ```go
  		if err != nil {
  			return err
  		}
  ```
- **[LOW] Proper handling** — `internal/health/integrations.go:233` in `NewMicrosoftOAuthChecker`
  ```go
  		if err != nil {
  			return err
  		}
  ```
- **[LOW] Proper handling** — `internal/health/integrations.go:237` in `NewMicrosoftOAuthChecker`
  ```go
  		if err != nil {
  			return err
  		}
  ```

### `internal/health/query.go`

- **[HIGH] Ignored error (`_`)** — `internal/health/query.go:17` in `ListNodes`
  - _error explicitly discarded with `_`_
  ```go
  	staleSeconds, _ := strconv.Atoi(s.getConfig("health.node.stale_timeout_seconds"))
  ```
- **[HIGH] Ignored error (`_`)** — `internal/health/query.go:24` in `ListNodes`
  - _error explicitly discarded with `_`_
  ```go
  	_, _ = s.db.SystemNodes().UpdateMany(ctx,
  ```
- **[HIGH] Swallowed error** — `internal/health/query.go:115` in `GetIntegrationCounts24h`
  ```go
  	if err != nil {
  		return 0, 0
  	}
  ```
- **[LOW] Proper handling** — `internal/health/query.go:31` in `ListNodes`
  ```go
  	if err != nil {
  		return nil, err
  	}
  ```
- **[LOW] Proper handling** — `internal/health/query.go:37` in `ListNodes`
  ```go
  	if err := cursor.All(ctx, &nodes); err != nil {
  		return nil, err
  	}
  ```
- **[LOW] Proper handling** — `internal/health/query.go:51` in `GetMetrics`
  ```go
  	if err != nil {
  		return nil, err
  	}
  ```
- **[LOW] Proper handling** — `internal/health/query.go:57` in `GetMetrics`
  ```go
  	if err := cursor.All(ctx, &metrics); err != nil {
  		return nil, err
  	}
  ```
- **[LOW] Proper handling** — `internal/health/query.go:70` in `GetAggregateMetrics`
  ```go
  	if err != nil {
  		return nil, err
  	}
  ```
- **[LOW] Proper handling** — `internal/health/query.go:76` in `GetAggregateMetrics`
  ```go
  	if err := cursor.All(ctx, &metrics); err != nil {
  		return nil, err
  	}
  ```
- **[LOW] Proper handling** — `internal/health/query.go:85` in `GetCurrentMetrics`
  ```go
  	if err != nil {
  		return nil, err
  	}
  ```

### `internal/metrics/metrics.go`

- **[HIGH] Ignored error (`_`)** — `internal/metrics/metrics.go:32` in `New`
  - _error explicitly discarded with `_`_
  ```go
  	hostname, _ := os.Hostname()
  ```
- **[HIGH] Swallowed error** — `internal/metrics/metrics.go:113` in `tryAcquireOrRenew`
  ```go
  	if result.Err() != nil {
  		if result.Err() == mongo.ErrNoDocuments {
  			// Another holder has the lock and it hasn't expired
  			return false
  		}
  		// On upsert conflict (duplicate key during race), the other machine won
  ... (6 more lines)
  ```
- **[HIGH] Swallowed error** — `internal/metrics/metrics.go:129` in `tryAcquireOrRenew`
  ```go
  	if err := result.Decode(&doc); err != nil {
  		return false
  	}
  ```
- **[HIGH] Swallowed error** — `internal/metrics/metrics.go:145` in `isLeader`
  ```go
  	if err != nil {
  		return false
  	}
  ```
- **[HIGH] Ignored error (`_`)** — `internal/metrics/metrics.go:153` in `releaseLock`
  - _error explicitly discarded with `_`_
  ```go
  	_, _ = s.db.LeaderLocks().DeleteOne(ctx, bson.M{
  ```
- **[HIGH] Swallowed error** — `internal/metrics/metrics.go:186` in `collectDaily`
  ```go
  		if err != nil {
  			slog.Error("Metrics DAU/WAU/MAU aggregation error", "error", err)
  			return
  		}
  ```
- **[HIGH] Swallowed error** — `internal/metrics/metrics.go:221` in `collectDaily`
  ```go
  		if err != nil {
  			slog.Error("Metrics revenue aggregation error", "error", err)
  			return
  		}
  ```
- **[HIGH] Swallowed error** — `internal/metrics/metrics.go:257` in `collectDaily`
  ```go
  		if err != nil {
  			slog.Error("Metrics ARR aggregation error", "error", err)
  			return
  		}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/metrics/metrics.go:285` in `collectDaily`
  ```go
  	if err != nil {
  		slog.Error("Metrics upsert daily metric error", "error", err)
  	}
  ```

### `internal/middleware/auth.go`

- **[HIGH] Ignored error (`_`)** — `internal/middleware/auth.go:155` in `authenticateAPIKey`
  - _error explicitly discarded with `_`_
  ```go
  		_, _ = m.db.APIKeys().UpdateByID(ctx, apiKey.ID,
  ```
- **[HIGH] Swallowed error** — `internal/middleware/auth.go:167` in `isTokenRevoked`
  ```go
  	if err != nil {
  		slog.Warn("revoked-token lookup failed, denying access", "error", err)
  		return true
  	}
  ```
- **[HIGH] Ignored error (`_`)** — `internal/middleware/auth.go:185` in `GetImpersonatedBy`
  - _error explicitly discarded with `_`_
  ```go
  	v, _ := ctx.Value(ImpersonatedByContextKey).(string)
  ```
- **[MEDIUM] Logged only (no return)** — `internal/middleware/auth.go:69` in `authenticateJWT`
  ```go
  	if err != nil {
  		if err == auth.ErrExpiredToken {
  			http.Error(w, `{"error":"Token has expired"}`, http.StatusUnauthorized)
  			return
  		}
  		http.Error(w, `{"error":"Invalid token"}`, http.StatusUnauthorized)
  ... (2 more lines)
  ```
- **[MEDIUM] Logged only (no return)** — `internal/middleware/auth.go:84` in `authenticateJWT`
  ```go
  	if err != nil {
  		http.Error(w, `{"error":"Invalid user ID"}`, http.StatusUnauthorized)
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/middleware/auth.go:91` in `authenticateJWT`
  ```go
  	if err != nil {
  		http.Error(w, `{"error":"User not found"}`, http.StatusUnauthorized)
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/middleware/auth.go:117` in `authenticateAPIKey`
  ```go
  	if err != nil {
  		http.Error(w, `{"error":"Invalid API key"}`, http.StatusUnauthorized)
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/middleware/auth.go:125` in `authenticateAPIKey`
  ```go
  	if err != nil || !user.IsActive {
  		http.Error(w, `{"error":"API key owner account is inactive"}`, http.StatusUnauthorized)
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/middleware/auth.go:136` in `authenticateAPIKey`
  ```go
  		if err != nil {
  			http.Error(w, `{"error":"System configuration error"}`, http.StatusInternalServerError)
  			return
  		}
  ```

### `internal/middleware/ratelimit.go`

- **[HIGH] Ignored error (`_`)** — `internal/middleware/ratelimit.go:99` in `NewDistributedRateLimiter`
  - _error explicitly discarded with `_`_
  ```go
  	_, _ = rl.collection.Indexes().CreateOne(ctx, mongo.IndexModel{
  ```
- **[HIGH] Missing error check** — `internal/middleware/ratelimit.go:109` in `Stop`
  - _statement-form call to known error-returning 'rl.stopOnce.Do()'_
  ```go
  	rl.stopOnce.Do(func() { close(rl.done) })
  ```
- **[HIGH] Swallowed error** — `internal/middleware/ratelimit.go:236` in `GetClientIP`
  ```go
  	if err != nil {
  		return r.RemoteAddr
  	}
  ```
- **[LOW] Proper handling** — `internal/middleware/ratelimit.go:160` in `allowDistributed`
  ```go
  	if err != nil {
  		if err == mongo.ErrNoDocuments {
  			// No valid window exists — reset/create with count=1.
  			err = rl.collection.FindOneAndUpdate(ctx,
  				bson.M{"_id": key},
  				bson.M{"$set": bson.M{
  ... (13 more lines)
  ```
- **[LOW] Proper handling** — `internal/middleware/ratelimit.go:172` in `allowDistributed`
  ```go
  			if err != nil {
  				return false, 0, now, err
  			}
  ```

### `internal/middleware/requestid.go`

- **[HIGH] Ignored error (`_`)** — `internal/middleware/requestid.go:26` in `GetRequestID`
  - _error explicitly discarded with `_`_
  ```go
  	id, _ := ctx.Value(RequestIDContextKey).(string)
  ```
- **[HIGH] Swallowed error** — `internal/middleware/requestid.go:32` in `generateRequestID`
  ```go
  	if _, err := rand.Read(b); err != nil {
  		// Fallback to timestamp-based ID on catastrophic rand failure
  		return fmt.Sprintf("%x", time.Now().UnixNano())
  	}
  ```

### `internal/middleware/tenant.go`

- **[MEDIUM] Logged only (no return)** — `internal/middleware/tenant.go:45` in `RequireTenant`
  ```go
  		if err != nil {
  			http.Error(w, `{"error":"Invalid tenant ID"}`, http.StatusBadRequest)
  			return
  		}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/middleware/tenant.go:52` in `RequireTenant`
  ```go
  		if err != nil {
  			http.Error(w, `{"error":"Tenant not found"}`, http.StatusNotFound)
  			return
  		}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/middleware/tenant.go:68` in `RequireTenant`
  ```go
  		if err != nil {
  			http.Error(w, `{"error":"Not a member of this tenant"}`, http.StatusForbidden)
  			return
  		}
  ```

### `internal/planstore/seed.go`

- **[HIGH] Swallowed error** — `internal/planstore/seed.go:36` in `Seed`
  ```go
  		if _, insertErr := col.InsertOne(ctx, plan); insertErr != nil {
  			return insertErr
  		}
  ```
- **[LOW] Proper handling** — `internal/planstore/seed.go:40` in `Seed`
  ```go
  	} else if err != nil {
  		return err
  	}
  ```

### `internal/stripe/stripe.go`

- **[LOW] Proper handling** — `internal/stripe/stripe.go:78` in `GetOrCreateCustomer`
  ```go
  	if err != nil {
  		return "", fmt.Errorf("stripe customer create: %w", err)
  	}
  ```
- **[LOW] Proper handling** — `internal/stripe/stripe.go:86` in `GetOrCreateCustomer`
  ```go
  	if err != nil {
  		return "", fmt.Errorf("save stripe customer id: %w", err)
  	}
  ```
- **[LOW] Proper handling** — `internal/stripe/stripe.go:121` in `GetOrCreatePrice`
  ```go
  	if err != nil {
  		return "", fmt.Errorf("stripe product create: %w", err)
  	}
  ```
- **[LOW] Proper handling** — `internal/stripe/stripe.go:138` in `GetOrCreatePrice`
  ```go
  	if err != nil {
  		return "", fmt.Errorf("stripe price create: %w", err)
  	}
  ```
- **[LOW] Proper handling** — `internal/stripe/stripe.go:228` in `CreateCheckoutSession`
  ```go
  		if err != nil {
  			return "", err
  		}
  ```
- **[LOW] Proper handling** — `internal/stripe/stripe.go:284` in `CreateCheckoutSession`
  ```go
  	if err != nil {
  		return "", fmt.Errorf("stripe checkout create: %w", err)
  	}
  ```
- **[LOW] Proper handling** — `internal/stripe/stripe.go:299` in `CreateBillingPortalSession`
  ```go
  	if err != nil {
  		return "", fmt.Errorf("stripe portal create: %w", err)
  	}
  ```
- **[LOW] Proper handling** — `internal/stripe/stripe.go:313` in `CancelSubscriptionAtPeriodEnd`
  ```go
  	if err != nil {
  		return nil, fmt.Errorf("stripe cancel subscription: %w", err)
  	}
  ```
- **[LOW] Proper handling** — `internal/stripe/stripe.go:333` in `CancelSubscriptionImmediately`
  ```go
  	if err != nil {
  		return fmt.Errorf("stripe cancel subscription: %w", err)
  	}
  ```
- **[LOW] Proper handling** — `internal/stripe/stripe.go:357` in `NextInvoiceNumber`
  ```go
  	if err != nil {
  		return "", fmt.Errorf("generate invoice number: %w", err)
  	}
  ```
- **[LOW] Proper handling** — `internal/stripe/stripe.go:379` in `UpdateSubscriptionQuantity`
  ```go
  	if err != nil {
  		return fmt.Errorf("stripe get subscription: %w", err)
  	}
  ```
- **[LOW] Proper handling** — `internal/stripe/stripe.go:399` in `UpdateSubscriptionQuantity`
  ```go
  	if err != nil {
  		return fmt.Errorf("stripe update subscription quantity: %w", err)
  	}
  ```

### `internal/syslog/syslog.go`

- **[MEDIUM] Logged only (no return)** — `internal/syslog/syslog.go:97` in `log`
  ```go
  	if _, err := l.db.SystemLogs().InsertOne(ctx, entry); err != nil {
  		slog.Error("syslog: failed to write log", "error", err)
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/syslog/syslog.go:114` in `log`
  ```go
  		if _, err := l.db.SystemLogs().InsertOne(ctx, alert); err != nil {
  			slog.Error("syslog: failed to write injection alert", "error", err)
  		}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/syslog/syslog.go:137` in `logCategorized`
  ```go
  	if _, err := l.db.SystemLogs().InsertOne(ctx, entry); err != nil {
  		slog.Error("syslog: failed to write log", "error", err)
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/syslog/syslog.go:154` in `logCategorized`
  ```go
  		if _, err := l.db.SystemLogs().InsertOne(ctx, alert); err != nil {
  			slog.Error("syslog: failed to write injection alert", "error", err)
  		}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/syslog/syslog.go:234` in `LogTenantActivity`
  ```go
  	if _, err := l.db.SystemLogs().InsertOne(ctx, entry); err != nil {
  		slog.Error("syslog: failed to write tenant activity log", "error", err)
  	}
  ```

### `internal/telemetry/service.go`

- **[HIGH] Swallowed error** — `internal/telemetry/service.go:84` in `flushLoop`
  ```go
  		if err != nil {
  			slog.Warn("telemetry: flush failed, will retry", "count", len(buf), "error", err)
  			return false // retain buffer for next attempt
  		}
  ```
- **[HIGH] Swallowed error** — `internal/telemetry/service.go:189` in `TrackBatch`
  ```go
  	if err != nil {
  		slog.Warn("telemetry: failed to track batch", "count", len(events), "error", err)
  	}
  ```
- **[HIGH] Ignored error (`_`)** — `internal/telemetry/service.go:311` in `FunnelMetrics`
  - _error explicitly discarded with `_`_
  ```go
  	visitors, _ := s.countDistinct(ctx, "sessionId", bson.M{
  ```
- **[HIGH] Ignored error (`_`)** — `internal/telemetry/service.go:317` in `FunnelMetrics`
  - _error explicitly discarded with `_`_
  ```go
  	registrations, _ := s.db.Users().CountDocuments(ctx, bson.M{
  ```
- **[HIGH] Ignored error (`_`)** — `internal/telemetry/service.go:322` in `FunnelMetrics`
  - _error explicitly discarded with `_`_
  ```go
  	planViews, _ := s.countDistinct(ctx, "sessionId", bson.M{
  ```
- **[HIGH] Ignored error (`_`)** — `internal/telemetry/service.go:329` in `FunnelMetrics`
  - _error explicitly discarded with `_`_
  ```go
  	checkouts, _ := s.db.TelemetryEvents().CountDocuments(ctx, bson.M{
  ```
- **[HIGH] Ignored error (`_`)** — `internal/telemetry/service.go:335` in `FunnelMetrics`
  - _error explicitly discarded with `_`_
  ```go
  	conversions, _ := s.db.FinancialTransactions().CountDocuments(ctx, bson.M{
  ```
- **[HIGH] Ignored error (`_`)** — `internal/telemetry/service.go:341` in `FunnelMetrics`
  - _error explicitly discarded with `_`_
  ```go
  	upgrades, _ := s.db.TelemetryEvents().CountDocuments(ctx, mergeBson(dateFilter, bson.M{
  ```
- **[HIGH] Swallowed error** — `internal/telemetry/service.go:486` in `EngagementMetrics`
  ```go
  	if err != nil {
  		return &EngagementData{}, nil
  	}
  ```
- **[HIGH] Swallowed error** — `internal/telemetry/service.go:492` in `EngagementMetrics`
  ```go
  	if err != nil {
  		return &EngagementData{}, nil
  	}
  ```
- **[HIGH] Ignored error (`_`)** — `internal/telemetry/service.go:511` in `EngagementMetrics`
  - _error explicitly discarded with `_`_
  ```go
  	totalLogins, _ := s.db.TelemetryEvents().CountDocuments(ctx, bson.M{
  ```
- **[HIGH] Ignored error (`_`)** — `internal/telemetry/service.go:549` in `KPIs`
  - _error explicitly discarded with `_`_
  ```go
  	v, err, _ := s.kpiGroup.Do("kpis", func() (interface{}, error) {
  ```
- **[HIGH] Ignored error (`_`)** — `internal/telemetry/service.go:572` in `computeKPIs`
  - _error explicitly discarded with `_`_
  ```go
  	activeSubscribers, _ := s.db.Tenants().CountDocuments(ctx, bson.M{
  ```
- **[HIGH] Ignored error (`_`)** — `internal/telemetry/service.go:578` in `computeKPIs`
  - _error explicitly discarded with `_`_
  ```go
  	totalRegistrations, _ := s.db.Users().CountDocuments(ctx, bson.M{})
  ```
- **[HIGH] Ignored error (`_`)** — `internal/telemetry/service.go:591` in `computeKPIs`
  - _error explicitly discarded with `_`_
  ```go
  	canceledThisMonth, _ := s.db.Tenants().CountDocuments(ctx, bson.M{
  ```
- **[HIGH] Ignored error (`_`)** — `internal/telemetry/service.go:594` in `computeKPIs`
  - _error explicitly discarded with `_`_
  ```go
  	activeAtMonthStart, _ := s.db.Tenants().CountDocuments(ctx, bson.M{
  ```
- **[HIGH] Ignored error (`_`)** — `internal/telemetry/service.go:604` in `computeKPIs`
  - _error explicitly discarded with `_`_
  ```go
  	totalTrials, _ := s.db.Tenants().CountDocuments(ctx, bson.M{
  ```
- **[HIGH] Ignored error (`_`)** — `internal/telemetry/service.go:607` in `computeKPIs`
  - _error explicitly discarded with `_`_
  ```go
  	convertedTrials, _ := s.db.Tenants().CountDocuments(ctx, bson.M{
  ```
- **[HIGH] Ignored error (`_`)** — `internal/telemetry/service.go:661` in `CustomEventSummary`
  - _error explicitly discarded with `_`_
  ```go
  	totalCount, _ := s.db.TelemetryEvents().CountDocuments(ctx, filter)
  ```
- **[HIGH] Swallowed error** — `internal/telemetry/service.go:675` in `CustomEventSummary`
  ```go
  	if err != nil {
  		return &CustomEventData{EventName: eventName, TotalCount: totalCount}, nil
  	}
  ```
- **[HIGH] Swallowed error** — `internal/telemetry/service.go:860` in `weeklyActiveUsers`
  ```go
  	if err != nil {
  		return nil
  	}
  ```
- **[HIGH] Swallowed error** — `internal/telemetry/service.go:907` in `monthlyActiveUsers`
  ```go
  	if err != nil {
  		return nil
  	}
  ```
- **[HIGH] Swallowed error** — `internal/telemetry/service.go:944` in `topCustomEvents`
  ```go
  	if err != nil {
  		return nil
  	}
  ```
- **[HIGH] Swallowed error** — `internal/telemetry/service.go:974` in `creditConsumptionTrend`
  ```go
  	if err != nil {
  		return nil
  	}
  ```
- **[HIGH] Swallowed error** — `internal/telemetry/service.go:1049` in `calculateMRR`
  ```go
  	if err != nil {
  		return 0
  	}
  ```
- **[HIGH] Swallowed error** — `internal/telemetry/service.go:1092` in `medianTimeToFirstPurchase`
  ```go
  	if err != nil {
  		return 0
  	}
  ```
- **[HIGH] Swallowed error** — `internal/telemetry/service.go:1141` in `planDistribution`
  ```go
  	if err != nil {
  		return nil
  	}
  ```
- **[HIGH] Swallowed error** — `internal/telemetry/service.go:1181` in `mrrTrend`
  ```go
  	if err != nil {
  		return nil
  	}
  ```
- **[HIGH] Swallowed error** — `internal/telemetry/service.go:1211` in `subscriberTrend`
  ```go
  	if err != nil {
  		return nil
  	}
  ```
- **[HIGH] Swallowed error** — `internal/telemetry/service.go:1231` in `aggregateDailyPoints`
  ```go
  	if err != nil {
  		return nil
  	}
  ```
- **[LOW] Proper handling** — `internal/telemetry/service.go:430` in `RetentionCohorts`
  ```go
  	if err != nil {
  		return nil, err
  	}
  ```
- **[LOW] Proper handling** — `internal/telemetry/service.go:551` in `KPIs`
  ```go
  		if err != nil {
  			return nil, err
  		}
  ```
- **[LOW] Proper handling** — `internal/telemetry/service.go:560` in `KPIs`
  ```go
  	if err != nil {
  		return nil, err
  	}
  ```
- **[LOW] Proper handling** — `internal/telemetry/service.go:711` in `ListEventTypes`
  ```go
  	if err != nil {
  		return nil, err
  	}
  ```
- **[LOW] Proper handling** — `internal/telemetry/service.go:750` in `countDistinct`
  ```go
  	if err != nil {
  		return 0, err
  	}
  ```
- **[LOW] Proper handling** — `internal/telemetry/service.go:771` in `getActiveTenantIDs`
  ```go
  	if err != nil {
  		return nil, err
  	}
  ```
- **[LOW] Proper handling** — `internal/telemetry/service.go:795` in `getUserIDsForTenants`
  ```go
  	if err != nil {
  		return nil, err
  	}
  ```

### `internal/testutil/testutil.go`

- **[HIGH] Ignored error (`_`)** — `internal/testutil/testutil.go:27` in `loadEnvTest`
  - _error explicitly discarded with `_`_
  ```go
  	dir, _ := os.Getwd()
  ```
- **[HIGH] Ignored error (`_`)** — `internal/testutil/testutil.go:90` in `MustConnectTestDB`
  - _error explicitly discarded with `_`_
  ```go
  		colls, _ := database.Database.ListCollectionNames(ctx, bson.M{})
  ```
- **[HIGH] Missing error check** — `internal/testutil/testutil.go:92` in `MustConnectTestDB`
  - _statement-form call to known error-returning 'database.Database.Collection(name).DeleteMany()'_
  ```go
  			database.Database.Collection(name).DeleteMany(ctx, bson.M{})
  ```
- **[HIGH] Missing error check** — `internal/testutil/testutil.go:94` in `MustConnectTestDB`
  - _statement-form call to known error-returning 'database.Close()'_
  ```go
  		database.Close(ctx)
  ```
- **[HIGH] Ignored error (`_`)** — `internal/testutil/testutil.go:129` in `ConnectTestDB`
  - _error explicitly discarded with `_`_
  ```go
  		colls, _ := database.Database.ListCollectionNames(ctx, bson.M{})
  ```
- **[HIGH] Missing error check** — `internal/testutil/testutil.go:131` in `ConnectTestDB`
  - _statement-form call to known error-returning 'database.Database.Collection(name).DeleteMany()'_
  ```go
  			database.Database.Collection(name).DeleteMany(ctx, bson.M{})
  ```
- **[HIGH] Missing error check** — `internal/testutil/testutil.go:133` in `ConnectTestDB`
  - _statement-form call to known error-returning 'database.Close()'_
  ```go
  		database.Close(ctx)
  ```
- **[HIGH] Ignored error (`_`)** — `internal/testutil/testutil.go:144` in `findAndSetConfigDir`
  - _error explicitly discarded with `_`_
  ```go
  	dir, _ := os.Getwd()
  ```
- **[HIGH] Swallowed error** — `internal/testutil/testutil.go:175` in `hasYAMLConfigs`
  ```go
  	if err != nil {
  		return false
  	}
  ```
- **[HIGH] Missing error check** — `internal/testutil/testutil.go:206` in `CleanupCollections`
  - _statement-form call to known error-returning 'database.Database.Collection(name).DeleteMany()'_
  ```go
  		database.Database.Collection(name).DeleteMany(ctx, bson.M{})
  ```
- **[LOW] Proper handling** — `internal/testutil/testutil.go:70` in `MustConnectTestDB`
  ```go
  	if err != nil {
  		t.Fatalf("testutil: failed to load test config: %v", err)
  	}
  ```
- **[LOW] Proper handling** — `internal/testutil/testutil.go:80` in `MustConnectTestDB`
  ```go
  	if err != nil {
  		t.Fatalf("testutil: failed to connect to test database: %v", err)
  	}
  ```
- **[LOW] Proper handling** — `internal/testutil/testutil.go:113` in `ConnectTestDB`
  ```go
  	if err != nil {
  		log.Fatalf("testutil: failed to load test config: %v", err)
  	}
  ```
- **[LOW] Proper handling** — `internal/testutil/testutil.go:122` in `ConnectTestDB`
  ```go
  	if err != nil {
  		log.Fatalf("testutil: failed to connect to test database: %v", err)
  	}
  ```
- **[LOW] Proper handling** — `internal/testutil/testutil.go:218` in `TestConfig`
  ```go
  	if err != nil {
  		t.Fatalf("testutil: failed to load test config: %v", err)
  	}
  ```
- **[LOW] Proper handling** — `internal/testutil/testutil.go:231` in `CreateTestUser`
  ```go
  	if err != nil {
  		t.Fatalf("testutil: failed to hash password: %v", err)
  	}
  ```
- **[LOW] Proper handling** — `internal/testutil/testutil.go:248` in `CreateTestUser`
  ```go
  	if err != nil {
  		t.Fatalf("testutil: failed to create test user: %v", err)
  	}
  ```
- **[LOW] Proper handling** — `internal/testutil/testutil.go:270` in `CreateTestTenant`
  ```go
  	if err != nil {
  		t.Fatalf("testutil: failed to create test tenant: %v", err)
  	}
  ```
- **[LOW] Proper handling** — `internal/testutil/testutil.go:283` in `CreateTestTenant`
  ```go
  	if err != nil {
  		t.Fatalf("testutil: failed to create test membership: %v", err)
  	}
  ```
- **[LOW] Proper handling** — `internal/testutil/testutil.go:301` in `MarkSystemInitialized`
  ```go
  	if err != nil {
  		t.Fatalf("testutil: failed to mark system initialized: %v", err)
  	}
  ```
- **[LOW] Proper handling** — `internal/testutil/testutil.go:319` in `InsertTestLogs`
  ```go
  		if err != nil {
  			t.Fatalf("testutil: failed to insert test log: %v", err)
  		}
  ```
- **[LOW] Proper handling** — `internal/testutil/testutil.go:330` in `CountDocuments`
  ```go
  	if err != nil {
  		t.Fatalf("testutil: failed to count documents: %v", err)
  	}
  ```
- **[LOW] Proper handling** — `internal/testutil/testutil.go:340` in `ParseJSON`
  ```go
  	if err := json.NewDecoder(resp.Body).Decode(target); err != nil {
  		t.Fatalf("testutil: failed to parse JSON response: %v", err)
  	}
  ```
- **[LOW] Proper handling** — `internal/testutil/testutil.go:370` in `CreateTestMembership`
  ```go
  	if err != nil {
  		t.Fatalf("testutil: failed to create test membership: %v", err)
  	}
  ```
- **[LOW] Proper handling** — `internal/testutil/testutil.go:394` in `CreateTestPlan`
  ```go
  	if err != nil {
  		t.Fatalf("testutil: failed to create test plan: %v", err)
  	}
  ```
- **[LOW] Proper handling** — `internal/testutil/testutil.go:416` in `CreateTestAPIKey`
  ```go
  	if err != nil {
  		t.Fatalf("testutil: failed to create test API key: %v", err)
  	}
  ```
- **[LOW] Proper handling** — `internal/testutil/testutil.go:440` in `CreateTestWebhook`
  ```go
  	if err != nil {
  		t.Fatalf("testutil: failed to create test webhook: %v", err)
  	}
  ```
- **[LOW] Proper handling** — `internal/testutil/testutil.go:463` in `CreateTestInvitation`
  ```go
  	if err != nil {
  		t.Fatalf("testutil: failed to create test invitation: %v", err)
  	}
  ```

### `internal/version/check.go`

- **[HIGH] Swallowed error** — `internal/version/check.go:29` in `CheckAndMigrate`
  ```go
  	if err != nil {
  		// System not initialized yet — nothing to check
  		return
  	}
  ```
- **[HIGH] Swallowed error** — `internal/version/check.go:65` in `sendUpgradeMessage`
  ```go
  	if err != nil {
  		slog.Warn("Could not find root tenant for upgrade message", "error", err)
  		return
  	}
  ```
- **[HIGH] Swallowed error** — `internal/version/check.go:75` in `sendUpgradeMessage`
  ```go
  	if err != nil {
  		slog.Warn("Could not find root tenant owner for upgrade message", "error", err)
  		return
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/version/check.go:90` in `sendUpgradeMessage`
  ```go
  	if _, err := database.Messages().InsertOne(ctx, msg); err != nil {
  		slog.Warn("Failed to send upgrade message", "error", err)
  	}
  ```

### `internal/version/version.go`

- **[HIGH] Ignored error (`_`)** — `internal/version/version.go:30` in `Load`
  - _error explicitly discarded with `_`_
  ```go
  	dir, _ := os.Getwd()
  ```

### `internal/webhooks/crypto.go`

- **[LOW] Proper handling** — `internal/webhooks/crypto.go:21` in `EncryptSecret`
  ```go
  	if err != nil {
  		return "", fmt.Errorf("create cipher: %w", err)
  	}
  ```
- **[LOW] Proper handling** — `internal/webhooks/crypto.go:26` in `EncryptSecret`
  ```go
  	if err != nil {
  		return "", fmt.Errorf("create GCM: %w", err)
  	}
  ```
- **[LOW] Proper handling** — `internal/webhooks/crypto.go:31` in `EncryptSecret`
  ```go
  	if _, err := io.ReadFull(rand.Reader, nonce); err != nil {
  		return "", fmt.Errorf("generate nonce: %w", err)
  	}
  ```
- **[LOW] Proper handling** — `internal/webhooks/crypto.go:46` in `DecryptSecret`
  ```go
  	if err != nil {
  		return "", fmt.Errorf("decode base64: %w", err)
  	}
  ```
- **[LOW] Proper handling** — `internal/webhooks/crypto.go:51` in `DecryptSecret`
  ```go
  	if err != nil {
  		return "", fmt.Errorf("create cipher: %w", err)
  	}
  ```
- **[LOW] Proper handling** — `internal/webhooks/crypto.go:56` in `DecryptSecret`
  ```go
  	if err != nil {
  		return "", fmt.Errorf("create GCM: %w", err)
  	}
  ```
- **[LOW] Proper handling** — `internal/webhooks/crypto.go:67` in `DecryptSecret`
  ```go
  	if err != nil {
  		return "", fmt.Errorf("decrypt: %w", err)
  	}
  ```
- **[LOW] Proper handling** — `internal/webhooks/crypto.go:81` in `ParseEncryptionKey`
  ```go
  	if err != nil {
  		return nil, fmt.Errorf("invalid hex key: %w", err)
  	}
  ```

### `internal/webhooks/dispatcher.go`

- **[HIGH] Swallowed error** — `internal/webhooks/dispatcher.go:198` in `dispatch`
  ```go
  	if err != nil {
  		slog.Error("webhooks: failed to query webhooks", "event_type", eventType, "error", err)
  		return
  	}
  ```
- **[HIGH] Swallowed error** — `internal/webhooks/dispatcher.go:205` in `dispatch`
  ```go
  	if err := cursor.All(ctx, &hooks); err != nil {
  		slog.Error("webhooks: failed to decode webhooks", "error", err)
  		return
  	}
  ```
- **[HIGH] Swallowed error** — `internal/webhooks/dispatcher.go:232` in `deliverWithRetry`
  ```go
  	if err != nil {
  		slog.Error("webhooks: failed to marshal payload", "error", err)
  		return
  	}
  ```
- **[HIGH] Swallowed error** — `internal/webhooks/dispatcher.go:241` in `deliverWithRetry`
  ```go
  	if err != nil {
  		slog.Error("webhooks: failed to create request", "webhook", hook.Name, "error", err)
  		return
  	}
  ```
- **[HIGH] Swallowed error** — `internal/webhooks/dispatcher.go:273` in `deliverWithRetry`
  ```go
  	if err != nil {
  		delivery.Success = false
  		delivery.ResponseCode = 0
  		delivery.ResponseBody = err.Error()
  	} else {
  ```
- **[HIGH] Missing error check** — `internal/webhooks/dispatcher.go:331` in `computeSignature`
  - _statement-form call to known error-returning 'mac.Write()'_
  ```go
  	mac.Write(payload)
  ```
- **[HIGH] Swallowed error** — `internal/webhooks/dispatcher.go:406` in `DeliverTest`
  ```go
  	if err != nil {
  		delivery.Success = false
  		delivery.ResponseCode = 0
  		delivery.ResponseBody = err.Error()
  	} else {
  ```
- **[MEDIUM] Logged only (no return)** — `internal/webhooks/dispatcher.go:287` in `deliverWithRetry`
  ```go
  	if _, err := d.db.WebhookDeliveries().InsertOne(deliverCtx, delivery); err != nil {
  		slog.Error("webhooks: failed to record delivery", "webhook", hook.Name, "error", err)
  	}
  ```
- **[MEDIUM] Logged only (no return)** — `internal/webhooks/dispatcher.go:419` in `DeliverTest`
  ```go
  	if _, err := d.db.WebhookDeliveries().InsertOne(ctx, delivery); err != nil {
  		slog.Error("webhooks: failed to record test delivery", "webhook", hook.Name, "error", err)
  	}
  ```
- **[LOW] Proper handling** — `internal/webhooks/dispatcher.go:317` in `resolveSecret`
  ```go
  	if err != nil {
  		// Fallback: may be a legacy plaintext secret not yet migrated
  		if len(stored) > 0 && stored[0] != 0 {
  			return stored
  		}
  		slog.Error("webhooks: failed to decrypt secret", "error", err)
  ... (2 more lines)
  ```
- **[LOW] Proper handling** — `internal/webhooks/dispatcher.go:354` in `DeliverTest`
  ```go
  	if err != nil {
  		slog.Error("webhooks: failed to marshal test payload", "error", err)
  		return models.WebhookDelivery{
  			ID:           primitive.NewObjectID(),
  			WebhookID:    hook.ID,
  			EventType:    models.WebhookEventTenantCreated,
  ... (6 more lines)
  ```
- **[LOW] Proper handling** — `internal/webhooks/dispatcher.go:368` in `DeliverTest`
  ```go
  	if err != nil {
  		return models.WebhookDelivery{
  			ID:           primitive.NewObjectID(),
  			WebhookID:    hook.ID,
  			EventType:    models.WebhookEventTenantCreated,
  			Payload:      string(body),
  ... (6 more lines)
  ```

## Test File Error Handling (summary)

| Metric | Value |
| --- | --- |
| Test files scanned | 33 |
| Total lines | 8,982 |
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

1. **`if X != nil { ... }` blocks** are located via brace matching (strings and comments are masked out first). The block body is then classified as: `proper_handling` (returns `err` or wraps it), `panic_on_error`, `logged_only` (only log calls, no return), or `swallowed` (anything else).
2. **Ignored errors** are detected as `result, _ := someFunc(...)` patterns where the last return value is discarded with `_`. `for k, _ := range m` is excluded.
3. **Missing error checks** are detected as statement-form calls (not assigned, not preceded by `defer`/`go`) to a known error-returning method such as `Close`, `Write`, `InsertOne`, `UpdateOne`, `Marshal`, etc. This is heuristic and may produce false positives — review each finding.

Severity: **HIGH** for swallowed/ignored/missing, **MEDIUM** for logged-only and panic-on-error, **LOW** for proper handling.
