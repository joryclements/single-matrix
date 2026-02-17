"""
Boot sequence: WiFi connection and RTC time sync.
Keeps main.py focused on the display loop.
Print strings are kept short (e.g. "WiFi", "Sync") so if they are
echoed to the matrix display on boot, they fit on 64px width.
"""
import os
import time
import wifi
import socketpool
import ssl
import rtc
import adafruit_requests

WIFI_RETRIES = 3
WIFI_RETRY_DELAY = 5
TIME_URLS = [
    ("http://timeapi.io/api/time/current/zone?timeZone=UTC", "dateTime"),
    ("http://worldtimeapi.org/api/timezone/UTC", "datetime"),
]
TIME_SYNC_ATTEMPTS = 2
TIME_SYNC_DELAY = 2


def connect_wifi(max_retries=None):
    """Connect to WiFi using CIRCUITPY_WIFI_SSID and CIRCUITPY_WIFI_PASSWORD.
    Returns True if connected, False after all retries."""
    retries = max_retries if max_retries is not None else WIFI_RETRIES
    ssid = os.getenv("CIRCUITPY_WIFI_SSID")
    password = os.getenv("CIRCUITPY_WIFI_PASSWORD")
    print("WiFi")
    for attempt in range(retries):
        try:
            wifi.radio.connect(ssid, password)
            print("OK")
            return True
        except Exception as e:
            print(f"WiFi fail {attempt + 1}: {e}")
            if attempt < retries - 1:
                print("Retry")
                time.sleep(WIFI_RETRY_DELAY)
    print("WiFi fail")
    return False


def sync_rtc():
    """Synchronize RTC from time APIs. Requires WiFi already connected.
    Returns True if sync succeeded, False otherwise."""
    print("Sync")
    pool = socketpool.SocketPool(wifi.radio)
    session = adafruit_requests.Session(pool, ssl.create_default_context())
    logged_error = False
    for url, key in TIME_URLS:
        for attempt in range(TIME_SYNC_ATTEMPTS):
            try:
                response = session.get(url)
                if response.status_code == 200:
                    time_data = response.json()
                    datetime_str = time_data[key][:19]
                    year = int(datetime_str[0:4])
                    month = int(datetime_str[5:7])
                    day = int(datetime_str[8:10])
                    hour = int(datetime_str[11:13])
                    minute = int(datetime_str[14:16])
                    second = int(datetime_str[17:19])
                    rtc.RTC().datetime = time.struct_time(
                        (year, month, day, hour, minute, second, 0, 0, -1)
                    )
                    print("OK")
                    return True
                if not logged_error:
                    print(f"API {response.status_code}")
                    logged_error = True
            except Exception:
                if not logged_error:
                    print("Sync err")
                    logged_error = True
            time.sleep(TIME_SYNC_DELAY)
    print("Sync fail")
    return False


def check_wifi_reconnect(max_retries=None):
    """If WiFi is disconnected, attempt to reconnect with retries and backoff. Returns True if connected."""
    if wifi.radio.connected:
        return True
    retries = max_retries if max_retries is not None else WIFI_RETRIES
    ssid = os.getenv("CIRCUITPY_WIFI_SSID")
    password = os.getenv("CIRCUITPY_WIFI_PASSWORD")
    print("Reconnect")
    for attempt in range(retries):
        try:
            wifi.radio.connect(ssid, password)
            print("OK")
            return True
        except OSError as e:
            print(f"Fail {attempt + 1}")
            if attempt < retries - 1:
                time.sleep(WIFI_RETRY_DELAY)
    return False
