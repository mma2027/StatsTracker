#!/usr/bin/env python3
"""
Verify TFRR Playwright Setup

This script checks if all requirements for TFRR fetching are met.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("=" * 60)
print("TFRR Playwright Setup Verification")
print("=" * 60)

# Check 1: Playwright module
print("\n1. Checking Playwright installation...")
try:
    import playwright
    try:
        version = playwright.__version__
    except AttributeError:
        # Try alternative way to get version
        try:
            from playwright import __version__ as version
        except ImportError:
            version = "installed (version unknown)"
    print(f"   ✅ Playwright module found ({version})")
except ImportError:
    print("   ❌ Playwright module NOT found")
    print("   → Install with: pip install playwright>=1.40.0")
    sys.exit(1)

# Check 2: Playwright async API
print("\n2. Checking Playwright async API...")
try:
    from playwright.async_api import async_playwright
    print("   ✅ Playwright async API available")
except ImportError as e:
    print(f"   ❌ Playwright async API NOT available: {e}")
    sys.exit(1)

# Check 3: TFRR Playwright Fetcher import
print("\n3. Checking TFRR Playwright Fetcher...")
try:
    from src.website_fetcher.tfrr_playwright_fetcher import HAVERFORD_TEAMS  # noqa: F401
    print("   ✅ TFRRPlaywrightFetcher can be imported")
    print(f"   → Teams configured: {list(HAVERFORD_TEAMS.keys())}")
except ImportError as e:
    print(f"   ❌ TFRRPlaywrightFetcher import failed: {e}")
    sys.exit(1)

# Check 4: Chromium browser installation
print("\n4. Checking Chromium browser...")
try:
    import asyncio
    from playwright.async_api import async_playwright  # noqa: F811

    async def check_browser():
        try:
            playwright = await async_playwright().start()
            browser = await playwright.chromium.launch(headless=True)
            await browser.close()
            await playwright.stop()
            return True
        except Exception as e:
            return str(e)

    result = asyncio.run(check_browser())
    if result is True:
        print("   ✅ Chromium browser is installed and working")
    else:
        print(f"   ❌ Chromium browser check failed: {result}")
        print("   → Install with: playwright install chromium")
        sys.exit(1)
except Exception as e:
    print(f"   ❌ Browser check failed: {e}")
    print("   → Install with: playwright install chromium")
    sys.exit(1)

# Check 5: CSV export directory
print("\n5. Checking CSV export directory...")
csv_dir = project_root / "csv_exports"
if csv_dir.exists():
    print(f"   ✅ CSV export directory exists: {csv_dir}")
    print(f"   → Current files: {len(list(csv_dir.glob('*.csv')))} CSV files")
else:
    print(f"   ⚠️  CSV export directory does not exist (will be created): {csv_dir}")
    csv_dir.mkdir(parents=True, exist_ok=True)
    print(f"   ✅ Created directory: {csv_dir}")

# Check 6: Database
print("\n6. Checking database...")
db_path = project_root / "data" / "stats.db"
if db_path.exists():
    print(f"   ✅ Database exists: {db_path}")
else:
    print(f"   ⚠️  Database does not exist (will be created): {db_path}")

print("\n" + "=" * 60)
print("✅ ALL CHECKS PASSED!")
print("=" * 60)
print("\nYou're ready to use the TFRR Playwright fetcher!")
print("\nNext steps:")
print("1. Start web server: python web/app.py")
print("2. Navigate to: http://localhost:5001/demo")
print("3. Click 'Update TFRR Stats' button")
print("=" * 60)
