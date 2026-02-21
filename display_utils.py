import displayio
import terminalio
from adafruit_display_text.label import Label
from config import (
    DISPLAY_WIDTH,
    CHAR_WIDTH,
    PADDING,
    TEAM_SPACE_CHARS,
    UNDERLINE_Y_OFFSET,
    DIAMOND_HALF_OFFSET,
    DIAMOND_Y_OFFSET,
)
from utils import BLACK, DIM_GRAY, WHITE


def _build_glyph_visual_bounds(font=None):
    """Scan font bitmap to find actual visible pixel bounds for each digit glyph.

    Returns a dict mapping char string -> (left_pad, right_pad) where:
      left_pad  = transparent columns on the left inside the cell
      right_pad = transparent columns on the right inside the cell
    So the visual width = cell_width - left_pad - right_pad.
    """
    if font is None:
        font = terminalio.FONT
    bitmap = font.bitmap
    bounds = {}
    for ch in "0123456789":
        glyph = font.get_glyph(ord(ch))
        tw = glyph.width
        th = glyph.height
        # Locate this glyph's tile in the font bitmap
        tiles_per_row = bitmap.width // tw
        tile_row = glyph.tile_index // tiles_per_row
        tile_col = glyph.tile_index % tiles_per_row
        sx = tile_col * tw
        sy = tile_row * th
        # Scan columns left-to-right for first lit pixel
        left_pad = 0
        for x in range(tw):
            col_has_pixel = False
            for y in range(th):
                if bitmap[sx + x, sy + y] != 0:
                    col_has_pixel = True
                    break
            if col_has_pixel:
                break
            left_pad += 1
        # Scan columns right-to-left for last lit pixel
        right_pad = 0
        for x in range(tw - 1, -1, -1):
            col_has_pixel = False
            for y in range(th):
                if bitmap[sx + x, sy + y] != 0:
                    col_has_pixel = True
                    break
            if col_has_pixel:
                break
            right_pad += 1
        bounds[ch] = (left_pad, right_pad)
    return bounds


# Pre-compute at import time (runs once on boot)
DIGIT_BOUNDS = _build_glyph_visual_bounds()


def get_visual_record_width(text):
    """Get the visual pixel width of a numeric string (digits only),
    accounting for actual glyph content rather than monospace cell width."""
    font = terminalio.FONT
    cell_w = font.get_glyph(ord("0")).shift_x  # cell advance (e.g. 6)
    if not text:
        return 0
    # Full cell width for all characters
    total = len(text) * cell_w
    # Subtract right padding of last char (trailing transparent pixels)
    last_bounds = DIGIT_BOUNDS.get(text[-1])
    if last_bounds:
        total -= last_bounds[1]
    # Subtract left padding of first char (leading transparent pixels)
    first_bounds = DIGIT_BOUNDS.get(text[0])
    if first_bounds:
        total -= first_bounds[0]
    return total


def get_visual_left_pad(text):
    """Get the left transparent padding (in pixels) of the first character."""
    if not text:
        return 0
    bounds = DIGIT_BOUNDS.get(text[0])
    return bounds[0] if bounds else 0


def get_visual_right_pad(text):
    """Get the right transparent padding (in pixels) of the last character."""
    if not text:
        return 0
    bounds = DIGIT_BOUNDS.get(text[-1])
    return bounds[1] if bounds else 0


def get_text_width(text, font=None):
    """Return pixel width of text in the given font (variable-width glyphs)."""
    if font is None:
        font = terminalio.FONT
    if not text:
        return 0
    label = Label(font, text=str(text), color=0)
    return label.bounding_box[2]

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

def calculate_text_positions(home_team, away_team, home_score, away_score, char_width=None, padding=None, display_width=None, font=None):
    """Calculate positions for team names and scores using actual pixel widths (64x32 layout)."""
    if display_width is None:
        display_width = DISPLAY_WIDTH
    if char_width is None:
        char_width = CHAR_WIDTH
    if padding is None:
        padding = PADDING
    if font is None:
        font = terminalio.FONT
    team_space_min = TEAM_SPACE_CHARS * char_width

    away_team_w = get_text_width(away_team, font)
    away_score_w = get_text_width(away_score, font)
    home_team_w = get_text_width(home_team, font)
    home_score_w = get_text_width(home_score, font)

    # Use same column width for both sides so team names center symmetrically (e.g. LA and CHC)
    col_w = max(
        away_team_w, away_score_w,
        home_team_w, home_score_w,
        team_space_min,
    )
    away_col_w = home_col_w = col_w

    # Left column: center team and score in reserved width
    away_x = padding + (away_col_w - away_team_w) // 2
    away_score_x = padding + (away_col_w - away_score_w) // 2

    # Right column: center team and score in reserved width (same as left)
    home_base_x = display_width - padding - home_col_w
    home_x = home_base_x + (home_col_w - home_team_w) // 2
    home_score_x = home_base_x + (home_col_w - home_score_w) // 2

    away_right_edge = padding + away_col_w
    center_x = away_right_edge + (home_base_x - away_right_edge) // 2

    return {
        "away_x": away_x,
        "home_x": home_x,
        "away_score_x": away_score_x,
        "home_score_x": home_score_x,
        "center_x": center_x,
        "team_space_width": team_space_min,
    }

