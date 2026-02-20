"""Telegram command handling service — orchestrates note workflow."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.logging_config import get_logger
from app.schemas.note_schema import NoteCreate
from app.services import note_service, notion_service

logger = get_logger(__name__)


async def handle_note_command(
    session: AsyncSession,
    telegram_user_id: str,
    username: str | None,
    text: str | None,
) -> str:
    """Handle the /note command end-to-end.

    Flow:
        1. Validate that text is non-empty.
        2. Persist the note in the database.
        3. Push the note to Notion.
        4. Update sync status in the database.
        5. Return the appropriate user-facing message.

    Args:
        session: Async database session.
        telegram_user_id: Sender's Telegram user ID.
        username: Sender's Telegram username (may be None).
        text: The note text provided after /note.

    Returns:
        A response message string to send back to the user.
    """
    # --- 1. Validate input ---
    if not text or not text.strip():
        logger.debug("Empty /note from user %s", telegram_user_id)
        return "❌ Please provide note text.\nExample: /note Buy milk"

    clean_text = text.strip()

    # --- 2. Save to database ---
    data = NoteCreate(
        telegram_user_id=telegram_user_id,
        username=username,
        text=clean_text,
    )
    note = await note_service.create_note(session, data)

    # --- 3. Push to Notion ---
    try:
        notion_page_id = await notion_service.push_note_to_notion(
            text=note.text,
            telegram_user_id=note.telegram_user_id,
            created_at=note.created_at,
        )
    except Exception as exc:
        error_msg = str(exc)
        logger.error(
            "Notion sync failed for note %s: %s",
            note.id,
            error_msg,
        )
        await note_service.mark_failed(session, note, error_msg)
        return "⚠️ Note saved locally but failed to sync to Notion."

    # --- 4. Update sync status ---
    await note_service.mark_synced(session, note, notion_page_id)
    logger.info("Note %s fully processed", note.id)

    return "✅ Note saved and synced to Notion!"
