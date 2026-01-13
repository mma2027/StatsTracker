#!/usr/bin/env python3
"""
Test fetching stats from all Haverford College NCAA teams.

This script validates that the generic parser works across all sports
by attempting to fetch stats for all 10 Haverford teams.
"""

import sys
sys.path.insert(0, '/Users/maxfieldma/CS/projects/StatsTracker')

from src.website_fetcher.ncaa_fetcher import NCAAFetcher, HAVERFORD_TEAMS
import time


def test_all_teams():
    """Test fetching stats from all Haverford teams."""
    print("=" * 70)
    print("Testing NCAA Stats Fetcher - All Haverford Teams")
    print("=" * 70)
    print()

    fetcher = NCAAFetcher()
    results = {}

    total_teams = len(HAVERFORD_TEAMS)

    for i, (sport_key, team_id) in enumerate(HAVERFORD_TEAMS.items(), 1):
        sport_display = sport_key.replace('_', ' ').title()

        print(f"[{i}/{total_teams}] Testing {sport_display}...")
        print(f"  Team ID: {team_id}")
        print(f"  URL: https://stats.ncaa.org/teams/{team_id}/season_to_date_stats")

        try:
            # Fetch the team stats
            result = fetcher.fetch_team_stats(str(team_id), sport_key)

            if result.success:
                data = result.data
                num_players = len(data['players'])
                num_stats = len(data['stat_categories'])
                season = data.get('season', 'Unknown')

                print(f"  ✓ SUCCESS")
                print(f"    Season: {season}")
                print(f"    Players: {num_players}")
                print(f"    Stat categories: {num_stats}")
                print(f"    Categories: {', '.join(data['stat_categories'][:5])}...")

                # Store successful result
                results[sport_key] = {
                    'success': True,
                    'players': num_players,
                    'stats': num_stats,
                    'season': season
                }

                # Show one sample player
                if data['players']:
                    player = data['players'][0]
                    print(f"    Sample: {player['name']} ({len(player['stats'])} stats)")
            else:
                print(f"  ✗ FAILED: {result.error}")
                results[sport_key] = {
                    'success': False,
                    'error': result.error
                }

        except Exception as e:
            print(f"  ✗ EXCEPTION: {e}")
            results[sport_key] = {
                'success': False,
                'error': str(e)
            }

        print()

        # Add a small delay between requests to be respectful
        if i < total_teams:
            time.sleep(2)

    # Summary
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print()

    successful = [k for k, v in results.items() if v.get('success')]
    failed = [k for k, v in results.items() if not v.get('success')]

    print(f"Total teams tested: {total_teams}")
    print(f"Successful: {len(successful)}")
    print(f"Failed: {len(failed)}")
    print()

    if successful:
        print("✓ SUCCESSFUL TEAMS:")
        for sport_key in successful:
            sport_display = sport_key.replace('_', ' ').title()
            info = results[sport_key]
            print(f"  • {sport_display:<25} {info['players']} players, {info['stats']} stats")
        print()

    if failed:
        print("✗ FAILED TEAMS:")
        for sport_key in failed:
            sport_display = sport_key.replace('_', ' ').title()
            error = results[sport_key].get('error', 'Unknown error')
            print(f"  • {sport_display:<25} {error}")
        print()

    # Overall result
    if len(successful) == total_teams:
        print("=" * 70)
        print("🎉 ALL TESTS PASSED! Generic parser works across all sports!")
        print("=" * 70)
        return True
    else:
        print("=" * 70)
        print(f"⚠️  {len(failed)} team(s) failed. See details above.")
        print("=" * 70)
        return False


if __name__ == "__main__":
    try:
        success = test_all_teams()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Fatal exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
