"""
Single display test module: quick, comprehensive, and status tests.
Run via run_tests.run_display_tests(display_manager, mode) with mode quick | comprehensive | status.
Can be run as __main__ for status tests (creates matrix and display manager).
"""
import asyncio
import random
import displayio
import terminalio
from adafruit_display_text.label import Label
from display_manager import DisplayManager
from config import DISPLAY_WIDTH, DISPLAY_HEIGHT
from mock_games import MOCK_GAMES_BY_SPORT, STATUS_TEST_LABELS, create_status_mock_game

# Random game data for comprehensive pass (broader status coverage)
RANDOM_TEAMS = {
    "MLB": {"AL": ["NYY", "BOS", "TOR", "BAL", "TB", "CLE", "CWS", "DET", "MIN", "KC", "HOU", "TEX", "LAA", "OAK", "SEA"],
            "NL": ["ATL", "MIA", "NYM", "PHI", "WSH", "CHC", "CIN", "MIL", "PIT", "STL", "ARI", "COL", "LAD", "SD", "SF"]},
    "NFL": {"AFC": ["BUF", "MIA", "NE", "NYJ", "BAL", "CIN", "CLE", "PIT", "HOU", "IND", "JAX", "TEN", "DEN", "KC", "LV", "LAC"],
            "NFC": ["DAL", "NYG", "PHI", "WAS", "CHI", "DET", "GB", "MIN", "ATL", "CAR", "NO", "TB", "ARI", "LAR", "SF", "SEA"]},
    "NBA": {"EAST": ["BOS", "BKN", "NYK", "PHI", "TOR", "CHI", "CLE", "DET", "IND", "MIL", "ATL", "CHA", "MIA", "ORL", "WAS"],
            "WEST": ["DEN", "MIN", "OKC", "POR", "UTA", "GSW", "LAC", "LAL", "PHX", "SAC", "DAL", "HOU", "MEM", "NO", "SA"]},
    "NHL": {"EAST": ["BOS", "BUF", "DET", "FLA", "MTL", "OTT", "TB", "TOR", "CAR", "CBJ", "NJ", "NYI", "NYR", "PHI", "PIT", "WSH"],
            "WEST": ["ANA", "ARI", "CGY", "EDM", "LA", "SJ", "VAN", "VGK", "CHI", "COL", "DAL", "MIN", "NSH", "STL", "WPG"]},
}
RANDOM_PERIODS = {
    "MLB": ["T1", "B1", "T2", "B2", "T3", "B3", "T4", "B4", "T5", "B5", "T6", "B6", "T7", "B7", "T8", "B8", "T9", "B9", "T10", "B10"],
    "NFL": ["1Q", "2Q", "3Q", "4Q", "OT"],
    "NBA": ["1Q", "2Q", "3Q", "4Q", "OT"],
    "NHL": ["1P", "2P", "3P", "OT", "SO"],
}
RANDOM_STATUSES = [
    "Scheduled", "Pre-Game", "1st Quarter", "2nd Quarter", "3rd Quarter", "4th Quarter", "Overtime", "Final",
    "1st Period", "2nd Period", "3rd Period", "Shootout", "Rain Delay", "Weather Delay", "Postponed", "Suspended", "Cancelled",
]


