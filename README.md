# CareerPilot AI

> **Intelligent Job Intelligence & Application Copilot**  
> *Target Markets: Thailand & Southeast Asia (English & Thai support)*

CareerPilot AI is an engineered career workflow automation engine designed to replace brute-force spamming with high-signal semantic discovery.

---

## Architecture Overview (Phase 1)

```
 ┌────────────────────────────────────────────────────────┐
 │           Local Context Store (/profile)               │
 │  Resume (PDF/MD) • Screening QA • Preferences JSON     │
 └───────────────────────────┬────────────────────────────┘
                             │
                             ▼
 ┌────────────────────────────────────────────────────────┐
 │             Multi-Source Aggregation Engine            │
 │     • LinkedIn (Public Guest API)                      │
 │     • JobsDB Thailand (SEEK HTML / SSR Cards)          │
 │     • JobThai (Direct GraphQL Endpoint)                │
 └───────────────────────────┬────────────────────────────┘
                             │
                             ▼
 ┌────────────────────────────────────────────────────────┐
 │                 Deduplication Engine                   │
 │   Composite Hash (Company + Title + Ref ID) • 90-Day   │
 └───────────────────────────┬────────────────────────────┘
                             │
                             ▼
 ┌────────────────────────────────────────────────────────┐
 │           Notion Control Center & Sync Pipeline        │
 │  11-Field Schema Mapping • Dry-Run & Live REST Sync    │
 └────────────────────────────────────────────────────────┘
```

---

## Features (Phase 1: Ingestion & Primary Scraping)

1. **Candidate Context Store (`/profile`)**:
   - Pydantic-validated career metadata (`profile.json`) with compensation expectations in THB/USD, language proficiencies, and notice period.
   - Master CV parser for both **Markdown** (`.md`) and **PDF** (`.pdf`) using `pypdf`.
   - Canonical vetting Q&A store (`screening_qa.json`) with keyword matching for zero-hallucination screening responses.
   - Strict PII shielding: `.gitignore` protects personal data while tracking sanitized templates (`sample_profile.json`, `sample_resume.md`, `sample_screening_qa.json`).

2. **Primary Portal Scrapers**:
   - **LinkedIn**: Public guest search endpoint with pagination support and metadata extraction.
   - **JobsDB Thailand**: Parses SEEK article cards, job IDs, salaries, classifications, and locations.
   - **JobThai**: Direct integration with JobThai's GraphQL API (`https://api.jobthai.com/v1/graphql`) for fast, structured extraction.
   - Resilient base with jitter delays (2.0s–6.5s) and exponential backoff on rate limits.

3. **Deduplication Engine**:
   - Company name normalizer stripping legal entities (English & Thai: `Co., Ltd.`, `Public Company Limited`, `บริษัท...จำกัด`).
   - Title normalizer cleaning punctuation and location parentheticals.
   - SHA256 composite hashing with a 90-day sliding window persisted in `storage/seen_jobs.json`.

4. **Notion Database Integration**:
   - Conforms to the 11-field PRD database schema (`Job Title`, `Company / Client`, `Source Channel`, `Agency Reference ID`, `Match Score`, `Location`, `Salary Range`, `Posting URL`, `Review Decision`, `Application Stage`, page body blocks).
   - Automatic schema detection & provisioning for empty Notion databases.
   - Duplicate prevention by checking existing URLs in Notion.
   - Safe `--dry-run` mode for local preview without requiring API keys.

---

## Installation & Setup

### 1. Prerequisites
- Python 3.11+ (Tested on Python 3.13)

### 2. Create & Activate Virtual Environment
Create an isolated Python virtual environment to manage dependencies cleanly:

**Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**Windows (Command Prompt):**
```cmd
python -m venv .venv
.\.venv\Scripts\activate.bat
```

**macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
With the virtual environment activated, install the package in editable mode with development tooling:
```bash
pip install -e ".[dev]"
```

### 4. Configure Environment
Copy the example environment file:
```bash
cp .env.example .env
```
Fill in your `NOTION_API_KEY` and `NOTION_DATABASE_ID` if you want live sync to Notion.

