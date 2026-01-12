"""
Gameday Checker Implementation

This module checks for games scheduled on specific dates.
"""

from datetime import datetime, date
from typing import List, Optional
import logging

from .models import Game, Team


logger = logging.getLogger(__name__)


class GamedayChecker:
    """
    Checks which Haverford College teams have games on a given day.

    This is a template class. Developers should implement the actual
    fetching logic based on the data source (website scraping, API, etc.)
    """

    def __init__(self, schedule_url: Optional[str] = None):
        """
        Initialize the gameday checker.

        Args:
            schedule_url: URL to fetch schedule data from
        """
        self.schedule_url = schedule_url
        logger.info(f"GamedayChecker initialized with URL: {schedule_url}")

    def get_games_for_date(self, check_date: date) -> List[Game]:
        """
        Get all games scheduled for a specific date.

        Args:
            check_date: The date to check for games

        Returns:
            List of Game objects scheduled for that date

        Example:
            >>> checker = GamedayChecker()
            >>> games = checker.get_games_for_date(date(2024, 3, 15))
            >>> for game in games:
            ...     print(f"{game.team.name} plays {game.opponent}")
        """
        logger.info(f"Checking games for date: {check_date}")

        # TODO: Implement actual fetching logic
        # This is where you would:
        # 1. Fetch schedule data from the website/API
        # 2. Parse the schedule
        # 3. Filter for the given date
        # 4. Return Game objects

        return self._fetch_games(check_date)

    def get_games_for_today(self) -> List[Game]:
        """
        Get all games scheduled for today.

        Returns:
            List of Game objects scheduled for today
        """
        return self.get_games_for_date(date.today())

    def get_games_for_team(self, team_name: str, start_date: date, end_date: date) -> List[Game]:
        """
        Get all games for a specific team within a date range.

        Args:
            team_name: Name of the team
            start_date: Start of date range
            end_date: End of date range

        Returns:
            List of Game objects for that team in the date range
        """
        logger.info(f"Checking games for team {team_name} from {start_date} to {end_date}")

        # TODO: Implement team-specific game fetching
        all_games = []
        current_date = start_date

        while current_date <= end_date:
            games = self.get_games_for_date(current_date)
            team_games = [g for g in games if g.team.name.lower() == team_name.lower()]
            all_games.extend(team_games)
            current_date = date.fromordinal(current_date.toordinal() + 1)

        return all_games

    def _fetch_games(self, check_date: date) -> List[Game]:
        """
        Internal method to fetch games from data source.

        This should be implemented by the developer working on this module.

        Args:
            check_date: Date to fetch games for

        Returns:
            List of Game objects
        """
        # TODO: Implement actual fetching logic here
        # Example placeholder:
        logger.warning("_fetch_games not yet implemented - returning empty list")
        return []

    def has_games_on_date(self, check_date: date) -> bool:
        """
        Check if there are any games on a specific date.

        Args:
            check_date: Date to check

        Returns:
            True if there are games, False otherwise
        """
        games = self.get_games_for_date(check_date)
        return len(games) > 0
