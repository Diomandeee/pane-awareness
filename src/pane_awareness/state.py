"""Locked file I/O for shared state files.

All pane state is stored as JSON files with file-locking for safe
concurrent access from multiple terminal sessions.

Uses fcntl on macOS/Linux and msvcrt on Windows.
"""

import json
from pathlib import Path
from typing import Any, Dict

from ._compat import lock_exclusive, lock_shared, unlock
from .config import get_config


def _ensure_state_dir() -> Path:
    """Ensure the state directory exists and return its path."""
    state_dir = get_config().state_dir
    state_dir.mkdir(parents=True, exist_ok=True)
    return state_dir


def get_state_dir() -> Path:
    """Return the configured state directory."""
    return get_config().state_dir


def registry_path() -> Path:
    """Path to the pane registry JSON file."""
    return _ensure_state_dir() / "pane_registry.json"


def claims_path() -> Path:
    """Path to the claims JSON file."""
    return _ensure_state_dir() / "pane_claims.json"


def predictions_path() -> Path:
    """Path to the predictions JSON file."""
    return _ensure_state_dir() / "pane_predictions.json"


def learned_domains_path() -> Path:
    """Path to the learned domains JSON file."""
    return _ensure_state_dir() / "learned_domains.json"


def read_json_locked(filepath: Path, default: Dict[str, Any]) -> Dict[str, Any]:
    """Read a JSON file with a shared (read) lock.

    Args:
        filepath: Path to the JSON file.
        default: Default value if file doesn't exist or is invalid.

    Returns:
        Parsed JSON data or the default.
    """
    if not filepath.exists():
        import copy
        return copy.deepcopy(default)

    try:
        with open(filepath, "r") as f:
            lock_shared(f.fileno())
            try:
                data = json.load(f)
            finally:
                unlock(f.fileno())
        return data
    except (json.JSONDecodeError, OSError):
        return dict(default)


def write_json_locked(filepath: Path, data: Dict[str, Any]) -> None:
    """Write a JSON file with an exclusive (write) lock.

    Args:
        filepath: Path to the JSON file.
        data: Data to serialize as JSON.
    """
    _ensure_state_dir()

    with open(filepath, "w") as f:
        lock_exclusive(f.fileno())
        try:
            json.dump(data, f, indent=2)
        finally:
            unlock(f.fileno())


# Default schemas for each state file

REGISTRY_DEFAULT = {
    "panes": {},
    "cross_pollination": [],
    "message_log": [],
    "last_updated": None,
}

CLAIMS_DEFAULT = {
    "active_claims": {},
    "claims_log": [],
    "last_updated": None,
}

PREDICTIONS_DEFAULT = {
    "active_predictions": [],
    "resolved": [],
    "accuracy": {},
    "last_updated": None,
}

LEARNED_DOMAINS_DEFAULT = {
    "learned": {},
    "last_scan": None,
}


def read_registry() -> Dict[str, Any]:
    """Read the pane registry."""
    return read_json_locked(registry_path(), REGISTRY_DEFAULT)


def write_registry(data: Dict[str, Any]) -> None:
    """Write the pane registry."""
    from datetime import datetime, timezone
    data["last_updated"] = datetime.now(timezone.utc).isoformat()
    write_json_locked(registry_path(), data)


def read_claims() -> Dict[str, Any]:
    """Read the claims state."""
    return read_json_locked(claims_path(), CLAIMS_DEFAULT)


def write_claims(data: Dict[str, Any]) -> None:
    """Write the claims state."""
    from datetime import datetime, timezone
    data["last_updated"] = datetime.now(timezone.utc).isoformat()
    write_json_locked(claims_path(), data)


def read_predictions() -> Dict[str, Any]:
    """Read the predictions state."""
    return read_json_locked(predictions_path(), PREDICTIONS_DEFAULT)


def write_predictions(data: Dict[str, Any]) -> None:
    """Write the predictions state."""
    from datetime import datetime, timezone
    data["last_updated"] = datetime.now(timezone.utc).isoformat()
    write_json_locked(predictions_path(), data)


def read_learned_domains() -> Dict[str, Any]:
    """Read the learned domains map."""
    return read_json_locked(learned_domains_path(), LEARNED_DOMAINS_DEFAULT)


def write_learned_domains(data: Dict[str, Any]) -> None:
    """Write the learned domains map."""
    write_json_locked(learned_domains_path(), data)
