"""
Game processing: normalize status, filter old finals, and build processed game dicts.
Used by the API layer; can be tested with raw dicts without HTTP.
"""
import time
import rtc
from config import ACTIVE_STATUSES, DEBUG_DISPLAY

# Normalize API status strings to canonical display status (dict lookup + keywords fallback).
STATUS_MAP = {
    "final": "Final", "f": "Final",
    "scheduled": "Scheduled", "pre-game": "Scheduled",
    "in progress": "In Progress", "i": "In Progress",
    "halftime": "In Progress", "half time": "In Progress",
    "end of period": "In Progress", "end period": "In Progress",
    "between periods": "In Progress",
    "postponed": "Postponed", "ppd": "Postponed",
    "suspended": "Suspended",
    "cancelled": "Cancelled", "canceled": "Cancelled",
}
DELAY_KEYWORDS = ("delay", "rain", "weather", "lightning")
CANCEL_KEYWORDS = ("void", "forfeit", "abandon")
TWENTY_FOUR_HOURS = 24 * 60 * 60
THIRTY_SIX_HOURS = 36 * 60 * 60


def get_rtc_now():
    """Return current RTC as epoch seconds, or None if unavailable."""
    try:
        current_time = rtc.RTC().datetime
        return time.mktime((
            current_time.tm_year, current_time.tm_mon, current_time.tm_mday,
            current_time.tm_hour, current_time.tm_min, current_time.tm_sec, 0, 0, -1
        ))
    except Exception:
        return None


def parse_game_timestamp(date):
    """Parse API date string to epoch seconds, or None if unparseable."""
    if not date or "-" not in date:
        return None
    try:
        y, m, d = int(date[:4]), int(date[5:7]), int(date[8:10])
        h, mn = int(date[11:13]), int(date[14:16])
        return time.mktime((y, m, d, h, mn, 0, 0, 0, -1))
    except (ValueError, IndexError):
        return None


def is_game_in_time_window(game, now=None):
    """
    Whether a processed game falls within the display time window.
    Active games are always included. Finals within 24h and other games
    within the next 36h are included. Returns True when RTC is unavailable.
    """
    if now is None:
        now = get_rtc_now()
        if now is None:
            return True

    status = game.get("status", "")
    if status in ACTIVE_STATUSES:
        return True

    game_ts = parse_game_timestamp(game.get("date", ""))
    if game_ts is None:
        return True

    if status == "Final":
        return game_ts >= now - TWENTY_FOUR_HOURS

    return now <= game_ts <= now + THIRTY_SIX_HOURS


def is_game_date_today(date):
    """True if the game's calendar date matches the RTC day (month/day)."""
    if not date or "-" not in date:
        return True
    try:
        now = rtc.RTC().datetime
        return int(date[5:7]) == now.tm_mon and int(date[8:10]) == now.tm_mday
    except Exception:
        return True


def normalize_and_infer_status(raw_status, game, sport):
    """Normalize status string and infer unknown states from game data."""
    if not raw_status:
        return _infer_status_from_game_data(raw_status, game, sport)
    lower = str(raw_status).strip().lower()
    normalized = STATUS_MAP.get(lower)
    if normalized:
        return normalized
    if any(k in lower for k in DELAY_KEYWORDS):
        return "Delayed"
    if any(k in lower for k in CANCEL_KEYWORDS):
        return "Cancelled"
    return _infer_status_from_game_data(raw_status, game, sport)


