# 🗑️ Dead Components Report — lastsaas

**Found 1 component(s) that are exported but never imported anywhere.**

These are safe to delete (after manual verification).

| Component | File | Export Type |
|-----------|------|-------------|
| `AdminRoute` | `frontend/src/components/AdminRoute.tsx` | default |

## How to verify

Before deleting, run these commands to confirm:

```bash
# Verify AdminRoute is not imported anywhere
grep -rn "AdminRoute" src/ --include="*.tsx" --include="*.ts"
```

## Common false positives

- **Lazy-loaded pages**: imported via `lazy(() => import('./path'))` — these are detected and excluded
- **Route entry points**: files in `pages/` or `app/` directories — excluded by path
- **String-based references**: if a component name is used as a string (e.g., in a registry), grep will find it
- **Dynamic component resolution**: if you use `componentRegistry['ComponentName']`, grep will find the string
