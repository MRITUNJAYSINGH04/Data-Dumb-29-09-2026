from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.app.core.database import get_db
from backend.app.core.deps import get_current_user, record_audit_log
from backend.app.models.user import User
from backend.app.models.investigation import Investigation, EvidenceItem
from backend.app.schemas.investigation import InvestigationResponse, InvestigationInput, NormalizedResult, VerificationStatus
from backend.app.schemas.export import ExportRequest, ExportFormat
from backend.app.exporter.exporter import exporter

router = APIRouter(prefix="/export", tags=["Export Center"])

@router.post("")
async def export_data(
    req: ExportRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Investigation).where(Investigation.id == req.investigation_id)
    res = await db.execute(stmt)
    inv = res.scalars().first()
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found")

    ev_stmt = select(EvidenceItem).where(EvidenceItem.investigation_id == req.investigation_id)
    ev_res = await db.execute(ev_stmt)
    items = ev_res.scalars().all()

    results = [
        NormalizedResult(
            source=i.source,
            source_type=i.source_type,
            query=i.query,
            entity_type=i.entity_type,
            entity=i.entity,
            attribute=i.attribute,
            value=i.value,
            url=i.url,
            timestamp=i.timestamp,
            confidence=i.confidence,
            status=VerificationStatus(i.status),
            evidence=i.evidence,
            raw_reference=i.raw_reference or ""
        )
        for i in items
    ]

    inv_resp = InvestigationResponse(
        id=inv.id,
        title=inv.title,
        mode=inv.mode,
        status=inv.status,
        progress=inv.progress,
        current_step=inv.current_step,
        created_at=inv.created_at,
        updated_at=inv.updated_at,
        input_data=InvestigationInput(**inv.input_data),
        modules_planned=inv.modules_planned,
        modules_completed=inv.modules_completed,
        results_count=len(results),
        entity_match_score=inv.entity_match_score,
        contradictions=inv.contradictions or [],
        lead_score=inv.lead_score,
        report_markdown=inv.report_markdown,
        report_json=inv.report_json
    )

    await record_audit_log(
        db,
        action="data_exported",
        target_type="export",
        target_id=inv.id,
        user_id=current_user.id,
        details={"format": req.format.value}
    )

    if req.format == ExportFormat.JSON:
        content = exporter.export_json(inv_resp, results)
        return Response(content=content, media_type="application/json", headers={"Content-Disposition": f'attachment; filename="uie_{inv.id}.json"'})
    elif req.format == ExportFormat.CSV:
        content = exporter.export_csv(results)
        return Response(content=content, media_type="text/csv", headers={"Content-Disposition": f'attachment; filename="uie_{inv.id}.csv"'})
    elif req.format == ExportFormat.MARKDOWN:
        content = exporter.export_markdown(inv_resp)
        return Response(content=content, media_type="text/markdown", headers={"Content-Disposition": f'attachment; filename="uie_{inv.id}.md"'})
    elif req.format in [ExportFormat.HTML, ExportFormat.PDF]:
        content = exporter.export_html(inv_resp, results)
        return Response(content=content, media_type="text/html", headers={"Content-Disposition": f'attachment; filename="uie_{inv.id}.html"'})

    raise HTTPException(status_code=400, detail="Unsupported format")
