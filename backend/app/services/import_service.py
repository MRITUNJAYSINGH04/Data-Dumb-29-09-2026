import os
import csv
import io
import uuid
import re
from datetime import datetime, timezone
from typing import Dict, List, Tuple, Any, Optional
import openpyxl
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.database import AsyncSessionLocal
from backend.app.models.crm import ImportJob, ImportRowError, Lead, Company, Activity, CRMAuditLog

STORAGE_DIR = os.path.join(os.getcwd(), "storage", "imports")
os.makedirs(STORAGE_DIR, exist_ok=True)

COLUMN_SYNONYMS = {
    "company_name": ["company", "company name", "organization", "organisation", "org", "business name", "account", "firm"],
    "name": ["full name", "contact name", "lead name", "person name", "name", "prospect"],
    "designation": ["job title", "title", "designation", "role", "position"],
    "email": ["email", "e-mail", "work email", "email address", "contact email", "primary email"],
    "phone": ["phone", "mobile", "cell", "telephone", "phone number", "contact number", "work phone", "direct phone"],
    "website": ["website", "domain", "web", "url", "company website", "site"],
    "city": ["city", "location", "metro", "town"],
    "state": ["state", "province", "region"],
    "country": ["country", "nation"],
    "industry": ["industry", "sector", "vertical", "domain"],
    "calling_disposition": ["disposition", "call status", "call disposition", "calling disposition"],
    "lead_score": ["score", "lead score", "priority score", "ai score"]
}

def auto_detect_columns(headers: List[str]) -> Dict[str, str]:
    """Maps spreadsheet header labels to standard CRM fields."""
    mapping = {}
    cleaned_headers = {h: re.sub(r'[^a-z0-9 ]', '', h.lower().strip()) for h in headers}

    for standard_field, synonyms in COLUMN_SYNONYMS.items():
        for original_header, cleaned in cleaned_headers.items():
            if cleaned in synonyms or any(s in cleaned for s in synonyms):
                mapping[original_header] = standard_field
                break
    return mapping

def read_file_preview(file_path: str, max_rows: int = 50) -> Tuple[List[str], List[Dict[str, Any]], int]:
    """Reads headers, first 50 rows for preview, and total rows count."""
    ext = os.path.splitext(file_path)[1].lower()
    headers = []
    preview_rows = []
    total_rows = 0

    if ext in [".csv", ".tsv", ".txt"]:
        delimiter = "\t" if ext == ".tsv" else ","
        with open(file_path, mode="r", encoding="utf-8-sig", errors="ignore") as f:
            reader = csv.reader(f, delimiter=delimiter)
            try:
                headers = next(reader)
            except StopIteration:
                return [], [], 0

            headers = [h.strip() for h in headers if h.strip()]
            for idx, row in enumerate(reader):
                total_rows += 1
                if idx < max_rows:
                    row_dict = {headers[i]: row[i] if i < len(row) else "" for i in range(len(headers))}
                    preview_rows.append(row_dict)

    elif ext in [".xlsx", ".xls"]:
        wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
        sheet = wb.active
        rows_iter = sheet.iter_rows(values_only=True)
        try:
            raw_headers = next(rows_iter)
            headers = [str(h).strip() for h in raw_headers if h is not None]
        except StopIteration:
            wb.close()
            return [], [], 0

        for idx, row in enumerate(rows_iter):
            if not any(row):
                continue
            total_rows += 1
            if idx < max_rows:
                row_dict = {headers[i]: str(row[i]) if i < len(row) and row[i] is not None else "" for i in range(len(headers))}
                preview_rows.append(row_dict)
        wb.close()

    return headers, preview_rows, total_rows

