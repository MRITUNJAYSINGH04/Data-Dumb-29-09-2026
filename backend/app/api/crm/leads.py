from typing import Optional, List
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, update, delete, desc, or_

from backend.app.core.database import get_db
from backend.app.core.deps import get_current_user
from backend.app.core.permissions import require_permission
from backend.app.models.crm import Lead, Company, Contact, Opportunity, Activity, CRMAuditLog
from backend.app.models.user import User

router = APIRouter(prefix="/leads", tags=["CRM - Leads"])

class LeadCreateSchema(BaseModel):
    name: str
    company_name: str
    designation: Optional[str] = ""
    department: Optional[str] = ""
    email: Optional[str] = None
    phone: Optional[str] = None
    city: Optional[str] = ""
    state: Optional[str] = ""
    country: Optional[str] = "India"
    industry: Optional[str] = "General Enterprise"
    calling_disposition: Optional[str] = "Open Leads"
    status: Optional[str] = "New"
    priority: Optional[str] = "Medium"
    lead_score: Optional[int] = 65
    assigned_user_id: Optional[str] = None
    assigned_user_name: Optional[str] = None
    source: Optional[str] = "Manual Entry"

class LeadUpdateSchema(BaseModel):
    name: Optional[str] = None
    company_name: Optional[str] = None
    designation: Optional[str] = None
    department: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    city: Optional[str] = None
    industry: Optional[str] = None
    calling_disposition: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    lead_score: Optional[int] = None
    assigned_user_id: Optional[str] = None
    assigned_user_name: Optional[str] = None
    score_reason: Optional[str] = None

class ConvertLeadSchema(BaseModel):
    create_opportunity: bool = True
    deal_title: Optional[str] = None
    deal_value: Optional[float] = 1000000.0
    stage: Optional[str] = "discovery"

class BulkActionSchema(BaseModel):
    lead_ids: List[str]
    action: str # "assign", "change_status", "change_disposition", "delete"
    target_value: Optional[str] = None
    target_name: Optional[str] = None

@router.get("")
async def list_leads(
    disposition: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    sort_by: str = "created_at",
    sort_dir: str = "desc",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("leads.view"))
):
    """Retrieve leads with real server-side filtering by 17 calling dispositions and search."""
    stmt = select(Lead)

    if disposition and disposition != "all":
        stmt = stmt.where(Lead.calling_disposition == disposition)

    if status_filter and status_filter != "all":
        stmt = stmt.where(Lead.status == status_filter)

    if search:
        search_term = f"%{search}%"
        stmt = stmt.where(
            or_(
                Lead.name.ilike(search_term),
                Lead.company_name.ilike(search_term),
                Lead.email.ilike(search_term),
                Lead.phone.ilike(search_term),
                Lead.city.ilike(search_term),
                Lead.industry.ilike(search_term),
            )
        )

    # Count total
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_res = await db.execute(count_stmt)
    total = total_res.scalar() or 0

    # Sort
    sort_col = getattr(Lead, sort_by, Lead.created_at)
    if sort_dir.lower() == "asc":
        stmt = stmt.order_by(sort_col.asc())
    else:
        stmt = stmt.order_by(sort_col.desc())

    # Pagination
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    leads = result.scalars().all()

    return {
        "items": leads,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size
    }

@router.get("/stats/dispositions")
async def get_disposition_counts(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("leads.view"))
):
    """Real database counts for the 17 Calling Dispositions ribbon."""
    stmt = select(Lead.calling_disposition, func.count(Lead.id)).group_by(Lead.calling_disposition)
    res = await db.execute(stmt)
    counts = {row[0]: row[1] for row in res.all()}

    # All 17 official dispositions from LionO360
    official_dispositions = [
        "Open Leads", "New", "Early Researcher", "Interested", "Call Back", "Follow UP",
        "Not-Intrested", "Invalid Number", "Language Barrier", "No Is Out Of service",
        "Not Reachable", "Voice mail", "Call Cut", "Bad Lead",
        "Not Contactable After 6 Attempt", "DNP", "Closed"
    ]

    total_leads = sum(counts.values())
    result = {"total": total_leads, "counts": {d: counts.get(d, 0) for d in official_dispositions}}
    return result

