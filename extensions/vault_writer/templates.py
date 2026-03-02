"""Markdown templates for pane-awareness vault notes."""

from .schema import fill_defaults, now_iso


def pane_note(
    tty: str,
    session_id: str,
    quadrant: str | None,
    project: str,
    cwd: str,
    last_prompt: str,
    created: str,
    last_active: str,
    prompt_history: list[str] | None = None,
    topics: list[str] | None = None,
    status: str = "active",
) -> str:
    """Generate a live pane session note for Obsidian."""
    fm_data = {
        "type": "pane-session",
        "tty": tty,
        "session_id": session_id,
        "status": status,
        "source": "pane-awareness",
        "last_active": last_active,
        "created": created,
    }
    if quadrant:
        fm_data["quadrant"] = quadrant
    if topics:
        fm_data["tags"] = topics

    fm = _frontmatter(fill_defaults(fm_data))

    label = f"{project} ({quadrant})" if quadrant else f"{project} ({tty.split('/')[-1]})"
    sections = [fm, f"# Pane: {label}", ""]

    sections.append("| | |")
    sections.append("|---|---|")
    sections.append(f"| **Project** | [[{project}]] |")
    sections.append(f"| **CWD** | `{cwd}` |")
    sections.append(f"| **Last Prompt** | {last_prompt[:120]} |")
    sections.append(f"| **Active Since** | {created[:16]} |")
    sections.append("")

    if prompt_history:
        sections.append("## Recent Activity")
        for entry in prompt_history[-10:]:
            sections.append(f"- {entry}")
        sections.append("")

    sections.append("## Links")
    sections.append(f"- Project: [[{project}]]")
    if topics:
        for topic in topics[:5]:
            sections.append(f"- Related: [[{topic}]]")
    sections.append("")

    return "\n".join(sections)


def prediction_note(
    prediction_type: str,
    pane_a: str,
    pane_b: str,
    shared_topics: list[str],
    confidence: float,
    urgency: str = "MEDIUM",
    pane_a_project: str = "",
    pane_b_project: str = "",
    trajectory_context: dict | None = None,
    status: str = "active",
    resolution: str | None = None,
) -> str:
    """Generate a convergence prediction note."""
    fm_data = fill_defaults({
        "type": "prediction",
        "prediction_type": prediction_type,
        "confidence": round(confidence, 2),
        "urgency": urgency,
        "status": status,
        "pane_a": pane_a,
        "pane_b": pane_b,
        "source": "pane-awareness",
        "created": now_iso(),
    })
    if shared_topics:
        fm_data["tags"] = shared_topics
    if pane_a_project:
        fm_data["project_a"] = pane_a_project
    if pane_b_project:
        fm_data["project_b"] = pane_b_project
    if resolution:
        fm_data["resolution"] = resolution

    fm = _frontmatter(fm_data)
    title = f"{prediction_type}: {pane_a} <> {pane_b}"
    sections = [fm, f"# {title}", ""]

    sections.append("| | |")
    sections.append("|---|---|")
    sections.append(f"| **Type** | {prediction_type} |")
    sections.append(f"| **Confidence** | {confidence:.0%} |")
    sections.append(f"| **Urgency** | {urgency} |")
    sections.append(f"| **Status** | {status} |")
    sections.append("")

    sections.append("## Panes")
    if pane_a_project:
        sections.append(f"- **A**: {pane_a} — [[{pane_a_project}]]")
    else:
        sections.append(f"- **A**: {pane_a}")
    if pane_b_project:
        sections.append(f"- **B**: {pane_b} — [[{pane_b_project}]]")
    else:
        sections.append(f"- **B**: {pane_b}")
    sections.append("")

    if shared_topics:
        topic_links = ", ".join(f"[[{t}]]" for t in shared_topics)
        sections.append("## Shared Topics")
        sections.append(topic_links)
        sections.append("")

    if trajectory_context:
        sections.append("## Trajectory Context")
        for pane_label, vectors in trajectory_context.items():
            sections.append(f"### {pane_label}")
            for direction, topics in vectors.items():
                if topics:
                    sections.append(f"- **{direction}**: {', '.join(topics)}")
        sections.append("")

    if resolution:
        sections.append("## Resolution")
        sections.append(f"Resolved as: **{resolution}**")
        sections.append("")

    return "\n".join(sections)


