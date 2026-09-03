import sys
import json
import asyncio
import logging
import argparse
from pathlib import Path
from typing import Optional, List

# Ensure UTF-8 output on Windows consoles so Thai text renders without charmap encode errors
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from careerpilot.config import settings
from careerpilot.models.job import SourceChannel, JobPosting
from careerpilot.profile.store import CandidateContextStore
from careerpilot.scrapers.engine import AggregationEngine
from careerpilot.notion.sync import NotionSyncPipeline
from careerpilot.notion.client import NotionClientWrapper

console = Console(highlight=False)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def cmd_profile_check(args: argparse.Namespace) -> None:
    """Inspect and validate candidate profile, resume, and screening Q&A."""
    console.print(Panel.fit("[bold cyan]CareerPilot AI -- Profile Engine Inspection[/bold cyan]"))
    store = CandidateContextStore(profile_dir=args.profile_dir)

    try:
        store.load()
    except Exception as exc:
        console.print(f"[bold red]Error loading candidate context store:[/bold red] {exc}")
        sys.exit(1)

    profile = store.profile
    table = Table(title="Candidate Profile Metadata", show_header=True, header_style="bold magenta")
    table.add_column("Field", style="cyan", width=24)
    table.add_column("Value", style="green")

    table.add_row("Metadata Source", f"{store.profile_source_file} {'[yellow](Template Fallback)[/yellow]' if store.is_using_sample_profile else '[green](Active Profile)[/green]'}")
    table.add_row("Full Name", profile.contact.full_name)
    table.add_row("Email", profile.contact.email)
    table.add_row("Location", profile.contact.location)
    table.add_row("Experience", f"{profile.years_of_experience} years")
    table.add_row("Notice Period", profile.notice_period)
    table.add_row("Work Authorization", profile.work_authorization)
    table.add_row("Target Roles", ", ".join(profile.target_job_titles))
    table.add_row("Preferred Locations", ", ".join(profile.preferred_locations))
    table.add_row(
        "Expected Monthly Salary",
        f"{profile.compensation.min_monthly_thb:,} - {profile.compensation.target_monthly_thb:,} THB"
        if profile.compensation.min_monthly_thb and profile.compensation.target_monthly_thb
        else "Negotiable",
    )
    table.add_row("Core Skills", ", ".join(profile.core_skills[:6]) + (f" (+{len(profile.core_skills)-6} more)" if len(profile.core_skills) > 6 else ""))
    table.add_row("Resume Source", str(store.resume_source_file))
    table.add_row("Resume Text Length", f"{len(store.resume_text):,} characters")
    table.add_row("Screening Q&A Items", f"{len(store.screening_qa.items)} canonical answers")

    console.print(table)

    # Display preview of parsed resume text
    preview_lines = [line.strip() for line in store.resume_text.splitlines() if line.strip()][:8]
    preview_snippet = "\n".join(preview_lines)
    console.print(Panel(
        f"[dim white]{preview_snippet}[/dim white]\n[dim]... ({len(store.resume_text):,} characters parsed)[/dim]",
        title=f"Parsed Resume Text Preview: {store.resume_source_file}",
        border_style="cyan",
    ))

    if store.is_using_sample_profile:
        console.print(Panel(
            "[bold yellow]Notice: 'profile/profile.json' was not found.[/bold yellow]\n\n"
            "• Your resume file ([bold cyan]{resume_file}[/bold cyan]) was [bold green]parsed successfully[/bold green] (see preview above).\n"
            "• However, candidate settings (target roles, compensation, notice period) are currently using the default template ([dim]sample_profile.json[/dim]).\n\n"
            "To personalize your metadata with your name and preferences, run:\n"
            "    [bold cyan]careerpilot profile init[/bold cyan]\n"
            "or copy and edit manually:\n"
            "    [bold cyan]cp profile/sample_profile.json profile/profile.json[/bold cyan]".format(
                resume_file=store.resume_source_file
            ),
            border_style="yellow",
        ))

    console.print("[bold green]Profile verification completed successfully![/bold green]\n")


