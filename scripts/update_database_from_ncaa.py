#!/usr/bin/env python3
"""
Update Player Database from NCAA Stats

This script fetches stats from NCAA for all Haverford teams and updates
the player database. Can be run manually or scheduled via cron.
"""

import sys
import hashlib
from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.website_fetcher.ncaa_fetcher import NCAAFetcher, HAVERFORD_TEAMS  # noqa: E402
from src.player_database.database import PlayerDatabase  # noqa: E402
from src.player_database.models import Player, StatEntry  # noqa: E402
from auto_update_team_ids import fetch_with_auto_recovery  # noqa: E402


def generate_player_id(name: str, sport: str) -> str:
    """
    Generate a unique player ID from name and sport.

    Args:
        name: Player name
        sport: Sport

    Returns:
        Unique player ID (hash-based)
    """
    # Create a deterministic ID based on name + sport
    raw = f"{name.lower().strip()}_{sport.lower()}"
    # Use first 16 chars of hash for shorter ID
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def extract_player_info(player_data: Dict[str, Any], sport: str) -> Dict[str, str]:
    """
    Extract player metadata from NCAA stats.

    Args:
        player_data: Player dict from NCAA fetcher
        sport: Sport name

    Returns:
        Dict with position, year, etc.
    """
    stats = player_data.get("stats", {})

    return {
        "position": stats.get("Pos", stats.get("Position", "")),
        "year": stats.get("Yr", stats.get("Year", stats.get("Class", ""))),
        "number": stats.get("#", stats.get("No", stats.get("Jersey", ""))),
    }


def update_database_for_team(
    fetcher: NCAAFetcher, db: PlayerDatabase, sport_key: str, team_id: str, season: str, dry_run: bool = False
) -> Dict[str, Any]:
    """
    Fetch stats for one team and update database.

    Args:
        fetcher: NCAAFetcher instance
        db: PlayerDatabase instance
        sport_key: Sport key (e.g., 'mens_basketball')
        team_id: NCAA team ID
        season: Season string (e.g., '2025-26')
        dry_run: If True, don't actually update database

    Returns:
        Dict with results (players_added, stats_added, errors)
    """
    sport_display = sport_key.replace("_", " ").title()

    print(f"\n{'=' * 60}")
    print(f"{sport_display} (ID: {team_id})")
    print(f"{'=' * 60}")

    # Fetch with auto-recovery (team_id first, then sport)
    result = fetch_with_auto_recovery(team_id, sport_key)

    if not result:
        return {"error": "Auto-recovery failed", "players_added": 0, "stats_added": 0}

    if not result.success:
        if "No statistics available yet" in result.error:
            print("  ⚠️  Season not started yet - skipping")
            return {"skipped": True, "players_added": 0, "stats_added": 0}
        else:
            print(f"  ✗ Error: {result.error}")
            return {"error": result.error, "players_added": 0, "stats_added": 0}

    # Process players
    data = result.data
    players = data["players"]
    stat_categories = data["stat_categories"]

    print(f"  Found {len(players)} players with {len(stat_categories)} stat categories")

    players_added = 0
    players_updated = 0
    stats_added = 0
    errors = []

    for player_data in players:
        player_name = player_data["name"]

        try:
            # Generate player ID
            player_id = generate_player_id(player_name, sport_key)

            # Extract player info
            player_info = extract_player_info(player_data, sport_key)

            # Check if player exists
            existing_player = db.get_player(player_id)

            if existing_player:
                # Update player info if needed
                if not dry_run:
                    existing_player.position = player_info["position"] or existing_player.position
                    existing_player.year = player_info["year"] or existing_player.year
                    db.update_player(existing_player)
                players_updated += 1
            else:
                # Add new player
                player = Player(
                    player_id=player_id,
                    name=player_name,
                    sport=sport_key,
                    team="Haverford",
                    position=player_info["position"],
                    year=player_info["year"],
                    active=True,
                )

                if not dry_run:
                    db.add_player(player)
                players_added += 1

            # Clear existing stats for this player/season before adding new ones
            if not dry_run:
                db.clear_player_stats(player_id, season)

            # Add stats
            for stat_name, stat_value in player_data["stats"].items():
                # Skip empty stats
                if stat_value == "" or stat_value is None:
                    continue

                stat_entry = StatEntry(
                    player_id=player_id,
                    stat_name=stat_name,
                    stat_value=stat_value,
                    season=season,
                    date_recorded=datetime.now(),
                )

                if not dry_run:
                    db.add_stat(stat_entry)
                stats_added += 1

        except Exception as e:
            error_msg = f"Error processing {player_name}: {e}"
            print(f"  ✗ {error_msg}")
            errors.append(error_msg)

    # Summary
    if dry_run:
        print(f"  [DRY RUN] Would add {players_added} players, update {players_updated} players")
        print(f"  [DRY RUN] Would add {stats_added} stat entries")
    else:
        print(f"  ✓ Added {players_added} new players, updated {players_updated} players")
        print(f"  ✓ Added {stats_added} stat entries")

    if errors:
        print(f"  ⚠️  {len(errors)} errors occurred")

    return {
        "success": True,
        "players_added": players_added,
        "players_updated": players_updated,
        "stats_added": stats_added,
        "errors": errors,
    }


