from typing import Optional
from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from backend.app.core.database import get_db
from backend.app.core.security import oauth2_scheme, api_key_header, decode_access_token, hash_api_key
from backend.app.models.user import User, APIKey
from backend.app.models.audit import AuditLog
from backend.app.schemas.auth import Role

async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
    token: Optional[str] = Depends(oauth2_scheme),
    api_key: Optional[str] = Depends(api_key_header)
) -> User:
    # 1. Check API Key if provided
    if api_key:
        hashed = hash_api_key(api_key)
        stmt = select(APIKey).where(APIKey.key_hash == hashed, APIKey.is_active == True)
        result = await db.execute(stmt)
        key_record = result.scalars().first()
        if key_record:
            user_stmt = select(User).where(User.id == key_record.user_id, User.is_active == True)
            user_res = await db.execute(user_stmt)
            user = user_res.scalars().first()
            if user:
                return user
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or inactive API Key",
        )

    # 2. Check Bearer Token
    if token:
        payload = decode_access_token(token)
        user_id = payload.sub
        stmt = select(User).where(User.id == user_id, User.is_active == True)
        result = await db.execute(stmt)
        user = result.scalars().first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
            )
        return user

    # 3. For local single-tenant fallback, if no token, create or return default admin
    stmt = select(User).where(User.username == "admin")
    result = await db.execute(stmt)
    admin = result.scalars().first()
    if admin:
        return admin

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated. Provide Authorization Bearer token or X-API-Key header.",
    )

def require_role(allowed_roles: list[Role]):
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in [r.value for r in allowed_roles]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation not permitted for role {current_user.role}",
            )
        return current_user
    return role_checker

async def record_audit_log(
    db: AsyncSession,
    action: str,
    target_type: str,
    target_id: Optional[str] = None,
    user_id: Optional[str] = None,
    details: Optional[dict] = None,
    ip_address: Optional[str] = None
):
    audit = AuditLog(
        user_id=user_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        details=details or {},
        ip_address=ip_address
    )
    db.add(audit)
    await db.commit()
