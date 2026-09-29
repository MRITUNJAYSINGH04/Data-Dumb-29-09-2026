import time
import httpx
import shutil
from typing import List
from backend.app.adapters.base import BaseAdapter
from backend.app.schemas.investigation import InvestigationInput, NormalizedResult, VerificationStatus
from backend.app.core.config import settings

class SocialAnalyzerAdapter(BaseAdapter):
    name: str = "Social Analyzer"
    category: str = "social_profiles"
    description: str = "API & Web App for analyzing & finding a person's profile across 300+ social networks"
    version: str = "1.1.8"
    license: str = "AGPL-3.0"
    supported_identifiers: List[str] = ["username", "name"]

    def is_installed(self) -> bool:
        return shutil.which("social-analyzer") is not None

    async def execute(self, input_data: InvestigationInput) -> List[NormalizedResult]:
        start = time.time()
        self.execution_count += 1
        results: List[NormalizedResult] = []

        target = input_data.username or (input_data.name.lower().replace(" ", "") if input_data.name else None)
        if not target:
            return results

        # Check public technical profiles
        targets = [
            ("Devpost", f"https://devpost.com/{target}"),
            ("NPM", f"https://www.npmjs.com/~{target}"),
            ("Keybase", f"https://keybase.io/{target}")
        ]

        async with httpx.AsyncClient(timeout=4.0, headers={"User-Agent": settings.USER_AGENT}) as client:
            for platform, url in targets:
                try:
                    res = await client.get(url)
                    if res.status_code == 200 and "not found" not in res.text.lower():
                        results.append(self.create_result(
                            query=target,
                            entity_type="social_profile",
                            entity=target,
                            attribute="platform_presence",
                            value=f"{platform} profile (@{target})",
                            url=url,
                            confidence=0.85,
                            status=VerificationStatus.LIKELY,
                            evidence=f"Active public account identified on {platform}"
                        ))
                except Exception:
                    pass

        self.success_count += 1
        self.total_execution_time += (time.time() - start)
        return results