def update_all_teams(
    db_path: str = "data/stats.db", season: str = "2025-26", dry_run: bool = False, sports_filter: List[str] = None
):
    """
    Update database with stats from all Haverford teams.

    Args:
        db_path: Path to database file
        season: Season string
        dry_run: If True, don't actually update database
        sports_filter: Optional list of sports to update (e.g., ['mens_basketball'])
    """
    print("=" * 60)
    print("Update Player Database from NCAA Stats")
    print("=" * 60)
    print()
    print(f"Database: {db_path}")
    print(f"Season: {season}")
    print(f"Dry run: {dry_run}")
    print()

    # Initialize
    fetcher = NCAAFetcher()
    db = PlayerDatabase(db_path)

    # Track results
    total_results = {
        "teams_processed": 0,
        "teams_skipped": 0,
        "teams_failed": 0,
        "players_added": 0,
        "players_updated": 0,
        "stats_added": 0,
    }

    # Process each team
    teams_to_process = HAVERFORD_TEAMS.items()
    if sports_filter:
        teams_to_process = [(k, v) for k, v in teams_to_process if k in sports_filter]

    for sport_key, team_id in teams_to_process:
        result = update_database_for_team(fetcher, db, sport_key, str(team_id), season, dry_run)

        if result.get("skipped"):
            total_results["teams_skipped"] += 1
        elif result.get("error"):
            total_results["teams_failed"] += 1
        else:
            total_results["teams_processed"] += 1
            total_results["players_added"] += result.get("players_added", 0)
            total_results["players_updated"] += result.get("players_updated", 0)
            total_results["stats_added"] += result.get("stats_added", 0)

    # Final summary
    print()
    print("=" * 60)
    print("FINAL SUMMARY")
    print("=" * 60)
    print()
    print(f"Teams processed: {total_results['teams_processed']}")
    print(f"Teams skipped (no stats): {total_results['teams_skipped']}")
    print(f"Teams failed: {total_results['teams_failed']}")
    print()
    print(f"Players added: {total_results['players_added']}")
    print(f"Players updated: {total_results['players_updated']}")
    print(f"Stats added: {total_results['stats_added']}")
    print()

    if dry_run:
        print("=" * 60)
        print("This was a DRY RUN - no database changes were made")
        print("Run without --dry-run to actually update the database")
        print("=" * 60)
    else:
        print("=" * 60)
        print("✓ Database update complete!")
        print("=" * 60)


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Update player database with stats from NCAA")
    parser.add_argument("--db-path", default="data/stats.db", help="Path to database file (default: data/stats.db)")
    parser.add_argument("--season", default="2025-26", help="Season string (default: 2025-26)")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without updating database")
    parser.add_argument("--sports", nargs="+", help="Only update specific sports (e.g., mens_basketball womens_soccer)")

    args = parser.parse_args()

    try:
        update_all_teams(db_path=args.db_path, season=args.season, dry_run=args.dry_run, sports_filter=args.sports)
        sys.exit(0)

    except Exception as e:
        print(f"\n✗ Fatal error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
