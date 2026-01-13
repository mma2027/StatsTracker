"""
Cricket Statistics Fetcher

Fetches cricket statistics from cricclubs.com for Haverford Cricket Games.
Supports fetching batting, bowling, and fielding records and merging them.
"""

import requests
import pandas as pd
from bs4 import BeautifulSoup
from typing import Dict, Any, List, Optional
import logging
import csv
from pathlib import Path

try:
    import cloudscraper
    CLOUDSCRAPER_AVAILABLE = True
except ImportError:
    CLOUDSCRAPER_AVAILABLE = False

from .base_fetcher import BaseFetcher, FetchResult
from .cricket_urls import get_all_urls, get_url


logger = logging.getLogger(__name__)


class CricketFetcher(BaseFetcher):
    """
    Fetcher for Haverford Cricket statistics from cricclubs.com.

    This fetcher:
    1. Scrapes batting, bowling, and fielding statistics
    2. Merges all stats based on player name
    3. Exports merged data to CSV
    """

    def __init__(self, timeout: int = 30, use_cloudscraper: bool = True):
        """
        Initialize the cricket fetcher with cricclubs.com URLs.

        Args:
            timeout: Request timeout in seconds
            use_cloudscraper: Use cloudscraper to bypass Cloudflare (default: True)
        """
        base_url = "https://cricclubs.com/HaverfordCricketGames"
        super().__init__(base_url, timeout)
        self.urls = get_all_urls()

        # Use cloudscraper if available and requested
        self.use_cloudscraper = use_cloudscraper and CLOUDSCRAPER_AVAILABLE

        if self.use_cloudscraper:
            # Create cloudscraper session to bypass Cloudflare
            self.scraper = cloudscraper.create_scraper(
                browser={
                    'browser': 'chrome',
                    'platform': 'windows',
                    'desktop': True
                }
            )
            logger.info("Using cloudscraper to bypass Cloudflare protection")
        else:
            # Fallback to regular requests with headers
            self.scraper = requests.Session()
            self.scraper.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            })
            if not CLOUDSCRAPER_AVAILABLE:
                logger.warning("cloudscraper not available, using regular requests (may fail with Cloudflare)")

    def fetch_player_stats(self, player_id: str, sport: str = "cricket") -> FetchResult:
        """
        Fetch statistics for a specific player.

        Note: For cricket, we fetch all player stats and filter by name.

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

    def fetch_all_stats(self) -> Dict[str, Any]:
        """
        Fetch and merge all cricket statistics (batting, bowling, fielding).

        Returns:
            Dictionary with 'success', 'data' (DataFrame), and optional 'error'
        """
        try:
            logger.info("Fetching all cricket statistics from cricclubs.com")

            # Fetch each type of statistics
            batting_df = self._fetch_batting_stats()
            bowling_df = self._fetch_bowling_stats()
            fielding_df = self._fetch_fielding_stats()

            # Check if all fetches were successful
            if batting_df is None or bowling_df is None or fielding_df is None:
                return {
                    "success": False,
                    "error": "Failed to fetch one or more stat types",
                }

            # Merge all dataframes on Player column
            merged_df = self._merge_stats(batting_df, bowling_df, fielding_df)

            logger.info(f"Successfully fetched and merged stats for {len(merged_df)} players")

            return {"success": True, "data": merged_df}

        except Exception as e:
            logger.error(f"Error fetching all stats: {e}")
            return {"success": False, "error": str(e)}

    def _fetch_batting_stats(self) -> Optional[pd.DataFrame]:
        """Fetch batting statistics from cricclubs.com."""
        try:
            url = get_url("batting")
            logger.info(f"Fetching batting stats from {url}")

            response = self.scraper.get(url, timeout=self.timeout)

            if not self.validate_response(response):
                logger.error("Invalid response for batting stats")
                return None

            # Parse HTML table
            soup = BeautifulSoup(response.content, "html.parser")
            df = self._parse_batting_table(soup)

            logger.info(f"Fetched batting stats for {len(df)} players")
            return df

        except Exception as e:
            logger.error(f"Error fetching batting stats: {e}")
            return None

    def _fetch_bowling_stats(self) -> Optional[pd.DataFrame]:
        """Fetch bowling statistics from cricclubs.com."""
        try:
            url = get_url("bowling")
            logger.info(f"Fetching bowling stats from {url}")

            response = self.scraper.get(url, timeout=self.timeout)

            if not self.validate_response(response):
                logger.error("Invalid response for bowling stats")
                return None

            # Parse HTML table
            soup = BeautifulSoup(response.content, "html.parser")
            df = self._parse_bowling_table(soup)

            logger.info(f"Fetched bowling stats for {len(df)} players")
            return df

        except Exception as e:
            logger.error(f"Error fetching bowling stats: {e}")
            return None

    def _fetch_fielding_stats(self) -> Optional[pd.DataFrame]:
        """Fetch fielding statistics from cricclubs.com."""
        try:
            url = get_url("fielding")
            logger.info(f"Fetching fielding stats from {url}")

            response = self.scraper.get(url, timeout=self.timeout)

            if not self.validate_response(response):
                logger.error("Invalid response for fielding stats")
                return None

            # Parse HTML table
            soup = BeautifulSoup(response.content, "html.parser")
            df = self._parse_fielding_table(soup)

            logger.info(f"Fetched fielding stats for {len(df)} players")
            return df

        except Exception as e:
            logger.error(f"Error fetching fielding stats: {e}")
            return None

    def _parse_batting_table(self, soup: BeautifulSoup) -> pd.DataFrame:
        """
        Parse batting statistics table from HTML.

        Args:
            soup: BeautifulSoup object of the page

        Returns:
            DataFrame with batting statistics
        """
        # Find the main stats table
        table = soup.find("table", {"class": "table"}) or soup.find("table")

        if not table:
            logger.warning("No table found in batting stats page")
            return pd.DataFrame()

        # Extract headers and rows
        rows = []
        headers = []

        # Get headers
        header_row = table.find("tr")
        if header_row:
            headers = [th.get_text(strip=True) for th in header_row.find_all(["th", "td"])]

        # Get data rows
        for row in table.find_all("tr")[1:]:  # Skip header row
            cols = [td.get_text(strip=True) for td in row.find_all("td")]
            if cols:
                rows.append(cols)

        # Create DataFrame
        if headers and rows:
            df = pd.DataFrame(rows, columns=headers)
            # Prefix columns with 'Batting_' except for Player column
            df.columns = [
                col if col.lower() in ["player", "name"] else f"Batting_{col}"
                for col in df.columns
            ]
            # Standardize player column name
            if "name" in df.columns.str.lower():
                df.rename(columns={df.columns[df.columns.str.lower() == "name"][0]: "Player"}, inplace=True)
            return df
        else:
            return pd.DataFrame()

    def _parse_bowling_table(self, soup: BeautifulSoup) -> pd.DataFrame:
        """
        Parse bowling statistics table from HTML.

        Args:
            soup: BeautifulSoup object of the page

        Returns:
            DataFrame with bowling statistics
        """
        table = soup.find("table", {"class": "table"}) or soup.find("table")

        if not table:
            logger.warning("No table found in bowling stats page")
            return pd.DataFrame()

        rows = []
        headers = []

        header_row = table.find("tr")
        if header_row:
            headers = [th.get_text(strip=True) for th in header_row.find_all(["th", "td"])]

        for row in table.find_all("tr")[1:]:
            cols = [td.get_text(strip=True) for td in row.find_all("td")]
            if cols:
                rows.append(cols)

        if headers and rows:
            df = pd.DataFrame(rows, columns=headers)
            # Prefix columns with 'Bowling_' except for Player column
            df.columns = [
                col if col.lower() in ["player", "name"] else f"Bowling_{col}"
                for col in df.columns
            ]
            if "name" in df.columns.str.lower():
                df.rename(columns={df.columns[df.columns.str.lower() == "name"][0]: "Player"}, inplace=True)
            return df
        else:
            return pd.DataFrame()

    def _parse_fielding_table(self, soup: BeautifulSoup) -> pd.DataFrame:
        """
        Parse fielding statistics table from HTML.

        Args:
            soup: BeautifulSoup object of the page

        Returns:
            DataFrame with fielding statistics
        """
        table = soup.find("table", {"class": "table"}) or soup.find("table")

        if not table:
            logger.warning("No table found in fielding stats page")
            return pd.DataFrame()

        rows = []
        headers = []

        header_row = table.find("tr")
        if header_row:
            headers = [th.get_text(strip=True) for th in header_row.find_all(["th", "td"])]

        for row in table.find_all("tr")[1:]:
            cols = [td.get_text(strip=True) for td in row.find_all("td")]
            if cols:
                rows.append(cols)

        if headers and rows:
            df = pd.DataFrame(rows, columns=headers)
            # Prefix columns with 'Fielding_' except for Player column
            df.columns = [
                col if col.lower() in ["player", "name"] else f"Fielding_{col}"
                for col in df.columns
            ]
            if "name" in df.columns.str.lower():
                df.rename(columns={df.columns[df.columns.str.lower() == "name"][0]: "Player"}, inplace=True)
            return df
        else:
            return pd.DataFrame()

    def _merge_stats(
        self,
        batting_df: pd.DataFrame,
        bowling_df: pd.DataFrame,
        fielding_df: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Merge batting, bowling, and fielding statistics based on Player name.

        Args:
            batting_df: Batting statistics DataFrame
            bowling_df: Bowling statistics DataFrame
            fielding_df: Fielding statistics DataFrame

        Returns:
            Merged DataFrame with all statistics
        """
        # Ensure all dataframes have Player column
        for df, name in [(batting_df, "batting"), (bowling_df, "bowling"), (fielding_df, "fielding")]:
            if "Player" not in df.columns:
                logger.warning(f"{name} DataFrame missing Player column")
                return pd.DataFrame()

        # Merge on Player column (outer join to include all players)
        merged = batting_df.merge(bowling_df, on="Player", how="outer")
        merged = merged.merge(fielding_df, on="Player", how="outer")

        # Filter for Haverford team players only (if team column exists)
        # This filters out opponent players
        if "Batting_Team" in merged.columns:
            merged = merged[
                merged["Batting_Team"].str.contains("Haverford", case=False, na=False)
            ]
        elif "Bowling_Team" in merged.columns:
            merged = merged[
                merged["Bowling_Team"].str.contains("Haverford", case=False, na=False)
            ]
        elif "Fielding_Team" in merged.columns:
            merged = merged[
                merged["Fielding_Team"].str.contains("Haverford", case=False, na=False)
            ]

        # Sort by player name
        merged = merged.sort_values("Player")

        # Reset index
        merged = merged.reset_index(drop=True)

        return merged

    def export_to_csv(
        self,
        output_path: str = "haverford_cricket_stats.csv",
        include_all_players: bool = True,
    ) -> bool:
        """
        Export cricket statistics to CSV file.

        Args:
            output_path: Path where CSV file should be saved
            include_all_players: If True, includes all players. If False, only Haverford

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

            # Create output directory if it doesn't exist
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            # Export to CSV
            df.to_csv(output_path, index=False, encoding="utf-8")

            logger.info(f"Successfully exported {len(df)} player records to {output_path}")
            return True

        except Exception as e:
            logger.error(f"Error exporting to CSV: {e}")
            return False
