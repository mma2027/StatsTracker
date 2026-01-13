#!/usr/bin/env python3
"""
Test TFRR fetcher with individual athlete PR scraping.
"""

import sys
sys.path.insert(0, '/Users/maxfieldma/CS/projects/StatsTracker')

from src.website_fetcher.tfrr_fetcher import TFRRFetcher, HAVERFORD_TEAMS


def test_mens_track_with_prs():
    """Test fetching men's track team with PRs from individual pages."""
    print("=" * 70)
    print("Testing Men's Track Team (with individual PR scraping)")
    print("=" * 70)
    print()

    fetcher = TFRRFetcher()
    team_code = HAVERFORD_TEAMS["mens_track"]

    print(f"Fetching stats for team code: {team_code}")
    print("This will visit each athlete's page to get their PRs...")
    print("(This may take a few minutes)")
    print()

    result = fetcher.fetch_team_stats(team_code, "track")

    if result.success:
        data = result.data
        print(f"✓ Success!")
        print(f"  Team: {data['team_name']}")
        print(f"  Season: {data['season']}")
        print(f"  Athletes: {len(data['athletes'])}")
        print(f"  Event Categories: {len(data['event_categories'])}")
        print()

        if data['event_categories']:
            print(f"  Events found: {', '.join(data['event_categories'][:15])}")
            if len(data['event_categories']) > 15:
                print(f"  ... and {len(data['event_categories']) - 15} more")
        print()

        # Show first few athletes with their PRs
        print("  First 5 Athletes with PRs:")
        for athlete in data['athletes'][:5]:
            print(f"    - {athlete['name']} ({athlete.get('year', 'N/A')})")
            if athlete.get('events'):
                events_list = list(athlete['events'].items())[:3]
                for event, result in events_list:
                    print(f"      {event}: {result}")
                if len(athlete['events']) > 3:
                    print(f"      ... and {len(athlete['events']) - 3} more events")
            else:
                print(f"      (No PRs found)")
        print()
    else:
        print(f"✗ Failed: {result.error}")
        print()


if __name__ == "__main__":
    test_mens_track_with_prs()
