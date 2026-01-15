"""
Unit and integration tests for gameday checker
"""

import pytest
from datetime import date
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from gameday_checker.checker import GamedayChecker  # noqa: E402


def test_find_march_5_2026_baseball_game():
    """Test finding the known baseball game on March 5, 2026"""

    checker = GamedayChecker(schedule_url="https://haverfordathletics.com")
    games = checker.get_games_for_date(date(2026, 3, 5))

    # Should find at least 1 game
    assert len(games) > 0, "Should find at least one game on March 5, 2026"

    # Find baseball game
    baseball_games = [g for g in games if "baseball" in g.team.sport.lower()]
    assert len(baseball_games) > 0, "Should find baseball game"

    # Verify details
    game = baseball_games[0]
    assert "rowan" in game.opponent.lower(), f"Expected Rowan, got {game.opponent}"


def test_find_games_on_march_9_2026():
    """Test finding tennis games on March 9, 2026"""

    checker = GamedayChecker(schedule_url="https://haverfordathletics.com")
    games = checker.get_games_for_date(date(2026, 3, 9))

    # Should find tennis games (previously missed due to rolling window)
    assert isinstance(games, list), "Should return a list"
    assert len(games) >= 2, "Should find at least 2 games on March 9, 2026"

    # Verify tennis games are found
    tennis_games = [g for g in games if "tennis" in g.team.sport.lower()]
    assert len(tennis_games) >= 2, "Should find tennis games"


def test_find_january_14_2026_basketball_games():
    """Test finding basketball games on January 14, 2026"""

    checker = GamedayChecker(schedule_url="https://haverfordathletics.com")
    games = checker.get_games_for_date(date(2026, 1, 14))

    # Should find at least 2 basketball games
    assert len(games) >= 2, "Should find at least 2 games on January 14, 2026"

    # Find basketball games
    basketball_games = [g for g in games if "basketball" in g.team.sport.lower()]
    assert len(basketball_games) >= 2, "Should find at least 2 basketball games"

    # Verify opponent
    opponents = [g.opponent.lower() for g in basketball_games]
    assert any("ursinus" in opp for opp in opponents), "Should have Ursinus as opponent"


def test_find_april_15_2026_games():
    """Test finding games on April 15, 2026"""

    checker = GamedayChecker(schedule_url="https://haverfordathletics.com")
    games = checker.get_games_for_date(date(2026, 4, 15))

    # Should find multiple games
    assert len(games) >= 2, "Should find at least 2 games on April 15, 2026"

    # Verify various sports are represented
    sports = [g.team.sport.lower() for g in games]
    # April typically has lacrosse, tennis, baseball, etc.
    assert len(set(sports)) > 1, "Should have multiple different sports"


def test_no_regression_feb_22_2026():
    """Ensure February 22, 2026 still works (previously working date)"""

    checker = GamedayChecker(schedule_url="https://haverfordathletics.com")
    games = checker.get_games_for_date(date(2026, 2, 22))

    # Should find at least the women's tennis game
    assert len(games) > 0, "Should find games on February 22, 2026"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
