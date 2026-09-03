# Changelog

All notable changes to the **CareerPilot AI** project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- **Notion Database Auto-Configuration**: Detects empty Notion databases (0 records with default single title property) and automatically provisions all required PRD columns (`Job Title`, `Company / Client`, `Source Channel`, `Posting URL`, `Location`, `Salary Range`, `Agency Reference ID`, `Match Score`, `Review Decision`, and `Application Stage`).
- Unit tests for Notion empty check (`is_database_empty`), schema configuration (`setup_database_schema`), and auto-provision trigger (`ensure_schema`) in `tests/test_notion_sync.py`.

### Changed
- Pinned Notion client API version explicitly to `2022-06-28` for stable database schema update operations across client environments.
- Enhanced CLI `sync` and `run` commands to display live status notifications when an empty Notion database is detected and configured.

### Fixed
- Fixed `AttributeError: 'DatabasesEndpoint' object has no attribute 'query'` when using newer `notion-client` releases by implementing `_query_database` with backward and forward compatibility (falling back to direct `client.request` on `databases/{id}/query`).
- Fixed schema provisioning on modern Notion databases containing `data_sources` by updating properties directly on the underlying data source (`data_sources.update`), resolving `ValidationError: Job Title is not a property that exists` on initial page creation.

### Documentation
- Updated `README.md` with explicit instructions to supply the Database ID of a brand-new, empty database and a caution against using pre-filled or schema-mismatched databases.
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
