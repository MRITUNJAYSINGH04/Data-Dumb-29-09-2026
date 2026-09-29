import pytest
from backend.app.schemas.investigation import InvestigationInput, InvestigationMode, NormalizedResult, VerificationStatus
from backend.app.adapters.registry import tool_registry

@pytest.mark.asyncio
async def test_tool_registry_registration():
    all_tools = tool_registry.list_all()
    assert len(all_tools) == 50
    
    # Verify 10 tools per layer
    layer1 = [t for t in all_tools if t.layer == "layer1_infrastructure"]
    layer2 = [t for t in all_tools if t.layer == "layer2_corporate"]
    layer3 = [t for t in all_tools if t.layer == "layer3_identity"]
    layer4 = [t for t in all_tools if t.layer == "layer4_developer"]
    layer5 = [t for t in all_tools if t.layer == "layer5_media_synthesis"]

    assert len(layer1) == 10
    assert len(layer2) == 10
    assert len(layer3) == 10
    assert len(layer4) == 10
    assert len(layer5) == 10

    tool_names = [t.name for t in all_tools]
    assert "SpiderFoot" in tool_names
    assert "BuiltWith" in tool_names
    assert "Sherlock" in tool_names
    assert "GitHub" in tool_names
    assert "Wikipedia/Wikidata" in tool_names

@pytest.mark.asyncio
async def test_layer1_infrastructure_adapter():
    dns_adapter = tool_registry.get("dnsrecord")
    assert dns_adapter is not None
    inp = InvestigationInput(domain="example.com", investigation_mode=InvestigationMode.QUICK)
    results = await dns_adapter.execute(inp)
    assert len(results) >= 1
    for r in results:
        assert isinstance(r, NormalizedResult)
        assert r.source == "DNSRecord"
        assert 0.0 <= r.confidence <= 1.0
        assert r.url != ""

@pytest.mark.asyncio
async def test_layer2_corporate_adapter():
    bw_adapter = tool_registry.get("builtwith")
    assert bw_adapter is not None
    inp = InvestigationInput(domain="example.com", investigation_mode=InvestigationMode.QUICK)
    results = await bw_adapter.execute(inp)
    assert len(results) >= 1
    for r in results:
        assert isinstance(r, NormalizedResult)
        assert r.url.startswith("http")

@pytest.mark.asyncio
async def test_layer3_identity_adapter():
    sherlock_adapter = tool_registry.get("sherlock")
    assert sherlock_adapter is not None
    inp = InvestigationInput(username="johndoe", investigation_mode=InvestigationMode.QUICK)
    results = await sherlock_adapter.execute(inp)
    assert len(results) >= 1
    for r in results:
        assert isinstance(r, NormalizedResult)
        assert r.source == "Sherlock"
        assert r.url != ""

