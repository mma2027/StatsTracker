# TFRR Stats Update Button - Quick Start Guide

This guide explains how to use the new TFRR Stats Update button in the web interface.

## What It Does

The "Update TFRR Stats" button fetches personal records for all Haverford track & field and cross country athletes from TFRR using the new Playwright-based fetcher.

### What Gets Updated

- **Men's Track & Field** roster and PRs
- **Women's Track & Field** roster and PRs
- **Men's Cross Country** roster and PRs
- **Women's Cross Country** roster and PRs

For each athlete, it fetches:
- Name and TFRR athlete ID
- All personal records (100m, 200m, 400m, 800m, 1500m, 5K, etc.)
- Both indoor and outdoor track records
- Cross country best times

## How to Use

### 1. Navigate to Demo Page

Open your web browser and go to:
```
http://localhost:5001/demo
```

(Or your server's address if running remotely)

### 2. Find the TFRR Section

Scroll to **Section 3: Update TFRR Stats (Track & Field / Cross Country)**

You'll see:
- A warning box explaining the process takes 20-40 minutes
- The "🏃 Update TFRR Stats" button

### 3. Click the Button

1. Click the **"🏃 Update TFRR Stats"** button
2. You'll see a confirmation dialog: **"This will take 20-40 minutes to complete due to rate limiting. Continue?"**
3. Click **OK** to proceed (or **Cancel** to abort)

### 4. Monitor Progress

Once started, you'll see:

**Progress Box** showing real-time updates:
- "Initializing TFRR Playwright fetcher..."
- "Fetching Mens Track roster and PRs..."
- "Processing 25 Mens Track athletes..."
- "Processing Mens Track athlete 5/25: John Doe"
- "✅ Mens Track: 25 athletes, 180 PRs added"
- ...and so on for each team

**Status Messages:**
- Blue info messages for progress updates
- Green success messages when teams complete
- Yellow warning messages if any issues occur
- Red error messages if something fails

### 5. View Results

When complete, you'll see:

**Results Summary:**
- Teams Processed: 4
- Athletes Added: 85
- Athletes Updated: 12
- PRs Added: 642

**Button Updates:**
- Button shows "✅ TFRR Stats Updated" for 5 seconds
- Then resets to "🏃 Update TFRR Stats"

## Expected Timeline

| Team | Roster Size | Estimated Time |
|------|-------------|----------------|
| Men's Track | ~25 athletes | 8-12 minutes |
| Women's Track | ~25 athletes | 8-12 minutes |
| Men's Cross Country | ~15 athletes | 5-8 minutes |
| Women's Cross Country | ~15 athletes | 5-8 minutes |
| **Total** | **~80 athletes** | **20-40 minutes** |

*Times vary based on TFRR server response and rate limiting*

## What Happens During the Process

### For Each Team:

1. **Fetch Roster** - Gets list of all athletes on the team
2. **Smart Delays** - Waits 4-8 seconds between requests
3. **Fetch Each Athlete** - Gets personal records for each athlete
4. **Extended Breaks** - Takes 20-40 second break every 8-12 requests
5. **Update Database** - Saves all data to the StatsTracker database

### Rate Limiting

The fetcher implements aggressive rate limiting to avoid being blocked:

- **Base delay**: 4-8 seconds between requests
- **Random variation**: Makes delays unpredictable
- **Extended breaks**: Longer pauses every 8-12 requests
- **Exponential backoff**: If errors occur, wait time increases
- **Human-like behavior**: Randomized timing mimics manual browsing

## Viewing the Data

After the update completes, you can view the data:

### 1. Stats Browser

Navigate to: **Stats Browser** → Select a track/cross country sport

You'll see all athletes with their personal records organized by event.

### 2. Milestone Detection

The milestone detector can now use TFRR PRs to alert when athletes are close to breaking records or hitting time goals.

### 3. Database Query

The data is stored in the database at `data/stats.db` and can be queried directly:

```sql
SELECT * FROM players WHERE sport LIKE '%track%' OR sport LIKE '%cross_country%';
SELECT * FROM stats WHERE player_id IN (SELECT player_id FROM players WHERE sport = 'mens_track');
```

## Troubleshooting

### Button is Disabled

**Issue**: Button stays grayed out and won't click

**Solutions**:
1. Wait for any ongoing update to complete
2. Refresh the page
3. Check browser console for JavaScript errors (F12 → Console)

### Update Takes Too Long

**Issue**: Process seems stuck or frozen

**What's Normal**:
- Long pauses (20-40 seconds) are expected - this is the extended break
- Some athletes may take longer to fetch than others
- Progress updates come every 5 athletes, not continuously

**When to Worry**:
- No progress updates for 5+ minutes
- Browser shows "Page unresponsive"
- Error messages appear

**Solutions**:
1. Don't refresh the page - let it complete
2. Check server logs: `tail -f logs/statstrack.log`
3. If truly stuck, refresh page and try again

### 403 or 429 Errors

**Issue**: Seeing "rate limited" or "403 Forbidden" warnings

**What's Happening**: TFRR's rate limiting is kicking in

**Solutions**:
1. Let the fetcher handle it automatically (it has exponential backoff)
2. If it fails completely, wait 30-60 minutes before trying again
3. Consider running during off-peak hours (late evening or early morning)

### Playwright Not Installed

**Issue**: Error message: "playwright not found" or "No module named 'playwright'"

**Solutions**:
```bash
# Install Playwright
pip install playwright>=1.40.0

# Install browser binaries
playwright install chromium
```

### Missing Athletes or PRs

**Issue**: Some expected athletes or PRs are missing

**Possible Reasons**:
1. Athlete not listed on TFRR roster page
2. TFRR page structure changed (scraper needs updating)
3. Athlete has no PRs recorded on TFRR
4. Fetch failed for that specific athlete (check warnings)

**Solutions**:
1. Check TFRR website directly to confirm data exists
2. Look for warning messages in the progress log
3. Check server logs for detailed error messages
4. Try updating again - transient network issues may have caused it

## Advanced Usage

### Background Updates

You can close the browser tab and the update will continue running on the server. To check status:

1. Return to the demo page
2. Look at server logs: `tail -f logs/statstrack.log`
3. Check database for new entries

### Multiple Concurrent Updates

**DO NOT** run multiple TFRR updates simultaneously:
- Only one update should run at a time
- Running multiple will trigger aggressive rate limiting
- May result in temporary IP blocking from TFRR

### Scheduling Automatic Updates

To schedule automatic TFRR updates (e.g., weekly):

**Option 1: Cron Job** (Linux/Mac)
```bash
# Edit crontab
crontab -e

# Add line to run every Sunday at 2 AM
0 2 * * 0 cd /path/to/StatsTracker && python -c "from src.website_fetcher import TFRRPlaywrightFetcher; ..."
```

**Option 2: Python Script**
Create a scheduled task that calls the API endpoint programmatically.

**Note**: For scheduled updates, consider using a dedicated script rather than the web button.

## Data Structure

### Database Tables

**Players Table:**
```
player_id: "john_doe_mens_track"
name: "John Doe"
sport: "mens_track"
team: "Haverford"
active: true
```

**Stats Table:**
```
player_id: "john_doe_mens_track"
stat_name: "100m"
stat_value: "11.23"
season: "2024-25"
date_recorded: 2026-01-14 15:30:00
```

### Events Tracked

**Sprint Events:**
- 55m, 60m, 100m, 200m, 400m

**Middle Distance:**
- 600m, 800m, 1000m, 1500m, Mile

**Distance:**
- 3000m, 5000m, 10000m

**Hurdles:**
- 60mH, 100mH, 110mH, 400mH

**Field Events:**
- High Jump, Pole Vault, Long Jump, Triple Jump
- Shot Put, Discus, Hammer, Javelin

**Relays:**
- 4x100m, 4x400m, 4x800m, DMR, etc.

**Cross Country:**
- 5K, 6K, 8K, 10K

## Best Practices

1. **Update Regularly**: Run once per week during the season
2. **Off-Peak Hours**: Update during low-traffic times (late evening)
3. **Monitor Progress**: Keep the page open to see warnings
4. **Check Results**: Verify data in Stats Browser after completion
5. **Avoid Concurrent Updates**: Only run one update at a time
6. **Be Patient**: Don't interrupt the process - rate limiting is intentional

## Support

If you encounter issues:

1. **Check server logs**: `logs/statstrack.log`
2. **Browser console**: F12 → Console tab
3. **Network tab**: F12 → Network tab (for failed requests)
4. **Review this guide**: Most issues are covered above
5. **TFRR status**: Check if TFRR website is accessible

## Technical Details

For developers who want to understand the implementation:

- **Backend**: [web/app.py](../web/app.py) - `api_update_tfrr_stats()` function
- **Frontend**: [web/templates/demo.html](../web/templates/demo.html) - JavaScript event handler
- **Fetcher**: [src/website_fetcher/tfrr_playwright_fetcher.py](../src/website_fetcher/tfrr_playwright_fetcher.py)
- **Progress Streaming**: Server-Sent Events (SSE) via `/api/progress/{session_id}`

## Comparison with Old Method

| Feature | Old (Selenium) | New (Playwright) |
|---------|---------------|------------------|
| Setup | ChromeDriver required | Just install browsers |
| Rate Limiting | Basic | Advanced with backoff |
| Progress Tracking | None | Real-time SSE updates |
| Error Handling | Basic | Comprehensive |
| Container Support | Difficult | Excellent |
| Speed | ~30 min | ~30 min (similar) |
| Reliability | Medium | High |

The new method is more reliable and provides better feedback, but takes similar time due to necessary rate limiting.
