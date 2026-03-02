#!/usr/bin/env python3
"""Full 4-pane simulation with messages, claims, and predictions.

Simulates a realistic scenario:
- 4 panes working on different aspects of a web application
- Cross-pane messaging
- Resource claiming and handoffs
- Convergence detection

No real terminal panes needed — everything is simulated via state files.
"""

import json
from datetime import datetime, timezone

import pane_awareness as pa
from pane_awareness.state import read_registry, write_registry
from pane_awareness.topics import extract_topics, compute_trajectory_vector


PANES = {
    "/dev/ttys200": {
        "project": "api-server",
        "quadrant": "top-left",
        "prompts": [
            "set up Express server with TypeScript",
            "add PostgreSQL database connection pool",
            "implement user registration endpoint",
            "add JWT authentication middleware",
            "fix the auth middleware token validation",
        ],
    },
    "/dev/ttys201": {
        "project": "frontend",
        "quadrant": "top-right",
        "prompts": [
            "create React project with Vite",
            "build the navigation sidebar component",
            "implement login page with form validation",
            "connect login form to backend auth API",
            "add JWT token storage and refresh logic",
        ],
    },
    "/dev/ttys202": {
        "project": "e2e-tests",
        "quadrant": "bottom-left",
        "prompts": [
            "set up Playwright test framework",
            "write test for homepage loading",
            "add user registration test flow",
            "test the authentication end-to-end",
            "fix flaky auth test timing issues",
        ],
    },
    "/dev/ttys203": {
        "project": "infrastructure",
        "quadrant": "bottom-right",
        "prompts": [
            "write Docker compose for dev environment",
            "configure nginx reverse proxy",
            "add database migration scripts",
            "set up CI/CD pipeline with GitHub Actions",
            "optimize database query performance",
        ],
    },
}


def simulate_panes():
    """Register all 4 simulated panes."""
    print("=== Registering 4 Simulated Panes ===\n")
    registry = read_registry()
    if "panes" not in registry:
        registry["panes"] = {}

    for tty, config in PANES.items():
        trajectory_window = []
        for prompt in config["prompts"]:
            topics = extract_topics(prompt)
            trajectory_window.append({"topics": topics, "hash": str(hash(prompt))})

        all_topics = []
        for entry in trajectory_window:
            all_topics.extend(entry["topics"])
        key_topics = list(dict.fromkeys(all_topics))[:10]
        trajectory_vector = compute_trajectory_vector(trajectory_window)

        now = datetime.now(timezone.utc).isoformat()
        registry["panes"][tty] = {
            "session_id": f"sim-{config['project']}",
            "tty": tty,
            "cwd": f"/projects/{config['project']}",
            "project": config["project"],
            "quadrant": config["quadrant"],
            "last_prompt": config["prompts"][-1],
            "prompt_count": len(config["prompts"]),
            "key_topics": key_topics,
            "trajectory_window": trajectory_window,
            "trajectory_vector": trajectory_vector,
            "created": now,
            "last_active": now,
        }
        print(f"  [{config['quadrant']}] {config['project']}")
        print(f"    Topics: {', '.join(key_topics[:5])}")
        print(f"    Deepening: {', '.join(trajectory_vector.get('deepening', []))}")
        print(f"    Emerging: {', '.join(trajectory_vector.get('emerging', []))}")

    write_registry(registry)


def simulate_claims():
    """Simulate resource claims."""
    print("\n=== Resource Claims ===\n")

    # API server claims the auth module
    from pane_awareness.claims import claim_resource
    from pane_awareness.state import read_claims, write_claims

    claims_data = read_claims()
    now = datetime.now(timezone.utc).isoformat()

    claims_data["claims"] = [
        {
            "resource": "file:src/auth/middleware.ts",
            "holder_tty": "/dev/ttys200",
            "holder_project": "api-server",
            "scope": "exclusive",
            "reason": "refactoring auth middleware",
            "claimed_at": now,
            "last_active": now,
            "contested_by": None,
            "contested_at": None,
        },
        {
            "resource": "file:src/components/LoginForm.tsx",
            "holder_tty": "/dev/ttys201",
            "holder_project": "frontend",
            "scope": "exclusive",
            "reason": "building login UI",
            "claimed_at": now,
            "last_active": now,
            "contested_by": None,
            "contested_at": None,
        },
    ]
    write_claims(claims_data)

    for claim in claims_data["claims"]:
        print(f"  {claim['resource']}")
        print(f"    Held by: {claim['holder_project']} ({claim['holder_tty']})")


