#!/usr/bin/env python3
"""
StatsTracker Web Interface

A Flask web application to:
1. Browse and view CSV files (NCAA and TFRR stats)
2. Manually trigger stats updates (re-fetch NCAA data)
3. Simulate gameday checker for any date
4. Preview and send email notifications
"""

import sys
import os
import csv
from pathlib import Path
from datetime import datetime, date
from flask import Flask, render_template, request, jsonify, send_file, Response
import logging
import json
import time
from queue import Queue
from threading import Thread
import yaml

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.gameday_checker import GamedayChecker
from src.website_fetcher import NCAAFetcher, TFRRFetcher
from src.website_fetcher.tfrr_fetcher import HAVERFORD_TEAMS as TFRR_TEAMS
from src.player_database import PlayerDatabase, Player, StatEntry
from src.milestone_detector import MilestoneDetector
from src.email_notifier import EmailNotifier, EmailTemplate
from main import update_stats, load_config, update_team_stats, generate_player_id
import pandas as pd
import hashlib

app = Flask(__name__)
app.config['SECRET_KEY'] = 'haverford-stats-tracker-2026'

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
CSV_EXPORTS_DIR = PROJECT_ROOT / 'csv_exports'
CONFIG_PATH = PROJECT_ROOT / 'config' / 'config.yaml'

# Progress tracking
progress_queues = {}  # session_id -> Queue

def create_progress_stream(session_id):
    """Create a new progress queue for a session."""
    progress_queues[session_id] = Queue()
    return progress_queues[session_id]

def send_progress(session_id, message):
    """Send progress update to a specific session."""
    if session_id in progress_queues:
        progress_queues[session_id].put(message)

def close_progress_stream(session_id):
    """Close and cleanup a progress stream."""
    if session_id in progress_queues:
        progress_queues[session_id].put(None)  # Signal end
        del progress_queues[session_id]


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


@app.route('/')
def index():
    """Home page with navigation."""
    return render_template('index.html')


@app.route('/csv-browser')
def csv_browser():
    """Browse all teams/sports from database."""
    try:
        config = load_config(str(CONFIG_PATH))
        db_config = config.get('database', {})
        database = PlayerDatabase(db_path=str(PROJECT_ROOT / db_config.get('path', 'data/stats.db')))

        # Get all players and organize by sport
        players = database.get_all_players()
        sports_data = {}

        for player in players:
            sport = player.sport
            if sport not in sports_data:
                sports_data[sport] = {
                    'name': sport.replace('_', ' ').title(),
                    'sport_key': sport,
                    'player_count': 0,
                    'last_updated': None
                }
            sports_data[sport]['player_count'] += 1

            # Get most recent stat for this player to determine last update
            player_stats = database.get_player_stats(player.player_id)
            if player_stats and player_stats.recent_entries:
                latest_stat = max(player_stats.recent_entries, key=lambda s: s.date_recorded)
                if not sports_data[sport]['last_updated'] or latest_stat.date_recorded > sports_data[sport]['last_updated']:
                    sports_data[sport]['last_updated'] = latest_stat.date_recorded

        # Convert to sorted list
        sports_list = sorted(sports_data.values(), key=lambda x: x['name'])

        return render_template('csv_browser.html', sports=sports_list, total_players=len(players))

    except Exception as e:
        logger.error(f"Error loading sports from database: {e}")
        return render_template('csv_browser.html', sports=[], error=str(e), total_players=0)


@app.route('/api/search-players')
def api_search_players():
    """API endpoint to search for players across all sports."""
    try:
        query = request.args.get('q', '').strip().lower()
        if not query:
            return jsonify({'results': []})

        config = load_config(str(CONFIG_PATH))
        db_config = config.get('database', {})
        database = PlayerDatabase(db_path=str(PROJECT_ROOT / db_config.get('path', 'data/stats.db')))

        # Get all players
        all_players = database.get_all_players()

        # Filter players by name matching query
        matching_players = []
        for player in all_players:
            if query in player.name.lower():
                # Get player stats to show recent data
                player_stats = database.get_player_stats(player.player_id)
                last_updated = None
                if player_stats and player_stats.recent_entries:
                    latest_stat = max(player_stats.recent_entries, key=lambda s: s.date_recorded)
                    last_updated = latest_stat.date_recorded.strftime('%Y-%m-%d %H:%M')

                matching_players.append({
                    'name': player.name,
                    'sport': player.sport.replace('_', ' ').title(),
                    'sport_key': player.sport,
                    'last_updated': last_updated
                })

        # Sort by name
        matching_players.sort(key=lambda x: x['name'])

        return jsonify({
            'results': matching_players,
            'count': len(matching_players)
        })

    except Exception as e:
        logger.error(f"Error searching players: {e}")
        return jsonify({'error': str(e), 'results': []}), 500


@app.route('/settings')
def settings():
    """Display and edit configuration settings."""
    try:
        # Load current config
        with open(CONFIG_PATH, 'r') as f:
            config = yaml.safe_load(f)

        # Get available stats from database for each sport
        db_config = config.get('database', {})
        database = PlayerDatabase(db_path=str(PROJECT_ROOT / db_config.get('path', 'data/stats.db')))

        available_stats_by_sport = {}
        all_players = database.get_all_players()

        for player in all_players:
            sport = player.sport
            if sport not in available_stats_by_sport:
                available_stats_by_sport[sport] = set()

            # Get player stats to find all stat names
            player_stats = database.get_player_stats(player.player_id)
            if player_stats and player_stats.career_stats:
                for stat_name in player_stats.career_stats.keys():
                    available_stats_by_sport[sport].add(stat_name)

        # Convert sets to sorted lists
        for sport in available_stats_by_sport:
            available_stats_by_sport[sport] = sorted(list(available_stats_by_sport[sport]))

        return render_template('settings.html', config=config, available_stats=available_stats_by_sport)

    except Exception as e:
        logger.error(f"Error loading settings: {e}")
        return render_template('settings.html', config={}, error=str(e), available_stats={})


