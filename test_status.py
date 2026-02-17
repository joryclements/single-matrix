"""
Status-only display test: exercises status labels (Rain Delay, Postponed, etc.).
Can be run standalone (creates matrix/display) or via run_tests.run_display_tests(..., "status").
"""
import asyncio
import board
import displayio
import terminalio
from adafruit_matrixportal.matrix import Matrix
from adafruit_display_text.label import Label
from config import DISPLAY_WIDTH, DISPLAY_HEIGHT
from display_manager import DisplayManager
from mock_games import STATUS_TEST_LABELS, create_status_mock_game

# Used only when run as __main__
matrix = None
display = None


async def _show_on_display(display_obj, text, color=0xFFFFFF):
    """Show one centered label on the display."""
    group = displayio.Group()
    label = Label(terminalio.FONT, text=text, color=color, scale=1)
    label.anchor_point = (0.5, 0.5)
    label.anchored_position = (DISPLAY_WIDTH // 2, DISPLAY_HEIGHT // 2)
    group.append(label)
    display_obj.root_group = group
    await asyncio.sleep(2)


async def _test_one_status(status, display_manager):
    """Create and display one status via the display manager."""
    mock_game = create_status_mock_game(status)
    try:
        display_data = display_manager.create_game_text(mock_game)
        await display_manager.display_scoreboard(display_data)
        print(f"✅ Status '{status}' displayed successfully")
    except Exception as e:
        print(f"❌ Error displaying status '{status}': {e}")


async def run_status_tests(display_manager):
    """
    Run status-only tests using the given display_manager.
    Uses display_manager.display for status labels and display_manager for scoreboard.
    """
    disp = display_manager.display
    total = len(STATUS_TEST_LABELS)
    try:
        await _show_on_display(disp, "STATUS TEST")
        for i, status in enumerate(STATUS_TEST_LABELS, 1):
            print(f"\n--- Testing Status {i}/{total}: '{status}' ---")
            await _show_on_display(disp, status)
            await _test_one_status(status, display_manager)
            await asyncio.sleep(1)
        await _show_on_display(disp, "TEST COMPLETE", color=0x00FF00)
        await asyncio.sleep(3)
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"Test error: {e}")
    finally:
        disp.root_group = displayio.Group()
        print("\nStatus display test completed!")


def _create_display_and_manager():
    """Create matrix, display, and DisplayManager with MockAPI. For standalone run."""
    global matrix, display
    matrix = Matrix(width=DISPLAY_WIDTH, height=DISPLAY_HEIGHT, bit_depth=6)
    display = matrix.display

    class MockAPI:
        pass

    return DisplayManager(display, MockAPI())


async def main():
    """Standalone entry: create hardware and run status tests."""
    display_manager = _create_display_and_manager()
    await run_status_tests(display_manager)


if __name__ == "__main__":
    asyncio.run(main())
