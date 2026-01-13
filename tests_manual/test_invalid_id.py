#!/usr/bin/env python3
"""
Test what happens with invalid team IDs vs. valid IDs with no stats yet.
"""

import sys
sys.path.insert(0, '/Users/maxfieldma/CS/projects/StatsTracker')

from src.website_fetcher.ncaa_fetcher import NCAAFetcher, HAVERFORD_TEAMS


def test_scenarios():
    """Test different error scenarios."""
    print("=" * 70)
    print("Testing Different Error Scenarios")
    print("=" * 70)
    print()

    fetcher = NCAAFetcher()

    scenarios = [
        {
            "name": "Valid ID - Season Not Started",
            "team_id": str(HAVERFORD_TEAMS["baseball"]),
            "sport": "baseball",
            "description": "Baseball team (season starts Feb/Mar)"
        },
        {
            "name": "Invalid ID - Made Up",
            "team_id": "999999",
            "sport": "unknown",
            "description": "Completely fake team ID"
        },
        {
            "name": "Invalid ID - Old Year",
            "team_id": "500000",
            "sport": "unknown",
            "description": "Old team ID from previous year"
        },
        {
            "name": "Valid ID - Active Season",
            "team_id": str(HAVERFORD_TEAMS["mens_basketball"]),
            "sport": "basketball",
            "description": "Basketball team (currently mid-season)"
        }
    ]

    for i, scenario in enumerate(scenarios, 1):
        print(f"[{i}/{len(scenarios)}] {scenario['name']}")
        print(f"  Description: {scenario['description']}")
        print(f"  Team ID: {scenario['team_id']}")
        print(f"  URL: https://stats.ncaa.org/teams/{scenario['team_id']}/season_to_date_stats")
        print()

        try:
            result = fetcher.fetch_team_stats(scenario['team_id'], scenario['sport'])

            print(f"  Success: {result.success}")
            print(f"  Error: {result.error}")

            if result.success and result.data:
                print(f"  Players: {len(result.data.get('players', []))}")

        except Exception as e:
            print(f"  Exception: {type(e).__name__}: {e}")

        print()
        print("-" * 70)
        print()


if __name__ == "__main__":
    test_scenarios()
