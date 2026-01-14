#!/usr/bin/env python3
"""
StatsTracker Main Orchestrator

This script coordinates all modules to:
1. Check for games today
2. Fetch statistics from websites
3. Update player database
4. Detect milestone proximities
5. Send email notifications

Run this script daily (e.g., via cron job) to send notifications.
"""

import sys
import logging
import hashlib
from datetime import date, datetime
from pathlib import Path
import yaml
import pandas as pd

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.gameday_checker import GamedayChecker
from src.website_fetcher import NCAAFetcher, TFRRFetcher
from src.website_fetcher.cricket_fetcher import CricketFetcher
from src.player_database import PlayerDatabase, Player, StatEntry
from src.milestone_detector import MilestoneDetector
from src.email_notifier import EmailNotifier
from scripts.auto_update_team_ids import fetch_with_auto_recovery


def setup_logging(log_level: str = "INFO", log_file: str = None):
    """
    Configure logging for the application.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path
    """
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    handlers = [logging.StreamHandler()]
    if log_file:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(log_file))

    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        handlers=handlers
    )


def load_config(config_path: str = "config/config.yaml") -> dict:
    """
    Load configuration from YAML file.

    Args:
        config_path: Path to configuration file

    Returns:
        Configuration dictionary
    """
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        logging.info(f"Configuration loaded from {config_path}")
        return config
    except FileNotFoundError:
        logging.error(f"Configuration file not found: {config_path}")
        logging.info("Please copy config/config.example.yaml to config/config.yaml and configure it")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Error loading configuration: {e}")
        sys.exit(1)


def generate_player_id(name: str, sport: str) -> str:
    """
    Generate a unique player ID from name and sport.

    Args:
        name: Player name
        sport: Sport

    Returns:
        Unique player ID (hash-based)
    """
    raw = f"{name.lower().strip()}_{sport.lower()}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def extract_player_info(player_data: dict, sport: str) -> dict:
    """
    Extract player metadata from NCAA stats.

    Args:
        player_data: Player dict from NCAA fetcher
        sport: Sport name

    Returns:
        Dict with position, year, etc.
    """
    stats = player_data.get('stats', {})

    return {
        'position': stats.get('Pos', stats.get('Position', '')),
        'year': stats.get('Yr', stats.get('Year', stats.get('Class', ''))),
        'number': stats.get('#', stats.get('No', stats.get('Jersey', ''))),
    }


def update_team_stats(
    fetcher: NCAAFetcher,
    db: PlayerDatabase,
    sport_key: str,
    team_id: str,
    season: str,
    logger: logging.Logger
) -> dict:
    """
    Fetch stats for one team and update database.

    Args:
        fetcher: NCAAFetcher instance
        db: PlayerDatabase instance
        sport_key: Sport key (e.g., 'mens_basketball')
        team_id: NCAA team ID
        season: Season string (e.g., '2025-26')
        logger: Logger instance

    Returns:
        Dict with results (players_added, stats_added, errors)
    """
    sport_display = sport_key.replace('_', ' ').title()
    logger.info(f"Processing {sport_display} (ID: {team_id})")

    # Fetch with auto-recovery
    result = fetch_with_auto_recovery(team_id, sport_key)

    if not result:
        logger.error(f"Auto-recovery failed for {sport_display}")
        return {'error': 'Auto-recovery failed', 'players_added': 0, 'stats_added': 0}

    if not result.success:
        if "No statistics available yet" in result.error:
            logger.warning(f"Season not started yet for {sport_display} - skipping")
            return {'skipped': True, 'players_added': 0, 'stats_added': 0}
        else:
            logger.error(f"Error fetching {sport_display}: {result.error}")
            return {'error': result.error, 'players_added': 0, 'stats_added': 0}

    # Process players
    data = result.data
    players = data['players']
    stat_categories = data['stat_categories']

    logger.info(f"Found {len(players)} players with {len(stat_categories)} stat categories")

    players_added = 0
    players_updated = 0
    stats_added = 0
    errors = []

    for player_data in players:
        player_name = player_data['name']

        try:
            # Generate player ID
            player_id = generate_player_id(player_name, sport_key)

            # Extract player info
            player_info = extract_player_info(player_data, sport_key)

            # Check if player exists
            existing_player = db.get_player(player_id)

            if existing_player:
                # Update player info if needed
                existing_player.position = player_info['position'] or existing_player.position
                existing_player.year = player_info['year'] or existing_player.year
                db.update_player(existing_player)
                players_updated += 1
            else:
                # Add new player
                player = Player(
                    player_id=player_id,
                    name=player_name,
                    sport=sport_key,
                    team='Haverford',
                    position=player_info['position'],
                    year=player_info['year'],
                    active=True
                )
                db.add_player(player)
                players_added += 1

            # Add stats
            for stat_name, stat_value in player_data['stats'].items():
                if stat_value == '' or stat_value is None:
                    continue

                stat_entry = StatEntry(
                    player_id=player_id,
                    stat_name=stat_name,
                    stat_value=stat_value,
                    season=season,
                    date_recorded=datetime.now()
                )
                db.add_stat(stat_entry)
                stats_added += 1

        except Exception as e:
            error_msg = f"Error processing {player_name}: {e}"
            logger.error(error_msg)
            errors.append(error_msg)

    logger.info(f"Added {players_added} new players, updated {players_updated} players")
    logger.info(f"Added {stats_added} stat entries")

    if errors:
        logger.warning(f"{len(errors)} errors occurred")

    return {
        'success': True,
        'players_added': players_added,
        'players_updated': players_updated,
        'stats_added': stats_added,
        'errors': errors
    }