def cmd_profile_init(args: argparse.Namespace) -> None:
    """Initialize profile/profile.json and screening_qa.json from the parsed resume."""
    console.print(Panel.fit("[bold cyan]CareerPilot AI -- Profile Initialization[/bold cyan]"))
    store = CandidateContextStore(profile_dir=args.profile_dir)
    profile_dir = store.profile_dir
    profile_file = profile_dir / "profile.json"
    qa_file = profile_dir / "screening_qa.json"

    # 1. Parse resume text to prefill contact info
    try:
        resume_text = store.load_resume()
    except Exception:
        resume_text = ""

    import re
    full_name = "Candidate"
    email = "candidate@example.com"
    phone = "+66 81 234 5678"
    github = None
    linkedin = None

    if resume_text:
        lines = [line.strip() for line in resume_text.splitlines() if line.strip()]
        if lines:
            # First clean line is usually the candidate's name
            full_name = re.sub(r"[^\w\s\u0E00-\u0E7F\.-]", "", lines[0]).strip()
        email_match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", resume_text)
        if email_match:
            email = email_match.group(0)
        phone_match = re.search(r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{2,3}\)?[-.\s]?\d{3,4}[-.\s]?\d{4}", resume_text)
        if phone_match:
            phone = phone_match.group(0).strip()
        gh_match = re.search(r"github\.com/([\w\-]+)", resume_text)
        if gh_match:
            github = f"https://github.com/{gh_match.group(1)}"
        li_match = re.search(r"linkedin\.com/in/([\w\-]+)", resume_text)
        if li_match:
            linkedin = f"https://linkedin.com/in/{li_match.group(1)}"

    # Load sample profile as base template
    sample_profile_path = profile_dir / "sample_profile.json"
    if sample_profile_path.is_file():
        data = json.loads(sample_profile_path.read_text(encoding="utf-8"))
    else:
        data = {}

    data["contact"] = {
        "full_name": full_name or "Candidate Name",
        "email": email,
        "phone": phone,
        "location": "Bangkok, Thailand",
        "linkedin_url": linkedin,
        "github_url": github,
        "portfolio_url": None,
    }

    if not profile_file.is_file() or args.force:
        profile_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        console.print(f"[bold green]Created:[/bold green] {profile_file} (Prefilled with name: [bold cyan]{full_name}[/bold cyan], email: [bold cyan]{email}[/bold cyan])")
    else:
        console.print(f"[yellow]Skipped:[/yellow] {profile_file} already exists. Use --force to overwrite.")

    # Initialize screening_qa.json if not present
    sample_qa_path = profile_dir / "sample_screening_qa.json"
    if not qa_file.is_file() and sample_qa_path.is_file():
        qa_file.write_text(sample_qa_path.read_text(encoding="utf-8"), encoding="utf-8")
        console.print(f"[bold green]Created:[/bold green] {qa_file}")

    console.print("\n[bold green]Profile initialized! You can now edit profile/profile.json and run 'careerpilot profile check'.[/bold green]\n")


def cmd_scrape(args: argparse.Namespace) -> None:
    """Run scrapers and save deduplicated results."""
    console.print(Panel.fit(f"[bold cyan]CareerPilot AI -- Multi-Source Aggregator[/bold cyan]\nKeywords: [yellow]{args.keywords}[/yellow] | Location: [yellow]{args.location}[/yellow]"))

    sources = None
    if args.source and args.source.lower() != "all":
        source_map = {
            "linkedin": SourceChannel.LINKEDIN,
            "jobsdb": SourceChannel.JOBSDB,
            "jobthai": SourceChannel.JOBTHAI,
        }
        selected = source_map.get(args.source.lower())
        if not selected:
            console.print(f"[bold red]Unknown source '{args.source}'. Choose: all, linkedin, jobsdb, jobthai[/bold red]")
            sys.exit(1)
        sources = [selected]

    engine = AggregationEngine()
    unique_jobs, dropped_jobs = asyncio.run(
        engine.run(
            keywords=args.keywords,
            location=args.location,
            limit_per_source=args.limit,
            sources=sources,
            save_to_storage=True,
        )
    )

    table = Table(title=f"Scraped & Deduplicated Opportunities ({len(unique_jobs)} new, {len(dropped_jobs)} dropped)", show_header=True)
    table.add_column("Source", style="cyan", width=12)
    table.add_column("Title", style="bold white", width=30)
    table.add_column("Company", style="green", width=25)
    table.add_column("Location", style="yellow", width=18)
    table.add_column("Salary Range", style="magenta", width=18)

    for job in unique_jobs[:15]:
        table.add_row(
            job.source.value,
            job.title[:28],
            job.company[:23],
            job.location[:16],
            (job.salary_range or "Not Disclosed")[:16],
        )

    console.print(table)
    if len(unique_jobs) > 15:
        console.print(f"[dim]... and {len(unique_jobs) - 15} more opportunities saved to storage/latest_jobs.json[/dim]")


