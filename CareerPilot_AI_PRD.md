# Product Requirements Document (PRD)

## Project: CareerPilot AI – Intelligent Job Intelligence & Application Copilot
**Target Markets:** Thailand & Regional Southeast Asia (English & Thai support)  
**Document Version:** 2.0   
**Product Positioning:** Intelligent Career Workflow Automation & Semantic Opportunity Matching Engine

---

## 1. Executive Summary & Philosophy

### 1.1 The Problem
High-performing professionals spend 15–20 hours weekly navigating fragmented recruitment portals, agency listings, and corporate boards. Traditional search lacks nuanced semantic matching against a candidate’s granular technical competencies and career trajectory. Conversely, automated "spray-and-pray" bots undermine candidate credibility, burden talent acquisition teams with unqualified noise, and frequently lead to platform account bans.

### 1.2 The Solution
**CareerPilot AI** is an intelligent, high-precision job discovery and application workflow copilot. It models career progression as an engineered pipeline:
1. Aggregates listings across regional portals and premier tier-1 recruitment agencies.
2. Applies semantic ranking and profile fit scoring based on structured resume metadata.
3. Surfaces a curated daily feed of exactly 50 deduplicated, high-relevance opportunities.
4. Provides a human-in-the-loop review interface inside Notion.
5. Offers guided, human-verified application assistance (pre-filling screening questionnaires and generating tailored context briefs) without blind mass-spamming.

---

## 2. Core Value Pillars & Design Principles

| Pillar | Principle | Recruiter Benefit | Candidate Benefit |
| :--- | :--- | :--- | :--- |
| **High Signal, Zero Spam** | Quality over brute force | Recruiters receive carefully reviewed, highly aligned submissions. | Candidate preserves professional reputation and brand. |
| **Human-in-the-Loop** | Explicit confirmation required | Every submission is intentionally verified by the applicant. | No unintended submissions or mismatched applications. |
| **Bespoke Localization** | Tailored for Thailand's market | Integrates both multinational portals and premier Thai headhunting firms. | Unlocks unlisted and agency-exclusive enterprise mandates. |
| **Contextual Integrity** | Grounded LLM generation | Answers are strictly factual and derived from verified candidate experience. | Eliminates hallucinations or exaggerated credentials. |

---

## 3. Supported Sources & Search Aggregation Matrix

The system continuously indexes, deduplicates, and standardizes job postings from 8 core channels across public boards and executive recruitment agencies:

| Channel Category | Target Platforms | Primary Data Extractors | Regional Focus |
| :--- | :--- | :--- | :--- |
| **Global & Regional Boards** | • LinkedIn Jobs<br>• JobsDB Thailand (SEEK API/Web)<br>• JobThai | Public feeds, structured JSON-LD, session-safe scrapers | Thailand & APAC Remote |
| **Tier-1 Executive & Tech Recruiters** | • **Adecco Thailand**<br>• **ManpowerGroup Thailand**<br>• **PRTR Recruitment**<br>• **Robert Walters Thailand**<br>• **JAC Recruitment Thailand** | Agency search portal scrapers, RSS / XML endpoints, Career site DOM parsers | Bangkok, Eastern Seaboard (EEC), Regional SEA |

---

## 4. System Architecture & End-to-End Workflow

