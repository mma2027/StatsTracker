"""
Test gameday checker with today's date
"""

import sys
import logging
from pathlib import Path
from datetime import date

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from gameday_checker.checker import GamedayChecker  # noqa: E402

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")

checker = GamedayChecker(schedule_url="https://haverfordathletics.com")

today = date.today()

print("=" * 70)
print(f"Testing with TODAY'S date: {today}")
print(f"Season parameter: {checker._get_season_param(today)}")
print("=" * 70)

games = checker.get_games_for_today()

print(f"\nResult: Found {len(games)} games today")

if games:
    print("\nGames today:")
    for game in games:
        print(f"  - {game.team.sport}: vs {game.opponent}")
        print(f"    Time: {game.time}")
        print(f"    Location: {game.location} ({'Home' if game.is_home_game else 'Away'})")
else:
    print("\nNo games scheduled for today")

# Also test validate_scraping to see what data is available
print("\n" + "=" * 70)
print("Checking what's available in baseball schedule")
print("=" * 70)

diagnostics = checker.validate_scraping("baseball")
print(f"Total games: {diagnostics.get('total_games')}")
date_range = diagnostics.get("date_range")
if date_range:
    print(f"Date range: {date_range['min']} to {date_range['max']}")
    print(f"\nToday ({today}) is in range: {date_range['min'] <= str(today) <= date_range['max']}")
