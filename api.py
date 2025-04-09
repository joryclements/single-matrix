import ssl
import wifi
import socketpool
import adafruit_requests

class SportsAPI:
    def __init__(self, api_key):
        self.api_key = api_key
        self.pool = socketpool.SocketPool(wifi.radio)
        self.session = adafruit_requests.Session(self.pool, ssl.create_default_context())
        self.base_url = "https://sports-slim-api.vercel.app/api"
        
    async def get_games(self, sport="NFL"):
        """Fetch games for the specified sport"""
        try:
            url = f"{self.base_url}/{sport.lower()}/scores?api_key={self.api_key}"
            response = self.session.get(url)
            
            if response.status_code == 200:
                data = response.json()
                return self.process_games(data["games"], sport)
            else:
                print(f"API error: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"Error fetching {sport} games: {e}")
            return []
            
    def process_games(self, games, sport):
        """Process the raw games data into a simplified format"""
        processed_games = []
        
        # print(f"Processing {len(games)} games from API")
        
        for game in games:
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
                if inning and inning_half:
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
            
            # Normalize status to ensure consistency
            if raw_status in ["Final", "final", "FINAL", "F"]:
                status = "Final"
            elif raw_status in ["Scheduled", "scheduled", "SCHEDULED", "Pre-Game", "pre-game", "PRE-GAME"]:
                status = "Scheduled"
            # Special case for games that show as "In Progress" but haven't really started
            elif raw_status in ["In Progress", "in progress", "IN PROGRESS", "I"]:
                status = "In Progress"
            else:
                status = raw_status
            
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
            
        return processed_games