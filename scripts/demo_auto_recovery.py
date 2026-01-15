#!/usr/bin/env python3
"""
Demo: Auto-recovery when encountering invalid team IDs.

This script demonstrates how the fetcher can automatically discover
and use the correct team ID when it encounters an invalid one.
"""

import sys

sys.path.insert(0, "/Users/maxfieldma/CS/projects/StatsTracker")

from src.website_fetcher.ncaa_fetcher import NCAAFetcher  # noqa: E402


def fetch_with_auto_recovery(sport_key, initial_team_id):
    """
    Fetch team stats with automatic recovery if ID is invalid.

    Args:
        sport_key: Sport key (e.g., 'mens_basketball')
        initial_team_id: Team ID to try first

    Returns:
        FetchResult or None
    """
    print("=" * 70)
    print(f"Fetching: {sport_key.replace('_', ' ').title()}")
    print("=" * 70)
    print()

    fetcher = NCAAFetcher()

    print(f"Attempting with Team ID: {initial_team_id}")
    result = fetcher.fetch_team_stats(str(initial_team_id), sport_key)

    # Check if ID is invalid
    if not result.success and "Invalid team ID" in result.error:
        print(f"✗ Invalid team ID: {initial_team_id}")
        print(f"   Error: {result.error}")
        print()
        print("🔄 Attempting auto-recovery...")
        print("   Discovering current team IDs from NCAA...")

        # Discover current teams
        discovery_result = fetcher.get_haverford_teams()

        if not discovery_result.success:
            print(f"✗ Auto-recovery failed: {discovery_result.error}")
            return None

        print(f"✓ Discovered {len(discovery_result.data['teams'])} teams")
        print()

        # Map sport keys to sport names
        sport_names = {
            "mens_basketball": "Men's Basketball",
            "womens_basketball": "Women's Basketball",
            "mens_soccer": "Men's Soccer",
            "womens_soccer": "Women's Soccer",
            "field_hockey": "Field Hockey",
            "womens_volleyball": "Women's Volleyball",
            "baseball": "Baseball",
            "mens_lacrosse": "Men's Lacrosse",
            "womens_lacrosse": "Women's Lacrosse",
            "softball": "Softball",
        }

        target_sport = sport_names.get(sport_key)
        if not target_sport:
            print(f"✗ Unknown sport key: {sport_key}")
            return None

        # Find the correct team ID
        for team in discovery_result.data["teams"]:
            if team["sport"] == target_sport:
                new_team_id = team["team_id"]
                print(f"✓ Found correct team ID: {new_team_id}")
                print(f"   (was: {initial_team_id}, should be: {new_team_id})")
                print()
                print("🔄 Retrying with correct ID...")

                # Retry with new ID
                result = fetcher.fetch_team_stats(new_team_id, sport_key)

                if result.success:
                    print("✅ SUCCESS!")
                    print(f"   Fetched {len(result.data['players'])} players")
                    print()
                    print("⚠️  ACTION REQUIRED:")
                    print(f"   Update your config to use team ID: {new_team_id}")
                    print()
                elif "No statistics available yet" in result.error:
                    print("✅ ID IS VALID (but season hasn't started)")
                    print()
                    print("⚠️  ACTION REQUIRED:")
                    print(f"   Update your config to use team ID: {new_team_id}")
                    print()
                else:
                    print(f"✗ Still failed: {result.error}")

                return result

        print(f"✗ Could not find {target_sport} in discovered teams")
        return None

    elif result.success:
        print(f"✅ SUCCESS! Team ID {initial_team_id} is valid")
        print(f"   Fetched {len(result.data['players'])} players")
        return result

    elif "No statistics available yet" in result.error:
        print(f"✅ Team ID {initial_team_id} is valid")
        print("   (Season hasn't started yet)")
        return result

    else:
        print(f"✗ Error: {result.error}")
        return result


def main():
    """Demonstrate auto-recovery with different scenarios."""
    print()
    print("=" * 70)
    print("AUTO-RECOVERY DEMONSTRATION")
    print("=" * 70)
    print()
    print("This script demonstrates automatic team ID recovery.")
    print()

    # Scenario 1: Valid ID (should work immediately)
    print("\n" + "=" * 70)
    print("SCENARIO 1: Valid Team ID")
    print("=" * 70)
    print()
    fetch_with_auto_recovery("mens_basketball", "611523")

    # Scenario 2: Invalid ID (should trigger auto-recovery)
    print("\n" + "=" * 70)
    print("SCENARIO 2: Invalid Team ID (triggers auto-recovery)")
    print("=" * 70)
    print()
    fetch_with_auto_recovery("mens_basketball", "999999")

    # Scenario 3: Old ID (simulate previous year's ID)
    print("\n" + "=" * 70)
    print("SCENARIO 3: Old Team ID from Previous Year")
    print("=" * 70)
    print()
    fetch_with_auto_recovery("womens_soccer", "500000")

    print()
    print("=" * 70)
    print("DEMO COMPLETE")
    print("=" * 70)
    print()
    print("Key Takeaway:")
    print("  When invalid team IDs are detected, the system can automatically")
    print("  discover and use the correct IDs, then notify you to update config.")
    print()


if __name__ == "__main__":
    main()
