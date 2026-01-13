"""
Models for milestone detection
"""

from dataclasses import dataclass
from typing import Any, Optional
from enum import Enum


class MilestoneType(Enum):
    """Types of milestones"""

    CAREER_TOTAL = "career_total"  # e.g., 1000 career points
    SEASON_TOTAL = "season_total"  # e.g., 500 points in a season
    PERSONAL_RECORD = "personal_record"  # e.g., new PR in track event
    GAME_PERFORMANCE = "game_performance"  # e.g., 30 points in a game
    AVERAGE = "average"  # e.g., averaging 20 points per game


@dataclass
class Milestone:
    """Represents a milestone achievement target"""

    milestone_id: str
    sport: str
    stat_name: str
    threshold: Any
    milestone_type: MilestoneType
    description: str
    priority: int = 1  # 1 = high, 2 = medium, 3 = low

    def __str__(self):
        return f"{self.description} ({self.threshold})"


@dataclass
class MilestoneProximity:
    """
    Represents how close a player is to achieving a milestone.
    """

    player_id: str
    player_name: str
    milestone: Milestone
    current_value: Any
    distance: Any  # How far from milestone (threshold - current_value)
    percentage: float  # Progress as percentage
    games_remaining: Optional[int] = None
    estimated_games_to_milestone: Optional[int] = None

    def __str__(self):
        return f"{self.player_name} is {self.distance} away from {self.milestone.description}"

    @property
    def is_very_close(self) -> bool:
        """Check if player is very close (>90%)"""
        return self.percentage >= 90.0

    @property
    def is_achievable_soon(self) -> bool:
        """Check if milestone is likely to be achieved soon"""
        if self.estimated_games_to_milestone is None:
            return False
        return self.estimated_games_to_milestone <= 5
