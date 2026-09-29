import time
import httpx
from typing import List
from backend.app.adapters.base import BaseAdapter
from backend.app.schemas.investigation import InvestigationInput, NormalizedResult, VerificationStatus
from backend.app.core.config import settings

class GitHubAdapter(BaseAdapter):
    name: str = "GitHub"
    category: str = "code_repository"
    description: str = "Public GitHub REST API for developers, repositories, and organizations"
    version: str = "1.0.0"
    license: str = "MIT"
    supported_identifiers: List[str] = ["username", "name", "company", "email"]

    def is_installed(self) -> bool:
        return True

    async def execute(self, input_data: InvestigationInput) -> List[NormalizedResult]:
        start = time.time()
        self.execution_count += 1
        results: List[NormalizedResult] = []

        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": settings.USER_AGENT
        }
        if settings.GITHUB_TOKEN:
            headers["Authorization"] = f"token {settings.GITHUB_TOKEN}"

        target = input_data.username or input_data.name
        if not target:
            return results

        try:
            async with httpx.AsyncClient(timeout=8.0, headers=headers) as client:
                # 1. Search Users
                search_q = target
                if input_data.company and not input_data.username:
                    search_q = f"{target} {input_data.company}"

                res = await client.get("https://api.github.com/search/users", params={"q": search_q, "per_page": 3})
                if res.status_code == 200:
                    items = res.json().get("items", [])
                    for user in items:
                        username = user.get("login")
                        profile_url = user.get("html_url")
                        avatar_url = user.get("avatar_url")

                        # Fetch user details
                        user_res = await client.get(f"https://api.github.com/users/{username}")
                        if user_res.status_code == 200:
                            u_data = user_res.json()
                            full_name = u_data.get("name") or username
                            company = u_data.get("company")
                            bio = u_data.get("bio")
                            public_repos = u_data.get("public_repos", 0)
                            location = u_data.get("location")

                            results.append(self.create_result(
                                query=target,
                                entity_type="github_user",
                                entity=username,
                                attribute="github_handle",
                                value=f"@{username} ({full_name})",
                                url=profile_url,
                                confidence=0.92,
                                status=VerificationStatus.VERIFIED,
                                evidence=f"Public GitHub account with {public_repos} repositories. Bio: {bio or 'N/A'}",
                                raw_reference=avatar_url or ""
                            ))

                            if company:
                                results.append(self.create_result(
                                    query=username,
                                    entity_type="company",
                                    entity=username,
                                    attribute="employer",
                                    value=company.strip("@ "),
                                    url=profile_url,
                                    confidence=0.88,
                                    status=VerificationStatus.LIKELY,
                                    evidence=f"Self-declared company on GitHub profile: {company}"
                                ))

                            if location:
                                results.append(self.create_result(
                                    query=username,
                                    entity_type="location",
                                    entity=username,
                                    attribute="location",
                                    value=location,
                                    url=profile_url,
                                    confidence=0.82,
                                    status=VerificationStatus.LIKELY,
                                    evidence=f"Location specified on GitHub profile: {location}"
                                ))

                        # Also fetch top repos for user
                        repo_res = await client.get(f"https://api.github.com/users/{username}/repos", params={"sort": "updated", "per_page": 3})
                        if repo_res.status_code == 200:
                            for repo in repo_res.json():
                                repo_name = repo.get("name")
                                repo_url = repo.get("html_url")
                                desc = repo.get("description") or "Public repository"
                                lang = repo.get("language") or "General"
                                stars = repo.get("stargazers_count", 0)

                                results.append(self.create_result(
                                    query=username,
                                    entity_type="github_repo",
                                    entity=username,
                                    attribute="repository",
                                    value=f"{repo_name} ({lang} - ★{stars})",
                                    url=repo_url,
                                    confidence=0.95,
                                    status=VerificationStatus.VERIFIED,
                                    evidence=desc
                                ))

            self.success_count += 1
        except Exception:
            pass

        self.total_execution_time += (time.time() - start)
        return results
