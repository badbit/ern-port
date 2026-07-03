"""Session persistence (docs/FEATURES.md §3).

Stores a tiny JSON blob with the last issue that was open and which forms
were open in it, so the launcher can offer a "continue where you left off"
shortcut. IO is best-effort: any failure is logged to stderr and swallowed --
this is a convenience feature, never a reason to crash the app.

Location (respects XDG on Linux, %APPDATA% on Windows):
    $XDG_DATA_HOME/ernreader/state.json          (Linux/macOS, default
    ~/.local/share/ernreader/state.json)
    %APPDATA%/ernreader/state.json                (Windows)
"""

from __future__ import annotations

import os
import sys
import json
import time


def _log(msg: str) -> None:
    print(f"[ernreader] {msg}", file=sys.stderr)


def _state_dir() -> str:
    if sys.platform.startswith("win"):
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
        return os.path.join(base, "ernreader")
    xdg = os.environ.get("XDG_DATA_HOME")
    base = xdg if xdg else os.path.join(os.path.expanduser("~"), ".local", "share")
    return os.path.join(base, "ernreader")


def _state_path() -> str:
    return os.path.join(_state_dir(), "state.json")


def load_state() -> dict | None:
    """Return the saved state dict, or None if there is none / it's unreadable."""
    path = _state_path()
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except FileNotFoundError:
        return None
    except (OSError, json.JSONDecodeError) as exc:
        _log(f"could not read session state ({path}): {exc}")
        return None
    if not isinstance(data, dict):
        return None
    return data


def save_state(data: dict) -> None:
    """Persist ``data`` (expected keys: last_issue, open_forms, ts). Never
    raises; IO problems are logged to stderr and otherwise ignored."""
    path = _state_path()
    payload = dict(data)
    payload.setdefault("ts", time.time())
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        tmp_path = path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=2)
        os.replace(tmp_path, path)
    except OSError as exc:
        _log(f"could not save session state ({path}): {exc}")
