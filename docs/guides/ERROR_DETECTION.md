# Error Detection - Invalid IDs vs Season Not Started

## Can We Tell the Difference?

**YES!** The fetcher now distinguishes between invalid team IDs and valid teams whose season hasn't started yet.

## Error Types

### 1. ✅ Valid Team, Active Season
**Example**: Men's Basketball (currently mid-season)

```python
result = fetcher.fetch_team_stats("611523", "basketball")

# Returns:
FetchResult(
    success=True,
    data={...},  # Full stats
    error=None
)
```

### 2. ⚠️ Valid Team, No Stats Yet (Season Not Started)
**Example**: Baseball in January (season starts Feb/Mar)

```python
result = fetcher.fetch_team_stats("615223", "baseball")

# Returns:
FetchResult(
    success=False,
    data=None,
    error="No statistics available yet (season may not have started)"
)
```

**Why this happens**: The team page exists and is valid, but there's no stats table because no games have been played yet.

### 3. ❌ Invalid Team ID
**Example**: Made-up team ID "999999"

```python
result = fetcher.fetch_team_stats("999999", "unknown")

# Returns:
FetchResult(
    success=False,
    data=None,
    error="Invalid team ID - page does not contain team information"
)
```

**Why this happens**: The page doesn't have team context (no sport names, no breadcrumbs, no team headers).

## Detection Logic

The fetcher checks for:

1. **Error messages on page**: "page not found", "404", "no team found"
2. **Team context indicators**: Sport names, "season to date", navigation breadcrumbs
3. **Table presence**: Has any tables at all?

### Decision Tree:
```
Page loaded successfully?
├─ NO → Exception (network/timeout error)
└─ YES → Check page content
    ├─ Has "page not found" or "404"?
    │   └─ YES → "Invalid team ID - page not found"
    ├─ Has team context (sport name, breadcrumbs)?
    │   ├─ YES → Valid team page
    │   │   ├─ Has stats table?
    │   │   │   ├─ YES → Parse and return data
    │   │   │   └─ NO → "No statistics available yet (season may not have started)"
    │   └─ NO → "Invalid team ID - page does not contain team information"
```

## How to Handle in Code

### Check for Invalid IDs
```python
result = fetcher.fetch_team_stats(team_id, sport)

if not result.success:
    if "Invalid team ID" in result.error:
        # This is a problem - wrong ID
        logger.error(f"Bad team ID: {team_id}")
        notify_admin(f"Invalid team ID in config: {team_id}")
    elif "No statistics available yet" in result.error:
        # This is expected for off-season sports
        logger.info(f"{sport} season hasn't started yet")
    else:
        # Other error (network, parsing, etc.)
        logger.warning(f"Unexpected error: {result.error}")
```

### Smart Retry Logic
```python
def fetch_with_validation(team_id, sport):
    result = fetcher.fetch_team_stats(team_id, sport)

    if not result.success:
        if "Invalid team ID" in result.error:
            # Don't retry - ID is wrong
            raise ValueError(f"Invalid team ID: {team_id}")
        elif "No statistics available yet" in result.error:
            # Don't retry now - season hasn't started
            return None  # Try again later in the season
        else:
            # Retry on other errors (network issues, etc.)
            return retry_fetch(team_id, sport)

    return result.data
```

### Batch Processing with Smart Filtering
```python
def fetch_all_active_teams():
    """Fetch stats only for teams with active seasons."""
    results = {}

    for sport_key, team_id in HAVERFORD_TEAMS.items():
        result = fetcher.fetch_team_stats(str(team_id), sport_key)

        if result.success:
            results[sport_key] = result.data
        elif "Invalid team ID" in result.error:
            # Critical error - log and alert
            logger.error(f"Config error: {sport_key} has invalid team ID {team_id}")
        elif "No statistics available yet" in result.error:
            # Expected - skip silently
            logger.debug(f"Skipping {sport_key} - season not started")
        else:
            # Unexpected error
            logger.warning(f"Error fetching {sport_key}: {result.error}")

    return results
```

## Test Results

Test run on January 12, 2026:

| Scenario | Team ID | Error Message | Interpretation |
|----------|---------|---------------|----------------|
| Baseball (spring sport) | 615223 | "No statistics available yet (season may not have started)" | ✅ Valid team, wait for season |
| Made-up ID | 999999 | "Invalid team ID - page does not contain team information" | ❌ Fix the team ID |
| Old team ID | 500000 | "No statistics available yet (season may not have started)" | ⚠️ Update team ID for new year |
| Basketball (active) | 611523 | None (success=True) | ✅ Working correctly |

## Edge Case: Old Team IDs

**Note**: Old team IDs from previous years (e.g., 500000) may return "No statistics available yet" instead of "Invalid team ID" because the page still exists but is empty.

**Solution**: Use the `discover_haverford_teams()` method at the start of each season to get current IDs.

## Benefits

1. **Clear error messages** - Caller knows exactly what went wrong
2. **Smart retry logic** - Don't waste time retrying invalid IDs
3. **Better logging** - Distinguish between config errors and expected behavior
4. **User-friendly** - Can show different messages to users ("Coming soon!" vs "Error")

## Summary

The fetcher now provides three distinct outcomes:

1. ✅ **Success** - Stats fetched, data available
2. ⚠️ **Season not started** - Valid team, try again later
3. ❌ **Invalid ID** - Fix the configuration

This makes the fetcher much more robust and easier to integrate with other systems!
