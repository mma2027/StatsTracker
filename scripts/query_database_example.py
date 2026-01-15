#!/usr/bin/env python3
"""
Example: Query the player database after NCAA stats update.

Demonstrates how to query stats from the database after updating from NCAA.
"""

import sys

sys.path.insert(0, "/Users/maxfieldma/CS/projects/StatsTracker")

from src.player_database.database import PlayerDatabase  # noqa: E402


def main():
    """Query and display database contents."""
    print("=" * 70)
    print("Player Database Query Example")
    print("=" * 70)
    print()

    # Connect to database
    db = PlayerDatabase("data/test_stats.db")

    # Get all basketball players
    print("All Basketball Players:")
    print("-" * 70)
    players = db.get_all_players(sport="mens_basketball")
    print(f"Found {len(players)} players\n")

    for i, player in enumerate(players[:5], 1):
        print(f"{i}. {player.name}")
        print(f"   Position: {player.position}, Year: {player.year}")
        print(f"   Player ID: {player.player_id}")

        # Get stats for this player
        player_stats = db.get_player_stats(player.player_id, season="2025-26")

        if player_stats and player_stats.season_stats:
            season_data = player_stats.season_stats.get("2025-26", {})

            # Show a few key stats
            pts = season_data.get("PTS", "N/A")
            gp = season_data.get("GP", "N/A")
            fg_pct = season_data.get("FG%", "N/A")

            print(f"   Stats: {gp} GP, {pts} PTS, {fg_pct} FG%")

        print()

    if len(players) > 5:
        print(f"... and {len(players) - 5} more players")
        print()

    # Search for specific player
    print("=" * 70)
    print("Search Example:")
    print("-" * 70)
    search_results = db.search_players("Isaac", sport="mens_basketball")

    if search_results:
        for player in search_results:
            print(f"\nFound: {player.name}")

            stats = db.get_player_stats(player.player_id, season="2025-26")
            if stats and stats.season_stats:
                season_data = stats.season_stats.get("2025-26", {})
                print("  2025-26 Stats:")
                for stat_name, stat_value in list(season_data.items())[:10]:
                    print(f"    {stat_name}: {stat_value}")
                if len(season_data) > 10:
                    print(f"    ... and {len(season_data) - 10} more stats")
    else:
        print("No players found")

    print()
    print("=" * 70)
    print("✓ Query complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
