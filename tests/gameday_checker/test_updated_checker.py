"""
Test the updated gameday checker with calendar endpoint
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

# Test dates that were previously working and failing
test_dates = [
    (date(2026, 1, 14), "January 14, 2026 (previously FAILED)"),
    (date(2026, 3, 5), "March 5, 2026 (previously WORKED)"),
    (date(2026, 4, 15), "April 15, 2026 (previously FAILED)"),
]

print("=" * 70)
print("Testing Updated GamedayChecker with Calendar Endpoint")
print("=" * 70)

for test_date, description in test_dates:
    print(f"\n{description}")
    print("-" * 70)

    games = checker.get_games_for_date(test_date)

    if games:
        print(f"PASS: Found {len(games)} games:")
        for game in games:
            home_away = "Home" if game.is_home_game else "Away"
            print(f"  - {game.team.sport}: vs {game.opponent}")
            print(f"    Time: {game.time}, Location: {home_away}")
    else:
        print("FAIL: No games found")

print("\n" + "=" * 70)
print("Summary")
print("=" * 70)
print("All dates that were previously failing should now work!")
