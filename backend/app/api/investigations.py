import asyncio
import os
import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status, Query
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from backend.app.core.database import get_db, AsyncSessionLocal
from backend.app.core.deps import get_current_user, record_audit_log
from backend.app.models.user import User
from backend.app.models.investigation import Investigation, EvidenceItem, GraphNode, GraphEdge
from backend.app.schemas.investigation import (
    InvestigationInput, InvestigationResponse, InvestigationSummary,
    NormalizedResult, InvestigationStatus, VerificationStatus, VectorExecutionStatus,
    QualifiedLeadItem, ExecutionLogEntry
)
from backend.app.services.investigation_service import investigation_service
from backend.app.graph.builder import graph_builder
from backend.app.adapters.registry import tool_registry

router = APIRouter(prefix="/investigations", tags=["Investigations"])

@router.post("", response_model=InvestigationResponse, status_code=status.HTTP_201_CREATED)
async def create_investigation(
    input_data: InvestigationInput,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    inv = await investigation_service.create_investigation(db, input_data, user_id=current_user.id)
    
    # Launch background investigation job
    background_tasks.add_task(investigation_service.run_investigation_job, AsyncSessionLocal, inv.id)

    await record_audit_log(
        db,
        action="investigation_created",
        target_type="investigation",
        target_id=inv.id,
        user_id=current_user.id,
        details={"mode": inv.mode, "target": inv.title}
    )

    return InvestigationResponse(
        id=inv.id,
        title=inv.title,
        mode=inv.mode,
        status=inv.status,
        progress=inv.progress,
        current_step=inv.current_step,
        workspace_dir=inv.workspace_dir,
        created_at=inv.created_at,
        updated_at=inv.updated_at,
        input_data=InvestigationInput(**inv.input_data),
        modules_planned=inv.modules_planned,
        modules_completed=inv.modules_completed,
        results_count=0,
        entity_match_score=0,
        contradictions=[],
        vector_statuses=[],
        leads=[],
        logs=[]
    )

@router.get("", response_model=List[InvestigationSummary])
async def list_investigations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Investigation).order_by(Investigation.created_at.desc())
    res = await db.execute(stmt)
    invs = res.scalars().all()

    summaries = []
    for inv in invs:
        # Count results
        count_stmt = select(EvidenceItem).where(EvidenceItem.investigation_id == inv.id)
        c_res = await db.execute(count_stmt)
        count = len(c_res.scalars().all())

        summaries.append(InvestigationSummary(
            id=inv.id,
            title=inv.title,
            mode=inv.mode,
            status=inv.status,
            progress=inv.progress,
            current_step=inv.current_step,
            workspace_dir=inv.workspace_dir,
            created_at=inv.created_at,
            updated_at=inv.updated_at,
            results_count=count,
            entity_match_score=inv.entity_match_score
        ))
    return summaries

