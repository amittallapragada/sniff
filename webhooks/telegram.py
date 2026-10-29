import asyncio
import logging

from fastapi import APIRouter, Request

from agent.core import handle_message
from auth.users import resolve_user_by_telegram_id
from capabilities.call.session import get_active_session, inject_user_input
from interfaces.telegram import pick_emoji, react_to_message, send_message, send_message_to_chat

logger = logging.getLogger(__name__)
router = APIRouter()

REJECTION_MESSAGE = "This is a private service."

# Track update IDs to prevent duplicate processing from Telegram retries
_processed_updates: set[int] = set()
_MAX_TRACKED = 1000


@router.post("/telegram")
async def inbound_telegram(request: Request):
    update = await request.json()

    # Deduplicate: Telegram retries on timeout with the same update_id
    update_id = update.get("update_id")
    if update_id in _processed_updates:
        logger.info("Skipping duplicate update_id %s", update_id)
        return {"status": "duplicate"}
    _processed_updates.add(update_id)
    if len(_processed_updates) > _MAX_TRACKED:
        # Trim oldest entries
        to_remove = sorted(_processed_updates)[: _MAX_TRACKED // 2]
        _processed_updates.difference_update(to_remove)

    message = update.get("message") or update.get("edited_message")
    if not message or "text" not in message:
        return {"status": "ignored"}

    chat_id: int = message["chat"]["id"]
    telegram_id: int = message["from"]["id"]
    text: str = message["text"].strip()
    logger.info("Telegram message from %s: %s", telegram_id, text)

    user = await resolve_user_by_telegram_id(telegram_id)
    if not user:
        logger.info("Unknown telegram_id %s, rejecting", telegram_id)
        await send_message_to_chat(chat_id, REJECTION_MESSAGE)
        return {"status": "rejected"}

    # Check if there's a call waiting on input from this user
    active_session = await get_active_session(user.id)
    if active_session and active_session.status == "awaiting_input":
        await inject_user_input(active_session.id, text)
        return {"status": "input_injected"}

    # React with a contextual emoji to acknowledge receipt
    message_id = message.get("message_id")
    if message_id:
        emoji = await pick_emoji(text)
        await react_to_message(chat_id, message_id, emoji)

    # Process in background so we return 200 immediately (prevents Telegram retries)
    asyncio.create_task(_process_message(user, text))
    return {"status": "ok"}


async def _process_message(user, text: str):
    try:
        logger.info("Calling handle_message for user %s", user.id)
        reply = await handle_message(user, text, channel="telegram")
        logger.info("Got reply (%d chars), sending to Telegram", len(reply))
        await send_message(user, reply)
    except Exception as e:
        logger.error("Error processing message: %s", e)
        await send_message(user, "Something went wrong. Try again?")
