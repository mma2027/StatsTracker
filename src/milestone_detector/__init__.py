"""
Milestone Detector Module

This module analyzes player statistics to identify who is close to milestones.
"""

from .detector import MilestoneDetector
from .models import Milestone, MilestoneProximity

__all__ = ['MilestoneDetector', 'Milestone', 'MilestoneProximity']
