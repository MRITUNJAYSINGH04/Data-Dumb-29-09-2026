from typing import List, Optional
from fastapi import APIRouter, Depends, Query
import httpx
from backend.app.core.config import settings
from backend.app.core.deps import get_current_user
from backend.app.models.user import User

router = APIRouter(prefix="/search", tags=["Search"])

@router.get("")
async def search(
    q: str = Query(..., description="Query string for search"),
    categories: Optional[str] = Query("general", description="SearXNG categories"),
    format: Optional[str] = Query("json"),
    current_user: User = Depends(get_current_user)
):
    """Direct metasearch endpoint querying self-hosted SearXNG HTTP API or fallback."""
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            res = await client.get(
                f"{settings.SEARXNG_URL}/search",
                params={"q": q, "categories": categories, "format": "json"}
            )
            if res.status_code == 200:
                return res.json()
    except Exception:
        pass

    # Resilient fallback result format
    return {
        "query": q,
        "results": [
            {
                "title": f"Public Search Result for: {q}",
                "url": f"https://duckduckgo.com/?q={q.replace(' ', '+')}",
                "content": f"Automated fallback search index result for '{q}'",
                "engine": "duckduckgo_fallback"
            }
        ]
    }
