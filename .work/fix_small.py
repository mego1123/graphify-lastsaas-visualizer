#!/usr/bin/env python3
"""Apply fixes to small handler files. Uses \t for tabs."""
import sys, os
sys.path.insert(0, "/home/z/my-project/.work")
from apply_fix import apply_fixes, go_build

T = "\t"

# ============================================================
# helpers.go — 1 finding
# json.NewEncoder(w).Encode(payload) missing check
# ============================================================
helpers_fixes = [
    (
        # Add log/slog import
        'import (\n\t"crypto/rand"\n\t"encoding/base64"\n\t"encoding/json"\n\t"net/http"\n\t"regexp"\n\t"strings"\n)',
        'import (\n\t"crypto/rand"\n\t"encoding/base64"\n\t"encoding/json"\n\t"log/slog"\n\t"net/http"\n\t"regexp"\n\t"strings"\n)',
        "add log/slog import",
    ),
    (
        'func respondWithJSON(w http.ResponseWriter, status int, payload interface{}) {\n\tw.Header().Set("Content-Type", "application/json")\n\tw.WriteHeader(status)\n\tjson.NewEncoder(w).Encode(payload)\n}',
        'func respondWithJSON(w http.ResponseWriter, status int, payload interface{}) {\n\tw.Header().Set("Content-Type", "application/json")\n\tw.WriteHeader(status)\n\tif err := json.NewEncoder(w).Encode(payload); err != nil {\n\t\tslog.Error("failed to encode JSON response", "error", err)\n\t}\n}',
        "check Encode error in respondWithJSON",
    ),
]

# ============================================================
# health.go — 1 finding (swallowed in SendTestEmail)
# ============================================================
health_fixes = [
    (
        'import (\n\t"encoding/json"\n\t"fmt"\n\t"net/http"\n\t"time"\n\n\t"lastsaas/internal/email"\n\t"lastsaas/internal/health"\n\t"lastsaas/internal/models"\n)',
        'import (\n\t"encoding/json"\n\t"fmt"\n\t"log/slog"\n\t"net/http"\n\t"time"\n\n\t"lastsaas/internal/email"\n\t"lastsaas/internal/health"\n\t"lastsaas/internal/models"\n)',
        "add log/slog import",
    ),
    (
        '\tif err := h.emailService.SendEmail(req.To, subject, body); err != nil {\n\t\trespondWithJSON(w, http.StatusOK, map[string]interface{}{\n\t\t\t"success": false,\n\t\t\t"error":   err.Error(),\n\t\t})\n\t\treturn\n\t}',
        '\tif err := h.emailService.SendEmail(req.To, subject, body); err != nil {\n\t\tslog.Error("failed to send test email", "to", req.To, "error", err)\n\t\trespondWithJSON(w, http.StatusOK, map[string]interface{}{\n\t\t\t"success": false,\n\t\t\t"error":   err.Error(),\n\t\t})\n\t\treturn\n\t}',
        "log SendEmail error in SendTestEmail",
    ),
]

# ============================================================
# config.go — 1 finding (ignored: updated, _ := h.store.GetVar(name))
# ============================================================
config_fixes = [
    (
        '\th.syslog.Critical(r.Context(), fmt.Sprintf("Config variable \'%s\' updated", name))\n\n\tupdated, _ := h.store.GetVar(name)\n\trespondWithJSON(w, http.StatusOK, updated)',
        '\th.syslog.Critical(r.Context(), fmt.Sprintf("Config variable \'%s\' updated", name))\n\n\tupdated, ok := h.store.GetVar(name)\n\tif !ok {\n\t\trespondWithError(w, http.StatusInternalServerError, "Failed to reload config variable")\n\t\treturn\n\t}\n\trespondWithJSON(w, http.StatusOK, updated)',
        "check GetVar ok flag in UpdateConfig",
    ),
]

# ============================================================
# apikeys.go — 1 finding (ignored: total, _ := CountDocuments)
# ============================================================
apikeys_fixes = [
    (
        '\ttotal, _ := h.db.APIKeys().CountDocuments(r.Context(), bson.M{"isActive": true})\n\trespondWithJSON(w, http.StatusOK, map[string]interface{}{"apiKeys": keys, "total": total})',
        '\ttotal, err := h.db.APIKeys().CountDocuments(r.Context(), bson.M{"isActive": true})\n\tif err != nil {\n\t\trespondWithError(w, http.StatusInternalServerError, "Failed to count API keys")\n\t\treturn\n\t}\n\trespondWithJSON(w, http.StatusOK, map[string]interface{}{"apiKeys": keys, "total": total})',
        "check CountDocuments error in ListAPIKeys",
    ),
]

