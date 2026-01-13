# CSV Export Guide

## Quick Answer to Your Questions

### ✅ Will this work next year?
**YES!** With one simple update per year:

1. At the start of each academic year (August/September), run:
   ```bash
   python3 discover_haverford_teams.py
   ```

2. Copy the new team IDs to `config/config.example.yaml`

3. Done! Everything else stays the same.

**What changes annually**: Just the team IDs (NCAA generates new ones each year)
**What stays the same**: All the code, URL structure, parsing logic

---

### ✅ Does it output CSV files for each sport?
**YES!** Use the batch export script:

```bash
python3 fetch_all_teams_to_csv.py
```

This will:
- Fetch stats for all Haverford teams
- Save each sport to its own CSV file
- Skip teams whose season hasn't started yet
- Add date stamp to filenames

## Usage

### Fetch All Teams to CSV (Recommended)

```bash
# Save to default directory (ncaa_stats_output/)
python3 fetch_all_teams_to_csv.py

# Save to custom directory
python3 fetch_all_teams_to_csv.py --output-dir my_stats
```

**Output:**
```
ncaa_stats_output/
├── haverford_mens_basketball_20260112.csv      (19 players)
├── haverford_womens_basketball_20260112.csv    (15 players)
├── haverford_mens_soccer_20260112.csv          (34 players)
├── haverford_womens_soccer_20260112.csv        (31 players)
├── haverford_field_hockey_20260112.csv         (18 players)
└── haverford_womens_volleyball_20260112.csv    (19 players)
```

### Fetch Single Team to CSV

```bash
# Fetch just men's basketball
python3 fetch_basketball_to_csv.py
```

## CSV Format

Each CSV file contains:
- **Column 1**: Player Name
- **Columns 2+**: All stat categories for that sport

### Example: Basketball (33 stat columns)
```csv
Player Name,#,Yr,Pos,Ht,GP,GS,MP,FGM,FGA,FG%,3FG,3FGA,3FG%,FT,FTA,FT%,...
Isaac Varghese,,Jr,G,6-1,13,1,203:49,24,70,34.29,14,38,36.84,9,11,81.82,...
```

### Example: Soccer (19 stat columns)
```csv
Player Name,#,Yr,Pos,Ht,GP,GS,Minutes,Goals,Assists,Points,ShAtt,SoG,...
Madeline Dosen,,Sr,D,-,11,8,559:07,,,0,7,4,7,,1,...
```

**Note**: Different sports have different columns - the parser handles this automatically!

## Scripts Available

| Script | Purpose | Usage |
|--------|---------|-------|
| `fetch_all_teams_to_csv.py` | Fetch all teams, save each to CSV | Main batch export tool |
| `fetch_basketball_to_csv.py` | Fetch just men's basketball | Single team example |
| `discover_haverford_teams.py` | Find current team IDs | Run once per year |
| `test_all_haverford_teams.py` | Test all teams without saving | Validation testing |

## Yearly Update Process

At the start of each academic year (around September):

```bash
# Step 1: Discover new team IDs
python3 discover_haverford_teams.py

# Step 2: Copy output to config/config.example.yaml
#         (Replace the haverford_teams section)

# Step 3: Test with a single team
python3 fetch_basketball_to_csv.py

# Step 4: Fetch all teams
python3 fetch_all_teams_to_csv.py
```

That's it! The scraper is ready for the new season.

## Notes

- **Filename format**: `haverford_{sport}_{YYYYMMDD}.csv`
- **Date stamp**: Automatically added so you can track when stats were fetched
- **Spring sports**: Baseball, Lacrosse, Softball won't have stats in fall/winter
- **Error handling**: Script continues if one team fails, reports summary at end

## Integration with Other Tools

The CSV files can be:
- Opened in Excel/Google Sheets
- Imported into databases
- Processed with pandas/Python
- Shared with coaches/athletic staff
- Archived for historical tracking

## File Sizes

Typical CSV file sizes:
- Basketball: ~2-3 KB (15-20 players, 33 stats)
- Soccer: ~1-2 KB (30-35 players, 17-19 stats)
- Field Hockey: ~800 bytes (18 players, 14 stats)
- Volleyball: ~1-2 KB (19 players, 23 stats)

Very lightweight and easy to work with!
