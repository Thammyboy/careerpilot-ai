"""Notion API client wrapper and database schema definition."""

import logging
from typing import Optional, Dict, Any, List
from notion_client import Client
from notion_client.errors import APIResponseError

from careerpilot.config import settings

logger = logging.getLogger(__name__)


# Schema conforming directly to PRD Section 5.4 ("Career Intelligence Hub")
NOTION_DB_SCHEMA = {
    "Job Title": {"title": {}},
    "Company / Client": {"rich_text": {}},
    "Source Channel": {
        "select": {
            "options": [
                {"name": "LinkedIn", "color": "blue"},
                {"name": "JobsDB", "color": "red"},
                {"name": "JobThai", "color": "orange"},
                {"name": "Adecco", "color": "purple"},
                {"name": "Manpower", "color": "green"},
                {"name": "PRTR", "color": "yellow"},
                {"name": "Robert Walters", "color": "brown"},
                {"name": "JAC Recruitment", "color": "pink"},
            ]
        }
    },
    "Agency Reference ID": {"rich_text": {}},
    "Match Score": {"number": {"format": "percent"}},
    "Location": {"rich_text": {}},
    "Salary Range": {"rich_text": {}},
    "Posting URL": {"url": {}},
    "Review Decision": {
        "status": {
            "options": [
                {"name": "Inbox", "color": "default"},
                {"name": "Approved", "color": "green"},
                {"name": "Pass", "color": "gray"},
                {"name": "Follow Up", "color": "yellow"},
            ]
        }
    },
    "Application Stage": {
        "status": {
            "options": [
                {"name": "Unapplied", "color": "default"},
                {"name": "Draft Ready", "color": "purple"},
                {"name": "Submitted", "color": "blue"},
                {"name": "Interviewing", "color": "green"},
                {"name": "Archived", "color": "gray"},
            ]
        }
    },
}


class NotionClientWrapper:
    """Wrapper around official Notion REST API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        database_id: Optional[str] = None,
        client: Optional[Client] = None,
    ):
        self.api_key = api_key or settings.notion_api_key
        self.database_id = database_id or settings.notion_database_id
        if client:
            self._client = client
        elif self.api_key:
            self._client = Client(auth=self.api_key)
        else:
            self._client = None

    @property
    def is_configured(self) -> bool:
        """Check whether both API key and Database ID are present."""
        return bool(self.api_key and self.database_id and self._client)

    def verify_connection(self) -> bool:
        """Verify database connectivity and permissions."""
        if not self.is_configured:
            return False
        try:
            self._client.databases.retrieve(database_id=self.database_id)
            return True
        except APIResponseError as exc:
            logger.error("Notion verification failed: %s", exc)
            return False

    def query_existing_urls(self) -> set:
        """Retrieve set of existing Posting URLs in the Notion database to avoid re-syncing."""
        if not self.is_configured:
            return set()

        existing_urls = set()
        has_more = True
        start_cursor = None

        while has_more:
            try:
                response = self._client.databases.query(
                    database_id=self.database_id,
                    start_cursor=start_cursor,
                    page_size=100,
                )
                for page in response.get("results", []):
                    props = page.get("properties", {})
                    url_prop = props.get("Posting URL", {})
                    if url_prop and url_prop.get("url"):
                        existing_urls.add(url_prop["url"])

                has_more = response.get("has_more", False)
                start_cursor = response.get("next_cursor")
            except APIResponseError as exc:
                logger.error("Error querying existing Notion records: %s", exc)
                break

        return existing_urls

    def create_page(
        self,
        properties: Dict[str, Any],
        children: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Create a new page in the database."""
        if not self.is_configured:
            raise RuntimeError("Notion client is not configured with valid API key and Database ID.")

        return self._client.pages.create(
            parent={"database_id": self.database_id},
            properties=properties,
            children=children or [],
        )
