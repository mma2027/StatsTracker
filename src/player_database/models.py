"""
Database models for player statistics
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional


@dataclass
class Player:
    """Represents a player in the database"""

    player_id: str
    name: str
    sport: str
    team: str = "Haverford"
    position: Optional[str] = None
    year: Optional[str] = None  # Freshman, Sophomore, etc.
    active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def __str__(self):
        return f"{self.name} ({self.sport})"


@dataclass
class StatEntry:
    """
    Represents a single statistical entry.
    This is flexible to handle different sports' stat categories.
    """

    stat_id: Optional[int] = None
    player_id: str = ""
    stat_name: str = ""  # e.g., "points", "rebounds", "100m_time"
    stat_value: Any = None  # Can be int, float, str depending on stat type
    season: str = ""  # e.g., "2023-24"
    date_recorded: datetime = field(default_factory=datetime.now)
    game_id: Optional[str] = None  # Link to specific game if applicable
    notes: Optional[str] = None

    def __str__(self):
        return f"{self.stat_name}: {self.stat_value}"


@dataclass
class PlayerStats:
    """
    Aggregated statistics for a player.
    Contains both career and season stats.
    """

    player: Player
    career_stats: Dict[str, Any] = field(default_factory=dict)
    season_stats: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    recent_entries: List[StatEntry] = field(default_factory=list)

    def get_stat(self, stat_name: str, season: Optional[str] = None) -> Any:
        """
        Get a specific stat value.

        Args:
            stat_name: Name of the stat to retrieve
            season: Optional season to get stat for. If None, returns career stat.

        Returns:
            The stat value, or None if not found
        """
        if season:
            return self.season_stats.get(season, {}).get(stat_name)
        return self.career_stats.get(stat_name)

    def add_stat(self, stat_name: str, value: Any, season: str):
        """Add or update a stat"""
        if season not in self.season_stats:
            self.season_stats[season] = {}
        self.season_stats[season][stat_name] = value

        # Update career stats (this is simplified - actual aggregation logic may vary)
        if stat_name not in self.career_stats:
            self.career_stats[stat_name] = value
        else:
            # For cumulative stats
            if isinstance(value, (int, float)):
                self.career_stats[stat_name] = self.career_stats.get(stat_name, 0) + value
