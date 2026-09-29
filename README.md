# Universal Intelligence Engine (UIE) - God's Eye B2B Reconnaissance Matrix

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI_0.111+-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com)
[![Next.js 14](https://img.shields.io/badge/Frontend-Next.js_14-black.svg?logo=next.js)](https://nextjs.org)
[![Docker](https://img.shields.io/badge/Deployment-Docker_Compose-2496ED.svg?logo=docker)](https://www.docker.com)
[![OSINT Tools](https://img.shields.io/badge/Tactical_Vectors-50_Tools_Active-cyan.svg)](#gods-eye-50-tool-reconnaissance-matrix)

**Universal Intelligence Engine (UIE)** is a production-grade, self-hostable, evidence-first autonomous OSINT and executive lead-intelligence platform upgraded with the **"God's Eye" Multi-Vector Reconnaissance Architecture**. It unifies multi-source reconnaissance across 50 distinct OSINT and B2B intelligence tools across 5 isolated tactical layers with concurrent socket orchestration, timestamped workspace isolation, automated entity resolution, contradiction detection, and multi-format reporting.

---

## God's Eye 50-Tool Reconnaissance Matrix

| Tactical Layer | Vectors (10 Tools per Layer) | Capabilities & Data Gathered |
| :--- | :--- | :--- |
| **Layer 1: Infrastructure & Perimeter Recon** | `SpiderFoot`, `theHarvester`, `Sublist3r`, `Amass`, `DNSRecord`, `Fierce`, `WAFW00F`, `Shodan`, `Censys`, `SecurityTrails` | DNS records (A/MX/TXT/NS), subdomains, CDN/WAF detection, cloud endpoints, exposed open ports & services, ASN mapping. |
| **Layer 2: Corporate & Business Intelligence** | `BuiltWith`, `Crunchbase`, `Clearbit`, `Hunter`, `Snov.io`, `ZoomInfo Proxy`, `Apollo`, `OpenCorporates`, `SEC EDGAR`, `Job Board Scraper` | Corporate incorporation numbers, SEC 10-K/D filings, tech stack fingerprints, funding rounds, employee headcount, hiring trends, verified public email patterns. |
| **Layer 3: Professional & Identity Recon** | `Sherlock`, `Maigret`, `SocialScan`, `GHunt`, `Holehe`, `Blackbird`, `H8mail`, `Metagoofil`, `SkyMem`, `Twint Archive` | Cross-platform public profile presence (GitHub, GitLab, Dev.to, Twitter, Gravatar, Kaggle), verified username handles, public document metadata, domain-level breach audit flags. |
| **Layer 4: Developer & Code Intelligence** | `GitHub`, `GitLab`, `NPMJS`, `PyPI`, `Docker Hub`, `Hacker News`, `StackOverflow`, `Pastebin`, `Bugcrowd/H1`, `Packagist` | Public code repositories, commit histories, package publisher profiles, container images, developer forum answers, vulnerability disclosure mentions. |
| **Layer 5: Media, News & Synthesis** | `NewsAPI`, `Google News RSS`, `Wayback Machine`, `Common Crawl`, `Wikipedia/Wikidata`, `X/Twitter Public`, `Reddit`, `Legal Gazette`, `Patent Office`, `God's Eye AI Synthesis` | Real-time news syndication, historical web snapshots, open web crawl graphs, biographical knowledge graphs, patent filings, public community discussions, unified AI dossier synthesis. |

---

## Workspace Directory Architecture

On target launch, the engine automatically provisions an isolated, timestamped target workspace:

```
investigations/[clean_target]_[timestamp]/
├── layer1_infrastructure/
│   ├── spiderfoot/result.json
│   ├── theharvester/result.json
│   ├── sublist3r/result.json
│   ├── amass/result.json
│   ├── dnsrecord/result.json
│   ├── fierce/result.json
│   ├── wafw00f/result.json
│   ├── shodan/result.json
│   ├── censys/result.json
│   └── securitytrails/result.json
├── layer2_corporate/
│   ├── builtwith/result.json
│   ├── crunchbase/result.json
│   ├── clearbit/result.json
│   ├── hunter/result.json
│   ├── snov_io/result.json
│   ├── zoominfo_proxy/result.json
│   ├── apollo/result.json
│   ├── opencorporates/result.json
│   ├── sec_edgar/result.json
│   └── job_board_scraper/result.json
├── layer3_identity/
│   ├── sherlock/result.json
│   ├── maigret/result.json
│   ├── socialscan/result.json
│   ├── ghunt/result.json
│   ├── holehe/result.json
│   ├── blackbird/result.json
│   ├── h8mail/result.json
│   ├── metagoofil/result.json
│   ├── skymem/result.json
│   └── twint_archive/result.json
├── layer4_developer/
│   ├── github/result.json
│   ├── gitlab/result.json
│   ├── npmjs/result.json
│   ├── pypi/result.json
│   ├── docker_hub/result.json
│   ├── hacker_news/result.json
│   ├── stackoverflow/result.json
│   ├── pastebin/result.json
│   ├── bugcrowd_hackerone/result.json
│   └── packagist/result.json
├── layer5_media_synthesis/
│   ├── newsapi/result.json
│   ├── google_news_rss/result.json
│   ├── wayback_machine/result.json
│   ├── common_crawl/result.json
│   ├── wikipedia_wikidata/result.json
│   ├── x_twitter_public/result.json
│   ├── reddit/result.json
│   ├── legal_gazette/result.json
│   ├── patent_office/result.json
│   └── gods_eye_ai_synthesis/result.json
├── gods_eye_master_brief.json        <-- Synthesized master dossier
└── gods_eye_qualified_leads.csv       <-- Tabular CRM lead acquisition ledger
```

---

## Key Features & Architecture

- **Unified Intelligence Input Form**: Submit targets by Name, Email, Phone, Handle, Company, Domain, Profile URLs, Location, or ICP criteria.
- **50-Tool Concurrent Orchestration**: Parallel asynchronous execution with `asyncio.Semaphore(12)` preventing socket exhaustion and rate-limit blocks.
- **Evidence-First Epistemics**: Distinguishes **VERIFIED**, **LIKELY**, **POSSIBLE**, and **UNCONFIRMED** claims with cryptographic timestamps and URL provenance.
- **Cross-Source Contradiction Detection**: Flags conflicting claims (diverging job titles, employer timelines) with automated analysis.
- **Entity Resolution Engine**: Computes composite **Identity Match Scores (0–100)** across all 50 vectors.
- **Executive Lead Qualification & ICP Scoring**: Calculates composite ICP fit scores (0–100) and automatically synthesizes personalized outreach research briefs and icebreakers.
- **Interactive Knowledge Graph**: Directed Neo4j-compatible topology model with Cypher export capabilities.
- **Comprehensive Dashboard (14 Dedicated Views)**:
  1. Dashboard Overview
  2. New Investigation Form
  3. Live Multi-Stage Progress View (50-Vector Tactical Matrix & Checkpoints)
  4. Person Intelligence Profile
  5. Company Intelligence & Domain Infrastructure
  6. Correlated Evidence Explorer & Provenance Ledger
  7. Entity Relationship Graph Visualizer
  8. Lead Scoring & Outreach Studio
  9. Search History & Audit Archive
  10. Tactical Vector & Tool Registry Manager (Tabs for Layers 1–5)
  11. API Key Access Center
  12. Global Engine Settings
  13. Data Retention & GDPR Privacy Sovereignty
  14. Multi-Format Export Center (Master Brief JSON, Leads CSV, Markdown, HTML/PDF)

---

## Safety & Compliance Requirements

1. **Lawful, Public & Permitted Data Only**: Adapters operate exclusively against publicly accessible, licensed, or open API-accessible registries.
2. **Zero LinkedIn Scraping**: In strict adherence to safety guidelines and terms of service, unauthorized browser automation or scraping of LinkedIn is prohibited.
3. **No Credential Abuse or Session Hijacking**: System excludes private social media, stolen credentials, leaked password dumps, and paywall bypasses. Breach tools operate in public audit mode only.
4. **GDPR / Privacy Sovereignty**: Full deletion controls, configurable retention horizons (e.g., 30 days), and immutable audit logging.

---

## Quickstart & Local Development

### Prerequisites

- **Python**: 3.11+
- **Node.js**: 18+ (tested on Node v24)
- **Git**

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/universal-intelligence-engine.git
cd "universal-intelligence-engine"
```

### 2. Backend Setup

```bash
# Windows PowerShell
& "C:\Users\singh\AppData\Local\Programs\Python\Python311\python.exe" -m venv backend\venv
& "backend\venv\Scripts\pip.exe" install -r backend\requirements.txt email-validator

# Run tests to verify setup
$env:PYTHONPATH="."
& "backend\venv\Scripts\pytest.exe" backend\tests

# Seed database and start FastAPI server
& "backend\venv\Scripts\python.exe" backend\app\seed.py
& "backend\venv\Scripts\uvicorn.exe" backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

Backend API will be available at: `http://localhost:8000`  
Swagger API Docs: `http://localhost:8000/docs`

### 3. Frontend Setup

```bash
cd frontend
npm install
npm run build
npm run dev
```

Frontend Dashboard will be available at: `http://localhost:3000`

---

## Docker Deployment (Single-Server)

UIE includes a complete multi-container production `docker-compose.yml` orchestrating:
- `frontend` (Next.js on port 3000)
- `backend` (FastAPI core on port 8000)
- `worker` (OSINT async runner)
- `postgres` (PostgreSQL 16 on port 5432)
- `redis` (Message broker on port 6379)
- `searxng` (Self-hosted search layer on port 8080)
- Optional `neo4j` (Graph engine on port 7474)
- Optional `ollama` (Local LLM on port 11434)

### Launching Docker Compose

```bash
# 1. Copy environment template
cp .env.example .env

# 2. Start core services
docker compose up --build -d

# 3. Start with optional Neo4j graph & Ollama local AI
docker compose --profile graph --profile local-ai up --build -d
```

---

## Cloud Deployment Guide

### Frontend (Vercel)
1. Import repository on [Vercel](https://vercel.com).
2. Set Root Directory to `frontend`.
3. Configure environment variable:
   `NEXT_PUBLIC_API_URL=https://your-backend-domain.com/api`
4. Deploy.

### Backend & Workers (Railway / Render / Fly.io)
1. Deploy `backend/Dockerfile`.
2. Connect managed database:
   - **PostgreSQL**: [Supabase](https://supabase.com) or Railway Postgres.
   - **Redis**: [Upstash](https://upstash.com) or Railway Redis.
3. Configure environment variables in dashboard:
   - `DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dbname`
   - `REDIS_URL=rediss://default:pass@host:port`
   - `SECRET_KEY=your-secure-random-32-byte-hex`
   - `AI_PROVIDER=heuristic` (or `openai`)

### Search Layer (SearXNG on VPS / Docker)
- Deploy SearXNG on any VPS using the provided `docker/searxng/settings.yml` and point `SEARXNG_URL` to it.

---

## Adding an OSINT Adapter

All adapters inherit from `BaseAdapter` in [`backend/app/adapters/base.py`](file:///c:/Users/singh/OneDrive/Documents/DATA%20TOOL/backend/app/adapters/base.py):

```python
from backend.app.adapters.base import BaseAdapter
from backend.app.schemas.investigation import InvestigationInput, NormalizedResult, VerificationStatus

class CustomAdapter(BaseAdapter):
    name: str = "Custom Tool"
    category: str = "public_registry"
    description: str = "Queries public corporate registries"
    version: str = "1.0.0"
    license: str = "MIT"
    supported_identifiers = ["company", "domain"]

    def is_installed(self) -> bool:
        return True

    async def execute(self, input_data: InvestigationInput) -> list[NormalizedResult]:
        # Perform query and return NormalizedResult objects
        return [
            self.create_result(
                query=input_data.company,
                entity_type="company",
                entity=input_data.company,
                attribute="registration_number",
                value="REG-109283",
                url="https://registry.example.org/record",
                confidence=0.95,
                status=VerificationStatus.VERIFIED,
                evidence="Verified registration entry in public gazette"
            )
        ]
```

Register your adapter in [`backend/app/adapters/__init__.py`](file:///c:/Users/singh/OneDrive/Documents/DATA%20TOOL/backend/app/adapters/__init__.py) with:
```python
tool_registry.register(CustomAdapter())
```

---

## API Documentation

- `POST /api/investigations`: Launch new investigation across 50 tactical vectors.
- `GET /api/investigations`: List all past investigations.
- `GET /api/investigations/{id}`: Retrieve investigation status, workspace dir, and report.
- `GET /api/investigations/{id}/vectors`: Retrieve live execution matrix for all 50 vectors across 5 layers.
- `GET /api/investigations/{id}/master-brief`: Retrieve or download `gods_eye_master_brief.json` (`?download=true`).
- `GET /api/investigations/{id}/leads-csv`: Download `gods_eye_qualified_leads.csv` as tabular CRM ledger.
- `GET /api/investigations/{id}/results`: Retrieve normalized evidence ledger.
- `GET /api/investigations/{id}/graph`: Retrieve knowledge graph or Cypher script (`?format=cypher`).
- `POST /api/leads/score`: Calculate ICP fit score and outreach brief.
- `POST /api/export`: Export dossier in `json`, `csv`, `markdown`, or `html` format.
- `GET /api/tools`: List tool statuses and metrics for all 50 adapters.
- `POST /api/tools/{id}/toggle`: Enable or disable an adapter.
- `POST /api/privacy/purge`: Permanently purge all user investigation records.

---

## License

Universal Intelligence Engine is released under the **MIT License**.