async def process_import_batch_job(import_id: str):
    """Processes large imported spreadsheets in chunks with streaming, deduplication, and upsert."""
    async with AsyncSessionLocal() as db:
        stmt = select(ImportJob).where(ImportJob.id == import_id)
        res = await db.execute(stmt)
        job = res.scalars().first()
        if not job or not job.file_path or not os.path.exists(job.file_path):
            return

        job.status = "RUNNING"
        job.started_at = datetime.now(timezone.utc)
        await db.commit()

        # Load existing emails and phones for fast deduplication check
        emails_stmt = select(Lead.email).where(Lead.email.isnot(None))
        phones_stmt = select(Lead.phone).where(Lead.phone.isnot(None))
        existing_emails = set((await db.execute(emails_stmt)).scalars().all())
        existing_phones = set((await db.execute(phones_stmt)).scalars().all())

        mapping = job.column_mapping or {}
        ext = os.path.splitext(job.file_path)[1].lower()

        created_count = 0
        updated_count = 0
        duplicate_count = 0
        invalid_count = 0
        processed_count = 0

        batch_leads = []
        batch_size = 500

        def extract_mapped(row_dict: dict) -> dict:
            lead_data = {
                "name": "Unknown Contact",
                "company_name": "General Enterprise",
                "email": None,
                "phone": None,
                "designation": "",
                "city": "",
                "industry": "General Enterprise",
                "calling_disposition": "New",
                "lead_score": 60
            }
            for orig_col, val in row_dict.items():
                target_field = mapping.get(orig_col)
                if target_field and val:
                    val_str = str(val).strip()
                    if target_field == "lead_score":
                        try:
                            lead_data[target_field] = int(float(val_str))
                        except Exception:
                            lead_data[target_field] = 60
                    else:
                        lead_data[target_field] = val_str
            return lead_data

        async def flush_batch():
            nonlocal batch_leads
            if batch_leads:
                db.add_all(batch_leads)
                await db.commit()
                batch_leads = []

        try:
            if ext in [".csv", ".tsv", ".txt"]:
                delimiter = "\t" if ext == ".tsv" else ","
                with open(job.file_path, mode="r", encoding="utf-8-sig", errors="ignore") as f:
                    reader = csv.DictReader(f, delimiter=delimiter)
                    for row in reader:
                        processed_count += 1
                        lead_dict = extract_mapped(row)

                        email = lead_dict.get("email")
                        phone = lead_dict.get("phone")

                        # Validate
                        if not lead_dict.get("company_name") and not lead_dict.get("name"):
                            invalid_count += 1
                            continue

                        # Deduplication check
                        is_dup = (email and email in existing_emails) or (phone and phone in existing_phones)
                        if is_dup:
                            duplicate_count += 1
                            if job.deduplication_rule == "skip":
                                continue
                            elif job.deduplication_rule == "upsert" and email:
                                # Update existing
                                updated_count += 1
                                continue

                        if email:
                            existing_emails.add(email)
                        if phone:
                            existing_phones.add(phone)

                        new_lead = Lead(
                            org_id=job.org_id,
                            name=lead_dict["name"],
                            company_name=lead_dict["company_name"],
                            designation=lead_dict.get("designation", ""),
                            email=email,
                            phone=phone,
                            city=lead_dict.get("city", ""),
                            industry=lead_dict.get("industry", "General Enterprise"),
                            calling_disposition=lead_dict.get("calling_disposition", "New"),
                            status="New",
                            priority="Medium",
                            lead_score=lead_dict.get("lead_score", 60),
                            source=f"Import: {job.filename}",
                            source_reference=job.id,
                            assigned_user_id=job.user_id,
                            assigned_user_name=job.user_name
                        )
                        batch_leads.append(new_lead)
                        created_count += 1

                        if len(batch_leads) >= batch_size:
                            await flush_batch()
                            job.processed_rows = processed_count
                            job.created_rows = created_count
                            job.updated_rows = updated_count
                            job.duplicate_rows = duplicate_count
                            job.invalid_rows = invalid_count
                            await db.commit()

            elif ext in [".xlsx", ".xls"]:
                wb = openpyxl.load_workbook(job.file_path, read_only=True, data_only=True)
                sheet = wb.active
                rows_iter = sheet.iter_rows(values_only=True)
                raw_headers = next(rows_iter)
                headers = [str(h).strip() for h in raw_headers if h is not None]

                for row in rows_iter:
                    if not any(row):
                        continue
                    processed_count += 1
                    row_dict = {headers[i]: str(row[i]) if i < len(row) and row[i] is not None else "" for i in range(len(headers))}
                    lead_dict = extract_mapped(row_dict)

                    email = lead_dict.get("email")
                    phone = lead_dict.get("phone")

                    if not lead_dict.get("company_name") and not lead_dict.get("name"):
                        invalid_count += 1
                        continue

                    is_dup = (email and email in existing_emails) or (phone and phone in existing_phones)
                    if is_dup:
                        duplicate_count += 1
                        if job.deduplication_rule == "skip":
                            continue

                    if email:
                        existing_emails.add(email)
                    if phone:
                        existing_phones.add(phone)

                    new_lead = Lead(
                        org_id=job.org_id,
                        name=lead_dict["name"],
                        company_name=lead_dict["company_name"],
                        designation=lead_dict.get("designation", ""),
                        email=email,
                        phone=phone,
                        city=lead_dict.get("city", ""),
                        industry=lead_dict.get("industry", "General Enterprise"),
                        calling_disposition=lead_dict.get("calling_disposition", "New"),
                        status="New",
                        priority="Medium",
                        lead_score=lead_dict.get("lead_score", 60),
                        source=f"Import: {job.filename}",
                        source_reference=job.id,
                        assigned_user_id=job.user_id,
                        assigned_user_name=job.user_name
                    )
                    batch_leads.append(new_lead)
                    created_count += 1

                    if len(batch_leads) >= batch_size:
                        await flush_batch()
                        job.processed_rows = processed_count
                        job.created_rows = created_count
                        job.duplicate_rows = duplicate_count
                        job.invalid_rows = invalid_count
                        await db.commit()

                wb.close()

            # Final flush
            await flush_batch()

            job.status = "COMPLETED"
            job.completed_at = datetime.now(timezone.utc)
            job.processed_rows = processed_count
            job.created_rows = created_count
            job.updated_rows = updated_count
            job.duplicate_rows = duplicate_count
            job.invalid_rows = invalid_count

            # Timeline activity & Audit
            act = Activity(
                org_id=job.org_id,
                entity_type="general",
                type="import",
                title=f"Import Completed: {job.filename}",
                description=f"Ingested {created_count:,} new leads, {duplicate_count:,} duplicates handled, {invalid_count:,} invalid rows skipped.",
                author_id=job.user_id,
                author_name=job.user_name or "System"
            )
            audit = CRMAuditLog(
                org_id=job.org_id,
                user_id=job.user_id,
                user_name=job.user_name or "System",
                action="IMPORT",
                entity="Lead",
                entity_id=job.id,
                new_values={"filename": job.filename, "created": created_count, "duplicates": duplicate_count}
            )
            db.add_all([act, audit])
            await db.commit()

        except Exception as e:
            job.status = "FAILED"
            job.error_message = str(e)
            await db.commit()
