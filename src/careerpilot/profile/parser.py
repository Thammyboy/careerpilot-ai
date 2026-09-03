"""Parser utilities for candidate resumes (PDF/Markdown), metadata, and screening Q&A."""

import json
from pathlib import Path
from typing import Union
from pypdf import PdfReader

from careerpilot.models.profile import CandidateProfile, ScreeningQABase


class ProfileParseError(Exception):
    """Raised when parsing or validating profile artifacts fails."""
    pass


def parse_resume_pdf(pdf_path: Union[str, Path]) -> str:
    """Extract and normalize plain text from a candidate PDF resume."""
    path = Path(pdf_path)
    if not path.is_file():
        raise FileNotFoundError(f"Resume PDF not found: {path}")

    try:
        reader = PdfReader(str(path))
        extracted_pages = []
        for index, page in enumerate(reader.pages):
            text = page.extract_text()
            if text:
                extracted_pages.append(text.strip())
        return "\n\n".join(extracted_pages)
    except Exception as exc:
        raise ProfileParseError(f"Failed to extract text from PDF '{path}': {exc}") from exc


def parse_resume_markdown(md_path: Union[str, Path]) -> str:
    """Read and normalize markdown resume text."""
    path = Path(md_path)
    if not path.is_file():
        raise FileNotFoundError(f"Resume Markdown file not found: {path}")

    try:
        return path.read_text(encoding="utf-8").strip()
    except Exception as exc:
        raise ProfileParseError(f"Failed to read Markdown file '{path}': {exc}") from exc


def load_candidate_profile(json_path: Union[str, Path]) -> CandidateProfile:
    """Load and validate CandidateProfile metadata from a JSON file."""
    path = Path(json_path)
    if not path.is_file():
        raise FileNotFoundError(f"Candidate profile JSON not found: {path}")

    try:
        content = json.loads(path.read_text(encoding="utf-8"))
        return CandidateProfile.model_validate(content)
    except Exception as exc:
        raise ProfileParseError(f"Validation failed for candidate profile '{path}': {exc}") from exc


def load_screening_qa(json_path: Union[str, Path]) -> ScreeningQABase:
    """Load and validate ScreeningQABase questions and answers from a JSON file."""
    path = Path(json_path)
    if not path.is_file():
        raise FileNotFoundError(f"Screening QA JSON not found: {path}")

    try:
        content = json.loads(path.read_text(encoding="utf-8"))
        return ScreeningQABase.model_validate(content)
    except Exception as exc:
        raise ProfileParseError(f"Validation failed for screening QA '{path}': {exc}") from exc
