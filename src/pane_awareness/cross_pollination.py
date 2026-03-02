"""Compound signal orchestrator — detects all cross-pane signals.

Combines keyword overlap, trajectory convergence, synergy opportunities,
claim conflicts, handoff opportunities, and delegation suggestions
into a single analysis result.
"""

from typing import Any, Dict, List

from ._compat import get_identity_noise
from .convergence import (
    detect_claim_conflicts,
    detect_opportunities,
    predict_convergence,
    resolve_predictions,
    store_prediction,
)
from .delegation import suggest_delegations
from .handoff import detect_handoff_opportunities
from .registry import get_all_panes


def detect_cross_pollination(include_predictions: bool = True) -> Dict[str, Any]:
    """Analyze keyword overlap and trajectory convergence across active panes.

    Returns dict with:
    - hints: keyword overlap hints (Jaccard similarity)
    - predictions: convergence predictions from trajectory analysis
    - opportunities: synergy opportunities
    - claim_conflicts: compound claim/trajectory signals
    - handoff_opportunities: recent release + approaching trajectory
    - delegations: suggested delegations
    - trajectory_summary: per-pane trajectory vectors

    Args:
        include_predictions: If False, returns just hints list (compat mode).

    Returns:
        Dict with all signal types, or list of hints if not include_predictions.
    """
    panes = get_all_panes()
    if len(panes) < 2:
        if include_predictions:
            return {"hints": [], "predictions": [], "opportunities": [],
                    "claim_conflicts": [], "handoff_opportunities": [],
                    "delegations": [], "trajectory_summary": {}}
        return []

    # Build topic sets per pane
    identity_noise = get_identity_noise()
    pane_topics: Dict[str, set] = {}
    pane_labels: Dict[str, str] = {}
    for tty, pane in panes.items():
        topics = set(pane.get("key_topics", []))
        project = pane.get("project", "")
        if project:
            topics.add(project.lower())
        pane_topics[tty] = topics
        pane_labels[tty] = pane.get("quadrant") or pane.get("project", tty)

    # Find keyword overlaps between all pairs
    hints: List[Dict[str, Any]] = []
    ttys = list(pane_topics.keys())
    for i in range(len(ttys)):
        for j in range(i + 1, len(ttys)):
            a, b = ttys[i], ttys[j]
            if pane_labels[a] == pane_labels[b]:
                continue
            shared = pane_topics[a] & pane_topics[b]
            shared -= {pane_labels[a].lower(), pane_labels[b].lower()}
            shared -= identity_noise
            if shared:
                score = len(shared) / max(len(pane_topics[a] | pane_topics[b]), 1)
                hints.append({
                    "pane_a": pane_labels[a],
                    "pane_b": pane_labels[b],
                    "pane_a_tty": a,
                    "pane_b_tty": b,
                    "shared_topics": sorted(shared),
                    "score": round(score, 2),
                })

    hints.sort(key=lambda h: h["score"], reverse=True)

    if not include_predictions:
        return hints

    # Trajectory-based analysis
    predictions = predict_convergence(panes)
    opportunities = detect_opportunities(panes)

    # Compound signals
    claim_conflicts = detect_claim_conflicts(panes)
    handoff_opps = detect_handoff_opportunities(panes)
    delegations = suggest_delegations(panes)

    # Store predictions for resolution tracking
    for pred in predictions:
        store_prediction(pred)
    for conflict in claim_conflicts:
        store_prediction(conflict)

    # Resolve active predictions
    try:
        resolve_predictions()
    except Exception:
        pass

    # Build trajectory summary
    trajectory_summary: Dict[str, Dict] = {}
    for tty, pane in panes.items():
        vec = pane.get("trajectory_vector", {})
        label = pane.get("quadrant") or pane.get("project", tty)
        if any(vec.get(k) for k in ("deepening", "emerging", "fading", "stable")):
            trajectory_summary[label] = {
                k: vec.get(k, []) for k in ("deepening", "emerging", "fading", "stable")
            }

    return {
        "hints": hints,
        "predictions": predictions,
        "opportunities": opportunities,
        "claim_conflicts": claim_conflicts,
        "handoff_opportunities": handoff_opps,
        "delegations": delegations,
        "trajectory_summary": trajectory_summary,
    }
