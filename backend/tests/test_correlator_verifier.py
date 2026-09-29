import pytest
from datetime import datetime, timezone
from backend.app.schemas.investigation import InvestigationInput, InvestigationMode, NormalizedResult, VerificationStatus
from backend.app.correlator.correlator import correlator
from backend.app.verifier.verifier import verifier
from backend.app.lead_scorer.lead_scorer import lead_scorer

def test_correlator_scoring():
    inp = InvestigationInput(
        name="Alex Rivera",
        company="Vanguard Dynamics",
        username="arivera",
        investigation_mode=InvestigationMode.QUICK
    )
    mock_results = [
        NormalizedResult(
            source="GitHub", source_type="code", query="Alex Rivera",
            entity_type="person", entity="Alex Rivera", attribute="job_title",
            value="VP of Engineering at Vanguard Dynamics", url="https://github.com/arivera",
            timestamp=datetime.now(timezone.utc).isoformat(), confidence=0.9,
            status=VerificationStatus.VERIFIED, evidence="Bio says VP of Engineering at Vanguard Dynamics"
        ),
        NormalizedResult(
            source="News RSS", source_type="news", query="Alex Rivera",
            entity_type="person", entity="Alex Rivera", attribute="employer",
            value="Vanguard Dynamics", url="https://news.google.com/article1",
            timestamp=datetime.now(timezone.utc).isoformat(), confidence=0.85,
            status=VerificationStatus.VERIFIED, evidence="Press article mentions Alex Rivera joining Vanguard Dynamics"
        )
    ]

    score, signals = correlator.correlate(inp, mock_results)
    assert score >= 50
    assert any(s["signal"] == "name_congruence" for s in signals)
    assert any(s["signal"] == "company_domain_alignment" for s in signals)

def test_verifier_contradiction_detection():
    mock_results = [
        NormalizedResult(
            source="Source A", source_type="public_web", query="target",
            entity_type="person", entity="Target", attribute="job_title",
            value="Software Engineer", url="https://source-a.com",
            timestamp=datetime.now(timezone.utc).isoformat(), confidence=0.8,
            status=VerificationStatus.LIKELY, evidence="Listed as Software Engineer"
        ),
        NormalizedResult(
            source="Source B", source_type="press", query="target",
            entity_type="person", entity="Target", attribute="job_title",
            value="Chief Technology Officer", url="https://source-b.com",
            timestamp=datetime.now(timezone.utc).isoformat(), confidence=0.85,
            status=VerificationStatus.LIKELY, evidence="Press release mentions CTO appointment"
        )
    ]

    deduped, contradictions = verifier.verify_and_deduplicate(mock_results)
    assert len(deduped) == 2
    assert len(contradictions) == 1
    assert contradictions[0].attribute == "job_title"

def test_lead_scoring():
    inp = InvestigationInput(
        name="Sarah Chen",
        company="Synthetix AI",
        target_role="CTO",
        target_industry="Artificial Intelligence",
        target_company_size="51-200",
        investigation_mode=InvestigationMode.LEAD_GENERATION
    )
    mock_results = [
        NormalizedResult(
            source="GitHub", source_type="code", query="Sarah Chen",
            entity_type="person", entity="Sarah Chen", attribute="job_title",
            value="CTO at Synthetix AI", url="https://github.com/sarahchen",
            timestamp=datetime.now(timezone.utc).isoformat(), confidence=0.95,
            status=VerificationStatus.VERIFIED, evidence="CTO and Co-founder at Synthetix AI. Expert in Python, AI, and Cloud."
        )
    ]
    breakdown = lead_scorer.score_lead(inp, mock_results, 90)
    assert breakdown.total_score >= 70
    assert breakdown.decision_maker >= 15
    assert breakdown.outreach_brief is not None
    assert breakdown.suggested_icebreaker is not None
