"""
TFRR (Track & Field Results Reporting) Fetcher

Fetches statistics from tfrrs.org
"""

import requests
from typing import Dict, Any, List, Optional
import logging
from bs4 import BeautifulSoup
import re
import time

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

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
        # Set headers to mimic a browser request and avoid 403 errors
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }

    def fetch_player_stats(self, player_id: str, sport: str) -> FetchResult:
        """
        Fetch athlete statistics from TFRR.

        Args:
            player_id: TFRR athlete ID
            sport: Either "track" or "cross_country" (determines subdomain)

        Returns:
            FetchResult with athlete statistics including PRs
        """
        try:
            logger.info(f"Fetching TFRR athlete stats for {player_id} in {sport}")

            # Determine subdomain based on sport
            if sport.lower() in ["cross_country", "xc", "cross country"]:
                url = f"https://xc.tfrrs.org/athletes/{player_id}.html"
            else:
                url = f"{self.base_url}/athletes/{player_id}.html"

            response = requests.get(url, headers=self.headers, timeout=self.timeout)

            if self.validate_response(response):
                data = self._parse_athlete_data_from_html(response.content, sport, url)
                if data and data.get('personal_records'):
                    return FetchResult(success=True, data=data, source=self.name)

            # Fallback to Selenium if needed
            logger.debug(f"Falling back to Selenium for athlete {player_id}")
            self._init_driver()
            self.driver.get(url)
            time.sleep(2)  # Wait for content to load
            page_source = self.driver.page_source

            data = self._parse_athlete_data_from_html(page_source, sport, url)
            if data:
                return FetchResult(success=True, data=data, source=self.name)
            else:
                return FetchResult(
                    success=False, error="Failed to parse athlete data", source=self.name
                )

        except Exception as e:
            return self.handle_error(e, "fetching athlete stats")

    def fetch_team_stats(self, team_code: str, sport: str) -> FetchResult:
        """
        Fetch team statistics from TFRR.

        Args:
            team_code: TFRR team code (e.g., "PA_college_m_Haverford")
            sport: Either "track" or "cross_country"

        Returns:
            FetchResult with team statistics and roster
        """
        try:
            logger.info(f"Fetching TFRR team stats for {team_code} in {sport}")

            # Determine subdomain based on sport
            if sport.lower() in ["cross_country", "xc", "cross country"]:
                url = f"https://xc.tfrrs.org/teams/{team_code}.html"
            else:
                url = f"{self.base_url}/teams/{team_code}.html"

            response = requests.get(url, headers=self.headers, timeout=self.timeout)

            # Load the page
            self.driver.get(url)

            # Wait longer for JavaScript to fully render
            time.sleep(5)  # Give page time to fully load

            # Wait for roster section to appear
            try:
                WebDriverWait(self.driver, 15).until(
                    lambda driver: driver.find_element(By.TAG_NAME, "h3")
                )
                time.sleep(2)  # Additional wait for dynamic content to stabilize
            except Exception as e:
                logger.warning(f"Timeout waiting for page content: {e}")

            # Get the page source after JavaScript execution
            page_source = self.driver.page_source

            data = self._parse_team_data_from_html(page_source, sport, url)
            if data:
                return FetchResult(success=True, data=data, source=self.name)
            else:
                return FetchResult(
                    success=False, error="Failed to parse team data", source=self.name
                )

        except Exception as e:
            return self.handle_error(e, "fetching team stats")

        finally:
            self._close_driver()

    def _parse_team_data(self, response, sport: str) -> Optional[Dict[str, Any]]:
        """
        Parse TFRR team data from response (for requests library).

        Args:
            response: HTTP response
            sport: Sport type

        Returns:
            Team data dictionary with roster and stats
        """
        return self._parse_team_data_from_html(response.content, sport, response.url)

    def _parse_team_data_from_html(self, html_content, sport: str, url: str) -> Optional[Dict[str, Any]]:
        """
        Parse TFRR team data from HTML content.

        Args:
            html_content: HTML content (string or bytes)
            sport: Sport type
            url: Page URL

        Returns:
            Team data dictionary with roster and stats
        """
        try:
            soup = BeautifulSoup(html_content, "html.parser")

            # Extract team name
            name_elem = soup.find("h3") or soup.find("h2")
            team_name = name_elem.text.strip() if name_elem else "Unknown"

            # Extract conference/division info
            conference = ""
            conf_elem = soup.find(text=re.compile("Conference|Division"))
            if conf_elem:
                conference = conf_elem.find_parent().text.strip()

            # Extract roster
            roster = self._extract_roster(soup)

            # Extract team rankings if available
            rankings = self._extract_team_rankings(soup)

            team_data = {
                "team_id": self._extract_team_id(url),
                "name": team_name,
                "sport": sport,
                "conference": conference,
                "roster": roster,
                "rankings": rankings,
                "profile_url": url,
            }

            logger.info(f"Successfully parsed team data for {team_name}: {len(roster)} athletes")
            return team_data

        except Exception as e:
            logger.error(f"Error parsing team data: {e}")
            return None

    def _extract_team_id(self, url: str) -> str:
        """Extract team ID from URL."""
        match = re.search(r"/teams/(\w+)", url)
        return match.group(1) if match else ""

    def _extract_roster(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extract team roster from page."""
        roster = []
        try:
            # Look for tables with athlete links - TFRR uses "tablesaw" class
            tables = soup.find_all("table", class_="tablesaw")

            # Find the table with the most athlete links (usually the roster)
            best_table = None
            max_athletes = 0

            for table in tables:
                athlete_links = table.find_all("a", href=re.compile(r"/athletes/"))
                if len(athlete_links) > max_athletes:
                    max_athletes = len(athlete_links)
                    best_table = table

            if best_table:
                logger.debug(f"Found roster table with {max_athletes} athletes")
                rows = best_table.find_all("tr")
                for row in rows[1:]:  # Skip header
                    athlete_link = row.find("a", href=re.compile(r"/athletes/"))
                    if athlete_link:
                        cols = row.find_all("td")
                        athlete = {
                            "name": athlete_link.text.strip(),
                            "athlete_id": self._extract_athlete_id(athlete_link["href"]),
                            "year": cols[1].text.strip() if len(cols) > 1 else "",
                        }
                        roster.append(athlete)

                logger.info(f"Extracted {len(roster)} athletes from roster")

            # Method 3: Find all athlete links on page (last resort)
            if not roster:
                all_athlete_links = soup.find_all("a", href=re.compile(r"/athletes/\d+/Haverford/"))
                seen_ids = set()
                for link in all_athlete_links:
                    athlete_id = self._extract_athlete_id(link["href"])
                    if athlete_id and athlete_id not in seen_ids:
                        seen_ids.add(athlete_id)
                        athlete = {
                            "name": link.text.strip(),
                            "athlete_id": athlete_id,
                            "year": "",
                        }
                        roster.append(athlete)

        except Exception as e:
            logger.warning(f"Error extracting roster: {e}")

        return roster

    def _extract_team_rankings(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract team ranking information."""
        rankings = {}
        try:
            ranking_elem = soup.find(class_=re.compile("rank|rating"))
            if ranking_elem:
                rankings["current_rank"] = ranking_elem.text.strip()

        except Exception as e:
            logger.warning(f"Error extracting rankings: {e}")

        return rankings

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

            # TFRRS search URL pattern
            # Note: TFRRS doesn't have a direct search API, so we construct a search URL
            search_url = f"{self.base_url}/search.html"
            params = {"q": name, "type": "athlete"}

            response = requests.get(search_url, params=params, headers=self.headers, timeout=self.timeout)

            if not self.validate_response(response):
                return FetchResult(
                    success=False, error="Invalid search response", source=self.name
                )

            athletes = self._parse_search_results(response, sport)

            if athletes is not None:
                return FetchResult(
                    success=True,
                    data={"athletes": athletes, "count": len(athletes)},
                    source=self.name,
                )
            else:
                return FetchResult(
                    success=False, error="Failed to parse search results", source=self.name
                )

        except Exception as e:
            return self.handle_error(e, "searching for athlete")

    def _parse_search_results(
        self, response, sport: str
    ) -> Optional[List[Dict[str, str]]]:
        """
        Parse search results page.

        Args:
            response: HTTP response from search
            sport: Sport filter

        Returns:
            List of athlete dictionaries with id, name, team
        """
        try:
            soup = BeautifulSoup(response.content, "html.parser")
            athletes = []

            # Look for athlete links in search results
            # TFRRS typically shows results in a list or table format
            athlete_links = soup.find_all("a", href=re.compile(r"/athletes/\d+"))

            for link in athlete_links:
                athlete_id = self._extract_athlete_id(link["href"])
                name = link.text.strip()

                # Try to find associated team info
                parent = link.find_parent("tr") or link.find_parent("div")
                team = ""
                if parent:
                    team_elem = parent.find(class_=re.compile("team|school"))
                    if team_elem:
                        team = team_elem.text.strip()

                athletes.append({"athlete_id": athlete_id, "name": name, "team": team})

            logger.info(f"Found {len(athletes)} athletes matching search")
            return athletes

        except Exception as e:
            logger.error(f"Error parsing search results: {e}")
            return None

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
            logger.info(
                f"Fetching TFRR event results for athlete {athlete_id}, event {event_name}"
            )

            # Fetch the athlete's full profile first
            url = f"{self.base_url}/athletes/{athlete_id}.html"
            response = requests.get(url, headers=self.headers, timeout=self.timeout)

            if not self.validate_response(response):
                return FetchResult(
                    success=False, error="Invalid response from TFRRS", source=self.name
                )

            # Parse and filter for specific event
            event_data = self._parse_event_specific_data(response, event_name)

            if event_data:
                return FetchResult(success=True, data=event_data, source=self.name)
            else:
                return FetchResult(
                    success=False,
                    error=f"No results found for event: {event_name}",
                    source=self.name,
                )

        except Exception as e:
            return self.handle_error(e, "fetching event results")

    def _parse_event_specific_data(
        self, response, event_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Parse event-specific data from athlete profile.

        Args:
            response: HTTP response
            event_name: Event to filter for

        Returns:
            Dictionary with event-specific results and PR
        """
        try:
            soup = BeautifulSoup(response.content, "html.parser")

            # Find PR for this event
            event_pr = None
            pr_tables = soup.find_all("table", class_=re.compile("bests|records"))

            for table in pr_tables:
                rows = table.find_all("tr")
                for row in rows:
                    cols = row.find_all("td")
                    if len(cols) >= 2:
                        event = cols[0].text.strip()
                        if event_name.lower() in event.lower() or event.lower() in event_name.lower():
                            event_pr = {
                                "event": event,
                                "mark": cols[1].text.strip(),
                                "date": cols[2].text.strip() if len(cols) > 2 else "",
                                "meet": cols[3].text.strip() if len(cols) > 3 else "",
                            }
                            break

            # Find all results for this event
            event_results = []
            result_tables = soup.find_all("table", class_=re.compile("results|performances"))

            for table in result_tables:
                rows = table.find_all("tr")
                for row in rows[1:]:  # Skip header
                    cols = row.find_all("td")
                    if len(cols) >= 3:
                        event_col = None
                        # Find which column has the event name
                        for i, col in enumerate(cols):
                            if event_name.lower() in col.text.strip().lower():
                                event_col = i
                                break

                        if event_col is not None:
                            result = {
                                "date": cols[0].text.strip() if len(cols) > 0 else "",
                                "meet": cols[1].text.strip() if len(cols) > 1 else "",
                                "event": cols[event_col].text.strip(),
                                "mark": (
                                    cols[event_col + 1].text.strip()
                                    if len(cols) > event_col + 1
                                    else ""
                                ),
                                "place": (
                                    cols[event_col + 2].text.strip()
                                    if len(cols) > event_col + 2
                                    else ""
                                ),
                            }
                            event_results.append(result)

            if event_pr or event_results:
                return {
                    "athlete_id": self._extract_athlete_id(response.url),
                    "event": event_name,
                    "personal_record": event_pr,
                    "results": event_results,
                    "total_results": len(event_results),
                }

            return None

        except Exception as e:
            logger.error(f"Error parsing event-specific data: {e}")
            return None

    def _parse_athlete_data(self, response, sport: str) -> Optional[Dict[str, Any]]:
        """
        Parse TFRR athlete data from response (for requests library).

        Args:
            response: HTTP response
            sport: Sport type for context

        Returns:
            Standardized athlete data dictionary with PRs
        """
        return self._parse_athlete_data_from_html(response.content, sport, response.url)

    def _parse_athlete_data_from_html(self, html_content, sport: str, url: str) -> Optional[Dict[str, Any]]:
        """
        Parse TFRR athlete data from HTML content.

        TFRR athlete pages have PR tables where each event gets its own table.
        The table header contains the event name, and the first data row contains
        the best mark/time.

        Args:
            html_content: HTML content (string or bytes)
            sport: Sport type for context
            url: Page URL

        Returns:
            Standardized athlete data dictionary with PRs
        """
        try:
            soup = BeautifulSoup(html_content, "html.parser")

            # Extract athlete name
            name_elem = soup.find("h3")
            name = name_elem.text.strip() if name_elem else "Unknown"

            # Extract school/team
            team_elem = soup.find("div", class_="team-name") or soup.find("h4")
            team = team_elem.text.strip() if team_elem else "Unknown"

            # Extract personal records (PRs)
            prs = self._extract_personal_records(soup)

            # Extract recent results
            recent_results = self._extract_recent_results(soup)

            # Extract athlete bio info
            bio_info = self._extract_bio_info(soup)

            athlete_data = {
                "athlete_id": self._extract_athlete_id(url),
                "name": name,
                "team": team,
                "sport": sport,
                "personal_records": prs,
                "recent_results": recent_results,
                "bio": bio_info,
                "profile_url": url,
            }

            logger.info(f"Successfully parsed athlete data for {name}: {len(prs)} PRs")
            return athlete_data

        except Exception as e:
            logger.error(f"Error parsing athlete data: {e}")
            return None

    def _extract_athlete_id(self, url: str) -> str:
        """Extract athlete ID from URL."""
        match = re.search(r"/athletes/(\w+)", url)
        return match.group(1) if match else ""

    def _extract_personal_records(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract personal records from athlete profile."""
        prs = {}
        try:
            # Look for PR tables - TFRRS typically has tables with class 'bests' or similar
            pr_tables = soup.find_all("table", class_=re.compile("bests|records"))

            for table in pr_tables:
                rows = table.find_all("tr")
                for row in rows[1:]:  # Skip header row
                    cols = row.find_all("td")
                    if len(cols) >= 2:
                        event = cols[0].text.strip()
                        mark_raw = cols[1].text.strip()

                        # Clean the mark: take only the first line, remove wind info and imperial conversions
                        # Examples: "22.75\n(0.1)" -> "22.75", "6.18m\n\n20' 3.5\"" -> "6.18m"

                        # First split by newline to isolate the metric value (always comes first)
                        lines = mark_raw.split('\n')
                        if not lines:
                            continue

                        # Take first non-empty line
                        mark = lines[0].strip()

                        # Remove wind speed indicators in parentheses: "22.75 (0.1)" -> "22.75"
                        mark = re.sub(r'\s*\([+-]?\d+\.?\d*\)\s*', '', mark).strip()

                        # Remove any imperial measurements (feet/inches) if they leaked through
                        # Pattern: remove anything with feet (') or inches (")
                        mark = re.sub(r"[\s]*\d+['\"][\s\d.\"']*", '', mark).strip()

                        if mark and mark != '-' and mark != '—':
                            prs[event] = mark

            # Also check for divs with PR data
            if not prs:
                pr_divs = soup.find_all("div", class_=re.compile("pr-|best-"))
                for div in pr_divs:
                    event_elem = div.find(class_=re.compile("event"))
                    mark_elem = div.find(class_=re.compile("mark|time"))
                    if event_elem and mark_elem:
                        prs[event_elem.text.strip()] = mark_elem.text.strip()

        except Exception as e:
            logger.warning(f"Error extracting PRs: {e}")

        return prs

    def _extract_recent_results(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract recent competition results."""
        results = []
        try:
            # Look for results tables
            result_tables = soup.find_all("table", class_=re.compile("results|performances"))

            for table in result_tables[:1]:  # Just get the first/main results table
                rows = table.find_all("tr")
                for row in rows[1:6]:  # Get up to 5 recent results
                    cols = row.find_all("td")
                    if len(cols) >= 3:
                        result = {
                            "date": cols[0].text.strip() if len(cols) > 0 else "",
                            "meet": cols[1].text.strip() if len(cols) > 1 else "",
                            "event": cols[2].text.strip() if len(cols) > 2 else "",
                            "mark": cols[3].text.strip() if len(cols) > 3 else "",
                            "place": cols[4].text.strip() if len(cols) > 4 else "",
                        }
                        results.append(result)

        except Exception as e:
            logger.warning(f"Error extracting recent results: {e}")

        return results

    def _extract_bio_info(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract biographical information."""
        bio = {}
        try:
            # Look for bio panel or info section
            bio_section = soup.find("div", class_=re.compile("bio|info|profile-info"))
            if bio_section:
                # Extract common fields
                for field in ["year", "class", "eligibility", "hometown", "high_school"]:
                    elem = bio_section.find(text=re.compile(field, re.IGNORECASE))
                    if elem:
                        parent = elem.find_parent()
                        if parent:
                            bio[field] = parent.text.strip()

        except Exception as e:
            logger.warning(f"Error extracting bio info: {e}")

        return bio

    def _init_driver(self):
        """Initialize Selenium WebDriver for JavaScript-rendered pages."""
        if self.driver is not None:
            return

        logger.debug("Initializing Selenium WebDriver for TFRR...")

        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument(
            "--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
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
                logger.debug("WebDriver closed")
            except Exception as e:
                logger.warning(f"Error closing WebDriver: {e}")
            finally:
                self.driver = None
