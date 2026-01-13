# Cron Job Setup for Daily 8 AM Automation

This guide explains how to set up the StatsTracker system to run automatically every day at 8 AM using Unix cron.

## Overview

The daily automation workflow:
1. Fetches latest stats from NCAA for all 10 teams (~5-10 minutes)
2. Checks gameday schedule to find which teams have games today
3. Only checks milestones for players on teams with games
4. Always sends email (even on days with no games or milestones)

## Prerequisites

Before setting up the cron job:

1. **Python 3.8+ installed** with all dependencies
2. **Virtual environment set up** at `/Users/maxfieldma/CS/projects/StatsTracker/venv`
3. **Configuration file** at `config/config.yaml` with valid email credentials
4. **Database initialized** at `data/stats.db`
5. **Wrapper script created** at `run_daily_check.sh` (already included)

## Step 1: Verify Wrapper Script

The `run_daily_check.sh` script handles environment setup for cron execution.

Check that it's executable:
```bash
ls -la run_daily_check.sh
```

If not executable, make it so:
```bash
chmod +x run_daily_check.sh
```

## Step 2: Test Manual Execution

Before setting up cron, test the wrapper script manually:

```bash
cd /Users/maxfieldma/CS/projects/StatsTracker
./run_daily_check.sh
```

**Expected output:**
- Stats update starts
- Gameday check completes
- Milestone checks (if any games)
- Email sent
- Exit code 0

**Check logs:**
```bash
tail -f logs/statstrack.log
```

## Step 3: Edit Crontab

Open your crontab for editing:
```bash
crontab -e
```

Add this line for daily 8 AM execution:
```cron
# StatsTracker - Daily 8 AM check (Monday-Sunday)
0 8 * * * /Users/maxfieldma/CS/projects/StatsTracker/run_daily_check.sh >> /Users/maxfieldma/CS/projects/StatsTracker/logs/cron_daily.log 2>&1
```

**Cron syntax breakdown:**
- `0` = minute (0 = top of the hour)
- `8` = hour (8 = 8 AM)
- `*` = any day of month
- `*` = any month
- `*` = any day of week
- `>> logs/cron_daily.log` = append output to log file
- `2>&1` = redirect errors to same log file

Save and exit (`:wq` in vim, `Ctrl+X` in nano).

## Step 4: Verify Cron Job

List your cron jobs to confirm it was added:
```bash
crontab -l
```

You should see the line you just added.

## Step 5: Monitor First Run

For testing, you can temporarily set a more frequent schedule:

```cron
# TESTING ONLY - Every 5 minutes
*/5 * * * * /Users/maxfieldma/CS/projects/StatsTracker/run_daily_check.sh >> /Users/maxfieldma/CS/projects/StatsTracker/logs/cron_daily.log 2>&1
```

Wait 5 minutes, then check the log:
```bash
tail -f logs/cron_daily.log
```

**Once verified, change back to daily 8 AM schedule!**

## Troubleshooting

### Cron Not Running

1. **Check cron service is running:**
   ```bash
   # macOS
   sudo launchctl list | grep cron

   # Linux
   ps aux | grep cron
   ```

2. **Check system logs:**
   ```bash
   # macOS
   log show --predicate 'process == "cron"' --last 1h

   # Linux
   grep CRON /var/log/syslog
   ```

3. **Verify script permissions:**
   ```bash
   ls -la run_daily_check.sh
   ```
   Should show `-rwxr-xr-x` (executable)

### Email Not Sending

1. **Check email credentials in config.yaml:**
   ```yaml
   email:
     smtp_server: "smtp.gmail.com"
     smtp_port: 587
     sender_email: "your-email@gmail.com"
     sender_password: "app-specific-password"  # NOT your regular Gmail password
   ```

2. **For Gmail, use App-Specific Password:**
   - Go to https://myaccount.google.com/apppasswords
   - Generate app password for "Mail"
   - Use that password in config.yaml

3. **Test email manually:**
   ```bash
   cd /Users/maxfieldma/CS/projects/StatsTracker
   python main.py --test-email
   ```

4. **Check logs for errors:**
   ```bash
   grep -i "error\|fail" logs/cron_daily.log
   grep -i "smtp\|email" logs/statstrack.log
   ```

### Database Errors

1. **Ensure data directory exists:**
   ```bash
   mkdir -p data
   ```

2. **Check database file permissions:**
   ```bash
   ls -la data/stats.db
   ```

3. **Verify database schema:**
   ```bash
   sqlite3 data/stats.db ".schema"
   ```

4. **Check database for recent stats:**
   ```bash
   sqlite3 data/stats.db "SELECT COUNT(*) FROM stats WHERE date_recorded > datetime('now', '-1 day');"
   ```

### Python/Virtual Environment Issues

