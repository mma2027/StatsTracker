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

        Uses the calendar AJAX endpoint to get full month data.

        Args:
            check_date: Date to fetch games for

        Returns:
            List of Game objects
        """
        import requests

        all_games = []
        target_date_str = check_date.strftime("%Y-%m-%d")
        logger.info(f"Fetching games for {target_date_str} from calendar endpoint")

        try:
            # Use calendar AJAX endpoint
            # Extract base domain from schedule_url (remove /calendar path if present)
            base_url = self.schedule_url.rstrip('/').split('/calendar')[0] if self.schedule_url else 'https://haverfordathletics.com'
            url = f"{base_url}/services/responsive-calendar.ashx"

            # Format date as M/D/YYYY for API
            date_str = f"{check_date.month}/{check_date.day}/{check_date.year}"

            # Request parameters
            params = {"type": "month", "sport": "0", "location": "all", "date": date_str}  # 0 = all sports

            # Headers to mimic browser AJAX request
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Referer": f"{base_url}/calendar",
                "X-Requested-With": "XMLHttpRequest",
            }

            logger.debug(f"Fetching calendar data: {url}?date={date_str}")
            response = requests.get(url, params=params, headers=headers, timeout=10)

            if response.status_code != 200:
                logger.error(f"Failed to fetch calendar: HTTP {response.status_code}")
                return []

            # Parse JSON response
            calendar_data = response.json()
            logger.debug(f"Retrieved {len(calendar_data)} days from calendar")

            # Find the target date in the calendar data
            for day in calendar_data:
                day_date_str = day.get("date", "").split("T")[0]

                if day_date_str == target_date_str:
                    events = day.get("events")
                    if not events:
                        logger.info(f"No games on {target_date_str}")
                        return []

                    logger.info(f"Found {len(events)} games on {target_date_str}")

                    # Parse each event into a Game object
                    for event_data in events:
                        game = self._parse_game_data_from_calendar(event_data)
                        if game:
                            all_games.append(game)

                    break

            if not all_games:
                logger.info(f"No games found for {target_date_str}")

        except Exception as e:
            logger.error(f"Error fetching games from calendar endpoint: {e}")

        return all_games

    def _get_season_param(self, check_date: date) -> str:
        """
        Determine the season parameter for a given date.

        Athletic seasons typically run from August to July (e.g., 2025-26 season).

        Args:
            check_date: Date to get season for

        Returns:
            Season string in format "YYYY-YY" (e.g., "2025-26")
        """
        year = check_date.year
        month = check_date.month

        # If August or later, it's the start of a new season (e.g., Aug 2025 = 2025-26)
        # If before August, it's the second half of the season (e.g., March 2026 = 2025-26)
        if month >= 8:
            start_year = year
            end_year = year + 1
        else:
            start_year = year - 1
            end_year = year

        # Format as YYYY-YY (e.g., "2025-26")
        return f"{start_year}-{str(end_year)[-2:]}"

    def _get_sports_list(self) -> List[str]:
        """
        Get list of sport shortnames for Haverford College.

        Returns:
            List of sport shortnames
        """
        # Hardcoded list of Haverford sports
        # This could be dynamically scraped, but a static list is more reliable
        return [
            "baseball",
            "mens-basketball",
            "womens-basketball",
            "mens-cross-country",
            "womens-cross-country",
            "field-hockey",
            "mens-lacrosse",
            "womens-lacrosse",
            "mens-soccer",
            "womens-soccer",
            "softball",
            "mens-squash",
            "womens-squash",
            "mens-tennis",
            "wten",  # wten is women's tennis
            "mens-track-and-field",
            "womens-track-and-field",
        ]

    def _parse_game_data_from_calendar(self, event_data: dict) -> Optional[Game]:
        """
        Parse event data from calendar endpoint into a Game object.

        Args:
            event_data: Dictionary containing event information from calendar API

        Returns:
            Game object or None if parsing fails
        """
        try:
            # Extract date and time
            date_str = event_data.get("date")
            if not date_str:
                return None

            game_datetime = datetime.fromisoformat(date_str.replace("Z", "+00:00"))

            # Extract opponent
            opponent_data = event_data.get("opponent", {})
            if isinstance(opponent_data, dict):
                opponent_name = opponent_data.get("title", "Unknown")
            else:
                opponent_name = str(opponent_data)

            # Extract location
            location_indicator = event_data.get("location_indicator", "")
            location_desc = event_data.get("location", "")

            # Determine if home or away
            if location_indicator == "H":
                location = "home"
            elif location_indicator == "A":
                location = "away"
            else:
                location = location_desc

            # Extract sport info
            sport_data = event_data.get("sport", {})
            if isinstance(sport_data, dict):
                sport_name = sport_data.get("title", "Unknown")
            else:
                sport_name = str(sport_data)

            # Create Team object
            team = Team(name=f"Haverford {sport_name}", sport=sport_name)

            # Create Game object
            game = Game(
                team=team, opponent=opponent_name.strip(), date=game_datetime, location=location, time=event_data.get("time")
            )

            return game

        except (KeyError, ValueError, AttributeError) as e:
            logger.error(f"Error parsing calendar event data: {e}")
            return None

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

    def validate_scraping(self, test_sport: str = "baseball") -> dict:
        """
        Diagnostic tool to validate scraping is working correctly.

        Args:
            test_sport: Sport to test scraping with (default: baseball)

        Returns:
            Dictionary containing diagnostic information about the scraping process

        Example:
            >>> checker = GamedayChecker(schedule_url="https://haverfordathletics.com")
            >>> diagnostics = checker.validate_scraping("baseball")
            >>> print(f"Found {diagnostics['total_games']} games")
            >>> print(f"Date range: {diagnostics['date_range']}")
        """
        import requests
        import json
        import re

        try:
            # Use current date's season for validation
            season_param = self._get_season_param(date.today())

            sport_url = f"{self.schedule_url.rstrip('/')}/sports/{test_sport}/schedule"
            response = requests.get(sport_url, params={"season": season_param}, timeout=10)

            diagnostics = {
                "url": f"{sport_url}?season={season_param}",
                "status_code": response.status_code,
                "page_length": len(response.text),
                "var_obj_count": response.text.count("var obj = "),
                "matches_found": 0,
                "valid_json_objects": 0,
                "events_objects": 0,
                "total_games": 0,
                "date_range": None,
                "sample_dates": [],
            }

            if response.status_code != 200:
                return diagnostics

            pattern = re.compile(r"var obj = (\{.*?\});\s*if\s*\(", re.DOTALL)
            matches = pattern.findall(response.text)
            diagnostics["matches_found"] = len(matches)

            all_dates = []
            for match in matches:
                try:
                    obj = json.loads(match)
                    diagnostics["valid_json_objects"] += 1

                    if obj.get("type") == "events" and "data" in obj:
                        diagnostics["events_objects"] += 1
                        games = obj["data"]
                        diagnostics["total_games"] += len(games)

                        for game in games[:5]:  # Sample first 5
                            date_str = game.get("date", "").split("T")[0]
                            if date_str:
                                all_dates.append(date_str)
                                if len(diagnostics["sample_dates"]) < 5:
                                    opponent = game.get("opponent", {})
                                    opponent_name = (
                                        opponent.get("name", "Unknown") if isinstance(opponent, dict) else str(opponent)
                                    )
                                    diagnostics["sample_dates"].append({"date": date_str, "opponent": opponent_name})

                except json.JSONDecodeError:
                    pass

            if all_dates:
                diagnostics["date_range"] = {"min": min(all_dates), "max": max(all_dates)}

            return diagnostics

        except Exception as e:
            return {"error": str(e)}
