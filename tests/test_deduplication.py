"""Tests for deduplication engine and text normalizers."""

from pathlib import Path
import tempfile
import pytest
from careerpilot.models.job import JobPosting, SourceChannel
from careerpilot.deduplication.normalizer import (
    normalize_company_name,
    normalize_job_title,
    generate_composite_hash,
    DeduplicationEngine,
)


def test_normalize_company_name():
    assert normalize_company_name("THAI CREDIT BANK PUBLIC COMPANY LIMITED") == "thai credit bank"
    assert normalize_company_name("บริษัท แอสเตโม โคราช จำกัด") == "แอสเตโม โคราช"
    assert normalize_company_name("Acme Services Co., Ltd. (Thailand)") == "acme services"
    assert normalize_company_name("Google Inc.") == "google"


def test_normalize_job_title():
    assert normalize_job_title("Senior Software Engineer (Bangkok)") == "senior software engineer"
    assert normalize_job_title("Backend Developer - Python / Go") == "backend developer python go"
    assert normalize_job_title("Lead Full-Stack Developer [Hybrid]") == "lead full stack developer"


def test_generate_composite_hash():
    h1 = generate_composite_hash("Agoda Co., Ltd.", "Software Engineer (Backend)", "job-1001")
    h2 = generate_composite_hash("Agoda", "Software Engineer - Backend", "job-1001")
    assert h1 == h2, "Equivalent company and title should produce identical hash"

    h3 = generate_composite_hash("Grab", "Software Engineer", "job-1002")
    assert h1 != h3


def test_deduplication_engine(tmp_path: Path):
    cache_file = tmp_path / "test_seen.json"
    engine = DeduplicationEngine(storage_file=cache_file, window_days=90)

    job1 = JobPosting(
        id="1",
        title="Python Engineer",
        company="TechCorp Co., Ltd.",
        source=SourceChannel.LINKEDIN,
        url="https://linkedin.com/jobs/view/1",
        external_id="1",
    )
    job2 = JobPosting(
        id="2",
        title="Python Engineer",
        company="TechCorp",
        source=SourceChannel.JOBSDB,
        url="https://th.jobsdb.com/job/1",
        external_id="1",
    )
    job3 = JobPosting(
        id="3",
        title="React Developer",
        company="Startup Co.",
        source=SourceChannel.JOBTHAI,
        url="https://jobthai.com/job/2",
        external_id="2",
    )

    # First batch: job1 and job2 are identical in normalized company & ref
    unique, dropped = engine.process([job1, job2, job3])
    assert len(unique) == 2
    assert len(dropped) == 1
    assert unique[0].id == job1.id
    assert unique[1].id == job3.id

    # Second batch run with same jobs should drop them since they're in 90-day window
    unique2, dropped2 = engine.process([job1, job3])
    assert len(unique2) == 0
    assert len(dropped2) == 2
