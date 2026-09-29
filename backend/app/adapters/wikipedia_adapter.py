import time
import httpx
from typing import List
from urllib.parse import quote
from backend.app.adapters.base import BaseAdapter
from backend.app.schemas.investigation import InvestigationInput, NormalizedResult, VerificationStatus
from backend.app.core.config import settings

class WikipediaAdapter(BaseAdapter):
    name: str = "Wikipedia"
    category: str = "knowledge_base"
    description: str = "MediaWiki & Wikidata public API for biographical and corporate knowledge"
    version: str = "1.0.0"
    license: str = "CC-BY-SA"
    supported_identifiers: List[str] = ["name", "company"]

    def is_installed(self) -> bool:
        return True

    async def execute(self, input_data: InvestigationInput) -> List[NormalizedResult]:
        start = time.time()
        self.execution_count += 1
        results: List[NormalizedResult] = []

        query = input_data.name or input_data.company
        if not query:
            return results

        headers = {"User-Agent": settings.USER_AGENT}
        try:
            async with httpx.AsyncClient(timeout=8.0, headers=headers) as client:
                encoded = quote(query)
                # Query Wikipedia summary API
                url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{encoded}"
                res = await client.get(url)
                if res.status_code == 200:
                    data = res.json()
                    title = data.get("title", "")
                    extract = data.get("extract", "")
                    page_url = data.get("content_urls", {}).get("desktop", {}).get("page", f"https://en.wikipedia.org/wiki/{encoded}")
                    thumbnail = data.get("thumbnail", {}).get("source", "")

                    if extract:
                        results.append(self.create_result(
                            query=query,
                            entity_type="wikipedia_article",
                            entity=title,
                            attribute="encyclopedic_summary",
                            value=extract[:300],
                            url=page_url,
                            confidence=0.95,
                            status=VerificationStatus.VERIFIED,
                            evidence=extract,
                            raw_reference=thumbnail
                        ))
            self.success_count += 1
        except Exception:
            pass

        self.total_execution_time += (time.time() - start)
        return results
