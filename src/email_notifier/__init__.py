"""
Email Notifier Module

This module sends email notifications about milestone achievements.
"""

from .notifier import EmailNotifier
from .templates import EmailTemplate

__all__ = ['EmailNotifier', 'EmailTemplate']
