"""
Comprehensive test of gameday checker across multiple months
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from gameday_checker.checker import GamedayChecker  # noqa: E402
from datetime import date  # noqa: E402
import logging  # noqa: E402

# Set up logging
logging.basicConfig(level=logging.WARNING)

checker = GamedayChecker(schedule_url="https://haverfordathletics.com")

print("=" * 70)
print("COMPREHENSIVE GAMEDAY CHECKER TEST")
print("=" * 70)

test_dates = [
    (date(2026, 1, 12), "Today (January 12, 2026)", 0),
    (date(2026, 1, 14), "January 14, 2026", 2),
    (date(2026, 2, 22), "February 22, 2026", ">=1"),
    (date(2026, 3, 5), "March 5, 2026", 1),
    (date(2026, 3, 9), "March 9, 2026", 2),
    (date(2026, 4, 15), "April 15, 2026", ">=2"),
]

results = []
for test_date, description, expected in test_dates:
    games = checker.get_games_for_date(test_date)
    count = len(games)

    if isinstance(expected, int):
        passed = count == expected
        status = "PASS" if passed else "FAIL"
        expected_str = str(expected)
    else:  # ">=N" format
        min_count = int(expected.replace(">=", ""))
        passed = count >= min_count
        status = "PASS" if passed else "FAIL"
        expected_str = expected

    results.append((description, count, expected_str, status))

    print(f"\n{description}")
    print(f"  Expected: {expected_str} games, Found: {count} games - {status}")  # noqa: F541

    if games and count <= 3:
        for game in games:
            print(f"    - {game.team.sport}: vs {game.opponent} at {game.time}")

print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)

for desc, count, expected, status in results:
    symbol = "[PASS]" if status == "PASS" else "[FAIL]"
    print(f"{symbol} {desc}: {count} games (expected {expected})")

all_passed = all(status == "PASS" for _, _, _, status in results)
print("\n" + "=" * 70)
if all_passed:
    print("ALL TESTS PASSED!")
else:
    print("SOME TESTS FAILED")
print("=" * 70)
