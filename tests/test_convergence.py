"""Tests for convergence prediction engine."""

from datetime import datetime, timezone

from pane_awareness.convergence import (
    detect_opportunities,
    get_active_predictions,
    predict_convergence,
    resolve_predictions,
    store_prediction,
)


def _make_pane(
    quadrant, project, deepening=None, emerging=None,
    fading=None, stable=None, topics=None,
):
    now = datetime.now(timezone.utc).isoformat()
    return {
        "quadrant": quadrant,
        "project": project,
        "last_active": now,
        "key_topics": topics or (deepening or []) + (emerging or []),
        "trajectory_vector": {
            "deepening": deepening or [],
            "emerging": emerging or [],
            "fading": fading or [],
            "stable": stable or [],
        },
    }


def test_predict_convergence_mutual_deepening():
    panes = {
        "/dev/ttys001": _make_pane("top-left", "A", deepening=["supabase", "migration"]),
        "/dev/ttys002": _make_pane("top-right", "B", deepening=["supabase", "schema"]),
    }
    predictions = predict_convergence(panes)
    # Both deepening into "supabase" should produce a CONFLICT
    conflicts = [p for p in predictions if p["type"] == "CONFLICT"]
    assert len(conflicts) >= 1
    assert "supabase" in conflicts[0]["converging_topics"]


def test_predict_convergence_approaching():
    panes = {
        "/dev/ttys001": _make_pane("top-left", "A", deepening=["docker"]),
        "/dev/ttys002": _make_pane("top-right", "B", emerging=["docker"]),
    }
    predictions = predict_convergence(panes)
    assert len(predictions) >= 1
    assert predictions[0]["type"] == "APPROACHING"


def test_no_convergence_different_topics():
    panes = {
        "/dev/ttys001": _make_pane("top-left", "A", deepening=["supabase"]),
        "/dev/ttys002": _make_pane("top-right", "B", deepening=["react"]),
    }
    predictions = predict_convergence(panes)
    assert len(predictions) == 0


def test_detect_opportunities():
    panes = {
        "/dev/ttys001": _make_pane("top-left", "A", fading=["docker"], stable=["nginx"]),
        "/dev/ttys002": _make_pane("top-right", "B", deepening=["docker"], emerging=["nginx"]),
    }
    opps = detect_opportunities(panes)
    assert len(opps) >= 1
    assert opps[0]["type"] == "SYNERGY"


def test_store_and_get_predictions(temp_state_dir):
    pred = {
        "type": "CONFLICT",
        "pane_a_tty": "/dev/ttys001",
        "pane_b_tty": "/dev/ttys002",
        "converging_topics": ["supabase"],
        "confidence": 0.85,
    }
    store_prediction(pred)

    result = get_active_predictions()
    assert result["prediction_count"] == 1
    assert result["predictions"][0]["converging_topics"] == ["supabase"]


def test_store_prediction_dedup(temp_state_dir):
    pred = {
        "type": "CONFLICT",
        "pane_a_tty": "/dev/ttys001",
        "pane_b_tty": "/dev/ttys002",
        "converging_topics": ["docker"],
        "confidence": 0.7,
    }
    store_prediction(pred)
    store_prediction(pred)  # Duplicate

    result = get_active_predictions()
    assert result["prediction_count"] == 1
    assert result["predictions"][0]["refresh_count"] == 1


def test_resolve_predictions_empty(temp_state_dir):
    result = resolve_predictions()
    assert result["resolved_count"] == 0
