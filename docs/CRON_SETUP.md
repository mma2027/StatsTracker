# Cron Job Setup Guide

This guide explains how to set up a daily cron job to automatically run StatsTracker at 8 AM every day.

## Quick Setup

### 1. Test the Wrapper Script

First, verify that the wrapper script works correctly:

```bash
cd /Users/maxfieldma/CS/projects/StatsTracker
./run_daily_check.sh
```

Check the log file to confirm it ran successfully:
```bash
tail -50 logs/cron_daily.log
```

### 2. Configure Cron Job

Edit your crontab:
```bash
crontab -e
```

Add this line to run StatsTracker daily at 8 AM:
```bash
0 8 * * * /Users/maxfieldma/CS/projects/StatsTracker/run_daily_check.sh
```

**Important:** Use the absolute path to the script, not a relative path.

### 3. Verify Cron Configuration

List your cron jobs to confirm it was added:
```bash
crontab -l
```

## Testing

### Test with Frequent Execution

For testing purposes, you can temporarily set the cron job to run every 5 minutes:

```bash
# Edit crontab
crontab -e

# Add test schedule (every 5 minutes)
*/5 * * * * /Users/maxfieldma/CS/projects/StatsTracker/run_daily_check.sh
```

Wait 5 minutes, then check the logs:
```bash
tail -100 logs/cron_daily.log
```

**Remember to change it back to the daily schedule (0 8 * * *) after testing!**

### Test Email Delivery

To test email functionality separately:
```bash
cd /Users/maxfieldma/CS/projects/StatsTracker
source venv/bin/activate
python main.py --test-email
```

## Cron Schedule Format

The cron format is: `minute hour day-of-month month day-of-week`

Examples:
- `0 8 * * *` - Daily at 8:00 AM
- `30 7 * * *` - Daily at 7:30 AM
- `0 8 * * 1-5` - Weekdays only at 8:00 AM
- `0 8 * * 0,6` - Weekends only at 8:00 AM
- `*/5 * * * *` - Every 5 minutes (for testing)

## Monitoring

### Check Recent Logs

View the most recent log entries:
```bash
tail -50 /Users/maxfieldma/CS/projects/StatsTracker/logs/cron_daily.log
```

### Watch Logs in Real-Time

Monitor the logs as they update:
```bash
tail -f /Users/maxfieldma/CS/projects/StatsTracker/logs/cron_daily.log
```

Press `Ctrl+C` to stop watching.

### Check Application Logs

The main application also writes to a separate log file:
```bash
tail -50 /Users/maxfieldma/CS/projects/StatsTracker/logs/statstrack.log
```

## Log Rotation

To prevent log files from growing too large, set up log rotation.

### Manual Log Rotation

Rotate logs manually with a script:

```bash
cd /Users/maxfieldma/CS/projects/StatsTracker/logs
mv cron_daily.log cron_daily.log.$(date +%Y%m%d)
touch cron_daily.log
gzip cron_daily.log.*

# Delete logs older than 30 days
find . -name "cron_daily.log.*.gz" -mtime +30 -delete
```

## Troubleshooting

### Cron Not Running

1. **Check if cron service is running:**
   ```bash
   # macOS
   sudo launchctl list | grep cron
   ```

2. **Check cron logs:**
   ```bash
   # macOS
   log show --predicate 'process == "cron"' --last 1h
   ```

### Email Not Sending

1. **Verify email configuration:**
   ```bash
   python main.py --test-email
   ```

2. **Check email credentials:**
   - For Gmail, use an [App Password](https://support.google.com/accounts/answer/185833)
   - Verify SMTP settings in `config/config.yaml`

3. **Check logs for SMTP errors:**
   ```bash
   grep -i "smtp\|email" logs/statstrack.log
   ```

### Stats Not Updating

1. **Test stats update manually:**
   ```bash
   python main.py --update-stats
   ```

2. **Check for NCAA website issues:**
   - The NCAA stats website may be temporarily unavailable
   - Check logs for HTTP errors or timeouts

3. **Verify database permissions:**
   ```bash
   ls -la data/stats.db
   ```

### Permission Errors

If you see permission errors:

```bash
# Fix script permissions
chmod +x run_daily_check.sh

# Fix log directory permissions
chmod 755 logs
chmod 644 logs/*.log 2>/dev/null || true

# Fix virtual environment permissions
chmod -R 755 venv
```

### Python Not Found

If cron can't find Python:

1. Find Python path:
   ```bash
   which python3
   ```

2. Update `run_daily_check.sh` to use the full path:
   ```bash
   /usr/local/bin/python3 "$SCRIPT_DIR/main.py"
   ```

### Environment Variables

Cron runs with a minimal environment. If you need specific environment variables, add them to `run_daily_check.sh`.

## Security Considerations

### Protect Email Credentials

- **Never commit `config/config.yaml` to git** (it's in `.gitignore`)
- Use app-specific passwords, not main account passwords
- Restrict file permissions:
  ```bash
  chmod 600 config/config.yaml
  ```

### Limit Cron Script Permissions

```bash
chmod 750 run_daily_check.sh  # Only owner can execute
```

### Database Backup

Consider backing up the database regularly:

```bash
# Add to crontab (daily at 2 AM)
0 2 * * * cp /Users/maxfieldma/CS/projects/StatsTracker/data/stats.db /Users/maxfieldma/CS/projects/StatsTracker/data/stats.db.backup
```

## Performance

### Expected Runtime

- Stats update: 5-10 minutes (fetching 10 NCAA teams)
- Milestone checks: 1-2 seconds
- Email sending: 1-2 seconds
- **Total: ~10-15 minutes**

Running at 8 AM ensures completion before most people check email at 8:15-8:30 AM.

### Rate Limiting

If you encounter rate limiting from NCAA:
- The script includes delays between requests (0.5s)
- Consider increasing delays in `src/website_fetcher/ncaa_fetcher.py`
- Run at off-peak hours (early morning is usually good)

## Disable/Remove Cron Job

### Temporarily Disable

Comment out the line in crontab:
```bash
crontab -e

# Add # at the beginning of the line:
# 0 8 * * * /Users/maxfieldma/CS/projects/StatsTracker/run_daily_check.sh
```

### Permanently Remove

```bash
crontab -e

# Delete the entire line and save
```

## Additional Resources

- [Crontab Guru](https://crontab.guru/) - Cron schedule expression editor
- [Gmail App Passwords](https://support.google.com/accounts/answer/185833)
- [NCAA Stats Website](https://stats.ncaa.org/)
