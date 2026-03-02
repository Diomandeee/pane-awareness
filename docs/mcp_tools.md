# MCP Tools Reference

The pane-awareness MCP server exposes 20 tools for cross-session coordination.

## Setup

```bash
pip install pane-awareness[mcp]
```

Add to Claude Code MCP config (`~/.claude/settings.json`):

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

Or run standalone:

```bash
pa mcp serve
```

## Tools

### Pane Registry

| Tool | Description | Parameters |
|------|-------------|------------|
| `pane_status` | Show all active panes with topics and trajectory | `include_stale` (bool, optional) |
| `pane_info` | Get info for a specific pane by TTY | `tty` (string) |

### Messaging

| Tool | Description | Parameters |
|------|-------------|------------|
| `send_pane_message` | Send a message to another pane | `target` (required), `message` (required), `priority`, `msg_type` |
| `get_pane_messages` | Read messages from current pane's inbox | — |
| `pane_message_log` | Read the global message audit log | `limit` (int, default 50) |

### Resource Claims

| Tool | Description | Parameters |
|------|-------------|------------|
| `claim_resource` | Claim a shared resource | `resource` (required), `scope`, `reason` |
| `release_resource` | Release a claimed resource | `resource` (required) |
| `contest_claim` | Contest a claim held by another pane | `resource` (required), `reason` |
| `force_release` | Force-release a contested claim after timeout | `resource` (required), `reason` |
| `active_claims` | Show all active resource claims | — |
| `claims_log` | Read the claims history log | `limit` (int, default 50) |

### Convergence & Analysis

| Tool | Description | Parameters |
|------|-------------|------------|
| `cross_pollination` | Full compound signal analysis | — |
| `active_predictions` | Get active convergence predictions | — |
| `resolve_predictions` | Resolve predictions against current state | — |

### Handoff & Delegation

| Tool | Description | Parameters |
|------|-------------|------------|
| `handoff_context` | Build a handoff context blob | `tier2_fields` (object, optional) |
| `suggest_delegations` | Get delegation suggestions | — |
| `send_handoff` | Send a structured handoff to another pane | `target` (required), `task` (required), `context_blob`, `next_steps` |

### Quadrant & Domain

| Tool | Description | Parameters |
|------|-------------|------------|
| `set_pane_quadrant` | Set the quadrant label for current pane | `quadrant` (required) |
| `detect_quadrant` | Auto-detect quadrant from window position | — |
| `domain_map` | Get the effective domain map | — |

## Example Responses

### `pane_status`

```json
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
```

### `cross_pollination`

```json
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
```
