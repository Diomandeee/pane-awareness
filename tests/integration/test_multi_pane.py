"""Integration test: simulates a 4-pane session with messages, claims, predictions."""

from unittest.mock import patch

from pane_awareness.claims import claim_resource, get_active_claims, release_resource
from pane_awareness.cross_pollination import detect_cross_pollination
from pane_awareness.messages import get_messages, send_ack, send_handoff, send_message
from pane_awareness.registry import get_all_panes, update_pane


def test_full_4_pane_scenario(temp_state_dir):
    """Simulate 4 Claude Code sessions working in parallel."""
    ttys = ["/dev/ttys001", "/dev/ttys002", "/dev/ttys003", "/dev/ttys004"]

    # Phase 1: Register all 4 panes
    for i, tty in enumerate(ttys):
        with patch("pane_awareness.registry.get_current_tty", return_value=tty):
            with patch("pane_awareness.quadrant.detect_quadrant", return_value=None):
                update_pane(f"session-{i}", f"/project-{i}", f"working on task {i}")

    panes = get_all_panes()
    assert len(panes) == 4

    # Phase 2: Pane 1 claims a resource
    with patch("pane_awareness.claims.get_current_tty", return_value=ttys[0]):
        with patch("pane_awareness.messages.get_current_tty", return_value=ttys[0]):
            result = claim_resource("file:database.sql", reason="writing migration")
    assert result["granted"] is True

    claims = get_active_claims()
    assert claims["claim_count"] == 1

    # Phase 3: Pane 1 sends a message to pane 2
    with patch("pane_awareness.messages.get_current_tty", return_value=ttys[0]):
        send_message(ttys[1], "I'm working on the DB migration, FYI")

    with patch("pane_awareness.messages.get_current_tty", return_value=ttys[1]):
        msgs = get_messages()
    assert len(msgs) == 2  # 1 claim broadcast + 1 direct message

    # Phase 4: Pane 1 hands off to pane 2
    with patch("pane_awareness.messages.get_current_tty", return_value=ttys[0]):
        result = send_handoff(
            target=ttys[1],
            task="Continue DB migration",
            context_blob={"files": ["001.sql"], "project": "mydb"},
            next_steps=["run migrate", "verify"],
        )
    assert result["msg_type"] == "handoff"

    # Phase 5: Pane 2 acknowledges
    with patch("pane_awareness.messages.get_current_tty", return_value=ttys[1]):
        msgs = get_messages()  # Read handoff message
    assert any(m["msg_type"] == "handoff" for m in msgs)

    with patch("pane_awareness.messages.get_current_tty", return_value=ttys[1]):
        send_ack(target=ttys[0], ref_id=result["message_id"], accepted=True, reason="on it")

    # Phase 6: Pane 1 releases the resource
    with patch("pane_awareness.claims.get_current_tty", return_value=ttys[0]):
        with patch("pane_awareness.messages.get_current_tty", return_value=ttys[0]):
            rel = release_resource("file:database.sql")
    assert rel["released"] is True

    # Phase 7: Run cross-pollination
    result = detect_cross_pollination()
    assert "hints" in result
    assert "predictions" in result

    # Phase 8: Verify final state
    final_claims = get_active_claims()
    assert final_claims["claim_count"] == 0

    final_panes = get_all_panes()
    assert len(final_panes) == 4
