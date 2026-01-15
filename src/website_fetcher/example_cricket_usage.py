"""
Example usage of the Cricket Fetcher with Selenium

This script demonstrates how to use the CricketFetcher to:
1. Fetch batting, bowling, and fielding statistics from cricclubs.com
2. Merge all stats into a single dataset
3. Filter for Haverford players only
4. Export to CSV

The fetcher uses Selenium WebDriver to bypass website protection.
"""

import logging
from cricket_fetcher import CricketFetcher

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

logger = logging.getLogger(__name__)


def main():
    """Main function to fetch and export cricket statistics."""

    logger.info("Starting Cricket Statistics Fetcher")

    # Create fetcher instance
    # Set headless=False if you want to see the browser in action
    fetcher = CricketFetcher(timeout=30, headless=True)

    # Method 1: Fetch all stats and export to CSV in one call
    logger.info("Method 1: Direct export to CSV")
    output_path = "haverford_cricket_stats.csv"

    success = fetcher.export_to_csv(output_path)

    if success:
        logger.info(f"Successfully exported cricket stats to {output_path}")
    else:
        logger.error("Failed to export cricket stats")

    # Method 2: Fetch stats and work with the data programmatically
    logger.info("\nMethod 2: Fetch and work with data")

    result = fetcher.fetch_all_stats()

    if result["success"]:
        df = result["data"]
        logger.info(f"Successfully fetched stats for {len(df)} Haverford players")
        logger.info(f"\nColumns available: {list(df.columns)}")
        logger.info(f"\nFirst few players:\n{df['Player'].head(10).tolist()}")

        # You can now work with the DataFrame
        # Example: Get top batsmen by runs
        if "Batting_Runs" in df.columns:
            df["Batting_Runs"] = pd.to_numeric(df["Batting_Runs"], errors="coerce")
            top_batsmen = df.nlargest(5, "Batting_Runs")[["Player", "Batting_Runs"]]
            logger.info(f"\nTop 5 Batsmen:\n{top_batsmen}")

    else:
        logger.error(f"Failed to fetch stats: {result.get('error')}")

    # Method 3: Search for a specific player
    logger.info("\nMethod 3: Search for specific player")

    player_result = fetcher.search_player("Smith")  # Replace with actual player name

    if player_result.success:
        logger.info(f"Found players: {player_result.data}")
    else:
        logger.info(f"Player search: {player_result.error}")

    logger.info("\nDone!")


if __name__ == "__main__":
    try:
        import pandas as pd

        main()
    except ImportError as e:
        logger.error(f"Missing required dependency: {e}")
        logger.error("Please install required packages:")
        logger.error("  pip install selenium pandas")
    except Exception as e:
        logger.error(f"Error running cricket fetcher: {e}")
        import traceback

        traceback.print_exc()
