"""Delegation suggestions based on trajectory and claims.

Suggests task delegations when:
- A pane holds a claim but its trajectory is drifting away
- A pane has fading expertise another pane needs (knowledge transfer)
"""

from typing import Any, Dict, List, Optional, Set

from .domains import claim_to_domains, topic_to_domains
from .registry import get_all_panes
from .state import read_claims


def suggest_delegations(panes: Optional[Dict[str, Dict]] = None) -> List[Dict[str, Any]]:
    """Suggest task delegations based on trajectory + claims.

    Args:
        panes: Dict mapping TTY to pane state. Auto-fetched if None.

    Returns:
        List of delegation suggestion dicts.
    """
    if panes is None:
        panes = get_all_panes()

    if len(panes) < 2:
        return []

    suggestions: List[Dict[str, Any]] = []
    claims_data = read_claims()
    active_claims = claims_data.get("active_claims", {})

    # Check: holder's trajectory moving away from claimed domain
    for resource, claim in active_claims.items():
        holder = claim.get("holder")
        if holder not in panes:
            continue

        holder_pane = panes[holder]
        vec = holder_pane.get("trajectory_vector", {})
        if not vec:
            continue

        claim_domains = claim_to_domains(resource)
        fading = set(vec.get("fading", []))
        fading_domains: Set[str] = set()
        for topic in fading:
            fading_domains |= topic_to_domains(topic)

        drifting_domains = claim_domains & fading_domains
        if drifting_domains:
            holder_label = holder_pane.get("quadrant") or holder_pane.get("project", holder)

            for tty, pane in panes.items():
                if tty == holder:
                    continue
                p_vec = pane.get("trajectory_vector", {})
                approaching = set(p_vec.get("emerging", [])) | set(p_vec.get("deepening", []))
                approaching_domains: Set[str] = set()
                for topic in approaching:
                    approaching_domains |= topic_to_domains(topic)

                match = drifting_domains & approaching_domains
                if match:
                    candidate_label = pane.get("quadrant") or pane.get("project", tty)
                    suggestions.append({
                        "type": "DELEGATE_CLAIM",
                        "from_pane": holder_label,
                        "from_tty": holder,
                        "to_pane": candidate_label,
                        "to_tty": tty,
                        "resource": resource,
                        "domains": sorted(match),
                        "reason": (
                            f"{holder_label} is drifting from "
                            f"[{', '.join(sorted(match))}] but holds '{resource}'. "
                            f"{candidate_label} is approaching — consider delegating."
                        ),
                    })

    # Check: fading expertise another pane needs
    ttys = list(panes.keys())
    for i in range(len(ttys)):
        for j in range(i + 1, len(ttys)):
            a = panes[ttys[i]]
            b = panes[ttys[j]]
            vec_a = a.get("trajectory_vector", {})
            vec_b = b.get("trajectory_vector", {})
            if not vec_a or not vec_b:
                continue

            a_fading: Set[str] = set()
            for t in vec_a.get("fading", []):
                a_fading |= topic_to_domains(t)
            b_emerging: Set[str] = set()
            for t in vec_b.get("emerging", []):
                b_emerging |= topic_to_domains(t)

            knowledge_transfer = a_fading & b_emerging
            if knowledge_transfer:
                label_a = a.get("quadrant") or a.get("project", ttys[i])
                label_b = b.get("quadrant") or b.get("project", ttys[j])
                if not any(s["from_tty"] == ttys[i] and s["to_tty"] == ttys[j]
                           for s in suggestions):
                    suggestions.append({
                        "type": "KNOWLEDGE_TRANSFER",
                        "from_pane": label_a,
                        "from_tty": ttys[i],
                        "to_pane": label_b,
                        "to_tty": ttys[j],
                        "domains": sorted(knowledge_transfer),
                        "reason": (
                            f"{label_a} has experience in "
                            f"[{', '.join(sorted(knowledge_transfer))}] (fading). "
                            f"{label_b} is entering that domain. "
                            f"Send a handoff to transfer context."
                        ),
                    })

    return suggestions
