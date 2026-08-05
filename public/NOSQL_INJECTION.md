# NoSQL Injection Audit

**Target:** `/home/z/my-project/repos/lastsaas`

## Summary (non-test files)

| Metric | Value |
| --- | ---: |
| Files scanned | 101 |
| Total lines | 29,012 |
| MongoDB queries scanned | **598** |
| Total findings | 151 |
| Risky findings (CRITICAL/HIGH/MEDIUM) | **25** |
| Sanitized (LOW) | 126 |

### Findings by risk

| Risk | Count | Meaning |
| --- | ---: | --- |
| CRITICAL | 0 | `$where` with user input — JS injection |
| HIGH | 25 | Direct user input in filter / `$regex` injection |
| MEDIUM | 0 | User input in `$or`/`$and`/`$nor` arrays |
| LOW | 126 | User input was sanitized before query |

### Findings by user-input source

| Source | Count |
| --- | ---: |
| sanitized | 112 |
| json-body | 21 |
| path | 7 |
| query | 6 |
| tracer | 4 |
| form | 1 |

## Top Files by Risk

| File | Queries | Findings | CRITICAL | HIGH | MEDIUM | LOW |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `backend/internal/api/handlers/auth.go` | 97 | 13 | 0 | 9 | 0 | 4 |
| `backend/internal/api/handlers/branding.go` | 20 | 7 | 0 | 6 | 0 | 1 |
| `backend/internal/api/handlers/usage.go` | 5 | 4 | 0 | 4 | 0 | 0 |
| `backend/internal/api/handlers/admin.go` | 78 | 40 | 0 | 2 | 0 | 38 |
| `backend/internal/api/handlers/tenant.go` | 26 | 14 | 0 | 2 | 0 | 12 |
| `backend/internal/api/handlers/config.go` | 3 | 2 | 0 | 2 | 0 | 0 |
| `backend/internal/api/handlers/plans.go` | 31 | 22 | 0 | 0 | 0 | 22 |
| `backend/internal/api/handlers/event_definitions.go` | 17 | 12 | 0 | 0 | 0 | 12 |
| `backend/internal/api/handlers/billing.go` | 22 | 9 | 0 | 0 | 0 | 9 |
| `backend/internal/api/handlers/bundles.go` | 13 | 8 | 0 | 0 | 0 | 8 |
| `backend/internal/api/handlers/webhook.go` | 35 | 8 | 0 | 0 | 0 | 8 |
| `backend/internal/api/handlers/webhooks.go` | 15 | 4 | 0 | 0 | 0 | 4 |
| `backend/internal/api/handlers/announcements.go` | 7 | 2 | 0 | 0 | 0 | 2 |
| `backend/internal/middleware/tenant.go` | 3 | 2 | 0 | 0 | 0 | 2 |
| `backend/cmd/lastsaas/cmd_financial.go` | 11 | 1 | 0 | 0 | 0 | 1 |
| `backend/cmd/lastsaas/cmd_tenants.go` | 9 | 1 | 0 | 0 | 0 | 1 |
| `backend/internal/api/handlers/messages.go` | 4 | 1 | 0 | 0 | 0 | 1 |
| `backend/internal/middleware/auth.go` | 6 | 1 | 0 | 0 | 0 | 1 |
| `backend/cmd/lastsaas/cmd_db.go` | 0 | 0 | 0 | 0 | 0 | 0 |
| `backend/cmd/lastsaas/cmd_doctor.go` | 4 | 0 | 0 | 0 | 0 | 0 |

## Detailed Findings

### `backend/cmd/lastsaas/cmd_financial.go`

- **[LOW] Find** — `backend/cmd/lastsaas/cmd_financial.go:231` in `cmdFinancialTransactions`
  - **Field:** `tenantId`
  - **Source:** `sanitized:primitive.ObjectIDFromHex(*tenantID)` (var `oid`)
  - **Sanitized:** yes, via `primitive.ObjectIDFromHex`
  - _value passed through sanitizer 'primitive.ObjectIDFromHex' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
          cursor, err := database.FinancialTransactions().Find(ctx, filter, opts)
  ```

### `backend/cmd/lastsaas/cmd_tenants.go`

- **[LOW] FindOne** — `backend/cmd/lastsaas/cmd_tenants.go:160` in `cmdTenantsGet`
  - **Field:** `_id`
  - **Source:** `sanitized:primitive.ObjectIDFromHex(idOrSlug)` (var `oid`)
  - **Sanitized:** yes, via `primitive.ObjectIDFromHex`
  - _value passed through sanitizer 'primitive.ObjectIDFromHex' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
                  if err := database.Tenants().FindOne(ctx, bson.M{"_id": oid}).Decode(&tenant); err != nil {
  ```

### `backend/internal/api/handlers/admin.go`

