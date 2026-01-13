# StatsTracker Project Structure

## Directory Organization

```
StatsTracker/
├── src/                        # Core source code
│   ├── email_notifier/         # Email notification system
│   ├── gameday_checker/        # Game schedule checker
│   ├── milestone_detector/     # Milestone detection logic
│   ├── player_database/        # Database operations
│   └── website_fetcher/        # Web scrapers (NCAA, TFRR, Cricket)
│
├── scripts/                    # Utility and execution scripts
│   ├── fetch_*.py              # Data fetching scripts
│   ├── auto_update_team_ids.py # Team ID management
│   ├── discover_haverford_teams.py
│   ├── update_database_from_ncaa.py
│   └── query_database_example.py
│
├── csv_exports/                # All CSV output files
│   ├── batting_real.csv
│   ├── bowling_real.csv
│   ├── haverford_*.csv
│   └── [generated CSV files]
│
├── tests/                      # Automated unit tests
│   ├── email_notifier/
│   ├── gameday_checker/
│   ├── milestone_detector/
│   ├── player_database/
│   └── website_fetcher/
│
├── tests_manual/               # Manual test scripts
│   ├── test_*.py               # Manual testing scripts
│   └── [debugging scripts]
│
├── docs/                       # Documentation
│   ├── guides/                 # Comprehensive guides
│   │   ├── AUTO_RECOVERY_GUIDE.md
│   │   ├── CSV_EXPORT_GUIDE.md
│   │   ├── DATABASE_INTEGRATION_GUIDE.md
│   │   ├── EMAIL_SETUP_SUMMARY.md
│   │   ├── HOW_TO_SEND_EMAIL.md
│   │   └── TFRR_INTEGRATION_GUIDE.md
│   ├── TEAM_GUIDE.md
│   ├── deployment.md
│   ├── getting_started.md
│   └── interfaces.md
│
├── config/                     # Configuration files
│   └── config.example.yaml     # Configuration template
│
├── data/                       # Runtime data
│   ├── stats.db                # SQLite database
│   └── cache/                  # Cache directory
│
├── output/                     # Generated output files
│   ├── email_preview.html
│   └── [other output files]
│
├── .github/                    # GitHub workflows and CI/CD
│   └── workflows/
│
├── main.py                     # Main orchestrator script
├── requirements.txt            # Python dependencies
├── pyproject.toml             # Project metadata
├── pytest.ini                 # Test configuration
├── README.md                  # Project overview
├── PROJECT_STATUS.md          # Current project status
└── CONTRIBUTING.md            # Contribution guidelines
```

## Key Directories

### `/src/` - Core Modules
All production code organized by functionality:
- **email_notifier**: Send HTML email notifications
- **gameday_checker**: Check upcoming game schedules
- **milestone_detector**: Detect player milestones
- **player_database**: SQLite database operations
- **website_fetcher**: Web scrapers for various sports statistics sites

### `/scripts/` - Utility Scripts
Standalone scripts for data operations:
- Fetch stats from various sources (NCAA, TFRR, Cricket)
- Update database with latest stats
- Manage team IDs
- Query and analyze data

### `/csv_exports/` - CSV Files
**All CSV output files are stored here**, including:
- Basketball stats
- Track & field PRs
- Cricket statistics
- Any exported team data

### `/tests_manual/` - Manual Tests
Interactive test scripts for debugging and validation:
- Individual athlete tests
- Data fetching tests
- Parser validation

### `/docs/guides/` - Comprehensive Guides
Detailed documentation for specific features:
- Setup guides
- Integration guides
- How-to documents

### `/output/` - Generated Files
HTML previews, reports, and other generated output files

## Quick Start

### Fetch Latest Stats
```bash
# NCAA stats
python3 scripts/fetch_all_teams_to_csv.py

# TFRR track stats
python3 scripts/fetch_tfrr_to_csv.py --sport mens_track

# Cricket stats
python3 scripts/fetch_real_cricket_data.py
```

### Update Database
```bash
python3 scripts/update_database_from_ncaa.py
```

### Run Main Orchestrator
```bash
python3 main.py
```

### Find CSV Files
All exported CSV files are in: `csv_exports/`

## File Naming Conventions

### CSV Files
- `haverford_{sport}_{date}.csv` - Exported stats
- `{sport}_real.csv` - Real data imports

### Scripts
- `fetch_*.py` - Data fetching scripts
- `update_*.py` - Database update scripts
- `test_*.py` - Test scripts (in tests_manual/)

### Documentation
- `*_GUIDE.md` - Comprehensive guides (in docs/guides/)
- `HOW_TO_*.md` - Step-by-step tutorials (in docs/guides/)
- `*_STATUS.md` - Status documents (in root)

## Development Workflow

1. **Write Code**: Add to appropriate module in `src/`
2. **Create Scripts**: Add utility scripts to `scripts/`
3. **Write Tests**: Add tests to `tests/` (automated) or `tests_manual/` (manual)
4. **Generate CSV**: Outputs go to `csv_exports/`
5. **Document**: Add guides to `docs/guides/`

## Notes

- All CSV files are now centralized in `csv_exports/` for easy access
- Manual test scripts are separated from automated tests
- Documentation is organized in `docs/` with guides in a subdirectory
- Scripts are separated from core source code
- Output files (HTML, etc.) go to `output/`
