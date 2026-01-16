"""
Query builder that converts LLM structured output into database queries.
"""

import logging
from typing import Dict, List

logger = logging.getLogger(__name__)

# Sport name migration mapping (old -> new)
SPORT_MIGRATION = {
    "mens_track": "mens_track_xc",
    "mens_cross_country": "mens_track_xc",
    "womens_track": "womens_track_xc",
    "womens_cross_country": "womens_track_xc",
}

# Sport display names
SPORT_DISPLAY_NAMES = {
    "mens_track_xc": "Men's Track & Field / Cross Country",
    "womens_track_xc": "Women's Track & Field / Cross Country",
}


def get_sport_display_name(sport_key: str) -> str:
    """Convert sport key to display name."""
    if sport_key in SPORT_DISPLAY_NAMES:
        return SPORT_DISPLAY_NAMES[sport_key]
    return sport_key.replace("_", " ").title()


class SemanticQueryBuilder:
    """
    Converts structured LLM output to database queries and executes them.
    """

    def __init__(self, database):
        """
        Initialize query builder with database instance.

        Args:
            database: PlayerDatabase instance
        """
        self.database = database

    def _migrate_sport_name(self, sport: str) -> str:
        """
        Migrate old sport names to new merged names.

        Args:
            sport: Sport name (possibly old)

        Returns:
            Migrated sport name
        """
        if sport in SPORT_MIGRATION:
            new_sport = SPORT_MIGRATION[sport]
            logger.info(f"Migrating sport name: {sport} -> {new_sport}")
            return new_sport
        return sport

    def execute(self, structured_params: Dict) -> List[Dict]:
        """
        Execute semantic search query from LLM-generated parameters.

        Args:
            structured_params: Dict from LLM with intent, sport, stat_name, filters, etc.

        Returns:
            List of result dicts with player info and stat values
        """
        # Migrate old sport names to new ones
        if "sport" in structured_params and structured_params["sport"]:
            structured_params["sport"] = self._migrate_sport_name(structured_params["sport"])

        intent = structured_params.get("intent")

        logger.info(f"Executing query with intent: {intent}")
        logger.debug(f"Full params: {structured_params}")

        try:
            if intent == "rank_by_stat":
                return self._rank_by_stat(structured_params)
            elif intent == "filter_threshold":
                return self._filter_threshold(structured_params)
            elif intent == "search_name":
                return self._search_name(structured_params)
            elif intent == "compare_players":
                return self._compare_players(structured_params)
            elif intent == "ambiguous":
                # Return empty results for ambiguous queries
                # Frontend will show clarification message
                return []
            else:
                logger.warning(f"Unknown intent: {intent}, falling back to name search")
                return self._search_name(structured_params)

        except Exception as e:
            logger.error(f"Error executing query: {e}")
            # Return empty results on error
            return []

    def _rank_by_stat(self, params: Dict) -> List[Dict]:
        """
        Execute ranking query (e.g., "best scorers", "top assist leaders").

        Args:
            params: Structured parameters with sport, stat_name, ordering, limit, filters

        Returns:
            List of player results sorted by stat value
        """
        sport = params.get("sport")
        stat_name = params.get("stat_name")
        ordering = params.get("ordering", "DESC")
        limit = params.get("limit", 20)
        filters = params.get("filters", {})

        if not stat_name:
            logger.warning("No stat_name provided for ranking query")
            return []

        # Special handling for 5K queries across both genders
        # Men's track uses "5000" while women's XC uses "5K (XC)"
        if sport == "all" and stat_name in ["5K (XC)", "5000"]:
            logger.info("Handling cross-gender 5K query - searching both '5000' and '5K (XC)'")

            # Query men's 5000
            mens_results = self.database.semantic_query(
                {
                    "intent": "rank_by_stat",
                    "sport": None,
                    "stat_name": "5000",
                    "filters": {**filters, "sport_pattern": "mens_track"},
                    "ordering": ordering,
                    "limit": limit,
                }
            )

            # Query women's 5K (XC)
            womens_results = self.database.semantic_query(
                {
                    "intent": "rank_by_stat",
                    "sport": None,
                    "stat_name": "5K (XC)",
                    "filters": {**filters, "sport_pattern": "womens_track"},
                    "ordering": ordering,
                    "limit": limit,
                }
            )

            # Merge and sort results
            all_results = mens_results + womens_results

            # Sort by stat value (convert to float for comparison)
            def get_sort_value(result):
                val = result.get("stat_value")
                if val is None:
                    return float("inf") if ordering == "ASC" else float("-inf")
                # Handle time formats like "16:49.87" (MM:SS.ms)
                if isinstance(val, str) and ":" in val:
                    parts = val.split(":")
                    try:
                        minutes = float(parts[0])
                        seconds = float(parts[1])
                        return minutes * 60 + seconds
                    except (ValueError, IndexError):
                        return float("inf") if ordering == "ASC" else float("-inf")
                try:
                    return float(val)
                except (ValueError, TypeError):
                    return float("inf") if ordering == "ASC" else float("-inf")

            all_results.sort(key=get_sort_value, reverse=(ordering == "DESC"))
            results = all_results[:limit]

            logger.info(
                f"Combined 5K query returned {len(results)} results "
                f"(men's: {len(mens_results)}, women's: {len(womens_results)})"
            )
            return results

        # Use database's semantic_query method
        results = self.database.semantic_query(
            {
                "intent": "rank_by_stat",
                "sport": sport if sport != "all" else None,
                "stat_name": stat_name,
                "filters": filters,
                "ordering": ordering,
                "limit": limit,
            }
        )

        logger.info(f"Ranking query returned {len(results)} results")
        return results

    def _filter_threshold(self, params: Dict) -> List[Dict]:
        """
        Execute threshold filter query (e.g., "players close to 1000 points").

        Args:
            params: Structured parameters with stat_name, min/max values, filters

        Returns:
            List of players within the threshold range
        """
        sport = params.get("sport")
        stat_name = params.get("stat_name")
        filters = params.get("filters", {})
        ordering = params.get("ordering", "DESC")
        limit = params.get("limit", 50)  # Higher default for threshold queries

        if not stat_name:
            logger.warning("No stat_name provided for threshold query")
            return []

        # Use database's semantic_query method
        results = self.database.semantic_query(
            {
                "intent": "filter_threshold",
                "sport": sport if sport != "all" else None,
                "stat_name": stat_name,
                "filters": filters,
                "ordering": ordering,
                "limit": limit,
            }
        )

        logger.info(f"Threshold query returned {len(results)} results")
        return results

    def _search_name(self, params: Dict) -> List[Dict]:
        """
        Execute name search query.

        Args:
            params: May contain player_name, query string, or interpretation

        Returns:
            List of matching players with their career stats
        """
        # Try to extract player name from various fields
        query = params.get("player_name", "") or params.get("query", "")
        interpretation = params.get("interpretation", "")
        sport_filter = params.get("sport")

        # If query is empty, try interpretation
        if not query and interpretation:
            query = interpretation

        if not query:
            logger.warning("No query text for name search")
            return []

        # Filter by sport if specified and not "all"
        sport = sport_filter if sport_filter and sport_filter != "all" else None

        # Use database's search_players method
        players = self.database.search_players(query, sport=sport)

        # Convert to result format with career stats summary
        results = []
        for player in players:
            # Get player's career stats for display
            player_stats = self.database.get_player_stats(player.player_id)

            # Get top 3 career stats to show
            top_stats = {}
            if player_stats and player_stats.career_stats:
                # Sort stats by value (descending) and take top 3
                sorted_stats = sorted(
                    player_stats.career_stats.items(),
                    key=lambda x: x[1] if isinstance(x[1], (int, float)) else 0,
                    reverse=True,
                )[:3]
                top_stats = dict(sorted_stats)

            results.append(
                {
                    "player_id": player.player_id,
                    "name": player.name,
                    "sport": get_sport_display_name(player.sport),
                    "sport_key": player.sport,
                    "team": player.team,
                    "position": player.position,
                    "year": player.year,
                    "career_stats": top_stats,
                    "stat_name": None,
                    "stat_value": None,
                    "season": "Career",
                }
            )

        logger.info(f"Name search for '{query}' returned {len(results)} results")
        return results

    def _compare_players(self, params: Dict) -> List[Dict]:
        """
        Execute player comparison query.

        Args:
            params: Parameters for comparing specific players

        Returns:
            List of players with their stats for comparison
        """
        # For now, treat as name search for the mentioned players
        # This could be enhanced to show side-by-side comparison
        return self._search_name(params)
