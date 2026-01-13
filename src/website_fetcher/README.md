# Website Fetcher Module

## Purpose
Fetches sports statistics from various sources (NCAA, TFRR, etc.)

## Architecture

The module uses an abstract base class pattern to ensure consistency across different data sources.

### Base Class: `BaseFetcher`

All fetchers inherit from `BaseFetcher` and must implement:
- `fetch_player_stats(player_id: str, sport: str) -> FetchResult`
- `fetch_team_stats(team_id: str, sport: str) -> FetchResult`
- `search_player(name: str, sport: str) -> FetchResult`

### Implemented Fetchers

1. **NCAAFetcher** - Fetches from NCAA.org
2. **TFRRFetcher** - Fetches from TFRR (Track & Field Results Reporting)

### Adding New Fetchers

To add a new data source:

1. Create a new file `src/website_fetcher/your_source_fetcher.py`
2. Import and inherit from `BaseFetcher`
3. Implement the three required methods
4. Add to `__init__.py`

Example:
```python
from .base_fetcher import BaseFetcher, FetchResult

class CustomFetcher(BaseFetcher):
    def fetch_player_stats(self, player_id: str, sport: str) -> FetchResult:
        # Your implementation
        pass

    def fetch_team_stats(self, team_id: str, sport: str) -> FetchResult:
        # Your implementation
        pass

    def search_player(self, name: str, sport: str) -> FetchResult:
        # Your implementation
        pass
```

## Data Format

All fetchers return a `FetchResult` object:

```python
@dataclass
class FetchResult:
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: datetime = None
    source: str = ""
```

### Standard Data Structure

Player stats should follow this format:
```python
{
    "player_id": "12345",
    "name": "John Doe",
    "sport": "basketball",
    "season": "2023-24",
    "stats": {
        # Sport-specific stats
        "points": 450,
        "rebounds": 120,
        # etc.
    }
}
```

## NCAA Fetcher - Haverford College Implementation ✅

The NCAAFetcher has been implemented to fetch player statistics for Haverford College teams.

### Features
- ✅ Fetches season-to-date stats from `stats.ncaa.org/teams/{team_id}/season_to_date_stats`
- ✅ Uses Selenium WebDriver for JavaScript rendering
- ✅ Generic table parsing works across all sports
- ✅ Supports all 10 Haverford College teams

### Haverford College Team IDs (2025-26 Season)

| Sport | Team ID | Stats URL |
|-------|---------|-----------|
| Men's Basketball | 611523 | https://stats.ncaa.org/teams/611523/season_to_date_stats |
| Women's Basketball | 611724 | https://stats.ncaa.org/teams/611724/season_to_date_stats |
| Men's Soccer | 604522 | https://stats.ncaa.org/teams/604522/season_to_date_stats |
| Women's Soccer | 603609 | https://stats.ncaa.org/teams/603609/season_to_date_stats |
| Field Hockey | 603834 | https://stats.ncaa.org/teams/603834/season_to_date_stats |
| Women's Volleyball | 605677 | https://stats.ncaa.org/teams/605677/season_to_date_stats |
| Baseball | 615223 | https://stats.ncaa.org/teams/615223/season_to_date_stats |
| Men's Lacrosse | 612459 | https://stats.ncaa.org/teams/612459/season_to_date_stats |
| Women's Lacrosse | 613103 | https://stats.ncaa.org/teams/613103/season_to_date_stats |
| Softball | 614273 | https://stats.ncaa.org/teams/614273/season_to_date_stats |

**Note**: Team IDs change each academic year. Use the `get_haverford_teams()` method to automatically discover updated team IDs at the start of each season.

### Usage Examples

#### Fetching Team Stats

