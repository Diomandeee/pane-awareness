/**
 * Reference React dashboard page for Pane Awareness.
 *
 * This is a standalone component showing how to build a dashboard
 * that consumes the Pane Awareness Dashboard API.
 *
 * Adapt the styling, imports, and API URL to your own project.
 *
 * Dependencies: react, lucide-react (icons)
 */

'use client'

import { useState, useEffect, useCallback } from 'react'

// -- Types --

interface LivePane {
  tty: string
  quadrant: string | null
  project: string
  last_prompt: string
  key_topics: string[]
  last_active: string | null
  status: string
}

interface PredictionNote {
  filename: string
  title: string
  modified: string
  prediction_type?: string
  confidence?: string
  status?: string
  pane_a?: string
  pane_b?: string
  urgency?: string
}

interface ClaimNote {
  filename: string
  title: string
  modified: string
  resource?: string
  event?: string
  holder?: string
  scope?: string
}

interface ThreadNote {
  filename: string
  title: string
  modified: string
  from_pane?: string
  to_pane?: string
  task?: string
}

interface TopologyRow {
  quadrant: string
  project: string
  last_prompt: string
}

interface PaneMessage {
  id?: string
  from: string
  target: string
  message: string
  priority?: string
  msg_type?: string
  timestamp: string
}

interface PredictionStats {
  total: number
  active: number
  resolved: number
  prevented: number
  occurred: number
  false_positive: number
  expired: number
  prevention_rate: number
}

interface PanesData {
  live_panes: LivePane[]
  predictions: {
    active: unknown[]
    vault_notes: PredictionNote[]
  }
  claims: {
    active: unknown[]
    vault_notes: ClaimNote[]
  }
  threads: ThreadNote[]
  latest_topology: {
    filename: string
    title: string
    pane_count?: string
    pane_rows?: TopologyRow[]
    modified: string
  } | null
  summary: {
    active_panes: number
    active_predictions: number
    active_claims: number
    total_threads: number
  }
  timestamp: string
}

// -- Helpers --

// Configure this to point to your dashboard API
const API_URL = process.env.NEXT_PUBLIC_PANE_API_URL || 'http://localhost:8005'

function timeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return 'just now'
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs}h ${mins % 60}m ago`
  return `${Math.floor(hrs / 24)}d ago`
}

// -- Component --

export default function PanesPage() {
  const [data, setData] = useState<PanesData | null>(null)
  const [messages, setMessages] = useState<PaneMessage[]>([])
  const [predStats, setPredStats] = useState<PredictionStats | null>(null)
  const [error, setError] = useState<string | null>(null)

  const refresh = useCallback(async () => {
    try {
      const [panesRes, msgRes, statsRes] = await Promise.allSettled([
        fetch(`${API_URL}/panes`, { cache: 'no-store' }),
        fetch(`${API_URL}/panes/messages?limit=30`, { cache: 'no-store' }),
        fetch(`${API_URL}/panes/stats`, { cache: 'no-store' }),
      ])
      if (panesRes.status === 'fulfilled' && panesRes.value.ok) {
        setData(await panesRes.value.json())
      }
      if (msgRes.status === 'fulfilled' && msgRes.value.ok) {
        const msgJson = await msgRes.value.json()
        setMessages(msgJson.messages || [])
      }
      if (statsRes.status === 'fulfilled' && statsRes.value.ok) {
        const sJson = await statsRes.value.json()
        setPredStats(sJson.stats || null)
      }
      setError(null)
    } catch (e) {
      setError(`Failed to fetch: ${e}`)
    }
  }, [])

  useEffect(() => {
    refresh()
    const interval = setInterval(refresh, 15000) // Auto-refresh every 15s
    return () => clearInterval(interval)
  }, [refresh])

  const s = data?.summary

  return (
    <div style={{ maxWidth: 1200, margin: '0 auto', padding: 24, fontFamily: 'system-ui' }}>
      <h1>Pane Awareness Dashboard</h1>
      <p style={{ color: '#888' }}>
        Cross-session coordination — predictions, claims, and handoffs
      </p>

      {error && <div style={{ color: 'red', marginBottom: 16 }}>{error}</div>}

      {/* Summary Stats */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16, marginBottom: 24 }}>
        <StatCard label="Active Panes" value={s?.active_panes ?? 0} />
        <StatCard label="Predictions" value={s?.active_predictions ?? 0} />
        <StatCard label="Claims" value={s?.active_claims ?? 0} />
        <StatCard label="Handoffs" value={s?.total_threads ?? 0} />
      </div>

      {/* Active Panes (2x2 Grid) */}
      <Section title="Active Topology">
        {data?.live_panes?.length ? (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
            {['top-left', 'top-right', 'bottom-left', 'bottom-right'].map(q => {
              const panesInQ = data.live_panes.filter(p => p.quadrant === q)
              return (
                <div key={q} style={{ border: '1px solid #333', borderRadius: 8, padding: 12, minHeight: 80 }}>
                  <small style={{ color: '#888', textTransform: 'uppercase' }}>{q}</small>
                  {panesInQ.length === 0 ? (
                    <p style={{ color: '#555', fontSize: 12, fontStyle: 'italic' }}>empty</p>
                  ) : panesInQ.map((p, i) => (
                    <div key={i} style={{ marginTop: 8 }}>
                      <strong>{p.project}</strong>
                      <p style={{ fontSize: 11, color: '#888', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {p.last_prompt || 'idle'}
                      </p>
                    </div>
                  ))}
                </div>
              )
            })}
          </div>
        ) : (
          <p style={{ color: '#888' }}>No active panes</p>
        )}
      </Section>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
        {/* Predictions */}
        <Section title="Convergence Predictions">
          {data?.predictions?.vault_notes?.length ? (
            data.predictions.vault_notes.map(p => (
              <div key={p.filename} style={{ padding: '8px 0', borderBottom: '1px solid #222' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                  <span>
                    <Badge label={p.prediction_type || '?'} />
                    <Badge label={p.status || '?'} />
                  </span>
                  <small style={{ color: '#888' }}>{timeAgo(p.modified)}</small>
                </div>
                <p style={{ fontSize: 12 }}>{p.pane_a} &harr; {p.pane_b}</p>
                <small style={{ color: '#888' }}>
                  Confidence: {p.confidence} &middot; {p.urgency || 'NORMAL'}
                </small>
              </div>
            ))
          ) : <p style={{ color: '#888' }}>No predictions</p>}
        </Section>

        {/* Claims */}
        <Section title="Resource Claims">
          {data?.claims?.vault_notes?.length ? (
            data.claims.vault_notes.map(c => (
              <div key={c.filename} style={{ padding: '8px 0', borderBottom: '1px solid #222' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                  <Badge label={c.event || '?'} />
                  <small style={{ color: '#888' }}>{timeAgo(c.modified)}</small>
                </div>
                <p style={{ fontSize: 12, fontFamily: 'monospace' }}>{c.resource}</p>
                <small style={{ color: '#888' }}>
                  Holder: {c.holder} &middot; {c.scope}
                </small>
              </div>
            ))
          ) : <p style={{ color: '#888' }}>No claims</p>}
        </Section>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginTop: 16 }}>
        {/* Handoff Threads */}
        <Section title="Handoff Threads">
          {data?.threads?.length ? (
            data.threads.map(t => (
              <div key={t.filename} style={{ padding: '8px 0', borderBottom: '1px solid #222' }}>
                <div style={{ display: 'flex', gap: 8, marginBottom: 4 }}>
                  <span style={{ fontSize: 12, color: '#4af' }}>{t.from_pane}</span>
                  <span style={{ color: '#888' }}>&rarr;</span>
                  <span style={{ fontSize: 12, color: '#4fa' }}>{t.to_pane}</span>
                  <small style={{ color: '#888', marginLeft: 'auto' }}>{timeAgo(t.modified)}</small>
                </div>
                <p style={{ fontSize: 12, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {t.task}
                </p>
              </div>
            ))
          ) : <p style={{ color: '#888' }}>No handoff threads</p>}
        </Section>

        {/* Messages */}
        <Section title="Message Log">
          {messages.length ? (
            <div style={{ maxHeight: 300, overflow: 'auto' }}>
              {messages.map((m, i) => (
                <div key={m.id || i} style={{ padding: '6px 0', borderBottom: '1px solid #222' }}>
                  <div style={{ display: 'flex', gap: 8, marginBottom: 2, fontSize: 11 }}>
                    <span style={{ color: '#4af', fontFamily: 'monospace' }}>
                      {m.from?.split('/').pop() || '??'}
                    </span>
                    <span style={{ color: '#888' }}>&rarr;</span>
                    <span style={{ color: '#4fa', fontFamily: 'monospace' }}>
                      {m.target === 'all' ? 'ALL' : m.target?.split('/').pop() || m.target}
                    </span>
                    {m.priority === 'urgent' && <Badge label="urgent" />}
                    {m.msg_type && m.msg_type !== 'info' && <Badge label={m.msg_type} />}
                    <small style={{ color: '#888', marginLeft: 'auto' }}>{timeAgo(m.timestamp)}</small>
                  </div>
                  <p style={{ fontSize: 12, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {m.message}
                  </p>
                </div>
              ))}
            </div>
          ) : <p style={{ color: '#888' }}>No messages</p>}
        </Section>
      </div>

      {/* Prediction Accuracy */}
      {predStats && predStats.resolved > 0 && (
        <Section title="Prediction Accuracy">
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 16, textAlign: 'center' }}>
            <div><p style={{ fontSize: 24, fontWeight: 'bold' }}>{predStats.total}</p><small>Total</small></div>
            <div><p style={{ fontSize: 24, fontWeight: 'bold', color: '#4fa' }}>{predStats.prevented}</p><small>Prevented</small></div>
            <div><p style={{ fontSize: 24, fontWeight: 'bold', color: '#fa4' }}>{predStats.occurred}</p><small>Occurred</small></div>
            <div><p style={{ fontSize: 24, fontWeight: 'bold', color: '#f44' }}>{predStats.false_positive}</p><small>False Positive</small></div>
            <div><p style={{ fontSize: 24, fontWeight: 'bold', color: '#888' }}>{predStats.expired}</p><small>Expired</small></div>
          </div>
          <div style={{ marginTop: 12 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
              <small>Prevention Rate</small>
              <small style={{ fontWeight: 'bold' }}>{predStats.prevention_rate}%</small>
            </div>
            <div style={{ background: '#333', borderRadius: 4, height: 8 }}>
              <div style={{
                background: '#4fa',
                borderRadius: 4,
                height: 8,
                width: `${Math.min(predStats.prevention_rate, 100)}%`,
                transition: 'width 0.3s',
              }} />
            </div>
          </div>
        </Section>
      )}
    </div>
  )
}

// -- Sub-components --

function StatCard({ label, value }: { label: string; value: number }) {
  return (
    <div style={{ border: '1px solid #333', borderRadius: 8, padding: 16, textAlign: 'center' }}>
      <p style={{ fontSize: 28, fontWeight: 'bold', margin: 0 }}>{value}</p>
      <small style={{ color: '#888' }}>{label}</small>
    </div>
  )
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div style={{ border: '1px solid #333', borderRadius: 8, overflow: 'hidden', marginBottom: 16 }}>
      <div style={{ padding: '8px 16px', borderBottom: '1px solid #333' }}>
        <h3 style={{ margin: 0, fontSize: 14 }}>{title}</h3>
      </div>
      <div style={{ padding: 16 }}>{children}</div>
    </div>
  )
}

function Badge({ label }: { label: string }) {
  return (
    <span style={{
      fontSize: 10,
      padding: '2px 6px',
      borderRadius: 4,
      background: '#333',
      color: '#aaa',
      marginRight: 4,
    }}>
      {label}
    </span>
  )
}
