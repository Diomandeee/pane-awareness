#!/usr/bin/env python3
"""Generic hook template for pane-awareness.

Adapt this template for any AI coding assistant that supports
pre/post prompt hooks. The key integration points are:

1. ON PROMPT SUBMIT: Call update_pane() with session ID, CWD, and prompt text.
2. ON SESSION START: Read other panes, format context, inject into session.
3. ON FILE WRITE (optional): Check claims, warn if conflict.

Your AI assistant needs to provide:
- A way to run code on each user prompt (for update_pane)
- A way to inject context into the session (for pane awareness display)
- Optionally, a pre-action hook (for claim checking)
"""

import os
import sys

# Add pane-awareness to path
_HERE = os.path.dirname(os.path.abspath(__file__))
_SRC = os.path.join(_HERE, "..", "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, _SRC)


def on_prompt_submit(session_id: str, cwd: str, prompt_text: str) -> None:
    """Call this on every user prompt submission.

    Args:
        session_id: Unique identifier for this AI session.
        cwd: Current working directory.
        prompt_text: The user's prompt text.
    """
    from pane_awareness import update_pane
    update_pane(session_id=session_id, cwd=cwd, prompt_text=prompt_text)


def on_session_start() -> str:
    """Call this when a new session starts.

    Returns a formatted string to inject into the session context.
    """
    from pane_awareness import (
        get_all_panes, get_messages, get_active_predictions,
        get_active_claims, auto_detect_and_set_quadrant,
    )
    from pane_awareness._compat import get_current_tty

    auto_detect_and_set_quadrant()
    my_tty = get_current_tty()
    panes = get_all_panes()
    other = {t: p for t, p in panes.items() if t != my_tty}

    if not other:
        return ""

    lines = [f"Active panes: {len(other)}"]
    for tty, pane in other.items():
        q = pane.get("quadrant", "?")
        proj = pane.get("project", "?")
        lines.append(f"  [{q}] {proj}")

    messages = get_messages()
    if messages:
        lines.append(f"Unread messages: {len(messages)}")

    return "\n".join(lines)


def on_file_write(file_path: str) -> str:
    """Call before writing a file. Returns a warning if the file is claimed.

    Args:
        file_path: Path of the file about to be written.

    Returns:
        Warning string, or empty string if no conflict.
    """
    from pane_awareness.claims import get_active_claims
    from pane_awareness._compat import get_current_tty

    my_tty = get_current_tty()
    claims = get_active_claims()

    for claim in claims.get("claims", []):
        if claim.get("holder_tty") == my_tty:
            continue
        resource = claim.get("resource", "")
        if resource.startswith("file:") and resource[5:] in file_path:
            return f"WARNING: {file_path} is claimed by {claim.get('holder')}"

    return ""
