# MCP Server

Model Context Protocol server exposing 20 pane-awareness tools.

## Setup

```bash
pip install pane-awareness[mcp]
```

Add to your Claude Code MCP config (`~/.claude/settings.json`):

```json
{
  "mcpServers": {
    "pane-awareness": {
      "command": "python3",
      "args": ["/path/to/pane-awareness/mcp/server.py"]
    }
  }
}
```

## Available Tools

| Tool | Description |
|------|-------------|
| `pane_status` | Show all active panes with topics and trajectory |
| `pane_info` | Get info for a specific pane by TTY |
| `send_pane_message` | Send a message to another pane |
| `get_pane_messages` | Read messages from current pane's inbox |
| `pane_message_log` | Read the global message audit log |
| `claim_resource` | Claim a shared resource |
| `release_resource` | Release a claimed resource |
| `contest_claim` | Contest a claim held by another pane |
| `force_release` | Force-release a contested claim after timeout |
| `active_claims` | Show all active resource claims |
| `claims_log` | Read the claims history log |
| `cross_pollination` | Analyze keyword overlap and convergence |
| `active_predictions` | Get active convergence predictions |
| `resolve_predictions` | Resolve predictions against current state |
| `handoff_context` | Build a handoff context blob |
| `suggest_delegations` | Get delegation suggestions |
| `set_pane_quadrant` | Set the quadrant label for current pane |
| `detect_quadrant` | Auto-detect quadrant from window position |
| `domain_map` | Get the effective domain map |
| `send_handoff` | Send a structured handoff to another pane |
