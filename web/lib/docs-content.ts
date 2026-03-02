export const docsContent: Record<string, string> = {
  configuration: `# Configuration Reference

pane-awareness uses a layered configuration system with sensible defaults. Most users won't need a config file at all.

## Config File Locations

Loaded in priority order (first found wins):

1. **Environment variable**: \`PANE_AWARENESS_CONFIG=/path/to/config.toml\`
2. **Project-local**: \`.pane-awareness.toml\` in current working directory
3. **User-global**: \`~/.config/pane-awareness/config.toml\`
4. **Built-in defaults**: No file needed

Config files support TOML (Python 3.11+) with JSON fallback for Python 3.9-3.10.

## Full Reference

\`\`\`toml
[general]
# Directory for state files (pane_registry.json, pane_claims.json, etc.)
# Default: ~/.config/pane-awareness/state
state_dir = ""

# Hours of inactivity before a pane is considered stale
stale_hours = 2.0

# Extra words to filter from topic extraction (your username, hostname, etc.)
# These are auto-detected from $USER and $HOME, but you can add more
identity_noise_extra = []

# Base directories for project name extraction
# When a pane's CWD is under one of these, the immediate subdirectory is the project name
project_base_dirs = ["~/projects", "~/Desktop", "~/src", "~/code", "~/work"]

[topics]
# Maximum number of topics to extract per prompt
max_topics = 8

# Size of the rolling topic trajectory window
trajectory_window_size = 10

# Additional stop words to filter (beyond the built-in ~80)
extra_stop_words = []

[convergence]
# Initial convergence threshold (auto-adjusted by the calibration engine)
threshold = 0.8

# Bounds for auto-calibration
threshold_min = 0.6
threshold_max = 0.95
threshold_step = 0.05

# Minutes before a prediction expires without resolution
prediction_ttl_min = 60

# Maximum stored predictions
predictions_cap = 50

# Minutes after resolution before a prediction is considered resolved
resolution_window_min = 5

[claims]
# Minutes before a contested claim can be force-released
contest_timeout_min = 5

# Maximum entries in the claims log
log_cap = 200

[messages]
# Maximum entries in the message log
log_cap = 500

# Maximum read messages stored per pane
read_cap = 100

[quadrant]
# Terminal detection method: auto, terminal, iterm2, linux
# "auto" tries Terminal.app, then iTerm2, then xdotool
terminal = "auto"

[domains]
# Map domain names to topic keywords for proximity detection
# Uncomment and customize for your project:
#
# auth = ["authentication", "login", "jwt", "oauth", "session", "token"]
# database = ["sql", "migration", "schema", "query", "postgres", "mysql"]
# api = ["endpoint", "rest", "graphql", "route", "handler"]
# frontend = ["react", "component", "css", "layout", "form"]
# testing = ["test", "e2e", "playwright", "jest", "mock"]
# infra = ["docker", "kubernetes", "ci", "deploy", "nginx"]

# Port-to-domain mapping for claim inference
# When a claim is on "port:8000", it maps to the corresponding domain
# [domains.ports]
# 3000 = "frontend"
# 5432 = "database"
# 8000 = "api"
\`\`\`

## Environment Variables

| Variable | Description |
|----------|-------------|
| \`PANE_AWARENESS_CONFIG\` | Path to config file |
| \`PANE_AWARENESS_STATE_DIR\` | Override state directory (takes precedence over config) |
| \`VAULT_PATH\` | Obsidian vault path (for vault_writer extension) |

## JSON Config (Python 3.9-3.10)

If TOML is not available, you can use JSON:

\`\`\`json
{
  "general": {
    "state_dir": "",
    "stale_hours": 2.0
  },
  "topics": {
    "max_topics": 8
  },
  "convergence": {
    "threshold": 0.8
  },
  "domains": {
    "auth": ["authentication", "login", "jwt"]
  }
}
\`\`\`

Save as \`.pane-awareness.json\` alongside where you'd put the \`.toml\` file.`,

  'api-reference': `# Python API Reference

All functions are available from the top-level \`pane_awareness\` module:

\`\`\`python
import pane_awareness as pa
\`\`\`

## Pane Registry

### \`update_pane(session_id, cwd, prompt_text)\`

Register or update the current pane's state.

- **session_id** (str): Unique identifier for this session
- **cwd** (str): Current working directory
- **prompt_text** (str): The user's prompt text

Extracts topics, computes trajectory, auto-detects quadrant, and writes to the registry.

### \`get_all_panes(include_stale=False)\`

Returns a dict of \`{tty: pane_data}\` for all registered panes.

- **include_stale** (bool): If True, includes panes past the stale timeout

### \`get_pane_info(tty=None)\`

Get info for a specific pane. If \`tty\` is None, returns info for the current pane.

### \`set_quadrant(quadrant)\`

Manually set the quadrant label for the current pane. Returns True on success.

### \`auto_detect_and_set_quadrant()\`

Auto-detect quadrant from window position (macOS Terminal/iTerm2, Linux xdotool). Returns the detected quadrant string or None.

## Messages

### \`send_message(target, message, priority="normal", msg_type="info")\`

Send a message to another pane.

- **target** (str): TTY path, quadrant name ("top-left"), or "all"
- **message** (str): Message text
- **priority** (str): "normal" or "urgent"
- **msg_type** (str): One of: info, question, claim, release, delegate, handoff, ack, block

### \`get_messages()\`

Read unread messages for the current pane. Messages are archived after reading.

### \`get_message_log(limit=50)\`

Read the global message audit log. Returns the last \`limit\` entries.

### \`send_handoff(target, task, context_blob=None, next_steps=None)\`

Send a structured handoff message with context.

### \`send_delegation(target, resource, reason="")\`

Send a delegation suggestion to another pane.

### \`send_question(target, question)\`

Send a question to another pane.

### \`send_ack(target, ref_message_id)\`

Acknowledge receipt of a message.

### \`send_block(target, reason)\`

Signal that you're blocked and need help.

## Claims

### \`claim_resource(resource, scope="exclusive", reason="")\`

Claim a shared resource. Returns a dict with \`status\` ("granted" or "denied") and details.

- **resource** (str): Resource identifier (e.g., "file:src/auth.py", "port:8000")
- **scope** (str): "exclusive" or "shared"
- **reason** (str): Why you need this resource

### \`release_resource(resource)\`

Release a previously claimed resource.

### \`contest_claim(resource, reason="")\`

Contest a claim held by another pane. Starts the contest timer.

### \`force_release(resource, reason="")\`

Force-release a contested claim (only works after contest timeout or if holder is stale).

### \`get_active_claims()\`

Returns all active claims. Auto-cleans stale claims.

### \`get_claims_log(limit=50)\`

Returns the claims history log.

## Convergence & Predictions

### \`detect_cross_pollination()\`

Run the full compound signal analysis. Returns:

\`\`\`python
{
    "overlap": [...],          # Keyword overlap between pane pairs
    "predictions": [...],      # Convergence predictions
    "opportunities": [...],    # Synergy opportunities
    "claim_conflicts": [...],  # Resource claim conflicts
    "handoff_opportunities": [...],
    "delegations": [...],      # Delegation suggestions
    "trajectory_summary": {...},
}
\`\`\`

### \`get_active_predictions()\`

Returns currently active convergence predictions.

### \`resolve_predictions()\`

Resolve active predictions against current state. Classifies each as:
- **prevented**: Teams coordinated, no collision
- **occurred**: Collision happened despite warning
- **false_positive**: Prediction was wrong
- **expired**: Prediction timed out

### \`predict_convergence(pane_a, pane_b)\`

Run convergence detection between two specific panes.

### \`detect_opportunities()\`

Detect synergy opportunities across all panes.

## Handoff & Delegation

### \`build_handoff_context(tier2_fields=None)\`

Build a tiered handoff context blob for the current pane.

- **Tier 1** (automatic): project, CWD, recent prompts, git diff, active claims
- **Tier 2** (explicit): Additional fields passed via \`tier2_fields\`

### \`suggest_delegations()\`

Analyze all panes and suggest delegations based on trajectory drift and domain expertise.

### \`detect_handoff_opportunities()\`

Detect opportunities for context handoffs between panes.

## Domains

### \`get_effective_domain_map()\`

Returns the merged domain map (configured + learned). Maps domain names to lists of topic keywords.

## Configuration

### \`get_config()\`

Returns the current \`PaneConfig\` dataclass. Loaded lazily on first access.

### \`reset_config()\`

Force reload of configuration from disk.`,

  'mcp-tools': `# MCP Tools Reference

The pane-awareness MCP server exposes 20 tools for cross-session coordination.

## Setup

\`\`\`bash
pip install pane-awareness[mcp]
\`\`\`

Add to Claude Code MCP config (\`~/.claude/settings.json\`):

\`\`\`json
{
  "mcpServers": {
    "pane-awareness": {
      "command": "python3",
      "args": ["-m", "pane_awareness.mcp"]
    }
  }
}
\`\`\`

Or run standalone:

\`\`\`bash
pa mcp serve
\`\`\`

## Tools

### Pane Registry

| Tool | Description | Parameters |
|------|-------------|------------|
| \`pane_status\` | Show all active panes with topics and trajectory | \`include_stale\` (bool, optional) |
| \`pane_info\` | Get info for a specific pane by TTY | \`tty\` (string) |

### Messaging

| Tool | Description | Parameters |
|------|-------------|------------|
| \`send_pane_message\` | Send a message to another pane | \`target\` (required), \`message\` (required), \`priority\`, \`msg_type\` |
| \`get_pane_messages\` | Read messages from current pane's inbox | — |
| \`pane_message_log\` | Read the global message audit log | \`limit\` (int, default 50) |

### Resource Claims

| Tool | Description | Parameters |
|------|-------------|------------|
| \`claim_resource\` | Claim a shared resource | \`resource\` (required), \`scope\`, \`reason\` |
| \`release_resource\` | Release a claimed resource | \`resource\` (required) |
| \`contest_claim\` | Contest a claim held by another pane | \`resource\` (required), \`reason\` |
| \`force_release\` | Force-release a contested claim after timeout | \`resource\` (required), \`reason\` |
| \`active_claims\` | Show all active resource claims | — |
| \`claims_log\` | Read the claims history log | \`limit\` (int, default 50) |

### Convergence & Analysis

| Tool | Description | Parameters |
|------|-------------|------------|
| \`cross_pollination\` | Full compound signal analysis | — |
| \`active_predictions\` | Get active convergence predictions | — |
| \`resolve_predictions\` | Resolve predictions against current state | — |

### Handoff & Delegation

| Tool | Description | Parameters |
|------|-------------|------------|
| \`handoff_context\` | Build a handoff context blob | \`tier2_fields\` (object, optional) |
| \`suggest_delegations\` | Get delegation suggestions | — |
| \`send_handoff\` | Send a structured handoff to another pane | \`target\` (required), \`task\` (required), \`context_blob\`, \`next_steps\` |

### Quadrant & Domain

| Tool | Description | Parameters |
|------|-------------|------------|
| \`set_pane_quadrant\` | Set the quadrant label for current pane | \`quadrant\` (required) |
| \`detect_quadrant\` | Auto-detect quadrant from window position | — |
| \`domain_map\` | Get the effective domain map | — |

## Example Responses

### \`pane_status\`

\`\`\`json
{
  "/dev/ttys001": {
    "quadrant": "top-left",
    "project": "api-server",
    "key_topics": ["auth", "jwt", "middleware"],
    "last_prompt": "fix the token validation in auth middleware",
    "last_active": "2024-01-01T12:30:00Z",
    "trajectory_vector": {
      "deepening": ["auth", "jwt"],
      "emerging": ["middleware"],
      "fading": [],
      "stable": []
    }
  }
}
\`\`\`

### \`cross_pollination\`

\`\`\`json
{
  "overlap": [
    {
      "pane_a": "/dev/ttys001",
      "pane_b": "/dev/ttys002",
      "shared_topics": ["auth", "login"],
      "score": 0.42
    }
  ],
  "predictions": [
    {
      "type": "APPROACHING",
      "pane_a": "/dev/ttys001",
      "pane_b": "/dev/ttys002",
      "shared_topics": ["auth", "login"],
      "confidence": 0.34,
      "recommendation": "Both panes are heading toward [auth, login]. Coordinate before proceeding."
    }
  ]
}
\`\`\``,

  'hooks-guide': `# Hooks Integration Guide

pane-awareness integrates with AI coding assistants via hooks — scripts that run at key lifecycle points.

## Claude Code (Built-in)

The easiest setup — one command:

\`\`\`bash
pa install --claude-code
\`\`\`

This adds three hooks to \`~/.claude/settings.json\`:

### 1. Prompt Hook (\`UserPromptSubmit\`)

Runs on every user prompt. Updates the pane registry with:
- Current working directory and project name
- Extracted topics from the prompt
- Trajectory vector (topic momentum over last 10 prompts)
- Auto-detected quadrant from window position

**File**: \`hooks/claude_code/prompt_hook.py\`

### 2. Session Start Hook (\`SessionStart\`)

Runs when a new Claude Code session starts. Injects context about other active panes:
- List of active panes with projects and quadrants
- Unread messages
- Active convergence predictions
- Active resource claims

**File**: \`hooks/claude_code/session_start_hook.py\`

### 3. Claim Guard (\`PreToolUse\`)

Runs before file operations (Write, Edit). Issues advisory warnings if the target file is claimed by another pane.

**File**: \`hooks/claude_code/claim_guard.py\`

### Manual Installation

If you prefer to set up hooks manually, add to \`~/.claude/settings.json\`:

\`\`\`json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "type": "command",
        "command": "python3 /path/to/pane-awareness/hooks/claude_code/prompt_hook.py"
      }
    ],
    "SessionStart": [
      {
        "type": "command",
        "command": "python3 /path/to/pane-awareness/hooks/claude_code/session_start_hook.py"
      }
    ],
    "PreToolUse": [
      {
        "type": "command",
        "command": "python3 /path/to/pane-awareness/hooks/claude_code/claim_guard.py",
        "matcher": "Write|Edit"
      }
    ]
  }
}
\`\`\`

## Generic / Other AI Assistants

For Cursor, Continue, Aider, or any other AI coding tool, use the template at \`hooks/generic/hook_template.py\`.

### Integration Points

Your assistant needs to provide:

1. **On prompt submit** — call \`on_prompt_submit(session_id, cwd, prompt_text)\`
2. **On session start** — call \`on_session_start()\` and inject the result into context
3. **On file write** (optional) — call \`on_file_write(path)\` and show any warnings

### Example: Python Extension

\`\`\`python
from pane_awareness.hooks.generic.hook_template import (
    on_prompt_submit, on_session_start, on_file_write,
)

# In your prompt handler:
on_prompt_submit(session_id="my-session", cwd=os.getcwd(), prompt_text=user_input)

# On session start:
context = on_session_start()
if context:
    inject_into_system_prompt(context)

# Before file writes:
warning = on_file_write("/path/to/file.py")
if warning:
    show_warning_to_user(warning)
\`\`\`

### Example: Subprocess Approach

\`\`\`bash
# Pipe prompt data to the hook
echo '{"session_id": "s1", "cwd": "/my/project", "prompt": "fix the bug"}' \\
  | python3 /path/to/pane-awareness/hooks/generic/hook_template.py
\`\`\`

## Writing Custom Hooks

The core functions you need:

\`\`\`python
import pane_awareness as pa

# Update pane state (call on every prompt)
pa.update_pane(session_id="...", cwd="...", prompt_text="...")

# Get context for injection (call on session start)
panes = pa.get_all_panes()
messages = pa.get_messages()
predictions = pa.get_active_predictions()
claims = pa.get_active_claims()

# Check claims before file ops
claims = pa.get_active_claims()
for claim in claims.get("claims", []):
    if file_path in claim.get("resource", ""):
        warn(f"File claimed by {claim.get('holder_project')}")
\`\`\`

## What Gets Shared

Each pane shares (via local JSON files):
- Session ID, TTY, CWD, project name
- Keywords from the last prompt
- Topic trajectory (last 10 prompts, classified as deepening/emerging/fading/stable)
- Quadrant position (auto-detected from terminal window geometry)

Nothing is sent to any remote server. All state is local files.`,

  'vault-integration': `# Obsidian Vault Integration

The vault_writer extension writes pane-awareness data as Obsidian-compatible markdown notes with YAML frontmatter and [[wikilinks]].

## Setup

\`\`\`bash
pip install pane-awareness[vault]
\`\`\`

Set your vault path:

\`\`\`bash
export VAULT_PATH=~/my-obsidian-vault
\`\`\`

Or configure in \`config.toml\`:

\`\`\`toml
[vault]
path = "~/my-obsidian-vault"
\`\`\`

## Usage

\`\`\`python
from pane_awareness.extensions.vault_writer import VaultWriter

writer = VaultWriter()  # uses VAULT_PATH env var

# Write a pane state note (idempotent — overwrites same pane)
writer.write_pane_state({
    "tty": "/dev/ttys001",
    "session_id": "abc123",
    "quadrant": "top-left",
    "project": "my-project",
    "cwd": "/home/user/my-project",
    "last_prompt": "fix the auth bug",
    "key_topics": ["auth", "jwt"],
    "created": "2024-01-01T12:00:00Z",
    "last_active": "2024-01-01T12:30:00Z",
})

# Write a convergence prediction (deduplicates within 1-hour window)
writer.write_prediction({
    "prediction_type": "APPROACHING",
    "pane_a": "/dev/ttys001",
    "pane_b": "/dev/ttys002",
    "shared_topics": ["auth", "login"],
    "confidence": 0.42,
    "urgency": "HIGH",
    "pane_a_project": "api-server",
    "pane_b_project": "frontend",
})

# Write a claim event
writer.write_claim_event({
    "resource": "file:src/auth.py",
    "event": "claimed",
    "holder": "/dev/ttys001",
    "holder_project": "api-server",
    "scope": "exclusive",
    "reason": "refactoring login flow",
})

# Write a topology snapshot
writer.write_topology_snapshot({
    "panes": [
        {"quadrant": "top-left", "project": "api-server", "last_prompt": "fix auth"},
        {"quadrant": "top-right", "project": "frontend", "last_prompt": "build login page"},
    ],
    "connections": [
        {"pane_a": "top-left", "pane_b": "top-right", "shared_topics": ["auth"], "score": 0.4},
    ],
    "prediction_count": 1,
})

# Write a handoff thread
writer.write_handoff_thread({
    "from_pane": "/dev/ttys001",
    "to_pane": "/dev/ttys002",
    "task": "Implement the frontend login form",
    "from_project": "api-server",
    "to_project": "frontend",
    "next_steps": ["Connect form to POST /api/auth/login", "Handle JWT token storage"],
})
\`\`\`

## Vault Directory Structure

The extension creates these subdirectories:

\`\`\`
obsidian-vault/
├── Panes/              # Live pane session notes (overwritten per-pane)
├── Predictions/        # Convergence prediction notes (deduplicated)
├── Claims/             # Resource claim event notes (timestamped)
├── Threads/            # Handoff thread notes (timestamped)
├── Topologies/         # Periodic topology snapshots
├── Projects/           # Auto-generated project stubs (for backlinks)
└── Inbox/
    └── YYYY-MM-DD/     # Enhanced connection notes (daily subdirs)
\`\`\`

## Note Types

### Pane Session (\`Panes/\`)

Filename: \`{project}-{tty_short}.md\` (idempotent — same pane overwrites)

Frontmatter: \`type: pane-session\`, \`tty\`, \`session_id\`, \`status\`, \`quadrant\`, \`tags\`

### Prediction (\`Predictions/\`)

Filename: \`{type}-{hash}.md\` (deduplicated by type + panes + topics)

Frontmatter: \`type: prediction\`, \`prediction_type\`, \`confidence\`, \`urgency\`, \`status\`, \`pane_a\`, \`pane_b\`

### Claim Event (\`Claims/\`)

Filename: \`{date}-{event}-{resource}-{time}.md\`

Frontmatter: \`type: claim\`, \`resource\`, \`event\`, \`holder\`, \`scope\`

### Topology Snapshot (\`Topologies/\`)

Filename: \`topology-{datetime}.md\`

Contains a markdown table of active panes, connections, and claims.

### Handoff Thread (\`Threads/\`)

Filename: \`{datetime}-{from}-to-{to}.md\`

Frontmatter: \`type: handoff-thread\`, \`from_pane\`, \`to_pane\`, \`task\`, \`context_tier\`

## Backlinks

All notes include [[wikilinks]] to project stubs, creating an automatic backlink graph in Obsidian:

- Pane notes link to \`[[project-name]]\`
- Prediction notes link to \`[[project-a]]\` and \`[[project-b]]\`
- Shared topics become \`[[topic]]\` links
- Handoff threads link to both \`[[from-project]]\` and \`[[to-project]]\`

Project stubs in \`Projects/\` serve as hubs where all related notes accumulate via Obsidian's backlinks panel.`,
}
