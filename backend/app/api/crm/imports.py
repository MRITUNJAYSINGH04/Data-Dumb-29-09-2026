import os
import shutil
import uuid
from typing import Optional, Dict
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.app.core.database import get_db
from backend.app.core.permissions import require_permission
from backend.app.models.crm import ImportJob
from backend.app.models.user import User
from backend.app.services.import_service import (
    STORAGE_DIR, read_file_preview, auto_detect_columns, process_import_batch_job
)

router = APIRouter(prefix="/imports", tags=["CRM - Imports"])

class ExecuteImportSchema(BaseModel):
    column_mapping: Dict[str, str]
    deduplication_rule: Optional[str] = "email_or_phone" # skip, upsert, merge

@router.post("/upload")
async def upload_import_file(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("imports.create"))
):
    """Accepts CSV, XLSX, TSV files, creates an import job, auto-detects columns, and returns a preview."""
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".csv", ".tsv", ".xlsx", ".xls", ".txt"]:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format '{ext}'. Please upload .csv, .xlsx, or .tsv."
        )

    job_id = "imp-" + str(uuid.uuid4())[:8]
    save_filename = f"{job_id}_{file.filename}"
    save_path = os.path.join(STORAGE_DIR, save_filename)

    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    file_size = os.path.getsize(save_path)

    # Read preview and auto detect columns
    headers, preview_rows, total_rows = read_file_preview(save_path, max_rows=50)
    suggested_mapping = auto_detect_columns(headers)

    job = ImportJob(
        id=job_id,
        org_id="org-thefullcircle",
        user_id=current_user.id,
        user_name=current_user.full_name or "Mritunjay Singh",
        filename=file.filename,
        file_path=save_path,
        file_size_bytes=file_size,
        total_rows=total_rows,
        status="QUEUED",
        column_mapping=suggested_mapping,
        sample_preview=preview_rows[:10]
    )
    db.add(job)
    await db.commit()

    return {
        "import_id": job.id,
        "filename": job.filename,
        "total_rows": total_rows,
        "detected_headers": headers,
        "suggested_mapping": suggested_mapping,
        "preview": preview_rows
    }

@router.post("/{id}/execute")
async def execute_import(
    id: str,
    payload: ExecuteImportSchema,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("imports.create"))
):
    stmt = select(ImportJob).where(ImportJob.id == id)
    res = await db.execute(stmt)
    job = res.scalars().first()
    if not job:
        raise HTTPException(status_code=404, detail="Import job not found")

    job.column_mapping = payload.column_mapping
    job.deduplication_rule = payload.deduplication_rule or "email_or_phone"
    job.status = "RUNNING"
    await db.commit()

    # Launch streaming chunk background worker
    background_tasks.add_task(process_import_batch_job, job.id)

    return {
        "status": "started",
        "import_id": job.id,
        "message": f"Processing import '{job.filename}' in background chunks."
    }

@router.get("/{id}/progress")
async def get_import_progress(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("imports.view"))
):
    stmt = select(ImportJob).where(ImportJob.id == id)
    res = await db.execute(stmt)
    job = res.scalars().first()
    if not job:
        raise HTTPException(status_code=404, detail="Import job not found")

    progress_pct = 0.0
    if job.total_rows > 0:
        progress_pct = round((job.processed_rows / job.total_rows) * 100, 1)

    return {
        "import_id": job.id,
        "filename": job.filename,
        "status": job.status,
        "total_rows": job.total_rows,
        "processed_rows": job.processed_rows,
        "created_rows": job.created_rows,
        "updated_rows": job.updated_rows,
        "duplicate_rows": job.duplicate_rows,
        "invalid_rows": job.invalid_rows,
        "progress_percent": progress_pct,
        "error_message": job.error_message
    }

@router.get("/history")
async def list_import_history(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("imports.view"))
):
    stmt = select(ImportJob).order_by(ImportJob.created_at.desc()).limit(20)
    res = await db.execute(stmt)
    return res.scalars().all()