# ============================================================
# telemetry.go — 2 findings (ignored: tenant, _ := GetTenantFromContext x2)
# ============================================================
telemetry_fixes = [
    # TrackAuthenticated
    (
        '\ttenant, _ := middleware.GetTenantFromContext(r.Context())\n\n\tvar req struct {\n\t\tEvent      string                 `json:"event"`\n\t\tProperties map[string]interface{} `json:"properties"`\n\t}\n\tif err := json.NewDecoder(r.Body).Decode(&req); err != nil {\n\t\trespondWithError(w, http.StatusBadRequest, "Invalid request body")\n\t\treturn\n\t}\n\n\tif req.Event == "" {',
        '\ttenant, hasTenant := middleware.GetTenantFromContext(r.Context())\n\n\tvar req struct {\n\t\tEvent      string                 `json:"event"`\n\t\tProperties map[string]interface{} `json:"properties"`\n\t}\n\tif err := json.NewDecoder(r.Body).Decode(&req); err != nil {\n\t\trespondWithError(w, http.StatusBadRequest, "Invalid request body")\n\t\treturn\n\t}\n\n\tif req.Event == "" {',
        "rename _ to hasTenant in TrackAuthenticated",
    ),
    (
        '\tif tenant != nil {\n\t\tevent.TenantID = &tenant.ID\n\t}\n\n\tif err := h.telemetry.Track(r.Context(), event); err != nil {\n\t\trespondWithError(w, http.StatusInternalServerError, "Failed to track event")\n\t\treturn\n\t}\n\n\trespondWithJSON(w, http.StatusOK, map[string]string{"status": "ok"})\n}\n\n// TrackBatch handles batch telemetry event ingestion.',
        '\tif hasTenant && tenant != nil {\n\t\tevent.TenantID = &tenant.ID\n\t}\n\n\tif err := h.telemetry.Track(r.Context(), event); err != nil {\n\t\trespondWithError(w, http.StatusInternalServerError, "Failed to track event")\n\t\treturn\n\t}\n\n\trespondWithJSON(w, http.StatusOK, map[string]string{"status": "ok"})\n}\n\n// TrackBatch handles batch telemetry event ingestion.',
        "use hasTenant in TrackAuthenticated",
    ),
    # TrackBatch
    (
        '\ttenant, _ := middleware.GetTenantFromContext(r.Context())\n\n\tvar req struct {\n\t\tEvents []struct {',
        '\ttenant, hasTenant := middleware.GetTenantFromContext(r.Context())\n\n\tvar req struct {\n\t\tEvents []struct {',
        "rename _ to hasTenant in TrackBatch",
    ),
    (
        '\t\t\tif tenant != nil {\n\t\t\t\tevent.TenantID = &tenant.ID\n\t\t\t}\n\t\t\tevents = append(events, event)',
        '\t\t\tif hasTenant && tenant != nil {\n\t\t\t\tevent.TenantID = &tenant.ID\n\t\t\t}\n\t\t\tevents = append(events, event)',
        "use hasTenant in TrackBatch",
    ),
]

# ============================================================
# branding.go — 2 findings (missing_check: w.Write(asset.Data) x2)
# ============================================================
branding_fixes = [
    (
        'import (\n\t"encoding/json"\n\t"fmt"\n\t"io"\n\t"net/http"\n\t"strings"\n\t"time"\n\n\t"lastsaas/internal/configstore"\n\t"lastsaas/internal/db"\n\t"lastsaas/internal/models"\n\t"lastsaas/internal/syslog"\n',
        'import (\n\t"encoding/json"\n\t"fmt"\n\t"io"\n\t"log/slog"\n\t"net/http"\n\t"strings"\n\t"time"\n\n\t"lastsaas/internal/configstore"\n\t"lastsaas/internal/db"\n\t"lastsaas/internal/models"\n\t"lastsaas/internal/syslog"\n',
        "add log/slog import",
    ),
    # ServeAsset (logo/favicon)
    (
        '\tw.Header().Set("Content-Type", asset.ContentType)\n\tw.Header().Set("Cache-Control", "public, max-age=3600")\n\tw.Write(asset.Data)\n}\n\n// ServeMedia serves a media library file by ID.',
        '\tw.Header().Set("Content-Type", asset.ContentType)\n\tw.Header().Set("Cache-Control", "public, max-age=3600")\n\tif _, err := w.Write(asset.Data); err != nil {\n\t\tslog.Error("failed to write branding asset", "key", key, "error", err)\n\t\treturn\n\t}\n}\n\n// ServeMedia serves a media library file by ID.',
        "check w.Write in ServeAsset",
    ),
    # ServeMedia
    (
        '\tw.Header().Set("Content-Type", asset.ContentType)\n\tw.Header().Set("Cache-Control", "public, max-age=3600")\n\tw.Write(asset.Data)\n}\n\n// GetPublicPage returns a published custom page by slug.',
        '\tw.Header().Set("Content-Type", asset.ContentType)\n\tw.Header().Set("Cache-Control", "public, max-age=3600")\n\tif _, err := w.Write(asset.Data); err != nil {\n\t\tslog.Error("failed to write media asset", "id", key, "error", err)\n\t\treturn\n\t}\n}\n\n// GetPublicPage returns a published custom page by slug.',
        "check w.Write in ServeMedia",
    ),
]

