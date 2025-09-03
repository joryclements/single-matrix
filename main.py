import os
import wifi
import asyncio
import board
import digitalio
import time
import rtc
import socketpool
import ssl
import adafruit_requests
from adafruit_matrixportal.matrix import Matrix
from api import SportsAPI
from display_manager import DisplayManager
from comprehensive_display_test import run_comprehensive_display_test
# Constants
DISPLAY_WIDTH = 64
DISPLAY_HEIGHT = 32

# Initialize the Matrix
matrix = Matrix(width=DISPLAY_WIDTH, height=DISPLAY_HEIGHT, bit_depth=6)
display = matrix.display

# Set up buttons
button_up = digitalio.DigitalInOut(board.BUTTON_UP)
button_up.direction = digitalio.Direction.INPUT
button_up.pull = digitalio.Pull.UP

button_down = digitalio.DigitalInOut(board.BUTTON_DOWN)
button_down.direction = digitalio.Direction.INPUT
button_down.pull = digitalio.Pull.UP

# Connect to WiFi with retry logic
print("Connecting to WiFi...")
wifi_retries = 3
for attempt in range(wifi_retries):
    try:
        wifi.radio.connect(os.getenv("CIRCUITPY_WIFI_SSID"), os.getenv("CIRCUITPY_WIFI_PASSWORD"))
        print(f"Connected to WiFi! IP: {wifi.radio.ipv4_address}")
        break
    except Exception as e:
        print(f"WiFi connection attempt {attempt + 1} failed: {e}")
        if attempt < wifi_retries - 1:
            print("Retrying WiFi connection...")
            time.sleep(5)
        else:
            print("Failed to connect to WiFi after all attempts")
            # Could potentially continue with cached data if available

# Synchronize time using world time API
print("Synchronizing time...")
try:
    pool = socketpool.SocketPool(wifi.radio)
    requests = adafruit_requests.Session(pool, ssl.create_default_context())
    response = requests.get("http://worldtimeapi.org/api/timezone/UTC")
    if response.status_code == 200:
        time_data = response.json()
        # Parse datetime string like "2024-06-28T15:30:45.123456+00:00"
        datetime_str = time_data["datetime"][:19]  # Get just "2024-06-28T15:30:45"
        year = int(datetime_str[0:4])
        month = int(datetime_str[5:7])
        day = int(datetime_str[8:10])
        hour = int(datetime_str[11:13])
        minute = int(datetime_str[14:16])
        second = int(datetime_str[17:19])
        
        # Set RTC time (year, month, day, hour, minute, second, weekday, yearday)
        rtc.RTC().datetime = time.struct_time((year, month, day, hour, minute, second, 0, 0, -1))
        print(f"Time synchronized: {rtc.RTC().datetime}")
    else:
        print(f"Failed to get time: {response.status_code}")
except Exception as e:
    print(f"Time sync failed: {e}")

# Initialize API and Display Manager
api = SportsAPI(os.getenv("API_KEY"))
display_manager = DisplayManager(display, api)

# Button state tracking
last_button_up_state = True
last_button_up_time = 0
last_button_down_state = True
last_button_down_time = 0
DEBOUNCE_TIME = 0.3  # 300ms debounce

def check_wifi_connection():
    """Check if WiFi is still connected and reconnect if needed"""
    try:
        if not wifi.radio.connected:
            print("WiFi disconnected, attempting reconnection...")
            wifi.radio.connect(os.getenv("CIRCUITPY_WIFI_SSID"), os.getenv("CIRCUITPY_WIFI_PASSWORD"))
            print("WiFi reconnected successfully")
            return True
        return True
    except Exception as e:
        print(f"WiFi reconnection failed: {e}")
        return False

async def check_buttons():
    """Check button states and handle presses"""
    global last_button_up_state, last_button_up_time, last_button_down_state, last_button_down_time
    
    current_time = time.monotonic()
    fetch_data = False
    
    # Check UP button (toggle between all games and active/scheduled games)
    current_button_up_state = button_up.value
    if not current_button_up_state and last_button_up_state and (current_time - last_button_up_time) > DEBOUNCE_TIME:
        # print("UP button pressed - toggling game display mode")
        fetch_data, reset_display = display_manager.toggle_game_display()
        if fetch_data or reset_display:
            last_button_up_time = current_time
            
            # Fetch data
            await display_manager.update_games()
            
            # Reset display timers by returning True
            fetch_data = True
    
    last_button_up_state = current_button_up_state
    
    # Check DOWN button (toggle between sports)
    current_button_down_state = button_down.value
    if not current_button_down_state and last_button_down_state and (current_time - last_button_down_time) > DEBOUNCE_TIME:
        # print("DOWN button pressed - toggling sport")
        fetch_data, reset_display = display_manager.toggle_sport()
        if fetch_data or reset_display:
            last_button_down_time = current_time
            # Fetch data
            await display_manager.update_games()
            
            # Reset display timers by returning True
            fetch_data = True
    
    last_button_down_state = current_button_down_state
    return fetch_data

