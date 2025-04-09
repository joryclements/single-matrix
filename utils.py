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
    if not date:
        return "TBD"
    if ' ' in date:
        time_part = date.split(' ')[1][:5]
    elif 'T' in date:
        time_part = date.split('T')[1][:5]
    else:
        time_part = date
    
    try:
        hour, minute = time_part.split(':')
        hour_int = int(hour)
        if hour_int > 12:
            return f"{hour_int-12}:{minute}PM"
        elif hour_int == 12:
            return f"12:{minute}PM"
        elif hour_int == 0:
            return f"12:{minute}AM"
        else:
            return f"{hour_int}:{minute}AM"
    except:
        return time_part

def parse_team_record(record):
    """Parse team record string into wins and losses"""
    try:
        record_parts = record.split('-')
        wins = record_parts[0] if len(record_parts) > 0 else ''
        losses = record_parts[1] if len(record_parts) > 1 else ''
        return wins, losses
    except (AttributeError, IndexError):
        return '', '' 