# TFRR Playwright Setup - Quick Start

The JavaScript bug has been fixed! The web page was showing "success" too early because it was treating the API start response as completion, instead of waiting for the actual SSE 'complete' message from the backend.

Now you need to install Playwright to test the fix.

## Step 1: Install Playwright

```bash
# Make sure you're in the StatsTracker directory
cd /Users/zero_legend/StatsTracker

# Install Playwright Python package (use quotes!)
pip install "playwright>=1.40.0"

# Install Chromium browser binaries
playwright install chromium
```

## Step 2: Verify Installation

```bash
# Run verification script
python verify_tfrr_setup.py
```

You should see all checks pass with ✅ marks.

## Step 3: Start the Server

```bash
# Start the web server
python web/app.py
```

The server should start without errors now.

## Step 4: Test the Button

1. Open your browser and go to: `http://localhost:5001/demo`
2. Scroll to **Section 3: Update TFRR Stats**
3. Click the **"🏃 Update TFRR Stats"** button
4. Click **OK** on the confirmation dialog

**What to expect:**

- Button text will update as each team is processed:
  - "⏳ Initializing Playwright..."
  - "⏳ Fetching Mens Track..."
  - "⏳ Mens Track (5/25 - 20%)" (shows progress)
  - "⏳ Exporting Mens Track CSV..."
  - (repeats for 4 teams: Mens Track, Womens Track, Mens XC, Womens XC)

- **Total time: 20-40 minutes** due to rate limiting

- When truly complete (after 20-40 min), you'll see:
  - "✅ TFRR stats updated successfully!"
  - Results box with statistics
  - List of CSV files created

## Step 5: Verify Results

After completion, check:

1. **CSV Files:**
   ```bash
   ls -la csv_exports/haverford_*
   ```
   You should see 4 new CSV files with today's date

2. **Database:**
   - Go to: `http://localhost:5001/browse`
   - Select a track/cross country sport
   - You should see athletes with their personal records

3. **Server Logs:**
   ```bash
   tail -f logs/statstrack.log
   ```
   Look for "TFRR update complete" message

## What Was Fixed

**The Problem:**
- JavaScript was showing success after 5 seconds when backend returned initial API response
- Backend continued running for 5 minutes in background
- No CSV files created, no data in database

**The Fix:**
- JavaScript now only checks if API call started successfully
- Waits for SSE 'complete' message type before showing success
- All completion logic (close EventSource, show results, list CSV files) only executes when backend actually finishes

**Code Change Location:**
- File: `web/templates/demo.html`
- Lines: 625-688 (in the `else if (data.type === 'complete')` handler)

## Troubleshooting

If you still see issues after following these steps:

1. **Make sure Playwright installed correctly:**
   ```bash
   python -c "import playwright; print('Playwright OK')"
   playwright --version
   ```

2. **Check browser installation:**
   ```bash
   playwright install --dry-run chromium
   ```

3. **Check server logs for errors:**
   ```bash
   tail -f logs/statstrack.log
   ```

4. **Open browser console (F12 → Console tab)** to see any JavaScript errors

## Expected Output

When working correctly:
- ✅ Button updates in real-time as teams are processed
- ✅ Takes 20-40 minutes to complete
- ✅ Creates 4 CSV files in `csv_exports/` directory
- ✅ Adds/updates athletes and PRs in database
- ✅ Shows summary with CSV file list when done
- ✅ Data visible in Stats Browser

The fix is complete - you just need to install Playwright and test!
