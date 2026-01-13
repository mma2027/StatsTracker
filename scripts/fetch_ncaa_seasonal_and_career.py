#!/usr/bin/env python3
"""
Fetch both seasonal and career NCAA stats for Haverford teams.

This script:
1. Fetches current season stats → seasonal CSV
2. Gets active roster from current season
3. Fetches previous 6 years of stats for active roster only
4. Aggregates career totals → career CSV
"""

import sys
import csv
import os
import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict

sys.path.insert(0, '/Users/maxfieldma/CS/projects/StatsTracker')

from src.website_fetcher.ncaa_fetcher import NCAAFetcher, HAVERFORD_TEAMS


def load_historical_team_ids(filepath="data/historical_team_ids.json"):
    """
    Load historical team IDs from JSON file.

    Returns:
        Dict of {sport_key: {season: team_id}} or None if file doesn't exist
    """
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return None
    except Exception as e:
        print(f"  ⚠️  Error loading historical IDs: {e}")
        return None


def save_seasonal_csv(team_data, sport_name, output_dir="csv_exports"):
    """
    Save current season stats to CSV.

    Args:
        team_data: The data dict from FetchResult
        sport_name: Name of the sport
        output_dir: Directory to save CSV files

    Returns:
        Path to saved CSV file, or None if failed
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    safe_sport_name = sport_name.replace(' ', '_').lower()
    timestamp = datetime.now().strftime('%Y%m%d')
    season = team_data.get('season', 'unknown').replace('-', '_')
    filename = f"haverford_{safe_sport_name}_seasonal_{season}_{timestamp}.csv"
    filepath = os.path.join(output_dir, filename)

    try:
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            headers = ['Player Name', 'Season'] + team_data['stat_categories']
            writer = csv.DictWriter(csvfile, fieldnames=headers)
            writer.writeheader()

            for player in team_data['players']:
                row = {
                    'Player Name': player['name'],
                    'Season': team_data.get('season', 'Unknown')
                }
                row.update(player['stats'])
                writer.writerow(row)

        return filepath
    except Exception as e:
        print(f"    ✗ Error saving seasonal CSV: {e}")
        return None


def save_career_csv(career_stats, sport_name, stat_categories, output_dir="csv_exports"):
    """
    Save aggregated career stats to CSV.

    Args:
        career_stats: Dict of {player_name: {stat: total_value}}
        sport_name: Name of the sport
        stat_categories: List of stat column names
        output_dir: Directory to save CSV files

    Returns:
        Path to saved CSV file, or None if failed
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    safe_sport_name = sport_name.replace(' ', '_').lower()
    timestamp = datetime.now().strftime('%Y%m%d')
    filename = f"haverford_{safe_sport_name}_career_{timestamp}.csv"
    filepath = os.path.join(output_dir, filename)

    try:
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            headers = ['Player Name'] + stat_categories
            writer = csv.DictWriter(csvfile, fieldnames=headers)
            writer.writeheader()

            for player_name in sorted(career_stats.keys()):
                row = {'Player Name': player_name}
                row.update(career_stats[player_name])
                writer.writerow(row)

        return filepath
    except Exception as e:
        print(f"    ✗ Error saving career CSV: {e}")
        return None


def aggregate_career_stats(all_seasons_data):
    """
    Aggregate stats across multiple seasons for career totals.

    Args:
        all_seasons_data: List of season data dicts

    Returns:
        Dict of {player_name: {stat: total_value}}
    """
    career_stats = defaultdict(lambda: defaultdict(float))

    for season_data in all_seasons_data:
        for player in season_data['players']:
            player_name = player['name']

            for stat_name, stat_value in player['stats'].items():
                # Try to convert to float and add
                try:
                    # Remove commas and convert
                    clean_value = str(stat_value).replace(',', '')

                    # Handle percentage stats (keep as average, not sum)
                    if '%' in stat_name.upper() or 'PCT' in stat_name.upper():
                        # For percentages, we'll just take the most recent
                        career_stats[player_name][stat_name] = clean_value
                    else:
                        # Sum numeric stats
                        numeric_value = float(clean_value)
                        career_stats[player_name][stat_name] += numeric_value
                except (ValueError, TypeError):
                    # Non-numeric stat, just keep most recent value
                    career_stats[player_name][stat_name] = stat_value

    # Convert back to regular dict and format numbers
    return {
        player: dict(stats)
        for player, stats in career_stats.items()
    }


