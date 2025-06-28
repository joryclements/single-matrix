import asyncio
import displayio
import terminalio
from adafruit_display_text.label import Label
from team_colors import NBA_COLORS, NFL_COLORS, NHL_COLORS, MLB_COLORS, BRIGHT_YELLOW
from utils import (
    BLACK, WHITE, GREEN, DIM_GRAY, GRAY,
    get_team_color, format_game_time, parse_team_record
)
from display_utils import (
    create_baseball_diamond, create_underline, calculate_text_positions,
    handle_nfl_display, handle_mlb_display, handle_game_status
)

# Display dimensions
DISPLAY_WIDTH = 64
DISPLAY_HEIGHT = 32

class DisplayManager:
    def __init__(self, display, api):
        self.display = display
        self.api = api
        self.display_task = None
        self.current_sport = "MLB"
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
        self.separator_bitmap = displayio.Bitmap(1, 4, 2)  # 1px wide, 4px tall bitma
        self.separator_palette = displayio.Palette(2)
        self.separator_palette[0] = BLACK  # Background
        self.separator_palette[1] = DIM_GRAY  # Separator color
        # Set the separator pixels
        for y in range(4):
            self.separator_bitmap[0, y] = 1
    
    def create_text_label(self, text, color=WHITE, x=0, y=16):
        """Create a text label with the given parameters"""
        return Label(terminalio.FONT, text=text, color=color, x=x, y=y)

    def create_game_text(self, game, middle_text=None):
        """Create the text to display for a game in scoreboard format"""
        try:
            # Get team abbreviations and ensure they're uppercase for color lookup
            home_team_abbr = str(game.get('home_team', 'UNK')).upper()
            away_team_abbr = str(game.get('away_team', 'UNK')).upper()
        
            # Determine the sport for this game (either from game or current setting)
            game_sport = game.get('sport', self.current_sport)
            
            # Get team colors
            home_color = get_team_color(home_team_abbr, game_sport)
            away_color = get_team_color(away_team_abbr, game_sport)
            
            # Ensure team names are max 3 chars and not empty
            home_team = home_team_abbr[:3] if home_team_abbr else "HOM"
            away_team = away_team_abbr[:3] if away_team_abbr else "AWY"
            
            # Convert scores to strings with fallbacks
            home_score = str(game.get('home_score', 0))
            away_score = str(game.get('away_score', 0))
        
            # Show sport name in the center, but not for live/postponed/delayed MLB games
            if (game.get("status") in ["Postponed", "Delayed", "Suspended", "Cancelled"] or 
                (game_sport == "MLB" and game.get("status") == "In Progress")):
                middle_text = None
            else:
                middle_text = game_sport

            # Calculate positions for text elements
            positions = calculate_text_positions(
                home_team, away_team, home_score, away_score,
                char_width=6, padding=2, display_width=DISPLAY_WIDTH
            )
            
            display_data = {    
                'top_row': [
                {'text': away_team, 'color': away_color, 'x': positions['away_x']},
                {'text': home_team, 'color': home_color, 'x': positions['home_x']}
                ],
                'middle_row': [
                    {'text': away_score, 'color': WHITE, 'x': positions['away_score_x']},
                    {'text': home_score, 'color': WHITE, 'x': positions['home_score_x']},
                ],
                'bottom_row': []
                }
            
            # Add middle text if provided
            if middle_text:
                middle_width = len(middle_text) * 6
                middle_x = positions['center_x'] - (middle_width // 2)
                display_data['middle_row'].insert(1, {'text': middle_text, 'color': DIM_GRAY, 'x': middle_x})

            # Handle game status and get clock text
            clock_text = handle_game_status(game, display_data, positions['center_x'], 6)
            
            game_status = game.get("status", "Unknown")
            
            if game_status == "Final":
                # Handle final game display (winner colors, records)
                self._handle_final_game(game, display_data, positions)
            elif game_status == "Scheduled":
                # Handle scheduled game display
                self._handle_scheduled_game(game, display_data, positions)
            elif game_status in ["Postponed", "Delayed", "Suspended", "Cancelled", "Unknown"]:
                # Handle postponed/delayed/suspended/cancelled/unknown game display
                self._handle_delayed_game(game, display_data, positions)
            else:
                # Handle in-progress game or unknown status
                period = str(game.get('period', ''))
                period_width = len(period) * 6
                period_x = positions['center_x'] - (period_width // 2)
                display_data['top_row'].insert(1, {'text': period, 'color': WHITE, 'x': period_x})
                
                # Handle sport-specific display
                if game_sport == "NFL":
                    clock_text = handle_nfl_display(game, display_data, home_team, away_team) or clock_text
                elif game_sport == "MLB":
                    clock_text = handle_mlb_display(
                        game, display_data, period, home_team, away_team,
                        home_color, away_color, create_underline,
                        lambda bases: create_baseball_diamond(self.base_bitmap, self.base_palette, bases),
                        positions['away_x'], positions['home_x'], positions['center_x'],
                        positions['away_score_x'], positions['home_score_x']
                    ) or clock_text
                
                # Add clock text if available
                if clock_text:
                    clock_width = len(clock_text) * 6
                    clock_x = positions['center_x'] - (clock_width // 2)
                    display_data['bottom_row'].append({'text': clock_text, 'color': WHITE, 'x': clock_x})
            
            return display_data
            
        except Exception as e:
            print(f"Error creating game text: {e}")
            # Return a minimal safe display structure
            return {
                'top_row': [
                    {'text': 'ERR', 'color': WHITE, 'x': 5},
                    {'text': 'ERR', 'color': WHITE, 'x': 45}
                ],
                'middle_row': [
                    {'text': 'Game Error', 'color': WHITE, 'x': 8}
                ],
                'bottom_row': []
            }

    def _handle_final_game(self, game, display_data, positions):
        """Handle display for a final game"""
        # Determine winner and set score colors
        home_score_int = int(game['home_score'])
        away_score_int = int(game['away_score'])
        display_data['middle_row'][0]['color'] = WHITE if away_score_int > home_score_int else DIM_GRAY
        display_data['middle_row'][-1]['color'] = WHITE if home_score_int > away_score_int else DIM_GRAY
        
        # Handle team records
        away_record = game.get('away_record', '')
        home_record = game.get('home_record', '')
        away_record_wins, away_record_losses = parse_team_record(away_record)
        home_record_wins, home_record_losses = parse_team_record(home_record)
        
        if away_record_wins and away_record_losses and home_record_wins and home_record_losses:
            self._add_team_records(
                display_data, positions,
                away_record_wins, away_record_losses,
                home_record_wins, home_record_losses
            )

    def _handle_scheduled_game(self, game, display_data, positions):
        """Handle display for a scheduled game"""
        # Format and display game time
        date = game.get('date', '')
        time_part = format_game_time(date)
        time_width = len(time_part) * 6
        time_x = positions['center_x'] - (time_width // 2)
        
        # Update display data
        display_data['middle_row'][0]['text'] = ''
        display_data['middle_row'][-1]['text'] = ''
        display_data['bottom_row'].append({'text': time_part, 'color': WHITE, 'x': time_x})

    def _handle_delayed_game(self, game, display_data, positions):
        """Handle display for postponed/delayed/suspended/cancelled games"""
        # Handle team records
        away_record = game.get('away_record', '')
        home_record = game.get('home_record', '')
        away_record_wins, away_record_losses = parse_team_record(away_record)
        home_record_wins, home_record_losses = parse_team_record(home_record)
        
        if away_record_wins and away_record_losses and home_record_wins and home_record_losses:
            self._add_team_records(
                display_data, positions,
                away_record_wins, away_record_losses,
                home_record_wins, home_record_losses
            )
        
        # Get status and create appropriate display text
        status = game.get('status', 'Unknown')
        display_text = self._get_status_display_text(status)
        
        # Update display data middle row with status and center it
        display_data['middle_row'][0]['text'] = display_text
        display_data['middle_row'][-1]['text'] = ''
        display_data['middle_row'][0]['x'] = positions['center_x'] - (len(display_text) * 6 // 2)
        
        # If there are scores, show them (for delayed games that were in progress)
        try:
            home_score = int(game.get('home_score', 0))
            away_score = int(game.get('away_score', 0))
        except (ValueError, TypeError):
            home_score = away_score = 0
            
        if home_score > 0 or away_score > 0:
            display_data['middle_row'][0]['text'] = str(away_score)
            display_data['middle_row'][-1]['text'] = str(home_score)
            display_data['middle_row'][0]['x'] = positions['away_score_x']
            display_data['middle_row'][-1]['x'] = positions['home_score_x']
            
            # Add status as bottom text
            display_data['bottom_row'].append({
                'text': display_text, 
                'color': DIM_GRAY, 
                'x': positions['center_x'] - (len(display_text) * 6 // 2)
            })
    
    def _get_status_display_text(self, status):
        """Convert status to appropriate display text (max 5 chars for screen space)"""
        status_map = {
            'Postponed': 'POSTPONED',
            'Delayed': 'DELAY',
            'Suspended': 'SUSPENDED', 
            'Cancelled': 'CANCELLED',
            'Rain Delay': 'RAIN DELAY',
            'Weather Delay': 'RAIN DELAY',  # Use RAIN DELAY for all weather delays
            'Unknown': 'UNKNOWN'
        }
        
        # Check if status contains certain keywords for better mapping
        status_lower = status.lower()
        if 'rain' in status_lower or 'weather' in status_lower:
            return 'RAIN DELAY'  # Use full RAIN DELAY text
        elif 'delay' in status_lower:
            return 'DELAY'
        elif 'suspend' in status_lower:
            return 'SUSPENDED'
        elif 'cancel' in status_lower:
            return 'CANCELLED'
        elif 'postpone' in status_lower:
            return 'POSTPONED'
        
        # Use mapping or truncate long status to reasonable length
        return status_map.get(status, status[:10].upper())

    def _add_team_records(self, display_data, positions, away_wins, away_losses, home_wins, home_losses):
        """Add team records to the display data"""
        # Calculate record widths
        away_width_wins = len(away_wins) * 6
        away_width_losses = len(away_losses) * 6
        home_width_wins = len(home_wins) * 6
        home_width_losses = len(home_losses) * 6
        
        # Calculate positions
        away_record_x = 0
        home_record_x = DISPLAY_WIDTH - home_width_wins - home_width_losses - 2
        
        # Check if records fit
        center_gap = home_record_x - (away_record_x + away_width_wins + away_width_losses)
        if center_gap >= 0:
            # Add away team record
            display_data['bottom_row'].append({'text': away_wins, 'color': DIM_GRAY, 'x': away_record_x})
            away_separator = displayio.TileGrid(self.separator_bitmap, pixel_shader=self.separator_palette)
            away_separator.x = away_record_x + away_width_wins
            away_separator.y = 25
            display_data['separators'] = [away_separator]
            display_data['bottom_row'].append(
                {'text': away_losses, 'color': DIM_GRAY, 'x': away_record_x + away_width_wins + 2}
            )
            
            # Add home team record
            display_data['bottom_row'].append({'text': home_wins, 'color': DIM_GRAY, 'x': home_record_x})
            home_separator = displayio.TileGrid(self.separator_bitmap, pixel_shader=self.separator_palette)
            home_separator.x = home_record_x + home_width_wins
            home_separator.y = 25
            display_data['separators'].append(home_separator)
            display_data['bottom_row'].append(
                {'text': home_losses, 'color': DIM_GRAY, 'x': home_record_x + home_width_wins + 2}
            )

    async def display_scoreboard(self, display_data):
        """Display multi-line text in scoreboard format with error recovery"""
        try:
            # Validate display_data structure
            if not isinstance(display_data, dict):
                print("Invalid display_data: not a dictionary")
                self.display_static_text("Data\nError")
                return
                
            # Ensure required keys exist
            required_keys = ['top_row', 'middle_row', 'bottom_row']
            for key in required_keys:
                if key not in display_data:
                    display_data[key] = []
            
            # Create the display group
            display_group = displayio.Group()
            
            # Create labels for each line with better vertical spacing
            y_positions = [5, 16, 27]  # More evenly spaced positions
            
            # Display top row
            try:
                for item in display_data['top_row']:
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
                # Add the underline if it exists
                if 'underline' in display_data:
                    display_group.append(display_data['underline'])
                
                # Add the baseball diamond if it exists
                if 'diamond' in display_data:
                    display_group.append(display_data['diamond'])
                    
                # Add the record separators if they exist
                if 'separators' in display_data:
                    for separator in display_data['separators']:
                        display_group.append(separator)
            except Exception as e:
                print(f"Error adding special elements: {e}")
            
            # Display middle row
            try:
                for item in display_data['middle_row']:
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
                for item in display_data['bottom_row']:
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
            
            # Keep display static for 8 seconds
            await asyncio.sleep(8)
            
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
                print(f"Invalid game data, skipping: {game}")
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
            print("No games available")
            return []
            
        # Debug: print all games and their statuses
        print(f"Total games: {len(self.games)}")
        for i, game in enumerate(self.games):
            print(f"Game {i+1}: {game['home_team']} vs {game['away_team']} - Status: {game['status']}")
            
        if self.show_all_games:
            # Return all games regardless of status
            print(f"Showing all games: {len(self.games)} games")
            return self.games
        else:
            # Consider active/live games: In Progress, Delayed, Suspended, Unknown (treated as active)
            active_statuses = ["In Progress", "Delayed", "Suspended", "Unknown"]
            active_games = [g for g in self.games if g["status"] in active_statuses]
            
            if active_games:
                # If we have active games, show only those
                print(f"Showing active/live games: {len(active_games)} games")
                return active_games
            else:
                # If no active games, show upcoming scheduled games
                scheduled_games = [g for g in self.games if g["status"] == "Scheduled"]
                print(f"No active games found. Showing scheduled games: {len(scheduled_games)} games")
                return scheduled_games