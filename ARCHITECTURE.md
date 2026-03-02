# Architecture

## System Design

pane-awareness is a coordination layer that runs alongside AI coding sessions. Each session writes its state to shared JSON files, and reads other sessions' state to make coordination decisions.

### Core Principle: Shared-Nothing with File-Based State

No server, no database, no daemon. Sessions coordinate through locked JSON files on the local filesystem. This makes the system:

- **Zero-dependency** — nothing to install beyond Python
- **Zero-configuration** — works out of the box
- **Crash-resilient** — stale panes auto-expire, no orphan processes
- **Portable** — works on macOS, Linux, and Windows

### Data Flow

```
┌───────────┐     UserPromptSubmit      ┌──────────────────┐
│ AI Session│────────────────────────────▶│  update_pane()   │
│ (Claude   │                            │                  │
│  Code)    │     SessionStart           │  • extract topics│
│           │◀───────────────────────────│  • compute       │
│           │  inject pane context       │    trajectory    │
│           │                            │  • detect        │
│           │     PreToolUse             │    quadrant      │
│           │◀───────────────────────────│  • write state   │
│           │  advisory claim warning    │                  │
└───────────┘                            └────────┬─────────┘
                                                  │
                                                  ▼
                                    ┌─────────────────────────┐
                                    │   State Files (locked)   │
                                    │                         │
                                    │  pane_registry.json     │
                                    │  ├── panes: {}          │
                                    │  └── message_log: []    │
                                    │                         │
                                    │  pane_claims.json       │
                                    │  ├── claims: []         │
                                    │  └── claims_log: []     │
                                    │                         │
                                    │  pane_predictions.json  │
                                    │  ├── active_predictions │
                                    │  ├── resolved: []       │
                                    │  └── accuracy: {}       │
                                    │                         │
                                    │  learned_domains.json   │
                                    └─────────────────────────┘
```

### Module Map

```
src/pane_awareness/
├── _compat.py          Platform detection, TTY helpers, file locking
├── config.py           TOML/JSON config loading, dataclass schema
├── state.py            Locked file I/O (fcntl on Unix, msvcrt on Windows)
│
├── registry.py         Pane registration, staleness detection
├── topics.py           Keyword extraction, trajectory classification
├── quadrant.py         macOS AppleScript + Linux xdotool window detection
│
├── messages.py         8-type messaging protocol
├── claims.py           Resource claiming lifecycle
├── domains.py          Topic-to-domain mapping + learning
│
├── convergence.py      4-signal prediction engine + self-calibration
├── cross_pollination.py  Compound signal orchestrator
├── handoff.py          Tiered context builder
├── delegation.py       Delegation suggestion engine
│
├── cli.py              CLI entry point (pa command)
└── __init__.py         Public API re-exports
```

## State File Schemas

### pane_registry.json

```json
{
  "panes": {
    "/dev/ttys001": {
      "session_id": "abc123",
      "tty": "/dev/ttys001",
      "cwd": "/Users/me/project",
      "project": "my-project",
      "quadrant": "top-left",
      "last_prompt": "fix the auth bug",
      "last_prompt_hash": "a1b2c3",
      "prompt_count": 42,
      "key_topics": ["auth", "jwt", "login"],
      "trajectory_window": [
        {"topics": ["auth", "jwt"], "hash": "a1b2c3"}
      ],
      "trajectory_vector": {
        "deepening": ["auth"],
        "emerging": ["jwt"],
        "fading": [],
        "stable": ["login"]
      },
      "created": "2024-01-01T12:00:00Z",
      "last_active": "2024-01-01T12:30:00Z"
    }
  },
  "message_log": [
    {
      "id": "msg_abc123",
      "from": "/dev/ttys001",
      "target": "/dev/ttys002",
      "message": "I'm done with auth",
      "msg_type": "info",
      "priority": "normal",
      "timestamp": "2024-01-01T12:30:00Z"
    }
  ]
}
```

### pane_claims.json

