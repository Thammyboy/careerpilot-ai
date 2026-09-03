"""Tests for Pydantic models in careerpilot.models."""

import pytest
from careerpilot.models.profile import (
    CandidateContact,
    CompensationExpectation,
    LanguageFluency,
    CandidateProfile,
    ScreeningQAItem,
    ScreeningQABase,
)
from careerpilot.models.job import (
    SourceChannel,
    ReviewDecision,
    ApplicationStage,
    JobPosting,
)


def test_candidate_profile_validation():
    profile = CandidateProfile(
        contact=CandidateContact(
            full_name="Somchai Techaprasert",
            email="somchai@example.com",
            location="Bangkok, Thailand",
        ),
        target_job_titles=["Senior Backend Engineer"],
        preferred_locations=["Bangkok", "Remote"],
        years_of_experience=8.0,
        compensation=CompensationExpectation(
            currency="THB",
            min_monthly_thb=120000,
            target_monthly_thb=150000,
        ),
        core_skills=["Python", "FastAPI", "Docker"],
    )
    assert profile.contact.full_name == "Somchai Techaprasert"
    assert profile.years_of_experience == 8.0
    assert "FastAPI" in profile.core_skills
    assert profile.compensation.min_monthly_thb == 120000


def test_screening_qa_matching():
    qa_base = ScreeningQABase(
        items=[
            ScreeningQAItem(
                id="leadership_style",
                category="leadership",
                question="What is your leadership style?",
                answer="Servant leadership with clear goals.",
                keywords=["leadership", "team lead", "mentorship"],
            ),
            ScreeningQAItem(
                id="notice_period",
                category="availability",
                question="What is your notice period?",
                answer="30 days.",
                keywords=["notice period", "availability"],
            ),
        ]
    )
    # Search by keyword
    result = qa_base.find_best_answer("Tell me about your team lead experience")
    assert result is not None
    assert result.id == "leadership_style"

    # Search by id
    result_id = qa_base.find_best_answer("What is notice_period?")
    assert result_id is not None
    assert result_id.id == "notice_period"


def test_job_posting_model():
    job = JobPosting(
        id="job_123",
        title="Senior Python Engineer",
        company="Agoda Services Co., Ltd.",
        source=SourceChannel.LINKEDIN,
        url="https://linkedin.com/jobs/view/123",
        location="Bangkok",
        salary_range="120k - 160k THB",
        match_score=88,
    )
    assert job.title == "Senior Python Engineer"
    assert job.source == SourceChannel.LINKEDIN
    assert job.review_decision == ReviewDecision.INBOX
    assert job.application_stage == ApplicationStage.UNAPPLIED
    assert job.match_score == 88
