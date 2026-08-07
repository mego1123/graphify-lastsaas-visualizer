'use client'

import { useEffect, useState, useCallback } from 'react'

type AuditEntry = {
  timestamp: string
  action: string
  user: string
  resource: string
  details: Record<string, unknown>
  source_ip: string
  session_id: string
}

type AuditSummary = {
  total: number
  by_action: Record<string, number>
  by_user: Record<string, number>
  first_entry?: string
  last_entry?: string
}

type AuditResponse = {
  entries: AuditEntry[]
  summary: AuditSummary
}

export default function AuditView() {
  const [data, setData] = useState<AuditResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [filterUser, setFilterUser] = useState('')
  const [filterAction, setFilterAction] = useState('')

  const load = useCallback(() => {
    const params = new URLSearchParams()
    if (filterUser) params.set('user', filterUser)
    if (filterAction) params.set('action', filterAction)
    params.set('limit', '100')
    fetch(`/api/audit?${params}`)
      .then((r) => r.json())
      .then((d: AuditResponse) => {
        setData(d)
        setLoading(false)
      })
      .catch(() => setLoading(false))
  }, [filterUser, filterAction])

  useEffect(() => {
    load()
    const interval = setInterval(load, 10000)
    return () => clearInterval(interval)
  }, [load])

  if (loading) {
    return (
      <div style={styles.loading}>
        <div style={styles.spinner} />
        <p style={{ color: '#888', fontSize: 13 }}>Loading audit log…</p>
      </div>
    )
  }

  const entries = data?.entries || []
  const summary = data?.summary || { total: 0, by_action: {}, by_user: {} }

  return (
    <div style={styles.container}>
      <div style={styles.leftCol}>
        {/* Summary */}
        <div style={styles.sectionHeader}>
          <h2 style={styles.sectionTitle}>Audit Log Summary</h2>
          <span style={styles.sectionMeta}>
            {summary.total} total entries
            {summary.last_entry && ` · last: ${summary.last_entry}`}
          </span>
        </div>

        <div style={styles.summaryRow}>
          <div style={styles.summaryCard}>
            <span style={styles.summaryLabel}>Total Events</span>
            <span style={styles.summaryValue}>{summary.total}</span>
          </div>
          <div style={styles.summaryCard}>
            <span style={styles.summaryLabel}>Unique Users</span>
            <span style={styles.summaryValue}>{Object.keys(summary.by_user).length}</span>
          </div>
          <div style={styles.summaryCard}>
            <span style={styles.summaryLabel}>Action Types</span>
            <span style={styles.summaryValue}>{Object.keys(summary.by_action).length}</span>
          </div>
        </div>

        {/* By action */}
        <div style={styles.panel}>
          <h3 style={styles.panelTitle}>Events by Action</h3>
          {Object.entries(summary.by_action).sort((a, b) => b[1] - a[1]).map(([action, count]) => (
            <div key={action} style={styles.barRow}>
              <span style={styles.barLabel}>{action}</span>
              <div style={styles.barTrack}>
                <div
                  style={{
                    ...styles.barFill,
                    width: `${(count / Math.max(...Object.values(summary.by_action), 1)) * 100}%`,
                    background: actionColor(action),
                  }}
                />
              </div>
              <span style={styles.barCount}>{count}</span>
            </div>
          ))}
        </div>

        {/* By user */}
        <div style={styles.panel}>
          <h3 style={styles.panelTitle}>Events by User</h3>
          {Object.entries(summary.by_user).sort((a, b) => b[1] - a[1]).map(([user, count]) => (
            <div key={user} style={styles.barRow}>
              <span style={styles.barLabel}>{user}</span>
              <div style={styles.barTrack}>
                <div
                  style={{
                    ...styles.barFill,
                    width: `${(count / Math.max(...Object.values(summary.by_user), 1)) * 100}%`,
                    background: '#4E79A7',
                  }}
                />
              </div>
              <span style={styles.barCount}>{count}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Right: entries list */}
      <div style={styles.rightCol}>
        <div style={styles.sectionHeader}>
          <h2 style={styles.sectionTitle}>Recent Events</h2>
          <div style={styles.filters}>
            <input
              style={styles.filterInput}
              placeholder="Filter by user…"
              value={filterUser}
              onChange={(e) => setFilterUser(e.target.value)}
            />
            <input
              style={styles.filterInput}
              placeholder="Filter by action…"
              value={filterAction}
              onChange={(e) => setFilterAction(e.target.value)}
            />
          </div>
        </div>

        <div style={styles.entriesList}>
          {entries.length === 0 ? (
            <p style={styles.empty}>No audit entries found.</p>
          ) : (
            entries.map((e, i) => (
              <div key={i} style={styles.entryRow}>
                <span style={{ ...styles.actionBadge, background: actionColor(e.action) }}>
                  {e.action}
                </span>
                <div style={styles.entryMain}>
                  <div style={styles.entryTop}>
                    <span style={styles.entryUser}>{e.user}</span>
                    <span style={styles.entryTime}>{formatTime(e.timestamp)}</span>
                  </div>
                  <div style={styles.entryResource}>{e.resource || '—'}</div>
                  {Object.keys(e.details).length > 0 && (
                    <code style={styles.entryDetails}>
                      {JSON.stringify(e.details).slice(0, 120)}
                    </code>
                  )}
                </div>
                <span style={styles.entryIp}>{e.source_ip}</span>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  )
}

function actionColor(action: string): string {
  const colors: Record<string, string> = {
    extract: '#4CAF50',
    query: '#2196F3',
    verify: '#4E79A7',
    verify_breaking: '#F44336',
    prs: '#FF9800',
    digest: '#9C27B0',
    label: '#FF9800',
    update: '#4CAF50',
    delete: '#F44336',
    export: '#00BCD4',
    sso_login: '#8BC34A',
    sso_logout: '#FFC107',
    error: '#F44336',
  }
  return colors[action] || '#888'
}

function formatTime(ts: string): string {
  try {
    const d = new Date(ts)
    return d.toLocaleString()
  } catch {
    return ts
  }
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    display: 'flex', gap: 16, padding: 16, height: '100%',
    overflow: 'hidden', background: '#0f0f1a', color: '#e0e0e0',
  },
  leftCol: { flex: 1, overflowY: 'auto', paddingRight: 8 },
  rightCol: { flex: 2, overflowY: 'auto' },
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
    marginBottom: 12, marginTop: 8,
  },
  sectionTitle: { fontSize: 14, color: '#fff', margin: 0, fontWeight: 600 },
  sectionMeta: { fontSize: 11, color: '#666' },
  summaryRow: { display: 'flex', gap: 8, marginBottom: 16 },
  summaryCard: {
    flex: 1, background: '#1a1a2e', borderRadius: 6, padding: 12,
    border: '1px solid #2a2a4e', display: 'flex', flexDirection: 'column', gap: 4,
  },
  summaryLabel: { fontSize: 10, color: '#888', textTransform: 'uppercase', letterSpacing: '0.05em' },
  summaryValue: { fontSize: 24, fontWeight: 700, color: '#fff' },
  panel: { background: '#1a1a2e', borderRadius: 6, padding: 12, border: '1px solid #2a2a4e', marginBottom: 12 },
  panelTitle: {
    fontSize: 11, color: '#888', textTransform: 'uppercase', letterSpacing: '0.05em',
    margin: '0 0 8px 0', fontWeight: 600,
  },
  barRow: { display: 'flex', alignItems: 'center', gap: 8, padding: '3px 0' },
  barLabel: { width: 120, fontSize: 11, color: '#ccc', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' },
  barTrack: { flex: 1, height: 8, background: '#0f0f1a', borderRadius: 4, overflow: 'hidden' },
  barFill: { height: '100%', borderRadius: 4, transition: 'width 0.3s' },
  barCount: { width: 30, textAlign: 'right', fontSize: 11, color: '#4E79A7', fontWeight: 600 },
  filters: { display: 'flex', gap: 8 },
  filterInput: {
    background: '#0f0f1a', border: '1px solid #3a3a5e', color: '#e0e0e0',
    padding: '4px 8px', borderRadius: 4, fontSize: 11, width: 120,
  },
  entriesList: { display: 'flex', flexDirection: 'column', gap: 2 },
  entryRow: {
    display: 'flex', gap: 10, padding: '8px 10px', borderRadius: 4,
    background: '#1a1a2e', alignItems: 'flex-start',
  },
  actionBadge: {
    padding: '3px 8px', borderRadius: 4, fontSize: 10, fontWeight: 700, color: '#fff',
    whiteSpace: 'nowrap', flexShrink: 0, minWidth: 80, textAlign: 'center',
  },
  entryMain: { flex: 1, minWidth: 0 },
  entryTop: { display: 'flex', justifyContent: 'space-between', marginBottom: 2 },
  entryUser: { fontSize: 12, color: '#e0e0e0', fontWeight: 600 },
  entryTime: { fontSize: 10, color: '#666' },
  entryResource: { fontSize: 11, color: '#aaa', fontFamily: 'ui-monospace, monospace', marginBottom: 2 },
  entryDetails: {
    fontSize: 10, color: '#666', fontFamily: 'ui-monospace, monospace',
    display: 'block', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
  },
  entryIp: { fontSize: 10, color: '#555', flexShrink: 0 },
  empty: { fontSize: 12, color: '#555', fontStyle: 'italic', padding: 16 },
}
