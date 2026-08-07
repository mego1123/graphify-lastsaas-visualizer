'use client'

import { useEffect, useState, useMemo } from 'react'

type TopSymbol = {
  label: string
  degree: number
  source_file: string
}

type CommunityInfo = {
  id: number
  label: string
  color: string
  count: number
  top_symbols: TopSymbol[]
}

type Subsystem = {
  name: string
  communities: CommunityInfo[]
  total_communities: number
  total_nodes: number
}

type GodNode = {
  rank: number
  label: string
  degree: number
  source_file: string
  community: number
  community_name: string
}

type ChecklistItem = {
  capability: string
  subsystem: string
  present: boolean
}

type ArchData = {
  subsystems: Subsystem[]
  god_nodes: GodNode[]
  checklist: ChecklistItem[]
  totals: {
    nodes: number
    edges: number
    communities: number
    subsystems: number
  }
}

// Color palette for subsystems (deterministic by index)
const SUBSYSTEM_COLORS = [
  '#4E79A7', '#F28E2B', '#E15759', '#76B7B2', '#59A14F',
  '#EDC948', '#B07AA1', '#FF9DA7', '#9C755F', '#BAB0AC',
  '#86BCB6', '#A0CBE8', '#F1CE63', '#D37295', '#6E5168',
  '#0173B2', '#DE8F05', '#029E73', '#CC78BC', '#CA9161',
]

