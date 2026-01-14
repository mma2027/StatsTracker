#!/bin/bash
# Quick verification script for daily automation implementation

echo "=========================================="
echo "Daily Automation Implementation Checker"
echo "=========================================="
echo ""

cd /Users/maxfieldma/CS/projects/StatsTracker

# Check 1: Core files exist
echo "[1/6] Checking core files..."
if [ -f "main.py" ] && [ -f "run_daily_check.sh" ]; then
    echo "  ✓ Core files exist"
else
    echo "  ✗ Missing core files"
    exit 1
fi

# Check 2: Documentation exists
echo "[2/6] Checking documentation..."
if [ -f "docs/CRON_SETUP.md" ] && [ -f "docs/DAILY_AUTOMATION_README.md" ]; then
    echo "  ✓ Documentation exists"
else
    echo "  ✗ Missing documentation"
    exit 1
fi

# Check 3: Wrapper script is executable
echo "[3/6] Checking script permissions..."
if [ -x "run_daily_check.sh" ]; then
    echo "  ✓ Wrapper script is executable"
else
    echo "  ✗ Wrapper script not executable (run: chmod +x run_daily_check.sh)"
    exit 1
fi

# Check 4: Virtual environment exists
echo "[4/6] Checking virtual environment..."
if [ -d "venv" ] && [ -f "venv/bin/activate" ]; then
    echo "  ✓ Virtual environment exists"
else
    echo "  ✗ Virtual environment not found"
    exit 1
fi

# Check 5: Config file exists
echo "[5/6] Checking configuration..."
if [ -f "config/config.yaml" ]; then
    echo "  ✓ Config file exists"
    
    # Check if it's still the example file
    if grep -q "your-email@example.com" config/config.yaml; then
        echo "  ⚠  WARNING: Config file appears to be unconfigured (contains example values)"
        echo "     Please edit config/config.yaml with your actual email settings"
    else
        echo "  ✓ Config file appears to be customized"
    fi
else
    echo "  ⚠  Config file not found"
    echo "     Copy config/config.example.yaml to config/config.yaml"
fi

# Check 6: Key code sections
echo "[6/6] Verifying implementation..."

# Check main.py has always-update logic
if grep -q "Fetching latest stats for all teams" main.py; then
    echo "  ✓ Stats always-update logic present"
else
    echo "  ✗ Missing stats update logic"
fi

# Check templates.py has empty-day handling
if grep -q "No Games or Milestone Alerts Today" src/email_notifier/templates.py; then
    echo "  ✓ Empty-day email template present"
else
    echo "  ✗ Missing empty-day template"
fi

# Check main.py has sport filtering
if grep -q "sports_with_games_today" main.py; then
    echo "  ✓ Sport filtering logic present"
else
    echo "  ✗ Missing sport filtering"
fi

echo ""
echo "=========================================="
echo "Verification Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Configure email settings in config/config.yaml"
echo "2. Test the workflow: python main.py --test-email"
echo "3. Test stats update: python main.py --update-stats"
echo "4. Test full workflow: python main.py"
echo "5. Set up cron job: crontab -e"
echo "   Add: 0 8 * * * /Users/maxfieldma/CS/projects/StatsTracker/run_daily_check.sh"
echo ""
