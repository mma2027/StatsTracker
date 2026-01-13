#!/usr/bin/env python3
"""
Send notification email for January 14, 2026

This script simulates the notification that would be sent for Jan 14
when there are basketball games vs Ursinus.

Before running:
1. Update config/config.yaml with your Gmail app password
2. Make sure sender_email and recipients are correct

Usage:
    ./venv/bin/python send_jan14_notification.py
"""

import sys
from datetime import date
from pathlib import Path
import yaml

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.gameday_checker.models import Game, Team
from src.player_database import PlayerDatabase
from src.milestone_detector import MilestoneDetector
from src.email_notifier import EmailNotifier


def main():
    print("="*70)
    print("Send Notification for January 14, 2026")
    print("="*70)
    print()

    # Load config
    try:
        with open('config/config.yaml') as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        print("❌ Error: config/config.yaml not found")
        print("   Please copy config.example.yaml to config.yaml and configure it")
        return

    # Setup
    check_date = date(2026, 1, 14)

    # Create games for Jan 14
    games = [
        Game(
            team=Team(name="Haverford Women's Basketball", sport="Women's Basketball"),
            opponent="Ursinus",
            date=check_date,
            location="home",
            time="7:00 PM"
        ),
        Game(
            team=Team(name="Haverford Men's Basketball", sport="Men's Basketball"),
            opponent="Ursinus",
            date=check_date,
            location="home",
            time="5:00 PM"
        )
    ]

    print(f"📅 Games for {check_date}:")
    for game in games:
        print(f"   • {game.team.sport}: Haverford vs {game.opponent} ({game.time})")
    print()

    # Get milestones
    print("🔍 Checking milestone proximities...")
    db = PlayerDatabase('data/stats.db')
    milestones = config.get('milestones', {})
    detector = MilestoneDetector(db, milestones)
    all_proximities = detector.check_all_players_milestones(proximity_threshold=20)

    # Filter individual players only (exclude team totals)
    proximities_list = []
    for player_id, prox_list in all_proximities.items():
        for prox in prox_list:
            # Filter out team totals
            if 'Total' not in prox.player_name and 'Opponent' not in prox.player_name:
                proximities_list.append(prox)

    # Sort by distance (closest first)
    proximities_list.sort(key=lambda p: abs(p.distance))

    # Show top alerts
    print(f"🎯 Found {len(proximities_list)} milestone alerts")
    if proximities_list:
        print("   Top 5:")
        for prox in proximities_list[:5]:
            status = "✓" if prox.distance <= 0 else f"{abs(prox.distance)} away"
            print(f"   • {prox.player_name}: {prox.current_value}/{prox.milestone.threshold} {prox.milestone.stat_name} ({status})")
    print()

    # Send email
    email_config = config.get('email', {})
    notifier = EmailNotifier(email_config)

    # Check configuration
    if not notifier.validate_config():
        print("❌ Email configuration is invalid")
        print()
        print("Please update config/config.yaml with:")
        print("  - sender_email: Your Gmail address")
        print("  - sender_password: Gmail app password (16 chars)")
        print("  - recipients: List of recipient emails")
        print()
        print("See HOW_TO_SEND_EMAIL.md for instructions")
        return

    # Show what will be sent
    recipients = email_config.get('recipients', [])
    print(f"📧 Sending email...")
    print(f"   To: {', '.join(recipients)}")
    print(f"   From: {email_config.get('sender_email')}")
    print(f"   Games: {len(games)}")
    print(f"   Milestone alerts: {len(proximities_list[:10])}")
    print()

    # Confirm
    response = input("Send email now? (y/n): ")
    if response.lower() != 'y':
        print("❌ Cancelled")
        return

    print()
    print("Sending...")

    # Send the email
    success = notifier.send_milestone_alert(
        proximities=proximities_list[:10],
        games=games,
        date_for=check_date
    )

    print()
    if success:
        print("="*70)
        print("✅ Email sent successfully!")
        print("="*70)
        print()
        print(f"Check your inbox at {recipients[0]}")
    else:
        print("="*70)
        print("❌ Failed to send email")
        print("="*70)
        print()
        print("Common issues:")
        print("  - Invalid Gmail app password")
        print("  - 2-Step Verification not enabled")
        print("  - Incorrect sender_email")
        print()
        print("See HOW_TO_SEND_EMAIL.md for troubleshooting")


if __name__ == "__main__":
    main()
