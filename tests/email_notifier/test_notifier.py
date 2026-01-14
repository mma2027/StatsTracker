"""
Unit tests for EmailNotifier class
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, call
import smtplib
from datetime import date

from src.email_notifier import EmailNotifier
from src.milestone_detector import MilestoneProximity, Milestone
from src.gameday_checker import Game, Team


class TestEmailNotifier:
    """Test cases for EmailNotifier class"""

    @pytest.fixture
    def valid_config(self):
        """Create valid email configuration for testing"""
        return {
            'smtp_server': 'smtp.example.com',
            'smtp_port': 587,
            'sender_email': 'sender@example.com',
            'sender_password': 'test_password',
            'recipients': ['recipient1@example.com', 'recipient2@example.com']
        }

    @pytest.fixture
    def notifier(self, valid_config):
        """Create EmailNotifier instance with valid config"""
        return EmailNotifier(valid_config)

    @pytest.fixture
    def sample_milestone(self):
        """Create a sample milestone for testing"""
        from src.milestone_detector.models import MilestoneType
        milestone = Milestone(
            milestone_id="bball_1000pts",
            sport="basketball",
            stat_name="points",
            threshold=1000,
            milestone_type=MilestoneType.CAREER_TOTAL,
            description="1000 career points"
        )
        return MilestoneProximity(
            player_id="player123",
            player_name="John Doe",
            milestone=milestone,
            current_value=950,
            distance=50,
            percentage=95.0,
            estimated_games_to_milestone=3
        )

    @pytest.fixture
    def sample_game(self):
        """Create a sample game for testing"""
        from datetime import datetime
        team = Team(
            name="Men's Basketball",
            sport="basketball"
        )
        return Game(
            team=team,
            opponent="Rival College",
            date=datetime(2024, 3, 15),
            location="home",
            time="19:00"
        )

    def test_init(self, valid_config):
        """Test EmailNotifier initialization"""
        notifier = EmailNotifier(valid_config)

        assert notifier.smtp_server == 'smtp.example.com'
        assert notifier.smtp_port == 587
        assert notifier.sender_email == 'sender@example.com'
        assert notifier.sender_password == 'test_password'
        assert len(notifier.recipients) == 2

    def test_init_default_port(self):
        """Test initialization with default port"""
        config = {
            'smtp_server': 'smtp.example.com',
            'sender_email': 'sender@example.com',
            'sender_password': 'password'
        }
        notifier = EmailNotifier(config)

        assert notifier.smtp_port == 587

    def test_init_empty_recipients(self):
        """Test initialization with no recipients"""
        config = {
            'smtp_server': 'smtp.example.com',
            'sender_email': 'sender@example.com',
            'sender_password': 'password'
        }
        notifier = EmailNotifier(config)

        assert notifier.recipients == []

    def test_validate_config_valid(self, notifier):
        """Test configuration validation with valid config"""
        assert notifier.validate_config() is True

    def test_validate_config_no_smtp_server(self):
        """Test validation fails without SMTP server"""
        config = {
            'sender_email': 'sender@example.com',
            'sender_password': 'password',
            'recipients': ['test@example.com']
        }
        notifier = EmailNotifier(config)

        assert notifier.validate_config() is False

    def test_validate_config_no_sender_email(self):
        """Test validation fails without sender email"""
        config = {
            'smtp_server': 'smtp.example.com',
            'sender_password': 'password',
            'recipients': ['test@example.com']
        }
        notifier = EmailNotifier(config)

        assert notifier.validate_config() is False

    def test_validate_config_no_password(self):
        """Test validation fails without password"""
        config = {
            'smtp_server': 'smtp.example.com',
            'sender_email': 'sender@example.com',
            'recipients': ['test@example.com']
        }
        notifier = EmailNotifier(config)

        assert notifier.validate_config() is False

    def test_validate_config_no_recipients(self):
        """Test validation fails without recipients"""
        config = {
            'smtp_server': 'smtp.example.com',
            'sender_email': 'sender@example.com',
            'sender_password': 'password'
        }
        notifier = EmailNotifier(config)

        assert notifier.validate_config() is False

    def test_add_recipient(self, notifier):
        """Test adding a recipient"""
        initial_count = len(notifier.recipients)
        notifier.add_recipient('new@example.com')

        assert len(notifier.recipients) == initial_count + 1
        assert 'new@example.com' in notifier.recipients

    def test_add_duplicate_recipient(self, notifier):
        """Test adding a duplicate recipient doesn't create duplicates"""
        existing = notifier.recipients[0]
        initial_count = len(notifier.recipients)

        notifier.add_recipient(existing)

        assert len(notifier.recipients) == initial_count

    def test_remove_recipient(self, notifier):
        """Test removing a recipient"""
        email_to_remove = notifier.recipients[0]
        initial_count = len(notifier.recipients)

        notifier.remove_recipient(email_to_remove)

        assert len(notifier.recipients) == initial_count - 1
        assert email_to_remove not in notifier.recipients

    def test_remove_nonexistent_recipient(self, notifier):
        """Test removing a nonexistent recipient doesn't cause error"""
        initial_count = len(notifier.recipients)

        notifier.remove_recipient('nonexistent@example.com')

        assert len(notifier.recipients) == initial_count

    @patch('src.email_notifier.notifier.smtplib.SMTP')
    def test_send_test_email_success(self, mock_smtp, notifier):
        """Test sending a test email successfully"""
        # Setup mock
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        # Send test email
        result = notifier.send_test_email()

        # Verify
        assert result is True
        mock_smtp.assert_called_once_with('smtp.example.com', 587)
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with('sender@example.com', 'test_password')
        mock_server.send_message.assert_called_once()

    @patch('src.email_notifier.notifier.smtplib.SMTP')
    def test_send_email_smtp_auth_error(self, mock_smtp, notifier):
        """Test handling SMTP authentication error"""
        # Setup mock to raise auth error
        mock_server = MagicMock()
        mock_server.login.side_effect = smtplib.SMTPAuthenticationError(535, b'Authentication failed')
        mock_smtp.return_value.__enter__.return_value = mock_server

        # Send test email
        result = notifier.send_test_email()

        # Verify
        assert result is False

    @patch('src.email_notifier.notifier.smtplib.SMTP')
    def test_send_email_smtp_exception(self, mock_smtp, notifier):
        """Test handling general SMTP exception"""
        # Setup mock to raise SMTP exception
        mock_server = MagicMock()
        mock_server.send_message.side_effect = smtplib.SMTPException("Connection error")
        mock_smtp.return_value.__enter__.return_value = mock_server

        # Send test email
        result = notifier.send_test_email()

        # Verify
        assert result is False

    @patch('src.email_notifier.notifier.smtplib.SMTP')
    def test_send_email_general_exception(self, mock_smtp, notifier):
        """Test handling general exception"""
        # Setup mock to raise general exception
        mock_smtp.side_effect = Exception("Unexpected error")

        # Send test email
        result = notifier.send_test_email()

        # Verify
        assert result is False

    @patch('src.email_notifier.notifier.smtplib.SMTP')
    @patch('src.email_notifier.notifier.EmailTemplate.generate_subject')
    @patch('src.email_notifier.notifier.EmailTemplate.generate_milestone_email')
    @patch('src.email_notifier.notifier.EmailTemplate.generate_text_version')
    def test_send_milestone_alert_success(
        self,
        mock_text_gen,
        mock_html_gen,
        mock_subject_gen,
        mock_smtp,
        notifier,
        sample_milestone,
        sample_game
    ):
        """Test sending milestone alert successfully"""
        # Setup mocks
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        mock_subject_gen.return_value = "Test Subject"
        mock_html_gen.return_value = "<html>Test HTML</html>"
        mock_text_gen.return_value = "Test text"

        # Send milestone alert
        test_date = date(2024, 3, 15)
        result = notifier.send_milestone_alert(
            proximities=[sample_milestone],
            games=[sample_game],
            date_for=test_date
        )

        # Verify
        assert result is True
        mock_subject_gen.assert_called_once_with(test_date, 1, True)
        mock_html_gen.assert_called_once_with([sample_milestone], [sample_game], test_date)
        mock_text_gen.assert_called_once_with([sample_milestone], [sample_game], test_date)
        mock_server.send_message.assert_called_once()

    @patch('src.email_notifier.notifier.smtplib.SMTP')
    @patch('src.email_notifier.notifier.EmailTemplate.generate_subject')
    @patch('src.email_notifier.notifier.EmailTemplate.generate_milestone_email')
    @patch('src.email_notifier.notifier.EmailTemplate.generate_text_version')
    def test_send_milestone_alert_empty_lists(
        self,
        mock_text_gen,
        mock_html_gen,
        mock_subject_gen,
        mock_smtp,
        notifier
    ):
        """Test sending milestone alert with empty proximities and games"""
        # Setup mocks
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        mock_subject_gen.return_value = "Test Subject"
        mock_html_gen.return_value = "<html>No milestones</html>"
        mock_text_gen.return_value = "No milestones"

        # Send milestone alert with empty lists
        test_date = date(2024, 3, 15)
        result = notifier.send_milestone_alert(
            proximities=[],
            games=[],
            date_for=test_date
        )

        # Verify
        assert result is True
        mock_subject_gen.assert_called_once_with(test_date, 0, False)

    @patch('src.email_notifier.notifier.smtplib.SMTP')
    @patch('src.email_notifier.notifier.EmailTemplate.generate_subject')
    def test_send_milestone_alert_template_error(
        self,
        mock_subject_gen,
        mock_smtp,
        notifier,
        sample_milestone
    ):
        """Test handling error in template generation"""
        # Setup mock to raise exception
        mock_subject_gen.side_effect = Exception("Template error")

        # Send milestone alert
        test_date = date(2024, 3, 15)
        result = notifier.send_milestone_alert(
            proximities=[sample_milestone],
            games=[],
            date_for=test_date
        )

        # Verify
        assert result is False

    @patch('src.email_notifier.notifier.smtplib.SMTP')
    def test_send_email_creates_correct_message_structure(self, mock_smtp, notifier):
        """Test that email message is created with correct structure"""
        # Setup mock
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        # Send test email
        notifier.send_test_email()

        # Get the message that was sent
        assert mock_server.send_message.called
        sent_message = mock_server.send_message.call_args[0][0]

        # Verify message structure
        assert sent_message['Subject'] == "StatsTracker Test Email"
        assert sent_message['From'] == 'sender@example.com'
        assert sent_message['To'] == 'recipient1@example.com, recipient2@example.com'

        # Verify multipart structure (HTML and text parts)
        parts = list(sent_message.walk())
        assert len(parts) >= 2  # At least container + HTML part

    @patch('src.email_notifier.notifier.smtplib.SMTP')
    def test_send_email_uses_tls(self, mock_smtp, notifier):
        """Test that TLS is enabled for secure connection"""
        # Setup mock
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        # Send test email
        notifier.send_test_email()

        # Verify TLS was started
        mock_server.starttls.assert_called_once()

    @patch('src.email_notifier.notifier.smtplib.SMTP')
    def test_multiple_recipients(self, mock_smtp):
        """Test sending to multiple recipients"""
        config = {
            'smtp_server': 'smtp.example.com',
            'smtp_port': 587,
            'sender_email': 'sender@example.com',
            'sender_password': 'password',
            'recipients': ['user1@example.com', 'user2@example.com', 'user3@example.com']
        }
        notifier = EmailNotifier(config)

        # Setup mock
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        # Send test email
        result = notifier.send_test_email()

        # Verify
        assert result is True
        sent_message = mock_server.send_message.call_args[0][0]
        assert sent_message['To'] == 'user1@example.com, user2@example.com, user3@example.com'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
