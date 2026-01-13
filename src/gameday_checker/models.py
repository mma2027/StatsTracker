"""
Data models for gameday checker
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Team:
    """Represents a sports team"""

    name: str
    sport: str
    division: Optional[str] = None

    def __str__(self):
        return f"{self.name} ({self.sport})"


@dataclass
class Game:
    """Represents a scheduled game"""

    team: Team
    opponent: str
    date: datetime
    location: str  # "home" or "away" or venue name
    time: Optional[str] = None

    def __str__(self):
        return f"{self.team.name} vs {self.opponent} on {self.date.strftime('%Y-%m-%d')}"

    @property
    def is_home_game(self) -> bool:
        """Check if this is a home game"""
        return self.location.lower() == "home"
