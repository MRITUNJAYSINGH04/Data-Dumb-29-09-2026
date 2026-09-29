from fastapi import APIRouter, Depends
from backend.app.schemas.investigation import InvestigationInput, LeadScoreBreakdown
from backend.app.core.deps import get_current_user
from backend.app.models.user import User
from backend.app.lead_scorer.lead_scorer import lead_scorer

router = APIRouter(prefix="/leads", tags=["Lead Generation"])

@router.post("/score", response_model=LeadScoreBreakdown)
async def score_lead_endpoint(
    input_data: InvestigationInput,
    current_user: User = Depends(get_current_user)
):
    """Calculates ICP match, decision maker authority, and generates outreach briefs."""
    return lead_scorer.score_lead(input_data, [], 85)
