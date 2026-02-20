"""Pydantic schemas for note validation and serialization."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class NoteCreate(BaseModel):
    """Schema for creating a new note."""

    telegram_user_id: str = Field(..., description="Telegram user ID")
    username: Optional[str] = Field(None, description="Telegram username")
    text: str = Field(..., min_length=1, description="Note content")


class NoteResponse(BaseModel):
    """Schema for note API responses."""

    id: str = Field(..., description="Note UUID")
    telegram_user_id: str
    username: Optional[str] = None
    text: str
    created_at: datetime
    notion_page_id: Optional[str] = None
    pushed_to_notion: bool = False
    error_message: Optional[str] = None

    model_config = {"from_attributes": True}