async def run_comprehensive_test():
    """Run the comprehensive test suite"""
    print("🚀 Starting Comprehensive Test Suite...")
    await run_comprehensive_display_test(display_manager, "comprehensive")

async def run_quick_test():
    """Run a quick test suite"""
    print("⚡ Starting Quick Test Suite...")
    await run_comprehensive_display_test(display_manager, "quick")

async def main():
    """Main program loop"""
    try:
        # Show startup message
        display_manager.display_static_text("Starting")
        await asyncio.sleep(0.5)
        
        # Fetch initial data with error handling
        print("Starting display...")
        
        try:
            # Fetch data
            await display_manager.update_games()
        except Exception as e:
            print(f"Error fetching initial data: {e}")
            display_manager.display_static_text("Init\nError")
            await asyncio.sleep(3)
        # Run the display manager with button checking
        last_update = 0
        last_display_time = 0
        display_interval = os.getenv("DISPLAY_INTERVAL", 7)  # Show each game for 8 seconds
        refresh_interval = os.getenv("REFRESH_INTERVAL", 10)  # Refresh every 10 seconds
        error_count = 0
        max_errors = 5  # Maximum consecutive errors before entering safe mode
        last_wifi_check = 0
        wifi_check_interval = 60  # Check WiFi every 60 seconds
        
        while True:
            try:
                current_time = time.monotonic()
                
                # Periodically check WiFi connection
                if current_time - last_wifi_check >= wifi_check_interval:
                    try:
                        check_wifi_connection()
                        last_wifi_check = current_time
                    except Exception as e:
                        print(f"Error checking WiFi: {e}")
                
                # Check buttons and see if we need to fetch data
                try:
                    fetch_data = await check_buttons()
                except Exception as e:
                    print(f"Error checking buttons: {e}")
                    fetch_data = False
                
                # If fetch_data is True, reset our timers to force immediate display
                if fetch_data:
                    last_update = current_time
                    last_display_time = 0  # Force immediate display
                    continue
                
                # Update games every refresh_interval seconds
                if current_time - last_update >= refresh_interval:
                    try:
                        await display_manager.update_games()
                        last_update = current_time
                        error_count = 0  # Reset error count on successful operation
                    except Exception as e:
                        print(f"Error updating games: {e}")
                        error_count += 1
                        if error_count >= max_errors:
                            print("Too many consecutive errors, entering safe mode")
                            display_manager.display_static_text("Safe\nMode")
                            await asyncio.sleep(30)  # Wait longer in safe mode
                            error_count = 0  # Reset after safe mode
                        else:
                            last_update = current_time  # Still update timer to avoid rapid retries
                    continue
                
                # Display current game every display_interval seconds
                if current_time - last_display_time >= display_interval:
                    try:
                        await display_manager.display_current_game()
                        last_display_time = current_time
                        error_count = 0  # Reset error count on successful operation
                    except Exception as e:
                        print(f"Error displaying game: {e}")
                        print(f"Error type: {type(e)}")
                        try:
                            import traceback
                            print(f"Full traceback:\n{traceback.format_exc()}")
                        except:
                            print("Could not get traceback")
                        
                        # Try to get current game info for debugging
                        try:
                            current_games = display_manager.get_filtered_games()
                            if current_games and display_manager.current_game_index < len(current_games):
                                current_game = current_games[display_manager.current_game_index]
                                print(f"Problematic game: {current_game.get('away_team', 'UNK')} vs {current_game.get('home_team', 'UNK')}")
                                print(f"Game status: {current_game.get('status', 'UNK')}")
                        except:
                            print("Could not get current game info")
                            
                        error_count += 1
                        if error_count >= max_errors:
                            print("Too many display errors, showing error message")
                            display_manager.display_static_text("Display\nIssue")
                            await asyncio.sleep(10)
                            error_count = 0
                        else:
                            # Skip to next game to avoid getting stuck on the same problematic game
                            try:
                                display_manager.current_game_index = (display_manager.current_game_index + 1) % len(display_manager.get_filtered_games())
                                print(f"Skipping to next game, index now: {display_manager.current_game_index}")
                            except:
                                print("Could not skip to next game")
                        
                        last_display_time = current_time  # Still update timer
                
                # Small delay to avoid consuming too much CPU
                await asyncio.sleep(0.1)
                
            except Exception as e:
                print(f"Critical error in main loop: {e}")
                print(f"Critical error type: {type(e)}")
                try:
                    import traceback
                    print(f"Critical error traceback:\n{traceback.format_exc()}")
                except:
                    print("Could not get critical error traceback")
                    
                error_count += 1
                if error_count >= max_errors:
                    print("Critical system error, restarting display")
                    try:
                        display_manager.display_static_text("System\nRestart")
                        await asyncio.sleep(10)
                        # Reset everything
                        last_update = 0
                        last_display_time = 0
                        error_count = 0
                    except:
                        print("Cannot display error message, continuing...")
                        await asyncio.sleep(5)
                else:
                    await asyncio.sleep(5)
        
    except Exception as e:
        print(f"Error in main: {e}")
        display_manager.display_static_text("Error!")
        await asyncio.sleep(5)

# Start the async event loop
asyncio.run(main())