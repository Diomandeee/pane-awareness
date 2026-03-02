"""CLI entry point — `pa status`, `pa send`, `pa claim`, etc.

Usage:
    pa status              Show active panes and their state
    pa send TARGET MSG     Send a message to a pane
    pa messages            Read messages for current pane
    pa claim RESOURCE      Claim a resource
    pa release RESOURCE    Release a resource
    pa claims              Show active claims
    pa predictions         Show active predictions
    pa pollination         Run cross-pollination analysis
    pa install --claude-code  Install Claude Code hooks
"""

import argparse
import json
import sys
from typing import Optional


def cmd_status(args: argparse.Namespace) -> None:
    """Show active panes."""
    from . import get_all_panes
    panes = get_all_panes(include_stale=args.all)

    if not panes:
        print("No active panes.")
        return

    for tty, pane in panes.items():
        quadrant = pane.get("quadrant", "?")
        project = pane.get("project", "?")
        topics = ", ".join(pane.get("key_topics", [])[:5])
        last = pane.get("last_active", "?")[:19]
        print(f"  [{quadrant}] {project} ({tty})")
        print(f"    Topics: {topics or 'none'}")
        print(f"    Active: {last}")

        vec = pane.get("trajectory_vector", {})
        if vec:
            deep = ", ".join(vec.get("deepening", []))
            emerge = ", ".join(vec.get("emerging", []))
            if deep:
                print(f"    Deepening: {deep}")
            if emerge:
                print(f"    Emerging: {emerge}")
        print()


def cmd_send(args: argparse.Namespace) -> None:
    """Send a message."""
    from . import send_message
    result = send_message(
        target=args.target,
        message=args.message,
        priority=args.priority or "normal",
        msg_type=args.type or "info",
    )
    print(f"Sent to {result['sent_count']} pane(s). ID: {result['message_id']}")


def cmd_messages(args: argparse.Namespace) -> None:
    """Read messages."""
    from . import get_messages
    msgs = get_messages()
    if not msgs:
        print("No new messages.")
        return

    for msg in msgs:
        ts = msg.get("timestamp", "?")[:19]
        sender = msg.get("from", "?")
        mtype = msg.get("msg_type", "info")
        text = msg.get("message", "")
        priority = msg.get("priority", "normal")
        prefix = "!" if priority == "urgent" else " "
        print(f"  {prefix}[{mtype}] from {sender} at {ts}")
        print(f"    {text}")
        print()


def cmd_claim(args: argparse.Namespace) -> None:
    """Claim a resource."""
    from . import claim_resource
    result = claim_resource(
        resource=args.resource,
        scope=args.scope or "exclusive",
        reason=args.reason or "",
    )
    print(result["message"])


def cmd_release(args: argparse.Namespace) -> None:
    """Release a resource."""
    from . import release_resource
    result = release_resource(resource=args.resource)
    print(result["message"])


def cmd_claims(args: argparse.Namespace) -> None:
    """Show active claims."""
    from . import get_active_claims
    result = get_active_claims()
    claims = result.get("claims", [])
    if not claims:
        print("No active claims.")
        return

    for c in claims:
        contested = " [CONTESTED]" if c.get("contested") else ""
        print(f"  {c['resource']} — held by {c['holder']}{contested}")
        if c.get("reason"):
            print(f"    Reason: {c['reason']}")
    print(f"\n  Total: {result['claim_count']}")


def cmd_predictions(args: argparse.Namespace) -> None:
    """Show active predictions."""
    from . import get_active_predictions
    result = get_active_predictions()
    preds = result.get("predictions", [])

    if not preds:
        print("No active predictions.")
    else:
        for p in preds:
            topics = ", ".join(p.get("converging_topics", []))
            print(f"  [{p.get('type')}] {p.get('pane_a')} <-> {p.get('pane_b')}")
            print(f"    Topics: {topics}")
            print(f"    Confidence: {p.get('confidence', 0):.0%}")
            print()

    acc = result.get("accuracy", {})
    if acc:
        total = result.get("total_resolved", 0)
        print(f"  Accuracy: {acc.get('prevented', 0)} prevented, "
              f"{acc.get('occurred', 0)} occurred, "
              f"{acc.get('false_positive', 0)} FP "
              f"(total: {total})")


