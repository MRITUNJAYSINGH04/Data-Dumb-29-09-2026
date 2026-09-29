from typing import Optional, List
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, or_

from backend.app.core.database import get_db
from backend.app.core.permissions import require_permission
from backend.app.models.crm import Contact, Company
from backend.app.models.user import User

router = APIRouter(prefix="/contacts", tags=["CRM - Contacts"])

class ContactCreateSchema(BaseModel):
    company_id: str
    full_name: str
    first_name: Optional[str] = ""
    last_name: Optional[str] = ""
    designation: Optional[str] = ""
    department: Optional[str] = ""
    seniority: Optional[str] = "Manager"
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    location: Optional[str] = ""
    is_decision_maker: Optional[bool] = False

class ContactUpdateSchema(BaseModel):
    full_name: Optional[str] = None
    designation: Optional[str] = None
    department: Optional[str] = None
    seniority: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    is_decision_maker: Optional[bool] = None
    status: Optional[str] = None

@router.get("")
async def list_contacts(
    company_id: Optional[str] = None,
    decision_maker_only: bool = False,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("contacts.view"))
):
    stmt = select(Contact, Company.name.label("company_name")).join(Company, Contact.company_id == Company.id, isouter=True)

    if company_id:
        stmt = stmt.where(Contact.company_id == company_id)
    if decision_maker_only:
        stmt = stmt.where(Contact.is_decision_maker == True)
    if search:
        search_term = f"%{search}%"
        stmt = stmt.where(
            or_(
                Contact.full_name.ilike(search_term),
                Contact.email.ilike(search_term),
                Contact.designation.ilike(search_term),
                Company.name.ilike(search_term)
            )
        )

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_res = await db.execute(count_stmt)
    total = total_res.scalar() or 0

    stmt = stmt.order_by(Contact.full_name.asc()).offset((page - 1) * page_size).limit(page_size)
    res = await db.execute(stmt)
    rows = res.all()

    items = []
    for contact, comp_name in rows:
        c_dict = {
            "id": contact.id,
            "company_id": contact.company_id,
            "company_name": comp_name or "Independent",
            "full_name": contact.full_name,
            "first_name": contact.first_name,
            "last_name": contact.last_name,
            "designation": contact.designation,
            "department": contact.department,
            "seniority": contact.seniority,
            "email": contact.email,
            "phone": contact.phone,
            "linkedin_url": contact.linkedin_url,
            "location": contact.location,
            "is_decision_maker": contact.is_decision_maker,
            "verification_status": contact.verification_status,
            "status": contact.status,
            "created_at": contact.created_at.isoformat() if contact.created_at else None
        }
        items.append(c_dict)

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size
    }

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_contact(
    payload: ContactCreateSchema,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("contacts.create"))
):
    parts = payload.full_name.strip().split(" ", 1)
    f_name = payload.first_name or parts[0]
    l_name = payload.last_name or (parts[1] if len(parts) > 1 else "")

    contact = Contact(
        org_id="org-thefullcircle",
        company_id=payload.company_id,
        first_name=f_name,
        last_name=l_name,
        full_name=payload.full_name.strip(),
        designation=payload.designation,
        department=payload.department,
        seniority=payload.seniority,
        email=payload.email,
        phone=payload.phone,
        linkedin_url=payload.linkedin_url,
        location=payload.location,
        is_decision_maker=payload.is_decision_maker
    )
    db.add(contact)
    await db.commit()
    await db.refresh(contact)
    return contact

@router.patch("/{id}")
async def update_contact(
    id: str,
    payload: ContactUpdateSchema,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("contacts.edit"))
):
    stmt = select(Contact).where(Contact.id == id)
    res = await db.execute(stmt)
    contact = res.scalars().first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    update_dict = payload.model_dump(exclude_unset=True)
    for k, v in update_dict.items():
        setattr(contact, k, v)
    contact.updated_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(contact)
    return contact
