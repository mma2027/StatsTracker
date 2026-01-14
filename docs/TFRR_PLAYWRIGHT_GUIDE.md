# TFRR Playwright Fetcher Guide

This guide explains how to use the new **TFRRPlaywrightFetcher** to scrape personal records from TFRR for Haverford track and field teams.

## Why Playwright Instead of Selenium?

The new Playwright-based fetcher offers several advantages over the existing Selenium-based TFRR fetcher:

1. **Better Rate Limit Handling**: Smarter delays and exponential backoff
2. **Containerization Support**: Works better in Docker/containerized environments
3. **More Reliable**: Better page load detection and error handling
4. **Async Support**: Can be used in async workflows for better performance
5. **Easier Setup**: No need for ChromeDriver management

## Installation

### 1. Install Playwright

First, install the Playwright Python package:

```bash
pip install playwright>=1.40.0
```

Or install all requirements:

```bash
cd /Users/zero_legend/StatsTracker
pip install -r web/requirements.txt
```

### 2. Install Playwright Browsers

After installing the package, you need to install the browser binaries:

```bash
playwright install chromium
```

For containerized environments:

```bash
playwright install --with-deps chromium
```

## Usage

### Quick Start - Test Script

The easiest way to test the fetcher is using the provided test script:

```bash
# Test fetching a single team (Men's Track)
python tests_manual/test_tfrr_playwright.py --mode single-team

# Test fetching all Haverford teams (WARNING: Takes 15-30 minutes!)
python tests_manual/test_tfrr_playwright.py --mode all-teams
```

### Using in Your Code

#### Fetch Team Roster with Personal Records

```python
from src.website_fetcher import TFRRPlaywrightFetcher

# Initialize the fetcher
fetcher = TFRRPlaywrightFetcher(
    base_url="https://www.tfrrs.org",
    timeout=30,
    headless=True,  # Run in headless mode
    slow_mo=0,      # No artificial slowdown
)

# Fetch Haverford Men's Track team
result = fetcher.fetch_team_stats("PA_college_m_Haverford", "track")

if result.success:
    data = result.data
    print(f"Team: {data['name']}")
    print(f"Athletes: {len(data['roster'])}")

    # Access each athlete's data
    for athlete in data['roster']:
        print(f"\n{athlete['name']} (ID: {athlete['athlete_id']})")

        # Access personal records
        prs = athlete.get('personal_records', {})
        for event, mark in prs.items():
            print(f"  {event}: {mark}")
else:
    print(f"Error: {result.error}")
```

#### Fetch Single Athlete's Personal Records

```python
from src.website_fetcher import TFRRPlaywrightFetcher

fetcher = TFRRPlaywrightFetcher()

# Fetch a specific athlete by ID
result = fetcher.fetch_player_stats("1234567", "track")

if result.success:
    data = result.data
    print(f"Athlete: {data['name']}")
    print(f"Team: {data['team']}")

    prs = data.get('personal_records', {})
    for event, mark in prs.items():
        print(f"{event}: {mark}")
```

## Haverford Team Codes

The fetcher includes pre-configured codes for Haverford teams:

```python
from src.website_fetcher.tfrr_playwright_fetcher import HAVERFORD_TEAMS

# Available teams:
# - mens_track: "PA_college_m_Haverford"
# - womens_track: "PA_college_f_Haverford"
# - mens_cross_country: "PA_college_m_Haverford"
# - womens_cross_country: "PA_college_f_Haverford"
```

## Rate Limiting and Performance

The fetcher implements aggressive rate limiting to avoid being blocked by TFRR:

- **Base delay**: 4-8 seconds between requests (randomized)
- **Extended breaks**: Every 8-12 requests, takes a 20-40 second break
- **Exponential backoff**: On errors (403, 429), increases wait time exponentially
- **Request tracking**: Monitors consecutive errors and adjusts behavior

### Expected Timing

- **Single team**: 5-15 minutes (depending on roster size)
- **All 4 Haverford teams**: 20-60 minutes
- **Single athlete**: ~10 seconds

## Configuration Options

```python
fetcher = TFRRPlaywrightFetcher(
    base_url="https://www.tfrrs.org",  # TFRR base URL
    timeout=30,                         # Page load timeout in seconds
    headless=True,                      # Run browser in headless mode
    slow_mo=0,                          # Milliseconds to slow down operations
)
```

### Debugging Options

For debugging, you can:

1. **See the browser**: Set `headless=False`
2. **Slow down actions**: Set `slow_mo=500` (500ms between actions)
3. **Enable debug logging**:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Docker/Container Support

To use Playwright in a Docker container:

### Dockerfile

