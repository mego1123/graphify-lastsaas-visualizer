# N+1 Query Detection Report

**Target:** `/home/z/my-project/repos/lastsaas/backend`

Finds MongoDB queries that run inside loop bodies. Each such query is an N+1 problem: the loop runs N times, and each iteration hits the database — N+1 round trips instead of one.

## Summary

| Metric | Value |
| --- | --- |
| Total N+1 findings | **27** |
| HIGH severity | 14 |
| MEDIUM severity | 13 |
| LOW severity | 0 |

## Operations Involved

| Operation | Count |
| --- | ---: |
| `FindOne` | 8 |
| `DeleteMany` | 7 |
| `Find` | 3 |
| `CountDocuments` | 3 |
| `InsertOne` | 3 |
| `DeleteOne` | 2 |
| `UpdateOne` | 1 |

## Collections Affected

| Collection | Count |
| --- | ---: |
| `tenant_memberships` | 6 |
| `tenants` | 6 |
| `dynamic:name` | 3 |
| `system_logs` | 2 |
| `invitations` | 2 |
| `webhook_deliveries` | 2 |
| `config_vars` | 2 |
| `users` | 1 |
| `event_definitions` | 1 |
| `messages` | 1 |
| `system_metrics` | 1 |

## Loop Kinds

| Loop kind | Count |
| --- | ---: |
| `range` | 24 |
| `infinite` | 2 |
| `condition` | 1 |

## Files With Most Findings

| File | Findings |
| --- | ---: |
| `internal/api/handlers/admin.go` | 9 |
| `internal/api/handlers/auth.go` | 6 |
| `internal/testutil/testutil.go` | 4 |
| `internal/api/handlers/webhooks.go` | 2 |
| `internal/configstore/seed.go` | 2 |
| `cmd/lastsaas/cmd_logs.go` | 1 |
| `internal/api/handlers/event_definitions.go` | 1 |
| `internal/api/handlers/webhook.go` | 1 |
| `internal/health/query.go` | 1 |

## Detailed Findings

### `cmd/lastsaas/cmd_logs.go`

- **[MEDIUM] Find on `system_logs`** — `cmd/lastsaas/cmd_logs.go:193` (loop at line 180, infinite loop over `_`) in `logsFollow`
  - _Find call inside infinite loop_
  - Suggestion: Use $in operator with a batch of IDs instead of querying in a loop. e.g. `col.Find(ctx, bson.M{"_id": bson.M{"$in": ids}})`
  ```go
          for {
                  time.Sleep(2 * time.Second)
  
                  followFilter := bson.M{}
                  for k, v := range filter {
                          followFilter[k] = v
                  }
                  followFilter["createdAt"] = bson.M{"$gt": lastTime}
  ... (20 more lines)
  ```

### `internal/api/handlers/admin.go`

- **[MEDIUM] Find on `tenant_memberships`** — `internal/api/handlers/admin.go:1280` (loop at line 1277, range loop over `m`) in `PreflightDeleteUser`
  - _Find call inside range loop_
  - Suggestion: Use $in operator with a batch of IDs instead of querying in a loop. e.g. `col.Find(ctx, bson.M{"_id": bson.M{"$in": ids}})`
  ```go
  	for _, m := range ownerships {
  		tenant := tenantMap[m.TenantID]
  
  		memberCursor, err := h.db.TenantMemberships().Find(ctx, bson.M{
  			"tenantId": m.TenantID,
  			"userId":   bson.M{"$ne": userID},
  		})
  		if err != nil {
  ... (48 more lines)
  ```
- **[MEDIUM] Find on `users`** — `internal/api/handlers/admin.go:1301` (loop at line 1277, range loop over `m`) in `PreflightDeleteUser`
  - _Find call inside range loop_
  - Suggestion: Use $in operator with a batch of IDs instead of querying in a loop. e.g. `col.Find(ctx, bson.M{"_id": bson.M{"$in": ids}})`
  ```go
  	for _, m := range ownerships {
  		tenant := tenantMap[m.TenantID]
  
  		memberCursor, err := h.db.TenantMemberships().Find(ctx, bson.M{
  			"tenantId": m.TenantID,
  			"userId":   bson.M{"$ne": userID},
  		})
  		if err != nil {
  ... (48 more lines)
  ```
