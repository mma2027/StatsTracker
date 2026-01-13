#!/usr/bin/env python3
"""
Fetch all Haverford NCAA team stats and save each to a separate CSV file.

This script fetches stats for all Haverford teams that have active seasons
and saves each team's stats to its own CSV file in the output directory.
"""

import sys
import csv
import os
from pathlib import Path
from datetime import datetime

sys.path.insert(0, '/Users/maxfieldma/CS/projects/StatsTracker')

from src.website_fetcher.ncaa_fetcher import NCAAFetcher, HAVERFORD_TEAMS


def save_team_to_csv(team_data, sport_name, output_dir="ncaa_stats_output"):
    """
    Save team stats to a CSV file.

    Args:
        team_data: The data dict from FetchResult
        sport_name: Name of the sport (for filename)
        output_dir: Directory to save CSV files

    Returns:
        Path to saved CSV file, or None if failed
    """
    # Create output directory if it doesn't exist
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Generate filename
    safe_sport_name = sport_name.replace(' ', '_').lower()
    timestamp = datetime.now().strftime('%Y%m%d')
    filename = f"haverford_{safe_sport_name}_{timestamp}.csv"
    filepath = os.path.join(output_dir, filename)

    try:
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            # Prepare headers: Player Name + all stat categories
            headers = ['Player Name'] + team_data['stat_categories']

            writer = csv.DictWriter(csvfile, fieldnames=headers)
            writer.writeheader()

            # Write player data
            for player in team_data['players']:
                row = {'Player Name': player['name']}
                row.update(player['stats'])
                writer.writerow(row)

        return filepath

    except Exception as e:
        print(f"    ✗ Error saving CSV: {e}")
        return None


def fetch_all_to_csv(output_dir="ncaa_stats_output"):
    """
    Fetch stats for all Haverford teams and save each to CSV.

    Args:
        output_dir: Directory to save CSV files
    """
    print("=" * 70)
    print("Fetching All Haverford NCAA Team Stats to CSV")
    print("=" * 70)
    print()

    fetcher = NCAAFetcher()
    results = {
        'successful': [],
        'no_stats': [],
        'failed': []
    }

    total_teams = len(HAVERFORD_TEAMS)

    for i, (sport_key, team_id) in enumerate(HAVERFORD_TEAMS.items(), 1):
        sport_display = sport_key.replace('_', ' ').title()

        print(f"[{i}/{total_teams}] {sport_display}...")

        try:
            # Fetch the team stats
            result = fetcher.fetch_team_stats(str(team_id), sport_key)

            if result.success:
                data = result.data
                num_players = len(data['players'])

                # Save to CSV
                csv_path = save_team_to_csv(data, sport_display, output_dir)

                if csv_path:
                    print(f"  ✓ Saved {num_players} players to {csv_path}")
                    results['successful'].append({
                        'sport': sport_display,
                        'players': num_players,
                        'file': csv_path
                    })
                else:
                    print(f"  ⚠️  Fetched data but failed to save CSV")
                    results['failed'].append({
                        'sport': sport_display,
                        'error': 'CSV save failed'
                    })

            elif "No player statistics found" in result.error:
                print(f"  ⚠️  No stats yet (season hasn't started)")
                results['no_stats'].append(sport_display)

            else:
                print(f"  ✗ Error: {result.error}")
                results['failed'].append({
                    'sport': sport_display,
                    'error': result.error
                })

        except Exception as e:
            print(f"  ✗ Exception: {e}")
            results['failed'].append({
                'sport': sport_display,
                'error': str(e)
            })

        print()

    # Summary
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print()

    print(f"Total teams: {total_teams}")
    print(f"✓ Successfully saved: {len(results['successful'])}")
    print(f"⚠️  No stats yet: {len(results['no_stats'])}")
    print(f"✗ Failed: {len(results['failed'])}")
    print()

    if results['successful']:
        print("=" * 70)
        print("SAVED FILES:")
        print("=" * 70)
        for item in results['successful']:
            print(f"  • {item['sport']:<25} {item['players']} players")
            print(f"    → {item['file']}")
        print()

    if results['no_stats']:
        print("=" * 70)
        print("NO STATS YET (Season not started):")
        print("=" * 70)
        for sport in results['no_stats']:
            print(f"  • {sport}")
        print()

    if results['failed']:
        print("=" * 70)
        print("FAILED:")
        print("=" * 70)
        for item in results['failed']:
            print(f"  • {item['sport']}: {item['error']}")
        print()

    print("=" * 70)
    print(f"✓ Complete! CSV files saved to: {output_dir}/")
    print("=" * 70)

    return len(results['successful']) > 0


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description='Fetch all Haverford NCAA team stats and save to CSV files'
    )
    parser.add_argument(
        '--output-dir',
        default='ncaa_stats_output',
        help='Directory to save CSV files (default: ncaa_stats_output)'
    )

    args = parser.parse_args()

    try:
        success = fetch_all_to_csv(output_dir=args.output_dir)
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Fatal exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
