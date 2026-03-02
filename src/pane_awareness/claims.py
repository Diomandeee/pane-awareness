"""Resource claiming lifecycle — advisory, cooperative locking.

Panes can claim shared resources (files, ports, Docker services,
deployment targets). Claims are advisory — enforcement is cooperative.
Supports: claim, release, contest, force-release, auto-expiry.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from ._compat import get_current_tty
from .config import get_config
from .registry import _is_stale
from .state import read_claims, read_registry, write_claims


def _append_claims_log(data: Dict[str, Any], entry: Dict[str, Any]) -> None:
    """Append to claims history log with FIFO cap."""
    cfg = get_config()
    if "claims_log" not in data:
        data["claims_log"] = []
    data["claims_log"].append(entry)
    if len(data["claims_log"]) > cfg.claims.log_cap:
        data["claims_log"] = data["claims_log"][-cfg.claims.log_cap:]


def _check_holder_liveness(holder_tty: str) -> bool:
    """Check if a claim holder pane is still active (not stale)."""
    data = read_registry()
    panes = data.get("panes", {})
    pane = panes.get(holder_tty)
    if not pane:
        return False
    return not _is_stale(pane.get("last_active", ""))


def _resource_matches(pattern: str, resource: str) -> bool:
    """Check if a resource matches a claim pattern (supports glob-like *)."""
    if pattern == resource:
        return True
    if "*" in pattern:
        prefix = pattern.split("*")[0]
        return resource.startswith(prefix)
    return False


def claim_resource(
    resource: str,
    scope: str = "exclusive",
    reason: str = "",
    from_tty: Optional[str] = None,
) -> Dict[str, Any]:
    """Claim a shared resource (advisory, cooperative).

    If the resource is already held by a live pane, the claim is denied.
    If held by a stale pane, the claim overrides the stale holder.

    Args:
        resource: Resource identifier (e.g. "file:src/migrations/*",
                  "docker:my-service", "port:8001").
        scope: "exclusive" or "shared".
        reason: Why this resource is being claimed.
        from_tty: Claimer TTY (auto-detected).

    Returns:
        Dict with granted status, claim details, and any warnings.
    """
    claimer = from_tty or get_current_tty() or "unknown"
    now = datetime.now(timezone.utc).isoformat()

    claims_data = read_claims()
    active = claims_data.get("active_claims", {})

    # Check for existing claims on this resource
    for claimed_resource, claim in list(active.items()):
        if not _resource_matches(claimed_resource, resource) and \
           not _resource_matches(resource, claimed_resource):
            continue

        holder = claim.get("holder")
        if holder == claimer:
            claim["last_refreshed"] = now
            claim["reason"] = reason or claim.get("reason", "")
            claims_data["active_claims"] = active
            write_claims(claims_data)
            return {
                "granted": True,
                "refreshed": True,
                "resource": resource,
                "message": "Claim refreshed (already held by you).",
            }

        if _check_holder_liveness(holder):
            return {
                "granted": False,
                "resource": resource,
                "held_by": holder,
                "held_by_label": claim.get("holder_label", holder),
                "held_since": claim.get("claimed_at"),
                "reason": claim.get("reason", ""),
                "contested": claim.get("contested", False),
                "message": (
                    f"Resource '{resource}' is held by "
                    f"{claim.get('holder_label', holder)}. "
                    f"Use contest_claim() if you need it urgently."
                ),
            }
        else:
            _append_claims_log(claims_data, {
                "event": "stale_override",
                "resource": claimed_resource,
                "old_holder": holder,
                "new_holder": claimer,
                "timestamp": now,
            })
            del active[claimed_resource]

    # Get claimer label
    reg_data = read_registry()
    claimer_pane = reg_data.get("panes", {}).get(claimer, {})
    claimer_label = claimer_pane.get("quadrant") or claimer_pane.get("project", claimer)

    # Grant the claim
    active[resource] = {
        "holder": claimer,
        "holder_label": claimer_label,
        "scope": scope,
        "reason": reason,
        "claimed_at": now,
        "last_refreshed": now,
        "contested": False,
        "contested_by": None,
        "contested_at": None,
    }
    claims_data["active_claims"] = active

    _append_claims_log(claims_data, {
        "event": "claim",
        "resource": resource,
        "holder": claimer,
        "holder_label": claimer_label,
        "scope": scope,
        "reason": reason,
        "timestamp": now,
    })

    write_claims(claims_data)

    # Broadcast claim message
    from .messages import send_message
    send_message(
        target="all",
        message=f"CLAIMED: {resource} by {claimer_label} — {reason}",
        priority="normal",
        from_tty=claimer,
        msg_type="claim",
        payload={"resource": resource, "scope": scope, "reason": reason},
    )

    return {
        "granted": True,
        "resource": resource,
        "holder": claimer,
        "holder_label": claimer_label,
        "scope": scope,
        "message": f"Resource '{resource}' claimed successfully.",
    }


def release_resource(
    resource: str,
    artifacts: Optional[List[str]] = None,
    from_tty: Optional[str] = None,
) -> Dict[str, Any]:
    """Release a previously claimed resource.

    Args:
        resource: Resource to release.
        artifacts: Optional list of files/results produced.
        from_tty: Releaser TTY (auto-detected).

    Returns:
        Dict with release status.
    """
    releaser = from_tty or get_current_tty() or "unknown"
    now = datetime.now(timezone.utc).isoformat()

    claims_data = read_claims()
    active = claims_data.get("active_claims", {})

    if resource not in active:
        return {"released": False, "resource": resource,
                "message": f"Resource '{resource}' is not currently claimed."}

    claim = active[resource]
    if claim.get("holder") != releaser:
        holder = claim.get('holder_label', '?')
        return {
            "released": False, "resource": resource,
            "message": f"Resource '{resource}' is held by {holder}, not you.",
        }

    holder_label = claim.get("holder_label", releaser)
    del active[resource]
    claims_data["active_claims"] = active

    _append_claims_log(claims_data, {
        "event": "release",
        "resource": resource,
        "holder": releaser,
        "holder_label": holder_label,
        "artifacts": artifacts or [],
        "timestamp": now,
    })

    write_claims(claims_data)

    from .messages import send_message
    send_message(
        target="all",
        message=f"RELEASED: {resource} by {holder_label}",
        priority="normal",
        from_tty=releaser,
        msg_type="release",
        payload={"resource": resource, "artifacts": artifacts or []},
    )

    return {
        "released": True,
        "resource": resource,
        "artifacts": artifacts or [],
        "message": f"Resource '{resource}' released.",
    }


def contest_claim(
    resource: str,
    reason: str = "",
    from_tty: Optional[str] = None,
) -> Dict[str, Any]:
    """Contest an active claim held by another pane.

    Sends an urgent message to the holder. If not resolved within
    the contest timeout, force_release() becomes available.

    Args:
        resource: Resource to contest.
        reason: Why you need the resource.
        from_tty: Contester TTY (auto-detected).

    Returns:
        Dict with contest status.
    """
    cfg = get_config()
    contester = from_tty or get_current_tty() or "unknown"
    now = datetime.now(timezone.utc).isoformat()

    claims_data = read_claims()
    active = claims_data.get("active_claims", {})

    if resource not in active:
        return {"contested": False, "resource": resource,
                "message": f"Resource '{resource}' is not currently claimed."}

    claim = active[resource]
    holder = claim.get("holder")

    if holder == contester:
        return {"contested": False, "resource": resource,
                "message": "You hold this claim. Use release_resource() to release it."}

    claim["contested"] = True
    claim["contested_by"] = contester
    claim["contested_at"] = now
    claim["contest_reason"] = reason
    active[resource] = claim
    claims_data["active_claims"] = active

    _append_claims_log(claims_data, {
        "event": "contest",
        "resource": resource,
        "holder": holder,
        "contested_by": contester,
        "reason": reason,
        "timestamp": now,
    })

    write_claims(claims_data)

    from .messages import send_message
    timeout = cfg.claims.contest_timeout_min
    send_message(
        target=holder,
        message=(
            f"CONTESTED: Your claim on '{resource}' is contested. "
            f"Reason: {reason or 'not given'}. "
            f"Please release if done. Force-release in {timeout} min."
        ),
        priority="urgent",
        from_tty=contester,
        msg_type="info",
    )

    return {
        "contested": True,
        "resource": resource,
        "holder": claim.get("holder_label", holder),
        "force_available_at": f"{timeout} minutes from now",
        "message": "Claim contested. Holder notified.",
    }


def force_release(
    resource: str,
    reason: str = "",
    from_tty: Optional[str] = None,
) -> Dict[str, Any]:
    """Force-release a contested claim after the contest timeout.

    Only works if the claim has been contested and the timeout
    has elapsed, OR the holder pane is stale.

    Args:
        resource: Resource to force-release.
        reason: Why force-release is needed.
        from_tty: Requester TTY.

    Returns:
        Dict with release status.
    """
    cfg = get_config()
    requester = from_tty or get_current_tty() or "unknown"
    now_dt = datetime.now(timezone.utc)
    now = now_dt.isoformat()

    claims_data = read_claims()
    active = claims_data.get("active_claims", {})

    if resource not in active:
        return {"released": False, "resource": resource,
                "message": f"Resource '{resource}' is not currently claimed."}

    claim = active[resource]
    holder = claim.get("holder")
    holder_is_stale = not _check_holder_liveness(holder)

    if not holder_is_stale:
        if not claim.get("contested"):
            return {"released": False, "resource": resource,
                    "message": "Cannot force-release: claim is not contested."}

        contested_at = claim.get("contested_at", "")
        try:
            contest_ts = datetime.fromisoformat(contested_at.replace("Z", "+00:00"))
            elapsed_min = (now_dt - contest_ts).total_seconds() / 60
        except (ValueError, TypeError):
            elapsed_min = 0

        timeout = cfg.claims.contest_timeout_min
        if elapsed_min < timeout:
            remaining = round(timeout - elapsed_min, 1)
            return {"released": False, "resource": resource,
                    "message": f"Contest timeout not reached. {remaining} min remaining."}

    holder_label = claim.get("holder_label", holder)
    del active[resource]
    claims_data["active_claims"] = active
    release_reason = "stale_holder" if holder_is_stale else "contest_timeout"

    _append_claims_log(claims_data, {
        "event": "force_release",
        "resource": resource,
        "old_holder": holder,
        "old_holder_label": holder_label,
        "released_by": requester,
        "release_reason": release_reason,
        "reason": reason,
        "timestamp": now,
    })

    write_claims(claims_data)

    from .messages import send_message
    send_message(
        target="all",
        message=f"FORCE-RELEASED: {resource} (was held by {holder_label})",
        priority="urgent",
        from_tty=requester,
        msg_type="release",
        payload={"resource": resource, "force_released": True,
                 "old_holder": holder_label, "release_reason": release_reason},
    )

    return {
        "released": True,
        "resource": resource,
        "old_holder": holder_label,
        "release_reason": release_reason,
        "message": f"Resource '{resource}' force-released from {holder_label}.",
    }


def get_active_claims() -> Dict[str, Any]:
    """Get all active resource claims (auto-cleans stale).

    Returns:
        Dict with claim_count, claims list, and stale_cleaned count.
    """
    claims_data = read_claims()
    active = claims_data.get("active_claims", {})

    stale_resources = []
    for resource, claim in active.items():
        if not _check_holder_liveness(claim.get("holder", "")):
            stale_resources.append(resource)

    if stale_resources:
        now = datetime.now(timezone.utc).isoformat()
        for r in stale_resources:
            _append_claims_log(claims_data, {
                "event": "auto_expired",
                "resource": r,
                "holder": active[r].get("holder"),
                "timestamp": now,
            })
            del active[r]
        claims_data["active_claims"] = active
        write_claims(claims_data)

    claims_list = []
    for resource, claim in active.items():
        claims_list.append({
            "resource": resource,
            "holder": claim.get("holder_label", claim.get("holder")),
            "holder_tty": claim.get("holder"),
            "scope": claim.get("scope"),
            "reason": claim.get("reason"),
            "claimed_at": claim.get("claimed_at"),
            "contested": claim.get("contested", False),
            "contested_by": claim.get("contested_by"),
        })

    return {
        "claim_count": len(claims_list),
        "claims": claims_list,
        "stale_cleaned": len(stale_resources),
    }


def get_claims_log(limit: int = 50) -> List[Dict[str, Any]]:
    """Read the claims history log.

    Args:
        limit: Maximum entries to return.

    Returns:
        List of recent claims log entries.
    """
    claims_data = read_claims()
    log = claims_data.get("claims_log", [])
    return log[-limit:]
