import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.future import select
from sqlalchemy import text
from backend.app.main import app
from backend.app.core.database import engine, Base, AsyncSessionLocal
from backend.app.models.user import User
from backend.app.core.security import get_password_hash
from backend.app.services.investigation_service import investigation_service

@pytest_asyncio.fixture(autouse=True)
async def init_test_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        try:
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
async def test_end_to_end_investigation_flow():
    payload = {
        "name": "Mritunjay Singh",
        "company": "Acme AI",
        "investigation_mode": "quick"
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Create investigation
        res = await ac.post("/api/investigations", json=payload)
        assert res.status_code == 201
        inv_data = res.json()
        inv_id = inv_data["id"]
        assert inv_data["status"] == "QUEUED"
        assert len(inv_data["modules_planned"]) > 0
        assert inv_data["workspace_dir"] is not None

        # Execute investigation job synchronously in test
        await investigation_service.run_investigation_job(AsyncSessionLocal, inv_id)

        # Retrieve completed investigation
        get_res = await ac.get(f"/api/investigations/{inv_id}")
        assert get_res.status_code == 200
        completed = get_res.json()
        assert completed["status"] == "COMPLETED"
        assert completed["progress"] == 100
        assert completed["results_count"] > 0
        assert completed["entity_match_score"] > 0
        assert completed["report_markdown"] is not None

        # Retrieve evidence results
        results_res = await ac.get(f"/api/investigations/{inv_id}/results")
        assert results_res.status_code == 200
        evidence_list = results_res.json()
        assert len(evidence_list) > 0
        for ev in evidence_list:
            assert "url" in ev
            assert "confidence" in ev
            assert "status" in ev

        # Retrieve graph
        graph_res = await ac.get(f"/api/investigations/{inv_id}/graph")
        assert graph_res.status_code == 200
        graph_data = graph_res.json()
        assert len(graph_data["nodes"]) > 0
        assert len(graph_data["edges"]) > 0

        # Retrieve cypher export
        cypher_res = await ac.get(f"/api/investigations/{inv_id}/graph?format=cypher")
        assert cypher_res.status_code == 200
        assert "MERGE (n:" in cypher_res.json()["cypher"]

        # Retrieve report
        rep_res = await ac.get(f"/api/investigations/{inv_id}/report")
        assert rep_res.status_code == 200
        assert "Universal Intelligence Engine" in rep_res.json()["report_markdown"]

        # Test CSV and JSON Export
        export_json = await ac.post("/api/export", json={"investigation_id": inv_id, "format": "json"})
        assert export_json.status_code == 200
        assert export_json.headers["content-type"] == "application/json"

        export_csv = await ac.post("/api/export", json={"investigation_id": inv_id, "format": "csv"})
        assert export_csv.status_code == 200
        assert "text/csv" in export_csv.headers["content-type"]

        # God's Eye 50-Vector Endpoint Verifications
        # 1. Master Brief
        brief_res = await ac.get(f"/api/investigations/{inv_id}/master-brief")
        assert brief_res.status_code == 200
        brief_json = brief_res.json()
        assert brief_json["investigation_id"] == inv_id
        assert "vector_execution_summary" in brief_json
        assert len(brief_json["vector_execution_summary"]) == 50
        assert "verified_signals" in brief_json

        # 2. Leads CSV
        leads_csv_res = await ac.get(f"/api/investigations/{inv_id}/leads-csv")
        assert leads_csv_res.status_code == 200
        assert "text/csv" in leads_csv_res.headers["content-type"]

        # 3. Vectors List
        vectors_res = await ac.get(f"/api/investigations/{inv_id}/vectors")
        assert vectors_res.status_code == 200
        vectors_list = vectors_res.json()
        assert len(vectors_list) == 50

        # 4. Omni Leads Endpoint
        leads_res = await ac.get(f"/api/investigations/{inv_id}/leads")
        assert leads_res.status_code == 200
        leads_data = leads_res.json()
        assert isinstance(leads_data, list)
        assert len(leads_data) > 0
        assert "lead_score" in leads_data[0]
        assert "email_status" in leads_data[0]

        # 5. Omni Logs Endpoint
        logs_res = await ac.get(f"/api/investigations/{inv_id}/logs")
        assert logs_res.status_code == 200
        logs_data = logs_res.json()
        assert isinstance(logs_data, list)
        assert len(logs_data) > 0
        assert "level" in logs_data[0]

        # 6. Omni Master Export (CSV)
        omni_csv_res = await ac.get(f"/api/investigations/{inv_id}/omni-export?format=csv")
        assert omni_csv_res.status_code == 200
        assert "text/csv" in omni_csv_res.headers["content-type"]
        assert "attachment" in omni_csv_res.headers.get("content-disposition", "")

        # 7. Omni Master Export (JSON)
        omni_json_res = await ac.get(f"/api/investigations/{inv_id}/omni-export?format=json")
        assert omni_json_res.status_code == 200
        assert "application/json" in omni_json_res.headers["content-type"]
        omni_json_body = omni_json_res.json()
        assert "total_vectors_executed" in omni_json_body
        assert "qualified_leads" in omni_json_body


