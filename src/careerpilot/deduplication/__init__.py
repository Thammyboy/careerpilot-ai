"""Deduplication and normalization engine."""

from careerpilot.deduplication.normalizer import (
    normalize_company_name,
    normalize_job_title,
    generate_composite_hash,
    DeduplicationEngine,
)

__all__ = [
    "normalize_company_name",
    "normalize_job_title",
    "generate_composite_hash",
    "DeduplicationEngine",
]
