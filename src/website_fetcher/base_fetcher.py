"""
Base Fetcher Class

Abstract base class that all website fetchers must inherit from.
This ensures consistent interface across different data sources.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, Optional
from datetime import datetime
import logging


logger = logging.getLogger(__name__)


@dataclass
class FetchResult:
    """
    Standard result object returned by all fetchers.

    Attributes:
        success: Whether the fetch was successful
        data: The fetched data as a dictionary
        error: Error message if fetch failed
        timestamp: When the data was fetched
        source: Name of the data source
    """

    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: datetime = None
    source: str = ""

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class BaseFetcher(ABC):
    """
    Abstract base class for all website fetchers.

    All fetcher implementations (NCAA, TFRR, etc.) must inherit from this class
    and implement the required methods.
    """

    def __init__(self, base_url: str, timeout: int = 30):
        """
        Initialize the fetcher.

        Args:
            base_url: Base URL for the data source
            timeout: Request timeout in seconds
        """
        self.base_url = base_url
        self.timeout = timeout
        self.name = self.__class__.__name__
        logger.info(f"Initialized {self.name} with base URL: {base_url}")

    @abstractmethod
    def fetch_player_stats(self, player_id: str, sport: str) -> FetchResult:
        """
        Fetch statistics for a specific player.

        Args:
            player_id: Unique identifier for the player on this source
            sport: Sport name (basketball, soccer, track, etc.)

        Returns:
            FetchResult object containing player statistics

        Example data format:
        {
            "player_id": "12345",
            "name": "John Doe",
            "sport": "basketball",
            "season": "2023-24",
            "stats": {
                "points": 450,
                "rebounds": 120,
                "assists": 80
            }
        }
        """
        pass

    @abstractmethod
    def fetch_team_stats(self, team_id: str, sport: str) -> FetchResult:
        """
        Fetch statistics for an entire team.

        Args:
            team_id: Unique identifier for the team on this source
            sport: Sport name

        Returns:
            FetchResult object containing team statistics
        """
        pass

    @abstractmethod
    def search_player(self, name: str, sport: str) -> FetchResult:
        """
        Search for a player by name.

        Args:
            name: Player name to search for
            sport: Sport to search within

        Returns:
            FetchResult with list of matching players and their IDs
        """
        pass

    def validate_response(self, response: Any) -> bool:
        """
        Validate that a response is usable.

        Args:
            response: Response object to validate

        Returns:
            True if valid, False otherwise
        """
        # Basic validation - can be overridden by subclasses
        if response is None:
            logger.warning(f"{self.name}: Response is None")
            return False

        if hasattr(response, "status_code"):
            if response.status_code != 200:
                logger.warning(f"{self.name}: Bad status code {response.status_code}")
                return False

        return True

    def handle_error(self, error: Exception, context: str = "") -> FetchResult:
        """
        Handle errors consistently across fetchers.

        Args:
            error: The exception that occurred
            context: Additional context about what was being done

        Returns:
            FetchResult with error information
        """
        error_msg = f"{self.name} error"
        if context:
            error_msg += f" during {context}"
        error_msg += f": {str(error)}"

        logger.error(error_msg)

        return FetchResult(success=False, error=error_msg, source=self.name)

    def get_source_name(self) -> str:
        """Get the name of this data source"""
        return self.name
