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
            self._client = Client(auth=self.api_key, notion_version="2022-06-28")
        else:
            self._client = None

    @property
    def is_configured(self) -> bool:
        """Check whether both API key and Database ID are present."""
        return bool(self.api_key and self.database_id and self._client)

    def get_database_info(self) -> Optional[Dict[str, Any]]:
        """Retrieve database metadata from Notion API."""
        if not self.is_configured:
            return None
        try:
            db = self._client.databases.retrieve(database_id=self.database_id)
            # If properties dictionary is empty but data_sources are present (modern Notion API model),
            # retrieve properties from the primary data source
            if not db.get("properties") and db.get("data_sources"):
                ds_id = db["data_sources"][0]["id"]
                if hasattr(self._client, "data_sources") and hasattr(self._client.data_sources, "retrieve"):
                    ds = self._client.data_sources.retrieve(data_source_id=ds_id)
                else:
                    ds = self._client.request(path=f"data_sources/{ds_id}", method="GET")
                db["properties"] = ds.get("properties", {})
            return db
        except Exception as exc:
            logger.error("Failed to retrieve Notion database info: %s", exc)
            return None

    def verify_connection(self) -> bool:
        """Verify database connectivity and permissions."""
        if not self.is_configured:
            return False
        info = self.get_database_info()
        return info is not None

    def _query_database(
        self,
        page_size: Optional[int] = None,
        start_cursor: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Query database records with cross-version notion-client compatibility.
        Supports both older notion-client SDKs (databases.query) and newer SDKs (client.request).
        """
        if hasattr(self._client, "databases") and hasattr(self._client.databases, "query"):
            kwargs: Dict[str, Any] = {"database_id": self.database_id}
            if page_size is not None:
                kwargs["page_size"] = page_size
            if start_cursor is not None:
                kwargs["start_cursor"] = start_cursor
            return self._client.databases.query(**kwargs)

        body: Dict[str, Any] = {}
        if page_size is not None:
            body["page_size"] = page_size
        if start_cursor is not None:
            body["start_cursor"] = start_cursor

        return self._client.request(
            path=f"databases/{self.database_id}/query",
            method="POST",
            body=body,
        )

    def is_database_empty(self) -> bool:
        """
        Check whether the target Notion database is empty and requires initial schema configuration.
        Returns True if the database has 0 records and does not yet have CareerPilot's schema.
        """
        if not self.is_configured:
            return False

        db_info = self.get_database_info()
        if not db_info:
            return False

        # Query first page to check if database has any existing records
        try:
            query_res = self._query_database(page_size=1)
            has_records = len(query_res.get("results", [])) > 0
        except Exception as exc:
            logger.error("Failed to query Notion database rows: %s", exc)
            return False

        if has_records:
            return False

        properties = db_info.get("properties", {})
        # If database already has the required properties, it's already configured
        required_keys = {"Job Title", "Posting URL", "Source Channel"}
        if required_keys.issubset(properties.keys()):
            return False

        return True

    def setup_database_schema(self) -> bool:
        """
        Configure the CareerPilot schema on an empty Notion database.
        Renames the default title column to 'Job Title' and adds all custom properties.
        """
        if not self.is_configured:
            logger.warning("Notion is not configured; cannot setup schema.")
            return False

        db_info = self.get_database_info()
        if not db_info:
            return False

        properties = db_info.get("properties", {})
        # Identify existing title property to rename it to "Job Title"
        title_prop_name = None
        for name, prop in properties.items():
            if prop.get("type") == "title":
                title_prop_name = name
                break

        update_payload: Dict[str, Any] = {}
        if title_prop_name and title_prop_name != "Job Title":
            update_payload[title_prop_name] = {"name": "Job Title"}

        # Add all other required properties from NOTION_DB_SCHEMA
        for prop_name, prop_def in NOTION_DB_SCHEMA.items():
            if prop_name == "Job Title":
                continue
            if prop_name not in properties:
                update_payload[prop_name] = prop_def

        if not update_payload:
            logger.info("Notion database schema is already up to date.")
            return True

        # Check if database uses modern data_sources model (Notion 2025-09-03 architecture)
        data_sources = db_info.get("data_sources", [])
        if data_sources:
            ds_id = data_sources[0]["id"]
            try:
                if hasattr(self._client, "data_sources") and hasattr(self._client.data_sources, "update"):
                    self._client.data_sources.update(data_source_id=ds_id, properties=update_payload)
                else:
                    self._client.request(path=f"data_sources/{ds_id}", method="PATCH", body={"properties": update_payload})
                logger.info("Successfully configured CareerPilot schema in Notion data source.")
                return True
            except Exception as exc:
                logger.error("Failed to configure Notion data source schema: %s", exc)
                return False

        try:
            self._client.databases.update(
                database_id=self.database_id,
                properties=update_payload,
            )
            logger.info("Successfully configured CareerPilot schema in Notion database.")
            return True
        except APIResponseError as exc:
            logger.error("Failed to configure Notion database schema: %s", exc)
            # If status property configuration failed, attempt fallback without custom status options
            if "status" in str(exc).lower():
                logger.info("Retrying schema configuration with fallback status properties...")
                fallback_payload = dict(update_payload)
                for k in ["Review Decision", "Application Stage"]:
                    if k in fallback_payload:
                        fallback_payload[k] = {"status": {}}
                try:
                    self._client.databases.update(
                        database_id=self.database_id,
                        properties=fallback_payload,
                    )
                    logger.info("Successfully configured CareerPilot schema with fallback status properties.")
                    return True
                except APIResponseError as fallback_exc:
                    logger.error("Fallback schema configuration failed: %s", fallback_exc)
            return False

    def ensure_schema(self) -> bool:
        """
        Inspect the database and automatically configure the schema if the database is empty.
        Returns True if database is ready (either was already configured or successfully auto-configured).
        """
        if not self.is_configured:
            return False

        if self.is_database_empty():
            logger.info("Detected empty Notion database. Initializing CareerPilot schema...")
            return self.setup_database_schema()

        return True

    def query_existing_urls(self) -> set:
        """Retrieve set of existing Posting URLs in the Notion database to avoid re-syncing."""
        if not self.is_configured:
            return set()

        existing_urls = set()
        has_more = True
        start_cursor = None

        while has_more:
            try:
                response = self._query_database(
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
            except Exception as exc:
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
