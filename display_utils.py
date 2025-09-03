import displayio
from utils import BLACK, DIM_GRAY, GREEN, WHITE

def create_baseball_diamond(base_bitmap, base_palette, bases):
    """Create a baseball diamond using pixels with diamond shapes"""
    # Ensure the bitmap is large enough for our diamond pattern
    # For a 5x5 diamond at each base, we need at least 20x15
    bitmap_width = base_bitmap.width
    bitmap_height = base_bitmap.height
    
    # Clear the bitmap to black background
    for x in range(bitmap_width):
        for y in range(bitmap_height):
            base_bitmap[x, y] = 0
            
    # Helper function to draw an actual diamond shape
    def draw_diamond(start_x, start_y, is_occupied):
        color = 1 if is_occupied else 2  # 1=yellow (occupied), 2=gray (empty)

        # Top point
        base_bitmap[start_x + 2, start_y] = color
        
        # Second row
        base_bitmap[start_x + 1, start_y + 1] = color
        base_bitmap[start_x + 2, start_y + 1] = color
        base_bitmap[start_x + 3, start_y + 1] = color
        
        # Middle row (widest part)
        base_bitmap[start_x, start_y + 2] = color
        base_bitmap[start_x + 1, start_y + 2] = color
        base_bitmap[start_x + 2, start_y + 2] = color
        base_bitmap[start_x + 3, start_y + 2] = color
        base_bitmap[start_x + 4, start_y + 2] = color
        
        # Fourth row
        base_bitmap[start_x + 1, start_y + 3] = color
        base_bitmap[start_x + 2, start_y + 3] = color
        base_bitmap[start_x + 3, start_y + 3] = color
        
        # Bottom point
        base_bitmap[start_x + 2, start_y + 4] = color
    
    # Position the diamonds in a classic baseball diamond layout
    # Calculate center point of the bitmap for better positioning
    center_x = bitmap_width // 2
    center_y = bitmap_height // 2
    
    # Draw second base (top) - raised by 1 pixel
    second_base_y = 0
    draw_diamond(center_x - 2, second_base_y, bases.get('second', False))
    
    # Draw third base (left) - moved 1 pixel down and 1 pixel closer to center
    draw_diamond(1, center_y - 1, bases.get('third', False))
    
    # Draw first base (right) - moved 1 pixel down and 1 pixel closer to center
    draw_diamond(bitmap_width - 6, center_y - 1, bases.get('first', False))
    
    return displayio.TileGrid(base_bitmap, pixel_shader=base_palette)

def create_underline(width, color):
    """Create an underline bitmap with the given width and color"""
    # Create a new bitmap and palette for each underline
    bitmap = displayio.Bitmap(18, 1, 2)  # 18x1 bitmap for underline (3 chars * 6 pixels)
    palette = displayio.Palette(2)
    palette[0] = BLACK  # Background
    palette[1] = color  # Underline color
    
    # Set the underline pixels for the given width
    for x in range(width):
        bitmap[x, 0] = 1
        
    return displayio.TileGrid(bitmap, pixel_shader=palette)

