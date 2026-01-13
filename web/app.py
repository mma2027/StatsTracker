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
from flask import Flask, render_template, request, jsonify, send_file
import logging

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.gameday_checker import GamedayChecker
from src.website_fetcher import NCAAFetcher
from src.player_database import PlayerDatabase
from src.milestone_detector import MilestoneDetector
from src.email_notifier import EmailNotifier, EmailTemplate
from main import update_stats, load_config

app = Flask(__name__)
app.config['SECRET_KEY'] = 'haverford-stats-tracker-2026'

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
CSV_EXPORTS_DIR = PROJECT_ROOT / 'csv_exports'
CONFIG_PATH = PROJECT_ROOT / 'config' / 'config.yaml'


@app.route('/')
def index():
    """Home page with navigation."""
    return render_template('index.html')


@app.route('/csv-browser')
def csv_browser():
    """Browse all CSV files organized by source."""
    csv_files = {
        'ncaa': [],
        'tfrr': [],
        'archive': []
    }

    # Scan NCAA directory
    ncaa_dir = CSV_EXPORTS_DIR / 'ncaa'
    if ncaa_dir.exists():
        for csv_file in sorted(ncaa_dir.glob('*.csv'), key=lambda x: x.stat().st_mtime, reverse=True):
            csv_files['ncaa'].append({
                'name': csv_file.name,
                'path': str(csv_file.relative_to(PROJECT_ROOT)),
                'size': csv_file.stat().st_size,
                'modified': datetime.fromtimestamp(csv_file.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')
            })

    # Scan TFRR directory
    tfrr_dir = CSV_EXPORTS_DIR / 'tfrr'
    if tfrr_dir.exists():
        for csv_file in sorted(tfrr_dir.glob('*.csv'), key=lambda x: x.stat().st_mtime, reverse=True):
            csv_files['tfrr'].append({
                'name': csv_file.name,
                'path': str(csv_file.relative_to(PROJECT_ROOT)),
                'size': csv_file.stat().st_size,
                'modified': datetime.fromtimestamp(csv_file.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')
            })

    # Count archive files
    archive_dir = CSV_EXPORTS_DIR / 'archive'
    if archive_dir.exists():
        archive_count = len(list(archive_dir.glob('*.csv')))
        csv_files['archive_count'] = archive_count

    return render_template('csv_browser.html', csv_files=csv_files)


@app.route('/view-csv/<path:filepath>')
def view_csv(filepath):
    """View contents of a specific CSV file."""
    csv_path = PROJECT_ROOT / filepath

    if not csv_path.exists() or not csv_path.is_file():
        return jsonify({'error': 'File not found'}), 404

    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            rows = list(reader)

        return render_template('csv_viewer.html',
                             filename=csv_path.name,
                             headers=headers,
                             rows=rows)

    except Exception as e:
        logger.error(f"Error reading CSV: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/demo')
def demo():
    """Demo page with testing buttons."""
    return render_template('demo.html')


@app.route('/api/update-stats', methods=['POST'])
def api_update_stats():
    """API endpoint to trigger stats update."""
    try:
        logger.info("Manual stats update triggered via web interface")

        # Run update_stats in background
        # For now, run synchronously (can be improved with Celery/background tasks)
        update_stats(auto_mode=False)

        return jsonify({
            'success': True,
            'message': 'Stats updated successfully',
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Stats update failed: {e}")
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
        schedule_url = config.get('gameday', {}).get('haverford_schedule_url', 'https://haverfordathletics.com/calendar')
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
            proximities_data.append({
                'player_name': prox.player_name,
                'milestone': prox.milestone.description,
                'current': str(prox.current_value),
                'target': str(prox.milestone.threshold),
                'remaining': str(prox.distance),
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
        schedule_url = config.get('gameday', {}).get('haverford_schedule_url', 'https://haverfordathletics.com/calendar')
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


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
