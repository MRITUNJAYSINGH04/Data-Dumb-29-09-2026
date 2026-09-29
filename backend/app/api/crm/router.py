from fastapi import APIRouter

from backend.app.api.crm.leads import router as leads_router
from backend.app.api.crm.companies import router as companies_router
from backend.app.api.crm.contacts import router as contacts_router
from backend.app.api.crm.opportunities import router as opportunities_router
from backend.app.api.crm.tasks import router as tasks_router
from backend.app.api.crm.activities import router as activities_router
from backend.app.api.crm.imports import router as imports_router
from backend.app.api.crm.intelligence import router as intelligence_router
from backend.app.api.crm.analytics import router as analytics_router
from backend.app.api.crm.users import router as users_router
from backend.app.api.crm.notifications import router as notifications_router
from backend.app.api.crm.audit import router as audit_router
from backend.app.api.crm.automations import router as automations_router
from backend.app.api.crm.google_sheets import router as google_sheets_router

crm_router = APIRouter(prefix="/crm", tags=["The Full Circle CRM"])

crm_router.include_router(leads_router)
crm_router.include_router(companies_router)
crm_router.include_router(contacts_router)
crm_router.include_router(opportunities_router)
crm_router.include_router(tasks_router)
crm_router.include_router(activities_router)
crm_router.include_router(imports_router)
crm_router.include_router(intelligence_router)
crm_router.include_router(analytics_router)
crm_router.include_router(users_router)
crm_router.include_router(notifications_router)
crm_router.include_router(audit_router)
crm_router.include_router(automations_router)
crm_router.include_router(google_sheets_router)
