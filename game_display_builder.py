"""
Builds display_data dict for a single game (scoreboard layout).
Used by DisplayManager; testable without hardware.

display_data contract (between builder and DisplayManager.display_scoreboard):
  - top_row, middle_row, bottom_row: lists of {"text": str, "color": int, "x": int}
  - optional: "underline" (TileGrid), "diamond" (TileGrid), "separators" (list of TileGrid)
  - Rows are rendered at y positions 5, 16, 27; items may be empty string (skipped).
"""
import displayio
from config import DISPLAY_WIDTH, CHAR_WIDTH, PADDING, TEAM_SPACE_CHARS, SEPARATOR_Y
from utils import (
    BLACK, WHITE, DIM_GRAY, GRAY,
    get_team_color, format_game_time, parse_team_record,
)
from display_utils import (
    create_baseball_diamond, create_underline, calculate_text_positions,
    get_text_width,
    handle_nfl_display, handle_mlb_display, handle_game_status,
)


class GameDisplayBuilder:
    """Builds the display_data dict for one game from bitmaps and game dict."""

    def __init__(self, base_bitmap, base_palette, separator_bitmap, separator_palette):
        self.base_bitmap = base_bitmap
        self.base_palette = base_palette
        self.separator_bitmap = separator_bitmap
        self.separator_palette = separator_palette

    def create_game_text(self, game, current_sport):
        """Create the display_data dict for the given game and current sport."""
        try:
            home_team_abbr = str(game.get("home_team", "UNK")).upper()
            away_team_abbr = str(game.get("away_team", "UNK")).upper()
            game_sport = game.get("sport", current_sport)
            home_color = get_team_color(home_team_abbr, game_sport)
            away_color = get_team_color(away_team_abbr, game_sport)
            home_team = home_team_abbr[:3] if home_team_abbr else "HOM"
            away_team = away_team_abbr[:3] if away_team_abbr else "AWY"
            home_score = str(game.get("home_score", 0))
            away_score = str(game.get("away_score", 0))

            # Scheduled: league in top row only. Other live games: sport in middle row.
            if game.get("status") in ["Postponed", "Delayed", "Suspended", "Cancelled", "Unknown"] or (
                game_sport == "MLB" and game.get("status") == "In Progress"
            ):
                middle_text = None
            elif game.get("status") == "Scheduled":
                middle_text = None
            else:
                middle_text = game_sport

            positions = calculate_text_positions(
                home_team, away_team, home_score, away_score,
                display_width=DISPLAY_WIDTH
            )
            display_data = {
                "top_row": [
                    {"text": away_team, "color": away_color, "x": positions["away_x"]},
                    {"text": home_team, "color": home_color, "x": positions["home_x"]},
                ],
                "middle_row": [
                    {"text": away_score, "color": WHITE, "x": positions["away_score_x"]},
                    {"text": home_score, "color": WHITE, "x": positions["home_score_x"]},
                ],
                "bottom_row": [],
            }
            if middle_text:
                middle_width = get_text_width(middle_text)
                middle_x = positions["center_x"] - (middle_width // 2)
                display_data["middle_row"].insert(
                    1, {"text": middle_text, "color": DIM_GRAY, "x": middle_x}
                )

            clock_text = handle_game_status(game, display_data, positions["center_x"])
            game_status = game.get("status", "Unknown")

            if game_status == "Final":
                self._handle_final_game(game, display_data, positions)
            elif game_status == "Scheduled":
                # Top row: TM1 [LEA] TM2 — league in top only, darker (GRAY); not in middle/bottom
                league_label = game_sport if game_sport in ("NFL", "NBA", "NHL", "MLB") else "LEA"
                league_w = get_text_width(league_label)
                league_x = positions["center_x"] - (league_w // 2)
                display_data["top_row"].insert(
                    1, {"text": league_label, "color": GRAY, "x": league_x}
                )
                self._handle_scheduled_game(game, display_data, positions, current_sport)
            elif game_status in ["Postponed", "Delayed", "Suspended", "Cancelled", "Unknown"] or "Delay" in str(game_status):
                self._handle_delayed_game(game, display_data, positions)
            else:
                period = str(game.get("period", ""))
                period_width = get_text_width(period)
                period_x = positions["center_x"] - (period_width // 2)
                display_data["top_row"].insert(1, {"text": period, "color": WHITE, "x": period_x})
                if game_sport == "NFL":
                    clock_text = handle_nfl_display(
                        game, display_data, home_team, away_team,
                        home_color, away_color, create_underline,
                        positions["away_x"], positions["home_x"]
                    ) or clock_text
                elif game_sport == "MLB":
                    clock_text = handle_mlb_display(
                        game, display_data, period, home_team, away_team,
                        home_color, away_color, create_underline,
                        lambda bases: create_baseball_diamond(
                            self.base_bitmap, self.base_palette, bases
                        ),
                        positions["away_x"], positions["home_x"], positions["center_x"],
                        positions["away_score_x"], positions["home_score_x"],
                    ) or clock_text
                if clock_text:
                    clock_width = len(clock_text) * 6
                    clock_x = positions["center_x"] - (clock_width // 2)
                    display_data["bottom_row"].append({"text": clock_text, "color": WHITE, "x": clock_x})

            return display_data
        except Exception as e:
            print(f"Error creating game text: {e}")
            return {
                "top_row": [{"text": "ERR", "color": WHITE, "x": 5}, {"text": "ERR", "color": WHITE, "x": 45}],
                "middle_row": [{"text": "Game Error", "color": WHITE, "x": 8}],
                "bottom_row": [],
            }

    def _handle_final_game(self, game, display_data, positions):
        home_score_int = int(game["home_score"])
        away_score_int = int(game["away_score"])
        display_data["middle_row"][0]["color"] = WHITE if away_score_int > home_score_int else DIM_GRAY
        display_data["middle_row"][-1]["color"] = WHITE if home_score_int > away_score_int else DIM_GRAY
        away_record = game.get("away_record", "")
        home_record = game.get("home_record", "")
        away_wins, away_losses = parse_team_record(away_record)
        home_wins, home_losses = parse_team_record(home_record)
        if away_wins and away_losses and home_wins and home_losses:
            self._add_team_records(
                display_data, positions, away_wins, away_losses, home_wins, home_losses
            )

    def _handle_scheduled_game(self, game, display_data, positions, current_sport):
        date = game.get("date", "")
        time_part = format_game_time(date)
        time_width = len(time_part) * 6
        time_x = positions["center_x"] - (time_width // 2)
        game_is_today = True
        try:
            import rtc
            now = rtc.RTC().datetime
            if date and "-" in date:
                dp = date.split("-")
                game_is_today = int(dp[1]) == now.tm_mon and int(dp[2][:2]) == now.tm_mday
        except Exception:
            pass
        # Remove league from middle row: only blank scores, or show date only when not today (no sport)
        display_data["middle_row"][0]["text"] = ""
        display_data["middle_row"][-1]["text"] = ""
        if len(display_data["middle_row"]) > 2:
            display_data["middle_row"].pop(1)
        if not game_is_today and date and "-" in date:
            try:
                dp = date.split("-")
                date_str = f"{int(dp[1])}/{int(dp[2][:2])}"
                date_w = get_text_width(date_str)
                date_x = positions["center_x"] - (date_w // 2)
                display_data["middle_row"].insert(
                    1, {"text": date_str, "color": DIM_GRAY, "x": date_x}
                )
            except Exception:
                pass
        display_data["bottom_row"].append({"text": time_part, "color": DIM_GRAY, "x": time_x})

    def _handle_delayed_game(self, game, display_data, positions):
        status = game.get("status", "Unknown")
        display_text = self._get_status_display_text(status)
        display_data["middle_row"] = [
            {"text": display_text, "color": DIM_GRAY, "x": positions["center_x"] - (len(display_text) * 6 // 2)}
        ]
        try:
            home_score = int(game.get("home_score", 0))
            away_score = int(game.get("away_score", 0))
        except (ValueError, TypeError):
            home_score = away_score = 0
        status_lower = status.lower()
        if (home_score > 0 or away_score > 0) and ("rain" in status_lower or "weather" in status_lower):
            display_data["bottom_row"] = [
                {"text": str(away_score), "color": WHITE, "x": positions["away_score_x"]},
                {"text": str(home_score), "color": WHITE, "x": positions["home_score_x"]},
            ]
        else:
            away_record = game.get("away_record", "")
            home_record = game.get("home_record", "")
            away_wins, away_losses = parse_team_record(away_record)
            home_wins, home_losses = parse_team_record(home_record)
            if away_wins and away_losses and home_wins and home_losses:
                self._add_team_records(
                    display_data, positions, away_wins, away_losses, home_wins, home_losses
                )

    def _get_status_display_text(self, status):
        status_map = {
            "Postponed": "POSTPONED",
            "Delayed": "DELAY",
            "Suspended": "SUSPENDED",
            "Cancelled": "CANCELLED",
            "Rain Delay": "RAIN DELAY",
            "Weather Delay": "RAIN DELAY",
            "Unknown": "UNKNOWN",
        }
        status_lower = status.lower()
        if "rain" in status_lower or "weather" in status_lower:
            return "RAIN DELAY"
        if "delay" in status_lower:
            return "DELAY"
        if "suspend" in status_lower:
            return "SUSPENDED"
        if "cancel" in status_lower:
            return "CANCELLED"
        if "postpone" in status_lower:
            return "POSTPONED"
        return status_map.get(status, status[:10].upper())

    def _add_team_records(self, display_data, positions, away_wins, away_losses, home_wins, home_losses):
        away_width_wins = len(away_wins) * CHAR_WIDTH
        away_width_losses = len(away_losses) * CHAR_WIDTH
        home_width_wins = len(home_wins) * CHAR_WIDTH
        home_width_losses = len(home_losses) * CHAR_WIDTH
        away_record_x = 0
        home_record_x = DISPLAY_WIDTH - home_width_wins - home_width_losses - PADDING
        center_gap = home_record_x - (away_record_x + away_width_wins + away_width_losses)
        if center_gap >= 0:
            display_data["bottom_row"].append({"text": away_wins, "color": DIM_GRAY, "x": away_record_x})
            away_sep = displayio.TileGrid(self.separator_bitmap, pixel_shader=self.separator_palette)
            away_sep.x = away_record_x + away_width_wins
            away_sep.y = SEPARATOR_Y
            display_data["separators"] = [away_sep]
            display_data["bottom_row"].append(
                {"text": away_losses, "color": DIM_GRAY, "x": away_record_x + away_width_wins + PADDING}
            )
            display_data["bottom_row"].append({"text": home_wins, "color": DIM_GRAY, "x": home_record_x})
            home_sep = displayio.TileGrid(self.separator_bitmap, pixel_shader=self.separator_palette)
            home_sep.x = home_record_x + home_width_wins
            home_sep.y = SEPARATOR_Y
            display_data["separators"].append(home_sep)
            display_data["bottom_row"].append(
                {"text": home_losses, "color": DIM_GRAY, "x": home_record_x + home_width_wins + PADDING}
            )
