from datetime import UTC, datetime

from memory.db import get_client


async def append_message(user_id: str, channel: str, role: str, content: str) -> None:
    """Append a message to conversation history."""
    get_client().table("conversations").insert(
        {
            "user_id": user_id,
            "channel": channel,
            "role": role,
            "content": content,
            "created_at": datetime.now(UTC).isoformat(),
        }
    ).execute()


async def get_recent_history(user_id: str, channel: str, limit: int = 20) -> list[dict]:
    """Fetch recent conversation history for context injection."""
    result = (
        get_client()
        .table("conversations")
        .select("role, content, created_at")
        .eq("user_id", user_id)
        .eq("channel", channel)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return list(reversed(result.data or []))
