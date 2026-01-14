#!/usr/bin/env python3
"""
Quick test to verify milestone detection is working with correct stat names
"""

from src.player_database import PlayerDatabase
from src.milestone_detector import MilestoneDetector
import yaml

# Load config
with open('config/config.yaml') as f:
    config = yaml.safe_load(f)

# Initialize
db = PlayerDatabase('data/stats.db')
detector = MilestoneDetector(db, config['milestones'])

print("=" * 70)
print("Testing Milestone Detection with NCAA Stat Names")
print("=" * 70)
print()

# Test with mens_basketball
print("Checking Men's Basketball players...")
mens_bb = detector.check_all_players_milestones(sport='mens_basketball', proximity_threshold=20)

if mens_bb:
    print(f"✅ Found {len(mens_bb)} players with milestone alerts")
    for player_id, proximities in list(mens_bb.items())[:3]:
        for prox in proximities:
            print(f"  • {prox.player_name}: {prox.current_value}/{prox.milestone.threshold} {prox.milestone.stat_name} ({prox.distance} away)")
else:
    print("❌ No alerts found for men's basketball")

print()

# Test with womens_basketball
print("Checking Women's Basketball players...")
womens_bb = detector.check_all_players_milestones(sport='womens_basketball', proximity_threshold=20)

if womens_bb:
    print(f"✅ Found {len(womens_bb)} players with milestone alerts")
    for player_id, proximities in list(womens_bb.items())[:3]:
        for prox in proximities:
            print(f"  • {prox.player_name}: {prox.current_value}/{prox.milestone.threshold} {prox.milestone.stat_name} ({prox.distance} away)")
else:
    print("❌ No alerts found for women's basketball")

print()
print("=" * 70)
