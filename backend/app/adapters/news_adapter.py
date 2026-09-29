import time
import httpx
from bs4 import BeautifulSoup
from typing import List
from urllib.parse import quote_plus
from backend.app.adapters.base import BaseAdapter
from backend.app.schemas.investigation import InvestigationInput, NormalizedResult, VerificationStatus
from backend.app.core.config import settings

class NewsAdapter(BaseAdapter):
    name: str = "News RSS"
    category: str = "news_media"
    description: str = "Public news syndication and press mention monitor"
    version: str = "1.0.0"
    license: str = "MIT"
    supported_identifiers: List[str] = ["name", "company", "domain"]

    def is_installed(self) -> bool:
        return True

    async def execute(self, input_data: InvestigationInput) -> List[NormalizedResult]:
        start = time.time()
        self.execution_count += 1
        results: List[NormalizedResult] = []

        query = input_data.name or input_data.company
        if not query:
            return results

        if input_data.company and input_data.name:
            search_terms = f"{input_data.name} {input_data.company}"
        else:
            search_terms = query

        rss_url = f"https://news.google.com/rss/search?q={quote_plus(search_terms)}&hl=en-US&gl=US&ceid=US:en"
        headers = {"User-Agent": settings.USER_AGENT}

        try:
            async with httpx.AsyncClient(timeout=8.0, headers=headers) as client:
                res = await client.get(rss_url)
                if res.status_code == 200:
                    soup = BeautifulSoup(res.text, "html.parser")
                    items = soup.find_all("item")[:4]
                    for item in items:
                        title_el = item.find("title")
                        link_el = item.find("link")
                        pub_date_el = item.find("pubdate")
                        source_el = item.find("source")

                        title = title_el.text if title_el else "News Mention"
                        link = link_el.text if link_el else ""
                        pub_date = pub_date_el.text if pub_date_el else ""
                        pub_source = source_el.text if source_el else "Press Media"

                        if title and link:
                            results.append(self.create_result(
                                query=search_terms,
                                entity_type="news_article",
                                entity=query,
                                attribute="news_mention",
                                value=f"{title} ({pub_source})",
                                url=link,
                                confidence=0.88,
                                status=VerificationStatus.VERIFIED,
                                evidence=f"Published {pub_date}. Press headline: {title}",
                                raw_reference=pub_source
                            ))
            self.success_count += 1
        except Exception:
            pass

        self.total_execution_time += (time.time() - start)
        return results
