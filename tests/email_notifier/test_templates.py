"""
Unit tests for EmailTemplate class
"""

import pytest
from datetime import date

from src.email_notifier.templates import EmailTemplate
from src.milestone_detector import MilestoneProximity, Milestone
from src.gameday_checker import Game, Team


class TestEmailTemplate:
    """Test cases for EmailTemplate class"""

    @pytest.fixture
    def sample_milestone_close(self):
        """Create a milestone that's very close to completion"""
        from src.milestone_detector.models import MilestoneType

        milestone = Milestone(
            milestone_id="bball_1000pts",
            sport="basketball",
            stat_name="points",
            threshold=1000,
            milestone_type=MilestoneType.CAREER_TOTAL,
            description="1000 career points",
        )
        return MilestoneProximity(
            player_id="player001",
            player_name="Jane Smith",
            milestone=milestone,
            current_value=985,
            distance=15,
            percentage=98.5,
            estimated_games_to_milestone=2,
        )

    @pytest.fixture
    def sample_milestone_far(self):
        """Create a milestone that's further from completion"""
        from src.milestone_detector.models import MilestoneType

        milestone = Milestone(
            milestone_id="soccer_50goals",
            sport="soccer",
            stat_name="goals",
            threshold=50,
            milestone_type=MilestoneType.CAREER_TOTAL,
            description="50 career goals",
        )
        return MilestoneProximity(
            player_id="player002",
            player_name="John Doe",
            milestone=milestone,
            current_value=40,
            distance=10,
            percentage=80.0,
            estimated_games_to_milestone=None,  # No estimate
        )

    @pytest.fixture
    def sample_milestone_at_100(self):
        """Create a milestone at exactly 100% (edge case)"""
        from src.milestone_detector.models import MilestoneType

        milestone = Milestone(
            milestone_id="track_4min_mile",
            sport="track",
            stat_name="pr_time",
            threshold=240.0,
            milestone_type=MilestoneType.PERSONAL_RECORD,
            description="Break 4:00 mile",
        )
        return MilestoneProximity(
            player_id="player003",
            player_name="Alex Runner",
            milestone=milestone,
            current_value=240.0,
            distance=0,
            percentage=100.0,
            estimated_games_to_milestone=0,
        )

    @pytest.fixture
    def sample_home_game(self):
        """Create a home game"""
        from datetime import datetime

        team = Team(name="Men's Basketball", sport="basketball")
        return Game(team=team, opponent="State University", date=datetime(2024, 3, 15), location="home", time="19:00")

    @pytest.fixture
    def sample_away_game(self):
        """Create an away game"""
        from datetime import datetime

        team = Team(name="Women's Soccer", sport="soccer")
        return Game(team=team, opponent="Rival College", date=datetime(2024, 3, 20), location="away", time="15:30")

    @pytest.fixture
    def sample_game_no_time(self):
        """Create a game without a specified time"""
        from datetime import datetime

        team = Team(name="Track and Field", sport="track")
        return Game(team=team, opponent="Conference Meet", date=datetime(2024, 4, 5), location="home", time=None)

    def test_generate_subject_with_games(self):
        """Test subject generation with games"""
        test_date = date(2024, 3, 15)
        subject = EmailTemplate.generate_subject(test_date, 2)

        assert "March 15, 2024" in subject
        assert "2 games" in subject
        assert "Haverford Sports Alert" in subject

    def test_generate_subject_no_games(self):
        """Test subject generation without games (empty day)"""
        test_date = date(2024, 3, 15)
        subject = EmailTemplate.generate_subject(test_date, 0, 0)

        assert "March 15, 2024" in subject
        assert "Haverford Sports Alert" in subject

    def test_generate_subject_one_game(self):
        """Test subject generation with one game"""
        test_date = date(2024, 12, 25)
        subject = EmailTemplate.generate_subject(test_date, 1)

        assert "December 25, 2024" in subject
        assert "1 game" in subject

    def test_generate_html_with_milestones_and_games(self, sample_milestone_close, sample_home_game):
        """Test HTML generation with both milestones and games"""
        test_date = date(2024, 3, 15)
        html = EmailTemplate.generate_milestone_email([sample_milestone_close], [sample_home_game], test_date)

        # Verify HTML structure
        assert "<html>" in html
        assert "</html>" in html
        assert "<style>" in html

        # Verify date
        assert "March 15, 2024" in html

        # Verify game section
        assert "Today's Games" in html
        assert "Men's Basketball" in html
        assert "State University" in html
        assert "Home" in html
        assert "19:00" in html

        # Verify milestone section
        assert "Players Close to Milestones" in html
        assert "Jane Smith" in html
        assert "1000 career points" in html
        assert "985" in html  # current value
        assert "1000" in html  # threshold
        assert "15" in html  # distance

    def test_generate_html_only_milestones(self, sample_milestone_close):
        """Test HTML generation with only milestones, no games"""
        test_date = date(2024, 3, 15)
        html = EmailTemplate.generate_milestone_email([sample_milestone_close], [], test_date)

        # Should not have games section
        assert "Today's Games" not in html

        # Should have milestone section
        assert "Players Close to Milestones" in html
        assert "Jane Smith" in html

    def test_generate_html_only_games(self, sample_home_game):
        """Test HTML generation with only games, no milestones"""
        test_date = date(2024, 3, 15)
        html = EmailTemplate.generate_milestone_email([], [sample_home_game], test_date)

        # Should have games section
        assert "Today's Games" in html
        assert "Men's Basketball" in html

        # Should have no milestones message
        assert "No Milestone Alerts" in html

    def test_generate_html_empty_lists(self):
        """Test HTML generation with empty lists (empty day)"""
        test_date = date(2024, 3, 15)
        html = EmailTemplate.generate_milestone_email([], [], test_date)

        # Should have basic structure
        assert "<html>" in html
        assert "March 15, 2024" in html

        # Should have no games section
        assert "Today's Games" not in html

        # Should have no milestones message
        assert "No Milestone Alerts" in html

    def test_generate_html_multiple_milestones(self, sample_milestone_close, sample_milestone_far):
        """Test HTML generation with multiple milestones"""
        test_date = date(2024, 3, 15)
        html = EmailTemplate.generate_milestone_email([sample_milestone_close, sample_milestone_far], [], test_date)

        # Should show count
        assert "2 player(s)" in html

        # Should include both players
        assert "Jane Smith" in html
        assert "John Doe" in html

        # Should include both milestones
        assert "1000 career points" in html
        assert "50 career goals" in html

    def test_generate_html_progress_bar(self, sample_milestone_close):
        """Test that progress bar is included in HTML"""
        test_date = date(2024, 3, 15)
        html = EmailTemplate.generate_milestone_email([sample_milestone_close], [], test_date)

        # Should have progress bar elements
        assert "progress-bar" in html
        assert "98.5%" in html  # percentage display

    def test_generate_html_progress_bar_caps_at_100(self, sample_milestone_at_100):
        """Test that progress bar doesn't exceed 100%"""
        test_date = date(2024, 3, 15)
        html = EmailTemplate.generate_milestone_email([sample_milestone_at_100], [], test_date)

        # Should cap at 100%
        assert 'style="width: 100%"' in html or 'style="width: 100.0%"' in html

    def test_generate_html_estimated_games(self, sample_milestone_close):
        """Test that estimated games to milestone is shown"""
        test_date = date(2024, 3, 15)
        html = EmailTemplate.generate_milestone_email([sample_milestone_close], [], test_date)

        # Should show estimated games
        assert "Estimated 2 game(s)" in html

    def test_generate_html_no_estimated_games(self, sample_milestone_far):
        """Test handling when estimated games is None"""
        test_date = date(2024, 3, 15)
        html = EmailTemplate.generate_milestone_email([sample_milestone_far], [], test_date)

        # Should not show estimated games when None
        assert "Estimated" not in html or "N/A" in html

    def test_generate_html_away_game(self, sample_away_game):
        """Test HTML generation for away game"""
        test_date = date(2024, 3, 20)
        html = EmailTemplate.generate_milestone_email([], [sample_away_game], test_date)

        # Should show away location
        assert "Away" in html
        assert "Women's Soccer" in html

    def test_generate_html_game_no_time(self, sample_game_no_time):
        """Test HTML generation for game without time"""
        test_date = date(2024, 4, 5)
        html = EmailTemplate.generate_milestone_email([], [sample_game_no_time], test_date)

        # Should show TBD for time
        assert "TBD" in html

    def test_generate_html_styles_included(self):
        """Test that CSS styles are included in HTML"""
        test_date = date(2024, 3, 15)
        html = EmailTemplate.generate_milestone_email([], [], test_date)

        # Should have style definitions
        assert "font-family:" in html
        assert "color:" in html
        assert "#8B0000" in html  # Haverford color

    def test_generate_text_version_with_milestones_and_games(self, sample_milestone_close, sample_home_game):
        """Test plain text generation with milestones and games"""
        test_date = date(2024, 3, 15)
        text = EmailTemplate.generate_text_version([sample_milestone_close], [sample_home_game], test_date)

        # Verify structure
        assert "HAVERFORD COLLEGE SPORTS MILESTONES" in text
        assert "March 15, 2024" in text

        # Verify games section
        assert "TODAY'S GAMES" in text
        assert "Men's Basketball" in text
        assert "State University" in text
        assert "Home" in text

        # Verify milestone section
        assert "PLAYERS CLOSE TO MILESTONES" in text
        assert "Jane Smith" in text
        assert "1000 career points" in text
        assert "Current: 985" in text
        assert "Target: 1000" in text

    def test_generate_text_version_only_milestones(self, sample_milestone_close):
        """Test text generation with only milestones"""
        test_date = date(2024, 3, 15)
        text = EmailTemplate.generate_text_version([sample_milestone_close], [], test_date)

        # Should not have games section
        assert "TODAY'S GAMES" not in text

        # Should have milestone section
        assert "PLAYERS CLOSE TO MILESTONES" in text

    def test_generate_text_version_only_games(self, sample_home_game):
        """Test text generation with only games"""
        test_date = date(2024, 3, 15)
        text = EmailTemplate.generate_text_version([], [sample_home_game], test_date)

        # Should have games section
        assert "TODAY'S GAMES" in text

        # Should have no milestones message
        assert "NO MILESTONE ALERTS" in text

    def test_generate_text_version_empty_lists(self):
        """Test text generation with empty lists (empty day)"""
        test_date = date(2024, 3, 15)
        text = EmailTemplate.generate_text_version([], [], test_date)

        # Should have basic structure
        assert "HAVERFORD COLLEGE SPORTS MILESTONES" in text
        assert "NO MILESTONE ALERTS" in text

    def test_generate_text_version_formatting(self, sample_milestone_close):
        """Test that text version has proper formatting"""
        test_date = date(2024, 3, 15)
        text = EmailTemplate.generate_text_version([sample_milestone_close], [], test_date)

        # Should have separator lines
        assert "=" * 60 in text
        assert "-" * 60 in text

        # Should have proper indentation
        assert "  Milestone:" in text
        assert "  Current:" in text

    def test_generate_text_version_percentage(self, sample_milestone_close):
        """Test that percentage is shown in text version"""
        test_date = date(2024, 3, 15)
        text = EmailTemplate.generate_text_version([sample_milestone_close], [], test_date)

        # Should show percentage
        assert "98.5% complete" in text

    def test_generate_text_version_multiple_games(self, sample_home_game, sample_away_game):
        """Test text generation with multiple games"""
        test_date = date(2024, 3, 15)
        text = EmailTemplate.generate_text_version([], [sample_home_game, sample_away_game], test_date)

        # Should include both games
        assert "Men's Basketball" in text
        assert "Women's Soccer" in text
        assert "Home" in text
        assert "Away" in text

    def test_generate_text_version_footer(self):
        """Test that footer is included in text version"""
        test_date = date(2024, 3, 15)
        text = EmailTemplate.generate_text_version([], [], test_date)

        # Should have footer
        assert "automated notification" in text.lower()
        assert "StatsTracker" in text

    def test_html_and_text_contain_same_info(self, sample_milestone_close, sample_home_game):
        """Test that HTML and text versions contain the same information"""
        test_date = date(2024, 3, 15)

        html = EmailTemplate.generate_milestone_email([sample_milestone_close], [sample_home_game], test_date)

        text = EmailTemplate.generate_text_version([sample_milestone_close], [sample_home_game], test_date)

        # Both should contain key information
        key_info = ["Jane Smith", "Men's Basketball", "State University", "1000 career points"]

        for info in key_info:
            assert info in html
            assert info in text

    def test_special_characters_in_player_name(self):
        """Test handling of special characters in player names"""
        from src.milestone_detector.models import MilestoneType

        milestone = Milestone(
            milestone_id="bball_1000pts",
            sport="basketball",
            stat_name="points",
            threshold=1000,
            milestone_type=MilestoneType.CAREER_TOTAL,
            description="1000 points",
        )
        prox = MilestoneProximity(
            player_id="player_special",
            player_name="O'Connor, José-María",
            milestone=milestone,
            current_value=950,
            distance=50,
            percentage=95.0,
            estimated_games_to_milestone=3,
        )

        test_date = date(2024, 3, 15)
        html = EmailTemplate.generate_milestone_email([prox], [], test_date)
        text = EmailTemplate.generate_text_version([prox], [], test_date)

        # Should handle special characters
        assert "O'Connor" in html
        assert "José-María" in html
        assert "O'Connor" in text
        assert "José-María" in text

    def test_large_numbers_formatted_correctly(self):
        """Test that large numbers are displayed correctly"""
        from src.milestone_detector.models import MilestoneType

        milestone = Milestone(
            milestone_id="bball_10000pts",
            sport="basketball",
            stat_name="points",
            threshold=10000,
            milestone_type=MilestoneType.CAREER_TOTAL,
            description="10000 career points",
        )
        prox = MilestoneProximity(
            player_id="player_superstar",
            player_name="Superstar Player",
            milestone=milestone,
            current_value=9876,
            distance=124,
            percentage=98.76,
            estimated_games_to_milestone=5,
        )

        test_date = date(2024, 3, 15)
        html = EmailTemplate.generate_milestone_email([prox], [], test_date)

        # Should display large numbers
        assert "9876" in html
        assert "10000" in html
        assert "124" in html


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
