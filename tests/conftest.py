"""Shared fixtures for pane-awareness tests."""

from unittest.mock import patch

import pytest

from pane_awareness.config import GeneralConfig, PaneConfig, reset_config


@pytest.fixture(autouse=True)
def temp_state_dir(tmp_path):
    """Use a temporary state directory for every test."""
    state_dir = tmp_path / "state"
    state_dir.mkdir()

    cfg = PaneConfig(general=GeneralConfig(state_dir=str(state_dir)))

    with patch("pane_awareness.config.get_config", return_value=cfg):
        with patch("pane_awareness.state.get_config", return_value=cfg):
            yield state_dir

    reset_config()


@pytest.fixture
def fake_tty():
    """Return a fake TTY path and patch get_current_tty."""
    tty = "/dev/ttys099"
    with patch("pane_awareness._compat.get_current_tty", return_value=tty):
        with patch("pane_awareness.registry.get_current_tty", return_value=tty):
            with patch("pane_awareness.messages.get_current_tty", return_value=tty):
                with patch("pane_awareness.claims.get_current_tty", return_value=tty):
                    yield tty


@pytest.fixture
def four_panes(temp_state_dir):
    """Set up 4 fake panes in the registry."""
    from datetime import datetime, timezone

    from pane_awareness.state import write_registry

    now = datetime.now(timezone.utc).isoformat()
    panes = {}
    configs = [
        ("/dev/ttys001", "top-left", "project-alpha", ["supabase", "migration", "schema"]),
        ("/dev/ttys002", "top-right", "project-beta", ["docker", "deploy", "nginx"]),
        ("/dev/ttys003", "bottom-left", "project-gamma", ["swift", "xcode", "camera"]),
        ("/dev/ttys004", "bottom-right", "project-delta", ["react", "dashboard", "api"]),
    ]
    for tty, quadrant, project, topics in configs:
        panes[tty] = {
            "tty": tty,
            "pid": 1000,
            "session_id": f"session-{quadrant}",
            "quadrant": quadrant,
            "project": project,
            "cwd": f"/home/user/{project}",
            "last_prompt": f"working on {topics[0]}",
            "last_active": now,
            "created": now,
            "messages": [],
            "read_messages": [],
            "key_topics": topics,
            "topic_trajectory": [
                {"topics": topics[:2], "ts": now, "hash": "abc123"},
                {"topics": topics[1:], "ts": now, "hash": "def456"},
                {"topics": topics, "ts": now, "hash": "ghi789"},
            ],
            "trajectory_vector": {
                "deepening": [topics[0]],
                "emerging": [topics[-1]],
                "fading": [],
                "stable": topics[1:-1],
            },
        }

    write_registry({"panes": panes, "message_log": [], "last_updated": now})
    return panes