def simulate_messages():
    """Send some cross-pane messages."""
    print("\n=== Cross-Pane Messages ===\n")

    registry = read_registry()
    if "message_log" not in registry:
        registry["message_log"] = []

    now = datetime.now(timezone.utc).isoformat()
    messages = [
        {
            "id": "msg_sim_001",
            "from": "/dev/ttys200",
            "target": "/dev/ttys201",
            "message": "Auth API is ready — POST /api/auth/login accepts {email, password}",
            "msg_type": "info",
            "priority": "normal",
            "timestamp": now,
        },
        {
            "id": "msg_sim_002",
            "from": "/dev/ttys201",
            "target": "/dev/ttys200",
            "message": "What format does the JWT payload use? Need it for the frontend token parser.",
            "msg_type": "question",
            "priority": "normal",
            "timestamp": now,
        },
        {
            "id": "msg_sim_003",
            "from": "/dev/ttys202",
            "target": "all",
            "message": "E2E tests for auth are passing. Don't break the login endpoint!",
            "msg_type": "info",
            "priority": "urgent",
            "timestamp": now,
        },
    ]

    registry["message_log"].extend(messages)
    write_registry(registry)

    for msg in messages:
        from_proj = PANES.get(msg["from"], {}).get("project", "?")
        target = msg["target"]
        if target in PANES:
            target = PANES[target].get("project", target)
        print(f"  {from_proj} -> {target}: {msg['message'][:60]}...")


def run_analysis():
    """Run cross-pollination analysis to find convergence."""
    print("\n=== Cross-Pollination Analysis ===\n")

    result = pa.detect_cross_pollination()

    # Overlap
    for pair in result.get("overlap", []):
        pane_a = pair.get("pane_a", "?")
        pane_b = pair.get("pane_b", "?")
        shared = pair.get("shared_topics", [])
        score = pair.get("score", 0)
        if shared:
            proj_a = PANES.get(pane_a, {}).get("project", pane_a)
            proj_b = PANES.get(pane_b, {}).get("project", pane_b)
            print(f"  {proj_a} <> {proj_b}")
            print(f"    Shared: {', '.join(shared)} (score: {score:.0%})")

    # Predictions
    predictions = result.get("predictions", [])
    if predictions:
        print(f"\n  Convergence Predictions: {len(predictions)}")
        for pred in predictions:
            ptype = pred.get("type", "?")
            conf = pred.get("confidence", 0)
            rec = pred.get("recommendation", "")
            print(f"    [{ptype}] confidence={conf:.0%}")
            print(f"    {rec}")

    # Delegation suggestions
    delegations = result.get("delegations", [])
    if delegations:
        print(f"\n  Delegation Suggestions: {len(delegations)}")
        for d in delegations:
            print(f"    [{d.get('type')}] {d.get('description', '')}")

    # Handoff opportunities
    handoffs = result.get("handoff_opportunities", [])
    if handoffs:
        print(f"\n  Handoff Opportunities: {len(handoffs)}")
        for h in handoffs:
            print(f"    {h.get('description', '')}")


def cleanup():
    """Remove simulated panes."""
    print("\n=== Cleanup ===\n")
    registry = read_registry()
    for tty in PANES:
        registry.get("panes", {}).pop(tty, None)
    # Remove simulated messages
    registry["message_log"] = [
        m for m in registry.get("message_log", [])
        if not m.get("id", "").startswith("msg_sim_")
    ]
    write_registry(registry)

    from pane_awareness.state import read_claims, write_claims
    claims_data = read_claims()
    claims_data["claims"] = [
        c for c in claims_data.get("claims", [])
        if c.get("holder_tty") not in PANES
    ]
    write_claims(claims_data)

    print("  Removed all simulated panes, messages, and claims.")


def main():
    simulate_panes()
    simulate_claims()
    simulate_messages()
    run_analysis()
    cleanup()

    print("\nDone! In a real setup, each pane would be a separate terminal session.")
    print("The hooks handle registration automatically — no manual calls needed.")


if __name__ == "__main__":
    main()
