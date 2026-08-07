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

type ComplexityItem = {
  name: string
  file: string
  lines: number
  prop_count: number
  hook_count: number
  nesting_depth: number
  complexity_score: number
  flags: string[]
}

type I18nData = {
  has_i18n: boolean
  hardcoded_count: number
  translated_count: number
  coverage_pct: number
  hardcoded_samples: Array<{ text: string; type: string; file: string }>
}

type A11yIssue = {
  file: string
  line: number
  severity: string
  rule: string
  message: string
}

type TestCoverageData = {
  total_components: number
  with_tests: number
  without_tests: number
  coverage_pct: number
  untested: Array<{ name: string; file: string }>
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
  const [complexity, setComplexity] = useState<ComplexityItem[]>([])
  const [i18n, setI18n] = useState<I18nData | null>(null)
  const [a11y, setA11y] = useState<A11yIssue[]>([])
  const [testCoverage, setTestCoverage] = useState<TestCoverageData | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      fetch('/dead-components.json').then(r => r.json()).catch(() => []),
      fetch('/route-tree.json').then(r => r.json()).catch(() => []),
      fetch('/bundle-impact.json').then(r => r.json()).catch(() => null),
      fetch('/prop-drilling.json').then(r => r.json()).catch(() => []),
      fetch('/hook-deps.json').then(r => r.json()).catch(() => []),
      fetch('/context-usage.json').then(r => r.json()).catch(() => []),
      fetch('/complexity.json').then(r => r.json()).catch(() => []),
      fetch('/i18n.json').then(r => r.json()).catch(() => null),
      fetch('/a11y.json').then(r => r.json()).catch(() => []),
      fetch('/test-coverage.json').then(r => r.json()).catch(() => null),
    ]).then(([dead, rts, bi, pd, hd, cu, cx, i18nData, a11yData, tc]) => {
      setDeadComponents(dead)
      setRoutes(rts)
      setBundleImpact(bi)
      setPropDrilling(pd)
      setHookIssues(hd)
      setContexts(cu)
      setComplexity(cx)
      setI18n(i18nData)
      setA11y(a11yData)
      setTestCoverage(tc)
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

        {/* Component Complexity */}
        <div style={styles.sectionHeader}>
          <h2 style={styles.sectionTitle}>📊 Component Complexity</h2>
          <span style={styles.sectionMeta}>
            {complexity.length} components, {complexity.filter(c => c.flags.length > 0).length} flagged
          </span>
        </div>
        <div style={styles.panel}>
          {complexity.length === 0 ? (
            <p style={styles.empty}>No components analyzed.</p>
          ) : (
            <>
              <div style={styles.complexList}>
                {complexity.slice(0, 8).map((c, i) => (
                  <div key={i} style={styles.complexRow}>
                    <span style={styles.complexScore(c.complexity_score)}>{c.complexity_score}</span>
                    <div style={styles.complexInfo}>
                      <span style={styles.complexName}>{c.name}</span>
                      <span style={styles.complexFile}>{c.file}</span>
                    </div>
                    <div style={styles.complexMetrics}>
                      <span style={styles.metricTag}>{c.lines}L</span>
                      <span style={styles.metricTag}>{c.prop_count}P</span>
                      <span style={styles.metricTag}>{c.hook_count}H</span>
                      <span style={styles.metricTag}>{c.nesting_depth}D</span>
                    </div>
                    {c.flags.length > 0 && (
                      <span style={styles.flagBadge}>⚠️</span>
                    )}
                  </div>
                ))}
              </div>
              {complexity.length > 8 && (
                <span style={styles.moreRoutes}>+ {complexity.length - 8} more</span>
              )}
            </>
          )}
        </div>

        {/* i18n Coverage */}
        {i18n && (
          <>
            <div style={styles.sectionHeader}>
              <h2 style={styles.sectionTitle}>🌍 i18n Coverage</h2>
              <span style={styles.sectionMeta}>{i18n.coverage_pct.toFixed(0)}% translated</span>
            </div>
            <div style={styles.panel}>
              <div style={styles.i18nBar}>
                <div
                  style={{
                    ...styles.i18nFill,
                    width: `${i18n.coverage_pct}%`,
                    background: i18n.coverage_pct > 50 ? '#4CAF50' : i18n.coverage_pct > 20 ? '#FF9800' : '#F44336',
                  }}
                />
              </div>
              <div style={styles.i18nStats}>
                <span style={styles.i18nStat}>
                  <span style={styles.i18nStatVal}>{i18n.translated_count}</span> translated
                </span>
                <span style={styles.i18nStat}>
                  <span style={styles.i18nStatVal}>{i18n.hardcoded_count}</span> hardcoded
                </span>
                {!i18n.has_i18n && (
                  <span style={styles.i18nWarning}>⚠️ No i18n library detected</span>
                )}
              </div>
              {i18n.hardcoded_samples.length > 0 && (
                <div style={styles.hardcodedList}>
                  <span style={styles.hardcodedTitle}>Sample hardcoded strings:</span>
                  {i18n.hardcoded_samples.slice(0, 5).map((s, i) => (
                    <div key={i} style={styles.hardcodedItem}>
                      <code style={styles.hardcodedText}>"{s.text.slice(0, 30)}"</code>
                      <span style={styles.hardcodedType}>{s.type}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </>
        )}

        {/* Accessibility */}
        <div style={styles.sectionHeader}>
          <h2 style={styles.sectionTitle}>♿ Accessibility</h2>
          <span style={styles.sectionMeta}>{a11y.length} issues</span>
        </div>
        <div style={styles.panel}>
          {a11y.length === 0 ? (
            <p style={styles.successMsg}>✅ No accessibility issues found.</p>
          ) : (
            <>
              <div style={styles.a11yStats}>
                {['high', 'medium'].map(sev => {
                  const count = a11y.filter(a => a.severity === sev).length
                  if (count === 0) return null
                  return (
                    <div key={sev} style={styles.a11yStat(sev)}>
                      <span style={styles.a11yStatCount}>{count}</span>
                      <span style={styles.a11yStatLabel}>{sev}</span>
                    </div>
                  )
                })}
              </div>
              <div style={styles.a11yList}>
                {a11y.slice(0, 6).map((a, i) => (
                  <div key={i} style={styles.a11yRow}>
                    <span style={styles.a11yIcon(a.severity)}>
                      {a.severity === 'high' ? '🔴' : '🟡'}
                    </span>
                    <div style={styles.a11yInfo}>
                      <span style={styles.a11yRule}>{a.rule}</span>
                      <span style={styles.a11yFile}>{a.file}:{a.line}</span>
                    </div>
                    <span style={styles.a11yMsg}>{a.message}</span>
                  </div>
                ))}
                {a11y.length > 6 && (
                  <span style={styles.moreRoutes}>+ {a11y.length - 6} more issues</span>
                )}
              </div>
            </>
          )}
        </div>

        {/* Test Coverage */}
        {testCoverage && (
          <>
            <div style={styles.sectionHeader}>
              <h2 style={styles.sectionTitle}>🧪 Test Coverage</h2>
              <span style={styles.sectionMeta}>{testCoverage.coverage_pct.toFixed(0)}%</span>
            </div>
            <div style={styles.panel}>
              <div style={styles.coverageBar}>
                <div
                  style={{
                    ...styles.coverageFill,
                    width: `${testCoverage.coverage_pct}%`,
                    background: testCoverage.coverage_pct > 80 ? '#4CAF50' : testCoverage.coverage_pct > 50 ? '#FF9800' : '#F44336',
                  }}
                />
              </div>
              <div style={styles.coverageStats}>
                <span style={styles.coverageStat}>
                  <span style={styles.coverageStatVal}>{testCoverage.with_tests}</span> tested
                </span>
                <span style={styles.coverageStat}>
                  <span style={styles.coverageStatVal}>{testCoverage.without_tests}</span> untested
                </span>
                <span style={styles.coverageStat}>
                  <span style={styles.coverageStatVal}>{testCoverage.total_components}</span> total
                </span>
              </div>
              {testCoverage.untested.length > 0 && (
                <div style={styles.untestedList}>
                  <span style={styles.untestedTitle}>Untested components:</span>
                  <div style={styles.untestedChips}>
                    {testCoverage.untested.slice(0, 12).map((u, i) => (
                      <span key={i} style={styles.untestedChip}>{u.name}</span>
                    ))}
                    {testCoverage.without_tests > 12 && (
                      <span style={styles.moreUntested}>+{testCoverage.without_tests - 12} more</span>
                    )}
                  </div>
                </div>
              )}
            </div>
          </>
        )}

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
  complexList: { display: 'flex', flexDirection: 'column', gap: 2 },
  complexRow: { display: 'flex', alignItems: 'center', gap: 8, padding: '6px 8px', background: '#0f0f1a', borderRadius: 4, fontSize: 11 },
  complexScore: (score: number) => ({ width: 32, textAlign: 'center', fontSize: 14, fontWeight: 700, color: score > 100 ? '#F44336' : score > 50 ? '#FF9800' : '#4CAF50' }),
  complexInfo: { flex: 1, display: 'flex', flexDirection: 'column' },
  complexName: { color: '#e0e0e0', fontWeight: 600, fontSize: 11 },
  complexFile: { color: '#555', fontSize: 9, fontFamily: 'ui-monospace, monospace' },
  complexMetrics: { display: 'flex', gap: 3 },
  metricTag: { fontSize: 9, padding: '1px 4px', borderRadius: 2, background: '#2a2a4e', color: '#aaa', fontFamily: 'ui-monospace, monospace' },
  flagBadge: { fontSize: 12 },
  i18nBar: { height: 10, background: '#0f0f1a', borderRadius: 5, overflow: 'hidden', marginBottom: 8 },
  i18nFill: { height: '100%', borderRadius: 5, transition: 'width 0.3s' },
  i18nStats: { display: 'flex', gap: 12, fontSize: 11, color: '#aaa', alignItems: 'center' },
  i18nStat: { display: 'flex', gap: 4 },
  i18nStatVal: { fontWeight: 700, color: '#fff' },
  i18nWarning: { color: '#FF6B6B', fontSize: 10 },
  hardcodedList: { marginTop: 8, display: 'flex', flexDirection: 'column', gap: 3 },
  hardcodedTitle: { fontSize: 10, color: '#888' },
  hardcodedItem: { display: 'flex', gap: 6, alignItems: 'center' },
  hardcodedText: { fontSize: 10, color: '#FFB347', fontFamily: 'ui-monospace, monospace' },
  hardcodedType: { fontSize: 9, color: '#666', padding: '1px 4px', background: '#2a2a4e', borderRadius: 2 },
  a11yStats: { display: 'flex', gap: 8, marginBottom: 8 },
  a11yStat: (sev: string) => ({ flex: 1, background: '#0f0f1a', borderRadius: 4, padding: 8, display: 'flex', flexDirection: 'column', alignItems: 'center', borderLeft: `3px solid ${sev === 'high' ? '#F44336' : '#FF9800'}` }),
  a11yStatCount: { fontSize: 16, fontWeight: 700, color: '#fff' },
  a11yStatLabel: { fontSize: 9, color: '#888', textTransform: 'uppercase' },
  a11yList: { display: 'flex', flexDirection: 'column', gap: 2 },
  a11yRow: { display: 'flex', alignItems: 'center', gap: 8, padding: '4px 6px', background: '#0f0f1a', borderRadius: 3, fontSize: 10 },
  a11yIcon: (sev: string) => ({ fontSize: 10 }),
  a11yInfo: { display: 'flex', flexDirection: 'column', minWidth: 100 },
  a11yRule: { color: '#4E79A7', fontWeight: 600, fontSize: 10 },
  a11yFile: { color: '#555', fontSize: 9, fontFamily: 'ui-monospace, monospace' },
  a11yMsg: { color: '#aaa', flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' },
  coverageBar: { height: 10, background: '#0f0f1a', borderRadius: 5, overflow: 'hidden', marginBottom: 8 },
  coverageFill: { height: '100%', borderRadius: 5, transition: 'width 0.3s' },
  coverageStats: { display: 'flex', gap: 12, fontSize: 11, color: '#aaa' },
  coverageStat: { display: 'flex', gap: 4 },
  coverageStatVal: { fontWeight: 700, color: '#fff' },
  untestedList: { marginTop: 8 },
  untestedTitle: { fontSize: 10, color: '#888', display: 'block', marginBottom: 4 },
  untestedChips: { display: 'flex', flexWrap: 'wrap', gap: 4 },
  untestedChip: { fontSize: 10, padding: '2px 6px', borderRadius: 3, background: '#3a1f1f', color: '#FF6B6B', fontFamily: 'ui-monospace, monospace' },
  moreUntested: { fontSize: 10, color: '#666', alignSelf: 'center' },
}
