"""
Milestone Detector Implementation

Analyzes player statistics to identify who is close to achieving milestones.
"""

from typing import List, Dict, Any, Optional
import logging

from .models import Milestone, MilestoneProximity, MilestoneType
from ..player_database import PlayerDatabase, PlayerStats


logger = logging.getLogger(__name__)


class MilestoneDetector:
    """
    Detects when players are close to achieving milestones.

    This class analyzes player statistics and compares them against
    configured milestone thresholds.
    """

    def __init__(self, database: PlayerDatabase, milestone_config: Dict[str, Any]):
        """
        Initialize the milestone detector.

        Args:
            database: PlayerDatabase instance
            milestone_config: Configuration dict with milestone definitions
        """
        self.database = database
        self.milestone_config = milestone_config
        self.milestones = self._load_milestones(milestone_config)
        logger.info(f"MilestoneDetector initialized with {len(self.milestones)} milestones")

    def _load_milestones(self, config: Dict[str, Any]) -> List[Milestone]:
        """
        Load milestone definitions from configuration.

        Args:
            config: Milestone configuration dictionary

        Returns:
            List of Milestone objects

        TODO: Implement configuration parsing
        """
        milestones = []

        # Example: Parse config to create Milestone objects
        # This is a template - implement based on your config structure
        for sport, sport_config in config.items():
            for stat_name, thresholds in sport_config.items():
                if isinstance(thresholds, list):
                    for threshold in thresholds:
                        milestone = Milestone(
                            milestone_id=f"{sport}_{stat_name}_{threshold}",
                            sport=sport,
                            stat_name=stat_name,
                            threshold=threshold,
                            milestone_type=MilestoneType.CAREER_TOTAL,
                            description=f"{threshold} career {stat_name} in {sport}",
                        )
                        milestones.append(milestone)

        return milestones

    def check_player_milestones(self, player_id: str, proximity_threshold: int = 10) -> List[MilestoneProximity]:
        """
        Check if a player is close to any milestones.

        Args:
            player_id: Player ID to check
            proximity_threshold: How close to consider (e.g., within 10 units)

        Returns:
            List of MilestoneProximity objects for milestones the player is close to
        """
        logger.info(f"Checking milestones for player {player_id}")

        player_stats = self.database.get_player_stats(player_id)
        if not player_stats:
            logger.warning(f"No stats found for player {player_id}")
            return []

        close_milestones = []

        # Get milestones for this player's sport
        relevant_milestones = [m for m in self.milestones if m.sport == player_stats.player.sport]

        for milestone in relevant_milestones:
            proximity = self._calculate_proximity(player_stats, milestone)

            # Only include if close AND not already passed
            if (
                proximity
                and self._is_close_to_milestone(proximity, proximity_threshold)
                and not self._has_passed_milestone(proximity)
            ):
                close_milestones.append(proximity)

        logger.info(f"Found {len(close_milestones)} close milestones for player {player_id}")
        return close_milestones

    def check_all_players_milestones(
        self, sport: Optional[str] = None, proximity_threshold: int = 10
    ) -> Dict[str, List[MilestoneProximity]]:
        """
        Check all players for milestone proximity.

        Args:
            sport: Filter by sport (None for all sports)
            proximity_threshold: How close to consider

        Returns:
            Dictionary mapping player_id to list of MilestoneProximity objects
        """
        logger.info(f"Checking milestones for all players in sport: {sport or 'all'}")

        results = {}
        players = self.database.get_all_players(sport=sport)

        for player in players:
            close_milestones = self.check_player_milestones(player.player_id, proximity_threshold)

            if close_milestones:
                results[player.player_id] = close_milestones

        logger.info(f"Found milestone proximities for {len(results)} players")
        return results

    def _calculate_proximity(self, player_stats: PlayerStats, milestone: Milestone) -> Optional[MilestoneProximity]:
        """
        Calculate how close a player is to a milestone.

        Args:
            player_stats: Player statistics
            milestone: Milestone to check

        Returns:
            MilestoneProximity object or None if stat not found
        """
        try:
            # Get current value based on milestone type
            if milestone.milestone_type == MilestoneType.CAREER_TOTAL:
                current_value = player_stats.career_stats.get(milestone.stat_name)
            elif milestone.milestone_type == MilestoneType.SEASON_TOTAL:
                # Get most recent season
                seasons = list(player_stats.season_stats.keys())
                if seasons:
                    latest_season = max(seasons)
                    current_value = player_stats.season_stats[latest_season].get(milestone.stat_name)
                else:
                    current_value = None
            else:
                # TODO: Implement other milestone types
                current_value = None

            if current_value is None:
                return None

            # Calculate distance and percentage
            distance = milestone.threshold - current_value
            percentage = (current_value / milestone.threshold) * 100 if milestone.threshold > 0 else 0

            # Estimate games to milestone (simplified - can be improved)
            estimated_games = self._estimate_games_to_milestone(current_value, milestone.threshold, player_stats)

            return MilestoneProximity(
                player_id=player_stats.player.player_id,
                player_name=player_stats.player.name,
                milestone=milestone,
                current_value=current_value,
                distance=distance,
                percentage=percentage,
                estimated_games_to_milestone=estimated_games,
            )

        except Exception as e:
            logger.error(f"Error calculating proximity: {e}")
            return None

    def _is_close_to_milestone(self, proximity: MilestoneProximity, threshold: int) -> bool:
        """
        Determine if a player is close enough to alert about.

        Args:
            proximity: MilestoneProximity object
            threshold: Distance threshold

        Returns:
            True if player is close enough to milestone
        """
        # Check if within threshold distance
        if isinstance(proximity.distance, (int, float)):
            if proximity.distance <= threshold and proximity.distance > 0:
                return True

        # Or check if very close by percentage
        if proximity.percentage >= 90:
            return True

        return False

    def _has_passed_milestone(self, proximity: MilestoneProximity) -> bool:
        """
        Check if a player has already passed/achieved a milestone.

        Args:
            proximity: MilestoneProximity object

        Returns:
            True if milestone already achieved, False otherwise
        """
        return proximity.current_value >= proximity.milestone.threshold

    def _estimate_games_to_milestone(self, current_value: Any, threshold: Any, player_stats: PlayerStats) -> Optional[int]:
        """
        Estimate how many games until milestone is reached.

        Args:
            current_value: Current stat value
            threshold: Milestone threshold
            player_stats: Player statistics for calculating average

        Returns:
            Estimated number of games, or None if can't estimate

        TODO: Implement more sophisticated estimation based on recent performance
        """
        # This is a simplified calculation
        # Can be enhanced with:
        # - Recent game performance trends
        # - Season averages
        # - Historical data

        try:
            if not isinstance(current_value, (int, float)) or not isinstance(threshold, (int, float)):
                return None

            remaining = threshold - current_value
            if remaining <= 0:
                return 0

            # Simple average calculation - can be improved
            # This would need actual game-by-game data
            # For now, just return None
            return None

        except Exception as e:
            logger.error(f"Error estimating games to milestone: {e}")
            return None

    def get_priority_alerts(self, sport: Optional[str] = None) -> List[MilestoneProximity]:
        """
        Get high-priority milestone alerts.

        Args:
            sport: Filter by sport

        Returns:
            List of MilestoneProximity objects for high-priority milestones
        """
        all_proximities = self.check_all_players_milestones(sport=sport)

        priority_alerts = []
        for player_id, proximities in all_proximities.items():
            for proximity in proximities:
                if proximity.milestone.priority == 1 and proximity.is_very_close:
                    priority_alerts.append(proximity)

        # Sort by distance (closest first)
        priority_alerts.sort(key=lambda x: x.distance if isinstance(x.distance, (int, float)) else float("inf"))

        return priority_alerts
