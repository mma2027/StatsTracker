#!/usr/bin/env python3
"""
Manual Cricket Data Merger

Use this script when you have manually downloaded cricket statistics CSVs
from cricclubs.com and want to merge them into a single file.

Usage:
    1. Download/export tables from cricclubs.com as CSV files
    2. Place them in the same directory as this script or specify paths
    3. Run: python merge_manual_cricket_data.py
"""

import pandas as pd
import argparse
import sys
from pathlib import Path


def merge_cricket_data(batting_file, bowling_file, fielding_file, output_file):
    """
    Merge batting, bowling, and fielding CSV files.

    Args:
        batting_file: Path to batting CSV
        bowling_file: Path to bowling CSV
        fielding_file: Path to fielding CSV
        output_file: Path for output merged CSV

    Returns:
        True if successful, False otherwise
    """
    try:
        print("=" * 70)
        print("CRICKET DATA MERGER")
        print("=" * 70)

        # Read CSV files
        print(f"\n1. Reading CSV files...")
        print(f"   - Batting:  {batting_file}")
        batting_df = pd.read_csv(batting_file)
        print(f"     ✅ Loaded {len(batting_df)} rows, {len(batting_df.columns)} columns")

        print(f"   - Bowling:  {bowling_file}")
        bowling_df = pd.read_csv(bowling_file)
        print(f"     ✅ Loaded {len(bowling_df)} rows, {len(bowling_df.columns)} columns")

        print(f"   - Fielding: {fielding_file}")
        fielding_df = pd.read_csv(fielding_file)
        print(f"     ✅ Loaded {len(fielding_df)} rows, {len(fielding_df.columns)} columns")

        # Identify player column
        print(f"\n2. Identifying player column...")
        player_col = None
        for col in batting_df.columns:
            if col.lower() in ['player', 'name', 'player name']:
                player_col = col
                break

        if not player_col:
            print("   ❌ ERROR: Could not find Player/Name column")
            print("   Available columns:", list(batting_df.columns))
            return False

        print(f"   ✅ Using '{player_col}' as player identifier")

        # Standardize column names
        print(f"\n3. Standardizing column names...")
        if player_col != "Player":
            batting_df.rename(columns={player_col: "Player"}, inplace=True)
            bowling_df.rename(columns={player_col: "Player"}, inplace=True)
            fielding_df.rename(columns={player_col: "Player"}, inplace=True)

        # Add prefixes to columns (except Player)
        print(f"   - Adding 'Batting_' prefix...")
        batting_df.columns = [
            col if col == "Player" else f"Batting_{col}"
            for col in batting_df.columns
        ]

        print(f"   - Adding 'Bowling_' prefix...")
        bowling_df.columns = [
            col if col == "Player" else f"Bowling_{col}"
            for col in bowling_df.columns
        ]

        print(f"   - Adding 'Fielding_' prefix...")
        fielding_df.columns = [
            col if col == "Player" else f"Fielding_{col}"
            for col in fielding_df.columns
        ]

        # Merge dataframes
        print(f"\n4. Merging dataframes...")
        print(f"   - Merging batting and bowling...")
        merged = batting_df.merge(bowling_df, on="Player", how="outer")
        print(f"     ✅ {len(merged)} rows after merge")

        print(f"   - Merging with fielding...")
        merged = merged.merge(fielding_df, on="Player", how="outer")
        print(f"     ✅ {len(merged)} rows after merge")

        # Filter for Haverford players (if team column exists)
        print(f"\n5. Filtering data...")
        team_cols = [col for col in merged.columns if 'team' in col.lower()]
        if team_cols:
            print(f"   Found team column(s): {team_cols}")
            for col in team_cols:
                if merged[col].str.contains("Haverford", case=False, na=False).any():
                    original_len = len(merged)
                    merged = merged[
                        merged[col].str.contains("Haverford", case=False, na=False)
                    ]
                    print(f"   ✅ Filtered to {len(merged)} Haverford players (removed {original_len - len(merged)})")
                    break
        else:
            print(f"   ℹ️  No team column found, keeping all {len(merged)} players")

        # Sort by player name
        print(f"\n6. Sorting by player name...")
        merged = merged.sort_values("Player").reset_index(drop=True)

        # Export to CSV
        print(f"\n7. Exporting to CSV...")
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        merged.to_csv(output_file, index=False, encoding="utf-8")
        print(f"   ✅ Exported to: {output_file}")

        # Summary
        print(f"\n" + "=" * 70)
        print(f"✅ SUCCESS!")
        print(f"=" * 70)
        print(f"\n📊 Final Statistics:")
        print(f"   - Total players:    {len(merged)}")
        print(f"   - Total columns:    {len(merged.columns)}")
        print(f"   - Batting columns:  {len([c for c in merged.columns if c.startswith('Batting_')])}")
        print(f"   - Bowling columns:  {len([c for c in merged.columns if c.startswith('Bowling_')])}")
        print(f"   - Fielding columns: {len([c for c in merged.columns if c.startswith('Fielding_')])}")

        print(f"\n👥 Players:")
        for i, player in enumerate(merged["Player"], 1):
            print(f"   {i}. {player}")

        print(f"\n📁 Output file: {output_file}")
        print("=" * 70)

        return True

    except FileNotFoundError as e:
        print(f"\n❌ ERROR: File not found - {e}")
        print("\nMake sure all CSV files exist:")
        print(f"  - {batting_file}")
        print(f"  - {bowling_file}")
        print(f"  - {fielding_file}")
        return False

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Merge manually downloaded cricket statistics CSV files"
    )
    parser.add_argument(
        "--batting",
        "-b",
        default="batting_manual.csv",
        help="Path to batting CSV file (default: batting_manual.csv)",
    )
    parser.add_argument(
        "--bowling",
        "-o",
        default="bowling_manual.csv",
        help="Path to bowling CSV file (default: bowling_manual.csv)",
    )
    parser.add_argument(
        "--fielding",
        "-f",
        default="fielding_manual.csv",
        help="Path to fielding CSV file (default: fielding_manual.csv)",
    )
    parser.add_argument(
        "--output",
        "-O",
        default="csv_exports/haverford_cricket_stats.csv",
        help="Output CSV file path (default: csv_exports/haverford_cricket_stats.csv)",
    )

    args = parser.parse_args()

    success = merge_cricket_data(
        args.batting,
        args.bowling,
        args.fielding,
        args.output
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
