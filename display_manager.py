import asyncio
import displayio
import terminalio
from adafruit_display_text.label import Label
from team_colors import BRIGHT_YELLOW
from config import (
    DISPLAY_WIDTH,
    DISPLAY_HEIGHT,
    DEBUG_DISPLAY,
    DISPLAY_INTERVAL,
    ROW_Y_TOP,
    ROW_Y_MIDDLE,
    ROW_Y_BOTTOM,
)
from utils import BLACK, WHITE, DIM_GRAY
from game_display_builder import GameDisplayBuilder

class DisplayManager:
    def __init__(self, display, api):
        self.display = display
        self.api = api
        self.display_task = None
        self.current_sport = "SPORTS"
        self.show_all_games = True  # True = show all games, False = show only active games
        self.games = []
        self.current_game_index = 0
        self.supported_sports = ["NFL", "NBA", "NHL", "MLB", "SPORTS"]  # "SPORTS" instead of "ALL"
        
        # Create bitmaps and palettes
        self._init_bitmaps()
        
    def _init_bitmaps(self):
        """Initialize all bitmaps and palettes"""
        # Create a bitmap for the baseball diamond
        self.base_bitmap = displayio.Bitmap(15, 10, 3)  # 15x10 bitmap for diamond bases with spacing
        self.base_palette = displayio.Palette(3)
        self.base_palette[0] = BLACK  # Background
        self.base_palette[1] = BRIGHT_YELLOW  # Active base
        self.base_palette[2] = DIM_GRAY  # Empty base
        
        # Create a bitmap for team name underlines
        self.underline_bitmap = displayio.Bitmap(18, 1, 2)  # 18x1 bitmap for underline
        self.underline_palette = displayio.Palette(2)
        self.underline_palette[0] = BLACK  # Background
        self.underline_palette[1] = WHITE  # Underline color (will be changed per team)
        
        # Create a bitmap for record separator
        self.separator_bitmap = displayio.Bitmap(1, 4, 2)  # 1px wide, 4px tall bitmap
        self.separator_palette = displayio.Palette(2)
        self.separator_palette[0] = BLACK  # Background
        self.separator_palette[1] = DIM_GRAY  # Separator color
        for y in range(4):
            self.separator_bitmap[0, y] = 1
        self._builder = GameDisplayBuilder(
            self.base_bitmap, self.base_palette,
            self.separator_bitmap, self.separator_palette,
        )

    def create_text_label(self, text, color=WHITE, x=0, y=16):
        """Create a text label with the given parameters"""
        return Label(terminalio.FONT, text=text, color=color, x=x, y=y)

    def create_game_text(self, game):
        """Create the display_data dict for a game. Delegates to GameDisplayBuilder."""
        return self._builder.create_game_text(game, self.current_sport)

    async def display_scoreboard(self, display_data):
        """Display multi-line text in scoreboard format with error recovery"""
        try:
            # Validate display_data structure
            if not isinstance(display_data, dict):
                print("Invalid display_data: not a dictionary")
                self.display_static_text("Data\nError")
                return

            # Work with a copy so we don't mutate the caller's dict
            data = dict(display_data)
            for key in ('top_row', 'middle_row', 'bottom_row'):
                data.setdefault(key, [])

            # Create the display group
            display_group = displayio.Group()

            # Create labels for each line (64x32 row baselines from config)
            y_positions = [ROW_Y_TOP, ROW_Y_MIDDLE, ROW_Y_BOTTOM]

            # Display top row
            try:
                for item in data['top_row']:
                    if isinstance(item, dict) and 'text' in item:
                        label = self.create_text_label(
                            str(item['text']), 
                            item.get('color', WHITE), 
                            x=item.get('x', 0), 
                            y=y_positions[0]
                        )
                        display_group.append(label)
            except Exception as e:
                print(f"Error rendering top row: {e}")
            
            # Add special display elements safely
            try:
                if 'underline' in data:
                    display_group.append(data['underline'])
                if 'diamond' in data:
                    display_group.append(data['diamond'])
                if 'separators' in data:
                    for separator in data['separators']:
                        display_group.append(separator)

            except Exception as e:
                print(f"Error adding special elements: {e}")
            
            # Display middle row
            try:
                for item in data['middle_row']:
                    if isinstance(item, dict) and 'text' in item and item['text']:
                        label = self.create_text_label(
                            str(item['text']), 
                            item.get('color', WHITE), 
                            x=item.get('x', 0), 
                            y=y_positions[1]
                        )
                        display_group.append(label)
            except Exception as e:
                print(f"Error rendering middle row: {e}")
            
            # Display bottom row
            try:
                for item in data['bottom_row']:
                    if isinstance(item, dict) and 'text' in item and item['text']:
                        label = self.create_text_label(
                            str(item['text']), 
                            item.get('color', WHITE), 
                            x=item.get('x', 0), 
                            y=y_positions[2]
                        )
                        display_group.append(label)
            except Exception as e:
                print(f"Error rendering bottom row: {e}")
            
            # Set as root group
            try:
                self.display.root_group = display_group
            except Exception as e:
                print(f"Error setting display group: {e}")
                self.display_static_text("Display\nFailed")
                return
            
            # Keep display static for configured interval (same as main loop advance)
            await asyncio.sleep(DISPLAY_INTERVAL)
            
        except Exception as e:
            print(f"Critical error in display_scoreboard: {e}")
            self.display_static_text("Render\nError")

    def stop_display(self):
        """Stop any active display"""
        if self.display_task:
            self.display_task.cancel()
            self.display_task = None

    def display_static_text(self, text, color=None):
        """Display static centered text with support for newlines"""
        # print(f"Displaying static text: {text}")
        
        color = WHITE if color is None else color  # Default white
        
        # Create the display group
        group = displayio.Group()
        
        # Split text by newlines
        lines = text.split('\n')
        num_lines = len(lines)
        
        # Calculate vertical positions based on number of lines
        if num_lines == 1:
            y_positions = [DISPLAY_HEIGHT // 2]
        else:
            # Distribute lines evenly in the display height
            line_height = min(10, DISPLAY_HEIGHT // num_lines)
            start_y = (DISPLAY_HEIGHT - (line_height * (num_lines - 1))) // 2
            y_positions = [start_y + (i * line_height) for i in range(num_lines)]
        
        # Create and center each line of text
        for i, line in enumerate(lines):
            label = self.create_text_label(line, color)
            
            # Center the text horizontally
            text_width = len(line) * 6  # Approximate width
            x_pos = DISPLAY_WIDTH // 2
            
            label.anchor_point = (0.5, 0.5)
            label.anchored_position = (x_pos, y_positions[i])
            
            group.append(label)
            
        self.display.root_group = group

    def toggle_sport(self):
        """Cycle through supported sports"""
        current_index = self.supported_sports.index(self.current_sport)
        next_index = (current_index + 1) % len(self.supported_sports)
        self.current_sport = self.supported_sports[next_index]
        self.current_game_index = 0
        self.games = []  # Clear existing games data
        
        # Clear any cached display elements
        if self.display_task:
            self.display_task.cancel()
            self.display_task = None
        
        # Display a short message about the current sport
        mode = "ALL" if self.show_all_games else "LIVE"
        self.display_static_text(f"{mode}\n{self.current_sport}")
        print(f"Switched to {self.current_sport}")
        
        # Return tuple of (fetch_data, reset_display)
        return (True, True)  # Signal that data should be fetched immediately and display should be reset
        
    def toggle_game_display(self):
        """Toggle between showing all games and only active/upcoming games"""
        # Simply toggle the flag
        self.show_all_games = not self.show_all_games
        self.current_game_index = 0
        
        # Display a short message about the current mode
        mode = "ALL" if self.show_all_games else "LIVE"
        self.display_static_text(f"{mode}\n{self.current_sport}")
        
        print(f"Now showing {'all' if self.show_all_games else 'active (or scheduled if no active)'} {self.current_sport} games")
        
        # Return tuple of (fetch_data, reset_display)
        return (True, True)  # Signal that data should be fetched immediately and display should be reset
        
    async def update_games(self):
        """Update games from API with error recovery"""
        try:
            if self.current_sport == "SPORTS":
                # Fetch games from all sports
                new_games = []
                successful_sports = 0
                for sport in ["NFL", "NBA", "NHL", "MLB"]:
                    try:
                        sport_games = await self.api.get_games(sport)
                        if sport_games:
                            # Add sport identifier to each game
                            for game in sport_games:
                                if isinstance(game, dict):  # Validate game is a dict
                                    game["sport"] = sport
                                    new_games.append(game)
                            successful_sports += 1
                            print(f"Fetched {len(sport_games)} {sport} games")
                    except Exception as e:
                        print(f"Failed to fetch {sport} games: {e}")
                        continue
                
                if new_games:
                    self.games = new_games
                    print(f"Updated games: {len(self.games)} games from {successful_sports}/4 sports")
                elif not self.games:  # Only show error if we have no cached games
                    print("No games available from any sport")
            else:
                # Regular single sport fetch
                try:
                    new_games = await self.api.get_games(self.current_sport)
                    if new_games:  # Only update if we got valid data
                        # Validate and add sport identifier
                        valid_games = []
                        for game in new_games:
                            if isinstance(game, dict):
                                game["sport"] = self.current_sport
                                valid_games.append(game)
                        
                        if valid_games:
                            self.games = valid_games
                            print(f"Updated games: {len(self.games)} {self.current_sport} games found")
                        else:
                            print("No valid games received from API")
                    else:
                        print("No games data received from API")
                except Exception as e:
                    print(f"Error fetching {self.current_sport} games: {e}")
        except Exception as e:
            print(f"Critical error updating games: {e}")
            
    async def display_current_game(self):
        """Display the current game with error recovery"""
        try:
            filtered_games = self.get_filtered_games()
            total_games = len(filtered_games)
            
            print(f"Display current game: {self.current_game_index + 1}/{total_games} games")
            
            if not filtered_games:
                if self.show_all_games:
                    self.display_static_text(f"No {self.current_sport}\nGames")
                else:
                    self.display_static_text(f"No Live\n{self.current_sport}")
                return
                
            # Ensure index is valid
            if self.current_game_index >= total_games:
                self.current_game_index = 0
                
            game = filtered_games[self.current_game_index]
            
            # Validate game data before processing
            if not self._validate_game_data(game):
                print(f"Invalid game data, skipping: {game.get('away_team')} @ {game.get('home_team')} ({game.get('status')})")
                self.current_game_index = (self.current_game_index + 1) % total_games
                return
                
            print(f"Showing game: {game['home_team']} vs {game['away_team']} - Status: {game['status']}")
            
            try:
                game_text_lines = self.create_game_text(game)
                
                # Stop any existing display
                self.stop_display()
                
                # Start new display task
                self.display_task = asyncio.create_task(self.display_scoreboard(game_text_lines))
                
            except Exception as e:
                print(f"Error creating display for game: {e}")
                self.display_static_text("Display\nError")
                
            # Update index for next time
            self.current_game_index = (self.current_game_index + 1) % total_games
            
        except Exception as e:
            print(f"Critical error in display_current_game: {e}")
            self.display_static_text("Game\nError")

    def _validate_game_data(self, game):
        """Validate essential game data fields"""
        try:
            required_fields = ['home_team', 'away_team', 'status']
            for field in required_fields:
                if field not in game or game[field] is None:
                    print(f"Missing required field: {field}")
                    return False
            
            # Ensure team names are strings
            if not isinstance(game['home_team'], str) or not isinstance(game['away_team'], str):
                print("Invalid team name types")
                return False
                
            return True
        except Exception as e:
            print(f"Error validating game data: {e}")
            return False

    def get_filtered_games(self):
        """Get games filtered by current settings"""
        if not self.games:
            if DEBUG_DISPLAY:
                print("No games available")
            return []
        if DEBUG_DISPLAY:
            print(f"Total games: {len(self.games)}")
            for i, game in enumerate(self.games):
                print(f"Game {i+1}: {game['home_team']} vs {game['away_team']} - Status: {game['status']}")
        if self.show_all_games:
            if DEBUG_DISPLAY:
                print(f"Showing all games: {len(self.games)} games")
            return self.games
        else:
            active_statuses = ["In Progress", "Delayed", "Suspended", "Unknown"]
            active_games = [g for g in self.games if g["status"] in active_statuses]
            if active_games:
                if DEBUG_DISPLAY:
                    print(f"Showing active/live games: {len(active_games)} games")
                return active_games
            # No active games: show nearby games (finals <24h + scheduled within 36h)
            nearby = self._get_nearby_games()
            if nearby:
                if DEBUG_DISPLAY:
                    print(f"No active games; showing {len(nearby)} nearby games")
                return nearby
            # RTC unavailable or nothing nearby: show everything so display isn't blank
            if DEBUG_DISPLAY:
                print("No nearby games; showing all games as fallback")
            return self.games

    def _get_nearby_games(self):
        """Return finals + scheduled games within 36 hours. Returns [] if RTC unavailable."""
        try:
            import rtc
            import time
            now_dt = rtc.RTC().datetime
            now = time.mktime((
                now_dt.tm_year, now_dt.tm_mon, now_dt.tm_mday,
                now_dt.tm_hour, now_dt.tm_min, now_dt.tm_sec, 0, 0, -1
            ))
        except Exception:
            return []

        thirty_six_hours = 36 * 60 * 60
        nearby = []
        for game in self.games:
            status = game.get("status", "")
            if status == "Final":
                # Already filtered to <24h old by games_processor
                nearby.append(game)
            else:
                date = game.get("date", "")
                if not date or "-" not in date:
                    nearby.append(game)  # No date info, include it
                    continue
                try:
                    y, m, d = int(date[:4]), int(date[5:7]), int(date[8:10])
                    h, mn = int(date[11:13]), int(date[14:16])
                    game_ts = time.mktime((y, m, d, h, mn, 0, 0, 0, -1))
                    if now <= game_ts <= now + thirty_six_hours:
                        nearby.append(game)
                    elif DEBUG_DISPLAY:
                        kind = "far-future" if game_ts > now + thirty_six_hours else "past"
                        print(f"Filtered {kind} game: {game.get('away_team')} @ {game.get('home_team')} on {date}")
                except (ValueError, IndexError):
                    nearby.append(game)  # Can't parse date, include it
        return nearby