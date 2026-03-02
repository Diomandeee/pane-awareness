"""Configuration system for pane-awareness.

Config hierarchy (highest priority first):
1. PANE_AWARENESS_CONFIG env var (path to config file)
2. .pane-awareness.toml in CWD
3. ~/.config/pane-awareness/config.toml
4. Built-in defaults

Uses tomllib (Python 3.11+) with JSON fallback for 3.9-3.10.
Zero external dependencies.
"""

import json
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional, Set


def _load_toml(path: Path) -> Dict[str, Any]:
    """Load a TOML file, falling back to JSON for Python < 3.11."""
    if sys.version_info >= (3, 11):
        import tomllib
        with open(path, "rb") as f:
            return tomllib.load(f)
    else:
        # Try tomli (backport) first, then fall back to JSON
        try:
            import tomli
            with open(path, "rb") as f:
                return tomli.load(f)
        except ImportError:
            pass
        # Last resort: if the file is actually JSON
        if path.suffix == ".json":
            return json.loads(path.read_text())
        raise ImportError(
            "Python < 3.11 requires 'tomli' package for TOML support, "
            "or use a .json config file instead."
        )


@dataclass
class GeneralConfig:
    """General settings."""
    state_dir: str = ""  # Empty = auto-detect (~/.config/pane-awareness/state)
    stale_hours: float = 2.0
    identity_noise_extra: list = field(default_factory=list)
    project_base_dirs: list = field(default_factory=list)  # Extra dirs to check for project names


@dataclass
class TopicsConfig:
    """Topic extraction settings."""
    max_topics: int = 8
    trajectory_window_size: int = 10
    extra_stop_words: list = field(default_factory=list)


@dataclass
class ConvergenceConfig:
    """Convergence prediction settings."""
    threshold: float = 0.8
    threshold_min: float = 0.6
    threshold_max: float = 0.95
    threshold_step: float = 0.05
    prediction_ttl_min: int = 60
    predictions_cap: int = 50
    resolution_window_min: int = 5


@dataclass
class ClaimsConfig:
    """Resource claiming settings."""
    contest_timeout_min: int = 5
    log_cap: int = 200


@dataclass
class MessagesConfig:
    """Messaging settings."""
    log_cap: int = 500
    read_cap: int = 100


@dataclass
class QuadrantConfig:
    """Quadrant detection settings."""
    terminal_app: str = "auto"  # "auto", "Terminal", "iTerm2", "disabled"


@dataclass
class DomainsConfig:
    """Domain map configuration."""
    domains: Dict[str, list] = field(default_factory=dict)
    port_map: Dict[str, str] = field(default_factory=dict)
    handoff_schemas: Dict[str, list] = field(default_factory=dict)
    learn_interval_days: int = 7


@dataclass
class PaneConfig:
    """Root configuration object."""
    general: GeneralConfig = field(default_factory=GeneralConfig)
    topics: TopicsConfig = field(default_factory=TopicsConfig)
    convergence: ConvergenceConfig = field(default_factory=ConvergenceConfig)
    claims: ClaimsConfig = field(default_factory=ClaimsConfig)
    messages: MessagesConfig = field(default_factory=MessagesConfig)
    quadrant: QuadrantConfig = field(default_factory=QuadrantConfig)
    domains: DomainsConfig = field(default_factory=DomainsConfig)

    @property
    def state_dir(self) -> Path:
        """Resolved state directory path."""
        if self.general.state_dir:
            return Path(self.general.state_dir).expanduser()
        return Path.home() / ".config" / "pane-awareness" / "state"


def _apply_section(target, data: Dict[str, Any]) -> None:
    """Apply a dict of values to a dataclass instance."""
    for key, value in data.items():
        if hasattr(target, key):
            setattr(target, key, value)


def load_config(path: Optional[str] = None) -> PaneConfig:
    """Load configuration from the first available source.

    Args:
        path: Explicit config file path. If None, searches the hierarchy.

    Returns:
        PaneConfig with merged values.
    """
    config = PaneConfig()

    # Find config file
    config_path = None
    if path:
        config_path = Path(path)
    else:
        # Check env var
        env_path = os.environ.get("PANE_AWARENESS_CONFIG")
        if env_path and Path(env_path).exists():
            config_path = Path(env_path)
        # Check CWD
        elif Path(".pane-awareness.toml").exists():
            config_path = Path(".pane-awareness.toml")
        elif Path(".pane-awareness.json").exists():
            config_path = Path(".pane-awareness.json")
        # Check ~/.config
        else:
            xdg = Path.home() / ".config" / "pane-awareness"
            for name in ("config.toml", "config.json"):
                candidate = xdg / name
                if candidate.exists():
                    config_path = candidate
                    break

    if config_path and config_path.exists():
        try:
            data = _load_toml(config_path) if config_path.suffix == ".toml" else \
                json.loads(config_path.read_text())
        except Exception:
            data = {}

        if "general" in data:
            _apply_section(config.general, data["general"])
        if "topics" in data:
            _apply_section(config.topics, data["topics"])
        if "convergence" in data:
            _apply_section(config.convergence, data["convergence"])
        if "claims" in data:
            _apply_section(config.claims, data["claims"])
        if "messages" in data:
            _apply_section(config.messages, data["messages"])
        if "quadrant" in data:
            _apply_section(config.quadrant, data["quadrant"])
        if "domains" in data:
            _apply_section(config.domains, data["domains"])

    return config