- **[MEDIUM] FindOne on `tenants`** — `internal/api/handlers/admin.go:1398` (loop at line 1392, range loop over `m`) in `DeleteUser`
  - _FindOne call inside range loop_
  - Suggestion: Use $in operator with a batch of IDs instead of querying in a loop. e.g. `col.Find(ctx, bson.M{"_id": bson.M{"$in": ids}})`
  ```go
  	for _, m := range memberships {
  		if m.Role != models.RoleOwner {
  			continue
  		}
  
  		var tenant models.Tenant
  		if err := h.db.Tenants().FindOne(ctx, bson.M{"_id": m.TenantID}).Decode(&tenant); err != nil {
  			respondWithError(w, http.StatusInternalServerError, "Failed to look up tenant")
  ... (77 more lines)
  ```
- **[MEDIUM] UpdateOne on `tenant_memberships`** — `internal/api/handlers/admin.go:1414` (loop at line 1392, range loop over `m`) in `DeleteUser`
  - _UpdateOne call inside range loop_
  - Suggestion: Use BulkWrite with a []mongo.WriteModel (UpdateOne models) instead of issuing UpdateOne per iteration.
  ```go
  	for _, m := range memberships {
  		if m.Role != models.RoleOwner {
  			continue
  		}
  
  		var tenant models.Tenant
  		if err := h.db.Tenants().FindOne(ctx, bson.M{"_id": m.TenantID}).Decode(&tenant); err != nil {
  			respondWithError(w, http.StatusInternalServerError, "Failed to look up tenant")
  ... (77 more lines)
  ```
- **[MEDIUM] CountDocuments on `tenant_memberships`** — `internal/api/handlers/admin.go:1430` (loop at line 1392, range loop over `m`) in `DeleteUser`
  - _CountDocuments call inside range loop_
  - Suggestion: Use $in operator with a batch of IDs instead of querying in a loop. e.g. `col.Find(ctx, bson.M{"_id": bson.M{"$in": ids}})`
  ```go
  	for _, m := range memberships {
  		if m.Role != models.RoleOwner {
  			continue
  		}
  
  		var tenant models.Tenant
  		if err := h.db.Tenants().FindOne(ctx, bson.M{"_id": m.TenantID}).Decode(&tenant); err != nil {
  			respondWithError(w, http.StatusInternalServerError, "Failed to look up tenant")
  ... (77 more lines)
  ```
- **[MEDIUM] DeleteMany on `tenant_memberships`** — `internal/api/handlers/admin.go:1454` (loop at line 1392, range loop over `m`) in `DeleteUser`
  - _DeleteMany call inside range loop_
  - Suggestion: Batch this operation — issue a single bulk/multi-document call instead of one DB call per loop iteration.
  ```go
  	for _, m := range memberships {
  		if m.Role != models.RoleOwner {
  			continue
  		}
  
  		var tenant models.Tenant
  		if err := h.db.Tenants().FindOne(ctx, bson.M{"_id": m.TenantID}).Decode(&tenant); err != nil {
  			respondWithError(w, http.StatusInternalServerError, "Failed to look up tenant")
  ... (77 more lines)
  ```
- **[MEDIUM] DeleteOne on `tenants`** — `internal/api/handlers/admin.go:1457` (loop at line 1392, range loop over `m`) in `DeleteUser`
  - _DeleteOne call inside range loop_
  - Suggestion: Use DeleteMany with an $in filter instead of DeleteOne in a loop.
  ```go
  	for _, m := range memberships {
  		if m.Role != models.RoleOwner {
  			continue
  		}
  
  		var tenant models.Tenant
  		if err := h.db.Tenants().FindOne(ctx, bson.M{"_id": m.TenantID}).Decode(&tenant); err != nil {
  			respondWithError(w, http.StatusInternalServerError, "Failed to look up tenant")
  ... (77 more lines)
  ```
- **[MEDIUM] DeleteMany on `invitations`** — `internal/api/handlers/admin.go:1460` (loop at line 1392, range loop over `m`) in `DeleteUser`
  - _DeleteMany call inside range loop_
  - Suggestion: Batch this operation — issue a single bulk/multi-document call instead of one DB call per loop iteration.
  ```go
  	for _, m := range memberships {
  		if m.Role != models.RoleOwner {
  			continue
  		}
  
  		var tenant models.Tenant
  		if err := h.db.Tenants().FindOne(ctx, bson.M{"_id": m.TenantID}).Decode(&tenant); err != nil {
  			respondWithError(w, http.StatusInternalServerError, "Failed to look up tenant")
  ... (77 more lines)
  ```
