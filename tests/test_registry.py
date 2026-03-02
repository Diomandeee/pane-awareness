"""Tests for pane registry operations."""

from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from pane_awareness.registry import (
    _is_stale,
    extract_project_name,
    get_all_panes,
    get_pane_info,
    set_quadrant,
    update_pane,
)


def test_is_stale_recent():
    now = datetime.now(timezone.utc).isoformat()
    assert _is_stale(now) is False


def test_is_stale_old():
    old = (datetime.now(timezone.utc) - timedelta(hours=3)).isoformat()
    assert _is_stale(old) is True


def test_is_stale_invalid():
    assert _is_stale("") is True
    assert _is_stale("not-a-date") is True


def test_extract_project_name_fallback():
    name = extract_project_name("/some/random/path/myproject")
    assert name == "myproject"


def test_extract_project_name_home_projects(tmp_path):
    proj_dir = tmp_path / "projects" / "cool-app" / "src"
    proj_dir.mkdir(parents=True)
    with patch("pane_awareness.registry.Path.home", return_value=tmp_path):
        name = extract_project_name(str(proj_dir))
    assert name == "cool-app"


def test_update_pane_and_get(temp_state_dir):
    tty = "/dev/ttys050"
    with patch("pane_awareness.registry.get_current_tty", return_value=tty):
        with patch("pane_awareness.quadrant.detect_quadrant", return_value=None):
            update_pane("sess-1", "/tmp/myproject", "fix the auth bug")

    panes = get_all_panes()
    assert tty in panes
    pane = panes[tty]
    assert pane["session_id"] == "sess-1"
    assert pane["project"] == "myproject"
    assert "auth" in pane["key_topics"]


def test_update_pane_trajectory_grows(temp_state_dir):
    tty = "/dev/ttys051"
    with patch("pane_awareness.registry.get_current_tty", return_value=tty):
        with patch("pane_awareness.quadrant.detect_quadrant", return_value=None):
            update_pane("s1", "/tmp/p", "working on supabase migrations")
            update_pane("s1", "/tmp/p", "now testing docker deployment")
            update_pane("s1", "/tmp/p", "checking nginx config")

    pane = get_all_panes()[tty]
    assert len(pane["topic_trajectory"]) == 3


def test_get_all_panes_filters_stale(temp_state_dir):
    from pane_awareness.state import write_registry
    old = (datetime.now(timezone.utc) - timedelta(hours=5)).isoformat()
    now = datetime.now(timezone.utc).isoformat()

    write_registry({
        "panes": {
            "/dev/ttys060": {"last_active": old, "tty": "/dev/ttys060"},
            "/dev/ttys061": {"last_active": now, "tty": "/dev/ttys061"},
        },
        "message_log": [],
    })

    panes = get_all_panes()
    assert "/dev/ttys061" in panes
    assert "/dev/ttys060" not in panes


def test_get_all_panes_include_stale(temp_state_dir):
    from pane_awareness.state import write_registry
    old = (datetime.now(timezone.utc) - timedelta(hours=5)).isoformat()

    write_registry({
        "panes": {
            "/dev/ttys070": {"last_active": old, "tty": "/dev/ttys070"},
        },
        "message_log": [],
    })

    panes = get_all_panes(include_stale=True)
    assert "/dev/ttys070" in panes


def test_set_quadrant(temp_state_dir):
    from pane_awareness.state import write_registry
    now = datetime.now(timezone.utc).isoformat()
    tty = "/dev/ttys080"

    write_registry({
        "panes": {tty: {"last_active": now, "tty": tty}},
        "message_log": [],
    })

    with patch("pane_awareness.registry.get_current_tty", return_value=tty):
        result = set_quadrant(quadrant="top-left")

    assert result is True
    pane = get_all_panes(include_stale=True)[tty]
    assert pane["quadrant"] == "top-left"


def test_get_pane_info(temp_state_dir):
    from pane_awareness.state import write_registry
    now = datetime.now(timezone.utc).isoformat()
    tty = "/dev/ttys090"

    write_registry({
        "panes": {tty: {"last_active": now, "tty": tty, "project": "testproj"}},
        "message_log": [],
    })

    info = get_pane_info(tty=tty)
    assert info is not None
    assert info["project"] == "testproj"
