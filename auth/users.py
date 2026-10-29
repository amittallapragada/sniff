from dataclasses import dataclass
from datetime import datetime

from memory.db import get_client


@dataclass
class User:
    id: str
    phone_number: str
    telegram_id: int | None
    name: str
    persona_name: str
    timezone: str
    created_at: datetime
    active: bool


def _row_to_user(d: dict) -> User:
    return User(
        id=d["id"],
        phone_number=d["phone_number"],
        telegram_id=d.get("telegram_id"),
        name=d["name"],
        persona_name=d["persona_name"],
        timezone=d.get("timezone", "UTC"),
        created_at=datetime.fromisoformat(d["created_at"]),
        active=d["active"],
    )


async def resolve_user_by_telegram_id(telegram_id: int) -> User | None:
    """Look up a user by their Telegram user ID."""
    result = (
        get_client()
        .table("users")
        .select("*")
        .eq("telegram_id", telegram_id)
        .eq("active", True)
        .single()
        .execute()
    )
    if not result.data:
        return None
    return _row_to_user(result.data)


async def get_user_by_id(user_id: str) -> User | None:
    """Look up a user by their UUID."""
    result = (
        get_client()
        .table("users")
        .select("*")
        .eq("id", user_id)
        .eq("active", True)
        .single()
        .execute()
    )
    if not result.data:
        return None
    return _row_to_user(result.data)