```
 ┌────────────────────────────────────────────────────────┐
 │           Local Context Store (/profile)               │
 │  Resume (PDF/MD) • Screening QA • Preferences JSON     │
 └───────────────────────────┬────────────────────────────┘
                             │
                             ▼
 ┌────────────────────────────────────────────────────────┐
 │             Multi-Source Aggregation Engine            │
 │  LinkedIn • JobsDB • JobThai • Adecco • ManpowerGroup  │
 │     PRTR • Robert Walters Thailand • JAC Recruitment   │
 └───────────────────────────┬────────────────────────────┘
                             │
                             ▼
 ┌────────────────────────────────────────────────────────┐
 │       Semantic Evaluation & Match Scoring Engine       │
 │   Role Fit (0-100%) • Tech Stack Match • Deduplication │
 └───────────────────────────┬────────────────────────────┘
                             │
                             ▼
 ┌────────────────────────────────────────────────────────┐
 │            Notion Daily Review Queue (50 Jobs)         │
 │   User sets Decision: [ Approved | Declined | Saved ]  │
 └───────────────────────────┬────────────────────────────┘
                             │
            ┌────────────────┴────────────────┐
            ▼                                 ▼
 ┌──────────────────────┐         ┌─────────────────────────┐
 │ Standard Direct Flow │         │  Complex ATS / Agency   │
 │ Semi-automated apply │         │  Generates tailored     │
 │ with field matching  │         │  dossier & 1-click link │
 └──────────┬───────────┘         └────────────┬────────────┘
            │                                  │
            ▼                                  ▼
 ┌────────────────────────────────────────────────────────┐
 │        Notion Job Tracker & Execution Auditing         │
 │   Status Update • Audit Logs • Notification Dispatch   │
 └────────────────────────────────────────────────────────┘
```

---

## 5. Detailed Functional Specifications

### 5.1 Module 1: Candidate Context Store & Profile Engine
* **Location:** Dedicated `/profile` directory (git-ignored for security).
* **Ingested Artifacts:**
  * Master Curriculum Vitae (`master_cv.pdf` / `master_cv.md`)
  * Structured Career Metadata (`profile.json`): Contact info, target titles, notice period, compensation expectations (THB/USD), English & Thai fluency scores, work authorization status.
  * Answer Knowledge Base (`screening_qa.json`): Canonical responses to recurring vetting questions (e.g., leadership philosophy, technical architecture achievements, conflict resolution).
* **Embedding & Retrieval:** Builds an in-memory vector index of profile milestones for zero-hallucination semantic context injection.

### 5.2 Module 2: Scraping, Aggregation & Agency Crawlers
* **Execution Schedule:** Daily at 06:00 AM ICT via automated runner (Codespaces, Cron, or Docker container).
* **Scraping Strategies:**
  * **Direct Feed / Metadata Parsing:** Extracts schema.org `JobPosting` JSON-LD where available.
  * **Headless Browser Execution (Playwright):** Interacts with dynamic agency portals (Robert Walters, PRTR, Adecco, JAC, Manpower).
* **Agency-Specific Normalization:**
  * Identifies Agency Reference Codes (e.g., Robert Walters Job Ref IDs, PRTR consultant codes).
  * Normalizes salary representations (monthly vs. annual THB rates).
* **Deduplication Engine:**
  * Generates a composite hash based on `(normalized_company_name, normalized_title, agency_ref_id)`.
  * Drops any listing reviewed within the prior 90 days.

### 5.3 Module 3: Semantic Evaluation & Ranking (50 Daily Quota)
* Evaluates all scraped opportunities against candidate profile requirements.
* **Scoring Dimensions (Weights):**
  * Core Skills & Domain Fit: 40%
  * Experience Level & Seniority: 25%
  * Location / Remote / Commute Feasibility: 20%
  * Compensation & Benefit Alignment: 15%
* **Output:** Ranks all matching listings and populates exactly the top 50 qualified positions into the user's daily triage queue.

### 5.4 Module 4: Notion Interactive Control Center
* Integrates directly via official Notion REST API.
* **Database Schema ("Career Intelligence Hub"):**
  1. `Job Title` (Title)
  2. `Company / Client` (Text or Select)
  3. `Source Channel` (Select: LinkedIn, JobsDB, JobThai, Adecco, Manpower, PRTR, Robert Walters, JAC)
  4. `Agency Reference ID` (Rich Text)
  5. `Match Score` (Number: 0–100% formatted with color thresholds)
  6. `Location` (Select: Bangkok, Eastern Seaboard, Remote, Hybrid)
  7. `Salary Range` (Text)
  8. `Posting URL` (URL)
  9. `Review Decision` (Status: `Inbox`, `Approved`, `Pass`, `Follow Up`)
  10. `Application Stage` (Status: `Unapplied`, `Draft Ready`, `Submitted`, `Interviewing`, `Archived`)
  11. `Tailored Cover Letter / Context` (Page Body Markdown)

