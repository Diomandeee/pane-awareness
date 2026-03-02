import type { PanesData, PaneMessage, PredictionStats } from './types'

const now = new Date().toISOString()
const fiveMinAgo = new Date(Date.now() - 5 * 60000).toISOString()
const tenMinAgo = new Date(Date.now() - 10 * 60000).toISOString()
const twentyMinAgo = new Date(Date.now() - 20 * 60000).toISOString()

export const mockPanesData: PanesData = {
  live_panes: [
    {
      tty: '/dev/ttys001',
      quadrant: 'top-left',
      project: 'api-server',
      last_prompt: 'fix the JWT token validation in auth middleware',
      key_topics: ['auth', 'jwt', 'middleware', 'validation'],
      last_active: fiveMinAgo,
      status: 'active',
    },
    {
      tty: '/dev/ttys002',
      quadrant: 'top-right',
      project: 'frontend',
      last_prompt: 'build the login form component with error handling',
      key_topics: ['login', 'form', 'react', 'validation'],
      last_active: now,
      status: 'active',
    },
    {
      tty: '/dev/ttys003',
      quadrant: 'bottom-left',
      project: 'tests',
      last_prompt: 'write e2e tests for the auth flow',
      key_topics: ['e2e', 'auth', 'playwright', 'testing'],
      last_active: tenMinAgo,
      status: 'active',
    },
    {
      tty: '/dev/ttys004',
      quadrant: 'bottom-right',
      project: 'docs',
      last_prompt: 'update API documentation for auth endpoints',
      key_topics: ['api-docs', 'openapi', 'auth'],
      last_active: twentyMinAgo,
      status: 'active',
    },
  ],
  predictions: {
    active: [],
    vault_notes: [
      {
        filename: 'APPROACHING-abc123.md',
        title: 'Convergence: api-server / frontend',
        modified: fiveMinAgo,
        prediction_type: 'APPROACHING',
        confidence: '0.72',
        status: 'active',
        pane_a: 'api-server (top-left)',
        pane_b: 'frontend (top-right)',
        urgency: 'HIGH',
      },
      {
        filename: 'CROSS_APPROACH-def456.md',
        title: 'Cross-approach: tests / api-server',
        modified: tenMinAgo,
        prediction_type: 'CROSS_APPROACH',
        confidence: '0.55',
        status: 'active',
        pane_a: 'tests (bottom-left)',
        pane_b: 'api-server (top-left)',
        urgency: 'NORMAL',
      },
    ],
  },
  claims: {
    active: [],
    vault_notes: [
      {
        filename: '2024-01-01-claimed-auth-py.md',
        title: 'Claimed: file:src/auth.py',
        modified: tenMinAgo,
        resource: 'file:src/auth.py',
        event: 'claimed',
        holder: 'api-server (top-left)',
        scope: 'exclusive',
      },
    ],
  },
  threads: [
    {
      filename: '2024-01-01-api-to-frontend.md',
      title: 'Handoff: Login form implementation',
      modified: fiveMinAgo,
      from_pane: 'api-server (top-left)',
      to_pane: 'frontend (top-right)',
      task: 'Implement the login form — POST /api/auth/login endpoint is ready',
    },
    {
      filename: '2024-01-01-api-to-tests.md',
      title: 'Handoff: Auth test suite',
      modified: twentyMinAgo,
      from_pane: 'api-server (top-left)',
      to_pane: 'tests (bottom-left)',
      task: 'Write integration tests for the new JWT middleware',
    },
  ],
  latest_topology: null,
  summary: {
    active_panes: 4,
    active_predictions: 2,
    active_claims: 1,
    total_threads: 2,
  },
  timestamp: now,
}

export const mockMessages: PaneMessage[] = [
  {
    id: 'msg_001',
    from: '/dev/ttys001',
    target: '/dev/ttys002',
    message: 'Auth endpoint is ready — POST /api/auth/login returns JWT',
    priority: 'normal',
    msg_type: 'info',
    timestamp: fiveMinAgo,
  },
  {
    id: 'msg_002',
    from: '/dev/ttys002',
    target: '/dev/ttys001',
    message: 'What format should the error response be? {error: string} or {errors: string[]}?',
    priority: 'normal',
    msg_type: 'question',
    timestamp: fiveMinAgo,
  },
  {
    id: 'msg_003',
    from: '/dev/ttys001',
    target: '/dev/ttys003',
    message: 'Delegating auth integration tests to you — JWT middleware is complete',
    priority: 'normal',
    msg_type: 'delegate',
    timestamp: tenMinAgo,
  },
  {
    id: 'msg_004',
    from: '/dev/ttys003',
    target: '/dev/ttys001',
    message: 'Acknowledged — starting e2e tests for auth flow',
    priority: 'normal',
    msg_type: 'ack',
    timestamp: tenMinAgo,
  },
  {
    id: 'msg_005',
    from: '/dev/ttys004',
    target: 'all',
    message: 'Updated OpenAPI spec — please review auth section',
    priority: 'urgent',
    msg_type: 'info',
    timestamp: twentyMinAgo,
  },
]

export const mockPredStats: PredictionStats = {
  total: 12,
  active: 2,
  resolved: 10,
  prevented: 6,
  occurred: 2,
  false_positive: 1,
  expired: 1,
  prevention_rate: 75.0,
}