@router.get("/{inv_id}", response_model=InvestigationResponse)
async def get_investigation(
    inv_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Investigation).where(Investigation.id == inv_id)
    res = await db.execute(stmt)
    inv = res.scalars().first()
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found")

    count_stmt = select(EvidenceItem).where(EvidenceItem.investigation_id == inv.id)
    c_res = await db.execute(count_stmt)
    count = len(c_res.scalars().all())

    vector_statuses: List[VectorExecutionStatus] = []
    if inv.workspace_dir and os.path.exists(inv.workspace_dir):
        brief_path = os.path.join(inv.workspace_dir, "gods_eye_master_brief.json")
        if os.path.exists(brief_path):
            try:
                with open(brief_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for item in data.get("vector_execution_summary", []):
                        vector_statuses.append(VectorExecutionStatus(
                            tool=item.get("tool", ""),
                            layer=item.get("layer", ""),
                            layer_display=item.get("layer_display", ""),
                            status=item.get("status", "success"),
                            execution_time_seconds=item.get("execution_time_seconds", 0.0),
                            findings_count=item.get("findings_count", 0)
                        ))
            except Exception:
                pass

    logs = investigation_service.get_logs(inv.id, inv.workspace_dir)
    leads: List[QualifiedLeadItem] = []
    if inv.report_json and isinstance(inv.report_json, dict) and "leads" in inv.report_json:
        try:
            leads = [QualifiedLeadItem(**l) for l in inv.report_json["leads"]]
        except Exception:
            pass
    elif inv.workspace_dir and os.path.exists(inv.workspace_dir):
        omni_json_path = os.path.join(inv.workspace_dir, "omni_leads_master_export.json")
        if os.path.exists(omni_json_path):
            try:
                with open(omni_json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    leads = [QualifiedLeadItem(**l) for l in data.get("qualified_leads", [])]
            except Exception:
                pass

    return InvestigationResponse(
        id=inv.id,
        title=inv.title,
        mode=inv.mode,
        status=inv.status,
        progress=inv.progress,
        current_step=inv.current_step,
        workspace_dir=inv.workspace_dir,
        created_at=inv.created_at,
        updated_at=inv.updated_at,
        input_data=InvestigationInput(**inv.input_data),
        modules_planned=inv.modules_planned,
        modules_completed=inv.modules_completed,
        results_count=count,
        entity_match_score=inv.entity_match_score,
        contradictions=inv.contradictions or [],
        lead_score=inv.lead_score,
        report_markdown=inv.report_markdown,
        report_json=inv.report_json,
        vector_statuses=vector_statuses,
        leads=leads,
        logs=logs
    )

@router.get("/{inv_id}/results", response_model=List[NormalizedResult])
async def get_investigation_results(
    inv_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(EvidenceItem).where(EvidenceItem.investigation_id == inv_id).order_by(EvidenceItem.created_at.asc())
    res = await db.execute(stmt)
    items = res.scalars().all()

    return [
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

@router.get("/{inv_id}/graph")
async def get_investigation_graph(
    inv_id: str,
    format: Optional[str] = "json",
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    nodes_stmt = select(GraphNode).where(GraphNode.investigation_id == inv_id)
    n_res = await db.execute(nodes_stmt)
    nodes = n_res.scalars().all()

    edges_stmt = select(GraphEdge).where(GraphEdge.investigation_id == inv_id)
    e_res = await db.execute(edges_stmt)
    edges = e_res.scalars().all()

    graph_payload = {
        "investigation_id": inv_id,
        "nodes": [
            {"id": n.node_id, "label": n.label, "type": n.node_type, "properties": n.properties}
            for n in nodes
        ],
        "edges": [
            {
                "source": e.source_node_id,
                "target": e.target_node_id,
                "type": e.relationship_type,
                "confidence": e.confidence,
                "evidence": e.evidence
            }
            for e in edges
        ]
    }

    if format == "cypher":
        cypher_text = graph_builder.to_cypher(graph_payload)
        return {"format": "cypher", "cypher": cypher_text}

    return graph_payload

@router.get("/{inv_id}/report")
async def get_investigation_report(
    inv_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Investigation).where(Investigation.id == inv_id)
    res = await db.execute(stmt)
    inv = res.scalars().first()
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found")

    return {
        "id": inv.id,
        "title": inv.title,
        "report_markdown": inv.report_markdown,
        "report_json": inv.report_json
    }

@router.get("/{inv_id}/master-brief")
async def get_master_brief(
    inv_id: str,
    download: bool = Query(default=False),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Investigation).where(Investigation.id == inv_id)
    res = await db.execute(stmt)
    inv = res.scalars().first()
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found")

    if not inv.workspace_dir or not os.path.exists(inv.workspace_dir):
        raise HTTPException(status_code=404, detail="Investigation workspace directory not found")

    brief_path = os.path.join(inv.workspace_dir, "gods_eye_master_brief.json")
    if not os.path.exists(brief_path):
        raise HTTPException(status_code=404, detail="God's Eye Master Brief has not yet been compiled")

    if download:
        return FileResponse(
            path=brief_path,
            filename=f"gods_eye_master_brief_{inv.id[:8]}.json",
            media_type="application/json"
        )

    with open(brief_path, "r", encoding="utf-8") as f:
        return json.load(f)

@router.get("/{inv_id}/leads-csv")
async def get_leads_csv(
    inv_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Investigation).where(Investigation.id == inv_id)
    res = await db.execute(stmt)
    inv = res.scalars().first()
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found")

    if not inv.workspace_dir or not os.path.exists(inv.workspace_dir):
        raise HTTPException(status_code=404, detail="Investigation workspace directory not found")

    csv_path = os.path.join(inv.workspace_dir, "gods_eye_qualified_leads.csv")
    if not os.path.exists(csv_path):
        raise HTTPException(status_code=404, detail="Qualified leads CSV ledger has not yet been generated")

    return FileResponse(
        path=csv_path,
        filename=f"gods_eye_qualified_leads_{inv.id[:8]}.csv",
        media_type="text/csv"
    )

@router.get("/{inv_id}/vectors", response_model=List[VectorExecutionStatus])
async def get_investigation_vectors(
    inv_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Investigation).where(Investigation.id == inv_id)
    res = await db.execute(stmt)
    inv = res.scalars().first()
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found")

    # 1. Check if master brief exists
    if inv.workspace_dir and os.path.exists(inv.workspace_dir):
        brief_path = os.path.join(inv.workspace_dir, "gods_eye_master_brief.json")
        if os.path.exists(brief_path):
            try:
                with open(brief_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    summary = data.get("vector_execution_summary", [])
                    if summary:
                        return [VectorExecutionStatus(**v) for v in summary]
            except Exception:
                pass

    # 2. Otherwise dynamically inspect workspace_dir layer folders and result.json files
    all_adapters = tool_registry.list_all()
    statuses: List[VectorExecutionStatus] = []

    for adapter in all_adapters:
        tool_slug = adapter.name.lower().replace(" ", "_").replace(".", "_").replace("/", "_")
        vector_res_file = None
        if inv.workspace_dir:
            vector_res_file = os.path.join(inv.workspace_dir, adapter.layer, tool_slug, "result.json")

        if vector_res_file and os.path.exists(vector_res_file):
            try:
                with open(vector_res_file, "r", encoding="utf-8") as f:
                    v_data = json.load(f)
                    statuses.append(VectorExecutionStatus(
                        tool=v_data.get("tool", adapter.name),
                        layer=v_data.get("layer", adapter.layer),
                        layer_display=v_data.get("layer_display", adapter.layer_display),
                        status=v_data.get("status", "completed"),
                        execution_time_seconds=v_data.get("execution_time_seconds", 0.0),
                        findings_count=v_data.get("findings_count", 0)
                    ))
                    continue
            except Exception:
                pass

        # If not completed yet, check if it's currently running or queued
        is_completed = tool_slug in (inv.modules_completed or [])
        is_planned = tool_slug in (inv.modules_planned or [])
        stat = "completed" if is_completed else ("in_progress" if is_planned and inv.status == "SEARCHING" else "pending")
        statuses.append(VectorExecutionStatus(
            tool=adapter.name,
            layer=adapter.layer,
            layer_display=adapter.layer_display,
            status=stat,
            execution_time_seconds=0.0,
            findings_count=0
        ))

    return statuses

@router.get("/{inv_id}/leads", response_model=List[QualifiedLeadItem])
async def get_investigation_leads(
    inv_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Investigation).where(Investigation.id == inv_id)
    res = await db.execute(stmt)
    inv = res.scalars().first()
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found")

    if inv.report_json and isinstance(inv.report_json, dict) and "leads" in inv.report_json:
        try:
            return [QualifiedLeadItem(**l) for l in inv.report_json["leads"]]
        except Exception:
            pass

    if inv.workspace_dir and os.path.exists(inv.workspace_dir):
        omni_json_path = os.path.join(inv.workspace_dir, "omni_leads_master_export.json")
        if os.path.exists(omni_json_path):
            try:
                with open(omni_json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return [QualifiedLeadItem(**l) for l in data.get("qualified_leads", [])]
            except Exception:
                pass

    return []

@router.get("/{inv_id}/logs", response_model=List[ExecutionLogEntry])
async def get_investigation_logs(
    inv_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Investigation).where(Investigation.id == inv_id)
    res = await db.execute(stmt)
    inv = res.scalars().first()
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found")

    return investigation_service.get_logs(inv.id, inv.workspace_dir)

@router.get("/{inv_id}/omni-export")
async def get_omni_export(
    inv_id: str,
    format: str = Query("csv"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Investigation).where(Investigation.id == inv_id)
    res = await db.execute(stmt)
    inv = res.scalars().first()
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found")

    if not inv.workspace_dir or not os.path.exists(inv.workspace_dir):
        raise HTTPException(status_code=404, detail="Investigation workspace directory not found")

    if format == "json":
        json_path = os.path.join(inv.workspace_dir, "omni_leads_master_export.json")
        if not os.path.exists(json_path):
            json_path = os.path.join(inv.workspace_dir, "gods_eye_master_brief.json")
        if not os.path.exists(json_path):
            raise HTTPException(status_code=404, detail="Omni-Leads master JSON export not ready")
        return FileResponse(path=json_path, filename=f"omni_leads_master_{inv.id[:8]}.json", media_type="application/json")

    csv_path = os.path.join(inv.workspace_dir, "omni_leads_master_export.csv")
    if not os.path.exists(csv_path):
        csv_path = os.path.join(inv.workspace_dir, "gods_eye_qualified_leads.csv")
    if not os.path.exists(csv_path):
        raise HTTPException(status_code=404, detail="Omni-Leads master CSV export not ready")
    return FileResponse(path=csv_path, filename=f"omni_leads_master_{inv.id[:8]}.csv", media_type="text/csv")

@router.delete("/{inv_id}")
async def delete_investigation(
    inv_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Investigation).where(Investigation.id == inv_id)
    res = await db.execute(stmt)
    inv = res.scalars().first()
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found")

    await db.delete(inv)
    await db.commit()
    await record_audit_log(db, action="investigation_deleted", target_type="investigation", target_id=inv_id, user_id=current_user.id)
    return {"status": "deleted", "id": inv_id}

