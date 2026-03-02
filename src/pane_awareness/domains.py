"""Domain map and learning — maps topics and resources to working domains.

Users define domains in config. The system also learns domain associations
from historical patterns (topology snapshots, co-occurrence).
"""

from typing import Dict, Set

from .config import get_config
from .state import read_learned_domains


def get_effective_domain_map() -> Dict[str, Set[str]]:
    """Get the merged domain map: configured + learned domains.

    Learned domains extend (never replace) the configured map.

    Returns:
        Dict mapping domain name to set of member topics/keywords.
    """
    cfg = get_config()
    merged: Dict[str, Set[str]] = {}

    # Start with configured domains
    for domain, members in cfg.domains.domains.items():
        merged[domain] = set(members)

    # Merge learned domains
    try:
        learned_data = read_learned_domains()
        for topic, related in learned_data.get("learned", {}).items():
            if isinstance(related, list):
                related = set(related)
            if topic in merged:
                merged[topic] |= related
            else:
                merged[topic] = set(related)
    except Exception:
        pass

    return merged


def topic_to_domains(topic: str) -> Set[str]:
    """Map a single topic to its domain(s).

    Args:
        topic: A topic keyword.

    Returns:
        Set of domain names this topic belongs to.
    """
    domains: Set[str] = set()
    try:
        effective = get_effective_domain_map()
    except Exception:
        effective = {}
    for domain, members in effective.items():
        if topic in members or topic == domain:
            domains.add(domain)
    return domains


def check_domain_proximity(topics_a: list, topics_b: list) -> float:
    """Check domain-level proximity between two topic sets.

    Returns a score based on shared domain membership, even when
    the actual keywords share zero characters.

    Args:
        topics_a: First set of topics.
        topics_b: Second set of topics.

    Returns:
        Proximity score (0.0 = no overlap, higher = more overlap).
    """
    domains_a: Set[str] = set()
    domains_b: Set[str] = set()
    for t in topics_a:
        domains_a |= topic_to_domains(t)
    for t in topics_b:
        domains_b |= topic_to_domains(t)

    shared = domains_a & domains_b
    if not shared:
        return 0.0
    return min(len(shared) * 0.5, 1.5)


def claim_to_domains(resource: str) -> Set[str]:
    """Map a claim resource string to domain(s).

    Uses the domain map plus prefix-based inference and port mapping.

    Args:
        resource: Resource identifier (e.g. "file:src/migrations/*").

    Returns:
        Set of domain names.
    """
    cfg = get_config()
    domains: Set[str] = set()

    if ":" in resource:
        prefix, value = resource.split(":", 1)
    else:
        prefix, value = "", resource

    value_lower = value.lower().replace("-", "").replace("_", "")
    effective = get_effective_domain_map()

    for domain, keywords in effective.items():
        domain_norm = domain.lower().replace("-", "")
        for kw in keywords:
            if kw in value_lower or kw in value:
                domains.add(domain)
                break
        if domain_norm in value_lower or domain in value:
            domains.add(domain)

    # Prefix-based inference
    if prefix in ("docker", "deploy"):
        domains.add("deployment") if "deployment" not in domains else None

    # Port mapping from config
    if prefix == "port" and cfg.domains.port_map:
        mapped = cfg.domains.port_map.get(value, "")
        if mapped:
            domains.add(mapped)

    return domains
