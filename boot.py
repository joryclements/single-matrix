"""
Boot sequence: WiFi connection and RTC time sync.
Keeps main.py focused on the display loop.
Print strings are kept short so boot progress fits on the 64px-wide matrix.

Set TIMEZONE in settings.toml (e.g. America/New_York) so RTC matches local
time; otherwise IP-based lookup is used. Sync uses timeapi.io and time.now (worldtimeapi.org is shut down).
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

# Prefer local timezone when TIMEZONE is set; otherwise fall back to IP-based local time.
_TIMEZONE = os.getenv("TIMEZONE", "").strip() or None


def _build_time_urls():
    """Ordered fallbacks for RTC sync. worldtimeapi.org shut down (410); use timeapi.io + time.now."""
    urls = []
    if _TIMEZONE:
        tz_query = _TIMEZONE.replace("/", "%2F")
        urls.append((
            f"https://timeapi.io/api/Time/current/zone?timeZone={tz_query}",
            "dateTime",
        ))
    # IP-based local time (no API key)
    urls.append(("https://time.now/developer/api/ip", "datetime"))
    # Last resort: UTC
    urls.append((
        "https://timeapi.io/api/Time/current/zone?timeZone=UTC",
        "dateTime",
    ))
    return urls


TIME_URLS = _build_time_urls()
TIME_SYNC_ATTEMPTS = 2
TIME_SYNC_DELAY = 2
TIME_SYNC_TIMEOUT = 10  # seconds; avoid hanging boot if time API is slow/unreachable


def _timezone_short():
    """Short display name from TIMEZONE, e.g. America/New_York -> New York."""
    if not _TIMEZONE:
        return None
    return _TIMEZONE.split("/")[-1].replace("_", " ")[:9]


def _sync_source_name(url):
    """Human-readable source name for serial logs."""
    if "time.now" in url:
        return "IP geolocation"
    if "timeZone=UTC" in url:
        return "UTC"
    if _TIMEZONE and "timeapi.io" in url:
        return f"timezone {_timezone_short() or _TIMEZONE}"
    return "time API"


def _sync_display_line2(url, source_idx, source_count, attempt=0, extra=""):
    """Second matrix line: step + plain-English source (~10 chars)."""
    step = f"{source_idx + 1}/{source_count}"
    if extra:
        return f"{step} {extra}"[:10]
    if attempt > 0:
        return f"{step} Retry"[:10]
    if "time.now" in url:
        return f"{step} By IP"
    if "timeZone=UTC" in url:
        return f"{step} UTC"
    if _TIMEZONE and "timeapi.io" in url:
        tz = _timezone_short()
        if tz and len(f"{step} {tz}") <= 10:
            return f"{step} {tz}"
        return f"{step} Local"
    return f"{step} Time"


def _boot_notify(on_progress, line1, line2=""):
    """Update boot display (if callback set) and print to serial."""
    serial = f"{line1} {line2}".strip()
    print(serial)
    if on_progress:
        on_progress(line1, line2)


def connect_wifi(max_retries=None, on_progress=None):
    """Connect to WiFi using CIRCUITPY_WIFI_SSID and CIRCUITPY_WIFI_PASSWORD.
    Returns True if connected, False after all retries."""
    retries = max_retries if max_retries is not None else WIFI_RETRIES
    ssid = os.getenv("CIRCUITPY_WIFI_SSID")
    password = os.getenv("CIRCUITPY_WIFI_PASSWORD")
    for attempt in range(retries):
        _boot_notify(on_progress, "WiFi", f"Try {attempt + 1}/{retries}")
        try:
            wifi.radio.connect(ssid, password)
            _boot_notify(on_progress, "WiFi", "Connected")
            return True
        except Exception as e:
            print(f"WiFi fail {attempt + 1}: {e}")
            if attempt < retries - 1:
                _boot_notify(on_progress, "WiFi", "Retrying")
                time.sleep(WIFI_RETRY_DELAY)
    _boot_notify(on_progress, "WiFi", "Failed")
    return False


def sync_rtc(on_progress=None):
    """Synchronize RTC from time APIs. Requires WiFi already connected.
    Returns True if sync succeeded, False otherwise."""
    pool = socketpool.SocketPool(wifi.radio)
    session = adafruit_requests.Session(pool, ssl.create_default_context())
    source_count = len(TIME_URLS)
    _boot_notify(on_progress, "Clock", "Starting")

    for source_idx, (url, key) in enumerate(TIME_URLS):
        name = _sync_source_name(url)
        step = f"{source_idx + 1}/{source_count}"
        for attempt in range(TIME_SYNC_ATTEMPTS):
            line2 = _sync_display_line2(url, source_idx, source_count, attempt)
            print(f"Clock sync {step} {name} try {attempt + 1}/{TIME_SYNC_ATTEMPTS}")
            _boot_notify(on_progress, "Clock", line2)

            try:
                response = session.get(url, timeout=TIME_SYNC_TIMEOUT)
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
                    _boot_notify(on_progress, "Clock", "Set OK")
                    print(f"RTC set via {name} ({step})")
                    return True
                print(f"Clock sync HTTP {response.status_code} ({name} {step})")
                _boot_notify(on_progress, "Clock", _sync_display_line2(
                    url, source_idx, source_count, attempt, str(response.status_code)
                ))
            except Exception as e:
                print(f"Clock sync err {name} {step}: {e}")
                _boot_notify(on_progress, "Clock", _sync_display_line2(
                    url, source_idx, source_count, attempt, "Error"
                ))
            time.sleep(TIME_SYNC_DELAY)

    _boot_notify(on_progress, "Clock", "Failed")
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
