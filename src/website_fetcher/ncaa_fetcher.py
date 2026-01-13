"""
NCAA Website Fetcher

Fetches statistics from NCAA.org or stats.ncaa.org
"""

import requests
from typing import Dict, Any, List, Optional
import logging
import time
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

from .base_fetcher import BaseFetcher, FetchResult


logger = logging.getLogger(__name__)


# Haverford College team IDs for 2025-26 season
HAVERFORD_SCHOOL_ID = 276
HAVERFORD_TEAMS = {
    "mens_basketball": 611523,
    "womens_basketball": 611724,
    "mens_soccer": 604522,
    "womens_soccer": 603609,
    "field_hockey": 603834,
    "womens_volleyball": 605677,
    "baseball": 615223,
    "mens_lacrosse": 612459,
    "womens_lacrosse": 613103,
    "softball": 614273,
}


class NCAAFetcher(BaseFetcher):
    """
    Fetcher for NCAA statistics website.

    Developer Notes:
    - Implement the actual NCAA website scraping/API calls
    - Handle NCAA-specific data formats
    - Parse HTML or JSON responses as needed
    """

    def __init__(self, base_url: str = "https://stats.ncaa.org", timeout: int = 30):
        super().__init__(base_url, timeout)
        self.driver = None

    def fetch_player_stats(self, player_id: str, sport: str) -> FetchResult:
        """
        Fetch player statistics from NCAA.

        Args:
            player_id: NCAA player ID
            sport: Sport name

        Returns:
            FetchResult with player statistics

        TODO: Implement actual NCAA API/scraping logic
        """
        try:
            logger.info(f"Fetching NCAA player stats for {player_id} in {sport}")

            # TODO: Implement actual fetching logic
            # Example structure:
            # url = f"{self.base_url}/players/{sport}/{player_id}"
            # response = requests.get(url, timeout=self.timeout)
            #
            # if not self.validate_response(response):
            #     return FetchResult(success=False, error="Invalid response", source=self.name)
            #
            # data = self._parse_player_data(response)
            # return FetchResult(success=True, data=data, source=self.name)

            # Placeholder return
            logger.warning("NCAA fetch_player_stats not yet implemented")
            return FetchResult(success=False, error="Not yet implemented", source=self.name)

        except Exception as e:
            return self.handle_error(e, "fetching player stats")

    def fetch_team_stats(self, team_id: str, sport: str) -> FetchResult:
        """
        Fetch team statistics from NCAA.

        Args:
            team_id: NCAA team ID
            sport: Sport name

        Returns:
            FetchResult with team statistics including all players and their stats

        Example data format:
        {
            "team_id": "611523",
            "sport": "basketball",
            "season": "2025-26",
            "players": [
                {
                    "name": "Player Name",
                    "stats": {"GP": "13", "PTS": "245", ...}
                }
            ],
            "stat_categories": ["GP", "GS", "MIN", "PTS", ...]
        }
        """
        try:
            logger.info(f"Fetching NCAA team stats for team {team_id} in {sport}")

            # Initialize Selenium driver
            self._init_selenium_driver()

            # Navigate to team stats page
            stats_url = f"{self.base_url}/teams/{team_id}/season_to_date_stats"
            logger.debug(f"Fetching URL: {stats_url}")
            self.driver.get(stats_url)

            # Wait for page to load
            time.sleep(3)

            # Get page source and parse with BeautifulSoup
            soup = BeautifulSoup(self.driver.page_source, "html.parser")

            # Extract season from page
            season = self._get_season_from_page(soup)

            # Check if page is valid (has team info) or is an error page
            page_error = self._check_for_page_errors(soup)
            if page_error:
                logger.error(f"Invalid team page for {team_id}: {page_error}")
                return FetchResult(
                    success=False,
                    error=page_error,
                    source=self.name,
                )

            # Parse the statistics table
            players_data, stat_categories = self._parse_stats_table(soup)

            if not players_data:
                logger.warning(f"No player data found for team {team_id}")
                return FetchResult(
                    success=False,
                    error="No statistics available yet (season may not have started)",
                    source=self.name,
                )

            # Build result data
            data = {
                "team_id": team_id,
                "sport": sport,
                "season": season,
                "players": players_data,
                "stat_categories": stat_categories,
            }

            logger.info(
                f"Successfully fetched stats for {len(players_data)} players from team {team_id}"
            )

            return FetchResult(success=True, data=data, source=self.name)

        except Exception as e:
            return self.handle_error(e, "fetching team stats")

        finally:
            # Always close the driver
            self._close_driver()

    def search_player(self, name: str, sport: str) -> FetchResult:
        """
        Search for a player on NCAA website.

        Args:
            name: Player name
            sport: Sport to search in

        Returns:
            FetchResult with list of matching players

        TODO: Implement player search functionality
        """
        try:
            logger.info(f"Searching NCAA for player {name} in {sport}")

            # TODO: Implement search logic

            logger.warning("NCAA search_player not yet implemented")
            return FetchResult(success=False, error="Not yet implemented", source=self.name)

        except Exception as e:
            return self.handle_error(e, "searching for player")

    def get_haverford_teams(self, school_id: int = HAVERFORD_SCHOOL_ID) -> FetchResult:
        """
        Automatically discover all Haverford College team IDs from NCAA website.

        This method scrapes the school's main page on stats.ncaa.org to find
        all current team IDs. Useful for updating team IDs at the start of
        each academic year.

        Args:
            school_id: NCAA school ID for Haverford College (default: 276)

        Returns:
            FetchResult with list of teams:
            {
                "school_id": 276,
                "teams": [
                    {
                        "sport": "Men's Basketball",
                        "team_id": "611523",
                        "url": "https://stats.ncaa.org/teams/611523"
                    },
                    ...
                ]
            }

        Example:
            fetcher = NCAAFetcher()
            result = fetcher.get_haverford_teams()
            if result.success:
                for team in result.data['teams']:
                    print(f"{team['sport']}: {team['team_id']}")
        """
        try:
            logger.info(f"Discovering Haverford College teams from NCAA (school ID: {school_id})")

            # Initialize Selenium driver
            self._init_selenium_driver()

            # Navigate to school page
            school_url = f"{self.base_url}/team/{school_id}"
            logger.debug(f"Fetching school page: {school_url}")
            self.driver.get(school_url)

            # Wait for page to load
            time.sleep(3)

            # Parse with BeautifulSoup
            soup = BeautifulSoup(self.driver.page_source, "html.parser")

            # Find all team links
            # NCAA uses links with format: /teams/{team_id}
            teams = []
            team_links = soup.find_all("a", href=lambda x: x and "/teams/" in x)

            for link in team_links:
                # Extract team ID from URL
                href = link["href"]
                team_id = href.split("/teams/")[-1].split("/")[0]  # Get just the ID

                # Extract sport name from link text
                sport_name_raw = link.text.strip()

                # Clean up sport name: remove season year and record
                # Format is typically "2025-26 Men's Basketball (6-7)"
                # We want just "Men's Basketball"
                import re
                # Remove season year pattern (YYYY-YY at start)
                sport_name = re.sub(r'^\d{4}-\d{2}\s+', '', sport_name_raw)
                # Remove record pattern (X-X) or (X-X-X) at end
                sport_name = re.sub(r'\s*\(\d+-\d+(-\d+)?\)\s*$', '', sport_name)
                sport_name = sport_name.strip()

                # Skip empty or invalid entries
                if not sport_name or not team_id:
                    continue

                teams.append({
                    "sport": sport_name,
                    "team_id": team_id,
                    "url": f"{self.base_url}/teams/{team_id}"
                })

            logger.info(f"Found {len(teams)} Haverford teams")

            data = {
                "school_id": school_id,
                "teams": teams
            }

            return FetchResult(success=True, data=data, source=self.name)

        except Exception as e:
            return self.handle_error(e, "discovering Haverford teams")

        finally:
            # Always close the driver
            self._close_driver()

    def _parse_player_data(self, response) -> Dict[str, Any]:
        """
        Parse NCAA player data from response.

        Args:
            response: HTTP response or parsed data

        Returns:
            Standardized player data dictionary

        TODO: Implement parsing logic based on NCAA's data format
        """
        # This is where you would parse the HTML/JSON response
        # and convert it to the standard format
        pass

    def _init_selenium_driver(self):
        """Initialize Chrome WebDriver with headless options for scraping."""
        logger.debug("Initializing Selenium WebDriver")

        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument(
            "--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")

        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.set_page_load_timeout(15)

        logger.debug("WebDriver initialized successfully")

    def _close_driver(self):
        """Close and clean up the Selenium WebDriver."""
        if self.driver:
            try:
                self.driver.quit()
                logger.debug("WebDriver closed successfully")
            except Exception as e:
                logger.warning(f"Error closing WebDriver: {e}")
            finally:
                self.driver = None

    def _check_for_page_errors(self, soup: BeautifulSoup) -> str:
        """
        Check if the page is an error page or invalid team page.

        Args:
            soup: BeautifulSoup object of the page

        Returns:
            Error message if page is invalid, None if page is valid
        """
        # Check for common error indicators
        page_text = soup.get_text().lower()

        # Check for "page not found" or "no team found" messages
        if "page not found" in page_text or "404" in page_text:
            return "Invalid team ID - page not found"

        if "no team found" in page_text:
            return "Invalid team ID - no team found"

        # Check if there's a team header/breadcrumb (indicates valid team page)
        # Valid pages usually have navigation breadcrumbs or team headers
        has_team_context = False

        # Look for team/sport indicators in headers
        for element in soup.find_all(["h1", "h2", "h3", "div"]):
            text = element.get_text().strip()
            # Check for sport names or "season to date" text
            if any(keyword in text.lower() for keyword in [
                "basketball", "soccer", "lacrosse", "baseball", "softball",
                "field hockey", "volleyball", "season to date", "statistics"
            ]):
                has_team_context = True
                break

        # Also check for breadcrumb navigation (common on valid pages)
        breadcrumbs = soup.find_all("a", class_="skipMask")
        if len(breadcrumbs) >= 2:  # Usually has school > sport navigation
            has_team_context = True

        # If no team context found, likely an invalid page
        if not has_team_context:
            # But check if there's any table at all (might just be empty stats)
            if soup.find("table"):
                # Has a table, probably just no stats yet
                return None
            else:
                # No tables, no context - likely invalid ID
                return "Invalid team ID - page does not contain team information"

        return None

    def _get_season_from_page(self, soup: BeautifulSoup) -> str:
        """
        Extract the season/year from the page.

        Args:
            soup: BeautifulSoup object of the page

        Returns:
            Season string (e.g., "2025-26") or "Unknown"
        """
        # Try to find season in page title or headers
        title = soup.find("title")
        if title and title.text:
            # NCAA pages often have format like "2025-26 Men's Basketball"
            import re

            match = re.search(r"(\d{4}-\d{2})", title.text)
            if match:
                return match.group(1)

        # Try to find in breadcrumbs or other common locations
        for element in soup.find_all(["h1", "h2", "span"]):
            if element.text:
                import re

                match = re.search(r"(\d{4}-\d{2})", element.text)
                if match:
                    return match.group(1)

        logger.warning("Could not extract season from page")
        return "Unknown"

    def _parse_stats_table(
        self, soup: BeautifulSoup
    ) -> tuple[List[Dict[str, Any]], List[str]]:
        """
        Parse the statistics table from NCAA page.

        Uses generic parsing to handle all sports automatically by extracting
        table headers and mapping data cells to those headers.

        Args:
            soup: BeautifulSoup object of the page

        Returns:
            Tuple of (players_data, stat_categories)
            - players_data: List of dictionaries with player name and stats
            - stat_categories: List of stat column names
        """
        players_data = []
        stat_categories = []

        # Find the main statistics table
        # NCAA typically uses tables with specific classes or the first table on the page
        tables = soup.find_all("table")

        if not tables:
            logger.warning("No tables found on page")
            return players_data, stat_categories

        # Use the first substantial table (likely the stats table)
        stats_table = None
        for table in tables:
            rows = table.find_all("tr")
            if len(rows) > 2:  # Need header + at least one data row
                stats_table = table
                break

        if not stats_table:
            logger.warning("No suitable stats table found")
            return players_data, stat_categories

        # Extract headers from the first row
        header_row = stats_table.find("tr")
        if not header_row:
            logger.warning("No header row found in table")
            return players_data, stat_categories

        headers = []
        for th in header_row.find_all(["th", "td"]):
            header_text = th.text.strip()
            headers.append(header_text)

        if not headers:
            logger.warning("No headers found in table")
            return players_data, stat_categories

        # Store stat categories (excluding player name column)
        stat_categories = [h for h in headers if h and h.lower() != "player"]

        # Parse data rows
        data_rows = stats_table.find_all("tr")[1:]  # Skip header row

        for row in data_rows:
            cells = row.find_all(["td", "th"])

            if len(cells) < 2:  # Need at least name + one stat
                continue

            # Build player data dict
            player_data = {"name": "", "stats": {}}

            for i, cell in enumerate(cells):
                if i >= len(headers):
                    break

                header = headers[i]
                cell_text = cell.text.strip()

                # Check if this cell contains the player name
                player_link = cell.find("a")
                if player_link or header.lower() == "player" or i == 0:
                    player_data["name"] = cell_text
                elif header:  # It's a stat column
                    player_data["stats"][header] = cell_text

            # Only add if we have a player name
            if player_data["name"]:
                players_data.append(player_data)

        logger.debug(
            f"Parsed {len(players_data)} players with {len(stat_categories)} stat categories"
        )

        return players_data, stat_categories
