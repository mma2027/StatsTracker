# Deployment Guide

This guide explains how to deploy StatsTracker to run automatically.

## Running Locally

### One-Time Execution

```bash
# Activate virtual environment
source venv/bin/activate

# Run the system
python main.py

# Or with custom config
python main.py --config /path/to/config.yaml
```

### Test Email Setup

```bash
python main.py --test-email
```

### Update Stats Only

```bash
python main.py --update-stats
```

## Automated Execution

### Using Cron (Linux/Mac)

Edit crontab:
```bash
crontab -e
```

Add entry to run daily at 8 AM:
```cron
0 8 * * * cd /path/to/StatsTracker && /path/to/venv/bin/python main.py >> logs/cron.log 2>&1
```

Run on game days only (example: Tuesdays and Fridays at 8 AM):
```cron
0 8 * * 2,5 cd /path/to/StatsTracker && /path/to/venv/bin/python main.py
```

### Using Task Scheduler (Windows)

1. Open Task Scheduler
2. Create Basic Task
3. Set trigger (daily at 8 AM)
4. Set action: Start a program
   - Program: `C:\path\to\venv\Scripts\python.exe`
   - Arguments: `main.py`
   - Start in: `C:\path\to\StatsTracker`

### Using systemd (Linux)

Create service file `/etc/systemd/system/statstracker.service`:

```ini
[Unit]
Description=StatsTracker Daily Notification
After=network.target

[Service]
Type=oneshot
User=youruser
WorkingDirectory=/path/to/StatsTracker
ExecStart=/path/to/venv/bin/python main.py
StandardOutput=append:/path/to/StatsTracker/logs/service.log
StandardError=append:/path/to/StatsTracker/logs/service.log

[Install]
WantedBy=multi-user.target
```

Create timer file `/etc/systemd/system/statstracker.timer`:

```ini
[Unit]
Description=Run StatsTracker daily at 8 AM

[Timer]
OnCalendar=daily
OnCalendar=08:00
Persistent=true

[Install]
WantedBy=timers.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable statstracker.timer
sudo systemctl start statstracker.timer
```

Check status:
```bash
systemctl status statstracker.timer
systemctl list-timers
```

## Server Deployment

### Requirements

- Python 3.8+
- Internet connection
- SMTP access (for email)
- Sufficient storage for database

### Setup Steps

1. **Clone repository**
   ```bash
   git clone https://github.com/mma2027/StatsTracker.git
   cd StatsTracker
   ```

2. **Create virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure**
   ```bash
   cp config/config.example.yaml config/config.yaml
   nano config/config.yaml
   ```

5. **Test setup**
   ```bash
   python main.py --test-email
   ```

6. **Set up automation** (see above)

### Environment Variables

For production, use environment variables instead of config file:

```bash
export SMTP_SERVER="smtp.gmail.com"
export SMTP_PORT="587"
export SENDER_EMAIL="your-email@example.com"
export SENDER_PASSWORD="your-app-password"
export DB_PATH="/path/to/data/stats.db"
```

Update code to read from environment:
```python
import os

smtp_server = os.getenv('SMTP_SERVER', config.get('smtp_server'))
```

## Docker Deployment

Create `Dockerfile`:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
```

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  statstracker:
    build: .
    volumes:
      - ./data:/app/data
      - ./config:/app/config
      - ./logs:/app/logs
    environment:
      - SMTP_SERVER=${SMTP_SERVER}
      - SMTP_PORT=${SMTP_PORT}
      - SENDER_EMAIL=${SENDER_EMAIL}
      - SENDER_PASSWORD=${SENDER_PASSWORD}
    restart: unless-stopped
```

Run with cron in Docker:

```dockerfile
# Add to Dockerfile
RUN apt-get update && apt-get install -y cron
COPY crontab /etc/cron.d/statstracker
RUN chmod 0644 /etc/cron.d/statstracker
RUN crontab /etc/cron.d/statstracker

CMD ["cron", "-f"]
```

## Cloud Deployment Options

### AWS Lambda

- Use AWS Lambda with CloudWatch Events for scheduling
- Package dependencies in Lambda layer
- Set environment variables in Lambda console
- Configure SES for email sending

### Google Cloud Functions

- Deploy as scheduled Cloud Function
- Use Cloud Scheduler for timing
- Store config in Secret Manager
- Use SendGrid or similar for email

### Heroku

```bash
# Install Heroku CLI
heroku create statstracker

# Add scheduler addon
heroku addons:create scheduler:standard

# Deploy
git push heroku main

# Configure in Heroku dashboard
heroku addons:open scheduler
# Add: python main.py
```

## Monitoring

### Log Monitoring

Check logs regularly:
```bash
tail -f logs/statstrack.log
```

Set up log rotation:
```bash
# /etc/logrotate.d/statstracker
/path/to/StatsTracker/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
}
```

### Alert on Failures

Add to cron or systemd to email on failure:

```bash
# Cron with error notification
0 8 * * * cd /path/to/StatsTracker && /path/to/venv/bin/python main.py || echo "StatsTracker failed" | mail -s "StatsTracker Error" admin@example.com
```

### Health Checks

Create simple health check:
```python
# health_check.py
from src.player_database import PlayerDatabase

try:
    db = PlayerDatabase()
    # Test database connection
    db.get_all_players()
    print("OK")
except Exception as e:
    print(f"ERROR: {e}")
    exit(1)
```

Run periodically:
```bash
0 */6 * * * cd /path/to/StatsTracker && /path/to/venv/bin/python health_check.py
```

## Security Considerations

1. **Protect config files**
   ```bash
   chmod 600 config/config.yaml
   ```

2. **Use app passwords** not main account passwords

3. **Restrict database access**
   ```bash
   chmod 600 data/*.db
   ```

4. **Keep dependencies updated**
   ```bash
   pip list --outdated
   pip install --upgrade package-name
   ```

5. **Use HTTPS** for all web scraping

6. **Rotate credentials** periodically

## Backup Strategy

### Database Backups

```bash
# Backup script
#!/bin/bash
DATE=$(date +%Y%m%d)
cp data/stats.db backups/stats_$DATE.db
find backups/ -name "stats_*.db" -mtime +30 -delete
```

Add to cron:
```bash
0 2 * * * /path/to/backup_script.sh
```

### Configuration Backups

Keep config in private git repository or secure storage.

## Troubleshooting

### Emails Not Sending

1. Check SMTP credentials
2. Verify port (587 for TLS, 465 for SSL)
3. Check firewall rules
4. Test with `--test-email` flag
5. Check spam folder

### Database Locked

- Ensure only one instance is running
- Check file permissions
- Use connection pooling if multiple processes

### Website Scraping Fails

- Check if website structure changed
- Verify timeout settings
- Implement retry logic
- Add user agent headers

## Updating the System

```bash
# Pull latest changes
git pull origin main

# Update dependencies
pip install -r requirements.txt --upgrade

# Restart service (if using systemd)
sudo systemctl restart statstracker.service
```
