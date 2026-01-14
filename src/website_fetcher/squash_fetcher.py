"""
ClubLocker Website Fetcher

Fetches squash statistics from clublocker.com
"""

import re
from typing import Dict, Any, List, Optional, Tuple
import logging
import time
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

from .base_fetcher import BaseFetcher, FetchResult


logger = logging.getLogger(__name__)


# Haverford College ClubLocker team IDs
CLUBLOCKER_TEAMS = {
    "squash_mens": 40879,
    # Add more teams as needed
}


class SquashFetcher(BaseFetcher):
    """
    Fetcher for ClubLocker squash statistics.

    Scrapes roster and match data from ClubLocker's Angular-based web interface.
    Requires Selenium WebDriver due to JavaScript-rendered content.
    """

    def __init__(self, base_url: str = "https://clublocker.com", timeout: int = 30):
        super().__init__(base_url, timeout)
        self.driver = None

    def fetch_team_stats(self, team_id: str, sport: str) -> FetchResult:
        """
        Fetch team roster and statistics from ClubLocker.

        Args:
            team_id: ClubLocker team ID (e.g., "40879")
            sport: Sport name (typically "squash")

        Returns:
            FetchResult with team roster data including player wins
        """
        try:
            logger.info(f"Fetching ClubLocker team stats for {team_id}")

            # 1. Initialize Selenium driver
            self._init_selenium_driver()

            # 2. Load roster page
            url = f"{self.base_url}/teams/{team_id}/roster"
            logger.debug(f"Loading URL: {url}")
            self.driver.get(url)

            # 3. Wait for Angular to render (ClubLocker is an Angular SPA)
            logger.debug("Waiting for Angular to render...")
            time.sleep(8)

            # 4. Parse with BeautifulSoup
            soup = BeautifulSoup(self.driver.page_source, "html.parser")

            # 5. Validate page loaded correctly
            page_error = self._check_for_page_errors(soup)
            if page_error:
                return FetchResult(success=False, error=page_error, source=self.name)

            # 6. Extract roster data
            players_data, season = self._parse_roster(soup)

            if not players_data:
                return FetchResult(
                    success=False,
                    error="No player data found on roster page",
                    source=self.name
                )

            # 7. Return structured result
            logger.info(f"Successfully fetched {len(players_data)} players for team {team_id}")
            return FetchResult(
                success=True,
                data={
                    "team_id": team_id,
                    "sport": sport,
                    "season": season,
                    "players": players_data,
                    "stat_categories": ["wins"]
                },
                source=self.name
            )

        except Exception as e:
            return self.handle_error(e, "fetching team stats")
        finally:
            self._close_driver()

    def fetch_player_stats(self, player_id: str, sport: str) -> FetchResult:
        """
        Fetch individual player statistics.

        Args:
            player_id: Player ID
            sport: Sport name

        Returns:
            FetchResult (not yet implemented)

        Note: This method is not yet implemented for ClubLocker.
        """
        try:
            logger.info(f"ClubLocker fetch_player_stats called for {player_id}")
            logger.warning("ClubLocker fetch_player_stats not yet implemented")
            return FetchResult(
                success=False,
                error="Not yet implemented",
                source=self.name
            )
        except Exception as e:
            return self.handle_error(e, "fetching player stats")

    def search_player(self, name: str, sport: str) -> FetchResult:
        """
        Search for players by name.

        Args:
            name: Player name to search for
            sport: Sport name

        Returns:
            FetchResult (not yet implemented)

        Note: This method is not yet implemented for ClubLocker.
        """
        try:
            logger.info(f"ClubLocker search_player called for {name}")
            logger.warning("ClubLocker search_player not yet implemented")
            return FetchResult(
                success=False,
                error="Not yet implemented",
                source=self.name
            )
        except Exception as e:
            return self.handle_error(e, "searching for player")

    # Private helper methods

    def _init_selenium_driver(self):
        """Initialize Chrome WebDriver with options for scraping."""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument(
            "--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.set_page_load_timeout(15)
        logger.debug("ClubLocker WebDriver initialized successfully")

    def _close_driver(self):
        """Close and cleanup WebDriver resources."""
        if self.driver:
            try:
                self.driver.quit()
                logger.debug("ClubLocker WebDriver closed")
            except Exception as e:
                logger.warning(f"Error closing WebDriver: {e}")
            finally:
                self.driver = None

    def _check_for_page_errors(self, soup: BeautifulSoup) -> Optional[str]:
        """
        Check if the page loaded correctly or has errors.

        Args:
            soup: BeautifulSoup object of the page

        Returns:
            Error message if page is invalid, None if valid
        """
        page_text = soup.get_text().lower()

        # Check for error indicators
        if "page not found" in page_text or "404" in page_text:
            return "Invalid team ID - page not found"

        if "not found" in page_text or "error" in page_text:
            return "Error loading roster page"

        # Check that we're not stuck on loading screen
        if "club locker is loading" in page_text and len(page_text) < 200:
            return "Page did not finish loading - Angular app initialization failed"

        logger.debug("Page validation passed")
        return None

    def _parse_roster(self, soup: BeautifulSoup) -> Tuple[List[Dict], str]:
        """
        Parse roster to extract player names and wins.

        Args:
            soup: BeautifulSoup object of the roster page

        Returns:
            Tuple of (players_data, season)
            - players_data: List of dicts with player name and stats
            - season: Season string (e.g., "2025-26")

        ClubLocker uses Angular Material table components with mat-row and mat-cell elements.
        """
        players_data = []
        season = self._extract_season(soup)

        logger.debug("Parsing ClubLocker Angular Material table structure...")

        # Find all player rows (Angular Material mat-row elements)
        rows = soup.find_all("mat-row", class_="mat-row")
        logger.debug(f"Found {len(rows)} mat-row elements")

        for row in rows:
            # Find player name cell (contains the player name)
            name_cell = row.find("mat-cell", class_=lambda x: x and "cdk-column-Players" in str(x) if x else False)

            # Find win/loss cell (contains "X/Y" format)
            win_loss_cell = row.find("mat-cell", class_=lambda x: x and "cdk-column-Win-Loss" in str(x) if x else False)

            if name_cell and win_loss_cell:
                # Extract player name (may be in an <a> tag)
                name_link = name_cell.find("a")
                name = name_link.text.strip() if name_link else name_cell.text.strip()

                # Extract wins from "X/Y" format
                win_loss_text = win_loss_cell.text.strip()
                wins = self._extract_wins_from_record(win_loss_text)

                if name:
                    logger.debug(f"  Found player: {name}, Wins: {wins}, Record: {win_loss_text}")
                    players_data.append({
                        "name": name,
                        "stats": {"wins": str(wins)}
                    })

        logger.info(f"Parsed {len(players_data)} players from ClubLocker roster")
        return players_data, season

    def _extract_wins_from_record(self, record_text: str) -> str:
        """
        Extract wins number from record text.

        Args:
            record_text: Text like "6/14" (wins/losses) or "10" (just wins)

        Returns:
            String with wins count
        """
        record_text = record_text.strip()

        # Handle "X/Y" format (wins/losses)
        if "/" in record_text:
            wins = record_text.split("/")[0].strip()
            return wins

        # Handle just a number
        if record_text.isdigit():
            return record_text

        # Default fallback
        logger.warning(f"Could not parse wins from record text: '{record_text}'")
        return "0"

    def _extract_season(self, soup: BeautifulSoup) -> str:
        """
        Extract season/year from page.

        Args:
            soup: BeautifulSoup object of the page

        Returns:
            Season string (e.g., "2025-26")

        Looks for patterns like "2025-26", "2026", "Fall 2025", etc.
        Falls back to current academic year if not found.
        """
        # Look in page title
        title = soup.find("title")
        if title:
            match = re.search(r'20\d{2}(?:-\d{2})?', title.text)
            if match:
                logger.debug(f"Found season in title: {match.group(0)}")
                return match.group(0)

        # Look in headers and prominent text
        for tag in soup.find_all(["h1", "h2", "h3", "span"], limit=20):
            text = tag.text.strip()
            match = re.search(r'20\d{2}(?:-\d{2})?', text)
            if match:
                logger.debug(f"Found season in {tag.name}: {match.group(0)}")
                return match.group(0)

        # Fallback: use current academic year
        year = datetime.now().year
        month = datetime.now().month

        if month >= 7:  # July or later = new academic year starting
            season = f"{year}-{str(year+1)[-2:]}"
        else:
            season = f"{year-1}-{str(year)[-2:]}"

        logger.debug(f"Using fallback season: {season}")
        return season
