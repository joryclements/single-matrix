from team_colors import NBA_COLORS, NFL_COLORS, NHL_COLORS, MLB_COLORS
BLACK = 0x000000
WHITE = 0xFFFFFF
GREEN = 0x00FF00
DIM_GRAY = 0x444444
GRAY = 0x202020

def get_team_color(team, current_sport):
    """Get the color for a team based on current sport"""
    if not team:
        print(f"Warning: Empty team name passed to get_team_color")
        return GRAY
        
    team_key = str(team).upper()
    
    if current_sport == "NBA":
        colors = NBA_COLORS
    elif current_sport == "NFL":
        colors = NFL_COLORS
    elif current_sport == "NHL":
        colors = NHL_COLORS
    elif current_sport == "MLB":
        colors = MLB_COLORS
    else:
        print(f"Warning: Unknown sport {current_sport}")
        colors = {}
    color = colors.get(team_key, GRAY) 
        
    return color

def format_game_time(date, include_date=False):
    """Format game time from various date formats to 12-hour time.
    If include_date is True, prepends M/DD like '2/19 7:00PM'."""
    try:
        if not date:
            return "TBD"

        # Extract date and time parts
        date_part = ""
        time_part = ""
        if ' ' in date:
            parts = date.split(' ')
            date_part = parts[0]
            if len(parts) > 1:
                time_part = parts[1][:5] if len(parts[1]) >= 5 else parts[1]
        elif 'T' in date:
            parts = date.split('T')
            date_part = parts[0]
            if len(parts) > 1:
                time_part = parts[1][:5] if len(parts[1]) >= 5 else parts[1]
        else:
            time_part = date

        if not time_part or ':' not in time_part:
            return "TBD"

        time_parts = time_part.split(':')
        if len(time_parts) < 2:
            return "TBD"

        hour, minute = time_parts[0], time_parts[1]
        hour_int = int(hour)

        if hour_int > 12:
            time_str = f"{hour_int-12}:{minute}PM"
        elif hour_int == 12:
            time_str = f"12:{minute}PM"
        elif hour_int == 0:
            time_str = f"12:{minute}AM"
        else:
            time_str = f"{hour_int}:{minute}AM"

        if include_date and date_part and '-' in date_part:
            # Parse "2026-02-19" -> "2/19"
            dp = date_part.split('-')
            month = int(dp[1])
            day = int(dp[2])
            return f"{month}/{day} {time_str}"

        return time_str

    except Exception as e:
        print(f"Error formatting time '{date}': {e}")
        return "TBD"

def parse_team_record(record):
    """Parse team record string into wins and losses"""
    try:
        record_parts = record.split('-')
        wins = record_parts[0] if len(record_parts) > 0 else ''
        losses = record_parts[1] if len(record_parts) > 1 else ''
        return wins, losses
    except (AttributeError, IndexError):
        return '', '' 