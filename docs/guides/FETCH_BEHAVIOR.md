# NCAA Fetcher Return Behavior

This document describes what `NCAAFetcher.fetch_team_stats()` returns in different scenarios.

## Scenario 1: Active Season with Stats ✅

**Example**: Men's Basketball (January 2026 - mid-season)

### Return Value
```python
FetchResult(
    success=True,
    data={
        "team_id": "611523",
        "sport": "basketball",
        "season": "Unknown",  # Could be improved, but not critical
        "players": [
            {
                "name": "Isaac Varghese",
                "stats": {
                    "#": "0",
                    "Yr": "SR",
                    "Pos": "G",
                    "Ht": "5-9",
                    "GP": "13",
                    "GS": "13",
                    "MIN": "395",
                    "PTS": "193",
                    "FG": "68",
                    "FGA": "154",
                    # ... 33 total stat categories
                }
            },
            # ... 19 total players
        ],
        "stat_categories": ["#", "Yr", "Pos", "Ht", "GP", "GS", "MIN", "PTS", ...]
    },
    error=None,
    source="NCAAFetcher",
    timestamp=datetime(2026, 1, 12, ...)
)
```

### Key Points
- ✅ `success=True`
- ✅ `data` contains full team stats with all players
- ✅ `stat_categories` lists all column headers dynamically parsed
- ✅ Number of stats varies by sport (14-33 categories)
- ✅ Each player has all their stats in a dictionary

## Scenario 2: Season Not Started (No Stats Yet) ❌

**Example**: Baseball (January 2026 - season starts in February/March)

### Return Value
```python
FetchResult(
    success=False,
    data=None,
    error="No player statistics found on page",
    source="NCAAFetcher",
    timestamp=datetime(2026, 1, 12, ...)
)
```

### Key Points
- ❌ `success=False` - Caller knows fetch didn't work
- ⚠️ `data=None` - No partial data returned
- ✅ `error` message explains why (no stats table on page)
- ✅ Not a crash - clean error handling
- ✅ Page exists but has no stats table yet

### Why This Happens
The NCAA page exists at the URL, but it doesn't contain a statistics table because:
1. The season hasn't started yet
2. No games have been played
3. The stats table will appear once the first game is played

### How to Handle in Code
```python
result = fetcher.fetch_team_stats("615223", "baseball")

if result.success:
    # Process stats
    for player in result.data['players']:
        print(f"{player['name']}: {player['stats']}")
else:
    # Handle gracefully
    print(f"No stats available: {result.error}")
    # Could log, skip team, or try again later
```

## Scenario 3: Invalid Team ID (Hypothetical) ❌

**Example**: Made-up team ID "999999"

### Expected Return Value
```python
FetchResult(
    success=False,
    data=None,
    error="<exception message from Selenium or parsing>",
    source="NCAAFetcher",
    timestamp=datetime(...)
)
```

### Key Points
- ❌ `success=False`
- ⚠️ `data=None`
- ✅ Exception caught and returned in `error` field
- ✅ Clean error handling via `handle_error()` method

## Scenario 4: Network Error (Hypothetical) ❌

**Example**: No internet connection or NCAA website down

### Expected Return Value
```python
FetchResult(
    success=False,
    data=None,
    error="<network exception message>",
    source="NCAAFetcher",
    timestamp=datetime(...)
)
```

## Summary Table

| Scenario | success | data | error | Notes |
|----------|---------|------|-------|-------|
| Active season with stats | `True` | Full stats dict | `None` | Ready to use |
| Season not started | `False` | `None` | "No player statistics found on page" | Page exists but empty |
| Invalid team ID | `False` | `None` | Exception message | 404 or parsing error |
| Network error | `False` | `None` | Network exception | Connection issue |

## Best Practices for Callers

### Always Check Success Flag
```python
result = fetcher.fetch_team_stats(team_id, sport)

if not result.success:
    logger.warning(f"Failed to fetch {sport}: {result.error}")
    return

# Now safe to use result.data
process_stats(result.data)
```

### Handle Different Error Types
```python
if not result.success:
    if "No player statistics found" in result.error:
        # Season hasn't started - this is expected
        logger.info(f"{sport} season not started yet")
    else:
        # Unexpected error - might need attention
        logger.error(f"Error fetching {sport}: {result.error}")
```

### Batch Processing with Error Recovery
```python
for sport_key, team_id in HAVERFORD_TEAMS.items():
    result = fetcher.fetch_team_stats(str(team_id), sport_key)

    if result.success:
        # Store in database
        save_to_db(result.data)
        successful_teams.append(sport_key)
    else:
        # Log and continue with other teams
        logger.warning(f"Skipping {sport_key}: {result.error}")
        failed_teams.append((sport_key, result.error))

# Report summary
print(f"Successfully fetched {len(successful_teams)} teams")
print(f"Failed: {len(failed_teams)} teams")
```

## Design Benefits

The consistent `FetchResult` return type provides:

1. **Explicit Success/Failure**: No need to check for `None` or catch exceptions
2. **Error Context**: `error` field explains what went wrong
3. **Timestamp**: Know when data was fetched
4. **Source Tracking**: `source` field identifies which fetcher was used
5. **Type Safety**: Same return structure for all scenarios

This makes the fetcher robust and easy to integrate with other modules like the player database.
