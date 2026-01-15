#!/usr/bin/env python3
"""
Fetch career NCAA stats for Haverford teams using player-level approach.

This script:
1. Fetches current roster with player IDs from the team roster page
2. For each player, visits their individual page to get career stats
3. Filters stats to only include Haverford seasons
4. Saves one CSV file per player with all their Haverford seasons

This approach eliminates the need for historical team ID tracking!
"""

import sys
import csv
import os
from pathlib import Path
from datetime import datetime
import time

sys.path.insert(0, "/Users/maxfieldma/CS/projects/StatsTracker")

from src.website_fetcher.ncaa_fetcher import NCAAFetcher, HAVERFORD_TEAMS  # noqa: E402


def save_player_career_csv(player_data, sport_name, player_name_override=None, output_dir="csv_exports/ncaa"):
    """
    Save player career stats to CSV with one row per season.

    Args:
        player_data: Player data dict from fetch_player_career_stats()
        sport_name: Name of the sport
        player_name_override: Override player name (use if player_data name is Unknown)
        output_dir: Directory to save CSV files

    Returns:
        Path to saved CSV file, or None if failed

    CSV format:
    Player Name, Year, Team, G, PTS, ...
    Seth Anderson, 2023-24, Haverford, 19, 32, ...
    Seth Anderson, 2024-25, Haverford, 20, 81, ...
    Seth Anderson, 2025-26, Haverford, 13, 44, ...
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Use override if provided, otherwise use data player_name
    player_name = player_name_override if player_name_override else player_data.get("player_name", "Unknown")
    safe_player_name = player_name.replace(" ", "_").replace(".", "")
    safe_sport_name = sport_name.replace(" ", "_").lower()
    timestamp = datetime.now().strftime("%Y%m%d")

    filename = f"{safe_sport_name}_{safe_player_name}_career_{timestamp}.csv"
    filepath = os.path.join(output_dir, filename)

    try:
        with open(filepath, "w", newline="", encoding="utf-8") as csvfile:
            # Build headers: Player Name + all stat categories
            headers = ["Player Name"] + player_data["stat_categories"]
            writer = csv.DictWriter(csvfile, fieldnames=headers)
            writer.writeheader()

            # Write one row per season
            for season in player_data["seasons"]:
                row = {"Player Name": player_name}
                row.update(season["stats"])
                # Override Year column with our season year value (fixes "Totals" -> "Career")
                if "Year" in row:
                    row["Year"] = season["year"]
                writer.writerow(row)

        return filepath

    except Exception as e:
        print(f"    ✗ Error saving CSV: {e}")
        return None


def fetch_team_career_stats(team_id, sport_key, sport_display, output_dir="csv_exports/ncaa"):
    """
    Fetch career stats for all players on a team.

    Args:
        team_id: Current season team ID
        sport_key: Sport key (e.g., "mens_basketball")
        sport_display: Display name (e.g., "Men's Basketball")
        output_dir: Directory to save CSV files

    Returns:
        Dict with results
    """
    fetcher = NCAAFetcher()

    print(f"\n{'='*70}")
    print(f"Processing: {sport_display}")
    print(f"{'='*70}")

    # Step 1: Fetch roster with player IDs
    print("\n[1/2] Fetching roster with player IDs...")
    roster_result = fetcher.fetch_team_roster_with_ids(str(team_id), sport_key)

    if not roster_result.success:
        print(f"  ✗ Failed to fetch roster: {roster_result.error}")
        return {"success": False, "error": roster_result.error}

    roster = roster_result.data["players"]
    print(f"  ✓ Found {len(roster)} players on roster\n")

    # Step 2: Fetch career stats for each player
    print("[2/2] Fetching career stats for each player...")
    successful_files = []
    failed_players = []

    for i, player in enumerate(roster, 1):
        player_name = player["name"]
        player_id = player["player_id"]

        print(f"  [{i}/{len(roster)}] {player_name}... ", end="", flush=True)

        try:
            # Fetch career stats for this player
            career_result = fetcher.fetch_player_career_stats(player_id, sport_key)

            if career_result.success:
                player_data = career_result.data
                num_seasons = len(player_data["seasons"])

                # Save CSV (pass player_name from roster to override "Unknown")
                csv_path = save_player_career_csv(player_data, sport_display, player_name, output_dir)

                if csv_path:
                    print(f"✓ ({num_seasons} seasons)")
                    successful_files.append(csv_path)
                else:
                    print("✗ (failed to save CSV)")
                    failed_players.append({"name": player_name, "error": "CSV save failed"})
            else:
                print(f"⊘ ({career_result.error})")
                # This is common - some players may not have Haverford history yet
                # (e.g., freshmen)

            # Small delay to avoid rate limiting
            time.sleep(0.5)

        except Exception as e:
            print(f"✗ ({str(e)})")
            failed_players.append({"name": player_name, "error": str(e)})

    return {"success": True, "files": successful_files, "failed": failed_players, "num_players": len(roster)}


def fetch_all_teams_career_stats(output_dir="csv_exports/ncaa"):
    """
    Fetch career stats for all Haverford teams.

    Args:
        output_dir: Directory to save CSV files
    """
    print("=" * 70)
    print("Fetching Career Stats for All Haverford NCAA Teams")
    print("Using Player-Level Approach (No Historical Team IDs Required!)")
    print("=" * 70)

    results = {"successful": [], "failed": []}

    total_teams = len(HAVERFORD_TEAMS)

    for i, (sport_key, team_id) in enumerate(HAVERFORD_TEAMS.items(), 1):
        sport_display = sport_key.replace("_", " ").title()

        print(f"\n[{i}/{total_teams}] {sport_display}")

        try:
            result = fetch_team_career_stats(team_id, sport_key, sport_display, output_dir)

            if result["success"]:
                results["successful"].append(
                    {
                        "sport": sport_display,
                        "files": result["files"],
                        "failed_players": result["failed"],
                        "num_players": result["num_players"],
                    }
                )
            else:
                results["failed"].append({"sport": sport_display, "error": result["error"]})

        except Exception as e:
            print(f"  ✗ Exception: {e}")
            results["failed"].append({"sport": sport_display, "error": str(e)})

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"\nTotal teams: {total_teams}")
    print(f"✓ Successful: {len(results['successful'])}")
    print(f"✗ Failed: {len(results['failed'])}")

    if results["successful"]:
        print("\n" + "=" * 70)
        print("SUCCESSFULLY PROCESSED:")
        print("=" * 70)
        for item in results["successful"]:
            num_files = len(item["files"])
            num_failed = len(item["failed_players"])
            total_players = item["num_players"]
            print(f"\n  • {item['sport']} ({total_players} players)")
            print(f"    CSV files: {num_files}")
            if num_failed > 0:
                print(f"    Failed: {num_failed} players")

    if results["failed"]:
        print("\n" + "=" * 70)
        print("FAILED:")
        print("=" * 70)
        for item in results["failed"]:
            print(f"  • {item['sport']}: {item['error']}")

    print("\n" + "=" * 70)
    print(f"✓ Complete! Files saved to: {output_dir}/")
    print("=" * 70)

    return len(results["successful"]) > 0


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Fetch career NCAA stats for Haverford teams (player-level approach)")
    parser.add_argument(
        "--output-dir", default="csv_exports/ncaa", help="Directory to save CSV files (default: csv_exports/ncaa)"
    )
    parser.add_argument(
        "--team",
        default=None,
        help="Specific team to fetch (e.g., mens_basketball). If not specified, fetches all teams.",
    )

    args = parser.parse_args()

    try:
        if args.team:
            # Fetch specific team
            if args.team not in HAVERFORD_TEAMS:
                print(f"✗ Unknown team: {args.team}")
                print(f"Available teams: {', '.join(HAVERFORD_TEAMS.keys())}")
                sys.exit(1)

            team_id = HAVERFORD_TEAMS[args.team]
            sport_display = args.team.replace("_", " ").title()

            result = fetch_team_career_stats(team_id, args.team, sport_display, args.output_dir)

            success = result["success"]
        else:
            # Fetch all teams
            success = fetch_all_teams_career_stats(output_dir=args.output_dir)

        sys.exit(0 if success else 1)

    except Exception as e:
        print(f"\n✗ Fatal exception: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
