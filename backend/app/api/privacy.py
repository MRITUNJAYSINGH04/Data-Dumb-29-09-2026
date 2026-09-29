from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete

from backend.app.core.database import get_db
from backend.app.core.config import settings
from backend.app.core.deps import get_current_user, record_audit_log
from backend.app.models.user import User
from backend.app.models.investigation import Investigation, EvidenceItem
from backend.app.models.audit import AuditLog

router = APIRouter(prefix="/privacy", tags=["Privacy & Data Retention"])

@router.get("/audit-logs")
async def get_audit_logs(
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit)
    res = await db.execute(stmt)
    logs = res.scalars().all()
    return [
        {
            "id": l.id,
            "action": l.action,
            "target_type": l.target_type,
            "target_id": l.target_id,
            "details": l.details,
            "timestamp": l.timestamp.isoformat()
        }
        for l in logs
    ]

@router.post("/purge")
async def purge_all_data(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Permanently deletes all investigations and evidence for current user."""
    stmt = delete(Investigation).where(Investigation.user_id == current_user.id)
    await db.execute(stmt)
    await db.commit()

    await record_audit_log(
        db,
        action="all_data_purged",
        target_type="privacy",
        user_id=current_user.id,
        details={"retention_policy": "immediate_purge"}
    )
    return {"status": "success", "message": "All user investigation records permanently purged."}

@router.post("/retention-cleanup")
async def run_retention_cleanup(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Purges records older than configured DATA_RETENTION_DAYS."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=settings.DATA_RETENTION_DAYS)
    stmt = delete(Investigation).where(Investigation.created_at < cutoff)
    result = await db.execute(stmt)
    await db.commit()

    await record_audit_log(
        db,
        action="retention_cleanup_executed",
        target_type="privacy",
        user_id=current_user.id,
        details={"cutoff": cutoff.isoformat()}
    )
    return {"status": "success", "message": f"Retention cleanup executed for records older than {settings.DATA_RETENTION_DAYS} days."}
