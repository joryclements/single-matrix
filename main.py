import os
import asyncio
import board
import digitalio
import displayio
import time
import terminalio
from adafruit_matrixportal.matrix import Matrix
from adafruit_display_text.label import Label
from api import SportsAPI
import wifi
from boot import connect_wifi, sync_rtc, check_wifi_reconnect
from config import (
    DISPLAY_WIDTH,
    DISPLAY_HEIGHT,
    DEBOUNCE_TIME,
    DISPLAY_INTERVAL,
    REFRESH_INTERVAL_LIVE,
    REFRESH_INTERVAL_IDLE,
    MAX_CONSECUTIVE_ERRORS,
    WIFI_CHECK_INTERVAL,
    ACTIVE_STATUSES,
)
from display_manager import DisplayManager
from buttons import ButtonController
from utils import WHITE

# Initialize the Matrix
matrix = Matrix(width=DISPLAY_WIDTH, height=DISPLAY_HEIGHT, bit_depth=6)
display = matrix.display


def _show_boot_message(line1, line2=""):
    """Show 1–2 short lines centered on the matrix (64x32). Keep lines ~8 chars."""
    group = displayio.Group()
    text = line1 if not line2 else f"{line1}\n{line2}"
    lines = text.split("\n")
    num_lines = len(lines)
    if num_lines == 1:
        y_positions = [DISPLAY_HEIGHT // 2]
    else:
        line_height = min(10, DISPLAY_HEIGHT // num_lines)
        start_y = (DISPLAY_HEIGHT - (line_height * (num_lines - 1))) // 2
        y_positions = [start_y + (i * line_height) for i in range(num_lines)]

    for i, line in enumerate(lines):
        label = Label(terminalio.FONT, text=line, color=WHITE)
        label.anchor_point = (0.5, 0.5)
        label.anchored_position = (DISPLAY_WIDTH // 2, y_positions[i])
        group.append(label)
    display.root_group = group


def _on_boot_progress(line1, line2=""):
    _show_boot_message(line1, line2)


# Set up buttons and controller
button_up = digitalio.DigitalInOut(board.BUTTON_UP)
button_up.direction = digitalio.Direction.INPUT
button_up.pull = digitalio.Pull.UP
button_down = digitalio.DigitalInOut(board.BUTTON_DOWN)
button_down.direction = digitalio.Direction.INPUT
button_down.pull = digitalio.Pull.UP
button_controller = ButtonController(button_up, button_down, debounce_seconds=DEBOUNCE_TIME)

# Boot: WiFi and RTC (progress shown on matrix + serial)
if connect_wifi(on_progress=_on_boot_progress):
    if not sync_rtc(on_progress=_on_boot_progress):
        print("No RTC sync; time filters may be skipped")
else:
    print("WiFi failed; skipping RTC sync")
    _on_boot_progress("Clock", "No WiFi")

_show_boot_message("Load", "Scores")

# Initialize API and Display Manager
api = SportsAPI(os.getenv("API_KEY"))
display_manager = DisplayManager(display, api)


def _refresh_interval_for_games(games):
    """Return refresh interval (seconds) based on whether any game is live."""
    has_live = any(g.get("status") in ACTIVE_STATUSES for g in games) if games else False
    return REFRESH_INTERVAL_LIVE if has_live else REFRESH_INTERVAL_IDLE


async def _do_fetch_phase():
    """Run fetch phase; returns (success, new_interval). On error returns (False, None)."""
    try:
        await display_manager.update_games()
        return (True, _refresh_interval_for_games(display_manager.games))
    except Exception as e:
        print(f"Error updating games: {e}")
        return (False, None)


async def _do_display_phase():
    """Run display phase. Returns True on success. On error may show Display Issue and sleep."""
    try:
        await display_manager.display_current_game()
        return True
    except (OSError, RuntimeError) as e:
        print(f"Display error: {e}")
        import traceback
        print(traceback.format_exc())
        current_games = display_manager.get_filtered_games()
        if current_games and display_manager.current_game_index < len(current_games):
            g = current_games[display_manager.current_game_index]
            print(f"Game: {g.get('away_team', '?')} vs {g.get('home_team', '?')}")
        return False


async def main():
    """Main program loop"""
    try:
        display_manager.display_static_text("Starting")
        await asyncio.sleep(0.5)
        try:
            await display_manager.update_games()
        except Exception as e:
            print(f"Error fetching initial data: {e}")
            display_manager.display_static_text("Init\nError")
            await asyncio.sleep(3)
        last_update = 0
        last_display_time = 0
        refresh_interval = REFRESH_INTERVAL_IDLE
        error_count = 0
        last_wifi_check = 0
        
        while True:
            try:
                current_time = time.monotonic()

                # Phase 1: if WiFi is down, show message and wait until it comes back
                if not wifi.radio.connected:
                    display_manager.display_static_text("WiFi\nDown")
                    while not wifi.radio.connected:
                        check_wifi_reconnect()
                        if not wifi.radio.connected:
                            await asyncio.sleep(5)
                    last_wifi_check = current_time
                    last_update = 0
                    last_display_time = 0
                    continue

                # Phase 1b: periodic WiFi check when connected
                if current_time - last_wifi_check >= WIFI_CHECK_INTERVAL:
                    try:
                        check_wifi_reconnect()
                        last_wifi_check = current_time
                    except OSError as e:
                        print(f"WiFi check failed: {e}")

                # Phase 2: buttons (may trigger fetch and reset timers)
                try:
                    fetch_data = await button_controller.check(display_manager)
                except OSError as e:
                    print(f"Error reading buttons: {e}")
                    fetch_data = False
                
                # If fetch_data is True, reset our timers to force immediate display
                if fetch_data:
                    last_update = current_time
                    last_display_time = 0  # Force immediate display
                    continue
                
                # Phase 3: refresh games on interval
                if current_time - last_update >= refresh_interval:
                    ok, new_interval = await _do_fetch_phase()
                    if ok:
                        last_update = current_time
                        error_count = 0
                        if new_interval and new_interval != refresh_interval:
                            print(f"Refresh: {refresh_interval}s -> {new_interval}s")
                            refresh_interval = new_interval
                    else:
                        error_count += 1
                        if error_count >= MAX_CONSECUTIVE_ERRORS:
                            display_manager.display_static_text("Safe\nMode")
                            await asyncio.sleep(30)
                            error_count = 0
                        else:
                            last_update = current_time
                    continue

                # Phase 4: advance display (hardware boundary)
                if current_time - last_display_time >= DISPLAY_INTERVAL:
                    if await _do_display_phase():
                        last_display_time = current_time
                        error_count = 0
                    else:
                        error_count += 1
                        current_games = display_manager.get_filtered_games()
                        if error_count >= MAX_CONSECUTIVE_ERRORS:
                            try:
                                display_manager.display_static_text("Display\nIssue")
                            except (OSError, RuntimeError):
                                pass
                            await asyncio.sleep(10)
                            error_count = 0
                        else:
                            n = len(current_games) if current_games else 1
                            display_manager.current_game_index = (display_manager.current_game_index + 1) % n
                        last_display_time = current_time
                
                # Small delay to avoid consuming too much CPU
                await asyncio.sleep(0.1)
                
            except Exception as e:
                print(f"Critical: {e}")
                import traceback
                print(traceback.format_exc())
                error_count += 1
                if error_count >= MAX_CONSECUTIVE_ERRORS:
                    try:
                        display_manager.display_static_text("System\nRestart")
                    except (OSError, RuntimeError):
                        pass
                    await asyncio.sleep(10)
                    last_update = 0
                    last_display_time = 0
                    error_count = 0
                else:
                    await asyncio.sleep(5)
        
    except Exception as e:
        print(f"Error in main: {e}")
        display_manager.display_static_text("Error!")
        await asyncio.sleep(5)

# Start the async event loop
asyncio.run(main())