export default function ArchitectureView({
  onSelectNode,
}: {
  onSelectNode?: (communityId: number) => void
}) {
  const [data, setData] = useState<ArchData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [expandedSub, setExpandedSub] = useState<string | null>(null)
  const [selectedSub, setSelectedSub] = useState<Subsystem | null>(null)
  const [selectedComm, setSelectedComm] = useState<CommunityInfo | null>(null)

  useEffect(() => {
    let cancelled = false
    fetch('/architecture.json')
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`)
        return r.json() as Promise<ArchData>
      })
      .then((d) => {
        if (cancelled) return
        setData(d)
        setLoading(false)
      })
      .catch((e) => {
        if (cancelled) return
        console.error(e)
        setError(String(e))
        setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [])

  const totalNodes = data?.totals.nodes ?? 0

  if (loading) {
    return (
      <div style={styles.loading}>
        <div style={styles.spinner} />
        <p style={{ color: '#888', fontSize: 13 }}>Loading architecture…</p>
      </div>
    )
  }
  if (error || !data) {
    return (
      <div style={styles.error}>
        <p>Failed to load architecture data.</p>
        <pre style={{ fontSize: 11 }}>{error}</pre>
      </div>
    )
  }

  return (
    <div style={styles.container}>
      {/* Left column: subsystem treemap */}
      <div style={styles.leftCol}>
        <div style={styles.sectionHeader}>
          <h2 style={styles.sectionTitle}>Subsystem Breakdown</h2>
          <span style={styles.sectionMeta}>
            {data.totals.subsystems} subsystems · {data.totals.communities} communities ·{' '}
            {data.totals.nodes.toLocaleString()} nodes
          </span>
        </div>

        {/* Treemap-style bars */}
        <div style={styles.treemap}>
          {data.subsystems.map((sub, idx) => {
            const pct = (sub.total_nodes / totalNodes) * 100
            const color = SUBSYSTEM_COLORS[idx % SUBSYSTEM_COLORS.length]
            const isExpanded = expandedSub === sub.name
            return (
              <div key={sub.name} style={styles.subsystemBlock}>
                <div
                  style={{
                    ...styles.subsystemBar,
                    background: color,
                    flex: sub.total_nodes,
                  }}
                  onClick={() => {
                    setExpandedSub(isExpanded ? null : sub.name)
                    setSelectedSub(isExpanded ? null : sub)
                    setSelectedComm(null)
                  }}
                  title={`${sub.name} — ${sub.total_nodes} nodes (${pct.toFixed(1)}%)`}
                >
                  <span style={styles.barLabel}>
                    {sub.name}
                  </span>
                  <span style={styles.barCount}>{sub.total_nodes}</span>
                </div>
                {isExpanded && (
                  <div style={styles.expandedRow}>
                    <div style={styles.commBarList}>
                      {sub.communities.map((c) => {
                        const maxCount = Math.max(...sub.communities.map((x) => x.count))
                        const w = (c.count / maxCount) * 100
                        return (
                          <div
                            key={c.id}
                            style={{
                              ...styles.commRow,
                              background:
                                selectedComm?.id === c.id ? '#2a2a4e' : 'transparent',
                            }}
                            onClick={() => {
                              setSelectedComm(c)
                              onSelectNode?.(c.id)
                            }}
                          >
                            <span style={{ ...styles.commDot, background: c.color }} />
                            <span style={styles.commLabel}>{c.label}</span>
                            <span style={styles.commCount}>{c.count}</span>
                            <div style={styles.commBarTrack}>
                              <div
                                style={{
                                  ...styles.commBarFill,
                                  width: `${w}%`,
                                  background: c.color,
                                }}
                              />
                            </div>
                          </div>
                        )
                      })}
                    </div>
                  </div>
                )}
              </div>
            )
          })}
        </div>

        {/* God nodes table */}
        <div style={styles.sectionHeader}>
          <h2 style={styles.sectionTitle}>God Nodes — architectural pillars</h2>
          <span style={styles.sectionMeta}>top {data.god_nodes.length} by degree</span>
        </div>
        <div style={styles.godTable}>
          {data.god_nodes.map((n) => (
            <div key={n.rank} style={styles.godRow}>
              <span style={styles.godRank}>{n.rank}</span>
              <span style={styles.godLabel}>{n.label}</span>
              <span style={styles.godDegree}>{n.degree}°</span>
              <span style={styles.godComm}>{n.community_name}</span>
              <code style={styles.godSrc}>{n.source_file}</code>
            </div>
          ))}
        </div>
      </div>

      {/* Right column: details + checklist */}
      <div style={styles.rightCol}>
        {/* Selected community details */}
        <div style={styles.panel}>
          <h3 style={styles.panelTitle}>Community Details</h3>
          {!selectedComm ? (
            <p style={styles.empty}>
              Click a subsystem to expand it, then click a community to see its top symbols.
            </p>
          ) : (
            <div style={styles.detailContent}>
              <div style={styles.detailHeader}>
                <span
                  style={{
                    ...styles.detailDot,
                    background: selectedComm.color,
                  }}
                />
                <h4 style={styles.detailName}>{selectedComm.label}</h4>
              </div>
              <div style={styles.detailMeta}>
                <span>Community #{selectedComm.id}</span>
                <span>·</span>
                <span>{selectedComm.count} nodes</span>
              </div>
              <h5 style={styles.subPanelTitle}>Top symbols (by degree)</h5>
              <div style={styles.symbolList}>
                {selectedComm.top_symbols.map((s, i) => (
                  <div key={i} style={styles.symbolRow}>
                    <span style={styles.symbolRank}>{i + 1}</span>
                    <span style={styles.symbolLabel}>{s.label}</span>
                    <span style={styles.symbolDeg}>{s.degree}°</span>
                    <code style={styles.symbolSrc}>{s.source_file || '—'}</code>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Capability checklist */}
        <div style={styles.panel}>
          <h3 style={styles.panelTitle}>SaaS Capability Checklist</h3>
          <div style={styles.checklist}>
            {data.checklist.map((c) => (
              <div key={c.capability} style={styles.checklistItem}>
                <span
                  style={{
                    ...styles.check,
                    background: c.present ? '#1f3a1f' : '#3a1f1f',
                    color: c.present ? '#7CFC7C' : '#FF6B6B',
                  }}
                >
                  {c.present ? '✓' : '✗'}
                </span>
                <span style={styles.checklistCap}>{c.capability}</span>
                {c.present && (
                  <span style={styles.checklistSub}>{c.subsystem}</span>
                )}
              </div>
            ))}
          </div>
          <div style={styles.checklistSummary}>
            {data.checklist.filter((c) => c.present).length} / {data.checklist.length}{' '}
            capabilities present
          </div>
        </div>

        {/* Link to full markdown report */}
        <div style={styles.panel}>
          <h3 style={styles.panelTitle}>Full Report</h3>
          <a
            href="/ARCHITECTURE_MAP.md"
            target="_blank"
            rel="noreferrer"
            style={styles.reportLink}
          >
            Open ARCHITECTURE_MAP.md →
          </a>
          <p style={styles.reportHint}>
            Includes cross-subsystem bridges (high-risk integration points) and per-community
            symbol lists not shown here.
          </p>
        </div>
      </div>
    </div>
  )
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    display: 'flex',
    gap: 16,
    padding: 16,
    height: '100%',
    overflow: 'hidden',
    background: '#0f0f1a',
    color: '#e0e0e0',
  },
  leftCol: { flex: 2, overflowY: 'auto', paddingRight: 8 },
  rightCol: {
    flex: 1,
    overflowY: 'auto',
    display: 'flex',
    flexDirection: 'column',
    gap: 12,
  },
  loading: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    height: '100%',
    gap: 12,
    background: '#0f0f1a',
  },
  spinner: {
    width: 32,
    height: 32,
    border: '3px solid #2a2a4e',
    borderTopColor: '#4E79A7',
    borderRadius: '50%',
    animation: 'spin 1s linear infinite',
  },
  error: {
    padding: 24,
    color: '#ff6b6b',
    background: '#0f0f1a',
    height: '100%',
  },
  sectionHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'baseline',
    marginBottom: 10,
    marginTop: 16,
  },
  sectionTitle: {
    fontSize: 14,
    color: '#fff',
    margin: 0,
    fontWeight: 600,
  },
  sectionMeta: { fontSize: 11, color: '#888' },
  treemap: {
    display: 'flex',
    flexDirection: 'row',
    gap: 2,
    height: 80,
    marginBottom: 12,
    background: '#1a1a2e',
    borderRadius: 6,
    padding: 4,
    overflow: 'hidden',
  },
  subsystemBlock: { display: 'flex', flexDirection: 'column', minWidth: 0 },
  subsystemBar: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    cursor: 'pointer',
    minWidth: 24,
    borderRadius: 4,
    padding: '4px 6px',
    color: '#fff',
    fontWeight: 600,
    fontSize: 10,
    textShadow: '0 1px 2px rgba(0,0,0,0.6)',
    transition: 'transform 0.15s',
    overflow: 'hidden',
  },
  barLabel: {
    writingMode: 'vertical-rl',
    textOrientation: 'mixed',
    transform: 'rotate(180deg)',
    whiteSpace: 'nowrap',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    maxHeight: 60,
    fontSize: 10,
  },
  barCount: { fontSize: 10, marginTop: 4 },
  expandedRow: {
    background: '#1a1a2e',
    borderRadius: 6,
    padding: 8,
    marginTop: 4,
    border: '1px solid #2a2a4e',
  },
  commBarList: { display: 'flex', flexDirection: 'column', gap: 2 },
  commRow: {
    display: 'flex',
    alignItems: 'center',
    gap: 8,
    padding: '4px 6px',
    cursor: 'pointer',
    borderRadius: 4,
    fontSize: 11,
  },
  commDot: { width: 8, height: 8, borderRadius: '50%', flexShrink: 0 },
  commLabel: {
    flex: 1,
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    whiteSpace: 'nowrap',
    color: '#ccc',
  },
  commCount: { color: '#666', fontSize: 10, width: 30, textAlign: 'right' },
  commBarTrack: {
    flex: '0 0 100px',
    height: 4,
    background: '#0f0f1a',
    borderRadius: 2,
    overflow: 'hidden',
  },
  commBarFill: { height: '100%', borderRadius: 2 },
  godTable: {
    display: 'flex',
    flexDirection: 'column',
    gap: 2,
    background: '#1a1a2e',
    borderRadius: 6,
    padding: 8,
  },
  godRow: {
    display: 'grid',
    gridTemplateColumns: '24px 1fr 50px 1.5fr 2fr',
    gap: 8,
    padding: '4px 4px',
    fontSize: 11,
    alignItems: 'center',
    borderBottom: '1px solid #20203a',
  },
  godRank: { color: '#666', textAlign: 'right' },
  godLabel: { color: '#e0e0e0', fontWeight: 600, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' },
  godDegree: { color: '#4E79A7', fontWeight: 600 },
  godComm: { color: '#aaa', fontSize: 10, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' },
  godSrc: {
    color: '#666',
    fontSize: 10,
    fontFamily: 'ui-monospace, "SF Mono", Menlo, monospace',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    whiteSpace: 'nowrap',
  },
  panel: {
    background: '#1a1a2e',
    borderRadius: 6,
    padding: 12,
    border: '1px solid #2a2a4e',
  },
  panelTitle: {
    fontSize: 11,
    color: '#888',
    textTransform: 'uppercase',
    letterSpacing: '0.05em',
    margin: '0 0 8px 0',
    fontWeight: 600,
  },
  empty: { fontSize: 12, color: '#555', fontStyle: 'italic' },
  detailContent: { fontSize: 12, color: '#ccc' },
  detailHeader: { display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 },
  detailDot: { width: 12, height: 12, borderRadius: '50%' },
  detailName: { fontSize: 14, color: '#fff', margin: 0, fontWeight: 600 },
  detailMeta: { display: 'flex', gap: 6, fontSize: 11, color: '#888', marginBottom: 10 },
  subPanelTitle: {
    fontSize: 10,
    color: '#888',
    textTransform: 'uppercase',
    letterSpacing: '0.05em',
    margin: '8px 0 4px 0',
  },
  symbolList: { display: 'flex', flexDirection: 'column', gap: 2 },
  symbolRow: {
    display: 'grid',
    gridTemplateColumns: '20px 1fr 40px 2fr',
    gap: 6,
    padding: '3px 0',
    fontSize: 11,
    borderBottom: '1px solid #20203a',
  },
  symbolRank: { color: '#666', textAlign: 'right' },
  symbolLabel: { color: '#e0e0e0', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' },
  symbolDeg: { color: '#4E79A7', fontSize: 10 },
  symbolSrc: {
    color: '#666',
    fontSize: 10,
    fontFamily: 'ui-monospace, "SF Mono", Menlo, monospace',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    whiteSpace: 'nowrap',
  },
  checklist: { display: 'flex', flexDirection: 'column', gap: 4 },
  checklistItem: {
    display: 'grid',
    gridTemplateColumns: '20px 1fr 1.4fr',
    gap: 8,
    padding: '4px 0',
    fontSize: 11,
    alignItems: 'center',
  },
  check: {
    width: 16,
    height: 16,
    borderRadius: 3,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontWeight: 700,
    fontSize: 10,
  },
  checklistCap: { color: '#ccc' },
  checklistSub: {
    color: '#666',
    fontSize: 10,
    fontStyle: 'italic',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    whiteSpace: 'nowrap',
  },
  checklistSummary: {
    marginTop: 8,
    paddingTop: 8,
    borderTop: '1px solid #2a2a4e',
    fontSize: 11,
    color: '#4E79A7',
    fontWeight: 600,
  },
  reportLink: {
    display: 'inline-block',
    color: '#4E79A7',
    textDecoration: 'none',
    fontSize: 12,
    padding: '6px 10px',
    border: '1px solid #3a3a5e',
    borderRadius: 4,
    background: '#0f0f1a',
  },
  reportHint: {
    marginTop: 6,
    fontSize: 10,
    color: '#666',
    lineHeight: 1.5,
  },
}
