from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from backend.app.core.database import get_db
from backend.app.core.permissions import require_permission
from backend.app.models.crm import CRMAuditLog
from backend.app.models.user import User

router = APIRouter(prefix="/audit", tags=["CRM - Audit Logs"])

@router.get("")
async def list_audit_logs(
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("reports.view"))
):
    stmt = select(CRMAuditLog).order_by(CRMAuditLog.created_at.desc()).limit(limit)
    res = await db.execute(stmt)
    return res.scalars().all()
