# Candidate Context Store (`/profile`)

This directory holds the private candidate artifacts used by CareerPilot AI.

## Security & Privacy
Per the PRD (Section 7), all personal CVs and confidential metadata in this folder are **git-ignored** (`.gitignore`). Only the `sample_*` template files are committed to source control for demonstration and testing.

## Files
1. `profile.json` (or `sample_profile.json`): Structured career metadata (contact info, target titles, notice period, compensation expectations, language fluency, work authorization).
2. `master_cv.md` or `master_cv.pdf` (or `sample_resume.md`): The comprehensive master CV / resume.
3. `screening_qa.json` (or `sample_screening_qa.json`): Canonical vetted answers to recurring screening questions (leadership, system design, salary justification, conflict resolution).

## Quick Setup
To use your own profile, copy the sample files:
```bash
cp profile/sample_profile.json profile/profile.json
cp profile/sample_screening_qa.json profile/screening_qa.json
cp profile/sample_resume.md profile/master_cv.md
```
Then customize with your personal information!
