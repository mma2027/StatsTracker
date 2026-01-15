#!/usr/bin/env python3
"""
Discover all Haverford College NCAA team IDs.

This script uses the NCAAFetcher to automatically find all current
Haverford team IDs from the NCAA website. Run this at the start of
each academic year to update team IDs in the config.
"""

import sys
sys.path.insert(0, '/Users/maxfieldma/CS/projects/StatsTracker')

from src.website_fetcher.ncaa_fetcher import NCAAFetcher  # noqa: E402


def main():
    print("=" * 70)
    print("Discovering Haverford College NCAA Team IDs")
    print("=" * 70)
    print()

    fetcher = NCAAFetcher()

    print("Fetching team information from NCAA website...")
    print("(This may take 10-15 seconds)")
    print()

    result = fetcher.get_haverford_teams()

    if not result.success:
        print(f"✗ Error: {result.error}")
        return False

    data = result.data
    teams = data['teams']

    print(f"✓ Found {len(teams)} Haverford teams!")
    print()
    print("=" * 70)
    print("TEAM IDs:")
    print("=" * 70)
    print()

    # Sort teams by sport name for easier reading
    sorted_teams = sorted(teams, key=lambda x: x['sport'])

    for team in sorted_teams:
        print(f"  {team['sport']:<25} ID: {team['team_id']:<10} {team['url']}")

    print()
    print("=" * 70)
    print("YAML CONFIG FORMAT:")
    print("=" * 70)
    print()
    print("haverford_teams:")

    # Convert sport names to config keys (lowercase, underscores)
    for team in sorted_teams:
        # Simple conversion: lowercase and replace spaces/apostrophes
        config_key = team['sport'].lower().replace("'", "").replace(" ", "_")
        print(f"  {config_key}: {team['team_id']}")

    print()
    print("=" * 70)
    print("✓ Complete! Copy the team IDs above to config/config.example.yaml")
    print("=" * 70)

    return True


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Exception occurred: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
