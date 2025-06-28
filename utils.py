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
    
    print(f"Getting color for team: {team_key} in sport: {current_sport}")
    
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

def format_game_time(date):
    """Format game time from various date formats to 12-hour time"""
    try:
        if not date:
            return "TBD"
            
        # Safely extract time part
        time_part = ""
        if ' ' in date:
            parts = date.split(' ')
            if len(parts) > 1:
                time_part = parts[1][:5] if len(parts[1]) >= 5 else parts[1]
        elif 'T' in date:
            parts = date.split('T')
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
            return f"{hour_int-12}:{minute}PM"
        elif hour_int == 12:
            return f"12:{minute}PM"
        elif hour_int == 0:
            return f"12:{minute}AM"
        else:
            return f"{hour_int}:{minute}AM"
            
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