"""Tiered context builder for pane handoffs.

Tier 1 (auto): project, cwd, recent prompts, trajectory, git diff, claims.
Tier 2 (explicit): domain-specific fields from config handoff_schemas.

Also detects handoff opportunities when a claim is released and another
pane's trajectory is approaching that domain.
"""

import subprocess
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set

from ._compat import get_current_tty
from .domains import claim_to_domains, topic_to_domains
from .state import read_claims, read_registry


def build_handoff_context(
    from_tty: Optional[str] = None,
    tier2_fields: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Build a handoff context blob.

    Tier 1 (always populated, zero effort):
    - project, cwd, last 3 prompts, trajectory vector
    - git diff file list from CWD
    - active claims held by sender

    Tier 2 (optional, explicit):
    - Domain-specific fields from config handoff_schemas

    Args:
        from_tty: Sender TTY (auto-detected).
        tier2_fields: Optional domain-specific enrichment.

    Returns:
        Dict with full handoff context.
    """
    sender = from_tty or get_current_tty() or "unknown"
    data = read_registry()
    panes = data.get("panes", {})
    pane = panes.get(sender, {})

    context: Dict[str, Any] = {
        "schema_version": 1,
        "tier": 1,
        "project": pane.get("project", "unknown"),
        "cwd": pane.get("cwd", ""),
        "last_prompts": [],
        "trajectory_vector": pane.get("trajectory_vector", {}),
        "files_modified": [],
        "claims_transferred": [],
    }

    # Last 3 prompts from trajectory
    trajectory = pane.get("topic_trajectory", [])
    for entry in trajectory[-3:]:
        context["last_prompts"].append({
            "topics": entry.get("topics", []),
            "ts": entry.get("ts", ""),
        })

    # Git diff file list
    cwd = pane.get("cwd", "")
    if cwd:
        try:
            result = subprocess.run(
                ["git", "diff", "--name-only", "HEAD"],
                capture_output=True, text=True, timeout=5, cwd=cwd
            )
            if result.returncode == 0 and result.stdout.strip():
                context["files_modified"] = result.stdout.strip().split("\n")[:20]
        except Exception:
            pass

    # Active claims held by sender
    claims_data = read_claims()
    for resource, claim in claims_data.get("active_claims", {}).items():
        if claim.get("holder") == sender:
            context["claims_transferred"].append({
                "resource": resource,
                "scope": claim.get("scope"),
                "reason": claim.get("reason"),
            })

    if tier2_fields:
        context["tier"] = 2
        context["enrichment"] = tier2_fields

    return context


def detect_handoff_opportunities(panes: Dict[str, Dict]) -> List[Dict[str, Any]]:
    """Detect handoff opportunities from recent claim releases.

    When a claim is released and another pane is approaching that domain,
    suggest a handoff to transfer context.

    Args:
        panes: Dict mapping TTY to pane state.

    Returns:
        List of handoff opportunity dicts.
    """
    opportunities: List[Dict[str, Any]] = []
    claims_data = read_claims()
    claims_log = claims_data.get("claims_log", [])

    now = datetime.now(timezone.utc)
    recent_releases = []
    for entry in reversed(claims_log):
        if entry.get("event") not in ("release", "force_release"):
            continue
        try:
            ts = datetime.fromisoformat(entry["timestamp"].replace("Z", "+00:00"))
            if (now - ts).total_seconds() > 1800:
                break
            recent_releases.append(entry)
        except (ValueError, KeyError):
            continue

    if not recent_releases:
        return opportunities

    for release in recent_releases:
        resource = release.get("resource", "")
        releaser = release.get("holder", "")
        release_domains = claim_to_domains(resource)

        if not release_domains:
            continue

        for tty, pane in panes.items():
            if tty == releaser:
                continue

            vec = pane.get("trajectory_vector", {})
            if not vec:
                continue

            emerging = set(vec.get("emerging", []))
            deepening = set(vec.get("deepening", []))
            approaching = emerging | deepening

            approaching_domains: Set[str] = set()
            for topic in approaching:
                approaching_domains |= topic_to_domains(topic)

            matching = release_domains & approaching_domains
            if matching:
                pane_label = pane.get("quadrant") or pane.get("project", tty)
                releaser_label = release.get("holder_label", releaser)

                opportunities.append({
                    "type": "HANDOFF_OPPORTUNITY",
                    "from_pane": releaser_label,
                    "from_tty": releaser,
                    "to_pane": pane_label,
                    "to_tty": tty,
                    "resource": resource,
                    "domains": sorted(matching),
                    "approaching_topics": sorted(
                        t for t in approaching
                        if any(d in topic_to_domains(t) for d in matching)
                    ),
                    "recommendation": (
                        f"{releaser_label} just released '{resource}'. "
                        f"{pane_label} is approaching [{', '.join(sorted(matching))}]. "
                        f"Consider sending a handoff with context."
                    ),
                })

    return opportunities
