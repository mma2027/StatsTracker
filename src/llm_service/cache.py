"""
Simple SQLite-based cache for semantic search results.
"""

import hashlib
import json
import logging
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict

logger = logging.getLogger(__name__)


class SemanticCache:
    """
    SQLite-based cache for semantic search query results.
    """

    def __init__(self, db_path: str = "data/semantic_cache.db", ttl: int = 3600):
        """
        Initialize cache.

        Args:
            db_path: Path to SQLite cache database
            ttl: Time-to-live in seconds (default: 1 hour)
        """
        self.db_path = Path(db_path)
        self.ttl = ttl

        # Create data directory if it doesn't exist
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize database
        self._init_database()

    def _init_database(self):
        """Create cache table if it doesn't exist."""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cache (
                    query_hash TEXT PRIMARY KEY,
                    query_text TEXT NOT NULL,
                    result_json TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    expires_at TIMESTAMP NOT NULL
                )
            """)

            # Create index on expiry for cleanup
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_expires_at
                ON cache(expires_at)
            """)

            conn.commit()
            conn.close()

            logger.info(f"Initialized semantic search cache at {self.db_path}")

        except Exception as e:
            logger.error(f"Error initializing cache database: {e}")

    def _generate_key(self, query: str, filters: Optional[Dict] = None) -> str:
        """
        Generate cache key from query and filters.

        Args:
            query: Search query text
            filters: Optional filter dict

        Returns:
            MD5 hash of query + filters
        """
        # Create a deterministic string from query and filters
        cache_input = query.strip().lower()
        if filters:
            # Sort dict keys for consistent hashing
            cache_input += json.dumps(filters, sort_keys=True)

        return hashlib.md5(cache_input.encode()).hexdigest()

    def get(self, query: str, filters: Optional[Dict] = None) -> Optional[Dict]:
        """
        Get cached result for query.

        Args:
            query: Search query text
            filters: Optional filter dict

        Returns:
            Cached result dict or None if not found/expired
        """
        try:
            query_hash = self._generate_key(query, filters)

            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            # Check if cached result exists and is not expired
            cursor.execute("""
                SELECT result_json, expires_at
                FROM cache
                WHERE query_hash = ?
            """, (query_hash,))

            row = cursor.fetchone()
            conn.close()

            if not row:
                logger.debug(f"Cache miss for query: {query[:50]}")
                return None

            result_json, expires_at_str = row
            expires_at = datetime.fromisoformat(expires_at_str)

            # Check if expired
            if datetime.now() > expires_at:
                logger.debug(f"Cache expired for query: {query[:50]}")
                self.delete(query, filters)
                return None

            logger.info(f"Cache hit for query: {query[:50]}")
            return json.loads(result_json)

        except Exception as e:
            logger.error(f"Error reading from cache: {e}")
            return None

    def set(
        self,
        query: str,
        result: Dict,
        ttl: Optional[int] = None,
        filters: Optional[Dict] = None
    ):
        """
        Store result in cache.

        Args:
            query: Search query text
            result: Result dict to cache
            ttl: Time-to-live in seconds (uses default if None)
            filters: Optional filter dict
        """
        try:
            query_hash = self._generate_key(query, filters)
            result_json = json.dumps(result)
            created_at = datetime.now()
            expires_at = created_at + timedelta(seconds=ttl or self.ttl)

            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            # Insert or replace
            cursor.execute("""
                INSERT OR REPLACE INTO cache
                (query_hash, query_text, result_json, created_at, expires_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                query_hash,
                query[:200],  # Truncate query for storage
                result_json,
                created_at.isoformat(),
                expires_at.isoformat()
            ))

            conn.commit()
            conn.close()

            logger.info(f"Cached result for query: {query[:50]} (expires in {ttl or self.ttl}s)")

        except Exception as e:
            logger.error(f"Error writing to cache: {e}")

    def delete(self, query: str, filters: Optional[Dict] = None):
        """
        Delete cached result.

        Args:
            query: Search query text
            filters: Optional filter dict
        """
        try:
            query_hash = self._generate_key(query, filters)

            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            cursor.execute("DELETE FROM cache WHERE query_hash = ?", (query_hash,))

            conn.commit()
            conn.close()

            logger.debug(f"Deleted cache entry for query: {query[:50]}")

        except Exception as e:
            logger.error(f"Error deleting from cache: {e}")

    def invalidate_expired(self):
        """Remove all expired cache entries."""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            cursor.execute("""
                DELETE FROM cache
                WHERE expires_at < ?
            """, (datetime.now().isoformat(),))

            deleted_count = cursor.rowcount
            conn.commit()
            conn.close()

            if deleted_count > 0:
                logger.info(f"Invalidated {deleted_count} expired cache entries")

        except Exception as e:
            logger.error(f"Error invalidating expired cache: {e}")

    def clear_all(self):
        """Clear all cached entries."""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            cursor.execute("DELETE FROM cache")

            conn.commit()
            conn.close()

            logger.info("Cleared all cache entries")

        except Exception as e:
            logger.error(f"Error clearing cache: {e}")

    def get_stats(self) -> Dict:
        """
        Get cache statistics.

        Returns:
            Dict with total_entries, expired_entries, valid_entries
        """
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM cache")
            total = cursor.fetchone()[0]

            cursor.execute("""
                SELECT COUNT(*) FROM cache
                WHERE expires_at < ?
            """, (datetime.now().isoformat(),))
            expired = cursor.fetchone()[0]

            conn.close()

            return {
                "total_entries": total,
                "expired_entries": expired,
                "valid_entries": total - expired
            }

        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {"total_entries": 0, "expired_entries": 0, "valid_entries": 0}
