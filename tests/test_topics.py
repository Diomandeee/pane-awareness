"""Tests for topic extraction and trajectory vectors."""

from pane_awareness.topics import (
    compute_trajectory_vector,
    extract_topics,
    filter_convergence_topics,
)


def test_extract_topics_basic():
    topics = extract_topics("fix the supabase migration for auth tables")
    assert "supabase" in topics
    assert "migration" in topics
    assert "auth" in topics
    assert "tables" in topics
    # Stop words should be filtered
    assert "the" not in topics
    assert "for" not in topics
    assert "fix" not in topics


def test_extract_topics_empty():
    assert extract_topics("") == []
    assert extract_topics(None) == []


def test_extract_topics_max_count():
    long = "alpha bravo charlie delta echo foxtrot golf hotel india juliet kilo"
    topics = extract_topics(long)
    assert len(topics) <= 8


def test_extract_topics_dedup():
    topics = extract_topics("docker docker docker nginx nginx")
    assert topics.count("docker") == 1
    assert topics.count("nginx") == 1


def test_extract_topics_strips_punctuation():
    topics = extract_topics("what's the (status) of [deployment]?")
    assert "whats" in topics or "status" in topics
    assert any(t in topics for t in ["status", "deployment"])


def test_filter_convergence_topics():
    topics = ["supabase", "fix", "deploy", "migration"]
    filtered = filter_convergence_topics(topics)
    assert "supabase" in filtered
    assert "migration" in filtered
    assert "fix" not in filtered
    assert "deploy" not in filtered


def test_trajectory_vector_empty():
    result = compute_trajectory_vector([])
    assert result == {"deepening": [], "emerging": [], "fading": [], "stable": []}


def test_trajectory_vector_short():
    result = compute_trajectory_vector([{"topics": ["foo"]}])
    assert result == {"deepening": [], "emerging": [], "fading": [], "stable": []}


def test_trajectory_vector_deepening():
    # Topic appears more in second half, total >= 3
    traj = [
        {"topics": ["alpha"]},
        {"topics": ["alpha"]},
        {"topics": ["alpha", "beta"]},
        {"topics": ["alpha", "beta"]},
        {"topics": ["alpha", "beta"]},
    ]
    vec = compute_trajectory_vector(traj)
    assert "beta" in vec["deepening"]


def test_trajectory_vector_emerging():
    # Topic appeared only once, in last 2 entries
    traj = [
        {"topics": ["alpha"]},
        {"topics": ["alpha"]},
        {"topics": ["alpha"]},
        {"topics": ["alpha"]},
        {"topics": ["newbie"]},
    ]
    vec = compute_trajectory_vector(traj)
    assert "newbie" in vec["emerging"]


def test_trajectory_vector_fading():
    # Topic more in first half, absent from last 2
    traj = [
        {"topics": ["oldie"]},
        {"topics": ["oldie"]},
        {"topics": ["oldie"]},
        {"topics": ["alpha"]},
        {"topics": ["alpha"]},
    ]
    vec = compute_trajectory_vector(traj)
    assert "oldie" in vec["fading"]


def test_trajectory_vector_stable():
    # Topic appears across window with even distribution
    traj = [
        {"topics": ["steady"]},
        {"topics": ["other"]},
        {"topics": ["steady"]},
        {"topics": ["other"]},
        {"topics": ["steady"]},
    ]
    vec = compute_trajectory_vector(traj)
    # "steady" has 3 total, appears in both halves evenly or slightly more in second
    assert "steady" in vec["stable"] or "steady" in vec["deepening"]
