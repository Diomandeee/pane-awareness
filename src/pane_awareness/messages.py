"""8-type messaging protocol for cross-pane communication.

Message types: info, question, claim, release, delegate, handoff, ack, block.
Messages are delivered to pane inboxes and archived on read.
A global message log provides an audit trail.
"""

import hashlib
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from ._compat import get_current_tty
from .config import MESSAGE_TYPES, get_config
from .state import read_registry, write_registry


def _generate_message_id() -> str:
    """Generate a unique message ID: timestamp_ms + random hex."""
    ts = int(datetime.now(timezone.utc).timestamp() * 1000)
    rand = hashlib.md5(os.urandom(8)).hexdigest()[:6]
    return f"{ts}_{rand}"


def _append_to_message_log(data: Dict[str, Any], msg_obj: Dict[str, Any]) -> None:
    """Append a message to the global message_log with FIFO cap."""
    cfg = get_config()
    if "message_log" not in data:
        data["message_log"] = []
    data["message_log"].append(msg_obj)
    if len(data["message_log"]) > cfg.messages.log_cap:
        data["message_log"] = data["message_log"][-cfg.messages.log_cap:]


def send_message(
    target: str,
    message: str,
    priority: str = "normal",
    from_tty: Optional[str] = None,
    msg_type: str = "info",
    payload: Optional[Dict[str, Any]] = None,
    ref_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Send a typed message to another pane's inbox.

    Args:
        target: TTY path, quadrant name (e.g. "top-left"), or "all".
        message: Message text (human-readable summary).
        priority: "normal" or "urgent".
        from_tty: Sender TTY (auto-detected if None).
        msg_type: One of MESSAGE_TYPES keys (default "info").
        payload: Type-specific structured data.
        ref_id: ID of the message this responds to.

    Returns:
        Dict with sent count, message ID, and message type.
    """
    sender = from_tty or get_current_tty() or "unknown"

    if msg_type not in MESSAGE_TYPES:
        msg_type = "info"

    msg_id = _generate_message_id()
    now = datetime.now(timezone.utc).isoformat()

    msg_obj = {
        "id": msg_id,
        "from": sender,
        "msg_type": msg_type,
        "message": message,
        "priority": priority,
        "timestamp": now,
    }
    if payload:
        msg_obj["payload"] = payload
    if ref_id:
        msg_obj["ref_id"] = ref_id

    data = read_registry()
    panes = data.get("panes", {})

    sent_count = 0
    for tty, pane in panes.items():
        if tty == sender:
            continue

        should_send = False
        if target == "all":
            should_send = True
        elif target == tty:
            should_send = True
        elif target == pane.get("quadrant"):
            should_send = True

        if should_send:
            if "messages" not in pane:
                pane["messages"] = []
            pane["messages"].append(msg_obj)
            sent_count += 1

    _append_to_message_log(data, {
        "id": msg_id,
        "from": sender,
        "target": target,
        "msg_type": msg_type,
        "message": message[:200],
        "priority": priority,
        "timestamp": now,
        "ref_id": ref_id,
    })

    data["panes"] = panes
    write_registry(data)

    return {
        "sent_count": sent_count,
        "message_id": msg_id,
        "msg_type": msg_type,
    }


def get_messages(tty: Optional[str] = None) -> List[Dict[str, Any]]:
    """Read and archive messages from a pane's inbox.

    Messages are moved from the active inbox to read_messages
    (capped at read_cap) rather than deleted.

    Args:
        tty: TTY to read messages for. If None, uses current.

    Returns:
        List of message objects from the inbox.
    """
    my_tty = tty or get_current_tty()
    if not my_tty:
        return []

    cfg = get_config()
    data = read_registry()
    panes = data.get("panes", {})
    pane = panes.get(my_tty)
    if not pane:
        return []

    messages = pane.get("messages", [])
    if messages:
        read = pane.get("read_messages", [])
        read.extend(messages)
        if len(read) > cfg.messages.read_cap:
            read = read[-cfg.messages.read_cap:]
        pane["read_messages"] = read
        pane["messages"] = []
        data["panes"] = panes
        write_registry(data)

    return messages


def get_message_log(limit: int = 50) -> List[Dict[str, Any]]:
    """Read the global message log (audit trail).

    Args:
        limit: Maximum entries to return.

    Returns:
        List of recent message log entries.
    """
    data = read_registry()
    log = data.get("message_log", [])
    return log[-limit:]


def get_read_messages(tty: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
    """Read archived (previously read) messages for a pane.

    Args:
        tty: TTY to read archived messages for.
        limit: Maximum entries to return.

    Returns:
        List of archived message objects.
    """
    my_tty = tty or get_current_tty()
    if not my_tty:
        return []

    data = read_registry()
    panes = data.get("panes", {})
    pane = panes.get(my_tty)
    if not pane:
        return []

    return pane.get("read_messages", [])[-limit:]


def send_handoff(
    target: str,
    task: str,
    context_blob: Dict[str, Any],
    artifacts: Optional[List[str]] = None,
    next_steps: Optional[List[str]] = None,
    from_tty: Optional[str] = None,
) -> Dict[str, Any]:
    """Send a structured handoff to another pane.

    Args:
        target: Target pane (quadrant, TTY, or "all").
        task: Brief description of the work being handed off.
        context_blob: Structured context (schema, files, etc.).
        artifacts: List of files/resources produced.
        next_steps: Suggested actions for the receiving pane.
        from_tty: Sender (auto-detected).

    Returns:
        send_message result with message_id.
    """
    payload = {
        "task": task,
        "context_blob": context_blob,
        "artifacts": artifacts or [],
        "next_steps": next_steps or [],
    }
    return send_message(
        target=target,
        message=f"HANDOFF: {task}",
        priority="urgent",
        from_tty=from_tty,
        msg_type="handoff",
        payload=payload,
    )


def send_delegation(
    target: str,
    task: str,
    context: str,
    deadline: Optional[str] = None,
    from_tty: Optional[str] = None,
) -> Dict[str, Any]:
    """Delegate pending work to another pane.

    Args:
        target: Target pane (quadrant, TTY).
        task: Description of work to delegate.
        context: Context needed to do the work.
        deadline: Optional deadline description.
        from_tty: Sender (auto-detected).

    Returns:
        send_message result with message_id.
    """
    payload = {"task": task, "context": context}
    if deadline:
        payload["deadline"] = deadline
    return send_message(
        target=target,
        message=f"DELEGATE: {task}",
        priority="normal",
        from_tty=from_tty,
        msg_type="delegate",
        payload=payload,
    )


def send_question(
    target: str,
    question: str,
    choices: Optional[List[str]] = None,
    from_tty: Optional[str] = None,
) -> Dict[str, Any]:
    """Send a question to another pane expecting a response.

    Args:
        target: Target pane (quadrant, TTY).
        question: The question text.
        choices: Optional list of valid answers.
        from_tty: Sender (auto-detected).

    Returns:
        send_message result with message_id.
    """
    payload = {"message": question}
    if choices:
        payload["choices"] = choices
    return send_message(
        target=target,
        message=question,
        priority="normal",
        from_tty=from_tty,
        msg_type="question",
        payload=payload,
    )


def send_ack(
    target: str,
    ref_id: str,
    accepted: bool = True,
    reason: str = "",
    from_tty: Optional[str] = None,
) -> Dict[str, Any]:
    """Acknowledge a message (delegation, handoff, or question).

    Args:
        target: Target pane to ack to.
        ref_id: ID of the message being acknowledged.
        accepted: Whether the request is accepted.
        reason: Optional explanation.
        from_tty: Sender (auto-detected).

    Returns:
        send_message result.
    """
    payload = {"ref_id": ref_id, "accepted": accepted, "reason": reason}
    status = "ACK" if accepted else "NACK"
    return send_message(
        target=target,
        message=f"{status}: {reason}" if reason else status,
        priority="normal",
        from_tty=from_tty,
        msg_type="ack",
        payload=payload,
        ref_id=ref_id,
    )


def send_block(
    resource: str,
    blocker: str,
    unblock_hint: str = "",
    from_tty: Optional[str] = None,
) -> Dict[str, Any]:
    """Broadcast that a resource is blocked.

    Args:
        resource: The blocked resource (e.g. "port:8001").
        blocker: What is blocking it.
        unblock_hint: How to unblock.
        from_tty: Sender (auto-detected).

    Returns:
        send_message result.
    """
    payload = {
        "resource": resource,
        "blocker": blocker,
        "unblock_hint": unblock_hint,
    }
    return send_message(
        target="all",
        message=f"BLOCKED: {resource} by {blocker}",
        priority="urgent",
        from_tty=from_tty,
        msg_type="block",
        payload=payload,
    )