def update_cricket_stats(
    db: PlayerDatabase,
    cricket_config: dict,
    season: str,
    logger: logging.Logger
) -> dict:
    """
    Fetch cricket stats and update database.

    Args:
        db: PlayerDatabase instance
        cricket_config: Cricket fetcher configuration
        season: Season string (e.g., '2025-26')
        logger: Logger instance

    Returns:
        Dict with results (players_added, stats_added, errors)
    """
    logger.info("Processing Cricket")

    try:
        # Initialize cricket fetcher
        cricket_fetcher = CricketFetcher(
            timeout=cricket_config.get('timeout', 30),
            headless=cricket_config.get('headless', True)
        )

        # Fetch all cricket stats
        result = cricket_fetcher.fetch_all_stats()

        if not result["success"]:
            logger.error(f"Error fetching cricket stats: {result.get('error')}")
            return {'error': result.get('error'), 'players_added': 0, 'stats_added': 0}

        # Get DataFrame with all players
        df = result["data"]
        logger.info(f"Found {len(df)} cricket players")

        players_added = 0
        players_updated = 0
        stats_added = 0
        errors = []

        # Process each player
        for _, row in df.iterrows():
            player_name = row['Player']

            try:
                # Generate player ID
                player_id = generate_player_id(player_name, 'cricket')

                # Check if player exists
                existing_player = db.get_player(player_id)

                if existing_player:
                    players_updated += 1
                else:
                    # Add new player
                    player = Player(
                        player_id=player_id,
                        name=player_name,
                        sport='cricket',
                        team='Haverford',
                        position=None,
                        year=None,
                        active=True
                    )
                    db.add_player(player)
                    players_added += 1

                # Add stats for all columns except Player name
                for col in df.columns:
                    if col == 'Player':
                        continue

                    stat_value = row[col]

                    # Skip empty or null values
                    if pd.isna(stat_value) or stat_value == '' or stat_value == 0:
                        continue

                    stat_entry = StatEntry(
                        player_id=player_id,
                        stat_name=col,
                        stat_value=str(stat_value),
                        season=season,
                        date_recorded=datetime.now()
                    )
                    db.add_stat(stat_entry)
                    stats_added += 1

            except Exception as e:
                error_msg = f"Error processing player {player_name}: {e}"
                logger.error(error_msg)
                errors.append(error_msg)

        logger.info(f"Added {players_added} new players, updated {players_updated} players")
        logger.info(f"Added {stats_added} stat entries")

        if errors:
            logger.warning(f"{len(errors)} errors occurred")

        return {
            'success': True,
            'players_added': players_added,
            'players_updated': players_updated,
            'stats_added': stats_added,
            'errors': errors
        }

    except Exception as e:
        logger.error(f"Critical error in cricket stats update: {e}", exc_info=True)
        return {'error': str(e), 'players_added': 0, 'stats_added': 0}


