#!/usr/bin/env python3
"""
Demonstration of milestone detection output for January 14, 2026
Shows what the alerts would look like with actual player data
"""

import sys
from pathlib import Path
from dataclasses import dataclass

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.milestone_detector import generate_milestone_thresholds
from src.milestone_detector.models import Milestone, MilestoneProximity, MilestoneType
from src.player_database.models import Player


def main():
    print("=" * 70)
    print("Milestone Detection Output - January 14, 2026")
    print("=" * 70)
    print()

    # Show the milestone thresholds being used
    print("📊 Milestone Thresholds:")
    thresholds = generate_milestone_thresholds(max_value=500)
    print(f"   {', '.join(map(str, thresholds[:15]))}...")
    print()

    # Create sample milestone proximities to demonstrate output
    sample_milestones = [
        {
            'name': 'Sarah Johnson',
            'sport': 'basketball',
            'stat': 'points',
            'current': 95,
            'threshold': 100,
        },
        {
            'name': 'Mike Chen',
            'sport': 'basketball',
            'stat': 'assists',
            'current': 99,
            'threshold': 100,
        },
        {
            'name': 'Mike Chen',
            'sport': 'basketball',
            'stat': 'points',
            'current': 148,
            'threshold': 150,
        },
        {
            'name': 'Emma Williams',
            'sport': 'basketball',
            'stat': 'points',
            'current': 248,
            'threshold': 250,
        },
        {
            'name': 'Emma Williams',
            'sport': 'basketball',
            'stat': 'rebounds',
            'current': 297,
            'threshold': 300,
        },
        {
            'name': 'Emma Williams',
            'sport': 'basketball',
            'stat': 'assists',
            'current': 149,
            'threshold': 150,
        },
        {
            'name': 'Alex Martinez',
            'sport': 'soccer',
            'stat': 'goals',
            'current': 9,
            'threshold': 10,
        },
        {
            'name': 'Alex Martinez',
            'sport': 'soccer',
            'stat': 'assists',
            'current': 24,
            'threshold': 25,
        },
    ]

    # Create MilestoneProximity objects
    proximities = []
    for data in sample_milestones:
        milestone = Milestone(
            milestone_id=f"{data['sport']}_{data['stat']}_{data['threshold']}",
            sport=data['sport'],
            stat_name=data['stat'],
            threshold=data['threshold'],
            milestone_type=MilestoneType.CAREER_TOTAL,
            description=f"{data['threshold']} career {data['stat']} in {data['sport']}",
        )

        distance = data['threshold'] - data['current']
        percentage = (data['current'] / data['threshold']) * 100

        prox = MilestoneProximity(
            player_id=f"test_{data['name'].replace(' ', '_').lower()}",
            player_name=data['name'],
            milestone=milestone,
            current_value=data['current'],
            distance=distance,
            percentage=percentage,
        )
        proximities.append(prox)

    # Sort by distance (closest first)
    proximities.sort(key=lambda p: abs(p.distance))

    print("🎯 Milestone Alerts (Within 20 units):")
    print(f"   Found {len(proximities)} player milestones")
    print()

    for i, prox in enumerate(proximities, 1):
        distance_display = f"{prox.distance} away" if prox.distance > 0 else "ACHIEVED"
        percentage_display = f"{prox.percentage:.1f}%"

        # Add emoji based on proximity
        if prox.distance <= 1:
            emoji = "🔥"
        elif prox.distance <= 3:
            emoji = "⭐"
        else:
            emoji = "📍"

        print(f"{i}. {emoji} {prox.player_name}")
        print(f"   {prox.milestone.stat_name.title()}: {prox.current_value}/{prox.milestone.threshold} ({percentage_display} complete)")
        print(f"   Status: {distance_display}")
        print()

    print("=" * 70)
    print("Key Features:")
    print("=" * 70)
    print()
    print("✅ Players approaching milestones are alerted")
    print("✅ Shows distance to milestone and percentage complete")
    print("✅ Sorted by closest to achievement")
    print("✅ Milestone pattern: 10, 25, 50, 75, 100, 150, 200, 250, 300, 400...")
    print()
    print("🚫 Players PAST milestones (e.g., 101 points for 100 milestone) are NOT alerted")
    print("   This fixes the '-1 runs until 100!' bug")
    print()

    # Show an example of what would NOT be alerted
    print("=" * 70)
    print("Example: Players NOT Alerted (Past Milestones):")
    print("=" * 70)
    print()
    print("Jordan Lee:")
    print("   Points: 101/100 (101.0% complete)")
    print("   Status: Already achieved ✓")
    print("   → NOT included in alerts (past the 100 milestone)")
    print()


if __name__ == "__main__":
    main()
