"""
Email Notifier Implementation

Sends formatted email notifications about milestones and game schedules.
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Any, Optional
from datetime import date
import logging

from .templates import EmailTemplate
from ..milestone_detector import MilestoneProximity
from ..gameday_checker import Game
from ..pr_tracker import PRBreakthrough


logger = logging.getLogger(__name__)


class EmailNotifier:
    """
    Sends email notifications about milestones and games.

    Handles email composition, formatting, and delivery.
    """

    def __init__(self, email_config: Dict[str, Any]):
        """
        Initialize email notifier.

        Args:
            email_config: Dictionary with email configuration
                - smtp_server: SMTP server address
                - smtp_port: SMTP port (usually 587 for TLS)
                - sender_email: Sender email address
                - sender_password: Sender email password/app password
                - recipients: List of recipient email addresses
        """
        self.smtp_server = email_config.get("smtp_server")
        self.smtp_port = email_config.get("smtp_port", 587)
        self.sender_email = email_config.get("sender_email")
        self.sender_password = email_config.get("sender_password")
        self.recipients = email_config.get("recipients", [])

        logger.info(f"EmailNotifier initialized for {len(self.recipients)} recipients")

    def send_milestone_alert(self, proximities: List[MilestoneProximity], games: List[Game], date_for: date, pr_breakthroughs: Optional[List[PRBreakthrough]] = None) -> bool:
        """
        Send an email alert about milestones and PR breakthroughs.

        Args:
            proximities: List of MilestoneProximity objects
            games: List of games scheduled for the date
            date_for: Date this notification is for
            pr_breakthroughs: List of PR breakthrough objects (optional)

        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            logger.info(
                f"Sending alert: {len(proximities)} milestones, "
                f"{len(games)} games, {len(pr_breakthroughs or [])} PR breakthroughs"
            )

            # Generate email content
            subject = EmailTemplate.generate_subject(date_for, len(games), len(pr_breakthroughs or []))
            html_body = EmailTemplate.generate_milestone_email(proximities, games, date_for, pr_breakthroughs)
            text_body = EmailTemplate.generate_text_version(proximities, games, date_for, pr_breakthroughs)

            # Send email
            return self._send_email(subject, html_body, text_body)

        except Exception as e:
            logger.error(f"Error sending milestone alert: {e}")
            return False

    def send_test_email(self) -> bool:
        """
        Send a test email to verify configuration.

        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            subject = "StatsTracker Test Email"
            html_body = "<h1>Test Email</h1><p>This is a test email from StatsTracker.</p>"
            text_body = "Test Email\n\nThis is a test email from StatsTracker."

            logger.info("Sending test email")
            return self._send_email(subject, html_body, text_body)

        except Exception as e:
            logger.error(f"Error sending test email: {e}")
            return False

    def _send_email(self, subject: str, html_body: str, text_body: Optional[str] = None) -> bool:
        """
        Internal method to send an email.

        Args:
            subject: Email subject
            html_body: HTML email body
            text_body: Plain text alternative (optional)

        Returns:
            True if sent successfully, False otherwise
        """
        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.sender_email
            message["To"] = ", ".join(self.recipients)

            # Add text and HTML parts
            if text_body:
                text_part = MIMEText(text_body, "plain")
                message.attach(text_part)

            html_part = MIMEText(html_body, "html")
            message.attach(html_part)

            # Connect to SMTP server and send
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()  # Enable TLS
                server.login(self.sender_email, self.sender_password)
                server.send_message(message)

            logger.info(f"Email sent successfully to {len(self.recipients)} recipients")
            return True

        except smtplib.SMTPAuthenticationError:
            logger.error("SMTP authentication failed - check credentials")
            return False
        except smtplib.SMTPException as e:
            logger.error(f"SMTP error: {e}")
            return False
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return False

    def add_recipient(self, email: str):
        """Add a recipient to the notification list"""
        if email not in self.recipients:
            self.recipients.append(email)
            logger.info(f"Added recipient: {email}")

    def remove_recipient(self, email: str):
        """Remove a recipient from the notification list"""
        if email in self.recipients:
            self.recipients.remove(email)
            logger.info(f"Removed recipient: {email}")

    def validate_config(self) -> bool:
        """
        Validate that email configuration is complete.

        Returns:
            True if configuration is valid, False otherwise
        """
        if not self.smtp_server:
            logger.error("SMTP server not configured")
            return False

        if not self.sender_email:
            logger.error("Sender email not configured")
            return False

        if not self.sender_password:
            logger.error("Sender password not configured")
            return False

        if not self.recipients:
            logger.warning("No recipients configured")
            return False

        logger.info("Email configuration is valid")
        return True
