from typing import Optional, List
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.app.core.database import get_db
from backend.app.core.permissions import require_permission
from backend.app.models.crm import Task, Activity
from backend.app.models.user import User

router = APIRouter(prefix="/tasks", tags=["CRM - Tasks"])

class TaskCreateSchema(BaseModel):
    title: str
    description: Optional[str] = ""
    due_date: datetime
    priority: Optional[str] = "Medium" # High, Medium, Low
    type: Optional[str] = "follow_up" # call, email, meeting, follow_up, research, custom
    lead_id: Optional[str] = None
    lead_name: Optional[str] = None
    company_id: Optional[str] = None
    company_name: Optional[str] = None
    assigned_to_id: Optional[str] = None
    assigned_to_name: Optional[str] = None

class TaskUpdateSchema(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    priority: Optional[str] = None
    status: Optional[str] = None # pending, in_progress, completed, overdue, cancelled

@router.get("")
async def list_tasks(
    urgency: Optional[str] = None, # today, overdue, upcoming, all
    status_filter: Optional[str] = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("tasks.view"))
):
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)

    stmt = select(Task)
    if status_filter:
        stmt = stmt.where(Task.status == status_filter)

    if urgency == "today":
        stmt = stmt.where(Task.due_date >= today_start, Task.due_date < today_end, Task.status != "completed")
    elif urgency == "overdue":
        stmt = stmt.where(Task.due_date < today_start, Task.status != "completed")
    elif urgency == "upcoming":
        stmt = stmt.where(Task.due_date >= today_end, Task.status != "completed")

    stmt = stmt.order_by(Task.due_date.asc())
    res = await db.execute(stmt)
    return res.scalars().all()

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_task(
    payload: TaskCreateSchema,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("tasks.create"))
):
    task = Task(
        org_id="org-thefullcircle",
        type=payload.type or "follow_up",
        title=payload.title,
        description=payload.description or "",
        due_date=payload.due_date,
        priority=payload.priority or "Medium",
        status="pending",
        assigned_to_id=payload.assigned_to_id or current_user.id,
        assigned_to_name=payload.assigned_to_name or current_user.full_name or "Mritunjay Singh",
        lead_id=payload.lead_id,
        lead_name=payload.lead_name,
        company_id=payload.company_id,
        company_name=payload.company_name
    )
    db.add(task)
    await db.flush()

    act = Activity(
        org_id="org-thefullcircle",
        entity_type="lead" if payload.lead_id else "general",
        entity_id=payload.lead_id or payload.company_id,
        entity_name=payload.lead_name or payload.company_name,
        type="task",
        title=f"Task Scheduled: {task.title}",
        description=f"Due on {task.due_date.strftime('%d %b %Y')}. Priority: {task.priority}.",
        author_id=current_user.id,
        author_name=current_user.full_name or "User"
    )
    db.add(act)
    await db.commit()
    await db.refresh(task)
    return task

@router.patch("/{id}")
async def update_task(
    id: str,
    payload: TaskUpdateSchema,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("tasks.edit"))
):
    stmt = select(Task).where(Task.id == id)
    res = await db.execute(stmt)
    task = res.scalars().first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    update_dict = payload.model_dump(exclude_unset=True)
    for k, v in update_dict.items():
        setattr(task, k, v)

    if update_dict.get("status") == "completed" and not task.completed_at:
        task.completed_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(task)
    return task

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("tasks.delete"))
):
    stmt = select(Task).where(Task.id == id)
    res = await db.execute(stmt)
    task = res.scalars().first()
    if task:
        await db.delete(task)
        await db.commit()
    return None
