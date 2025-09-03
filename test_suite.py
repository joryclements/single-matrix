import asyncio
import random
from display_manager import DisplayManager

print("🔧 Test suite module loaded successfully!")

class TestSuite:
    def __init__(self, display_manager: DisplayManager):
        self.display_manager = display_manager
        
        # Team data for each sport
        self.teams = {
            "MLB": {
                "AL": ["NYY", "BOS", "TOR", "BAL", "TB", "CLE", "CWS", "DET", "MIN", "KC", "HOU", "TEX", "LAA", "OAK", "SEA"],
                "NL": ["ATL", "MIA", "NYM", "PHI", "WSH", "CHC", "CIN", "MIL", "PIT", "STL", "ARI", "COL", "LAD", "SD", "SF"]
            },
            "NFL": {
                "AFC": ["BUF", "MIA", "NE", "NYJ", "BAL", "CIN", "CLE", "PIT", "HOU", "IND", "JAX", "TEN", "DEN", "KC", "LV", "LAC"],
                "NFC": ["DAL", "NYG", "PHI", "WAS", "CHI", "DET", "GB", "MIN", "ATL", "CAR", "NO", "TB", "ARI", "LAR", "SF", "SEA"]
            },
            "NBA": {
                "EAST": ["BOS", "BKN", "NYK", "PHI", "TOR", "CHI", "CLE", "DET", "IND", "MIL", "ATL", "CHA", "MIA", "ORL", "WAS"],
                "WEST": ["DEN", "MIN", "OKC", "POR", "UTA", "GSW", "LAC", "LAL", "PHX", "SAC", "DAL", "HOU", "MEM", "NO", "SA"]
            },
            "NHL": {
                "EAST": ["BOS", "BUF", "DET", "FLA", "MTL", "OTT", "TB", "TOR", "CAR", "CBJ", "NJ", "NYI", "NYR", "PHI", "PIT", "WSH"],
                "WEST": ["ANA", "ARI", "CGY", "EDM", "LA", "SJ", "VAN", "VGK", "CHI", "COL", "DAL", "MIN", "NSH", "STL", "WPG"]
            }
        }
        
        # Game statuses for testing
        self.game_statuses = [
            "Scheduled", "Pre-Game", "1st Quarter", "2nd Quarter", "3rd Quarter", "4th Quarter", "Overtime", "Final",
            "1st Period", "2nd Period", "3rd Period", "Shootout", "Rain Delay", "Weather Delay", "Postponed", "Suspended", "Cancelled"
        ]
        
        # Period indicators for each sport
        self.period_indicators = {
            "MLB": ["T1", "B1", "T2", "B2", "T3", "B3", "T4", "B4", "T5", "B5", "T6", "B6", "T7", "B7", "T8", "B8", "T9", "B9", "T10", "B10"],
            "NFL": ["1Q", "2Q", "3Q", "4Q", "OT"],
            "NBA": ["1Q", "2Q", "3Q", "4Q", "OT"],
            "NHL": ["1P", "2P", "3P", "OT", "SO"]
        }

    def get_random_teams(self, sport):
        """Get two random teams from the same conference/division"""
        if sport in self.teams:
            # Randomly choose a conference/division
            conference = random.choice(list(self.teams[sport].keys()))
            team_list = self.teams[sport][conference]
            
            # Get two different teams
            team1, team2 = random.sample(team_list, 2)
            return team1, team2
        return "TEAM1", "TEAM2"

    def get_random_period(self, sport):
        """Get a random period indicator for the sport"""
        if sport in self.period_indicators:
            return random.choice(self.period_indicators[sport])
        return ""

    def create_test_game(self, sport, status, has_scores=True, has_records=True):
        """Create a comprehensive test game with random data"""
        away_team, home_team = self.get_random_teams(sport)
        
        game = {
            'away_team': away_team,
            'home_team': home_team,
            'sport': sport,
            'status': status,
            'period': self.get_random_period(sport) if status not in ["Scheduled", "Pre-Game", "Postponed", "Cancelled"] else "",
            'clock': '15:00' if status not in ["Scheduled", "Pre-Game", "Postponed", "Cancelled"] else ''
        }
        
        # Add scores if appropriate
        if has_scores and status not in ["Scheduled", "Pre-Game", "Postponed", "Cancelled"]:
            game['away_score'] = random.randint(0, 50)
            game['home_score'] = random.randint(0, 50)
        else:
            game['away_score'] = 0
            game['home_score'] = 0
            
        # Add records if appropriate
        if has_records:
            game['away_record'] = f"{random.randint(10, 100)}-{random.randint(10, 100)}"
            game['home_record'] = f"{random.randint(10, 100)}-{random.randint(10, 100)}"
        else:
            game['away_record'] = ""
            game['home_record'] = ""
            
        return game

    async def test_all_sports(self):
        """Test all sports with various game statuses"""
        print("🏈🏀⚾🏒 Testing All Sports Display")
        print("=" * 50)
        
        for sport in ["MLB", "NFL", "NBA", "NHL"]:
            print(f"\n🎯 Testing {sport}")
            print("-" * 30)
            
            # Test different game statuses for each sport
            test_statuses = ["Scheduled", "1st Quarter", "Final", "Postponed"]
            
            for status in test_statuses:
                test_game = self.create_test_game(sport, status)
                print(f"  Testing: {test_game['away_team']} vs {test_game['home_team']} - {status}")
                
                try:
                    # Create display data
                    display_data = self.display_manager.create_game_text(test_game)
                    
                    # Display on matrix
                    await self.display_manager.display_scoreboard(display_data)
                    await asyncio.sleep(2)  # Show for 2 seconds
                    
                    print(f"    ✅ {status} display successful")
                    
                except Exception as e:
                    print(f"    ❌ {status} display failed: {e}")
                    
        print("\n🎉 All sports testing completed!")

    async def test_all_game_statuses(self):
        """Test all possible game statuses with MLB (most comprehensive)"""
        print("\n🔄 Testing All Game Statuses")
        print("=" * 50)
        
        for status in self.game_statuses:
            test_game = self.create_test_game("MLB", status)
            print(f"  Testing: {test_game['away_team']} vs {test_game['home_team']} - {status}")
            
            try:
                # Create display data
                display_data = self.display_manager.create_game_text(test_game)
                
                # Display on matrix
                await self.display_manager.display_scoreboard(display_data)
                await asyncio.sleep(1.5)  # Show for 1.5 seconds
                
                print(f"    ✅ {status} display successful")
                
            except Exception as e:
                print(f"    ❌ {status} display failed: {e}")
                
        print("\n🎉 All status testing completed!")

    async def test_edge_cases(self):
        """Test edge cases and unusual scenarios"""
        print("\n🔍 Testing Edge Cases")
        print("=" * 50)
        
        edge_cases = [
            # Very long team names (if any exist)
            {"away_team": "LONGNAME", "home_team": "VERYLONG", "sport": "MLB", "status": "1st Period", "away_score": 99, "home_score": 88, "period": "T1", "clock": "12:34"},
            
            # Zero scores
            {"away_team": "TEAM1", "home_team": "TEAM2", "sport": "NFL", "status": "2nd Quarter", "away_score": 0, "home_score": 0, "period": "2Q", "clock": "15:00"},
            
            # High scores
            {"away_team": "TEAM3", "home_team": "TEAM4", "sport": "NBA", "status": "4th Quarter", "away_score": 150, "home_score": 148, "period": "4Q", "clock": "00:05"},
            
            # Empty/None values
            {"away_team": "TEAM5", "home_team": "TEAM6", "sport": "NHL", "status": "Scheduled", "away_score": 0, "home_score": 0, "period": "", "clock": ""},
            
            # Special characters in team names
            {"away_team": "TEAM&", "home_team": "TEAM#", "sport": "MLB", "status": "Final", "away_score": 5, "home_score": 3, "period": "F", "clock": "0:00"},
        ]
        
        for i, test_case in enumerate(edge_cases):
            print(f"  Edge Case {i+1}: {test_case['away_team']} vs {test_case['home_team']} - {test_case['status']}")
            
            try:
                # Create display data
                display_data = self.display_manager.create_game_text(test_case)
                
                # Display on matrix
                await self.display_manager.display_scoreboard(display_data)
                await asyncio.sleep(1.5)
                
                print(f"    ✅ Edge case {i+1} successful")
                
            except Exception as e:
                print(f"    ❌ Edge case {i+1} failed: {e}")
                
        print("\n🎉 Edge case testing completed!")

    async def test_display_modes(self):
        """Test different display modes (ALL vs LIVE)"""
        print("\n🔄 Testing Display Modes")
        print("=" * 50)
        
        # Test ALL mode
        print("  Testing ALL mode display")
        self.display_manager.show_all_games = True
        test_game = self.create_test_game("MLB", "1st Period")
        try:
            display_data = self.display_manager.create_game_text(test_game)
            await self.display_manager.display_scoreboard(display_data)
            await asyncio.sleep(2)
            print("    ✅ ALL mode successful")
        except Exception as e:
            print(f"    ❌ ALL mode failed: {e}")
        
        # Test LIVE mode
        print("  Testing LIVE mode display")
        self.display_manager.show_all_games = False
        test_game = self.create_test_game("NFL", "2nd Quarter")
        try:
            display_data = self.display_manager.create_game_text(test_game)
            await self.display_manager.display_scoreboard(display_data)
            await asyncio.sleep(2)
            print("    ✅ LIVE mode successful")
        except Exception as e:
            print(f"    ❌ LIVE mode failed: {e}")
            
        print("\n🎉 Display mode testing completed!")

    async def test_sport_transitions(self):
        """Test switching between sports"""
        print("\n🔄 Testing Sport Transitions")
        print("=" * 50)
        
        sports = ["MLB", "NFL", "NBA", "NHL", "SPORTS"]
        
        for sport in sports:
            print(f"  Testing transition to {sport}")
            
            # Simulate sport change
            self.display_manager.current_sport = sport
            self.display_manager.current_game_index = 0
            
            # Create a test game for this sport
            if sport == "SPORTS":
                # For SPORTS, create a mixed game
                test_game = self.create_test_game("MLB", "1st Period")
                test_game["sport"] = "SPORTS"
            else:
                test_game = self.create_test_game(sport, "1st Period")
            
            try:
                # Create display data
                display_data = self.display_manager.create_game_text(test_game)
                
                # Display on matrix
                await self.display_manager.display_scoreboard(display_data)
                await asyncio.sleep(1.5)
                
                print(f"    ✅ {sport} transition successful")
                
            except Exception as e:
                print(f"    ❌ {sport} transition failed: {e}")
                
        print("\n🎉 Sport transition testing completed!")

    async def run_comprehensive_test(self):
        """Run the complete comprehensive test suite"""
        print("🚀 Starting Comprehensive Test Suite")
        print("=" * 60)
        
        try:
            # Test all sports
            await self.test_all_sports()
            
            # Test all game statuses
            await self.test_all_game_statuses()
            
            # Test edge cases
            await self.test_edge_cases()
            
            # Test display modes
            await self.test_display_modes()
            
            # Test sport transitions
            await self.test_sport_transitions()
            
            print("\n" + "=" * 60)
            print("🎉 COMPREHENSIVE TEST SUITE COMPLETED SUCCESSFULLY!")
            print("=" * 60)
            
        except Exception as e:
            print(f"\n❌ Test suite failed with error: {e}")
            import traceback
            print(f"Full traceback:\n{traceback.format_exc()}")

    async def run_quick_test(self):
        """Run a quick test with just a few key scenarios"""
        print("⚡ Running Quick Test")
        print("=" * 30)
        
        # Show "TESTING" on the matrix first
        try:
            self.display_manager.display_static_text("TESTING")
            await asyncio.sleep(1)
            print("  ✅ 'TESTING' displayed on matrix")
        except Exception as e:
            print(f"  ❌ Failed to display 'TESTING': {e}")
        
        try:
            # Test one game from each sport
            for sport in ["MLB", "NFL", "NBA", "NHL"]:
                test_game = self.create_test_game(sport, "1st Period")
                print(f"  Testing {sport}: {test_game['away_team']} vs {test_game['home_team']}")
                
                # Show sport name on matrix
                self.display_manager.display_static_text(sport)
                await asyncio.sleep(0.5)
                
                # Show the actual game
                display_data = self.display_manager.create_game_text(test_game)
                await self.display_manager.display_scoreboard(display_data)
                await asyncio.sleep(2)  # Show each game for 2 seconds
                
            print("\n✅ Quick test completed!")
            
        except Exception as e:
            print(f"❌ Quick test failed: {e}")
            import traceback
            print(f"Full traceback:\n{traceback.format_exc()}")

# Convenience function to run tests
async def run_test_suite(display_manager, test_type="comprehensive"):
    """Run the test suite with the specified test type"""
    test_suite = TestSuite(display_manager)
    
    if test_type == "quick":
        await test_suite.run_quick_test()
    elif test_type == "comprehensive":
        await test_suite.run_comprehensive_test()
    else:
        print(f"Unknown test type: {test_type}. Use 'quick' or 'comprehensive'")
