#!/usr/bin/env python3
"""Claude Code UserPromptSubmit hook — updates pane state on every prompt.

Wire into ~/.claude/settings.json:
{
  "hooks": {
    "UserPromptSubmit": [{
      "type": "command",
      "command": "python3 /path/to/pane-awareness/hooks/claude_code/prompt_hook.py"
    }]
  }
}

Reads the hook event from stdin (JSON with session_id, cwd, etc.),
extracts the prompt text, and calls update_pane().
"""

import json
import os
import sys

# Add pane-awareness src to path
_HERE = os.path.dirname(os.path.abspath(__file__))
_SRC = os.path.join(_HERE, "..", "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, _SRC)


def main():
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            return

        event = json.loads(raw)
        session_id = event.get("session_id", os.environ.get("CLAUDE_SESSION_ID", "unknown"))
        cwd = event.get("cwd", os.getcwd())

        # Extract prompt text from the hook event
        prompt_text = ""
        if "prompt" in event:
            prompt_text = event["prompt"]
        elif "message" in event:
            msg = event["message"]
            if isinstance(msg, str):
                prompt_text = msg
            elif isinstance(msg, dict):
                prompt_text = msg.get("content", "")
                if isinstance(prompt_text, list):
                    # Multi-part message — join text parts
                    prompt_text = " ".join(
                        p.get("text", "") for p in prompt_text
                        if isinstance(p, dict) and p.get("type") == "text"
                    )

        from pane_awareness import update_pane
        update_pane(session_id=session_id, cwd=cwd, prompt_text=prompt_text)

    except Exception as e:
        print(f"[pane-awareness] prompt_hook error: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
