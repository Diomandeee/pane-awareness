'use client'

import { useState, useEffect, useCallback } from 'react'
import { fetchPaneData } from '@/lib/api'
import type { PanesData, PaneMessage, PredictionStats } from '@/lib/types'
import StatCard from '@/components/dashboard/stat-card'
import TopologyGrid from '@/components/dashboard/topology-grid'
import Predictions from '@/components/dashboard/predictions'
import Claims from '@/components/dashboard/claims'
import Threads from '@/components/dashboard/threads'
import Messages from '@/components/dashboard/messages'
import Accuracy from '@/components/dashboard/accuracy'
import DemoBanner from '@/components/dashboard/demo-banner'

export default function DashboardPage() {
  const [data, setData] = useState<PanesData | null>(null)
  const [messages, setMessages] = useState<PaneMessage[]>([])
  const [predStats, setPredStats] = useState<PredictionStats | null>(null)
  const [isDemo, setIsDemo] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const refresh = useCallback(async () => {
    const result = await fetchPaneData()
    setData(result.data)
    setMessages(result.messages)
    setPredStats(result.predStats)
    setIsDemo(result.isDemo)
    setError(result.error)
  }, [])

  useEffect(() => {
    refresh()
    const interval = setInterval(refresh, 15000)
    return () => clearInterval(interval)
  }, [refresh])

  const s = data?.summary

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <div className="mb-6">
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <p className="text-sm text-gray-500">
          Cross-session coordination — predictions, claims, and handoffs
        </p>
      </div>

      {isDemo && <DemoBanner />}
      {error && (
        <div className="rounded-lg border border-red-800/50 bg-red-900/20 px-4 py-3 mb-6">
          <p className="text-sm text-red-400">{error}</p>
        </div>
      )}

      {/* Summary Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
        <StatCard label="Active Panes" value={s?.active_panes ?? 0} />
        <StatCard label="Predictions" value={s?.active_predictions ?? 0} />
        <StatCard label="Claims" value={s?.active_claims ?? 0} />
        <StatCard label="Handoffs" value={s?.total_threads ?? 0} />
      </div>

      {/* Topology */}
      <div className="mb-6">
        <TopologyGrid panes={data?.live_panes || []} />
      </div>

      {/* Predictions + Claims */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
        <Predictions predictions={data?.predictions?.vault_notes || []} />
        <Claims claims={data?.claims?.vault_notes || []} />
      </div>

      {/* Threads + Messages */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
        <Threads threads={data?.threads || []} />
        <Messages messages={messages} />
      </div>

      {/* Accuracy */}
      {predStats && <Accuracy stats={predStats} />}
    </div>
  )
}
