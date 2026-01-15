"""
Player Database Implementation

Handles all database operations for player statistics.
"""

from typing import List, Optional
from datetime import datetime
import logging
import sqlite3
from pathlib import Path

from .models import Player, PlayerStats, StatEntry


logger = logging.getLogger(__name__)


class PlayerDatabase:
    """
    Manages player statistics database.

    This implementation uses SQLite. Can be extended to support PostgreSQL.
    """

    def __init__(self, db_path: str = "data/stats.db"):
        """
        Initialize database connection.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._ensure_db_exists()
        self._init_tables()
        logger.info(f"PlayerDatabase initialized with path: {db_path}")

    def _ensure_db_exists(self):
        """Ensure the database directory exists"""
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)

    def _get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)

    def _init_tables(self):
        """Initialize database tables if they don't exist"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Players table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS players (
                player_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                sport TEXT NOT NULL,
                team TEXT DEFAULT 'Haverford',
                position TEXT,
                year TEXT,
                active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # Stats table - flexible design for different stat types
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS stats (
                stat_id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_id TEXT NOT NULL,
                stat_name TEXT NOT NULL,
                stat_value TEXT NOT NULL,
                season TEXT NOT NULL,
                date_recorded TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                game_id TEXT,
                notes TEXT,
                FOREIGN KEY (player_id) REFERENCES players(player_id)
            )
        """
        )

        # Create indexes for common queries
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_stats_player
            ON stats(player_id)
        """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_stats_season
            ON stats(season)
        """
        )

        conn.commit()
        conn.close()
        logger.info("Database tables initialized")

    # Player CRUD operations

    def add_player(self, player: Player) -> bool:
        """
        Add a new player to the database.

        Args:
            player: Player object to add

        Returns:
            True if successful, False otherwise
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO players (player_id, name, sport, team, position, year, active)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (player.player_id, player.name, player.sport, player.team, player.position, player.year, player.active),
            )

            conn.commit()
            conn.close()
            logger.info(f"Added player: {player.name}")
            return True

        except Exception as e:
            logger.error(f"Error adding player: {e}")
            return False

    def get_player(self, player_id: str) -> Optional[Player]:
        """
        Retrieve a player by ID.

        Args:
            player_id: Player ID

        Returns:
            Player object if found, None otherwise
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT player_id, name, sport, team, position, year, active,
                       created_at, updated_at
                FROM players WHERE player_id = ?
            """,
                (player_id,),
            )

            row = cursor.fetchone()
            conn.close()

            if row:
                return Player(
                    player_id=row[0],
                    name=row[1],
                    sport=row[2],
                    team=row[3],
                    position=row[4],
                    year=row[5],
                    active=bool(row[6]),
                    created_at=datetime.fromisoformat(row[7]),
                    updated_at=datetime.fromisoformat(row[8]),
                )
            return None

        except Exception as e:
            logger.error(f"Error getting player: {e}")
            return None

    def update_player(self, player: Player) -> bool:
        """
        Update player information.

        Args:
            player: Player object with updated information

        Returns:
            True if successful, False otherwise
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                UPDATE players
                SET name = ?, sport = ?, team = ?, position = ?,
                    year = ?, active = ?, updated_at = CURRENT_TIMESTAMP
                WHERE player_id = ?
            """,
                (player.name, player.sport, player.team, player.position, player.year, player.active, player.player_id),
            )

            conn.commit()
            conn.close()
            logger.info(f"Updated player: {player.player_id}")
            return True

        except Exception as e:
            logger.error(f"Error updating player: {e}")
            return False

    def get_all_players(self, sport: Optional[str] = None, active_only: bool = True) -> List[Player]:
        """
        Get all players, optionally filtered by sport.

        Args:
            sport: Filter by sport (None for all)
            active_only: Only return active players

        Returns:
            List of Player objects
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            query = "SELECT player_id, name, sport, team, position, year, active FROM players WHERE 1=1"
            params = []

            if sport:
                query += " AND sport = ?"
                params.append(sport)

            if active_only:
                query += " AND active = 1"

            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()

            return [
                Player(
                    player_id=row[0],
                    name=row[1],
                    sport=row[2],
                    team=row[3],
                    position=row[4],
                    year=row[5],
                    active=bool(row[6]),
                )
                for row in rows
            ]

        except Exception as e:
            logger.error(f"Error getting all players: {e}")
            return []

    # Stats operations

    def clear_player_stats(self, player_id: str, season: str = None) -> bool:
        """
        Clear stats for a player, optionally for a specific season.

        Args:
            player_id: Player ID
            season: Optional season to clear (None clears all seasons)

        Returns:
            True if successful, False otherwise
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            if season:
                cursor.execute("DELETE FROM stats WHERE player_id = ? AND season = ?", (player_id, season))
                logger.info(f"Cleared stats for player {player_id}, season {season}")
            else:
                cursor.execute("DELETE FROM stats WHERE player_id = ?", (player_id,))
                logger.info(f"Cleared all stats for player {player_id}")

            conn.commit()
            conn.close()
            return True

        except Exception as e:
            logger.error(f"Error clearing player stats: {e}")
            return False

    def add_stat(self, stat_entry: StatEntry) -> bool:
        """
        Add a stat entry to the database.

        Args:
            stat_entry: StatEntry object

        Returns:
            True if successful, False otherwise
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO stats (player_id, stat_name, stat_value, season,
                                   date_recorded, game_id, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    stat_entry.player_id,
                    stat_entry.stat_name,
                    str(stat_entry.stat_value),
                    stat_entry.season,
                    stat_entry.date_recorded,
                    stat_entry.game_id,
                    stat_entry.notes,
                ),
            )

            conn.commit()
            conn.close()
            logger.info(f"Added stat: {stat_entry.stat_name} for player {stat_entry.player_id}")
            return True

        except Exception as e:
            logger.error(f"Error adding stat: {e}")
            return False

    def get_player_stats(self, player_id: str, season: Optional[str] = None) -> Optional[PlayerStats]:
        """
        Get aggregated statistics for a player.

        Args:
            player_id: Player ID
            season: Optional season filter

        Returns:
            PlayerStats object with aggregated stats
        """
        try:
            player = self.get_player(player_id)
            if not player:
                return None

            conn = self._get_connection()
            cursor = conn.cursor()

            # Get stats
            query = "SELECT stat_name, stat_value, season FROM stats WHERE player_id = ?"
            params = [player_id]

            if season:
                query += " AND season = ?"
                params.append(season)

            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()

            # Aggregate stats
            career_stats = {}
            season_stats = {}

            for row in rows:
                stat_name, stat_value, stat_season = row

                # Try to convert to numeric if possible
                try:
                    stat_value = float(stat_value)
                    if stat_value.is_integer():
                        stat_value = int(stat_value)
                except (ValueError, AttributeError):
                    pass

                # Add to season stats
                if stat_season not in season_stats:
                    season_stats[stat_season] = {}
                season_stats[stat_season][stat_name] = stat_value

                # Aggregate to career (simplified - may need sport-specific logic)
                if isinstance(stat_value, (int, float)):
                    career_stats[stat_name] = career_stats.get(stat_name, 0) + stat_value
                else:
                    career_stats[stat_name] = stat_value

            return PlayerStats(player=player, career_stats=career_stats, season_stats=season_stats)

        except Exception as e:
            logger.error(f"Error getting player stats: {e}")
            return None

    def search_players(self, name: str, sport: Optional[str] = None) -> List[Player]:
        """
        Search for players by name.

        Args:
            name: Player name (partial match)
            sport: Optional sport filter

        Returns:
            List of matching Player objects
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            query = "SELECT player_id, name, sport, team, position, year, active FROM players WHERE name LIKE ?"
            params = [f"%{name}%"]

            if sport:
                query += " AND sport = ?"
                params.append(sport)

            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()

            return [
                Player(
                    player_id=row[0],
                    name=row[1],
                    sport=row[2],
                    team=row[3],
                    position=row[4],
                    year=row[5],
                    active=bool(row[6]),
                )
                for row in rows
            ]

        except Exception as e:
            logger.error(f"Error searching players: {e}")
            return []

    def semantic_query(self, structured_params: dict) -> List[dict]:
        """
        Execute semantic search query from LLM-generated parameters.

        Args:
            structured_params: Dict with keys:
                - intent: "rank_by_stat", "filter_threshold", etc.
                - sport: Sport filter (optional)
                - stat_name: Stat to query
                - filters: Additional filters (min_value, max_value, season, etc.)
                - ordering: "DESC" or "ASC"
                - limit: Max results

        Returns:
            List of dicts with player info and stat values
        """
        try:
            # Note: intent parameter is extracted but not currently used in query logic
            _intent = structured_params.get("intent")  # noqa: F841
            sport = structured_params.get("sport")
            stat_name = structured_params.get("stat_name")
            filters = structured_params.get("filters", {})
            ordering = structured_params.get("ordering", "DESC")
            limit = structured_params.get("limit", 20)

            conn = self._get_connection()
            cursor = conn.cursor()

            # Base query
            query = """
                SELECT p.player_id, p.name, p.sport, p.team, p.position, p.year,
                       s.stat_name, s.stat_value, s.season
                FROM players p
                JOIN stats s ON p.player_id = s.player_id
                WHERE 1=1
            """
            params = []

            # Add filters
            if sport:
                query += " AND p.sport = ?"
                params.append(sport)

            if stat_name:
                query += " AND s.stat_name = ?"
                params.append(stat_name)

            if filters.get("season"):
                query += " AND s.season = ?"
                params.append(filters["season"])
            else:
                query += " AND s.season = 'Career'"  # Default to career stats

            if filters.get("min_value"):
                query += " AND CAST(s.stat_value AS REAL) >= ?"
                params.append(filters["min_value"])

            if filters.get("max_value"):
                query += " AND CAST(s.stat_value AS REAL) <= ?"
                params.append(filters["max_value"])

            if filters.get("position"):
                query += " AND p.position = ?"
                params.append(filters["position"])

            if filters.get("year"):
                query += " AND p.year = ?"
                params.append(filters["year"])

            # Order and limit
            if stat_name:
                query += f" ORDER BY CAST(s.stat_value AS REAL) {ordering}"
            query += " LIMIT ?"
            params.append(limit)

            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()

            return [
                {
                    "player_id": row[0],
                    "name": row[1],
                    "sport": row[2].replace("_", " ").title(),
                    "sport_key": row[2],
                    "team": row[3],
                    "position": row[4],
                    "year": row[5],
                    "stat_name": row[6],
                    "stat_value": row[7],
                    "season": row[8],
                }
                for row in rows
            ]

        except Exception as e:
            logger.error(f"Semantic query error: {e}")
            return []
