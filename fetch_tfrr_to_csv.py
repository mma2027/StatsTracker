#!/usr/bin/env python3
"""
Fetch all Haverford TFRR team stats and save each to a separate CSV file.

This script fetches track & field and cross country stats for Haverford teams
and saves each team's stats to its own CSV file in the output directory.
"""

import sys
import csv
import os
from pathlib import Path
from datetime import datetime

sys.path.insert(0, '/Users/maxfieldma/CS/projects/StatsTracker')

from src.website_fetcher.tfrr_fetcher import TFRRFetcher, HAVERFORD_TEAMS


def save_team_to_csv(team_data, sport_name, output_dir="tfrr_stats_output"):
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
    season = team_data.get('season', 'unknown').replace(' ', '_').lower()
    filename = f"haverford_{safe_sport_name}_{season}_{timestamp}.csv"
    filepath = os.path.join(output_dir, filename)

    try:
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            # Prepare headers: Athlete Name, Year + all event categories
            headers = ['Athlete Name', 'Year'] + team_data['event_categories']

            writer = csv.DictWriter(csvfile, fieldnames=headers)
            writer.writeheader()

            # Write athlete data
            for athlete in team_data['athletes']:
                row = {
                    'Athlete Name': athlete['name'],
                    'Year': athlete.get('year', '')
                }
                # Add event results
                row.update(athlete['events'])
                writer.writerow(row)

        return filepath

    except Exception as e:
        print(f"    ✗ Error saving CSV: {e}")
        return None


def fetch_all_to_csv(output_dir="tfrr_stats_output"):
    """
    Fetch stats for all Haverford TFRR teams and save each to CSV.

    Args:
        output_dir: Directory to save CSV files
    """
    print("=" * 70)
    print("Fetching All Haverford TFRR Team Stats to CSV")
    print("=" * 70)
    print()

    fetcher = TFRRFetcher()
    results = {
        'successful': [],
        'no_stats': [],
        'failed': []
    }

    total_teams = len(HAVERFORD_TEAMS)

    for i, (sport_key, team_code) in enumerate(HAVERFORD_TEAMS.items(), 1):
        sport_display = sport_key.replace('_', ' ').title()

        print(f"[{i}/{total_teams}] {sport_display}...")

        try:
            # Determine sport type (track or cross_country)
            sport_type = "cross_country" if "cross_country" in sport_key else "track"

            # Fetch the team stats
            result = fetcher.fetch_team_stats(team_code, sport_type)

            if result.success:
                data = result.data
                num_athletes = len(data['athletes'])
                num_events = len(data['event_categories'])

                # Save to CSV
                csv_path = save_team_to_csv(data, sport_display, output_dir)

                if csv_path:
                    print(f"  ✓ Saved {num_athletes} athletes ({num_events} events) to {csv_path}")
                    results['successful'].append({
                        'sport': sport_display,
                        'athletes': num_athletes,
                        'events': num_events,
                        'file': csv_path
                    })
                else:
                    print(f"  ⚠️  Fetched data but failed to save CSV")
                    results['failed'].append({
                        'sport': sport_display,
                        'error': 'CSV save failed'
                    })

            elif "No athlete data available" in result.error or "season may not have started" in result.error:
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
            print(f"  • {item['sport']:<30} {item['athletes']} athletes, {item['events']} events")
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
        description='Fetch all Haverford TFRR team stats and save to CSV files'
    )
    parser.add_argument(
        '--output-dir',
        default='tfrr_stats_output',
        help='Directory to save CSV files (default: tfrr_stats_output)'
    )
    parser.add_argument(
        '--sport',
        choices=['mens_track', 'womens_track', 'mens_cross_country', 'womens_cross_country'],
        help='Fetch only a specific sport (default: all sports)'
    )

    args = parser.parse_args()

    try:
        # If specific sport requested, temporarily modify HAVERFORD_TEAMS
        if args.sport:
            from src.website_fetcher.tfrr_fetcher import HAVERFORD_TEAMS as ALL_TEAMS
            HAVERFORD_TEAMS = {args.sport: ALL_TEAMS[args.sport]}

        success = fetch_all_to_csv(output_dir=args.output_dir)
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Fatal exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
