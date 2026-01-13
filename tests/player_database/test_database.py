"""
Example test file for player database module
"""

import pytest
import tempfile
import os
from datetime import datetime

from src.player_database import PlayerDatabase, Player, StatEntry


class TestPlayerDatabase:
    """Test cases for PlayerDatabase class"""

    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing"""
        # Create temporary file
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)

        # Create database
        db = PlayerDatabase(path)

        yield db

        # Cleanup
        if os.path.exists(path):
            os.remove(path)

    def test_add_player(self, temp_db):
        """Test adding a player to database"""
        player = Player(player_id="test001", name="Test Player", sport="basketball", position="Guard")

        result = temp_db.add_player(player)
        assert result is True

        # Verify player was added
        retrieved = temp_db.get_player("test001")
        assert retrieved is not None
        assert retrieved.name == "Test Player"
        assert retrieved.sport == "basketball"

    def test_get_nonexistent_player(self, temp_db):
        """Test getting a player that doesn't exist"""
        result = temp_db.get_player("nonexistent")
        assert result is None

    def test_update_player(self, temp_db):
        """Test updating player information"""
        # Add player
        player = Player(player_id="test002", name="Test Player 2", sport="soccer")
        temp_db.add_player(player)

        # Update player
        player.position = "Forward"
        result = temp_db.update_player(player)
        assert result is True

        # Verify update
        retrieved = temp_db.get_player("test002")
        assert retrieved.position == "Forward"

    def test_add_stat(self, temp_db):
        """Test adding a stat entry"""
        # First add a player
        player = Player(player_id="test003", name="Test Player 3", sport="basketball")
        temp_db.add_player(player)

        # Add stat
        stat = StatEntry(player_id="test003", stat_name="points", stat_value=25, season="2023-24")
        result = temp_db.add_stat(stat)
        assert result is True

    def test_get_player_stats(self, temp_db):
        """Test retrieving player statistics"""
        # Add player
        player = Player(player_id="test004", name="Test Player 4", sport="basketball")
        temp_db.add_player(player)

        # Add multiple stats
        stats = [
            StatEntry(player_id="test004", stat_name="points", stat_value=100, season="2023-24"),
            StatEntry(player_id="test004", stat_name="rebounds", stat_value=50, season="2023-24"),
            StatEntry(player_id="test004", stat_name="points", stat_value=150, season="2024-25"),
        ]

        for stat in stats:
            temp_db.add_stat(stat)

        # Retrieve stats
        player_stats = temp_db.get_player_stats("test004")
        assert player_stats is not None
        assert player_stats.player.name == "Test Player 4"

        # Check season stats
        assert "2023-24" in player_stats.season_stats
        assert player_stats.season_stats["2023-24"]["points"] == 100

    def test_search_players(self, temp_db):
        """Test searching for players by name"""
        # Add multiple players
        players = [
            Player(player_id="test005", name="John Smith", sport="basketball"),
            Player(player_id="test006", name="John Doe", sport="soccer"),
            Player(player_id="test007", name="Jane Smith", sport="track"),
        ]

        for player in players:
            temp_db.add_player(player)

        # Search for "John"
        results = temp_db.search_players("John")
        assert len(results) == 2

        # Search for "Smith"
        results = temp_db.search_players("Smith")
        assert len(results) == 2

        # Search with sport filter
        results = temp_db.search_players("Smith", sport="basketball")
        assert len(results) == 1
        assert results[0].name == "John Smith"

    def test_get_all_players(self, temp_db):
        """Test getting all players"""
        # Add players
        players = [
            Player(player_id="test008", name="Player 8", sport="basketball", active=True),
            Player(player_id="test009", name="Player 9", sport="basketball", active=False),
            Player(player_id="test010", name="Player 10", sport="soccer", active=True),
        ]

        for player in players:
            temp_db.add_player(player)

        # Get all active players
        all_players = temp_db.get_all_players(active_only=True)
        assert len(all_players) == 2

        # Get all basketball players
        basketball_players = temp_db.get_all_players(sport="basketball", active_only=False)
        assert len(basketball_players) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