def claim_note(
    resource: str,
    event: str,
    holder: str,
    holder_project: str = "",
    scope: str = "advisory",
    reason: str = "",
    contested_by: str | None = None,
    artifacts: list[str] | None = None,
) -> str:
    """Generate a resource claim event note."""
    fm_data = fill_defaults({
        "type": "claim",
        "resource": resource,
        "event": event,
        "holder": holder,
        "scope": scope,
        "source": "pane-awareness",
        "created": now_iso(),
    })
    if holder_project:
        fm_data["project_ref"] = holder_project
    if contested_by:
        fm_data["contested_by"] = contested_by

    fm = _frontmatter(fm_data)
    title = f"Claim {event.title()}: {resource}"
    sections = [fm, f"# {title}", ""]

    sections.append("| | |")
    sections.append("|---|---|")
    sections.append(f"| **Resource** | `{resource}` |")
    sections.append(f"| **Event** | {event} |")
    sections.append(f"| **Holder** | {holder} |")
    sections.append(f"| **Scope** | {scope} |")
    if contested_by:
        sections.append(f"| **Contested By** | {contested_by} |")
    sections.append("")

    if holder_project:
        sections.append("## Project")
        sections.append(f"- [[{holder_project}]]")
        sections.append("")

    if reason:
        sections.append("## Reason")
        sections.append(reason)
        sections.append("")

    if artifacts:
        sections.append("## Artifacts")
        for a in artifacts:
            sections.append(f"- `{a}`")
        sections.append("")

    return "\n".join(sections)


def enhanced_connection_note(
    pane_a: str,
    pane_b: str,
    shared_topics: list[str],
    score: float,
    pane_a_project: str = "",
    pane_b_project: str = "",
    claim_conflicts: list[dict] | None = None,
    trajectory_context: dict | None = None,
) -> str:
    """Generate an enhanced cross-pollination connection note."""
    fm_data = {
        "type": "synthesis",
        "connection_score": round(score, 2),
        "source": "pane-awareness",
        "created": now_iso(),
    }
    if shared_topics:
        fm_data["tags"] = shared_topics
    projects = []
    if pane_a_project:
        projects.append(pane_a_project)
    if pane_b_project and pane_b_project != pane_a_project:
        projects.append(pane_b_project)
    if projects:
        fm_data["project_refs"] = projects

    fm = _frontmatter(fill_defaults(fm_data))
    title = f"Connection: {pane_a} <> {pane_b}"
    sections = [fm, f"# {title}", ""]

    sections.append(f"**Score**: {score:.0%}")
    sections.append("")

    if shared_topics:
        topic_links = ", ".join(f"[[{t}]]" for t in shared_topics)
        sections.append("## Shared Topics")
        sections.append(topic_links)
        sections.append("")

    if claim_conflicts:
        sections.append("## Claim Conflicts")
        for c in claim_conflicts:
            sections.append(f"- `{c.get('resource', '?')}` — {c.get('urgency', 'MEDIUM')}")
        sections.append("")

    if trajectory_context:
        sections.append("## Trajectory Context")
        for pane_label, vectors in trajectory_context.items():
            sections.append(f"### {pane_label}")
            for direction, topics in vectors.items():
                if topics:
                    sections.append(f"- **{direction}**: {', '.join(topics)}")
        sections.append("")

    sections.append("## Links")
    if pane_a_project:
        sections.append(f"- Project: [[{pane_a_project}]]")
    if pane_b_project and pane_b_project != pane_a_project:
        sections.append(f"- Project: [[{pane_b_project}]]")
    for topic in shared_topics[:5]:
        sections.append(f"- Related: [[{topic}]]")
    sections.append("")

    return "\n".join(sections)


