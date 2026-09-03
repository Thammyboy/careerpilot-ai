# CareerPilot AI — Agent Guidelines & Instructions

This repository defines strict operational rules for AI coding assistants working on **CareerPilot AI**.

---

## 🚨 Mandatory Rule: Always Document Changes

**Whenever you make code changes, modifications, additions, or deletions in this repository, you MUST document them before concluding your turn.**

### 1. Update User-Facing Documentation Immediately
- If you add or modify a **CLI command, argument, or flag**, update:
  - [`README.md`](README.md) under **CLI Usage**
  - Any relevant subcommand help text
- If you change **configuration options, environment variables, or paths**, update:
  - [`.env.example`](.env.example)
  - [`README.md`](README.md) under **Installation & Setup**
- If you modify the **candidate context store or profile structure**, update:
  - [`profile/README.md`](profile/README.md)
  - Sample templates (`sample_profile.json`, etc.)

### 2. Update `CHANGELOG.md`
For every meaningful change:
- Open [`CHANGELOG.md`](CHANGELOG.md).
- Under the `[Unreleased]` section (or the current milestone version), add a bullet point classifying the change under:
  - `### Added` for new features or commands
  - `### Changed` for changes in existing functionality
  - `### Fixed` for bug fixes
  - `### Documentation` for documentation additions
  - `### Security` for PII shielding or secret updates

### 3. Maintain Documentation Integrity
- Never leave code changes undocumented.
- Code changes, tests, and documentation updates must be delivered together in the same workflow.
- Ensure all example commands in documentation are tested and executable.

---

## Technical Guardrails

1. **Strict PII & Secret Shielding**:
   - Never commit private candidate data (`profile/master_cv.pdf`, `profile/profile.json`, `profile/screening_qa.json`, `.env`).
   - Only sanitized `sample_*` templates in `profile/` may be tracked in git.
   - Verify `.gitignore` before adding new files.

2. **Virtual Environment Testing**:
   - Always run tests (`pytest -v`) using the virtual environment (`.venv`).
   - Ensure all automated tests pass before concluding tasks.

3. **Polite Automation Philosophy (PRD Compliance)**:
   - All scrapers must implement rate limiting with jitter (2.0s–6.5s) and exponential backoff.
   - Zero spam: human confirmation and deduplication are mandatory.