- **[MEDIUM] FindOne on `tenants`** — `internal/api/handlers/admin.go:1680` (loop at line 1678, range loop over `m`) in `ImpersonateUser`
  - _FindOne call inside range loop_
  - Suggestion: Use $in operator with a batch of IDs instead of querying in a loop. e.g. `col.Find(ctx, bson.M{"_id": bson.M{"$in": ids}})`
  ```go
  	for _, m := range memberships {
  		var tenant models.Tenant
  		if err := h.db.Tenants().FindOne(r.Context(), bson.M{"_id": m.TenantID}).Decode(&tenant); err != nil {
  			continue
  		}
  		membershipInfos = append(membershipInfos, MembershipInfo{
  			TenantID:   tenant.ID.Hex(),
  			TenantName: tenant.Name,
  ... (5 more lines)
  ```

### `internal/api/handlers/auth.go`

- **[HIGH] FindOne on `tenants`** — `internal/api/handlers/auth.go:2062` (loop at line 2060, range loop over `m`) in `getUserMemberships`
  - _FindOne call inside range loop_
  - Suggestion: Use $in operator with a batch of IDs instead of querying in a loop. e.g. `col.Find(ctx, bson.M{"_id": bson.M{"$in": ids}})`
  ```go
          for _, m := range memberships {
                  var tenant models.Tenant
                  if err := h.db.Tenants().FindOne(ctx, bson.M{"_id": m.TenantID}).Decode(&tenant); err != nil {
                          continue
                  }
                  result = append(result, MembershipInfo{
                          TenantID:   tenant.ID.Hex(),
                          TenantName: tenant.Name,
  ... (5 more lines)
  ```
- **[HIGH] FindOne on `tenants`** — `internal/api/handlers/auth.go:2261` (loop at line 2255, range loop over `m`) in `DeleteAccount`
  - _FindOne call inside range loop_
  - Suggestion: Use $in operator with a batch of IDs instead of querying in a loop. e.g. `col.Find(ctx, bson.M{"_id": bson.M{"$in": ids}})`
  ```go
          for _, m := range memberships {
                  if m.Role != models.RoleOwner {
                          continue
                  }
  
                  var tenant models.Tenant
                  if err := h.db.Tenants().FindOne(ctx, bson.M{"_id": m.TenantID}).Decode(&tenant); err != nil {
                          continue
  ... (37 more lines)
  ```
- **[HIGH] CountDocuments on `tenant_memberships`** — `internal/api/handlers/auth.go:2270` (loop at line 2255, range loop over `m`) in `DeleteAccount`
  - _CountDocuments call inside range loop_
  - Suggestion: Use $in operator with a batch of IDs instead of querying in a loop. e.g. `col.Find(ctx, bson.M{"_id": bson.M{"$in": ids}})`
  ```go
          for _, m := range memberships {
                  if m.Role != models.RoleOwner {
                          continue
                  }
  
                  var tenant models.Tenant
                  if err := h.db.Tenants().FindOne(ctx, bson.M{"_id": m.TenantID}).Decode(&tenant); err != nil {
                          continue
  ... (37 more lines)
  ```
- **[HIGH] DeleteMany on `tenant_memberships`** — `internal/api/handlers/auth.go:2280` (loop at line 2255, range loop over `m`) in `DeleteAccount`
  - _DeleteMany call inside range loop_
  - Suggestion: Batch this operation — issue a single bulk/multi-document call instead of one DB call per loop iteration.
  ```go
          for _, m := range memberships {
                  if m.Role != models.RoleOwner {
                          continue
                  }
  
                  var tenant models.Tenant
                  if err := h.db.Tenants().FindOne(ctx, bson.M{"_id": m.TenantID}).Decode(&tenant); err != nil {
                          continue
  ... (37 more lines)
  ```
- **[HIGH] DeleteOne on `tenants`** — `internal/api/handlers/auth.go:2283` (loop at line 2255, range loop over `m`) in `DeleteAccount`
  - _DeleteOne call inside range loop_
  - Suggestion: Use DeleteMany with an $in filter instead of DeleteOne in a loop.
  ```go
          for _, m := range memberships {
                  if m.Role != models.RoleOwner {
                          continue
                  }
  
                  var tenant models.Tenant
                  if err := h.db.Tenants().FindOne(ctx, bson.M{"_id": m.TenantID}).Decode(&tenant); err != nil {
                          continue
  ... (37 more lines)
  ```
- **[HIGH] DeleteMany on `invitations`** — `internal/api/handlers/auth.go:2286` (loop at line 2255, range loop over `m`) in `DeleteAccount`
  - _DeleteMany call inside range loop_
  - Suggestion: Batch this operation — issue a single bulk/multi-document call instead of one DB call per loop iteration.
  ```go
          for _, m := range memberships {
                  if m.Role != models.RoleOwner {
                          continue
                  }
  
                  var tenant models.Tenant
                  if err := h.db.Tenants().FindOne(ctx, bson.M{"_id": m.TenantID}).Decode(&tenant); err != nil {
                          continue
  ... (37 more lines)
  ```

