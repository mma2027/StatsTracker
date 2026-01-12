"""
Email Templates

Generates formatted email content for notifications.
"""

from typing import List
from datetime import date

from ..milestone_detector import MilestoneProximity
from ..gameday_checker import Game


class EmailTemplate:
    """
    Generates email content from data.

    Provides both HTML and plain text versions.
    """

    @staticmethod
    def generate_subject(date_for: date, num_games: int) -> str:
        """
        Generate email subject line.

        Args:
            date_for: Date the notification is for
            num_games: Number of games scheduled

        Returns:
            Subject line string
        """
        date_str = date_for.strftime("%B %d, %Y")
        if num_games > 0:
            return f"Haverford Milestone Alert - {date_str} ({num_games} games today)"
        return f"Haverford Milestone Alert - {date_str}"

    @staticmethod
    def generate_milestone_email(
        proximities: List[MilestoneProximity],
        games: List[Game],
        date_for: date
    ) -> str:
        """
        Generate HTML email body for milestone notification.

        Args:
            proximities: List of milestone proximities
            games: List of scheduled games
            date_for: Date for notification

        Returns:
            HTML email body
        """
        date_str = date_for.strftime("%B %d, %Y")

        html = f"""
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                h1 {{
                    color: #8B0000;
                    border-bottom: 2px solid #8B0000;
                    padding-bottom: 10px;
                }}
                h2 {{
                    color: #555;
                    margin-top: 30px;
                }}
                .milestone {{
                    background-color: #f5f5f5;
                    padding: 15px;
                    margin: 10px 0;
                    border-left: 4px solid #8B0000;
                    border-radius: 4px;
                }}
                .player-name {{
                    font-weight: bold;
                    font-size: 1.1em;
                    color: #8B0000;
                }}
                .stat-detail {{
                    margin: 5px 0;
                }}
                .progress {{
                    background-color: #ddd;
                    height: 20px;
                    border-radius: 10px;
                    overflow: hidden;
                    margin: 10px 0;
                }}
                .progress-bar {{
                    height: 100%;
                    background-color: #8B0000;
                    text-align: center;
                    color: white;
                    line-height: 20px;
                    font-size: 12px;
                }}
                .game {{
                    background-color: #e8f4f8;
                    padding: 10px;
                    margin: 10px 0;
                    border-left: 4px solid #0066cc;
                    border-radius: 4px;
                }}
                .footer {{
                    margin-top: 40px;
                    padding-top: 20px;
                    border-top: 1px solid #ddd;
                    font-size: 0.9em;
                    color: #666;
                }}
            </style>
        </head>
        <body>
            <h1>Haverford College Sports Milestones</h1>
            <p><strong>Date:</strong> {date_str}</p>
        """

        # Add games section if there are games
        if games:
            html += "<h2>Today's Games</h2>"
            for game in games:
                location = "Home" if game.is_home_game else "Away"
                time_str = game.time if game.time else "TBD"
                html += f"""
                <div class="game">
                    <strong>{game.team.sport.title()}</strong> - {game.team.name}<br>
                    vs {game.opponent} ({location})<br>
                    Time: {time_str}
                </div>
                """

        # Add milestones section
        if proximities:
            html += "<h2>Players Close to Milestones</h2>"
            html += f"<p>{len(proximities)} player(s) are approaching milestone achievements:</p>"

            for prox in proximities:
                html += f"""
                <div class="milestone">
                    <div class="player-name">{prox.player_name}</div>
                    <div class="stat-detail">
                        <strong>Milestone:</strong> {prox.milestone.description}
                    </div>
                    <div class="stat-detail">
                        <strong>Current:</strong> {prox.current_value} |
                        <strong>Target:</strong> {prox.milestone.threshold} |
                        <strong>Remaining:</strong> {prox.distance}
                    </div>
                    <div class="progress">
                        <div class="progress-bar" style="width: {min(prox.percentage, 100)}%">
                            {prox.percentage:.1f}%
                        </div>
                    </div>
                """

                if prox.estimated_games_to_milestone:
                    html += f"""
                    <div class="stat-detail">
                        <em>Estimated {prox.estimated_games_to_milestone} game(s) to milestone</em>
                    </div>
                    """

                html += "</div>"
        else:
            html += "<h2>No Milestone Alerts</h2>"
            html += "<p>No players are currently close to milestone achievements.</p>"

        # Footer
        html += """
            <div class="footer">
                <p>This is an automated notification from the Haverford College StatsTracker system.</p>
                <p>Track the progress of our student-athletes throughout the season!</p>
            </div>
        </body>
        </html>
        """

        return html

    @staticmethod
    def generate_text_version(
        proximities: List[MilestoneProximity],
        games: List[Game],
        date_for: date
    ) -> str:
        """
        Generate plain text email body for milestone notification.

        Args:
            proximities: List of milestone proximities
            games: List of scheduled games
            date_for: Date for notification

        Returns:
            Plain text email body
        """
        date_str = date_for.strftime("%B %d, %Y")

        text = f"HAVERFORD COLLEGE SPORTS MILESTONES\n"
        text += f"Date: {date_str}\n"
        text += "=" * 60 + "\n\n"

        # Add games section
        if games:
            text += "TODAY'S GAMES\n"
            text += "-" * 60 + "\n"
            for game in games:
                location = "Home" if game.is_home_game else "Away"
                time_str = game.time if game.time else "TBD"
                text += f"\n{game.team.sport.title()} - {game.team.name}\n"
                text += f"vs {game.opponent} ({location})\n"
                text += f"Time: {time_str}\n"
            text += "\n"

        # Add milestones section
        if proximities:
            text += "PLAYERS CLOSE TO MILESTONES\n"
            text += "-" * 60 + "\n"
            text += f"\n{len(proximities)} player(s) approaching milestone achievements:\n\n"

            for prox in proximities:
                text += f"{prox.player_name}\n"
                text += f"  Milestone: {prox.milestone.description}\n"
                text += f"  Current: {prox.current_value} | Target: {prox.milestone.threshold}\n"
                text += f"  Remaining: {prox.distance} ({prox.percentage:.1f}% complete)\n"

                if prox.estimated_games_to_milestone:
                    text += f"  Estimated {prox.estimated_games_to_milestone} game(s) to milestone\n"

                text += "\n"
        else:
            text += "NO MILESTONE ALERTS\n"
            text += "-" * 60 + "\n"
            text += "No players are currently close to milestone achievements.\n\n"

        # Footer
        text += "=" * 60 + "\n"
        text += "This is an automated notification from the Haverford College\n"
        text += "StatsTracker system.\n"

        return text
