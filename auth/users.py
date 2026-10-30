from dataclasses import dataclass
from datetime import datetime

from memory.db import get_db


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


def _row_to_user(d) -> User:
    return User(
        id=d["id"],
        phone_number=d["phone_number"],
        telegram_id=d["telegram_id"],
        name=d["name"],
        persona_name=d["persona_name"],
        timezone=d["timezone"] or "UTC",
        created_at=datetime.fromisoformat(d["created_at"]),
        active=bool(d["active"]),
    )


async def resolve_user_by_telegram_id(telegram_id: int) -> User | None:
    """Look up a user by their Telegram user ID."""
    db = get_db()
    row = db.execute(
        "SELECT * FROM users WHERE telegram_id = ? AND active = 1", (telegram_id,)
    ).fetchone()
    if not row:
        return None
    return _row_to_user(row)


async def get_user_by_id(user_id: str) -> User | None:
    """Look up a user by their UUID."""
    db = get_db()
    row = db.execute(
        "SELECT * FROM users WHERE id = ? AND active = 1", (user_id,)
    ).fetchone()
    if not row:
        return None
    return _row_to_user(row)
