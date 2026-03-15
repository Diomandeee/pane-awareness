#!/usr/bin/env python3
"""MCP server for pane-awareness — 20 tools for cross-session coordination.

Run with: python -m mcp.server
Or: pa mcp serve

Requires: pip install mcp
"""

import json
import os
import sys

# Add pane-awareness src to path
_HERE = os.path.dirname(os.path.abspath(__file__))
_SRC = os.path.join(_HERE, "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, _SRC)

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
except ImportError:
    print("MCP server requires the 'mcp' package: pip install mcp", file=sys.stderr)
    sys.exit(1)

server = Server("pane-awareness")


def _result(data) -> list:
    """Format a result as MCP TextContent."""
    return [TextContent(type="text", text=json.dumps(data, indent=2, default=str))]


@server.list_tools()
async def list_tools():
    return [
        Tool(name="pane_status", description="Show all active panes with topics and trajectory", inputSchema={"type": "object", "properties": {"include_stale": {"type": "boolean", "default": False}}}),
        Tool(name="pane_info", description="Get info for a specific pane by TTY", inputSchema={"type": "object", "properties": {"tty": {"type": "string"}}}),
        Tool(name="send_pane_message", description="Send a message to another pane", inputSchema={"type": "object", "properties": {"target": {"type": "string"}, "message": {"type": "string"}, "priority": {"type": "string", "default": "normal"}, "msg_type": {"type": "string", "default": "info"}}, "required": ["target", "message"]}),
        Tool(name="get_pane_messages", description="Read messages from current pane's inbox", inputSchema={"type": "object", "properties": {}}),
        Tool(name="pane_message_log", description="Read the global message audit log", inputSchema={"type": "object", "properties": {"limit": {"type": "integer", "default": 50}}}),
        Tool(name="claim_resource", description="Claim a shared resource", inputSchema={"type": "object", "properties": {"resource": {"type": "string"}, "scope": {"type": "string", "default": "exclusive"}, "reason": {"type": "string", "default": ""}}, "required": ["resource"]}),
        Tool(name="release_resource", description="Release a claimed resource", inputSchema={"type": "object", "properties": {"resource": {"type": "string"}}, "required": ["resource"]}),
        Tool(name="contest_claim", description="Contest a claim held by another pane", inputSchema={"type": "object", "properties": {"resource": {"type": "string"}, "reason": {"type": "string", "default": ""}}, "required": ["resource"]}),
        Tool(name="force_release", description="Force-release a contested claim after timeout", inputSchema={"type": "object", "properties": {"resource": {"type": "string"}, "reason": {"type": "string", "default": ""}}, "required": ["resource"]}),
        Tool(name="active_claims", description="Show all active resource claims", inputSchema={"type": "object", "properties": {}}),
        Tool(name="claims_log", description="Read the claims history log", inputSchema={"type": "object", "properties": {"limit": {"type": "integer", "default": 50}}}),
        Tool(name="cross_pollination", description="Analyze keyword overlap and convergence across panes", inputSchema={"type": "object", "properties": {}}),
        Tool(name="active_predictions", description="Get active convergence predictions", inputSchema={"type": "object", "properties": {}}),
        Tool(name="resolve_predictions", description="Resolve active predictions against current state", inputSchema={"type": "object", "properties": {}}),
        Tool(name="handoff_context", description="Build a handoff context blob for the current pane", inputSchema={"type": "object", "properties": {"tier2_fields": {"type": "object"}}}),
        Tool(name="suggest_delegations", description="Get delegation suggestions based on trajectory", inputSchema={"type": "object", "properties": {}}),
        Tool(name="set_pane_quadrant", description="Set the quadrant label for current pane", inputSchema={"type": "object", "properties": {"quadrant": {"type": "string"}}, "required": ["quadrant"]}),
        Tool(name="detect_quadrant", description="Auto-detect and set quadrant from window position", inputSchema={"type": "object", "properties": {}}),
        Tool(name="domain_map", description="Get the effective domain map (configured + learned)", inputSchema={"type": "object", "properties": {}}),
        Tool(name="send_handoff", description="Send a structured handoff to another pane", inputSchema={"type": "object", "properties": {"target": {"type": "string"}, "task": {"type": "string"}, "context_blob": {"type": "object"}, "next_steps": {"type": "array", "items": {"type": "string"}}}, "required": ["target", "task"]}),
        Tool(name="spawn_panes", description="Spawn N new Terminal windows with Claude Code + injected prompts. Each directive becomes a new session with `claude -p`.", inputSchema={
            "type": "object",
            "properties": {
                "directives": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "prompt": {"type": "string", "description": "The task/prompt to inject into the new Claude session"},
                            "project_path": {"type": "string", "description": "Working directory for the new session (default: ~)"},
                            "title": {"type": "string", "description": "Window title for the new terminal"},
                        },
                        "required": ["prompt"],
                    },
                    "description": "List of directives to spawn (max 10)",
                },
                "enrich": {"type": "boolean", "default": False, "description": "Enrich prompts with AGENTS.md, RAG++, CIA context"},
                "stagger_seconds": {"type": "number", "default": 1.5, "description": "Delay between spawns"},
                "dangerously_skip_permissions": {"type": "boolean", "default": False, "description": "Run spawned sessions with --dangerously-skip-permissions"},
            },
            "required": ["directives"],
        }),
        Tool(name="pending_spawns", description="List pending (unclaimed) spawn records", inputSchema={"type": "object", "properties": {}}),
        Tool(name="spawn_status", description="Show all spawn records with status (pending/claimed/completed/stalled)", inputSchema={"type": "object", "properties": {"since_hours": {"type": "number", "default": 24, "description": "Only show spawns from the last N hours"}}}),
        Tool(name="spawn_continue", description="Manually trigger continuation for a completed spawn", inputSchema={"type": "object", "properties": {"spawn_id": {"type": "string", "description": "The spawn ID to continue"}}, "required": ["spawn_id"]}),
        Tool(name="mesh_load", description="Show pane counts and Claude process counts across all mesh machines", inputSchema={"type": "object", "properties": {}}),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict):
    import pane_awareness as pa

    if name == "pane_status":
        panes = pa.get_all_panes(include_stale=arguments.get("include_stale", False))
        summary = {}
        for tty, pane in panes.items():
            summary[tty] = {
                "quadrant": pane.get("quadrant"),
                "project": pane.get("project"),
                "key_topics": pane.get("key_topics", []),
                "last_prompt": pane.get("last_prompt", "")[:100],
                "last_active": pane.get("last_active"),
                "trajectory_vector": pane.get("trajectory_vector", {}),
            }
        return _result(summary)

    elif name == "pane_info":
        info = pa.get_pane_info(tty=arguments.get("tty"))
        return _result(info or {"error": "Pane not found"})

    elif name == "send_pane_message":
        result = pa.send_message(
            target=arguments["target"],
            message=arguments["message"],
            priority=arguments.get("priority", "normal"),
            msg_type=arguments.get("msg_type", "info"),
        )
        return _result(result)

    elif name == "get_pane_messages":
        return _result(pa.get_messages())

    elif name == "pane_message_log":
        return _result(pa.get_message_log(limit=arguments.get("limit", 50)))

    elif name == "claim_resource":
        result = pa.claim_resource(
            resource=arguments["resource"],
            scope=arguments.get("scope", "exclusive"),
            reason=arguments.get("reason", ""),
        )
        return _result(result)

    elif name == "release_resource":
        return _result(pa.release_resource(resource=arguments["resource"]))

    elif name == "contest_claim":
        return _result(pa.contest_claim(
            resource=arguments["resource"],
            reason=arguments.get("reason", ""),
        ))

    elif name == "force_release":
        return _result(pa.force_release(
            resource=arguments["resource"],
            reason=arguments.get("reason", ""),
        ))

    elif name == "active_claims":
        return _result(pa.get_active_claims())

    elif name == "claims_log":
        return _result(pa.get_claims_log(limit=arguments.get("limit", 50)))

    elif name == "cross_pollination":
        return _result(pa.detect_cross_pollination())

    elif name == "active_predictions":
        return _result(pa.get_active_predictions())

    elif name == "resolve_predictions":
        return _result(pa.resolve_predictions())

    elif name == "handoff_context":
        return _result(pa.build_handoff_context(
            tier2_fields=arguments.get("tier2_fields"),
        ))

    elif name == "suggest_delegations":
        return _result(pa.suggest_delegations())

    elif name == "set_pane_quadrant":
        result = pa.set_quadrant(quadrant=arguments["quadrant"])
        return _result({"success": result})

    elif name == "detect_quadrant":
        q = pa.auto_detect_and_set_quadrant()
        return _result({"quadrant": q})

    elif name == "domain_map":
        dm = pa.get_effective_domain_map()
        return _result({k: sorted(v) for k, v in dm.items()})

    elif name == "send_handoff":
        return _result(pa.send_handoff(
            target=arguments["target"],
            task=arguments["task"],
            context_blob=arguments.get("context_blob", {}),
            next_steps=arguments.get("next_steps"),
        ))

    elif name == "spawn_panes":
        # Import pane_spawner from prompt-logger hooks
        _spawner_dir = os.path.join(
            os.path.expanduser("~"), ".claude", "hooks", "prompt-logger"
        )
        if _spawner_dir not in sys.path:
            sys.path.insert(0, _spawner_dir)
        from pane_spawner import spawn_panes as _do_spawn
        result = _do_spawn(
            directives=arguments.get("directives", []),
            enrich=arguments.get("enrich", False),
            stagger_seconds=arguments.get("stagger_seconds", 1.5),
            dangerously_skip_permissions=arguments.get("dangerously_skip_permissions", False),
        )
        return _result(result)

    elif name == "pending_spawns":
        _spawner_dir = os.path.join(
            os.path.expanduser("~"), ".claude", "hooks", "prompt-logger"
        )
        if _spawner_dir not in sys.path:
            sys.path.insert(0, _spawner_dir)
        from pane_spawner import get_pending_spawns
        return _result(get_pending_spawns())

    elif name == "spawn_status":
        _spawner_dir = os.path.join(
            os.path.expanduser("~"), ".claude", "hooks", "prompt-logger"
        )
        if _spawner_dir not in sys.path:
            sys.path.insert(0, _spawner_dir)
        from pane_spawner import get_all_spawn_records
        from datetime import datetime, timezone, timedelta
        since_hours = arguments.get("since_hours", 24)
        all_records = get_all_spawn_records()
        cutoff = datetime.now(timezone.utc) - timedelta(hours=since_hours)
        filtered = {}
        for sid, rec in all_records.items():
            spawned_at = rec.get("spawned_at", "")
            try:
                ts = datetime.fromisoformat(spawned_at.replace("Z", "+00:00"))
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
                if ts >= cutoff:
                    filtered[sid] = rec
            except (ValueError, TypeError):
                filtered[sid] = rec  # Include records with unparseable timestamps
        summary = {
            "total": len(filtered),
            "by_status": {},
            "records": filtered,
        }
        for rec in filtered.values():
            s = rec.get("status", "unknown")
            summary["by_status"][s] = summary["by_status"].get(s, 0) + 1
        return _result(summary)

    elif name == "spawn_continue":
        _spawner_dir = os.path.join(
            os.path.expanduser("~"), ".claude", "hooks", "prompt-logger"
        )
        if _spawner_dir not in sys.path:
            sys.path.insert(0, _spawner_dir)
        from pane_spawner import get_all_spawn_records, spawn_panes, mark_follow_up_dispatched
        spawn_id = arguments["spawn_id"]
        all_records = get_all_spawn_records()
        spawn = all_records.get(spawn_id)
        if not spawn:
            return _result({"error": f"Spawn {spawn_id} not found"})
        if spawn.get("status") != "completed":
            return _result({"error": f"Spawn {spawn_id} is not completed (status={spawn.get('status')})"})
        # Build continuation prompt
        prompt = (
            f"# Continuation: {spawn.get('title', 'Task')}\n\n"
            f"Continue the work from spawn {spawn_id}.\n"
            f"Original task: {spawn.get('prompt_preview', 'N/A')}\n"
            f"Files modified: {', '.join(spawn.get('files_modified', [])[:10])}\n\n"
            f"Review the current state and complete any remaining work."
        )
        result = spawn_panes(
            directives=[{
                "prompt": prompt,
                "title": f"Continue: {spawn.get('title', 'Task')}",
                "project_path": spawn.get("project_path", os.path.expanduser("~")),
            }],
            dangerously_skip_permissions=True,
            auto_distribute=True,
            parent_spawn_id=spawn_id,
        )
        mark_follow_up_dispatched(spawn_id)
        return _result(result)

    elif name == "mesh_load":
        _spawner_dir = os.path.join(
            os.path.expanduser("~"), ".claude", "hooks", "prompt-logger"
        )
        if _spawner_dir not in sys.path:
            sys.path.insert(0, _spawner_dir)
        from pane_spawner import _get_mesh_load, _pick_target_machine, LOCAL_PANE_THRESHOLD, MACHINE_ID
        loads = _get_mesh_load()
        local_load = loads.get(MACHINE_ID, 0)
        next_target = _pick_target_machine(local_load)
        return _result({
            "loads": loads,
            "local_machine": MACHINE_ID,
            "local_threshold": LOCAL_PANE_THRESHOLD,
            "next_spawn_target": next_target,
            "would_distribute": next_target != MACHINE_ID,
        })

    return _result({"error": f"Unknown tool: {name}"})


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
