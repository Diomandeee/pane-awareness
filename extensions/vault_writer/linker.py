"""Extract [[wikilinks]] from pane-related data."""


def extract_pane_links(pane_data: dict) -> list[str]:
    """Extract [[wikilinks]] from pane-related data.

    Works with prediction, claim, connection, and handoff dicts.
    Returns formatted link strings for the Links section.
    """
    links = []
    seen = set()

    # Project refs
    for key in ("project", "project_a", "project_b", "from_project", "to_project",
                "holder_project", "pane_a_project", "pane_b_project"):
        val = pane_data.get(key)
        if val and isinstance(val, str) and val.strip():
            name = val.strip()
            if name.lower() not in seen:
                seen.add(name.lower())
                links.append(f"Project: [[{name}]]")

    for ref in pane_data.get("project_refs", []):
        if isinstance(ref, str) and ref.strip():
            name = ref.strip()
            if name.lower() not in seen:
                seen.add(name.lower())
                links.append(f"Project: [[{name}]]")

    # Topics / shared topics
    for key in ("shared_topics", "key_topics", "tags"):
        topics = pane_data.get(key) or []
        for topic in topics:
            if isinstance(topic, str) and topic.strip():
                name = topic.strip()
                if name.lower() not in seen:
                    seen.add(name.lower())
                    links.append(f"Related: [[{name}]]")

    return links
