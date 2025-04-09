import os
import sys
import time
import asyncio
import board
import displayio
import terminalio
from adafruit_matrixportal.matrix import Matrix
from adafruit_display_text.label import Label
from team_colors import (
    NBA_COLORS, NFL_COLORS, NHL_COLORS, MLB_COLORS,
    BLACK, WHITE, GRAY, 
    BLUE, NAVY, GREEN, FOREST_GREEN, SKY_BLUE,
    RED, BURGUNDY, ORANGE,
    PURPLE, LAVENDER, TEAL, LIGHT_CYAN,
    BRIGHT_YELLOW, GOLDEN_YELLOW
)

# Constants
DISPLAY_WIDTH = 64
DISPLAY_HEIGHT = 32

# Initialize the Matrix
matrix = Matrix(width=DISPLAY_WIDTH, height=DISPLAY_HEIGHT, bit_depth=6)
display = matrix.display

# Dictionary to map color values to color names
COLOR_NAMES = {
    BLACK: "BLACK",
    WHITE: "WHITE",
    GRAY: "GRAY",
    BLUE: "BLUE",
    NAVY: "NAVY",
    GREEN: "GREEN",
    FOREST_GREEN: "FOREST_GREEN",
    SKY_BLUE: "SKY_BLUE",
    RED: "RED",
    BURGUNDY: "BURGUNDY",
    ORANGE: "ORANGE",
    PURPLE: "PURPLE",
    LAVENDER: "LAVENDER",
    TEAL: "TEAL",
    LIGHT_CYAN: "LIGHT_CYAN",
    BRIGHT_YELLOW: "BRIGHT_YELLOW",
    GOLDEN_YELLOW: "GOLDEN_YELLOW"
}

# Delay for each team
DELAY_TIME = 2  # seconds to show each team

