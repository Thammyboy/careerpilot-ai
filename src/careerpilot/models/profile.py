"""Candidate profile and screening Q&A models."""

from typing import List, Optional, Dict
from pydantic import BaseModel, Field, EmailStr


class CandidateContact(BaseModel):
    """Candidate contact and links."""
    full_name: str = Field(..., description="Full legal name")
    email: EmailStr = Field(..., description="Primary contact email")
    phone: Optional[str] = Field(default=None, description="Contact phone number")
    location: str = Field(..., description="Current residence location (e.g., Bangkok, Thailand)")
    linkedin_url: Optional[str] = Field(default=None, description="LinkedIn profile URL")
    github_url: Optional[str] = Field(default=None, description="GitHub profile URL")
    portfolio_url: Optional[str] = Field(default=None, description="Personal site or portfolio")


class CompensationExpectation(BaseModel):
    """Salary expectations in THB and/or USD."""
    currency: str = Field(default="THB", description="Primary preferred currency (THB, USD)")
    min_monthly_thb: Optional[int] = Field(default=None, description="Minimum acceptable monthly salary in THB")
    target_monthly_thb: Optional[int] = Field(default=None, description="Target desirable monthly salary in THB")
    min_annual_usd: Optional[int] = Field(default=None, description="Minimum acceptable annual salary in USD")
    target_annual_usd: Optional[int] = Field(default=None, description="Target desirable annual salary in USD")
    negotiable: bool = Field(default=True, description="Whether compensation is negotiable")


class LanguageFluency(BaseModel):
    """Language proficiency indicators."""
    language: str = Field(..., description="Language name, e.g., English or Thai")
    proficiency: str = Field(
        ..., description="Proficiency level: Native, Bilingual, Fluent, Professional, Intermediate"
    )
    test_score: Optional[str] = Field(
        default=None, description="Standardized score if available (TOEIC, IELTS, etc.)"
    )


class CandidateProfile(BaseModel):
    """Master structured profile metadata from profile.json."""
    contact: CandidateContact
    target_job_titles: List[str] = Field(
        default_factory=list, description="Target job roles (e.g., ['Senior Software Engineer', 'Lead Backend Engineer'])"
    )
    preferred_locations: List[str] = Field(
        default_factory=lambda: ["Bangkok", "Remote", "Hybrid"],
        description="Target locations or work modes"
    )
    years_of_experience: float = Field(..., description="Total professional experience in years")
    notice_period: str = Field(
        default="30 days", description="Notice period (e.g., 'Immediate', '30 days', '60 days')"
    )
    work_authorization: str = Field(
        default="Thai Citizen", description="Work permit status (e.g., 'Thai Citizen', 'Eligible for BOI Smart Visa')"
    )
    compensation: CompensationExpectation
    languages: List[LanguageFluency] = Field(default_factory=list)
    core_skills: List[str] = Field(default_factory=list, description="Primary technical skills & domains")
    secondary_skills: List[str] = Field(default_factory=list, description="Secondary or familiar tools")
    professional_summary: Optional[str] = Field(default=None, description="Concise professional summary")


class ScreeningQAItem(BaseModel):
    """Canonical answer to a recurring vetting or application question."""
    id: str = Field(..., description="Unique slug for the question (e.g., 'leadership_style')")
    category: str = Field(
        default="general",
        description="Category: leadership, architecture, teamwork, conflict_resolution, motivation"
    )
    question: str = Field(..., description="Typical question wording")
    answer: str = Field(..., description="Verified canonical factual response")
    keywords: List[str] = Field(default_factory=list, description="Matching triggers or keywords")


class ScreeningQABase(BaseModel):
    """Collection of canonical screening answers."""
    items: List[ScreeningQAItem] = Field(default_factory=list)

    def find_best_answer(self, query: str) -> Optional[ScreeningQAItem]:
        """Find the most relevant screening answer by keyword matching."""
        query_lower = query.lower()
        # Direct keyword match
        for item in self.items:
            if any(k.lower() in query_lower for k in item.keywords):
                return item
            if item.id.lower() in query_lower:
                return item
        return None