def calculate_text_positions(home_team, away_team, home_score, away_score, char_width=6, padding=2, display_width=64):
    """Calculate positions for team names and scores"""
    team_space_width = 3 * char_width  # Always reserve 3 chars worth of space for team names
    
    # Calculate widths for scores
    home_score_width = len(home_score) * char_width
    away_score_width = len(away_score) * char_width
    
    # For away team (left side)
    away_x = padding  # Team space starts at padding
    # If team name is shorter than 3 chars, center it in the 3-char space
    if len(away_team) < 3:
        away_x = away_x + ((team_space_width - (len(away_team) * char_width)) // 2)
    # Center score under the 3-char team space
    away_center_width = max(team_space_width, away_score_width)
    away_score_x = padding + ((away_center_width - away_score_width) // 2)
        
    # For home team (right side)
    home_center_width = max(team_space_width, home_score_width)
    home_base_x = display_width - team_space_width - padding  # Right edge of team space
    # If team name is shorter than 3 chars, center it in the 3-char space
    home_x = home_base_x
    if len(home_team) < 3:
        home_x = home_base_x + ((team_space_width - (len(home_team) * char_width)) // 2)
    # Center score under the 3-char team space
    home_score_x = home_base_x + ((home_center_width - home_score_width) // 2)
    
    # Calculate center point
    away_right_edge = padding + max(team_space_width, away_score_width)
    home_left_edge = home_base_x
    center_x = away_right_edge + (home_left_edge - away_right_edge) // 2
    return {
        'away_x': away_x,
        'home_x': home_x,
        'away_score_x': away_score_x,
        'home_score_x': home_score_x,
        'center_x': center_x,
        'team_space_width': team_space_width
    }

# Sport-specific display handling functions (moved from sport_display.py)

def handle_nfl_display(game, display_data, home_team, away_team):
    """Handle NFL-specific display logic"""
    if game.get('down_distance'):
        # If we have down and distance info, show that instead of clock
        return game.get('down_distance', '')[:10]  # Limit length
    elif game.get('possession'):
        # Add possession indicator if available
        poss_team = game.get('possession', '')
        if poss_team:
            # Update team display with possession indicators
            if poss_team == game['home_team']:
                display_data['top_row'][1]['text'] = f"{home_team}<"
            elif poss_team == game['away_team']:
                display_data['top_row'][0]['text'] = f">{away_team}"
    return None

def handle_mlb_display(game, display_data, period, home_team, away_team, home_color, away_color, 
                      create_underline_fn, create_baseball_diamond_fn, away_x, home_x, center_x, 
                      away_score_x, home_score_x):
    """Handle MLB-specific display logic"""
    # Clear any existing underline
    if 'underline' in display_data:
        del display_data['underline']

    # Handle batting team indicator
    if period and len(period) > 0 and period[0].lower() == 't':
        # Away team is batting
        underline = create_underline_fn(len(away_team) * 6 - 1, away_color)
        underline.x = away_x
        underline.y = 9  # Just below the team name
        display_data['underline'] = underline
    elif period and len(period) > 0 and period[0].lower() == 'b':
        # Home team is batting
        underline = create_underline_fn(len(home_team) * 6 - 1, home_color)
        underline.x = home_x
        underline.y = 9
        display_data['underline'] = underline

    # Handle baseball diamond
    bases = game.get('bases', {})
    if bases:
        # Create the baseball diamond bitmap
        diamond = create_baseball_diamond_fn(bases)
        # Position the diamond in the center
        diamond.x = center_x - 8  # Center the 15-wide bitmap
        diamond.y = 11  # Position slightly above the middle row
        
        # Store the diamond in a special key for the display function
        display_data['diamond'] = diamond
        
        # For live MLB games, we want to show count/bases in middle row
        # The scores will be handled by the main create_game_text function
        # So we don't overwrite the middle row here

    # Format count display
    count_dict = game.get('count', {})
    if count_dict:
        balls = count_dict.get('balls', 0)
        strikes = count_dict.get('strikes', 0)
        outs = count_dict.get('outs', 0)
        
        # Calculate score widths
        away_score_width = len(str(game['away_score'])) * 6
        home_score_width = len(str(game['home_score'])) * 6
        
        # Add balls count under away team
        balls_text = f"B{balls}"
        balls_width = len(balls_text) * 6
        balls_x = away_score_x + (away_score_width // 2) - (balls_width // 2)
        display_data['bottom_row'].append({'text': balls_text, 'color': DIM_GRAY, 'x': balls_x})
        
        # Add strikes count in center
        strikes_text = f"S{strikes}"
        strikes_width = len(strikes_text) * 6
        strikes_x = center_x - (strikes_width // 2)
        display_data['bottom_row'].append({'text': strikes_text, 'color': DIM_GRAY, 'x': strikes_x})
        
        # Add outs count under home team
        outs_text = f"O{outs}"
        outs_width = len(outs_text) * 6
        outs_x = home_score_x + (home_score_width // 2) - (outs_width // 2)
        display_data['bottom_row'].append({'text': outs_text, 'color': DIM_GRAY, 'x': outs_x})
        
        return ""
    
    return ""

def handle_game_status(game, display_data, center_x, char_width):
    """Handle different game statuses and return appropriate clock text"""
    if game["status"] == "Final":
        # Add F indicator in top row center
        final_text = "F"
        final_width = len(final_text) * char_width
        final_x = center_x - (final_width // 2)
        display_data['top_row'].insert(1, {'text': final_text, 'color': DIM_GRAY, 'x': final_x})
        return None
    elif game["status"] == "Scheduled":
        return None
    else:
        clock = game.get('clock', '')
        # Check if clock is at 0.0 or similar
        if clock in ['0.0', '0:00', '00:00', '0']:
            return 'END'
        return clock 
    