"""pane-awareness — Cross-session coordination for AI coding assistants.

When running multiple AI sessions in parallel terminal panes, each session
sees what the others are working on, can send messages, claim resources,
and receive convergence predictions.

Basic usage:

    from pane_awareness import update_pane, get_all_panes, send_message

    # Register current session
    update_pane(session_id="abc123", cwd="/my/project", prompt_text="fix the auth bug")

    # See what other panes are doing
    panes = get_all_panes()

    # Send a message to another pane
    send_message("top-left", "I'm working on auth, FYI")
"""

__version__ = "0.1.0"

# Core API
from .claims import (
    claim_resource,
    contest_claim,
    force_release,
    get_active_claims,
    get_claims_log,
    release_resource,
)
from .config import PaneConfig, get_config, load_config
from .convergence import (
    auto_adjust_convergence_threshold,
    detect_claim_conflicts,
    detect_opportunities,
    get_active_predictions,
    predict_convergence,
    resolve_predictions,
)
from .cross_pollination import detect_cross_pollination
from .delegation import suggest_delegations
from .domains import (
    check_domain_proximity,
    get_effective_domain_map,
    topic_to_domains,
)
from .handoff import build_handoff_context, detect_handoff_opportunities
from .messages import (
    get_message_log,
    get_messages,
    get_read_messages,
    send_ack,
    send_block,
    send_delegation,
    send_handoff,
    send_message,
    send_question,
)
from .quadrant import auto_detect_and_set_quadrant, detect_quadrant
from .registry import (
    extract_project_name,
    get_all_panes,
    get_pane_info,
    set_quadrant,
    update_pane,
)
from .topics import (
    compute_trajectory_vector,
    extract_topics,
    filter_convergence_topics,
)

__all__ = [
    # Version
    "__version__",
    # Registry
    "update_pane",
    "get_all_panes",
    "get_pane_info",
    "set_quadrant",
    "extract_project_name",
    # Topics
    "extract_topics",
    "compute_trajectory_vector",
    "filter_convergence_topics",
    # Messages
    "send_message",
    "get_messages",
    "get_message_log",
    "get_read_messages",
    "send_handoff",
    "send_delegation",
    "send_question",
    "send_ack",
    "send_block",
    # Claims
    "claim_resource",
    "release_resource",
    "contest_claim",
    "force_release",
    "get_active_claims",
    "get_claims_log",
    # Convergence
    "predict_convergence",
    "detect_opportunities",
    "detect_claim_conflicts",
    "get_active_predictions",
    "resolve_predictions",
    "auto_adjust_convergence_threshold",
    # Cross-pollination
    "detect_cross_pollination",
    # Handoff
    "build_handoff_context",
    "detect_handoff_opportunities",
    # Delegation
    "suggest_delegations",
    # Quadrant
    "detect_quadrant",
    "auto_detect_and_set_quadrant",
    # Domains
    "get_effective_domain_map",
    "topic_to_domains",
    "check_domain_proximity",
    # Config
    "load_config",
    "get_config",
    "PaneConfig",
]
