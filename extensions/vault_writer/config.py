"""Configuration constants for the Obsidian Vault Writer extension."""

import os
from pathlib import Path

# Vault root — overridable via VAULT_PATH env var
VAULT_PATH = Path(os.environ.get("VAULT_PATH", os.path.expanduser("~/obsidian-vault")))

# Subdirectories for pane-awareness note types
PANES_DIR = "Panes"
PREDICTIONS_DIR = "Predictions"
CLAIMS_DIR = "Claims"
THREADS_DIR = "Threads"
TOPOLOGIES_DIR = "Topologies"
PROJECTS_DIR = "Projects"
INBOX_DIR = "Inbox"

ALL_DIRS = [
    PANES_DIR, PREDICTIONS_DIR, CLAIMS_DIR,
    THREADS_DIR, TOPOLOGIES_DIR, PROJECTS_DIR, INBOX_DIR,
]

# Max title length for slugs
MAX_TITLE_LENGTH = 60
