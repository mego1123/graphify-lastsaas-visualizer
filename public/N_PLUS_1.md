# N+1 Query Detection Report

**Target:** `/home/z/my-project/repos/lastsaas`

Finds MongoDB queries that run inside loop bodies. Each such query is an N+1 problem: the loop runs N times, and each iteration hits the database — N+1 round trips instead of one.

## Summary

| Metric | Value |
| --- | --- |
| Total N+1 findings | **21** |
| HIGH severity | 0 |
| MEDIUM severity | 6 |
| LOW severity | 15 |

## Operations Involved

| Operation | Count |
| --- | ---: |
| `FindOne` | 7 |
| `DeleteMany` | 4 |
| `CountDocuments` | 3 |
| `Find` | 2 |
| `DeleteOne` | 2 |
| `InsertOne` | 2 |
| `UpdateOne` | 1 |

## Collections Affected

| Collection | Count |
| --- | ---: |
| `tenant_memberships` | 6 |
| `tenants` | 5 |
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
| `range` | 20 |
| `infinite` | 1 |

## Files With Most Findings

| File | Findings |
| --- | ---: |
| `backend/internal/api/handlers/admin.go` | 9 |
| `backend/internal/api/handlers/auth.go` | 5 |
| `backend/internal/api/handlers/webhooks.go` | 2 |
| `backend/internal/configstore/seed.go` | 2 |
| `backend/internal/api/handlers/event_definitions.go` | 1 |
| `backend/internal/api/handlers/webhook.go` | 1 |
| `backend/internal/health/query.go` | 1 |

## Detailed Findings

### `backend/internal/api/handlers/admin.go`

- **[LOW] Find on `tenant_memberships`** — `backend/internal/api/handlers/admin.go:1280` (loop at line 1277, range loop over `m`) in `PreflightDeleteUser`
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
- **[LOW] Find on `users`** — `backend/internal/api/handlers/admin.go:1301` (loop at line 1277, range loop over `m`) in `PreflightDeleteUser`
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
- **[LOW] FindOne on `tenants`** — `backend/internal/api/handlers/admin.go:1398` (loop at line 1392, range loop over `m`) in `DeleteUser`
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
- **[LOW] UpdateOne on `tenant_memberships`** — `backend/internal/api/handlers/admin.go:1414` (loop at line 1392, range loop over `m`) in `DeleteUser`
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
- **[LOW] CountDocuments on `tenant_memberships`** — `backend/internal/api/handlers/admin.go:1430` (loop at line 1392, range loop over `m`) in `DeleteUser`
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
- **[LOW] DeleteMany on `tenant_memberships`** — `backend/internal/api/handlers/admin.go:1454` (loop at line 1392, range loop over `m`) in `DeleteUser`
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
- **[LOW] DeleteOne on `tenants`** — `backend/internal/api/handlers/admin.go:1457` (loop at line 1392, range loop over `m`) in `DeleteUser`
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
- **[LOW] DeleteMany on `invitations`** — `backend/internal/api/handlers/admin.go:1460` (loop at line 1392, range loop over `m`) in `DeleteUser`
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
- **[LOW] FindOne on `tenants`** — `backend/internal/api/handlers/admin.go:1680` (loop at line 1678, range loop over `m`) in `ImpersonateUser`
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

### `backend/internal/api/handlers/auth.go`

- **[LOW] FindOne on `tenants`** — `backend/internal/api/handlers/auth.go:2286` (loop at line 2280, range loop over `m`) in `DeleteAccount`
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
- **[LOW] CountDocuments on `tenant_memberships`** — `backend/internal/api/handlers/auth.go:2295` (loop at line 2280, range loop over `m`) in `DeleteAccount`
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
- **[LOW] DeleteMany on `tenant_memberships`** — `backend/internal/api/handlers/auth.go:2305` (loop at line 2280, range loop over `m`) in `DeleteAccount`
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
- **[LOW] DeleteOne on `tenants`** — `backend/internal/api/handlers/auth.go:2308` (loop at line 2280, range loop over `m`) in `DeleteAccount`
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
- **[LOW] DeleteMany on `invitations`** — `backend/internal/api/handlers/auth.go:2311` (loop at line 2280, range loop over `m`) in `DeleteAccount`
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

### `backend/internal/api/handlers/event_definitions.go`

- **[MEDIUM] FindOne on `event_definitions`** — `backend/internal/api/handlers/event_definitions.go:463` (loop at line 457, infinite loop over `_`) in `wouldCreateCycle`
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

### `backend/internal/api/handlers/webhook.go`

- **[LOW] InsertOne on `messages`** — `backend/internal/api/handlers/webhook.go:519` (loop at line 518, range loop over `m`) in `handleInvoicePaymentFailed`
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

### `backend/internal/api/handlers/webhooks.go`

- **[MEDIUM] CountDocuments on `webhook_deliveries`** — `backend/internal/api/handlers/webhooks.go:71` (loop at line 69, range loop over `hook`) in `ListWebhooks`
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
- **[MEDIUM] FindOne on `webhook_deliveries`** — `backend/internal/api/handlers/webhooks.go:83` (loop at line 69, range loop over `hook`) in `ListWebhooks`
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

### `backend/internal/configstore/seed.go`

- **[MEDIUM] FindOne on `config_vars`** — `backend/internal/configstore/seed.go:380` (loop at line 379, range loop over `def`) in `Seed`
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
- **[MEDIUM] InsertOne on `config_vars`** — `backend/internal/configstore/seed.go:384` (loop at line 379, range loop over `def`) in `Seed`
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

### `backend/internal/health/query.go`

- **[MEDIUM] FindOne on `system_metrics`** — `backend/internal/health/query.go:98` (loop at line 96, range loop over `node`) in `GetCurrentMetrics`
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

## Methodology

1. Each `.go` file is masked (strings/comments blanked out, length and newlines preserved) so brace-matching is safe.
2. Every loop header (`for ... {`) is located and the matching `}` is found via depth counting. The loop body spans lines `start_line+1` to `end_line`. Nested loops are recorded separately.
3. Every line is scanned for a MongoDB collection method call (Find, FindOne, InsertOne, InsertMany, UpdateOne, UpdateMany, ReplaceOne, DeleteOne, DeleteMany, Aggregate, CountDocuments, EstimatedDocumentCount). Option-builder calls like `options.Find()` are skipped.
4. For each DB-op line that falls inside a loop body, the collection is resolved via (a) literal `db.Collection("name")`, (b) an accessor call like `m.Users()`, or (c) an aliased local variable like `col := m.Users()`.
5. Risk is **HIGH** for queries whose loop iterates over a potentially-large collection (users, logs, transactions, events, messages, deliveries). **MEDIUM** for admin/CLI/batch code paths. **LOW** for loops over small-N collections (memberships, tenants — N is typically 1-5) and for test/CLI scaffolding that is excluded from the analysis entirely.
6. Test files (`*_test.go`), test utilities (`internal/testutil/`), and CLI tools (`cmd/lastsaas/`) are skipped entirely — deleting rows in a loop in test cleanup, or iterating results for CLI display, is intentional and not an N+1 problem.

---
_Generated by `graphify n-plus-1`._