1. **Verify Python path in wrapper script:**
   ```bash
   which python
   # Should show path inside venv
   ```

2. **Check virtual environment exists:**
   ```bash
   ls -la venv/bin/python
   ```

3. **Manually activate venv and test:**
   ```bash
   source venv/bin/activate
   python main.py
   ```

## Log Management

### Create Log Rotation (Optional)

Prevent logs from growing too large:

**On macOS:**
Create `/etc/newsyslog.d/statstrack.conf`:
```
# StatsTracker log rotation
/Users/maxfieldma/CS/projects/StatsTracker/logs/*.log 644 7 * * J
```

**On Linux:**
Create `/etc/logrotate.d/statstrack`:
```
/Users/maxfieldma/CS/projects/StatsTracker/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
}
```

### View Recent Logs

```bash
# Last 50 lines of cron log
tail -50 logs/cron_daily.log

# Last 100 lines of main log
tail -100 logs/statstrack.log

# Search for errors
grep -i error logs/*.log

# Filter by date
grep "$(date +%Y-%m-%d)" logs/cron_daily.log
```

## Security Best Practices

1. **Never commit config.yaml** with real credentials
   - Already in `.gitignore`

2. **Restrict file permissions:**
   ```bash
   chmod 600 config/config.yaml
   chmod 700 data/
   ```

3. **Use app-specific passwords** for Gmail (not your main password)

4. **Regular database backups:**
   ```bash
   cp data/stats.db data/stats_backup_$(date +%Y%m%d).db
   ```

## Alternative Scheduling Methods

### Using launchd (macOS)

Create `~/Library/LaunchAgents/com.haverford.statstracker.plist`:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.haverford.statstracker</string>
    <key>Program</key>
    <string>/Users/maxfieldma/CS/projects/StatsTracker/run_daily_check.sh</string>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>8</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>/Users/maxfieldma/CS/projects/StatsTracker/logs/launchd.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/maxfieldma/CS/projects/StatsTracker/logs/launchd_error.log</string>
</dict>
</plist>
```

Load it:
```bash
launchctl load ~/Library/LaunchAgents/com.haverford.statstracker.plist
```

### Using systemd (Linux)

Create `/etc/systemd/system/statstracker.service`:
```ini
[Unit]
Description=Haverford StatsTracker Daily Check
After=network.target

[Service]
Type=oneshot
User=maxfieldma
WorkingDirectory=/Users/maxfieldma/CS/projects/StatsTracker
ExecStart=/Users/maxfieldma/CS/projects/StatsTracker/run_daily_check.sh
```

Create `/etc/systemd/system/statstracker.timer`:
```ini
[Unit]
Description=Run StatsTracker Daily at 8 AM

[Timer]
OnCalendar=*-*-* 08:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

Enable and start:
```bash
sudo systemctl enable statstracker.timer
sudo systemctl start statstracker.timer
```

## Monitoring & Maintenance

### Daily Checks

1. **Verify email arrived** (check inbox at 8:05 AM daily)
2. **Check logs for errors** once per week
3. **Verify database growth** (should add ~1000-2000 stats daily)

### Weekly Maintenance

```bash
# Check log file sizes
du -sh logs/*

# Check database size
du -sh data/stats.db

# Verify recent stats were added
sqlite3 data/stats.db "SELECT COUNT(*), MAX(date_recorded) FROM stats;"
```

### Monthly Tasks

1. Review email alert accuracy
2. Update milestone thresholds if needed (config.yaml)
3. Backup database: `cp data/stats.db data/monthly_backup_$(date +%Y%m).db`
4. Clean old log files (if not using log rotation)

## Disabling Automation

To temporarily disable:
```bash
crontab -e
# Comment out the line with #
# 0 8 * * * /path/to/run_daily_check.sh ...
```

To remove completely:
```bash
crontab -e
# Delete the entire line
```

## Getting Help

If issues persist:

1. Check logs: `logs/cron_daily.log` and `logs/statstrack.log`
2. Run manually: `./run_daily_check.sh` to see errors directly
3. Test components individually:
   - Gameday: `python -c "from src.gameday_checker import GamedayChecker; g = GamedayChecker(); print(g.get_games_for_today())"`
   - Email: `python main.py --test-email`
   - Database: `sqlite3 data/stats.db "SELECT * FROM players LIMIT 5;"`

## Success Checklist

- [ ] Cron job added to crontab
- [ ] Wrapper script is executable
- [ ] Manual test run succeeds
- [ ] First automated run completes successfully
- [ ] Email received after first run
- [ ] Logs show no errors
- [ ] Database updates with new stats
- [ ] System runs reliably for 7+ consecutive days

---

**Last Updated:** January 13, 2026
**Script Version:** 1.0
**Project:** Haverford College StatsTracker