# ============================================================
# docs.go — 2 findings (missing_check: w.Write([]byte(sb.String())) x2)
# ============================================================
docs_fixes = [
    (
        'import (\n\t"fmt"\n\t"html"\n\t"net/http"\n\t"strings"\n\n\t"lastsaas/internal/models"\n\t"lastsaas/internal/version"\n)',
        'import (\n\t"fmt"\n\t"html"\n\t"log/slog"\n\t"net/http"\n\t"strings"\n\n\t"lastsaas/internal/models"\n\t"lastsaas/internal/version"\n)',
        "add log/slog import",
    ),
    # DocsHTML
    (
        '\tw.Header().Set("Content-Type", "text/html; charset=utf-8")\n\tw.Header().Set("Cache-Control", "no-cache")\n\tw.Write([]byte(sb.String()))\n}',
        '\tw.Header().Set("Content-Type", "text/html; charset=utf-8")\n\tw.Header().Set("Cache-Control", "no-cache")\n\tif _, err := w.Write([]byte(sb.String())); err != nil {\n\t\tslog.Error("failed to write HTML docs response", "error", err)\n\t\treturn\n\t}\n}',
        "check w.Write in DocsHTML",
    ),
    # DocsMarkdown
    (
        '\tw.Header().Set("Content-Type", "text/markdown; charset=utf-8")\n\tw.Header().Set("Cache-Control", "no-cache")\n\tw.Write([]byte(sb.String()))\n}',
        '\tw.Header().Set("Content-Type", "text/markdown; charset=utf-8")\n\tw.Header().Set("Cache-Control", "no-cache")\n\tif _, err := w.Write([]byte(sb.String())); err != nil {\n\t\tslog.Error("failed to write markdown docs response", "error", err)\n\t\treturn\n\t}\n}',
        "check w.Write in DocsMarkdown",
    ),
]

# ============================================================
# openapi.go — 3 findings (json.Unmarshal x2, enc.Encode x1)
# ============================================================
openapi_fixes = [
    (
        'import (\n\t"encoding/json"\n\t"net/http"\n\t"strings"\n\n\t"lastsaas/internal/version"\n)',
        'import (\n\t"encoding/json"\n\t"log/slog"\n\t"net/http"\n\t"strings"\n\n\t"lastsaas/internal/version"\n)',
        "add log/slog import",
    ),
    # body example
    (
        '\t\t\t\tif ep.Body != "" {\n\t\t\t\t\tvar bodyExample any\n\t\t\t\t\tjson.Unmarshal([]byte(ep.Body), &bodyExample)\n\t\t\t\t\top.RequestBody = &openAPIRequestBody{',
        '\t\t\t\tif ep.Body != "" {\n\t\t\t\t\tvar bodyExample any\n\t\t\t\t\tif err := json.Unmarshal([]byte(ep.Body), &bodyExample); err != nil {\n\t\t\t\t\t\tslog.Warn("OpenAPI: failed to parse body example", "path", path, "method", method, "error", err)\n\t\t\t\t\t}\n\t\t\t\t\top.RequestBody = &openAPIRequestBody{',
        "check json.Unmarshal for body example",
    ),
    # response example
    (
        '\t\t\t\tif ep.Response != "" {\n\t\t\t\t\tvar respExample any\n\t\t\t\t\tjson.Unmarshal([]byte(ep.Response), &respExample)\n\t\t\t\t\top.Responses["200"] = openAPIResponse{',
        '\t\t\t\tif ep.Response != "" {\n\t\t\t\t\tvar respExample any\n\t\t\t\t\tif err := json.Unmarshal([]byte(ep.Response), &respExample); err != nil {\n\t\t\t\t\t\tslog.Warn("OpenAPI: failed to parse response example", "path", path, "method", method, "error", err)\n\t\t\t\t\t}\n\t\t\t\t\top.Responses["200"] = openAPIResponse{',
        "check json.Unmarshal for response example",
    ),
    # enc.Encode
    (
        '\tw.Header().Set("Content-Type", "application/json; charset=utf-8")\n\tw.Header().Set("Cache-Control", "no-cache")\n\tenc := json.NewEncoder(w)\n\tenc.SetIndent("", "  ")\n\tenc.Encode(spec)\n}',
        '\tw.Header().Set("Content-Type", "application/json; charset=utf-8")\n\tw.Header().Set("Cache-Control", "no-cache")\n\tenc := json.NewEncoder(w)\n\tenc.SetIndent("", "  ")\n\tif err := enc.Encode(spec); err != nil {\n\t\tslog.Error("failed to encode OpenAPI spec response", "error", err)\n\t\treturn\n\t}\n}',
        "check enc.Encode in DocsOpenAPI",
    ),
]

if __name__ == "__main__":
    all_fixes = [
        ("helpers.go", helpers_fixes),
        ("health.go", health_fixes),
        ("config.go", config_fixes),
        ("apikeys.go", apikeys_fixes),
        ("telemetry.go", telemetry_fixes),
        ("branding.go", branding_fixes),
        ("docs.go", docs_fixes),
        ("openapi.go", openapi_fixes),
    ]
    ok = True
    for fname, fixes in all_fixes:
        print(f"\n=== {fname} ===")
        if not apply_fixes(fname, fixes):
            ok = False
            break
    if ok:
        print("\n=== BUILD ===")
        go_build()
