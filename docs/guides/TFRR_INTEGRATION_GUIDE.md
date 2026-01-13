# TFRR Fetcher Integration Guide

**Last Updated**: January 13, 2026

## Overview

The TFRR (Track & Field Results Reporting) fetcher allows you to scrape track & field and cross country statistics from tfrrs.org for Haverford College teams.

## Features

✅ **Implemented**:
- Selenium-based web scraping (handles JavaScript rendering)
- Fetch team rosters for all Haverford track teams
- Auto-detects and extracts athlete names and year
- CSV export functionality
- Headless browser support
- Error detection and validation

⚠️ **Current Limitations**:
- Event performance data (actual times/marks) not yet fully parsed
- Season detection needs improvement
- Individual athlete pages not fully implemented
- TFRR roster page structure is different from expected format

## Haverford Teams

The fetcher supports all Haverford track & field and cross country teams:

```python
HAVERFORD_TEAMS = {
    "mens_track": "PA_college_m_Haverford",
    "womens_track": "PA_college_f_Haverford",
    "mens_cross_country": "PA_college_m_Haverford",
    "womens_cross_country": "PA_college_f_Haverford",
}
```

Note: Track and cross country use the same team code but different sport parameters.

## Usage

### Fetch Team Stats

```python
from src.website_fetcher.tfrr_fetcher import TFRRFetcher

fetcher = TFRRFetcher()

# Fetch men's track team
result = fetcher.fetch_team_stats("PA_college_m_Haverford", "track")

if result.success:
    data = result.data
    print(f"Team: {data['team_name']}")
    print(f"Athletes: {len(data['athletes'])}")

    # Access athlete data
    for athlete in data['athletes']:
        print(f"{athlete['name']} - {athlete['year']}")
        # Event results in athlete['events']
```

### Export to CSV

Export all Haverford TFRR teams to CSV:

```bash
# Export all teams
python3 fetch_tfrr_to_csv.py

# Export specific team
python3 fetch_tfrr_to_csv.py --sport mens_track

# Custom output directory
python3 fetch_tfrr_to_csv.py --output-dir my_stats
```

### Manual Testing

Run the manual test script to verify functionality:

```bash
python3 test_tfrr_manual.py
```

## Data Format

### FetchResult Data Structure

```python
{
    "team_code": "PA_college_m_Haverford",
    "team_name": "Haverford College",
    "sport": "track",
    "season": "Indoor 2026",
    "athletes": [
        {
            "name": "John Doe",
            "year": "JR-3",
            "events": {
                "100m": "11.25",
                "200m": "23.45",
                ...
            }
        }
    ],
    "event_categories": ["100m", "200m", "400m", ...]
}
```

### CSV Format

The CSV export creates files with the following structure:

```csv
Athlete Name,Year,Event1,Event2,Event3,...
John Doe,JR-3,11.25,23.45,...
Jane Smith,SO-2,11.89,24.12,...
```

## Current Status

### What Works ✅

1. **Team Roster Fetching**: Successfully fetches athlete names and years
2. **CSV Export**: Exports roster data to CSV files
3. **Multi-team Support**: Can fetch multiple teams (men's/women's track and XC)
4. **Error Handling**: Detects invalid pages and missing data
5. **Selenium Integration**: Uses headless Chrome for JavaScript rendering

### What Needs Improvement ⚠️

1. **Event Data Parsing**: The current parser extracts table headers but not actual performance times/marks
   - TFRR's roster page structure differs from the expected format
   - May need to parse individual athlete profile pages for detailed stats
   - Or find a different table/section on the team page with PR data

2. **Season Detection**: Cannot reliably extract season from page
   - Returns "Unknown" for most pages
   - Need to improve regex patterns or look in different page locations

3. **Individual Athlete Pages**: `fetch_player_stats()` implemented but not fully tested
   - Should parse athlete profile pages for complete PR history
   - Need to verify URL format and parsing logic

## Comparison to NCAA Fetcher

| Feature | NCAA Fetcher | TFRR Fetcher |
|---------|-------------|--------------|
| Team roster | ✅ Full stats | ✅ Names/years only |
| Event/stat data | ✅ Complete | ⚠️ Limited |
| CSV export | ✅ Yes | ✅ Yes |
| Season detection | ✅ Reliable | ⚠️ Needs work |
| Database integration | ✅ Yes | ⚠️ Not yet |
| Auto-recovery | ✅ Yes | ❌ Not needed |

## Files

### Core Implementation
- `src/website_fetcher/tfrr_fetcher.py` - Main TFRR fetcher class
- `fetch_tfrr_to_csv.py` - CSV export script for all teams
- `test_tfrr_manual.py` - Manual testing script

### Configuration
- `config/config.example.yaml` - Contains TFRR base URL and settings

## Next Steps for Full Implementation

To complete the TFRR fetcher, the following improvements are needed:

1. **Parse Event Data**:
   - Investigate TFRR page structure more thoroughly
   - Find where PR (Personal Record) data is stored
   - May need to scrape individual athlete pages instead of team roster
   - Or look for a different table/section on team page

2. **Improve Season Detection**:
   - Study TFRR page HTML to find season indicators
   - Update regex patterns in `_get_season_from_page()`
   - Handle Indoor/Outdoor track vs. Cross Country seasons

3. **Database Integration**:
   - Create `update_database_from_tfrr.py` (similar to NCAA version)
   - Map TFRR events to database schema
   - Handle different event formats (times, distances, heights)

4. **Testing**:
   - Add unit tests with mocked responses
   - Test with actual TFRR pages
   - Verify CSV output format

5. **Individual Athlete Stats**:
   - Test `fetch_player_stats()` with real athlete IDs
   - Parse complete PR history from athlete profiles
   - Extract meet-by-meet results

## Known Issues

1. **Limited Event Data**: Currently only extracts roster information, not actual performance data
2. **Season Unknown**: Cannot detect current season from page
3. **Table Parsing**: TFRR table structure different from expected format
4. **No Database Integration**: Not yet connected to Player Database module

## Testing Results

### Test Run (January 13, 2026)

```
✓ Men's Track: 48 athletes fetched
✓ Women's Track: 41 athletes fetched
✓ Men's Cross Country: 48 athletes fetched
✓ Women's Cross Country: 41 athletes fetched
✓ CSV export: Working
⚠️ Event data: Limited (only NAME/YEAR columns)
⚠️ Season detection: Returns "Unknown"
```

## Troubleshooting

### "No athlete data available"
- The season may not have started yet
- Check if the team code is correct
- Verify TFRR website is accessible

### "Invalid page" error
- Team code may be incorrect
- TFRR website structure may have changed
- Check network connectivity

### Missing event data in CSV
- Known limitation - event parsing needs improvement
- Data structure on TFRR differs from expected format
- Consider scraping individual athlete pages instead

## Resources

- TFRR Website: https://www.tfrrs.org
- Haverford Men's Team: https://www.tfrrs.org/teams/PA_college_m_Haverford.html
- Haverford Women's Team: https://www.tfrrs.org/teams/PA_college_f_Haverford.html

## Contributing

To improve the TFRR fetcher:

1. Study the actual TFRR page HTML structure
2. Identify where PR data is located
3. Update `_parse_team_roster()` or `_parse_athlete_data()` methods
4. Test with real data
5. Update this documentation

---

**Status**: ⚠️ Partially Complete (60% - Core functionality works, event data parsing needs improvement)
