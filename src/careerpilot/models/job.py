"""Normalized Job Posting data models."""

from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from pydantic import BaseModel, Field, HttpUrl


class SourceChannel(str, Enum):
    """Supported job source platforms and recruitment agencies."""
    LINKEDIN = "LinkedIn"
    JOBSDB = "JobsDB"
    JOBTHAI = "JobThai"
    ADECCO = "Adecco"
    MANPOWER = "Manpower"
    PRTR = "PRTR"
    ROBERT_WALTERS = "Robert Walters"
    JAC = "JAC Recruitment"


class ReviewDecision(str, Enum):
    """User triage decision in Notion."""
    INBOX = "Inbox"
    APPROVED = "Approved"
    PASS = "Pass"
    FOLLOW_UP = "Follow Up"


class ApplicationStage(str, Enum):
    """Lifecycle stage of the application."""
    UNAPPLIED = "Unapplied"
    DRAFT_READY = "Draft Ready"
    SUBMITTED = "Submitted"
    INTERVIEWING = "Interviewing"
    ARCHIVED = "Archived"


class JobPosting(BaseModel):
    """Normalized job posting structure across all sources."""

    id: str = Field(..., description="Internal unique identifier or composite hash")
    title: str = Field(..., description="Job role title")
    company: str = Field(..., description="Company or hiring client name")
    source: SourceChannel = Field(..., description="Source board or recruitment agency")
    url: str = Field(..., description="Direct posting or application URL")
    external_id: Optional[str] = Field(default=None, description="Platform-specific job ID")
    agency_ref_id: Optional[str] = Field(default=None, description="Agency reference code or consultant code")
    location: str = Field(default="Thailand", description="Geographic location or remote status")
    salary_range: Optional[str] = Field(default=None, description="Raw or normalized salary string")
    description: Optional[str] = Field(default="", description="Job description or bullet points")
    tags: List[str] = Field(default_factory=list, description="Skills, categories, or keywords extracted")
    match_score: Optional[int] = Field(default=None, ge=0, le=100, description="Fit score 0-100%")
    review_decision: ReviewDecision = Field(default=ReviewDecision.INBOX, description="Notion review decision")
    application_stage: ApplicationStage = Field(default=ApplicationStage.UNAPPLIED, description="Application status")
    tailored_context: Optional[str] = Field(default=None, description="Tailored cover memo or notes")
    posted_at: Optional[str] = Field(default=None, description="Posted date or relative age string")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Scrape timestamp")
    composite_hash: Optional[str] = Field(default=None, description="Deduplication hash")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Arbitrary raw platform metadata")
