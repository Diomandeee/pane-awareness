"""Quadrant detection — maps TTY to screen position.

Supports macOS Terminal.app, iTerm2, and a Linux stub (xdotool).
Falls back gracefully when detection is unavailable.
"""

import subprocess
from typing import Optional

from ._compat import IS_LINUX, IS_MACOS, get_current_tty
from .config import get_config


def detect_quadrant(tty: Optional[str] = None) -> Optional[str]:
    """Map a TTY to a screen quadrant via window geometry.

    Uses AppleScript on macOS (Terminal.app / iTerm2) or xdotool on Linux.
    Returns one of: "top-left", "top-right", "bottom-left", "bottom-right".

    Args:
        tty: The TTY to detect quadrant for. If None, tries current.

    Returns:
        Quadrant string or None if detection fails.
    """
    cfg = get_config()
    terminal = cfg.quadrant.terminal_app

    if terminal == "disabled":
        return None

    my_tty = tty or get_current_tty()
    if not my_tty:
        return None

    if IS_MACOS:
        if terminal in ("auto", "Terminal"):
            result = _detect_macos_terminal(my_tty)
            if result:
                return result
        if terminal in ("auto", "iTerm2"):
            result = _detect_macos_iterm(my_tty)
            if result:
                return result
    elif IS_LINUX:
        return _detect_linux(my_tty)

    return None


def auto_detect_and_set_quadrant() -> Optional[str]:
    """Detect quadrant and set it in the registry.

    Returns the detected quadrant or None.
    """
    quadrant = detect_quadrant()
    if quadrant:
        from .registry import set_quadrant
        set_quadrant(quadrant=quadrant)
    return quadrant


def _detect_macos_terminal(tty: str) -> Optional[str]:
    """Detect quadrant via macOS Terminal.app AppleScript."""
    tty_suffix = tty.replace("/dev/tty", "")

    script = '''tell application "Terminal"
    set results to {}
    repeat with w in windows
        try
            set ttyName to tty of w
            set {wx, wy} to position of w
            set {ww, wh} to size of w
            set cx to wx + (ww / 2)
            set cy to wy + (wh / 2)
            set end of results to ttyName & "|" & (cx as text) & "," & (cy as text)
        end try
    end repeat
    set AppleScript's text item delimiters to linefeed
    return results as text
end tell'''

    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode != 0 or not result.stdout.strip():
            return None
    except Exception:
        return None

    return _parse_window_positions(result.stdout, tty_suffix)


def _detect_macos_iterm(tty: str) -> Optional[str]:
    """Detect quadrant via macOS iTerm2 AppleScript."""
    tty_suffix = tty.replace("/dev/tty", "")

    script = '''tell application "iTerm2"
    set results to {}
    repeat with w in windows
        try
            set {wx, wy} to position of w
            set {ww, wh} to size of w
            set cx to wx + (ww / 2)
            set cy to wy + (wh / 2)
            repeat with t in tabs of w
                repeat with s in sessions of t
                    set ttyName to tty of s
                    set end of results to ttyName & "|" & (cx as text) & "," & (cy as text)
                end repeat
            end repeat
        end try
    end repeat
    set AppleScript's text item delimiters to linefeed
    return results as text
end tell'''

    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode != 0 or not result.stdout.strip():
            return None
    except Exception:
        return None

    return _parse_window_positions(result.stdout, tty_suffix)


def _detect_linux(tty: str) -> Optional[str]:
    """Detect quadrant via xdotool on Linux (best-effort stub)."""
    try:
        # Get all terminal windows
        result = subprocess.run(
            ["xdotool", "search", "--class", "terminal"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode != 0:
            return None

        # Get screen dimensions
        subprocess.run(
            ["xdpyinfo"],
            capture_output=True, text=True, timeout=5
        )
        # This is a stub — full Linux support would need to map
        # window IDs to PTY devices, which varies by terminal emulator.
        return None
    except Exception:
        return None


def _parse_window_positions(output: str, tty_suffix: str) -> Optional[str]:
    """Parse window position output and compute quadrant."""
    windows = []
    my_pos = None

    for line in output.strip().split("\n"):
        line = line.strip()
        if "|" not in line:
            continue
        tty_name, pos_str = line.split("|", 1)
        try:
            cx, cy = [float(v) for v in pos_str.split(",")]
            windows.append((tty_name.strip(), cx, cy))
            if tty_suffix in tty_name:
                my_pos = (cx, cy)
        except (ValueError, IndexError):
            continue

    if not my_pos or len(windows) < 2:
        return None

    all_x = [w[1] for w in windows]
    all_y = [w[2] for w in windows]
    mid_x = (min(all_x) + max(all_x)) / 2
    mid_y = (min(all_y) + max(all_y)) / 2

    cx, cy = my_pos
    if cx < mid_x and cy < mid_y:
        return "top-left"
    elif cx >= mid_x and cy < mid_y:
        return "top-right"
    elif cx < mid_x and cy >= mid_y:
        return "bottom-left"
    else:
        return "bottom-right"
