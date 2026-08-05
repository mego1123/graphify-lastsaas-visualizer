'use client'

import { useState, useCallback } from 'react'

type AnalysisResults = {
  ok: boolean
  sessionId: string
  filename: string
  analysesRun: number
  results: Record<string, any>
}

export default function UploadView() {
  const [uploading, setUploading] = useState(false)
  const [results, setResults] = useState<AnalysisResults | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [dragOver, setDragOver] = useState(false)
  const [repoUrl, setRepoUrl] = useState('')
  const [mode, setMode] = useState<'zip' | 'repo'>('zip')

  const handleUpload = useCallback(async (file: File) => {
    if (!file.name.endsWith('.zip')) {
      setError('Only .zip files are accepted')
      return
    }

    setUploading(true)
    setError(null)

    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await fetch('/api/upload', { method: 'POST', body: formData })
      const data = await response.json()
      if (!response.ok) setError(data.error || 'Upload failed')
      else setResults(data)
    } catch (e) {
      setError(String(e))
    } finally {
      setUploading(false)
    }
  }, [])

  const handleRepoClone = useCallback(async () => {
    if (!repoUrl.includes('github.com')) {
      setError('Please enter a valid GitHub URL')
      return
    }

    setUploading(true)
    setError(null)

    try {
      const response = await fetch('/api/upload', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ repoUrl }),
      })
      const data = await response.json()
      if (!response.ok) setError(data.error || 'Clone failed')
      else setResults(data)
    } catch (e) {
      setError(String(e))
    } finally {
      setUploading(false)
    }
  }, [repoUrl])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(false)
    const file = e.dataTransfer.files[0]
    if (file) handleUpload(file)
  }, [handleUpload])

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h2 style={styles.title}>Upload Your Template</h2>
        <p style={styles.subtitle}>
          Upload a .zip of your frontend code to run all 10 graphify checks.
          The file is extracted and analyzed on the server — results appear below.
        </p>
      </div>

      {/* Mode toggle */}
      <div style={styles.modeToggle}>
        <button
          style={{ ...styles.modeBtn, ...(mode === 'zip' ? styles.modeBtnActive : {}) }}
          onClick={() => setMode('zip')}
        >
          📦 Upload ZIP
        </button>
        <button
          style={{ ...styles.modeBtn, ...(mode === 'repo' ? styles.modeBtnActive : {}) }}
          onClick={() => setMode('repo')}
        >
          🔗 GitHub URL
        </button>
      </div>

      {/* Upload zone or repo URL input */}
      {mode === 'zip' ? (
        <div
          style={{ ...styles.dropZone, ...(dragOver ? styles.dropZoneActive : {}) }}
          onDrop={handleDrop}
          onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
          onDragLeave={() => setDragOver(false)}
          onClick={() => document.getElementById('file-input')?.click()}
        >
          {uploading ? (
            <div style={styles.uploading}>
              <div style={styles.spinner} />
              <p style={styles.uploadingText}>Analyzing your template…</p>
              <p style={styles.uploadingHint}>Running 10 frontend checks (may take 30-60 seconds)</p>
            </div>
          ) : (
            <div style={styles.dropContent}>
              <div style={styles.dropIcon}>📦</div>
              <p style={styles.dropText}>{dragOver ? 'Drop your .zip here' : 'Drag & drop your .zip file here'}</p>
              <p style={styles.dropHint}>or click to browse</p>
              <p style={styles.dropNote}>Accepts: .zip containing your frontend source (src/ or frontend/src/)</p>
            </div>
          )}
          <input id="file-input" type="file" accept=".zip" style={{ display: 'none' }}
            onChange={(e) => { const f = e.target.files?.[0]; if (f) handleUpload(f) }}
          />
        </div>
      ) : (
        <div style={styles.repoZone}>
          {uploading ? (
            <div style={styles.uploading}>
              <div style={styles.spinner} />
              <p style={styles.uploadingText}>Cloning & analyzing…</p>
              <p style={styles.uploadingHint}>Cloning repo and running 10 frontend checks</p>
            </div>
          ) : (
            <>
              <div style={styles.repoIcon}>🔗</div>
              <p style={styles.repoText}>Enter a GitHub repository URL</p>
              <div style={styles.repoInputRow}>
                <input
                  style={styles.repoInput}
                  placeholder="https://github.com/user/repo"
                  value={repoUrl}
                  onChange={(e) => setRepoUrl(e.target.value)}
                  onKeyDown={(e) => { if (e.key === 'Enter') handleRepoClone() }}
                />
                <button style={styles.repoBtn} onClick={handleRepoClone}>
                  Analyze →
                </button>
              </div>
              <p style={styles.repoHint}>The repo will be cloned (shallow) and analyzed with all 10 checks</p>
            </>
          )}
        </div>
      )}

      {/* Error */}
      {error && (
        <div style={styles.errorBox}>
          <span style={styles.errorIcon}>❌</span>
          <span>{error}</span>
        </div>
      )}

      {/* Results */}
      {results && (
        <div style={styles.resultsSection}>
          <div style={styles.resultsHeader}>
            <h3 style={styles.resultsTitle}>Analysis Results</h3>
            <span style={styles.sessionId}>Session: {results.sessionId}</span>
          </div>

          <div style={styles.resultsGrid}>
            <ResultCard
              title="Dead Components"
              icon="🗑️"
              value={results.results['dead-components']?.length ?? 0}
              unit="found"
              color={results.results['dead-components']?.length > 0 ? '#F44336' : '#4CAF50'}
            />
            <ResultCard
              title="Route Tree"
              icon="🌳"
              value={countRoutes(results.results['route-tree'] ?? [])}
              unit="routes"
              color="#4E79A7"
            />
            <ResultCard
              title="Prop Drilling"
              icon="🔗"
              value={results.results['prop-drilling']?.length ?? 0}
              unit="found"
              color={results.results['prop-drilling']?.length > 0 ? '#FF9800' : '#4CAF50'}
            />
            <ResultCard
              title="Hook Issues"
              icon="🪝"
              value={results.results['hook-deps']?.length ?? 0}
              unit="issues"
              color={(results.results['hook-deps']?.length ?? 0) > 10 ? '#F44336' : '#FF9800'}
            />
            <ResultCard
              title="Contexts"
              icon="🌐"
              value={results.results['context-usage']?.length ?? 0}
              unit="Contexts"
              color="#4E79A7"
            />
            <ResultCard
              title="Complexity"
              icon="📊"
              value={results.results['complexity']?.length ?? 0}
              unit="components"
              color="#4E79A7"
            />
            <ResultCard
              title="i18n Coverage"
              icon="🌍"
              value={results.results['i18n']?.coverage_pct?.toFixed(0) ?? '?'}
              unit="%"
              color={(results.results['i18n']?.coverage_pct ?? 0) > 50 ? '#4CAF50' : '#F44336'}
            />
            <ResultCard
              title="Accessibility"
              icon="♿"
              value={results.results['a11y']?.length ?? 0}
              unit="issues"
              color={(results.results['a11y']?.length ?? 0) > 20 ? '#F44336' : '#FF9800'}
            />
            <ResultCard
              title="Test Coverage"
              icon="🧪"
              value={results.results['test-coverage']?.coverage_pct?.toFixed(0) ?? '?'}
              unit="%"
              color={(results.results['test-coverage']?.coverage_pct ?? 0) > 80 ? '#4CAF50' : '#F44336'}
            />
          </div>

          {/* Details */}
          <div style={styles.detailsSection}>
            <h4 style={styles.detailsTitle}>Detailed Findings</h4>

            {results.results['dead-components']?.length > 0 && (
              <DetailBlock title="🗑️ Dead Components" items={results.results['dead-components'].map((c: any) => `${c.name} (${c.file})`)} />
            )}

            {results.results['hook-deps']?.length > 0 && (
              <DetailBlock
                title="🪝 Hook Issues (top 5)"
                items={results.results['hook-deps'].slice(0, 5).map((h: any) => `${h.hook_type} — ${h.issue_type} in ${h.file}:${h.line}`)}
              />
            )}

            {results.results['context-usage']?.length > 0 && (
              <DetailBlock
                title="🌐 Context Usage"
                items={results.results['context-usage'].map((c: any) => `${c.name}: ${c.consumer_count} consumers (${c.risk_level})`)}
              />
            )}

            {results.results['a11y']?.length > 0 && (
              <DetailBlock
                title="♿ Accessibility Issues (top 5)"
                items={results.results['a11y'].slice(0, 5).map((a: any) => `${a.rule}: ${a.message} (${a.file}:${a.line})`)}
              />
            )}

            {results.results['test-coverage']?.untested?.length > 0 && (
              <DetailBlock
                title="🧪 Untested Components (top 10)"
                items={results.results['test-coverage'].untested.slice(0, 10).map((c: any) => `${c.name} (${c.file})`)}
              />
            )}
          </div>
        </div>
      )}

      {/* How it works */}
      {!results && !uploading && (
        <div style={styles.howItWorks}>
          <h3 style={styles.howTitle}>How It Works</h3>
          <div style={styles.steps}>
            <div style={styles.step}>
              <span style={styles.stepNum}>1</span>
              <div>
                <strong>Upload</strong> — Drag & drop a .zip of your frontend source code
              </div>
            </div>
            <div style={styles.step}>
              <span style={styles.stepNum}>2</span>
              <div>
                <strong>Extract</strong> — The server unzips your code to a temp directory
              </div>
            </div>
            <div style={styles.step}>
              <span style={styles.stepNum}>3</span>
              <div>
                <strong>Analyze</strong> — All 10 graphify frontend checks run automatically:
                <div style={styles.checkList}>
                  dead-components, route-tree, bundle-impact, prop-drilling,
                  hook-deps, context-usage, complexity, i18n, a11y, test-coverage
                </div>
              </div>
            </div>
            <div style={styles.step}>
              <span style={styles.stepNum}>4</span>
              <div>
                <strong>Review</strong> — Results appear above with actionable findings
              </div>
            </div>
          </div>
          <div style={styles.privacyNote}>
            🔒 Your code is processed locally and deleted after analysis. Nothing is stored permanently.
          </div>
        </div>
      )}
    </div>
  )
}

