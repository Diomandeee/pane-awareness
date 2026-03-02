"""Pane registration, staleness detection, and state management.

Each AI coding session registers its TTY, CWD, project, and last prompt.
Other sessions read this to know what's happening across panes.
"""

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from ._compat import get_current_tty
from .config import get_config
from .state import read_registry, write_registry
from .topics import (
    compute_trajectory_vector,
    extract_topics,
    filter_convergence_topics,
    prompt_hash,
)


def _is_stale(last_active: str) -> bool:
    """Check if a pane entry is stale (older than configured stale_hours)."""
    try:
        ts = datetime.fromisoformat(last_active.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        stale_hours = get_config().general.stale_hours
        return (now - ts).total_seconds() > stale_hours * 3600
    except (ValueError, TypeError):
        return True


def extract_project_name(cwd: str) -> str:
    """Extract a project name from the CWD.

    Checks configured base directories first, then falls back to
    git repo name detection, then directory name.

    Args:
        cwd: Current working directory path.

    Returns:
        Extracted project name string.
    """
    path = Path(cwd)
    cfg = get_config()

    # Check configured base directories
    base_dirs = [Path(d).expanduser() for d in cfg.general.project_base_dirs]
    # Also check common defaults
    home = Path.home()
    base_dirs.extend([home / "Desktop", home / "projects", home / "src", home / "repos"])

    for base in base_dirs:
        try:
            rel = path.relative_to(base)
            parts = rel.parts
            if parts:
                return parts[0]
        except ValueError:
            continue

    # Fallback: try git repo root name
    try:
        import subprocess
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, timeout=2, cwd=cwd
        )
        if result.returncode == 0 and result.stdout.strip():
            return Path(result.stdout.strip()).name
    except Exception:
        pass

    return path.name or "unknown"


def update_pane(session_id: str, cwd: str, prompt_text: str) -> None:
    """Register or update the current pane's state in the registry.

    Called on every prompt submission from the AI assistant.
    Maintains a topic trajectory window and computes trajectory vectors.

    Args:
        session_id: Unique session identifier.
        cwd: Current working directory.
        prompt_text: The user's prompt text.
    """
    tty = get_current_tty()
    if not tty:
        return

    cfg = get_config()
    now = datetime.now(timezone.utc).isoformat()
    project = extract_project_name(cwd)
    topics = extract_topics(prompt_text)

    data = read_registry()
    panes = data.get("panes", {})
    existing = panes.get(tty, {})

    # Trajectory tracking
    trajectory = existing.get("topic_trajectory", [])
    p_hash = prompt_hash(prompt_text) if prompt_text else ""

    if not trajectory or trajectory[-1].get("hash") != p_hash:
        filtered_topics = filter_convergence_topics(topics)
        trajectory.append({
            "topics": filtered_topics,
            "ts": now,
            "hash": p_hash,
        })
        window_size = cfg.topics.trajectory_window_size
        if len(trajectory) > window_size:
            trajectory = trajectory[-window_size:]

    trajectory_vector = compute_trajectory_vector(trajectory)

    # Auto-detect quadrant on first prompt if not set
    quadrant = existing.get("quadrant")
    if not quadrant:
        try:
            from .quadrant import detect_quadrant
            quadrant = detect_quadrant(tty=tty)
        except Exception:
            pass

    panes[tty] = {
        "tty": tty,
        "pid": os.getppid(),
        "session_id": session_id,
        "quadrant": quadrant,
        "project": project,
        "cwd": cwd,
        "last_prompt": prompt_text[:200] if prompt_text else "",
        "last_active": now,
        "created": existing.get("created", now),
        "messages": existing.get("messages", []),
        "read_messages": existing.get("read_messages", []),
        "key_topics": topics,
        "topic_trajectory": trajectory,
        "trajectory_vector": trajectory_vector,
    }

    data["panes"] = panes
    write_registry(data)


def get_all_panes(include_stale: bool = False) -> Dict[str, Dict[str, Any]]:
    """Read registry and return active panes.

    Auto-expires stale entries (older than stale_hours) unless
    include_stale=True.

    Args:
        include_stale: If True, return stale panes too.

    Returns:
        Dict mapping TTY path to pane state.
    """
    data = read_registry()
    panes = data.get("panes", {})

    if include_stale:
        return panes

    active = {}
    stale_keys = []
    for tty, pane in panes.items():
        if _is_stale(pane.get("last_active", "")):
            stale_keys.append(tty)
        else:
            active[tty] = pane

    # Clean up stale entries
    if stale_keys:
        for key in stale_keys:
            panes.pop(key)
        data["panes"] = panes
        write_registry(data)

    return active


def get_pane_info(tty: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Get info for a specific pane (defaults to current).

    Args:
        tty: TTY path to look up. If None, uses current TTY.

    Returns:
        Pane state dict, or None if not found.
    """
    my_tty = tty or get_current_tty()
    if not my_tty:
        return None

    panes = get_all_panes(include_stale=True)
    return panes.get(my_tty)


def set_quadrant(tty: Optional[str] = None, quadrant: Optional[str] = None) -> bool:
    """Set the quadrant label for a pane.

    Args:
        tty: TTY to set quadrant for. If None, uses current.
        quadrant: Quadrant label (e.g. "top-left").

    Returns:
        True if set successfully, False otherwise.
    """
    my_tty = tty or get_current_tty()
    if not my_tty or not quadrant:
        return False

    data = read_registry()
    panes = data.get("panes", {})

    if my_tty in panes:
        panes[my_tty]["quadrant"] = quadrant
        data["panes"] = panes
        write_registry(data)
        return True

    return False
