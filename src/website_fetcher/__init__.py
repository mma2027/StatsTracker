"""
Website Fetcher Module

This module fetches sports statistics from various sources (NCAA, TFRR, CricClubs, etc.)
"""

from .base_fetcher import BaseFetcher, FetchResult
from .ncaa_fetcher import NCAAFetcher
from .tfrr_fetcher import TFRRFetcher
from .tfrr_playwright_fetcher import TFRRPlaywrightFetcher
from .cricket_fetcher import CricketFetcher
from .squash_fetcher import SquashFetcher

__all__ = [
    "BaseFetcher",
    "FetchResult",
    "NCAAFetcher",
    "TFRRFetcher",
    "TFRRPlaywrightFetcher",
    "CricketFetcher",
    "SquashFetcher",
]
