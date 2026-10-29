import logging

import httpx

from config import settings
from memory.db import get_client

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


async def store_preference(user_id: str, content: str, metadata: dict | None = None) -> None:
    """Embed and store a preference or fact about the user."""
    vector = await embed(content)
    if vector is None:
        return
    get_client().table("embeddings").insert(
        {
            "user_id": user_id,
            "content": content,
            "vector": vector,
            "metadata": metadata or {},
        }
    ).execute()


async def recall(user_id: str, query: str, limit: int = 5) -> list[str]:
    """Semantic search over user's stored preferences/memory."""
    vector = await embed(query)
    if vector is None:
        return []
    result = (
        get_client()
        .rpc(
            "match_embeddings",
            {
                "query_vector": vector,
                "match_user_id": user_id,
                "match_count": limit,
            },
        )
        .execute()
    )
    return [row["content"] for row in (result.data or [])]
