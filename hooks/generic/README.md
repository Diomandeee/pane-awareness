# Generic AI Assistant Integration

Adapt `hook_template.py` for any AI coding assistant.

## Required Integration Points

1. **On prompt submit** — call `on_prompt_submit(session_id, cwd, prompt_text)`
2. **On session start** — call `on_session_start()` and inject the result into context
3. **On file write** (optional) — call `on_file_write(path)` and show any warnings

## Examples

### Cursor / Continue / Aider

Most AI coding tools support custom scripts or extensions:

```python
# In your extension's prompt handler:
from hook_template import on_prompt_submit
on_prompt_submit(session_id="my-session", cwd=os.getcwd(), prompt_text=user_input)
```

### Generic subprocess approach

```bash
# Pipe prompt to the hook
echo '{"session_id": "s1", "cwd": "/my/project", "prompt": "fix the bug"}' | python3 hook_template.py
```

## What Gets Shared

Each pane shares (via a local JSON file):
- Session ID, TTY, CWD, project name
- Keywords from the last prompt
- Topic trajectory (last 10 prompts, classified as deepening/emerging/fading/stable)
- Quadrant position (auto-detected from terminal window geometry)