def cmd_pollination(args: argparse.Namespace) -> None:
    """Run cross-pollination analysis."""
    from . import detect_cross_pollination
    result = detect_cross_pollination()

    hints = result.get("hints", [])
    preds = result.get("predictions", [])
    opps = result.get("opportunities", [])

    if hints:
        print("Cross-pollination hints:")
        for h in hints:
            topics = ", ".join(h["shared_topics"][:5])
            print(f"  {h['pane_a']} <-> {h['pane_b']}: [{topics}] (score: {h['score']})")
        print()

    if preds:
        print("Convergence predictions:")
        for p in preds:
            topics = ", ".join(p.get("converging_topics", []))
            print(f"  [{p['type']}] {p['pane_a']} <-> {p['pane_b']}: [{topics}]")
        print()

    if opps:
        print("Synergy opportunities:")
        for o in opps:
            topics = ", ".join(o.get("synergy_topics", []))
            print(f"  {o['pane_a']} <-> {o['pane_b']}: [{topics}]")
        print()

    if not hints and not preds and not opps:
        print("No cross-pane signals detected.")


def cmd_install(args: argparse.Namespace) -> None:
    """Install hooks for AI assistants."""
    if args.claude_code:
        _install_claude_code()
    else:
        print("Specify --claude-code to install Claude Code hooks.")


def _install_claude_code() -> None:
    """Install Claude Code hooks."""
    from pathlib import Path

    hooks_src = Path(__file__).parent.parent.parent / "hooks" / "claude_code"
    settings_path = Path.home() / ".claude" / "settings.json"

    if not hooks_src.exists():
        # Try installed package location
        print("Hook installation from installed package not yet supported.")
        print("Copy hooks/claude_code/ to your hooks directory manually.")
        return

    print(f"Hook source: {hooks_src}")
    print(f"Settings: {settings_path}")

    # Read existing settings
    settings: dict = {}
    if settings_path.exists():
        settings = json.loads(settings_path.read_text())

    hooks = settings.setdefault("hooks", {})

    # Add UserPromptSubmit hook
    prompt_hooks = hooks.setdefault("UserPromptSubmit", [])
    pa_prompt = {
        "type": "command",
        "command": f"{sys.executable} {hooks_src / 'prompt_hook.py'}",
    }
    if not any("prompt_hook.py" in str(h.get("command", "")) for h in prompt_hooks):
        prompt_hooks.append(pa_prompt)
        print("  Added UserPromptSubmit hook")

    # Add SessionStart hook
    session_hooks = hooks.setdefault("SessionStart", [])
    pa_session = {
        "type": "command",
        "command": f"{sys.executable} {hooks_src / 'session_start_hook.py'}",
    }
    if not any("session_start_hook.py" in str(h.get("command", "")) for h in session_hooks):
        session_hooks.append(pa_session)
        print("  Added SessionStart hook")

    settings["hooks"] = hooks
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text(json.dumps(settings, indent=2))
    print(f"Settings updated: {settings_path}")
    print("\nRestart Claude Code to activate pane awareness.")


def main(argv: Optional[list] = None) -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="pa",
        description="Pane Awareness — cross-session coordination for AI coding assistants.",
    )
    sub = parser.add_subparsers(dest="command")

    # status
    p_status = sub.add_parser("status", help="Show active panes")
    p_status.add_argument("--all", action="store_true", help="Include stale panes")

    # send
    p_send = sub.add_parser("send", help="Send a message")
    p_send.add_argument("target", help="Target pane (TTY, quadrant, or 'all')")
    p_send.add_argument("message", help="Message text")
    p_send.add_argument("--priority", choices=["normal", "urgent"], default="normal")
    p_send.add_argument(
        "--type",
        choices=["info", "question", "claim", "release",
                 "delegate", "handoff", "ack", "block"],
        default="info",
    )

    # messages
    sub.add_parser("messages", help="Read incoming messages")

    # claim
    p_claim = sub.add_parser("claim", help="Claim a resource")
    p_claim.add_argument("resource", help="Resource to claim (e.g. file:src/main.py)")
    p_claim.add_argument("--scope", choices=["exclusive", "shared"], default="exclusive")
    p_claim.add_argument("--reason", default="")

    # release
    p_release = sub.add_parser("release", help="Release a resource")
    p_release.add_argument("resource", help="Resource to release")

    # claims
    sub.add_parser("claims", help="Show active claims")

    # predictions
    sub.add_parser("predictions", help="Show active predictions")

    # pollination
    sub.add_parser("pollination", help="Run cross-pollination analysis")

    # install
    p_install = sub.add_parser("install", help="Install hooks")
    p_install.add_argument("--claude-code", action="store_true", help="Install Claude Code hooks")

    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return

    commands = {
        "status": cmd_status,
        "send": cmd_send,
        "messages": cmd_messages,
        "claim": cmd_claim,
        "release": cmd_release,
        "claims": cmd_claims,
        "predictions": cmd_predictions,
        "pollination": cmd_pollination,
        "install": cmd_install,
    }

    handler = commands.get(args.command)
    if handler:
        handler(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