### `internal/api/handlers/event_definitions.go`

- **[HIGH] FindOne on `event_definitions`** — `internal/api/handlers/event_definitions.go:463` (loop at line 457, infinite loop over `_`) in `wouldCreateCycle`
  - _FindOne call inside infinite loop_
  - Suggestion: Use $in operator with a batch of IDs instead of querying in a loop. e.g. `col.Find(ctx, bson.M{"_id": bson.M{"$in": ids}})`
  ```go
  	for {
  		if visited[current] {
  			return true
  		}
  		visited[current] = true
  		var parent models.EventDefinition
  		err := h.db.EventDefinitions().FindOne(ctx, bson.M{"_id": current}).Decode(&parent)
  		if err != nil {
  ... (8 more lines)
  ```

### `internal/api/handlers/webhook.go`

- **[HIGH] InsertOne on `messages`** — `internal/api/handlers/webhook.go:519` (loop at line 518, range loop over `m`) in `handleInvoicePaymentFailed`
  - _InsertOne call inside range loop_
  - Suggestion: Use InsertMany with a slice of documents instead of InsertOne in a loop.
  ```go
  	for _, m := range memberships {
  		h.db.Messages().InsertOne(ctx, models.Message{
  			UserID:    m.UserID,
  			Subject:   subject,
  			Body:      body,
  			IsSystem:  true,
  			Read:      false,
  			CreatedAt: time.Now(),
  ... (2 more lines)
  ```

### `internal/api/handlers/webhooks.go`

- **[HIGH] CountDocuments on `webhook_deliveries`** — `internal/api/handlers/webhooks.go:71` (loop at line 69, range loop over `k`) in `ListWebhooks`
  - _CountDocuments call inside range loop_
  - Suggestion: Use $in operator with a batch of IDs instead of querying in a loop. e.g. `col.Find(ctx, bson.M{"_id": bson.M{"$in": ids}})`
  ```go
  	for i, hook := range hooks {
  		result[i].Webhook = hook
  		count, err := h.db.WebhookDeliveries().CountDocuments(ctx, bson.M{
  			"webhookId": hook.ID,
  			"createdAt": bson.M{"$gte": since},
  		})
  		if err != nil {
  			slog.Warn("failed to count webhook deliveries", "webhookId", hook.ID, "error", err)
  ... (10 more lines)
  ```
- **[HIGH] FindOne on `webhook_deliveries`** — `internal/api/handlers/webhooks.go:83` (loop at line 69, range loop over `k`) in `ListWebhooks`
  - _FindOne call inside range loop_
  - Suggestion: Use $in operator with a batch of IDs instead of querying in a loop. e.g. `col.Find(ctx, bson.M{"_id": bson.M{"$in": ids}})`
  ```go
  	for i, hook := range hooks {
  		result[i].Webhook = hook
  		count, err := h.db.WebhookDeliveries().CountDocuments(ctx, bson.M{
  			"webhookId": hook.ID,
  			"createdAt": bson.M{"$gte": since},
  		})
  		if err != nil {
  			slog.Warn("failed to count webhook deliveries", "webhookId", hook.ID, "error", err)
  ... (10 more lines)
  ```

### `internal/configstore/seed.go`

- **[MEDIUM] FindOne on `config_vars`** — `internal/configstore/seed.go:380` (loop at line 379, range loop over `f`) in `Seed`
  - _FindOne call inside range loop_
  - Suggestion: Use $in operator with a batch of IDs instead of querying in a loop. e.g. `col.Find(ctx, bson.M{"_id": bson.M{"$in": ids}})`
  ```go
          for _, def := range SystemDefaults {
                  err := col.FindOne(ctx, bson.M{"name": def.Name}).Err()
                  if err == mongo.ErrNoDocuments {
                          def.CreatedAt = now
                          def.UpdatedAt = now
                          if _, err := col.InsertOne(ctx, def); err != nil {
                                  return err
                          }
  ... (5 more lines)
  ```
- **[MEDIUM] InsertOne on `config_vars`** — `internal/configstore/seed.go:384` (loop at line 379, range loop over `f`) in `Seed`
  - _InsertOne call inside range loop_
  - Suggestion: Use InsertMany with a slice of documents instead of InsertOne in a loop.
  ```go
          for _, def := range SystemDefaults {
                  err := col.FindOne(ctx, bson.M{"name": def.Name}).Err()
                  if err == mongo.ErrNoDocuments {
                          def.CreatedAt = now
                          def.UpdatedAt = now
                          if _, err := col.InsertOne(ctx, def); err != nil {
                                  return err
                          }
  ... (5 more lines)
  ```

