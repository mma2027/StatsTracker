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
import random

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from .base_fetcher import BaseFetcher, FetchResult


logger = logging.getLogger(__name__)

# Pool of realistic user agents to rotate through
USER_AGENTS = [
    (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
    ),
    (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
    ),
    (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
        "(KHTML, like Gecko) Version/17.1 Safari/605.1.15"
    ),
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
]


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
        self.session = requests.Session()  # Persistent session for cookies
        self.request_count = 0  # Track number of requests
        self.last_request_time = 0  # Track last request timestamp
        self.consecutive_errors = 0  # Track consecutive errors for backoff

        # Browser headers to avoid 403 blocking
        self.headers = {
            "User-Agent": random.choice(USER_AGENTS),  # Random user agent
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "DNT": "1",  # Do Not Track
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
        }

    def _get_random_user_agent(self) -> str:
        """Get a random user agent from the pool."""
        return random.choice(USER_AGENTS)

    def _smart_delay(self):
        """
        Implement smart delay between requests to avoid rate limiting.
        Uses randomized delays with exponential backoff on errors.
        """
        # Base delay: 3-7 seconds (randomized)
        base_delay = random.uniform(3.0, 7.0)

        # Add exponential backoff if we've had consecutive errors
        if self.consecutive_errors > 0:
            backoff = min(2**self.consecutive_errors, 60)  # Max 60 seconds
            jitter = random.uniform(0, backoff * 0.3)  # Add 0-30% jitter
            total_delay = base_delay + backoff + jitter
            logger.info(f"Exponential backoff: {total_delay:.1f}s ({self.consecutive_errors} consecutive errors)")
        else:
            total_delay = base_delay

        # Ensure minimum time between requests
        time_since_last = time.time() - self.last_request_time
        if time_since_last < total_delay:
            time.sleep(total_delay - time_since_last)

        self.last_request_time = time.time()
        self.request_count += 1

        # Every 10-15 requests, take a longer break
        if self.request_count % random.randint(10, 15) == 0:
            extended_delay = random.uniform(15.0, 30.0)
            logger.info(f"Taking extended break: {extended_delay:.1f}s after {self.request_count} requests")
            time.sleep(extended_delay)

    def _make_request_with_retry(self, url: str, max_retries: int = 3) -> Optional[requests.Response]:
        """
        Make HTTP request with exponential backoff retry logic.

        Args:
            url: URL to fetch
            max_retries: Maximum number of retry attempts

        Returns:
            Response object if successful, None otherwise
        """
        for attempt in range(max_retries):
            try:
                # Rotate user agent on retries
                if attempt > 0:
                    self.headers["User-Agent"] = self._get_random_user_agent()
                    logger.info(f"Retry attempt {attempt + 1}/{max_retries} with new user agent")

                # Apply smart delay before request
                if self.request_count > 0:  # Skip delay on first request
                    self._smart_delay()

                response = self.session.get(url, headers=self.headers, timeout=self.timeout)

                # Check for rate limiting or blocking
                if response.status_code == 403:
                    logger.warning(f"403 Forbidden - likely rate limited or blocked (attempt {attempt + 1})")
                    self.consecutive_errors += 1

                    # Wait progressively longer on 403s
                    if attempt < max_retries - 1:
                        wait_time = min(2 ** (attempt + 3), 300)  # 8s, 16s, 32s... max 5 min
                        jitter = random.uniform(0, wait_time * 0.2)
                        total_wait = wait_time + jitter
                        logger.info(f"Waiting {total_wait:.1f}s before retry...")
                        time.sleep(total_wait)
                    continue

                elif response.status_code == 429:
                    logger.warning(f"429 Too Many Requests - rate limited (attempt {attempt + 1})")
                    self.consecutive_errors += 1

                    # 429 means we're definitely rate limited - wait longer
                    if attempt < max_retries - 1:
                        wait_time = min(2 ** (attempt + 4), 900)  # 16s, 32s, 64s... max 15 min
                        jitter = random.uniform(0, wait_time * 0.2)
                        total_wait = wait_time + jitter
                        logger.info(f"Rate limited - waiting {total_wait:.1f}s before retry...")
                        time.sleep(total_wait)
                    continue

                elif response.status_code == 503:
                    logger.warning(f"503 Service Unavailable (attempt {attempt + 1})")
                    self.consecutive_errors += 1

                    if attempt < max_retries - 1:
                        wait_time = random.uniform(30, 60)
                        logger.info(f"Service unavailable - waiting {wait_time:.1f}s...")
                        time.sleep(wait_time)
                    continue

                # Success!
                if response.status_code == 200:
                    self.consecutive_errors = 0  # Reset error counter on success
                    return response

                # Other status codes
                logger.warning(f"Unexpected status code {response.status_code}")
                if attempt < max_retries - 1:
                    time.sleep(random.uniform(5, 10))
                    continue

            except requests.exceptions.Timeout:
                logger.warning(f"Request timeout (attempt {attempt + 1})")
                self.consecutive_errors += 1
                if attempt < max_retries - 1:
                    time.sleep(random.uniform(5, 10))
                    continue

            except requests.exceptions.RequestException as e:
                logger.error(f"Request exception: {e} (attempt {attempt + 1})")
                self.consecutive_errors += 1
                if attempt < max_retries - 1:
                    time.sleep(random.uniform(5, 10))
                    continue

        # All retries exhausted
        logger.error(f"Failed to fetch {url} after {max_retries} attempts")
        return None

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

            # Try with requests first (faster) - uses smart retry logic
            response = self._make_request_with_retry(url, max_retries=3)

            if response and self.validate_response(response):
                data = self._parse_athlete_data_from_html(response.content, sport, url)
                if data and data.get("personal_records"):
                    return FetchResult(success=True, data=data, source=self.name)

            # Fallback to Selenium if needed (e.g., for JavaScript-heavy pages)
            logger.debug(f"Falling back to Selenium for athlete {player_id}")
            self._init_driver()
            self.driver.get(url)
            time.sleep(random.uniform(2, 4))  # Random wait for content to load
            page_source = self.driver.page_source

            data = self._parse_athlete_data_from_html(page_source, sport, url)
            if data:
                return FetchResult(success=True, data=data, source=self.name)
            else:
                return FetchResult(success=False, error="Failed to parse athlete data", source=self.name)

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
        """
        try:
            logger.info(f"Fetching TFRR team stats for {team_code} in {sport}")

            # Determine subdomain based on sport
            if sport.lower() in ["cross_country", "xc", "cross country"]:
                url = f"https://xc.tfrrs.org/teams/{team_code}.html"
            else:
                url = f"{self.base_url}/teams/{team_code}.html"

            # Apply smart delay before Selenium request
            if self.request_count > 0:
                self._smart_delay()

            # Initialize Selenium driver for JavaScript-rendered content
            self._init_driver()

            # Load the page
            self.driver.get(url)
            self.request_count += 1  # Count Selenium requests too
            self.last_request_time = time.time()

            # Wait longer for JavaScript to fully render with randomization
            wait_time = random.uniform(4, 6)
            time.sleep(wait_time)

            # Wait for roster section to appear
            try:
                WebDriverWait(self.driver, 15).until(lambda driver: driver.find_element(By.TAG_NAME, "h3"))
                time.sleep(random.uniform(1.5, 2.5))  # Additional random wait
            except Exception as e:
                logger.warning(f"Timeout waiting for page content: {e}")

            # Get the page source after JavaScript execution
            page_source = self.driver.page_source

            data = self._parse_team_data_from_html(page_source, sport, url)
            if data:
                self.consecutive_errors = 0  # Reset error counter on success
                return FetchResult(success=True, data=data, source=self.name)
            else:
                return FetchResult(success=False, error="Failed to parse team data", source=self.name)

        except Exception as e:
            self.consecutive_errors += 1
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
            # Method 1: Look for roster section with H3 header
            roster_header = soup.find("h3", string=re.compile(r"ROSTER", re.IGNORECASE))
            if roster_header:
                # Find the parent container
                roster_section = roster_header.find_parent()
                if roster_section:
                    # Find all athlete links in this section (including nested)
                    athlete_links = roster_section.find_all("a", href=re.compile(r"/athletes/\d+/"))
                    seen_ids = set()
                    for link in athlete_links:
                        athlete_id = self._extract_athlete_id(link["href"])
                        name = link.text.strip()
                        # Only add unique athletes (avoid duplicates)
                        if athlete_id and name and athlete_id not in seen_ids:
                            seen_ids.add(athlete_id)
                            athlete = {
                                "name": name,
                                "athlete_id": athlete_id,
                                "year": "",  # Year not always available in roster section
                            }
                            roster.append(athlete)

                    if roster:
                        logger.info(f"Extracted {len(roster)} athletes from roster section")
                        return roster

            # Method 2: Look for roster table (fallback)
            roster_table = soup.find("table", class_=re.compile("roster|athletes"))
            if roster_table:
                rows = roster_table.find_all("tr")
                for row in rows[1:]:  # Skip header
                    cols = row.find_all("td")
                    if len(cols) >= 2:
                        athlete_link = row.find("a", href=re.compile(r"/athletes/"))
                        if athlete_link:
                            athlete = {
                                "name": athlete_link.text.strip(),
                                "athlete_id": self._extract_athlete_id(athlete_link["href"]),
                                "year": cols[1].text.strip() if len(cols) > 1 else "",
                            }
                            roster.append(athlete)

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

            # Use smart retry logic
            full_url = f"{search_url}?q={name}&type=athlete"
            response = self._make_request_with_retry(full_url, max_retries=3)

            if not response or not self.validate_response(response):
                return FetchResult(success=False, error="Invalid search response", source=self.name)

            athletes = self._parse_search_results(response, sport)

            if athletes is not None:
                return FetchResult(
                    success=True,
                    data={"athletes": athletes, "count": len(athletes)},
                    source=self.name,
                )
            else:
                return FetchResult(success=False, error="Failed to parse search results", source=self.name)

        except Exception as e:
            return self.handle_error(e, "searching for athlete")

    def _parse_search_results(self, response, sport: str) -> Optional[List[Dict[str, str]]]:
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
            logger.info(f"Fetching TFRR event results for athlete {athlete_id}, event {event_name}")

            # Fetch the athlete's full profile first with smart retry
            url = f"{self.base_url}/athletes/{athlete_id}.html"
            response = self._make_request_with_retry(url, max_retries=3)

            if not response or not self.validate_response(response):
                return FetchResult(success=False, error="Invalid response from TFRRS", source=self.name)

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

    def _parse_event_specific_data(self, response, event_name: str) -> Optional[Dict[str, Any]]:
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
                                "mark": (cols[event_col + 1].text.strip() if len(cols) > event_col + 1 else ""),
                                "place": (cols[event_col + 2].text.strip() if len(cols) > event_col + 2 else ""),
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
                        mark = cols[1].text.strip()
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
        """Initialize Selenium WebDriver for JavaScript-rendered pages with anti-detection."""
        if self.driver is not None:
            return

        logger.debug("Initializing Selenium WebDriver for TFRR...")

        chrome_options = Options()
        chrome_options.add_argument("--headless=new")  # Use new headless mode
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")

        # Randomize window size slightly
        width = random.randint(1900, 1920)
        height = random.randint(1060, 1080)
        chrome_options.add_argument(f"--window-size={width},{height}")

        # Use random user agent from pool
        user_agent = self._get_random_user_agent()
        chrome_options.add_argument(f"--user-agent={user_agent}")

        # Anti-detection measures
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)

        # Additional anti-bot measures
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--allow-running-insecure-content")
        chrome_options.add_argument("--disable-features=IsolateOrigins,site-per-process")

        # Set preferences to appear more human-like
        prefs = {
            "profile.default_content_setting_values.notifications": 2,
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False,
        }
        chrome_options.add_experimental_option("prefs", prefs)

        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)

        # Randomize page load timeout
        timeout = random.randint(15, 20)
        self.driver.set_page_load_timeout(timeout)

        # Execute CDP commands to further mask automation
        self.driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {
                "source": """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en']
                });
            """
            },
        )

        logger.debug("WebDriver initialized successfully with anti-detection measures")

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
