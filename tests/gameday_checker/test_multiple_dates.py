"""
Test multiple dates to see what's available
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from gameday_checker.checker import GamedayChecker
from datetime import date
import logging

# Set up logging to see what's happening
logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")

checker = GamedayChecker(schedule_url="https://haverfordathletics.com")

# Test various dates
test_dates = [
    date(2026, 1, 15),  # January
    date(2026, 2, 15),  # February
    date(2026, 3, 5),  # March (known to work)
    date(2026, 4, 15),  # April
]

print("=" * 70)
print("Testing multiple dates")
print("=" * 70)

for test_date in test_dates:
    print(f"\n{'='*70}")
    print(f"Testing: {test_date}")
    print(f"Season param: {checker._get_season_param(test_date)}")
    print("=" * 70)

    games = checker.get_games_for_date(test_date)
    print(f"Result: Found {len(games)} games")

    for game in games:
        print(f"  - {game.team.sport}: vs {game.opponent}")

print("\n" + "=" * 70)
print("Running diagnostic on baseball schedule")
print("=" * 70)

diagnostics = checker.validate_scraping("baseball")
print(f"Total games in baseball schedule: {diagnostics.get('total_games')}")
print(f"Date range: {diagnostics.get('date_range')}")
print(f"\nSample dates:")
for sample in diagnostics.get("sample_dates", []):
    print(f"  {sample['date']}: vs {sample['opponent']}")
