#!/usr/bin/env python3
"""
Manual test script for TFRR fetcher.

This script manually tests the TFRR fetcher by fetching real data from
the TFRR website for Haverford teams.
"""

import sys
sys.path.insert(0, '/Users/maxfieldma/CS/projects/StatsTracker')

from src.website_fetcher.tfrr_fetcher import TFRRFetcher, HAVERFORD_TEAMS


def test_mens_track():
    """Test fetching men's track team stats."""
    print("=" * 70)
    print("Testing Men's Track Team")
    print("=" * 70)
    print()

    fetcher = TFRRFetcher()
    team_code = HAVERFORD_TEAMS["mens_track"]

    print(f"Fetching stats for team code: {team_code}")
    result = fetcher.fetch_team_stats(team_code, "track")

    if result.success:
        data = result.data
        print(f"✓ Success!")
        print(f"  Team: {data['team_name']}")
        print(f"  Season: {data['season']}")
        print(f"  Athletes: {len(data['athletes'])}")
        print(f"  Event Categories: {len(data['event_categories'])}")
        print()
        print(f"  Events: {', '.join(data['event_categories'][:10])}...")
        print()

        # Show first few athletes
        print("  First 3 Athletes:")
        for athlete in data['athletes'][:3]:
            print(f"    - {athlete['name']} ({athlete.get('year', 'N/A')})")
            events_str = ', '.join([f"{event}: {result}" for event, result in list(athlete['events'].items())[:3]])
            print(f"      Events: {events_str}...")
        print()
    else:
        print(f"✗ Failed: {result.error}")
        print()


def test_womens_track():
    """Test fetching women's track team stats."""
    print("=" * 70)
    print("Testing Women's Track Team")
    print("=" * 70)
    print()

    fetcher = TFRRFetcher()
    team_code = HAVERFORD_TEAMS["womens_track"]

    print(f"Fetching stats for team code: {team_code}")
    result = fetcher.fetch_team_stats(team_code, "track")

    if result.success:
        data = result.data
        print(f"✓ Success!")
        print(f"  Team: {data['team_name']}")
        print(f"  Season: {data['season']}")
        print(f"  Athletes: {len(data['athletes'])}")
        print(f"  Event Categories: {len(data['event_categories'])}")
        print()
    else:
        print(f"✗ Failed: {result.error}")
        print()


def test_cross_country():
    """Test fetching cross country team stats."""
    print("=" * 70)
    print("Testing Cross Country Teams")
    print("=" * 70)
    print()

    fetcher = TFRRFetcher()

    # Men's cross country
    print("Men's Cross Country:")
    team_code = HAVERFORD_TEAMS["mens_cross_country"]
    result = fetcher.fetch_team_stats(team_code, "cross_country")

    if result.success:
        data = result.data
        print(f"  ✓ Success! {len(data['athletes'])} athletes")
    else:
        print(f"  ⚠️  {result.error}")
    print()

    # Women's cross country
    print("Women's Cross Country:")
    team_code = HAVERFORD_TEAMS["womens_cross_country"]
    result = fetcher.fetch_team_stats(team_code, "cross_country")

    if result.success:
        data = result.data
        print(f"  ✓ Success! {len(data['athletes'])} athletes")
    else:
        print(f"  ⚠️  {result.error}")
    print()


def run_all_tests():
    """Run all manual tests."""
    print("\n")
    print("#" * 70)
    print("# TFRR Fetcher Manual Test Suite")
    print("#" * 70)
    print()

    try:
        test_mens_track()
        test_womens_track()
        test_cross_country()

        print("=" * 70)
        print("✓ All tests completed!")
        print("=" * 70)
        print()
        print("Note: TFRR fetcher requires valid team codes and active seasons.")
        print("Some tests may fail if the season hasn't started yet.")
        print()

    except Exception as e:
        print(f"\n✗ Test suite failed with exception: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()
