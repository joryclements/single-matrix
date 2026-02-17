import ssl
import wifi
import socketpool
import adafruit_requests
import time
import rtc

class SportsAPI:
    def __init__(self, api_key):
        self.api_key = api_key
        self.pool = socketpool.SocketPool(wifi.radio)
        self.session = adafruit_requests.Session(self.pool, ssl.create_default_context())
        self.base_url = "https://sports-slim-api.vercel.app/api"
        self.last_good_data = {}  # Cache for fallback data
        
    async def get_games(self, sport="NFL"):
        """Fetch games for the specified sport with retry logic"""
        max_retries = 3
        retry_delay = 2  # seconds
        
        for attempt in range(max_retries):
            try:
                print(f"Fetching {sport} games (attempt {attempt + 1}/{max_retries})")
                url = f"{self.base_url}/{sport.lower()}/scores?api_key={self.api_key}"
                
                # Set timeout for request (CircuitPython doesn't support timeout in get)
                response = self.session.get(url)
                
                if response.status_code == 200:
                    data = response.json()
                    games = self.process_games(data["games"], sport)
                    # Cache successful data
                    if games:
                        self.last_good_data[sport] = games
                        print(f"Successfully fetched {len(games)} {sport} games")
                    return games
                else:
                    print(f"API error: {response.status_code}")
                    if attempt < max_retries - 1:
                        print(f"Retrying in {retry_delay} seconds...")
                        time.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                        continue
                        
            except Exception as e:
                print(f"Error fetching {sport} games (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    print(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    # All retries failed, try to return cached data
                    if sport in self.last_good_data:
                        print(f"Using cached data for {sport}")
                        return self.last_good_data[sport]
                    print(f"No cached data available for {sport}")
        
        return []  # Return empty list if all attempts fail
    
    def _normalize_and_infer_status(self, raw_status, game, sport):
        """Normalize status and intelligently infer unknown states"""
        try:
            # First, try standard normalization
            if raw_status in ["Final", "final", "FINAL", "F"]:
                return "Final"
            elif raw_status in ["Scheduled", "scheduled", "SCHEDULED", "Pre-Game", "pre-game", "PRE-GAME"]:
                return "Scheduled"
            elif raw_status in ["In Progress", "in progress", "IN PROGRESS", "I"]:
                return "In Progress"
            elif raw_status in ["Postponed", "postponed", "POSTPONED", "PPD"]:
                return "Postponed"
            elif raw_status in ["Suspended", "suspended", "SUSPENDED"]:
                return "Suspended"
            elif raw_status in ["Cancelled", "cancelled", "CANCELLED", "Canceled", "canceled"]:
                return "Cancelled"
            elif raw_status in ["End of Period", "End Period", "Between Periods", "Halftime", "Half Time", "HALFTIME"]:
                # Handle end of period/quarter/half - these are still in progress
                return "In Progress"
            elif any(keyword in raw_status.lower() for keyword in ["delay", "rain", "weather", "lightning"]):
                # Handle various delay statuses (Rain Delay, Weather Delay, Lightning Delay, etc.)
                return "Delayed"
            elif any(keyword in raw_status.lower() for keyword in ["void", "forfeit", "abandon"]):
                # Handle other game termination statuses
                return "Cancelled"
            else:
                # Unknown status - try to infer from game data
                return self._infer_status_from_game_data(raw_status, game, sport)
                
        except Exception as e:
            print(f"Error normalizing status '{raw_status}': {e}")
            return "Unknown"
    
    def _infer_status_from_game_data(self, raw_status, game, sport):
        """Infer game status from scores, period, and other game data"""
        try:
            # Safely convert scores to integers
            try:
                home_score = int(game.get("home_score", 0))
                away_score = int(game.get("away_score", 0))
            except (ValueError, TypeError):
                home_score = away_score = 0
            
            period = game.get("period", "")
            quarter = game.get("quarter", "")
            inning = game.get("inning", "")
            game_period = game.get("game_period", "")
            
            # If no scores, likely pre-game
            if home_score == 0 and away_score == 0:
                print(f"Inferring pre-game status for unknown state: {raw_status}")
                return "Scheduled"
            
            # If there are scores, check if game is likely finished
            has_scores = home_score > 0 or away_score > 0
            
            if has_scores:
                # Check if we're at or beyond expected end of game
                try:
                    if sport == "NFL":
                        # NFL has 4 quarters
                        if quarter and int(quarter) >= 4:
                            print(f"Inferring final status for NFL game in Q{quarter}: {raw_status}")
                            return "Final"
                    elif sport == "NBA":
                        # NBA has 4 quarters 
                        if quarter and int(quarter) >= 4:
                            print(f"Inferring final status for NBA game in Q{quarter}: {raw_status}")
                            return "Final"
                    elif sport == "NHL":
                        # NHL has 3 periods
                        if game_period and int(game_period) >= 3:
                            print(f"Inferring final status for NHL game in P{game_period}: {raw_status}")
                            return "Final"
                    elif sport == "MLB":
                        # MLB has 9 innings minimum
                        if inning and int(inning) >= 9:
                            print(f"Inferring final status for MLB game in inning {inning}: {raw_status}")
                            return "Final"
                except (ValueError, TypeError):
                    # If period/quarter/inning isn't a valid number, continue with other logic
                    pass
                
                # If we have scores but not at end of expected periods, likely delayed/suspended
                print(f"Inferring delayed status for game with scores: {raw_status}")
                return "Delayed"
            
            # Default for truly unknown cases - make it actionable
            print(f"Could not infer status, treating as delayed: {raw_status}")
            return "Delayed"  # Better than leaving raw unknown status
            
        except Exception as e:
            print(f"Error inferring status from game data: {e}")
            # Return a safe fallback instead of raw status
            return "Delayed"
            
    def process_games(self, games, sport):
        """Process the raw games data into a simplified format"""
        processed_games = []
        
        # Get current time and 24-hour window (in seconds since epoch)
        # Use RTC to get actual current time, not uptime
        try:
            current_time = rtc.RTC().datetime
            # Convert struct_time to timestamp (year, month, day, hour, minute, second, weekday, yearday, dst)
            now_tuple = (current_time.tm_year, current_time.tm_mon, current_time.tm_mday, 
                         current_time.tm_hour, current_time.tm_min, current_time.tm_sec, 0, 0, -1)
            now = time.mktime(now_tuple)
        except Exception as e:
            print(f"Error getting current time, using fallback: {e}")
            # Fallback to a reasonable timestamp if RTC fails
            now = 1735344000  # Jan 1, 2025 as fallback
        
        twenty_four_hours_seconds = 24 * 60 * 60  # 24 hours in seconds
        
        print(f"Processing {len(games)} games from API")
        
        for i, game in enumerate(games):
            try:
                # Validate game data structure
                if not isinstance(game, dict):
                    print(f"Skipping invalid game {i+1}: not a dictionary")
                    continue
                
                raw_status = game.get("status", "Unknown")
                
                # Get all relevant fields with proper fallbacks
                # Common fields across all sports
                home_team = game.get("home_abbreviation", "UNK")
                away_team = game.get("away_abbreviation", "UNK")
                home_score = game.get("home_score", 0)
                away_score = game.get("away_score", 0)
                date = game.get("date", "")
                venue = game.get("venue", "")
                home_record = game.get("home_record", "")
                away_record = game.get("away_record", "")
            
                # Sport-specific fields with fallbacks based on API documentation
                # Period/quarter information
                period = ""
                if "quarter" in game:  # NBA/NFL
                    period = game.get("quarter", "")
                elif "game_period" in game:  # NHL
                    period = game.get("game_period", "")
                elif "inning" in game and "inning_half" in game:  # MLB
                    inning = game.get("inning", "")
                    inning_half = game.get("inning_half", "")
                    if inning and inning_half and len(inning_half) > 0:
                        # Format as "T1" for Top 1st, "B9" for Bottom 9th
                        period = f"{inning_half[0].upper()}{inning}"
            
                # Clock/time information
                clock = ""
                if "time_remaining" in game:  # NBA
                    clock = game.get("time_remaining", "")
                elif "game_clock" in game:  # NHL
                    clock = game.get("game_clock", "")
            
                # Additional sport-specific fields
                # NFL
                down_distance = game.get("down_distance", "")
                possession = game.get("possession", "")
                
                # MLB
                count = game.get("count", {})
                bases = game.get("bases", {})
                
                # Last play for all sports
                last_play = game.get("last_play", "")
            
                # Normalize status with intelligent inference for unknown states
                status = self._normalize_and_infer_status(raw_status, game, sport)
                if raw_status != status:
                    print(f"Debug: Status normalized from '{raw_status}' to '{status}'")
            
                # Filter out old final games (>24h), keep everything else
                # The API already returns only relevant upcoming games
                if date and status == "Final":
                    try:
                        year, month, day = int(date[:4]), int(date[5:7]), int(date[8:10])
                        hour, minute = int(date[11:13]), int(date[14:16])
                        game_time_tuple = (year, month, day, hour, minute, 0, 0, 0, -1)
                        game_timestamp = time.mktime(game_time_tuple)
                        if game_timestamp < now - twenty_four_hours_seconds:
                            continue
                    except (ValueError, IndexError):
                        print(f"Could not parse date for game: {date}")
                        continue
            
                processed_game = {
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
                    "bases": bases
                }
                processed_games.append(processed_game)
                
                # Debug the processed game
                print(f"Processed: {home_team} vs {away_team} - Status: {status}, Period: {period}, Clock: {clock}")
                
            except Exception as e:
                print(f"Error processing game {i+1}: {e}")
                print(f"Skipping malformed game data: {game}")
                continue
            
        return processed_games