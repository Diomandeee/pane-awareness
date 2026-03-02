"""Prediction engine with self-calibration.

Detects trajectory convergence between active pane pairs using 4 signals:
1. A deepening into topics B is emerging into
2. B deepening into topics A is emerging into
3. Both deepening into same topics (highest risk)
4. Domain proximity (same domain, different keywords)

Includes prediction storage, resolution, and auto-threshold adjustment.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Set

from .config import get_config
from .domains import check_domain_proximity, claim_to_domains, topic_to_domains
from .registry import _is_stale, get_all_panes
from .state import read_claims, read_predictions, read_registry, write_predictions


def get_dynamic_convergence_threshold() -> float:
    """Get the current convergence threshold (may be auto-adjusted).

    Returns the configured threshold unless a dynamic override exists.
    """
    cfg = get_config()
    try:
        pred_data = read_predictions()
        dynamic = pred_data.get("dynamic_threshold")
        if (dynamic is not None
                and cfg.convergence.threshold_min <= dynamic <= cfg.convergence.threshold_max):
            return dynamic
    except Exception:
        pass
    return cfg.convergence.threshold


def _estimate_distance(vec_a: Dict, vec_b: Dict, converging: Set[str]) -> int:
    """Estimate prompts until collision based on trajectory momentum."""
    a_deep = set(vec_a.get("deepening", []))
    b_deep = set(vec_b.get("deepening", []))
    mutual = converging & a_deep & b_deep

    if mutual:
        return 1
    elif converging & a_deep:
        return 3
    elif converging & b_deep:
        return 3
    return 5


def _generate_recommendation(pred_type: str, topics: Set[str]) -> str:
    """Generate a human-readable recommendation for a prediction."""
    topic_str = ", ".join(sorted(topics)[:4])
    if pred_type == "conflict":
        return (f"Both panes are heading toward [{topic_str}]. "
                f"Coordinate before proceeding to avoid duplicate work.")
    elif pred_type == "synergy":
        return (f"Potential knowledge transfer opportunity on [{topic_str}]. "
                f"Consider sending context from the experienced pane.")
    return f"Shared interest in [{topic_str}]."


def predict_convergence(panes: Dict[str, Dict]) -> List[Dict[str, Any]]:
    """Detect trajectory convergence between active pane pairs.

    Args:
        panes: Dict mapping TTY to pane state.

    Returns:
        List of prediction dicts sorted by confidence.
    """
    predictions = []
    ttys = list(panes.keys())
    threshold = get_dynamic_convergence_threshold()

    for i in range(len(ttys)):
        for j in range(i + 1, len(ttys)):
            a = panes[ttys[i]]
            b = panes[ttys[j]]
            vec_a = a.get("trajectory_vector", {})
            vec_b = b.get("trajectory_vector", {})

            if not vec_a or not vec_b:
                continue

            a_deep = set(vec_a.get("deepening", []))
            b_emerge = set(vec_b.get("emerging", []))
            converging_ab = a_deep & b_emerge

            b_deep = set(vec_b.get("deepening", []))
            a_emerge = set(vec_a.get("emerging", []))
            converging_ba = b_deep & a_emerge

            mutual_deepening = a_deep & b_deep

            active_a = list(vec_a.get("deepening", [])) + list(vec_a.get("emerging", []))
            active_b = list(vec_b.get("deepening", [])) + list(vec_b.get("emerging", []))
            domain_overlap = check_domain_proximity(active_a, active_b)

            score = (
                len(converging_ab) * 0.8 +
                len(converging_ba) * 0.8 +
                len(mutual_deepening) * 1.0 +
                domain_overlap * 0.5
            )

            if score >= threshold:
                all_converging = converging_ab | converging_ba | mutual_deepening
                label_a = a.get("quadrant") or a.get("project", ttys[i])
                label_b = b.get("quadrant") or b.get("project", ttys[j])

                pred_type = "CONFLICT" if mutual_deepening else "APPROACHING"
                predictions.append({
                    "type": pred_type,
                    "pane_a": label_a,
                    "pane_b": label_b,
                    "pane_a_tty": ttys[i],
                    "pane_b_tty": ttys[j],
                    "converging_topics": sorted(all_converging),
                    "confidence": round(min(score / 3.0, 1.0), 2),
                    "estimated_prompts_until_collision": _estimate_distance(
                        vec_a, vec_b, all_converging
                    ),
                    "recommendation": _generate_recommendation(
                        pred_type.lower(), all_converging
                    ),
                })

    predictions.sort(key=lambda p: p["confidence"], reverse=True)
    return predictions


def detect_opportunities(panes: Dict[str, Dict]) -> List[Dict[str, Any]]:
    """Find synergy opportunities between panes.

    Detects:
    - A faded from a topic that B is now deepening into (handoff opportunity)
    - A is stable in a topic that B is emerging into (leverage opportunity)

    Args:
        panes: Dict mapping TTY to pane state.

    Returns:
        List of opportunity dicts.
    """
    opportunities = []
    ttys = list(panes.keys())

    for i in range(len(ttys)):
        for j in range(i + 1, len(ttys)):
            a = panes[ttys[i]]
            b = panes[ttys[j]]
            vec_a = a.get("trajectory_vector", {})
            vec_b = b.get("trajectory_vector", {})

            if not vec_a or not vec_b:
                continue

            a_faded = set(vec_a.get("fading", []))
            b_deepening = set(vec_b.get("deepening", []))
            handoff_ab = a_faded & b_deepening

            b_faded = set(vec_b.get("fading", []))
            a_deepening = set(vec_a.get("deepening", []))
            handoff_ba = b_faded & a_deepening

            a_stable = set(vec_a.get("stable", []))
            b_emerging = set(vec_b.get("emerging", []))
            leverage_ab = a_stable & b_emerging

            b_stable = set(vec_b.get("stable", []))
            a_emerging = set(vec_a.get("emerging", []))
            leverage_ba = b_stable & a_emerging

            synergy_topics = handoff_ab | handoff_ba | leverage_ab | leverage_ba
            if synergy_topics:
                label_a = a.get("quadrant") or a.get("project", ttys[i])
                label_b = b.get("quadrant") or b.get("project", ttys[j])
                opportunities.append({
                    "type": "SYNERGY",
                    "pane_a": label_a,
                    "pane_b": label_b,
                    "pane_a_tty": ttys[i],
                    "pane_b_tty": ttys[j],
                    "synergy_topics": sorted(synergy_topics),
                    "suggestion": _generate_recommendation("synergy", synergy_topics),
                })

    return opportunities


def detect_claim_conflicts(panes: Dict[str, Dict]) -> List[Dict[str, Any]]:
    """Detect CLAIM_CONFLICT: trajectory converging toward a claimed domain.

    Args:
        panes: Dict mapping TTY to pane state.

    Returns:
        List of conflict predictions.
    """
    conflicts = []
    claims_data = read_claims()
    active_claims = claims_data.get("active_claims", {})

    if not active_claims:
        return conflicts

    claim_domain_map: Dict[str, Dict[str, Any]] = {}
    for resource, claim in active_claims.items():
        domains = claim_to_domains(resource)
        for domain in domains:
            claim_domain_map[domain] = {
                "holder": claim.get("holder"),
                "holder_label": claim.get("holder_label", claim.get("holder")),
                "resource": resource,
                "scope": claim.get("scope"),
                "reason": claim.get("reason", ""),
            }

    if not claim_domain_map:
        return conflicts

    for tty, pane in panes.items():
        vec = pane.get("trajectory_vector", {})
        if not vec:
            continue

        emerging = set(vec.get("emerging", []))
        deepening = set(vec.get("deepening", []))
        approaching = emerging | deepening
        if not approaching:
            continue

        approaching_domains: Set[str] = set()
        for topic in approaching:
            approaching_domains |= topic_to_domains(topic)

        for domain, claim_info in claim_domain_map.items():
            if claim_info["holder"] == tty:
                continue

            if domain in approaching_domains:
                pane_label = pane.get("quadrant") or pane.get("project", tty)
                deep_in = any(domain in topic_to_domains(t) for t in deepening)
                urgency = "HIGH" if deep_in else "MEDIUM"

                conflicts.append({
                    "type": "CLAIM_CONFLICT",
                    "pane": pane_label,
                    "pane_tty": tty,
                    "claim_holder": claim_info["holder_label"],
                    "claim_holder_tty": claim_info["holder"],
                    "resource": claim_info["resource"],
                    "domain": domain,
                    "urgency": urgency,
                    "approaching_topics": sorted(
                        t for t in approaching if domain in topic_to_domains(t)
                    ),
                    "recommendation": (
                        f"{pane_label} is approaching [{domain}], but "
                        f"{claim_info['holder_label']} holds '{claim_info['resource']}'. "
                        f"Coordinate before proceeding."
                    ),
                })

    conflicts.sort(key=lambda c: 0 if c["urgency"] == "HIGH" else 1)
    return conflicts


def store_prediction(prediction: Dict[str, Any]) -> None:
    """Store a new prediction with deduplication.

    Args:
        prediction: Prediction dict to store.
    """
    cfg = get_config()
    pred_data = read_predictions()
    active = pred_data.get("active_predictions", [])

    key = (
        prediction.get("pane_a_tty", ""),
        prediction.get("pane_b_tty", ""),
        prediction.get("type", ""),
        tuple(sorted(prediction.get("converging_topics",
                                     prediction.get("approaching_topics", [])))),
    )

    now = datetime.now(timezone.utc)

    for i, existing in enumerate(active):
        existing_key = (
            existing.get("pane_a_tty", ""),
            existing.get("pane_b_tty", ""),
            existing.get("type", ""),
            tuple(sorted(existing.get("converging_topics",
                                       existing.get("approaching_topics", [])))),
        )
        if existing_key == key:
            active[i]["confidence"] = prediction.get("confidence", existing.get("confidence"))
            active[i]["last_refreshed"] = now.isoformat()
            active[i]["refresh_count"] = existing.get("refresh_count", 0) + 1
            pred_data["active_predictions"] = active
            write_predictions(pred_data)
            return

    prediction["created_at"] = now.isoformat()
    prediction["last_refreshed"] = now.isoformat()
    prediction["refresh_count"] = 0

    topics = prediction.get("converging_topics", prediction.get("approaching_topics", []))
    domains: Set[str] = set()
    for t in topics:
        domains |= topic_to_domains(t)
    prediction["domains"] = sorted(domains)

    active.append(prediction)
    if len(active) > cfg.convergence.predictions_cap:
        active = active[-cfg.convergence.predictions_cap:]

    pred_data["active_predictions"] = active
    write_predictions(pred_data)


def resolve_predictions() -> Dict[str, Any]:
    """Check active predictions against current state and resolve them.

    Resolution types:
    - prevented: A handoff/delegate/ack fired between the predicted panes.
    - occurred: Both panes submitted prompts in the predicted domain.
    - false_positive: TTL expired.
    - expired: Source pane went stale.

    Returns:
        Dict with resolved_count and resolution details.
    """
    cfg = get_config()
    pred_data = read_predictions()
    active = pred_data.get("active_predictions", [])

    if not active:
        return {"resolved_count": 0, "resolved": []}

    now = datetime.now(timezone.utc)
    panes = get_all_panes(include_stale=True)
    data = read_registry()
    message_log = data.get("message_log", [])

    resolved = []
    still_active = []

    for pred in active:
        created_at = pred.get("created_at", "")
        try:
            created = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            age_min = (now - created).total_seconds() / 60
        except (ValueError, TypeError):
            age_min = 999

        pane_a_tty = pred.get("pane_a_tty", "")
        pane_b_tty = pred.get("pane_b_tty", "")
        pred_topics = set(pred.get("converging_topics", []))

        pane_a = panes.get(pane_a_tty, {})
        pane_b = panes.get(pane_b_tty, {})
        a_stale = _is_stale(pane_a.get("last_active", ""))
        b_stale = _is_stale(pane_b.get("last_active", ""))

        if a_stale or b_stale:
            pred["resolution"] = "expired"
            pred["resolved_at"] = now.isoformat()
            resolved.append(pred)
            continue

        if age_min > cfg.convergence.prediction_ttl_min:
            pred["resolution"] = "false_positive"
            pred["resolved_at"] = now.isoformat()
            resolved.append(pred)
            continue

        # Check prevented by coordination messages
        prevented = False
        for msg in reversed(message_log[-100:]):
            if msg.get("msg_type") not in ("handoff", "delegate", "ack"):
                continue
            msg_from = msg.get("from", "")
            msg_target = msg.get("target", "")
            if (msg_from == pane_a_tty and msg_target in (pane_b_tty, "all")) or \
               (msg_from == pane_b_tty and msg_target in (pane_a_tty, "all")):
                try:
                    msg_ts = datetime.fromisoformat(msg["timestamp"].replace("Z", "+00:00"))
                    if msg_ts >= created:
                        prevented = True
                        break
                except (ValueError, KeyError):
                    continue

        if prevented:
            pred["resolution"] = "prevented"
            pred["prevention_method"] = msg.get("msg_type", "unknown")
            pred["resolved_at"] = now.isoformat()
            resolved.append(pred)
            continue

        a_topics = set(pane_a.get("key_topics", []))
        b_topics = set(pane_b.get("key_topics", []))
        if pred_topics & a_topics and pred_topics & b_topics:
            try:
                a_ts = datetime.fromisoformat(pane_a["last_active"].replace("Z", "+00:00"))
                b_ts = datetime.fromisoformat(pane_b["last_active"].replace("Z", "+00:00"))
                gap = abs((a_ts - b_ts).total_seconds()) / 60
                if gap <= cfg.convergence.resolution_window_min:
                    pred["resolution"] = "occurred"
                    pred["resolved_at"] = now.isoformat()
                    resolved.append(pred)
                    continue
            except (ValueError, KeyError):
                pass

        still_active.append(pred)

    if resolved:
        pred_data["active_predictions"] = still_active
        if "resolved" not in pred_data:
            pred_data["resolved"] = []
        pred_data["resolved"].extend(resolved)
        if len(pred_data["resolved"]) > 200:
            pred_data["resolved"] = pred_data["resolved"][-200:]

        accuracy = pred_data.get("accuracy", {})
        for r in resolved:
            res_type = r.get("resolution", "unknown")
            accuracy[res_type] = accuracy.get(res_type, 0) + 1
        pred_data["accuracy"] = accuracy
        write_predictions(pred_data)

        try:
            auto_adjust_convergence_threshold()
        except Exception:
            pass

    return {
        "resolved_count": len(resolved),
        "resolved": resolved,
        "still_active": len(still_active),
    }


def get_active_predictions() -> Dict[str, Any]:
    """Get all active (unresolved) predictions plus accuracy stats.

    Returns:
        Dict with prediction_count, predictions, accuracy, total_resolved.
    """
    cfg = get_config()
    pred_data = read_predictions()
    active = pred_data.get("active_predictions", [])
    accuracy = pred_data.get("accuracy", {})

    now = datetime.now(timezone.utc)
    still_active = []
    expired = 0
    for pred in active:
        try:
            created = datetime.fromisoformat(pred["created_at"].replace("Z", "+00:00"))
            if (now - created).total_seconds() / 60 > cfg.convergence.prediction_ttl_min:
                expired += 1
                continue
        except (ValueError, KeyError):
            expired += 1
            continue
        still_active.append(pred)

    if expired:
        pred_data["active_predictions"] = still_active
        accuracy["false_positive"] = accuracy.get("false_positive", 0) + expired
        pred_data["accuracy"] = accuracy
        write_predictions(pred_data)

    return {
        "prediction_count": len(still_active),
        "predictions": still_active,
        "accuracy": accuracy,
        "total_resolved": sum(accuracy.values()),
    }


def auto_adjust_convergence_threshold() -> Dict[str, Any]:
    """Auto-adjust the convergence threshold based on prediction accuracy.

    Rules:
    - false_positive rate > 30%: raise threshold (fewer predictions)
    - occurred (missed) rate > 10%: lower threshold (more predictions)
    - Bounds: [threshold_min, threshold_max]

    Returns:
        Dict with adjustment details.
    """
    cfg = get_config()
    pred_data = read_predictions()
    accuracy = pred_data.get("accuracy", {})
    total = sum(accuracy.values())

    if total < 10:
        return {"adjusted": False, "reason": f"Not enough data ({total}/10 min)",
                "threshold": get_dynamic_convergence_threshold()}

    current = pred_data.get("dynamic_threshold", cfg.convergence.threshold)
    false_positive = accuracy.get("false_positive", 0)
    occurred = accuracy.get("occurred", 0)

    fp_rate = false_positive / max(total, 1)
    occurred_rate = occurred / max(total, 1)

    new_threshold = current
    reason = "no adjustment needed"

    if fp_rate > 0.30:
        new_threshold = min(current + cfg.convergence.threshold_step, cfg.convergence.threshold_max)
        reason = f"false_positive rate {fp_rate:.0%} > 30%"
    elif occurred_rate > 0.10:
        new_threshold = max(current - cfg.convergence.threshold_step, cfg.convergence.threshold_min)
        reason = f"occurred rate {occurred_rate:.0%} > 10%"

    adjusted = new_threshold != current
    if adjusted:
        pred_data["dynamic_threshold"] = round(new_threshold, 2)
        pred_data["threshold_history"] = pred_data.get("threshold_history", [])
        pred_data["threshold_history"].append({
            "old": current,
            "new": round(new_threshold, 2),
            "reason": reason,
            "accuracy_snapshot": dict(accuracy),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        if len(pred_data["threshold_history"]) > 50:
            pred_data["threshold_history"] = pred_data["threshold_history"][-50:]
        write_predictions(pred_data)

    return {
        "adjusted": adjusted,
        "old_threshold": current,
        "new_threshold": round(new_threshold, 2),
        "reason": reason,
        "accuracy": {
            "total": total,
            "prevented": accuracy.get("prevented", 0),
            "occurred": occurred,
            "false_positive": false_positive,
            "expired": accuracy.get("expired", 0),
            "fp_rate": round(fp_rate, 2),
            "occurred_rate": round(occurred_rate, 2),
        },
    }