def fetch_seasonal_and_career(team_id, sport_key, sport_display, years_back=6, output_dir="csv_exports"):
    """
    Fetch both seasonal and career stats for a team.

    Args:
        team_id: Current season team ID
        sport_key: Sport key (e.g., "mens_basketball")
        sport_display: Display name (e.g., "Men's Basketball")
        years_back: How many years to look back for career stats
        output_dir: Directory to save CSV files

    Returns:
        Dict with results
    """
    fetcher = NCAAFetcher()

    print(f"\n{'='*70}")
    print(f"Processing: {sport_display}")
    print(f"{'='*70}")

    # Step 1: Fetch current season stats
    print(f"\n[1/2] Fetching current season stats...")
    current_result = fetcher.fetch_team_stats(str(team_id), sport_key)

    if not current_result.success:
        print(f"  ✗ Failed to fetch current season: {current_result.error}")
        return {'success': False, 'error': current_result.error}

    current_data = current_result.data
    num_players = len(current_data['players'])
    print(f"  ✓ Found {num_players} players in current roster")

    # Save seasonal CSV
    seasonal_path = save_seasonal_csv(current_data, sport_display, output_dir)
    if seasonal_path:
        print(f"  ✓ Saved seasonal stats: {seasonal_path}")

    # Get active roster names
    active_roster = set(player['name'] for player in current_data['players'])
    print(f"  ✓ Active roster: {len(active_roster)} players")

    # Step 2: Fetch previous years for career stats
    print(f"\n[2/2] Fetching career stats (last {years_back} years)...")
    all_seasons_data = [current_data]  # Start with current season

    # Load historical team IDs
    historical_ids = load_historical_team_ids()

    if historical_ids and sport_key in historical_ids:
        print(f"  ✓ Found historical team IDs for {sport_display}")

        # Fetch previous years' stats
        for season, hist_team_id in historical_ids[sport_key].items():
            if hist_team_id and hist_team_id != team_id:  # Skip if same as current or null
                print(f"    Fetching {season}... ", end='', flush=True)
                try:
                    hist_result = fetcher.fetch_team_stats(str(hist_team_id), sport_key)
                    if hist_result.success:
                        # Filter to active roster only for historical data
                        hist_data = hist_result.data
                        hist_data['players'] = [
                            p for p in hist_data['players']
                            if p['name'] in active_roster
                        ]
                        if hist_data['players']:
                            all_seasons_data.append(hist_data)
                            print(f"✓ ({len(hist_data['players'])} active players)")
                        else:
                            print(f"⊘ (no active players)")
                    else:
                        print(f"✗ ({hist_result.error})")
                except Exception as e:
                    print(f"✗ ({str(e)})")
    else:
        print(f"  ⚠️  No historical team IDs found")
        print(f"  💡 Create data/historical_team_ids.json to track career stats")
        print(f"  💡 See data/historical_team_ids.json.example for format")

    # Aggregate career stats (for now, just current season)
    print(f"\n  Aggregating career totals...")
    career_stats = aggregate_career_stats(all_seasons_data)

    # Filter to active roster only
    career_stats = {
        name: stats
        for name, stats in career_stats.items()
        if name in active_roster
    }

    print(f"  ✓ Career stats for {len(career_stats)} active players")

    # Save career CSV
    career_path = save_career_csv(
        career_stats,
        sport_display,
        current_data['stat_categories'],
        output_dir
    )
    if career_path:
        print(f"  ✓ Saved career stats: {career_path}")

    return {
        'success': True,
        'seasonal_path': seasonal_path,
        'career_path': career_path,
        'num_players': num_players
    }


def fetch_all_teams_seasonal_and_career(output_dir="csv_exports", years_back=6):
    """
    Fetch seasonal and career stats for all Haverford teams.

    Args:
        output_dir: Directory to save CSV files
        years_back: How many years to look back for career stats
    """
    print("=" * 70)
    print("Fetching Seasonal & Career Stats for All Haverford NCAA Teams")
    print("=" * 70)

    results = {
        'successful': [],
        'failed': []
    }

    total_teams = len(HAVERFORD_TEAMS)

    for i, (sport_key, team_id) in enumerate(HAVERFORD_TEAMS.items(), 1):
        sport_display = sport_key.replace('_', ' ').title()

        print(f"\n[{i}/{total_teams}] {sport_display}")

        try:
            result = fetch_seasonal_and_career(
                team_id,
                sport_key,
                sport_display,
                years_back,
                output_dir
            )

            if result['success']:
                results['successful'].append({
                    'sport': sport_display,
                    'seasonal': result['seasonal_path'],
                    'career': result['career_path'],
                    'players': result['num_players']
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
            print(f"\n  • {item['sport']} ({item['players']} players)")
            print(f"    Seasonal: {item['seasonal']}")
            print(f"    Career:   {item['career']}")

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
        description='Fetch seasonal and career NCAA stats for Haverford teams'
    )
    parser.add_argument(
        '--output-dir',
        default='csv_exports',
        help='Directory to save CSV files (default: csv_exports)'
    )
    parser.add_argument(
        '--years-back',
        type=int,
        default=6,
        help='How many years to look back for career stats (default: 6)'
    )

    args = parser.parse_args()

    try:
        success = fetch_all_teams_seasonal_and_career(
            output_dir=args.output_dir,
            years_back=args.years_back
        )
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Fatal exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
