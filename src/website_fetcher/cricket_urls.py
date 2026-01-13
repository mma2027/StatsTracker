"""
Cricket Statistics URLs Configuration

This file contains all URLs for fetching Haverford Cricket statistics
from cricclubs.com. Update these URLs if they change in the future.
"""

# Haverford Cricket Club ID
CLUB_ID = "1114507"

# Base URL for Haverford Cricket Games
BASE_URL = "https://cricclubs.com/HaverfordCricketGames"

# Statistics URLs
URLS = {
    "batting": f"{BASE_URL}/battingRecords.do?clubId={CLUB_ID}",
    "bowling": f"{BASE_URL}/bowlingRecords.do?clubId={CLUB_ID}",
    "fielding": f"{BASE_URL}/fieldingRecords.do?clubId={CLUB_ID}",
}

# Alternative: Direct URLs (for easy copy-paste updates)
BATTING_URL = "https://cricclubs.com/HaverfordCricketGames/battingRecords.do?clubId=1114507"
BOWLING_URL = "https://cricclubs.com/HaverfordCricketGames/bowlingRecords.do?clubId=1114507"
FIELDING_URL = "https://cricclubs.com/HaverfordCricketGames/fieldingRecords.do?clubId=1114507"


def get_all_urls():
    """
    Get all cricket statistics URLs.

    Returns:
        Dictionary with keys: 'batting', 'bowling', 'fielding'
    """
    return URLS.copy()


def get_url(stat_type: str) -> str:
    """
    Get URL for a specific statistic type.

    Args:
        stat_type: One of 'batting', 'bowling', or 'fielding'

    Returns:
        URL string

    Raises:
        ValueError: If stat_type is not valid
    """
    if stat_type not in URLS:
        raise ValueError(f"Invalid stat_type: {stat_type}. Must be one of {list(URLS.keys())}")
    return URLS[stat_type]


# Documentation for future updates
"""
HOW TO UPDATE URLs:

If the URLs change in the future, update them in one of two ways:

1. Update the CLUB_ID if only the club ID changes:
   CLUB_ID = "NEW_CLUB_ID"

2. Update individual URLs directly:
   BATTING_URL = "new_url_here"
   BOWLING_URL = "new_url_here"
   FIELDING_URL = "new_url_here"

   Then update the URLS dictionary:
   URLS = {
       "batting": BATTING_URL,
       "bowling": BOWLING_URL,
       "fielding": FIELDING_URL,
   }

3. If the base URL structure changes completely:
   Simply replace the entire URL strings in the URLS dictionary.
"""
