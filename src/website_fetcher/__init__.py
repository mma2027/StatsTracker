"""
Website Fetcher Module

This module fetches sports statistics from various sources (NCAA, TFRR, etc.)
"""

from .base_fetcher import BaseFetcher, FetchResult
from .ncaa_fetcher import NCAAFetcher
from .tfrr_fetcher import TFRRFetcher

__all__ = ["BaseFetcher", "FetchResult", "NCAAFetcher", "TFRRFetcher"]
