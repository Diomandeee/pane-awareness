# Claude Code Integration

Pane awareness hooks for [Claude Code](https://docs.anthropic.com/en/docs/claude-code).

## Quick Install

```bash
pa install --claude-code
```

Or manually add hooks to `~/.claude/settings.json` (see `settings_example.json`).

## Hooks

### `prompt_hook.py` — UserPromptSubmit

Runs on every user prompt. Registers/updates the current pane's state:
- TTY, session ID, CWD, project name
- Extracted topics from prompt text
- Topic trajectory and momentum vector

### `session_start_hook.py` — SessionStart

Runs when a new Claude Code session starts. Injects context showing:
- Other active panes and what they're working on
- Unread messages from other panes
- Active convergence predictions/warnings
- Active resource claims

### `claim_guard.py` — PreToolUse

Runs before file write/edit operations. Checks if the target file
is claimed by another pane and outputs an advisory warning if so.
Does **not** block the operation — enforcement is cooperative.

## Manual Setup

1. Copy this directory somewhere persistent
2. Edit `~/.claude/settings.json`:

```json
{
  "hooks": {
    "UserPromptSubmit": [{
      "type": "command",
      "command": "python3 /path/to/hooks/claude_code/prompt_hook.py"
    }],
    "SessionStart": [{
      "type": "command",
      "command": "python3 /path/to/hooks/claude_code/session_start_hook.py"
    }],
    "PreToolUse": [{
      "type": "command",
      "command": "python3 /path/to/hooks/claude_code/claim_guard.py",
      "timeout": 3000
    }]
  }
}
```

3. Restart Claude Code sessions
4. Open 2+ sessions in split terminal panes — they'll see each other