class ComprehensiveDisplayTest:
    def __init__(self, display_manager: DisplayManager):
        self.display_manager = display_manager
        self.mock_games = MOCK_GAMES_BY_SPORT

    def _random_teams(self, sport):
        if sport not in RANDOM_TEAMS:
            return "TEAM1", "TEAM2"
        conference = random.choice(list(RANDOM_TEAMS[sport].keys()))
        team_list = RANDOM_TEAMS[sport][conference]
        team1, team2 = random.sample(team_list, 2)
        return team1, team2

    def _random_period(self, sport):
        return random.choice(RANDOM_PERIODS[sport]) if sport in RANDOM_PERIODS else ""

    def _create_random_game(self, sport, status, has_scores=True, has_records=True):
        away_team, home_team = self._random_teams(sport)
        static = ["Scheduled", "Pre-Game", "Postponed", "Cancelled"]
        game = {
            "away_team": away_team,
            "home_team": home_team,
            "sport": sport,
            "status": status,
            "period": self._random_period(sport) if status not in static else "",
            "clock": "15:00" if status not in static else "",
        }
        if has_scores and status not in static:
            game["away_score"] = random.randint(0, 50)
            game["home_score"] = random.randint(0, 50)
        else:
            game["away_score"] = 0
            game["home_score"] = 0
        if has_records:
            game["away_record"] = f"{random.randint(10, 100)}-{random.randint(10, 100)}"
            game["home_record"] = f"{random.randint(10, 100)}-{random.randint(10, 100)}"
        else:
            game["away_record"] = ""
            game["home_record"] = ""
        return game

    async def test_all_sports_and_statuses(self):
        """Test every possible combination of sport and status"""
        print("🏈🏀⚾🏒 COMPREHENSIVE DISPLAY TEST")
        print("=" * 60)
        
        # Test each sport
        for sport in ["MLB", "NFL", "NBA", "NHL"]:
            print(f"\n🎯 Testing {sport}")
            print("-" * 40)
            
            # Set current sport
            self.display_manager.current_sport = sport
            
            # Test each game status for this sport
            for i, game in enumerate(self.mock_games[sport]):
                print(f"  Test {i+1}: {game['away_team']} vs {game['home_team']} - {game['status']}")
                
                try:
                    # Create display data
                    display_data = self.display_manager.create_game_text(game)
                    
                    # Display on matrix
                    await self.display_manager.display_scoreboard(display_data)
                    
                    # Show for appropriate time based on status
                    if game['status'] in ['Scheduled', 'Postponed']:
                        await asyncio.sleep(1.5)  # Quick view for static statuses
                    else:
                        await asyncio.sleep(2.5)  # Longer view for live/final games
                    
                    print(f"    ✅ {game['status']} display successful")
                    
                except Exception as e:
                    print(f"    ❌ {game['status']} display failed: {e}")
                    import traceback
                    print(f"    Traceback: {traceback.format_exc()}")

    async def test_edge_cases(self):
        """Test edge cases and unusual scenarios"""
        print("\n🔍 Testing Edge Cases")
        print("=" * 40)
        
        edge_cases = [
            # Zero scores
            {
                "home_team": "TEAM1", "away_team": "TEAM2", "home_score": 0, "away_score": 0,
                "status": "In Progress", "period": "1Q", "clock": "15:00",
                "home_record": "0-0", "away_record": "0-0"
            },
            # Very high scores
            {
                "home_team": "TEAM3", "away_team": "TEAM4", "home_score": 200, "away_score": 198,
                "status": "In Progress", "period": "4Q", "clock": "00:01",
                "home_record": "50-0", "away_record": "49-1"
            },
            # Long team names
            {
                "home_team": "LONGNAME", "away_team": "VERYLONG", "home_score": 5, "away_score": 3,
                "status": "Final", "period": "F", "clock": "0:00",
                "home_record": "45-35", "away_record": "42-38"
            },
            # Empty records
            {
                "home_team": "TEAM5", "away_team": "TEAM6", "home_score": 10, "away_score": 8,
                "status": "In Progress", "period": "2Q", "clock": "12:30",
                "home_record": "", "away_record": ""
            },
            # Empty period/clock (Scheduled)
            {
                "home_team": "TEAM5", "away_team": "TEAM6", "home_score": 0, "away_score": 0,
                "status": "Scheduled", "period": "", "clock": "",
                "home_record": "0-0", "away_record": "0-0"
            },
            # Special characters in team names
            {
                "home_team": "TEAM#", "away_team": "TEAM&", "home_score": 5, "away_score": 3,
                "status": "Final", "period": "F", "clock": "0:00",
                "home_record": "45-35", "away_record": "42-38"
            },
        ]
        
        for i, game in enumerate(edge_cases):
            print(f"  Edge Case {i+1}: {game['away_team']} vs {game['home_team']} - {game['status']}")
            
            try:
                # Create display data
                display_data = self.display_manager.create_game_text(game)
                
                # Display on matrix
                await self.display_manager.display_scoreboard(display_data)
                await asyncio.sleep(2)
                
                print(f"    ✅ Edge case {i+1} successful")
                
            except Exception as e:
                print(f"    ❌ Edge case {i+1} failed: {e}")

    async def test_display_modes(self):
        """Test ALL vs LIVE display modes"""
        print("\n🔄 Testing Display Modes")
        print("=" * 40)
        
        # Test ALL mode
        print("  Testing ALL mode")
        self.display_manager.show_all_games = True
        test_game = self.mock_games["MLB"][0]  # Use first MLB game
        
        try:
            display_data = self.display_manager.create_game_text(test_game)
            await self.display_manager.display_scoreboard(display_data)
            await asyncio.sleep(2)
            print("    ✅ ALL mode successful")
        except Exception as e:
            print(f"    ❌ ALL mode failed: {e}")
        
        # Test LIVE mode
        print("  Testing LIVE mode")
        self.display_manager.show_all_games = False
        test_game = self.mock_games["NFL"][0]  # Use first NFL game
        
        try:
            display_data = self.display_manager.create_game_text(test_game)
            await self.display_manager.display_scoreboard(display_data)
            await asyncio.sleep(2)
            print("    ✅ LIVE mode successful")
        except Exception as e:
            print(f"    ❌ LIVE mode failed: {e}")

    async def test_sport_transitions(self):
        """Test switching between sports"""
        print("\n🔄 Testing Sport Transitions")
        print("=" * 40)
        
        sports = ["MLB", "NFL", "NBA", "NHL", "SPORTS"]
        
        for sport in sports:
            print(f"  Testing transition to {sport}")
            
            # Simulate sport change
            self.display_manager.current_sport = sport
            self.display_manager.current_game_index = 0
            
            # Create a test game for this sport
            if sport == "SPORTS":
                # For SPORTS, create a mixed game
                test_game = self.mock_games["MLB"][0].copy()
                test_game["sport"] = "SPORTS"
            else:
                test_game = self.mock_games[sport][0]
            
            try:
                # Create display data
                display_data = self.display_manager.create_game_text(test_game)
                
                # Display on matrix
                await self.display_manager.display_scoreboard(display_data)
                await asyncio.sleep(1.5)
                
                print(f"    ✅ {sport} transition successful")
                
            except Exception as e:
                print(f"    ❌ {sport} transition failed: {e}")

    async def test_random_sports_and_statuses(self):
        """Random games across sports and key statuses (broader status coverage)."""
        print("\n🎲 Testing Random Games (sports × statuses)")
        print("=" * 40)
        test_statuses = ["Scheduled", "1st Quarter", "Final", "Postponed"]
        for sport in ["MLB", "NFL", "NBA", "NHL"]:
            self.display_manager.current_sport = sport
            for status in test_statuses:
                game = self._create_random_game(sport, status)
                try:
                    display_data = self.display_manager.create_game_text(game)
                    await self.display_manager.display_scoreboard(display_data)
                    await asyncio.sleep(1.5)
                    print(f"  ✅ {sport} {status}: {game['away_team']} @ {game['home_team']}")
                except Exception as e:
                    print(f"  ❌ {sport} {status}: {e}")
        print("  Random pass completed.")

    async def test_random_game_statuses(self):
        """Random MLB games for every status string (full status list)."""
        print("\n🎲 Testing All Status Strings (MLB random)")
        print("=" * 40)
        self.display_manager.current_sport = "MLB"
        for status in RANDOM_STATUSES:
            game = self._create_random_game("MLB", status)
            try:
                display_data = self.display_manager.create_game_text(game)
                await self.display_manager.display_scoreboard(display_data)
                await asyncio.sleep(1)
                print(f"  ✅ {status}")
            except Exception as e:
                print(f"  ❌ {status}: {e}")
        print("  All status strings completed.")

    async def run_comprehensive_test(self):
        """Run the complete comprehensive test suite (fixed mock data + random pass)."""
        print("🚀 Starting Comprehensive Display Test Suite")
        print("=" * 70)
        try:
            await self.test_all_sports_and_statuses()
            await self.test_edge_cases()
            await self.test_random_sports_and_statuses()
            await self.test_display_modes()
            await self.test_sport_transitions()
            print("\n" + "=" * 70)
            print("🎉 COMPREHENSIVE DISPLAY TEST COMPLETED SUCCESSFULLY!")
            print("=" * 70)
        except Exception as e:
            print(f"\n❌ Test suite failed with error: {e}")
            import traceback
            print(f"Full traceback:\n{traceback.format_exc()}")

    async def run_quick_test(self):
        """Run a quick test with key scenarios (fixed mock data, one game per sport)."""
        print("⚡ Running Quick Display Test")
        print("=" * 40)
        try:
            self.display_manager.display_static_text("TESTING")
            await asyncio.sleep(1)
            for sport in ["MLB", "NFL", "NBA", "NHL"]:
                test_game = self.mock_games[sport][0]
                print(f"  Testing {sport}: {test_game['away_team']} vs {test_game['home_team']} - {test_game['status']}")
                self.display_manager.current_sport = sport
                self.display_manager.display_static_text(sport)
                await asyncio.sleep(0.5)
                display_data = self.display_manager.create_game_text(test_game)
                await self.display_manager.display_scoreboard(display_data)
                await asyncio.sleep(2)
            print("\n✅ Quick test completed!")
        except Exception as e:
            print(f"❌ Quick test failed: {e}")
            import traceback
            print(f"Full traceback:\n{traceback.format_exc()}")

