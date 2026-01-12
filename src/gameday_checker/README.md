# Gameday Checker Module

## Purpose
Determines which Haverford College sports teams have games on a given day.

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

## Implementation Tasks

1. **Data Source Integration**
   - Determine the data source (Haverford athletics website, API, etc.)
   - Implement web scraping or API calls in `_fetch_games()`

2. **Parsing Logic**
   - Parse schedule data into Game objects
   - Handle different date formats
   - Extract team, opponent, and location information

3. **Error Handling**
   - Handle network errors
   - Handle parsing errors
   - Return empty list on failure with appropriate logging

4. **Caching** (Optional)
   - Cache schedule data to reduce network requests
   - Implement cache invalidation strategy

## Testing

Create tests in `tests/gameday_checker/test_checker.py`:
- Test date parsing
- Test game filtering
- Test with mock data
- Test error conditions

## Dependencies

- `requests` for HTTP requests
- `beautifulsoup4` for HTML parsing (if scraping)
- `datetime` for date handling

## Example Usage

```python
from datetime import date
from src.gameday_checker import GamedayChecker

checker = GamedayChecker(schedule_url="https://haverfordathletics.com/calendar")

# Get today's games
today_games = checker.get_games_for_today()
for game in today_games:
    print(f"{game.team.name} vs {game.opponent} at {game.time}")

# Check specific date
games = checker.get_games_for_date(date(2024, 3, 15))
if games:
    print(f"Found {len(games)} games on March 15")
```

## Integration Points

- **Used by**: Main orchestrator to check if notifications should be sent
- **Uses**: Configuration file for schedule URL
- **Output format**: List of Game objects that other modules can process
