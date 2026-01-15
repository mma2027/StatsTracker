"""
Test script for SquashFetcher

This script tests the SquashFetcher to ensure it correctly fetches
and parses player data from ClubLocker.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging  # noqa: E402
from src.website_fetcher import SquashFetcher  # noqa: E402

# Setup logging to see what's happening
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_squash_fetcher():
    """Test the SquashFetcher with Haverford's team ID"""

    print("=" * 80)
    print("TESTING SQUASH FETCHER")
    print("=" * 80)

    # Create fetcher instance
    fetcher = SquashFetcher()
    logger.info("Created SquashFetcher instance")

    # Test with Haverford's team ID
    team_id = "40879"
    sport = "squash"

    print(f"\nFetching stats for team {team_id}...")
    print("-" * 80)

    # Fetch team stats
    result = fetcher.fetch_team_stats(team_id, sport)

    # Check if successful
    if result.success:
        print("\n✅ SUCCESS! Data fetched successfully.")
        print("=" * 80)

        data = result.data

        # Display summary
        print(f"\nTeam ID: {data['team_id']}")
        print(f"Sport: {data['sport']}")
        print(f"Season: {data['season']}")
        print(f"Number of players: {len(data['players'])}")
        print(f"Stat categories: {data['stat_categories']}")

        # Display player data
        print("\n" + "=" * 80)
        print("PLAYER ROSTER:")
        print("=" * 80)
        print(f"{'#':<4} {'Name':<30} {'Wins':<10}")
        print("-" * 80)

        for i, player in enumerate(data['players'], 1):
            name = player['name']
            wins = player['stats'].get('wins', 'N/A')
            print(f"{i:<4} {name:<30} {wins:<10}")

        # Display result metadata
        print("\n" + "=" * 80)
        print("RESULT METADATA:")
        print("=" * 80)
        print(f"Timestamp: {result.timestamp}")
        print(f"Source: {result.source}")

        print("\n✅ Test completed successfully!")
        return True

    else:
        print(f"\n❌ FAILED! Error: {result.error}")
        print(f"Source: {result.source}")
        print(f"Timestamp: {result.timestamp}")
        print("\n❌ Test failed!")
        return False


def test_invalid_team_id():
    """Test with an invalid team ID to verify error handling"""

    print("\n\n" + "=" * 80)
    print("TESTING ERROR HANDLING (Invalid Team ID)")
    print("=" * 80)

    fetcher = SquashFetcher()
    result = fetcher.fetch_team_stats("99999999", "squash")

    if not result.success:
        print("\n✅ Error handling works correctly!")
        print(f"Error message: {result.error}")
        return True
    else:
        print("\n⚠️  Expected failure but got success (unexpected)")
        return False


if __name__ == "__main__":
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "SQUASH FETCHER TEST SUITE" + " " * 33 + "║")
    print("╚" + "=" * 78 + "╝")

    # Run main test
    test1_passed = test_squash_fetcher()

    # Run error handling test
    test2_passed = test_invalid_team_id()

    # Summary
    print("\n\n" + "=" * 80)
    print("TEST SUMMARY:")
    print("=" * 80)
    print(f"  Main functionality test: {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"  Error handling test:     {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    print("=" * 80)

    if test1_passed and test2_passed:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print("\n⚠️  Some tests failed!")
        sys.exit(1)
