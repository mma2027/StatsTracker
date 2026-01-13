# Seasonal and Career Stats Guide

## Overview

The NCAA fetcher now supports fetching **both seasonal and career statistics**:
- **Seasonal Stats**: Current season only
- **Career Stats**: Aggregated totals across multiple years (for active roster only)

## How It Works

1. **Fetch current season** → Get seasonal stats + active roster
2. **Fetch historical seasons** → Get stats from previous years
3. **Filter to active roster** → Only aggregate for current players
4. **Aggregate career totals** → Sum stats across all seasons
5. **Export to CSV** → Two files: seasonal and career

## Quick Start

### Basic Usage

```bash
# Fetch seasonal + career for all teams
python3 scripts/fetch_ncaa_seasonal_and_career.py

# Output:
# csv_exports/haverford_mens_basketball_seasonal_2025_26_20260113.csv
# csv_exports/haverford_mens_basketball_career_20260113.csv
```

### With Options

```bash
# Custom output directory
python3 scripts/fetch_ncaa_seasonal_and_career.py --output-dir my_stats

# Specify years to look back
python3 scripts/fetch_ncaa_seasonal_and_career.py --years-back 4
```

## CSV Output Format

### Seasonal CSV
```csv
Player Name,Season,GP,GS,MP,FGM,FGA,FG%,PTS,...
John Doe,2025-26,13,10,250,45,100,45.0,120,...
Jane Smith,2025-26,13,13,300,60,120,50.0,150,...
```

### Career CSV
```csv
Player Name,GP,GS,MP,FGM,FGA,FG%,PTS,...
John Doe,45,32,850,150,320,46.9,410,...
Jane Smith,60,55,1200,220,440,50.0,600,...
```

## Historical Team IDs

### Why Needed?

NCAA team IDs change every academic year. To get career stats spanning multiple years, you need the team ID for each historical season.

### Setup

1. **Copy the example file:**
   ```bash
   cp data/historical_team_ids.json.example data/historical_team_ids.json
   ```

2. **Fill in historical IDs:**
   ```json
   {
     "mens_basketball": {
       "2025-26": 611523,  // Current season (auto-detected)
       "2024-25": 599123,  // Fill in manually
       "2023-24": 587456,  // Fill in manually
       "2022-23": null,    // Leave null if unknown
       "2021-22": null,
       "2020-21": null
     }
   }
   ```

3. **Update annually:**
   - At the start of each season, run `scripts/auto_update_team_ids.py`
   - This discovers current team IDs
   - Manually copy them to historical_team_ids.json

### Finding Historical Team IDs

**Option 1: Manual Discovery**
1. Go to https://stats.ncaa.org/team/276 (Haverford)
2. Look for previous seasons in the dropdown/archives
3. Click on a team → check URL for team ID
4. Record in historical_team_ids.json

**Option 2: Saved Records**
- If you've been running the fetcher regularly, check your git history
- `git log --all -- src/website_fetcher/ncaa_fetcher.py`
- Look for HAVERFORD_TEAMS constants from previous commits

**Option 3: Database Records**
- If you've been storing data in the database, query for team_id field
- Historical data may have old team IDs recorded

## Career Stats Aggregation

### Numeric Stats (Summed)
- Games Played (GP)
- Points (PTS)
- Rebounds (Tot Reb)
- Assists (AST)
- Field Goals Made/Attempted (FGM, FGA)
- etc.

### Percentage Stats (Not Summed)
- Field Goal % (FG%)
- Free Throw % (FT%)
- 3-Point % (3FG%)

**Note**: Percentages use the most recent season's value, not an average. To calculate career averages, use: `Career FGM / Career FGA * 100`

### Active Roster Filtering

Only players on the **current season roster** have career stats calculated. This ensures:
- No stats for graduated/transferred players
- Only relevant for current team
- Cleaner career CSV with active players only

## Workflow Example

### First Time Setup

```bash
# 1. Discover current team IDs
python3 scripts/discover_haverford_teams.py

# 2. Create historical IDs file
cp data/historical_team_ids.json.example data/historical_team_ids.json

# 3. Fetch with current season only (no historical data yet)
python3 scripts/fetch_ncaa_seasonal_and_career.py
# → Seasonal CSV: ✓ Current season
# → Career CSV: ⚠️ Same as seasonal (no history)
```

### With Historical Data

