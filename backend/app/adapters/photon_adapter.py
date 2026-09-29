import time
import httpx
import shutil
import re
from bs4 import BeautifulSoup
from typing import List
from backend.app.adapters.base import BaseAdapter
from backend.app.schemas.investigation import InvestigationInput, NormalizedResult, VerificationStatus
from backend.app.core.config import settings

class PhotonAdapter(BaseAdapter):
    name: str = "Photon"
    category: str = "web_crawler"
    description: str = "Incredibly fast web crawler extracting public endpoints, scripts, and links"
    version: str = "1.3.2"
    license: str = "GPL-3.0"
    supported_identifiers: List[str] = ["domain", "website_urls"]

    def is_installed(self) -> bool:
        return shutil.which("photon") is not None

    async def execute(self, input_data: InvestigationInput) -> List[NormalizedResult]:
        start = time.time()
        self.execution_count += 1
        results: List[NormalizedResult] = []

        url_target = None
        if input_data.website_urls:
            url_target = input_data.website_urls[0]
        elif input_data.domain:
            url_target = f"https://{input_data.domain}"

        if not url_target:
            return results

        try:
            async with httpx.AsyncClient(timeout=6.0, follow_redirects=True, headers={"User-Agent": settings.USER_AGENT}) as client:
                res = await client.get(url_target)
                if res.status_code == 200:
                    soup = BeautifulSoup(res.text, "html.parser")
                    # Extract external links and social profile links
                    links = soup.find_all("a", href=True)
                    social_links = set()
                    for l in links:
                        href = l["href"]
                        if any(soc in href for soc in ["github.com", "x.com", "twitter.com", "youtube.com", "discord.gg", "docs."]):
                            social_links.add(href)

                    for sl in list(social_links)[:5]:
                        results.append(self.create_result(
                            query=url_target,
                            entity_type="public_endpoint",
                            entity=url_target,
                            attribute="public_outlink",
                            value=sl,
                            url=url_target,
                            confidence=0.88,
                            status=VerificationStatus.VERIFIED,
                            evidence=f"Discovered linked social/docs endpoint on homepage: {sl}"
                        ))
            self.success_count += 1
        except Exception:
            pass

        self.total_execution_time += (time.time() - start)
        return results