### 5.5 Module 5: Application Copilot & Assistive Execution
The engine categorizes approved jobs into two respectful application modes:

1. **Standardized Single-Step Portals (e.g., Simple JobThai/JobsDB Easy Submissions):**
   * Pre-fills verified contact details, resume uploads, and answers.
   * Prompts user for a final 1-click confirmation before triggering submission.
2. **Complex Agency & Enterprise ATS Portals (Workday, Taleo, Robert Walters, PRTR Portal):**
   * Rather than fragile, bot-like form manipulation, the copilot executes a **"Dossier Generation"** flow:
     * Generates a tailored 2-paragraph cover memo mapping the candidate's exact achievements to the agency consultant’s job description.
     * Extracts direct consultant contact email or deep-link submission URL.
     * Moves Notion status to `Draft Ready` and alerts the user.

---

## 6. Technical Stack & Tooling

| Component | Selected Technology | Rationale |
| :--- | :--- | :--- |
| **Orchestration Runtime** | Python 3.11+ / GitHub Codespaces | Highly portable, native async support, vast scraping ecosystem |
| **Automation Framework** | Playwright (Python Async API) | Robust handling of dynamic single-page applications and agency portals |
| **LLM & Semantic Engine** | OpenAI / Anthropic API (Structured Outputs) | Schema-enforced JSON extraction, factual prompt completion |
| **Database & Dashboard** | Notion API (`notion-client`) | Cloud-native, zero-maintenance UI on desktop and mobile |
| **Scheduling & Alerts** | Cron / Telegram Bot Webhook | Instant alerts when batch processing completes or human action is required |

---

## 7. Security, Privacy & Repository Hygiene

To ensure the repository is completely safe for public hosting and follows clean engineering standards:

* **Strict Credential Segregation:**
  * Zero credentials or API keys stored in Git.
  * Mandatory `.env.example` defining empty mock values for `NOTION_API_KEY`, `NOTION_DATABASE_ID`, `OPENAI_API_KEY`, and platform session tokens.
* **Complete PII Shielding:**
  * Git-ignore `/profile/*`, `*.pdf`, `*.json`, and `storage/`.
  * Provide sanitized mock candidate data (`sample_profile.json`, `sample_resume.md`) demonstrating clean architecture to reviewing hiring managers.
* **Respectful Scraping & Rate Limits:**
  * Implements exponential backoffs and jittered request intervals (2.0s to 6.5s) to avoid server load on agency sites.
  * Respects `robots.txt` guidelines and caches network payloads locally during development.

---

## 8. Implementation Roadmap

### Phase 1: Ingestion & Primary Scraping (Weeks 1–2)
* Local profile parser for PDF/Markdown.
* Implement scrapers for LinkedIn, JobsDB, and JobThai.
* Establish Notion Database schema and sync pipeline.

### Phase 2: Agency Aggregation & Deduplication (Weeks 3–4)
* Implement dedicated crawlers for Adecco Thailand, ManpowerGroup Thailand, PRTR, Robert Walters Thailand, and JAC Recruitment Thailand.
* Build unified deduplication and multi-channel normalizer.

### Phase 3: Semantic Scoring & Curated Top 50 Batch (Weeks 5–6)
* Implement LLM evaluation pipeline for scoring role alignment.
* Restrict Notion ingestion to the top 50 scored daily listings.

### Phase 4: Application Copilot & Human-in-the-Loop Assist (Weeks 7–8)
* Develop the Dossier Generator for agency postings.
* Build guided semi-automated submission flow with Telegram/Notion alerts.