```bash
# 1. Fill in historical team IDs in data/historical_team_ids.json
vim data/historical_team_ids.json

# 2. Fetch with career spanning 6 years
python3 scripts/fetch_ncaa_seasonal_and_career.py --years-back 6
# → Seasonal CSV: ✓ Current season
# → Career CSV: ✓ Aggregated across 6 seasons for active roster
```

### Annual Maintenance

At the start of each academic year:

```bash
# 1. Discover new team IDs
python3 scripts/auto_update_team_ids.py

# 2. Update historical_team_ids.json
# Copy current year IDs → add as new season
# Shift older seasons back

# 3. Fetch new data
python3 scripts/fetch_ncaa_seasonal_and_career.py
```

## Use Cases

### 1. Weekly Updates
```bash
# Run weekly during season
python3 scripts/fetch_ncaa_seasonal_and_career.py

# Seasonal CSV: Tracks weekly progress
# Career CSV: Shows cumulative career totals
```

### 2. Milestone Tracking
```python
# Read career CSV
import pandas as pd
career_df = pd.read_csv('csv_exports/haverford_mens_basketball_career_20260113.csv')

# Find players close to 1000 career points
close_to_1000 = career_df[career_df['PTS'] >= 900]
print(close_to_1000[['Player Name', 'PTS']])
```

### 3. Season vs Career Comparison
```python
import pandas as pd

seasonal = pd.read_csv('csv_exports/haverford_mens_basketball_seasonal_2025_26_20260113.csv')
career = pd.read_csv('csv_exports/haverford_mens_basketball_career_20260113.csv')

# Merge on player name
comparison = seasonal.merge(career, on='Player Name', suffixes=('_season', '_career'))

# Calculate percentage of career points scored this season
comparison['pct_this_season'] = (comparison['PTS_season'] / comparison['PTS_career']) * 100
```

## Limitations

### 1. Historical Data Required
- Career stats only work if you have historical team IDs
- Without history, career CSV = seasonal CSV

### 2. Team ID Changes
- NCAA changes team IDs every academic year
- Must manually track and update historical IDs

### 3. Active Roster Only
- Career stats only for current roster
- Graduated/transferred players not included

### 4. Percentage Stats
- Percentages use most recent value, not weighted average
- Must manually calculate career percentages if needed

## Troubleshooting

### "No historical team IDs found"

**Solution**: Create `data/historical_team_ids.json`
```bash
cp data/historical_team_ids.json.example data/historical_team_ids.json
# Edit file to add historical IDs
```

### "Career CSV same as seasonal"

**Cause**: No historical data available

**Solution**: Add historical team IDs to JSON file

### "Fetching historical season failed"

**Possible causes**:
- Invalid team ID (season may not exist)
- Network timeout
- Team ID for wrong school

**Solution**: Verify team ID is correct, check NCAA stats page manually

## Advanced Usage

### Custom Aggregation

You can modify `aggregate_career_stats()` in the script to:
- Calculate weighted averages for percentages
- Add custom calculated stats (e.g., PER, TS%)
- Include season-by-season breakdowns

### Integration with Database

```python
# After fetching, update database with both seasonal and career
from src.player_database.database import PlayerDatabase

db = PlayerDatabase()

# Import seasonal stats
db.import_from_csv('csv_exports/haverford_mens_basketball_seasonal_2025_26.csv', season='2025-26')

# Import career stats
db.import_from_csv('csv_exports/haverford_mens_basketball_career.csv', season='career')
```

## FAQ

**Q: Do I need historical IDs to use this?**
A: No, but without them you'll only get current season data in both CSVs.

**Q: How far back can I go?**
A: As far as you have team IDs. NCAA stats.ncaa.org typically has 10+ years of data.

**Q: Can I get stats for players who transferred out?**
A: Not with this script - it only tracks active roster. You'd need to modify the filtering logic.

**Q: Why are percentages not averaged?**
A: Simple aggregation would require weighted averaging. We use the most recent value. Calculate yourself if needed: `career_fg_pct = career_fgm / career_fga * 100`

## See Also

- [CSV Export Guide](CSV_EXPORT_GUIDE.md) - General CSV export documentation
- [Database Integration Guide](DATABASE_INTEGRATION_GUIDE.md) - Importing CSV to database
- [Auto Recovery Guide](AUTO_RECOVERY_GUIDE.md) - Handling invalid team IDs
