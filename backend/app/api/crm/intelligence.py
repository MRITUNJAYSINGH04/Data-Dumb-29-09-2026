from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.database import get_db
from backend.app.core.permissions import require_permission
from backend.app.models.crm import WebsiteScan
from backend.app.models.user import User
from backend.app.services.website_intel_service import analyze_website

router = APIRouter(prefix="/intelligence", tags=["CRM - Website Intelligence"])

class ScanRequestSchema(BaseModel):
    url: str

@router.post("/scan-website")
async def scan_website(
    payload: ScanRequestSchema,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("leads.view"))
):
    if not payload.url.strip():
        raise HTTPException(status_code=400, detail="Website URL is required")

    result = await analyze_website(payload.url.strip())

    # Save to website_scans table
    scan = WebsiteScan(
        url=result["url"],
        domain=result["domain"],
        title=result["title"],
        meta_description=result["meta_description"],
        business_type=result["business_type"],
        industry=result["industry"],
        services=result["services"],
        technologies=result["technologies"],
        contact_info=result["contact_info"],
        target_match_pct=result["target_match_pct"],
        confidence_score=result["confidence_score"],
        priority=result["priority"],
        extracted_text_snippet=result["extracted_text_snippet"]
    )
    db.add(scan)
    await db.commit()

    return result
