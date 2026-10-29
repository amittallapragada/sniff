import logging

import httpx
from google import genai
from google.genai import types

from auth.users import User
from config import settings

logger = logging.getLogger(__name__)

_llm = genai.Client(api_key=settings.gemini_api_key)

_API = f"https://api.telegram.org/bot{settings.telegram_bot_token}"


async def send_message(user: User, text: str) -> None:
    async with httpx.AsyncClient() as client:
        await client.post(
            f"{_API}/sendMessage",
            json={
                "chat_id": user.telegram_id,
                "text": text,
                "parse_mode": "HTML",
            },
        )


async def send_message_to_chat(chat_id: int, text: str) -> None:
    """Send to a raw chat_id — used before a User object is resolved."""
    async with httpx.AsyncClient() as client:
        await client.post(
            f"{_API}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "HTML",
            },
        )


# Telegram only supports these emojis for reactions
_ALLOWED_REACTIONS = {
    "👍",
    "👎",
    "❤️",
    "🔥",
    "🥰",
    "👏",
    "😁",
    "🤔",
    "🤯",
    "😱",
    "🤬",
    "😢",
    "🎉",
    "🤩",
    "🤮",
    "💩",
    "🙏",
    "👌",
    "🕊",
    "🤡",
    "🥱",
    "🥴",
    "😍",
    "🐳",
    "❤️‍🔥",
    "🌚",
    "🌭",
    "💯",
    "🤣",
    "⚡",
    "🍌",
    "🏆",
    "💔",
    "🤨",
    "😐",
    "🍓",
    "🍾",
    "💋",
    "🖕",
    "😈",
    "😴",
    "😭",
    "🤓",
    "👻",
    "👨‍💻",
    "👀",
    "🎃",
    "🙈",
    "😇",
    "😨",
    "🤝",
    "✍️",
    "🤗",
    "🫡",
    "🎅",
    "🎄",
    "☃️",
    "💅",
    "🤪",
    "🗿",
    "🆒",
    "💘",
    "🙉",
    "🦄",
    "😘",
    "💊",
    "🙊",
    "😎",
    "👾",
    "🤷",
    "😡",
}


async def pick_emoji(text: str) -> str:
    """Use Gemini Flash to pick a contextually appropriate emoji reaction."""
    try:
        resp = await _llm.aio.models.generate_content(
            model="gemini-3.8-flash",
            contents=text,
            config=types.GenerateContentConfig(
                max_output_tokens=4,
                system_instruction=(
                    "Reply with a single emoji that best reacts to this message. "
                    "Output nothing but the emoji. You MUST pick from this set:\n"
                    + " ".join(sorted(_ALLOWED_REACTIONS))
                ),
            ),
        )
        emoji = resp.text.strip()
        if emoji in _ALLOWED_REACTIONS:
            return emoji
    except Exception as e:
        logger.debug("Emoji pick failed: %s", e)
    return "👀"


async def react_to_message(chat_id: int, message_id: int, emoji: str = "👀") -> None:
    """React to a message with an emoji to acknowledge receipt."""
    async with httpx.AsyncClient() as client:
        await client.post(
            f"{_API}/setMessageReaction",
            json={
                "chat_id": chat_id,
                "message_id": message_id,
                "reaction": [{"type": "emoji", "emoji": emoji}],
            },
        )


async def register_webhook() -> None:
    """Point Telegram at our webhook endpoint. Call once on startup."""
    url = f"{settings.app_base_url}/webhook/telegram"
    async with httpx.AsyncClient() as client:
        await client.post(f"{_API}/setWebhook", json={"url": url})
