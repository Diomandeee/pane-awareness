"""Pane Awareness Dashboard API — Serves pane coordination data.

Lightweight FastAPI sidecar that reads pane-awareness state files
and serves them as JSON for dashboard frontends.

Usage:
    uvicorn extensions.dashboard.api:app --port 8005

Endpoints:
    GET /health         — Service status
    GET /panes          — All pane data (panes, predictions, claims, threads)
    GET /panes/messages — Recent cross-pane message log
    GET /panes/stats    — Prediction accuracy statistics
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

# Try to import pane_awareness for state file paths
try:
    from pane_awareness.config import get_config
    _config = get_config()
    STATE_DIR = Path(_config.general.state_dir)
except ImportError:
    STATE_DIR = Path(os.environ.get(
        "PANE_AWARENESS_STATE_DIR",
        os.path.expanduser("~/.local/share/pane-awareness"),
    ))

# Optional vault integration
VAULT_PATH = Path(os.environ.get("VAULT_PATH", os.path.expanduser("~/obsidian-vault")))

app = FastAPI(title="Pane Awareness Dashboard", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

VAULT_DIRS = ["Panes", "Predictions", "Claims", "Threads", "Topologies"]


def _read_state_file(filename: str) -> dict:
    """Read a JSON state file from the state directory."""
    filepath = STATE_DIR / filename
    try:
        if filepath.exists():
            return json.loads(filepath.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        pass
    return {}


def _parse_frontmatter(filepath: Path) -> dict:
    """Extract YAML frontmatter from a markdown file."""
    try:
        text = filepath.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return {}

    if not text.startswith("---"):
        return {}

    end = text.find("---", 3)
    if end == -1:
        return {}

    fm = {}
    for line in text[3:end].strip().splitlines():
        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        val = val.strip().strip('"')
        if val.startswith("[") and val.endswith("]"):
            val = [v.strip().strip('"') for v in val[1:-1].split(",") if v.strip()]
        fm[key.strip()] = val
    return fm


def _read_vault_notes(directory: str, limit: int = 50) -> list[dict]:
    """Read vault notes from a directory, returning parsed frontmatter."""
    d = VAULT_PATH / directory
    if not d.exists():
        return []
    notes = []
    for md in sorted(d.glob("*.md"), key=lambda f: f.stat().st_mtime, reverse=True)[:limit]:
        fm = _parse_frontmatter(md)
        text = md.read_text(encoding="utf-8", errors="replace")
        title = md.stem
        for line in text.splitlines():
            if line.startswith("# "):
                title = line[2:].strip()
                break
        notes.append({
            "filename": md.name,
            "title": title,
            "modified": datetime.fromtimestamp(md.stat().st_mtime, tz=timezone.utc).isoformat(),
            **fm,
        })
    return notes


@app.get("/health")
def health():
    return {
        "status": "ok",
        "state_dir": str(STATE_DIR),
        "state_dir_exists": STATE_DIR.exists(),
        "vault_path": str(VAULT_PATH),
        "vault_exists": VAULT_PATH.exists(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/panes")
def panes():
    """Pane Awareness dashboard data.

    Reads from both state files (live data) and vault notes (historical).
    """
    # Live pane data from state files
    registry = _read_state_file("pane_registry.json")
    predictions_data = _read_state_file("pane_predictions.json")
    claims_data = _read_state_file("pane_claims.json")

    # Format live panes
    live_panes = []
    for tty, pane in registry.get("panes", {}).items():
        live_panes.append({
            "tty": tty,
            "quadrant": pane.get("quadrant"),
            "project": pane.get("project", "unknown"),
            "last_prompt": (pane.get("last_prompt", "") or "")[:100],
            "key_topics": pane.get("key_topics", []),
            "last_active": pane.get("last_active"),
            "status": "active",
        })

    # Live predictions
    active_predictions = predictions_data.get("active_predictions", [])

    # Live claims
    active_claims = claims_data.get("claims", [])

    # Vault notes (if vault exists)
    vault_panes = _read_vault_notes("Panes", 20) if VAULT_PATH.exists() else []
    vault_predictions = _read_vault_notes("Predictions", 20) if VAULT_PATH.exists() else []
    vault_claims = _read_vault_notes("Claims", 30) if VAULT_PATH.exists() else []
    vault_threads = _read_vault_notes("Threads", 20) if VAULT_PATH.exists() else []

    # Latest topology from vault
    vault_topos = _read_vault_notes("Topologies", 1) if VAULT_PATH.exists() else []
    latest_topology = vault_topos[0] if vault_topos else None

    # Extract pane rows from topology markdown table
    if latest_topology:
        topo_path = VAULT_PATH / "Topologies" / latest_topology["filename"]
        text = topo_path.read_text(encoding="utf-8", errors="replace")
        pane_rows = []
        in_table = False
        for line in text.splitlines():
            if "| Quadrant |" in line:
                in_table = True
                continue
            if in_table and line.startswith("|---"):
                continue
            if in_table and line.startswith("|"):
                cols = [c.strip() for c in line.split("|")[1:-1]]
                if len(cols) >= 3:
                    project = cols[1].replace("[[", "").replace("]]", "")
                    pane_rows.append({
                        "quadrant": cols[0] or "None",
                        "project": project,
                        "last_prompt": cols[2][:80] if len(cols) > 2 else "",
                    })
            elif in_table and not line.startswith("|"):
                in_table = False
        latest_topology["pane_rows"] = pane_rows

    # Summary
    active_count = len(live_panes) or sum(1 for p in vault_panes if p.get("status") == "active")

    return {
        "live_panes": live_panes,
        "vault_panes": vault_panes,
        "predictions": {
            "active": active_predictions,
            "vault_notes": vault_predictions,
        },
        "claims": {
            "active": active_claims,
            "vault_notes": vault_claims,
        },
        "threads": vault_threads,
        "latest_topology": latest_topology,
        "summary": {
            "active_panes": active_count,
            "active_predictions": len(active_predictions),
            "active_claims": len(active_claims),
            "total_threads": len(vault_threads),
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/panes/messages")
def pane_messages(limit: int = Query(default=50, ge=1, le=200)):
    """Recent cross-pane message log from state files."""
    registry = _read_state_file("pane_registry.json")
    messages = registry.get("message_log", [])
    recent = list(reversed(messages[-limit:]))

    return {
        "messages": recent,
        "total": len(messages),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/panes/stats")
def prediction_stats():
    """Prediction accuracy statistics."""
    pred_data = _read_state_file("pane_predictions.json")
    active_preds = pred_data.get("active_predictions", [])
    resolved_preds = pred_data.get("resolved", [])
    accuracy = pred_data.get("accuracy", {})

    stats = {
        "total": len(active_preds) + len(resolved_preds),
        "active": len(active_preds),
        "resolved": len(resolved_preds),
        "prevented": accuracy.get("prevented", 0),
        "occurred": accuracy.get("occurred", 0),
        "false_positive": accuracy.get("false_positive", 0),
        "expired": accuracy.get("expired", 0),
    }

    resolvable = stats["prevented"] + stats["occurred"]
    stats["prevention_rate"] = round(
        (stats["prevented"] / resolvable * 100) if resolvable > 0 else 0, 1
    )

    return {
        "stats": stats,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)
