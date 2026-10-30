import uuid
from datetime import UTC, datetime

from memory.db import get_db


async def append_message(user_id: str, channel: str, role: str, content: str) -> None:
    """Append a message to conversation history."""
    db = get_db()
    db.execute(
        "INSERT INTO conversations (id, user_id, channel, role, content, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (str(uuid.uuid4()), user_id, channel, role, content, datetime.now(UTC).isoformat()),
    )
    db.commit()


async def get_recent_history(user_id: str, channel: str, limit: int = 20) -> list[dict]:
    """Fetch recent conversation history for context injection."""
    db = get_db()
    rows = db.execute(
        "SELECT role, content, created_at FROM conversations "
        "WHERE user_id = ? AND channel = ? ORDER BY created_at DESC LIMIT ?",
        (user_id, channel, limit),
    ).fetchall()
    return [dict(r) for r in reversed(rows)]
