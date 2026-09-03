"""Base asynchronous scraper with jitter, rate-limiting, and exponential backoff."""

import asyncio
import random
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
import httpx

from careerpilot.config import settings
from careerpilot.models.job import JobPosting, SourceChannel

logger = logging.getLogger(__name__)


DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9,th;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
}


class BaseScraper(ABC):
    """Abstract base class for all job board scrapers."""

    source_channel: SourceChannel

    def __init__(
        self,
        delay_min: Optional[float] = None,
        delay_max: Optional[float] = None,
        max_retries: Optional[int] = None,
        timeout: Optional[float] = None,
        client: Optional[httpx.AsyncClient] = None,
    ):
        self.delay_min = delay_min if delay_min is not None else settings.scraping_delay_min
        self.delay_max = delay_max if delay_max is not None else settings.scraping_delay_max
        self.max_retries = max_retries if max_retries is not None else settings.scraping_max_retries
        self.timeout = timeout if timeout is not None else settings.scraping_request_timeout
        self._external_client = client

    async def _polite_delay(self) -> None:
        """Sleep for a randomized jitter duration to respect portal rate limits (2.0s - 6.5s)."""
        if self.delay_max > 0:
            jitter = random.uniform(self.delay_min, self.delay_max)
            logger.debug("[%s] Jitter delay: %.2fs", self.source_channel.value, jitter)
            await asyncio.sleep(jitter)

    async def _request(
        self,
        url: str,
        method: str = "GET",
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        data: Optional[Any] = None,
    ) -> httpx.Response:
        """Execute resilient HTTP request with exponential backoff on rate limits / server errors."""
        merged_headers = {**DEFAULT_HEADERS, **(headers or {})}

        backoff = 2.0
        last_exception: Optional[Exception] = None

        for attempt in range(1, self.max_retries + 1):
            try:
                if self._external_client:
                    client = self._external_client
                    response = await client.request(
                        method=method,
                        url=url,
                        headers=merged_headers,
                        params=params,
                        json=json_data,
                        data=data,
                        timeout=self.timeout,
                        follow_redirects=True,
                    )
                else:
                    async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                        response = await client.request(
                            method=method,
                            url=url,
                            headers=merged_headers,
                            params=params,
                            json=json_data,
                            data=data,
                        )

                # Check for rate limits or server errors
                if response.status_code == 429 or 500 <= response.status_code < 600:
                    logger.warning(
                        "[%s] Attempt %d/%d: Received status %d from %s. Backing off for %.2fs",
                        self.source_channel.value,
                        attempt,
                        self.max_retries,
                        response.status_code,
                        url,
                        backoff,
                    )
                    await asyncio.sleep(backoff)
                    backoff *= 2.0
                    continue

                response.raise_for_status()
                return response

            except (httpx.RequestError, httpx.HTTPStatusError) as exc:
                last_exception = exc
                logger.warning(
                    "[%s] Attempt %d/%d failed for %s: %s",
                    self.source_channel.value,
                    attempt,
                    self.max_retries,
                    url,
                    exc,
                )
                if attempt < self.max_retries:
                    await asyncio.sleep(backoff)
                    backoff *= 2.0

        raise RuntimeError(
            f"[{self.source_channel.value}] Request failed after {self.max_retries} attempts: {last_exception}"
        ) from last_exception

    @abstractmethod
    async def scrape(
        self,
        keywords: str,
        location: str = "Thailand",
        limit: int = 25,
    ) -> List[JobPosting]:
        """Scrape jobs matching the given keywords and location up to the specified limit."""
        pass
