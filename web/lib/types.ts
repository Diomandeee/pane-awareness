export interface LivePane {
  tty: string
  quadrant: string | null
  project: string
  last_prompt: string
  key_topics: string[]
  last_active: string | null
  status: string
}

export interface PredictionNote {
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

export interface ClaimNote {
  filename: string
  title: string
  modified: string
  resource?: string
  event?: string
  holder?: string
  scope?: string
}

export interface ThreadNote {
  filename: string
  title: string
  modified: string
  from_pane?: string
  to_pane?: string
  task?: string
}

export interface PaneMessage {
  id?: string
  from: string
  target: string
  message: string
  priority?: string
  msg_type?: string
  timestamp: string
}

export interface PredictionStats {
  total: number
  active: number
  resolved: number
  prevented: number
  occurred: number
  false_positive: number
  expired: number
  prevention_rate: number
}

export interface PanesData {
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
