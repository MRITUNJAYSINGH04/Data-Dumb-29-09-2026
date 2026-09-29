from enum import Enum
from typing import Optional
from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime

class Role(str, Enum):
    ADMIN = "admin"
    ANALYST = "analyst"
    VIEWER = "viewer"

class UserBase(BaseModel):
    username: str
    email: EmailStr
    role: Role = Role.ANALYST
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    is_active: bool
    created_at: datetime

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class TokenPayload(BaseModel):
    sub: str
    role: str
    exp: int

class APIKeyCreate(BaseModel):
    name: str

class APIKeyResponse(BaseModel):
    id: str
    name: str
    masked_key: str
    raw_key: Optional[str] = None
    created_at: datetime
    last_used_at: Optional[datetime] = None
    is_active: bool
