#!/usr/bin/env python3
"""
Script to remove duplicate stat entries from the database.
Keeps only one entry per (player_id, stat_name, season) combination.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import sqlite3
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).parent.parent / "data" / "stats.db"


def cleanup_duplicates():
    """Remove duplicate stat entries, keeping only the most recent one."""

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Count current duplicates
    cursor.execute("""
        SELECT COUNT(*) as total_rows FROM stats
    """)
    total_before = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*) as unique_stats
        FROM (
            SELECT DISTINCT player_id, stat_name, stat_value, season
            FROM stats
        )
    """)
    unique_stats = cursor.fetchone()[0]

    duplicates_before = total_before - unique_stats

    logger.info(f"Database has {total_before:,} stat entries")
    logger.info(f"Expected {unique_stats:,} unique entries")
    logger.info(f"Found {duplicates_before:,} duplicate entries to remove")

    if duplicates_before == 0:
        logger.info("No duplicates found!")
        conn.close()
        return

    # Create a temporary table with deduplicated stats
    # Keep the row with the highest rowid (most recent) for each unique combination
    logger.info("Creating deduplicated temp table...")
    cursor.execute("""
        CREATE TEMP TABLE stats_deduped AS
        SELECT
            MAX(stat_id) as stat_id,
            player_id,
            stat_name,
            stat_value,
            season,
            date_recorded,
            game_id,
            notes
        FROM stats
        GROUP BY player_id, stat_name, stat_value, season
    """)

    # Count entries in temp table
    cursor.execute("SELECT COUNT(*) FROM stats_deduped")
    temp_count = cursor.fetchone()[0]
    logger.info(f"Temp table created with {temp_count:,} unique entries")

    # Delete all stats
    logger.info("Removing all stat entries...")
    cursor.execute("DELETE FROM stats")

    # Insert deduplicated stats back
    logger.info("Inserting deduplicated entries...")
    cursor.execute("""
        INSERT INTO stats (stat_id, player_id, stat_name, stat_value, season,
                          date_recorded, game_id, notes)
        SELECT stat_id, player_id, stat_name, stat_value, season,
               date_recorded, game_id, notes
        FROM stats_deduped
    """)

    conn.commit()

    # Verify results
    cursor.execute("SELECT COUNT(*) FROM stats")
    total_after = cursor.fetchone()[0]

    logger.info(f"\n=== Cleanup Complete ===")
    logger.info(f"Before: {total_before:,} entries")
    logger.info(f"After:  {total_after:,} entries")
    logger.info(f"Removed: {total_before - total_after:,} duplicates")

    conn.close()


if __name__ == "__main__":
    logger.info("Starting duplicate cleanup...")
    cleanup_duplicates()
    logger.info("Done!")
