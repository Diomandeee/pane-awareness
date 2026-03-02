"""Note schema for pane-awareness vault notes.

Defines note types, required fields, section ownership,
and validation for the pane-related subset of vault notes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

# --- Note Types (pane-awareness subset) ---

VALID_TYPES = {
    "pane-session",
    "prediction",
    "claim",
    "topology",
    "handoff-thread",
    "project",       # stub notes for backlinks
    "synthesis",     # enhanced connection notes
}

# --- Required Fields per Note Type ---

REQUIRED_FIELDS: dict[str, dict[str, Any]] = {
    "pane-session": {
        "type": None,
        "tty": None,
        "session_id": None,
        "status": "active",
        "source": "pane-awareness",
        "last_active": None,
        "created": None,
    },
    "prediction": {
        "type": None,
        "prediction_type": None,
        "confidence": 0.0,
        "status": "active",
        "source": "pane-awareness",
        "created": None,
    },
    "claim": {
        "type": None,
        "resource": None,
        "event": None,
        "source": "pane-awareness",
        "created": None,
    },
    "topology": {
        "type": None,
        "pane_count": 0,
        "source": "pane-awareness",
        "created": None,
    },
    "handoff-thread": {
        "type": None,
        "from_pane": None,
        "to_pane": None,
        "task": None,
        "source": "pane-awareness",
        "created": None,
    },
    "project": {
        "type": None,
        "project_ref": None,
        "source": "pane-awareness",
        "auto_generated": True,
        "created": None,
    },
    "synthesis": {
        "type": None,
        "source": "pane-awareness",
        "created": None,
    },
}

# --- Section Ownership ---

SECTION_OWNERS: dict[str, str] = {
    "## Resolution":        "pane-awareness",
    "## Claim History":     "pane-awareness",
    "## Pane Topology":     "pane-awareness",
    "## Handoff Context":   "pane-awareness",
    "## Cross-Pollination": "pane-awareness",
}

# --- Directories per Type ---

TYPE_DIRECTORIES: dict[str, str] = {
    "pane-session":    "Panes",
    "prediction":      "Predictions",
    "claim":           "Claims",
    "topology":        "Topologies",
    "handoff-thread":  "Threads",
    "project":         "Projects",
    "synthesis":       "Inbox",
}


@dataclass
class VaultNoteSchema:
    """Represents a parsed vault note's metadata."""
    path: str
    title: str
    note_type: str
    source: str = "pane-awareness"
    frontmatter: dict = field(default_factory=dict)
    links_out: list[str] = field(default_factory=list)
    created: str = ""
    mtime: float = 0.0

    @property
    def directory(self) -> str:
        """Expected directory for this note type."""
        return TYPE_DIRECTORIES.get(self.note_type, "Inbox")


def validate_frontmatter(frontmatter: dict) -> list[str]:
    """Validate frontmatter against the schema.

    Returns a list of error strings. Empty list means valid.
    """
    errors = []

    note_type = frontmatter.get("type")
    if not note_type:
        errors.append("Missing required field: type")
        return errors

    if note_type not in VALID_TYPES:
        errors.append(f"Invalid type: {note_type!r} (valid: {sorted(VALID_TYPES)})")
        return errors

    required = REQUIRED_FIELDS.get(note_type, {})
    for field_name, default in required.items():
        if field_name not in frontmatter:
            if default is None:
                errors.append(f"Missing required field: {field_name}")

    return errors


def fill_defaults(frontmatter: dict) -> dict:
    """Fill missing optional fields with their defaults.

    Returns a new dict with defaults applied. Does not modify the input.
    """
    note_type = frontmatter.get("type")
    if not note_type or note_type not in REQUIRED_FIELDS:
        return dict(frontmatter)

    result = {}
    required = REQUIRED_FIELDS[note_type]

    for field_name, default in required.items():
        if field_name in frontmatter:
            result[field_name] = frontmatter[field_name]
        elif default is not None:
            result[field_name] = default

    for key, val in frontmatter.items():
        if key not in result:
            result[key] = val

    return result


def now_iso() -> str:
    """Return current UTC time in ISO format for frontmatter."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
