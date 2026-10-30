import json
import logging
import math
import uuid

import httpx

from config import settings
from memory.db import get_db

logger = logging.getLogger(__name__)

EMBEDDING_MODEL = "gemini-embedding-001"
EMBEDDING_DIM = 3072
_EMBED_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/models/{EMBEDDING_MODEL}:embedContent"
)


async def embed(text: str) -> list[float] | None:
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                _EMBED_URL,
                headers={"x-goog-api-key": settings.gemini_api_key},
                json={"model": f"models/{EMBEDDING_MODEL}", "content": {"parts": [{"text": text}]}},
            )
            resp.raise_for_status()
            return resp.json()["embedding"]["values"]
    except Exception as e:
        logger.warning("Embedding unavailable: %s", e)
        return None


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


async def store_preference(user_id: str, content: str, metadata: dict | None = None) -> None:
    """Embed and store a preference or fact about the user."""
    vector = await embed(content)
    if vector is None:
        return
    db = get_db()
    db.execute(
        "INSERT INTO embeddings (id, user_id, content, vector, metadata) VALUES (?, ?, ?, ?, ?)",
        (str(uuid.uuid4()), user_id, content, json.dumps(vector), json.dumps(metadata or {})),
    )
    db.commit()


async def recall(user_id: str, query: str, limit: int = 5) -> list[str]:
    """Semantic search over user's stored preferences/memory."""
    query_vector = await embed(query)
    if query_vector is None:
        return []
    db = get_db()
    rows = db.execute(
        "SELECT content, vector FROM embeddings WHERE user_id = ?",
        (user_id,),
    ).fetchall()
    scored = []
    for row in rows:
        stored_vector = json.loads(row["vector"])
        similarity = _cosine_similarity(query_vector, stored_vector)
        scored.append((similarity, row["content"]))
    scored.sort(reverse=True)
    return [content for _, content in scored[:limit]]
