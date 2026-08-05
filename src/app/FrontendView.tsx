'use client'

import { useEffect, useState } from 'react'

type DeadComponent = {
  name: string
  file: string
  export_type: string
}

type RouteNode = {
  path: string
  component: string
  file: string
  is_lazy: boolean
  is_protected: boolean
  children: RouteNode[]
}

export default function FrontendView() {
  const [deadComponents, setDeadComponents] = useState<DeadComponent[]>([])
  const [routes, setRoutes] = useState<RouteNode[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      fetch('/dead-components.json').then(r => r.json()).catch(() => []),
      fetch('/route-tree.json').then(r => r.json()).catch(() => []),
    ]).then(([dead, rts]: [DeadComponent[], RouteNode[]]) => {
      setDeadComponents(dead)
      setRoutes(rts)
      setLoading(false)
    })
  }, [])

  if (loading) {
    return (
      <div style={styles.loading}>
        <div style={styles.spinner} />
        <p style={{ color: '#888', fontSize: 13 }}>Loading frontend analysis…</p>
      </div>
    )
  }

  const totalRoutes = countRoutes(routes)
  const lazyRoutes = countLazy(routes)

  return (
    <div style={styles.container}>
      <div style={styles.leftCol}>
        {/* Dead Components */}
        <div style={styles.sectionHeader}>
          <h2 style={styles.sectionTitle}>🗑️ Dead Components</h2>
          <span style={styles.sectionMeta}>
            {deadComponents.length} found
          </span>
        </div>
        <div style={styles.panel}>
          {deadComponents.length === 0 ? (
            <p style={styles.successMsg}>✅ No dead components found. All exported components are imported somewhere.</p>
          ) : (
            <>
              <p style={styles.warning}>
                {deadComponents.length} component(s) are exported but never imported. Safe to delete after verification.
              </p>
              <div style={styles.componentList}>
                {deadComponents.map((c, i) => (
                  <div key={i} style={styles.componentRow}>
                    <span style={styles.trashIcon}>🗑️</span>
                    <div style={styles.componentInfo}>
                      <span style={styles.componentName}>{c.name}</span>
                      <span style={styles.componentFile}>{c.file}</span>
                    </div>
                    <span style={styles.exportBadge}>{c.export_type}</span>
                  </div>
                ))}
              </div>
              <div style={styles.verifySection}>
                <h4 style={styles.subTitle}>Verify before deleting:</h4>
                <pre style={styles.codeBlock}>
                  {deadComponents.map(c => `grep -rn "${c.name}" src/ --include="*.tsx" --include="*.ts"`).join('\n')}
                </pre>
              </div>
            </>
          )}
        </div>

        {/* Route Summary */}
        <div style={styles.sectionHeader}>
          <h2 style={styles.sectionTitle}>🌳 Route Tree Summary</h2>
        </div>
        <div style={styles.panel}>
          <div style={styles.statsRow}>
            <div style={styles.statCard}>
              <span style={styles.statLabel}>Total Routes</span>
              <span style={styles.statValue}>{totalRoutes}</span>
            </div>
            <div style={styles.statCard}>
              <span style={styles.statLabel}>Lazy-loaded</span>
              <span style={styles.statValue}>{lazyRoutes}</span>
            </div>
            <div style={styles.statCard}>
              <span style={styles.statLabel}>Eager</span>
              <span style={styles.statValue}>{totalRoutes - lazyRoutes}</span>
            </div>
          </div>
          <p style={styles.bundleNote}>
            💡 {lazyRoutes} route(s) are lazy-loaded (separate chunks).
            {totalRoutes - lazyRoutes} are eagerly loaded (in main bundle).
          </p>
          <a href="/ROUTE_TREE.md" target="_blank" rel="noreferrer" style={styles.link}>
            View full route tree →
          </a>
        </div>
      </div>

      {/* Route tree visualization */}
      <div style={styles.rightCol}>
        <div style={styles.sectionHeader}>
          <h2 style={styles.sectionTitle}>Route Hierarchy</h2>
        </div>
        <div style={styles.routeTree}>
          {routes.map((r, i) => (
            <RouteRow key={i} route={r} depth={0} />
          ))}
        </div>
      </div>
    </div>
  )
}

