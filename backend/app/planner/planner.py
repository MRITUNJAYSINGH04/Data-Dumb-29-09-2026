import json
import httpx
from typing import List, Dict, Any
from backend.app.core.config import settings
from backend.app.schemas.investigation import InvestigationInput, InvestigationMode

class ResearchPlanner:
    """
    AI Research Planner:
    Determines exactly which OSINT modules are relevant based on input identifiers
    and investigation mode. Avoids executing irrelevant modules.
    """

    def plan_modules(self, input_data: InvestigationInput) -> List[str]:
        # If AI Provider is openai/anthropic/ollama and configured, we can do an LLM-assisted plan,
        # but always have deterministic heuristic matching as a dependable foundation.
        modules = set()

        has_name = bool(input_data.name and input_data.name.strip())
        has_company = bool(input_data.company and input_data.company.strip())
        has_email = bool(input_data.email and input_data.email.strip())
        has_username = bool(input_data.username and input_data.username.strip())
        has_phone = bool(input_data.phone and input_data.phone.strip())
        has_domain = bool(input_data.domain and input_data.domain.strip())
        has_urls = bool(input_data.profile_urls or input_data.website_urls)

        # Extract domain from email if domain was not provided
        inferred_domain = None
        if has_email and "@" in input_data.email:
            parts = input_data.email.split("@")
            if len(parts) == 2 and "." in parts[1]:
                domain_cand = parts[1].lower()
                common_freemail = {"gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "icloud.com", "proton.me", "protonmail.com"}
                if domain_cand not in common_freemail:
                    inferred_domain = domain_cand

        effective_domain = input_data.domain or inferred_domain

        # Core Search is relevant for name, company, email, username or domain
        if has_name or has_company or has_domain or has_username:
            modules.add("searxng")
            modules.add("web_search")

        # Name + Company combinations
        if has_name:
            modules.add("wikipedia")
            modules.add("github")
            modules.add("social_analyzer")
            if has_company or input_data.investigation_mode in [InvestigationMode.DEEP, InvestigationMode.PROFESSIONAL_VERIFICATION, InvestigationMode.LEAD_GENERATION]:
                modules.add("news")
                modules.add("company_domain")
                modules.add("sherlock")

        if has_company or effective_domain:
            modules.add("company_domain")
            modules.add("news")
            modules.add("wikipedia")
            if input_data.investigation_mode in [InvestigationMode.DEEP, InvestigationMode.COMPANY_INTELLIGENCE]:
                modules.add("theharvester")
                modules.add("photon")
                modules.add("spiderfoot")

        # Email identifier rules
        if has_email:
            modules.add("holehe")
            modules.add("web_search")
            if effective_domain:
                modules.add("company_domain")
                modules.add("theharvester")

        # Username identifier rules
        if has_username:
            modules.add("sherlock")
            modules.add("maigret")
            modules.add("social_analyzer")
            modules.add("github")

        # Phone identifier rules
        if has_phone:
            modules.add("phoneinfoga")

        # URLs provided
        if has_urls:
            modules.add("photon")
            modules.add("web_search")

        # Mode-based adjustments
        if input_data.investigation_mode == InvestigationMode.LEAD_GENERATION:
            modules.add("company_domain")
            modules.add("web_search")
            modules.add("news")

        if input_data.investigation_mode == InvestigationMode.COMPANY_INTELLIGENCE:
            modules.add("company_domain")
            modules.add("news")
            modules.add("theharvester")
            modules.add("photon")
            modules.add("wikipedia")
            modules.add("spiderfoot")

        # Deep investigation activates archive/wayback
        if input_data.investigation_mode == InvestigationMode.DEEP:
            modules.add("archive")
            if has_username or has_name:
                modules.add("maigret")
            if has_company or effective_domain:
                modules.add("spiderfoot")

        # Return ordered list
        priority_order = [
            "web_search", "searxng", "wikipedia", "github", "news",
            "company_domain", "sherlock", "maigret", "holehe", "phoneinfoga",
            "theharvester", "photon", "social_analyzer", "spiderfoot", "archive"
        ]
        
        ordered = [m for m in priority_order if m in modules]
        return ordered if ordered else ["web_search"]

planner = ResearchPlanner()