def cmd_sync(args: argparse.Namespace) -> None:
    """Sync job listings from local JSON to Notion."""
    console.print(Panel.fit(f"[bold cyan]CareerPilot AI -- Notion Sync Pipeline[/bold cyan]\nFile: [yellow]{args.input}[/yellow] | Dry Run: [yellow]{args.dry_run}[/yellow]"))

    path = Path(args.input)
    if not path.is_file():
        console.print(f"[bold red]Input file not found: {path}[/bold red]")
        sys.exit(1)

    raw_data = json.loads(path.read_text(encoding="utf-8"))
    jobs = [JobPosting.model_validate(item) for item in raw_data]

    pipeline = NotionSyncPipeline()
    if not args.dry_run and pipeline.client.is_configured:
        if pipeline.client.is_database_empty():
            console.print("[bold yellow]Empty Notion database detected. Auto-configuring CareerPilot schema...[/bold yellow]")
    synced, skipped, errors = pipeline.sync(jobs, dry_run=args.dry_run)

    console.print(
        f"\n[bold green]Sync Summary:[/bold green] Synced: [bold cyan]{synced}[/bold cyan] | "
        f"Skipped: [bold yellow]{skipped}[/bold yellow] | "
        f"Errors: [bold red]{errors}[/bold red]\n"
    )


def cmd_run(args: argparse.Namespace) -> None:
    """Execute end-to-end Phase 1 pipeline."""
    console.print(Panel.fit("[bold cyan]CareerPilot AI -- Full Phase 1 Pipeline[/bold cyan]"))

    # 1. Profile
    store = CandidateContextStore(profile_dir=args.profile_dir)
    store.load()
    keywords = args.keywords or (store.profile.target_job_titles[0] if store.profile.target_job_titles else settings.default_search_keywords)
    location = args.location or (store.profile.preferred_locations[0] if store.profile.preferred_locations else settings.default_search_location)

    console.print(f"Target Role: [bold green]{keywords}[/bold green] | Location: [bold green]{location}[/bold green]")

    # 2. Scrape & Deduplicate
    engine = AggregationEngine()
    unique_jobs, dropped_jobs = asyncio.run(
        engine.run(
            keywords=keywords,
            location=location,
            limit_per_source=args.limit,
            save_to_storage=True,
        )
    )

    # 3. Notion Sync
    pipeline = NotionSyncPipeline()
    if not args.dry_run and pipeline.client.is_configured:
        if pipeline.client.is_database_empty():
            console.print("[bold yellow]Empty Notion database detected. Auto-configuring CareerPilot schema...[/bold yellow]")
    synced, skipped, errors = pipeline.sync(unique_jobs, dry_run=args.dry_run)

    console.print(
        f"\n[bold green]Pipeline Run Completed![/bold green] Found: {len(unique_jobs)} unique | "
        f"Notion Synced: {synced} | Skipped: {skipped} | Errors: {errors}\n"
    )


def main() -> None:
    """Main CLI entrypoint."""
    parser = argparse.ArgumentParser(
        prog="careerpilot",
        description="CareerPilot AI: Intelligent Job Intelligence & Application Copilot",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Profile check & init
    p_profile = subparsers.add_parser("profile", help="Profile inspection and setup")
    p_profile_sub = p_profile.add_subparsers(dest="profile_action", required=True)
    p_check = p_profile_sub.add_parser("check", help="Validate candidate profile and context store")
    p_check.add_argument("--profile-dir", default=None, help="Path to profile directory")
    p_check.set_defaults(func=cmd_profile_check)

    p_init = p_profile_sub.add_parser("init", help="Initialize personal profile.json from parsed resume")
    p_init.add_argument("--profile-dir", default=None, help="Path to profile directory")
    p_init.add_argument("--force", action="store_true", help="Overwrite profile.json if it exists")
    p_init.set_defaults(func=cmd_profile_init)

    # Scrape
    p_scrape = subparsers.add_parser("scrape", help="Scrape and aggregate job portals")
    p_scrape.add_argument("--source", default="all", help="all, linkedin, jobsdb, jobthai")
    p_scrape.add_argument("--keywords", default=settings.default_search_keywords, help="Search keywords")
    p_scrape.add_argument("--location", default=settings.default_search_location, help="Search location")
    p_scrape.add_argument("--limit", type=int, default=15, help="Max listings per source")
    p_scrape.set_defaults(func=cmd_scrape)

    # Sync
    p_sync = subparsers.add_parser("sync", help="Sync opportunities to Notion database")
    p_sync.add_argument("--input", default="storage/latest_jobs.json", help="Path to jobs JSON")
    p_sync.add_argument("--dry-run", action="store_true", help="Format and log without writing to Notion")
    p_sync.set_defaults(func=cmd_sync)

    # Run (End-to-End)
    p_run = subparsers.add_parser("run", help="Run full end-to-end ingestion and sync pipeline")
    p_run.add_argument("--keywords", default=None, help="Search keywords (overrides profile)")
    p_run.add_argument("--location", default=None, help="Location (overrides profile)")
    p_run.add_argument("--limit", type=int, default=10, help="Max listings per source")
    p_run.add_argument("--dry-run", action="store_true", help="Dry run Notion sync")
    p_run.add_argument("--profile-dir", default=None, help="Path to profile directory")
    p_run.set_defaults(func=cmd_run)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
