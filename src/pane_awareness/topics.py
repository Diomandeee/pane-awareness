"""Topic extraction and trajectory vector computation.

Extracts keywords from prompt text and tracks topic momentum
over a rolling window to classify topics as deepening, emerging,
fading, or stable.
"""

import hashlib
import re
from typing import Dict, List, Set

from ._compat import get_identity_noise
from .config import CONVERGENCE_STOP_TOPICS, STOP_WORDS, get_config


def extract_topics(prompt_text: str) -> List[str]:
    """Lightweight keyword extraction from prompt text.

    Strips punctuation, removes stop words and identity noise,
    returns up to max_topics unique keywords (preserving order).

    Args:
        prompt_text: Raw user prompt text.

    Returns:
        List of extracted topic keywords, max 8 by default.
    """
    if not prompt_text:
        return []

    cfg = get_config()
    max_topics = cfg.topics.max_topics

    words = re.sub(r'[,.\?!:;()\[\]{}"\'`]', ' ', prompt_text.lower()).split()

    # Build noise set
    noise = STOP_WORDS | get_identity_noise()
    extra = set(cfg.general.identity_noise_extra)
    extra |= set(cfg.topics.extra_stop_words)
    noise |= extra

    keywords = [w for w in words if w not in noise and len(w) > 2 and w.isalpha()]

    # Deduplicate while preserving order
    seen: Set[str] = set()
    unique: List[str] = []
    for kw in keywords:
        if kw not in seen:
            seen.add(kw)
            unique.append(kw)
    return unique[:max_topics]


def filter_convergence_topics(topics: List[str]) -> List[str]:
    """Remove topics too common to carry convergence signal."""
    return [t for t in topics if t not in CONVERGENCE_STOP_TOPICS]


def prompt_hash(prompt_text: str) -> str:
    """Short hash for prompt deduplication in trajectory window."""
    return hashlib.md5(prompt_text.encode()).hexdigest()[:8]


def compute_trajectory_vector(trajectory: List[Dict]) -> Dict[str, List[str]]:
    """Classify topic momentum from a trajectory window.

    Each topic is classified as:
    - deepening: appears more in recent half, total >= 3
    - emerging: appeared only once, in last 2 entries
    - fading: appeared more in early half, absent from last 2
    - stable: appears across the window with roughly even distribution

    Args:
        trajectory: List of trajectory entries, each with a "topics" key.

    Returns:
        Dict mapping classification to list of topics.
    """
    if len(trajectory) < 3:
        return {"deepening": [], "emerging": [], "fading": [], "stable": []}

    # Count topic appearances by window position
    topic_positions: Dict[str, List[int]] = {}
    for idx, entry in enumerate(trajectory):
        for topic in entry.get("topics", []):
            if topic not in topic_positions:
                topic_positions[topic] = []
            topic_positions[topic].append(idx)

    window_size = len(trajectory)
    midpoint = window_size // 2
    result: Dict[str, List[str]] = {
        "deepening": [], "emerging": [], "fading": [], "stable": [],
    }

    for topic, positions in topic_positions.items():
        if topic in CONVERGENCE_STOP_TOPICS:
            continue

        first_half = sum(1 for p in positions if p < midpoint)
        second_half = sum(1 for p in positions if p >= midpoint)
        total = len(positions)

        if total == 1 and positions[0] >= window_size - 2:
            result["emerging"].append(topic)
        elif second_half > first_half and total >= 3:
            result["deepening"].append(topic)
        elif first_half > second_half and positions[-1] < window_size - 2:
            result["fading"].append(topic)
        elif total >= 2:
            result["stable"].append(topic)

    return result