- **[HIGH] FindOne** — `backend/internal/api/handlers/admin.go:1837` in `InviteRootMember`
  - **Field:** `email`
  - **Source:** `json-body:req.Email` (var `req.Email`)
  - **Sanitized:** no
  - _direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  	if h.db.Users().FindOne(ctx, bson.M{"email": req.Email}).Decode(&existingUser) == nil {
  ```
- **[HIGH] CountDocuments** — `backend/internal/api/handlers/admin.go:1853` in `InviteRootMember`
  - **Field:** `email`
  - **Source:** `json-body:req.Email` (var `req.Email`)
  - **Sanitized:** no
  - _direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  	invCount, err := h.db.Invitations().CountDocuments(ctx, bson.M{
  		"tenantId":  rootTenant.ID,
  		"email":     req.Email,
  		"status":    models.InvitationPending,
  		"expiresAt": bson.M{"$gt": time.Now()},
  	})
  ```
- **[LOW] CountDocuments** — `backend/internal/api/handlers/admin.go:153` in `ListTenants`
  - **Field:** `billingStatus`
  - **Source:** `query:billingStatus` (var `bs`)
  - **Sanitized:** yes, via `switch-allowlist`
  - _value passed through sanitizer 'switch-allowlist' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  	total, err := h.db.Tenants().CountDocuments(ctx, filter)
  ```
- **[LOW] Find** — `backend/internal/api/handlers/admin.go:153` in `ListTenants`
  - **Field:** `billingStatus`
  - **Source:** `query:billingStatus` (var `bs`)
  - **Sanitized:** yes, via `switch-allowlist`
  - _value passed through sanitizer 'switch-allowlist' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  	cursor, err := h.db.Tenants().Find(ctx, filter, opts)
  ```
- **[LOW] Find** — `backend/internal/api/handlers/admin.go:304` in `ExportTenantsCSV`
  - **Field:** `billingStatus`
  - **Source:** `query:billingStatus` (var `bs`)
  - **Sanitized:** yes, via `switch-allowlist`
  - _value passed through sanitizer 'switch-allowlist' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  	cursor, err := h.db.Tenants().Find(ctx, filter, opts)
  ```
- **[LOW] FindOne** — `backend/internal/api/handlers/admin.go:418` in `GetTenant`
  - **Field:** `_id`
  - **Source:** `sanitized:primitive.ObjectIDFromHex(tenantIDStr)` (var `tenantID`)
  - **Sanitized:** yes, via `primitive.ObjectIDFromHex`
  - _value passed through sanitizer 'primitive.ObjectIDFromHex' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  	if err := h.db.Tenants().FindOne(r.Context(), bson.M{"_id": tenantID}).Decode(&tenant); err != nil {
  ```
- **[LOW] Find** — `backend/internal/api/handlers/admin.go:424` in `GetTenant`
  - **Field:** `tenantId`
  - **Source:** `sanitized:primitive.ObjectIDFromHex(tenantIDStr)` (var `tenantID`)
  - **Sanitized:** yes, via `primitive.ObjectIDFromHex`
  - _value passed through sanitizer 'primitive.ObjectIDFromHex' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  	cursor, err := h.db.TenantMemberships().Find(r.Context(), bson.M{"tenantId": tenantID})
  ```
- **[LOW] FindOne** — `backend/internal/api/handlers/admin.go:483` in `UpdateTenantStatus`
  - **Field:** `_id`
  - **Source:** `sanitized:primitive.ObjectIDFromHex(tenantIDStr)` (var `tenantID`)
  - **Sanitized:** yes, via `primitive.ObjectIDFromHex`
  - _value passed through sanitizer 'primitive.ObjectIDFromHex' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  	if err := h.db.Tenants().FindOne(r.Context(), bson.M{"_id": tenantID}).Decode(&tenant); err != nil {
  ```
- **[LOW] UpdateOne** — `backend/internal/api/handlers/admin.go:502` in `UpdateTenantStatus`
  - **Field:** `_id`
  - **Source:** `sanitized:primitive.ObjectIDFromHex(tenantIDStr)` (var `tenantID`)
  - **Sanitized:** yes, via `primitive.ObjectIDFromHex`
  - _value passed through sanitizer 'primitive.ObjectIDFromHex' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  	h.db.Tenants().UpdateOne(r.Context(),
  		bson.M{"_id": tenantID},
  		bson.M{"$set": bson.M{"isActive": req.IsActive, "updatedAt": time.Now()}},
  	)
  ```
- **[LOW] UpdateOne** — `backend/internal/api/handlers/admin.go:774` in `UpdateUserStatus`
  - **Field:** `_id`
  - **Source:** `sanitized:primitive.ObjectIDFromHex(userIDStr)` (var `userID`)
  - **Sanitized:** yes, via `primitive.ObjectIDFromHex`
  - _value passed through sanitizer 'primitive.ObjectIDFromHex' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  	result, err := h.db.Users().UpdateOne(r.Context(),
  		bson.M{"_id": userID},
  		bson.M{"$set": bson.M{"isActive": req.IsActive, "updatedAt": time.Now()}},
  	)
  ```
- **[LOW] FindOne** — `backend/internal/api/handlers/admin.go:943` in `GetUser`
  - **Field:** `_id`
  - **Source:** `sanitized:primitive.ObjectIDFromHex(mux.Vars(r)["userId"])` (var `userID`)
  - **Sanitized:** yes, via `primitive.ObjectIDFromHex`
  - _value passed through sanitizer 'primitive.ObjectIDFromHex' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  	if err := h.db.Users().FindOne(r.Context(), bson.M{"_id": userID}).Decode(&user); err != nil {
  ```
- **[LOW] Find** — `backend/internal/api/handlers/admin.go:948` in `GetUser`
  - **Field:** `userId`
  - **Source:** `sanitized:primitive.ObjectIDFromHex(mux.Vars(r)["userId"])` (var `userID`)
  - **Sanitized:** yes, via `primitive.ObjectIDFromHex`
  - _value passed through sanitizer 'primitive.ObjectIDFromHex' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  	cursor, err := h.db.TenantMemberships().Find(r.Context(), bson.M{"userId": userID})
  ```
- **[LOW] FindOne** — `backend/internal/api/handlers/admin.go:1079` in `UpdateUser`
  - **Field:** `_id`
  - **Source:** `sanitized:primitive.ObjectIDFromHex(mux.Vars(r)["userId"])` (var `userID`)
  - **Sanitized:** yes, via `primitive.ObjectIDFromHex`
  - _value passed through sanitizer 'primitive.ObjectIDFromHex' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  	if err := h.db.Users().FindOne(r.Context(), bson.M{"_id": userID}).Decode(&user); err != nil {
  ```
- **[LOW] CountDocuments** — `backend/internal/api/handlers/admin.go:1098` in `UpdateUser`
  - **Field:** `_id.$ne`
  - **Source:** `sanitized:primitive.ObjectIDFromHex(mux.Vars(r)["userId"])` (var `userID`)
  - **Sanitized:** yes, via `primitive.ObjectIDFromHex`
  - _value passed through sanitizer 'primitive.ObjectIDFromHex' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  			count, err := h.db.Users().CountDocuments(r.Context(), bson.M{"email": newEmail, "_id": bson.M{"$ne": userID}})
  ```
- **[LOW] CountDocuments** — `backend/internal/api/handlers/admin.go:1098` in `UpdateUser`
  - **Field:** `_id`
  - **Source:** `sanitized:primitive.ObjectIDFromHex(mux.Vars(r)["userId"])` (var `userID`)
  - **Sanitized:** yes, via `primitive.ObjectIDFromHex`
  - _value passed through sanitizer 'primitive.ObjectIDFromHex' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  			count, err := h.db.Users().CountDocuments(r.Context(), bson.M{"email": newEmail, "_id": bson.M{"$ne": userID}})
  ```
- **[LOW] UpdateOne** — `backend/internal/api/handlers/admin.go:1121` in `UpdateUser`
  - **Field:** `_id`
  - **Source:** `sanitized:primitive.ObjectIDFromHex(mux.Vars(r)["userId"])` (var `userID`)
  - **Sanitized:** yes, via `primitive.ObjectIDFromHex`
  - _value passed through sanitizer 'primitive.ObjectIDFromHex' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  	if _, err := h.db.Users().UpdateOne(r.Context(), bson.M{"_id": userID}, bson.M{"$set": updates}); err != nil {
  ```
- **[LOW] FindOne** — `backend/internal/api/handlers/admin.go:1165` in `UpdateUserRole`
  - **Field:** `_id`
  - **Source:** `sanitized:primitive.ObjectIDFromHex(vars["tenantId"])` (var `tenantID`)
  - **Sanitized:** yes, via `primitive.ObjectIDFromHex`
  - _value passed through sanitizer 'primitive.ObjectIDFromHex' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  	if err := h.db.Tenants().FindOne(r.Context(), bson.M{"_id": tenantID}).Decode(&tenant); err != nil {
  ```
- **[LOW] FindOne** — `backend/internal/api/handlers/admin.go:1182` in `UpdateUserRole`
  - **Field:** `tenantId`
  - **Source:** `sanitized:primitive.ObjectIDFromHex(vars["tenantId"])` (var `tenantID`)
  - **Sanitized:** yes, via `primitive.ObjectIDFromHex`
  - _value passed through sanitizer 'primitive.ObjectIDFromHex' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  		if err := h.db.TenantMemberships().FindOne(ctx, bson.M{
  			"tenantId": tenantID,
  			"role":     models.RoleOwner,
  		}).Decode(&currentOwner); err == nil {
  ```
- **[LOW] UpdateOne** — `backend/internal/api/handlers/admin.go:1193` in `UpdateUserRole`
  - **Field:** `userId`
  - **Source:** `sanitized:primitive.ObjectIDFromHex(vars["userId"])` (var `userID`)
  - **Sanitized:** yes, via `primitive.ObjectIDFromHex`
  - _value passed through sanitizer 'primitive.ObjectIDFromHex' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  	result, err := h.db.TenantMemberships().UpdateOne(ctx,
  		bson.M{"userId": userID, "tenantId": tenantID},
  		bson.M{"$set": bson.M{"role": req.Role, "updatedAt": now}},
  	)
  ```
- **[LOW] UpdateOne** — `backend/internal/api/handlers/admin.go:1193` in `UpdateUserRole`
  - **Field:** `tenantId`
  - **Source:** `sanitized:primitive.ObjectIDFromHex(vars["tenantId"])` (var `tenantID`)
  - **Sanitized:** yes, via `primitive.ObjectIDFromHex`
  - _value passed through sanitizer 'primitive.ObjectIDFromHex' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  	result, err := h.db.TenantMemberships().UpdateOne(ctx,
  		bson.M{"userId": userID, "tenantId": tenantID},
  		bson.M{"$set": bson.M{"role": req.Role, "updatedAt": now}},
  	)
  ```
- **[LOW] Find** — `backend/internal/api/handlers/admin.go:1243` in `PreflightDeleteUser`
  - **Field:** `userId`
  - **Source:** `sanitized:primitive.ObjectIDFromHex(mux.Vars(r)["userId"])` (var `userID`)
  - **Sanitized:** yes, via `primitive.ObjectIDFromHex`
  - _value passed through sanitizer 'primitive.ObjectIDFromHex' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  	cursor, err := h.db.TenantMemberships().Find(ctx, bson.M{"userId": userID, "role": models.RoleOwner})
  ```
- **[LOW] Find** — `backend/internal/api/handlers/admin.go:1280` in `PreflightDeleteUser`
  - **Field:** `userId.$ne`
  - **Source:** `sanitized:primitive.ObjectIDFromHex(mux.Vars(r)["userId"])` (var `userID`)
  - **Sanitized:** yes, via `primitive.ObjectIDFromHex`
  - _value passed through sanitizer 'primitive.ObjectIDFromHex' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  		memberCursor, err := h.db.TenantMemberships().Find(ctx, bson.M{
  			"tenantId": m.TenantID,
  			"userId":   bson.M{"$ne": userID},
  		})
  ```
- **[LOW] Find** — `backend/internal/api/handlers/admin.go:1280` in `PreflightDeleteUser`
  - **Field:** `userId`
  - **Source:** `sanitized:primitive.ObjectIDFromHex(mux.Vars(r)["userId"])` (var `userID`)
  - **Sanitized:** yes, via `primitive.ObjectIDFromHex`
  - _value passed through sanitizer 'primitive.ObjectIDFromHex' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  		memberCursor, err := h.db.TenantMemberships().Find(ctx, bson.M{
  			"tenantId": m.TenantID,
  			"userId":   bson.M{"$ne": userID},
  		})
  ```
- **[LOW] FindOne** — `backend/internal/api/handlers/admin.go:1358` in `DeleteUser`
  - **Field:** `_id`
  - **Source:** `sanitized:primitive.ObjectIDFromHex(mux.Vars(r)["userId"])` (var `userID`)
  - **Sanitized:** yes, via `primitive.ObjectIDFromHex`
  - _value passed through sanitizer 'primitive.ObjectIDFromHex' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  	if err := h.db.Users().FindOne(r.Context(), bson.M{"_id": userID}).Decode(&user); err != nil {
  ```
- **[LOW] Find** — `backend/internal/api/handlers/admin.go:1378` in `DeleteUser`
  - **Field:** `userId`
  - **Source:** `sanitized:primitive.ObjectIDFromHex(mux.Vars(r)["userId"])` (var `userID`)
  - **Sanitized:** yes, via `primitive.ObjectIDFromHex`
  - _value passed through sanitizer 'primitive.ObjectIDFromHex' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  	cursor, err := h.db.TenantMemberships().Find(ctx, bson.M{"userId": userID})
  ```
- **[LOW] UpdateOne** — `backend/internal/api/handlers/admin.go:1414` in `DeleteUser`
  - **Field:** `userId`
  - **Source:** `sanitized:primitive.ObjectIDFromHex(replacementStr)` (var `replacementID`)
  - **Sanitized:** yes, via `primitive.ObjectIDFromHex`
  - _value passed through sanitizer 'primitive.ObjectIDFromHex' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  			result, err := h.db.TenantMemberships().UpdateOne(ctx,
  				bson.M{"userId": replacementID, "tenantId": m.TenantID},
  				bson.M{"$set": bson.M{"role": models.RoleOwner, "updatedAt": time.Now()}},
  			)
  ```
- **[LOW] CountDocuments** — `backend/internal/api/handlers/admin.go:1430` in `DeleteUser`
  - **Field:** `userId.$ne`
  - **Source:** `sanitized:primitive.ObjectIDFromHex(mux.Vars(r)["userId"])` (var `userID`)
  - **Sanitized:** yes, via `primitive.ObjectIDFromHex`
  - _value passed through sanitizer 'primitive.ObjectIDFromHex' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  			otherCount, err := h.db.TenantMemberships().CountDocuments(ctx, bson.M{
  				"tenantId": m.TenantID,
  				"userId":   bson.M{"$ne": userID},
  			})
  ```
- **[LOW] CountDocuments** — `backend/internal/api/handlers/admin.go:1430` in `DeleteUser`
  - **Field:** `userId`
  - **Source:** `sanitized:primitive.ObjectIDFromHex(mux.Vars(r)["userId"])` (var `userID`)
  - **Sanitized:** yes, via `primitive.ObjectIDFromHex`
  - _value passed through sanitizer 'primitive.ObjectIDFromHex' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  			otherCount, err := h.db.TenantMemberships().CountDocuments(ctx, bson.M{
  				"tenantId": m.TenantID,
  				"userId":   bson.M{"$ne": userID},
  			})
  ```
- **[LOW] DeleteMany** — `backend/internal/api/handlers/admin.go:1479` in `DeleteUser`
  - **Field:** `userId`
  - **Source:** `sanitized:primitive.ObjectIDFromHex(mux.Vars(r)["userId"])` (var `userID`)
  - **Sanitized:** yes, via `primitive.ObjectIDFromHex`
  - _value passed through sanitizer 'primitive.ObjectIDFromHex' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  	if _, err := h.db.TenantMemberships().DeleteMany(ctx, bson.M{"userId": userID}); err != nil {
  ```
- **[LOW] DeleteMany** — `backend/internal/api/handlers/admin.go:1482` in `DeleteUser`
  - **Field:** `userId`
  - **Source:** `sanitized:primitive.ObjectIDFromHex(mux.Vars(r)["userId"])` (var `userID`)
  - **Sanitized:** yes, via `primitive.ObjectIDFromHex`
  - _value passed through sanitizer 'primitive.ObjectIDFromHex' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  	if _, err := h.db.RefreshTokens().DeleteMany(ctx, bson.M{"userId": userID}); err != nil {
  ```
- **[LOW] DeleteMany** — `backend/internal/api/handlers/admin.go:1485` in `DeleteUser`
  - **Field:** `userId`
  - **Source:** `sanitized:primitive.ObjectIDFromHex(mux.Vars(r)["userId"])` (var `userID`)
  - **Sanitized:** yes, via `primitive.ObjectIDFromHex`
  - _value passed through sanitizer 'primitive.ObjectIDFromHex' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  	if _, err := h.db.Messages().DeleteMany(ctx, bson.M{"userId": userID}); err != nil {
  ```
- **[LOW] DeleteOne** — `backend/internal/api/handlers/admin.go:1488` in `DeleteUser`
  - **Field:** `_id`
  - **Source:** `sanitized:primitive.ObjectIDFromHex(mux.Vars(r)["userId"])` (var `userID`)
  - **Sanitized:** yes, via `primitive.ObjectIDFromHex`
  - _value passed through sanitizer 'primitive.ObjectIDFromHex' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  	if _, err := h.db.Users().DeleteOne(ctx, bson.M{"_id": userID}); err != nil {
  ```
- **[LOW] FindOne** — `backend/internal/api/handlers/admin.go:1529` in `UpdateTenant`
  - **Field:** `_id`
  - **Source:** `sanitized:primitive.ObjectIDFromHex(mux.Vars(r)["tenantId"])` (var `tenantID`)
  - **Sanitized:** yes, via `primitive.ObjectIDFromHex`
  - _value passed through sanitizer 'primitive.ObjectIDFromHex' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  	if err := h.db.Tenants().FindOne(r.Context(), bson.M{"_id": tenantID}).Decode(&tenant); err != nil {
  ```
- **[LOW] UpdateOne** — `backend/internal/api/handlers/admin.go:1587` in `UpdateTenant`
  - **Field:** `_id`
  - **Source:** `sanitized:primitive.ObjectIDFromHex(mux.Vars(r)["tenantId"])` (var `tenantID`)
  - **Sanitized:** yes, via `primitive.ObjectIDFromHex`
  - _value passed through sanitizer 'primitive.ObjectIDFromHex' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  	if _, err := h.db.Tenants().UpdateOne(r.Context(), bson.M{"_id": tenantID}, bson.M{"$set": updates}); err != nil {
  ```
- **[LOW] FindOne** — `backend/internal/api/handlers/admin.go:1619` in `ImpersonateUser`
  - **Field:** `_id`
  - **Source:** `sanitized:primitive.ObjectIDFromHex(mux.Vars(r)["userId"])` (var `targetUserID`)
  - **Sanitized:** yes, via `primitive.ObjectIDFromHex`
  - _value passed through sanitizer 'primitive.ObjectIDFromHex' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  	if err := h.db.Users().FindOne(r.Context(), bson.M{"_id": targetUserID}).Decode(&targetUser); err != nil {
  ```
- **[LOW] FindOne** — `backend/internal/api/handlers/admin.go:1628` in `ImpersonateUser`
  - **Field:** `userId`
  - **Source:** `sanitized:primitive.ObjectIDFromHex(mux.Vars(r)["userId"])` (var `targetUserID`)
  - **Sanitized:** yes, via `primitive.ObjectIDFromHex`
  - _value passed through sanitizer 'primitive.ObjectIDFromHex' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  		err := h.db.TenantMemberships().FindOne(r.Context(), bson.M{
  			"userId":   targetUserID,
  			"tenantId": rootTenant.ID,
  			"role":     models.RoleOwner,
  		}).Decode(&membership)
  ```
- **[LOW] Find** — `backend/internal/api/handlers/admin.go:1667` in `ImpersonateUser`
  - **Field:** `userId`
  - **Source:** `sanitized:primitive.ObjectIDFromHex(mux.Vars(r)["userId"])` (var `targetUserID`)
  - **Sanitized:** yes, via `primitive.ObjectIDFromHex`
  - _value passed through sanitizer 'primitive.ObjectIDFromHex' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  	cursor, err := h.db.TenantMemberships().Find(r.Context(), bson.M{"userId": targetUserID})
  ```
- **[LOW] FindOne** — `backend/internal/api/handlers/admin.go:1946` in `RemoveRootMember`
  - **Field:** `userId`
  - **Source:** `sanitized:primitive.ObjectIDFromHex(mux.Vars(r)["userId"])` (var `targetUserID`)
  - **Sanitized:** yes, via `primitive.ObjectIDFromHex`
  - _value passed through sanitizer 'primitive.ObjectIDFromHex' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  	if err := h.db.TenantMemberships().FindOne(ctx, bson.M{
  		"userId":   targetUserID,
  		"tenantId": rootTenant.ID,
  	}).Decode(&targetMembership); err != nil {
  ```
- **[LOW] UpdateOne** — `backend/internal/api/handlers/admin.go:2032` in `ChangeRootMemberRole`
  - **Field:** `userId`
  - **Source:** `sanitized:primitive.ObjectIDFromHex(mux.Vars(r)["userId"])` (var `targetUserID`)
  - **Sanitized:** yes, via `primitive.ObjectIDFromHex`
  - _value passed through sanitizer 'primitive.ObjectIDFromHex' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  	result, err := h.db.TenantMemberships().UpdateOne(ctx,
  		bson.M{"userId": targetUserID, "tenantId": rootTenant.ID},
  		bson.M{"$set": bson.M{"role": req.Role, "updatedAt": time.Now()}},
  	)
  ```
- **[LOW] DeleteOne** — `backend/internal/api/handlers/admin.go:2074` in `CancelRootInvitation`
  - **Field:** `_id`
  - **Source:** `sanitized:primitive.ObjectIDFromHex(mux.Vars(r)["invitationId"])` (var `invID`)
  - **Sanitized:** yes, via `primitive.ObjectIDFromHex`
  - _value passed through sanitizer 'primitive.ObjectIDFromHex' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  	result, err := h.db.Invitations().DeleteOne(ctx, bson.M{
  		"_id":      invID,
  		"tenantId": rootTenant.ID,
  		"status":   models.InvitationPending,
  	})
  ```

### `backend/internal/api/handlers/announcements.go`

- **[LOW] UpdateOne** — `backend/internal/api/handlers/announcements.go:152` in `Update`
  - **Field:** `_id`
  - **Source:** `sanitized:primitive.ObjectIDFromHex(mux.Vars(r)["id"])` (var `id`)
  - **Sanitized:** yes, via `primitive.ObjectIDFromHex`
  - _value passed through sanitizer 'primitive.ObjectIDFromHex' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  	result, err := h.db.Announcements().UpdateOne(r.Context(), bson.M{"_id": id}, bson.M{"$set": update})
  ```
- **[LOW] DeleteOne** — `backend/internal/api/handlers/announcements.go:168` in `Delete`
  - **Field:** `_id`
  - **Source:** `sanitized:primitive.ObjectIDFromHex(mux.Vars(r)["id"])` (var `id`)
  - **Sanitized:** yes, via `primitive.ObjectIDFromHex`
  - _value passed through sanitizer 'primitive.ObjectIDFromHex' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  	result, err := h.db.Announcements().DeleteOne(r.Context(), bson.M{"_id": id})
  ```

### `backend/internal/api/handlers/auth.go`

- **[HIGH] FindOne** — `backend/internal/api/handlers/auth.go:330` in `Login`
  - **Field:** `email`
  - **Source:** `json-body:req.Email` (var `req.Email`)
  - **Sanitized:** no
  - _direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
          if err := h.db.Users().FindOne(r.Context(), bson.M{"email": req.Email}).Decode(&user); err != nil {
  ```
- **[HIGH] FindOneAndUpdate** — `backend/internal/api/handlers/auth.go:601` in `VerifyEmail`
  - **Field:** `token`
  - **Source:** `json-body:req.Token` (var `req.Token`)
  - **Sanitized:** no
  - _direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
          err := h.db.VerificationTokens().FindOneAndUpdate(
                  r.Context(),
                  bson.M{
                          "token":     hashToken(req.Token),
                          "type":      models.TokenTypeEmailVerification,
                          "usedAt":    nil,
                          "expiresAt": bson.M{"$gt": now},
                  },
  ... (2 more lines)
  ```
- **[HIGH] FindOne** — `backend/internal/api/handlers/auth.go:651` in `ResendVerification`
  - **Field:** `email`
  - **Source:** `json-body:req.Email` (var `req.Email`)
  - **Sanitized:** no
  - _direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
          if err := h.db.Users().FindOne(r.Context(), bson.M{"email": req.Email}).Decode(&user); err != nil {
  ```
- **[HIGH] FindOne** — `backend/internal/api/handlers/auth.go:691` in `ForgotPassword`
  - **Field:** `email`
  - **Source:** `json-body:req.Email` (var `req.Email`)
  - **Sanitized:** no
  - _direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
          if err := h.db.Users().FindOne(r.Context(), bson.M{"email": req.Email}).Decode(&user); err != nil {
  ```
- **[HIGH] FindOne** — `backend/internal/api/handlers/auth.go:1190` in `MagicLinkRequest`
  - **Field:** `email`
  - **Source:** `json-body:req.Email` (var `req.Email`)
  - **Sanitized:** no
  - _direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
          if err := h.db.Users().FindOne(r.Context(), bson.M{"email": req.Email}).Decode(&user); err != nil {
  ```
- **[HIGH] FindOneAndUpdate** — `backend/internal/api/handlers/auth.go:1336` in `ExchangeCode`
  - **Field:** `code`
  - **Source:** `json-body:req.Code` (var `req.Code`)
  - **Sanitized:** no
  - _direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
          err := h.db.AuthCodes().FindOneAndUpdate(r.Context(),
                  bson.M{"code": req.Code, "usedAt": nil, "expiresAt": bson.M{"$gt": now}},
                  bson.M{"$set": bson.M{"usedAt": now}},
          ).Decode(&authCode)
  ```
- **[HIGH] FindOneAndDelete** — `backend/internal/api/handlers/auth.go:1398` in `GoogleOAuthCallback`
  - **Field:** `state`
  - **Source:** `query:state` (var `state`)
  - **Sanitized:** no
  - _direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
          result := h.db.OAuthStates().FindOneAndDelete(r.Context(), bson.M{
                  "state":     state,
                  "expiresAt": bson.M{"$gt": time.Now()},
          })
  ```
- **[HIGH] FindOneAndDelete** — `backend/internal/api/handlers/auth.go:1531` in `GitHubOAuthCallback`
  - **Field:** `state`
  - **Source:** `query:state` (var `state`)
  - **Sanitized:** no
  - _direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
          result := h.db.OAuthStates().FindOneAndDelete(r.Context(), bson.M{
                  "state":     state,
                  "expiresAt": bson.M{"$gt": time.Now()},
          })
  ```
- **[HIGH] FindOneAndDelete** — `backend/internal/api/handlers/auth.go:1673` in `MicrosoftOAuthCallback`
  - **Field:** `state`
  - **Source:** `query:state` (var `state`)
  - **Sanitized:** no
  - _direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
          result := h.db.OAuthStates().FindOneAndDelete(r.Context(), bson.M{
                  "state":     state,
                  "expiresAt": bson.M{"$gt": time.Now()},
          })
  ```
- **[LOW] FindOne** — `backend/internal/api/handlers/auth.go:223` in `Register`
  - **Field:** `email`
  - **Source:** `json-body:req.Email` (var `req.Email`)
  - **Sanitized:** yes, via `custom-validator:isValidEmail`
  - _value passed through sanitizer 'custom-validator:isValidEmail' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
          if err := h.db.Users().FindOne(r.Context(), bson.M{"email": req.Email}).Decode(&existing); err == nil {
  ```
- **[LOW] FindOne** — `backend/internal/api/handlers/auth.go:537` in `Refresh`
  - **Field:** `_id`
  - **Source:** `sanitized:primitive.ObjectIDFromHex(claims.UserID)` (var `userID`)
  - **Sanitized:** yes, via `primitive.ObjectIDFromHex`
  - _value passed through sanitizer 'primitive.ObjectIDFromHex' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
          if err := h.db.Users().FindOne(r.Context(), bson.M{"_id": userID, "isActive": true}).Decode(&user); err != nil {
  ```
- **[LOW] FindOne** — `backend/internal/api/handlers/auth.go:1051` in `MFAChallenge`
  - **Field:** `_id`
  - **Source:** `sanitized:primitive.ObjectIDFromHex(claims.UserID)` (var `userID`)
  - **Sanitized:** yes, via `primitive.ObjectIDFromHex`
  - _value passed through sanitizer 'primitive.ObjectIDFromHex' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
          if err := h.db.Users().FindOne(r.Context(), bson.M{"_id": userID}).Decode(&user); err != nil {
  ```
- **[LOW] UpdateOne** — `backend/internal/api/handlers/auth.go:1861` in `RevokeSession`
  - **Field:** `_id`
  - **Source:** `sanitized:primitive.ObjectIDFromHex(sessionID)` (var `objID`)
  - **Sanitized:** yes, via `primitive.ObjectIDFromHex`
  - _value passed through sanitizer 'primitive.ObjectIDFromHex' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
          result, err := h.db.RefreshTokens().UpdateOne(r.Context(),
                  bson.M{"_id": objID, "userId": user.ID},
                  bson.M{"$set": bson.M{"isRevoked": true}},
          )
  ```

### `backend/internal/api/handlers/billing.go`

- **[LOW] FindOne** — `backend/internal/api/handlers/billing.go:94` in `Checkout`
  - **Field:** `_id`
  - **Source:** `sanitized:primitive.ObjectIDFromHex(req.PlanID)` (var `planID`)
  - **Sanitized:** yes, via `primitive.ObjectIDFromHex`
  - _value passed through sanitizer 'primitive.ObjectIDFromHex' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  		if err := h.db.Plans().FindOne(ctx, bson.M{"_id": planID}).Decode(&plan); err != nil {
  ```
- **[LOW] FindOne** — `backend/internal/api/handlers/billing.go:313` in `Checkout`
  - **Field:** `_id`
  - **Source:** `sanitized:primitive.ObjectIDFromHex(req.BundleID)` (var `bundleID`)
  - **Sanitized:** yes, via `primitive.ObjectIDFromHex`
  - _value passed through sanitizer 'primitive.ObjectIDFromHex' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  		if err := h.db.CreditBundles().FindOne(ctx, bson.M{"_id": bundleID, "isActive": true}).Decode(&bundle); err != nil {
  ```
- **[LOW] FindOne** — `backend/internal/api/handlers/billing.go:457` in `GetInvoice`
  - **Field:** `_id`
  - **Source:** `sanitized:primitive.ObjectIDFromHex(mux.Vars(r)["id"])` (var `txID`)
  - **Sanitized:** yes, via `primitive.ObjectIDFromHex`
  - _value passed through sanitizer 'primitive.ObjectIDFromHex' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  	if err := h.db.FinancialTransactions().FindOne(ctx, bson.M{"_id": txID, "tenantId": tenant.ID}).Decode(&tx); err != nil {
  ```
- **[LOW] FindOne** — `backend/internal/api/handlers/billing.go:486` in `GetInvoicePDF`
  - **Field:** `_id`
  - **Source:** `sanitized:primitive.ObjectIDFromHex(mux.Vars(r)["id"])` (var `txID`)
  - **Sanitized:** yes, via `primitive.ObjectIDFromHex`
  - _value passed through sanitizer 'primitive.ObjectIDFromHex' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  	if err := h.db.FinancialTransactions().FindOne(ctx, bson.M{"_id": txID, "tenantId": tenant.ID}).Decode(&tx); err != nil {
  ```
- **[LOW] CountDocuments** — `backend/internal/api/handlers/billing.go:723` in `AdminListTransactions`
  - **Field:** `tenantId`
  - **Source:** `sanitized:primitive.ObjectIDFromHex(tenantID)` (var `oid`)
  - **Sanitized:** yes, via `primitive.ObjectIDFromHex`
  - _value passed through sanitizer 'primitive.ObjectIDFromHex' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  	total, err := h.db.FinancialTransactions().CountDocuments(ctx, filter)
  ```
- **[LOW] Find** — `backend/internal/api/handlers/billing.go:723` in `AdminListTransactions`
  - **Field:** `tenantId`
  - **Source:** `sanitized:primitive.ObjectIDFromHex(tenantID)` (var `oid`)
  - **Sanitized:** yes, via `primitive.ObjectIDFromHex`
  - _value passed through sanitizer 'primitive.ObjectIDFromHex' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  	cursor, err := h.db.FinancialTransactions().Find(ctx, filter, opts)
  ```
- **[LOW] FindOne** — `backend/internal/api/handlers/billing.go:958` in `AdminCancelSubscription`
  - **Field:** `_id`
  - **Source:** `sanitized:primitive.ObjectIDFromHex(mux.Vars(r)["tenantId"])` (var `tenantID`)
  - **Sanitized:** yes, via `primitive.ObjectIDFromHex`
  - _value passed through sanitizer 'primitive.ObjectIDFromHex' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  	if err := h.db.Tenants().FindOne(ctx, bson.M{"_id": tenantID}).Decode(&tenant); err != nil {
  ```
- **[LOW] UpdateOne** — `backend/internal/api/handlers/billing.go:1004` in `AdminCancelSubscription`
  - **Field:** `_id`
  - **Source:** `sanitized:primitive.ObjectIDFromHex(mux.Vars(r)["tenantId"])` (var `tenantID`)
  - **Sanitized:** yes, via `primitive.ObjectIDFromHex`
  - _value passed through sanitizer 'primitive.ObjectIDFromHex' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  		if _, err := h.db.Tenants().UpdateOne(ctx, bson.M{"_id": tenantID}, bson.M{"$set": updates}); err != nil {
  ```
- **[LOW] UpdateOne** — `backend/internal/api/handlers/billing.go:1037` in `AdminUpdateSubscription`
  - **Field:** `_id`
  - **Source:** `sanitized:primitive.ObjectIDFromHex(mux.Vars(r)["tenantId"])` (var `tenantID`)
  - **Sanitized:** yes, via `primitive.ObjectIDFromHex`
  - _value passed through sanitizer 'primitive.ObjectIDFromHex' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  	result, err := h.db.Tenants().UpdateOne(ctx, bson.M{"_id": tenantID}, bson.M{"$set": updates})
  ```

### `backend/internal/api/handlers/branding.go`

- **[HIGH] FindOne** — `backend/internal/api/handlers/branding.go:119` in `ServeAsset`
  - **Field:** `key`
  - **Source:** `path:key` (var `key`)
  - **Sanitized:** no
  - _direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  	err := h.db.BrandingAssets().FindOne(r.Context(), bson.M{"key": key}).Decode(&asset)
  ```
- **[HIGH] FindOne** — `backend/internal/api/handlers/branding.go:141` in `ServeMedia`
  - **Field:** `key`
  - **Source:** `path:id` (var `key`)
  - **Sanitized:** no
  - _direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  	err := h.db.BrandingAssets().FindOne(r.Context(), bson.M{"key": key}).Decode(&asset)
  ```
- **[HIGH] FindOne** — `backend/internal/api/handlers/branding.go:163` in `GetPublicPage`
  - **Field:** `slug`
  - **Source:** `path:slug` (var `slug`)
  - **Sanitized:** no
  - _direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  	err := h.db.CustomPages().FindOne(r.Context(), bson.M{"slug": slug, "isPublished": true}).Decode(&page)
  ```
- **[HIGH] UpdateOne** — `backend/internal/api/handlers/branding.go:324` in `UploadAsset`
  - **Field:** `key`
  - **Source:** `form:key` (var `key`)
  - **Sanitized:** no
  - _direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  	_, err = h.db.BrandingAssets().UpdateOne(r.Context(), bson.M{"key": key}, bson.M{"$set": asset}, opts)
  ```
- **[HIGH] DeleteOne** — `backend/internal/api/handlers/branding.go:348` in `DeleteAsset`
  - **Field:** `key`
  - **Source:** `path:key` (var `key`)
  - **Sanitized:** no
  - _direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  	_, err := h.db.BrandingAssets().DeleteOne(r.Context(), bson.M{"key": key})
  ```
- **[HIGH] DeleteOne** — `backend/internal/api/handlers/branding.go:487` in `DeleteMedia`
  - **Field:** `key`
  - **Source:** `path:id` (var `key`)
  - **Sanitized:** no
  - _direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  	result, err := h.db.BrandingAssets().DeleteOne(r.Context(), bson.M{"key": key})
  ```
- **[LOW] DeleteOne** — `backend/internal/api/handlers/branding.go:616` in `DeletePage`
  - **Field:** `_id`
  - **Source:** `sanitized:primitive.ObjectIDFromHex(mux.Vars(r)["id"])` (var `id`)
  - **Sanitized:** yes, via `primitive.ObjectIDFromHex`
  - _value passed through sanitizer 'primitive.ObjectIDFromHex' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  	result, err := h.db.CustomPages().DeleteOne(r.Context(), bson.M{"_id": id})
  ```

### `backend/internal/api/handlers/bundles.go`

- **[LOW] CountDocuments** — `backend/internal/api/handlers/bundles.go:96` in `CreateBundle`
  - **Field:** `name`
  - **Source:** `json-body:req.Name` (var `req.Name`)
  - **Sanitized:** yes, via `custom-validator:validateBundleRequest`
  - _value passed through sanitizer 'custom-validator:validateBundleRequest' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  	count, err := h.db.CreditBundles().CountDocuments(r.Context(), bson.M{"name": req.Name})
  ```
- **[LOW] FindOne** — `backend/internal/api/handlers/bundles.go:145` in `UpdateBundle`
  - **Field:** `_id`
  - **Source:** `sanitized:primitive.ObjectIDFromHex(mux.Vars(r)["bundleId"])` (var `bundleID`)
  - **Sanitized:** yes, via `primitive.ObjectIDFromHex`
  - _value passed through sanitizer 'primitive.ObjectIDFromHex' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  	if err := h.db.CreditBundles().FindOne(r.Context(), bson.M{"_id": bundleID}).Decode(&existing); err != nil {
  ```
- **[LOW] CountDocuments** — `backend/internal/api/handlers/bundles.go:166` in `UpdateBundle`
  - **Field:** `name`
  - **Source:** `json-body:req.Name` (var `req.Name`)
  - **Sanitized:** yes, via `custom-validator:validateBundleRequest`
  - _value passed through sanitizer 'custom-validator:validateBundleRequest' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  		count, err := h.db.CreditBundles().CountDocuments(r.Context(), bson.M{"name": req.Name, "_id": bson.M{"$ne": bundleID}})
  ```
- **[LOW] CountDocuments** — `backend/internal/api/handlers/bundles.go:166` in `UpdateBundle`
  - **Field:** `_id.$ne`
  - **Source:** `sanitized:primitive.ObjectIDFromHex(mux.Vars(r)["bundleId"])` (var `bundleID`)
  - **Sanitized:** yes, via `primitive.ObjectIDFromHex`
  - _value passed through sanitizer 'primitive.ObjectIDFromHex' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  		count, err := h.db.CreditBundles().CountDocuments(r.Context(), bson.M{"name": req.Name, "_id": bson.M{"$ne": bundleID}})
  ```
- **[LOW] CountDocuments** — `backend/internal/api/handlers/bundles.go:166` in `UpdateBundle`
  - **Field:** `_id`
  - **Source:** `sanitized:primitive.ObjectIDFromHex(mux.Vars(r)["bundleId"])` (var `bundleID`)
  - **Sanitized:** yes, via `primitive.ObjectIDFromHex`
  - _value passed through sanitizer 'primitive.ObjectIDFromHex' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  		count, err := h.db.CreditBundles().CountDocuments(r.Context(), bson.M{"name": req.Name, "_id": bson.M{"$ne": bundleID}})
  ```
- **[LOW] FindOne** — `backend/internal/api/handlers/bundles.go:196` in `UpdateBundle`
  - **Field:** `_id`
  - **Source:** `sanitized:primitive.ObjectIDFromHex(mux.Vars(r)["bundleId"])` (var `bundleID`)
  - **Sanitized:** yes, via `primitive.ObjectIDFromHex`
  - _value passed through sanitizer 'primitive.ObjectIDFromHex' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  	if err := h.db.CreditBundles().FindOne(r.Context(), bson.M{"_id": bundleID}).Decode(&updated); err != nil {
  ```
- **[LOW] FindOne** — `backend/internal/api/handlers/bundles.go:212` in `DeleteBundle`
  - **Field:** `_id`
  - **Source:** `sanitized:primitive.ObjectIDFromHex(mux.Vars(r)["bundleId"])` (var `bundleID`)
  - **Sanitized:** yes, via `primitive.ObjectIDFromHex`
  - _value passed through sanitizer 'primitive.ObjectIDFromHex' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  	if err := h.db.CreditBundles().FindOne(r.Context(), bson.M{"_id": bundleID}).Decode(&bundle); err != nil {
  ```
- **[LOW] DeleteOne** — `backend/internal/api/handlers/bundles.go:221` in `DeleteBundle`
  - **Field:** `_id`
  - **Source:** `sanitized:primitive.ObjectIDFromHex(mux.Vars(r)["bundleId"])` (var `bundleID`)
  - **Sanitized:** yes, via `primitive.ObjectIDFromHex`
  - _value passed through sanitizer 'primitive.ObjectIDFromHex' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  	if _, err := h.db.CreditBundles().DeleteOne(r.Context(), bson.M{"_id": bundleID}); err != nil {
  ```

### `backend/internal/api/handlers/config.go`

- **[HIGH] UpdateOne** — `backend/internal/api/handlers/config.go:94` in `UpdateConfig`
  - **Field:** `name`
  - **Source:** `path:name` (var `name`)
  - **Sanitized:** no
  - _direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  	_, err := h.db.ConfigVars().UpdateOne(r.Context(), bson.M{"name": name}, bson.M{"$set": updateFields})
  ```
- **[HIGH] DeleteOne** — `backend/internal/api/handlers/config.go:192` in `DeleteConfig`
  - **Field:** `name`
  - **Source:** `path:name` (var `name`)
  - **Sanitized:** no
  - _direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  	if _, err := h.db.ConfigVars().DeleteOne(r.Context(), bson.M{"name": name}); err != nil {
  ```

### `backend/internal/api/handlers/event_definitions.go`

- **[LOW] CountDocuments** — `backend/internal/api/handlers/event_definitions.go:135` in `CreateEventDefinition`
  - **Field:** `name`
  - **Source:** `json-body:req.Name` (var `req.Name`)
  - **Sanitized:** yes, via `regex-validator:validDefName.MatchString`
  - _value passed through sanitizer 'regex-validator:validDefName.MatchString' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  	count, err := h.db.EventDefinitions().CountDocuments(ctx, bson.M{"name": req.Name})
  ```
- **[LOW] CountDocuments** — `backend/internal/api/handlers/event_definitions.go:161` in `CreateEventDefinition`
  - **Field:** `_id`
  - **Source:** `sanitized:primitive.ObjectIDFromHex(*req.ParentID)` (var `parentID`)
  - **Sanitized:** yes, via `primitive.ObjectIDFromHex`
  - _value passed through sanitizer 'primitive.ObjectIDFromHex' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  		count, pErr := h.db.EventDefinitions().CountDocuments(ctx, bson.M{"_id": parentID})
  ```
- **[LOW] FindOne** — `backend/internal/api/handlers/event_definitions.go:212` in `UpdateEventDefinition`
  - **Field:** `_id`
  - **Source:** `sanitized:primitive.ObjectIDFromHex(mux.Vars(r)["defId"])` (var `defID`)
  - **Sanitized:** yes, via `primitive.ObjectIDFromHex`
  - _value passed through sanitizer 'primitive.ObjectIDFromHex' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  	if err := h.db.EventDefinitions().FindOne(ctx, bson.M{"_id": defID}).Decode(&existing); err != nil {
  ```
- **[LOW] CountDocuments** — `backend/internal/api/handlers/event_definitions.go:219` in `UpdateEventDefinition`
  - **Field:** `name`
  - **Source:** `json-body:req.Name` (var `req.Name`)
  - **Sanitized:** yes, via `regex-validator:validDefName.MatchString`
  - _value passed through sanitizer 'regex-validator:validDefName.MatchString' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  		count, err := h.db.EventDefinitions().CountDocuments(ctx, bson.M{"name": req.Name, "_id": bson.M{"$ne": defID}})
  ```
- **[LOW] CountDocuments** — `backend/internal/api/handlers/event_definitions.go:219` in `UpdateEventDefinition`
  - **Field:** `_id.$ne`
  - **Source:** `sanitized:primitive.ObjectIDFromHex(mux.Vars(r)["defId"])` (var `defID`)
  - **Sanitized:** yes, via `primitive.ObjectIDFromHex`
  - _value passed through sanitizer 'primitive.ObjectIDFromHex' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  		count, err := h.db.EventDefinitions().CountDocuments(ctx, bson.M{"name": req.Name, "_id": bson.M{"$ne": defID}})
  ```
- **[LOW] CountDocuments** — `backend/internal/api/handlers/event_definitions.go:219` in `UpdateEventDefinition`
  - **Field:** `_id`
  - **Source:** `sanitized:primitive.ObjectIDFromHex(mux.Vars(r)["defId"])` (var `defID`)
  - **Sanitized:** yes, via `primitive.ObjectIDFromHex`
  - _value passed through sanitizer 'primitive.ObjectIDFromHex' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  		count, err := h.db.EventDefinitions().CountDocuments(ctx, bson.M{"name": req.Name, "_id": bson.M{"$ne": defID}})
  ```
- **[LOW] CountDocuments** — `backend/internal/api/handlers/event_definitions.go:249` in `UpdateEventDefinition`
  - **Field:** `_id`
  - **Source:** `sanitized:primitive.ObjectIDFromHex(*req.ParentID)` (var `parentID`)
  - **Sanitized:** yes, via `primitive.ObjectIDFromHex`
  - _value passed through sanitizer 'primitive.ObjectIDFromHex' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  		count, pErr := h.db.EventDefinitions().CountDocuments(ctx, bson.M{"_id": parentID})
  ```
- **[LOW] UpdateOne** — `backend/internal/api/handlers/event_definitions.go:269` in `UpdateEventDefinition`
  - **Field:** `_id`
  - **Source:** `sanitized:primitive.ObjectIDFromHex(mux.Vars(r)["defId"])` (var `defID`)
  - **Sanitized:** yes, via `primitive.ObjectIDFromHex`
  - _value passed through sanitizer 'primitive.ObjectIDFromHex' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  	if _, err := h.db.EventDefinitions().UpdateOne(ctx, bson.M{"_id": defID}, update); err != nil {
  ```
- **[LOW] FindOne** — `backend/internal/api/handlers/event_definitions.go:278` in `UpdateEventDefinition`
  - **Field:** `_id`
  - **Source:** `sanitized:primitive.ObjectIDFromHex(mux.Vars(r)["defId"])` (var `defID`)
  - **Sanitized:** yes, via `primitive.ObjectIDFromHex`
  - _value passed through sanitizer 'primitive.ObjectIDFromHex' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  	if err := h.db.EventDefinitions().FindOne(ctx, bson.M{"_id": defID}).Decode(&updated); err != nil {
  ```
- **[LOW] FindOne** — `backend/internal/api/handlers/event_definitions.go:296` in `DeleteEventDefinition`
  - **Field:** `_id`
  - **Source:** `sanitized:primitive.ObjectIDFromHex(mux.Vars(r)["defId"])` (var `defID`)
  - **Sanitized:** yes, via `primitive.ObjectIDFromHex`
  - _value passed through sanitizer 'primitive.ObjectIDFromHex' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  	if err := h.db.EventDefinitions().FindOne(ctx, bson.M{"_id": defID}).Decode(&existing); err != nil {
  ```
- **[LOW] UpdateMany** — `backend/internal/api/handlers/event_definitions.go:302` in `DeleteEventDefinition`
  - **Field:** `parentId`
  - **Source:** `sanitized:primitive.ObjectIDFromHex(mux.Vars(r)["defId"])` (var `defID`)
  - **Sanitized:** yes, via `primitive.ObjectIDFromHex`
  - _value passed through sanitizer 'primitive.ObjectIDFromHex' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  	h.db.EventDefinitions().UpdateMany(ctx, bson.M{"parentId": defID}, bson.M{
  		"$unset": bson.M{"parentId": ""},
  		"$set":   bson.M{"updatedAt": time.Now()},
  	})
  ```
- **[LOW] DeleteOne** — `backend/internal/api/handlers/event_definitions.go:307` in `DeleteEventDefinition`
  - **Field:** `_id`
  - **Source:** `sanitized:primitive.ObjectIDFromHex(mux.Vars(r)["defId"])` (var `defID`)
  - **Sanitized:** yes, via `primitive.ObjectIDFromHex`
  - _value passed through sanitizer 'primitive.ObjectIDFromHex' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  	if _, err := h.db.EventDefinitions().DeleteOne(ctx, bson.M{"_id": defID}); err != nil {
  ```

### `backend/internal/api/handlers/messages.go`

- **[LOW] UpdateOne** — `backend/internal/api/handlers/messages.go:88` in `MarkRead`
  - **Field:** `_id`
  - **Source:** `sanitized:primitive.ObjectIDFromHex(msgIDStr)` (var `msgID`)
  - **Sanitized:** yes, via `primitive.ObjectIDFromHex`
  - _value passed through sanitizer 'primitive.ObjectIDFromHex' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  	result, err := h.db.Messages().UpdateOne(r.Context(),
  		bson.M{"_id": msgID, "userId": user.ID},
  		bson.M{"$set": bson.M{"read": true}})
  ```

### `backend/internal/api/handlers/plans.go`

- **[LOW] FindOne** — `backend/internal/api/handlers/plans.go:110` in `GetPlan`
  - **Field:** `_id`
  - **Source:** `sanitized:primitive.ObjectIDFromHex(mux.Vars(r)["planId"])` (var `planID`)
  - **Sanitized:** yes, via `primitive.ObjectIDFromHex`
  - _value passed through sanitizer 'primitive.ObjectIDFromHex' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  	if err := h.db.Plans().FindOne(r.Context(), bson.M{"_id": planID}).Decode(&plan); err != nil {
  ```
- **[LOW] CountDocuments** — `backend/internal/api/handlers/plans.go:253` in `CreatePlan`
  - **Field:** `name`
  - **Source:** `json-body:req.Name` (var `req.Name`)
  - **Sanitized:** yes, via `custom-validator:validatePlanRequest`
  - _value passed through sanitizer 'custom-validator:validatePlanRequest' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  	count, err := h.db.Plans().CountDocuments(r.Context(), bson.M{"name": req.Name})
  ```
- **[LOW] FindOne** — `backend/internal/api/handlers/plans.go:323` in `UpdatePlan`
  - **Field:** `_id`
  - **Source:** `sanitized:primitive.ObjectIDFromHex(mux.Vars(r)["planId"])` (var `planID`)
  - **Sanitized:** yes, via `primitive.ObjectIDFromHex`
  - _value passed through sanitizer 'primitive.ObjectIDFromHex' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  	if err := h.db.Plans().FindOne(r.Context(), bson.M{"_id": planID}).Decode(&existing); err != nil {
  ```
- **[LOW] CountDocuments** — `backend/internal/api/handlers/plans.go:350` in `UpdatePlan`
  - **Field:** `name`
  - **Source:** `json-body:req.Name` (var `req.Name`)
  - **Sanitized:** yes, via `custom-validator:validatePlanRequest`
  - _value passed through sanitizer 'custom-validator:validatePlanRequest' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  		count, err := h.db.Plans().CountDocuments(r.Context(), bson.M{"name": req.Name, "_id": bson.M{"$ne": planID}})
  ```
- **[LOW] CountDocuments** — `backend/internal/api/handlers/plans.go:350` in `UpdatePlan`
  - **Field:** `_id.$ne`
  - **Source:** `sanitized:primitive.ObjectIDFromHex(mux.Vars(r)["planId"])` (var `planID`)
  - **Sanitized:** yes, via `primitive.ObjectIDFromHex`
  - _value passed through sanitizer 'primitive.ObjectIDFromHex' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  		count, err := h.db.Plans().CountDocuments(r.Context(), bson.M{"name": req.Name, "_id": bson.M{"$ne": planID}})
  ```
- **[LOW] CountDocuments** — `backend/internal/api/handlers/plans.go:350` in `UpdatePlan`
  - **Field:** `_id`
  - **Source:** `sanitized:primitive.ObjectIDFromHex(mux.Vars(r)["planId"])` (var `planID`)
  - **Sanitized:** yes, via `primitive.ObjectIDFromHex`
  - _value passed through sanitizer 'primitive.ObjectIDFromHex' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  		count, err := h.db.Plans().CountDocuments(r.Context(), bson.M{"name": req.Name, "_id": bson.M{"$ne": planID}})
  ```
- **[LOW] DeleteMany** — `backend/internal/api/handlers/plans.go:368` in `UpdatePlan`
  - **Field:** `entityId`
  - **Source:** `sanitized:primitive.ObjectIDFromHex(mux.Vars(r)["planId"])` (var `planID`)
  - **Sanitized:** yes, via `primitive.ObjectIDFromHex`
  - _value passed through sanitizer 'primitive.ObjectIDFromHex' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  		h.db.StripeMappings().DeleteMany(r.Context(), bson.M{
  			"entityType": bson.M{"$in": []string{"plan_month", "plan_year", "plan_base_month", "plan_base_year", "plan_seat_month", "plan_seat_year"}},
  			"entityId":   planID,
  		})
  ```
- **[LOW] FindOne** — `backend/internal/api/handlers/plans.go:404` in `UpdatePlan`
  - **Field:** `_id`
  - **Source:** `sanitized:primitive.ObjectIDFromHex(mux.Vars(r)["planId"])` (var `planID`)
  - **Sanitized:** yes, via `primitive.ObjectIDFromHex`
  - _value passed through sanitizer 'primitive.ObjectIDFromHex' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  	if err := h.db.Plans().FindOne(r.Context(), bson.M{"_id": planID}).Decode(&updated); err != nil {
  ```
- **[LOW] CountDocuments** — `backend/internal/api/handlers/plans.go:408` in `UpdatePlan`
  - **Field:** `planId`
  - **Source:** `sanitized:primitive.ObjectIDFromHex(mux.Vars(r)["planId"])` (var `planID`)
  - **Sanitized:** yes, via `primitive.ObjectIDFromHex`
  - _value passed through sanitizer 'primitive.ObjectIDFromHex' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  	subCount, err := h.db.Tenants().CountDocuments(r.Context(), bson.M{"planId": planID})
  ```
- **[LOW] FindOne** — `backend/internal/api/handlers/plans.go:446` in `DeletePlan`
  - **Field:** `_id`
  - **Source:** `sanitized:primitive.ObjectIDFromHex(mux.Vars(r)["planId"])` (var `planID`)
  - **Sanitized:** yes, via `primitive.ObjectIDFromHex`
  - _value passed through sanitizer 'primitive.ObjectIDFromHex' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  	if err := h.db.Plans().FindOne(r.Context(), bson.M{"_id": planID}).Decode(&plan); err != nil {
  ```
- **[LOW] CountDocuments** — `backend/internal/api/handlers/plans.go:460` in `DeletePlan`
  - **Field:** `planId`
  - **Source:** `sanitized:primitive.ObjectIDFromHex(mux.Vars(r)["planId"])` (var `planID`)
  - **Sanitized:** yes, via `primitive.ObjectIDFromHex`
  - _value passed through sanitizer 'primitive.ObjectIDFromHex' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  	tenantCount, err := h.db.Tenants().CountDocuments(r.Context(), bson.M{"planId": planID})
  ```
- **[LOW] DeleteOne** — `backend/internal/api/handlers/plans.go:470` in `DeletePlan`
  - **Field:** `_id`
  - **Source:** `sanitized:primitive.ObjectIDFromHex(mux.Vars(r)["planId"])` (var `planID`)
  - **Sanitized:** yes, via `primitive.ObjectIDFromHex`
  - _value passed through sanitizer 'primitive.ObjectIDFromHex' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  	if _, err := h.db.Plans().DeleteOne(r.Context(), bson.M{"_id": planID}); err != nil {
  ```
- **[LOW] FindOne** — `backend/internal/api/handlers/plans.go:491` in `ArchivePlan`
  - **Field:** `_id`
  - **Source:** `sanitized:primitive.ObjectIDFromHex(mux.Vars(r)["planId"])` (var `planID`)
  - **Sanitized:** yes, via `primitive.ObjectIDFromHex`
  - _value passed through sanitizer 'primitive.ObjectIDFromHex' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  	if err := h.db.Plans().FindOne(r.Context(), bson.M{"_id": planID}).Decode(&plan); err != nil {
  ```
- **[LOW] UpdateByID** — `backend/internal/api/handlers/plans.go:505` in `ArchivePlan`
  - **Field:** `isArchived`
  - **Source:** `tracer:filter-tracer` (var `planID`)
  - **Sanitized:** yes, via `go/ssa-filter-tracer`
  - _filter field `isArchived` detected by go/ssa filter tracer on variable `planID` — value expression could not be statically resolved; manual review recommended_
  ```go
  	if _, err := h.db.Plans().UpdateByID(r.Context(), planID, bson.M{"$set": bson.M{"isArchived": true, "updatedAt": time.Now()}}); err != nil {
  ```
- **[LOW] UpdateByID** — `backend/internal/api/handlers/plans.go:505` in `ArchivePlan`
  - **Field:** `updatedAt`
  - **Source:** `tracer:filter-tracer` (var `planID`)
  - **Sanitized:** yes, via `go/ssa-filter-tracer`
  - _filter field `updatedAt` detected by go/ssa filter tracer on variable `planID` — value expression could not be statically resolved; manual review recommended_
  ```go
  	if _, err := h.db.Plans().UpdateByID(r.Context(), planID, bson.M{"$set": bson.M{"isArchived": true, "updatedAt": time.Now()}}); err != nil {
  ```
- **[LOW] FindOne** — `backend/internal/api/handlers/plans.go:526` in `UnarchivePlan`
  - **Field:** `_id`
  - **Source:** `sanitized:primitive.ObjectIDFromHex(mux.Vars(r)["planId"])` (var `planID`)
  - **Sanitized:** yes, via `primitive.ObjectIDFromHex`
  - _value passed through sanitizer 'primitive.ObjectIDFromHex' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  	if err := h.db.Plans().FindOne(r.Context(), bson.M{"_id": planID}).Decode(&plan); err != nil {
  ```
- **[LOW] UpdateByID** — `backend/internal/api/handlers/plans.go:540` in `UnarchivePlan`
  - **Field:** `isArchived`
  - **Source:** `tracer:filter-tracer` (var `planID`)
  - **Sanitized:** yes, via `go/ssa-filter-tracer`
  - _filter field `isArchived` detected by go/ssa filter tracer on variable `planID` — value expression could not be statically resolved; manual review recommended_
  ```go
  	if _, err := h.db.Plans().UpdateByID(r.Context(), planID, bson.M{"$set": bson.M{"isArchived": false, "updatedAt": time.Now()}}); err != nil {
  ```
- **[LOW] UpdateByID** — `backend/internal/api/handlers/plans.go:540` in `UnarchivePlan`
  - **Field:** `updatedAt`
  - **Source:** `tracer:filter-tracer` (var `planID`)
  - **Sanitized:** yes, via `go/ssa-filter-tracer`
  - _filter field `updatedAt` detected by go/ssa filter tracer on variable `planID` — value expression could not be statically resolved; manual review recommended_
  ```go
  	if _, err := h.db.Plans().UpdateByID(r.Context(), planID, bson.M{"$set": bson.M{"isArchived": false, "updatedAt": time.Now()}}); err != nil {
  ```
- **[LOW] FindOne** — `backend/internal/api/handlers/plans.go:576` in `AssignPlan`
  - **Field:** `_id`
  - **Source:** `sanitized:primitive.ObjectIDFromHex(mux.Vars(r)["tenantId"])` (var `tenantID`)
  - **Sanitized:** yes, via `primitive.ObjectIDFromHex`
  - _value passed through sanitizer 'primitive.ObjectIDFromHex' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  	if err := h.db.Tenants().FindOne(ctx, bson.M{"_id": tenantID}).Decode(&tenant); err != nil {
  ```
- **[LOW] FindOne** — `backend/internal/api/handlers/plans.go:598` in `AssignPlan`
  - **Field:** `_id`
  - **Source:** `sanitized:primitive.ObjectIDFromHex(*req.PlanID)` (var `planOID`)
  - **Sanitized:** yes, via `primitive.ObjectIDFromHex`
  - _value passed through sanitizer 'primitive.ObjectIDFromHex' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  			if err := h.db.Plans().FindOne(ctx, bson.M{"_id": planOID}).Decode(&plan); err != nil {
  ```
- **[LOW] FindOne** — `backend/internal/api/handlers/plans.go:703` in `ListPlansPublic`
  - **Field:** `_id`
  - **Source:** `sanitized:primitive.ObjectIDFromHex(tenantIDStr)` (var `tenantID`)
  - **Sanitized:** yes, via `primitive.ObjectIDFromHex`
  - _value passed through sanitizer 'primitive.ObjectIDFromHex' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  	if err := h.db.Tenants().FindOne(r.Context(), bson.M{"_id": tenantID}).Decode(&tenant); err != nil {
  ```
- **[LOW] CountDocuments** — `backend/internal/api/handlers/plans.go:714` in `ListPlansPublic`
  - **Field:** `tenantId`
  - **Source:** `sanitized:primitive.ObjectIDFromHex(tenantIDStr)` (var `tenantID`)
  - **Sanitized:** yes, via `primitive.ObjectIDFromHex`
  - _value passed through sanitizer 'primitive.ObjectIDFromHex' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  	memberCount, err := h.db.TenantMemberships().CountDocuments(r.Context(), bson.M{
  		"userId":   user.ID,
  		"tenantId": tenantID,
  	})
  ```

### `backend/internal/api/handlers/tenant.go`

- **[HIGH] FindOne** — `backend/internal/api/handlers/tenant.go:171` in `InviteMember`
  - **Field:** `email`
  - **Source:** `json-body:req.Email` (var `req.Email`)
  - **Sanitized:** no
  - _direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  	if err := h.db.Users().FindOne(r.Context(), bson.M{"email": req.Email}).Decode(&existingUser); err == nil {
  ```
- **[HIGH] CountDocuments** — `backend/internal/api/handlers/tenant.go:187` in `InviteMember`
  - **Field:** `email`
  - **Source:** `json-body:req.Email` (var `req.Email`)
  - **Sanitized:** no
  - _direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  	invCount, err := h.db.Invitations().CountDocuments(r.Context(), bson.M{
  		"tenantId":  tenant.ID,
  		"email":     req.Email,
  		"status":    models.InvitationPending,
  		"expiresAt": bson.M{"$gt": time.Now()},
  	})
  ```
- **[LOW] FindOne** — `backend/internal/api/handlers/tenant.go:344` in `RemoveMember`
  - **Field:** `userId`
  - **Source:** `sanitized:primitive.ObjectIDFromHex(targetUserIDStr)` (var `targetUserID`)
  - **Sanitized:** yes, via `primitive.ObjectIDFromHex`
  - _value passed through sanitizer 'primitive.ObjectIDFromHex' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  	if err := h.db.TenantMemberships().FindOne(r.Context(), bson.M{
  		"userId":   targetUserID,
  		"tenantId": tenant.ID,
  	}).Decode(&targetMembership); err != nil {
  ```
- **[LOW] UpdateOne** — `backend/internal/api/handlers/tenant.go:456` in `ChangeRole`
  - **Field:** `userId`
  - **Source:** `sanitized:primitive.ObjectIDFromHex(targetUserIDStr)` (var `targetUserID`)
  - **Sanitized:** yes, via `primitive.ObjectIDFromHex`
  - _value passed through sanitizer 'primitive.ObjectIDFromHex' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  	result, err := h.db.TenantMemberships().UpdateOne(r.Context(),
  		bson.M{"userId": targetUserID, "tenantId": tenant.ID},
  		bson.M{"$set": bson.M{"role": req.Role, "updatedAt": time.Now()}},
  	)
  ```
- **[LOW] CountDocuments** — `backend/internal/api/handlers/tenant.go:508` in `TransferOwnership`
  - **Field:** `userId`
  - **Source:** `sanitized:primitive.ObjectIDFromHex(targetUserIDStr)` (var `targetUserID`)
  - **Sanitized:** yes, via `primitive.ObjectIDFromHex`
  - _value passed through sanitizer 'primitive.ObjectIDFromHex' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  	count, err := h.db.TenantMemberships().CountDocuments(r.Context(), bson.M{
  		"userId":   targetUserID,
  		"tenantId": tenant.ID,
  	})
  ```
- **[LOW] UpdateOne** — `backend/internal/api/handlers/tenant.go:524` in `TransferOwnership`
  - **Field:** `userId`
  - **Source:** `sanitized:primitive.ObjectIDFromHex(targetUserIDStr)` (var `targetUserID`)
  - **Sanitized:** yes, via `primitive.ObjectIDFromHex`
  - _value passed through sanitizer 'primitive.ObjectIDFromHex' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  	if _, err := h.db.TenantMemberships().UpdateOne(r.Context(),
  		bson.M{"userId": targetUserID, "tenantId": tenant.ID},
  		bson.M{"$set": bson.M{"role": models.RoleOwner, "updatedAt": now}},
  	); err != nil {
  ```
- **[LOW] Find** — `backend/internal/api/handlers/tenant.go:587` in `GetActivity`
  - **Field:** `action.$regex`
  - **Source:** `sanitized:escapeRegexInput(...action...)` (var `action`)
  - **Sanitized:** yes, via `escapeRegexInput`
  - _value passed through sanitizer 'escapeRegexInput' before query; $regex with user input enables regex injection / ReDoS — ensure input is escaped via escapeRegexInput()_
  ```go
  	cursor, err := h.db.SystemLogs().Find(r.Context(), filter, opts)
  ```
- **[LOW] Find** — `backend/internal/api/handlers/tenant.go:587` in `GetActivity`
  - **Field:** `action`
  - **Source:** `sanitized:escapeRegexInput(...action...)` (var `action`)
  - **Sanitized:** yes, via `escapeRegexInput`
  - _value passed through sanitizer 'escapeRegexInput' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  	cursor, err := h.db.SystemLogs().Find(r.Context(), filter, opts)
  ```
- **[LOW] CountDocuments** — `backend/internal/api/handlers/tenant.go:587` in `GetActivity`
  - **Field:** `action.$regex`
  - **Source:** `sanitized:escapeRegexInput(...action...)` (var `action`)
  - **Sanitized:** yes, via `escapeRegexInput`
  - _value passed through sanitizer 'escapeRegexInput' before query; $regex with user input enables regex injection / ReDoS — ensure input is escaped via escapeRegexInput()_
  ```go
  	total, err := h.db.SystemLogs().CountDocuments(r.Context(), filter)
  ```
- **[LOW] CountDocuments** — `backend/internal/api/handlers/tenant.go:587` in `GetActivity`
  - **Field:** `action`
  - **Source:** `sanitized:escapeRegexInput(...action...)` (var `action`)
  - **Sanitized:** yes, via `escapeRegexInput`
  - _value passed through sanitizer 'escapeRegexInput' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  	total, err := h.db.SystemLogs().CountDocuments(r.Context(), filter)
  ```
- **[LOW] Find** — `backend/internal/api/handlers/tenant.go:590` in `GetActivity`
  - **Field:** `message.$regex`
  - **Source:** `sanitized:escapeRegexInput(...search...)` (var `search`)
  - **Sanitized:** yes, via `escapeRegexInput`
  - _value passed through sanitizer 'escapeRegexInput' before query; $regex with user input enables regex injection / ReDoS — ensure input is escaped via escapeRegexInput()_
  ```go
  	cursor, err := h.db.SystemLogs().Find(r.Context(), filter, opts)
  ```
- **[LOW] Find** — `backend/internal/api/handlers/tenant.go:590` in `GetActivity`
  - **Field:** `message`
  - **Source:** `sanitized:escapeRegexInput(...search...)` (var `search`)
  - **Sanitized:** yes, via `escapeRegexInput`
  - _value passed through sanitizer 'escapeRegexInput' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  	cursor, err := h.db.SystemLogs().Find(r.Context(), filter, opts)
  ```
- **[LOW] CountDocuments** — `backend/internal/api/handlers/tenant.go:590` in `GetActivity`
  - **Field:** `message.$regex`
  - **Source:** `sanitized:escapeRegexInput(...search...)` (var `search`)
  - **Sanitized:** yes, via `escapeRegexInput`
  - _value passed through sanitizer 'escapeRegexInput' before query; $regex with user input enables regex injection / ReDoS — ensure input is escaped via escapeRegexInput()_
  ```go
  	total, err := h.db.SystemLogs().CountDocuments(r.Context(), filter)
  ```
- **[LOW] CountDocuments** — `backend/internal/api/handlers/tenant.go:590` in `GetActivity`
  - **Field:** `message`
  - **Source:** `sanitized:escapeRegexInput(...search...)` (var `search`)
  - **Sanitized:** yes, via `escapeRegexInput`
  - _value passed through sanitizer 'escapeRegexInput' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  	total, err := h.db.SystemLogs().CountDocuments(r.Context(), filter)
  ```

### `backend/internal/api/handlers/usage.go`

- **[HIGH] UpdateOne** — `backend/internal/api/handlers/usage.go:90` in `RecordUsage`
  - **Field:** `subscriptionCredits.$gte`
  - **Source:** `json-body:req.Quantity` (var `req.Quantity`)
  - **Sanitized:** no
  - _direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  		result, err := h.db.Tenants().UpdateOne(sc,
  			bson.M{"_id": tenant.ID, "subscriptionCredits": bson.M{"$gte": int64(req.Quantity)}},
  			bson.M{"$inc": bson.M{"subscriptionCredits": -int64(req.Quantity)}},
  		)
  ```
- **[HIGH] UpdateOne** — `backend/internal/api/handlers/usage.go:90` in `RecordUsage`
  - **Field:** `subscriptionCredits`
  - **Source:** `json-body:req.Quantity` (var `req.Quantity`)
  - **Sanitized:** no
  - _direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  		result, err := h.db.Tenants().UpdateOne(sc,
  			bson.M{"_id": tenant.ID, "subscriptionCredits": bson.M{"$gte": int64(req.Quantity)}},
  			bson.M{"$inc": bson.M{"subscriptionCredits": -int64(req.Quantity)}},
  		)
  ```
- **[HIGH] UpdateOne** — `backend/internal/api/handlers/usage.go:100` in `RecordUsage`
  - **Field:** `purchasedCredits.$gte`
  - **Source:** `json-body:req.Quantity` (var `req.Quantity`)
  - **Sanitized:** no
  - _direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  			result, err = h.db.Tenants().UpdateOne(sc,
  				bson.M{"_id": tenant.ID, "purchasedCredits": bson.M{"$gte": int64(req.Quantity)}},
  				bson.M{"$inc": bson.M{"purchasedCredits": -int64(req.Quantity)}},
  			)
  ```
- **[HIGH] UpdateOne** — `backend/internal/api/handlers/usage.go:100` in `RecordUsage`
  - **Field:** `purchasedCredits`
  - **Source:** `json-body:req.Quantity` (var `req.Quantity`)
  - **Sanitized:** no
  - _direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  			result, err = h.db.Tenants().UpdateOne(sc,
  				bson.M{"_id": tenant.ID, "purchasedCredits": bson.M{"$gte": int64(req.Quantity)}},
  				bson.M{"$inc": bson.M{"purchasedCredits": -int64(req.Quantity)}},
  			)
  ```

### `backend/internal/api/handlers/webhook.go`

- **[LOW] FindOne** — `backend/internal/api/handlers/webhook.go:170` in `handleCheckoutCompleted`
  - **Field:** `_id`
  - **Source:** `sanitized:primitive.ObjectIDFromHex(session.Metadata["tenantId"])` (var `tenantID`)
  - **Sanitized:** yes, via `primitive.ObjectIDFromHex`
  - _value passed through sanitizer 'primitive.ObjectIDFromHex' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  		if err := h.db.Tenants().FindOne(ctx, bson.M{"_id": tenantID}).Decode(&checkTenant); err != nil {
  ```
- **[LOW] FindOne** — `backend/internal/api/handlers/webhook.go:182` in `handleCheckoutCompleted`
  - **Field:** `_id.$ne`
  - **Source:** `sanitized:primitive.ObjectIDFromHex(session.Metadata["tenantId"])` (var `tenantID`)
  - **Sanitized:** yes, via `primitive.ObjectIDFromHex`
  - _value passed through sanitizer 'primitive.ObjectIDFromHex' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  			if err := h.db.Tenants().FindOne(ctx, bson.M{
  				"stripeCustomerId": session.Customer.ID,
  				"_id":              bson.M{"$ne": tenantID},
  			}).Decode(&otherTenant); err == nil {
  ```
- **[LOW] FindOne** — `backend/internal/api/handlers/webhook.go:182` in `handleCheckoutCompleted`
  - **Field:** `_id`
  - **Source:** `sanitized:primitive.ObjectIDFromHex(session.Metadata["tenantId"])` (var `tenantID`)
  - **Sanitized:** yes, via `primitive.ObjectIDFromHex`
  - _value passed through sanitizer 'primitive.ObjectIDFromHex' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  			if err := h.db.Tenants().FindOne(ctx, bson.M{
  				"stripeCustomerId": session.Customer.ID,
  				"_id":              bson.M{"$ne": tenantID},
  			}).Decode(&otherTenant); err == nil {
  ```
- **[LOW] FindOne** — `backend/internal/api/handlers/webhook.go:205` in `handleCheckoutCompleted`
  - **Field:** `_id`
  - **Source:** `sanitized:primitive.ObjectIDFromHex(planIDStr)` (var `planID`)
  - **Sanitized:** yes, via `primitive.ObjectIDFromHex`
  - _value passed through sanitizer 'primitive.ObjectIDFromHex' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  		if err := h.db.Plans().FindOne(ctx, bson.M{"_id": planID}).Decode(&plan); err != nil {
  ```
- **[LOW] UpdateOne** — `backend/internal/api/handlers/webhook.go:239` in `handleCheckoutCompleted`
  - **Field:** `_id`
  - **Source:** `sanitized:primitive.ObjectIDFromHex(session.Metadata["userId"])` (var `userID`)
  - **Sanitized:** yes, via `primitive.ObjectIDFromHex`
  - _value passed through sanitizer 'primitive.ObjectIDFromHex' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  			h.db.Users().UpdateOne(ctx, bson.M{"_id": userID}, bson.M{
  				"$set": bson.M{"trialUsedAt": &now},
  			})
  ```
- **[LOW] UpdateOne** — `backend/internal/api/handlers/webhook.go:255` in `handleCheckoutCompleted`
  - **Field:** `_id`
  - **Source:** `sanitized:primitive.ObjectIDFromHex(session.Metadata["tenantId"])` (var `tenantID`)
  - **Sanitized:** yes, via `primitive.ObjectIDFromHex`
  - _value passed through sanitizer 'primitive.ObjectIDFromHex' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  		if _, err := h.db.Tenants().UpdateOne(ctx, bson.M{"_id": tenantID}, updateOp); err != nil {
  ```
- **[LOW] FindOne** — `backend/internal/api/handlers/webhook.go:322` in `handleCheckoutCompleted`
  - **Field:** `_id`
  - **Source:** `sanitized:primitive.ObjectIDFromHex(bundleIDStr)` (var `bundleID`)
  - **Sanitized:** yes, via `primitive.ObjectIDFromHex`
  - _value passed through sanitizer 'primitive.ObjectIDFromHex' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  		if err := h.db.CreditBundles().FindOne(ctx, bson.M{"_id": bundleID}).Decode(&bundle); err != nil {
  ```
- **[LOW] UpdateOne** — `backend/internal/api/handlers/webhook.go:328` in `handleCheckoutCompleted`
  - **Field:** `_id`
  - **Source:** `sanitized:primitive.ObjectIDFromHex(session.Metadata["tenantId"])` (var `tenantID`)
  - **Sanitized:** yes, via `primitive.ObjectIDFromHex`
  - _value passed through sanitizer 'primitive.ObjectIDFromHex' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  		if _, err := h.db.Tenants().UpdateOne(ctx, bson.M{"_id": tenantID}, bson.M{
  			"$inc": bson.M{"purchasedCredits": bundle.Credits},
  			"$set": bson.M{"updatedAt": time.Now()},
  		}); err != nil {
  ```

### `backend/internal/api/handlers/webhooks.go`

- **[LOW] FindOne** — `backend/internal/api/handlers/webhooks.go:105` in `GetWebhook`
  - **Field:** `_id`
  - **Source:** `sanitized:primitive.ObjectIDFromHex(mux.Vars(r)["webhookId"])` (var `whID`)
  - **Sanitized:** yes, via `primitive.ObjectIDFromHex`
  - _value passed through sanitizer 'primitive.ObjectIDFromHex' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  	if err := h.db.Webhooks().FindOne(r.Context(), bson.M{"_id": whID, "isActive": true}).Decode(&hook); err != nil {
  ```
- **[LOW] Find** — `backend/internal/api/handlers/webhooks.go:111` in `GetWebhook`
  - **Field:** `webhookId`
  - **Source:** `sanitized:primitive.ObjectIDFromHex(mux.Vars(r)["webhookId"])` (var `whID`)
  - **Sanitized:** yes, via `primitive.ObjectIDFromHex`
  - _value passed through sanitizer 'primitive.ObjectIDFromHex' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  	cursor, err := h.db.WebhookDeliveries().Find(r.Context(),
  		bson.M{"webhookId": whID},
  		options.Find().SetSort(bson.D{{Key: "createdAt", Value: -1}}).SetLimit(20),
  	)
  ```
- **[LOW] FindOne** — `backend/internal/api/handlers/webhooks.go:340` in `UpdateWebhook`
  - **Field:** `_id`
  - **Source:** `sanitized:primitive.ObjectIDFromHex(mux.Vars(r)["webhookId"])` (var `whID`)
  - **Sanitized:** yes, via `primitive.ObjectIDFromHex`
  - _value passed through sanitizer 'primitive.ObjectIDFromHex' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  	if err := h.db.Webhooks().FindOne(r.Context(), bson.M{"_id": whID}).Decode(&hook); err != nil {
  ```
- **[LOW] FindOne** — `backend/internal/api/handlers/webhooks.go:421` in `TestWebhook`
  - **Field:** `_id`
  - **Source:** `sanitized:primitive.ObjectIDFromHex(mux.Vars(r)["webhookId"])` (var `whID`)
  - **Sanitized:** yes, via `primitive.ObjectIDFromHex`
  - _value passed through sanitizer 'primitive.ObjectIDFromHex' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  	if err := h.db.Webhooks().FindOne(r.Context(), bson.M{"_id": whID, "isActive": true}).Decode(&hook); err != nil {
  ```

### `backend/internal/middleware/auth.go`

- **[LOW] FindOne** — `backend/internal/middleware/auth.go:90` in `authenticateJWT`
  - **Field:** `_id`
  - **Source:** `sanitized:primitive.ObjectIDFromHex(claims.UserID)` (var `userID`)
  - **Sanitized:** yes, via `primitive.ObjectIDFromHex`
  - _value passed through sanitizer 'primitive.ObjectIDFromHex' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
          err = m.db.Users().FindOne(r.Context(), bson.M{"_id": userID}).Decode(&user)
  ```

### `backend/internal/middleware/tenant.go`

- **[LOW] FindOne** — `backend/internal/middleware/tenant.go:51` in `RequireTenant`
  - **Field:** `_id`
  - **Source:** `sanitized:primitive.ObjectIDFromHex(tenantIDStr)` (var `tenantID`)
  - **Sanitized:** yes, via `primitive.ObjectIDFromHex`
  - _value passed through sanitizer 'primitive.ObjectIDFromHex' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  		err = m.db.Tenants().FindOne(r.Context(), bson.M{"_id": tenantID, "isActive": true}).Decode(&tenant)
  ```
- **[LOW] FindOne** — `backend/internal/middleware/tenant.go:64` in `RequireTenant`
  - **Field:** `tenantId`
  - **Source:** `sanitized:primitive.ObjectIDFromHex(tenantIDStr)` (var `tenantID`)
  - **Sanitized:** yes, via `primitive.ObjectIDFromHex`
  - _value passed through sanitizer 'primitive.ObjectIDFromHex' before query; direct user input in filter value — ensure type checking (e.g. primitive.ObjectIDFromHex) prevents operator injection_
  ```go
  		err = m.db.TenantMemberships().FindOne(r.Context(), bson.M{
  			"userId":   user.ID,
  			"tenantId": tenantID,
  		}).Decode(&membership)
  ```

## Methodology

The scanner walks every `.go` file (excluding `vendor/`, `node_modules/`, `.git/`, `graphify-out/`, `testdata/`) and applies these heuristics:

1. **Function-level user input tracking.** For each top-level function/method, build a map of variables that hold user input. Sources recognized: `r.URL.Query().Get(...)`, `q.Get(...)` (where `q := r.URL.Query()`), `r.FormValue(...)`, `chi.URLParam(...)`, `mux.Vars(r)[...]`, and JSON-body struct fields (`req.Field` where `req` was decoded from `r.Body`). String literals are preserved during pattern matching (only comments are stripped).
2. **Sanitizer tracking.** Variables assigned from `primitive.ObjectIDFromHex(...)`, `escapeRegexInput(...)`, `strconv.Atoi/ParseInt/ParseFloat/ParseBool(...)`, `time.Parse(...)`, `url.PathEscape/QueryEscape(...)`, `regexp.MustCompile(...)`, `uuid.Parse(...)`, or `primitive.Regex{Pattern: ...escapeRegexInput(...)...}` are marked sanitized. `switch X { case ... }` allowlist validation is also recognized when the case body assigns a literal (not `X`) to the filter. Struct-level validation via `validator.Struct(&req)` or the project's `validation.Validate(&req)` wrapper marks every `req.*` field as sanitized (when the validation call occurs BEFORE the query). Per-field custom validators (`if !isValidEmail(req.Email) { return ... }`) are recognized by function-name prefix (`is*`/`valid*`/`validate*`/`check*`) and mark their argument as sanitized.
3. **MongoDB query detection.** Every call to a known mongo-driver method (`Find`, `FindOne`, `InsertOne`, `UpdateOne`, `DeleteOne`, `Aggregate`, `CountDocuments`, etc.) is located via paren matching on a masked source (strings/comments blanked out).
4. **Filter analysis.** The filter argument (positional after `ctx`) is parsed. If it's a `bson.M{...}` / `bson.D{...}` literal, every key/value pair is extracted via balanced-brace matching on the masked source, then re-read from the original source to preserve string-literal field names; nested literals (e.g. inside `$or` arrays) are recursed. If the filter is a variable, the function is scanned for `varname["..."] = value` assignments.
5. **Risk classification.** `$where` with user input → CRITICAL (JS execution). Direct user input in a field value, or `$regex` with user input → HIGH. User input in `$or`/`$and`/`$nor` array elements → MEDIUM. Sanitized user input → LOW (informational).

**Note on Go type safety:** Go struct fields and `string`-returning APIs (`r.URL.Query().Get`) are statically typed, so classic operator-injection (`{"$ne": null}` passed as a *string*) is not directly exploitable. The real risks in Go are (a) `$where` (JavaScript execution context), (b) `$regex` (ReDoS), and (c) any code path that decodes user JSON into an `interface{}` / `map[string]interface{}` and passes it directly to a query. The HIGH findings for plain string fields are flagged conservatively for human review — most are safe but warrant a glance.
