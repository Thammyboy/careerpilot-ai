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


from unittest.mock import MagicMock
from careerpilot.notion.client import NotionClientWrapper


def test_notion_is_database_empty():
    mock_client = MagicMock()
    # Case 1: Empty database with only default 'Name' property and 0 rows
    mock_client.databases.retrieve.return_value = {
        "properties": {
            "Name": {"id": "title", "type": "title", "name": "Name"}
        }
    }
    mock_client.databases.query.return_value = {"results": []}

    wrapper = NotionClientWrapper(api_key="test_key", database_id="test_db", client=mock_client)
    assert wrapper.is_database_empty() is True

    # Case 2: Database has existing records
    mock_client.databases.query.return_value = {"results": [{"id": "page_1"}]}
    assert wrapper.is_database_empty() is False

    # Case 3: Database has 0 records but already has CareerPilot schema configured
    mock_client.databases.query.return_value = {"results": []}
    mock_client.databases.retrieve.return_value = {
        "properties": {
            "Job Title": {"type": "title"},
            "Posting URL": {"type": "url"},
            "Source Channel": {"type": "select"},
        }
    }
    assert wrapper.is_database_empty() is False

    # Case 4: notion-client version where databases has no 'query' attribute (falls back to client.request)
    mock_client_no_query = MagicMock(spec=["request", "databases"])
    mock_client_no_query.databases = MagicMock(spec=["retrieve", "update"])
    mock_client_no_query.databases.retrieve.return_value = {
        "properties": {"Name": {"type": "title"}}
    }
    mock_client_no_query.request.return_value = {"results": []}
    wrapper_no_query = NotionClientWrapper(api_key="test_key", database_id="test_db", client=mock_client_no_query)
    assert wrapper_no_query.is_database_empty() is True
    mock_client_no_query.request.assert_called_once_with(
        path="databases/test_db/query",
        method="POST",
        body={"page_size": 1},
    )


def test_notion_setup_database_schema():
    mock_client = MagicMock()
    mock_client.databases.retrieve.return_value = {
        "properties": {
            "Name": {"id": "title", "type": "title", "name": "Name"}
        }
    }
    wrapper = NotionClientWrapper(api_key="test_key", database_id="test_db", client=mock_client)

    success = wrapper.setup_database_schema()
    assert success is True

    mock_client.databases.update.assert_called_once()
    call_kwargs = mock_client.databases.update.call_args.kwargs
    assert call_kwargs["database_id"] == "test_db"
    props = call_kwargs["properties"]

    # Must rename default 'Name' column to 'Job Title'
    assert props["Name"] == {"name": "Job Title"}
    # Must contain essential CareerPilot columns
    assert "Company / Client" in props
    assert "Posting URL" in props
    assert "Source Channel" in props
    assert "Review Decision" in props
    assert "Application Stage" in props


def test_notion_ensure_schema_trigger():
    mock_client = MagicMock()
    mock_client.databases.retrieve.return_value = {
        "properties": {
            "Name": {"id": "title", "type": "title", "name": "Name"}
        }
    }
    mock_client.databases.query.return_value = {"results": []}

    wrapper = NotionClientWrapper(api_key="test_key", database_id="test_db", client=mock_client)
    assert wrapper.ensure_schema() is True
    mock_client.databases.update.assert_called_once()
