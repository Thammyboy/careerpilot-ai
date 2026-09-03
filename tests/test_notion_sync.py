"""Tests for Notion database mapping and sync pipeline."""

import pytest
from careerpilot.models.job import (
    JobPosting,
    SourceChannel,
    ReviewDecision,
    ApplicationStage,
)
from careerpilot.notion.sync import (
    format_job_to_notion_properties,
    format_job_to_notion_blocks,
    NotionSyncPipeline,
)


def test_format_job_to_notion_properties():
    job = JobPosting(
        id="test_job_1",
        title="Staff Backend Engineer",
        company="Agoda Services",
        source=SourceChannel.LINKEDIN,
        url="https://linkedin.com/jobs/view/999",
        agency_ref_id="REF-101",
        location="Bangkok, Thailand",
        salary_range="180,000 - 240,000 THB",
        match_score=92,
        review_decision=ReviewDecision.INBOX,
        application_stage=ApplicationStage.UNAPPLIED,
    )

    props = format_job_to_notion_properties(job)

    # Validate PRD Schema compliance
    assert "Job Title" in props
    assert props["Job Title"]["title"][0]["text"]["content"] == "Staff Backend Engineer"

    assert "Company / Client" in props
    assert props["Company / Client"]["rich_text"][0]["text"]["content"] == "Agoda Services"

    assert "Source Channel" in props
    assert props["Source Channel"]["select"]["name"] == "LinkedIn"

    assert "Agency Reference ID" in props
    assert props["Agency Reference ID"]["rich_text"][0]["text"]["content"] == "REF-101"

    assert "Location" in props
    assert props["Location"]["rich_text"][0]["text"]["content"] == "Bangkok, Thailand"

    assert "Salary Range" in props
    assert props["Salary Range"]["rich_text"][0]["text"]["content"] == "180,000 - 240,000 THB"

    assert "Posting URL" in props
    assert props["Posting URL"]["url"] == "https://linkedin.com/jobs/view/999"

    assert "Review Decision" in props
    assert props["Review Decision"]["status"]["name"] == "Inbox"

    assert "Application Stage" in props
    assert props["Application Stage"]["status"]["name"] == "Unapplied"

    assert "Match Score" in props
    assert props["Match Score"]["number"] == 0.92


def test_format_job_to_notion_blocks():
    job = JobPosting(
        id="test_job_2",
        title="Full Stack Engineer",
        company="Startup",
        source=SourceChannel.JOBTHAI,
        url="https://jobthai.com/job/10",
        description="Build scalable microservices and user interfaces in React.",
        tags=["React", "Node.js", "JobThai"],
    )

    blocks = format_job_to_notion_blocks(job)
    assert len(blocks) >= 2
    # Tags block
    assert "Tags & Domains: React | Node.js | JobThai" in str(blocks[0])
    # Description chunk block
    assert "Build scalable microservices" in str(blocks)


def test_notion_sync_pipeline_dry_run():
    pipeline = NotionSyncPipeline()
    jobs = [
        JobPosting(
            id="1",
            title="Backend Engineer",
            company="Company A",
            source=SourceChannel.JOBSDB,
            url="https://th.jobsdb.com/job/1",
        ),
        JobPosting(
            id="2",
            title="Frontend Engineer",
            company="Company B",
            source=SourceChannel.JOBTHAI,
            url="https://jobthai.com/job/2",
        ),
    ]

    synced, skipped, errors = pipeline.sync(jobs, dry_run=True)
    assert synced == 2
    assert skipped == 0
    assert errors == 0