@router.get("/{id}")
async def get_lead(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("leads.view"))
):
    stmt = select(Lead).where(Lead.id == id)
    res = await db.execute(stmt)
    lead = res.scalars().first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_lead(
    payload: LeadCreateSchema,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("leads.create"))
):
    new_lead = Lead(
        org_id="org-thefullcircle",
        name=payload.name,
        company_name=payload.company_name,
        designation=payload.designation,
        department=payload.department,
        email=payload.email,
        phone=payload.phone,
        city=payload.city,
        state=payload.state,
        country=payload.country,
        industry=payload.industry,
        calling_disposition=payload.calling_disposition,
        status=payload.status,
        priority=payload.priority,
        lead_score=payload.lead_score,
        assigned_user_id=payload.assigned_user_id or current_user.id,
        assigned_user_name=payload.assigned_user_name or current_user.full_name or "Mritunjay Singh",
        source=payload.source
    )
    db.add(new_lead)
    await db.flush()

    # Log activity & audit
    act = Activity(
        org_id="org-thefullcircle",
        entity_type="lead",
        entity_id=new_lead.id,
        entity_name=new_lead.name,
        type="note",
        title="Lead created in platform",
        description=f"Lead created with disposition '{new_lead.calling_disposition}'.",
        author_id=current_user.id,
        author_name=current_user.full_name or "User"
    )
    audit = CRMAuditLog(
        org_id="org-thefullcircle",
        user_id=current_user.id,
        user_name=current_user.full_name or "User",
        action="CREATE",
        entity="Lead",
        entity_id=new_lead.id,
        new_values={"name": new_lead.name, "company": new_lead.company_name}
    )
    db.add_all([act, audit])
    await db.commit()
    await db.refresh(new_lead)
    return new_lead

@router.patch("/{id}")
async def update_lead(
    id: str,
    payload: LeadUpdateSchema,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("leads.edit"))
):
    stmt = select(Lead).where(Lead.id == id)
    res = await db.execute(stmt)
    lead = res.scalars().first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    old_disposition = lead.calling_disposition
    old_status = lead.status

    update_dict = payload.model_dump(exclude_unset=True)
    for field, val in update_dict.items():
        setattr(lead, field, val)

    lead.updated_at = datetime.now(timezone.utc)

    # If disposition or status changed, log activity timeline
    if "calling_disposition" in update_dict and update_dict["calling_disposition"] != old_disposition:
        act = Activity(
            org_id="org-thefullcircle",
            entity_type="lead",
            entity_id=lead.id,
            entity_name=lead.name,
            type="status_change",
            title=f"Calling disposition changed to '{lead.calling_disposition}'",
            description=f"Shifted from '{old_disposition}' to '{lead.calling_disposition}'.",
            author_id=current_user.id,
            author_name=current_user.full_name or "User"
        )
        db.add(act)

    audit = CRMAuditLog(
        org_id="org-thefullcircle",
        user_id=current_user.id,
        user_name=current_user.full_name or "User",
        action="UPDATE",
        entity="Lead",
        entity_id=lead.id,
        old_values={"disposition": old_disposition, "status": old_status},
        new_values=update_dict
    )
    db.add(audit)
    await db.commit()
    await db.refresh(lead)
    return lead

