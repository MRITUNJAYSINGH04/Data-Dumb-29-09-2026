from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
from backend.app.core.config import settings
from backend.app.core.deps import get_current_user
from backend.app.models.user import User

router = APIRouter(prefix="/settings", tags=["Settings"])

class SettingsUpdate(BaseModel):
    searxng_url: Optional[str] = None
    ai_provider: Optional[str] = None
    openai_api_key: Optional[str] = None
    github_token: Optional[str] = None
    data_retention_days: Optional[int] = None

@router.get("")
async def get_settings(current_user: User = Depends(get_current_user)):
    return {
        "searxng_url": settings.SEARXNG_URL,
        "ai_provider": settings.AI_PROVIDER,
        "openai_api_key_configured": bool(settings.OPENAI_API_KEY),
        "github_token_configured": bool(settings.GITHUB_TOKEN),
        "data_retention_days": settings.DATA_RETENTION_DAYS,
        "version": settings.VERSION,
        "max_worker_timeout_seconds": settings.MAX_WORKER_TIMEOUT_SECONDS,
        "max_result_size": settings.MAX_RESULT_SIZE
    }

@router.post("")
async def update_settings(
    update_data: SettingsUpdate,
    current_user: User = Depends(get_current_user)
):
    if update_data.searxng_url is not None:
        settings.SEARXNG_URL = update_data.searxng_url
    if update_data.ai_provider is not None:
        settings.AI_PROVIDER = update_data.ai_provider
    if update_data.openai_api_key is not None:
        settings.OPENAI_API_KEY = update_data.openai_api_key
    if update_data.github_token is not None:
        settings.GITHUB_TOKEN = update_data.github_token
    if update_data.data_retention_days is not None:
        settings.DATA_RETENTION_DAYS = update_data.data_retention_days

    return {"status": "success", "message": "Settings updated successfully"}
