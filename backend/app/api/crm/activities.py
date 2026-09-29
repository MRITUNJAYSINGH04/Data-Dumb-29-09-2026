from typing import Optional, List
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.app.core.database import get_db
from backend.app.core.permissions import require_permission
from backend.app.models.crm import Activity
from backend.app.models.user import User

router = APIRouter(prefix="/activities", tags=["CRM - Activities"])

class ActivityCreateSchema(BaseModel):
    entity_type: str # lead, deal, contact, company, general
    entity_id: Optional[str] = None
    entity_name: Optional[str] = None
    type: str # call, email, meeting, note, stage_change, task, import, assignment
    title: str
    description: Optional[str] = ""
    status: Optional[str] = "completed"
    due_date: Optional[datetime] = None
    priority: Optional[str] = "Medium"

@router.get("")
async def list_activities(
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("activities.view"))
):
    stmt = select(Activity)
    if entity_type:
        stmt = stmt.where(Activity.entity_type == entity_type)
    if entity_id:
        stmt = stmt.where(Activity.entity_id == entity_id)

    stmt = stmt.order_by(Activity.timestamp.desc()).limit(limit)
    res = await db.execute(stmt)
    return res.scalars().all()

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_activity(
    payload: ActivityCreateSchema,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("activities.create"))
):
    act = Activity(
        org_id="org-thefullcircle",
        entity_type=payload.entity_type,
        entity_id=payload.entity_id,
        entity_name=payload.entity_name,
        type=payload.type,
        title=payload.title,
        description=payload.description or "",
        author_id=current_user.id,
        author_name=current_user.full_name or "Mritunjay Singh",
        status=payload.status,
        due_date=payload.due_date,
        priority=payload.priority,
        timestamp=datetime.now(timezone.utc)
    )
    db.add(act)
    await db.commit()
    await db.refresh(act)
    return act
