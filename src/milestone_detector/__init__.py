"""
Milestone Detector Module

This module analyzes player statistics to identify who is close to milestones.
"""

from .detector import MilestoneDetector, generate_milestone_thresholds, normalize_sport_name
from .models import Milestone, MilestoneProximity

__all__ = ["MilestoneDetector", "Milestone", "MilestoneProximity", "generate_milestone_thresholds", "normalize_sport_name"]