@app.route('/api/save-settings', methods=['POST'])
def api_save_settings():
    """API endpoint to save configuration settings."""
    try:
        data = request.get_json()

        # Load current config
        with open(CONFIG_PATH, 'r') as f:
            config = yaml.safe_load(f)

        # Update email settings
        if 'email' in data:
            config['email'] = config.get('email', {})
            if 'recipients' in data['email']:
                # Convert comma-separated string to list
                recipients_str = data['email']['recipients']
                config['email']['recipients'] = [r.strip() for r in recipients_str.split(',') if r.strip()]
            if 'smtp_server' in data['email']:
                config['email']['smtp_server'] = data['email']['smtp_server']
            if 'smtp_port' in data['email']:
                config['email']['smtp_port'] = int(data['email']['smtp_port'])
            if 'sender_email' in data['email']:
                config['email']['sender_email'] = data['email']['sender_email']

        # Update notification settings
        if 'notifications' in data:
            config['notifications'] = config.get('notifications', {})
            if 'enabled' in data['notifications']:
                config['notifications']['enabled'] = data['notifications']['enabled']
            if 'proximity_threshold' in data['notifications']:
                config['notifications']['proximity_threshold'] = int(data['notifications']['proximity_threshold'])

        # Update gameday settings
        if 'gameday' in data:
            config['gameday'] = config.get('gameday', {})
            if 'check_days_ahead' in data['gameday']:
                config['gameday']['check_days_ahead'] = int(data['gameday']['check_days_ahead'])

        # Update milestone settings
        if 'milestones' in data:
            config['milestones'] = {}
            for sport, stats in data['milestones'].items():
                config['milestones'][sport] = {}
                for stat_name, thresholds in stats.items():
                    # Convert string of comma-separated values to list of integers
                    if isinstance(thresholds, str):
                        threshold_list = [int(t.strip()) for t in thresholds.split(',') if t.strip()]
                        config['milestones'][sport][stat_name] = sorted(threshold_list)
                    elif isinstance(thresholds, list):
                        config['milestones'][sport][stat_name] = sorted([int(t) for t in thresholds])

        # Update milestone proximity thresholds (per-sport, per-stat)
        if 'milestone_proximity' in data:
            config['milestone_proximity'] = {}
            for sport, stats in data['milestone_proximity'].items():
                config['milestone_proximity'][sport] = {}
                for stat_name, proximity in stats.items():
                    config['milestone_proximity'][sport][stat_name] = int(proximity)

        # Save back to file
        with open(CONFIG_PATH, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)

        return jsonify({
            'success': True,
            'message': 'Settings saved successfully'
        })

    except Exception as e:
        logger.error(f"Error saving settings: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/view-sport/<sport_key>')
def view_sport(sport_key):
    """View stats for a specific sport from database."""
    try:
        config = load_config(str(CONFIG_PATH))
        db_config = config.get('database', {})
        database = PlayerDatabase(db_path=str(PROJECT_ROOT / db_config.get('path', 'data/stats.db')))

        # Get all players for this sport
        players = [p for p in database.get_all_players() if p.sport == sport_key]

        if not players:
            return jsonify({'error': 'No players found for this sport'}), 404

        # Build table data with seasons
        all_stat_names = set()
        player_seasons = []

        for player in players:
            # Get all stats for this player
            player_stats = database.get_player_stats(player.player_id)
            if not player_stats:
                continue

            # Add a row for each season
            for season, season_stats in sorted(player_stats.season_stats.items()):
                # Collect all stat names
                for stat_name in season_stats.keys():
                    all_stat_names.add(stat_name)

                # Add season row
                player_seasons.append({
                    'player_name': player.name,
                    'season': season,
                    'stats': season_stats,
                    'is_career': season == 'Career'
                })

        # Create headers - Player Name, Season, then all stats
        headers = ['Player Name', 'Season'] + sorted(all_stat_names)
        rows = []

        for entry in player_seasons:
            row = {
                'Player Name': entry['player_name'],
                'Season': entry['season']
            }
            # Add stats
            for stat_name in all_stat_names:
                row[stat_name] = entry['stats'].get(stat_name, '-')
            rows.append(row)

        sport_display = sport_key.replace('_', ' ').title()
        return render_template('csv_viewer.html',
                             filename=f"{sport_display} Stats",
                             headers=headers,
                             rows=rows)

    except Exception as e:
        logger.error(f"Error loading sport data: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/demo')
def demo():
    """Demo page with testing buttons."""
    return render_template('demo.html')


@app.route('/api/progress/<session_id>')
def progress_stream(session_id):
    """SSE endpoint for progress updates with keep-alive."""
    def generate():
        q = create_progress_stream(session_id)
        logger.info(f"SSE stream started for session {session_id}")
        try:
            while True:
                try:
                    # Use timeout to send keep-alive comments
                    message = q.get(timeout=10)  # 10 second timeout
                    if message is None:  # End signal
                        logger.info(f"SSE stream ending for session {session_id}")
                        break
                    logger.debug(f"SSE sending: {message}")
                    yield f"data: {json.dumps(message)}\n\n"
                except:
                    # Send keep-alive comment to prevent timeout
                    logger.debug(f"SSE keep-alive for session {session_id}")
                    yield ": keep-alive\n\n"
        except GeneratorExit:
            logger.info(f"SSE stream closed by client for session {session_id}")
            close_progress_stream(session_id)
        except Exception as e:
            logger.error(f"SSE stream error for session {session_id}: {e}")
            close_progress_stream(session_id)

    response = Response(generate(), mimetype='text/event-stream')
    response.headers['Cache-Control'] = 'no-cache'
    response.headers['X-Accel-Buffering'] = 'no'
    response.headers['Connection'] = 'keep-alive'
    return response


@app.route('/api/update-stats', methods=['POST'])
def api_update_stats():
    """API endpoint to trigger stats update with real-time progress."""
    try:
        data = request.get_json() or {}
        session_id = data.get('session_id')

        if not session_id:
            return jsonify({'error': 'session_id is required'}), 400

        logger.info(f"Manual stats update triggered via web interface (session: {session_id})")

        def run_update_with_progress():
            try:
                logger.info(f"[{session_id}] Background thread started")
                # Send initial message
                send_progress(session_id, {'type': 'info', 'message': 'Starting stats update...'})

                # Load config
                config = load_config(str(CONFIG_PATH))
                fetcher_config = config.get('fetchers', {})
                db_config = config.get('database', {})
                database = PlayerDatabase(db_path=str(PROJECT_ROOT / db_config.get('path', 'data/stats.db')))
                season = "2024-25"
                logger.info(f"[{session_id}] Database initialized")

                # Update NCAA stats with progress
                send_progress(session_id, {'type': 'info', 'message': 'Starting NCAA stats update...'})
                ncaa_config = fetcher_config.get('ncaa', {})
                logger.info(f"[{session_id}] NCAA config loaded: {bool(ncaa_config)}")
                if ncaa_config:
                    from src.website_fetcher.ncaa_fetcher import NCAAFetcher
                    import csv
                    ncaa_fetcher = NCAAFetcher(
                        base_url=ncaa_config.get('base_url'),
                        timeout=ncaa_config.get('timeout', 30)
                    )
                    haverford_teams = ncaa_config.get('haverford_teams', {})
                    csv_exports_successful = 0
                    logger.info(f"[{session_id}] Starting NCAA fetch for {len(haverford_teams)} teams")
                    for sport, team_id in haverford_teams.items():
                        logger.info(f"[{session_id}] Fetching {sport}")
                        send_progress(session_id, {'type': 'fetch', 'message': f'Fetching {sport.replace("_", " ").title()} roster...'})
                        try:
                            # First, get roster with player IDs
                            roster_result = ncaa_fetcher.fetch_team_roster_with_ids(str(team_id), sport)

                            if not roster_result.success or not roster_result.data:
                                logger.warning(f"[{session_id}] Failed to fetch roster for {sport}: {roster_result.error}")
                                send_progress(session_id, {'type': 'warning', 'message': f'Could not fetch roster for {sport.replace("_", " ").title()}'})
                                continue

                            roster = roster_result.data.get('players', [])
                            logger.info(f"[{session_id}] Found {len(roster)} players on {sport} roster")
                            send_progress(session_id, {'type': 'info', 'message': f'Fetching career stats for {len(roster)} {sport.replace("_", " ").title()} players...'})

                            players_added = 0
                            stats_added = 0

                            # Fetch career stats for each player
                            for idx, player_info in enumerate(roster):
                                player_name = player_info.get('name')
                                player_ncaa_id = player_info.get('player_id')

                                if not player_name or not player_ncaa_id:
                                    continue

                                # Send progress every 5 players
                                if idx % 5 == 0:
                                    send_progress(session_id, {'type': 'fetch', 'message': f'Fetching {sport.replace("_", " ").title()} player {idx+1}/{len(roster)}...'})

                                # Generate our internal player ID
                                player_id = generate_player_id(player_name, sport)

                                # Fetch career stats for this player
                                career_result = ncaa_fetcher.fetch_player_career_stats(player_ncaa_id, sport, "Haverford")

                                if not career_result.success or not career_result.data:
                                    logger.warning(f"[{session_id}] Failed to fetch career stats for {player_name}")
                                    continue

                                career_data = career_result.data
                                seasons_data = career_data.get('seasons', [])

                                # Check if player exists, add if not
                                existing_player = database.get_player(player_id)
                                if not existing_player:
                                    player = Player(
                                        player_id=player_id,
                                        name=player_name,
                                        sport=sport,
                                        team='Haverford',
                                        position=None,
                                        year=None,
                                        active=True
                                    )
                                    database.add_player(player)
                                    players_added += 1

                                # Add stats for each season
                                for season_data in seasons_data:
                                    season_year = season_data.get('year', 'Unknown')
                                    season_stats = season_data.get('stats', {})

                                    for stat_name, stat_value in season_stats.items():
                                        if stat_value and stat_value != '':
                                            stat_entry = StatEntry(
                                                player_id=player_id,
                                                stat_name=stat_name,
                                                stat_value=str(stat_value),
                                                season=season_year,
                                                date_recorded=datetime.now()
                                            )
                                            database.add_stat(stat_entry)
                                            stats_added += 1

                            logger.info(f"[{session_id}] Updated {sport}: {players_added} players, {stats_added} stats")

                            # Also fetch and export to CSV
                            send_progress(session_id, {'type': 'fetch', 'message': f'Exporting {sport.replace("_", " ").title()} to CSV...'})
                            result = ncaa_fetcher.fetch_team_stats(str(team_id), sport)

                            if result.success and result.data:
                                # Save to CSV
                                sport_display = sport.replace('_', ' ').title()
                                safe_sport_name = sport.replace(' ', '_').lower()
                                timestamp = datetime.now().strftime('%Y%m%d')
                                filename = f"haverford_{safe_sport_name}_{timestamp}.csv"
                                filepath = CSV_EXPORTS_DIR / filename

                                with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                                    headers = ['Player Name'] + result.data['stat_categories']
                                    writer = csv.DictWriter(csvfile, fieldnames=headers)
                                    writer.writeheader()

                                    for player in result.data['players']:
                                        row = {'Player Name': player['name']}
                                        row.update(player['stats'])
                                        writer.writerow(row)

                                csv_exports_successful += 1
                        except Exception as e:
                            send_progress(session_id, {'type': 'warning', 'message': f'Error fetching {sport}: {str(e)}'})

                # Update Cricket stats with progress
                # DISABLED: Cricket fetcher takes too long (2-3 minutes) causing SSE timeouts
                # To re-enable, uncomment this section
                # send_progress(session_id, {'type': 'info', 'message': 'Starting Cricket stats update...'})
                # cricket_config = fetcher_config.get('cricket', {})
                # if cricket_config:
                #     try:
                #         from src.website_fetcher.cricket_fetcher import CricketFetcher
                #         cricket_fetcher = CricketFetcher(
                #             timeout=cricket_config.get('timeout', 30),
                #             headless=cricket_config.get('headless', True)
                #         )
                #         send_progress(session_id, {'type': 'fetch', 'message': 'Fetching cricket stats from cricclubs.com (this may take 2-3 minutes)...'})
                #         result = cricket_fetcher.fetch_all_stats()
                #
                #         if result['success'] and result['data'] is not None:
                #             df = result['data']
                #             send_progress(session_id, {'type': 'info', 'message': f'Cricket fetch complete! Processing {len(df)} players...'})
                #
                #             for idx, row in enumerate(df.iterrows()):
                #                 _, row_data = row
                #                 player_name = row_data.get('Player', 'Unknown')
                #
                #                 # Send progress every 5 players to avoid too many messages
                #                 if idx % 5 == 0 or idx == len(df) - 1:
                #                     send_progress(session_id, {'type': 'fetch', 'message': f'Processing cricket player {idx+1}/{len(df)}: {player_name}'})
                #
                #                 # Generate player ID
                #                 player_id = generate_player_id(player_name, 'cricket')
                #
                #                 # Check if player exists, add if not
                #                 existing_player = database.get_player(player_id)
                #                 if not existing_player:
                #                     player = Player(
                #                         player_id=player_id,
                #                         name=player_name,
                #                         sport='cricket',
                #                         team='Haverford',
                #                         position=None,
                #                         year=None,
                #                         active=True
                #                     )
                #                     database.add_player(player)
                #
                #                 # Add stats for all columns except Player name
                #                 for col in df.columns:
                #                     if col == 'Player':
                #                         continue
                #
                #                     stat_value = row_data[col]
                #
                #                     # Skip empty or null values
                #                     if pd.isna(stat_value) or stat_value == '' or stat_value == 0:
                #                         continue
                #
                #                     stat_entry = StatEntry(
                #                         player_id=player_id,
                #                         stat_name=col,
                #                         stat_value=str(stat_value),
                #                         season=season,
                #                         date_recorded=datetime.now()
                #                     )
                #                     database.add_stat(stat_entry)
                #
                #             send_progress(session_id, {'type': 'info', 'message': f'Cricket stats completed: {len(df)} players processed'})
                #         else:
                #             send_progress(session_id, {'type': 'warning', 'message': f'Cricket fetch failed: {result.get("error", "Unknown error")}'})
                #
                #     except Exception as e:
                #         send_progress(session_id, {'type': 'warning', 'message': f'Error updating cricket stats: {str(e)}'})

                # Update TFRR stats with progress
                send_progress(session_id, {'type': 'info', 'message': 'Starting TFRR stats update...'})
                tfrr_fetcher = TFRRFetcher()
                tfrr_athletes_added = 0
                tfrr_stats_added = 0

                for sport_key, team_code in TFRR_TEAMS.items():
                    sport_display = sport_key.replace('_', ' ').title()
                    send_progress(session_id, {'type': 'fetch', 'message': f'Fetching TFRR {sport_display}...'})
                    try:
                        # Determine sport type
                        sport_type = "cross_country" if "cross_country" in sport_key else "track"

                        # Fetch team roster and PRs
                        result = tfrr_fetcher.fetch_team_stats(team_code, sport_type)

                        if result.success and result.data:
                            roster = result.data.get('roster', [])
                            logger.info(f"[{session_id}] Fetched {len(roster)} athletes for {sport_key}")

                            # Process each athlete
                            for idx, athlete in enumerate(roster):
                                athlete_name = athlete.get('name')
                                athlete_id_tfrr = athlete.get('athlete_id')

                                if not athlete_name or not athlete_id_tfrr:
                                    continue

                                # Send progress every 10 athletes
                                if idx % 10 == 0:
                                    send_progress(session_id, {'type': 'fetch', 'message': f'Fetching PRs for {sport_display} athlete {idx+1}/{len(roster)}...'})

                                # Generate player ID
                                player_id = generate_player_id(athlete_name, sport_key)

                                # Check if player exists
                                existing_player = database.get_player(player_id)
                                if not existing_player:
                                    player = Player(
                                        player_id=player_id,
                                        name=athlete_name,
                                        sport=sport_key,
                                        team='Haverford',
                                        position=None,
                                        year=athlete.get('year'),
                                        active=True
                                    )
                                    database.add_player(player)
                                    tfrr_athletes_added += 1

                                # Fetch athlete's PRs (Personal Records)
                                try:
                                    athlete_result = tfrr_fetcher.fetch_player_stats(athlete_id_tfrr, sport_type)

                                    if athlete_result.success and athlete_result.data:
                                        prs = athlete_result.data.get('personal_records', {})

                                        # Store each PR as a separate stat
                                        for event_name, pr_value in prs.items():
                                            if pr_value:
                                                stat_entry = StatEntry(
                                                    player_id=player_id,
                                                    stat_name=event_name,
                                                    stat_value=str(pr_value),
                                                    season=season,
                                                    date_recorded=datetime.now()
                                                )
                                                database.add_stat(stat_entry)
                                                tfrr_stats_added += 1

                                        logger.debug(f"[{session_id}] Fetched {len(prs)} PRs for {athlete_name}")
                                    else:
                                        logger.warning(f"[{session_id}] No PRs found for {athlete_name}")

                                except Exception as e:
                                    logger.warning(f"[{session_id}] Error fetching PRs for {athlete_name}: {e}")
                                    continue

                            logger.info(f"[{session_id}] Updated {sport_key}: {tfrr_athletes_added} athletes, {tfrr_stats_added} stats")
                        else:
                            send_progress(session_id, {'type': 'warning', 'message': f'Error fetching {sport_display}: {result.error}'})

                    except Exception as e:
                        logger.error(f"[{session_id}] Error fetching {sport_key}: {e}")
                        send_progress(session_id, {'type': 'warning', 'message': f'Error fetching {sport_display}: {str(e)}'})

                # Final success message
                if csv_exports_successful > 0:
                    send_progress(session_id, {'type': 'success', 'message': f'All stats updated successfully! Exported {csv_exports_successful} CSVs.'})
                else:
                    send_progress(session_id, {'type': 'success', 'message': 'All stats updated successfully!'})
                close_progress_stream(session_id)

            except Exception as e:
                logger.error(f"Stats update error in background thread: {e}", exc_info=True)
                send_progress(session_id, {'type': 'error', 'message': f'Error: {str(e)}'})
                close_progress_stream(session_id)

        # Run in background thread
        thread = Thread(target=run_update_with_progress)
        thread.daemon = True
        thread.start()

        return jsonify({
            'success': True,
            'message': 'Stats update started',
            'session_id': session_id
        })

    except Exception as e:
        logger.error(f"Stats update failed: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/update-cricket-stats', methods=['POST'])
def api_update_cricket_stats():
    """API endpoint to fetch cricket stats and export to CSV."""
    try:
        logger.info("Fetching cricket stats via API...")

        from src.website_fetcher.cricket_fetcher import CricketFetcher

        # Initialize cricket fetcher
        fetcher = CricketFetcher(timeout=30, headless=True)

        # Export to CSV (this also fetches the stats)
        output_path = str(CSV_EXPORTS_DIR / "haverford_cricket_stats.csv")
        success = fetcher.export_to_csv(output_path)

        if success:
            logger.info(f"Cricket stats exported to {output_path}")
            return jsonify({
                'success': True,
                'message': 'Cricket stats updated successfully',
                'csv_path': output_path,
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to export cricket stats'
            }), 500

    except Exception as e:
        logger.error(f"Cricket stats update failed: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/simulate-gameday', methods=['POST'])
def api_simulate_gameday():
    """API endpoint to simulate gameday checker for a specific date."""
    try:
        data = request.get_json()
        date_str = data.get('date')

        if not date_str:
            return jsonify({'error': 'Date is required'}), 400

        # Parse date
        check_date = datetime.strptime(date_str, '%Y-%m-%d').date()

        logger.info(f"Simulating gameday checker for {check_date}")

        # Load config
        config = load_config(str(CONFIG_PATH))

        # Initialize modules
        gameday_config = config.get('gameday', {})
        schedule_url = gameday_config.get('haverford_schedule_url', 'https://haverfordathletics.com/calendar')
        gameday_checker = GamedayChecker(schedule_url=schedule_url)
        database = PlayerDatabase(db_path=str(PROJECT_ROOT / 'data' / 'stats.db'))
        milestone_config = config.get('milestones', {})
        milestone_detector = MilestoneDetector(database, milestone_config)
        email_config = config.get('email', {})
        notifier = EmailNotifier(email_config)

        # Get games for the specified date
        games = gameday_checker.get_games_for_date(check_date)
        logger.info(f"Found {len(games)} games on {check_date}")

        # Extract sports with games
        sports_with_games = set()
        if games:
            for game in games:
                sport_key = game.team.sport.lower().replace(' ', '_').replace("'", '')
                sports_with_games.add(sport_key)

        # Check milestones for players on teams with games
        proximity_threshold = config.get('notifications', {}).get('proximity_threshold', 10)
        proximities_list = []

        if sports_with_games:
            for sport_key in sports_with_games:
                sport_proximities = milestone_detector.check_all_players_milestones(
                    sport=sport_key,
                    proximity_threshold=proximity_threshold
                )

                for player_id, proximities in sport_proximities.items():
                    proximities_list.extend(proximities)

        # Generate email preview (don't send)
        has_milestones = len(proximities_list) > 0
        subject = EmailTemplate.generate_subject(check_date, len(games), has_milestones)
        html_body = EmailTemplate.generate_milestone_email(proximities_list, games, check_date)

        # Convert games to dict for JSON serialization
        games_data = []
        for game in games:
            games_data.append({
                'sport': game.team.sport,
                'team': game.team.name,
                'opponent': game.opponent,
                'location': 'Home' if game.is_home_game else 'Away',
                'time': game.time or 'TBD',
                'date': game.date.isoformat() if game.date else None
            })

        # Convert proximities to dict
        proximities_data = []
        for prox in proximities_list:
            # Format numbers properly (remove .0 for whole numbers)
            current = int(prox.current_value) if isinstance(prox.current_value, (int, float)) and prox.current_value == int(prox.current_value) else prox.current_value
            target = int(prox.milestone.threshold) if isinstance(prox.milestone.threshold, (int, float)) and prox.milestone.threshold == int(prox.milestone.threshold) else prox.milestone.threshold
            remaining = int(prox.distance) if isinstance(prox.distance, (int, float)) and prox.distance == int(prox.distance) else prox.distance

            proximities_data.append({
                'player_name': prox.player_name,
                'milestone': prox.milestone.description,
                'current': str(current),
                'target': str(target),
                'remaining': str(remaining),
                'percentage': f"{prox.percentage:.1f}%"
            })

        return jsonify({
            'success': True,
            'date': date_str,
            'games': games_data,
            'games_count': len(games),
            'proximities': proximities_data,
            'proximities_count': len(proximities_list),
            'sports_with_games': list(sports_with_games),
            'email_subject': subject,
            'email_html': html_body
        })

    except Exception as e:
        logger.error(f"Gameday simulation failed: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/send-test-email', methods=['POST'])
def api_send_test_email():
    """API endpoint to send test email with simulated data."""
    try:
        data = request.get_json()
        date_str = data.get('date')

        if not date_str:
            return jsonify({'error': 'Date is required'}), 400

        check_date = datetime.strptime(date_str, '%Y-%m-%d').date()

        # Load config and initialize notifier
        config = load_config(str(CONFIG_PATH))
        email_config = config.get('email', {})
        notifier = EmailNotifier(email_config)

        # Run simulation to get games and milestones
        gameday_config = config.get('gameday', {})
        schedule_url = gameday_config.get('haverford_schedule_url', 'https://haverfordathletics.com/calendar')
        gameday_checker = GamedayChecker(schedule_url=schedule_url)
        database = PlayerDatabase(db_path=str(PROJECT_ROOT / 'data' / 'stats.db'))
        milestone_config = config.get('milestones', {})
        milestone_detector = MilestoneDetector(database, milestone_config)

        games = gameday_checker.get_games_for_date(check_date)

        sports_with_games = set()
        if games:
            for game in games:
                sport_key = game.team.sport.lower().replace(' ', '_').replace("'", '')
                sports_with_games.add(sport_key)

        proximity_threshold = config.get('notifications', {}).get('proximity_threshold', 10)
        proximities_list = []

        if sports_with_games:
            for sport_key in sports_with_games:
                sport_proximities = milestone_detector.check_all_players_milestones(
                    sport=sport_key,
                    proximity_threshold=proximity_threshold
                )
                for player_id, proximities in sport_proximities.items():
                    proximities_list.extend(proximities)

        # Send actual email
        success = notifier.send_milestone_alert(proximities_list, games, check_date)

        return jsonify({
            'success': success,
            'message': 'Email sent successfully' if success else 'Email send failed',
            'games_count': len(games),
            'proximities_count': len(proximities_list)
        })

    except Exception as e:
        logger.error(f"Test email send failed: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/run-daily-workflow', methods=['POST'])
def api_run_daily_workflow():
    """
    API endpoint to run the complete 8 AM daily workflow with real-time progress.

    This simulates exactly what happens at 8 AM:
    1. Update all stats (NCAA, Cricket, TFRR)
    2. Check for games on the specified date
    3. Check milestones for players on teams with games
    4. Send email notification
    """
    try:
        data = request.get_json()
        date_str = data.get('date')
        session_id = data.get('session_id')

        if not date_str:
            return jsonify({'error': 'Date is required'}), 400

        if not session_id:
            return jsonify({'error': 'session_id is required'}), 400

        check_date = datetime.strptime(date_str, '%Y-%m-%d').date()

        logger.info(f"Starting daily workflow for {check_date} (session: {session_id})")

        def run_workflow_with_progress():
            try:
                # Load config
                config = load_config(str(CONFIG_PATH))
                fetcher_config = config.get('fetchers', {})
                db_config = config.get('database', {})
                database = PlayerDatabase(db_path=str(PROJECT_ROOT / db_config.get('path', 'data/stats.db')))
                season = "2024-25"

                # Step 1: Update All Stats (NCAA, Cricket, TFRR)
                send_progress(session_id, {'type': 'step', 'message': 'Step 1/4: Updating all stats (NCAA, Cricket, TFRR)...'})

                # NCAA Stats
                send_progress(session_id, {'type': 'info', 'message': 'Updating NCAA stats...'})
                ncaa_config = fetcher_config.get('ncaa', {})
                if ncaa_config:
                    from src.website_fetcher.ncaa_fetcher import NCAAFetcher
                    ncaa_fetcher = NCAAFetcher(
                        base_url=ncaa_config.get('base_url'),
                        timeout=ncaa_config.get('timeout', 30)
                    )
                    haverford_teams = ncaa_config.get('haverford_teams', {})
                    for sport, team_id in haverford_teams.items():
                        send_progress(session_id, {'type': 'fetch', 'message': f'Fetching NCAA {sport.replace("_", " ").title()} roster...'})
                        try:
                            # Fetch roster with player IDs
                            roster_result = ncaa_fetcher.fetch_team_roster_with_ids(str(team_id), sport)
                            if not roster_result.success or not roster_result.data:
                                logger.warning(f"Failed to fetch roster for {sport}")
                                continue

                            roster = roster_result.data.get('players', [])
                            send_progress(session_id, {'type': 'info', 'message': f'Fetching career stats for {len(roster)} {sport.replace("_", " ").title()} players...'})

                            # Fetch career stats for each player
                            for idx, player_info in enumerate(roster):
                                player_name = player_info.get('name')
                                player_ncaa_id = player_info.get('player_id')
                                if not player_name or not player_ncaa_id:
                                    continue

                                if idx % 5 == 0:
                                    send_progress(session_id, {'type': 'fetch', 'message': f'Fetching {sport.replace("_", " ").title()} player {idx+1}/{len(roster)}...'})

                                player_id = generate_player_id(player_name, sport)
                                career_result = ncaa_fetcher.fetch_player_career_stats(player_ncaa_id, sport, "Haverford")

                                if not career_result.success or not career_result.data:
                                    continue

                                career_data = career_result.data
                                seasons_data = career_data.get('seasons', [])

                                existing_player = database.get_player(player_id)
                                if not existing_player:
                                    player = Player(
                                        player_id=player_id,
                                        name=player_name,
                                        sport=sport,
                                        team='Haverford',
                                        position=None,
                                        year=None,
                                        active=True
                                    )
                                    database.add_player(player)

                                for season_data in seasons_data:
                                    season_year = season_data.get('year', 'Unknown')
                                    season_stats = season_data.get('stats', {})
                                    for stat_name, stat_value in season_stats.items():
                                        if stat_value and stat_value != '':
                                            stat_entry = StatEntry(
                                                player_id=player_id,
                                                stat_name=stat_name,
                                                stat_value=str(stat_value),
                                                season=season_year,
                                                date_recorded=datetime.now()
                                            )
                                            database.add_stat(stat_entry)
                        except Exception as e:
                            send_progress(session_id, {'type': 'warning', 'message': f'Error fetching {sport}: {str(e)}'})

                # Cricket Stats
                # DISABLED: Cricket fetcher takes too long (2-3 minutes) causing SSE timeouts
                # To re-enable, uncomment this section
                # send_progress(session_id, {'type': 'info', 'message': 'Updating Cricket stats...'})
                # cricket_config = fetcher_config.get('cricket', {})
                # if cricket_config:
                #     try:
                #         from src.website_fetcher.cricket_fetcher import CricketFetcher
                #         cricket_fetcher = CricketFetcher(
                #             timeout=cricket_config.get('timeout', 30),
                #             headless=cricket_config.get('headless', True)
                #         )
                #         send_progress(session_id, {'type': 'fetch', 'message': 'Fetching cricket stats from cricclubs.com (this may take 2-3 minutes)...'})
                #         result = cricket_fetcher.fetch_all_stats()
                #
                #         if result['success'] and result['data'] is not None:
                #             df = result['data']
                #             send_progress(session_id, {'type': 'info', 'message': f'Cricket fetch complete! Processing {len(df)} players...'})
                #
                #             for idx, row in enumerate(df.iterrows()):
                #                 _, row_data = row
                #                 player_name = row_data.get('Player', 'Unknown')
                #
                #                 # Send progress every 5 players to avoid too many messages
                #                 if idx % 5 == 0 or idx == len(df) - 1:
                #                     send_progress(session_id, {'type': 'fetch', 'message': f'Processing cricket player {idx+1}/{len(df)}: {player_name}'})
                #
                #                 # Generate player ID
                #                 player_id = generate_player_id(player_name, 'cricket')
                #
                #                 # Check if player exists, add if not
                #                 existing_player = database.get_player(player_id)
                #                 if not existing_player:
                #                     player = Player(
                #                         player_id=player_id,
                #                         name=player_name,
                #                         sport='cricket',
                #                         team='Haverford',
                #                         position=None,
                #                         year=None,
                #                         active=True
                #                     )
                #                     database.add_player(player)
                #
                #                 # Add stats for all columns except Player name
                #                 for col in df.columns:
                #                     if col == 'Player':
                #                         continue
                #
                #                     stat_value = row_data[col]
                #
                #                     # Skip empty or null values
                #                     if pd.isna(stat_value) or stat_value == '' or stat_value == 0:
                #                         continue
                #
                #                     stat_entry = StatEntry(
                #                         player_id=player_id,
                #                         stat_name=col,
                #                         stat_value=str(stat_value),
                #                         season=season,
                #                         date_recorded=datetime.now()
                #                     )
                #                     database.add_stat(stat_entry)
                #
                #             send_progress(session_id, {'type': 'info', 'message': f'Cricket stats completed: {len(df)} players processed'})
                #         else:
                #             send_progress(session_id, {'type': 'warning', 'message': f'Cricket fetch failed: {result.get("error", "Unknown error")}'})
                #
                #     except Exception as e:
                #         send_progress(session_id, {'type': 'warning', 'message': f'Error updating cricket stats: {str(e)}'})

                # TFRR Stats
                # DISABLED: TFRR fetcher has aggressive rate limiting and takes too long (30+ minutes)
                # To re-enable, uncomment this section
                # send_progress(session_id, {'type': 'info', 'message': 'Updating TFRR stats...'})
                # tfrr_fetcher = TFRRFetcher()
                #
                # for sport_key, team_code in TFRR_TEAMS.items():
                #     sport_display = sport_key.replace('_', ' ').title()
                #     send_progress(session_id, {'type': 'fetch', 'message': f'Fetching TFRR {sport_display}...'})
                #     try:
                #         sport_type = "cross_country" if "cross_country" in sport_key else "track"
                #         result = tfrr_fetcher.fetch_team_stats(team_code, sport_type)
                #
                #         if result.success and result.data:
                #             roster = result.data.get('roster', [])
                #             for idx, athlete in enumerate(roster):
                #                 athlete_name = athlete.get('name')
                #                 athlete_id_tfrr = athlete.get('athlete_id')
                #                 if not athlete_name or not athlete_id_tfrr:
                #                     continue
                #
                #                 # Send progress every 10 athletes
                #                 if idx % 10 == 0:
                #                     send_progress(session_id, {'type': 'fetch', 'message': f'Fetching PRs for {sport_display} athlete {idx+1}/{len(roster)}...'})
                #
                #                 player_id = generate_player_id(athlete_name, sport_key)
                #                 existing_player = database.get_player(player_id)
                #                 if not existing_player:
                #                     player = Player(
                #                         player_id=player_id,
                #                         name=athlete_name,
                #                         sport=sport_key,
                #                         team='Haverford',
                #                         position=None,
                #                         year=athlete.get('year'),
                #                         active=True
                #                     )
                #                     database.add_player(player)
                #
                #                 # Fetch athlete's PRs (Personal Records)
                #                 try:
                #                     athlete_result = tfrr_fetcher.fetch_player_stats(athlete_id_tfrr, sport_type)
                #
                #                     if athlete_result.success and athlete_result.data:
                #                         prs = athlete_result.data.get('personal_records', {})
                #
                #                         # Store each PR as a separate stat
                #                         for event_name, pr_value in prs.items():
                #                             if pr_value:
                #                                 stat_entry = StatEntry(
                #                                     player_id=player_id,
                #                                     stat_name=event_name,
                #                                     stat_value=str(pr_value),
                #                                     season=season,
                #                                     date_recorded=datetime.now()
                #                                 )
                #                                 database.add_stat(stat_entry)
                #                 except Exception as e:
                #                     logger.warning(f"[{session_id}] Error fetching PRs for {athlete_name}: {e}")
                #                     continue
                #         else:
                #             send_progress(session_id, {'type': 'warning', 'message': f'Error fetching {sport_display}: {result.error}'})
                #     except Exception as e:
                #         send_progress(session_id, {'type': 'warning', 'message': f'Error fetching {sport_display}: {str(e)}'})

                # Step 2: Check for games
                send_progress(session_id, {'type': 'step', 'message': f'Step 2/4: Checking for games on {date_str}...'})
                gameday_config = config.get('gameday', {})
                schedule_url = gameday_config.get('haverford_schedule_url', 'https://haverfordathletics.com/calendar')
                gameday_checker = GamedayChecker(schedule_url=schedule_url)
                games = gameday_checker.get_games_for_date(check_date)
                send_progress(session_id, {'type': 'info', 'message': f'Found {len(games)} games scheduled'})

                # Step 3: Check milestones
                send_progress(session_id, {'type': 'step', 'message': 'Step 3/4: Checking milestones for players...'})

                proximities_list = []
                sports_with_games = set()

                if games:
                    for game in games:
                        sport_key = game.team.sport.lower().replace(' ', '_').replace("'", '')
                        sports_with_games.add(sport_key)

                    milestone_config = config.get('milestones', {})
                    milestone_detector = MilestoneDetector(database, milestone_config)
                    proximity_threshold = config.get('notifications', {}).get('proximity_threshold', 10)

                    for sport_key in sports_with_games:
                        send_progress(session_id, {'type': 'info', 'message': f'Checking milestones for {sport_key.replace("_", " ").title()}...'})
                        sport_proximities = milestone_detector.check_all_players_milestones(
                            sport=sport_key,
                            proximity_threshold=proximity_threshold
                        )
                        for player_id, proximities in sport_proximities.items():
                            proximities_list.extend(proximities)

                    send_progress(session_id, {'type': 'info', 'message': f'Found {len(proximities_list)} milestone alerts'})
                else:
                    send_progress(session_id, {'type': 'info', 'message': 'No games today - skipped milestone checks'})

                # Step 4: Send notification email
                send_progress(session_id, {'type': 'step', 'message': 'Step 4/4: Sending notification email...'})

                email_config = config.get('email', {})
                notifier = EmailNotifier(email_config)

                # Always send email (even if no games/milestones)
                send_progress(session_id, {'type': 'info', 'message': 'Preparing email notification...'})
                success = notifier.send_milestone_alert(
                    proximities=proximities_list,
                    games=games,
                    date_for=check_date
                )

                if success:
                    send_progress(session_id, {'type': 'success', 'message': 'Email sent successfully!'})
                else:
                    send_progress(session_id, {'type': 'error', 'message': 'Email send failed'})

                # Final completion message
                send_progress(session_id, {'type': 'complete', 'message': 'Daily workflow complete!'})
                close_progress_stream(session_id)

            except Exception as e:
                logger.error(f"Daily workflow error: {e}", exc_info=True)
                send_progress(session_id, {'type': 'error', 'message': f'Error: {str(e)}'})
                close_progress_stream(session_id)

        # Run in background thread
        thread = Thread(target=run_workflow_with_progress)
        thread.daemon = True
        thread.start()

        return jsonify({
            'success': True,
            'message': 'Daily workflow started',
            'session_id': session_id
        })

    except Exception as e:
        logger.error(f"Daily workflow failed: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/clear-stats', methods=['POST'])
def api_clear_stats():
    """
    API endpoint to clear all stats from the database.

    This will:
    1. Delete the stats database file
    2. A new empty database will be created on next stats update
    """
    try:
        config = load_config(str(CONFIG_PATH))
        db_config = config.get('database', {})
        db_path = PROJECT_ROOT / db_config.get('path', 'data/stats.db')

        # Check if database exists
        if db_path.exists():
            # Get stats before deleting
            database = PlayerDatabase(db_path=str(db_path))
            players = database.get_all_players()
            player_count = len(players)

            # Count by sport
            sports_count = {}
            for player in players:
                sports_count[player.sport] = sports_count.get(player.sport, 0) + 1

            # Delete the database
            db_path.unlink()

            logger.info(f"Cleared stats database: {player_count} players removed")

            return jsonify({
                'success': True,
                'message': f"Successfully cleared stats database ({player_count} players removed)",
                'stats': {
                    'total_players': player_count,
                    'sports': sports_count
                }
            })
        else:
            return jsonify({
                'success': True,
                'message': 'Database already empty or does not exist',
                'stats': {
                    'total_players': 0,
                    'sports': {}
                }
            })

    except Exception as e:
        logger.error(f"Failed to clear stats database: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
