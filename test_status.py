import os
import asyncio
import board
import displayio
import terminalio
from adafruit_matrixportal.matrix import Matrix
from adafruit_display_text.label import Label
from display_manager import DisplayManager
from api import SportsAPI

# Constants
DISPLAY_WIDTH = 64
DISPLAY_HEIGHT = 32

# Initialize the Matrix
matrix = Matrix(width=DISPLAY_WIDTH, height=DISPLAY_HEIGHT, bit_depth=6)
display = matrix.display

# Test status texts
TEST_STATUSES = [
    "RAIN DELAY",
    "POSTPONED", 
    "SUSPENDED",
    "CANCELLED",
]

def create_mock_game(status, sport="MLB"):
    """Create a mock game with the given status"""
    return {
        'home_team': 'ATL',
        'away_team': 'PHI', 
        'home_score': '0',
        'away_score': '0',
        'status': status,
        'sport': sport,
        'period': '',
        'clock': '',
        'date': '2025-06-27 19:15:00',
        'venue': 'Test Stadium',
        'home_record': '37-43',
        'away_record': '47-34',
        'last_play': '',
        'down_distance': '',
        'possession': '',
        'count': {},
        'bases': {}
    }

async def test_status_display(status, display_manager):
    """Test displaying a specific status"""
    # Create mock game with the status
    mock_game = create_mock_game(status)
    
    try:
        # Create game text display
        game_text_lines = display_manager.create_game_text(mock_game)
        
        # Display it
        await display_manager.display_scoreboard(game_text_lines)
        
        print(f"✅ Status '{status}' displayed successfully")
        
    except Exception as e:
        print(f"❌ Error displaying status '{status}': {e}")

async def display_status_info(status, index, total):
    """Display status information on screen"""
    group = displayio.Group()
    
    # Status counter

    # Current status being tested
    status_label = Label(terminalio.FONT, text=f"{status}", color=0xFFFFFF, scale=1)
    status_label.anchor_point = (0.5, 0.5)
    status_label.anchored_position = (DISPLAY_WIDTH // 2, DISPLAY_HEIGHT // 2)
    group.append(status_label)
    
    
    display.root_group = group
    await asyncio.sleep(2)

async def main():
    """Main test function"""
    try:
        # Show startup message
        group = displayio.Group()
        title = Label(terminalio.FONT, text="STATUS TEST", color=0xFFFFFF, scale=1)
        title.anchor_point = (0.5, 0.5)
        title.anchored_position = (DISPLAY_WIDTH // 2, DISPLAY_HEIGHT // 2)
        group.append(title)
        
        display.root_group = group
        await asyncio.sleep(2)
        
        # Initialize display manager (without API since we're using mock data)
        class MockAPI:
            pass
        
        display_manager = DisplayManager(display, MockAPI())
        
        total_statuses = len(TEST_STATUSES)
        
        # Test each status
        for i, status in enumerate(TEST_STATUSES, 1):
            print(f"\n--- Testing Status {i}/{total_statuses}: '{status}' ---")
            
            # Show what we're testing
            await display_status_info(status, i, total_statuses)
            
            # Test the actual display
            await test_status_display(status, display_manager)
            
            # Brief pause between tests
            await asyncio.sleep(1)
        
        # Show completion message
        group = displayio.Group()
        title = Label(terminalio.FONT, text="TEST COMPLETE", color=0x00FF00, scale=1)
        title.anchor_point = (0.5, 0.5)
        title.anchored_position = (DISPLAY_WIDTH // 2, DISPLAY_HEIGHT // 2)
        group.append(title)
        
        display.root_group = group
        await asyncio.sleep(3)
        
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"Test error: {e}")
    finally:
        # Clear display
        group = displayio.Group()
        display.root_group = group
        print("\nStatus display test completed!")

# Run the test
if __name__ == "__main__":
    asyncio.run(main())