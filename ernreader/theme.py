"""Win95/98 look-and-feel: colors, fonts and classic reliefs.

This module centralizes the "époque" styling so the engine and launcher stay
free of magic constants. Fonts are mapped from the VB names (MS Sans Serif,
Courier New, ...) to families that actually exist on Linux (Liberation / DejaVu)
with sensible fallbacks for Windows and macOS.
"""

from __future__ import annotations

import tkinter.font as tkfont


# --- Classic Win95 system palette -------------------------------------------
# These mirror the values the extractor resolves for &H8000000X& system colors.
BUTTON_FACE = "#C0C0C0"      # 0F ButtonFace  -- the iconic grey
BUTTON_SHADOW = "#808080"    # 10 ButtonShadow
BUTTON_HILIGHT = "#FFFFFF"   # 14 ButtonHighlight
BUTTON_TEXT = "#000000"      # 12 ButtonText
WINDOW = "#FFFFFF"           # 05 Window
WINDOW_TEXT = "#000000"      # 08 WindowText
HIGHLIGHT = "#000080"        # 0D Highlight (selection navy)
HIGHLIGHT_TEXT = "#FFFFFF"   # 0E HighlightText
DESKTOP = "#008080"          # 01 Desktop (teal)
ACTIVE_TITLE = "#000080"     # 02 ActiveTitle
INACTIVE_TITLE = "#808080"   # 0A InactiveTitle

# Convenience aliases used by the launcher chrome.
FACE = BUTTON_FACE
SHADOW = BUTTON_SHADOW
LIGHT = BUTTON_HILIGHT
DARK = "#000000"


# --- Font mapping ------------------------------------------------------------
# Ordered candidate families per logical VB font. First available wins.
_FONT_CANDIDATES = {
    "ms sans serif": ["MS Sans Serif", "Microsoft Sans Serif", "Tahoma",
                      "Liberation Sans", "DejaVu Sans", "Helvetica"],
    "microsoft sans serif": ["Microsoft Sans Serif", "Liberation Sans",
                             "DejaVu Sans", "Helvetica"],
    "arial": ["Arial", "Liberation Sans", "DejaVu Sans", "Helvetica"],
    "tahoma": ["Tahoma", "Liberation Sans", "DejaVu Sans", "Helvetica"],
    "courier new": ["Courier New", "Liberation Mono", "DejaVu Sans Mono",
                    "Courier 10 Pitch", "Courier"],
    "courier": ["Courier New", "Liberation Mono", "DejaVu Sans Mono", "Courier"],
    "fixedsys": ["FixedSys", "Liberation Mono", "DejaVu Sans Mono", "Courier"],
    "terminal": ["Terminal", "Liberation Mono", "DejaVu Sans Mono", "Courier"],
    "system": ["Liberation Sans", "DejaVu Sans", "Helvetica"],
    "times new roman": ["Times New Roman", "Liberation Serif", "DejaVu Serif",
                        "Times"],
    "ms serif": ["Liberation Serif", "DejaVu Serif", "Times"],
}

_DEFAULT_CANDIDATES = ["Liberation Sans", "DejaVu Sans", "Helvetica", "Arial"]

# Populated by init_theme() once a Tk root exists.
_available_families: set[str] | None = None
_resolved_cache: dict[str, str] = {}


# --- HiDPI scaling ------------------------------------------------------------
# Design pixels (manifest coordinates, thought for 96dpi) are multiplied by
# SCALE at render time. See docs/FEATURES.md §1.
SCALE = 1.0


def init_scale(root, requested="auto"):
    """Set the global UI scale factor. Called by the Launcher after creating
    the Tk root, before building any UI. ``requested`` is "auto" or a number
    as string/float."""
    global SCALE
    if requested in (None, "", "auto"):
        try:
            factor = root.winfo_fpixels("1i") / 96.0
        except Exception:
            factor = 1.0
        factor = round(factor * 4) / 4          # nearest 0.25
    else:
        try:
            factor = float(requested)
        except (TypeError, ValueError):
            factor = 1.0
    SCALE = min(max(factor, 1.0), 3.0)
    return SCALE


def s(px):
    """Scale a design-pixel measure to real pixels."""
    return int(round(px * SCALE))


def init_theme(root) -> None:
    """Detect the families actually installed. Call once with a live Tk root."""
    global _available_families
    try:
        fams = tkfont.families(root)
        _available_families = {f.lower() for f in fams}
    except Exception:
        _available_families = None
    _resolved_cache.clear()


def _pick_family(vb_name: str | None) -> str:
    key = (vb_name or "").strip().lower()
    if key in _resolved_cache:
        return _resolved_cache[key]
    candidates = _FONT_CANDIDATES.get(key, [vb_name] if vb_name else [])
    candidates = list(candidates) + _DEFAULT_CANDIDATES
    chosen = _DEFAULT_CANDIDATES[0]
    if _available_families is None:
        # No detection yet: trust the first candidate; Tk will substitute.
        chosen = next((c for c in candidates if c), _DEFAULT_CANDIDATES[0])
    else:
        for cand in candidates:
            if cand and cand.lower() in _available_families:
                chosen = cand
                break
    _resolved_cache[key] = chosen
    return chosen


def resolve_font(font_dict: dict | None, default_size: int = 8):
    """Return a Tk font spec tuple from a manifest font dict.

    VB sizes are in points; we keep them positive so Tk interprets them as
    points (negative would mean pixels).
    """
    if not font_dict:
        family = _pick_family("MS Sans Serif")
        size = default_size
        styles: list[str] = []
    else:
        family = _pick_family(font_dict.get("name"))
        size = font_dict.get("size") or default_size
        try:
            size = int(round(float(size)))
        except (TypeError, ValueError):
            size = default_size
        if size <= 0:
            size = default_size
        styles = []
        if font_dict.get("bold"):
            styles.append("bold")
        if font_dict.get("italic"):
            styles.append("italic")
        if font_dict.get("underline"):
            styles.append("underline")
    # Point sizes are scaled by SCALE: Tk renders points at the display's own
    # DPI and does not know about our manual HiDPI factor. s() == identity at
    # SCALE=1, so this is a no-op in the default (unscaled) path.
    size = max(1, s(size))
    return (family, size, *styles)


def ui_font(size: int = 8, bold: bool = False):
    """Font spec for the launcher chrome (MS Sans Serif equivalent)."""
    fam = _pick_family("MS Sans Serif")
    size = max(1, s(size))
    return (fam, size, "bold") if bold else (fam, size)


def mono_font(size: int = 9):
    return (_pick_family("Courier New"), size)
