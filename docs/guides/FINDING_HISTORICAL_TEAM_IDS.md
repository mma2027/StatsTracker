# Finding Historical NCAA Team IDs

## Overview

NCAA team IDs change every academic year. To track career stats, you need the team ID for each historical season. This guide shows you how to find them.

## Method 1: Manual Collection (Most Reliable)

### Steps:

1. **Go to NCAA Stats Website:**
   - Visit: https://stats.ncaa.org/

2. **Search for Haverford:**
   - Use the school search
   - Or go directly to: https://stats.ncaa.org/team/276

3. **Find Historical Years:**
   - Look for academic year dropdown/selector on the page
   - Try URLs like:
     - `https://stats.ncaa.org/team/276?academic_year=2024`
     - `https://stats.ncaa.org/team/276?academic_year=2023`
   - The `academic_year` parameter may vary

4. **For Each Year:**
   - Click on a team (e.g., "Men's Basketball")
   - Look at the URL: `https://stats.ncaa.org/teams/XXXXXX`
   - The number `XXXXXX` is the team ID
   - Record it in your JSON file

5. **Example:**
   ```
   2024-25 Men's Basketball URL: https://stats.ncaa.org/teams/611523
   Team ID: 611523
   ```

### Recording IDs:

Edit `data/historical_team_ids.json`:

```json
{
  "mens_basketball": {
    "2025-26": 611523,  // Current (found via script)
    "2024-25": 599123,  // Found manually
    "2023-24": 587456,  // Found manually
    "2022-23": 575789,  // Found manually
    "2021-22": 563234,  // Found manually
    "2020-21": 551678   // Found manually
  }
}
```

## Method 2: Use Our Scraper (Partial)

```bash
# This will get current year IDs automatically
python3 scripts/scrape_historical_team_ids.py

# Output saved to: data/historical_team_ids.json
```

**Limitation**: NCAA doesn't expose historical years via direct scraping. You'll still need to manually add past seasons.

## Method 3: Check Your Own Database

If you've been running the fetcher regularly:

```python
import sqlite3

conn = sqlite3.connect('data/stats.db')
cursor = conn.cursor()

# Find all unique team IDs by sport
cursor.execute("""
    SELECT DISTINCT sport, team_id, season
    FROM stats
    ORDER BY sport, season DESC
""")

for row in cursor.fetchall():
    print(f"{row[0]} - {row[2]}: Team ID {row[1]}")
```

## Method 4: Check Git History

If you've committed team ID changes over time:

```bash
# Search for historical HAVERFORD_TEAMS in git
git log --all -p src/website_fetcher/ncaa_fetcher.py | grep -A 15 "HAVERFORD_TEAMS"

# Check specific old commits
git show <commit-hash>:src/website_fetcher/ncaa_fetcher.py | grep HAVERFORD_TEAMS
```

## Method 5: Contact Haverford Athletics

Haverford's sports information office may have:
- Historical NCAA team ID records
- Links to archived statistics pages
- Previous season data exports

## Quick Reference: Team ID Patterns

NCAA team IDs generally follow these patterns:
- **Sequential**: IDs increment each year (but not predictably)
- **Sport-specific**: Different sports have different ID ranges
- **School-specific**: Each school's teams have IDs in certain ranges

**Example for Haverford Men's Basketball:**
- 2025-26: 611523
- 2024-25: ~599xxx (estimated range)
- 2023-24: ~587xxx (estimated range)

## Automated Recording System

### For Future Years

Create a script that runs at the start of each season:

```bash
#!/bin/bash
# save_current_team_ids.sh

# 1. Discover current team IDs
python3 scripts/auto_update_team_ids.py

# 2. Append to historical log
DATE=$(date +%Y-%m-%d)
echo "[$DATE] Current team IDs:" >> logs/team_id_history.log
grep "HAVERFORD_TEAMS" src/website_fetcher/ncaa_fetcher.py >> logs/team_id_history.log

# 3. Update historical JSON
python3 scripts/scrape_historical_team_ids.py
```

Run this at the start of each academic year (late August/early September).

## Complete Example

### Step-by-Step Manual Collection

**Goal**: Get Men's Basketball team IDs for 2020-2025

1. **Open Browser:**
   - Go to https://stats.ncaa.org/team/276

2. **Try Different Years:**
   - For 2024-25, try: `https://stats.ncaa.org/team/276?academic_year=2024`
   - Look for "Men's Basketball" link
   - Click it → URL shows team ID

3. **Record Each ID:**
   ```
   2024-25: Found team ID 599123 at /teams/599123
   2023-24: Found team ID 587456 at /teams/587456
   2022-23: Found team ID 575789 at /teams/575789
   2021-22: Found team ID 563234 at /teams/563234
   2020-21: Found team ID 551678 at /teams/551678
   ```

4. **Update JSON:**
   ```bash
   vim data/historical_team_ids.json
   ```

   Add the IDs you found:
   ```json
   {
     "mens_basketball": {
       "2025-26": 611523,
       "2024-25": 599123,
       "2023-24": 587456,
       "2022-23": 575789,
       "2021-22": 563234,
       "2020-21": 551678
     },
     "womens_basketball": {
       ...
     }
   }
   ```

5. **Test It:**
   ```bash
   python3 scripts/fetch_ncaa_seasonal_and_career.py
   ```

   Should now show:
   ```
   [2/2] Fetching career stats (last 6 years)...
     ✓ Found historical team IDs for Mens Basketball
       Fetching 2024-25... ✓ (12 active players)
       Fetching 2023-24... ✓ (8 active players)
       ...
   ```

## Troubleshooting

### "Team ID doesn't work"
- **Cause**: Wrong academic year or team ID
- **Solution**: Verify by visiting the URL directly in browser

### "Can't find year selector"
- **Cause**: NCAA redesigned their website
- **Solution**: Try different URL patterns or contact NCAA support

### "No active players found"
- **Cause**: Players from that year already graduated
- **Solution**: This is expected - only current roster gets career stats

## Best Practices

1. **Record IDs Annually**: At the start of each season, save current team IDs
2. **Verify URLs**: Always test team ID URLs in a browser first
3. **Back Up Data**: Keep a backup of historical_team_ids.json
4. **Document Changes**: Note when/how you found each ID
5. **Version Control**: Commit historical_team_ids.json to git

## Future Automation Ideas

### Ideal Workflow:
1. NCAA provides an API with historical team IDs (currently doesn't exist)
2. Auto-discovery script that crawls historical pages
3. Community-maintained database of team IDs
4. Integration with Haverford's athletics database

### What We Can Do Now:
- Manual collection (most reliable)
- Save current IDs each year
- Build up historical data over time
- Share findings with other Haverford developers

## Resources

- **NCAA Stats Site**: https://stats.ncaa.org/
- **Haverford School Page**: https://stats.ncaa.org/team/276
- **Auto Update Script**: `scripts/auto_update_team_ids.py`
- **Scraper Script**: `scripts/scrape_historical_team_ids.py`
- **Historical IDs Template**: `data/historical_team_ids.json.example`

## Need Help?

If you successfully find historical team IDs, please:
1. Update `data/historical_team_ids.json`
2. Commit and push to the repo
3. Share your method so others can replicate

This helps future developers and makes career stat tracking more complete!
