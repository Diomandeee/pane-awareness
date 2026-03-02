# pane-awareness

Cross-session coordination for AI coding assistants running in parallel terminal panes.

When you run 2-4 concurrent AI sessions (e.g., Claude Code in a tiled terminal), each session operates in isolation — unaware of what the others are doing. **pane-awareness** fixes this by giving each session visibility into the others' work, enabling:

- **Topic tracking** — see what each pane is working on and how their focus is shifting
- **Convergence prediction** — get warned before two panes collide on the same problem
- **Resource claiming** — cooperative advisory locks prevent duplicate work on files/APIs
- **Cross-pane messaging** — 8 message types (info, question, delegate, handoff, etc.)
- **Handoff context** — rich context blobs for delegating tasks between panes
- **Delegation suggestions** — automatic recommendations for who should do what

Zero external dependencies. Pure Python. Works with any AI assistant.

## Quick Start

```bash
pip install pane-awareness
```

### Claude Code Integration (Recommended)

```bash
# Auto-install hooks into Claude Code
pa install --claude-code
```

This adds three hooks to your `~/.claude/settings.json`:

| Hook | Event | What it does |
|------|-------|-------------|
| `prompt_hook.py` | UserPromptSubmit | Updates pane registry on each prompt |
| `session_start_hook.py` | SessionStart | Injects other panes' context |
| `claim_guard.py` | PreToolUse | Warns if a file is claimed by another pane |

### Manual / Other Assistants

```python
import pane_awareness as pa

# On each prompt submission
pa.update_pane(session_id="my-session", cwd="/my/project", prompt_text="fix the auth bug")

# See what other panes are doing
panes = pa.get_all_panes()
for tty, pane in panes.items():
    print(f"  [{pane.get('quadrant', '?')}] {pane.get('project')} — {pane.get('key_topics', [])}")

# Claim a resource before working on it
pa.claim_resource("file:src/auth.py", reason="fixing login flow")

# Send a message to another pane
pa.send_message(target="top-right", message="I'm done with auth, you can take over")
```

### MCP Server

Exposes all 20 tools via the Model Context Protocol:

```bash
pa mcp serve
```

Add to your Claude Code config:

```json
{
  "mcpServers": {
    "pane-awareness": {
      "command": "python3",
      "args": ["-m", "pane_awareness.mcp"]
    }
  }
}
```

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
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
│  ~/.local/share/pane-awareness/                              │
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
└──────────────────────────────────────────────────────────────┘
```

## Features

### Topic Extraction & Trajectory

Each prompt is analyzed for keywords. Over the last 10 prompts, topics are classified:

- **deepening** — frequency increasing (you're diving deeper)
- **emerging** — just appeared in recent prompts
- **fading** — frequency decreasing (moving away)
- **stable** — consistent presence

### Convergence Prediction

Four signal types detect when panes are heading toward the same work:

| Signal | Description |
|--------|-------------|
| MUTUAL_DEEPENING | Both panes deepening on the same topics |
| APPROACHING | Topic overlap score crossing threshold |
| CROSS_APPROACH | Pane A deepening into topics Pane B has been working on |
| DOMAIN_PROXIMITY | Different topics but same domain (e.g., both touching auth) |

Predictions self-calibrate: if the false-positive rate exceeds 30%, thresholds auto-adjust upward.

### Resource Claims

Cooperative advisory locking — no enforcement, just coordination:

```
claim → contest → force_release (after timeout)
```

Claims auto-expire when the holding pane goes stale (no activity for configured timeout).

### 8-Type Messaging Protocol

| Type | Purpose |
|------|---------|
| `info` | General information sharing |
| `question` | Ask another pane for input |
| `claim` | Announce a resource claim |
| `release` | Announce a resource release |
| `delegate` | Suggest work delegation |
| `handoff` | Full context handoff |
| `ack` | Acknowledge receipt |
| `block` | Signal that you're blocked |

### Cross-Pollination

The compound signal orchestrator combines all signals:
- Keyword overlap (Jaccard similarity)
- Convergence predictions
- Claim conflicts
- Handoff opportunities
- Delegation suggestions

## CLI

```bash
pa status                    # Show all active panes
pa status --include-stale    # Include stale panes
pa send <target> <message>   # Send a message
pa messages                  # Read your inbox
pa claim <resource>          # Claim a resource
pa release <resource>        # Release a claim
pa claims                    # Show active claims
pa predictions               # Show convergence predictions
pa pollination               # Full cross-pollination analysis
pa install --claude-code     # Install Claude Code hooks
pa mcp serve                 # Start MCP server
```

## Configuration

Config is loaded from (highest priority first):

1. `PANE_AWARENESS_CONFIG` environment variable
2. `.pane-awareness.toml` in current directory
3. `~/.config/pane-awareness/config.toml`
4. Built-in defaults

Example config:

```toml
[general]
state_dir = "~/.local/share/pane-awareness"
stale_timeout = 600        # seconds before a pane is considered stale
identity_noise = []        # extra words to filter from topics

[topics]
max_topics = 10
extra_stop_words = []

[convergence]
min_shared_topics = 2
threshold = 0.35
prediction_ttl = 3600      # seconds before predictions expire

[claims]
contest_timeout = 120      # seconds before a contested claim can be force-released
auto_expire = true

[messages]
max_log_entries = 500

[domains]
# Map topics to domains for proximity detection
# auth = ["authentication", "login", "jwt", "oauth"]
# database = ["sql", "migration", "schema", "query"]

[quadrant]
terminal = "auto"          # auto, terminal, iterm2, linux
```

## Optional Extensions

### Obsidian Vault Writer

Writes pane state as Obsidian-compatible markdown notes with [[wikilinks]]:

```bash
pip install pane-awareness[vault]
```

```python
from extensions.vault_writer import VaultWriter

writer = VaultWriter()  # uses VAULT_PATH env var
writer.write_pane_state(pane_data)
writer.write_prediction(prediction)
writer.write_topology_snapshot(topology)
```

### Dashboard API

FastAPI sidecar serving pane data for web dashboards:

```bash
pip install pane-awareness[dashboard]
uvicorn extensions.dashboard.api:app --port 8005
```

Endpoints: `/health`, `/panes`, `/panes/messages`, `/panes/stats`

A reference React dashboard component is included at `extensions/dashboard/frontend/panes.tsx`.

## License

MIT
