"""Sync pipeline for formatting and pushing JobPostings to Notion."""

import logging
from typing import List, Dict, Any, Tuple, Optional
from careerpilot.models.job import JobPosting
from careerpilot.notion.client import NotionClientWrapper

logger = logging.getLogger(__name__)


def format_job_to_notion_properties(job: JobPosting) -> Dict[str, Any]:
    """Map a JobPosting model to Notion database page properties."""
    properties: Dict[str, Any] = {
        "Job Title": {
            "title": [{"text": {"content": job.title[:200]}}]
        },
        "Company / Client": {
            "rich_text": [{"text": {"content": job.company[:200]}}]
        },
        "Source Channel": {
            "select": {"name": job.source.value}
        },
        "Agency Reference ID": {
            "rich_text": [{"text": {"content": (job.agency_ref_id or job.external_id or "")[:100]}}]
        },
        "Location": {
            "rich_text": [{"text": {"content": job.location[:100]}}]
        },
        "Salary Range": {
            "rich_text": [{"text": {"content": (job.salary_range or "Not Disclosed")[:100]}}]
        },
        "Posting URL": {
            "url": job.url
        },
        "Review Decision": {
            "status": {"name": job.review_decision.value}
        },
        "Application Stage": {
            "status": {"name": job.application_stage.value}
        },
    }

    if job.match_score is not None:
        # Format as fraction (0.0 - 1.0) for Notion percent formatting
        properties["Match Score"] = {"number": job.match_score / 100.0}

    return properties


def format_job_to_notion_blocks(job: JobPosting) -> List[Dict[str, Any]]:
    """Build readable Notion page body blocks containing tags and description."""
    blocks: List[Dict[str, Any]] = []

    # Tag callout or heading
    if job.tags:
        tag_str = " | ".join(job.tags)
        blocks.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": f"Tags & Domains: {tag_str}"},
                        "annotations": {"italic": True, "color": "gray"}
                    }
                ]
            }
        })

    # Section divider
    blocks.append({"object": "block", "type": "divider", "divider": {}})

    # Job Description
    desc_content = job.description or "No description snippet available."
    # Chunk long descriptions into 2000-char paragraphs (Notion block limit)
    for chunk in [desc_content[i:i+1900] for i in range(0, len(desc_content), 1900)]:
        blocks.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": chunk}}]
            }
        })

    return blocks


class NotionSyncPipeline:
    """Orchestrates syncing jobs into Notion with duplicate checking and dry-run preview."""

    def __init__(self, client_wrapper: Optional[NotionClientWrapper] = None):
        self.client = client_wrapper or NotionClientWrapper()

    def sync(
        self,
        jobs: List[JobPosting],
        dry_run: bool = False,
    ) -> Tuple[int, int, int]:
        """
        Sync a batch of JobPosting objects to Notion.
        Returns: (synced_count, skipped_count, error_count)
        """
        if not dry_run and not self.client.is_configured:
            logger.warning(
                "Notion is not configured (missing NOTION_API_KEY or NOTION_DATABASE_ID). "
                "Running in dry-run mode."
            )
            dry_run = True

        logger.info(
            "Starting Notion sync pipeline: %d candidate postings (dry_run=%s)",
            len(jobs),
            dry_run,
        )

        existing_urls = set()
        if not dry_run:
            schema_ok = self.client.ensure_schema()
            if not schema_ok:
                logger.warning(
                    "Notion schema check/auto-configuration could not be completed. "
                    "Sync will proceed, but may fail if properties are missing."
                )
            existing_urls = self.client.query_existing_urls()
            logger.info("Retrieved %d existing URLs from Notion database.", len(existing_urls))

        synced = 0
        skipped = 0
        errors = 0

        for job in jobs:
            if job.url in existing_urls:
                logger.debug("Skipping already synced URL: %s", job.url)
                skipped += 1
                continue

            properties = format_job_to_notion_properties(job)
            blocks = format_job_to_notion_blocks(job)

            if dry_run:
                logger.info("[Dry Run] Would sync: '%s' at '%s' (%s)", job.title, job.company, job.url)
                synced += 1
            else:
                try:
                    self.client.create_page(properties=properties, children=blocks)
                    synced += 1
                    existing_urls.add(job.url)
                    logger.info("Synced: '%s' at '%s'", job.title, job.company)
                except Exception as exc:
                    logger.error("Failed to sync job '%s': %s", job.title, exc)
                    errors += 1

        logger.info(
            "Notion Sync Complete -> Synced: %d, Skipped: %d, Errors: %d",
            synced,
            skipped,
            errors,
        )
        return synced, skipped, errors
