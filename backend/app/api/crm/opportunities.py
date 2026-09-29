from typing import Optional, List
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from backend.app.core.database import get_db
from backend.app.core.permissions import require_permission
from backend.app.models.crm import Opportunity, PipelineStage, Activity, CRMAuditLog
from backend.app.models.user import User

router = APIRouter(prefix="/opportunities", tags=["CRM - Opportunities"])

class OpportunityCreateSchema(BaseModel):
    title: str
    company_id: str
    company_name: str
    contact_name: Optional[str] = ""
    contact_email: Optional[str] = ""
    value: float # in ₹ INR
    stage: Optional[str] = "discovery" # discovery, proposal, negotiation, won, lost
    probability: Optional[int] = 30
    priority: Optional[str] = "Medium"
    expected_close_date: Optional[datetime] = None

class OpportunityUpdateSchema(BaseModel):
    title: Optional[str] = None
    value: Optional[float] = None
    stage: Optional[str] = None
    probability: Optional[int] = None
    priority: Optional[str] = None
    expected_close_date: Optional[datetime] = None

class StageMoveSchema(BaseModel):
    new_stage: str # discovery, proposal, negotiation, won, lost
    probability: Optional[int] = None

@router.get("/stages")
async def list_stages(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("opportunities.view"))
):
    stmt = select(PipelineStage).order_by(PipelineStage.display_order.asc())
    res = await db.execute(stmt)
    return res.scalars().all()

@router.get("")
async def list_opportunities(
    stage: Optional[str] = None,
    owner_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("opportunities.view"))
):
    stmt = select(Opportunity)
    if stage and stage != "all":
        stmt = stmt.where(Opportunity.stage == stage)
    if owner_id:
        stmt = stmt.where(Opportunity.owner_id == owner_id)

    stmt = stmt.order_by(Opportunity.created_at.desc())
    res = await db.execute(stmt)
    return res.scalars().all()

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_opportunity(
    payload: OpportunityCreateSchema,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("opportunities.create"))
):
    opp = Opportunity(
        org_id="org-thefullcircle",
        company_id=payload.company_id,
        title=payload.title,
        company_name=payload.company_name,
        contact_name=payload.contact_name or "",
        contact_email=payload.contact_email or "",
        value=payload.value,
        stage=payload.stage or "discovery",
        probability=payload.probability or 30,
        priority=payload.priority or "Medium",
        expected_close_date=payload.expected_close_date,
        owner_id=current_user.id,
        owner_name=current_user.full_name or "Mritunjay Singh"
    )
    db.add(opp)
    await db.flush()

    act = Activity(
        org_id="org-thefullcircle",
        entity_type="deal",
        entity_id=opp.id,
        entity_name=opp.company_name,
        type="stage_change",
        title=f"Deal Created: {opp.title}",
        description=f"Initial stage '{opp.stage}' with valuation ₹{opp.value:,.0f}.",
        author_id=current_user.id,
        author_name=current_user.full_name or "User"
    )
    db.add(act)
    await db.commit()
    await db.refresh(opp)
    return opp

@router.patch("/{id}/stage")
async def update_opportunity_stage(
    id: str,
    payload: StageMoveSchema,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("opportunities.stage_move"))
):
    """Kanban drag-and-drop backend mutation with activity and probability update."""
    stmt = select(Opportunity).where(Opportunity.id == id)
    res = await db.execute(stmt)
    opp = res.scalars().first()
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    old_stage = opp.stage
    opp.stage = payload.new_stage

    # Automatically set typical stage probability if not supplied
    default_probs = {"discovery": 25, "proposal": 50, "negotiation": 75, "won": 100, "lost": 0}
    opp.probability = payload.probability if payload.probability is not None else default_probs.get(payload.new_stage, opp.probability)
    opp.updated_at = datetime.now(timezone.utc)

    # Activity record
    act = Activity(
        org_id=opp.org_id,
        entity_type="deal",
        entity_id=opp.id,
        entity_name=opp.company_name,
        type="stage_change",
        title=f"Opportunity moved to '{opp.stage.capitalize()}'",
        description=f"Stage shifted from '{old_stage}' to '{opp.stage}'. Probability updated to {opp.probability}%.",
        author_id=current_user.id,
        author_name=current_user.full_name or "User"
    )
    db.add(act)
    await db.commit()
    await db.refresh(opp)
    return opp

@router.patch("/{id}")
async def update_opportunity(
    id: str,
    payload: OpportunityUpdateSchema,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("opportunities.edit"))
):
    stmt = select(Opportunity).where(Opportunity.id == id)
    res = await db.execute(stmt)
    opp = res.scalars().first()
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    update_dict = payload.model_dump(exclude_unset=True)
    for k, v in update_dict.items():
        setattr(opp, k, v)
    opp.updated_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(opp)
    return opp
