"""JobThai GraphQL API job scraper."""

import logging
from typing import List, Optional
from careerpilot.models.job import JobPosting, SourceChannel
from careerpilot.scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


GRAPHQL_QUERY = """
query ($searchJobsFilter: JobsSearchFilter, $orderBy: JobOrderBy) {
  searchJobs(filter: $searchJobsFilter, orderBy: $orderBy) {
    data {
      total
      data {
        id
        companyID
        jobTitle
        companyName
        workLocation
        salary
        tags
        updatedAt
        province {
          name
        }
        district {
          name
        }
      }
    }
  }
}
"""


class JobThaiScraper(BaseScraper):
    """Direct GraphQL scraper for JobThai listings."""

    source_channel = SourceChannel.JOBTHAI
    GRAPHQL_URL = "https://api.jobthai.com/v1/graphql"
    BASE_WEB_URL = "https://www.jobthai.com"

    async def scrape(
        self,
        keywords: str,
        location: str = "Thailand",
        limit: int = 25,
    ) -> List[JobPosting]:
        """Scrape JobThai listings via their GraphQL endpoint."""
        logger.info("[JobThai] Querying GraphQL API for '%s' (limit=%d)", keywords, limit)
        results: List[JobPosting] = []

        headers = {
            "Content-Type": "application/json",
            "apollographql-client-name": "jobthai-upgrade-web",
            "Origin": self.BASE_WEB_URL,
            "Referer": f"{self.BASE_WEB_URL}/th/jobs?keyword={keywords}",
        }

        payload = {
            "query": GRAPHQL_QUERY,
            "variables": {
                "searchJobsFilter": {
                    "keyword": keywords,
                },
                "orderBy": "UPDATED_AT_DESC",
            },
        }

        try:
            response = await self._request(
                url=self.GRAPHQL_URL,
                method="POST",
                headers=headers,
                json_data=payload,
            )
            data = response.json()
            jobs_data = (
                data.get("data", {})
                .get("searchJobs", {})
                .get("data", {})
                .get("data", [])
            )

            for item in jobs_data[:limit]:
                job_id = item.get("id")
                company_id = item.get("companyID")
                title = item.get("jobTitle") or "Untitled Position"
                company = item.get("companyName") or "Confidential"
                salary = item.get("salary")
                tags = ["JobThai"] + (item.get("tags") or [])
                updated_at = item.get("updatedAt")

                # Format location from province/district or workLocation
                loc_parts = []
                if item.get("district") and item["district"].get("name"):
                    loc_parts.append(item["district"]["name"])
                if item.get("province") and item["province"].get("name"):
                    loc_parts.append(item["province"]["name"])
                if not loc_parts and item.get("workLocation"):
                    loc_parts.append(item["workLocation"])
                location_str = ", ".join(loc_parts) if loc_parts else "Thailand"

                # Standard JobThai direct web URL
                job_url = f"{self.BASE_WEB_URL}/th/job/{job_id}"
                if company_id:
                    metadata = {"company_id": str(company_id)}
                else:
                    metadata = {}

                posting = JobPosting(
                    id=str(job_id),
                    title=title,
                    company=company,
                    source=self.source_channel,
                    url=job_url,
                    external_id=str(job_id),
                    location=location_str,
                    salary_range=salary if salary and salary.strip() else None,
                    posted_at=updated_at,
                    tags=tags,
                    metadata=metadata,
                )
                results.append(posting)

        except Exception as exc:
            logger.error("[JobThai] Failed to query GraphQL endpoint: %s", exc)

        logger.info("[JobThai] Extracted %d jobs.", len(results))
        return results
