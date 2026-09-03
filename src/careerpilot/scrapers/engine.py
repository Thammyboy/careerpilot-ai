"""Aggregation engine orchestrating multi-source scraping and deduplication."""

import json
import logging
from pathlib import Path
from typing import List, Optional, Dict, Tuple
from datetime import datetime, timezone

from careerpilot.config import settings
from careerpilot.models.job import JobPosting, SourceChannel
from careerpilot.deduplication.normalizer import DeduplicationEngine
from careerpilot.scrapers.base import BaseScraper
from careerpilot.scrapers.linkedin import LinkedInScraper
from careerpilot.scrapers.jobsdb import JobsDBScraper
from careerpilot.scrapers.jobthai import JobThaiScraper

logger = logging.getLogger(__name__)


class AggregationEngine:
    """Orchestrates job aggregation across all supported primary channels."""

    def __init__(
        self,
        dedup_engine: Optional[DeduplicationEngine] = None,
        storage_dir: Optional[Path] = None,
    ):
        self.dedup_engine = dedup_engine or DeduplicationEngine()
        self.storage_dir = storage_dir or settings.storage_dir
        self.scrapers: Dict[SourceChannel, BaseScraper] = {
            SourceChannel.LINKEDIN: LinkedInScraper(),
            SourceChannel.JOBSDB: JobsDBScraper(),
            SourceChannel.JOBTHAI: JobThaiScraper(),
        }

    async def run(
        self,
        keywords: str,
        location: str = "Thailand",
        limit_per_source: int = 25,
        sources: Optional[List[SourceChannel]] = None,
        save_to_storage: bool = True,
    ) -> Tuple[List[JobPosting], List[JobPosting]]:
        """
        Execute scraping across chosen sources, deduplicate, and optionally save results.
        Returns: (unique_jobs, dropped_jobs)
        """
        active_sources = sources or list(self.scrapers.keys())
        all_raw_jobs: List[JobPosting] = []

        logger.info(
            "Starting job aggregation for '%s' in '%s' across %d sources: %s",
            keywords,
            location,
            len(active_sources),
            [s.value for s in active_sources],
        )

        for source in active_sources:
            scraper = self.scrapers.get(source)
            if not scraper:
                logger.warning("No scraper registered for source %s. Skipping.", source)
                continue

            try:
                jobs = await scraper.scrape(keywords=keywords, location=location, limit=limit_per_source)
                all_raw_jobs.extend(jobs)
            except Exception as exc:
                logger.error("Error running scraper %s: %s", source.value, exc)

        logger.info("Total raw jobs collected across all sources: %d", len(all_raw_jobs))

        # Pass through deduplication engine
        unique_jobs, dropped_jobs = self.dedup_engine.process(all_raw_jobs)
        logger.info(
            "Deduplication complete: %d unique jobs, %d duplicates dropped.",
            len(unique_jobs),
            len(dropped_jobs),
        )

        if save_to_storage:
            self._save_results(unique_jobs)

        return unique_jobs, dropped_jobs

    def _save_results(self, jobs: List[JobPosting]) -> Path:
        """Save unique jobs to disk in storage directory."""
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        output_file = self.storage_dir / f"jobs_{timestamp}.json"
        latest_file = self.storage_dir / "latest_jobs.json"

        data = [job.model_dump(mode="json") for job in jobs]
        output_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        latest_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

        logger.info("Saved %d jobs to %s and %s", len(jobs), output_file, latest_file)
        return output_file
