const diagram = `┌──────────────────────────────────────────────────────────────┐
│                     Terminal (2x2 grid)                       │
│  ┌─────────────────────┐  ┌─────────────────────┐           │
│  │ top-left             │  │ top-right            │           │
│  │ Claude Code #1       │  │ Claude Code #2       │           │
│  │ Project: api-server  │  │ Project: frontend    │           │
│  │ Topics: auth, jwt    │  │ Topics: login, form  │           │
│  └─────────┬───────────┘  └──────────┬──────────┘           │
│  ┌─────────┴───────────┐  ┌──────────┴──────────┐           │
│  │ bottom-left          │  │ bottom-right         │           │
│  │ Claude Code #3       │  │ Claude Code #4       │           │
│  │ Project: tests       │  │ Project: docs        │           │
│  │ Topics: e2e, auth    │  │ Topics: api-docs     │           │
│  └─────────────────────┘  └─────────────────────┘           │
└──────────────────────────────────────────────────────────────┘
            │                          │
            ▼                          ▼
┌──────────────────────────────────────────────────────────────┐
│                  pane-awareness (shared state)                │
│                                                              │
│  ~/.config/pane-awareness/state/                              │
│  ├── pane_registry.json    ← pane states + topics            │
│  ├── pane_claims.json      ← resource claims                 │
│  ├── pane_predictions.json ← convergence predictions         │
│  └── learned_domains.json  ← topic-to-domain mapping         │
│                                                              │
│  Coordination signals:                                       │
│  • Topic overlap → convergence prediction (4 signal types)   │
│  • Claim conflict → advisory warning                         │
│  • Trajectory drift → delegation suggestion                  │
│  • Handoff opportunity → context blob + next steps           │
└──────────────────────────────────────────────────────────────┘`

export default function Architecture() {
  return (
    <section className="py-16 px-4">
      <div className="max-w-6xl mx-auto">
        <h2 className="text-3xl font-bold text-center mb-8">Architecture</h2>
        <p className="text-center text-gray-400 mb-8 max-w-2xl mx-auto">
          No server, no database, no daemon. Sessions coordinate through locked JSON files on the
          local filesystem.
        </p>
        <div className="overflow-x-auto">
          <pre className="bg-surface-50 border border-surface-300 rounded-lg p-6 text-xs sm:text-sm font-mono text-brand-300 leading-relaxed mx-auto max-w-fit">
            {diagram}
          </pre>
        </div>
      </div>
    </section>
  )
}
