"""
PR Tracker Models

Data class definitions for PR breakthrough tracking
"""

from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass
class PRBreakthrough:
    """
    Personal Record Breakthrough Entry

    Represents an athlete breaking their personal record in an event
    """

    athlete_id: str
    athlete_name: str
    event: str  # Event name, e.g. "100m", "Long Jump"
    old_pr: str  # Old PR, e.g. "11.25"
    new_pr: str  # New PR, e.g. "11.15"
    improvement: str  # Improvement amount, e.g. "0.10s" or "3.2%"
    date: date  # Date PR was broken
    meet_name: Optional[str] = None  # Meet name

    @property
    def improvement_percentage(self) -> Optional[float]:
        """
        Calculate improvement percentage

        Returns:
            Improvement percentage, or None if unable to calculate
        """
        try:
            # Extract numeric part
            import re

            # Remove units, keep only numbers
            old_value = float(re.sub(r'[^\d.]', '', self.old_pr))
            new_value = float(re.sub(r'[^\d.]', '', self.new_pr))

            if old_value == 0:
                return None

            # Calculate percentage change
            percentage = abs((new_value - old_value) / old_value) * 100
            return round(percentage, 2)

        except (ValueError, ZeroDivisionError):
            return None