```json
{
  "claims": [
    {
      "resource": "file:src/auth.py",
      "holder_tty": "/dev/ttys001",
      "holder_project": "api-server",
      "scope": "exclusive",
      "reason": "refactoring login flow",
      "claimed_at": "2024-01-01T12:00:00Z",
      "last_active": "2024-01-01T12:30:00Z",
      "contested_by": null,
      "contested_at": null
    }
  ],
  "claims_log": []
}
```

### pane_predictions.json

```json
{
  "active_predictions": [
    {
      "type": "APPROACHING",
      "pane_a": "/dev/ttys001",
      "pane_b": "/dev/ttys003",
      "shared_topics": ["auth", "login"],
      "confidence": 0.42,
      "distance_estimate": 3,
      "recommendation": "Coordinate before proceeding",
      "created": "2024-01-01T12:15:00Z"
    }
  ],
  "resolved": [],
  "accuracy": {
    "prevented": 0,
    "occurred": 0,
    "false_positive": 0,
    "expired": 0,
    "threshold_adjustments": 0
  },
  "dynamic_threshold": 0.35
}
```

## Key Algorithms

### Topic Extraction

1. Lowercase and tokenize the prompt
2. Remove stop words (configurable set of ~80 common words + convergence noise words)
3. Remove identity noise (username, hostname, configurable extras)
4. Deduplicate and take top N by frequency in the prompt
5. Store in trajectory window (rolling last 10 prompt snapshots)

### Trajectory Classification

For each topic in the trajectory window:

- **deepening**: Appears in 60%+ of recent prompts AND frequency is increasing
- **emerging**: Appears only in the last 3 prompts (new topic)
- **fading**: Was present in older prompts but absent from the last 3
- **stable**: Consistent presence without significant trend

### Convergence Detection (4 Signals)

**MUTUAL_DEEPENING**: Both panes have the same topic in their "deepening" category.
- Confidence = 0.6 + (number of shared deepening topics * 0.1)

**APPROACHING**: Jaccard similarity of key_topics exceeds the dynamic threshold.
- Confidence = overlap_score * 0.8
- Distance estimate = prompts until likely collision

**CROSS_APPROACH**: Pane A is deepening into topics that Pane B has been stably working on.
- Confidence = 0.5 + (match count * 0.1)

**DOMAIN_PROXIMITY**: Different topics but same domain (via configured domain map).
- Confidence = 0.3 + (domain match score * 0.4)

### Self-Calibrating Thresholds

After every 10 resolved predictions:
- If false-positive rate > 30%: raise threshold by 0.05
- If occurred rate > 10% (things we should have predicted): lower threshold by 0.02
- Thresholds clamped to [0.15, 0.70]

### Claim Lifecycle

```
  UNCLAIMED
      │
      ▼ claim_resource()
  CLAIMED ──────────────▶ AUTO-EXPIRED (holder went stale)
      │                         │
      ▼ contest_claim()         ▼ (anyone can re-claim)
  CONTESTED                 UNCLAIMED
      │
      ▼ force_release() (after timeout or holder stale)
  UNCLAIMED
```

- Claims are **advisory** — no enforcement, just coordination signals
- A claim by a stale pane can be immediately overridden
- Contest timeout is configurable (default 120 seconds)
- The `get_active_claims()` function auto-cleans stale claims

## File Locking

All state file access goes through `state.py`:

```python
# Unix (macOS/Linux): fcntl
fcntl.flock(fd, fcntl.LOCK_EX)  # exclusive lock for writes
fcntl.flock(fd, fcntl.LOCK_SH)  # shared lock for reads

# Windows: msvcrt
msvcrt.locking(fd, msvcrt.LK_LOCK, size)  # exclusive lock
```

Read operations use shared locks (multiple readers OK). Write operations use exclusive locks (one writer at a time). Lock acquisition retries up to 3 times with 0.1s delay.

## Quadrant Detection

On macOS, the system uses AppleScript to query Terminal.app or iTerm2 for the current window's position and screen dimensions:

```
┌────────────┬────────────┐
│  top-left  │ top-right  │
│            │            │
├────────────┼────────────┤
│bottom-left │bottom-right│
│            │            │
└────────────┴────────────┘
```

Window center coordinates are compared against screen midpoints to determine quadrant. On Linux, `xdotool` is used (if available). On Windows, quadrant detection is not yet supported (returns None).
