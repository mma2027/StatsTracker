# StatsTracker

A modular system for tracking Haverford College sports statistics and notifying about milestone achievements.

## Project Overview

StatsTracker fetches sports statistics from various sources, tracks player progress, identifies milestone achievements, and sends email notifications on game days when players are close to milestones.

## Architecture

The project is divided into independent modules that can be developed in parallel:

### 1. **Gameday Checker** (`src/gameday_checker/`) ✅ **Complete**
- **Purpose**: Determines which Haverford College sports teams have games on a given day
- **Input**: Date
- **Output**: List of teams with games scheduled
- **Status**: Fully implemented using Haverford athletics calendar API
- **Performance**: Single HTTP request, ~2-5 seconds, full season access

### 2. **Website Fetcher** (`src/website_fetcher/`)
- **Purpose**: Fetches statistics from various sources (NCAA, TFRR, etc.)
- **Components**:
  - Base fetcher interface
  - NCAA fetcher implementation
  - TFRR (Track & Field Results Reporting) fetcher
  - Additional sport-specific fetchers
- **Owner**: TBD

### 3. **Player Database** (`src/player_database/`) ✅ **Complete**
- **Purpose**: Stores and manages player statistics
- **Responsibilities**:
  - Data storage (SQLite)
  - CRUD operations for player data
  - Historical stats tracking
- **Status**: Fully implemented with comprehensive test coverage

### 4. **Milestone Detector** (`src/milestone_detector/`)
- **Purpose**: Analyzes player stats to identify who is close to milestones
- **Input**: Player statistics from database
- **Output**: List of players near milestones with details
- **Owner**: TBD

### 5. **Email Notifier** (`src/email_notifier/`) ✅ **Complete**
- **Purpose**: Sends formatted email notifications
- **Input**: Milestone information and game schedule
- **Output**: Email to recipients
- **Status**: Fully implemented with customizable HTML templates and 48 tests

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

```bash
python main.py
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
