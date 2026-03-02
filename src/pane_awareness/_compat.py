"""Platform compatibility layer.

Provides OS-agnostic file locking, TTY detection, and platform helpers.
Zero external dependencies — uses only the stdlib.
"""

import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

# Platform detection
IS_WINDOWS = sys.platform == "win32"
IS_MACOS = sys.platform == "darwin"
IS_LINUX = sys.platform.startswith("linux")


def lock_shared(fd: int) -> None:
    """Acquire a shared (read) lock on a file descriptor."""
    if IS_WINDOWS:
        import msvcrt
        msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
    else:
        import fcntl
        fcntl.flock(fd, fcntl.LOCK_SH)


def lock_exclusive(fd: int) -> None:
    """Acquire an exclusive (write) lock on a file descriptor."""
    if IS_WINDOWS:
        import msvcrt
        msvcrt.locking(fd, msvcrt.LK_LOCK, 1)
    else:
        import fcntl
        fcntl.flock(fd, fcntl.LOCK_EX)


def unlock(fd: int) -> None:
    """Release a lock on a file descriptor."""
    if IS_WINDOWS:
        import msvcrt
        msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
    else:
        import fcntl
        fcntl.flock(fd, fcntl.LOCK_UN)


def normalize_tty(raw: str) -> Optional[str]:
    """Normalize a TTY string to a canonical format.

    On macOS/Linux, ps -o tty= returns formats like:
    'ttys003', 's003', '/dev/ttys003', '??'

    We normalize all to '/dev/ttysNNN' (macOS) or '/dev/pts/N' (Linux).
    On Windows, returns None (no TTY concept).
    """
    if IS_WINDOWS:
        return None
    if not raw or raw in ("?", "??"):
        return None
    if raw.startswith("/dev/"):
        return raw
    if raw.startswith("tty"):
        return f"/dev/{raw}"
    if raw.startswith("pts/"):
        return f"/dev/{raw}"
    return f"/dev/tty{raw}"


def get_current_tty() -> Optional[str]:
    """Detect the TTY for the current process.

    Tries multiple methods:
    1. os.ttyname(0) — direct TTY name
    2. ps -o tty= with current PID
    3. ps -o tty= with parent PID (for hook subprocesses)

    Returns None on Windows or if detection fails.
    """
    if IS_WINDOWS:
        return None

    try:
        return os.ttyname(0)
    except (OSError, AttributeError):
        pass

    # Fallback: use ps to get TTY
    for pid in (os.getpid(), os.getppid()):
        try:
            result = subprocess.run(
                ["ps", "-o", "tty=", "-p", str(pid)],
                capture_output=True, text=True, timeout=2
            )
            tty = normalize_tty(result.stdout.strip())
            if tty:
                return tty
        except Exception:
            pass

    return None


def get_identity_noise() -> set:
    """Build a set of identity-related noise words to filter from topics.

    These are usernames, machine names, and common directory names that
    appear across all panes and create false cross-pollination signals.
    Users can add extras via config.
    """
    noise = {
        os.environ.get("USER", "").lower(),
        os.environ.get("LOGNAME", "").lower(),
        Path.home().name.lower(),
        "desktop", "projects",
    }
    return noise - {""}