def _infer_status_from_game_data(raw_status, game, sport):
    """Infer game status from scores, period, and other game data."""
    try:
        try:
            home_score = int(game.get("home_score", 0))
            away_score = int(game.get("away_score", 0))
        except (ValueError, TypeError):
            home_score = away_score = 0
        period = game.get("period", "")
        quarter = game.get("quarter", "")
        inning = game.get("inning", "")
        game_period = game.get("game_period", "")

        if home_score == 0 and away_score == 0:
            if DEBUG_DISPLAY:
                print(f"Inferring pre-game status for unknown state: {raw_status}")
            return "Scheduled"
        has_scores = home_score > 0 or away_score > 0
        if has_scores:
            try:
                if sport == "NFL" and quarter and int(quarter) >= 4:
                    if DEBUG_DISPLAY:
                        print(f"Inferring final status for NFL game in Q{quarter}: {raw_status}")
                    return "Final"
                if sport == "NBA" and quarter and int(quarter) >= 4:
                    if DEBUG_DISPLAY:
                        print(f"Inferring final status for NBA game in Q{quarter}: {raw_status}")
                    return "Final"
                if sport == "NHL" and game_period and int(game_period) >= 3:
                    if DEBUG_DISPLAY:
                        print(f"Inferring final status for NHL game in P{game_period}: {raw_status}")
                    return "Final"
                if sport == "MLB" and inning and int(inning) >= 9:
                    if DEBUG_DISPLAY:
                        print(f"Inferring final status for MLB game in inning {inning}: {raw_status}")
                    return "Final"
            except (ValueError, TypeError):
                pass
            if DEBUG_DISPLAY:
                print(f"Inferring delayed status for game with scores: {raw_status}")
            return "Delayed"
        if DEBUG_DISPLAY:
            print(f"Could not infer status, treating as delayed: {raw_status}")
        return "Delayed"
    except Exception as e:
        print(f"Error inferring status from game data: {e}")
        return "Delayed"


def process_games(raw_games, sport):
    """
    Process raw API game list into simplified display format.
    Normalizes status, filters by time window when RTC is available:
    finals older than 24h and non-active games more than 36h in the future.
    When RTC fails, skips time-based filtering so games are not incorrectly dropped.
    """
    processed = []
    now = get_rtc_now()
    if now is None:
        print("RTC unavailable; skipping time-based filtering")

    for i, game in enumerate(raw_games):
        try:
            if not isinstance(game, dict):
                if DEBUG_DISPLAY:
                    print(f"Skipping invalid game {i+1}: not a dictionary")
                continue
            raw_status = game.get("status", "Unknown")
            home_team = game.get("home_abbreviation", "UNK")
            away_team = game.get("away_abbreviation", "UNK")
            home_score = game.get("home_score", 0)
            away_score = game.get("away_score", 0)
            date = game.get("date", "")
            venue = game.get("venue", "")
            home_record = game.get("home_record", "")
            away_record = game.get("away_record", "")

            period = ""
            if "inning" in game and "inning_half" in game:
                inning = game.get("inning", "")
                inning_half = game.get("inning_half", "")
                if inning and inning_half and len(inning_half) > 0:
                    period = f"{inning_half[0].upper()}{inning}"
            if not period:
                if "quarter" in game:
                    period = game.get("quarter", "")
                elif "game_period" in game:
                    period = game.get("game_period", "")

            clock = ""
            if "time_remaining" in game:
                clock = game.get("time_remaining", "")
            elif "game_clock" in game:
                clock = game.get("game_clock", "")

            down_distance = game.get("down_distance", "")
            possession = game.get("possession", "")
            count = game.get("count", {})
            bases = game.get("bases", {})
            last_play = game.get("last_play", "")

            status = normalize_and_infer_status(raw_status, game, sport)
            if DEBUG_DISPLAY and raw_status != status:
                print(f"Debug: Status normalized from '{raw_status}' to '{status}'")

            candidate = {
                "home_team": home_team,
                "away_team": away_team,
                "home_score": home_score,
                "away_score": away_score,
                "status": status,
                "period": period,
                "clock": clock,
                "date": date,
                "venue": venue,
                "home_record": home_record,
                "away_record": away_record,
                "last_play": last_play,
                "down_distance": down_distance,
                "possession": possession,
                "count": count,
                "bases": bases,
            }
            if now is not None and not is_game_in_time_window(candidate, now):
                if DEBUG_DISPLAY:
                    print(f"Filtered out-of-window game: {away_team} @ {home_team} on {date} ({status})")
                continue

            processed.append(candidate)
            if DEBUG_DISPLAY:
                print(f"Processed: {home_team} vs {away_team} - Status: {status}, Period: {period}, Clock: {clock}")
        except Exception as e:
            print(f"Error processing game {i+1}: {e}")
            if DEBUG_DISPLAY:
                print(f"Skipping malformed game data: {game}")
    return processed
