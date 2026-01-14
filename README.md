# StatsTracker

A production-ready system for tracking Haverford College sports statistics, detecting milestones, and sending automated notifications. Features a comprehensive web interface for browsing stats, configuring milestones, and managing settings.

## Project Overview

StatsTracker automatically fetches sports statistics from NCAA and other sources, stores them in a database, tracks player progress toward milestones, and sends email notifications. The system includes a full web interface for browsing player stats, searching across all teams, and configuring milestone thresholds.

## Features

### Core System
- ✅ **Automated Stats Fetching**: Daily updates from NCAA for 10+ Haverford sports
- ✅ **Career Stats Tracking**: Season-by-season statistics with historical data
- ✅ **Milestone Detection**: Configurable thresholds with proximity alerts
- ✅ **Email Notifications**: Beautiful HTML emails with game schedules and milestone alerts
- ✅ **Gameday Checker**: Automatic detection of upcoming games

### Web Interface
- ✅ **Stats Browser**: Browse all player statistics by sport/team
- ✅ **Global Search**: Search for any player across all sports
- ✅ **Settings Page**: Configure email, milestones, and notifications via web UI
- ✅ **Milestone Configuration**: Per-sport stats selection with individual thresholds
- ✅ **Responsive Design**: Clean, mobile-friendly interface

### Supported Sports (10 NCAA Teams)
- Men's & Women's Basketball
- Men's & Women's Soccer
- Men's & Women's Lacrosse
- Baseball & Softball
- Field Hockey
- Women's Volleyball

## Architecture

### Core Modules

#### 1. **Website Fetcher** (`src/website_fetcher/`) ✅
- NCAA stats fetcher (Selenium-based, handles JavaScript)
- TFRR fetcher for track & field (in progress)
- Generic parser works across all sports
- Auto-recovery from invalid team IDs

#### 2. **Player Database** (`src/player_database/`) ✅
- SQLite database with flexible schema
- Stores career stats with season-by-season breakdown
- Fast search and filtering
- Automatic updates with timestamp tracking

#### 3. **Milestone Detector** (`src/milestone_detector/`) ✅
- Configurable milestone thresholds per sport and stat
- Proximity detection (alert when within X units)
- Per-stat alert customization
- Historical milestone tracking

#### 4. **Email Notifier** (`src/email_notifier/`) ✅
- HTML email templates with responsive design
- Game schedule integration
- Milestone proximity alerts
- Multiple recipients and CC support

#### 5. **Gameday Checker** (`src/gameday_checker/`) ✅
- Fetches schedules from Haverford Athletics calendar
- Fast single-request fetching for full season
- Parses team, opponent, date, time, location

#### 6. **Web Interface** (`web/`) ✅
- Flask-based web application
- Real-time stats browsing and search
- Configuration management via web UI
- Server-Sent Events for long-running operations

## Getting Started

### Prerequisites
- Python 3.8+
- pip
- Virtual environment (recommended)

### Installation

```bash
# Clone the repository
git clone https://github.com/mma2027/StatsTracker.git
cd StatsTracker

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy configuration template
cp config/config.example.yaml config/config.yaml
# Edit config.yaml with your settings
```

### Running the System

#### Web Interface (Recommended)
```bash
cd web
python app.py
```
Then open http://localhost:5000 in your browser to:
- Browse player statistics
- Search for players
- Configure milestones and settings
- Monitor stats updates

#### Command Line
```bash
# Fetch all NCAA stats and update database
python main.py

# Run milestone detection
python main.py --check-milestones

# Send test email
python main.py --test-email
```

## Module Development Guide

Each module has a defined interface. Developers should:

1. Work in your assigned module directory
2. Follow the interface contracts defined in `docs/interfaces.md`
3. Write tests in the corresponding `tests/` directory
4. Create a feature branch for your work: `git checkout -b feature/module-name-feature`
5. Submit pull requests when ready for review

### Module Interfaces

See [docs/interfaces.md](docs/interfaces.md) for detailed interface specifications.

## Testing

We have comprehensive test coverage with 55+ tests across multiple modules.

```bash
# Run all tests
pytest

# Run tests for a specific module
pytest tests/gameday_checker/
pytest tests/email_notifier/
pytest tests/player_database/

# Run with coverage
pytest --cov=src

# Run with verbose output
pytest -v
```

See [TEST_GUIDE.md](TEST_GUIDE.md) for detailed testing documentation.

## Project Structure

```
StatsTracker/
├── src/
│   ├── gameday_checker/      # Game schedule module
│   ├── website_fetcher/       # Stats fetching module
│   ├── player_database/       # Data storage module
│   ├── milestone_detector/    # Milestone analysis module
│   └── email_notifier/        # Email notification module
├── tests/                     # Test files mirroring src/
├── config/                    # Configuration files
├── data/                      # Local data storage
├── docs/                      # Documentation
├── main.py                    # Main orchestrator
└── requirements.txt           # Python dependencies
```

## Contributing

1. Choose a module to work on
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Implement your feature following the module interface
4. Write tests for your code
5. Commit your changes: `git commit -m "Add feature description"`
6. Push to your branch: `git push origin feature/your-feature-name`
7. Open a Pull Request

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

## Continuous Integration

The project includes automated CI/CD with GitHub Actions:

- **Code Quality Checks**: Black formatting, Flake8 linting, MyPy type checking
- **Automated Testing**: Full test suite runs on every PR and push to main
- **Coverage Reports**: Test coverage tracking and reporting
- **Branch Protection**: Requires passing tests and code review before merging

All PRs must pass the CI pipeline before merging. See [CONTRIBUTING.md](CONTRIBUTING.md) for details on running checks locally.

## Configuration

Edit `config/config.yaml` to set:
- Email settings (SMTP server, credentials)
- Database connection
- Milestone thresholds
- Notification recipients
- Website URLs for fetchers

## License

TBD
