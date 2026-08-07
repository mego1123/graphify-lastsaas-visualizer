'use client'

import { useState, useCallback } from 'react'
import GraphView from './GraphView'
import ArchitectureView from './ArchitectureView'
import VerifyView from './VerifyView'
import AuditView from './AuditView'
import FrontendView from './FrontendView'
import UploadView from './UploadView'

type Tab = 'graph' | 'architecture' | 'verify' | 'audit' | 'frontend' | 'upload'

export default function Home() {
  const [tab, setTab] = useState<Tab>('graph')
  // When user clicks a community in the Architecture tab, switch to Graph tab
  // and focus that community.
  const [focusCommunityId, setFocusCommunityId] = useState<number | null>(null)

  const handleSelectCommunity = useCallback((cid: number) => {
    setFocusCommunityId(cid)
    setTab('graph')
  }, [])

  return (
    <div style={styles.page}>
      <header style={styles.header}>
        <div style={styles.headerLeft}>
          <h1 style={styles.title}>graphify · lastsaas</h1>
          <span style={styles.subtitle}>
            2,507 nodes · 6,423 edges · 157 communities · 20 subsystems
          </span>
        </div>
        <nav style={styles.tabs}>
          <button
            style={{
              ...styles.tab,
              ...(tab === 'graph' ? styles.tabActive : {}),
            }}
            onClick={() => setTab('graph')}
          >
            Graph
          </button>
          <button
            style={{
              ...styles.tab,
              ...(tab === 'architecture' ? styles.tabActive : {}),
            }}
            onClick={() => setTab('architecture')}
          >
            Architecture
          </button>
          <button
            style={{
              ...styles.tab,
              ...(tab === 'verify' ? styles.tabActive : {}),
            }}
            onClick={() => setTab('verify')}
          >
            Verify
          </button>
          <button
            style={{
              ...styles.tab,
              ...(tab === 'audit' ? styles.tabActive : {}),
            }}
            onClick={() => setTab('audit')}
          >
            Audit
          </button>
          <button
            style={{
              ...styles.tab,
              ...(tab === 'frontend' ? styles.tabActive : {}),
            }}
            onClick={() => setTab('frontend')}
          >
            Frontend
          </button>
          <button
            style={{
              ...styles.tab,
              ...(tab === 'upload' ? styles.tabActive : {}),
            }}
            onClick={() => setTab('upload')}
          >
            Upload
          </button>
        </nav>
        <div style={styles.headerRight}>
          <a
            href="/DIGEST.md"
            target="_blank"
            rel="noreferrer"
            style={styles.linkBtn}
          >
            Digest →
          </a>
          <a
            href="/PR_REPORT.md"
            target="_blank"
            rel="noreferrer"
            style={styles.linkBtn}
          >
            PR Report →
          </a>
          <a
            href="/ARCHITECTURE_MAP.md"
            target="_blank"
            rel="noreferrer"
            style={styles.linkBtn}
          >
            Architecture Map →
          </a>
          <a
            href="/GRAPH_REPORT.md"
            target="_blank"
            rel="noreferrer"
            style={styles.linkBtn}
          >
            Graph Report →
          </a>
        </div>
      </header>

      <main style={styles.main}>
        {/* Keep both views mounted; hide the inactive one so state/network persists.
            This avoids re-initializing vis-network on every tab switch. */}
        <div style={{ display: tab === 'graph' ? 'flex' : 'none', height: '100%' }}>
          <GraphView focusCommunityId={focusCommunityId} />
        </div>
        <div style={{ display: tab === 'architecture' ? 'block' : 'none', height: '100%' }}>
          <ArchitectureView onSelectNode={handleSelectCommunity} />
        </div>
        <div style={{ display: tab === 'verify' ? 'block' : 'none', height: '100%' }}>
          <VerifyView />
        </div>
        <div style={{ display: tab === 'audit' ? 'block' : 'none', height: '100%' }}>
          <AuditView />
        </div>
        <div style={{ display: tab === 'frontend' ? 'block' : 'none', height: '100%' }}>
          <FrontendView />
        </div>
        <div style={{ display: tab === 'upload' ? 'block' : 'none', height: '100%' }}>
          <UploadView />
        </div>
      </main>
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
    gap: 16,
  },
  headerLeft: { display: 'flex', flexDirection: 'column', gap: 2, flex: 1 },
  title: { fontSize: 16, fontWeight: 600, color: '#fff', margin: 0 },
  subtitle: { fontSize: 12, color: '#888' },
  tabs: {
    display: 'flex',
    gap: 4,
    background: '#0f0f1a',
    padding: 3,
    borderRadius: 6,
    border: '1px solid #2a2a4e',
  },
  tab: {
    background: 'transparent',
    color: '#888',
    border: 'none',
    padding: '6px 14px',
    fontSize: 12,
    fontWeight: 600,
    cursor: 'pointer',
    borderRadius: 4,
    transition: 'all 0.15s',
  },
  tabActive: {
    background: '#4E79A7',
    color: '#fff',
  },
  headerRight: { display: 'flex', gap: 8, flex: 1, justifyContent: 'flex-end' },
  linkBtn: {
    fontSize: 11,
    color: '#4E79A7',
    textDecoration: 'none',
    padding: '6px 10px',
    border: '1px solid #3a3a5e',
    borderRadius: 4,
    background: '#0f0f1a',
    whiteSpace: 'nowrap',
  },
  main: { flex: 1, overflow: 'hidden' },
}
