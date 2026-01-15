"""
Example usage of NCAAFetcher for Haverford College teams.

This script demonstrates how to fetch player statistics from NCAA for
Haverford College teams using the NCAAFetcher class.
"""

from ncaa_fetcher import NCAAFetcher, HAVERFORD_TEAMS


def fetch_team_example(team_id: str, sport: str):
    """Example: Fetch stats for a specific Haverford team."""
    print(f"\n{'=' * 60}")
    print(f"Fetching {sport} stats for team {team_id}")
    print(f"{'=' * 60}\n")

    fetcher = NCAAFetcher()
    result = fetcher.fetch_team_stats(team_id, sport)

    if result.success:
        data = result.data
        print(f"Season: {data['season']}")
        print(f"Sport: {data['sport']}")
        print(f"Team ID: {data['team_id']}")
        print(f"Number of players: {len(data['players'])}")
        print(f"\nStat categories: {', '.join(data['stat_categories'])}")

        print("\nFirst 5 players:")
        for i, player in enumerate(data["players"][:5]):
            print(f"\n{i+1}. {player['name']}")
            print(f"   Stats: {player['stats']}")

    else:
        print(f"Error: {result.error}")


def discover_team_ids():
    """Example: Automatically discover all Haverford team IDs."""
    print("\n" + "=" * 60)
    print("Discovering Haverford College Team IDs")
    print("=" * 60)

    fetcher = NCAAFetcher()
    result = fetcher.get_haverford_teams()

    if result.success:
        teams = result.data["teams"]
        print(f"\n✓ Found {len(teams)} teams:\n")

        for team in sorted(teams, key=lambda x: x["sport"]):
            print(f"  {team['sport']:<25} ID: {team['team_id']}")

        print("\nUse these IDs in your config file for the current season!")
    else:
        print(f"✗ Error: {result.error}")


def fetch_all_haverford_teams():
    """Example: Fetch stats for all Haverford teams."""
    print("\n" + "=" * 60)
    print("Fetching stats for ALL Haverford College teams")
    print("=" * 60)

    fetcher = NCAAFetcher()

    for sport_name, team_id in HAVERFORD_TEAMS.items():
        print(f"\n--- {sport_name.replace('_', ' ').title()} (ID: {team_id}) ---")

        result = fetcher.fetch_team_stats(str(team_id), sport_name)

        if result.success:
            print(f"✓ Successfully fetched {len(result.data['players'])} players")
        else:
            print(f"✗ Error: {result.error}")


def main():
    """Main example runner."""
    print("NCAA Stats Fetcher - Example Usage")
    print("Haverford College Teams\n")

    # Example 1: Discover current team IDs
    # Uncomment to automatically find all current Haverford team IDs:
    # discover_team_ids()

    # Example 2: Fetch Men's Basketball stats
    mens_basketball_id = str(HAVERFORD_TEAMS["mens_basketball"])
    fetch_team_example(mens_basketball_id, "basketball")

    # Example 3: Fetch Women's Soccer stats
    womens_soccer_id = str(HAVERFORD_TEAMS["womens_soccer"])
    fetch_team_example(womens_soccer_id, "soccer")

    # Example 4: Fetch all teams (warning: takes several minutes)
    # Uncomment to test all teams:
    # fetch_all_haverford_teams()


if __name__ == "__main__":
    main()
