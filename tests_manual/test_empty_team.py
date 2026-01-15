#!/usr/bin/env python3
"""
Test what the fetcher returns for a team with no stats yet.
"""

import sys
sys.path.insert(0, '/Users/maxfieldma/CS/projects/StatsTracker')  # noqa: E402
import json  # noqa: E402

from src.website_fetcher.ncaa_fetcher import NCAAFetcher, HAVERFORD_TEAMS  # noqa: E402


def test_empty_team():
    """Test fetching a team with no stats (baseball - season hasn't started)."""
    print("=" * 70)
    print("Testing Empty Team (Baseball - Season Not Started)")
    print("=" * 70)
    print()

    team_id = str(HAVERFORD_TEAMS["baseball"])
    print("Team: Baseball")
    print(f"Team ID: {team_id}")
    print(f"URL: https://stats.ncaa.org/teams/{team_id}/season_to_date_stats")
    print()

    fetcher = NCAAFetcher()
    result = fetcher.fetch_team_stats(team_id, "baseball")

    print("=" * 70)
    print("RESULT:")
    print("=" * 70)
    print()

    print(f"Success: {result.success}")
    print(f"Error: {result.error}")
    print(f"Source: {result.source}")
    print(f"Timestamp: {result.timestamp}")
    print()

    if result.data:
        print("Data returned:")
        print(json.dumps(result.data, indent=2))
    else:
        print("Data: None")

    print()
    print("=" * 70)
    print("ANALYSIS:")
    print("=" * 70)
    print()

    if not result.success:
        print("✓ Returns FetchResult with success=False")
        print(f"✓ Error message: '{result.error}'")
        print("✓ This allows callers to handle gracefully")
        print()
        print("Expected behavior: The page exists but has no stats table yet")
        print("because the season hasn't started.")
    else:
        print("Unexpected: Returned success=True")
        if result.data:
            print(f"Players found: {len(result.data.get('players', []))}")


if __name__ == "__main__":
    test_empty_team()
