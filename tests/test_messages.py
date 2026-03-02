"""Tests for the messaging protocol."""

from unittest.mock import patch

from pane_awareness.messages import (
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


def test_send_message_to_all(four_panes):
    sender = "/dev/ttys001"
    with patch("pane_awareness.messages.get_current_tty", return_value=sender):
        result = send_message("all", "hello everyone")

    assert result["sent_count"] == 3  # 4 panes - 1 sender
    assert result["msg_type"] == "info"
    assert result["message_id"]


def test_send_message_to_quadrant(four_panes):
    sender = "/dev/ttys001"
    with patch("pane_awareness.messages.get_current_tty", return_value=sender):
        result = send_message("bottom-left", "hey bottom-left")

    assert result["sent_count"] == 1


def test_send_message_to_tty(four_panes):
    sender = "/dev/ttys001"
    with patch("pane_awareness.messages.get_current_tty", return_value=sender):
        result = send_message("/dev/ttys002", "direct message")

    assert result["sent_count"] == 1


def test_get_messages_archives(four_panes):
    sender = "/dev/ttys001"
    receiver = "/dev/ttys002"

    with patch("pane_awareness.messages.get_current_tty", return_value=sender):
        send_message(receiver, "test msg")

    with patch("pane_awareness.messages.get_current_tty", return_value=receiver):
        msgs = get_messages()

    assert len(msgs) == 1
    assert msgs[0]["message"] == "test msg"

    # Messages should now be archived
    with patch("pane_awareness.messages.get_current_tty", return_value=receiver):
        msgs2 = get_messages()
    assert len(msgs2) == 0

    # But readable from archive
    with patch("pane_awareness.messages.get_current_tty", return_value=receiver):
        archived = get_read_messages()
    assert len(archived) == 1


def test_message_log(four_panes):
    sender = "/dev/ttys001"
    with patch("pane_awareness.messages.get_current_tty", return_value=sender):
        send_message("all", "msg1")
        send_message("all", "msg2")

    log = get_message_log(limit=10)
    assert len(log) == 2
    assert log[0]["message"] == "msg1"
    assert log[1]["message"] == "msg2"


def test_send_handoff(four_panes):
    sender = "/dev/ttys001"
    with patch("pane_awareness.messages.get_current_tty", return_value=sender):
        result = send_handoff(
            target="top-right",
            task="finish the migration",
            context_blob={"files": ["001.sql"]},
            next_steps=["run migrate", "test"],
        )
    assert result["msg_type"] == "handoff"
    assert result["sent_count"] == 1


def test_send_delegation(four_panes):
    sender = "/dev/ttys001"
    with patch("pane_awareness.messages.get_current_tty", return_value=sender):
        result = send_delegation(
            target="bottom-right",
            task="review the PR",
            context="PR #42 needs review",
        )
    assert result["msg_type"] == "delegate"


def test_send_question(four_panes):
    sender = "/dev/ttys001"
    with patch("pane_awareness.messages.get_current_tty", return_value=sender):
        result = send_question(
            target="top-right",
            question="Should I use v2 or v3?",
            choices=["v2", "v3"],
        )
    assert result["msg_type"] == "question"


def test_send_ack(four_panes):
    sender = "/dev/ttys002"
    with patch("pane_awareness.messages.get_current_tty", return_value=sender):
        result = send_ack(
            target="/dev/ttys001",
            ref_id="12345_abc",
            accepted=True,
            reason="will do",
        )
    assert result["msg_type"] == "ack"


def test_send_block(four_panes):
    sender = "/dev/ttys001"
    with patch("pane_awareness.messages.get_current_tty", return_value=sender):
        result = send_block(
            resource="port:8001",
            blocker="another process",
            unblock_hint="kill PID 1234",
        )
    assert result["msg_type"] == "block"
    assert result["sent_count"] == 3
