from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from backend.app.schemas.tool import ToolStatus, ToolToggleRequest
from backend.app.adapters.registry import tool_registry
from backend.app.core.deps import get_current_user
from backend.app.models.user import User

router = APIRouter(prefix="/tools", tags=["Tool Manager"])

@router.get("", response_model=List[ToolStatus])
async def list_tools(current_user: User = Depends(get_current_user)):
    """Returns status, metadata, installation health, and metrics of all OSINT adapters."""
    return tool_registry.get_stats()

@router.post("/{tool_id}/toggle")
async def toggle_tool(
    tool_id: str,
    toggle: ToolToggleRequest,
    current_user: User = Depends(get_current_user)
):
    """Enables or disables an OSINT tool module."""
    success = tool_registry.toggle(tool_id, toggle.enabled)
    if not success:
        raise HTTPException(status_code=404, detail="Tool not found in registry")
    return {"id": tool_id, "enabled": toggle.enabled, "status": "updated"}
