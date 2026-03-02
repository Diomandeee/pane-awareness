# Hooks Integration Guide

pane-awareness integrates with AI coding assistants via hooks — scripts that run at key lifecycle points.

## Claude Code (Built-in)

The easiest setup — one command:

```bash
pa install --claude-code
```

This adds three hooks to `~/.claude/settings.json`:

### 1. Prompt Hook (`UserPromptSubmit`)

Runs on every user prompt. Updates the pane registry with:
- Current working directory and project name
- Extracted topics from the prompt
- Trajectory vector (topic momentum over last 10 prompts)
- Auto-detected quadrant from window position

**File**: `hooks/claude_code/prompt_hook.py`

### 2. Session Start Hook (`SessionStart`)

Runs when a new Claude Code session starts. Injects context about other active panes:
- List of active panes with projects and quadrants
- Unread messages
- Active convergence predictions
- Active resource claims

**File**: `hooks/claude_code/session_start_hook.py`

### 3. Claim Guard (`PreToolUse`)

Runs before file operations (Write, Edit). Issues advisory warnings if the target file is claimed by another pane.

**File**: `hooks/claude_code/claim_guard.py`

### Manual Installation

If you prefer to set up hooks manually, add to `~/.claude/settings.json`:

```json
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
```

## Generic / Other AI Assistants

For Cursor, Continue, Aider, or any other AI coding tool, use the template at `hooks/generic/hook_template.py`.

### Integration Points

Your assistant needs to provide:

1. **On prompt submit** — call `on_prompt_submit(session_id, cwd, prompt_text)`
2. **On session start** — call `on_session_start()` and inject the result into context
3. **On file write** (optional) — call `on_file_write(path)` and show any warnings

### Example: Python Extension

```python
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
```

### Example: Subprocess Approach

```bash
# Pipe prompt data to the hook
echo '{"session_id": "s1", "cwd": "/my/project", "prompt": "fix the bug"}' \
  | python3 /path/to/pane-awareness/hooks/generic/hook_template.py
```

## Writing Custom Hooks

The core functions you need:

```python
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
```

## What Gets Shared

Each pane shares (via local JSON files):
- Session ID, TTY, CWD, project name
- Keywords from the last prompt
- Topic trajectory (last 10 prompts, classified as deepening/emerging/fading/stable)
- Quadrant position (auto-detected from terminal window geometry)

Nothing is sent to any remote server. All state is local files.
