#!/usr/bin/env python3
"""
Test fetching a single athlete's PRs from TFRR.
"""

import sys
sys.path.insert(0, '/Users/maxfieldma/CS/projects/StatsTracker')  # noqa: E402

from src.website_fetcher.tfrr_fetcher import TFRRFetcher  # noqa: E402


def test_single_athlete():
    """Test fetching a single athlete's PRs."""
    print("Testing Single Athlete PR Fetch")
    print("=" * 70)
    print()

    fetcher = TFRRFetcher()

    # Use a sample athlete ID from TFRR
    # This is just a test ID - replace with actual Haverford athlete ID
    athlete_id = "9620803"  # Example ID

    print(f"Fetching PRs for athlete ID: {athlete_id}")
    result = fetcher.fetch_player_stats(athlete_id, "track")

    if result.success:
        data = result.data
        print("\n✓ Success!")
        print(f"  Name: {data.get('name', 'Unknown')}")
        print(f"  Year: {data.get('year', 'N/A')}")
        print(f"  Sport: {data.get('sport')}")
        print("\n  Personal Records:")

        if data.get('events'):
            for event, result_time in data['events'].items():
                print(f"    {event}: {result_time}")
        else:
            print("    (No PRs found)")
    else:
        print(f"\n✗ Failed: {result.error}")


if __name__ == "__main__":
    test_single_athlete()
