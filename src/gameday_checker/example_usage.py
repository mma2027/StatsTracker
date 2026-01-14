"""
Test the gameday checker implementation
"""

import sys
import logging
from pathlib import Path
from datetime import date

# Add parent directory to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from gameday_checker.checker import GamedayChecker

# Set up logging to see what's happening
logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")


def test_basic_functionality():
    """Test basic gameday checker functionality"""

    print("=" * 70)
    print("TEST: Basic Gameday Checker Functionality")
    print("=" * 70)

    # Initialize checker
    checker = GamedayChecker(schedule_url="https://haverfordathletics.com")

    # Test 1: Check today's games
    print("\n--- Test 1: Get today's games ---")
    try:
        today_games = checker.get_games_for_today()
        print(f"Games today: {len(today_games)}")
        for game in today_games:
            print(f"  - {game}")
    except Exception as e:
        print(f"Error: {e}")

    # Test 2: Check a specific date
    print("\n--- Test 2: Get games for specific date (2026-01-14) ---")
    try:
        test_date = date(2026, 1, 14)
        games = checker.get_games_for_date(test_date)
        print(f"Games on {test_date}: {len(games)}")
        for game in games:
            print(f"  - {game.team.sport}: {game.team.name} vs {game.opponent}")
            print(f"    Date: {game.date}")
            print(f"    Location: {game.location}")
            print(f"    Time: {game.time}")
            print(f"    Home game: {game.is_home_game}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()

    # Test 3: Check if games exist on a date
    print("\n--- Test 3: Check if games exist on date ---")
    try:
        has_games = checker.has_games_on_date(date(2026, 2, 22))
        print(f"Has games on 2026-02-22: {has_games}")
    except Exception as e:
        print(f"Error: {e}")

    # Test 4: Check a date with no games (far in the future)
    print("\n--- Test 4: Check date with no games ---")
    try:
        future_date = date(2027, 12, 31)
        future_games = checker.get_games_for_date(future_date)
        print(f"Games on {future_date}: {len(future_games)}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    test_basic_functionality()
