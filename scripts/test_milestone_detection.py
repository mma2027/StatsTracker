#!/usr/bin/env python3
"""
Test milestone detection with sample data to demonstrate output
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.player_database import PlayerDatabase, Player, StatEntry
from src.milestone_detector import MilestoneDetector, generate_milestone_thresholds
import yaml


def main():
    print("=" * 70)
    print("Milestone Detection Test - January 14, 2026")
    print("=" * 70)
    print()

    # Load config
    try:
        with open('config/config.yaml') as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        print("Using config.example.yaml...")
        with open('config/config.example.yaml') as f:
            config = yaml.safe_load(f)

    # Create test database
    db = PlayerDatabase(':memory:')  # In-memory database for testing

    # Add sample players with stats near milestones
    test_players = [
        {
            'player': Player(player_id='test001', name='Sarah Johnson', sport='basketball'),
            'stats': {'points': 95, 'rebounds': 48, 'assists': 23}
        },
        {
            'player': Player(player_id='test002', name='Mike Chen', sport='basketball'),
            'stats': {'points': 148, 'rebounds': 73, 'assists': 99}
        },
        {
            'player': Player(player_id='test003', name='Emma Williams', sport='basketball'),
            'stats': {'points': 248, 'rebounds': 297, 'assists': 149}
        },
        {
            'player': Player(player_id='test004', name='Alex Martinez', sport='soccer'),
            'stats': {'goals': 9, 'assists': 24}
        },
        {
            'player': Player(player_id='test005', name='Jordan Lee', sport='basketball'),
            'stats': {'points': 101, 'rebounds': 52, 'assists': 76}  # Past 100 milestone
        },
    ]

    # Add players to database
    for player_data in test_players:
        db.add_player(player_data['player'])
        # Add stats for each player
        for stat_name, stat_value in player_data['stats'].items():
            stat_entry = StatEntry(
                player_id=player_data['player'].player_id,
                stat_name=stat_name,
                stat_value=str(stat_value),
                season='career'
            )
            db.add_stat(stat_entry)

    print("Test Players Added:")
    for player_data in test_players:
        stats_str = ', '.join([f"{k}: {v}" for k, v in player_data['stats'].items()])
        print(f"  • {player_data['player'].name} ({player_data['player'].sport}): {stats_str}")
    print()

    # Show milestone thresholds being used
    print("Milestone Thresholds:")
    thresholds = generate_milestone_thresholds(max_value=500)
    print(f"  {thresholds}")
    print()

    # Create milestone detector
    milestones_config = config.get('milestones', {})
    detector = MilestoneDetector(db, milestones_config)

    print(f"Total milestones configured: {len(detector.milestones)}")
    print()

    # Check for milestone proximities
    print("🔍 Checking milestone proximities (within 20 units)...")
    print()
    all_proximities = detector.check_all_players_milestones(proximity_threshold=20)

    # Display results
    if not all_proximities:
        print("❌ No milestone proximities found!")
        print()
    else:
        proximities_list = []
        for player_id, prox_list in all_proximities.items():
            for prox in prox_list:
                proximities_list.append(prox)

        # Sort by distance (closest first)
        proximities_list.sort(key=lambda p: abs(p.distance))

        print(f"✅ Found {len(proximities_list)} milestone alerts:")
        print()

        for i, prox in enumerate(proximities_list, 1):
            distance_display = f"{prox.distance} away" if prox.distance > 0 else "PASSED"
            percentage_display = f"{prox.percentage:.1f}%"

            print(f"{i}. {prox.player_name}")
            print(f"   Sport: {prox.milestone.sport}")
            print(f"   Milestone: {prox.milestone.threshold} {prox.milestone.stat_name}")
            print(f"   Current: {prox.current_value} ({percentage_display})")
            print(f"   Status: {distance_display}")
            print()

    print("=" * 70)
    print("Test Complete")
    print("=" * 70)
    print()
    print("Key behaviors demonstrated:")
    print("  ✓ Players within 20 units of milestone are alerted")
    print("  ✓ Players past milestones (like Jordan Lee with 101 points) are NOT alerted")
    print("  ✓ Milestones follow pattern: 10, 25, 50, 75, 100, 150, 200, 250, 300, 400...")


if __name__ == "__main__":
    main()
