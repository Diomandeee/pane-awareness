#!/usr/bin/env python3
"""Claude Code PreToolUse hook — advisory claim warnings.

When a tool is about to write/edit a file, checks if that file path
matches any active claim held by another pane. If so, outputs a WARNING
to stderr (does not block the operation).

Wire into ~/.claude/settings.json:
{
  "hooks": {
    "PreToolUse": [{
      "type": "command",
      "command": "python3 /path/to/claim_guard.py",
      "timeout": 3000
    }]
  }
}
"""

import json
import os
import sys

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
        tool_name = event.get("tool_name", "")

        # Only check file-modifying tools
        if tool_name not in ("Write", "Edit", "write_file", "edit_file", "MultiEdit"):
            return

        # Extract file path from tool input
        tool_input = event.get("tool_input", {})
        file_path = tool_input.get("file_path", "") or tool_input.get("path", "")
        if not file_path:
            return

        from pane_awareness.claims import get_active_claims
        from pane_awareness._compat import get_current_tty

        my_tty = get_current_tty()
        claims = get_active_claims()

        for claim in claims.get("claims", []):
            resource = claim.get("resource", "")
            holder_tty = claim.get("holder_tty", "")

            if holder_tty == my_tty:
                continue  # Our own claim

            # Check if the file matches the claim
            if resource.startswith("file:"):
                pattern = resource[5:]  # Strip "file:" prefix
                if _matches(pattern, file_path):
                    holder = claim.get("holder", "unknown")
                    reason = claim.get("reason", "")
                    print(
                        f"[pane-awareness] WARNING: '{file_path}' is claimed by "
                        f"{holder} (reason: {reason}). "
                        f"Coordinate before modifying.",
                        file=sys.stderr,
                    )
                    return

    except Exception as e:
        print(f"[pane-awareness] claim_guard error: {e}", file=sys.stderr)


def _matches(pattern: str, path: str) -> bool:
    """Check if a file path matches a claim pattern."""
    if pattern == path:
        return True
    if "*" in pattern:
        prefix = pattern.split("*")[0]
        return path.startswith(prefix)
    # Check if pattern is a substring of the path
    return pattern in path


if __name__ == "__main__":
    main()
