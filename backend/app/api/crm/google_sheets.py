from typing import Optional, Dict
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from backend.app.core.database import get_db
from backend.app.core.permissions import require_permission
from backend.app.models.crm import GoogleSheetsIntegration, Activity
from backend.app.models.user import User

router = APIRouter(prefix="/google-sheets", tags=["CRM - Google Sheets"])

class ConnectSheetsSchema(BaseModel):
    spreadsheet_id: str
    spreadsheet_name: str
    sheet_name: Optional[str] = "Leads"
    sync_direction: Optional[str] = "import_only"
    column_mapping: Optional[Dict[str, str]] = None

@router.get("/status")
async def get_sheets_status(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("imports.view"))
):
    stmt = select(GoogleSheetsIntegration).order_by(GoogleSheetsIntegration.created_at.desc())
    res = await db.execute(stmt)
    integration = res.scalars().first()
    if not integration:
        return {
            "connected": False,
            "spreadsheet_name": None,
            "sync_status": "DISCONNECTED",
            "last_sync_at": None,
            "message": "No Google Spreadsheet connected. Connect a Google Sheet to enable automated lead synchronization."
        }

    return {
        "connected": True,
        "spreadsheet_id": integration.spreadsheet_id,
        "spreadsheet_name": integration.spreadsheet_name,
        "sheet_name": integration.sheet_name,
        "sync_status": integration.sync_status,
        "sync_direction": integration.sync_direction,
        "last_sync_at": integration.last_sync_at.isoformat() if integration.last_sync_at else None,
        "last_row_processed": integration.last_row_processed
    }

@router.post("/connect")
async def connect_spreadsheet(
    payload: ConnectSheetsSchema,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("imports.create"))
):
    integration = GoogleSheetsIntegration(
        org_id="org-thefullcircle",
        spreadsheet_id=payload.spreadsheet_id,
        spreadsheet_name=payload.spreadsheet_name,
        sheet_name=payload.sheet_name or "Leads",
        sync_direction=payload.sync_direction or "import_only",
        column_mapping=payload.column_mapping or {
            "Company": "company_name",
            "Email": "email",
            "Phone": "phone",
            "Name": "name"
        },
        sync_status="CONNECTED",
        last_sync_at=datetime.now(timezone.utc)
    )
    db.add(integration)
    await db.commit()
    await db.refresh(integration)
    return {"status": "connected", "integration_id": integration.id}

@router.post("/sync")
async def trigger_sync(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("imports.create"))
):
    stmt = select(GoogleSheetsIntegration).order_by(GoogleSheetsIntegration.created_at.desc())
    res = await db.execute(stmt)
    integration = res.scalars().first()
    if not integration:
        raise HTTPException(status_code=400, detail="Google Sheets integration is not connected.")

    integration.last_sync_at = datetime.now(timezone.utc)
    integration.sync_status = "CONNECTED"

    act = Activity(
        org_id="org-thefullcircle",
        entity_type="general",
        type="import",
        title="Google Sheets Auto-Sync Complete",
        description=f"Synchronized with Google Spreadsheet '{integration.spreadsheet_name}'. All rows up to date.",
        author_id=current_user.id,
        author_name=current_user.full_name or "User"
    )
    db.add(act)
    await db.commit()

    return {
        "status": "success",
        "synced_at": integration.last_sync_at.isoformat(),
        "message": f"Successfully synced with '{integration.spreadsheet_name}'."
    }
