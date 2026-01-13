# Auto-Recovery Guide - Handling Invalid Team IDs

## Yes, We Can Auto-Discover Teams When IDs Are Wrong! ✅

When the fetcher encounters an invalid team ID, it can automatically:
1. Detect that the ID is invalid (vs. season not started)
2. Discover all current Haverford team IDs from NCAA
3. Find the correct ID for the requested sport
4. Retry the fetch with the correct ID
5. Notify you to update your config

## Quick Start

### Option 1: Check All Team IDs
```bash
# Check if any team IDs need updating
python3 auto_update_team_ids.py

# Force check and show new IDs even if all valid
python3 auto_update_team_ids.py --force
```

### Option 2: Auto-Recovery in Your Code
```python
from auto_update_team_ids import fetch_with_auto_recovery

# Automatically recovers if ID is invalid
result = fetch_with_auto_recovery("mens_basketball", "999999")

if result and result.success:
    print(f"Got {len(result.data['players'])} players")
    print("Remember to update config with new team ID!")
```

## How Auto-Recovery Works

### Detection
```python
result = fetcher.fetch_team_stats(team_id, sport)

if not result.success and "Invalid team ID" in result.error:
    # This triggers auto-recovery
    ...
```

### Discovery
```python
# Get all current Haverford team IDs
discovery = fetcher.get_haverford_teams()

# Returns:
{
    "school_id": 276,
    "teams": [
        {"sport": "Men's Basketball", "team_id": "611523", ...},
        {"sport": "Women's Soccer", "team_id": "603609", ...},
        ...
    ]
}
```

### Mapping
```python
# Map config key to sport name
sport_names = {
    "mens_basketball": "Men's Basketball",
    "womens_soccer": "Women's Soccer",
    ...
}

# Find correct team
for team in teams:
    if team['sport'] == sport_names[sport_key]:
        new_team_id = team['team_id']
        # Retry with new ID
```

## Demo Scenarios

### Scenario 1: Valid ID ✅
```
Attempting with Team ID: 611523
✅ SUCCESS! Team ID 611523 is valid
   Fetched 19 players
```
**No recovery needed** - ID is correct

### Scenario 2: Invalid ID (Triggers Recovery) 🔄
```
Attempting with Team ID: 999999
✗ Invalid team ID: 999999

🔄 Attempting auto-recovery...
✓ Discovered 10 teams
✓ Found correct team ID: 611523

🔄 Retrying with correct ID...
✅ SUCCESS!
   Fetched 19 players

⚠️  ACTION REQUIRED:
   Update your config to use team ID: 611523
```
**Recovery successful** - Fetched data with correct ID

### Scenario 3: Old Year's ID ⚠️
```
Attempting with Team ID: 500000
✅ Team ID 500000 is valid
   (Season hasn't started yet)
```
**No recovery triggered** - Old IDs may still work but have no stats

To catch this case, use `--force` flag:
```bash
python3 auto_update_team_ids.py --force
```

## Integration Patterns

### Pattern 1: Fail Fast (Development)
```python
# Don't auto-recover - fail loudly so you fix config
result = fetcher.fetch_team_stats(team_id, sport)

if not result.success:
    if "Invalid team ID" in result.error:
        raise ValueError(f"Config error: Invalid team ID {team_id}")
```

### Pattern 2: Auto-Recover (Production)
```python
from auto_update_team_ids import fetch_with_auto_recovery

# Automatically try to recover, log warning
result = fetch_with_auto_recovery(sport_key, team_id)

if result and result.success:
    # Log: "Using recovered team ID, update config!"
    process_data(result.data)
```

### Pattern 3: Scheduled Check (Cron Job)
```bash
#!/bin/bash
# Run weekly to check for new season IDs

cd /path/to/StatsTracker
python3 auto_update_team_ids.py

if [ $? -eq 1 ]; then
    # Team IDs need updating
    echo "WARNING: Team IDs need updating!" | mail -s "StatsTracker Alert" admin@example.com
fi
```