def main():
    """Main execution function"""

    # Load configuration
    config = load_config()

    # Setup logging
    log_config = config.get('logging', {})
    setup_logging(
        log_level=log_config.get('level', 'INFO'),
        log_file=log_config.get('file')
    )

    logger = logging.getLogger(__name__)
    logger.info("=" * 60)
    logger.info("StatsTracker Starting")
    logger.info("=" * 60)

    try:
        # Initialize modules
        logger.info("Initializing modules...")

        # 1. Gameday Checker
        gameday_config = config.get('gameday', {})
        gameday_checker = GamedayChecker(
            schedule_url=gameday_config.get('haverford_schedule_url')
        )

        # 2. Player Database
        db_config = config.get('database', {})
        database = PlayerDatabase(
            db_path=db_config.get('path', 'data/stats.db')
        )

        # 3. Milestone Detector
        milestone_config = config.get('milestones', {})
        milestone_detector = MilestoneDetector(database, milestone_config)

        # 4. Email Notifier
        email_config = config.get('email', {})
        notifier = EmailNotifier(email_config)

        # Validate email configuration
        if not notifier.validate_config():
            logger.error("Email configuration is invalid. Please check config/config.yaml")
            return

        logger.info("All modules initialized successfully")

        # Always update stats for daily automation
        notification_config = config.get('notifications', {})
        logger.info("Fetching latest stats for all teams (daily update)...")
        try:
            update_stats(auto_mode=True)
            logger.info("Stats update completed successfully")
        except Exception as e:
            logger.warning(f"Stats update failed: {e}")
            logger.warning("Continuing with existing data...")

        # Check for games today
        today = date.today()
        logger.info(f"Checking for games on {today.strftime('%Y-%m-%d')}")

        games_today = gameday_checker.get_games_for_today()
        logger.info(f"Found {len(games_today)} game(s) today")

        # Check if notifications are enabled
        if not notification_config.get('enabled', True):
            logger.info("Notifications are disabled in configuration")
            return

        # Get proximity threshold from config
        proximity_threshold = notification_config.get('proximity_threshold', 10)

        # Extract sports with games today (only check milestones for these sports)
        sports_with_games_today = set()
        if games_today:
            for game in games_today:
                # Normalize sport name from Haverford Athletics API format to database format
                # e.g., "Men's Basketball" -> "mens_basketball"
                sport_key = game.team.sport.lower().replace(' ', '_').replace("'", '')
                sports_with_games_today.add(sport_key)

            logger.info(f"Sports with games today: {', '.join(sports_with_games_today)}")

        # Check for milestone proximities (ONLY for sports with games today)
        logger.info("Checking for milestone proximities...")
        proximities_list = []

        if sports_with_games_today:
            for sport_key in sports_with_games_today:
                logger.info(f"Checking milestones for {sport_key}...")
                sport_proximities = milestone_detector.check_all_players_milestones(
                    sport=sport_key,
                    proximity_threshold=proximity_threshold
                )

                # Flatten the proximities for this sport
                for player_id, proximities in sport_proximities.items():
                    proximities_list.extend(proximities)

            logger.info(f"Found {len(proximities_list)} milestone alerts for players with games today")
        else:
            logger.info("No games today - skipping milestone checks")

        # Check for PR breakthroughs
        logger.info("Checking for PR breakthroughs...")
        pr_breakthroughs = []

        try:
            from src.pr_tracker import PRTracker
            from src.website_fetcher.tfrr_fetcher import TFRRFetcher

            # Initialize PR tracker
            tfrr_fetcher = TFRRFetcher()
            pr_tracker = PRTracker(tfrr_fetcher)

            # Check for yesterday's PR breakthroughs
            pr_breakthroughs = pr_tracker.check_yesterday_breakthroughs()

            if pr_breakthroughs:
                logger.info(f"Found {len(pr_breakthroughs)} PR breakthroughs")
            else:
                logger.info("No PR breakthroughs detected")

        except Exception as e:
            logger.error(f"Error checking PR breakthroughs: {e}")
            # Continue even if PR checking fails

        # Send notification if there are games OR proximities OR PR breakthroughs
        if games_today or proximities_list or pr_breakthroughs:
            logger.info("Sending notification email...")
            success = notifier.send_milestone_alert(
                proximities=proximities_list,
                games=games_today,
                date_for=today,
                pr_breakthroughs=pr_breakthroughs
            )

            if success:
                logger.info("Notification sent successfully")
            else:
                logger.error("Failed to send notification")
        else:
            logger.info("No games, milestone alerts, or PR breakthroughs today - skipping notification")

        logger.info("StatsTracker completed successfully")

    except Exception as e:
        logger.error(f"Error in main execution: {e}", exc_info=True)
        sys.exit(1)


