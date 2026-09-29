from typing import List, Set, Optional
from fastapi import HTTPException, status, Depends
from backend.app.core.deps import get_current_user
from backend.app.models.user import User

# Role -> Permission mapping
ROLE_PERMISSIONS: dict[str, Set[str]] = {
    "SUPERADMIN": {"*"},
    "ADMIN": {"*"},
    "SALES_MANAGER": {
        "leads.view", "leads.create", "leads.edit", "leads.delete", "leads.assign", "leads.export", "leads.convert",
        "companies.view", "companies.create", "companies.edit", "companies.delete",
        "contacts.view", "contacts.create", "contacts.edit", "contacts.delete",
        "opportunities.view", "opportunities.create", "opportunities.edit", "opportunities.delete", "opportunities.stage_move",
        "tasks.view", "tasks.create", "tasks.edit", "tasks.delete",
        "activities.create", "activities.view",
        "imports.create", "imports.view",
        "reports.view", "reports.export",
        "automations.view", "automations.edit"
    },
    "SALES_EXECUTIVE": {
        "leads.view", "leads.create", "leads.edit", "leads.convert",
        "companies.view", "companies.create", "companies.edit",
        "contacts.view", "contacts.create", "contacts.edit",
        "opportunities.view", "opportunities.create", "opportunities.edit", "opportunities.stage_move",
        "tasks.view", "tasks.create", "tasks.edit",
        "activities.create", "activities.view",
        "reports.view"
    },
    "DATA_RESEARCHER": {
        "leads.view", "leads.create", "leads.edit", "leads.export",
        "companies.view", "companies.create", "companies.edit",
        "contacts.view", "contacts.create",
        "imports.create", "imports.view",
        "reports.view", "activities.create", "activities.view"
    },
    "VIEWER": {
        "leads.view", "companies.view", "contacts.view", "opportunities.view", "tasks.view", "reports.view", "activities.view"
    }
}

def has_permission(role: str, required_permission: str) -> bool:
    role_perms = ROLE_PERMISSIONS.get(role.upper(), set())
    if "*" in role_perms:
        return True
    return required_permission in role_perms

def require_permission(required_permission: str):
    """Dependency that enforces granular RBAC permissions on endpoints."""
    async def permission_checker(current_user: User = Depends(get_current_user)) -> User:
        user_role = (current_user.role or "VIEWER").upper()
        if not has_permission(user_role, required_permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: action '{required_permission}' requires higher privilege than '{current_user.role}'."
            )
        return current_user
    return permission_checker