```dockerfile
FROM python:3.11-slim

# Install Playwright dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Install Playwright browsers
RUN playwright install --with-deps chromium
```

### Docker Compose

```yaml
services:
  stats-tracker:
    build: .
    environment:
      - PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
    volumes:
      - playwright-cache:/ms-playwright

volumes:
  playwright-cache:
```

## Integration with Web App

To integrate with the web app's "Update All Stats" workflow:

### 1. Update `web/app.py`

Replace the TFRR section in the `api_update_stats` function:

```python
# In web/app.py, around line 597-691

# Update TFRR stats with Playwright
send_progress(session_id, {'type': 'info', 'message': 'Starting TFRR stats update...'})

from src.website_fetcher import TFRRPlaywrightFetcher
tfrr_fetcher = TFRRPlaywrightFetcher(headless=True)

for sport_key, team_code in HAVERFORD_TEAMS.items():
    sport_display = sport_key.replace('_', ' ').title()
    send_progress(session_id, {'type': 'fetch', 'message': f'Fetching TFRR {sport_display}...'})

    try:
        sport_type = "cross_country" if "cross_country" in sport_key else "track"
        result = tfrr_fetcher.fetch_team_stats(team_code, sport_type)

        if result.success and result.data:
            roster = result.data.get('roster', [])

            for idx, athlete in enumerate(roster):
                athlete_name = athlete.get('name')
                athlete_id_tfrr = athlete.get('athlete_id')

                if not athlete_name or not athlete_id_tfrr:
                    continue

                # Progress updates...
                if idx % 10 == 0:
                    send_progress(session_id, {
                        'type': 'fetch',
                        'message': f'Processing {sport_display} athlete {idx+1}/{len(roster)}...'
                    })

                player_id = generate_player_id(athlete_name, sport_key)

                # Check if player exists
                existing_player = database.get_player(player_id)
                if not existing_player:
                    player = Player(
                        player_id=player_id,
                        name=athlete_name,
                        sport=sport_key,
                        team='Haverford',
                        position=None,
                        year=athlete.get('year'),
                        active=True
                    )
                    database.add_player(player)

                # Add PRs to database
                prs = athlete.get('personal_records', {})
                for event_name, pr_value in prs.items():
                    if pr_value:
                        stat_entry = StatEntry(
                            player_id=player_id,
                            stat_name=event_name,
                            stat_value=str(pr_value),
                            season=season,
                            date_recorded=datetime.now()
                        )
                        database.add_stat(stat_entry)

            logger.info(f'Updated {sport_key}: {len(roster)} athletes')
        else:
            send_progress(session_id, {
                'type': 'warning',
                'message': f'Error fetching {sport_display}: {result.error}'
            })

    except Exception as e:
        logger.error(f'Error fetching {sport_key}: {e}')
        send_progress(session_id, {
            'type': 'warning',
            'message': f'Error fetching {sport_display}: {str(e)}'
        })
```

## Troubleshooting

### Issue: "Playwright not found"

**Solution**: Install Playwright browsers:
```bash
playwright install chromium
```

### Issue: "TimeoutError" or pages loading slowly

**Solution**: Increase timeout:
```python
fetcher = TFRRPlaywrightFetcher(timeout=60)  # 60 seconds
```

### Issue: Getting blocked (403 errors)

**Solution**: The fetcher should handle this automatically with exponential backoff. If persistent:
1. Check if you're making too many concurrent requests
2. Increase delays manually by modifying `_smart_delay()` method
3. Run during off-peak hours

### Issue: "Browser not found" in Docker

**Solution**: Install with dependencies:
```bash
playwright install --with-deps chromium
```

### Issue: Memory issues in container

**Solution**: Add shared memory to Docker:
```yaml
services:
  app:
    shm_size: '2gb'
```

## Comparison with Old Fetcher

| Feature | Old (Selenium) | New (Playwright) |
|---------|---------------|------------------|
| Setup | ChromeDriver needed | Simpler - just install browsers |
| Rate Limiting | Basic | Advanced with exponential backoff |
| Container Support | Difficult | Excellent |
| Async Support | No | Yes |
| Error Handling | Basic | Comprehensive |
| Browser Management | Manual | Automatic |
| Speed | Similar | Similar |

## Next Steps

1. **Test the fetcher**: Run the test script to verify it works
2. **Install Playwright**: Follow installation instructions
3. **Integrate with web app**: Update `web/app.py` to use new fetcher
4. **Monitor performance**: Check logs for rate limiting issues
5. **Adjust delays**: Tune rate limiting parameters if needed

## Support

For issues or questions:
- Check logs for detailed error messages
- Use debug mode: `headless=False` and `slow_mo=500`
- Review TFRR website structure (it may change over time)
