"""
Shared mock game data for display tests.
Single source of truth for comprehensive and quick tests.
"""

MOCK_GAMES_BY_SPORT = {
    "MLB": [
        {
            "home_team": "NYY", "away_team": "BOS", "home_score": 3, "away_score": 2,
            "status": "In Progress", "period": "B5",
            "home_record": "45-35", "away_record": "42-38",
            "date": "2025-09-03 20:05:00", "count": {"balls": 2, "strikes": 1},
            "bases": {"first": True, "second": False, "third": True},
        },
        {
            "home_team": "LAD", "away_team": "SF", "home_score": 0, "away_score": 0,
            "status": "Scheduled", "period": "", "clock": "",
            "home_record": "50-30", "away_record": "38-42",
            "date": "2025-09-03 22:10:00",
        },
        {
            "home_team": "CHC", "away_team": "STL", "home_score": 5, "away_score": 3,
            "status": "Final", "period": "F", "clock": "0:00",
            "home_record": "40-40", "away_record": "35-45",
            "date": "2025-09-03 19:05:00",
        },
        {
            "home_team": "PHI", "away_team": "NYM", "home_score": 1, "away_score": 1,
            "status": "Rain Delay", "period": "T3",
            "home_record": "42-38", "away_record": "45-35",
            "date": "2025-09-03 19:10:00",
        },
        {
            "home_team": "HOU", "away_team": "TEX", "home_score": 2, "away_score": 0,
            "status": "Weather Delay", "period": "B7",
            "home_record": "48-32", "away_record": "44-36",
            "date": "2025-09-03 20:00:00",
        },
        {
            "home_team": "ATL", "away_team": "MIA", "home_score": 0, "away_score": 0,
            "status": "Postponed", "period": "", "clock": "",
            "home_record": "46-34", "away_record": "39-41",
            "date": "2025-09-03 19:05:00",
        },
        {
            "home_team": "OAK", "away_team": "SEA", "home_score": 4, "away_score": 4,
            "status": "In Progress", "period": "T12",
            "home_record": "35-45", "away_record": "38-42",
            "date": "2025-09-03 20:15:00", "count": {"balls": 0, "strikes": 0},
            "bases": {"first": False, "second": False, "third": False},
        },
        {
            "home_team": "CLE", "away_team": "DET", "home_score": 6, "away_score": 5,
            "status": "In Progress", "period": "B8",
            "home_record": "42-38", "away_record": "40-40",
            "date": "2025-09-03 19:20:00", "count": {"balls": 3, "strikes": 2},
            "bases": {"first": True, "second": True, "third": False},
        },
    ],
    "NFL": [
        {
            "home_team": "KC", "away_team": "BUF", "home_score": 17, "away_score": 14,
            "status": "In Progress", "period": "2Q", "clock": "8:45",
            "home_record": "8-2", "away_record": "7-3",
            "date": "2025-09-03 20:00:00", "down_distance": "2nd & 7", "possession": "KC",
        },
        {
            "home_team": "DAL", "away_team": "PHI", "home_score": 0, "away_score": 0,
            "status": "Scheduled", "period": "", "clock": "",
            "home_record": "6-4", "away_record": "5-5",
            "date": "2025-09-03 22:00:00",
        },
        {
            "home_team": "NE", "away_team": "NYJ", "home_score": 24, "away_score": 17,
            "status": "Final", "period": "F", "clock": "0:00",
            "home_record": "4-6", "away_record": "3-7",
            "date": "2025-09-03 19:00:00",
        },
        {
            "home_team": "BAL", "away_team": "CIN", "home_score": 28, "away_score": 28,
            "status": "In Progress", "period": "OT", "clock": "12:30",
            "home_record": "7-3", "away_record": "6-4",
            "date": "2025-09-03 20:30:00",
        },
    ],
    "NBA": [
        {
            "home_team": "LAL", "away_team": "BOS", "home_score": 98, "away_score": 95,
            "status": "In Progress", "period": "4Q", "clock": "2:15",
            "home_record": "35-15", "away_record": "40-10",
            "date": "2025-09-03 20:30:00",
        },
        {
            "home_team": "GSW", "away_team": "PHX", "home_score": 0, "away_score": 0,
            "status": "Scheduled", "period": "", "clock": "",
            "home_record": "30-20", "away_record": "25-25",
            "date": "2025-09-03 22:00:00",
        },
        {
            "home_team": "MIA", "away_team": "ORL", "home_score": 112, "away_score": 108,
            "status": "Final", "period": "F", "clock": "0:00",
            "home_record": "28-22", "away_record": "26-24",
            "date": "2025-09-03 19:00:00",
        },
        {
            "home_team": "DAL", "away_team": "HOU", "home_score": 145, "away_score": 142,
            "status": "In Progress", "period": "4Q", "clock": "0:05",
            "home_record": "32-18", "away_record": "24-26",
            "date": "2025-09-03 21:00:00",
        },
    ],
    "NHL": [
        {
            "home_team": "TOR", "away_team": "MTL", "home_score": 2, "away_score": 1,
            "status": "In Progress", "period": "2P", "clock": "8:45",
            "home_record": "15-8", "away_record": "12-11",
            "date": "2025-09-03 19:00:00",
        },
        {
            "home_team": "BOS", "away_team": "NYR", "home_score": 0, "away_score": 0,
            "status": "Scheduled", "period": "", "clock": "",
            "home_record": "18-5", "away_record": "16-7",
            "date": "2025-09-03 21:00:00",
        },
        {
            "home_team": "VGK", "away_team": "EDM", "home_score": 4, "away_score": 2,
            "status": "Final", "period": "F", "clock": "0:00",
            "home_record": "20-3", "away_record": "14-9",
            "date": "2025-09-03 18:30:00",
        },
        {
            "home_team": "COL", "away_team": "MIN", "home_score": 3, "away_score": 3,
            "status": "In Progress", "period": "SO", "clock": "0:00",
            "home_record": "16-7", "away_record": "13-10",
            "date": "2025-09-03 20:00:00",
        },
    ],
}

# Statuses used by status-only test (display labels like RAIN DELAY, POSTPONED)
STATUS_TEST_LABELS = [
    "Rain Delay",
    "Postponed",
    "Suspended",
    "Cancelled",
]


def create_status_mock_game(status, sport="MLB"):
    """Create a minimal mock game for testing a specific status label."""
    return {
        "home_team": "ATL",
        "away_team": "PHI",
        "home_score": 0,
        "away_score": 0,
        "status": status,
        "sport": sport,
        "period": "",
        "clock": "",
        "date": "2025-06-27 19:15:00",
        "venue": "Test Stadium",
        "home_record": "37-43",
        "away_record": "47-34",
        "last_play": "",
        "down_distance": "",
        "possession": "",
        "count": {},
        "bases": {},
    }