# Sport-specific display handling functions (moved from sport_display.py)

def handle_nfl_display(game, display_data, home_team, away_team, home_color, away_color, 
                      create_underline_fn, away_x, home_x):
    """Handle NFL-specific display logic"""
    # Clear any existing underline
    if 'underline' in display_data:
        del display_data['underline']
    
    # Handle possession indicator with underline (like MLB batting indicator)
    if game.get('possession'):
        poss_team = game.get('possession', '')
        if poss_team:
            home_team_abbr = game.get('home_team', '')
            away_team_abbr = game.get('away_team', '')
            
            # Add underline to show which team has possession
            if poss_team == home_team_abbr:
                w = min(18, max(1, get_text_width(home_team) - 1))
                underline = create_underline_fn(w, home_color)
                underline.x = home_x
                underline.y = UNDERLINE_Y_OFFSET
                display_data['underline'] = underline
            elif poss_team == away_team_abbr:
                w = min(18, max(1, get_text_width(away_team) - 1))
                underline = create_underline_fn(w, away_color)
                underline.x = away_x
                underline.y = UNDERLINE_Y_OFFSET
                display_data['underline'] = underline
    
    # Handle down and distance display
    if game.get('down_distance'):
        # If we have down and distance info, show that instead of clock
        # Remove spaces except around "on" to make it more readable
        down_distance = game.get('down_distance', '')
        # Replace " & " with "&" but keep spaces around "on"
        down_distance = down_distance.replace(' & ', '&').replace('on', ' on ')
        # Remove any double spaces that might have been created
        down_distance = down_distance.replace('  ', ' ')
        return down_distance[:10]  # Limit to 10 chars to accommodate " on "
    else:
        # If no down & distance, check for timeout in last play
        last_play = game.get('last_play', '').lower()
        clock = game.get('game_clock', '') or game.get('clock', '')
        
        if 'timeout' in last_play and clock:
            # Show "TO - 7:09" format for timeouts
            return f"TO - {clock}"[:10]  # Limit to 10 chars
    
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
        w = min(18, max(1, get_text_width(away_team) - 1))
        underline = create_underline_fn(w, away_color)
        underline.x = away_x
        underline.y = UNDERLINE_Y_OFFSET
        display_data['underline'] = underline
    elif period and len(period) > 0 and period[0].lower() == 'b':
        w = min(18, max(1, get_text_width(home_team) - 1))
        underline = create_underline_fn(w, home_color)
        underline.x = home_x
        underline.y = UNDERLINE_Y_OFFSET
        display_data['underline'] = underline

    # Handle baseball diamond
    bases = game.get('bases', {})
    if bases:
        diamond = create_baseball_diamond_fn(bases)
        diamond.x = center_x - DIAMOND_HALF_OFFSET
        diamond.y = DIAMOND_Y_OFFSET
        
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
        
        # Calculate score widths (actual pixel widths)
        away_score_width = get_text_width(str(game['away_score']))
        home_score_width = get_text_width(str(game['home_score']))

        # Add balls count under away team
        balls_text = f"B{balls}"
        balls_width = get_text_width(balls_text)
        balls_x = away_score_x + (away_score_width // 2) - (balls_width // 2)
        display_data['bottom_row'].append({'text': balls_text, 'color': DIM_GRAY, 'x': balls_x})

        # Add strikes count in center
        strikes_text = f"S{strikes}"
        strikes_width = get_text_width(strikes_text)
        strikes_x = center_x - (strikes_width // 2)
        display_data['bottom_row'].append({'text': strikes_text, 'color': DIM_GRAY, 'x': strikes_x})

        # Add outs count under home team
        outs_text = f"O{outs}"
        outs_width = get_text_width(outs_text)
        outs_x = home_score_x + (home_score_width // 2) - (outs_width // 2)
        display_data['bottom_row'].append({'text': outs_text, 'color': DIM_GRAY, 'x': outs_x})
        
        return ""
    
    return ""

def handle_game_status(game, display_data, center_x, char_width=None):
    """Handle different game statuses and return appropriate clock text"""
    if game["status"] == "Final":
        # Add F indicator in top row center
        final_text = "F"
        final_width = get_text_width(final_text)
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