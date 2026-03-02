# Obsidian Vault Integration

The vault_writer extension writes pane-awareness data as Obsidian-compatible markdown notes with YAML frontmatter and [[wikilinks]].

## Setup

```bash
pip install pane-awareness[vault]
```

Set your vault path:

```bash
export VAULT_PATH=~/my-obsidian-vault
```

Or configure in `config.toml`:

```toml
[vault]
path = "~/my-obsidian-vault"
```

## Usage

```python
from extensions.vault_writer import VaultWriter

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
```

## Vault Directory Structure

The extension creates these subdirectories:

```
obsidian-vault/
├── Panes/              # Live pane session notes (overwritten per-pane)
├── Predictions/        # Convergence prediction notes (deduplicated)
├── Claims/             # Resource claim event notes (timestamped)
├── Threads/            # Handoff thread notes (timestamped)
├── Topologies/         # Periodic topology snapshots
├── Projects/           # Auto-generated project stubs (for backlinks)
└── Inbox/
    └── YYYY-MM-DD/     # Enhanced connection notes (daily subdirs)
```

## Note Types

### Pane Session (`Panes/`)

Filename: `{project}-{tty_short}.md` (idempotent — same pane overwrites)

Frontmatter: `type: pane-session`, `tty`, `session_id`, `status`, `quadrant`, `tags`

### Prediction (`Predictions/`)

Filename: `{type}-{hash}.md` (deduplicated by type + panes + topics)

Frontmatter: `type: prediction`, `prediction_type`, `confidence`, `urgency`, `status`, `pane_a`, `pane_b`

### Claim Event (`Claims/`)

Filename: `{date}-{event}-{resource}-{time}.md`

Frontmatter: `type: claim`, `resource`, `event`, `holder`, `scope`

### Topology Snapshot (`Topologies/`)

Filename: `topology-{datetime}.md`

Contains a markdown table of active panes, connections, and claims.

### Handoff Thread (`Threads/`)

Filename: `{datetime}-{from}-to-{to}.md`

Frontmatter: `type: handoff-thread`, `from_pane`, `to_pane`, `task`, `context_tier`

## Backlinks

All notes include [[wikilinks]] to project stubs, creating an automatic backlink graph in Obsidian:

- Pane notes link to `[[project-name]]`
- Prediction notes link to `[[project-a]]` and `[[project-b]]`
- Shared topics become `[[topic]]` links
- Handoff threads link to both `[[from-project]]` and `[[to-project]]`

Project stubs in `Projects/` serve as hubs where all related notes accumulate via Obsidian's backlinks panel.
