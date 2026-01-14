"""
Cricket Statistics Fetcher using Selenium

Fetches cricket statistics from cricclubs.com for Haverford Cricket Games.
Uses Selenium to bypass website protection and scrape data from all three records:
- Batting Records
- Bowling Records
- Fielding Records

Outputs a single CSV file with all stats combined per player (Haverford players only).
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
import pandas as pd
from typing import Dict, Any, Optional
import logging
from pathlib import Path
import time
from bs4 import BeautifulSoup

from .base_fetcher import BaseFetcher, FetchResult
from .cricket_urls import get_all_urls, get_url


logger = logging.getLogger(__name__)


class CricketFetcher(BaseFetcher):
    """
    Fetcher for Haverford Cricket statistics from cricclubs.com using Selenium.

    This fetcher:
    1. Uses Selenium WebDriver to bypass website protection
    2. Scrapes batting, bowling, and fielding statistics
    3. Merges all stats based on player name
    4. Filters for Haverford players only
    5. Exports merged data to CSV
    """

    def __init__(self, timeout: int = 30, headless: bool = True):
        """
        Initialize the cricket fetcher with Selenium WebDriver.

        Args:
            timeout: Request timeout in seconds
            headless: Run browser in headless mode (default: True)
        """
        base_url = "https://cricclubs.com/HaverfordCricketGames"
        super().__init__(base_url, timeout)
        self.urls = get_all_urls()
        self.headless = headless
        self.driver = None

    def _setup_driver(self):
        """Setup and configure Chrome WebDriver."""
        if self.driver is not None:
            return

        chrome_options = Options()

        if self.headless:
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")

        # Additional options to avoid detection
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument(
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"  # noqa: E501
        )
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)

        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.set_page_load_timeout(self.timeout)
            logger.info("Chrome WebDriver initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Chrome WebDriver: {e}")
            raise

    def _close_driver(self):
        """Close the WebDriver."""
        if self.driver:
            try:
                self.driver.quit()
                self.driver = None
                logger.info("Chrome WebDriver closed")
            except Exception as e:
                logger.error(f"Error closing WebDriver: {e}")

    def fetch_player_stats(self, player_id: str, sport: str = "cricket") -> FetchResult:
        """
        Fetch statistics for a specific player.

        Args:
            player_id: Player name (used as identifier in cricket)
            sport: Sport name (default: cricket)

        Returns:
            FetchResult with player statistics
        """
        try:
            logger.info(f"Fetching cricket stats for player: {player_id}")

            # Fetch all stats
            all_stats = self.fetch_all_stats()

            if not all_stats["success"]:
                return FetchResult(
                    success=False,
                    error=all_stats.get("error", "Failed to fetch stats"),
                    source=self.name,
                )

            # Filter for specific player
            df = all_stats["data"]
            player_data = df[df["Player"].str.contains(player_id, case=False, na=False)]

            if player_data.empty:
                return FetchResult(
                    success=False,
                    error=f"Player '{player_id}' not found",
                    source=self.name,
                )

            return FetchResult(
                success=True,
                data=player_data.to_dict("records")[0],
                source=self.name,
            )

        except Exception as e:
            return self.handle_error(e, f"fetching stats for player {player_id}")
        finally:
            self._close_driver()

    def fetch_team_stats(self, team_id: str = "Haverford", sport: str = "cricket") -> FetchResult:
        """
        Fetch statistics for Haverford Cricket team.

        Args:
            team_id: Team name (default: Haverford)
            sport: Sport name (default: cricket)

        Returns:
            FetchResult with team statistics (all players)
        """
        try:
            logger.info(f"Fetching cricket team stats for {team_id}")
            return self.fetch_all_stats()

        except Exception as e:
            return self.handle_error(e, "fetching team stats")
        finally:
            self._close_driver()

    def search_player(self, name: str, sport: str = "cricket") -> FetchResult:
        """
        Search for players by name.

        Args:
            name: Player name to search for
            sport: Sport name (default: cricket)

        Returns:
            FetchResult with list of matching players
        """
        try:
            logger.info(f"Searching for cricket player: {name}")

            all_stats = self.fetch_all_stats()

            if not all_stats["success"]:
                return FetchResult(
                    success=False,
                    error=all_stats.get("error", "Failed to fetch stats"),
                    source=self.name,
                )

            df = all_stats["data"]
            matches = df[df["Player"].str.contains(name, case=False, na=False)]

            if matches.empty:
                return FetchResult(
                    success=False,
                    error=f"No players found matching '{name}'",
                    source=self.name,
                )

            player_list = matches["Player"].unique().tolist()

            return FetchResult(
                success=True,
                data={"players": player_list, "count": len(player_list)},
                source=self.name,
            )

        except Exception as e:
            return self.handle_error(e, f"searching for player {name}")
        finally:
            self._close_driver()

    def fetch_all_stats(self) -> Dict[str, Any]:
        """
        Fetch and merge all cricket statistics (batting, bowling, fielding).

        Returns:
            Dictionary with 'success', 'data' (DataFrame), and optional 'error'
        """
        try:
            logger.info("Fetching all cricket statistics from cricclubs.com using Selenium")

            # Setup driver
            self._setup_driver()
            assert self.driver is not None, "Driver should be initialized"

            # Fetch each type of statistics
            batting_df = self._fetch_batting_stats()
            bowling_df = self._fetch_bowling_stats()
            fielding_df = self._fetch_fielding_stats()

            # Check if at least one fetch was successful
            successful_fetches = []
            if batting_df is not None and not batting_df.empty:
                successful_fetches.append("batting")
            if bowling_df is not None and not bowling_df.empty:
                successful_fetches.append("bowling")
            if fielding_df is not None and not fielding_df.empty:
                successful_fetches.append("fielding")

            if not successful_fetches:
                return {
                    "success": False,
                    "error": "Failed to fetch any stat types",
                }

            logger.info(f"Successfully fetched: {', '.join(successful_fetches)}")

            # Use empty DataFrames for failed fetches
            if batting_df is None or batting_df.empty:
                batting_df = pd.DataFrame()
                logger.warning("Using empty DataFrame for batting stats")
            if bowling_df is None or bowling_df.empty:
                bowling_df = pd.DataFrame()
                logger.warning("Using empty DataFrame for bowling stats")
            if fielding_df is None or fielding_df.empty:
                fielding_df = pd.DataFrame()
                logger.warning("Using empty DataFrame for fielding stats")

            # Merge all dataframes on Player column
            merged_df = self._merge_stats(batting_df, bowling_df, fielding_df)

            logger.info(f"Successfully fetched and merged stats for {len(merged_df)} players")

            return {"success": True, "data": merged_df}

        except Exception as e:
            logger.error(f"Error fetching all stats: {e}")
            return {"success": False, "error": str(e)}
        finally:
            self._close_driver()

    def _fetch_batting_stats(self) -> Optional[pd.DataFrame]:
        """Fetch batting statistics using Selenium."""
        try:
            url = get_url("batting")
            logger.info(f"Fetching batting stats from {url}")

            self.driver.get(url)

            # Wait for page to load (reduced wait time)
            time.sleep(8)

            # Get page source and parse with BeautifulSoup
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, "html.parser")

            # Find the stats table
            df = self._parse_table_from_soup(soup, "batting")

            if df is not None and not df.empty:
                logger.info(f"Fetched batting stats for {len(df)} players")
            else:
                logger.warning("No batting stats found")

            return df

        except TimeoutException:
            logger.error("Timeout waiting for batting stats page to load")
            return None
        except Exception as e:
            logger.error(f"Error fetching batting stats: {e}")
            return None

    def _fetch_bowling_stats(self) -> Optional[pd.DataFrame]:
        """Fetch bowling statistics using Selenium."""
        try:
            url = get_url("bowling")
            logger.info(f"Fetching bowling stats from {url}")

            self.driver.get(url)

            # Wait for page to load
            time.sleep(8)

            # Get page source and parse with BeautifulSoup
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, "html.parser")

            df = self._parse_table_from_soup(soup, "bowling")

            if df is not None and not df.empty:
                logger.info(f"Fetched bowling stats for {len(df)} players")
            else:
                logger.warning("No bowling stats found")

            return df

        except TimeoutException:
            logger.error("Timeout waiting for bowling stats page to load")
            return None
        except Exception as e:
            logger.error(f"Error fetching bowling stats: {e}")
            return None

    def _fetch_fielding_stats(self) -> Optional[pd.DataFrame]:
        """Fetch fielding statistics using Selenium."""
        try:
            url = get_url("fielding")
            logger.info(f"Fetching fielding stats from {url}")

            self.driver.get(url)

            # Wait for page to load
            time.sleep(8)

            # Get page source and parse with BeautifulSoup
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, "html.parser")

            df = self._parse_table_from_soup(soup, "fielding")

            if df is not None and not df.empty:
                logger.info(f"Fetched fielding stats for {len(df)} players")
            else:
                logger.warning("No fielding stats found")

            return df

        except TimeoutException:
            logger.error("Timeout waiting for fielding stats page to load")
            return None
        except Exception as e:
            logger.error(f"Error fetching fielding stats: {e}")
            return None

    def _parse_table_from_soup(self, soup, stat_type: str) -> Optional[pd.DataFrame]:
        """
        Parse statistics table from BeautifulSoup object.

        Args:
            soup: BeautifulSoup object of the page
            stat_type: One of 'batting', 'bowling', or 'fielding'

        Returns:
            DataFrame with statistics
        """
        try:
            # Find all tables on the page
            tables = soup.find_all("table")

            if not tables:
                logger.warning(f"No tables found on {stat_type} stats page")
                return pd.DataFrame()

            # Try to find the main stats table (usually the largest one with data)
            for table in tables:
                try:
                    # Get all rows
                    rows = table.find_all("tr")

                    if len(rows) < 2:  # Need at least header + 1 data row
                        continue

                    # Extract headers from first row
                    header_row = rows[0]
                    headers = []
                    for cell in header_row.find_all(["th", "td"]):
                        headers.append(cell.get_text(strip=True))

                    if not headers:
                        continue

                    # Extract data rows
                    data = []
                    for row in rows[1:]:
                        cells = row.find_all("td")
                        if cells:
                            row_data = [cell.get_text(strip=True) for cell in cells]
                            if row_data and any(row_data):  # Skip empty rows
                                data.append(row_data)

                    if not data:
                        continue

                    # Create DataFrame
                    # Handle case where row length doesn't match header length
                    max_cols = max(len(headers), max(len(row) for row in data))

                    # Pad headers if needed
                    while len(headers) < max_cols:
                        headers.append(f"Column_{len(headers)}")

                    # Pad rows if needed
                    for row in data:
                        while len(row) < len(headers):
                            row.append("")

                    df = pd.DataFrame(data, columns=headers[: len(data[0])])

                    # Prefix columns with stat type (except Player/Name column)
                    prefix = stat_type.capitalize()
                    df.columns = [col if col.lower() in ["player", "name"] else f"{prefix}_{col}" for col in df.columns]

                    # Standardize player column name
                    for col in df.columns:
                        if col.lower() in ["name", "player"]:
                            df.rename(columns={col: "Player"}, inplace=True)
                            break

                    # Return the first table with substantial data
                    if len(df) > 0 and "Player" in df.columns:
                        return df

                except Exception as e:
                    logger.debug(f"Error parsing table: {e}")
                    continue

            logger.warning(f"Could not find valid stats table on {stat_type} page")
            return pd.DataFrame()

        except Exception as e:
            logger.error(f"Error parsing {stat_type} table: {e}")
            return pd.DataFrame()

    def _merge_stats(
        self,
        batting_df: pd.DataFrame,
        bowling_df: pd.DataFrame,
        fielding_df: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Merge batting, bowling, and fielding statistics based on Player name.
        Filters for Haverford players only.

        Args:
            batting_df: Batting statistics DataFrame
            bowling_df: Bowling statistics DataFrame
            fielding_df: Fielding statistics DataFrame

        Returns:
            Merged DataFrame with all statistics for Haverford players only
        """
        # Ensure all dataframes have Player column
        for df, name in [(batting_df, "batting"), (bowling_df, "bowling"), (fielding_df, "fielding")]:
            if df is not None and not df.empty and "Player" not in df.columns:
                logger.warning(f"{name} DataFrame missing Player column")

        # Start with batting as base (or first non-empty dataframe)
        if not batting_df.empty:
            merged = batting_df.copy()
        elif not bowling_df.empty:
            merged = bowling_df.copy()
        elif not fielding_df.empty:
            merged = fielding_df.copy()
        else:
            logger.error("All dataframes are empty")
            return pd.DataFrame()

        # Merge bowling stats
        if not bowling_df.empty and "Player" in bowling_df.columns:
            if "Player" in merged.columns:
                merged = merged.merge(bowling_df, on="Player", how="outer")
            else:
                merged = bowling_df.copy()

        # Merge fielding stats
        if not fielding_df.empty and "Player" in fielding_df.columns:
            if "Player" in merged.columns:
                merged = merged.merge(fielding_df, on="Player", how="outer")
            else:
                merged = fielding_df.copy()

        # Filter for Haverford team players only
        # Look for team column in any of the stat categories
        team_columns = [col for col in merged.columns if "team" in col.lower()]

        if team_columns:
            # Try to filter by Haverford team
            for team_col in team_columns:
                if merged[team_col].notna().any():
                    haverford_mask = merged[team_col].str.contains("Haverford", case=False, na=False)
                    if haverford_mask.any():
                        merged = merged[haverford_mask]
                        logger.info(f"Filtered to Haverford players using column: {team_col}")
                        break

        # Sort by player name
        if "Player" in merged.columns:
            merged = merged.sort_values("Player")

        # Reset index
        merged = merged.reset_index(drop=True)

        # Remove duplicate player entries (keep first occurrence)
        if "Player" in merged.columns:
            merged = merged.drop_duplicates(subset=["Player"], keep="first")

        return merged

    def export_to_csv(
        self,
        output_path: str = "haverford_cricket_stats.csv",
    ) -> bool:
        """
        Export cricket statistics to CSV file (Haverford players only).

        Args:
            output_path: Path where CSV file should be saved

        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Exporting cricket stats to {output_path}")

            # Fetch all stats
            result = self.fetch_all_stats()

            if not result["success"]:
                logger.error(f"Failed to fetch stats: {result.get('error')}")
                return False

            df = result["data"]

            if df.empty:
                logger.warning("No data to export")
                return False

            # Create output directory if it doesn't exist
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            # Export to CSV
            df.to_csv(output_path, index=False, encoding="utf-8")

            logger.info(f"Successfully exported {len(df)} Haverford player records to {output_path}")
            return True

        except Exception as e:
            logger.error(f"Error exporting to CSV: {e}")
            return False
