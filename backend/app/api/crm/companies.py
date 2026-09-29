from typing import Optional, List
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, or_
from sqlalchemy.orm import selectinload

from backend.app.core.database import get_db
from backend.app.core.permissions import require_permission
from backend.app.models.crm import Company, Contact, Opportunity, Activity
from backend.app.models.user import User

router = APIRouter(prefix="/companies", tags=["CRM - Companies"])

class CompanyCreateSchema(BaseModel):
    name: str
    website: Optional[str] = None
    domain: Optional[str] = None
    industry: Optional[str] = "General Enterprise"
    description: Optional[str] = ""
    hq_location: Optional[str] = ""
    city: Optional[str] = ""
    state: Optional[str] = ""
    country: Optional[str] = "India"
    employee_count: Optional[int] = 50
    revenue_range: Optional[str] = ""
    company_type: Optional[str] = "B2B"
    status: Optional[str] = "Prospect"

class CompanyUpdateSchema(BaseModel):
    name: Optional[str] = None
    website: Optional[str] = None
    domain: Optional[str] = None
    industry: Optional[str] = None
    description: Optional[str] = None
    city: Optional[str] = None
    employee_count: Optional[int] = None
    revenue_range: Optional[str] = None
    status: Optional[str] = None
    classification: Optional[str] = None
    company_score: Optional[int] = None

@router.get("")
async def list_companies(
    search: Optional[str] = None,
    industry: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("companies.view"))
):
    stmt = select(Company)
    if search:
        search_term = f"%{search}%"
        stmt = stmt.where(
            or_(
                Company.name.ilike(search_term),
                Company.domain.ilike(search_term),
                Company.city.ilike(search_term),
                Company.industry.ilike(search_term)
            )
        )
    if industry and industry != "all":
        stmt = stmt.where(Company.industry == industry)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_res = await db.execute(count_stmt)
    total = total_res.scalar() or 0

    stmt = stmt.order_by(Company.name.asc()).offset((page - 1) * page_size).limit(page_size)
    res = await db.execute(stmt)
    companies = res.scalars().all()

    return {
        "items": companies,
        "total": total,
        "page": page,
        "page_size": page_size
    }

@router.get("/{id}")
async def get_company_360(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("companies.view"))
):
    """Company 360 overview: returns full company profile with associated contacts and deals."""
    stmt = select(Company).where(Company.id == id)
    res = await db.execute(stmt)
    company = res.scalars().first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    # Fetch contacts
    contacts_stmt = select(Contact).where(Contact.company_id == id)
    contacts_res = await db.execute(contacts_stmt)
    contacts = contacts_res.scalars().all()

    # Fetch opportunities
    deals_stmt = select(Opportunity).where(Opportunity.company_id == id)
    deals_res = await db.execute(deals_stmt)
    deals = deals_res.scalars().all()

    # Fetch activities
    act_stmt = select(Activity).where(Activity.entity_id == id).order_by(Activity.timestamp.desc()).limit(20)
    act_res = await db.execute(act_stmt)
    activities = act_res.scalars().all()

    return {
        "company": company,
        "contacts": contacts,
        "deals": deals,
        "activities": activities
    }

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_company(
    payload: CompanyCreateSchema,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("companies.create"))
):
    domain = payload.domain
    if not domain and payload.website:
        domain = payload.website.replace("https://", "").replace("http://", "").replace("www.", "").split("/")[0]

    company = Company(
        org_id="org-thefullcircle",
        name=payload.name,
        website=payload.website,
        domain=domain,
        industry=payload.industry,
        description=payload.description,
        hq_location=payload.hq_location,
        city=payload.city,
        state=payload.state,
        country=payload.country,
        employee_count=payload.employee_count,
        revenue_range=payload.revenue_range,
        company_type=payload.company_type,
        status=payload.status
    )
    db.add(company)
    await db.commit()
    await db.refresh(company)
    return company

@router.patch("/{id}")
async def update_company(
    id: str,
    payload: CompanyUpdateSchema,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("companies.edit"))
):
    stmt = select(Company).where(Company.id == id)
    res = await db.execute(stmt)
    company = res.scalars().first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    update_dict = payload.model_dump(exclude_unset=True)
    for k, v in update_dict.items():
        setattr(company, k, v)
    company.updated_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(company)
    return company
