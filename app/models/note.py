"""SQLAlchemy ORM model for the notes table."""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, DateTime, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Note(Base):
    """Represents a user note captured via Telegram and optionally synced to Notion."""

    __tablename__ = "notes"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        doc="UUID primary key",
    )
    telegram_user_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
        doc="Telegram user ID who created the note",
    )
    username: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        doc="Telegram username (optional)",
    )
    text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Note content",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        doc="Timestamp when the note was created",
    )
    notion_page_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        doc="Notion page ID after successful sync",
    )
    pushed_to_notion: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="Whether the note has been synced to Notion",
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Error message if Notion sync failed",
    )

    __table_args__ = (
        Index("ix_notes_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<Note(id={self.id!r}, user={self.telegram_user_id!r}, "
            f"synced={self.pushed_to_notion})>"
        )
