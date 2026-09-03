"""Candidate Context Store managing profile metadata, resumes, and vetting Q&A."""

from pathlib import Path
from typing import Optional, List, Union

from careerpilot.config import settings
from careerpilot.models.profile import CandidateProfile, ScreeningQABase, ScreeningQAItem
from careerpilot.profile.parser import (
    parse_resume_pdf,
    parse_resume_markdown,
    load_candidate_profile,
    load_screening_qa,
)


class CandidateContextStore:
    """Central store for candidate artifacts with automatic fallback to sample templates."""

    def __init__(self, profile_dir: Optional[Union[str, Path]] = None):
        self.profile_dir = Path(profile_dir or settings.profile_dir)
        self._profile: Optional[CandidateProfile] = None
        self._resume_text: Optional[str] = None
        self._screening_qa: Optional[ScreeningQABase] = None
        self._resume_source_file: Optional[Path] = None

    def load(self) -> "CandidateContextStore":
        """Load all artifacts from directory, falling back to sample files if private files are absent."""
        self.load_profile()
        self.load_resume()
        self.load_screening_qa()
        return self

    def load_profile(self) -> CandidateProfile:
        """Load candidate metadata from profile.json (or sample_profile.json)."""
        candidate_file = self.profile_dir / "profile.json"
        sample_file = self.profile_dir / "sample_profile.json"

        target_file = candidate_file if candidate_file.is_file() else sample_file
        if not target_file.is_file():
            raise FileNotFoundError(
                f"No candidate profile found. Neither '{candidate_file}' nor '{sample_file}' exists."
            )

        self._profile = load_candidate_profile(target_file)
        return self._profile

    def load_resume(self) -> str:
        """Load resume text from master_cv.pdf, master_cv.md (or sample_resume.md)."""
        candidates = [
            self.profile_dir / "master_cv.pdf",
            self.profile_dir / "master_cv.md",
            self.profile_dir / "sample_resume.md",
        ]

        target_file = next((f for f in candidates if f.is_file()), None)
        if not target_file:
            raise FileNotFoundError(
                f"No CV or resume found in '{self.profile_dir}'. Expected master_cv.pdf/md or sample_resume.md."
            )

        if target_file.suffix.lower() == ".pdf":
            self._resume_text = parse_resume_pdf(target_file)
        else:
            self._resume_text = parse_resume_markdown(target_file)

        self._resume_source_file = target_file
        return self._resume_text

    def load_screening_qa(self) -> ScreeningQABase:
        """Load screening Q&A from screening_qa.json (or sample_screening_qa.json)."""
        qa_file = self.profile_dir / "screening_qa.json"
        sample_file = self.profile_dir / "sample_screening_qa.json"

        target_file = qa_file if qa_file.is_file() else sample_file
        if not target_file.is_file():
            raise FileNotFoundError(
                f"No screening QA found. Neither '{qa_file}' nor '{sample_file}' exists."
            )

        self._screening_qa = load_screening_qa(target_file)
        return self._screening_qa

    @property
    def profile(self) -> CandidateProfile:
        """Get the loaded CandidateProfile."""
        if self._profile is None:
            self.load_profile()
        return self._profile  # type: ignore

    @property
    def resume_text(self) -> str:
        """Get the extracted resume text."""
        if self._resume_text is None:
            self.load_resume()
        return self._resume_text  # type: ignore

    @property
    def screening_qa(self) -> ScreeningQABase:
        """Get the loaded screening Q&A items."""
        if self._screening_qa is None:
            self.load_screening_qa()
        return self._screening_qa  # type: ignore

    @property
    def resume_source_file(self) -> Optional[Path]:
        """Path of the file from which resume text was loaded."""
        return self._resume_source_file

    def get_search_keywords(self) -> List[str]:
        """Return candidate target job titles as search keywords."""
        if self.profile.target_job_titles:
            return self.profile.target_job_titles
        return [settings.default_search_keywords]

    def get_preferred_locations(self) -> List[str]:
        """Return candidate preferred locations."""
        if self.profile.preferred_locations:
            return self.profile.preferred_locations
        return [settings.default_search_location]

    def answer_vetting_question(self, question: str) -> Optional[ScreeningQAItem]:
        """Query canonical answer database for a vetting question."""
        return self.screening_qa.find_best_answer(question)
