"""
TFRR (Track & Field Results Reporting) Fetcher

Fetches statistics from tfrrs.org
"""

import requests
from typing import Dict, Any, List, Optional
import logging
import time
import re

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


# Haverford College TFRR team codes
# Format: /teams/PA_college_m_Haverford.html or /teams/PA_college_f_Haverford.html
HAVERFORD_TEAMS = {
    "mens_track": "PA_college_m_Haverford",
    "womens_track": "PA_college_f_Haverford",
    "mens_cross_country": "PA_college_m_Haverford",
    "womens_cross_country": "PA_college_f_Haverford",
}


class TFRRFetcher(BaseFetcher):
    """
    Fetcher for TFRR (Track & Field Results Reporting) website.

    Handles both track & field and cross country statistics.
    """

    def __init__(self, base_url: str = "https://www.tfrrs.org", timeout: int = 30):
        super().__init__(base_url, timeout)
        self.driver = None

    def fetch_player_stats(self, player_id: str, sport: str) -> FetchResult:
        """
        Fetch athlete statistics from TFRR.

        Args:
            player_id: TFRR athlete ID
            sport: Either "track" or "cross_country"

        Returns:
            FetchResult with athlete statistics including PRs
        """
        try:
            logger.info(f"Fetching TFRR athlete stats for {player_id} in {sport}")

            # Initialize Selenium driver
            self._init_selenium_driver()

            # Navigate to athlete page
            athlete_url = f"{self.base_url}/athletes/{player_id}.html"
            logger.debug(f"Fetching URL: {athlete_url}")
            self.driver.get(athlete_url)

            # Wait for page to load
            time.sleep(2)

            # Get page source and parse with BeautifulSoup
            soup = BeautifulSoup(self.driver.page_source, "html.parser")

            # Check if page is valid
            page_error = self._check_for_page_errors(soup)
            if page_error:
                logger.error(f"Invalid athlete page for {player_id}: {page_error}")
                return FetchResult(
                    success=False,
                    error=page_error,
                    source=self.name,
                )

            # Parse athlete data
            athlete_data = self._parse_athlete_data(soup, player_id, sport)

            if not athlete_data:
                logger.warning(f"No data found for athlete {player_id}")
                return FetchResult(
                    success=False,
                    error="No athlete data found",
                    source=self.name,
                )

            logger.info(f"Successfully fetched stats for athlete {player_id}")
            return FetchResult(success=True, data=athlete_data, source=self.name)

        except Exception as e:
            return self.handle_error(e, "fetching athlete stats")

        finally:
            self._close_driver()

    def fetch_team_stats(self, team_code: str, sport: str) -> FetchResult:
        """
        Fetch team statistics from TFRR.

        Args:
            team_code: TFRR team code (e.g., "PA_college_m_Haverford")
            sport: Either "track" or "cross_country"

        Returns:
            FetchResult with team statistics and roster

        Example data format:
        {
            "team_code": "PA_college_m_Haverford",
            "team_name": "Haverford College",
            "sport": "track",
            "season": "Indoor 2026",
            "athletes": [
                {
                    "name": "John Doe",
                    "year": "JR",
                    "events": {
                        "60m": "7.25",
                        "200m": "23.45",
                        ...
                    }
                }
            ],
            "event_categories": ["60m", "200m", ...]
        }
        """
        try:
            logger.info(f"Fetching TFRR team stats for team {team_code} in {sport}")

            # Initialize Selenium driver
            self._init_selenium_driver()

            # Navigate to team page
            team_url = f"{self.base_url}/teams/{team_code}.html"
            logger.debug(f"Fetching URL: {team_url}")
            self.driver.get(team_url)

            # Wait for page to load
            time.sleep(3)

            # Get page source and parse with BeautifulSoup
            soup = BeautifulSoup(self.driver.page_source, "html.parser")

            # Check if page is valid
            page_error = self._check_for_page_errors(soup)
            if page_error:
                logger.error(f"Invalid team page for {team_code}: {page_error}")
                return FetchResult(
                    success=False,
                    error=page_error,
                    source=self.name,
                )

            # Extract team name and season
            team_name = self._get_team_name(soup)
            season = self._get_season_from_page(soup)

            # Parse the roster and PRs
            athletes_data, event_categories = self._parse_team_roster(soup, sport)

            if not athletes_data:
                logger.warning(f"No athlete data found for team {team_code}")
                return FetchResult(
                    success=False,
                    error="No athlete data available yet (season may not have started)",
                    source=self.name,
                )

            # Build result data
            data = {
                "team_code": team_code,
                "team_name": team_name,
                "sport": sport,
                "season": season,
                "athletes": athletes_data,
                "event_categories": event_categories,
            }

            logger.info(
                f"Successfully fetched stats for {len(athletes_data)} athletes from team {team_code}"
            )

            return FetchResult(success=True, data=data, source=self.name)

        except Exception as e:
            return self.handle_error(e, "fetching team stats")

        finally:
            self._close_driver()

    def search_player(self, name: str, sport: str) -> FetchResult:
        """
        Search for an athlete on TFRR.

        Args:
            name: Athlete name
            sport: Either "track" or "cross_country"

        Returns:
            FetchResult with list of matching athletes
        """
        try:
            logger.info(f"Searching TFRR for athlete {name} in {sport}")

            # TFRR search is complex and requires form submission
            # For now, we'll implement a basic version
            logger.warning("TFRR search_player not yet fully implemented")
            return FetchResult(success=False, error="Search not yet implemented", source=self.name)

        except Exception as e:
            return self.handle_error(e, "searching for athlete")

    def fetch_event_results(self, athlete_id: str, event_name: str) -> FetchResult:
        """
        Fetch results for a specific event for an athlete.

        Args:
            athlete_id: TFRR athlete ID
            event_name: Event name (e.g., "100m", "5000m", "High Jump")

        Returns:
            FetchResult with event-specific results and PRs
        """
        try:
            logger.info(f"Fetching TFRR event results for athlete {athlete_id}, event {event_name}")

            # This would require navigating to athlete page and filtering by event
            # For simplicity, we'll use fetch_player_stats and filter
            result = self.fetch_player_stats(athlete_id, "track")

            if not result.success:
                return result

            # Filter for specific event
            athlete_data = result.data
            if "events" in athlete_data and event_name in athlete_data["events"]:
                filtered_data = {
                    "athlete_id": athlete_id,
                    "name": athlete_data.get("name", ""),
                    "event": event_name,
                    "result": athlete_data["events"][event_name]
                }
                return FetchResult(success=True, data=filtered_data, source=self.name)
            else:
                return FetchResult(
                    success=False,
                    error=f"Event {event_name} not found for athlete",
                    source=self.name
                )

        except Exception as e:
            return self.handle_error(e, "fetching event results")

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

    def _check_for_page_errors(self, soup: BeautifulSoup) -> Optional[str]:
        """
        Check if the page is an error page or invalid page.

        Args:
            soup: BeautifulSoup object of the page

        Returns:
            Error message if page is invalid, None if page is valid
        """
        page_text = soup.get_text().lower()

        # Check for common error indicators
        if "page not found" in page_text or "404" in page_text:
            return "Invalid ID - page not found"

        if "no results found" in page_text:
            return "Invalid ID - no results found"

        # Check if page has expected TFRR content
        has_tfrr_context = False

        # Look for TFRR-specific elements
        if soup.find("div", class_="custom-table-container") or \
           soup.find("table", class_="bests") or \
           soup.find("h3", string=re.compile("Personal Records", re.I)) or \
           soup.find("div", id="meet-results"):
            has_tfrr_context = True

        if not has_tfrr_context:
            # Check for any table (might have data in different format)
            if soup.find("table"):
                has_tfrr_context = True

        if not has_tfrr_context:
            return "Invalid page - does not contain expected TFRR data"

        return None

    def _get_team_name(self, soup: BeautifulSoup) -> str:
        """Extract team name from page."""
        # Try to find team name in header
        header = soup.find("h1") or soup.find("h2")
        if header:
            return header.text.strip()

        # Fallback
        return "Haverford College"

    def _get_season_from_page(self, soup: BeautifulSoup) -> str:
        """
        Extract the season from the page.

        Args:
            soup: BeautifulSoup object of the page

        Returns:
            Season string (e.g., "Indoor 2026") or "Unknown"
        """
        # Try to find season in page title or headers
        title = soup.find("title")
        if title and title.text:
            # TFRR pages often have format like "Haverford College - Indoor 2026"
            match = re.search(r"(Indoor|Outdoor|Cross Country)\s+(\d{4})", title.text)
            if match:
                return f"{match.group(1)} {match.group(2)}"

        # Try to find in headers
        for element in soup.find_all(["h1", "h2", "h3", "span"]):
            if element.text:
                match = re.search(r"(Indoor|Outdoor|Cross Country)\s+(\d{4})", element.text)
                if match:
                    return f"{match.group(1)} {match.group(2)}"

        logger.warning("Could not extract season from page")
        return "Unknown"

    def _parse_athlete_data(self, soup: BeautifulSoup, athlete_id: str, sport: str) -> Dict[str, Any]:
        """
        Parse TFRR athlete data from response.

        TFRR athlete pages have PR tables where each event gets its own table.
        The table header contains the event name, and the first data row contains
        the best mark/time.

        Args:
            soup: BeautifulSoup object
            athlete_id: Athlete ID
            sport: Sport type

        Returns:
            Standardized athlete data dictionary with PRs
        """
        athlete_data = {
            "athlete_id": athlete_id,
            "name": "",
            "year": "",
            "sport": sport,
            "events": {}
        }

        # Extract athlete name
        name_elem = soup.find("h3") or soup.find("h2") or soup.find("h1")
        if name_elem:
            athlete_data["name"] = name_elem.text.strip()

        # Parse PR tables - TFRR has one table per event
        # Look for tables with event names in the header (like "60 Meters", "Long Jump", etc.)
        all_tables = soup.find_all("table")

        for table in all_tables:
            # Get the header row
            header_row = table.find("tr")
            if not header_row:
                continue

            # Get header cells
            header_cells = header_row.find_all(["th", "td"])
            if not header_cells:
                continue

            # Check if this looks like an event PR table
            # Event tables have format: "Event Name (Indoor)" or "Event Name (Outdoor)"
            first_header = header_cells[0].get_text(strip=True)

            # Look for event patterns like "60 Meters", "Long Jump", etc.
            # These tables have the event name in the header and PR in first data row
            if any(keyword in first_header.lower() for keyword in ['meters', 'jump', 'throw', 'hurdles', 'vault', 'run']):
                # This looks like an event PR table
                event_name = re.sub(r'\s*\(Indoor\).*|\s*\(Outdoor\).*|Top↑', '', first_header).strip()

                # Get the first data row (contains the PR)
                data_rows = table.find_all("tr")[1:]  # Skip header
                if data_rows:
                    first_data_row = data_rows[0]
                    data_cells = first_data_row.find_all(["td", "th"])

                    if data_cells:
                        # The PR is in the first cell
                        pr_value = data_cells[0].get_text(strip=True)

                        # Clean up the PR value (remove extra text like meet names)
                        # TFRR format is often like "7.59" or "6.52m21' 4.75"" or "14.25m46' 9""
                        # Keep just the primary measurement
                        # Skip if it's just a year (like "2025") - these are year-by-year tables
                        if pr_value and pr_value != "NM" and pr_value != "NMNM" and not re.match(r'^\d{4}$', pr_value):
                            athlete_data["events"][event_name] = pr_value

        return athlete_data if athlete_data["name"] or athlete_data["events"] else None

    def _parse_team_roster(
        self, soup: BeautifulSoup, sport: str
    ) -> tuple[List[Dict[str, Any]], List[str]]:
        """
        Parse the team roster and PRs from TFRR page.

        This method extracts athlete links from the roster page, then visits
        each athlete's individual page to scrape their Personal Records (PRs).

        Args:
            soup: BeautifulSoup object of the page
            sport: Sport type

        Returns:
            Tuple of (athletes_data, event_categories)
        """
        athletes_data = []
        event_categories = set()

        # Find the main roster table
        tables = soup.find_all("table")

        if not tables:
            logger.warning("No tables found on page")
            return athletes_data, list(event_categories)

        # Find the roster table (has athlete names/links)
        roster_table = None
        max_rows = 0

        for table in tables:
            rows = table.find_all("tr")
            if len(rows) > max_rows and len(rows) > 2:
                # Check if it looks like an athlete roster
                header_row = rows[0]
                header_text = header_row.get_text().lower()
                if "name" in header_text or "athlete" in header_text:
                    roster_table = table
                    max_rows = len(rows)

        if not roster_table:
            # Just use the first substantial table
            for table in tables:
                rows = table.find_all("tr")
                if len(rows) > 2:
                    roster_table = table
                    break

        if not roster_table:
            logger.warning("No suitable roster table found")
            return athletes_data, list(event_categories)

        # Extract athlete links and basic info from roster
        athlete_links = []
        data_rows = roster_table.find_all("tr")[1:]  # Skip header

        for row in data_rows:
            cells = row.find_all(["td", "th"])
            if len(cells) < 2:
                continue

            # Find athlete link and year
            athlete_name = ""
            athlete_year = ""
            athlete_href = None

            for i, cell in enumerate(cells):
                # Look for athlete link (usually in first column)
                athlete_link = cell.find("a", href=lambda x: x and "/athletes/" in x)
                if athlete_link:
                    athlete_name = athlete_link.text.strip()
                    athlete_href = athlete_link.get("href")

                # Try to find year (usually in second column)
                cell_text = cell.text.strip()
                if re.match(r"(FR|SO|JR|SR)(-\d)?", cell_text):
                    athlete_year = cell_text

            if athlete_name and athlete_href:
                athlete_links.append({
                    "name": athlete_name,
                    "year": athlete_year,
                    "href": athlete_href
                })

        logger.info(f"Found {len(athlete_links)} athlete links on roster page")

        # Visit each athlete's page to get their PRs
        for idx, athlete_info in enumerate(athlete_links, 1):
            try:
                logger.info(f"Fetching PRs for athlete {idx}/{len(athlete_links)}: {athlete_info['name']}")

                # Navigate to athlete page with retry logic
                athlete_url = f"{self.base_url}{athlete_info['href']}"

                try:
                    self.driver.set_page_load_timeout(10)  # Shorter timeout per page
                    self.driver.get(athlete_url)
                    time.sleep(0.5)  # Brief pause
                except Exception as timeout_error:
                    logger.warning(f"Timeout loading page for {athlete_info['name']}, skipping")
                    athletes_data.append({
                        "name": athlete_info["name"],
                        "year": athlete_info["year"],
                        "events": {}
                    })
                    continue

                # Parse athlete page
                athlete_soup = BeautifulSoup(self.driver.page_source, "html.parser")

                # Extract athlete ID from URL
                athlete_id = athlete_info['href'].split('/')[-1].replace('.html', '')

                # Parse PRs from athlete page
                athlete_data = self._parse_athlete_data(athlete_soup, athlete_id, sport)

                if athlete_data:
                    # Use roster info for name/year (more reliable)
                    athlete_data["name"] = athlete_info["name"]
                    athlete_data["year"] = athlete_info["year"]

                    # Track all event categories
                    for event in athlete_data.get("events", {}).keys():
                        event_categories.add(event)

                    athletes_data.append(athlete_data)

                    # Log progress
                    if len(athlete_data.get("events", {})) > 0:
                        logger.info(f"  ✓ Found {len(athlete_data['events'])} PRs")
                else:
                    # Still add athlete even if no PRs found
                    athletes_data.append({
                        "name": athlete_info["name"],
                        "year": athlete_info["year"],
                        "events": {}
                    })
                    logger.info(f"  - No PRs found")

            except Exception as e:
                logger.warning(f"Error fetching PRs for {athlete_info['name']}: {e}")
                # Add athlete with no events rather than skipping
                athletes_data.append({
                    "name": athlete_info["name"],
                    "year": athlete_info["year"],
                    "events": {}
                })

        logger.info(
            f"Successfully parsed {len(athletes_data)} athletes with {len(event_categories)} event categories"
        )

        return athletes_data, sorted(list(event_categories))
