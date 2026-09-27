"""
ScrapeFlow - Resilient Async Web Scraping & Data Pipeline Engine.
Pure Python, zero mandatory dependencies.
"""

from .engine import Crawler
from .limiter import DomainRateLimiter
from .models import Request, Response
from .parser import Selector, SimpleHTMLParser
from .pipeline import (
    BasePipeline,
    CsvPipeline,
    JsonLinesPipeline,
    SqlitePipeline,
)

__version__ = "0.1.0"
__all__ = [
    "Crawler",
    "Request",
    "Response",
    "Selector",
    "SimpleHTMLParser",
    "DomainRateLimiter",
    "BasePipeline",
    "CsvPipeline",
    "JsonLinesPipeline",
    "SqlitePipeline",
]
