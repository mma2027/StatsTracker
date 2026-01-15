"""
Tests for NCAAFetcher class.

These tests validate the NCAA stats scraping functionality.
"""

import pytest
from unittest.mock import Mock, patch
from bs4 import BeautifulSoup

from src.website_fetcher.ncaa_fetcher import NCAAFetcher, HAVERFORD_TEAMS


class TestNCAAFetcher:
    """Test suite for NCAAFetcher class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.fetcher = NCAAFetcher()

    def teardown_method(self):
        """Clean up after tests."""
        if self.fetcher.driver:
            self.fetcher._close_driver()

    def test_init(self):
        """Test NCAAFetcher initialization."""
        assert self.fetcher.base_url == "https://stats.ncaa.org"
        assert self.fetcher.timeout == 30
        assert self.fetcher.driver is None

    def test_init_custom_params(self):
        """Test NCAAFetcher with custom parameters."""
        fetcher = NCAAFetcher(base_url="https://test.com", timeout=60)
        assert fetcher.base_url == "https://test.com"
        assert fetcher.timeout == 60

    def test_haverford_teams_constant(self):
        """Test that all Haverford team IDs are defined."""
        expected_sports = [
            "mens_basketball",
            "womens_basketball",
            "mens_soccer",
            "womens_soccer",
            "field_hockey",
            "womens_volleyball",
            "baseball",
            "mens_lacrosse",
            "womens_lacrosse",
            "softball",
        ]

        for sport in expected_sports:
            assert sport in HAVERFORD_TEAMS
            assert isinstance(HAVERFORD_TEAMS[sport], int)
            assert HAVERFORD_TEAMS[sport] > 0

    @patch("src.website_fetcher.ncaa_fetcher.webdriver.Chrome")
    @patch("src.website_fetcher.ncaa_fetcher.ChromeDriverManager")
    def test_init_selenium_driver(self, mock_driver_manager, mock_chrome):
        """Test Selenium driver initialization."""
        mock_driver = Mock()
        mock_chrome.return_value = mock_driver

        self.fetcher._init_selenium_driver()

        assert self.fetcher.driver is not None
        mock_chrome.assert_called_once()
        mock_driver.set_page_load_timeout.assert_called_once_with(15)

    def test_close_driver(self):
        """Test driver cleanup."""
        # Mock driver
        mock_driver = Mock()
        self.fetcher.driver = mock_driver

        self.fetcher._close_driver()

        mock_driver.quit.assert_called_once()
        assert self.fetcher.driver is None

    def test_close_driver_no_driver(self):
        """Test closing driver when none exists."""
        self.fetcher.driver = None
        self.fetcher._close_driver()  # Should not raise exception
        assert self.fetcher.driver is None

    def test_get_season_from_page_with_title(self):
        """Test extracting season from page title."""
        html = "<html><head><title>2025-26 Men's Basketball</title></head></html>"
        soup = BeautifulSoup(html, "html.parser")

        season = self.fetcher._get_season_from_page(soup)

        assert season == "2025-26"

    def test_get_season_from_page_with_header(self):
        """Test extracting season from h1 header."""
        html = "<html><body><h1>Women's Soccer - 2024-25 Season</h1></body></html>"
        soup = BeautifulSoup(html, "html.parser")

        season = self.fetcher._get_season_from_page(soup)

        assert season == "2024-25"

    def test_get_season_from_page_not_found(self):
        """Test when season cannot be extracted."""
        html = "<html><body><p>No season info here</p></body></html>"
        soup = BeautifulSoup(html, "html.parser")

        season = self.fetcher._get_season_from_page(soup)

        assert season == "Unknown"

    def test_parse_stats_table_simple(self):
        """Test parsing a simple stats table."""
        html = """
        <table>
            <tr>
                <th>Player</th>
                <th>GP</th>
                <th>PTS</th>
            </tr>
            <tr>
                <td><a href="/player/123">John Doe</a></td>
                <td>10</td>
                <td>150</td>
            </tr>
            <tr>
                <td><a href="/player/456">Jane Smith</a></td>
                <td>12</td>
                <td>180</td>
            </tr>
        </table>
        """
        soup = BeautifulSoup(html, "html.parser")

        players, categories = self.fetcher._parse_stats_table(soup)

        assert len(players) == 2
        assert len(categories) == 2
        assert "GP" in categories
        assert "PTS" in categories

        assert players[0]["name"] == "John Doe"
        assert players[0]["stats"]["GP"] == "10"
        assert players[0]["stats"]["PTS"] == "150"

        assert players[1]["name"] == "Jane Smith"
        assert players[1]["stats"]["GP"] == "12"
        assert players[1]["stats"]["PTS"] == "180"

    def test_parse_stats_table_no_tables(self):
        """Test parsing when no tables exist."""
        html = "<html><body><p>No tables here</p></body></html>"
        soup = BeautifulSoup(html, "html.parser")

        players, categories = self.fetcher._parse_stats_table(soup)

        assert len(players) == 0
        assert len(categories) == 0

    def test_parse_stats_table_empty_table(self):
        """Test parsing an empty table."""
        html = "<table><tr></tr></table>"
        soup = BeautifulSoup(html, "html.parser")

        players, categories = self.fetcher._parse_stats_table(soup)

        assert len(players) == 0

    @patch.object(NCAAFetcher, "_init_selenium_driver")
    @patch.object(NCAAFetcher, "_close_driver")
    @patch.object(NCAAFetcher, "_get_season_from_page")
    @patch.object(NCAAFetcher, "_parse_stats_table")
    def test_fetch_team_stats_success(
        self,
        mock_parse_table,
        mock_get_season,
        mock_close,
        mock_init_driver,
    ):
        """Test successful team stats fetching."""
        # Setup mocks
        mock_driver = Mock()
        # Mock page source needs to contain sport keywords and a table to pass validation
        mock_driver.page_source = """
        <html>
            <body>
                <h1>Men's Basketball - Season to Date Statistics</h1>
                <table>
                    <tr><th>Player</th><th>GP</th></tr>
                    <tr><td>Player 1</td><td>10</td></tr>
                </table>
            </body>
        </html>
        """
        self.fetcher.driver = mock_driver

        mock_get_season.return_value = "2025-26"
        mock_parse_table.return_value = (
            [{"name": "Player 1", "stats": {"GP": "10"}}],
            ["GP"],
        )

        # Call method
        result = self.fetcher.fetch_team_stats("611523", "basketball")

        # Assertions
        assert result.success is True
        assert result.data["team_id"] == "611523"
        assert result.data["sport"] == "basketball"
        assert result.data["season"] == "2025-26"
        assert len(result.data["players"]) == 1
        assert result.data["players"][0]["name"] == "Player 1"

        mock_init_driver.assert_called_once()
        mock_close.assert_called_once()

    @patch.object(NCAAFetcher, "_init_selenium_driver")
    @patch.object(NCAAFetcher, "_close_driver")
    def test_fetch_team_stats_exception(self, mock_close, mock_init_driver):
        """Test fetch_team_stats handles exceptions."""
        # Make init_driver raise an exception
        mock_init_driver.side_effect = Exception("Driver init failed")

        result = self.fetcher.fetch_team_stats("611523", "basketball")

        assert result.success is False
        assert "Driver init failed" in result.error
        mock_close.assert_called_once()

    def test_fetch_player_stats_not_implemented(self):
        """Test that fetch_player_stats returns not implemented."""
        result = self.fetcher.fetch_player_stats("12345", "basketball")

        assert result.success is False
        assert "Not yet implemented" in result.error

    def test_search_player_not_implemented(self):
        """Test that search_player returns not implemented."""
        result = self.fetcher.search_player("John Doe", "basketball")

        assert result.success is False
        assert "Not yet implemented" in result.error


# Integration tests (require internet connection)
# Mark with @pytest.mark.integration and run with: pytest -m integration


@pytest.mark.integration
class TestNCAAFetcherIntegration:
    """Integration tests that hit the real NCAA website."""

    def test_fetch_real_mens_basketball(self):
        """Test fetching real Haverford men's basketball stats."""
        fetcher = NCAAFetcher()
        team_id = str(HAVERFORD_TEAMS["mens_basketball"])

        try:
            result = fetcher.fetch_team_stats(team_id, "basketball")

            assert result.success is True
            assert result.data is not None
            assert "players" in result.data
            assert len(result.data["players"]) > 0

            # Check that we have some expected stat categories
            assert "stat_categories" in result.data
            assert len(result.data["stat_categories"]) > 0

            print(f"\nFetched {len(result.data['players'])} players")
            print(f"Stat categories: {result.data['stat_categories']}")

        finally:
            fetcher._close_driver()

    @pytest.mark.slow
    def test_fetch_multiple_sports(self):
        """Test fetching stats for multiple Haverford sports."""
        fetcher = NCAAFetcher()

        sports_to_test = {
            "mens_basketball": "basketball",
            "womens_soccer": "soccer",
            "womens_volleyball": "volleyball",
        }

        results = {}

        try:
            for sport_key, sport_name in sports_to_test.items():
                team_id = str(HAVERFORD_TEAMS[sport_key])
                result = fetcher.fetch_team_stats(team_id, sport_name)

                results[sport_key] = result

                assert result.success is True
                assert len(result.data["players"]) > 0

                print(f"\n{sport_key}: {len(result.data['players'])} players")

        finally:
            fetcher._close_driver()

        # Verify all were successful
        assert all(r.success for r in results.values())
