import time
import httpx
from typing import List
from backend.app.adapters.base import BaseAdapter
from backend.app.schemas.investigation import InvestigationInput, NormalizedResult, VerificationStatus
from backend.app.core.config import settings

class WaybackArchiveAdapter(BaseAdapter):
    name: str = "Wayback Machine"
    category: str = "web_archive"
    description: str = "Internet Archive Wayback Machine API for historical web snapshots"
    version: str = "1.0.0"
    license: str = "Public Domain"
    supported_identifiers: List[str] = ["domain", "website_urls"]

    def is_installed(self) -> bool:
        return True

    async def execute(self, input_data: InvestigationInput) -> List[NormalizedResult]:
        start = time.time()
        self.execution_count += 1
        results: List[NormalizedResult] = []

        target = input_data.domain or (input_data.website_urls[0] if input_data.website_urls else None)
        if not target:
            return results

        clean_url = target if target.startswith("http") else f"https://{target}"

        try:
            async with httpx.AsyncClient(timeout=6.0, headers={"User-Agent": settings.USER_AGENT}) as client:
                res = await client.get(f"https://archive.org/wayback/available?url={clean_url}")
                if res.status_code == 200:
                    data = res.json()
                    closest = data.get("archived_snapshots", {}).get("closest", {})
                    if closest.get("available"):
                        snapshot_url = closest.get("url")
                        timestamp = closest.get("timestamp")

                        results.append(self.create_result(
                            query=target,
                            entity_type="web_snapshot",
                            entity=target,
                            attribute="historical_snapshot",
                            value=f"Archived Snapshot from {timestamp[:8]}",
                            url=snapshot_url,
                            confidence=0.95,
                            status=VerificationStatus.VERIFIED,
                            evidence=f"Public historical snapshot preserved in Internet Archive at {timestamp}"
                        ))
            self.success_count += 1
        except Exception:
            pass

        self.total_execution_time += (time.time() - start)
        return results
