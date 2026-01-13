#!/usr/bin/env python3
"""
Test final Jory Lee PR parsing.
"""

import sys
sys.path.insert(0, '/Users/maxfieldma/CS/projects/StatsTracker')

from src.website_fetcher.tfrr_fetcher import TFRRFetcher

fetcher = TFRRFetcher()

print("Fetching Jory Lee's PRs...")
result = fetcher.fetch_player_stats("8317912", "track")

if result.success:
    data = result.data
    print(f"\n✅ SUCCESS!")
    print(f"\nAthlete: {data['name']}")
    print(f"Sport: {data['sport']}")
    print(f"\nPersonal Records ({len(data['events'])} events):")
    print("=" * 50)
    for event, pr in sorted(data['events'].items()):
        print(f"  {event}: {pr}")
else:
    print(f"\n❌ Failed: {result.error}")
