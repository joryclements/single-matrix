import asyncio
import time
from display_manager import DisplayManager

class ComprehensiveDisplayTest:
    def __init__(self, display_manager: DisplayManager):
        self.display_manager = display_manager
        
        # Realistic mock data based on actual API structure
        self.mock_games = {
            "MLB": [
                # Live game with scores
                {
                    "home_team": "NYY", "away_team": "BOS", "home_score": 3, "away_score": 2,
                    "status": "In Progress", "period": "B5",
                    "home_record": "45-35", "away_record": "42-38",
                    "date": "2025-09-03 20:05:00", "count": {"balls": 2, "strikes": 1}, "bases": {"first": True, "second": False, "third": True}
                },
                # Scheduled game
                {
                    "home_team": "LAD", "away_team": "SF", "home_score": 0, "away_score": 0,
                    "status": "Scheduled", "period": "", "clock": "",
                    "home_record": "50-30", "away_record": "38-42",
                    "date": "2025-09-03 22:10:00"
                },
                # Final game
                {
                    "home_team": "CHC", "away_team": "STL", "home_score": 5, "away_score": 3,
                    "status": "Final", "period": "F", "clock": "0:00",
                    "home_record": "40-40", "away_record": "35-45",
                    "date": "2025-09-03 19:05:00"
                },
                # Rain delay
                {
                    "home_team": "PHI", "away_team": "NYM", "home_score": 1, "away_score": 1,
                    "status": "Rain Delay", "period": "T3",
                    "home_record": "42-38", "away_record": "45-35",
                    "date": "2025-09-03 19:10:00"
                },
                # Weather delay
                {
                    "home_team": "HOU", "away_team": "TEX", "home_score": 2, "away_score": 0,
                    "status": "Weather Delay", "period": "B7",
                    "home_record": "48-32", "away_record": "44-36",
                    "date": "2025-09-03 20:00:00"
                },
                # Postponed
                {
                    "home_team": "ATL", "away_team": "MIA", "home_score": 0, "away_score": 0,
                    "status": "Postponed", "period": "", "clock": "",
                    "home_record": "46-34", "away_record": "39-41",
                    "date": "2025-09-03 19:05:00"
                },
                # Extra innings game
                {
                    "home_team": "OAK", "away_team": "SEA", "home_score": 4, "away_score": 4,
                    "status": "In Progress", "period": "T12",
                    "home_record": "35-45", "away_record": "38-42",
                    "date": "2025-09-03 20:15:00", "count": {"balls": 0, "strikes": 0}, "bases": {"first": False, "second": False, "third": False}
                },
                # Game with runners on base
                {
                    "home_team": "CLE", "away_team": "DET", "home_score": 6, "away_score": 5,
                    "status": "In Progress", "period": "B8",
                    "home_record": "42-38", "away_record": "40-40",
                    "date": "2025-09-03 19:20:00", "count": {"balls": 3, "strikes": 2}, "bases": {"first": True, "second": True, "third": False}
                }
            ],
            "NFL": [
                # Live game
                {
                    "home_team": "KC", "away_team": "BUF", "home_score": 17, "away_score": 14,
                    "status": "In Progress", "period": "2Q", "clock": "8:45",
                    "home_record": "8-2", "away_record": "7-3",
                    "date": "2025-09-03 20:00:00", "down_distance": "2nd & 7", "possession": "KC"
                },
                # Scheduled game
                {
                    "home_team": "DAL", "away_team": "PHI", "home_score": 0, "away_score": 0,
                    "status": "Scheduled", "period": "", "clock": "",
                    "home_record": "6-4", "away_record": "5-5",
                    "date": "2025-09-03 22:00:00"
                },
                # Final game
                {
                    "home_team": "NE", "away_team": "NYJ", "home_score": 24, "away_score": 17,
                    "status": "Final", "period": "F", "clock": "0:00",
                    "home_record": "4-6", "away_record": "3-7",
                    "date": "2025-09-03 19:00:00"
                },
                # Overtime
                {
                    "home_team": "BAL", "away_team": "CIN", "home_score": 28, "away_score": 28,
                    "status": "In Progress", "period": "OT", "clock": "12:30",
                    "home_record": "7-3", "away_record": "6-4",
                    "date": "2025-09-03 20:30:00"
                }
            ],
            "NBA": [
                # Live game
                {
                    "home_team": "LAL", "away_team": "BOS", "home_score": 98, "away_score": 95,
                    "status": "In Progress", "period": "4Q", "clock": "2:15",
                    "home_record": "35-15", "away_record": "40-10",
                    "date": "2025-09-03 20:30:00"
                },
                # Scheduled game
                {
                    "home_team": "GSW", "away_team": "PHX", "home_score": 0, "away_score": 0,
                    "status": "Scheduled", "period": "", "clock": "",
                    "home_record": "30-20", "away_record": "25-25",
                    "date": "2025-09-03 22:00:00"
                },
                # Final game
                {
                    "home_team": "MIA", "away_team": "ORL", "home_score": 112, "away_score": 108,
                    "status": "Final", "period": "F", "clock": "0:00",
                    "home_record": "28-22", "away_record": "26-24",
                    "date": "2025-09-03 19:00:00"
                },
                # High scoring game
                {
                    "home_team": "DAL", "away_team": "HOU", "home_score": 145, "away_score": 142,
                    "status": "In Progress", "period": "4Q", "clock": "0:05",
                    "home_record": "32-18", "away_record": "24-26",
                    "date": "2025-09-03 21:00:00"
                }
            ],
            "NHL": [
                # Live game
                {
                    "home_team": "TOR", "away_team": "MTL", "home_score": 2, "away_score": 1,
                    "status": "In Progress", "period": "2P", "clock": "8:45",
                    "home_record": "15-8", "away_record": "12-11",
                    "date": "2025-09-03 19:00:00"
                },
                # Scheduled game
                {
                    "home_team": "BOS", "away_team": "NYR", "home_score": 0, "away_score": 0,
                    "status": "Scheduled", "period": "", "clock": "",
                    "home_record": "18-5", "away_record": "16-7",
                    "date": "2025-09-03 21:00:00"
                },
                # Final game
                {
                    "home_team": "VGK", "away_team": "EDM", "home_score": 4, "away_score": 2,
                    "status": "Final", "period": "F", "clock": "0:00",
                    "home_record": "20-3", "away_record": "14-9",
                    "date": "2025-09-03 18:30:00"
                },
                # Shootout
                {
                    "home_team": "COL", "away_team": "MIN", "home_score": 3, "away_score": 3,
                    "status": "In Progress", "period": "SO", "clock": "0:00",
                    "home_record": "16-7", "away_record": "13-10",
                    "date": "2025-09-03 20:00:00"
                }
            ]
        }

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
            }
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

    async def run_comprehensive_test(self):
        """Run the complete comprehensive test suite"""
        print("🚀 Starting Comprehensive Display Test Suite")
        print("=" * 70)
        
        try:
            # Test all sports and statuses
            await self.test_all_sports_and_statuses()
            
            # Test edge cases
            await self.test_edge_cases()
            
            # Test display modes
            await self.test_display_modes()
            
            # Test sport transitions
            await self.test_sport_transitions()
            
            print("\n" + "=" * 70)
            print("🎉 COMPREHENSIVE DISPLAY TEST COMPLETED SUCCESSFULLY!")
            print("=" * 70)
            
        except Exception as e:
            print(f"\n❌ Test suite failed with error: {e}")
            import traceback
            print(f"Full traceback:\n{traceback.format_exc()}")

    async def run_quick_test(self):
        """Run a quick test with key scenarios"""
        print("⚡ Running Quick Display Test")
        print("=" * 40)
        
        try:
            # Test one game from each sport
            for sport in ["MLB", "NFL", "NBA", "NHL"]:
                test_game = self.mock_games[sport][0]  # First game from each sport
                print(f"  Testing {sport}: {test_game['away_team']} vs {test_game['home_team']} - {test_game['status']}")
                
                # Set sport
                self.display_manager.current_sport = sport
                
                # Create and display
                display_data = self.display_manager.create_game_text(test_game)
                await self.display_manager.display_scoreboard(display_data)
                await asyncio.sleep(2)
                
            print("\n✅ Quick test completed!")
            
        except Exception as e:
            print(f"❌ Quick test failed: {e}")
            import traceback
            print(f"Full traceback:\n{traceback.format_exc()}")

# Convenience function to run tests
async def run_comprehensive_display_test(display_manager, test_type="comprehensive"):
    """Run the comprehensive display test suite"""
    test_suite = ComprehensiveDisplayTest(display_manager)
    
    if test_type == "quick":
        await test_suite.run_quick_test()
    elif test_type == "comprehensive":
        await test_suite.run_comprehensive_test()
    else:
        print(f"Unknown test type: {test_type}. Use 'quick' or 'comprehensive'")
