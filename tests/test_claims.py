"""Tests for resource claiming lifecycle."""

from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from pane_awareness.claims import (
    claim_resource,
    contest_claim,
    force_release,
    get_active_claims,
    get_claims_log,
    release_resource,
)


def test_claim_and_release(four_panes):
    tty = "/dev/ttys001"
    with patch("pane_awareness.claims.get_current_tty", return_value=tty):
        with patch("pane_awareness.messages.get_current_tty", return_value=tty):
            result = claim_resource("file:src/main.py", reason="editing")

    assert result["granted"] is True
    assert result["resource"] == "file:src/main.py"

    claims = get_active_claims()
    assert claims["claim_count"] == 1

    with patch("pane_awareness.claims.get_current_tty", return_value=tty):
        with patch("pane_awareness.messages.get_current_tty", return_value=tty):
            rel = release_resource("file:src/main.py")
    assert rel["released"] is True

    claims = get_active_claims()
    assert claims["claim_count"] == 0


def test_claim_denied_by_live_holder(four_panes):
    holder = "/dev/ttys001"
    contender = "/dev/ttys002"

    with patch("pane_awareness.claims.get_current_tty", return_value=holder):
        with patch("pane_awareness.messages.get_current_tty", return_value=holder):
            claim_resource("port:8001", reason="running server")

    with patch("pane_awareness.claims.get_current_tty", return_value=contender):
        with patch("pane_awareness.messages.get_current_tty", return_value=contender):
            result = claim_resource("port:8001", reason="need it")

    assert result["granted"] is False
    assert "held_by" in result


def test_claim_refresh(four_panes):
    tty = "/dev/ttys001"
    with patch("pane_awareness.claims.get_current_tty", return_value=tty):
        with patch("pane_awareness.messages.get_current_tty", return_value=tty):
            claim_resource("port:3000", reason="dev server")
            result = claim_resource("port:3000", reason="still using it")

    assert result["granted"] is True
    assert result.get("refreshed") is True


def test_contest_and_force_release(four_panes):
    holder = "/dev/ttys001"
    contester = "/dev/ttys002"

    with patch("pane_awareness.claims.get_current_tty", return_value=holder):
        with patch("pane_awareness.messages.get_current_tty", return_value=holder):
            claim_resource("deploy:staging", reason="deploying")

    with patch("pane_awareness.claims.get_current_tty", return_value=contester):
        with patch("pane_awareness.messages.get_current_tty", return_value=contester):
            result = contest_claim("deploy:staging", reason="urgent hotfix")

    assert result["contested"] is True

    # Force release before timeout should fail
    with patch("pane_awareness.claims.get_current_tty", return_value=contester):
        with patch("pane_awareness.messages.get_current_tty", return_value=contester):
            result = force_release("deploy:staging")
    assert result["released"] is False

    # Simulate timeout by backdating contested_at
    from pane_awareness.state import read_claims, write_claims
    data = read_claims()
    claim = data["active_claims"]["deploy:staging"]
    old_time = (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat()
    claim["contested_at"] = old_time
    write_claims(data)

    with patch("pane_awareness.claims.get_current_tty", return_value=contester):
        with patch("pane_awareness.messages.get_current_tty", return_value=contester):
            result = force_release("deploy:staging")
    assert result["released"] is True


def test_release_by_non_holder_denied(four_panes):
    holder = "/dev/ttys001"
    other = "/dev/ttys002"

    with patch("pane_awareness.claims.get_current_tty", return_value=holder):
        with patch("pane_awareness.messages.get_current_tty", return_value=holder):
            claim_resource("file:config.json", reason="editing")

    with patch("pane_awareness.claims.get_current_tty", return_value=other):
        with patch("pane_awareness.messages.get_current_tty", return_value=other):
            result = release_resource("file:config.json")

    assert result["released"] is False


def test_claims_log(four_panes):
    tty = "/dev/ttys001"
    with patch("pane_awareness.claims.get_current_tty", return_value=tty):
        with patch("pane_awareness.messages.get_current_tty", return_value=tty):
            claim_resource("port:9000", reason="test")
            release_resource("port:9000")

    log = get_claims_log()
    assert len(log) >= 2
    events = [e["event"] for e in log]
    assert "claim" in events
    assert "release" in events
