"""Notion API integration service — pushes notes to a Notion database."""

from datetime import datetime
from typing import Optional

import httpx

from app.config import get_settings
from app.logging_config import get_logger

logger = get_logger(__name__)

NOTION_API_URL = "https://api.notion.com/v1/pages"
NOTION_API_VERSION = "2022-06-28"


async def push_note_to_notion(
    text: str,
    telegram_user_id: str,
    created_at: datetime,
) -> str:
    """Create a page in the configured Notion database.

    Args:
        text: Note content (mapped to the Title property).
        telegram_user_id: Telegram user ID (mapped to a Rich text property).
        created_at: Timestamp when the note was created (mapped to a Date property).

    Returns:
        The Notion page ID of the newly created page.

    Raises:
        httpx.HTTPStatusError: If the Notion API returns a non-2xx response.
        httpx.RequestError: If there is a network-level error.
    """
    settings = get_settings()

    headers = {
        "Authorization": f"Bearer {settings.notion_token}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_API_VERSION,
    }

    payload = {
        "parent": {"database_id": settings.notion_database_id},
        "properties": {
            "Name": {
                "title": [
                    {
                        "text": {"content": text[:2000]},
                    }
                ]
            },
            "Telegram User": {
                "rich_text": [
                    {
                        "text": {"content": telegram_user_id},
                    }
                ]
            },
            "Created": {
                "date": {
                    "start": created_at.isoformat(),
                }
            },
        },
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            NOTION_API_URL,
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
        data = response.json()
        page_id: str = data["id"]
        logger.info("Notion page created: %s", page_id)
        return page_id


async def retry_sync(
    text: str,
    telegram_user_id: str,
    created_at: datetime,
) -> Optional[str]:
    """Attempt to push a note to Notion with retry logic.

    Args:
        text: Note content.
        telegram_user_id: Telegram user ID.
        created_at: Note creation timestamp.

    Returns:
        Notion page ID on success, None on failure.
    """
    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            return await push_note_to_notion(text, telegram_user_id, created_at)
        except (httpx.HTTPStatusError, httpx.RequestError) as exc:
            logger.warning(
                "Notion sync attempt %d/%d failed: %s",
                attempt,
                max_retries,
                str(exc),
            )
            if attempt == max_retries:
                logger.error("All Notion sync retries exhausted")
                return None
    return None
