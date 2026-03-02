#!/usr/bin/env python3
"""Claude Code SessionStart hook — injects pane awareness context.

Outputs a formatted text block showing:
- Other active panes (quadrant, project, topics)
- Unread messages
- Active predictions/warnings
- Active claims

This text is injected into the session context at startup.
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
        from pane_awareness import (
            get_all_panes, get_messages, get_active_predictions,
            get_active_claims, auto_detect_and_set_quadrant,
        )
        from pane_awareness._compat import get_current_tty

        # Auto-detect quadrant
        quadrant = auto_detect_and_set_quadrant()

        my_tty = get_current_tty()
        panes = get_all_panes()

        # Filter out self
        other_panes = {t: p for t, p in panes.items() if t != my_tty}

        if not other_panes:
            return  # No other panes — no context to inject

        lines = [
            "=" * 50,
            "PANE AWARENESS",
            "=" * 50,
            "",
        ]

        if quadrant:
            lines.append(f"You are: {quadrant}")
            lines.append("")

        # Active panes
        lines.append(f"Active sessions: {len(other_panes)}")
        for tty, pane in other_panes.items():
            q = pane.get("quadrant", "?")
            proj = pane.get("project", "?")
            topics = ", ".join(pane.get("key_topics", [])[:4])
            prompt = pane.get("last_prompt", "")[:60]
            lines.append(f"  [{q}] {proj}: \"{prompt}\"")
            if topics:
                lines.append(f"    Topics: {topics}")

            vec = pane.get("trajectory_vector", {})
            deep = vec.get("deepening", [])
            emerge = vec.get("emerging", [])
            if deep:
                lines.append(f"    Deepening: {', '.join(deep[:3])}")
            if emerge:
                lines.append(f"    Emerging: {', '.join(emerge[:3])}")

        # Unread messages
        messages = get_messages()
        if messages:
            lines.append("")
            lines.append(f"Unread messages: {len(messages)}")
            for msg in messages[:5]:
                sender = msg.get("from", "?")
                text = msg.get("message", "")[:80]
                mtype = msg.get("msg_type", "info")
                priority = "!" if msg.get("priority") == "urgent" else " "
                lines.append(f"  {priority}[{mtype}] {sender}: {text}")

        # Active predictions
        pred_result = get_active_predictions()
        preds = pred_result.get("predictions", [])
        if preds:
            lines.append("")
            lines.append(f"Predictions: {len(preds)}")
            for p in preds[:3]:
                topics = ", ".join(p.get("converging_topics", [])[:3])
                lines.append(f"  [{p.get('type')}] {p.get('pane_a')} <-> {p.get('pane_b')}: {topics}")

        # Active claims
        claims_result = get_active_claims()
        claims = claims_result.get("claims", [])
        if claims:
            lines.append("")
            lines.append(f"Active claims: {len(claims)}")
            for c in claims[:5]:
                contested = " [CONTESTED]" if c.get("contested") else ""
                lines.append(f"  {c['resource']} — {c['holder']}{contested}")

        lines.append("")
        lines.append("=" * 50)

        print("\n".join(lines))

    except Exception as e:
        print(f"[pane-awareness] session_start error: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
