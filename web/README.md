# StatsTracker Web Interface

A Flask-based web application for browsing CSV statistics and testing the StatsTracker system.

## Features

### 1. CSV Browser
- Browse all NCAA and TFRR CSV files
- View file metadata (size, modified date)
- Open and view CSV contents in a table format

### 2. Demo/Testing Panel
- **Update Stats Button**: Manually trigger NCAA stats update
- **Gameday Simulator**:
  - Pick any date with a date picker
  - See what games are scheduled
  - Check which players have milestone proximities
  - Preview the email that would be sent
  - Send actual test email

### 3. Dashboard
- System status overview
- Quick links to external resources

## Installation

1. **Install Flask** (if not already installed):
   ```bash
   pip install flask
   ```

2. **Run the web server**:
   ```bash
   cd /Users/maxfieldma/CS/projects/StatsTracker
   python web/app.py
   ```

3. **Access the interface**:
   - Open browser to http://localhost:5001

## Usage

### Starting the Server

```bash
# From project root
python web/app.py

# Or make it executable
chmod +x web/app.py
./web/app.py
```

The server will start on http://0.0.0.0:5001 (accessible from any network interface).

### CSV Browser

1. Click "CSV Browser" in navigation
2. Browse NCAA or TFRR files
3. Click "View" to see CSV contents in a table

### Demo Panel

1. Click "Demo/Testing" in navigation
2. **Update Stats**:
   - Click "Update Stats Now"
   - Wait 5-10 minutes for completion
   - New CSV files will be generated

3. **Simulate Gameday**:
   - Select a date using the date picker
   - Click "Simulate Gameday"
   - View results: games, milestones, email preview
   - Optionally click "Send Test Email" to actually send

## API Endpoints

### POST /api/update-stats
Triggers manual stats update from NCAA.

**Request:**
```bash
curl -X POST http://localhost:5001/api/update-stats
```

**Response:**
```json
{
  "success": true,
  "message": "Stats updated successfully",
  "timestamp": "2026-01-13T..."
}
```

### POST /api/simulate-gameday
Simulates gameday checker for a specific date.

**Request:**
```bash
curl -X POST http://localhost:5001/api/simulate-gameday \
  -H "Content-Type: application/json" \
  -d '{"date": "2026-02-15"}'
```

**Response:**
```json
{
  "success": true,
  "date": "2026-02-15",
  "games": [...],
  "games_count": 2,
  "proximities": [...],
  "proximities_count": 1,
  "sports_with_games": ["mens_basketball"],
  "email_subject": "...",
  "email_html": "..."
}
```

### POST /api/send-test-email
Sends actual test email for a simulated date.

**Request:**
```bash
curl -X POST http://localhost:5001/api/send-test-email \
  -H "Content-Type: application/json" \
  -d '{"date": "2026-02-15"}'
```

**Response:**
```json
{
  "success": true,
  "message": "Email sent successfully",
  "games_count": 2,
  "proximities_count": 1
}
```

## File Structure

```
web/
├── app.py                 # Flask application
├── README.md             # This file
├── templates/            # HTML templates
│   ├── base.html        # Base template with nav
│   ├── index.html       # Home page
│   ├── csv_browser.html # CSV file browser
│   ├── csv_viewer.html  # CSV file viewer
│   └── demo.html        # Demo/testing panel
├── static/              # Static assets
│   ├── css/
│   │   └── style.css   # Stylesheet
│   └── js/
│       └── main.js     # JavaScript
```

## Production Deployment

For production use, consider using a production WSGI server like Gunicorn:

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5001 web.app:app
```

Or with systemd service:

```ini
[Unit]
Description=StatsTracker Web Interface
After=network.target

[Service]
User=maxfieldma
WorkingDirectory=/Users/maxfieldma/CS/projects/StatsTracker
ExecStart=/path/to/venv/bin/gunicorn -w 4 -b 0.0.0.0:5001 web.app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

## Security Notes

1. **Debug Mode**: The app runs in debug mode by default for development. For production, set `debug=False` in `app.py`.

2. **Secret Key**: Change the `SECRET_KEY` in production.

3. **Access Control**: The interface has no authentication. For production, add authentication middleware.

4. **Email Credentials**: Ensure `config/config.yaml` is not publicly accessible.

## Troubleshooting

### Flask Not Found
```bash
pip install flask
```

### Port Already in Use
Change the port in `app.py`:
```python
app.run(debug=True, host='0.0.0.0', port=5002)
```

### Database Not Found
Ensure `data/stats.db` exists:
```bash
python main.py --update-stats
```

### CSV Files Not Showing
Generate CSV files first:
```bash
python scripts/fetch_ncaa_seasonal_and_career.py
```

## Future Enhancements

- [ ] Add authentication (login system)
- [ ] Real-time progress updates for stats fetch (WebSockets)
- [ ] Database statistics page (player count, stat entries)
- [ ] Download CSV files directly from browser
- [ ] Filtering and searching in CSV viewer
- [ ] Historical gameday simulations (batch test multiple dates)
- [ ] Email template editor
- [ ] Milestone threshold configuration UI

---

**Last Updated:** January 13, 2026
**Version:** 1.0
