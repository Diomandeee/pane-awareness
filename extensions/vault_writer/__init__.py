"""Obsidian vault integration for pane-awareness.

Optional extension that writes pane state, predictions, claims,
and topology snapshots as Obsidian-compatible markdown notes.

Usage:
    from pane_awareness.extensions.vault_writer import VaultWriter

    writer = VaultWriter()  # uses VAULT_PATH env var or ~/obsidian-vault
    writer.write_pane_state(pane_data)
    writer.write_prediction(prediction_data)
    writer.write_claim_event(claim_data)
    writer.write_topology_snapshot(topology_data)
    writer.write_handoff_thread(handoff_data)
"""

from .writer import VaultWriter
from .config import VAULT_PATH

__all__ = ["VaultWriter", "VAULT_PATH"]