def topology_note(
    panes: list[dict],
    connections: list[dict] | None = None,
    active_claims: list[dict] | None = None,
    prediction_count: int = 0,
) -> str:
    """Generate a topology snapshot note."""
    fm_data = fill_defaults({
        "type": "topology",
        "pane_count": len(panes),
        "connection_count": len(connections) if connections else 0,
        "claim_count": len(active_claims) if active_claims else 0,
        "prediction_count": prediction_count,
        "source": "pane-awareness",
        "created": now_iso(),
    })
    projects = []
    for p in panes:
        proj = p.get("project", "")
        if proj and proj not in projects:
            projects.append(proj)
    if projects:
        fm_data["project_refs"] = projects

    fm = _frontmatter(fm_data)
    ts = now_iso()[:16].replace("T", " ")
    sections = [fm, f"# Topology Snapshot — {ts}", ""]

    sections.append("## Active Panes")
    sections.append("| Quadrant | Project | Last Prompt |")
    sections.append("|----------|---------|-------------|")
    for p in panes:
        quad = p.get("quadrant", p.get("tty", "?"))
        proj = p.get("project", "?")
        prompt = (p.get("last_prompt", "") or "")[:60]
        sections.append(f"| {quad} | [[{proj}]] | {prompt} |")
    sections.append("")

    if connections:
        sections.append("## Connections")
        for c in connections:
            pa = c.get("pane_a", "?")
            pb = c.get("pane_b", "?")
            topics = ", ".join(c.get("shared_topics", [])[:5])
            score = c.get("score", 0)
            sections.append(f"- {pa} <> {pb}: [{topics}] (score: {score:.0%})")
        sections.append("")

    if active_claims:
        sections.append("## Active Claims")
        for cl in active_claims:
            res = cl.get("resource", "?")
            holder = cl.get("holder_label", cl.get("holder", "?"))
            sections.append(f"- `{res}` — held by {holder}")
        sections.append("")

    if prediction_count:
        sections.append("## Predictions")
        sections.append(f"{prediction_count} active predictions at time of snapshot.")
        sections.append("")

    return "\n".join(sections)


def handoff_thread_note(
    from_pane: str,
    to_pane: str,
    task: str,
    from_project: str = "",
    to_project: str = "",
    context_tier: int = 1,
    files_included: int = 0,
    claims_transferred: list[str] | None = None,
    next_steps: list[str] | None = None,
) -> str:
    """Generate a handoff thread note."""
    fm_data = fill_defaults({
        "type": "handoff-thread",
        "from_pane": from_pane,
        "to_pane": to_pane,
        "task": task[:80],
        "context_tier": context_tier,
        "source": "pane-awareness",
        "created": now_iso(),
    })
    projects = []
    if from_project:
        projects.append(from_project)
    if to_project and to_project != from_project:
        projects.append(to_project)
    if projects:
        fm_data["project_refs"] = projects

    fm = _frontmatter(fm_data)
    title = f"Handoff: {from_pane} -> {to_pane}"
    sections = [fm, f"# {title}", ""]

    sections.append("| | |")
    sections.append("|---|---|")
    sections.append(f"| **From** | {from_pane} |")
    sections.append(f"| **To** | {to_pane} |")
    sections.append(f"| **Context Tier** | {context_tier} |")
    sections.append(f"| **Files Included** | {files_included} |")
    sections.append("")

    sections.append("## Task")
    sections.append(task)
    sections.append("")

    if claims_transferred:
        sections.append("## Claims Transferred")
        for c in claims_transferred:
            sections.append(f"- `{c}`")
        sections.append("")

    if next_steps:
        sections.append("## Next Steps")
        for step in next_steps:
            sections.append(f"- [ ] {step}")
        sections.append("")

    sections.append("## Links")
    if from_project:
        sections.append(f"- From: [[{from_project}]]")
    if to_project:
        sections.append(f"- To: [[{to_project}]]")
    sections.append("")

    return "\n".join(sections)


def project_stub(ref: str) -> str:
    """Generate a minimal project stub note."""
    fm = _frontmatter(fill_defaults({
        "type": "project",
        "project_ref": ref,
        "source": "pane-awareness",
        "auto_generated": True,
        "created": now_iso(),
    }))
    return f"""{fm}
# {ref}

> Auto-generated project index. Backlinks from pane sessions and predictions will accumulate here.

## Related Notes

_See backlinks below._
"""


def _frontmatter(data: dict) -> str:
    """Render YAML frontmatter block."""
    lines = ["---"]
    for key, value in data.items():
        if isinstance(value, list):
            lines.append(f"{key}: [{', '.join(str(v) for v in value)}]")
        elif isinstance(value, bool):
            lines.append(f"{key}: {'true' if value else 'false'}")
        elif isinstance(value, (int, float)):
            lines.append(f"{key}: {value}")
        else:
            s = str(value)
            if any(c in s for c in ":#[]{}|>&*!%@`"):
                lines.append(f'{key}: "{s}"')
            else:
                lines.append(f"{key}: {s}")
    lines.append("---")
    return "\n".join(lines)
