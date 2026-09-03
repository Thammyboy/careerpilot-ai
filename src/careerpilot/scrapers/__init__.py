"""Scrapers package for aggregating job listings across regional portals."""

from careerpilot.scrapers.base import BaseScraper
from careerpilot.scrapers.linkedin import LinkedInScraper
from careerpilot.scrapers.jobsdb import JobsDBScraper
from careerpilot.scrapers.jobthai import JobThaiScraper
from careerpilot.scrapers.engine import AggregationEngine

__all__ = [
    "BaseScraper",
    "LinkedInScraper",
    "JobsDBScraper",
    "JobThaiScraper",
    "AggregationEngine",
]