# Module-level singleton (lazy-loaded)
_config: Optional[PaneConfig] = None


def get_config() -> PaneConfig:
    """Get the global config singleton (loads on first access)."""
    global _config
    if _config is None:
        _config = load_config()
    return _config


def reset_config() -> None:
    """Reset the config singleton (for testing)."""
    global _config
    _config = None


# Convergence stop topics — too common to carry signal
CONVERGENCE_STOP_TOPICS: Set[str] = {
    "fix", "add", "update", "test", "build", "run", "check", "create",
    "delete", "modify", "refactor", "debug", "implement", "configure",
    "error", "issue", "bug", "feature", "endpoint", "function", "file",
    "service", "config", "setup", "install", "import", "export",
    "deploy", "commit", "push", "pull", "merge", "branch", "release",
    "start", "stop", "restart", "status", "log", "monitor",
}

# Stop words for keyword extraction
STOP_WORDS: Set[str] = {
    'a', 'an', 'the', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
    'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
    'should', 'may', 'might', 'must', 'shall', 'can', 'need', 'to', 'of',
    'in', 'for', 'on', 'with', 'at', 'by', 'from', 'as', 'into', 'through',
    'during', 'before', 'after', 'above', 'below', 'between', 'under',
    'again', 'further', 'then', 'once', 'i', 'me', 'my', 'myself', 'we',
    'our', 'ours', 'ourselves', 'you', 'your', 'yours', 'yourself', 'he',
    'him', 'his', 'himself', 'she', 'her', 'hers', 'herself', 'it', 'its',
    'itself', 'they', 'them', 'their', 'theirs', 'themselves', 'what',
    'which', 'who', 'whom', 'this', 'that', 'these', 'those', 'am', 'about',
    'and', 'or', 'but', 'if', 'because', 'until', 'while', 'how', 'all',
    'each', 'every', 'both', 'few', 'more', 'most', 'other', 'some', 'such',
    'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very',
    'just', 'also', 'now', 'here', 'there', 'when', 'where', 'why',
    'don', 'let', 'use', 'using', 'want', 'need', 'like', 'make', 'get',
    'got', 'see', 'look', 'give', 'take', 'come', 'go', 'know', 'think',
    'say', 'tell', 'ask', 'work', 'try', 'call', 'keep', 'put', 'seem',
    'help', 'show', 'hear', 'run', 'move', 'live', 'bring', 'happen',
    'write', 'provide', 'set', 'learn', 'change', 'lead', 'understand',
    'watch', 'follow', 'stop', 'create', 'speak', 'read', 'allow', 'add',
    'spend', 'grow', 'open', 'walk', 'win', 'offer', 'remember', 'consider',
    'appear', 'buy', 'wait', 'serve', 'send', 'expect', 'build', 'stay',
    'fall', 'cut', 'reach', 'remain', 'suggest', 'raise', 'pass', 'sell',
    'require', 'report', 'decide', 'pull', 'please', 'thanks', 'thank',
    'hi', 'hello', 'hey', 'okay', 'ok', 'yes', 'yeah', 'no', 'nope',
    'implement', 'file', 'code', 'update', 'fix', 'check', 'test', 'new',
    'first', 'next', 'last', 'commit', 'push', 'pull', 'merge', 'branch',
    'deploy', 'start', 'continue', 'done', 'finish', 'complete',
    'remaining', 'tasks',
}

# Valid message types
MESSAGE_TYPES = {
    "info": {
        "direction": "one-way", "ttl_min": 30,
        "fields": ["message"],
    },
    "question": {
        "direction": "request-response", "ttl_min": 15,
        "fields": ["message", "choices"],
    },
    "claim": {
        "direction": "broadcast", "ttl_min": None,
        "fields": ["resource", "scope", "reason"],
    },
    "release": {
        "direction": "broadcast", "ttl_min": 5,
        "fields": ["resource", "artifacts"],
    },
    "delegate": {
        "direction": "targeted", "ttl_min": 10,
        "fields": ["task", "context", "deadline"],
    },
    "handoff": {
        "direction": "targeted", "ttl_min": 10,
        "fields": ["task", "context_blob", "artifacts", "next_steps"],
    },
    "ack": {
        "direction": "response", "ttl_min": 5,
        "fields": ["ref_id", "accepted", "reason"],
    },
    "block": {
        "direction": "broadcast", "ttl_min": None,
        "fields": ["resource", "blocker", "unblock_hint"],
    },
}

# Claimable resource type descriptions
RESOURCE_TYPES = {
    "file":    "File path or glob pattern (e.g. file:src/migrations/*)",
    "docker":  "Docker service name (e.g. docker:my-service)",
    "port":    "Network port (e.g. port:8001)",
    "deploy":  "Deployment target (e.g. deploy:staging)",
    "project": "Project name (e.g. project:my-app)",
}
