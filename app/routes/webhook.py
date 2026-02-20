"""FastAPI webhook route for receiving Telegram updates."""

from fastapi import APIRouter, Header, HTTPException, Request, status

from app.config import get_settings
from app.database import async_session_factory
from app.logging_config import get_logger
from app.services.telegram_service import handle_note_command

logger = get_logger(__name__)

router = APIRouter()


@router.post("/webhook", status_code=status.HTTP_200_OK)
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
) -> dict:
    """Receive and process Telegram webhook updates.

    Validates the secret token header, parses the update payload,
    and delegates command handling to the service layer.

    Returns:
        JSON ``{"status": "ok"}`` on success.
    """
    settings = get_settings()

    # --- Validate webhook secret ---
    if x_telegram_bot_api_secret_token != settings.telegram_webhook_secret:
        logger.warning("Webhook request with invalid secret token")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid secret token",
        )

    # --- Parse update ---
    try:
        update: dict = await request.json()
    except Exception as exc:
        logger.error("Failed to parse webhook payload: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid payload",
        )

    logger.debug("Received update: %s", update)

    # --- Process message ---
    message: dict | None = update.get("message")
    if not message:
        return {"status": "ok"}

    text: str | None = message.get("text")
    if not text:
        return {"status": "ok"}

    from_user: dict = message.get("from", {})
    user_id: str = str(from_user.get("id", ""))
    username: str | None = from_user.get("username")
    chat_id: int = message["chat"]["id"]

    # Only handle /note commands
    if text.startswith("/note"):
        note_text = text[len("/note"):].strip() or None
        async with async_session_factory() as session:
            try:
                reply = await handle_note_command(
                    session=session,
                    telegram_user_id=user_id,
                    username=username,
                    text=note_text,
                )
                await session.commit()
            except Exception as exc:
                await session.rollback()
                logger.error("Error handling /note: %s", exc, exc_info=True)
                reply = "⚠️ An unexpected error occurred. Please try again."

        # Send reply via Telegram Bot API
        await _send_message(chat_id, reply)

    return {"status": "ok"}


async def _send_message(chat_id: int, text: str) -> None:
    """Send a text message back to the Telegram chat.

    Args:
        chat_id: Target Telegram chat ID.
        text: Message content.
    """
    import httpx

    settings = get_settings()
    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"

    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            response = await client.post(
                url,
                json={"chat_id": chat_id, "text": text},
            )
            response.raise_for_status()
            logger.debug("Message sent to chat %s", chat_id)
        except httpx.HTTPError as exc:
            logger.error("Failed to send message to chat %s: %s", chat_id, exc)