async def display_team_color(team, color, sport, teams_count=None, team_idx=None, delay=DELAY_TIME):
    """Display a team name with its color"""
    group = displayio.Group()
        
    # Number of teams indicator
    counter_text = ""
    if teams_count is not None and team_idx is not None:
        counter_text = f" {team_idx}/{teams_count}"
    
    # Create the sport label at the top
    sport_label = Label(terminalio.FONT, text=f"{sport}{counter_text}", color=GRAY, scale=1)
    sport_label.anchor_point = (0.5, 0)
    sport_label.anchored_position = (DISPLAY_WIDTH // 2, 2)
    group.append(sport_label)
    
    # Create the team name label
    team_label = Label(terminalio.FONT, text=f"{team}", color=color, scale=1)
    team_label.anchor_point = (0.5, 0.5)
    team_label.anchored_position = (DISPLAY_WIDTH // 2, DISPLAY_HEIGHT // 2)
    group.append(team_label)
    
    # Display the color name or hex value
    color_name = COLOR_NAMES.get(color, f"0x{color:06X}")
    
    color_label = Label(terminalio.FONT, text=color_name, color=GRAY, scale=1)
    color_label.anchor_point = (0.5, 1)
    color_label.anchored_position = (DISPLAY_WIDTH // 2, DISPLAY_HEIGHT - 2)
    group.append(color_label)
    
    display.root_group = group
    await asyncio.sleep(delay)

async def test_specific_teams(teams_to_test):
    """Display only specific teams from each league
    
    teams_to_test format: {
        "NBA": ["DAL", "TOR"],
        "NFL": ["SF", "KC"]
    }
    """
    sport_colors = {
        "NBA": NBA_COLORS,
        "NFL": NFL_COLORS,
        "NHL": NHL_COLORS,
        "MLB": MLB_COLORS
    }
    
    total_teams = 0
    for sport, teams in teams_to_test.items():
        for team in teams:
            if team in sport_colors[sport]:
                total_teams += 1
    
    current_idx = 1
    for sport, team_list in teams_to_test.items():
        if not team_list:  # Skip if empty list
            continue
            
        # Display sport header
        group = displayio.Group()
        sport_header = Label(terminalio.FONT, text=f"TESTING: {sport}", color=WHITE, scale=1)
        sport_header.anchor_point = (0.5, 0.5)
        sport_header.anchored_position = (DISPLAY_WIDTH // 2, DISPLAY_HEIGHT // 2)
        group.append(sport_header)
        
        teams_count = Label(terminalio.FONT, text=f"{len(team_list)} teams", color=GRAY, scale=1)
        teams_count.anchor_point = (0.5, 0.5)
        teams_count.anchored_position = (DISPLAY_WIDTH // 2, DISPLAY_HEIGHT // 2 + 10)
        group.append(teams_count)
        
        display.root_group = group
        await asyncio.sleep(1)
        
        # Display only the selected teams for this sport
        for team in team_list:
            if team in sport_colors[sport]:
                color = sport_colors[sport][team]
                await display_team_color(team, color, sport, total_teams, current_idx)
                current_idx += 1
            else:
                print(f"Warning: Team {team} not found in {sport}")

async def cycle_teams():
    """Cycle through all team names in all sports"""
    # Create a list of all sports and their teams
    sports_teams = [
        ("NBA", NBA_COLORS),
        ("NFL", NFL_COLORS),
        ("NHL", NHL_COLORS),
        ("MLB", MLB_COLORS)
    ]
    
    while True:  # Loop forever
        for sport_name, team_colors in sports_teams:
            # Display sport header
            group = displayio.Group()
            sport_header = Label(terminalio.FONT, text=f"SPORT: {sport_name}", color=WHITE, scale=1)
            sport_header.anchor_point = (0.5, 0.5)
            sport_header.anchored_position = (DISPLAY_WIDTH // 2, DISPLAY_HEIGHT // 2)
            group.append(sport_header)
            
            teams_count = Label(terminalio.FONT, text=f"{len(team_colors)} teams", color=GRAY, scale=1)
            teams_count.anchor_point = (0.5, 0.5)
            teams_count.anchored_position = (DISPLAY_WIDTH // 2, DISPLAY_HEIGHT // 2 + 10)
            group.append(teams_count)
            
            display.root_group = group
            await asyncio.sleep(1)
            
            # Display each team in the sport
            total_teams = len(team_colors)
            for idx, (team, color) in enumerate(team_colors.items(), 1):
                await display_team_color(team, color, sport_name, total_teams, idx)

def parse_teams_arg(arg_str):
    """Parse a command line argument string for teams to test
    
    Format: 'NBA:DAL,TOR;NFL:SF,KC'
    Returns: {
        "NBA": ["DAL", "TOR"],
        "NFL": ["SF", "KC"]
    }
    """
    teams_to_test = {
        "NBA": ["PHX    " ],
        "NFL": [],
        "NHL": [],
        "MLB": []
    }
    
    if not arg_str:
        return teams_to_test
        
    try:
        # Split by league sections
        league_sections = arg_str.split(';')
        
        for section in league_sections:
            if ':' not in section:
                continue
                
            league, teams = section.split(':', 1)
            if league in teams_to_test:
                teams_to_test[league] = [t.strip() for t in teams.split(',') if t.strip()]
    except Exception as e:
        print(f"Error parsing teams arg: {e}")
        
    return teams_to_test

async def main():
    """Main function"""
    try:
        # Show startup message
        group = displayio.Group()
        title = Label(terminalio.FONT, text="TEAM COLORS", color=WHITE, scale=1)
        title.anchor_point = (0.5, 0.5)
        title.anchored_position = (DISPLAY_WIDTH // 2, DISPLAY_HEIGHT // 2 - 5)
        group.append(title)
        
        display.root_group = group
        await asyncio.sleep(2)
        
        # Check for command line arg with teams to test
        teams_to_test = {
            "NBA": [],
            "NFL": [],
            "NHL": [],
            "MLB": []
        }
        
        # Get teams from command line if provided
        if len(sys.argv) > 1:
            teams_to_test = parse_teams_arg(sys.argv[1])
            print(f"Testing teams: {teams_to_test}")
        else:
            # Default teams to test when no args provided
            teams_to_test = {
                # Example: Uncomment to test specific teams
                # "NBA": ["PHX", "NY"],
                "NFL": ["PHI", "CHI"],
                # "NHL": [],
                # "MLB": []
            }
        
        # If teams_to_test has entries, test those teams only
        if any(teams_to_test.values()):
            await test_specific_teams(teams_to_test)
        else:
            # Otherwise cycle through all teams
            await cycle_teams()
            
    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        # Clear display
        group = displayio.Group()
        display.root_group = group

# Run the main function
if __name__ == "__main__":
    asyncio.run(main()) 