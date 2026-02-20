"""Note persistence service — handles all database operations for notes."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.logging_config import get_logger
from app.models.note import Note
from app.schemas.note_schema import NoteCreate

logger = get_logger(__name__)


async def create_note(session: AsyncSession, data: NoteCreate) -> Note:
    """Create and persist a new note.

    Args:
        session: Async database session.
        data: Validated note creation data.

    Returns:
        The newly created Note ORM instance.
    """
    note = Note(
        telegram_user_id=data.telegram_user_id,
        username=data.username,
        text=data.text,
    )
    session.add(note)
    await session.flush()
    await session.refresh(note)
    logger.info(
        "Note created: id=%s, user=%s",
        note.id,
        note.telegram_user_id,
    )
    return note


async def mark_synced(
    session: AsyncSession,
    note: Note,
    notion_page_id: str,
) -> Note:
    """Mark a note as successfully synced to Notion.

    Args:
        session: Async database session.
        note: The Note instance to update.
        notion_page_id: Notion page ID returned by the API.

    Returns:
        Updated Note instance.
    """
    note.pushed_to_notion = True
    note.notion_page_id = notion_page_id
    note.error_message = None
    await session.flush()
    await session.refresh(note)
    logger.info("Note %s synced to Notion (page=%s)", note.id, notion_page_id)
    return note


async def mark_failed(
    session: AsyncSession,
    note: Note,
    error: str,
) -> Note:
    """Record a Notion sync failure on a note.

    Args:
        session: Async database session.
        note: The Note instance to update.
        error: Human-readable error description.

    Returns:
        Updated Note instance.
    """
    note.pushed_to_notion = False
    note.error_message = error
    await session.flush()
    await session.refresh(note)
    logger.warning("Note %s failed to sync: %s", note.id, error)
    return note


async def get_unsynced_notes(session: AsyncSession) -> list[Note]:
    """Fetch all notes that have not yet been synced to Notion.

    Args:
        session: Async database session.

    Returns:
        List of unsynced Note instances.
    """
    stmt = select(Note).where(Note.pushed_to_notion == False).order_by(Note.created_at)  # noqa: E712
    result = await session.execute(stmt)
    return list(result.scalars().all())