### Pattern 4: Startup Validation
```python
# At application startup, validate all team IDs
from auto_update_team_ids import check_and_update_if_needed

def startup():
    print("Validating team IDs...")
    result = check_and_update_if_needed()

    if result['needs_update']:
        print(f"WARNING: {result['invalid_count']} team IDs are invalid!")
        print("Update config with new IDs:")
        for sport, team_id in result['new_team_ids'].items():
            print(f"  {sport}: {team_id}")

        # Optionally: auto-update config file here
    else:
        print("✓ All team IDs valid")
```

## Scripts Available

| Script | Purpose | Use Case |
|--------|---------|----------|
| `auto_update_team_ids.py` | Check all IDs, show updates needed | Run at start of season |
| `demo_auto_recovery.py` | Demonstrate auto-recovery | See how it works |
| `discover_haverford_teams.py` | Just discover team IDs | Manual ID lookup |

## When to Use Auto-Recovery

### ✅ Good Use Cases:
- Production data pipelines (recover and log)
- Scheduled batch jobs (fail gracefully, alert admin)
- User-facing apps (seamless experience)
- Testing/development (quick fixes)

### ⚠️ Use With Caution:
- Initial setup (fix config instead)
- Critical data validation (validate IDs explicitly)
- Performance-critical code (discovery takes 10-15 seconds)

### ❌ Don't Use When:
- You need guaranteed consistency (use validated config)
- Network is unreliable (discovery requires NCAA website access)
- Running offline (no internet connection)

## Best Practices

1. **Check Annually**: Run `auto_update_team_ids.py` every August/September
2. **Log Recovery**: Always log when auto-recovery is used
3. **Update Config**: Don't rely on auto-recovery indefinitely - update config!
4. **Monitor Alerts**: Set up alerts when invalid IDs are detected
5. **Test First**: Use `--force` flag to test discovery before season starts

## Performance Considerations

- **Discovery time**: 10-15 seconds (loads 1 page + validates structure)
- **Caching**: Discovery results could be cached for 24 hours
- **Rate limiting**: Add delays if checking frequently

## Error Handling

```python
try:
    result = fetch_with_auto_recovery(sport_key, team_id)

    if result is None:
        # Auto-recovery failed
        logger.error(f"Could not recover team ID for {sport_key}")
        # Fallback: notify admin, use cached data, etc.

    elif result.success:
        # Got data (possibly with recovered ID)
        process_data(result.data)

    else:
        # Valid ID but no stats (season not started)
        logger.info(f"{sport_key} season not started")

except Exception as e:
    logger.error(f"Unexpected error: {e}")
    # Handle network errors, parsing errors, etc.
```

## Real-World Example

**September 2026** - New academic year starts:

```bash
# Step 1: Check if IDs need updating
$ python3 auto_update_team_ids.py

Testing current team IDs...
  ✗ Mens Basketball ID 611523 - INVALID
  ✗ Womens Basketball ID 611724 - INVALID
  ...

⚠️  Invalid team IDs detected!

🔍 Discovering new team IDs...
✓ Discovered 10 teams

Update config with:
  mens_basketball: 625431  # ← UPDATED (was 611523)
  womens_basketball: 625632  # ← UPDATED (was 611724)
  ...

# Step 2: Update config file
$ nano config/config.example.yaml
# (paste new team IDs)

# Step 3: Verify
$ python3 auto_update_team_ids.py
✓ All team IDs are valid!
```

## Summary

**Auto-recovery provides**:
- ✅ Automatic detection of invalid IDs
- ✅ Self-healing data fetching
- ✅ Clear notifications to update config
- ✅ Seamless user experience

**You still need to**:
- ⚠️ Update config file with new IDs
- ⚠️ Monitor for invalid ID alerts
- ⚠️ Check annually at start of season

Auto-recovery is a safety net, not a replacement for proper configuration management!
