from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.app.core.database import get_db
from backend.app.core.permissions import require_permission
from backend.app.models.crm import CRMUser
from backend.app.models.user import User

router = APIRouter(prefix="/users", tags=["CRM - Users"])

class UserProfileUpdateSchema(BaseModel):
    firstName: Optional[str] = None
    middleName: Optional[str] = None
    lastName: Optional[str] = None
    gender: Optional[str] = None
    workEmail: Optional[str] = None
    personalEmail: Optional[str] = None
    phoneNumbers: Optional[Dict[str, str]] = None
    aboutMe: Optional[str] = None
    communicationPreferences: Optional[Dict[str, bool]] = None

class UserPreferenceUpdateSchema(BaseModel):
    menuType: Optional[str] = None
    landingPage: Optional[str] = None
    inputStyle: Optional[str] = None
    flatLayoutColor: Optional[str] = None
    specialLayoutColor: Optional[str] = None
    themeColor: Optional[str] = None

class UserInviteSchema(BaseModel):
    name: str
    email: str
    role: str # SALES_EXECUTIVE, SALES_MANAGER, ADMIN, DATA_RESEARCHER, VIEWER
    quota: Optional[float] = 800000.0

@router.get("")
async def list_crm_users(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("leads.view"))
):
    stmt = select(CRMUser).order_by(CRMUser.full_name.asc())
    res = await db.execute(stmt)
    users = res.scalars().all()
    items = []
    for u in users:
        items.append({
            "id": u.id,
            "name": u.full_name,
            "email": u.email,
            "role": u.role,
            "teamId": u.team_id or "team-enterprise",
            "teamName": "Enterprise Sales & Outreach",
            "status": u.status,
            "avatar": u.avatar,
            "phone": u.phone,
            "quota": u.quota,
            "wonRevenue": u.won_revenue,
            "activeDealsCount": u.active_deals_count,
            "profileData": u.profile_data or {},
            "preferences": u.preferences or {}
        })
    return items

@router.get("/me/profile")
async def get_my_profile(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("leads.view"))
):
    stmt = select(CRMUser).where(CRMUser.email == current_user.email)
    res = await db.execute(stmt)
    u = res.scalars().first()
    if not u:
        # Fallback to Mritunjay
        stmt_fallback = select(CRMUser).where(CRMUser.id == "usr-mritunjay")
        u = (await db.execute(stmt_fallback)).scalars().first()

    return {
        "user": {
            "id": u.id,
            "name": u.full_name,
            "email": u.email,
            "role": u.role,
            "phone": u.phone,
            "avatar": u.avatar,
            "quota": u.quota,
            "wonRevenue": u.won_revenue
        },
        "profile": u.profile_data or {},
        "preferences": u.preferences or {}
    }

@router.patch("/me/profile")
async def update_my_profile(
    payload: UserProfileUpdateSchema,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("leads.view"))
):
    stmt = select(CRMUser).where(CRMUser.email == current_user.email)
    res = await db.execute(stmt)
    u = res.scalars().first()
    if not u:
        stmt_fallback = select(CRMUser).where(CRMUser.id == "usr-mritunjay")
        u = (await db.execute(stmt_fallback)).scalars().first()

    current_profile = u.profile_data or {}
    for k, v in payload.model_dump(exclude_unset=True).items():
        current_profile[k] = v
    u.profile_data = current_profile

    if payload.firstName or payload.lastName:
        f = payload.firstName or u.first_name
        l = payload.lastName or u.last_name
        u.full_name = f"{f} {l}".strip()

    await db.commit()
    return {"status": "success", "profile": u.profile_data}

@router.patch("/me/preferences")
async def update_my_preferences(
    payload: UserPreferenceUpdateSchema,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("leads.view"))
):
    stmt = select(CRMUser).where(CRMUser.email == current_user.email)
    res = await db.execute(stmt)
    u = res.scalars().first()
    if not u:
        stmt_fallback = select(CRMUser).where(CRMUser.id == "usr-mritunjay")
        u = (await db.execute(stmt_fallback)).scalars().first()

    current_prefs = u.preferences or {}
    for k, v in payload.model_dump(exclude_unset=True).items():
        current_prefs[k] = v
    u.preferences = current_prefs

    await db.commit()
    return {"status": "success", "preferences": u.preferences}