### `internal/health/query.go`

- **[HIGH] FindOne on `system_metrics`** — `internal/health/query.go:98` (loop at line 96, range loop over `e`) in `GetCurrentMetrics`
  - _FindOne call inside range loop_
  - Suggestion: Use $in operator with a batch of IDs instead of querying in a loop. e.g. `col.Find(ctx, bson.M{"_id": bson.M{"$in": ids}})`
  ```go
          for _, node := range nodes {
                  var metric models.SystemMetric
                  err := s.db.SystemMetrics().FindOne(ctx,
                          bson.M{"nodeId": node.MachineID},
                          options.FindOne().SetSort(bson.D{{Key: "timestamp", Value: -1}}),
                  ).Decode(&metric)
                  if err == nil {
                          results = append(results, metric)
  ... (2 more lines)
  ```

### `internal/testutil/testutil.go`

- **[HIGH] DeleteMany on `dynamic:name`** — `internal/testutil/testutil.go:98` (loop at line 97, range loop over `e`) in `MustConnectTestDB`
  - _DeleteMany call inside range loop_
  - Suggestion: Batch this operation — issue a single bulk/multi-document call instead of one DB call per loop iteration.
  ```go
                  for _, name := range colls {
                          if _, err := database.Database.Collection(name).DeleteMany(ctx, bson.M{}); err != nil {
                                  log.Printf("testutil: warning: failed to delete from %s: %v", name, err)
                          }
                  }
  ```
- **[HIGH] DeleteMany on `dynamic:name`** — `internal/testutil/testutil.go:144` (loop at line 143, range loop over `e`) in `ConnectTestDB`
  - _DeleteMany call inside range loop_
  - Suggestion: Batch this operation — issue a single bulk/multi-document call instead of one DB call per loop iteration.
  ```go
                  for _, name := range colls {
                          if _, err := database.Database.Collection(name).DeleteMany(ctx, bson.M{}); err != nil {
                                  log.Printf("testutil: warning: failed to delete from %s: %v", name, err)
                          }
                  }
  ```
- **[HIGH] InsertOne on `system_logs`** — `internal/testutil/testutil.go:341` (loop at line 333, condition loop over `_`) in `InsertTestLogs`
  - _InsertOne call inside condition loop_
  - Suggestion: Use InsertMany with a slice of documents instead of InsertOne in a loop.
  ```go
          for i := 0; i < count; i++ {
                  entry := models.SystemLog{
                          ID:        primitive.NewObjectID(),
                          Severity:  severity,
                          Category:  category,
                          Message:   fmt.Sprintf("Test log entry %d", i+1),
                          CreatedAt: time.Now().Add(-time.Duration(i) * time.Minute),
                  }
  ... (5 more lines)
  ```
- **[MEDIUM] DeleteMany on `dynamic:name`** — `internal/testutil/testutil.go:227` (loop at line 226, range loop over `e`) in `CleanupCollections`
  - _DeleteMany call inside range loop_
  - Suggestion: Batch this operation — issue a single bulk/multi-document call instead of one DB call per loop iteration.
  ```go
          for _, name := range collections {
                  if _, err := database.Database.Collection(name).DeleteMany(ctx, bson.M{}); err != nil {
                          log.Printf("testutil: warning: failed to delete from %s: %v", name, err)
                  }
          }
  ```

## Methodology

1. Each `.go` file is masked (strings/comments blanked out, length and newlines preserved) so brace-matching is safe.
2. Every loop header (`for ... {`) is located and the matching `}` is found via depth counting. The loop body spans lines `start_line+1` to `end_line`. Nested loops are recorded separately.
3. Every line is scanned for a MongoDB collection method call (Find, FindOne, InsertOne, InsertMany, UpdateOne, UpdateMany, ReplaceOne, DeleteOne, DeleteMany, Aggregate, CountDocuments, EstimatedDocumentCount). Option-builder calls like `options.Find()` are skipped.
4. For each DB-op line that falls inside a loop body, the collection is resolved via (a) literal `db.Collection("name")`, (b) an accessor call like `m.Users()`, or (c) an aliased local variable like `col := m.Users()`.
5. Risk is **HIGH** for queries in user-facing handler code, **MEDIUM** for admin/CLI/batch paths (still bad, but lower blast radius).
6. Test files (`*_test.go`) are skipped by default; pass `--include-tests` to include them.

---
_Generated by `graphify n-plus-1`._