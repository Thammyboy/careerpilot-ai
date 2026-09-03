---
name: document-changes
description: Use whenever code changes, refactors, or new features have been implemented to ensure README, CHANGELOG, and relevant documentation files are completely up to date.
---

# Change Documentation Workflow

This skill ensures that whenever changes are made to the **CareerPilot AI** codebase, documentation is updated immediately.

## Workflow

1. **Audit Unstaged and Staged Changes**:
   ```bash
   git status -s
   git diff --stat
   ```
   Identify which files were modified, created, or deleted.

2. **Determine Documentation Impact**:
   - **CLI / Commands changed?**
     - Update [`README.md`](file:///d:/personal-projects/careerpilot-ai/README.md) under `## CLI Usage`.
     - Update command help strings in `src/careerpilot/cli.py`.
   - **Configuration / Settings changed?**
     - Update [`.env.example`](file:///d:/personal-projects/careerpilot-ai/.env.example).
     - Update [`README.md`](file:///d:/personal-projects/careerpilot-ai/README.md) under `### Configure Environment`.
   - **Profile / Context Store changed?**
     - Update [`profile/README.md`](file:///d:/personal-projects/careerpilot-ai/profile/README.md).
     - Update sample templates in `profile/` if schemas evolved.
   - **Models / Scrapers / Logic changed?**
     - Update [`CHANGELOG.md`](file:///d:/personal-projects/careerpilot-ai/CHANGELOG.md).

3. **Update `CHANGELOG.md`**:
   Add an entry under `## [Unreleased]` using Keep a Changelog formatting:
   - `### Added`: New features, commands, flags.
   - `### Changed`: Modifications to existing behavior.
   - `### Fixed`: Bug fixes.
   - `### Security`: Changes affecting PII or security boundaries.

4. **Verify Documentation Accuracy**:
   - Check line numbers and file paths referenced in markdown.
   - Ensure all code snippets and command lines run without error.
