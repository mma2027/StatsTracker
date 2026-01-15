#!/usr/bin/env python3
"""
Manual test script for NCAAFetcher.

This script tests the NCAA fetcher implementation by fetching
real stats from Haverford Men's Basketball team.
"""

import sys
sys.path.insert(0, '/Users/maxfieldma/CS/projects/StatsTracker')  # noqa: E402

from src.website_fetcher.ncaa_fetcher import NCAAFetcher, HAVERFORD_TEAMS  # noqa: E402


def test_mens_basketball():
    """Test fetching Men's Basketball stats."""
    print("=" * 70)
    print("Testing NCAA Fetcher - Haverford Men's Basketball")
    print("=" * 70)

    team_id = str(HAVERFORD_TEAMS["mens_basketball"])
    print(f"\nTeam ID: {team_id}")
    print(f"URL: https://stats.ncaa.org/teams/{team_id}/season_to_date_stats")

    print("\nInitializing NCAAFetcher...")
    fetcher = NCAAFetcher()

    print("Fetching team stats (this may take 10-15 seconds)...")
    result = fetcher.fetch_team_stats(team_id, "basketball")

    print("\n" + "-" * 70)
    print("RESULTS:")
    print("-" * 70)

    if result.success:
        data = result.data
        print("✓ SUCCESS!")
        print(f"\nSeason: {data['season']}")
        print(f"Sport: {data['sport']}")
        print(f"Team ID: {data['team_id']}")
        print(f"Number of players: {len(data['players'])}")
        print(f"Stat categories ({len(data['stat_categories'])}): {', '.join(data['stat_categories'][:10])}...")

        print("=" * 70)
        print("FIRST 3 PLAYERS:")
        print("=" * 70)

        for i, player in enumerate(data['players'][:3]):
            print(f"\n{i+1}. {player['name']}")
            print(f"   Stats: {list(player['stats'].items())[:5]}...")

        return True
    else:
        print("✗ FAILED!")
        print(f"Error: {result.error}")
        return False


if __name__ == "__main__":
    try:
        success = test_mens_basketball()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Exception occurred: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
