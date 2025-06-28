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

# Connect to WiFi
print("Connecting to WiFi...")
wifi.radio.connect(os.getenv("CIRCUITPY_WIFI_SSID"), os.getenv("CIRCUITPY_WIFI_PASSWORD"))
print(f"Connected to WiFi! IP: {wifi.radio.ipv4_address}")

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
            # Wait for message to be visible and fetch data
            await asyncio.sleep(2)  # Show message for 2 seconds
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
            # Wait for message to be visible and fetch data
            await asyncio.sleep(2)  # Show message for 2 seconds
            await display_manager.update_games()
            # Reset display timers by returning True
            fetch_data = True
    
    last_button_down_state = current_button_down_state
    return fetch_data

async def main():
    """Main program loop"""
    try:
        # Show startup message
        display_manager.display_static_text("Starting")
        await asyncio.sleep(0.5)
        
        # Fetch initial data
        print("Fetching initial data...")
        await display_manager.update_games()
        # Run the display manager with button checking
        last_update = 0
        last_display_time = 0
        display_interval = os.getenv("DISPLAY_INTERVAL", 7)  # Show each game for 8 seconds
        refresh_interval = os.getenv("REFRESH_INTERVAL", 10)  # Refresh every 10 seconds
        while True:
            try:
                current_time = time.monotonic()
                
                # Check buttons and see if we need to fetch data
                fetch_data = await check_buttons()
                
                # If fetch_data is True, reset our timers to force immediate display
                if fetch_data:
                    last_update = current_time
                    last_display_time = 0  # Force immediate display
                    continue
                
                # Update games every refresh_interval seconds
                if current_time - last_update >= refresh_interval:
                    await display_manager.update_games()
                    last_update = current_time
                    continue
                
                # Display current game every display_interval seconds
                if current_time - last_display_time >= display_interval:
                    await display_manager.display_current_game()
                    last_display_time = current_time
                
                # Small delay to avoid consuming too much CPU
                await asyncio.sleep(0.1)
                
            except Exception as e:
                print(f"Error in display loop: {e}")
                await asyncio.sleep(5)
        
    except Exception as e:
        print(f"Error in main: {e}")
        display_manager.display_static_text("Error!")
        await asyncio.sleep(5)

# Start the async event loop
asyncio.run(main())