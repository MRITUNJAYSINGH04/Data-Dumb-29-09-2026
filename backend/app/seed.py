import asyncio
from sqlalchemy.future import select
from datetime import datetime, timezone
from backend.app.core.database import engine, Base, AsyncSessionLocal
from backend.app.core.security import get_password_hash
from backend.app.models.user import User
from backend.app.models.investigation import Investigation, EvidenceItem
from backend.app.schemas.investigation import InvestigationInput, InvestigationMode, InvestigationStatus

async def seed_database():
    print("[UIE] Initializing database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        # Check if admin exists
        stmt = select(User).where(User.username == "admin")
        res = await db.execute(stmt)
        admin = res.scalars().first()
        if not admin:
            print("[UIE] Seeding default administrator account...")
            admin = User(
                username="admin",
                email="admin@universal-intel.local",
                full_name="Chief Intelligence Officer",
                hashed_password=get_password_hash("admin123456"),
                role="admin"
            )
            db.add(admin)
            await db.commit()
            print("[UIE] Default admin created: username='admin', password='admin123456'")

        # Check if sample investigation exists
        inv_stmt = select(Investigation)
        inv_res = await db.execute(inv_stmt)
        existing_inv = inv_res.scalars().first()

        if not existing_inv:
            print("[UIE] Seeding demonstration investigation...")
            sample_input = InvestigationInput(
                name="Mritunjay Singh",
                company="Acme AI",
                username="mritunjaysingh42",
                investigation_mode=InvestigationMode.QUICK
            )
            sample_inv = Investigation(
                id="inv-sample-demo-01",
                user_id=admin.id,
                title="Investigation: Mritunjay Singh",
                mode="quick",
                status=InvestigationStatus.COMPLETED.value,
                progress=100,
                current_step="Investigation finalized successfully",
                input_data=sample_input.model_dump(),
                modules_planned=["searxng", "web_search", "github", "wikipedia", "company_domain", "sherlock"],
                modules_completed=["searxng", "web_search", "github", "wikipedia", "company_domain", "sherlock"],
                entity_match_score=94,
                contradictions=[],
                lead_score={
                    "total_score": 92,
                    "icp_match": 24,
                    "decision_maker": 19,
                    "company_size": 14,
                    "industry_relevance": 14,
                    "technology_match": 9,
                    "recent_activity": 4,
                    "public_business_email": 4,
                    "evidence_confidence": 4,
                    "explanation": {
                        "icp_match": "High congruence across role and company metrics.",
                        "decision_maker": "Key technical leadership authority confirmed."
                    },
                    "outreach_brief": "Mritunjay Singh is affiliated with Acme AI with public expertise in intelligence architecture and distributed workflows.",
                    "suggested_icebreaker": "Hi Mritunjay, saw your work around scalable intelligence engines and would love to connect."
                },
                report_markdown="# Demonstration Investigation Dossier\n\nSubject: Mritunjay Singh\nIdentity Match Score: 94/100\nStatus: VERIFIED",
                report_json={"title": "Demonstration Investigation", "score": 94},
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            db.add(sample_inv)

            # Add sample evidence items
            db.add(EvidenceItem(
                investigation_id="inv-sample-demo-01",
                source="GitHub",
                source_type="code_repository",
                query="Mritunjay Singh",
                entity_type="github_user",
                entity="mritunjaysingh42",
                attribute="github_handle",
                value="@mritunjaysingh42 (Mritunjay Singh)",
                url="https://github.com/mritunjaysingh42",
                timestamp=datetime.now(timezone.utc).isoformat(),
                confidence=0.96,
                status="verified",
                evidence="Public GitHub profile verified with multiple active repositories."
            ))

            db.add(EvidenceItem(
                investigation_id="inv-sample-demo-01",
                source="Company Domain",
                source_type="infrastructure",
                query="acme.ai",
                entity_type="domain",
                entity="acme.ai",
                attribute="mail_exchanger",
                value="aspmx.l.google.com",
                url="https://dns.google/resolve?name=acme.ai&type=MX",
                timestamp=datetime.now(timezone.utc).isoformat(),
                confidence=0.98,
                status="verified",
                evidence="Authoritative DNS MX routing confirmed for domain acme.ai"
            ))

            await db.commit()
            print("[UIE] Sample investigation and evidence seeded.")

    print("[UIE] Database ready!")

if __name__ == "__main__":
    asyncio.run(seed_database())
