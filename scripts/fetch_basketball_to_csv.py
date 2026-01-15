#!/usr/bin/env python3
"""
Fetch Haverford Men's Basketball stats from NCAA and save to CSV.
"""

import sys
import csv

# Add project root to path
sys.path.insert(0, "/Users/maxfieldma/CS/projects/StatsTracker")

from src.website_fetcher.ncaa_fetcher import NCAAFetcher, HAVERFORD_TEAMS  # noqa: E402


def fetch_basketball_to_csv(output_file="csv_exports/haverford_mens_basketball_stats.csv"):
    """
    Fetch Haverford Men's Basketball stats and save to CSV.

    Args:
        output_file: Path to output CSV file
    """
    print("=" * 70)
    print("Fetching Haverford Men's Basketball Stats")
    print("=" * 70)

    # Get team ID
    team_id = str(HAVERFORD_TEAMS["mens_basketball"])
    print(f"\nTeam ID: {team_id}")
    print(f"URL: https://stats.ncaa.org/teams/{team_id}/season_to_date_stats")

    # Initialize fetcher
    print("\nInitializing NCAA fetcher...")
    fetcher = NCAAFetcher()

    # Fetch stats
    print("Fetching stats (this may take 10-15 seconds)...")
    result = fetcher.fetch_team_stats(team_id, "basketball")

    if not result.success:
        print(f"\n✗ Error: {result.error}")
        return False

    # Parse data
    data = result.data
    print("\n✓ Successfully fetched data!")
    print(f"Season: {data['season']}")
    print(f"Sport: {data['sport']}")
    print(f"Number of players: {len(data['players'])}")
    print(f"Stat categories: {', '.join(data['stat_categories'])}")

    # Write to CSV
    print(f"\nWriting to {output_file}...")

    with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
        # Prepare headers
        headers = ["Player Name"] + data["stat_categories"]

        writer = csv.DictWriter(csvfile, fieldnames=headers)
        writer.writeheader()

        # Write player data
        for player in data["players"]:
            row = {"Player Name": player["name"]}
            row.update(player["stats"])
            writer.writerow(row)

    print(f"✓ Saved {len(data['players'])} players to {output_file}")

    # Display preview
    print("\n" + "=" * 70)
    print("PREVIEW (First 5 players):")
    print("=" * 70)

    for i, player in enumerate(data["players"][:5], 1):
        print(f"\n{i}. {player['name']}")
        # Show first 5 stats
        stats_preview = list(player["stats"].items())[:5]
        for stat_name, stat_value in stats_preview:
            print(f"   {stat_name}: {stat_value}")
        if len(player["stats"]) > 5:
            print(f"   ... and {len(player['stats']) - 5} more stats")

    print("\n" + "=" * 70)
    print(f"✓ Complete! Open {output_file} to see all stats.")
    print("=" * 70)

    return True


if __name__ == "__main__":
    try:
        success = fetch_basketball_to_csv()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Exception occurred: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
