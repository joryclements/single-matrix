"""
Central configuration and display constants.
Reads from environment (settings.toml on CircuitPython); all numeric values are normalized to int/float.
"""
import os

# Display dimensions (64x32 LED matrix)
DISPLAY_WIDTH = 64
DISPLAY_HEIGHT = 32

# Layout: terminalio font advance (cell) width per character position. Glyph widths vary
# (e.g. "1", "V" ~3px, ":" ~1px, many letters ~5px); we use 6px per position for alignment.
CHAR_WIDTH = 6
PADDING = 2
TEAM_SPACE_CHARS = 3  # team abbrs max 3 chars

# Row baseline Y (pixels) for top / middle / bottom text on 32px-tall display
ROW_Y_TOP = 5
ROW_Y_MIDDLE = 16
ROW_Y_BOTTOM = 27

# Underline: pixels below top-row baseline for possession/batting indicator
UNDERLINE_Y_OFFSET = 9

# Baseball diamond: bitmap is 15px wide; center_x - 8 centers it. Y position above middle row.
DIAMOND_HALF_OFFSET = 8
DIAMOND_Y_OFFSET = 11

# Record separator (W-L) vertical position
SEPARATOR_Y = 25


def _int_env(key, default):
    """Get env value as int. CircuitPython may return int from settings.toml."""
    val = os.getenv(key, default)
    if val is None:
        return default
    try:
        return int(val)
    except (TypeError, ValueError):
        return default


def _bool_env(key, default=False):
    """Get env value as bool (e.g. DEBUG_DISPLAY)."""
    val = os.getenv(key, "false" if not default else "true")
    if val is None:
        return default
    if isinstance(val, bool):
        return val
    return str(val).lower() in ("1", "true", "yes")


# Intervals (seconds). Override in settings.toml.
DISPLAY_INTERVAL = _int_env("DISPLAY_INTERVAL", 7)
REFRESH_INTERVAL_LIVE = _int_env("REFRESH_INTERVAL_LIVE", 30)
REFRESH_INTERVAL_IDLE = _int_env("REFRESH_INTERVAL_IDLE", 300)

# Button debounce (seconds)
DEBOUNCE_TIME = 0.3

# When True, extra logging (e.g. per-game in get_filtered_games). Set DEBUG_DISPLAY = true in settings.toml.
DEBUG_DISPLAY = _bool_env("DEBUG_DISPLAY", False)

# Main loop policy
MAX_CONSECUTIVE_ERRORS = 5
WIFI_CHECK_INTERVAL = 600 # seconds
LIVE_STATUSES = ("In Progress", "Delayed", "Suspended")
