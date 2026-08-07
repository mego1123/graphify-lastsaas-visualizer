'use client'

import { useEffect, useState } from 'react'

type VerifyResult = {
  function: string
  file: string
  status: 'EQUIVALE' | 'BREAKING' | 'INCONCLUSIVE' | 'ERROR'
  iterations?: number
  breaking_input?: string
  old_output?: string
  new_output?: string
  error?: string
  language?: string
  affected_callers?: string[]
}

type VerifyStatus = {
  last_run: string | null
  running: boolean
  results: VerifyResult[]
  summary: {
    equivalent: number
    breaking: number
    inconclusive: number
  }
}

export default function VerifyView() {
  const [status, setStatus] = useState<VerifyStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selected, setSelected] = useState<VerifyResult | null>(null)

  useEffect(() => {
    let cancelled = false
    const load = () => {
      fetch('/verify-status.json?t=' + Date.now())
        .then((r) => {
          if (!r.ok) throw new Error(`HTTP ${r.status}`)
          return r.json() as Promise<VerifyStatus>
        })
        .then((d) => {
          if (cancelled) return
          setStatus(d)
          setLoading(false)
        })
        .catch((e) => {
          if (cancelled) return
          setError(String(e))
          setLoading(false)
        })
    }
    load()
    // Poll every 5s for live updates (when watcher is running)
    const interval = setInterval(load, 5000)
    return () => {
      cancelled = true
      clearInterval(interval)
    }
  }, [])

  if (loading) {
    return (
      <div style={styles.loading}>
        <div style={styles.spinner} />
        <p style={{ color: '#888', fontSize: 13 }}>Loading verification status…</p>
      </div>
    )
  }

  if (error || !status) {
    return (
      <div style={styles.container}>
        <div style={styles.errorPanel}>
          <h3 style={styles.panelTitle}>Verification Status</h3>
          <p style={styles.empty}>
            No verification data found. Run{' '}
            <code style={styles.code}>python scripts/graphify_verify.py .</code>{' '}
            or start the watcher with{' '}
            <code style={styles.code}>python scripts/graphify_verify_watch.py .</code>
          </p>
        </div>
      </div>
    )
  }

  const total = status.summary.equivalent + status.summary.breaking + status.summary.inconclusive

  return (
    <div style={styles.container}>
      <div style={styles.leftCol}>
        {/* Status header */}
        <div style={styles.statusHeader}>
          <div style={styles.statusRow}>
            <span style={styles.statusIcon(status.running)}>
              {status.running ? '⟳' : '✓'}
            </span>
            <h2 style={styles.sectionTitle}>
              {status.running ? 'Verifying…' : 'Verification Complete'}
            </h2>
            <span style={styles.timestamp}>
              {status.last_run ? `Last run: ${status.last_run}` : 'Never run'}
            </span>
          </div>
          <div style={styles.summaryBar}>
            <div style={{ ...styles.summaryCell, background: '#1f3a1f', color: '#7CFC7C' }}>
              ✓ {status.summary.equivalent} EQUIVALENT
            </div>
            <div style={{ ...styles.summaryCell, background: '#3a1f1f', color: '#FF6B6B' }}>
              ✗ {status.summary.breaking} BREAKING
            </div>
            <div style={{ ...styles.summaryCell, background: '#3a3a1f', color: '#FFB347' }}>
              ? {status.summary.inconclusive} OTHER
            </div>
            <div style={{ ...styles.summaryCell, background: '#2a2a4e', color: '#aaa' }}>
              {total} TOTAL
            </div>
          </div>
        </div>

        {/* Results list */}
        <div style={styles.sectionHeader}>
          <h2 style={styles.sectionTitle}>Verified Functions</h2>
        </div>
        <div style={styles.resultsList}>
          {status.results.length === 0 ? (
            <p style={styles.empty}>No functions verified yet. Make a change to a Go or TS file.</p>
          ) : (
            status.results.map((r, i) => (
              <div
                key={i}
                style={{
                  ...styles.resultRow,
                  background: selected?.function === r.function ? '#2a2a4e' : '#1a1a2e',
                  borderLeft: `3px solid ${statusColor(r.status)}`,
                }}
                onClick={() => setSelected(r)}
              >
                <span style={{ ...styles.statusBadge, background: statusColor(r.status) }}>
                  {statusIcon(r.status)}
                </span>
                <span style={styles.funcName}>{r.function}</span>
                <span style={styles.langBadge}>{r.language || 'go'}</span>
                <span style={styles.funcFile}>{r.file}</span>
                <span style={styles.funcIters}>
                  {r.iterations ? `${r.iterations} inputs` : ''}
                </span>
              </div>
            ))
          )}
        </div>

        {/* How to run */}
        <div style={styles.sectionHeader}>
          <h2 style={styles.sectionTitle}>How to Run</h2>
        </div>
        <div style={styles.helpPanel}>
          <div style={styles.helpSection}>
            <h4 style={styles.helpTitle}>One-time verification</h4>
            <pre style={styles.codeBlock}>{`# Go functions
python scripts/graphify_verify.py .

# TypeScript functions
python scripts/graphify_verify_ts.py .

# Specific function only
python scripts/graphify_verify.py . --function ParseEncryptionKey

# More iterations
python scripts/graphify_verify.py . --iterations 1000`}</pre>
          </div>
          <div style={styles.helpSection}>
            <h4 style={styles.helpTitle}>Auto-verify on file save (watcher)</h4>
            <pre style={styles.codeBlock}>{`# Start the watcher in background
python scripts/graphify_verify_watch.py .

# Make changes to any .go or .ts/.tsx file
# Results appear here automatically (refreshes every 5s)`}</pre>
          </div>
        </div>
      </div>

      {/* Right column: details */}
      <div style={styles.rightCol}>
        <div style={styles.panel}>
          <h3 style={styles.panelTitle}>Function Details</h3>
          {!selected ? (
            <p style={styles.empty}>Click a function to see details.</p>
          ) : (
            <div style={styles.detailContent}>
              <div style={styles.detailHeader}>
                <span style={{ ...styles.detailBadge, background: statusColor(selected.status) }}>
                  {statusIcon(selected.status)} {selected.status}
                </span>
                <h4 style={styles.detailName}>{selected.function}</h4>
              </div>
              <div style={styles.detailMeta}>
                <span>📁 {selected.file}</span>
                {selected.language && <span>· {selected.language}</span>}
                {selected.iterations && <span>· {selected.iterations} inputs tested</span>}
              </div>

              {selected.status === 'BREAKING' && (
                <>
                  <h5 style={styles.subTitle}>🚨 Breaking Input</h5>
                  <pre style={styles.breakingInput}>{selected.breaking_input}</pre>
                  {selected.old_output && selected.new_output && (
                    <div style={styles.outputComparison}>
                      <div style={styles.outputBox}>
                        <span style={styles.outputLabel}>Old output:</span>
                        <code style={styles.outputCode}>{selected.old_output}</code>
                      </div>
                      <div style={styles.outputBox}>
                        <span style={styles.outputLabel}>New output:</span>
                        <code style={styles.outputCode}>{selected.new_output}</code>
                      </div>
                    </div>
                  )}
                </>
              )}

              {selected.status === 'EQUIVALE' && (
                <p style={styles.successMsg}>
                  ✓ Proven equivalent across {selected.iterations} test inputs.
                  The refactor is behavior-preserving.
                </p>
              )}

              {selected.affected_callers && selected.affected_callers.length > 0 && (
                <>
                  <h5 style={styles.subTitle}>Affected Callers (from graph.json)</h5>
                  <div style={styles.callerList}>
                    {selected.affected_callers.map((c, i) => (
                      <span key={i} style={styles.callerChip}>{c}</span>
                    ))}
                  </div>
                </>
              )}

              {selected.error && (
                <>
                  <h5 style={styles.subTitle}>Error</h5>
                  <pre style={styles.errorOutput}>{selected.error}</pre>
                </>
              )}
            </div>
          )}
        </div>

        <div style={styles.panel}>
          <h3 style={styles.panelTitle}>How It Works</h3>
          <div style={styles.methodContent}>
            <p style={styles.methodP}>
              <b>1. Detect changes.</b> Compares your working tree against{' '}
              <code style={styles.inlineCode}>git HEAD</code> using tree-sitter AST parsing
              to identify which functions changed at the structural level.
            </p>
            <p style={styles.methodP}>
              <b>2. Generate differential tests.</b> For each changed function, the old
              version (from git) is renamed to <code style={styles.inlineCode}>Old_&lt;name&gt;</code>{' '}
              and compiled alongside the new version. A test harness calls both with the
              same inputs.
            </p>
            <p style={styles.methodP}>
              <b>3. Three layers of testing:</b>
            </p>
            <ul style={styles.methodList}>
              <li><b>Random inputs</b> — Go's <code style={styles.inlineCode}>testing/quick</code> or TS's <code style={styles.inlineCode}>fast-check</code> generates N random inputs matching the param types</li>
              <li><b>Curated boundary values</b> — empty strings, boundary integers, valid hex strings of exact length</li>
              <li><b>LLM-generated cases</b> — for complex param types (structs, interfaces), the LLM generates realistic test inputs based on real call sites from the graph</li>
            </ul>
            <p style={styles.methodP}>
              <b>4. Report.</b> If all outputs match → <b>PROVEN EQUIVALENT</b>. If any
              diverge → <b>BREAKING INPUT FOUND</b> with the exact input and both outputs.
            </p>
            <p style={styles.methodP}>
              <b>Methods supported.</b> Go methods (with receivers) are verified by
              constructing a zero-value receiver (e.g. <code style={styles.inlineCode}>&JWTService{'{}'}</code>).
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

function statusColor(status: string): string {
  switch (status) {
    case 'EQUIVALE': return '#4CAF50'
    case 'BREAKING': return '#F44336'
    case 'INCONCLUSIVE': return '#FF9800'
    case 'ERROR': return '#9C27B0'
    default: return '#888'
  }
}

function statusIcon(status: string): string {
  switch (status) {
    case 'EQUIVALE': return '✓'
    case 'BREAKING': return '✗'
    case 'INCONCLUSIVE': return '?'
    case 'ERROR': return '!'
    default: return '·'
  }
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
  rightCol: { flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 12 },
  loading: {
    display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
    height: '100%', gap: 12, background: '#0f0f1a',
  },
  spinner: {
    width: 32, height: 32, border: '3px solid #2a2a4e', borderTopColor: '#4E79A7',
    borderRadius: '50%', animation: 'spin 1s linear infinite',
  },
  errorPanel: { background: '#1a1a2e', borderRadius: 6, padding: 16, border: '1px solid #2a2a4e' },
  statusHeader: { marginBottom: 16 },
  statusRow: { display: 'flex', alignItems: 'center', gap: 12, marginBottom: 10 },
  statusIcon: (running: boolean) => ({
    fontSize: 24,
    color: running ? '#FF9800' : '#4CAF50',
    animation: running ? 'spin 2s linear infinite' : 'none',
  }),
  sectionTitle: { fontSize: 14, color: '#fff', margin: 0, fontWeight: 600 },
  timestamp: { fontSize: 11, color: '#666', marginLeft: 'auto' },
  summaryBar: { display: 'flex', gap: 4 },
  summaryCell: {
    flex: 1, padding: '8px 12px', borderRadius: 4, fontSize: 12, fontWeight: 600,
    textAlign: 'center',
  },
  sectionHeader: { marginBottom: 10, marginTop: 16 },
  resultsList: { display: 'flex', flexDirection: 'column', gap: 2 },
  resultRow: {
    display: 'grid', gridTemplateColumns: '28px 1fr 40px 2fr 80px', gap: 8,
    padding: '8px 10px', borderRadius: 4, cursor: 'pointer', fontSize: 12, alignItems: 'center',
    transition: 'background 0.15s',
  },
  statusBadge: {
    width: 20, height: 20, borderRadius: '50%', display: 'flex', alignItems: 'center',
    justifyContent: 'center', fontWeight: 700, fontSize: 11, color: '#fff',
  },
  funcName: { color: '#e0e0e0', fontWeight: 600, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' },
  langBadge: {
    fontSize: 9, padding: '2px 6px', borderRadius: 3, background: '#2a2a4e', color: '#aaa',
    textTransform: 'uppercase', textAlign: 'center',
  },
  funcFile: {
    color: '#666', fontSize: 10, fontFamily: 'ui-monospace, monospace',
    overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
  },
  funcIters: { color: '#4E79A7', fontSize: 10, textAlign: 'right' },
  empty: { fontSize: 12, color: '#555', fontStyle: 'italic', padding: 16 },
  helpPanel: { background: '#1a1a2e', borderRadius: 6, padding: 12, border: '1px solid #2a2a4e' },
  helpSection: { marginBottom: 16 },
  helpTitle: { fontSize: 12, color: '#4E79A7', margin: '0 0 6px 0', fontWeight: 600 },
  codeBlock: {
    background: '#0f0f1a', padding: 10, borderRadius: 4, fontSize: 11,
    fontFamily: 'ui-monospace, "SF Mono", Menlo, monospace', color: '#aaa',
    overflowX: 'auto', whiteSpace: 'pre',
  },
  panel: { background: '#1a1a2e', borderRadius: 6, padding: 12, border: '1px solid #2a2a4e' },
  panelTitle: {
    fontSize: 11, color: '#888', textTransform: 'uppercase', letterSpacing: '0.05em',
    margin: '0 0 8px 0', fontWeight: 600,
  },
  detailContent: { fontSize: 12, color: '#ccc' },
  detailHeader: { display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 },
  detailBadge: {
    padding: '3px 8px', borderRadius: 4, fontSize: 10, fontWeight: 700, color: '#fff',
  },
  detailName: { fontSize: 14, color: '#fff', margin: 0, fontWeight: 600 },
  detailMeta: { display: 'flex', gap: 6, fontSize: 11, color: '#888', marginBottom: 12 },
  subTitle: {
    fontSize: 10, color: '#888', textTransform: 'uppercase', letterSpacing: '0.05em',
    margin: '10px 0 4px 0',
  },
  breakingInput: {
    background: '#3a1f1f', padding: 10, borderRadius: 4, fontSize: 11,
    fontFamily: 'ui-monospace, monospace', color: '#FF6B6B', whiteSpace: 'pre-wrap',
    wordBreak: 'break-all',
  },
  outputComparison: { display: 'flex', flexDirection: 'column', gap: 6, marginTop: 8 },
  outputBox: {
    background: '#0f0f1a', padding: 8, borderRadius: 4, display: 'flex',
    flexDirection: 'column', gap: 4,
  },
  outputLabel: { fontSize: 10, color: '#666', textTransform: 'uppercase' },
  outputCode: {
    fontSize: 11, fontFamily: 'ui-monospace, monospace', color: '#ccc',
    whiteSpace: 'pre-wrap', wordBreak: 'break-all',
  },
  successMsg: { color: '#7CFC7C', fontSize: 12, lineHeight: 1.6 },
  callerList: { display: 'flex', flexWrap: 'wrap', gap: 4, marginTop: 4 },
  callerChip: {
    fontSize: 10, padding: '3px 8px', borderRadius: 3, background: '#2a2a4e', color: '#aaa',
    fontFamily: 'ui-monospace, monospace',
  },
  errorOutput: {
    background: '#3a1f3a', padding: 10, borderRadius: 4, fontSize: 10,
    fontFamily: 'ui-monospace, monospace', color: '#FF6B6B', whiteSpace: 'pre-wrap',
    wordBreak: 'break-all', maxHeight: 200, overflowY: 'auto',
  },
  methodContent: { fontSize: 11, color: '#aaa', lineHeight: 1.7 },
  methodP: { margin: '0 0 8px 0' },
  methodList: { margin: '4px 0 8px 20px', padding: 0 },
  inlineCode: {
    background: '#0f0f1a', padding: '1px 4px', borderRadius: 2, fontSize: 10,
    fontFamily: 'ui-monospace, monospace', color: '#4E79A7',
  },
}
