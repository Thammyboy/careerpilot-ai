"""JobsDB Thailand (SEEK) job scraper."""

import re
import logging
from typing import List
from bs4 import BeautifulSoup

from careerpilot.models.job import JobPosting, SourceChannel
from careerpilot.scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class JobsDBScraper(BaseScraper):
    """Scraper for JobsDB Thailand (SEEK platform) listings."""

    source_channel = SourceChannel.JOBSDB
    BASE_URL = "https://th.jobsdb.com"
    SEARCH_PATH = "/jobs"

    async def scrape(
        self,
        keywords: str,
        location: str = "Thailand",
        limit: int = 25,
    ) -> List[JobPosting]:
        """Scrape JobsDB Thailand job listings."""
        logger.info("[JobsDB] Searching for '%s' in '%s' (limit=%d)", keywords, location, limit)
        results: List[JobPosting] = []
        page = 1

        while len(results) < limit:
            params = {
                "keywords": keywords,
                "where": location,
                "page": page,
            }

            try:
                response = await self._request(f"{self.BASE_URL}{self.SEARCH_PATH}", params=params)
                batch = self._parse_html(response.text)

                if not batch:
                    logger.info("[JobsDB] No further postings found at page %d.", page)
                    break

                for item in batch:
                    results.append(item)
                    if len(results) >= limit:
                        break

                page += 1
                if len(results) < limit:
                    await self._polite_delay()

            except Exception as exc:
                logger.error("[JobsDB] Error scraping batch at page %d: %s", page, exc)
                break

        logger.info("[JobsDB] Extracted %d jobs.", len(results))
        return results

    def _parse_html(self, html: str) -> List[JobPosting]:
        """Parse raw HTML containing JobsDB article cards."""
        soup = BeautifulSoup(html, "html.parser")
        articles = soup.find_all("article", attrs={"data-job-id": True})
        postings: List[JobPosting] = []

        for article in articles:
            job_id = article.get("data-job-id")
            if not job_id:
                continue

            # Title
            title_tag = article.find(attrs={"data-automation": "jobTitle"})
            if not title_tag:
                h3_tag = article.find("h3")
                raw_title = h3_tag.get_text(strip=True) if h3_tag else article.get("aria-label", "")
            else:
                raw_title = title_tag.get_text(strip=True)

            if not raw_title:
                continue

            # Clean potential "Jobs at Company" prefix if aria-label fallback occurred
            raw_title = re.sub(r"^Jobs at\s+", "", raw_title)

            # Company
            company_tag = article.find(attrs={"data-automation": "jobCompany"})
            raw_company = company_tag.get_text(strip=True) if company_tag else "Confidential"

            # Location
            location_tag = article.find(attrs={"data-automation": "jobLocation"})
            raw_location = location_tag.get_text(strip=True) if location_tag else "Thailand"

            # Salary
            salary_tag = article.find(attrs={"data-automation": "jobSalary"})
            raw_salary = salary_tag.get_text(strip=True) if salary_tag else None

            # Description snippet / bullet points
            bullets = [li.get_text(strip=True) for li in article.find_all("li")]
            desc_text = "\n".join(bullets) if bullets else article.get_text(separator=" ", strip=True)[:400]

            # Tags / Classifications
            tags = ["JobsDB"]
            classification_tag = article.find(attrs={"data-automation": "jobClassification"})
            if classification_tag:
                tags.append(classification_tag.get_text(strip=True))

            # Job URL
            job_url = f"{self.BASE_URL}/job/{job_id}"

            posting = JobPosting(
                id=str(job_id),
                title=raw_title,
                company=raw_company,
                source=self.source_channel,
                url=job_url,
                external_id=str(job_id),
                location=raw_location,
                salary_range=raw_salary,
                description=desc_text,
                tags=tags,
            )
            postings.append(posting)

        return postings
