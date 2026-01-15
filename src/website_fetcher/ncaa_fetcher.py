"""
NCAA Website Fetcher

Fetches statistics from NCAA.org or stats.ncaa.org
"""

from typing import Dict, Any, List
import logging
import time

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
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

    def fetch_player_career_stats(
        self, player_id: str, sport: str, school_filter: str = "Haverford", reuse_driver: bool = False
    ) -> FetchResult:
        """
        Fetch career statistics for an individual player across all their seasons.

        This method visits the player's individual page which contains season-by-season
        stats. It filters to only include seasons at the specified school.

        Args:
            player_id: NCAA player ID (e.g., "9335071")
            sport: Sport name (e.g., "mens_basketball")
            school_filter: School name to filter for (default: "Haverford")
            reuse_driver: If True, reuse existing driver instead of creating new one (default: False)

        Returns:
            FetchResult with player career statistics

        Example data format:
        {
            "player_id": "9335071",
            "player_name": "Seth Anderson",
            "sport": "mens_basketball",
            "seasons": [
                {
                    "year": "2025-26",
                    "team": "Haverford",
                    "stats": {"G": "13", "PTS": "44", ...}
                },
                {
                    "year": "2024-25",
                    "team": "Haverford",
                    "stats": {"G": "20", "PTS": "81", ...}
                }
            ],
            "stat_categories": ["Year", "Team", "G", "MP", "FGM", ...]
        }

        Notes:
        - Player pages are at: https://stats.ncaa.org/players/{player_id}
        - Player roster links are found on: https://stats.ncaa.org/teams/{team_id}/roster
        - The second table on player pages contains season-by-season stats
        - Rows with "Totals" in the year column are filtered out
        """
        try:
            logger.info(f"Fetching career stats for player {player_id} in {sport}")

            # Initialize Selenium driver if not reusing
            if not reuse_driver or not self.driver:
                self._init_selenium_driver()

            # Navigate to player page
            player_url = f"{self.base_url}/players/{player_id}"
            logger.debug(f"Fetching URL: {player_url}")
            self.driver.get(player_url)

            # Wait for page to load
            time.sleep(3)

            # Get page source and parse
            soup = BeautifulSoup(self.driver.page_source, "html.parser")

            # Check for page errors
            page_error = self._check_for_page_errors(soup)
            if page_error:
                logger.error(f"Invalid player page for {player_id}: {page_error}")
                return FetchResult(
                    success=False,
                    error=page_error,
                    source=self.name,
                )

            # Parse player career table
            player_data = self._parse_player_career_table(soup, school_filter)

            if not player_data or not player_data.get("seasons"):
                logger.warning(f"No {school_filter} career data found for player {player_id}")
                return FetchResult(
                    success=False,
                    error=f"No {school_filter} career statistics found",
                    source=self.name,
                )

            # Add player_id and sport to data
            player_data["player_id"] = player_id
            player_data["sport"] = sport

            logger.info(f"Successfully fetched {len(player_data['seasons'])} seasons for player {player_id}")

            return FetchResult(success=True, data=player_data, source=self.name)

        except Exception as e:
            return self.handle_error(e, "fetching player career stats")

        finally:
            # Only close the driver if not reusing
            if not reuse_driver:
                self._close_driver()

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

            logger.info(f"Successfully fetched stats for {len(players_data)} players from team {team_id}")

            return FetchResult(success=True, data=data, source=self.name)

        except Exception as e:
            return self.handle_error(e, "fetching team stats")

        finally:
            # Always close the driver
            self._close_driver()

    def fetch_team_roster_with_ids(self, team_id: str, sport: str, reuse_driver: bool = False) -> FetchResult:
        """
        Fetch team roster with player IDs from the roster page.

        Unlike fetch_team_stats() which gets current season stats from the stats page,
        this method visits the roster page to extract player names and their NCAA player IDs.
        These player IDs can then be used with fetch_player_career_stats() to get
        career statistics for each player.

        Args:
            team_id: NCAA team ID
            sport: Sport name
            reuse_driver: If True, reuse existing driver instead of creating new one (default: False)

        Returns:
            FetchResult with roster data

        Example data format:
        {
            "team_id": "611523",
            "sport": "mens_basketball",
            "players": [
                {
                    "name": "Seth Anderson",
                    "player_id": "9335071"
                },
                {
                    "name": "Raja Coleman",
                    "player_id": "11198481"
                },
                ...
            ]
        }
        """
        try:
            logger.info(f"Fetching roster with player IDs for team {team_id}")

            # Initialize Selenium driver if not reusing
            if not reuse_driver or not self.driver:
                self._init_selenium_driver()

            # Navigate to team roster page
            roster_url = f"{self.base_url}/teams/{team_id}/roster"
            logger.debug(f"Fetching URL: {roster_url}")
            self.driver.get(roster_url)

            # Wait for page to load
            time.sleep(3)

            # Get page source and parse
            soup = BeautifulSoup(self.driver.page_source, "html.parser")

            # Check for page errors
            page_error = self._check_for_page_errors(soup)
            if page_error:
                logger.error(f"Invalid roster page for {team_id}: {page_error}")
                return FetchResult(
                    success=False,
                    error=page_error,
                    source=self.name,
                )

            # Extract player links
            import re

            players = []

            # Find all links with /players/{player_id} pattern
            all_links = soup.find_all("a", href=True)
            player_links = [link for link in all_links if "/players/" in link.get("href", "")]

            for link in player_links:
                href = link.get("href")
                name = link.get_text().strip()

                # Extract player ID from href (e.g., /players/9335071 → 9335071)
                match = re.search(r"/players/(\d+)", href)
                if match:
                    player_id = match.group(1)

                    # Skip generic links like "Players" or "Game By Game"
                    if player_id and name and len(name) > 3 and not name.lower() in ["players", "game by game"]:
                        players.append({"name": name, "player_id": player_id})

            if not players:
                logger.warning(f"No players found on roster page for team {team_id}")
                return FetchResult(
                    success=False,
                    error="No players found on roster page",
                    source=self.name,
                )

            data = {"team_id": team_id, "sport": sport, "players": players}

            logger.info(f"Successfully fetched roster with {len(players)} players")

            return FetchResult(success=True, data=data, source=self.name)

        except Exception as e:
            return self.handle_error(e, "fetching team roster")

        finally:
            # Only close the driver if not reusing
            if not reuse_driver:
                self._close_driver()

    def fetch_team_with_career_stats(self, team_id: str, sport: str, school_filter: str = "Haverford") -> FetchResult:
        """
        Fetch team roster and career stats for all players using a single driver instance.

        This is an optimized method that reuses the same ChromeDriver for all fetches
        within a team, significantly improving performance and avoiding driver timeout issues.

        Args:
            team_id: NCAA team ID
            sport: Sport name
            school_filter: School name to filter for career stats (default: "Haverford")

        Returns:
            FetchResult with roster and all player career stats

        Example data format:
        {
            "team_id": "611523",
            "sport": "mens_basketball",
            "players": [
                {
                    "name": "Seth Anderson",
                    "player_id": "9335071",
                    "career_stats": {...}
                },
                ...
            ]
        }
        """
        try:
            logger.info(f"Fetching team {team_id} with career stats (single driver)")

            # Initialize driver once for the entire team
            self._init_selenium_driver()

            # Fetch roster with player IDs
            roster_result = self.fetch_team_roster_with_ids(team_id, sport, reuse_driver=True)

            if not roster_result.success:
                return roster_result

            players = roster_result.data["players"]
            logger.info(f"Fetching career stats for {len(players)} players")

            # Fetch career stats for each player (reusing the same driver)
            players_with_stats = []
            for player in players:
                player_id = player["player_id"]
                player_name = player["name"]

                career_result = self.fetch_player_career_stats(player_id, sport, school_filter, reuse_driver=True)

                if career_result.success:
                    players_with_stats.append(
                        {"name": player_name, "player_id": player_id, "career_stats": career_result.data}
                    )
                    logger.debug(f"Fetched career stats for {player_name}")
                else:
                    logger.warning(f"Failed to fetch career stats for {player_name}: {career_result.error}")
                    # Still include player in list but without career stats
                    players_with_stats.append(
                        {"name": player_name, "player_id": player_id, "career_stats": None, "error": career_result.error}
                    )

            data = {"team_id": team_id, "sport": sport, "players": players_with_stats}

            logger.info(f"Successfully fetched team {team_id} with {len(players_with_stats)} players")

            return FetchResult(success=True, data=data, source=self.name)

        except Exception as e:
            return self.handle_error(e, "fetching team with career stats")

        finally:
            # Close driver once at the end
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
                sport_name = re.sub(r"^\d{4}-\d{2}\s+", "", sport_name_raw)
                # Remove record pattern (X-X) or (X-X-X) at end
                sport_name = re.sub(r"\s*\(\d+-\d+(-\d+)?\)\s*$", "", sport_name)
                sport_name = sport_name.strip()

                # Skip empty or invalid entries
                if not sport_name or not team_id:
                    continue

                teams.append({"sport": sport_name, "team_id": team_id, "url": f"{self.base_url}/teams/{team_id}"})

            logger.info(f"Found {len(teams)} Haverford teams")

            data = {"school_id": school_id, "teams": teams}

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
        user_agent = (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )
        chrome_options.add_argument(f"--user-agent={user_agent}")
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
            if any(
                keyword in text.lower()
                for keyword in [
                    "basketball",
                    "soccer",
                    "lacrosse",
                    "baseball",
                    "softball",
                    "field hockey",
                    "volleyball",
                    "season to date",
                    "statistics",
                ]
            ):
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

    def _parse_player_career_table(self, soup: BeautifulSoup, school_filter: str = "Haverford") -> Dict[str, Any]:
        """
        Parse the career statistics table from an individual player's page.

        Player pages have multiple tables. The second table (index 1) contains
        season-by-season career stats. This method extracts that table and filters
        for only seasons at the specified school.

        Args:
            soup: BeautifulSoup object of the player page
            school_filter: School name to filter for (case-insensitive)

        Returns:
            Dictionary with:
            {
                "player_name": "Player Name",
                "seasons": [
                    {
                        "year": "2025-26",
                        "team": "Haverford",
                        "stats": {"G": "13", "PTS": "44", ...}
                    },
                    ...
                ],
                "stat_categories": ["Year", "Team", "G", "MP", ...]
            }

        Table Structure (example for basketball):
        Headers: ['Year', 'Team', 'G', 'MP', 'FGM', 'FGA', 'FG%', ...]
        Row 1: ['Totals', '52', '663:54', '59', '157', ...] <- Skip this
        Row 2: ['2023-24', 'Haverford', '19', '171:21', ...] <- Include
        Row 3: ['2024-25', 'Haverford', '20', '286:09', ...] <- Include
        Row 4: ['2025-26', 'Haverford', '13', '206:24', ...] <- Include
        """
        import re

        # Find all tables on the page
        tables = soup.find_all("table")

        if len(tables) < 2:
            logger.warning("Player page does not have career stats table (expected at least 2 tables)")
            return {}

        # The second table (index 1) contains season-by-season career stats
        career_table = tables[1]

        # Extract headers
        headers = career_table.find_all("th")
        if not headers:
            logger.warning("No headers found in career stats table")
            return {}

        stat_categories = [h.get_text().strip() for h in headers]
        logger.debug(f"Career table headers: {stat_categories}")

        # Extract player name from page (usually in h1 or title)
        player_name = "Unknown"
        h1_tag = soup.find("h1")
        if h1_tag:
            player_name = h1_tag.get_text().strip()

        # Parse data rows
        rows = career_table.find_all("tr")
        data_rows = [r for r in rows if r.find_all("td")]

        seasons = []
        career_totals = None
        school_filter_lower = school_filter.lower()

        for row in data_rows:
            cells = row.find_all("td")
            cell_values = [c.get_text().strip() for c in cells]

            if not cell_values:
                logger.debug("Skipping row: no cells")
                continue

            # First cell should be the year
            year = cell_values[0] if cell_values else ""
            logger.debug(f"Processing row with year='{year}', {len(cell_values)} cells")

            # Check if this row is shorter than headers (common for totals rows)
            # If so, pad it with empty strings to match header length
            while len(cell_values) < len(stat_categories):
                cell_values.append("")

            # Check if this is the "Totals" row
            if "total" in year.lower():
                logger.debug(f"Detected totals row with year='{year}', {len(cell_values)} cells")

                # IMPORTANT: Totals row is missing the "Team" column, so it's shifted left by 1
                # Insert empty string at position 1 to align with headers
                # Before: ["Totals", "52", "663:54", "59", "157", ...]
                # After:  ["Totals", "", "52", "663:54", "59", "157", ...]
                cell_values.insert(1, "")
                logger.debug(f"After inserting empty Team: {len(cell_values)} cells")

                # Build stats dictionary for career totals
                stats = {}
                for i, stat_name in enumerate(stat_categories):
                    if i < len(cell_values):
                        stats[stat_name] = cell_values[i]

                # Store career totals separately
                career_totals = {
                    "year": "Career",  # Label it as "Career" instead of "Totals"
                    "team": school_filter,  # Use school filter as team name
                    "stats": stats,
                }
                logger.debug(f"Stored career_totals: G={stats.get('G', 'N/A')}, PTS={stats.get('PTS', 'N/A')}")
                continue

            # Second cell should be the team
            team = cell_values[1] if len(cell_values) > 1 else ""

            # Filter for specified school only
            if school_filter_lower not in team.lower():
                logger.debug(f"Skipping row with team '{team}' (not {school_filter})")
                continue

            # Check if this looks like a valid season year (e.g., "2024-25")
            if not re.match(r"\d{4}-\d{2}", year):
                logger.debug(f"Skipping row with invalid year format: {year}")
                continue

            # Build stats dictionary mapping stat names to values
            stats = {}
            for i, stat_name in enumerate(stat_categories):
                if i < len(cell_values):
                    stats[stat_name] = cell_values[i]

            seasons.append({"year": year, "team": team, "stats": stats})

        # Add career totals as the last row if we found it
        if career_totals:
            logger.debug(f"Adding career totals row: {career_totals['year']}")
            seasons.append(career_totals)
        else:
            logger.debug("No career totals found to add")

        logger.info(f"Found {len(seasons)} {school_filter} seasons for {player_name}")

        return {"player_name": player_name, "seasons": seasons, "stat_categories": stat_categories}

    def _parse_stats_table(self, soup: BeautifulSoup) -> tuple[List[Dict[str, Any]], List[str]]:
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

        logger.debug(f"Parsed {len(players_data)} players with {len(stat_categories)} stat categories")

        return players_data, stat_categories
