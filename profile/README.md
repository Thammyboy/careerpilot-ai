# Candidate Context Store (`/profile`)

This directory holds the private candidate artifacts used by CareerPilot AI.

## Security & Privacy
Per the PRD (Section 7), all personal CVs and confidential metadata in this folder are **git-ignored** (`.gitignore`). Only the `sample_*` template files are committed to source control for demonstration and testing.

## Files Structure & Architecture
CareerPilot AI separates **unstructured resume text** from **structured job search preferences**:

1. **Master CV (`master_cv.pdf` or `master_cv.md`)**:
   - The primary resume document containing full work history, achievements, and education.
   - Extracted automatically via `pypdf` (for PDF) or markdown parser.
   - Used for zero-hallucination context injection, semantic fit scoring, and dossier generation.
2. **Career Metadata (`profile.json`)**:
   - Structured JSON parameters used for opportunity search filtering:
     - Contact details (name, email, phone, LinkedIn, GitHub)
     - `target_job_titles`: Roles to search for across LinkedIn, JobsDB, JobThai.
     - `preferred_locations`: Geographic targeting (e.g. `["Bangkok", "Hybrid", "Remote"]`).
     - `compensation`: Minimum and target monthly salary expectations in THB/USD.
     - `notice_period` & `work_authorization`.
3. **Screening Knowledge Base (`screening_qa.json`)**:
   - Canonical, verified answers to recurring recruiter vetting questions (leadership, system design, salary justification, conflict resolution).

---

## Setup Options

### Option A: Automatic Initialization from Your Resume (Recommended)
Place your resume PDF into this folder as `master_cv.pdf`, then run:
```bash
careerpilot profile init
```
This will automatically:
- Parse `master_cv.pdf` using `pypdf`.
- Extract your name, email, phone number, and social links.
- Create your personal `profile.json` prefilled with your extracted contact info.
- Create `screening_qa.json` from canonical templates.

### Option B: Manual Setup from Sample Templates
Copy the sample templates:
```bash
cp profile/sample_profile.json profile/profile.json
cp profile/sample_screening_qa.json profile/screening_qa.json
cp profile/sample_resume.md profile/master_cv.md
```
Then customize `profile/profile.json` with your desired target roles, salary, and notice period!

---

## Verification
Inspect your active profile and view a live text preview of your parsed resume:
```bash
careerpilot profile check
```