> [!IMPORTANT]
> **Notion Database Requirements:**
> - **Use a brand-new, empty Notion database.** Create a new database in Notion and copy its Database ID into `NOTION_DATABASE_ID`.
> - **Do NOT use an already filled database** or one with pre-existing custom columns. Notion enforces strict schema validation and will reject page creation if property names or types differ from what the pipeline expects.
> - **Automatic Schema Provisioning:** CareerPilot AI automatically detects when the database is empty and configures all required columns (`Job Title`, `Company / Client`, `Source Channel`, `Posting URL`, `Location`, `Salary Range`, `Agency Reference ID`, `Match Score`, `Review Decision`, and `Application Stage`).
> - **Share with Integration:** Remember to invite/connect your Notion Integration to the new database in Notion (click `•••` -> `Connections` -> add your integration).

### 5. Configure Candidate Profile
CareerPilot AI separates **unstructured resume text** (`profile/master_cv.pdf` or `profile/master_cv.md`) from **structured search metadata** (`profile/profile.json` — target roles, desired salary, notice period).

#### Automatic Setup (Recommended):
Place your resume PDF into the `profile/` folder as `master_cv.pdf`, then run:
```bash
careerpilot profile init
```
This automatically parses your resume, extracts your contact details (name, email, phone, social profiles), creates `profile/profile.json`, and sets up `profile/screening_qa.json`.

#### Manual Setup:
Alternatively, copy the sample templates to create your files manually:
```bash
cp profile/sample_profile.json profile/profile.json
cp profile/sample_screening_qa.json profile/screening_qa.json
cp profile/sample_resume.md profile/master_cv.md
```

---

## CLI Usage

### Check Candidate Profile
Inspect your active profile metadata, verify loaded screening Q&As, and view a live text preview of your parsed resume:
```bash
careerpilot profile check
```

### Initialize Profile from Resume
Automatically extract contact info from `profile/master_cv.pdf` or `profile/master_cv.md` to initialize `profile/profile.json`:
```bash
careerpilot profile init

# Use --force to overwrite an existing profile.json
careerpilot profile init --force
```

### Run Scrapers
Scrape opportunities across portals and save deduplicated listings to `storage/latest_jobs.json`:
```bash
# Scrape all supported sources
careerpilot scrape --keywords "Senior Software Engineer" --location "Bangkok" --limit 15

# Scrape a specific source (linkedin, jobsdb, jobthai)
careerpilot scrape --source jobsdb --keywords "Python Developer" --limit 10
careerpilot scrape --source jobthai --keywords "Tech Lead" --limit 10
careerpilot scrape --source linkedin --keywords "Backend Engineer" --limit 10
```

### Sync to Notion
Sync scraped listings into your Notion database (or use `--dry-run` to preview):
```bash
# Dry-run preview
careerpilot sync --input storage/latest_jobs.json --dry-run

# Live Notion sync
careerpilot sync --input storage/latest_jobs.json
```

### Full End-to-End Pipeline
Run the complete Phase 1 pipeline (loads target roles from profile -> scrapes 3 portals -> deduplicates -> syncs to Notion):
```bash
# Dry run
careerpilot run --limit 10 --dry-run

# Live run
careerpilot run --limit 20
```

---

## Running Tests

Run the complete pytest test suite:
```bash
pytest -v
```

---

## Roadmap

- [x] **Phase 1: Ingestion & Primary Scraping (Weeks 1–2)**
  - Local profile parser for PDF/Markdown.
  - Scrapers for LinkedIn, JobsDB, and JobThai.
  - Establish Notion database schema and sync pipeline.
- [ ] **Phase 2: Agency Aggregation & Deduplication (Weeks 3–4)**
  - Dedicated crawlers for Adecco, ManpowerGroup, PRTR, Robert Walters, and JAC Recruitment.
- [ ] **Phase 3: Semantic Scoring & Curated Top 50 Batch (Weeks 5–6)**
  - LLM role fit scoring (0–100%) and daily top 50 prioritization.
- [ ] **Phase 4: Application Copilot & Human-in-the-Loop Assist (Weeks 7–8)**
  - Tailored dossier generator and semi-automated application submission.