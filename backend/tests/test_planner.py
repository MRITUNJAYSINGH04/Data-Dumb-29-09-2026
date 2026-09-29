import pytest
from backend.app.schemas.investigation import InvestigationInput, InvestigationMode
from backend.app.planner.planner import planner

def test_planner_name_and_company():
    inp = InvestigationInput(
        name="John Smith",
        company="Acme AI",
        investigation_mode=InvestigationMode.QUICK
    )
    modules = planner.plan_modules(inp)
    assert "web_search" in modules
    assert "wikipedia" in modules
    assert "github" in modules
    assert "news" in modules
    # Phone should be skipped because no phone was supplied!
    assert "phoneinfoga" not in modules
    assert "holehe" not in modules

def test_planner_email_only():
    inp = InvestigationInput(
        email="john@acme.ai",
        investigation_mode=InvestigationMode.QUICK
    )
    modules = planner.plan_modules(inp)
    assert "holehe" in modules
    assert "web_search" in modules
    assert "company_domain" in modules # Inferred domain acme.ai
    assert "phoneinfoga" not in modules

def test_planner_username_only():
    inp = InvestigationInput(
        username="johnsmith42",
        investigation_mode=InvestigationMode.QUICK
    )
    modules = planner.plan_modules(inp)
    assert "sherlock" in modules
    assert "maigret" in modules
    assert "social_analyzer" in modules
    assert "github" in modules
    assert "phoneinfoga" not in modules

def test_planner_phone_only():
    inp = InvestigationInput(
        phone="+919876543210",
        investigation_mode=InvestigationMode.QUICK
    )
    modules = planner.plan_modules(inp)
    assert "phoneinfoga" in modules
    assert "sherlock" not in modules
    assert "holehe" not in modules