@router.post("/{id}/convert")
async def convert_lead_transaction(
    id: str,
    payload: ConvertLeadSchema,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("leads.convert"))
):
    """Transactional lead conversion: creates Company + Contact + Opportunity safely."""
    stmt = select(Lead).where(Lead.id == id)
    res = await db.execute(stmt)
    lead = res.scalars().first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    # 1. Match or Create Company
    comp_stmt = select(Company).where(Company.name.ilike(lead.company_name.strip()))
    comp_res = await db.execute(comp_stmt)
    company = comp_res.scalars().first()

    if not company:
        company = Company(
            org_id=lead.org_id,
            name=lead.company_name.strip(),
            industry=lead.industry or "General Enterprise",
            city=lead.city or "",
            country=lead.country or "India",
            status="Active"
        )
        db.add(company)
        await db.flush()

    # 2. Match or Create Contact
    cont_stmt = select(Contact).where(
        or_(
            Contact.email == lead.email if lead.email else False,
            Contact.full_name.ilike(lead.name.strip())
        )
    )
    cont_res = await db.execute(cont_stmt)
    contact = cont_res.scalars().first()

    if not contact:
        contact = Contact(
            org_id=lead.org_id,
            company_id=company.id,
            full_name=lead.name.strip(),
            designation=lead.designation or "",
            email=lead.email,
            phone=lead.phone,
            is_decision_maker=True
        )
        db.add(contact)
        await db.flush()

    # 3. Create Opportunity if requested
    opportunity = None
    if payload.create_opportunity:
        deal_title = payload.deal_title or f"{company.name} Corporate Care Plan"
        opportunity = Opportunity(
            org_id=lead.org_id,
            company_id=company.id,
            contact_id=contact.id,
            associated_lead_id=lead.id,
            title=deal_title,
            company_name=company.name,
            contact_name=contact.full_name,
            contact_email=contact.email or "",
            value=payload.deal_value or 1000000.0,
            stage=payload.stage or "discovery",
            probability=30,
            owner_id=lead.assigned_user_id or current_user.id,
            owner_name=lead.assigned_user_name or current_user.full_name
        )
        db.add(opportunity)
        await db.flush()

    # Mark lead as qualified and converted
    lead.is_qualified = True
    lead.converted_at = datetime.now(timezone.utc)
    lead.status = "Opportunity"
    lead.company_id = company.id
    lead.contact_id = contact.id

    # Timeline record
    act = Activity(
        org_id=lead.org_id,
        entity_type="lead",
        entity_id=lead.id,
        entity_name=lead.name,
        type="stage_change",
        title="Lead Converted to Account & Opportunity",
        description=f"Created Account '{company.name}', Contact '{contact.full_name}'" + (f", and Deal '{opportunity.title}' (₹{opportunity.value:,.0f})." if opportunity else "."),
        author_id=current_user.id,
        author_name=current_user.full_name or "User"
    )
    db.add(act)
    await db.commit()

    return {
        "status": "success",
        "message": "Lead converted successfully",
        "company_id": company.id,
        "contact_id": contact.id,
        "opportunity_id": opportunity.id if opportunity else None
    }

@router.post("/bulk-action")
async def bulk_lead_action(
    payload: BulkActionSchema,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("leads.edit"))
):
    if not payload.lead_ids:
        return {"status": "success", "modified_count": 0}

    if payload.action == "delete":
        del_stmt = delete(Lead).where(Lead.id.in_(payload.lead_ids))
        await db.execute(del_stmt)
        await db.commit()
        return {"status": "success", "action": "delete", "modified_count": len(payload.lead_ids)}

    update_vals = {}
    if payload.action == "assign":
        update_vals["assigned_user_id"] = payload.target_value
        update_vals["assigned_user_name"] = payload.target_name or "Assigned Rep"
    elif payload.action == "change_status":
        update_vals["status"] = payload.target_value
    elif payload.action == "change_disposition":
        update_vals["calling_disposition"] = payload.target_value

    if update_vals:
        update_vals["updated_at"] = datetime.now(timezone.utc)
        stmt = update(Lead).where(Lead.id.in_(payload.lead_ids)).values(**update_vals)
        await db.execute(stmt)
        await db.commit()

    return {"status": "success", "action": payload.action, "modified_count": len(payload.lead_ids)}

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lead(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("leads.delete"))
):
    stmt = delete(Lead).where(Lead.id == id)
    res = await db.execute(stmt)
    await db.commit()
    return None
