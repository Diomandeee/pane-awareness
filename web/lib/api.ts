import type { PanesData, PaneMessage, PredictionStats } from './types'
import { mockPanesData, mockMessages, mockPredStats } from './mock-data'

const API_URL = process.env.NEXT_PUBLIC_PANE_API_URL || 'http://localhost:8005'

interface FetchResult {
  data: PanesData | null
  messages: PaneMessage[]
  predStats: PredictionStats | null
  isDemo: boolean
  error: string | null
}

export async function fetchPaneData(): Promise<FetchResult> {
  try {
    const [panesRes, msgRes, statsRes] = await Promise.allSettled([
      fetch(`${API_URL}/panes`, { cache: 'no-store' }),
      fetch(`${API_URL}/panes/messages?limit=30`, { cache: 'no-store' }),
      fetch(`${API_URL}/panes/stats`, { cache: 'no-store' }),
    ])

    let data: PanesData | null = null
    let messages: PaneMessage[] = []
    let predStats: PredictionStats | null = null
    let anySuccess = false

    if (panesRes.status === 'fulfilled' && panesRes.value.ok) {
      data = await panesRes.value.json()
      anySuccess = true
    }
    if (msgRes.status === 'fulfilled' && msgRes.value.ok) {
      const json = await msgRes.value.json()
      messages = json.messages || []
      anySuccess = true
    }
    if (statsRes.status === 'fulfilled' && statsRes.value.ok) {
      const json = await statsRes.value.json()
      predStats = json.stats || null
      anySuccess = true
    }

    if (anySuccess) {
      return { data, messages, predStats, isDemo: false, error: null }
    }

    // All requests failed — fall back to demo
    return {
      data: mockPanesData,
      messages: mockMessages,
      predStats: mockPredStats,
      isDemo: true,
      error: null,
    }
  } catch {
    // Network error — fall back to demo
    return {
      data: mockPanesData,
      messages: mockMessages,
      predStats: mockPredStats,
      isDemo: true,
      error: null,
    }
  }
}
