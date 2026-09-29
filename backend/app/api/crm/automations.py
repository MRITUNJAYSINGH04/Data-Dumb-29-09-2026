from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from backend.app.core.database import get_db
from backend.app.core.permissions import require_permission
from backend.app.models.crm import AutomationWorkflow, AutomationRun
from backend.app.models.user import User

router = APIRouter(prefix="/automations", tags=["CRM - Automations"])

class AutomationToggleSchema(BaseModel):
    is_active: bool

@router.get("")
async def list_automations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("automations.view"))
):
    stmt = select(AutomationWorkflow)
    res = await db.execute(stmt)
    workflows = res.scalars().all()
    if not workflows:
        # Provide default initial workflows if none created yet
        wf1 = AutomationWorkflow(
            id="auto-1",
            org_id="org-thefullcircle",
            name="Auto-Route Healthcare & Hospital Leads",
            description="When industry is Healthcare or Hospital, assign to Clinical & POSH Advisory team.",
            trigger_type="LEAD_CREATED",
            conditions=[{"field": "industry", "operator": "contains", "value": "Healthcare"}],
            actions=[{"action": "assign_team", "target": "team-clinical"}],
            is_active=True,
            execution_count=34
        )
        wf2 = AutomationWorkflow(
            id="auto-2",
            org_id="org-thefullcircle",
            name="High Score Priority Task Trigger",
            description="When AI Lead Score > 85, immediately create High Priority follow-up task.",
            trigger_type="SCORE_THRESHOLD",
            conditions=[{"field": "lead_score", "operator": "gte", "value": 85}],
            actions=[{"action": "create_task", "priority": "High", "due_hours": 24}],
            is_active=True,
            execution_count=128
        )
        wf3 = AutomationWorkflow(
            id="auto-3",
            org_id="org-thefullcircle",
            name="Notify Manager on Stale Interested Leads",
            description="Trigger alert to Supriya Nair if lead remains in 'Interested' disposition > 7 days.",
            trigger_type="STATUS_CHANGED",
            conditions=[{"field": "calling_disposition", "operator": "equals", "value": "Interested"}],
            actions=[{"action": "send_notification", "target": "usr-supriya"}],
            is_active=True,
            execution_count=19
        )
        db.add_all([wf1, wf2, wf3])
        await db.commit()
        workflows = [wf1, wf2, wf3]

    return workflows

@router.patch("/{id}/toggle")
async def toggle_automation(
    id: str,
    payload: AutomationToggleSchema,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("automations.edit"))
):
    stmt = select(AutomationWorkflow).where(AutomationWorkflow.id == id)
    res = await db.execute(stmt)
    wf = res.scalars().first()
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")
    wf.is_active = payload.is_active
    await db.commit()
    return {"status": "success", "id": wf.id, "is_active": wf.is_active}

@router.get("/runs")
async def list_automation_runs(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("automations.view"))
):
    stmt = select(AutomationRun).order_by(AutomationRun.executed_at.desc()).limit(30)
    res = await db.execute(stmt)
    return res.scalars().all()
