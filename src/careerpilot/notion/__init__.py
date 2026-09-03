"""Notion integration package for syncing curated job feeds into Notion databases."""

from careerpilot.notion.client import NotionClientWrapper, NOTION_DB_SCHEMA
from careerpilot.notion.sync import NotionSyncPipeline

__all__ = [
    "NotionClientWrapper",
    "NOTION_DB_SCHEMA",
    "NotionSyncPipeline",
]
