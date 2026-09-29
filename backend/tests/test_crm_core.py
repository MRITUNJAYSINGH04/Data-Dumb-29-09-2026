import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from backend.app.main import app
from backend.app.core.crm_seed import seed_crm_database

@pytest_asyncio.fixture(autouse=True)
async def init_crm_db():
    await seed_crm_database()

@pytest.mark.asyncio
async def test_crm_disposition_counts():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/crm/leads/stats/dispositions")
        assert response.status_code == 200
        data = response.json()
        assert "counts" in data
        assert "Open Leads" in data["counts"]
        assert "Interested" in data["counts"]
        assert "Follow UP" in data["counts"]
        assert data["total"] >= 17

@pytest.mark.asyncio
async def test_crm_leads_crud_and_lifecycle():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Create
        create_payload = {
            "name": "Pooja Hegde Test",
            "company_name": "Test Healthcare Diagnostics",
            "designation": "Head of Corporate Care",
            "email": "pooja.test@diagnostics.in",
            "phone": "+91 9988776655",
            "city": "Bengaluru",
            "industry": "Healthcare",
            "calling_disposition": "New",
            "lead_score": 88
        }
        res = await ac.post("/api/crm/leads", json=create_payload)
        assert res.status_code == 201
        lead = res.json()
        lead_id = lead["id"]
        assert lead["calling_disposition"] == "New"

        # Update disposition to Interested
        update_payload = {"calling_disposition": "Interested"}
        patch_res = await ac.patch(f"/api/crm/leads/{lead_id}", json=update_payload)
        assert patch_res.status_code == 200
        assert patch_res.json()["calling_disposition"] == "Interested"

@pytest.mark.asyncio
async def test_transactional_lead_conversion():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Convert lead-xitij
        convert_payload = {
            "create_opportunity": True,
            "deal_title": "Parmar Capital Executive Retainer Mandate",
            "deal_value": 1800000.0,
            "stage": "discovery"
        }
        res = await ac.post("/api/crm/leads/lead-xitij/convert", json=convert_payload)
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "success"
        assert data["company_id"] is not None
        assert data["contact_id"] is not None
        assert data["opportunity_id"] is not None

@pytest.mark.asyncio
async def test_opportunity_stage_move_kanban():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Move deal-zomato-eap to negotiation
        move_payload = {"new_stage": "negotiation"}
        res = await ac.patch("/api/crm/opportunities/deal-zomato-eap/stage", json=move_payload)
        assert res.status_code == 200
        data = res.json()
        assert data["stage"] == "negotiation"
        assert data["probability"] == 75

@pytest.mark.asyncio
async def test_tasks_urgency_buckets():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res_today = await ac.get("/api/crm/tasks?urgency=today")
        assert res_today.status_code == 200
        assert len(res_today.json()) >= 1

        res_overdue = await ac.get("/api/crm/tasks?urgency=overdue")
        assert res_overdue.status_code == 200
        assert len(res_overdue.json()) >= 1

@pytest.mark.asyncio
async def test_analytics_dashboard_metrics():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/api/crm/analytics/dashboard")
        assert res.status_code == 200
        data = res.json()
        assert data["total_leads"] >= 17
        assert data["pipeline_value_inr"] > 0
        assert "stage_breakdown" in data
        assert len(data["reps_performance"]) >= 1

@pytest.mark.asyncio
async def test_website_intelligence_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.post("/api/crm/intelligence/scan-website", json={"url": "https://www.thefullcircle.in"})
        assert res.status_code == 200
        data = res.json()
        assert "domain" in data
        assert "lead_score" in data
        assert data["lead_score"] >= 50
        assert "score_breakdown" in data