def update_stats(auto_mode: bool = False):
    """
    Update stats from NCAA websites.

    This can be run independently to fetch and update player statistics
    without sending notifications.

    Args:
        auto_mode: If True, called from main() - use quieter logging
    """
    config = load_config()

    log_config = config.get('logging', {})
    if not auto_mode:
        setup_logging(
            log_level=log_config.get('level', 'INFO'),
            log_file=log_config.get('file')
        )

    logger = logging.getLogger(__name__)

    if not auto_mode:
        logger.info("=" * 60)
        logger.info("Update Player Database from NCAA Stats")
        logger.info("=" * 60)
    else:
        logger.info("Updating player statistics from NCAA...")

    try:
        # Initialize database
        db_config = config.get('database', {})
        database = PlayerDatabase(db_path=db_config.get('path', 'data/stats.db'))

        # Initialize NCAA fetcher
        fetcher_config = config.get('fetchers', {})
        ncaa_config = fetcher_config.get('ncaa', {})
        ncaa_fetcher = NCAAFetcher(
            base_url=ncaa_config.get('base_url', 'https://stats.ncaa.org'),
            timeout=ncaa_config.get('timeout', 30)
        )

        # Get NCAA teams from config
        ncaa_teams = ncaa_config.get('haverford_teams', {})
        if not ncaa_teams:
            logger.error("No NCAA teams configured in config file")
            return

        # Determine current season (e.g., "2025-26")
        today = date.today()
        if today.month >= 8:  # August or later
            season = f"{today.year}-{str(today.year + 1)[-2:]}"
        else:
            season = f"{today.year - 1}-{str(today.year)[-2:]}"

        logger.info(f"Season: {season}")
        logger.info(f"Processing {len(ncaa_teams)} NCAA teams")

        # Track results
        total_results = {
            'teams_processed': 0,
            'teams_skipped': 0,
            'teams_failed': 0,
            'players_added': 0,
            'players_updated': 0,
            'stats_added': 0
        }

        # Process each NCAA team
        for sport_key, team_id in ncaa_teams.items():
            result = update_team_stats(
                ncaa_fetcher,
                database,
                sport_key,
                str(team_id),
                season,
                logger
            )

            if result.get('skipped'):
                total_results['teams_skipped'] += 1
            elif result.get('error'):
                total_results['teams_failed'] += 1
            else:
                total_results['teams_processed'] += 1
                total_results['players_added'] += result.get('players_added', 0)
                total_results['players_updated'] += result.get('players_updated', 0)
                total_results['stats_added'] += result.get('stats_added', 0)

        # Process Cricket
        # DISABLED: Cricket fetcher takes too long (2-3 minutes) and causes workflow delays
        # To re-enable, uncomment this section
        # cricket_config = fetcher_config.get('cricket', {})
        # if cricket_config:
        #     logger.info("")
        #     logger.info("Fetching Cricket stats...")
        #     cricket_result = update_cricket_stats(
        #         database,
        #         cricket_config,
        #         season,
        #         logger
        #     )
        #
        #     if not cricket_result.get('error'):
        #         total_results['teams_processed'] += 1
        #         total_results['players_added'] += cricket_result.get('players_added', 0)
        #         total_results['players_updated'] += cricket_result.get('players_updated', 0)
        #         total_results['stats_added'] += cricket_result.get('stats_added', 0)
        #     else:
        #         total_results['teams_failed'] += 1

        # Final summary
        if not auto_mode:
            logger.info("")
            logger.info("=" * 60)
            logger.info("SUMMARY")
            logger.info("=" * 60)

        logger.info(f"Teams processed: {total_results['teams_processed']}")
        logger.info(f"Teams skipped (no stats): {total_results['teams_skipped']}")
        logger.info(f"Teams failed: {total_results['teams_failed']}")
        logger.info(f"Players added: {total_results['players_added']}")
        logger.info(f"Players updated: {total_results['players_updated']}")
        logger.info(f"Stats added: {total_results['stats_added']}")

        if not auto_mode:
            logger.info("=" * 60)
            logger.info("Database update complete")
            logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Error updating stats: {e}", exc_info=True)
        if not auto_mode:
            sys.exit(1)
        else:
            raise


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="StatsTracker - Haverford Sports Statistics Tracker")
    parser.add_argument(
        '--update-stats',
        action='store_true',
        help='Update player statistics from websites (no notifications)'
    )
    parser.add_argument(
        '--test-email',
        action='store_true',
        help='Send a test email to verify configuration'
    )
    parser.add_argument(
        '--config',
        default='config/config.yaml',
        help='Path to configuration file (default: config/config.yaml)'
    )

    args = parser.parse_args()

    if args.test_email:
        # Test email functionality
        config = load_config(args.config)
        setup_logging(log_level='INFO')

        email_config = config.get('email', {})
        notifier = EmailNotifier(email_config)

        if notifier.validate_config():
            print("Email configuration is valid")
            print("Sending test email...")
            if notifier.send_test_email():
                print("Test email sent successfully!")
            else:
                print("Failed to send test email")
        else:
            print("Email configuration is invalid")

    elif args.update_stats:
        # Update stats only
        update_stats()

    else:
        # Normal operation - check and notify
        main()
