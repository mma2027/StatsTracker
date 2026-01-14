# Daily Automated Stats & Milestone Notifications - Implementation Summary

## Overview

The StatsTracker system has been fully implemented with daily automated workflow capabilities. This document summarizes what has been implemented and how to use it.

## What It Does

Every day at 8 AM (via cron job), the system will automatically:

1. **Update ALL NCAA stats** - Fetches latest statistics for all 10 Haverford teams from NCAA website
2. **Check for games today** - Uses Haverford Athletics calendar to find games scheduled for today
3. **Check milestones** - ONLY checks milestone proximity for players on teams with games today
4. **Send email** - ALWAYS sends an email (even on days with no games or milestones)

## Email Behavior

### On Days WITH Games
- Subject: "Haverford Milestone Alert - [Date] (X games today)"
- Content:
  - Today's Games section (lists all games)
  - Players Close to Milestones section (only for sports with games today)

### On Days WITHOUT Games
- Subject: "Haverford Daily Update - [Date] (No Games Today)"
- Content:
  - Special "No Games or Milestone Alerts Today" message
  - Confirmation that system is running and database was updated

## Implementation Status

### ✅ Completed Components

#### 1. Core Logic (main.py)
- **Lines 283-291**: Always updates stats before checking milestones
- **Lines 308-337**: Filters milestone checks by sports with games today
- **Lines 339-353**: Always sends email (including empty-day notifications)
- **Sport normalization**: Converts "Men's Basketball" → "mens_basketball" for database filtering

#### 2. Email Templates (src/email_notifier/templates.py)
- **Lines 22-45**: Updated subject line generation with empty-day case
- **Lines 134-163**: HTML empty-day message template
- **Lines 246-260**: Plain text empty-day message template
- Both templates show styled confirmation message on empty days

#### 3. Email Notifier (src/email_notifier/notifier.py)
- **Line 68**: Passes `has_milestones` flag to subject generator
- **Lines 49-77**: Always sends email regardless of content
- Updated docstring to reflect always-send behavior

#### 4. Cron Infrastructure
- **run_daily_check.sh**: Wrapper script for cron execution
  - Activates virtual environment
  - Sets PYTHONPATH
  - Handles logging
  - Returns proper exit codes
- **docs/CRON_SETUP.md**: Complete setup and troubleshooting guide

## Files Modified

| File | Purpose | Key Changes |
|------|---------|-------------|
| [main.py](main.py) | Core orchestrator | Always update stats, filter by game day, always send email |
| [src/email_notifier/templates.py](src/email_notifier/templates.py) | Email generation | Empty-day templates |
| [src/email_notifier/notifier.py](src/email_notifier/notifier.py) | Email sending | Updated signature |
| [run_daily_check.sh](run_daily_check.sh) | Cron wrapper | NEW - Environment setup |
| [docs/CRON_SETUP.md](docs/CRON_SETUP.md) | Documentation | NEW - Setup guide |

## Setup Instructions

### 1. Configure Email Settings

Edit `config/config.yaml`:

```yaml
email:
  smtp_server: "smtp.gmail.com"
  smtp_port: 587
  sender_email: "your-email@gmail.com"
  sender_password: "your-app-specific-password"  # NOT your regular password!
  recipients:
    - "recipient@example.com"

notifications:
  enabled: true
  proximity_threshold: 10  # Alert when within 10 units of milestone
```