function RouteRow({ route, depth }: { route: RouteNode; depth: number }) {
  const icon = route.is_protected ? '🔒' : route.is_lazy ? '📄' : '📄'
  const lazyTag = route.is_lazy ? ' (lazy)' : ''
  return (
    <div>
      <div style={{ ...styles.routeRow, paddingLeft: 12 + depth * 20 }}>
        <span style={styles.routeIcon}>{icon}</span>
        <span style={styles.routePath}>{route.path || '(index)'}</span>
        <span style={styles.routeArrow}>→</span>
        <span style={styles.routeComponent}>{route.component}{lazyTag}</span>
        {route.file && <span style={styles.routeFile}>[{route.file}]</span>}
      </div>
      {route.children.map((c, i) => (
        <RouteRow key={i} route={c} depth={depth + 1} />
      ))}
    </div>
  )
}

function countRoutes(routes: RouteNode[]): number {
  let count = 0
  for (const r of routes) {
    count += 1
    count += countRoutes(r.children)
  }
  return count
}

function countLazy(routes: RouteNode[]): number {
  let count = 0
  for (const r of routes) {
    if (r.is_lazy) count += 1
    count += countLazy(r.children)
  }
  return count
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    display: 'flex', gap: 16, padding: 16, height: '100%',
    overflow: 'hidden', background: '#0f0f1a', color: '#e0e0e0',
  },
  leftCol: { flex: 1, overflowY: 'auto', paddingRight: 8 },
  rightCol: { flex: 1, overflowY: 'auto' },
  loading: {
    display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
    height: '100%', gap: 12, background: '#0f0f1a',
  },
  spinner: {
    width: 32, height: 32, border: '3px solid #2a2a4e', borderTopColor: '#4E79A7',
    borderRadius: '50%', animation: 'spin 1s linear infinite',
  },
  sectionHeader: {
    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
    marginBottom: 10, marginTop: 8,
  },
  sectionTitle: { fontSize: 14, color: '#fff', margin: 0, fontWeight: 600 },
  sectionMeta: { fontSize: 11, color: '#666' },
  panel: { background: '#1a1a2e', borderRadius: 6, padding: 12, border: '1px solid #2a2a4e', marginBottom: 12 },
  successMsg: { color: '#7CFC7C', fontSize: 12, lineHeight: 1.6 },
  warning: { color: '#FFB347', fontSize: 12, marginBottom: 10 },
  componentList: { display: 'flex', flexDirection: 'column', gap: 4 },
  componentRow: {
    display: 'flex', alignItems: 'center', gap: 10, padding: '8px 10px',
    background: '#0f0f1a', borderRadius: 4, fontSize: 12,
  },
  trashIcon: { fontSize: 14 },
  componentInfo: { flex: 1, display: 'flex', flexDirection: 'column' },
  componentName: { color: '#e0e0e0', fontWeight: 600 },
  componentFile: { color: '#666', fontSize: 10, fontFamily: 'ui-monospace, monospace' },
  exportBadge: {
    fontSize: 9, padding: '2px 6px', borderRadius: 3, background: '#2a2a4e',
    color: '#aaa', textTransform: 'uppercase',
  },
  verifySection: { marginTop: 12, paddingTop: 12, borderTop: '1px solid #2a2a4e' },
  subTitle: { fontSize: 11, color: '#888', margin: '0 0 6px 0', textTransform: 'uppercase' },
  codeBlock: {
    background: '#0f0f1a', padding: 8, borderRadius: 4, fontSize: 10,
    fontFamily: 'ui-monospace, monospace', color: '#4E79A7', overflowX: 'auto',
    whiteSpace: 'pre',
  },
  statsRow: { display: 'flex', gap: 8, marginBottom: 10 },
  statCard: {
    flex: 1, background: '#0f0f1a', borderRadius: 4, padding: 10,
    display: 'flex', flexDirection: 'column', gap: 4, alignItems: 'center',
  },
  statLabel: { fontSize: 10, color: '#888', textTransform: 'uppercase' },
  statValue: { fontSize: 20, fontWeight: 700, color: '#fff' },
  bundleNote: { fontSize: 11, color: '#aaa', lineHeight: 1.6, marginBottom: 8 },
  link: { color: '#4E79A7', fontSize: 12, textDecoration: 'none' },
  routeTree: { background: '#1a1a2e', borderRadius: 6, padding: 8, border: '1px solid #2a2a4e' },
  routeRow: {
    display: 'flex', alignItems: 'center', gap: 6, padding: '4px 8px',
    fontSize: 11, borderBottom: '1px solid #20203a', fontFamily: 'ui-monospace, monospace',
  },
  routeIcon: { width: 16, textAlign: 'center' },
  routePath: { color: '#4E79A7', fontWeight: 600, minWidth: 120 },
  routeArrow: { color: '#666' },
  routeComponent: { color: '#e0e0e0' },
  routeFile: { color: '#555', fontSize: 10, marginLeft: 'auto' },
}
