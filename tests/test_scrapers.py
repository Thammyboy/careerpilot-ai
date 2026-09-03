"""Tests for scraper parsing logic and resilient handlers."""

import pytest
from careerpilot.scrapers.linkedin import LinkedInScraper
from careerpilot.scrapers.jobsdb import JobsDBScraper
from careerpilot.scrapers.jobthai import JobThaiScraper
from careerpilot.models.job import SourceChannel


SAMPLE_LINKEDIN_HTML = """
<ul>
  <li>
    <div class="base-card">
      <a class="base-card__full-link" href="https://th.linkedin.com/jobs/view/engineer-software-development-engineering-at-analog-devices-4441066293?refId=123"></a>
      <h3 class="base-search-card__title">Engineer, Software Development Engineering</h3>
      <h4 class="base-search-card__subtitle"><a href="#">Analog Devices</a></h4>
      <span class="job-search-card__location">Chon Buri, Thailand</span>
      <time datetime="2026-09-01">2 days ago</time>
    </div>
  </li>
  <li>
    <div class="base-card">
      <a class="base-card__full-link" href="https://th.linkedin.com/jobs/view/senior-python-engineer-at-grab-4441066294"></a>
      <h3 class="base-search-card__title">Senior Python Engineer</h3>
      <h4 class="base-search-card__subtitle">Grab</h4>
      <span class="job-search-card__location">Bangkok, Thailand</span>
      <time datetime="2026-09-02">1 day ago</time>
    </div>
  </li>
</ul>
"""

SAMPLE_JOBSDB_HTML = """
<div>
  <article data-job-id="94400400" aria-label="Full Stack Developer">
    <h3 class="_17onnmg0"><a data-automation="jobTitle" href="/job/94400400">Full Stack Developer</a></h3>
    <span data-automation="jobCompany">THAI CREDIT BANK PUBLIC COMPANY LIMITED</span>
    <span data-automation="jobLocation">Bangkok</span>
    <span data-automation="jobSalary">80,000 - 120,000 THB</span>
    <span data-automation="jobClassification">Information & Communication Technology</span>
    <ul>
      <li>C# proficiency with .NET Core</li>
      <li>Database knowledge in MongoDB and SQL Server</li>
    </ul>
  </article>
  <article data-job-id="94392454">
    <h3 class="_17onnmg0"><a data-automation="jobTitle" href="/job/94392454">DevOps Engineer</a></h3>
    <span data-automation="jobCompany">Fitwhey Co., Ltd.</span>
    <span data-automation="jobLocation">Lat Phrao, Bangkok</span>
  </article>
</div>
"""


def test_linkedin_html_parser():
    scraper = LinkedInScraper(delay_min=0, delay_max=0)
    postings = scraper._parse_html(SAMPLE_LINKEDIN_HTML)

    assert len(postings) == 2
    p1 = postings[0]
    assert p1.title == "Engineer, Software Development Engineering"
    assert p1.company == "Analog Devices"
    assert p1.location == "Chon Buri, Thailand"
    assert p1.external_id == "4441066293"
    assert p1.source == SourceChannel.LINKEDIN
    assert "https://th.linkedin.com/jobs/view/engineer-software-development-engineering-at-analog-devices-4441066293" in p1.url

    p2 = postings[1]
    assert p2.title == "Senior Python Engineer"
    assert p2.company == "Grab"
    assert p2.external_id == "4441066294"


def test_jobsdb_html_parser():
    scraper = JobsDBScraper(delay_min=0, delay_max=0)
    postings = scraper._parse_html(SAMPLE_JOBSDB_HTML)

    assert len(postings) == 2
    p1 = postings[0]
    assert p1.title == "Full Stack Developer"
    assert p1.company == "THAI CREDIT BANK PUBLIC COMPANY LIMITED"
    assert p1.location == "Bangkok"
    assert p1.external_id == "94400400"
    assert p1.salary_range == "80,000 - 120,000 THB"
    assert "MongoDB" in p1.description
    assert p1.source == SourceChannel.JOBSDB
    assert p1.url == "https://th.jobsdb.com/job/94400400"

    p2 = postings[1]
    assert p2.title == "DevOps Engineer"
    assert p2.company == "Fitwhey Co., Ltd."
    assert p2.external_id == "94392454"
