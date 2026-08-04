'use client'

import { useEffect, useRef, useState, useMemo } from 'react'
import { Network, DataSet } from 'vis-network/standalone'
import { Input } from '@/components/ui/input'

type RawNode = {
  id: string
  label: string
  community: number
  community_name: string
  color: string
  size: number
  source_file: string
  file_type: string
  degree: number
}

type RawEdge = {
  from: string
  to: string
  label: string
  context: string
  confidence: string
}

type Community = {
  id: number
  label: string
  color: string
  count: number
}

export default function GraphView({
  focusCommunityId,
}: {
  focusCommunityId?: number | null
}) {
  const containerRef = useRef<HTMLDivElement | null>(null)
  const networkRef = useRef<Network | null>(null)
  const nodesDSRef = useRef<DataSet<any> | null>(null)
  const edgesDSRef = useRef<DataSet<any> | null>(null)

  const [nodes, setNodes] = useState<RawNode[]>([])
  const [edges, setEdges] = useState<RawEdge[]>([])
  const [communities, setCommunities] = useState<Community[]>([])

  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState<string | null>(null)

  const [search, setSearch] = useState('')

  const [selected, setSelected] = useState<RawNode | null>(null)
  const [selectedEdges, setSelectedEdges] = useState<
    Array<{ dir: 'in' | 'out'; label: string; other: string; context: string; confidence: string }>
  >([])

  const [hidden, setHidden] = useState<Set<number>>(new Set())
  const [selectAll, setSelectAll] = useState(true)

  const [stats, setStats] = useState({ nodes: 0, edges: 0, communities: 0 })

  // ---- Load graph data ----
  useEffect(() => {
    let cancelled = false
    Promise.all([
      fetch('/graph-nodes.json').then((r) => r.json()),
      fetch('/graph-edges.json').then((r) => r.json()),
      fetch('/graph-communities.json').then((r) => r.json()),
    ])
      .then(([n, e, c]: [RawNode[], RawEdge[], Community[]]) => {
        if (cancelled) return
        setNodes(n)
        setEdges(e)
        setCommunities(c)
        setStats({ nodes: n.length, edges: e.length, communities: c.length })
        setLoading(false)
      })
      .catch((err) => {
        if (cancelled) return
        console.error(err)
        setLoadError(String(err))
        setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [])

  // ---- Build network once data arrives ----
  useEffect(() => {
    if (!containerRef.current || loading || nodes.length === 0) return

    const nodesDS = new DataSet(
      nodes.map((n) => ({
        id: n.id,
        label: n.label,
        community: n.community,
        title: n.label,
        size: n.size,
        color: {
          background: n.color,
          border: n.color,
          highlight: { background: '#ffffff', border: n.color },
        },
        font: { size: 0, color: '#ffffff' },
        raw: n,
      }))
    )
    const edgesDS = new DataSet(
      edges.map((e, i) => ({
        id: `e${i}`,
        from: e.from,
        to: e.to,
        label: undefined,
        arrows: 'to',
        color: { color: 'rgba(140,140,180,0.35)', highlight: '#4E79A7' },
        width: 0.6,
        smooth: { type: 'continuous', roundness: 0.2 },
        raw: e,
      }))
    )
    nodesDSRef.current = nodesDS
    edgesDSRef.current = edgesDS

    const net = new Network(
      containerRef.current,
      { nodes: nodesDS, edges: edgesDS },
      {
        nodes: { shape: 'dot', borderWidth: 1.5 },
        edges: { smooth: { type: 'continuous', roundness: 0.2 }, selectionWidth: 3 },
        physics: {
          solver: 'forceAtlas2Based',
          forceAtlas2Based: {
            gravitationalConstant: -30,
            centralGravity: 0.005,
            springLength: 50,
            springConstant: 0.05,
            damping: 0.4,
            avoidOverlap: 0.5,
          },
          stabilization: { enabled: true, iterations: 200, fit: true },
          timestep: 0.35,
        },
        interaction: {
          hover: true,
          tooltipDelay: 150,
          navigationButtons: true,
          keyboard: false,
          multiselect: false,
        },
      }
    )
    networkRef.current = net

    net.on('click', (params: any) => {
      const id = params?.nodes?.[0]
      if (!id) {
        setSelected(null)
        setSelectedEdges([])
        return
      }
      const node = nodesDS.get(id)
      if (!node?.raw) return
      const raw = node.raw as RawNode
      setSelected(raw)
      const connected = edges
        .filter((e) => e.from === id || e.to === id)
        .map((e) => {
          const out = e.from === id
          return {
            dir: out ? ('out' as const) : ('in' as const),
            label: e.label || e.context || '',
            other: out ? e.to : e.from,
            context: e.context || '',
            confidence: e.confidence || '',
          }
        })
        .slice(0, 60)
      setSelectedEdges(connected)
    })

    return () => {
      net.destroy()
      networkRef.current = null
      nodesDSRef.current = null
      edgesDSRef.current = null
    }
  }, [loading, nodes, edges])

  // ---- External focus trigger (from Architecture tab) ----
  useEffect(() => {
    if (focusCommunityId == null || focusCommunityId < 0) return
    if (loading) return  // wait for graph to load first
    const net = networkRef.current
    if (!net || nodes.length === 0) return
    // Find first node in this community
    const target = nodes.find((n) => n.community === focusCommunityId)
    if (!target) return
    // Defer focus to allow network to be ready
    const t = setTimeout(() => {
      net.selectNodes([target.id])
      net.focus(target.id, {
        scale: 1.4,
        animation: { duration: 700, easingFunction: 'easeInOutQuad' },
      })
      // Populate info panel
      setSelected(target)
      const connected = edges
        .filter((e) => e.from === target.id || e.to === target.id)
        .map((e) => {
          const out = e.from === target.id
          return {
            dir: out ? ('out' as const) : ('in' as const),
            label: e.label || e.context || '',
            other: out ? e.to : e.from,
            context: e.context || '',
            confidence: e.confidence || '',
          }
        })
        .slice(0, 60)
      setSelectedEdges(connected)
    }, 800)
    return () => clearTimeout(t)
  }, [focusCommunityId, nodes, edges, loading])

  // ---- Search (derived from `search` + `nodes`) ----
  const searchResults = useMemo<RawNode[]>(() => {
    if (!search.trim()) return []
    const q = search.toLowerCase()
    return nodes.filter((n) => n.label.toLowerCase().includes(q)).slice(0, 20)
  }, [search, nodes])
  const showSearch = search.trim().length > 0

  const focusNode = (id: string) => {
    const net = networkRef.current
    if (!net) return
    net.selectNodes([id])
    net.focus(id, { scale: 1.5, animation: { duration: 600, easingFunction: 'easeInOutQuad' } })
    const node = nodes.find((n) => n.id === id)
    if (node) {
      setSelected(node)
      const connected = edges
        .filter((e) => e.from === id || e.to === id)
        .map((e) => {
          const out = e.from === id
          return {
            dir: out ? ('out' as const) : ('in' as const),
            label: e.label || e.context || '',
            other: out ? e.to : e.from,
            context: e.context || '',
            confidence: e.confidence || '',
          }
        })
        .slice(0, 60)
      setSelectedEdges(connected)
    }
    setSearch('')
  }

  // ---- Legend toggle ----
  const toggleCommunity = (cid: number) => {
    const ds = nodesDSRef.current
    if (!ds) return
    const next = new Set(hidden)
    if (next.has(cid)) {
      next.delete(cid)
    } else {
      next.add(cid)
    }
    setHidden(next)
    const updates = nodes
      .filter((n) => n.community === cid)
      .map((n) => ({ id: n.id, hidden: next.has(cid) }))
    ds.update(updates)
    const stillAll = communities.every((c) => !next.has(c.id))
    setSelectAll(stillAll)
  }

  const toggleSelectAll = () => {
    const ds = nodesDSRef.current
    if (!ds) return
    const nextAll = !selectAll
    setSelectAll(nextAll)
    if (nextAll) {
      setHidden(new Set())
      ds.update(nodes.map((n) => ({ id: n.id, hidden: false })))
    } else {
      const all = new Set(communities.map((c) => c.id))
      setHidden(all)
      ds.update(nodes.map((n) => ({ id: n.id, hidden: true })))
    }
  }

  const sortedCommunities = useMemo(
    () => [...communities].sort((a, b) => b.count - a.count),
    [communities]
  )

  const topGodNodes = useMemo(() => {
    return [...nodes].sort((a, b) => b.degree - a.degree).slice(0, 12)
  }, [nodes])

  return (
    <div style={styles.split}>
      {/* Graph canvas */}
      <div style={styles.canvasWrap}>
        {loading && (
          <div style={styles.loadingOverlay}>
            <div style={styles.spinner} />
            <p style={styles.loadingText}>Loading {stats.nodes || 2507} nodes…</p>
          </div>
        )}
        {loadError && (
          <div style={styles.errorOverlay}>
            <p>Failed to load graph data.</p>
            <pre style={{ fontSize: 11 }}>{loadError}</pre>
          </div>
        )}
        <div ref={containerRef} style={{ flex: 1, background: '#0f0f1a' }} />
      </div>

        {/* Sidebar */}
        <aside style={styles.sidebar}>
          {/* Search */}
          <div style={styles.searchWrap}>
            <Input
              placeholder="Search nodes…  (e.g. AuthHandler, MongoDB)"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              onFocus={() => setShowSearch(true)}
              style={styles.searchInput}
            />
            {showSearch && searchResults.length > 0 && (
              <div style={styles.searchResults}>
                {searchResults.map((n) => (
                  <div
                    key={n.id}
                    style={styles.searchItem}
                    onClick={() => focusNode(n.id)}
                  >
                    <span
                      style={{
                        ...styles.searchDot,
                        background: n.color,
                      }}
                    />
                    <span style={styles.searchLabel}>{n.label}</span>
                    <span style={styles.searchMeta}>· {n.community_name}</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Info panel */}
          <div style={styles.infoPanel}>
            <h3 style={styles.panelTitle}>Node Info</h3>
            {!selected ? (
              <p style={styles.empty}>Click a node to inspect its connections.</p>
            ) : (
              <div style={styles.infoContent}>
                <div style={styles.field}>
                  <b>Label:</b> {selected.label}
                </div>
                <div style={styles.field}>
                  <b>Community:</b>{' '}
                  <span
                    style={{
                      ...styles.commPill,
                      background: selected.color,
                    }}
                  >
                    {selected.community_name}
                  </span>
                </div>
                <div style={styles.field}>
                  <b>Degree:</b> {selected.degree}
                </div>
                <div style={styles.field}>
                  <b>Source:</b>{' '}
                  <code style={styles.codeChip}>{selected.source_file}</code>
                </div>
                <div style={styles.field}>
                  <b>Type:</b> {selected.file_type}
                </div>

                <h4 style={styles.subTitle}>
                  Connections ({selectedEdges.length})
                </h4>
                <div style={styles.connList}>
                  {selectedEdges.slice(0, 25).map((e, i) => (
                    <div key={i} style={styles.connItem}>
                      <span style={styles.arrow}>{e.dir === 'out' ? '→' : '←'}</span>
                      <span style={styles.connLabel}>{e.label}</span>
                      <span style={styles.connOther}>{e.other}</span>
                      {e.confidence && (
                        <span
                          style={{
                            ...styles.confTag,
                            background:
                              e.confidence === 'EXTRACTED' ? '#1f3a1f' : '#3a2f1f',
                            color: e.confidence === 'EXTRACTED' ? '#7CFC7C' : '#FFB347',
                          }}
                        >
                          {e.confidence}
                        </span>
                      )}
                    </div>
                  ))}
                  {selectedEdges.length > 25 && (
                    <div style={styles.moreConn}>
                      + {selectedEdges.length - 25} more
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* God nodes */}
          <div style={styles.infoPanel}>
            <h3 style={styles.panelTitle}>God Nodes (top 12)</h3>
            <div style={styles.godList}>
              {topGodNodes.map((n, i) => (
                <div
                  key={n.id}
                  style={styles.godItem}
                  onClick={() => focusNode(n.id)}
                >
                  <span style={styles.godRank}>{i + 1}.</span>
                  <span
                    style={{
                      ...styles.godDot,
                      background: n.color,
                    }}
                  />
                  <span style={styles.godLabel}>{n.label}</span>
                  <span style={styles.godDeg}>{n.degree}°</span>
                </div>
              ))}
            </div>
          </div>

          {/* Legend */}
          <div style={styles.legendWrap}>
            <div style={styles.legendHeader}>
              <h3 style={styles.panelTitle}>Communities</h3>
              <label style={styles.selectAll}>
                <input
                  type="checkbox"
                  checked={selectAll}
                  onChange={toggleSelectAll}
                  style={styles.checkbox}
                />
                <span>All</span>
              </label>
            </div>
            <div style={styles.legendList}>
              {sortedCommunities.map((c) => (
                <div
                  key={c.id}
                  style={{
                    ...styles.legendItem,
                    opacity: hidden.has(c.id) ? 0.35 : 1,
                  }}
                  onClick={() => toggleCommunity(c.id)}
                >
                  <input
                    type="checkbox"
                    checked={!hidden.has(c.id)}
                    onChange={() => toggleCommunity(c.id)}
                    style={styles.checkbox}
                    onClick={(e) => e.stopPropagation()}
                  />
                  <span
                    style={{
                      ...styles.legendDot,
                      background: c.color,
                    }}
                  />
                  <span style={styles.legendLabel}>{c.label}</span>
                  <span style={styles.legendCount}>{c.count}</span>
                </div>
              ))}
            </div>
          </div>
        </aside>
      </div>
  )
}

const styles: Record<string, React.CSSProperties> = {
  page: {
    display: 'flex',
    flexDirection: 'column',
    height: '100vh',
    background: '#0f0f1a',
    color: '#e0e0e0',
    fontFamily:
      '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
    overflow: 'hidden',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '10px 16px',
    background: '#1a1a2e',
    borderBottom: '1px solid #2a2a4e',
    flexShrink: 0,
  },
  headerLeft: { display: 'flex', flexDirection: 'column', gap: 2 },
  title: { fontSize: 16, fontWeight: 600, color: '#fff', margin: 0 },
  subtitle: { fontSize: 12, color: '#888' },
  headerRight: { display: 'flex', gap: 8 },
  linkBtn: {
    fontSize: 12,
    color: '#4E79A7',
    textDecoration: 'none',
    padding: '6px 10px',
    border: '1px solid #3a3a5e',
    borderRadius: 6,
    background: '#0f0f1a',
  },
  split: { display: 'flex', flex: 1, overflow: 'hidden', height: '100%' },
  canvasWrap: { flex: 1, position: 'relative', display: 'flex' },
  loadingOverlay: {
    position: 'absolute',
    inset: 0,
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    background: 'rgba(15,15,26,0.9)',
    zIndex: 10,
    gap: 12,
  },
  spinner: {
    width: 32,
    height: 32,
    border: '3px solid #2a2a4e',
    borderTopColor: '#4E79A7',
    borderRadius: '50%',
    animation: 'spin 1s linear infinite',
  },
  loadingText: { fontSize: 13, color: '#888' },
  errorOverlay: {
    position: 'absolute',
    inset: 0,
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    background: 'rgba(40,15,15,0.95)',
    zIndex: 10,
    color: '#ff6b6b',
    fontSize: 13,
    padding: 24,
    textAlign: 'center',
  },
  sidebar: {
    width: 320,
    background: '#1a1a2e',
    borderLeft: '1px solid #2a2a4e',
    display: 'flex',
    flexDirection: 'column',
    overflow: 'hidden',
  },
  searchWrap: {
    padding: 10,
    borderBottom: '1px solid #2a2a4e',
    position: 'relative',
  },
  searchInput: {
    background: '#0f0f1a',
    border: '1px solid #3a3a5e',
    color: '#e0e0e0',
    fontSize: 13,
  },
  searchResults: {
    position: 'absolute',
    top: 50,
    left: 10,
    right: 10,
    maxHeight: 220,
    overflowY: 'auto',
    background: '#1a1a2e',
    border: '1px solid #2a2a4e',
    borderRadius: 6,
    zIndex: 20,
    boxShadow: '0 6px 18px rgba(0,0,0,0.5)',
  },
  searchItem: {
    display: 'flex',
    alignItems: 'center',
    gap: 8,
    padding: '6px 10px',
    cursor: 'pointer',
    fontSize: 12,
    borderBottom: '1px solid #20203a',
  },
  searchDot: {
    width: 8,
    height: 8,
    borderRadius: '50%',
    flexShrink: 0,
  },
  searchLabel: { color: '#e0e0e0', flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' },
  searchMeta: { color: '#666', fontSize: 11 },
  infoPanel: {
    padding: 12,
    borderBottom: '1px solid #2a2a4e',
    maxHeight: 360,
    overflowY: 'auto',
  },
  panelTitle: {
    fontSize: 11,
    color: '#888',
    margin: '0 0 8px 0',
    textTransform: 'uppercase',
    letterSpacing: '0.05em',
    fontWeight: 600,
  },
  empty: { fontSize: 12, color: '#555', fontStyle: 'italic' },
  infoContent: { fontSize: 12, color: '#ccc', lineHeight: 1.6 },
  field: { marginBottom: 4 },
  commPill: {
    display: 'inline-block',
    padding: '1px 6px',
    borderRadius: 4,
    fontSize: 11,
    color: '#000',
    fontWeight: 600,
  },
  codeChip: {
    background: '#0f0f1a',
    padding: '1px 5px',
    borderRadius: 3,
    fontSize: 11,
    color: '#aaa',
    fontFamily: 'ui-monospace, "SF Mono", Menlo, monospace',
  },
  subTitle: {
    fontSize: 11,
    color: '#888',
    margin: '10px 0 6px 0',
    textTransform: 'uppercase',
    letterSpacing: '0.05em',
  },
  connList: { display: 'flex', flexDirection: 'column', gap: 3 },
  connItem: {
    display: 'flex',
    alignItems: 'center',
    gap: 6,
    fontSize: 11,
    padding: '3px 0',
    borderBottom: '1px solid #20203a',
  },
  arrow: { color: '#4E79A7', fontWeight: 700, width: 12 },
  connLabel: { color: '#aaa', fontStyle: 'italic' },
  connOther: { color: '#e0e0e0', flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' },
  confTag: {
    fontSize: 9,
    padding: '1px 4px',
    borderRadius: 3,
    fontWeight: 600,
    flexShrink: 0,
  },
  moreConn: { fontSize: 11, color: '#666', padding: '4px 0', textAlign: 'center' },
  godList: { display: 'flex', flexDirection: 'column', gap: 2 },
  godItem: {
    display: 'flex',
    alignItems: 'center',
    gap: 6,
    padding: '3px 4px',
    cursor: 'pointer',
    fontSize: 12,
    borderRadius: 4,
  },
  godRank: { color: '#666', width: 18 },
  godDot: { width: 8, height: 8, borderRadius: '50%', flexShrink: 0 },
  godLabel: {
    flex: 1,
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    whiteSpace: 'nowrap',
    color: '#ccc',
  },
  godDeg: { color: '#666', fontSize: 11 },
  legendWrap: { flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' },
  legendHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '12px 12px 6px 12px',
  },
  legendList: { flex: 1, overflowY: 'auto', padding: '0 12px 12px 12px' },
  legendItem: {
    display: 'flex',
    alignItems: 'center',
    gap: 8,
    padding: '4px 4px',
    cursor: 'pointer',
    borderRadius: 4,
    fontSize: 12,
  },
  checkbox: {
    appearance: 'none',
    width: 14,
    height: 14,
    border: '1.5px solid #3a3a5e',
    borderRadius: 3,
    background: '#0f0f1a',
    cursor: 'pointer',
    position: 'relative',
    flexShrink: 0,
  },
  legendDot: { width: 10, height: 10, borderRadius: '50%', flexShrink: 0 },
  legendLabel: { flex: 1, color: '#ccc', fontSize: 11, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' },
  legendCount: { color: '#666', fontSize: 10 },
  selectAll: {
    display: 'flex',
    alignItems: 'center',
    gap: 6,
    cursor: 'pointer',
    fontSize: 11,
    color: '#888',
  },
}
