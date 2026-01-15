"""
PR Tracker - Personal Record Breakthrough Detection

Detects personal record (PR/PB) breakthroughs for track & field athletes
"""

import csv
import logging
from typing import Dict, List, Any
from datetime import datetime, date
from pathlib import Path
import re

from ..website_fetcher.tfrr_fetcher import TFRRFetcher, HAVERFORD_TEAMS
from .models import PRBreakthrough


logger = logging.getLogger(__name__)


class PRTracker:
    """
    PR Tracker - Detects personal record breakthroughs for track & field athletes

    Workflow:
    1. Fetch current PR data from TFRR fetcher
    2. Load historical PR data from CSV file
    3. Compare and detect breakthroughs
    4. Update CSV file
    """

    # Time-based events (lower is better)
    TIME_EVENTS = ["m", "h", "hurdle", "relay", "walk", "steeple"]

    # Distance/height events (higher is better)
    DISTANCE_EVENTS = [
        "jump",
        "throw",
        "put",
        "javelin",
        "shot",
        "discus",
        "hammer",
        "lj",
        "tj",
        "hj",
        "pv",  # Long Jump, Triple Jump, High Jump, Pole Vault
        "sp",
        "dt",
        "jt",
        "ht",  # Shot Put, Discus Throw, Javelin Throw, Hammer Throw
    ]

    def __init__(self, tfrr_fetcher: TFRRFetcher, history_file: str = "data/pr_history.csv"):
        """
        Initialize PR tracker

        Args:
            tfrr_fetcher: TFRRFetcher instance
            history_file: CSV file path for historical PR data
        """
        self.tfrr_fetcher = tfrr_fetcher
        self.history_file = history_file

    def fetch_current_prs(self, team_code: str, sport: str) -> Dict[str, Dict[str, str]]:
        """
        Fetch current PRs for all athletes from TFRR

        Args:
            team_code: TFRR team code
            sport: Sport type ("track" or "cross_country")

        Returns:
            {athlete_name: {event: pr_value}}
        """
        try:
            # Step 1: Fetch team roster to get athlete IDs
            logger.info(f"Fetching team roster for {team_code}")
            result = self.tfrr_fetcher.fetch_team_stats(team_code, sport)

            if not result.success:
                logger.error(f"Failed to fetch team stats: {result.error}")
                return {}

            team_data = result.data
            current_prs = {}

            # Step 2: Extract roster (athlete IDs and names)
            roster = team_data.get("roster", [])

            if not roster:
                logger.warning(f"No roster found in team data for {team_code}")
                return {}

            logger.info(f"Found {len(roster)} athletes in roster")

            # Step 3: For each athlete, fetch their individual stats (including PRs)
            for athlete in roster:
                athlete_id = athlete.get("athlete_id")
                athlete_name = athlete.get("name")

                if not athlete_id or not athlete_name:
                    continue

                try:
                    logger.debug(f"Fetching PRs for {athlete_name} (ID: {athlete_id})")

                    # Call fetch_player_stats to get individual athlete data
                    player_result = self.tfrr_fetcher.fetch_player_stats(athlete_id, sport)

                    if not player_result.success:
                        logger.warning(f"Failed to fetch stats for {athlete_name}: {player_result.error}")
                        continue

                    player_data = player_result.data

                    # Extract personal records from player data
                    personal_records = player_data.get("personal_records", {})

                    if not personal_records:
                        logger.debug(f"No PRs found for {athlete_name}")
                        continue

                    # Filter valid PR data
                    valid_prs = {
                        event: pr
                        for event, pr in personal_records.items()
                        if pr and str(pr).strip() and pr != "-" and pr != "—"
                    }

                    if valid_prs:
                        current_prs[athlete_name] = valid_prs
                        logger.debug(f"Fetched {len(valid_prs)} PRs for {athlete_name}")

                except Exception as e:
                    logger.warning(f"Error fetching PRs for {athlete_name}: {e}")
                    continue  # Continue with next athlete even if this one fails

            logger.info(f"Successfully fetched PRs for {len(current_prs)} out of {len(roster)} athletes from {team_code}")
            return current_prs

        except Exception as e:
            logger.error(f"Error fetching current PRs: {e}")
            return {}

    def load_historical_prs(self) -> Dict[str, Dict[str, Any]]:
        """
        Load historical PR data from CSV

        Returns:
            {athlete_name: {event: {"pr": value, "date": date}}}
        """
        historical_prs = {}

        if not Path(self.history_file).exists():
            logger.warning(f"No PR history file found at {self.history_file}")
            return {}

        try:
            with open(self.history_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)

                for row in reader:
                    athlete_name = row["athlete_name"]
                    event = row["event"]
                    pr_value = row["pr_value"]
                    date_str = row["date_recorded"]

                    # Parse date
                    try:
                        recorded_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                    except ValueError:
                        recorded_date = None

                    # Organize data structure
                    if athlete_name not in historical_prs:
                        historical_prs[athlete_name] = {}

                    historical_prs[athlete_name][event] = {"pr": pr_value, "date": recorded_date}

            logger.info(f"Loaded historical PRs for {len(historical_prs)} athletes")
            return historical_prs

        except Exception as e:
            logger.error(f"Error loading historical PRs: {e}")
            return {}

    def detect_breakthroughs(
        self,
        current_prs: Dict[str, Dict[str, str]],
        historical_prs: Dict[str, Dict[str, Any]],
        date_range_days: int = 1,
    ) -> List[PRBreakthrough]:
        """
        Detect PR breakthroughs

        Args:
            current_prs: Current PR data
            historical_prs: Historical PR data
            date_range_days: Detect breakthroughs within N days (default 1 day, yesterday)

        Returns:
            List of PRBreakthrough objects
        """
        breakthroughs = []
        today = date.today()

        for athlete_name, events in current_prs.items():
            if athlete_name not in historical_prs:
                continue  # New athlete, no historical comparison

            hist_events = historical_prs[athlete_name]

            for event, new_pr in events.items():
                if event not in hist_events:
                    continue  # New event, no historical comparison

                old_data = hist_events[event]
                old_pr = old_data["pr"]
                old_date = old_data["date"]

                # Check for improvement
                if self._is_improvement(event, old_pr, new_pr):
                    # Check if date is within range
                    if old_date and (today - old_date).days <= date_range_days:
                        # Calculate improvement amount
                        improvement = self._calculate_improvement(event, old_pr, new_pr)

                        breakthrough = PRBreakthrough(
                            athlete_id=self._generate_athlete_id(athlete_name),
                            athlete_name=athlete_name,
                            event=event,
                            old_pr=old_pr,
                            new_pr=new_pr,
                            improvement=improvement,
                            date=today,
                            meet_name=None,  # Can be obtained from TFRR recent_results
                        )
                        breakthroughs.append(breakthrough)

        logger.info(f"Detected {len(breakthroughs)} PR breakthroughs")
        return breakthroughs

    def _is_improvement(self, event: str, old_pr: str, new_pr: str) -> bool:
        """
        Determine if it's an improvement (considering running time lower is better, jump distance higher is better)

        Args:
            event: Event name
            old_pr: Old PR value
            new_pr: New PR value

        Returns:
            True if improvement
        """
        try:
            event_lower = event.lower()

            # Determine event type - check distance events first (more specific)
            is_distance_event = any(keyword in event_lower for keyword in self.DISTANCE_EVENTS)

            if is_distance_event:
                # Distance/height: higher is better
                old_distance = self._parse_distance(old_pr)
                new_distance = self._parse_distance(new_pr)
                return new_distance > old_distance
            else:
                # Time: lower is better
                old_time = self._parse_time(old_pr)
                new_time = self._parse_time(new_pr)
                return new_time < old_time

        except Exception as e:
            logger.warning(f"Error comparing PRs for {event}: {e}")
            return False

    def _parse_time(self, time_str: str) -> float:
        """
        Parse time string to seconds

        Supported formats:
        - "11.25" -> 11.25 seconds
        - "11.25s" -> 11.25 seconds
        - "1:45.32" -> 105.32 seconds (1 minute 45.32 seconds)
        """
        time_str = time_str.strip().lower()

        # Remove unit
        time_str = time_str.replace("s", "").strip()

        # Handle minute:second format
        if ":" in time_str:
            parts = time_str.split(":")
            minutes = float(parts[0])
            seconds = float(parts[1])
            return minutes * 60 + seconds
        else:
            return float(time_str)

    def _parse_distance(self, distance_str: str) -> float:
        """
        Parse distance string to meters

        Supported formats:
        - "5.89m" -> 5.89 meters
        - "5.89" -> 5.89 meters
        - "19'3\"" -> feet and inches (convert to meters)
        """
        distance_str = distance_str.strip().lower()

        # Remove unit
        distance_str = distance_str.replace("m", "").strip()

        # Handle feet and inches format (if any)
        if "'" in distance_str or '"' in distance_str:
            # Simplified handling: extract numbers only
            distance_str = re.sub(r"[^\d.]", "", distance_str)

        return float(distance_str)

    def _calculate_improvement(self, event: str, old_pr: str, new_pr: str) -> str:
        """
        Calculate improvement amount

        Returns:
            Formatted improvement string like "0.10s" or "0.15m"
        """
        try:
            event_lower = event.lower()
            is_distance_event = any(keyword in event_lower for keyword in self.DISTANCE_EVENTS)

            if is_distance_event:
                old_val = self._parse_distance(old_pr)
                new_val = self._parse_distance(new_pr)
                diff = new_val - old_val  # Distance increase
                return f"{abs(diff):.2f}m"
            else:
                old_val = self._parse_time(old_pr)
                new_val = self._parse_time(new_pr)
                diff = old_val - new_val  # Time decrease
                return f"{abs(diff):.2f}s"

        except Exception as e:
            logger.warning(f"Error calculating improvement: {e}")
            return "—"

    def _generate_athlete_id(self, athlete_name: str) -> str:
        """
        Generate ID from athlete name

        Args:
            athlete_name: Athlete name

        Returns:
            ID string
        """
        # Simple implementation: remove spaces and convert to lowercase
        return athlete_name.replace(" ", "_").lower()

    def save_current_prs(self, current_prs: Dict[str, Dict[str, str]]):
        """
        Save current PRs to CSV as new historical baseline

        Args:
            current_prs: Current PR data {athlete_name: {event: pr_value}}
        """
        try:
            # Ensure directory exists
            Path(self.history_file).parent.mkdir(parents=True, exist_ok=True)

            with open(self.history_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)

                # Write header
                writer.writerow(["athlete_name", "event", "pr_value", "date_recorded"])

                # Write data
                today_str = date.today().isoformat()

                for athlete_name, events in current_prs.items():
                    for event, pr_value in events.items():
                        writer.writerow([athlete_name, event, pr_value, today_str])

            logger.info(f"Saved PR history to {self.history_file}")

        except Exception as e:
            logger.error(f"Error saving PR history: {e}")

    def check_yesterday_breakthroughs(self) -> List[PRBreakthrough]:
        """
        Convenience method - Check yesterday's PR breakthroughs

        This is the main entry method, integrating all steps

        Returns:
            List of PRs broken yesterday
        """
        try:
            logger.info("Checking for yesterday's PR breakthroughs...")

            # 1. Fetch current PRs for all Haverford track teams
            all_current_prs = {}

            for sport_key, team_code in HAVERFORD_TEAMS.items():
                sport = "cross_country" if "cross_country" in sport_key else "track"
                prs = self.fetch_current_prs(team_code, sport)
                all_current_prs.update(prs)

            if not all_current_prs:
                logger.warning("No current PRs fetched")
                return []

            # 2. Load historical PR data
            historical_prs = self.load_historical_prs()

            if not historical_prs:
                # First run, initialize historical data
                logger.info("Initializing PR history (first run)")
                self.save_current_prs(all_current_prs)
                return []  # First run doesn't report breakthroughs

            # 3. Detect breakthroughs
            breakthroughs = self.detect_breakthroughs(all_current_prs, historical_prs, date_range_days=1)

            # 4. Update CSV history file
            if breakthroughs:
                logger.info(f"Updating PR history with {len(breakthroughs)} breakthroughs")

            self.save_current_prs(all_current_prs)

            return breakthroughs

        except Exception as e:
            logger.error(f"Error in check_yesterday_breakthroughs: {e}")
            return []