# --- Status-only tests (Rain Delay, Postponed, etc.) ---

async def _show_status_label(display_obj, text, color=0xFFFFFF):
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
    """Run status-only tests (Rain Delay, Postponed, Suspended, Cancelled, etc.)."""
    disp = display_manager.display
    total = len(STATUS_TEST_LABELS)
    try:
        await _show_status_label(disp, "STATUS TEST")
        for i, status in enumerate(STATUS_TEST_LABELS, 1):
            print(f"\n--- Testing Status {i}/{total}: '{status}' ---")
            await _show_status_label(disp, status)
            await _test_one_status(status, display_manager)
            await asyncio.sleep(1)
        await _show_status_label(disp, "TEST COMPLETE", color=0x00FF00)
        await asyncio.sleep(3)
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"Test error: {e}")
    finally:
        disp.root_group = displayio.Group()
        print("\nStatus display test completed!")


# --- Entry points for run_tests ---

async def run_comprehensive_display_test(display_manager, test_type="comprehensive"):
    """Run quick or comprehensive display test suite."""
    suite = ComprehensiveDisplayTest(display_manager)
    if test_type == "quick":
        await suite.run_quick_test()
    elif test_type == "comprehensive":
        await suite.run_comprehensive_test()
    else:
        print(f"Unknown test type: {test_type}. Use 'quick' or 'comprehensive'")


# Standalone: run status tests (e.g. python comprehensive_display_test.py on device)
if __name__ == "__main__":
    import board
    from adafruit_matrixportal.matrix import Matrix
    matrix = Matrix(width=DISPLAY_WIDTH, height=DISPLAY_HEIGHT, bit_depth=6)
    display = matrix.display

    class MockAPI:
        pass

    display_manager = DisplayManager(display, MockAPI())
    asyncio.run(run_status_tests(display_manager))
