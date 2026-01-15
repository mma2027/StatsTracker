"""
Fetch women's squash data from both 2024-25 and 2025-26 seasons and create CSV
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import csv  # noqa: E402
from collections import defaultdict  # noqa: E402
import logging  # noqa: E402
from src.website_fetcher import SquashFetcher  # noqa: E402

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def fetch_womens_squash():
    """Fetch women's squash data from both seasons and create combined CSV"""

    print("=" * 80)
    print("FETCHING HAVERFORD WOMEN'S SQUASH DATA FROM BOTH SEASONS")
    print("=" * 80)

    # Team IDs for women's squash
    team_2024_25 = "40967"  # 2024-25 season
    team_2025_26 = "45078"  # 2025-26 season

    # Create fetcher
    fetcher = SquashFetcher()

    # Fetch 2024-25 data
    print(f"\n1. Fetching women's 2024-25 season data (team {team_2024_25})...")
    result_24_25 = fetcher.fetch_team_stats(team_2024_25, "squash")

    if not result_24_25.success:
        print(f"   ❌ Failed to fetch 2024-25 data: {result_24_25.error}")
        return

    print(f"   ✓ Fetched {len(result_24_25.data['players'])} players from 2024-25")

    # Fetch 2025-26 data
    print(f"\n2. Fetching women's 2025-26 season data (team {team_2025_26})...")
    result_25_26 = fetcher.fetch_team_stats(team_2025_26, "squash")

    if not result_25_26.success:
        print(f"   ❌ Failed to fetch 2025-26 data: {result_25_26.error}")
        return

    print(f"   ✓ Fetched {len(result_25_26.data['players'])} players from 2025-26")

    # Combine data by player name
    print("\n3. Combining data...")
    player_stats = defaultdict(lambda: {"2024-25": 0, "2025-26": 0})

    # Add 2024-25 wins
    for player in result_24_25.data["players"]:
        name = player["name"]
        wins = int(player["stats"]["wins"])
        player_stats[name]["2024-25"] = wins

    # Add 2025-26 wins
    for player in result_25_26.data["players"]:
        name = player["name"]
        wins = int(player["stats"]["wins"])
        player_stats[name]["2025-26"] = wins

    # Calculate totals
    for name in player_stats:
        player_stats[name]["total"] = player_stats[name]["2024-25"] + player_stats[name]["2025-26"]

    # Sort by total wins (descending)
    sorted_players = sorted(player_stats.items(), key=lambda x: x[1]["total"], reverse=True)

    # Create CSV
    output_dir = Path(__file__).parent.parent / "csv_exports"
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / "haverford_womens_squash_combined_seasons.csv"

    print(f"\n4. Writing CSV to {output_file}...")
    with open(output_file, "w", newline="") as f:
        writer = csv.writer(f)

        # Write header
        writer.writerow(["Player Name", "Wins 2024-25", "Wins 2025-26", "Total Wins"])

        # Write data
        for name, stats in sorted_players:
            writer.writerow([name, stats["2024-25"], stats["2025-26"], stats["total"]])

    print("   ✓ CSV file created successfully!")

    # Display summary
    print("\n" + "=" * 80)
    print("COMBINED RESULTS - WOMEN'S SQUASH")
    print("=" * 80)
    print(f"{'Player Name':<30} {'2024-25':<12} {'2025-26':<12} {'Total':<10}")
    print("-" * 80)

    for name, stats in sorted_players:
        print(f"{name:<30} {stats['2024-25']:<12} {stats['2025-26']:<12} {stats['total']:<10}")

    print("\n" + "=" * 80)
    print("SUMMARY STATISTICS - WOMEN'S SQUASH")
    print("=" * 80)
    total_24_25 = sum(s["2024-25"] for s in player_stats.values())
    total_25_26 = sum(s["2025-26"] for s in player_stats.values())
    total_combined = sum(s["total"] for s in player_stats.values())

    print(f"Total players: {len(player_stats)}")
    print(f"Total wins 2024-25: {total_24_25}")
    print(f"Total wins 2025-26: {total_25_26}")
    print(f"Total wins combined: {total_combined}")
    print(f"\nCSV saved to: {output_file}")

    return output_file


if __name__ == "__main__":
    fetch_womens_squash()
