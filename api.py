"""
Sports API client: fetch raw game data with retries and cache.
Delegates processing to games_processor.
"""
import asyncio
import ssl
import wifi
import socketpool
import adafruit_requests
from games_processor import process_games


class SportsAPI:
    """Facade: fetches raw games from API and returns processed game list."""

    def __init__(self, api_key):
        self.api_key = api_key
        self.pool = socketpool.SocketPool(wifi.radio)
        self.session = adafruit_requests.Session(self.pool, ssl.create_default_context())
        self.base_url = "https://sports-slim-api.vercel.app/api"
        self._cache = {}

    async def get_games(self, sport="NFL"):
        """Fetch and process games for the specified sport. Returns list of processed game dicts."""
        max_retries = 3
        retry_delay = 2

        for attempt in range(max_retries):
            try:
                print(f"Fetching {sport} games (attempt {attempt + 1}/{max_retries})")
                raw = self._get_raw_games(sport)
                if raw is None:
                    if attempt < max_retries - 1:
                        await asyncio.sleep(retry_delay)
                        retry_delay *= 2
                        continue
                    if sport in self._cache:
                        print(f"Using cached data for {sport}")
                        return self._cache[sport]
                    print(f"No cached data available for {sport}")
                    return []
                games = process_games(raw, sport)
                if games:
                    self._cache[sport] = games
                    print(f"Successfully fetched {len(games)} {sport} games")
                return games
            except Exception as e:
                print(f"Error fetching {sport} games (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    if sport in self._cache:
                        print(f"Using cached data for {sport}")
                        return self._cache[sport]
                    return []
        return []

    def _get_raw_games(self, sport):
        """GET raw games list from API. Returns list of dicts or None on failure."""
        url = f"{self.base_url}/{sport.lower()}/scores?api_key={self.api_key}"
        try:
            response = self.session.get(url)
            if response.status_code == 200:
                data = response.json()
                return data.get("games", [])
            print(f"API error: {response.status_code}")
            return None
        except Exception as e:
            print(f"Request failed: {e}")
            return None
