import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.future import select
from backend.app.main import app
from backend.app.core.database import engine, Base, AsyncSessionLocal
from backend.app.core.security import get_password_hash
from backend.app.models.user import User

@pytest_asyncio.fixture(autouse=True)
async def init_test_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        try:
            from sqlalchemy import text
            await conn.execute(text("ALTER TABLE investigations ADD COLUMN workspace_dir VARCHAR"))
        except Exception:
            pass

    async with AsyncSessionLocal() as db:
        stmt = select(User).where(User.username == "admin")
        res = await db.execute(stmt)
        admin = res.scalars().first()
        if not admin:
            default_admin = User(
                username="admin",
                email="admin@universal-intel.local",
                full_name="Chief Intelligence Officer",
                hashed_password=get_password_hash("admin123456"),
                role="admin"
            )
            db.add(default_admin)
            await db.commit()

@pytest.mark.asyncio
async def test_health_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["adapters_count"] >= 12

@pytest.mark.asyncio
async def test_tools_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/tools")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 12
        assert any(t["name"] == "GitHub" for t in data)

@pytest.mark.asyncio
async def test_lead_score_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        payload = {
            "name": "Marcus Vance",
            "company": "CyberShield Systems",
            "target_role": "VP of Security",
            "target_industry": "Cybersecurity",
            "investigation_mode": "lead_generation"
        }
        response = await ac.post("/api/leads/score", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "total_score" in data
        assert "outreach_brief" in data

@pytest.mark.asyncio
async def test_directory_search():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Test POST search
        post_res = await ac.post("/api/directory/search", json={"query": "AI startups in Pune"})
        assert post_res.status_code == 200
        post_data = post_res.json()
        assert isinstance(post_data, list)
        assert len(post_data) > 0
        assert "name" in post_data[0]
        assert "decision_makers" in post_data[0]

        # Test GET search
        get_res = await ac.get("/api/directory/search?query=SaaS+companies+using+Python")
        assert get_res.status_code == 200
        get_data = get_res.json()
        assert isinstance(get_data, list)
        assert len(get_data) > 0

