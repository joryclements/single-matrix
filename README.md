# Single Matrix — Sports Scoreboard

A CircuitPython app for the **Adafruit Matrix Portal** (or compatible board) that shows live and upcoming scores for NFL, NBA, NHL, and MLB on a 64×32 LED matrix. Use the **UP** button to toggle all games vs live-only; use the **DOWN** button to cycle sports (NFL → NBA → NHL → MLB → all).

## Hardware

- [Adafruit Matrix Portal](https://www.adafruit.com/product/4745) (or similar ESP32-S2 + matrix setup)
- 64×32 RGB LED matrix
- CircuitPython 8.x+ with WiFi and display support

## Setup

1. **Install CircuitPython** on the Matrix Portal and install the required libraries (Adafruit CircuitPython Bundle):
   - `adafruit_matrixportal`
   - `adafruit_requests`
   - `adafruit_display_text`
   - Plus any dependencies those pull in (see [CircuitPython bundle](https://circuitpython.org/libraries)).

2. **Copy this project** onto the `CIRCUITPY` drive so the root of the drive contains `code.py` and the rest of the `.py` files (or set `code.py` to run `main.py` via a one-line import).

3. **Configure settings:**
   - Copy `settings.toml.example` to `settings.toml` on the `CIRCUITPY` drive.
   - Edit `settings.toml` and set:
     - `CIRCUITPY_WIFI_SSID` / `CIRCUITPY_WIFI_PASSWORD` — your WiFi
     - `API_KEY` — API key for the sports API (e.g. [sports-slim-api](https://sports-slim-api.vercel.app))
   - Optional: adjust `REFRESH_INTERVAL_LIVE`, `REFRESH_INTERVAL_IDLE`, `DISPLAY_INTERVAL` (see example file).

4. **Rename or wire entrypoint:** If your main logic is in `main.py`, either:
   - Rename `main.py` to `code.py`, or  
   - Use a one-line `code.py`: `from main import *` / or run the async main from `main`.

## Running

- On power-up the device connects to WiFi, syncs time, then fetches games and cycles through them on the matrix.
- **UP** — toggle between “all games” and “live (and scheduled if no live)” for the current sport.
- **DOWN** — cycle sport: NFL → NBA → NHL → MLB → SPORTS (all).

## Configuration (settings.toml)

| Variable | Description | Example |
|----------|-------------|---------|
| `CIRCUITPY_WIFI_SSID` | WiFi network name | `"MyNetwork"` |
| `CIRCUITPY_WIFI_PASSWORD` | WiFi password | `"secret"` |
| `API_KEY` | Sports API key | `"your_key"` |
| `DISPLAY_INTERVAL` | Seconds each game is shown | `7` |
| `REFRESH_INTERVAL_LIVE` | Seconds between API refreshes when a game is live | `30` |
| `REFRESH_INTERVAL_IDLE` | Seconds between API refreshes when no live game | `300` |
| `DEBUG_DISPLAY` | Extra serial logging (games list, etc.) | `false` |

## Tests

Tests are unified under **`run_tests.run_display_tests(display_manager, mode)`** with three modes:

- **quick** — One game per sport; short run.
- **comprehensive** — All sports, statuses, edge cases, display modes, and sport transitions (uses shared mock data from `mock_games.py`).
- **status** — Status labels only (Rain Delay, Postponed, Suspended, Cancelled).

From `main.py` you can call `run_quick_test()` or `run_comprehensive_test()` (they delegate to `run_display_tests`). To run **status** tests, call `await run_display_tests(display_manager, "status")` or run **`test_status.py`** standalone (it creates its own matrix and display manager). Mock game data lives in **`mock_games.py`** and is used by both `comprehensive_display_test.py` and `test_status.py`.

## Project layout

- `main.py` — entrypoint, main loop (buttons via ButtonController)
- `boot.py` — WiFi connect, RTC sync, WiFi recheck (with retries)
- `buttons.py` — ButtonController (debounced UP/DOWN, no globals)
- `api.py` — sports API client (fetch + cache); delegates processing to `games_processor`
- `games_processor.py` — normalize status, filter old finals, build processed game dicts
- `game_display_builder.py` — build display_data for one game (scoreboard layout)
- `display_manager.py` — display state and scoreboard rendering
- `display_utils.py` — layout and sport-specific display helpers
- `utils.py` — colors, time formatting, record parsing
- `team_colors.py` — team color definitions
- `config.py` — display size, intervals, layout constants (row Y, underline, diamond, separator), env-backed settings
- `mock_games.py` — shared mock game data for tests
- `run_tests.py` — unified test runner (quick | comprehensive | status)
- `comprehensive_display_test.py` — full and quick display tests
- `test_status.py` — status-only test; run standalone or via `run_tests`

## Troubleshooting

- **WiFi fails:** Check SSID/password in `settings.toml` and that the board supports your WiFi band.
- **Time sync fails:** Game filtering uses RTC; if sync fails, check serial for “Time sync failed” and ensure the device can reach the time APIs.
- **“Safe Mode” / “Display Issue”:** The device enters a limited state after several consecutive errors; it will retry. Check API key and network.
