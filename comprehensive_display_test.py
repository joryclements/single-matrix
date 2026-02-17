import asyncio
from display_manager import DisplayManager
from mock_games import MOCK_GAMES_BY_SPORT

class ComprehensiveDisplayTest:
    def __init__(self, display_manager: DisplayManager):
        self.display_manager = display_manager
        self.mock_games = MOCK_GAMES_BY_SPORT

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
