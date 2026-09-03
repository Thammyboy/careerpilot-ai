"""Tests for profile parser and context store."""

from pathlib import Path
import pytest
from careerpilot.profile.parser import (
    load_candidate_profile,
    load_screening_qa,
    parse_resume_markdown,
)
from careerpilot.profile.store import CandidateContextStore

PROFILE_DIR = Path("profile")


def test_load_sample_profile():
    sample_file = PROFILE_DIR / "sample_profile.json"
    assert sample_file.is_file(), "sample_profile.json must exist"
    profile = load_candidate_profile(sample_file)
    assert profile.contact.full_name == "Somchai Techaprasert"
    assert profile.years_of_experience > 5.0
    assert len(profile.core_skills) > 0
    assert profile.compensation.min_monthly_thb is not None


def test_load_sample_screening_qa():
    sample_qa_file = PROFILE_DIR / "sample_screening_qa.json"
    assert sample_qa_file.is_file(), "sample_screening_qa.json must exist"
    qa = load_screening_qa(sample_qa_file)
    assert len(qa.items) >= 4
    match = qa.find_best_answer("How do you handle conflict with teammates?")
    assert match is not None
    assert match.id == "conflict_resolution"


def test_parse_sample_resume_markdown():
    sample_cv = PROFILE_DIR / "sample_resume.md"
    assert sample_cv.is_file(), "sample_resume.md must exist"
    content = parse_resume_markdown(sample_cv)
    assert "Somchai Techaprasert" in content
    assert "Executive Summary" in content
    assert "Core Technical Competencies" in content


def test_parse_resume_pdf(tmp_path: Path):
    from pypdf import PdfWriter
    from careerpilot.profile.parser import parse_resume_pdf

    pdf_file = tmp_path / "test_cv.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    with open(pdf_file, "wb") as f:
        writer.write(f)

    # Blank page returns empty string without error
    extracted = parse_resume_pdf(pdf_file)
    assert isinstance(extracted, str)


def test_candidate_context_store():
    store = CandidateContextStore(profile_dir=PROFILE_DIR)
    store.load()

    assert store.profile.contact.full_name == "Somchai Techaprasert"
    assert len(store.resume_text) > 0
    assert len(store.screening_qa.items) >= 4

    keywords = store.get_search_keywords()
    assert len(keywords) > 0
    assert "Senior Software Engineer" in keywords

    locations = store.get_preferred_locations()
    assert "Bangkok" in locations
