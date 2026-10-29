import logging

import httpx

from config import settings

logger = logging.getLogger(__name__)

_BASE = "https://scrappa.co/api"
_HEADERS = {
    "X-API-KEY": settings.scrappa_api_key,
    "Accept": "application/json",
}


async def scrappa_search(endpoint: str, params: dict) -> dict:
    """Call any Scrappa API endpoint and return the raw JSON response."""
    url = f"{_BASE}/{endpoint.lstrip('/')}"
    try:
        async with httpx.AsyncClient(timeout=45) as client:
            resp = await client.get(url, headers=_HEADERS, params=params)
            if resp.status_code != 200:
                logger.error("Scrappa %s error %s: %s", endpoint, resp.status_code, resp.text)
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        logger.error("Scrappa search failed: %s %s", type(e).__name__, e, exc_info=True)
        return {"error": f"{type(e).__name__}: {e}"}
