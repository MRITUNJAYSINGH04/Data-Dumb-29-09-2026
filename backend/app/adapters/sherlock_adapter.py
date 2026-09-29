import time
import httpx
import shutil
import asyncio
from typing import List
from backend.app.adapters.base import BaseAdapter
from backend.app.schemas.investigation import InvestigationInput, NormalizedResult, VerificationStatus
from backend.app.core.config import settings

class SherlockAdapter(BaseAdapter):
    name: str = "Sherlock"
    category: str = "username_osint"
    description: str = "Hunt down social media accounts by username across social networks"
    version: str = "0.14.3"
    license: str = "MIT"
    supported_identifiers: List[str] = ["username", "name"]

    def is_installed(self) -> bool:
        return shutil.which("sherlock") is not None

    async def execute(self, input_data: InvestigationInput) -> List[NormalizedResult]:
        start = time.time()
        self.execution_count += 1
        results: List[NormalizedResult] = []

        target = input_data.username or (input_data.name.lower().replace(" ", "") if input_data.name else None)
        if not target:
            return results

        # Key public developer and tech community profile endpoints
        platforms = [
            {"name": "GitLab", "url": f"https://gitlab.com/{target}", "check": f"https://gitlab.com/{target}"},
            {"name": "Reddit", "url": f"https://reddit.com/user/{target}", "check": f"https://www.reddit.com/user/{target}/about.json"},
            {"name": "Dev.to", "url": f"https://dev.to/{target}", "check": f"https://dev.to/api/users/by_username?url={target}"},
            {"name": "Medium", "url": f"https://medium.com/@{target}", "check": f"https://medium.com/@{target}"},
            {"name": "HackerNews", "url": f"https://news.ycombinator.com/user?id={target}", "check": f"https://hacker-news.firebaseio.com/v0/user/{target}.json"},
            {"name": "PyPI", "url": f"https://pypi.org/user/{target}/", "check": f"https://pypi.org/user/{target}/"},
            {"name": "DockerHub", "url": f"https://hub.docker.com/u/{target}", "check": f"https://hub.docker.com/v2/users/{target}/"},
        ]

        async with httpx.AsyncClient(timeout=4.0, headers={"User-Agent": settings.USER_AGENT}) as client:
            tasks = []
            for p in platforms:
                tasks.append(self._check_platform(client, p, target))
            found_profiles = await asyncio.gather(*tasks, return_exceptions=True)

            for item in found_profiles:
                if isinstance(item, NormalizedResult):
                    results.append(item)

        self.success_count += 1
        self.total_execution_time += (time.time() - start)
        return results

    async def _check_platform(self, client: httpx.AsyncClient, platform: dict, username: str) -> NormalizedResult | None:
        try:
            res = await client.get(platform["check"])
            if res.status_code == 200:
                # Discard generic 404 disguised as 200 if necessary
                if "Not Found" not in res.text[:200]:
                    return self.create_result(
                        query=username,
                        entity_type="user_profile",
                        entity=username,
                        attribute="profile_handle",
                        value=f"{platform['name']} profile for @{username}",
                        url=platform["url"],
                        confidence=0.88,
                        status=VerificationStatus.VERIFIED,
                        evidence=f"Active public account detected on {platform['name']}."
                    )
        except Exception:
            pass
        return None
