#!/usr/bin/env python3
"""Simulate converging panes to trigger convergence predictions.

Creates fake pane states with overlapping topics to demonstrate
the prediction engine.
"""

import pane_awareness as pa
from pane_awareness._compat import get_current_tty
from pane_awareness.state import read_registry, write_registry
from datetime import datetime, timezone


def _simulate_pane(tty: str, project: str, prompts: list[str]):
    """Simulate a pane by writing its state directly to the registry."""
    from pane_awareness.topics import extract_topics, compute_trajectory_vector

    registry = read_registry()
    if "panes" not in registry:
        registry["panes"] = {}

    # Build trajectory window from prompts
    trajectory_window = []
    for prompt in prompts:
        topics = extract_topics(prompt)
        trajectory_window.append({"topics": topics, "hash": str(hash(prompt))})

    all_topics = []
    for entry in trajectory_window:
        all_topics.extend(entry["topics"])
    # Deduplicate, keep order
    key_topics = list(dict.fromkeys(all_topics))[:10]

    trajectory_vector = compute_trajectory_vector(trajectory_window)

    now = datetime.now(timezone.utc).isoformat()
    registry["panes"][tty] = {
        "session_id": f"sim-{project}",
        "tty": tty,
        "cwd": f"/projects/{project}",
        "project": project,
        "quadrant": None,
        "last_prompt": prompts[-1] if prompts else "",
        "prompt_count": len(prompts),
        "key_topics": key_topics,
        "trajectory_window": trajectory_window,
        "trajectory_vector": trajectory_vector,
        "created": now,
        "last_active": now,
    }

    write_registry(registry)
    print(f"  Registered {tty} ({project})")
    print(f"    Topics: {', '.join(key_topics)}")
    print(f"    Trajectory: {trajectory_vector}")


def main():
    print("=== Simulating Converging Panes ===\n")

    # Pane A: working on authentication
    print("Pane A (auth-service):")
    _simulate_pane("/dev/ttys100", "auth-service", [
        "implement JWT token generation",
        "add token refresh endpoint",
        "fix JWT expiration handling",
        "add login rate limiting",
        "implement password reset flow",
    ])

    # Pane B: working on frontend, gradually moving toward auth
    print("\nPane B (frontend):")
    _simulate_pane("/dev/ttys101", "frontend", [
        "build the navigation component",
        "add form validation utilities",
        "implement the login page UI",
        "connect login form to auth API",
        "handle JWT token storage in frontend",
    ])

    # Run cross-pollination to detect the convergence
    print("\n=== Cross-Pollination Analysis ===\n")
    result = pa.detect_cross_pollination()

    # Show overlap
    for pair in result.get("overlap", []):
        pane_a = pair.get("pane_a", "?")
        pane_b = pair.get("pane_b", "?")
        shared = pair.get("shared_topics", [])
        score = pair.get("score", 0)
        print(f"  {pane_a} <> {pane_b}")
        print(f"    Shared topics: {', '.join(shared)}")
        print(f"    Overlap score: {score:.0%}")

    # Show predictions
    predictions = result.get("predictions", [])
    if predictions:
        print(f"\n  Convergence Predictions: {len(predictions)}")
        for pred in predictions:
            print(f"    [{pred.get('type')}] confidence={pred.get('confidence', 0):.0%}")
            print(f"    {pred.get('recommendation', '')}")
    else:
        print("\n  No convergence predictions triggered.")

    # Show opportunities
    opportunities = result.get("opportunities", [])
    if opportunities:
        print(f"\n  Synergy Opportunities: {len(opportunities)}")
        for opp in opportunities:
            print(f"    [{opp.get('type')}] {opp.get('description', '')}")

    # Clean up simulated panes
    print("\n=== Cleanup ===")
    registry = read_registry()
    for tty in ["/dev/ttys100", "/dev/ttys101"]:
        registry.get("panes", {}).pop(tty, None)
    write_registry(registry)
    print("  Removed simulated panes.")


if __name__ == "__main__":
    main()
