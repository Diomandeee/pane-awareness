"""Tests for cross-pollination orchestrator."""

from pane_awareness.cross_pollination import detect_cross_pollination


def test_cross_pollination_with_overlap(four_panes):
    result = detect_cross_pollination()
    assert "hints" in result
    assert "predictions" in result
    assert "opportunities" in result
    assert "trajectory_summary" in result


def test_cross_pollination_compat_mode(four_panes):
    # When include_predictions=False, returns just the hints list
    result = detect_cross_pollination(include_predictions=False)
    assert isinstance(result, list)


def test_cross_pollination_single_pane(temp_state_dir):
    from datetime import datetime, timezone

    from pane_awareness.state import write_registry

    now = datetime.now(timezone.utc).isoformat()
    write_registry({
        "panes": {
            "/dev/ttys001": {"last_active": now, "key_topics": ["foo"]},
        },
        "message_log": [],
    })

    result = detect_cross_pollination()
    assert result["hints"] == []
    assert result["predictions"] == []
