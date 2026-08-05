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

type BundleImpact = {
  component: string
  file: string
  risk_level: string
  affected_routes: Array<{ path: string; component: string; is_lazy: boolean; file: string }>
  affected_chunks: string[]
  shared_components: Array<{ component: string; route_count: number; note: string }>
}

type PropDrilling = Array<{
  prop_name: string
  source_component: string
  depth: number
  chain: Array<{ component: string; file: string; uses_prop: boolean }>
}>

type HookIssue = {
  file: string
  component: string
  hook_type: string
  line: number
  issue_type: string
  description: string
  missing_vars: string[]
  unnecessary_vars: string[]
}

type ContextInfo = {
  name: string
  file: string
  consumer_count: number
  risk_level: string
  consumers: Array<{ component: string; file: string; hook: string }>
}

export default function FrontendView() {
  const [deadComponents, setDeadComponents] = useState<DeadComponent[]>([])
  const [routes, setRoutes] = useState<RouteNode[]>([])
  const [bundleImpact, setBundleImpact] = useState<BundleImpact | null>(null)
  const [propDrilling, setPropDrilling] = useState<PropDrilling>([])
  const [hookIssues, setHookIssues] = useState<HookIssue[]>([])
  const [contexts, setContexts] = useState<ContextInfo[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      fetch('/dead-components.json').then(r => r.json()).catch(() => []),
      fetch('/route-tree.json').then(r => r.json()).catch(() => []),
      fetch('/bundle-impact.json').then(r => r.json()).catch(() => null),
      fetch('/prop-drilling.json').then(r => r.json()).catch(() => []),
      fetch('/hook-deps.json').then(r => r.json()).catch(() => []),
      fetch('/context-usage.json').then(r => r.json()).catch(() => []),
    ]).then(([dead, rts, bi, pd, hd, cu]: [DeadComponent[], RouteNode[], BundleImpact | null, PropDrilling, HookIssue[], ContextInfo[]]) => {
      setDeadComponents(dead)
      setRoutes(rts)
      setBundleImpact(bi)
      setPropDrilling(pd)
      setHookIssues(hd)
      setContexts(cu)
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
          <span style={styles.sectionMeta}>{deadComponents.length} found</span>
        </div>
        <div style={styles.panel}>
          {deadComponents.length === 0 ? (
            <p style={styles.successMsg}>✅ No dead components found.</p>
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
            </>
          )}
        </div>

        {/* Bundle Impact */}
        {bundleImpact && (
          <>
            <div style={styles.sectionHeader}>
              <h2 style={styles.sectionTitle}>📦 Bundle Impact (top shared component)</h2>
            </div>
            <div style={styles.panel}>
              <div style={styles.bundleHeader}>
                <span style={{ ...styles.riskBadge, background: riskColor(bundleImpact.risk_level) }}>
                  {bundleImpact.risk_level}
                </span>
                <span style={styles.bundleComponent}>{bundleImpact.component}</span>
                <span style={styles.bundleFile}>{bundleImpact.file}</span>
              </div>
              <div style={styles.bundleStats}>
                <div style={styles.bundleStat}>
                  <span style={styles.bundleStatLabel}>Routes</span>
                  <span style={styles.bundleStatValue}>{bundleImpact.affected_routes.length}</span>
                </div>
                <div style={styles.bundleStat}>
                  <span style={styles.bundleStatLabel}>Bundles</span>
                  <span style={styles.bundleStatValue}>{bundleImpact.affected_chunks.length}</span>
                </div>
              </div>
              {bundleImpact.affected_routes.length > 0 && (
                <div style={styles.affectedRoutes}>
                  {bundleImpact.affected_routes.slice(0, 8).map((r, i) => (
                    <div key={i} style={styles.affectedRoute}>
                      <span style={styles.routePath}>{r.path || '/'}</span>
                      <span style={styles.routeLazy}>{r.is_lazy ? 'lazy' : 'eager'}</span>
                    </div>
                  ))}
                  {bundleImpact.affected_routes.length > 8 && (
                    <span style={styles.moreRoutes}>+ {bundleImpact.affected_routes.length - 8} more</span>
                  )}
                </div>
              )}
              <a href="/bundle-impact.json" target="_blank" rel="noreferrer" style={styles.link}>
                Full report →
              </a>
            </div>
          </>
        )}

        {/* Prop Drilling */}
        <div style={styles.sectionHeader}>
          <h2 style={styles.sectionTitle}>🔗 Prop Drilling</h2>
          <span style={styles.sectionMeta}>{propDrilling.length} found (depth ≥ 3)</span>
        </div>
        <div style={styles.panel}>
          {propDrilling.length === 0 ? (
            <p style={styles.successMsg}>✅ No prop drilling detected. Props are well-managed via Context.</p>
          ) : (
            propDrilling.slice(0, 5).map((pf, i) => (
              <div key={i} style={styles.drillingRow}>
                <span style={styles.drillingProp}>{pf.prop_name}</span>
                <span style={styles.drillingDepth}>depth {pf.depth}</span>
                <div style={styles.drillingChain}>
                  {pf.chain.map((c, j) => (
                    <span key={j} style={styles.chainNode(c.uses_prop)}>
                      {c.uses_prop ? '✅' : '➡️'} {c.component}
                    </span>
                  ))}
                </div>
              </div>
            ))
          )}
        </div>

        {/* Hook Dependencies */}
        <div style={styles.sectionHeader}>
          <h2 style={styles.sectionTitle}>🪝 Hook Dependencies</h2>
          <span style={styles.sectionMeta}>{hookIssues.length} issues</span>
        </div>
        <div style={styles.panel}>
          {hookIssues.length === 0 ? (
            <p style={styles.successMsg}>✅ No hook dependency issues found.</p>
          ) : (
            <>
              <div style={styles.hookStats}>
                {['missing_dep', 'empty_deps', 'unnecessary_dep'].map(t => {
                  const count = hookIssues.filter(h => h.issue_type === t).length
                  if (count === 0) return null
                  return (
                    <div key={t} style={styles.hookStat(t)}>
                      <span style={styles.hookStatCount}>{count}</span>
                      <span style={styles.hookStatLabel}>{t.replace('_', ' ')}</span>
                    </div>
                  )
                })}
              </div>
              <div style={styles.hookList}>
                {hookIssues.slice(0, 8).map((h, i) => (
                  <div key={i} style={styles.hookRow}>
                    <span style={styles.hookIcon(h.issue_type)}>
                      {h.issue_type === 'missing_dep' ? '🔴' : h.issue_type === 'empty_deps' ? '🟡' : '🟢'}
                    </span>
                    <div style={styles.hookInfo}>
                      <span style={styles.hookType}>{h.hook_type}</span>
                      <span style={styles.hookFile}>{h.file}:{h.line}</span>
                    </div>
                    <span style={styles.hookDesc}>{h.description}</span>
                  </div>
                ))}
                {hookIssues.length > 8 && (
                  <span style={styles.moreRoutes}>+ {hookIssues.length - 8} more issues</span>
                )}
              </div>
            </>
          )}
        </div>

        {/* Context Usage */}
        <div style={styles.sectionHeader}>
          <h2 style={styles.sectionTitle}>🌐 Context Usage</h2>
          <span style={styles.sectionMeta}>{contexts.length} Contexts</span>
        </div>
        <div style={styles.panel}>
          {contexts.length === 0 ? (
            <p style={styles.empty}>No Contexts found.</p>
          ) : (
            <div style={styles.contextList}>
              {contexts.sort((a, b) => b.consumer_count - a.consumer_count).map((ctx, i) => (
                <div key={i} style={styles.contextRow}>
                  <span style={{ ...styles.contextRisk, background: riskColor(ctx.risk_level) }}>
                    {ctx.risk_level}
                  </span>
                  <div style={styles.contextInfo}>
                    <span style={styles.contextName}>{ctx.name}</span>
                    <span style={styles.contextFile}>{ctx.file}</span>
                  </div>
                  <div style={styles.contextConsumers}>
                    <span style={styles.consumerCount}>{ctx.consumer_count}</span>
                    <span style={styles.consumerLabel}>consumers</span>
                  </div>
                  {/* Mini bar showing consumer distribution */}
                  <div style={styles.consumerBar}>
                    <div
                      style={{
                        ...styles.consumerBarFill,
                        width: `${Math.min(100, (ctx.consumer_count / Math.max(...contexts.map(c => c.consumer_count))) * 100)}%`,
                        background: riskColor(ctx.risk_level),
                      }}
                    />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Route Summary */}
        <div style={styles.sectionHeader}>
          <h2 style={styles.sectionTitle}>🌳 Route Tree Summary</h2>
        </div>
        <div style={styles.panel}>
          <div style={styles.statsRow}>
            <div style={styles.statCard}>
              <span style={styles.statLabel}>Total</span>
              <span style={styles.statValue}>{totalRoutes}</span>
            </div>
            <div style={styles.statCard}>
              <span style={styles.statLabel}>Lazy</span>
              <span style={styles.statValue}>{lazyRoutes}</span>
            </div>
            <div style={styles.statCard}>
              <span style={styles.statLabel}>Eager</span>
              <span style={styles.statValue}>{totalRoutes - lazyRoutes}</span>
            </div>
          </div>
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
  for (const r of routes) { count += 1; count += countRoutes(r.children) }
  return count
}

function countLazy(routes: RouteNode[]): number {
  let count = 0
  for (const r of routes) { if (r.is_lazy) count += 1; count += countLazy(r.children) }
  return count
}

function riskColor(risk: string): string {
  return { LOW: '#4CAF50', MEDIUM: '#FF9800', HIGH: '#F44336' }[risk] || '#888'
}

const styles: Record<string, React.CSSProperties> = {
  container: { display: 'flex', gap: 16, padding: 16, height: '100%', overflow: 'hidden', background: '#0f0f1a', color: '#e0e0e0' },
  leftCol: { flex: 1, overflowY: 'auto', paddingRight: 8 },
  rightCol: { flex: 1, overflowY: 'auto' },
  loading: { display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', gap: 12, background: '#0f0f1a' },
  spinner: { width: 32, height: 32, border: '3px solid #2a2a4e', borderTopColor: '#4E79A7', borderRadius: '50%', animation: 'spin 1s linear infinite' },
  sectionHeader: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10, marginTop: 8 },
  sectionTitle: { fontSize: 14, color: '#fff', margin: 0, fontWeight: 600 },
  sectionMeta: { fontSize: 11, color: '#666' },
  panel: { background: '#1a1a2e', borderRadius: 6, padding: 12, border: '1px solid #2a2a4e', marginBottom: 12 },
  successMsg: { color: '#7CFC7C', fontSize: 12, lineHeight: 1.6 },
  warning: { color: '#FFB347', fontSize: 12, marginBottom: 10 },
  componentList: { display: 'flex', flexDirection: 'column', gap: 4 },
  componentRow: { display: 'flex', alignItems: 'center', gap: 10, padding: '8px 10px', background: '#0f0f1a', borderRadius: 4, fontSize: 12 },
  trashIcon: { fontSize: 14 },
  componentInfo: { flex: 1, display: 'flex', flexDirection: 'column' },
  componentName: { color: '#e0e0e0', fontWeight: 600 },
  componentFile: { color: '#666', fontSize: 10, fontFamily: 'ui-monospace, monospace' },
  exportBadge: { fontSize: 9, padding: '2px 6px', borderRadius: 3, background: '#2a2a4e', color: '#aaa', textTransform: 'uppercase' },
  bundleHeader: { display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 },
  riskBadge: { padding: '3px 8px', borderRadius: 4, fontSize: 10, fontWeight: 700, color: '#fff' },
  bundleComponent: { fontSize: 14, color: '#fff', fontWeight: 600 },
  bundleFile: { fontSize: 10, color: '#666', fontFamily: 'ui-monospace, monospace' },
  bundleStats: { display: 'flex', gap: 8, marginBottom: 10 },
  bundleStat: { flex: 1, background: '#0f0f1a', borderRadius: 4, padding: 8, display: 'flex', flexDirection: 'column', gap: 2, alignItems: 'center' },
  bundleStatLabel: { fontSize: 10, color: '#888', textTransform: 'uppercase' },
  bundleStatValue: { fontSize: 18, fontWeight: 700, color: '#fff' },
  affectedRoutes: { display: 'flex', flexDirection: 'column', gap: 2, marginBottom: 8 },
  affectedRoute: { display: 'flex', justifyContent: 'space-between', padding: '3px 6px', background: '#0f0f1a', borderRadius: 3, fontSize: 11 },
  routeLazy: { fontSize: 9, padding: '1px 4px', borderRadius: 2, background: '#2a2a4e', color: '#4E79A7' },
  moreRoutes: { fontSize: 10, color: '#666', textAlign: 'center', padding: 4 },
  link: { color: '#4E79A7', fontSize: 12, textDecoration: 'none' },
  drillingRow: { display: 'flex', flexDirection: 'column', gap: 4, padding: '6px 0', borderBottom: '1px solid #20203a' },
  drillingProp: { fontSize: 12, color: '#e0e0e0', fontWeight: 600 },
  drillingDepth: { fontSize: 10, color: '#FF9800' },
  drillingChain: { display: 'flex', flexWrap: 'wrap', gap: 4, fontSize: 10 },
  chainNode: (uses: boolean) => ({ padding: '2px 6px', borderRadius: 3, background: uses ? '#1f3a1f' : '#3a2f1f', color: uses ? '#7CFC7C' : '#FFB347' }),
  statsRow: { display: 'flex', gap: 8, marginBottom: 10 },
  statCard: { flex: 1, background: '#0f0f1a', borderRadius: 4, padding: 10, display: 'flex', flexDirection: 'column', gap: 4, alignItems: 'center' },
  statLabel: { fontSize: 10, color: '#888', textTransform: 'uppercase' },
  statValue: { fontSize: 20, fontWeight: 700, color: '#fff' },
  routeTree: { background: '#1a1a2e', borderRadius: 6, padding: 8, border: '1px solid #2a2a4e' },
  routeRow: { display: 'flex', alignItems: 'center', gap: 6, padding: '4px 8px', fontSize: 11, borderBottom: '1px solid #20203a', fontFamily: 'ui-monospace, monospace' },
  routeIcon: { width: 16, textAlign: 'center' },
  routePath: { color: '#4E79A7', fontWeight: 600, minWidth: 120 },
  routeArrow: { color: '#666' },
  routeComponent: { color: '#e0e0e0' },
  routeFile: { color: '#555', fontSize: 10, marginLeft: 'auto' },
  hookStats: { display: 'flex', gap: 8, marginBottom: 10 },
  hookStat: (itype: string) => ({ flex: 1, background: '#0f0f1a', borderRadius: 4, padding: 8, display: 'flex', flexDirection: 'column', gap: 2, alignItems: 'center', borderLeft: `3px solid ${itype === 'missing_dep' ? '#F44336' : itype === 'empty_deps' ? '#FF9800' : '#4CAF50'}` }),
  hookStatCount: { fontSize: 18, fontWeight: 700, color: '#fff' },
  hookStatLabel: { fontSize: 9, color: '#888', textTransform: 'uppercase' },
  hookList: { display: 'flex', flexDirection: 'column', gap: 2 },
  hookRow: { display: 'flex', alignItems: 'center', gap: 8, padding: '6px 8px', background: '#0f0f1a', borderRadius: 4, fontSize: 11 },
  hookIcon: (itype: string) => ({ fontSize: 12 }),
  hookInfo: { display: 'flex', flexDirection: 'column', minWidth: 120 },
  hookType: { color: '#4E79A7', fontWeight: 600, fontSize: 11 },
  hookFile: { color: '#555', fontSize: 9, fontFamily: 'ui-monospace, monospace' },
  hookDesc: { color: '#aaa', fontSize: 10, flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' },
  empty: { fontSize: 12, color: '#555', fontStyle: 'italic', padding: 8 },
  contextList: { display: 'flex', flexDirection: 'column', gap: 4 },
  contextRow: { display: 'flex', alignItems: 'center', gap: 8, padding: '6px 8px', background: '#0f0f1a', borderRadius: 4, fontSize: 11 },
  contextRisk: { padding: '2px 6px', borderRadius: 3, fontSize: 9, fontWeight: 700, color: '#fff', minWidth: 50, textAlign: 'center' },
  contextInfo: { flex: 1, display: 'flex', flexDirection: 'column' },
  contextName: { color: '#e0e0e0', fontWeight: 600 },
  contextFile: { color: '#555', fontSize: 9, fontFamily: 'ui-monospace, monospace' },
  contextConsumers: { display: 'flex', flexDirection: 'column', alignItems: 'center', minWidth: 50 },
  consumerCount: { fontSize: 16, fontWeight: 700, color: '#fff' },
  consumerLabel: { fontSize: 8, color: '#888', textTransform: 'uppercase' },
  consumerBar: { flex: '0 0 80px', height: 6, background: '#0f0f1a', borderRadius: 3, overflow: 'hidden' },
  consumerBarFill: { height: '100%', borderRadius: 3, transition: 'width 0.3s' },
}