**For Gmail users**: Create an [App Password](https://support.google.com/accounts/answer/185833) - DO NOT use your regular password.

### 2. Test the System

Before setting up cron, test each component:

```bash
cd /Users/maxfieldma/CS/projects/StatsTracker
source venv/bin/activate

# Test 1: Email configuration
python main.py --test-email

# Test 2: Stats update
python main.py --update-stats

# Test 3: Full workflow (stats + milestones + email)
python main.py

# Test 4: Wrapper script
./run_daily_check.sh
```

### 3. Set Up Cron Job

Edit your crontab:
```bash
crontab -e
```

Add this line:
```bash
0 8 * * * /Users/maxfieldma/CS/projects/StatsTracker/run_daily_check.sh
```

Save and exit. Verify it was added:
```bash
crontab -l
```

### 4. Monitor First Run

Check the logs after 8 AM the next day:
```bash
tail -100 /Users/maxfieldma/CS/projects/StatsTracker/logs/cron_daily.log
```

## Testing with Frequent Runs

To test without waiting until 8 AM tomorrow, temporarily change the cron schedule:

```bash
crontab -e

# Add this line for testing (runs every 5 minutes):
*/5 * * * * /Users/maxfieldma/CS/projects/StatsTracker/run_daily_check.sh

# Check logs after 5 minutes:
tail -f logs/cron_daily.log
```

**IMPORTANT**: Change it back to `0 8 * * *` after testing!

## Data Flow

```
┌─────────────────────────────────────────────────────────┐
│                    8 AM Daily Trigger                    │
│                      (Cron Job)                         │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              Step 1: Update ALL Stats                    │
│        (Fetch from NCAA for all 10 teams)               │
│              → Update Database                           │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│         Step 2: Check Games Today                        │
│    (Query Haverford Athletics Calendar)                 │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
           ┌─────────┴─────────┐
           │                   │
    No Games Today      Games Found
           │                   │
           │                   ▼
           │         ┌─────────────────────────┐
           │         │  Extract Sports with    │
           │         │  Games Today            │
           │         │  (e.g., mens_basketball)│
           │         └──────────┬──────────────┘
           │                    │
           │                    ▼
           │         ┌─────────────────────────┐
           │         │  Check Milestones       │
           │         │  ONLY for Those Sports  │
           │         └──────────┬──────────────┘
           │                    │
           └──────────┬─────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│              Step 3: ALWAYS Send Email                   │
│                                                          │
│  If games + milestones: Normal alert email              │
│  If games only: Games section + "No milestones"         │
│  If neither: "No Games Today" confirmation email        │
└─────────────────────────────────────────────────────────┘
```

## Sport Name Normalization

The system handles different sport name formats across systems:

| Source | Format | Example |
|--------|--------|---------|
| Haverford Athletics API | Human-readable | "Men's Basketball" |
| Database/Config | snake_case | "mens_basketball" |
| Email Display | Title Case | "Men's Basketball" |

**Normalization function** (in main.py line 314):
```python
sport_key = game.team.sport.lower().replace(' ', '_').replace("'", '')
```

## Configuration Notes

### Auto-Update Stats Behavior

The `auto_update_stats` config option is **IGNORED** in the daily workflow. The system ALWAYS updates stats every morning to ensure the database has the latest data before checking milestones.

```yaml
notifications:
  auto_update_stats: false  # Documentation only - always true in daily run
```

If you run `python main.py` manually outside of cron, the stats will still always be updated.

## Performance Expectations

### Typical Runtime
- Stats update: 5-10 minutes (10 teams × 30-60 seconds each)
- Game checking: 2-3 seconds
- Milestone checking: 1-2 seconds
- Email sending: 1-2 seconds
- **Total: 10-15 minutes**

### Why This Matters
Running at 8:00 AM means:
- Completion by ~8:15 AM
- Email arrives before most people check morning email (8:30-9:00 AM)
- Low system load (early morning)
- Minimal NCAA website traffic (less rate limiting)

## Troubleshooting

### Email Not Received

1. Check logs for errors:
   ```bash
   grep -i "email\|smtp" logs/statstrack.log
   ```

2. Verify email credentials:
   ```bash
   python main.py --test-email
   ```

3. Check spam folder

4. Verify Gmail App Password (if using Gmail)

### Stats Not Updating

1. Test manually:
   ```bash
   python main.py --update-stats
   ```

2. Check for NCAA website issues in logs

3. Verify Selenium ChromeDriver is installed:
   ```bash
   python -c "from selenium import webdriver; print('Selenium OK')"
   ```

### Cron Not Running

1. Check cron service:
   ```bash
   sudo launchctl list | grep cron
   ```

2. Check system logs:
   ```bash
   log show --predicate 'process == "cron"' --last 1h
   ```

3. Verify script permissions:
   ```bash
   ls -la run_daily_check.sh
   # Should show: -rwxr-xr-x
   ```

### Empty Logs

If `logs/cron_daily.log` is empty:
- Cron may not have run yet (wait until after 8 AM)
- Check crontab configuration: `crontab -l`
- Verify script path is absolute, not relative

## Security Best Practices

### Email Credentials
- Use App-specific passwords (not main account password)
- Never commit `config/config.yaml` to git (already in .gitignore)
- Restrict file permissions:
  ```bash
  chmod 600 config/config.yaml
  ```

### Database Backup
Add a backup cron job:
```bash
0 2 * * * cp /Users/maxfieldma/CS/projects/StatsTracker/data/stats.db /Users/maxfieldma/CS/projects/StatsTracker/data/stats.db.backup
```

## Verification Checklist

Before going live, verify:

- [ ] Email configuration is valid (`python main.py --test-email`)
- [ ] Stats update works (`python main.py --update-stats`)
- [ ] Full workflow works (`python main.py`)
- [ ] Wrapper script works (`./run_daily_check.sh`)
- [ ] Cron job is configured (`crontab -l`)
- [ ] Logs directory exists (`ls logs/`)
- [ ] Empty-day email received (test on a day with no games)
- [ ] Game-day email received (test on a day with games)

## Maintenance

### Daily
- Verify email was received (check inbox around 8:15 AM)

### Weekly
- Check logs for errors:
  ```bash
  grep -i "error\|failed" logs/cron_daily.log
  ```

### Monthly
- Review milestone thresholds in `config/config.yaml`
- Clean up old logs:
  ```bash
  find logs/ -name "*.log" -mtime +30 -delete
  ```

### Annually
- Update NCAA team IDs in config (team IDs change each academic year)
- Run team ID update script:
  ```bash
  python scripts/auto_update_team_ids.py
  ```

## Support Resources

- **Setup Guide**: [docs/CRON_SETUP.md](CRON_SETUP.md)
- **General Getting Started**: [docs/getting_started.md](getting_started.md)
- **NCAA Team IDs**: [docs/TEAM_GUIDE.md](TEAM_GUIDE.md)

## Summary

The system is **fully implemented and ready to deploy**. All code changes are complete:
- ✅ Always updates stats daily
- ✅ Filters milestones by game day
- ✅ Always sends email (including empty days)
- ✅ Cron infrastructure ready
- ✅ Documentation complete

**Next step**: Configure email credentials and set up the cron job!