```python
from src.website_fetcher import NCAAFetcher

# Fetch Haverford Men's Basketball stats
fetcher = NCAAFetcher()
result = fetcher.fetch_team_stats("611523", "basketball")

if result.success:
    data = result.data
    print(f"Season: {data['season']}")
    print(f"Found {len(data['players'])} players")

    for player in data['players']:
        print(f"{player['name']}: {player['stats']}")
else:
    print(f"Error: {result.error}")
```

#### Auto-Discovering Team IDs (New Season)

At the start of each academic year, team IDs change. Use this method to automatically find all current Haverford team IDs:

```python
from src.website_fetcher import NCAAFetcher

# Discover all Haverford teams
fetcher = NCAAFetcher()
result = fetcher.get_haverford_teams()

if result.success:
    for team in result.data['teams']:
        print(f"{team['sport']}: {team['team_id']}")
        print(f"  Stats URL: {team['url']}/season_to_date_stats")
```

Or use the convenience script:
```bash
python3 discover_haverford_teams.py
```

See [example_ncaa_usage.py](example_ncaa_usage.py) and [discover_haverford_teams.py](../../discover_haverford_teams.py) for more examples.

### Data Format

The NCAAFetcher returns data in this format:

```python
{
    "team_id": "611523",
    "sport": "basketball",
    "season": "2025-26",
    "players": [
        {
            "name": "Player Name",
            "stats": {
                "GP": "13",     # Games played
                "PTS": "245",   # Points
                # ... all stat columns from NCAA page
            }
        }
    ],
    "stat_categories": ["GP", "GS", "MIN", "PTS", ...]
}
```

The parser dynamically extracts whatever stat columns are present for that sport, so it works across all sports without modification.

### Implementation Status

- ✅ `fetch_team_stats()` - Fully implemented with Selenium
- ⏸️ `fetch_player_stats()` - Deferred (not needed for current use case)
- ⏸️ `search_player()` - Deferred (not needed for current use case)

## Implementation Tasks

### NCAA Fetcher
- [x] Identify NCAA API endpoints or HTML structure
- [x] Implement `fetch_team_stats()` with Selenium and HTML parsing
- [ ] Implement `fetch_player_stats()` with HTML parsing (deferred)
- [ ] Implement `search_player()` functionality (deferred)
- [x] Handle different sports (generic parser works for all)
- [ ] Add error handling for rate limits

### TFRR Fetcher
- [ ] Study TFRR website structure
- [ ] Parse athlete profile pages
- [ ] Extract PRs (personal records) for track events
- [ ] Handle cross country results
- [ ] Implement event-specific queries

### General Tasks
- [ ] Add caching mechanism to reduce requests
- [ ] Implement retry logic with exponential backoff
- [ ] Add rate limiting to respect website policies
- [ ] Create mock responses for testing
- [ ] Add logging for debugging

## Testing

Create tests in `tests/website_fetcher/`:
- `test_base_fetcher.py` - Test base functionality
- `test_ncaa_fetcher.py` - Test NCAA-specific logic
- `test_tfrr_fetcher.py` - Test TFRR-specific logic

Use mock responses to avoid hitting actual websites during tests.

## Dependencies

- `requests` - HTTP requests
- `beautifulsoup4` - HTML parsing
- `lxml` - Fast HTML parsing
- `selenium` (optional) - For JavaScript-heavy sites

## Example Usage

```python
from src.website_fetcher import NCAAFetcher, TFRRFetcher

# NCAA example
ncaa = NCAAFetcher()
result = ncaa.fetch_player_stats(player_id="12345", sport="basketball")
if result.success:
    print(f"Points: {result.data['stats']['points']}")
else:
    print(f"Error: {result.error}")

# TFRR example
tfrr = TFRRFetcher()
result = tfrr.fetch_player_stats(player_id="67890", sport="track")
if result.success:
    print(f"100m PR: {result.data['stats']['100m']}")
```

## Integration Points

- **Used by**: Player database module (to fetch and store stats)
- **Uses**: Configuration file for URLs and timeouts
- **Output**: FetchResult objects consumed by database module
