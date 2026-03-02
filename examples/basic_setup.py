#!/usr/bin/env python3
"""Basic pane-awareness setup: register a pane and read others.

Run this in two or more terminals to see cross-pane awareness.
"""

import pane_awareness as pa


def main():
    # Register this pane with some context
    pa.update_pane(
        session_id="demo-session-1",
        cwd="/home/user/my-project",
        prompt_text="implement the user authentication flow with JWT tokens",
    )
    print("Pane registered.")

    # See all active panes
    panes = pa.get_all_panes()
    print(f"\nActive panes: {len(panes)}")
    for tty, pane in panes.items():
        quadrant = pane.get("quadrant", "?")
        project = pane.get("project", "?")
        topics = pane.get("key_topics", [])
        trajectory = pane.get("trajectory_vector", {})
        print(f"  [{quadrant}] {project}")
        print(f"    Topics: {', '.join(topics)}")
        if trajectory:
            for direction, items in trajectory.items():
                if items:
                    print(f"    {direction}: {', '.join(items)}")

    # Check for unread messages
    messages = pa.get_messages()
    if messages:
        print(f"\nUnread messages: {len(messages)}")
        for msg in messages:
            print(f"  From {msg.get('from', '?')}: {msg.get('message', '')}")
    else:
        print("\nNo unread messages.")

    # Check active predictions
    predictions = pa.get_active_predictions()
    if predictions:
        print(f"\nActive predictions: {len(predictions)}")
        for pred in predictions:
            ptype = pred.get("type", "?")
            topics = pred.get("shared_topics", [])
            conf = pred.get("confidence", 0)
            print(f"  [{ptype}] {', '.join(topics)} (confidence: {conf:.0%})")


if __name__ == "__main__":
    main()
