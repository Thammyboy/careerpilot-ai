"""LinkedIn public guest search scraper."""

import re
import logging
from typing import List, Optional
from bs4 import BeautifulSoup

from careerpilot.models.job import JobPosting, SourceChannel
from careerpilot.scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class LinkedInScraper(BaseScraper):
    """Scraper for public LinkedIn job listings via the guest API endpoint."""

    source_channel = SourceChannel.LINKEDIN
    SEARCH_URL = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"

    async def scrape(
        self,
        keywords: str,
        location: str = "Thailand",
        limit: int = 25,
    ) -> List[JobPosting]:
        """Scrape LinkedIn public guest jobs."""
        logger.info("[LinkedIn] Searching for '%s' in '%s' (limit=%d)", keywords, location, limit)
        results: List[JobPosting] = []
        start = 0

        while len(results) < limit:
            params = {
                "keywords": keywords,
                "location": location,
                "start": start,
            }

            try:
                response = await self._request(self.SEARCH_URL, params=params)
                batch = self._parse_html(response.text)

                if not batch:
                    logger.info("[LinkedIn] No further job postings found at offset %d.", start)
                    break

                for item in batch:
                    results.append(item)
                    if len(results) >= limit:
                        break

                start += len(batch)
                if len(results) < limit:
                    await self._polite_delay()

            except Exception as exc:
                logger.error("[LinkedIn] Error scraping batch at offset %d: %s", start, exc)
                break

        logger.info("[LinkedIn] Extracted %d jobs.", len(results))
        return results

    def _parse_html(self, html: str) -> List[JobPosting]:
        """Parse raw HTML snippet into normalized JobPosting models."""
        soup = BeautifulSoup(html, "html.parser")
        cards = soup.find_all("li")
        postings: List[JobPosting] = []

        for card in cards:
            title_tag = card.find("h3", class_=re.compile(r"base-search-card__title"))
            company_tag = card.find("h4", class_=re.compile(r"base-search-card__subtitle"))
            location_tag = card.find("span", class_=re.compile(r"job-search-card__location"))
            link_tag = card.find("a", class_=re.compile(r"base-card__full-link"))
            time_tag = card.find("time")

            if not (title_tag and link_tag):
                continue

            raw_title = title_tag.get_text(strip=True)
            raw_company = company_tag.get_text(strip=True) if company_tag else "Confidential / Unknown"
            raw_location = location_tag.get_text(strip=True) if location_tag else "Thailand"
            raw_url = link_tag.get("href", "").split("?")[0]
            posted_at = time_tag.get_text(strip=True) if time_tag else None

            # Extract LinkedIn Job ID from URL (e.g., ...-4441066293 or view/4441066293)
            ext_id_match = re.search(r"(\d{8,12})", raw_url)
            external_id = ext_id_match.group(1) if ext_id_match else None

            posting = JobPosting(
                id=external_id or raw_url,
                title=raw_title,
                company=raw_company,
                source=self.source_channel,
                url=raw_url,
                external_id=external_id,
                location=raw_location,
                posted_at=posted_at,
                tags=[keywords for keywords in ["LinkedIn", "Public Guest Feed"]],
            )
            postings.append(posting)

        return postings