function ResultCard({ title, icon, value, unit, color }: { title: string; icon: string; value: number | string; unit: string; color: string }) {
  return (
    <div style={styles.resultCard}>
      <span style={styles.resultIcon}>{icon}</span>
      <span style={{ ...styles.resultValue, color }}>{value}</span>
      <span style={styles.resultUnit}>{unit}</span>
      <span style={styles.resultTitle}>{title}</span>
    </div>
  )
}

function DetailBlock({ title, items }: { title: string; items: string[] }) {
  if (!items || items.length === 0) return null
  return (
    <div style={styles.detailBlock}>
      <h5 style={styles.detailBlockTitle}>{title}</h5>
      {items.map((item, i) => (
        <div key={i} style={styles.detailItem}>
          <span style={styles.detailBullet}>•</span>
          <code style={styles.detailCode}>{item}</code>
        </div>
      ))}
    </div>
  )
}

function countRoutes(routes: any[]): number {
  let count = 0
  for (const r of routes) {
    count += 1
    if (r.children) count += countRoutes(r.children)
  }
  return count
}

const styles: Record<string, React.CSSProperties> = {
  container: { padding: 24, height: '100%', overflowY: 'auto', background: '#0f0f1a', color: '#e0e0e0' },
  header: { marginBottom: 20 },
  title: { fontSize: 20, color: '#fff', margin: '0 0 8px 0' },
  subtitle: { fontSize: 13, color: '#888', lineHeight: 1.6 },
  dropZone: {
    border: '2px dashed #3a3a5e', borderRadius: 12, padding: 48, textAlign: 'center',
    cursor: 'pointer', transition: 'all 0.2s', background: '#1a1a2e', marginBottom: 20,
  },
  dropZoneActive: { borderColor: '#4E79A7', background: '#1a2a3e' },
  dropContent: { display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8 },
  dropIcon: { fontSize: 48 },
  dropText: { fontSize: 16, color: '#e0e0e0', fontWeight: 600 },
  dropHint: { fontSize: 12, color: '#666' },
  dropNote: { fontSize: 11, color: '#555', marginTop: 8 },
  uploading: { display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8 },
  spinner: { width: 32, height: 32, border: '3px solid #2a2a4e', borderTopColor: '#4E79A7', borderRadius: '50%', animation: 'spin 1s linear infinite' },
  uploadingText: { fontSize: 14, color: '#e0e0e0', fontWeight: 600 },
  uploadingHint: { fontSize: 12, color: '#666' },
  errorBox: { background: '#3a1f1f', borderRadius: 6, padding: 12, display: 'flex', gap: 8, alignItems: 'center', color: '#FF6B6B', marginBottom: 16 },
  errorIcon: { fontSize: 16 },
  resultsSection: { marginTop: 20 },
  resultsHeader: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 },
  resultsTitle: { fontSize: 16, color: '#fff', margin: 0 },
  sessionId: { fontSize: 11, color: '#555', fontFamily: 'ui-monospace, monospace' },
  resultsGrid: { display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12, marginBottom: 20 },
  resultCard: { background: '#1a1a2e', borderRadius: 8, padding: 16, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4, border: '1px solid #2a2a4e' },
  resultIcon: { fontSize: 20 },
  resultValue: { fontSize: 28, fontWeight: 700 },
  resultUnit: { fontSize: 11, color: '#888' },
  resultTitle: { fontSize: 11, color: '#aaa', fontWeight: 600 },
  detailsSection: { background: '#1a1a2e', borderRadius: 8, padding: 16, border: '1px solid #2a2a4e' },
  detailsTitle: { fontSize: 14, color: '#fff', margin: '0 0 12px 0' },
  detailBlock: { marginBottom: 16 },
  detailBlockTitle: { fontSize: 12, color: '#4E79A7', margin: '0 0 6px 0', fontWeight: 600 },
  detailItem: { display: 'flex', gap: 6, padding: '3px 0', fontSize: 11 },
  detailBullet: { color: '#666' },
  detailCode: { color: '#aaa', fontFamily: 'ui-monospace, monospace', fontSize: 10, wordBreak: 'break-all' },
  howItWorks: { marginTop: 24, background: '#1a1a2e', borderRadius: 8, padding: 20, border: '1px solid #2a2a4e' },
  howTitle: { fontSize: 14, color: '#fff', margin: '0 0 16px 0' },
  steps: { display: 'flex', flexDirection: 'column', gap: 16 },
  step: { display: 'flex', gap: 12, alignItems: 'flex-start', fontSize: 12, color: '#aaa', lineHeight: 1.6 },
  stepNum: { width: 24, height: 24, borderRadius: '50%', background: '#4E79A7', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 12, fontWeight: 700, flexShrink: 0 },
  checkList: { fontSize: 10, color: '#666', marginTop: 4, fontFamily: 'ui-monospace, monospace' },
  privacyNote: { marginTop: 16, fontSize: 11, color: '#555', textAlign: 'center', padding: 8, background: '#0f0f1a', borderRadius: 4 },
  modeToggle: { display: 'flex', gap: 4, marginBottom: 16, background: '#1a1a2e', borderRadius: 6, padding: 3, border: '1px solid #2a2a4e' },
  modeBtn: { background: 'transparent', color: '#888', border: 'none', padding: '8px 16px', fontSize: 12, fontWeight: 600, cursor: 'pointer', borderRadius: 4 },
  modeBtnActive: { background: '#4E79A7', color: '#fff' },
  repoZone: { border: '2px dashed #3a3a5e', borderRadius: 12, padding: 48, textAlign: 'center', background: '#1a1a2e', marginBottom: 20, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8 },
  repoIcon: { fontSize: 48 },
  repoText: { fontSize: 16, color: '#e0e0e0', fontWeight: 600 },
  repoInputRow: { display: 'flex', gap: 8, marginTop: 12, width: '100%', maxWidth: 500 },
  repoInput: { flex: 1, background: '#0f0f1a', border: '1px solid #3a3a5e', color: '#e0e0e0', padding: '10px 14px', borderRadius: 6, fontSize: 13, outline: 'none' },
  repoBtn: { background: '#4E79A7', color: '#fff', border: 'none', padding: '10px 20px', borderRadius: 6, fontSize: 13, fontWeight: 600, cursor: 'pointer', whiteSpace: 'nowrap' },
  repoHint: { fontSize: 11, color: '#555', marginTop: 4 },
}
