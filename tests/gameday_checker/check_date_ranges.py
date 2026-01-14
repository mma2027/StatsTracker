"""
Check what date ranges are actually available in schedule pages
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from gameday_checker.checker import GamedayChecker  # noqa: E402

checker = GamedayChecker(schedule_url="https://haverfordathletics.com")

# Test several sports
sports_to_check = ["baseball", "mens-basketball", "mens-lacrosse", "softball", "wten"]

print("=" * 70)
print("Checking date ranges for different sports")
print("=" * 70)

for sport in sports_to_check:
    print(f"\n{sport}:")
    diagnostics = checker.validate_scraping(sport)

    if "error" in diagnostics:
        print(f"  Error: {diagnostics['error']}")
    else:
        print(f"  Total games: {diagnostics.get('total_games', 0)}")
        date_range = diagnostics.get("date_range")
        if date_range:
            print(f"  Date range: {date_range['min']} to {date_range['max']}")
        else:
            print("  No date range (no games)")

        # Show all sample dates
        samples = diagnostics.get("sample_dates", [])
        if samples:
            print("  Sample dates:")
            for sample in samples:
                print(f"    - {sample['date']}: vs {sample['opponent']}")
