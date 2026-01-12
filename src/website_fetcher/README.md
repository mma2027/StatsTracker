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

## Implementation Tasks

### NCAA Fetcher
- [ ] Identify NCAA API endpoints or HTML structure
- [ ] Implement `fetch_player_stats()` with HTML parsing
- [ ] Implement `search_player()` functionality
- [ ] Handle different sports (basketball, soccer, etc.)
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
