#!/usr/bin/env python3
"""
Automatically update team IDs when invalid IDs are detected.

This script demonstrates how to automatically discover and update team IDs
when the fetcher encounters invalid team IDs.
"""

import sys
from pathlib import Path

sys.path.insert(0, '/Users/maxfieldma/CS/projects/StatsTracker')

from src.website_fetcher.ncaa_fetcher import NCAAFetcher, HAVERFORD_TEAMS


def discover_and_map_teams():
    """
    Discover current team IDs and map them to sport keys.

    Returns:
        Dict mapping sport keys to team IDs, or None if failed
    """
    print("🔍 Detecting invalid team IDs, attempting auto-discovery...")
    print()

    fetcher = NCAAFetcher()
    result = fetcher.get_haverford_teams()

    if not result.success:
        print(f"✗ Failed to discover teams: {result.error}")
        return None

    teams = result.data['teams']
    print(f"✓ Discovered {len(teams)} teams from NCAA")
    print()

    # Map sport names to config keys
    sport_name_to_key = {
        "Men's Basketball": "mens_basketball",
        "Women's Basketball": "womens_basketball",
        "Men's Soccer": "mens_soccer",
        "Women's Soccer": "womens_soccer",
        "Field Hockey": "field_hockey",
        "Women's Volleyball": "womens_volleyball",
        "Baseball": "baseball",
        "Men's Lacrosse": "mens_lacrosse",
        "Women's Lacrosse": "womens_lacrosse",
        "Softball": "softball",
    }

    # Build new team ID mapping
    new_team_ids = {}
    for team in teams:
        sport_name = team['sport']
        if sport_name in sport_name_to_key:
            config_key = sport_name_to_key[sport_name]
            new_team_ids[config_key] = team['team_id']
            print(f"  {sport_name:<25} → {config_key:<25} ID: {team['team_id']}")

    print()
    return new_team_ids


def check_and_update_if_needed(force_check=False):
    """
    Check if team IDs are valid and auto-update if needed.

    Args:
        force_check: If True, check all teams even if config seems current

    Returns:
        Dict with results
    """
    print("=" * 70)
    print("Auto-Update Team IDs")
    print("=" * 70)
    print()

    fetcher = NCAAFetcher()
    invalid_teams = []
    valid_teams = []

    # Test each team ID
    print("Testing current team IDs...")
    print()

    for sport_key, team_id in HAVERFORD_TEAMS.items():
        sport_display = sport_key.replace('_', ' ').title()

        # Quick test - just check if page is valid
        result = fetcher.fetch_team_stats(str(team_id), sport_key)

        if result.success:
            valid_teams.append(sport_key)
            print(f"  ✓ {sport_display:<25} ID {team_id} - Valid")
        elif "Invalid team ID" in result.error:
            invalid_teams.append((sport_key, team_id))
            print(f"  ✗ {sport_display:<25} ID {team_id} - INVALID")
        elif "No statistics available yet" in result.error:
            valid_teams.append(sport_key)
            print(f"  ⚠️  {sport_display:<25} ID {team_id} - Valid (season not started)")
        else:
            print(f"  ? {sport_display:<25} ID {team_id} - Unknown error")

    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print()
    print(f"Valid team IDs: {len(valid_teams)}/{len(HAVERFORD_TEAMS)}")
    print(f"Invalid team IDs: {len(invalid_teams)}/{len(HAVERFORD_TEAMS)}")
    print()

    # If we have invalid IDs, try to discover new ones
    if invalid_teams or force_check:
        if invalid_teams:
            print("⚠️  Invalid team IDs detected!")
            print()
            for sport_key, team_id in invalid_teams:
                print(f"  • {sport_key}: {team_id}")
            print()

        # Discover new team IDs
        new_team_ids = discover_and_map_teams()

        if new_team_ids:
            print("=" * 70)
            print("RECOMMENDED UPDATES")
            print("=" * 70)
            print()
            print("Update config/config.example.yaml with these team IDs:")
            print()
            print("haverford_teams:")
            for sport_key in sorted(HAVERFORD_TEAMS.keys()):
                new_id = new_team_ids.get(sport_key, HAVERFORD_TEAMS[sport_key])
                old_id = HAVERFORD_TEAMS[sport_key]

                if sport_key in [s for s, _ in invalid_teams]:
                    print(f"  {sport_key}: {new_id}  # ← UPDATED (was {old_id})")
                else:
                    print(f"  {sport_key}: {new_id}")

            print()
            print("=" * 70)
            print("✓ Auto-discovery complete!")
            print("  Copy the team IDs above to update your config.")
            print("=" * 70)

            return {
                'needs_update': True,
                'invalid_count': len(invalid_teams),
                'new_team_ids': new_team_ids
            }
    else:
        print("✓ All team IDs are valid!")
        print()

        return {
            'needs_update': False,
            'invalid_count': 0,
            'new_team_ids': None
        }


def fetch_with_auto_recovery(team_id, sport):
    """
    Fetch team stats with automatic recovery if ID is invalid.

    This is an example of how to integrate auto-recovery into your
    data fetching workflow.

    Args:
        team_id: NCAA team ID
        sport: Sport key (e.g., 'mens_basketball')

    Returns:
        FetchResult or None
    """
    fetcher = NCAAFetcher()

    # First attempt
    result = fetcher.fetch_team_stats(str(team_id), sport)

    # Check if ID is invalid
    if not result.success and "Invalid team ID" in result.error:
        print(f"⚠️  Invalid team ID {team_id} for {sport}")
        print("🔄 Attempting auto-recovery...")

        # Discover current teams
        discovery_result = fetcher.get_haverford_teams()

        if discovery_result.success:
            # Try to find the correct team ID
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

            target_sport = sport_names.get(sport)
            if target_sport:
                for team in discovery_result.data['teams']:
                    if team['sport'] == target_sport:
                        new_team_id = team['team_id']
                        print(f"✓ Found new team ID: {new_team_id}")
                        print(f"🔄 Retrying with new ID...")

                        # Retry with new ID
                        result = fetcher.fetch_team_stats(new_team_id, sport)

                        if result.success:
                            print(f"✓ Success! Update config to use team ID {new_team_id}")

                        return result

        print("✗ Auto-recovery failed")
        return None

    return result


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Check and auto-update Haverford team IDs'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force check all teams and discover new IDs'
    )

    args = parser.parse_args()

    try:
        result = check_and_update_if_needed(force_check=args.force)

        if result['needs_update']:
            print()
            print("⚠️  Action required: Update your config file with new team IDs")
            sys.exit(1)
        else:
            print("✓ No updates needed")
            sys.exit(0)

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
