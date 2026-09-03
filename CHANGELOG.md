# Changelog

All notable changes to the **CareerPilot AI** project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Changed
- Refactored project positioning, PRD documentation, and guidelines to remove all "recruiter-friendly" phrasing in favor of standard production engineering terminology.

---

## [0.1.0] - 2026-09-03

### Added
- **Phase 1 Implementation**: Candidate Context Store, primary scraping engine, deduplication, and Notion database integration per PRD specifications.
- **Candidate Context Store (`profile/`)**:
  - Pydantic models for candidate metadata, compensation expectations, language fluency, and canonical screening Q&A (`src/careerpilot/models/profile.py`).
  - Resume parser for PDF (`pypdf`) and Markdown (`src/careerpilot/profile/parser.py`).
  - CandidateContextStore with fallback to sample data (`src/careerpilot/profile/store.py`).
  - Sanitized demonstration templates (`sample_profile.json`, `sample_resume.md`, `sample_screening_qa.json`).
- **Primary Job Scrapers (`src/careerpilot/scrapers/`)**:
  - `JobThaiScraper`: Direct GraphQL client for `api.jobthai.com/v1/graphql`.
  - `JobsDBScraper`: HTML/SSR article card extractor for `th.jobsdb.com`.
  - `LinkedInScraper`: Public guest search extractor with pagination.
  - `BaseScraper`: Jittered delays (2.0s–6.5s) and exponential backoff retry.
  - `AggregationEngine`: Multi-source scraping runner with persistence to `storage/latest_jobs.json`.
- **Deduplication Engine (`src/careerpilot/deduplication/`)**:
  - Text normalizers for company names (English and Thai legal affixes) and titles.
  - SHA256 composite hashing with a 90-day tracking window in `storage/seen_jobs.json`.
- **Notion Database Integration (`src/careerpilot/notion/`)**:
  - Exact 11-field schema mapping conforming to PRD Section 5.4.
  - Deduplication via URL check in database.
  - Safe `--dry-run` execution mode.
- **CLI Commands (`careerpilot`)**:
  - `careerpilot profile check`: Validates profile, active vs. fallback template detection, and live resume text preview.
  - `careerpilot profile init`: Automatically extracts contact info from `master_cv.pdf` and writes personal `profile.json`.
  - `careerpilot scrape`: Runs scrapers with source and keyword filters.
  - `careerpilot sync`: Syncs local jobs JSON to Notion database.
  - `careerpilot run`: Full end-to-end ingestion and sync pipeline.
- **Virtual Environment & Hygiene**:
  - Setup and activation instructions in `.venv` across Windows and macOS/Linux.
  - PII security shielding in `.gitignore` and template `.env.example`.
  - 17 automated tests in `tests/` covering models, parsers, deduplication, scrapers, and Notion mappers.
