import asyncio
import logging

from duckduckgo_search import DDGS

logger = logging.getLogger(__name__)


async def web_search(query: str, max_results: int = 5) -> str:
    """Run a DuckDuckGo search and return formatted results."""
    try:
        results = await asyncio.to_thread(_search_sync, query, max_results)

        if not results:
            return "No results found."

        lines = []
        for r in results:
            lines.append(f"{r['title']}\n{r['href']}\n{r['body']}")
        return "\n\n".join(lines)
    except Exception as e:
        logger.error("Web search failed: %s", e)
        return f"Search failed: {e}"


def _search_sync(query: str, max_results: int) -> list[dict]:
    with DDGS() as ddgs:
        return list(ddgs.text(query, max_results=max_results))
