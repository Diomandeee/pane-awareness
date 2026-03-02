# Python API Reference

All functions are available from the top-level `pane_awareness` module:

```python
import pane_awareness as pa
```

## Pane Registry

### `update_pane(session_id, cwd, prompt_text)`

Register or update the current pane's state.

- **session_id** (str): Unique identifier for this session
- **cwd** (str): Current working directory
- **prompt_text** (str): The user's prompt text

Extracts topics, computes trajectory, auto-detects quadrant, and writes to the registry.

### `get_all_panes(include_stale=False)`

Returns a dict of `{tty: pane_data}` for all registered panes.

- **include_stale** (bool): If True, includes panes past the stale timeout

### `get_pane_info(tty=None)`

Get info for a specific pane. If `tty` is None, returns info for the current pane.

### `set_quadrant(quadrant)`

Manually set the quadrant label for the current pane. Returns True on success.

### `auto_detect_and_set_quadrant()`

Auto-detect quadrant from window position (macOS Terminal/iTerm2, Linux xdotool). Returns the detected quadrant string or None.

## Messages

### `send_message(target, message, priority="normal", msg_type="info")`

Send a message to another pane.

- **target** (str): TTY path, quadrant name ("top-left"), or "all"
- **message** (str): Message text
- **priority** (str): "normal" or "urgent"
- **msg_type** (str): One of: info, question, claim, release, delegate, handoff, ack, block

### `get_messages()`

Read unread messages for the current pane. Messages are archived after reading.

### `get_message_log(limit=50)`

Read the global message audit log. Returns the last `limit` entries.

### `send_handoff(target, task, context_blob=None, next_steps=None)`

Send a structured handoff message with context.

### `send_delegation(target, resource, reason="")`

Send a delegation suggestion to another pane.

### `send_question(target, question)`

Send a question to another pane.

### `send_ack(target, ref_message_id)`

Acknowledge receipt of a message.

### `send_block(target, reason)`

Signal that you're blocked and need help.

## Claims

### `claim_resource(resource, scope="exclusive", reason="")`

Claim a shared resource. Returns a dict with `status` ("granted" or "denied") and details.

- **resource** (str): Resource identifier (e.g., "file:src/auth.py", "port:8000")
- **scope** (str): "exclusive" or "shared"
- **reason** (str): Why you need this resource

### `release_resource(resource)`

Release a previously claimed resource.

### `contest_claim(resource, reason="")`

Contest a claim held by another pane. Starts the contest timer.

### `force_release(resource, reason="")`

Force-release a contested claim (only works after contest timeout or if holder is stale).

### `get_active_claims()`

Returns all active claims. Auto-cleans stale claims.

### `get_claims_log(limit=50)`

Returns the claims history log.

## Convergence & Predictions

### `detect_cross_pollination()`

Run the full compound signal analysis. Returns:

```python
{
    "overlap": [...],          # Keyword overlap between pane pairs
    "predictions": [...],      # Convergence predictions
    "opportunities": [...],    # Synergy opportunities
    "claim_conflicts": [...],  # Resource claim conflicts
    "handoff_opportunities": [...],
    "delegations": [...],      # Delegation suggestions
    "trajectory_summary": {...},
}
```

### `get_active_predictions()`

Returns currently active convergence predictions.

### `resolve_predictions()`

Resolve active predictions against current state. Classifies each as:
- **prevented**: Teams coordinated, no collision
- **occurred**: Collision happened despite warning
- **false_positive**: Prediction was wrong
- **expired**: Prediction timed out

### `predict_convergence(pane_a, pane_b)`

Run convergence detection between two specific panes.

### `detect_opportunities()`

Detect synergy opportunities across all panes.

## Handoff & Delegation

### `build_handoff_context(tier2_fields=None)`

Build a tiered handoff context blob for the current pane.

- **Tier 1** (automatic): project, CWD, recent prompts, git diff, active claims
- **Tier 2** (explicit): Additional fields passed via `tier2_fields`

### `suggest_delegations()`

Analyze all panes and suggest delegations based on trajectory drift and domain expertise.

### `detect_handoff_opportunities()`

Detect opportunities for context handoffs between panes.

## Domains

### `get_effective_domain_map()`

Returns the merged domain map (configured + learned). Maps domain names to lists of topic keywords.

## Configuration

### `get_config()`

Returns the current `PaneConfig` dataclass. Loaded lazily on first access.

### `reset_config()`

Force reload of configuration from disk.
