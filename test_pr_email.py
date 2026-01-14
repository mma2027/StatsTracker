#!/usr/bin/env python3
"""
Quick test script for PR breakthrough email generation
Tests the email content generation without actually sending emails
"""

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.pr_tracker import PRBreakthrough
from src.email_notifier.templates import EmailTemplate
from src.gameday_checker.models import Game, Team
from src.milestone_detector.models import Milestone, MilestoneProximity, MilestoneType

def test_pr_email_generation():
    """Test email content generation with PR breakthroughs"""

    print("=" * 70)
    print("Testing PR Breakthrough Email Generation")
    print("=" * 70)
    print()

    # Create mock PR breakthroughs
    pr_breakthroughs = [
        PRBreakthrough(
            athlete_id="jory_lee",
            athlete_name="Jory Lee",
            event="60m",
            old_pr="7.70",
            new_pr="7.65",
            improvement="0.05s",
            date=date(2026, 1, 13),
            meet_name="Penn Relays"
        ),
        PRBreakthrough(
            athlete_id="aaron_benjamin",
            athlete_name="Aaron Benjamin",
            event="Long Jump",
            old_pr="5.80m",
            new_pr="5.95m",
            improvement="0.15m",
            date=date(2026, 1, 13),
            meet_name=None
        ),
        PRBreakthrough(
            athlete_id="test_athlete",
            athlete_name="Test Runner",
            event="200m",
            old_pr="24.50",
            new_pr="24.25",
            improvement="0.25s",
            date=date(2026, 1, 13),
            meet_name="Indoor Championships"
        )
    ]

    # Create mock games
    games = [
        Game(
            team=Team(name="Haverford Men's Basketball", sport="Men's Basketball"),
            opponent="Ursinus",
            date=date(2026, 1, 14),
            location="home",
            time="5:00 PM"
        )
    ]

    # Create mock milestone proximity
    milestone = Milestone(
        milestone_id="m1000pts",
        sport="basketball",
        stat_name="points",
        threshold=1000,
        milestone_type=MilestoneType.CAREER_TOTAL,
        description="1000 career points"
    )

    proximities = [
        MilestoneProximity(
            player_id="test_player",
            player_name="Test Player",
            milestone=milestone,
            current_value=985,
            distance=15,
            percentage=98.5,
            estimated_games_to_milestone=2
        )
    ]

    check_date = date(2026, 1, 14)

    # Generate subject
    print("📧 Generating email subject...")
    subject = EmailTemplate.generate_subject(
        check_date,
        len(games),
        len(pr_breakthroughs)
    )
    print(f"   Subject: {subject}")
    print()

    # Generate HTML body
    print("📧 Generating HTML email body...")
    html_body = EmailTemplate.generate_milestone_email(
        proximities,
        games,
        check_date,
        pr_breakthroughs
    )
    print(f"   HTML length: {len(html_body)} characters")
    print()

    # Generate text version
    print("📧 Generating plain text email body...")
    text_body = EmailTemplate.generate_text_version(
        proximities,
        games,
        check_date,
        pr_breakthroughs
    )
    print(f"   Text length: {len(text_body)} characters")
    print()

    # Save to files for inspection
    output_dir = Path("test_output")
    output_dir.mkdir(exist_ok=True)

    with open(output_dir / "test_email.html", "w") as f:
        f.write(html_body)
    print(f"✓ HTML email saved to: {output_dir / 'test_email.html'}")

    with open(output_dir / "test_email.txt", "w") as f:
        f.write(text_body)
    print(f"✓ Text email saved to: {output_dir / 'test_email.txt'}")
    print()

    # Show preview of text version
    print("=" * 70)
    print("Preview of Plain Text Email:")
    print("=" * 70)
    print(text_body)
    print()

    print("=" * 70)
    print("✅ Email generation test completed successfully!")
    print("=" * 70)
    print()
    print("Next steps:")
    print("  1. Open test_output/test_email.html in a browser to see the HTML version")
    print("  2. Check test_output/test_email.txt to see the plain text version")
    print("  3. To actually send emails, configure config/config.yaml and run:")
    print("     python3 scripts/send_jan14_notification.py")

if __name__ == "__main__":
    test_pr_email_generation()
