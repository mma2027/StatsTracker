#!/usr/bin/env python3
"""
Script to merge cross country and track into single sports:
- mens_cross_country + mens_track → mens_track_xc
- womens_cross_country + womens_track → womens_track_xc
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


def merge_track_cross_country():
    """
    Merge track and cross country by updating the sport field.
    This preserves all player_ids and stat references.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Count before
    cursor.execute("""
        SELECT sport, COUNT(*)
        FROM players
        WHERE sport IN ('mens_track', 'mens_cross_country', 'womens_track', 'womens_cross_country')
        GROUP BY sport
    """)
    before = dict(cursor.fetchall())
    logger.info("Before merge:")
    for sport, count in before.items():
        logger.info(f"  {sport}: {count} players")

    # Update men's sports
    logger.info("\nMerging men's track and cross country...")
    cursor.execute("""
        UPDATE players
        SET sport = 'mens_track_xc'
        WHERE sport IN ('mens_track', 'mens_cross_country')
    """)
    mens_updated = cursor.rowcount
    logger.info(f"Updated {mens_updated} player records")

    # Update women's sports
    logger.info("Merging women's track and cross country...")
    cursor.execute("""
        UPDATE players
        SET sport = 'womens_track_xc'
        WHERE sport IN ('womens_track', 'womens_cross_country')
    """)
    womens_updated = cursor.rowcount
    logger.info(f"Updated {womens_updated} player records")

    conn.commit()

    # Count after and remove duplicates
    logger.info("\nChecking for duplicate players...")

    # Find duplicates in men's
    cursor.execute("""
        SELECT name, COUNT(*) as count, GROUP_CONCAT(player_id) as ids
        FROM players
        WHERE sport = 'mens_track_xc'
        GROUP BY name
        HAVING COUNT(*) > 1
    """)
    mens_dupes = cursor.fetchall()

    if mens_dupes:
        logger.info(f"Found {len(mens_dupes)} duplicate men's players, removing...")
        for name, count, ids in mens_dupes:
            id_list = ids.split(',')
            # Keep the first ID, delete the rest
            keep_id = id_list[0]
            delete_ids = id_list[1:]

            # Update stats to point to the kept player
            for delete_id in delete_ids:
                cursor.execute("""
                    UPDATE stats SET player_id = ? WHERE player_id = ?
                """, (keep_id, delete_id))

                # Delete the duplicate player
                cursor.execute("DELETE FROM players WHERE player_id = ?", (delete_id,))

            logger.info(f"  Merged {count} entries for {name}")

    # Find duplicates in women's
    cursor.execute("""
        SELECT name, COUNT(*) as count, GROUP_CONCAT(player_id) as ids
        FROM players
        WHERE sport = 'womens_track_xc'
        GROUP BY name
        HAVING COUNT(*) > 1
    """)
    womens_dupes = cursor.fetchall()

    if womens_dupes:
        logger.info(f"Found {len(womens_dupes)} duplicate women's players, removing...")
        for name, count, ids in womens_dupes:
            id_list = ids.split(',')
            keep_id = id_list[0]
            delete_ids = id_list[1:]

            for delete_id in delete_ids:
                cursor.execute("""
                    UPDATE stats SET player_id = ? WHERE player_id = ?
                """, (keep_id, delete_id))

                cursor.execute("DELETE FROM players WHERE player_id = ?", (delete_id,))

            logger.info(f"  Merged {count} entries for {name}")

    conn.commit()

    # Final count
    cursor.execute("""
        SELECT sport, COUNT(*)
        FROM players
        WHERE sport IN ('mens_track_xc', 'womens_track_xc')
        GROUP BY sport
    """)
    after = dict(cursor.fetchall())

    logger.info("\n=== Merge Complete ===")
    for sport, count in after.items():
        logger.info(f"{sport}: {count} players")

    conn.close()


if __name__ == "__main__":
    logger.info("Starting track/cross country merge...")
    merge_track_cross_country()
    logger.info("Done!")
