"""Deduplication and text normalization utilities."""

import re
import json
import hashlib
from pathlib import Path
from typing import List, Tuple, Optional, Dict
from datetime import datetime, timezone, timedelta

from careerpilot.config import settings
from careerpilot.models.job import JobPosting


# Legal entities in English & Thai to strip for canonical company matching
LEGAL_AFFIXES = [
    r"\bpublic\s+company\s+limited\b",
    r"\bcompany\s+limited\b",
    r"\bco\.,?\s*ltd\.?\b",
    r"\bpublic\s+co(mpany)?\.?\s*ltd\.?\b",
    r"\bcorporation\b",
    r"\bcorp\.?\b",
    r"\binc\.?\b",
    r"\bltd\.?\b",
    r"\bllc\.?\b",
    r"\bpublic\b",
    r"\bgroup\b",
    r"\bholdings?\b",
    r"\(thailand\)",
    r"thailand",
    r"^บริษัท\s*",
    r"\s*จำกัด\s*\(มหาชน\)",
    r"\s*จำกัด",
    r"^บจก\.?\s*",
    r"^บมจ\.?\s*",
]

LEGAL_REGEX = re.compile("|".join(LEGAL_AFFIXES), re.IGNORECASE)


def normalize_company_name(name: str) -> str:
    """Standardize company name by removing legal affixes and excess symbols."""
    if not name:
        return ""
    cleaned = LEGAL_REGEX.sub(" ", name)
    cleaned = re.sub(r"[^\w\s\u0E00-\u0E7F]", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip().lower()
    return cleaned


LOCATION_PARENTHETICALS = re.compile(
    r"\s*[\(\[\{]\s*(?:bangkok|thailand|hybrid|remote|wfh|bkk|chonburi|rayong|full[\s\-]*time|contract)\s*[\)\]\}]",
    re.IGNORECASE,
)


def normalize_job_title(title: str) -> str:
    """Standardize job title by normalizing spacing, casing, and common separators."""
    if not title:
        return ""
    # Strip common location or work-mode parentheticals like (Bangkok), (Hybrid), (Remote)
    cleaned = LOCATION_PARENTHETICALS.sub(" ", title)
    # Replace remaining parentheses, brackets, slashes, dashes with space
    cleaned = re.sub(r"[\(\)\[\]\{\}\-/\\|–—:,]", " ", cleaned)
    cleaned = re.sub(r"[^\w\s\u0E00-\u0E7F]", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip().lower()
    return cleaned


def generate_composite_hash(company: str, title: str, identifier: Optional[str] = None) -> str:
    """
    Generate composite hash for deduplication:
    hash(normalized_company_name, normalized_title, external_id_or_ref)
    """
    norm_comp = normalize_company_name(company)
    norm_title = normalize_job_title(title)
    clean_id = (identifier or "").strip().lower()
    key = f"{norm_comp}|{norm_title}|{clean_id}"
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]


class DeduplicationEngine:
    """Stateful deduplication engine tracking seen job postings over a sliding window (default: 90 days)."""

    def __init__(
        self,
        storage_file: Optional[Path] = None,
        window_days: Optional[int] = None,
    ):
        self.storage_file = storage_file or (settings.storage_dir / "seen_jobs.json")
        self.window_days = window_days or settings.deduplication_window_days
        self._seen_cache: Dict[str, str] = {}  # hash -> ISO timestamp
        self._load()

    def _load(self) -> None:
        """Load seen hashes from disk."""
        if not self.storage_file.is_file():
            self._seen_cache = {}
            return

        try:
            data = json.loads(self.storage_file.read_text(encoding="utf-8"))
            cutoff = datetime.now(timezone.utc) - timedelta(days=self.window_days)

            # Filter out entries older than the window
            filtered = {}
            for h, ts in data.items():
                try:
                    dt = datetime.fromisoformat(ts)
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                    if dt >= cutoff:
                        filtered[h] = ts
                except Exception:
                    filtered[h] = ts
            self._seen_cache = filtered
        except Exception:
            self._seen_cache = {}

    def _save(self) -> None:
        """Persist seen hashes to disk."""
        self.storage_file.parent.mkdir(parents=True, exist_ok=True)
        self.storage_file.write_text(
            json.dumps(self._seen_cache, indent=2),
            encoding="utf-8"
        )

    def is_seen(self, composite_hash: str) -> bool:
        """Check whether the job hash is currently recognized as seen within the window."""
        return composite_hash in self._seen_cache

    def mark_seen(self, composite_hash: str) -> None:
        """Record a hash as seen at the current time."""
        self._seen_cache[composite_hash] = datetime.now(timezone.utc).isoformat()

    def process(self, jobs: List[JobPosting]) -> Tuple[List[JobPosting], List[JobPosting]]:
        """
        Process a list of job postings:
        - Computes composite hash if absent
        - Drops duplicates within the same batch
        - Drops postings already seen in prior 90 days
        - Returns (new_unique_jobs, dropped_duplicate_jobs)
        """
        unique_jobs: List[JobPosting] = []
        dropped_jobs: List[JobPosting] = []
        batch_hashes = set()

        for job in jobs:
            ref = job.agency_ref_id or job.external_id or job.url
            comp_hash = generate_composite_hash(job.company, job.title, ref)
            job.composite_hash = comp_hash
            if not job.id:
                job.id = comp_hash

            if comp_hash in batch_hashes or self.is_seen(comp_hash):
                dropped_jobs.append(job)
            else:
                batch_hashes.add(comp_hash)
                self.mark_seen(comp_hash)
                unique_jobs.append(job)

        # Persist updated state
        self._save()
        return unique_jobs, dropped_jobs
