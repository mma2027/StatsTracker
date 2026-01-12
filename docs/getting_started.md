# Getting Started with StatsTracker

This guide will help you get StatsTracker up and running quickly.

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Git
- A Gmail account or other SMTP email service

## Quick Start

### 1. Clone the Repository

```bash
cd /path/to/your/projects
git clone https://github.com/mma2027/StatsTracker.git
cd StatsTracker
```

### 2. Set Up Python Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
# On Mac/Linux:
source venv/bin/activate

# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure the Application

```bash
# Copy the example configuration
cp config/config.example.yaml config/config.yaml

# Edit the configuration file
nano config/config.yaml
# or use your preferred editor
```

**Important configuration items:**

1. **Email settings** (required for notifications)
   ```yaml
   email:
     smtp_server: "smtp.gmail.com"
     smtp_port: 587
     sender_email: "your-email@gmail.com"
     sender_password: "your-app-password"  # See below for setup
     recipients:
       - "recipient@example.com"
   ```

2. **Database path** (default is fine)
   ```yaml
   database:
     type: "sqlite"
     path: "data/stats.db"
   ```

3. **Milestones** (customize for your needs)
   ```yaml
   milestones:
     basketball:
       points: [500, 1000, 1500, 2000]
       rebounds: [300, 500, 750, 1000]
   ```

### 4. Set Up Gmail for Sending Emails

If using Gmail:

1. Go to your Google Account settings
2. Enable 2-Factor Authentication
3. Generate an App Password:
   - Go to Security → 2-Step Verification → App passwords
   - Select "Mail" and "Other (Custom name)"
   - Name it "StatsTracker"
   - Copy the 16-character password
4. Use this app password in your `config.yaml`

### 5. Test Your Setup

```bash
# Test email configuration
python main.py --test-email
```

You should receive a test email at the configured recipient address.

### 6. Add Players to Database

Create a simple script to add players:

```python
# add_players.py
from src.player_database import PlayerDatabase, Player

db = PlayerDatabase("data/stats.db")

players = [
    Player(
        player_id="p001",
        name="John Smith",
        sport="basketball",
        position="Guard",
        year="Junior"
    ),
    Player(
        player_id="p002",
        name="Jane Doe",
        sport="track",
        year="Senior"
    ),
    # Add more players...
]

for player in players:
    db.add_player(player)
    print(f"Added {player.name}")
```

Run it:
```bash
python add_players.py
```

### 7. Add Some Test Stats

```python
# add_stats.py
from src.player_database import PlayerDatabase, StatEntry
from datetime import datetime

db = PlayerDatabase("data/stats.db")

stats = [
    StatEntry(
        player_id="p001",
        stat_name="points",
        stat_value=950,  # Close to 1000 milestone
        season="2023-24"
    ),
    StatEntry(
        player_id="p001",
        stat_name="rebounds",
        stat_value=280,  # Close to 300 milestone
        season="2023-24"
    ),
]

for stat in stats:
    db.add_stat(stat)
    print(f"Added stat: {stat.stat_name} = {stat.stat_value}")
```

### 8. Run the System

```bash
# Run the main program
python main.py
```

This will:
1. Check for games today
2. Check for milestone proximities
3. Send an email if there are alerts

## What's Next?

### For Developers

Choose a module to work on:

1. **Gameday Checker** - Implement website scraping for Haverford athletics
   - See `src/gameday_checker/README.md`
   - Start with `src/gameday_checker/checker.py`

2. **Website Fetcher** - Implement stats fetching from NCAA, TFRR, etc.
   - See `src/website_fetcher/README.md`
   - Start with `src/website_fetcher/ncaa_fetcher.py`

3. **Milestone Detector** - Enhance milestone detection logic
   - See `src/milestone_detector/README.md`
   - Add sport-specific milestone calculations

4. **Email Templates** - Improve email formatting
   - See `src/email_notifier/templates.py`
   - Customize the HTML/CSS styling

### Development Workflow

1. **Create a branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Edit files in your module
   - Write tests
   - Test locally

3. **Commit and push**
   ```bash
   git add .
   git commit -m "Description of changes"
   git push origin feature/your-feature-name
   ```

4. **Create Pull Request**
   - Go to GitHub
   - Create PR from your branch
   - Request review

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/player_database/test_database.py

# Run with coverage
pytest --cov=src

# Run with verbose output
pytest -v
```

### Viewing Logs

Logs are saved to `logs/statstrack.log` (configure in `config.yaml`):

```bash
# View recent logs
tail -f logs/statstrack.log

# Search logs
grep "ERROR" logs/statstrack.log
```

## Common Issues

### Email Not Sending

**Problem**: "SMTP authentication failed"

**Solution**:
- Make sure you're using an app password, not your regular Gmail password
- Enable 2-Factor Authentication on your Google account first
- Check that the email and password are correct in config.yaml

### Database Errors

**Problem**: "database is locked"

**Solution**:
- Make sure only one instance of the program is running
- Check file permissions on `data/stats.db`

### Module Import Errors

**Problem**: "ModuleNotFoundError"

**Solution**:
- Make sure virtual environment is activated: `source venv/bin/activate`
- Reinstall dependencies: `pip install -r requirements.txt`

## Documentation

- [README.md](../README.md) - Project overview
- [CONTRIBUTING.md](../CONTRIBUTING.md) - How to contribute
- [docs/interfaces.md](interfaces.md) - Module interfaces
- [docs/deployment.md](deployment.md) - Deployment guide
- Module-specific READMEs in each `src/` subdirectory

## Getting Help

- Check module READMEs for specific implementation guidance
- Look at example test files for usage patterns
- Open an issue on GitHub for bugs or questions
- Review the interfaces documentation for how modules connect

## Next Steps

1. Implement the gameday checker to fetch real game schedules
2. Implement website fetchers to get real player stats
3. Set up automated daily execution (see deployment guide)
4. Customize milestone thresholds for your needs
5. Enhance email templates with your branding

Happy coding! 🎉
