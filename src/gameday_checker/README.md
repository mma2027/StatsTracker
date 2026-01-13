# Gameday Checker Module

## Purpose
Determines which Haverford College sports teams have games on a given day by scraping the athletics website.

## Implementation Details

This module fetches game schedules from https://haverfordathletics.com by:
1. Iterating through all Haverford sports
2. Fetching each sport's schedule page
3. Extracting embedded JSON data from the JavaScript on each page
4. Parsing game information and filtering by date

## Interface

### Main Class: `GamedayChecker`

#### Methods

```python
def get_games_for_date(self, check_date: date) -> List[Game]:
    """Get all games scheduled for a specific date"""

def get_games_for_today(self) -> List[Game]:
    """Get all games scheduled for today"""

def get_games_for_team(self, team_name: str, start_date: date, end_date: date) -> List[Game]:
    """Get all games for a specific team within a date range"""

def has_games_on_date(self, check_date: date) -> bool:
    """Check if there are any games on a specific date"""
```

### Data Models

#### `Game`
- `team`: Team object
- `opponent`: str
- `date`: datetime
- `location`: str (home/away)
- `time`: Optional[str]

#### `Team`
- `name`: str
- `sport`: str
- `division`: Optional[str]

## Implementation Status

✅ **Completed** - The gameday checker is fully implemented and working.

### How It Works

The module uses Haverford's athletics calendar AJAX endpoint:
- Endpoint: `https://haverfordathletics.com/services/responsive-calendar.ashx`
- Makes a single request to fetch a full month of games across all sports
- Returns clean JSON data (no HTML scraping required)
- Games are parsed from the response and filtered by the requested date

### Features

- ✅ **Full season access** - Can fetch games months in advance
- ✅ **Fast performance** - Single HTTP request instead of 17+ per query
- ✅ Parse opponent, location (home/away), and time information
- ✅ Handle all sports automatically in one request
- ✅ Robust error handling with logging
- ✅ Returns structured Game objects
- ✅ Clean JSON API (no regex scraping)

### Performance Improvements

**Before (sport pages):** 17+ HTTP requests, 30-60 seconds, rolling window only
**After (calendar endpoint):** 1 HTTP request, ~2-5 seconds, full season access ⚡

## Testing

Unit tests are located in `tests/gameday_checker/test_checker.py`:
- ✅ Test finding games on various dates (January, March, April, etc.)
- ✅ Test game details (opponent, time, location)
- ✅ Test with real data from live endpoint
- ✅ Test edge cases and error conditions

Run tests with: `pytest tests/gameday_checker/test_checker.py -v`

## Dependencies

- `requests` - For HTTP requests to fetch calendar data
- Standard library: `datetime`, `logging`

## Performance Notes

- Makes 1 HTTP request per query (calendar endpoint)
- Request takes ~2-5 seconds depending on network latency
- Returns full month of data in single response
- **Optimization**: Consider caching calendar data for 1-2 hours to reduce load on athletics website

## Example Usage

```python
from datetime import date
from src.gameday_checker import GamedayChecker

# Initialize the checker
checker = GamedayChecker(schedule_url="https://haverfordathletics.com")

# Get today's games
today_games = checker.get_games_for_today()
print(f"Games today: {len(today_games)}")
for game in today_games:
    print(f"  {game.team.sport}: {game.team.name} vs {game.opponent}")
    print(f"    Time: {game.time}, Location: {game.location}")

# Check a specific date
games = checker.get_games_for_date(date(2026, 2, 22))
if games:
    print(f"\nFound {len(games)} games on 2026-02-22:")
    for game in games:
        home_away = "Home" if game.is_home_game else "Away"
        print(f"  - {game.team.sport}: vs {game.opponent} ({home_away})")

# Check if games exist on a date
has_games = checker.has_games_on_date(date(2026, 2, 22))
print(f"\nGames on 2026-02-22: {has_games}")
```

See `example_usage.py` for a complete working example.

## Integration Points

- **Used by**: Main orchestrator to check if notifications should be sent
- **Uses**: Configuration file for schedule URL
- **Output format**: List of Game objects that other modules can process
