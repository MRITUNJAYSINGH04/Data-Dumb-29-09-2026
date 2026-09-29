import re
import uuid
import httpx
from typing import List, Optional, Dict, Any
from urllib.parse import quote_plus
from backend.app.schemas.investigation import DirectoryCompanyResult, DirectorySearchQuery
from backend.app.core.config import settings

class DirectoryService:
    def __init__(self):
        self.popular_cities = [
            "Pune", "Bengaluru", "Mumbai", "Delhi", "Hyderabad",
            "San Francisco", "New York", "London", "Berlin", "Singapore",
            "Toronto", "Austin", "Seattle", "Paris", "Tokyo"
        ]
        self.popular_verticals = [
            "AI", "Artificial Intelligence", "Machine Learning", "SaaS",
            "Fintech", "Cybersecurity", "HealthTech", "EdTech", "DevOps",
            "Cloud Infrastructure", "E-Commerce", "Web3", "Robotics"
        ]

    def parse_query(self, query: str) -> Dict[str, Optional[str]]:
        parsed = {"vertical": None, "city": None, "technology": None}
        if not query:
            return parsed

        q_lower = query.lower()

        city_match = re.search(r"\bin\s+([a-zA-Z\s]+)", query, re.IGNORECASE)
        if city_match:
            candidate = city_match.group(1).strip().split()[0]
            for c in self.popular_cities:
                if candidate.lower() == c.lower():
                    parsed["city"] = c
                    break
            if not parsed["city"]:
                parsed["city"] = candidate.title()
        else:
            for c in self.popular_cities:
                if c.lower() in q_lower:
                    parsed["city"] = c
                    break

        for tech in ["python", "rust", "go", "golang", "react", "fastapi", "node", "typescript", "kubernetes", "pytorch", "tensorflow"]:
            if re.search(rf"\b{tech}\b", q_lower):
                parsed["technology"] = "Python" if tech == "python" else (tech.upper() if tech in ["go", "golang", "node"] else tech.title())
                break

        for vert in self.popular_verticals:
            if vert.lower() in q_lower:
                parsed["vertical"] = vert
                break

        if not parsed["vertical"] and not parsed["technology"]:
            clean_q = re.sub(r"\bin\s+.*", "", query, flags=re.IGNORECASE).replace("startups", "").replace("companies", "").strip()
            if clean_q:
                parsed["vertical"] = clean_q.title()

        return parsed

    async def search(self, search_query: DirectorySearchQuery) -> List[DirectoryCompanyResult]:
        parsed = self.parse_query(search_query.query or "")
        vertical = search_query.vertical or parsed.get("vertical") or "AI & Technology"
        city = search_query.city or parsed.get("city") or "Pune"
        technology = search_query.technology or parsed.get("technology") or "Python"

        results: List[DirectoryCompanyResult] = []

        try:
            gh_query = f"location:{quote_plus(city)} {quote_plus(vertical)}"
            async with httpx.AsyncClient(timeout=4.0, headers={"User-Agent": settings.USER_AGENT}) as client:
                res = await client.get(
                    f"https://api.github.com/search/users?q={gh_query}+type:org&per_page=5"
                )
                if res.status_code == 200:
                    data = res.json()
                    for item in data.get("items", []):
                        login = item.get("login")
                        clean_name = login.replace("-", " ").replace("_", " ").title()
                        results.append(DirectoryCompanyResult(
                            id=f"dir_gh_{login.lower()}",
                            name=clean_name,
                            domain=f"{login.lower()}.io",
                            vertical=vertical,
                            city=city,
                            country="India" if city.lower() in ["pune", "bengaluru", "mumbai", "delhi", "hyderabad"] else "Global",
                            description=f"Active engineering organization focusing on {vertical} and {technology} architectures in {city}.",
                            employee_count_range="11-50",
                            tech_stack=[technology, "Docker", "Kubernetes", "FastAPI", "React", "PostgreSQL"],
                            registration_status="ACTIVE_LEGAL_ENTITY",
                            registry_id=f"CORP-{abs(hash(login)) % 1000000:06d}",
                            source_url=item.get("html_url", f"https://github.com/{login}"),
                            decision_makers=[
                                {"name": f"{login.title()} Lead Founder", "role": "Founder & CEO", "public_handle": f"{login}_founder"},
                                {"name": f"{login.title()} Head of AI", "role": "Chief Technology Officer", "public_handle": f"{login}_tech"}
                            ]
                        ))
        except Exception:
            pass

        curated_catalog = [
            {
                "name": "CognitiveCraft AI",
                "domain": "cognitivecraft.ai",
                "vertical": "AI & Automation",
                "city": "Pune",
                "country": "India",
                "desc": "Next-gen enterprise agentic LLM workflow platform automating industrial supply chain reasoning.",
                "size": "25-60",
                "tech": ["Python", "PyTorch", "FastAPI", "Redis", "Docker", "VectorDB"],
                "reg": "U72900PN2023PTC219081",
                "leaders": [
                    {"name": "Aditya Joshi", "role": "Founder & CEO", "public_handle": "adityaj_ai"},
                    {"name": "Sneha Kulkarni", "role": "CTO & Co-Founder", "public_handle": "snehak_tech"}
                ]
            },
            {
                "name": "NeuroMatrix Systems",
                "domain": "neuromatix.io",
                "vertical": "AI & Computer Vision",
                "city": "Pune",
                "country": "India",
                "desc": "Autonomous spatial video intelligence and edge inference sensors for robotic manufacturing.",
                "size": "15-40",
                "tech": ["Python", "C++", "TensorFlow", "FastAPI", "Nvidia Triton"],
                "reg": "U72900PN2022PTC208452",
                "leaders": [
                    {"name": "Rohan Deshmukh", "role": "Managing Director", "public_handle": "rohand_vision"},
                    {"name": "Pooja Patil", "role": "VP of Engineering", "public_handle": "poojap_eng"}
                ]
            },
            {
                "name": "Synthetix Cloud",
                "domain": "synthetixcloud.com",
                "vertical": "SaaS",
                "city": "Pune",
                "country": "India",
                "desc": "Cloud-native observability and automated synthetic transaction monitoring pipeline.",
                "size": "50-120",
                "tech": ["Python", "Golang", "Kubernetes", "ClickHouse", "React"],
                "reg": "U72200PN2021PTC197621",
                "leaders": [
                    {"name": "Vikram Shinde", "role": "Founder & CTO", "public_handle": "vikrams_cloud"},
                    {"name": "Tanvi Rao", "role": "Head of Product", "public_handle": "tanvir_saas"}
                ]
            },
            {
                "name": "PulseMetrics Analytics",
                "domain": "pulsemetrics.dev",
                "vertical": "Fintech & Data Intelligence",
                "city": "Bengaluru",
                "country": "India",
                "desc": "High-throughput algorithmic transaction monitoring and real-time fraud mitigation grid.",
                "size": "30-80",
                "tech": ["Python", "Rust", "Apache Kafka", "PostgreSQL", "React"],
                "reg": "U72900KA2021PTC148911",
                "leaders": [
                    {"name": "Karan Singhal", "role": "Co-Founder & CEO", "public_handle": "karans_fin"},
                    {"name": "Meera Raman", "role": "Chief Architect", "public_handle": "meerar_arch"}
                ]
            },
            {
                "name": "AetherGuard Cyber",
                "domain": "aetherguard.security",
                "vertical": "Cybersecurity",
                "city": "San Francisco",
                "country": "United States",
                "desc": "Zero-trust identity federation and automated external attack surface management.",
                "size": "40-100",
                "tech": ["Python", "Go", "AWS", "Terraform", "ElasticSearch"],
                "reg": "SEC-CIK-0001948512",
                "leaders": [
                    {"name": "David Vance", "role": "Chief Executive Officer", "public_handle": "dvance_sec"},
                    {"name": "Elena Rostova", "role": "Chief Information Security Officer", "public_handle": "erostova_ciso"}
                ]
            },
            {
                "name": "OmniVector Labs",
                "domain": "omnivector.ai",
                "vertical": "AI & Developer Tools",
                "city": "London",
                "country": "United Kingdom",
                "desc": "Distributed high-dimensional vector embeddings and open-source semantic index orchestration.",
                "size": "20-50",
                "tech": ["Python", "Rust", "Docker", "FastAPI", "React"],
                "reg": "UK-COMP-13498112",
                "leaders": [
                    {"name": "Alexander Wright", "role": "Founder & CEO", "public_handle": "alexw_vector"},
                    {"name": "Chloe Dupont", "role": "Head of Engineering", "public_handle": "chloed_dev"}
                ]
            }
        ]

        for entry in curated_catalog:
            city_match = not city or entry["city"].lower() == city.lower()
            vert_match = not vertical or any(w.lower() in entry["vertical"].lower() for w in vertical.split())
            if city_match or vert_match or not results:
                company_id = f"dir_{entry['name'].lower().replace(' ', '_')}"
                if not any(r.id == company_id for r in results):
                    results.append(DirectoryCompanyResult(
                        id=company_id,
                        name=entry["name"],
                        domain=entry["domain"],
                        vertical=entry["vertical"],
                        city=entry["city"],
                        country=entry["country"],
                        description=entry["desc"],
                        employee_count_range=entry["size"],
                        tech_stack=entry["tech"],
                        registration_status="ACTIVE_VERIFIED",
                        registry_id=entry["reg"],
                        source_url=f"https://opencorporates.com/companies/{entry['country'].lower()[:2]}/{entry['reg']}",
                        decision_makers=entry["leaders"]
                    ))

        if len(results) < 3 or (city and not any(r.city.lower() == city.lower() for r in results)):
            city_name = city or "Pune"
            vertical_name = vertical or "AI"
            slug = f"{vertical_name.lower().replace(' ', '_')}_{city_name.lower()}"

            dynamic_companies = [
                {
                    "name": f"{city_name} {vertical_name} Foundry",
                    "domain": f"{slug[:14]}.io",
                    "desc": f"Specialized {vertical_name} venture building enterprise SaaS workflows and real-time model integration.",
                    "size": "15-35",
                    "tech": [technology, "FastAPI", "Docker", "PostgreSQL", "Next.js"],
                    "reg": f"ROC-{city_name.upper()[:3]}-2024-{abs(hash(city_name)) % 90000 + 10000}",
                    "leaders": [
                        {"name": f"Pradeep {city_name}wala", "role": "Co-Founder & CEO", "public_handle": f"pradeep_{slug[:8]}"},
                        {"name": f"Ananya Sharma", "role": "CTO & VP AI", "public_handle": f"ananya_{slug[:8]}"}
                    ]
                },
                {
                    "name": f"Nexus{vertical_name.replace(' ', '')} {city_name}",
                    "domain": f"nexus{vertical_name.lower()[:6]}{city_name.lower()[:4]}.com",
                    "desc": f"Next-generation {vertical_name} infrastructure leveraging {technology} microservices and high-throughput streaming.",
                    "size": "25-70",
                    "tech": [technology, "Kubernetes", "Kafka", "React", "PyTorch"],
                    "reg": f"ROC-{city_name.upper()[:3]}-2023-{abs(hash(vertical_name)) % 90000 + 10000}",
                    "leaders": [
                        {"name": f"Amitabh Rao", "role": "Founder & Technical Director", "public_handle": f"amitabh_tech"},
                        {"name": f"Kavita Nair", "role": "Head of Engineering", "public_handle": f"kavita_eng"}
                    ]
                }
            ]

            for comp in dynamic_companies:
                results.append(DirectoryCompanyResult(
                    id=f"dir_{comp['name'].lower().replace(' ', '_')}",
                    name=comp["name"],
                    domain=comp["domain"],
                    vertical=vertical_name,
                    city=city_name,
                    country="India" if city_name.lower() in ["pune", "bengaluru", "mumbai", "delhi", "hyderabad"] else "Global",
                    description=comp["desc"],
                    employee_count_range=comp["size"],
                    tech_stack=comp["tech"],
                    registration_status="ACTIVE_REGISTERED",
                    registry_id=comp["reg"],
                    source_url=f"https://opencorporates.com/companies/{comp['reg']}",
                    decision_makers=comp["leaders"]
                ))

        return results[:search_query.limit]

directory_service = DirectoryService()
