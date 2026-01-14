#!/usr/bin/env python3
"""
Fetch Haverford TFRR athlete PRs and save each athlete to a separate CSV file.

This script fetches track & field and cross country personal records for Haverford athletes
and saves each athlete's PRs to their own CSV file.
"""

import sys
import csv
import os
from pathlib import Path
from datetime import datetime

sys.path.insert(0, '/Users/maxfieldma/CS/projects/StatsTracker')

from src.website_fetcher.tfrr_fetcher import TFRRFetcher, HAVERFORD_TEAMS


def save_athlete_prs_csv(athlete_data, sport_name, output_dir="csv_exports/tfrr"):
    """
    Save athlete PRs to a CSV file with one row per event.

    Args:
        athlete_data: Athlete dict with name, year, and events
        sport_name: Name of the sport (for filename)
        output_dir: Directory to save CSV files

    Returns:
        Path to saved CSV file, or None if failed

    CSV format:
    Athlete Name,Year,Event,PR
    Jory Lee,SR,60m,7.70
    Jory Lee,SR,200m,25.47
    Jory Lee,SR,Long Jump,5.89m
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    athlete_name = athlete_data['name']
    athlete_year = athlete_data.get('year', '')
    safe_athlete_name = athlete_name.replace(' ', '_').replace('.', '')
    safe_sport_name = sport_name.replace(' ', '_').lower()
    timestamp = datetime.now().strftime('%Y%m%d')

    filename = f"{safe_sport_name}_{safe_athlete_name}_prs_{timestamp}.csv"
    filepath = os.path.join(output_dir, filename)

    try:
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            headers = ['Athlete Name', 'Year', 'Event', 'PR']
            writer = csv.DictWriter(csvfile, fieldnames=headers)
            writer.writeheader()

            # Write one row per event
            for event_name, pr_value in athlete_data['events'].items():
                if pr_value:  # Only write events with actual PR values
                    row = {
                        'Athlete Name': athlete_name,
                        'Year': athlete_year,
                        'Event': event_name,
                        'PR': pr_value
                    }
                    writer.writerow(row)

        return filepath

    except Exception as e:
        print(f"    ✗ Error saving CSV: {e}")
        return None


def fetch_team_athlete_prs(team_code, sport_key, sport_display, output_dir="csv_exports/tfrr"):
    """
    Fetch PRs for all athletes on a team and save individual CSV files.

    Args:
        team_code: TFRR team code
        sport_key: Sport key (e.g., "mens_track")
        sport_display: Display name (e.g., "Men's Track")
        output_dir: Directory to save CSV files

    Returns:
        Dict with results
    """
    fetcher = TFRRFetcher()

    print(f"\n{'='*70}")
    print(f"Processing: {sport_display}")
    print(f"{'='*70}")

    # Determine sport type
    sport_type = "cross_country" if "cross_country" in sport_key else "track"

    # Fetch team stats
    print(f"\n[1/2] Fetching team roster and PRs...")
    result = fetcher.fetch_team_stats(team_code, sport_type)

    if not result.success:
        print(f"  ✗ Failed to fetch team: {result.error}")
        return {'success': False, 'error': result.error}

    team_data = result.data
    athletes = team_data.get('roster', team_data.get('athletes', []))
    print(f"  ✓ Found {len(athletes)} athletes\n")

    # Fetch individual athlete PRs
    print(f"[2/2] Fetching PRs for each athlete...")
    successful_files = []
    failed_athletes = []

    for i, athlete in enumerate(athletes, 1):
        athlete_name = athlete['name']
        athlete_id = athlete.get('athlete_id')

        print(f"  [{i}/{len(athletes)}] {athlete_name}... ", end='', flush=True)

        if not athlete_id:
            print(f"⊘ (no athlete ID)")
            failed_athletes.append({'name': athlete_name, 'error': 'No athlete ID'})
            continue

        # Fetch individual athlete PRs (smart rate limiting is now built into the fetcher)
        athlete_result = fetcher.fetch_player_stats(athlete_id, sport_type)

        if not athlete_result or not athlete_result.success:
            if athlete_result:
                print(f"✗ (fetch failed: {athlete_result.error})")
                failed_athletes.append({'name': athlete_name, 'error': athlete_result.error})
            else:
                print(f"✗ (no result)")
                failed_athletes.append({'name': athlete_name, 'error': 'No result returned'})
            continue

        athlete_pr_data = athlete_result.data
        prs = athlete_pr_data.get('personal_records', {})

        if not prs:
            print(f"⊘ (no PRs)")
            continue

        # Transform data for CSV
        athlete_csv_data = {
            'name': athlete_name,
            'year': athlete.get('year', ''),
            'events': prs
        }

        try:
            csv_path = save_athlete_prs_csv(athlete_csv_data, sport_display, output_dir)

            if csv_path:
                print(f"✓ ({len(prs)} PRs)")
                successful_files.append(csv_path)
            else:
                print(f"✗ (failed to save)")
                failed_athletes.append({'name': athlete_name, 'error': 'CSV save failed'})

        except Exception as e:
            print(f"✗ ({str(e)})")
            failed_athletes.append({'name': athlete_name, 'error': str(e)})

    return {
        'success': True,
        'files': successful_files,
        'failed': failed_athletes,
        'num_athletes': len(athletes)
    }


def fetch_all_teams_prs(output_dir="csv_exports/tfrr"):
    """
    Fetch PRs for all Haverford TFRR teams.

    Args:
        output_dir: Directory to save CSV files
    """
    print("=" * 70)
    print("Fetching PRs for All Haverford TFRR Athletes")
    print("Using Individual Athlete Approach")
    print("=" * 70)

    results = {
        'successful': [],
        'failed': []
    }

    total_teams = len(HAVERFORD_TEAMS)

    for i, (sport_key, team_code) in enumerate(HAVERFORD_TEAMS.items(), 1):
        sport_display = sport_key.replace('_', ' ').title()

        print(f"\n[{i}/{total_teams}] {sport_display}")

        try:
            result = fetch_team_athlete_prs(
                team_code,
                sport_key,
                sport_display,
                output_dir
            )

            if result['success']:
                results['successful'].append({
                    'sport': sport_display,
                    'files': result['files'],
                    'failed_athletes': result['failed'],
                    'num_athletes': result['num_athletes']
                })
            else:
                results['failed'].append({
                    'sport': sport_display,
                    'error': result['error']
                })

        except Exception as e:
            print(f"  ✗ Exception: {e}")
            results['failed'].append({
                'sport': sport_display,
                'error': str(e)
            })

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"\nTotal teams: {total_teams}")
    print(f"✓ Successful: {len(results['successful'])}")
    print(f"✗ Failed: {len(results['failed'])}")

    if results['successful']:
        print("\n" + "=" * 70)
        print("SUCCESSFULLY PROCESSED:")
        print("=" * 70)
        for item in results['successful']:
            num_files = len(item['files'])
            num_failed = len(item['failed_athletes'])
            total_athletes = item['num_athletes']
            print(f"\n  • {item['sport']} ({total_athletes} athletes)")
            print(f"    CSV files: {num_files}")
            if num_failed > 0:
                print(f"    Failed: {num_failed} athletes")

    if results['failed']:
        print("\n" + "=" * 70)
        print("FAILED:")
        print("=" * 70)
        for item in results['failed']:
            print(f"  • {item['sport']}: {item['error']}")

    print("\n" + "=" * 70)
    print(f"✓ Complete! Files saved to: {output_dir}/")
    print("=" * 70)

    return len(results['successful']) > 0


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description='Fetch TFRR athlete PRs for Haverford teams (individual athlete approach)'
    )
    parser.add_argument(
        '--output-dir',
        default='csv_exports/tfrr',
        help='Directory to save CSV files (default: csv_exports/tfrr)'
    )
    parser.add_argument(
        '--sport',
        choices=['mens_track', 'womens_track', 'mens_cross_country', 'womens_cross_country'],
        help='Fetch only a specific sport (default: all sports)'
    )

    args = parser.parse_args()

    try:
        if args.sport:
            # Fetch specific sport
            from src.website_fetcher.tfrr_fetcher import HAVERFORD_TEAMS as ALL_TEAMS

            if args.sport not in ALL_TEAMS:
                print(f"✗ Unknown sport: {args.sport}")
                print(f"Available sports: {', '.join(ALL_TEAMS.keys())}")
                sys.exit(1)

            team_code = ALL_TEAMS[args.sport]
            sport_display = args.sport.replace('_', ' ').title()

            result = fetch_team_athlete_prs(
                team_code,
                args.sport,
                sport_display,
                args.output_dir
            )

            success = result['success']
        else:
            # Fetch all sports
            success = fetch_all_teams_prs(output_dir=args.output_dir)

        sys.exit(0 if success else 1)

    except Exception as e:
        print(f"\n✗ Fatal exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
