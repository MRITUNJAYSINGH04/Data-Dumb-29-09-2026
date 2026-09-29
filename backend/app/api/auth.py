from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime, timezone

from backend.app.core.database import get_db
from backend.app.core.security import verify_password, get_password_hash, create_access_token, generate_api_key
from backend.app.core.deps import get_current_user, record_audit_log
from backend.app.models.user import User, APIKey
from backend.app.schemas.auth import UserCreate, UserLogin, Token, UserResponse, APIKeyCreate, APIKeyResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserResponse)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    stmt = select(User).where((User.username == user_in.username) | (User.email == user_in.email))
    res = await db.execute(stmt)
    existing = res.scalars().first()
    if existing:
        raise HTTPException(status_code=400, detail="Username or email already registered")

    user = User(
        username=user_in.username,
        email=user_in.email,
        full_name=user_in.full_name,
        hashed_password=get_password_hash(user_in.password),
        role=user_in.role.value
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    await record_audit_log(db, action="user_registered", target_type="user", target_id=user.id, user_id=user.id)
    return user

@router.post("/login", response_model=Token)
async def login(login_in: UserLogin, db: AsyncSession = Depends(get_db)):
    stmt = select(User).where(User.username == login_in.username)
    res = await db.execute(stmt)
    user = res.scalars().first()
    if not user or not verify_password(login_in.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    access_token = create_access_token(subject=user.id, role=user.role)
    await record_audit_log(db, action="user_login", target_type="user", target_id=user.id, user_id=user.id)
    return Token(access_token=access_token, user=UserResponse.model_validate(user))

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.post("/api-keys", response_model=APIKeyResponse)
async def create_api_key(
    key_in: APIKeyCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    raw_key, masked_key, key_hash = generate_api_key()
    api_key_obj = APIKey(
        user_id=current_user.id,
        name=key_in.name,
        masked_key=masked_key,
        key_hash=key_hash
    )
    db.add(api_key_obj)
    await db.commit()
    await db.refresh(api_key_obj)

    await record_audit_log(db, action="api_key_created", target_type="api_key", target_id=api_key_obj.id, user_id=current_user.id)
    return APIKeyResponse(
        id=api_key_obj.id,
        name=api_key_obj.name,
        masked_key=api_key_obj.masked_key,
        raw_key=raw_key,
        created_at=api_key_obj.created_at,
        last_used_at=api_key_obj.last_used_at,
        is_active=api_key_obj.is_active
    )

@router.get("/api-keys", response_model=list[APIKeyResponse])
async def list_api_keys(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(APIKey).where(APIKey.user_id == current_user.id)
    res = await db.execute(stmt)
    keys = res.scalars().all()
    return [
        APIKeyResponse(
            id=k.id,
            name=k.name,
            masked_key=k.masked_key,
            created_at=k.created_at,
            last_used_at=k.last_used_at,
            is_active=k.is_active
        )
        for k in keys
    ]
