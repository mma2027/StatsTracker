"""
TFRR (Track & Field Results Reporting) Fetcher using Playwright

Uses Playwright with containerization support to scrape personal records
from tfrrs.org while handling rate limiting gracefully.
"""

import asyncio
import logging
import random
import time
from typing import Dict, Any, List, Optional
from pathlib import Path
import re

from playwright.async_api import async_playwright, Browser, Page, TimeoutError as PlaywrightTimeout
from bs4 import BeautifulSoup

from .base_fetcher import BaseFetcher, FetchResult


logger = logging.getLogger(__name__)


# Haverford College TFRR team codes
HAVERFORD_TEAMS = {
    "mens_track": "PA_college_m_Haverford",
    "womens_track": "PA_college_f_Haverford",
    "mens_cross_country": "PA_college_m_Haverford",
    "womens_cross_country": "PA_college_f_Haverford",
}


class TFRRPlaywrightFetcher(BaseFetcher):
    """
    Fetcher for TFRR (Track & Field Results Reporting) website using Playwright.

    This fetcher uses Playwright instead of Selenium for better rate limit handling,
    containerization support, and more reliable scraping.
    """

    def __init__(
        self,
        base_url: str = "https://www.tfrrs.org",
        timeout: int = 30,
        headless: bool = True,
        slow_mo: int = 0,
    ):
        """
        Initialize the TFRR Playwright fetcher.

        Args:
            base_url: Base URL for TFRR
            timeout: Request timeout in seconds
            headless: Run browser in headless mode
            slow_mo: Slow down Playwright operations by specified milliseconds
        """
        super().__init__(base_url, timeout)
        self.headless = headless
        self.slow_mo = slow_mo
        self.browser = None
        self.context = None
        self.playwright = None
        self.request_count = 0
        self.last_request_time = 0
        self.consecutive_errors = 0

    async def _init_browser(self):
        """Initialize Playwright browser with anti-detection measures."""
        if self.browser is not None:
            return

        logger.info("Initializing Playwright browser...")

        self.playwright = await async_playwright().start()

        # Use Chromium with custom args to avoid detection
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            slow_mo=self.slow_mo,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-sandbox",
                "--disable-web-security",
            ],
        )

        # Create a new context with realistic settings
        self.context = await self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            locale="en-US",
            timezone_id="America/New_York",
        )

        # Add script to remove webdriver property
        await self.context.add_init_script(
            """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
        """
        )

        logger.info("Playwright browser initialized successfully")

    async def _close_browser(self):
        """Close the Playwright browser and cleanup."""
        try:
            if self.context:
                await self.context.close()
                self.context = None
            if self.browser:
                await self.browser.close()
                self.browser = None
            if self.playwright:
                await self.playwright.stop()
                self.playwright = None
            logger.info("Playwright browser closed")
        except Exception as e:
            logger.error(f"Error closing browser: {e}")

    async def _smart_delay(self):
        """
        Implement smart delay between requests to avoid rate limiting.
        Uses randomized delays with exponential backoff on errors.
        """
        # Base delay: 4-8 seconds (randomized)
        base_delay = random.uniform(4.0, 8.0)

        # Add exponential backoff if we've had consecutive errors
        if self.consecutive_errors > 0:
            backoff = min(2**self.consecutive_errors, 60)  # Max 60 seconds
            jitter = random.uniform(0, backoff * 0.3)  # Add 0-30% jitter
            total_delay = base_delay + backoff + jitter
            logger.info(f"Exponential backoff: {total_delay:.1f}s " f"({self.consecutive_errors} consecutive errors)")
        else:
            total_delay = base_delay

        # Ensure minimum time between requests
        time_since_last = time.time() - self.last_request_time
        if time_since_last < total_delay:
            await asyncio.sleep(total_delay - time_since_last)

        self.last_request_time = time.time()
        self.request_count += 1

        # Every 8-12 requests, take a longer break
        if self.request_count % random.randint(8, 12) == 0:
            extended_delay = random.uniform(20.0, 40.0)
            logger.info(f"Taking extended break: {extended_delay:.1f}s " f"after {self.request_count} requests")
            await asyncio.sleep(extended_delay)

    async def _fetch_page_with_retry(self, url: str, max_retries: int = 3) -> Optional[str]:
        """
        Fetch a page with retry logic and rate limit handling.

        Args:
            url: URL to fetch
            max_retries: Maximum number of retry attempts

        Returns:
            Page HTML content if successful, None otherwise
        """
        for attempt in range(max_retries):
            try:
                # Apply smart delay before request (skip on first ever request)
                if self.request_count > 0:
                    await self._smart_delay()

                page = await self.context.new_page()

                try:
                    # Navigate to the page with timeout
                    logger.info(f"Fetching {url} (attempt {attempt + 1}/{max_retries})")
                    response = await page.goto(
                        url,
                        wait_until="domcontentloaded",
                        timeout=self.timeout * 1000,
                    )

                    # Check response status
                    if response.status == 403:
                        logger.warning(f"403 Forbidden - likely rate limited (attempt {attempt + 1})")
                        self.consecutive_errors += 1

                        if attempt < max_retries - 1:
                            wait_time = min(2 ** (attempt + 3), 300)
                            jitter = random.uniform(0, wait_time * 0.2)
                            total_wait = wait_time + jitter
                            logger.info(f"Waiting {total_wait:.1f}s before retry...")
                            await asyncio.sleep(total_wait)
                        continue

                    elif response.status == 429:
                        logger.warning(f"429 Too Many Requests - rate limited (attempt {attempt + 1})")
                        self.consecutive_errors += 1

                        if attempt < max_retries - 1:
                            wait_time = min(2 ** (attempt + 4), 900)
                            jitter = random.uniform(0, wait_time * 0.2)
                            total_wait = wait_time + jitter
                            logger.info(f"Rate limited - waiting {total_wait:.1f}s before retry...")
                            await asyncio.sleep(total_wait)
                        continue

                    elif response.status >= 500:
                        logger.warning(f"{response.status} Server Error (attempt {attempt + 1})")
                        self.consecutive_errors += 1

                        if attempt < max_retries - 1:
                            await asyncio.sleep(random.uniform(30, 60))
                        continue

                    # Success - wait for page to fully load
                    await asyncio.sleep(random.uniform(2.0, 4.0))

                    # Get page content
                    content = await page.content()
                    self.consecutive_errors = 0  # Reset on success

                    return content

                finally:
                    await page.close()

            except PlaywrightTimeout:
                logger.warning(f"Request timeout (attempt {attempt + 1})")
                self.consecutive_errors += 1
                if attempt < max_retries - 1:
                    await asyncio.sleep(random.uniform(5, 10))
                continue

            except Exception as e:
                logger.error(f"Error fetching page: {e} (attempt {attempt + 1})")
                self.consecutive_errors += 1
                if attempt < max_retries - 1:
                    await asyncio.sleep(random.uniform(5, 10))
                continue

        # All retries exhausted
        logger.error(f"Failed to fetch {url} after {max_retries} attempts")
        return None

    async def _fetch_team_roster_async(self, team_code: str, sport: str) -> Optional[Dict[str, Any]]:
        """
        Fetch team roster from TFRR asynchronously.

        Args:
            team_code: TFRR team code (e.g., "PA_college_m_Haverford")
            sport: Either "track" or "cross_country"

        Returns:
            Dictionary with team data and roster
        """
        try:
            # Determine subdomain based on sport
            if sport.lower() in ["cross_country", "xc", "cross country"]:
                url = f"https://xc.tfrrs.org/teams/{team_code}.html"
            else:
                url = f"{self.base_url}/teams/{team_code}.html"

            logger.info(f"Fetching TFRR team roster for {team_code} in {sport}")

            # Fetch the page
            html_content = await self._fetch_page_with_retry(url)

            if not html_content:
                return None

            # Parse the HTML
            soup = BeautifulSoup(html_content, "html.parser")

            # Extract team name
            name_elem = soup.find("h3") or soup.find("h2")
            team_name = name_elem.text.strip() if name_elem else "Unknown"

            # Extract roster
            roster = self._extract_roster(soup)

            team_data = {
                "team_id": team_code,
                "name": team_name,
                "sport": sport,
                "roster": roster,
                "profile_url": url,
            }

            logger.info(f"Successfully fetched team roster for {team_name}: {len(roster)} athletes")
            return team_data

        except Exception as e:
            logger.error(f"Error fetching team roster: {e}")
            return None

    async def _fetch_athlete_prs_async(self, athlete_id: str, sport: str) -> Optional[Dict[str, Any]]:
        """
        Fetch athlete's personal records from TFRR asynchronously.

        Args:
            athlete_id: TFRR athlete ID
            sport: Either "track" or "cross_country"

        Returns:
            Dictionary with athlete data and personal records
        """
        try:
            # Determine subdomain based on sport
            if sport.lower() in ["cross_country", "xc", "cross country"]:
                url = f"https://xc.tfrrs.org/athletes/{athlete_id}.html"
            else:
                url = f"{self.base_url}/athletes/{athlete_id}.html"

            logger.debug(f"Fetching PRs for athlete {athlete_id}")

            # Fetch the page
            html_content = await self._fetch_page_with_retry(url)

            if not html_content:
                return None

            # Parse the HTML
            soup = BeautifulSoup(html_content, "html.parser")

            # Extract athlete name
            name_elem = soup.find("h3")
            name = name_elem.text.strip() if name_elem else "Unknown"

            # Extract team
            team_elem = soup.find("div", class_="team-name") or soup.find("h4")
            team = team_elem.text.strip() if team_elem else "Unknown"

            # Extract personal records
            prs = self._extract_personal_records(soup)

            athlete_data = {
                "athlete_id": athlete_id,
                "name": name,
                "team": team,
                "sport": sport,
                "personal_records": prs,
                "profile_url": url,
            }

            logger.debug(f"Successfully fetched PRs for {name}: {len(prs)} events")
            return athlete_data

        except Exception as e:
            logger.error(f"Error fetching athlete PRs: {e}")
            return None

    def _extract_roster(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extract team roster from parsed HTML."""
        roster = []
        try:
            # Look for roster section with H3 header
            roster_header = soup.find("h3", string=re.compile(r"ROSTER", re.IGNORECASE))

            if roster_header:
                roster_section = roster_header.find_parent()
                if roster_section:
                    # Find all athlete links
                    athlete_links = roster_section.find_all("a", href=re.compile(r"/athletes/\d+/"))
                    seen_ids = set()

                    for link in athlete_links:
                        athlete_id = self._extract_athlete_id(link["href"])
                        name = link.text.strip()

                        if athlete_id and name and athlete_id not in seen_ids:
                            seen_ids.add(athlete_id)
                            roster.append(
                                {
                                    "name": name,
                                    "athlete_id": athlete_id,
                                    "year": "",
                                }
                            )

            # Fallback: Look for any athlete links with Haverford in URL
            if not roster:
                all_athlete_links = soup.find_all("a", href=re.compile(r"/athletes/\d+/Haverford/"))
                seen_ids = set()

                for link in all_athlete_links:
                    athlete_id = self._extract_athlete_id(link["href"])
                    if athlete_id and athlete_id not in seen_ids:
                        seen_ids.add(athlete_id)
                        roster.append(
                            {
                                "name": link.text.strip(),
                                "athlete_id": athlete_id,
                                "year": "",
                            }
                        )

            logger.info(f"Extracted {len(roster)} athletes from roster")

        except Exception as e:
            logger.warning(f"Error extracting roster: {e}")

        return roster

    def _extract_athlete_id(self, url: str) -> str:
        """Extract athlete ID from URL."""
        match = re.search(r"/athletes/(\d+)", url)
        return match.group(1) if match else ""

    def _extract_personal_records(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract personal records from athlete profile."""
        prs = {}
        try:
            # Look for PR tables
            pr_tables = soup.find_all("table", class_=re.compile("bests|records"))

            for table in pr_tables:
                rows = table.find_all("tr")
                for row in rows[1:]:  # Skip header row
                    cols = row.find_all("td")
                    if len(cols) >= 2:
                        event = cols[0].text.strip()
                        mark = cols[1].text.strip()
                        if event and mark:
                            prs[event] = mark

            # Also check for divs with PR data (alternative layout)
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

    # Synchronous wrapper methods for compatibility with BaseFetcher interface

    def fetch_team_stats(self, team_code: str, sport: str) -> FetchResult:
        """
        Fetch team statistics (synchronous wrapper).

        Args:
            team_code: TFRR team code
            sport: Sport type

        Returns:
            FetchResult with team data and roster
        """

        async def _fetch_and_cleanup():
            """Wrapper to fetch data and cleanup browser in same async context."""
            try:
                data = await self._fetch_team_with_prs(team_code, sport)
                return data
            finally:
                # Close browser in same async context
                await self._close_browser()

        try:
            # Run the async function with cleanup
            data = asyncio.run(_fetch_and_cleanup())

            if data:
                return FetchResult(success=True, data=data, source=self.name)
            else:
                return FetchResult(success=False, error="Failed to fetch team data", source=self.name)

        except Exception as e:
            return self.handle_error(e, "fetching team stats")

    async def _fetch_team_with_prs(self, team_code: str, sport: str) -> Optional[Dict[str, Any]]:
        """
        Fetch team roster and PRs for all athletes.

        Args:
            team_code: TFRR team code
            sport: Sport type

        Returns:
            Dictionary with team data including all athlete PRs
        """
        try:
            # Initialize browser
            await self._init_browser()

            # Fetch team roster
            team_data = await self._fetch_team_roster_async(team_code, sport)

            if not team_data or not team_data.get("roster"):
                logger.warning(f"No roster found for team {team_code}")
                return team_data

            roster = team_data["roster"]
            logger.info(f"Fetching PRs for {len(roster)} athletes...")

            # Fetch PRs for each athlete
            athletes_with_prs = []
            for idx, athlete in enumerate(roster):
                athlete_id = athlete["athlete_id"]

                # Progress logging
                if idx % 5 == 0 or idx == len(roster) - 1:
                    logger.info(f"Progress: {idx + 1}/{len(roster)} athletes")

                # Fetch athlete PRs
                athlete_data = await self._fetch_athlete_prs_async(athlete_id, sport)

                if athlete_data:
                    athletes_with_prs.append(athlete_data)
                else:
                    # Keep athlete in list even if PR fetch fails
                    athletes_with_prs.append(
                        {
                            "athlete_id": athlete_id,
                            "name": athlete["name"],
                            "team": team_data.get("name", "Unknown"),
                            "sport": sport,
                            "personal_records": {},
                        }
                    )

            # Update roster with PR data
            team_data["roster"] = athletes_with_prs

            logger.info(f"Successfully fetched team data with PRs for " f"{len(athletes_with_prs)} athletes")
            return team_data

        except Exception as e:
            logger.error(f"Error fetching team with PRs: {e}")
            return None

    def fetch_player_stats(self, player_id: str, sport: str) -> FetchResult:
        """
        Fetch statistics for a single player (synchronous wrapper).

        Args:
            player_id: TFRR athlete ID
            sport: Sport type

        Returns:
            FetchResult with athlete data and PRs
        """

        async def _fetch_and_cleanup():
            """Wrapper to fetch data and cleanup browser in same async context."""
            try:
                await self._init_browser()
                return await self._fetch_athlete_prs_async(player_id, sport)
            finally:
                # Close browser in same async context
                await self._close_browser()

        try:
            data = asyncio.run(_fetch_and_cleanup())

            if data:
                return FetchResult(success=True, data=data, source=self.name)
            else:
                return FetchResult(success=False, error="Failed to fetch player data", source=self.name)

        except Exception as e:
            return self.handle_error(e, "fetching player stats")

    def search_player(self, name: str, sport: str) -> FetchResult:
        """
        Search for a player by name.

        Note: TFRR search is not implemented in this version.
        Use fetch_team_stats and filter by name instead.
        """
        return FetchResult(
            success=False,
            error="Search not implemented for Playwright fetcher. Use fetch_team_stats instead.",
            source=self.name,
        )
