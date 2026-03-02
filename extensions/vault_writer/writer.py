"""Core VaultWriter class for pane-awareness Obsidian integration.

Writes pane state, predictions, claims, topology snapshots, and
handoff threads as Obsidian-compatible markdown notes.
"""

import hashlib
import time
from datetime import datetime, timezone
from pathlib import Path

from .config import (
    VAULT_PATH, PANES_DIR, PREDICTIONS_DIR, CLAIMS_DIR,
    THREADS_DIR, TOPOLOGIES_DIR, PROJECTS_DIR, INBOX_DIR, ALL_DIRS,
)
from .schema import SECTION_OWNERS
from .templates import (
    pane_note, prediction_note, claim_note, enhanced_connection_note,
    topology_note, handoff_thread_note, project_stub,
)


class VaultWriter:
    """Writes pane-awareness notes to an Obsidian vault directory."""

    def __init__(self, vault_path: Path | str | None = None):
        self.vault = Path(vault_path) if vault_path else VAULT_PATH
        self._ensure_dirs()

    def _ensure_dirs(self):
        """Create vault subdirectories if missing."""
        for d in ALL_DIRS:
            (self.vault / d).mkdir(parents=True, exist_ok=True)

    def write_pane_state(self, pane: dict) -> Path:
        """Write or update a live pane note in the Panes/ directory.

        Idempotent — same pane (by TTY) overwrites its previous note.

        Args:
            pane: Dict with tty, session_id, quadrant, project, cwd,
                  last_prompt, created, last_active, key_topics, messages.
        """
        tty = pane.get("tty", "unknown")
        project = pane.get("project", "unknown")
        tty_short = tty.split("/")[-1] if "/" in tty else tty

        content = pane_note(
            tty=tty,
            session_id=pane.get("session_id", "unknown"),
            quadrant=pane.get("quadrant"),
            project=project,
            cwd=pane.get("cwd", ""),
            last_prompt=pane.get("last_prompt", ""),
            created=pane.get("created", datetime.now(timezone.utc).isoformat()),
            last_active=pane.get("last_active", datetime.now(timezone.utc).isoformat()),
            prompt_history=pane.get("prompt_history"),
            topics=pane.get("key_topics"),
            status="active",
        )

        safe_project = self._safe_filename(project)
        note_path = self.vault / PANES_DIR / f"{safe_project}-{tty_short}.md"
        note_path.write_text(content, encoding="utf-8")

        self.ensure_project(project)
        return note_path

    def mark_pane_inactive(self, tty: str, project: str = "") -> None:
        """Mark a pane note as inactive when the session expires."""
        tty_short = tty.split("/")[-1] if "/" in tty else tty
        safe_project = self._safe_filename(project)
        note_path = self.vault / PANES_DIR / f"{safe_project}-{tty_short}.md"

        if note_path.exists():
            content = note_path.read_text(encoding="utf-8")
            content = content.replace("status: active", "status: inactive")
            note_path.write_text(content, encoding="utf-8")

    def write_prediction(self, prediction: dict) -> Path:
        """Write or update a convergence prediction note.

        Implements deduplication: predictions with the same key are
        updated in-place within a 1-hour window.
        """
        pred_type = prediction.get("prediction_type", prediction.get("type", "APPROACHING"))
        pane_a = prediction.get("pane_a", prediction.get("pane_a_tty", "?"))
        pane_b = prediction.get("pane_b", prediction.get("pane_b_tty", "?"))
        topics = sorted(prediction.get("shared_topics", prediction.get("topics", [])))

        key_str = f"{pred_type}:{pane_a}:{pane_b}:{','.join(topics)}"
        key_hash = hashlib.md5(key_str.encode()).hexdigest()[:10]
        filename = f"{pred_type.lower()}-{key_hash}.md"

        note_path = self.vault / PREDICTIONS_DIR / filename

        # Update in-place if within 1-hour window
        if note_path.exists():
            try:
                age_sec = time.time() - note_path.stat().st_mtime
                if age_sec < 3600:
                    content = note_path.read_text(encoding="utf-8")
                    new_status = prediction.get("status", "active")
                    resolution = prediction.get("resolution")
                    content = content.replace("status: active", f"status: {new_status}")
                    if resolution and "## Resolution" not in content:
                        content += f"\n## Resolution\nResolved as: **{resolution}**\n"
                    note_path.write_text(content, encoding="utf-8")
                    return note_path
            except Exception:
                pass

        content = prediction_note(
            prediction_type=pred_type,
            pane_a=pane_a,
            pane_b=pane_b,
            shared_topics=topics,
            confidence=prediction.get("confidence", 0),
            urgency=prediction.get("urgency", "MEDIUM"),
            pane_a_project=prediction.get("pane_a_project", ""),
            pane_b_project=prediction.get("pane_b_project", ""),
            trajectory_context=prediction.get("trajectory_context"),
            status=prediction.get("status", "active"),
            resolution=prediction.get("resolution"),
        )

        note_path.write_text(content, encoding="utf-8")

        for key in ("pane_a_project", "pane_b_project"):
            proj = prediction.get(key, "")
            if proj:
                self.ensure_project(proj)

        return note_path

    def write_claim_event(self, claim: dict) -> Path:
        """Write a resource claim event note."""
        resource = claim.get("resource", "unknown")
        event = claim.get("event", "claimed")
        now = datetime.now(timezone.utc)

        safe_res = self._safe_filename(resource)[:30]
        ts = now.strftime("%H%M%S")
        filename = f"{now.strftime('%Y-%m-%d')}-{event}-{safe_res}-{ts}.md"

        content = claim_note(
            resource=resource,
            event=event,
            holder=claim.get("holder", "unknown"),
            holder_project=claim.get("holder_project", ""),
            scope=claim.get("scope", "advisory"),
            reason=claim.get("reason", ""),
            contested_by=claim.get("contested_by"),
            artifacts=claim.get("artifacts"),
        )

        note_path = self.vault / CLAIMS_DIR / filename
        note_path.write_text(content, encoding="utf-8")

        proj = claim.get("holder_project", "")
        if proj:
            self.ensure_project(proj)

        return note_path

    def write_enhanced_connection(self, connection: dict) -> Path:
        """Write an enhanced cross-pollination connection note.

        Written when cross-pollination score >= 0.4.
        """
        pane_a = connection.get("pane_a", "?")
        pane_b = connection.get("pane_b", "?")
        topics = sorted(connection.get("shared_topics", []))

        key_str = f"{pane_a}:{pane_b}:{','.join(topics)}"
        key_hash = hashlib.md5(key_str.encode()).hexdigest()[:10]
        now = datetime.now(timezone.utc)
        date_str = now.strftime("%Y-%m-%d")
        filename = f"{date_str}-connection-{key_hash}.md"

        note_dir = self.vault / INBOX_DIR / date_str
        note_dir.mkdir(parents=True, exist_ok=True)
        note_path = note_dir / filename

        # Skip if recently written (within 1 hour)
        if note_path.exists():
            try:
                if time.time() - note_path.stat().st_mtime < 3600:
                    return note_path
            except Exception:
                pass

        content = enhanced_connection_note(
            pane_a=pane_a,
            pane_b=pane_b,
            shared_topics=topics,
            score=connection.get("score", 0),
            pane_a_project=connection.get("pane_a_project", ""),
            pane_b_project=connection.get("pane_b_project", ""),
            claim_conflicts=connection.get("claim_conflicts"),
            trajectory_context=connection.get("trajectory_context"),
        )

        note_path.write_text(content, encoding="utf-8")

        for key in ("pane_a_project", "pane_b_project"):
            proj = connection.get(key, "")
            if proj:
                self.ensure_project(proj)

        return note_path

    def write_topology_snapshot(self, topology: dict) -> Path:
        """Write a topology snapshot note."""
        now = datetime.now(timezone.utc)
        ts = now.strftime("%Y-%m-%dT%H%M")
        filename = f"topology-{ts}.md"

        content = topology_note(
            panes=topology.get("panes", []),
            connections=topology.get("connections"),
            active_claims=topology.get("active_claims"),
            prediction_count=topology.get("prediction_count", 0),
        )

        note_path = self.vault / TOPOLOGIES_DIR / filename
        note_path.write_text(content, encoding="utf-8")
        return note_path

    def write_handoff_thread(self, handoff: dict) -> Path:
        """Write a handoff thread note."""
        now = datetime.now(timezone.utc)
        ts = now.strftime("%Y-%m-%d-%H%M%S")
        from_label = handoff.get("from_pane", "?").replace("/", "-")
        to_label = handoff.get("to_pane", "?").replace("/", "-")
        filename = f"{ts}-{self._safe_filename(from_label)[:15]}-to-{self._safe_filename(to_label)[:15]}.md"

        content = handoff_thread_note(
            from_pane=handoff.get("from_pane", "?"),
            to_pane=handoff.get("to_pane", "?"),
            task=handoff.get("task", ""),
            from_project=handoff.get("from_project", ""),
            to_project=handoff.get("to_project", ""),
            context_tier=handoff.get("context_tier", 1),
            files_included=handoff.get("files_included", 0),
            claims_transferred=handoff.get("claims_transferred"),
            next_steps=handoff.get("next_steps"),
        )

        note_path = self.vault / THREADS_DIR / filename
        note_path.write_text(content, encoding="utf-8")

        for key in ("from_project", "to_project"):
            proj = handoff.get(key, "")
            if proj:
                self.ensure_project(proj)

        return note_path

    def ensure_project(self, ref: str) -> Path:
        """Create a project stub if it doesn't exist."""
        safe_name = self._safe_filename(ref)
        note_path = self.vault / PROJECTS_DIR / f"{safe_name}.md"
        if not note_path.exists():
            content = project_stub(ref)
            note_path.write_text(content, encoding="utf-8")
        return note_path

    def update_note_section(
        self,
        note_path: Path | str,
        section_header: str,
        new_content: str,
        source: str,
        *,
        create_if_missing: bool = True,
        append: bool = False,
    ) -> bool:
        """Update a specific section in an existing vault note.

        Respects section ownership from SECTION_OWNERS.
        """
        if isinstance(note_path, str):
            note_path = Path(note_path)
        if not note_path.is_absolute():
            note_path = self.vault / note_path

        if not note_path.exists():
            return False

        owner = SECTION_OWNERS.get(section_header)
        if owner and owner != source:
            return False

        text = note_path.read_text(encoding="utf-8")
        lines = text.split("\n")

        header_level = section_header.count("#")
        start_idx = None
        end_idx = None

        for i, line in enumerate(lines):
            if line.strip() == section_header.strip():
                start_idx = i
                continue
            if start_idx is not None and end_idx is None:
                stripped = line.lstrip()
                if stripped.startswith("#"):
                    level = len(stripped) - len(stripped.lstrip("#"))
                    if level <= header_level:
                        end_idx = i
                        break

        if end_idx is None and start_idx is not None:
            end_idx = len(lines)

        content_block = new_content.rstrip("\n")

        if start_idx is not None:
            if append:
                existing = "\n".join(lines[start_idx + 1:end_idx]).strip()
                if existing:
                    content_block = existing + "\n" + content_block
            new_lines = (
                lines[:start_idx + 1]
                + [content_block, ""]
                + lines[end_idx:]
            )
        elif create_if_missing:
            new_lines = lines + ["", section_header, content_block, ""]
        else:
            return False

        note_path.write_text("\n".join(new_lines), encoding="utf-8")
        return True

    def _safe_filename(self, name: str) -> str:
        """Make a name safe for use as a filename."""
        safe = name.replace("/", "-").replace("\\", "-")
        safe = safe.replace(":", "-").replace("|", "-")
        safe = safe.replace("<", "").replace(">", "")
        safe = safe.replace('"', "").replace("?", "").replace("*", "")
        return safe.strip() or "untitled"
