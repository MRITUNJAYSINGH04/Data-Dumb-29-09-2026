from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update
from backend.app.core.database import get_db
from backend.app.core.permissions import require_permission
from backend.app.models.crm import Notification
from backend.app.models.user import User

router = APIRouter(prefix="/notifications", tags=["CRM - Notifications"])

@router.get("")
async def list_notifications(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("leads.view"))
):
    stmt = select(Notification).order_by(Notification.created_at.desc()).limit(30)
    res = await db.execute(stmt)
    notifications = res.scalars().all()
    unread_count = sum(1 for n in notifications if not n.is_read)
    return {
        "items": notifications,
        "unread_count": unread_count
    }

@router.patch("/{id}/read")
async def mark_notification_read(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("leads.view"))
):
    stmt = select(Notification).where(Notification.id == id)
    res = await db.execute(stmt)
    n = res.scalars().first()
    if n:
        n.is_read = True
        await db.commit()
    return {"status": "success"}

@router.post("/read-all")
async def mark_all_notifications_read(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("leads.view"))
):
    stmt = update(Notification).values(is_read=True)
    await db.execute(stmt)
    await db.commit()
    return {"status": "success"}
