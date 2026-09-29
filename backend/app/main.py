from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.future import select

from backend.app.core.config import settings
from backend.app.core.database import engine, Base, AsyncSessionLocal
from backend.app.core.security import get_password_hash
from backend.app.models.user import User
from backend.app.adapters import tool_registry  # Loads all OSINT adapter registrations

# Import API routers
from backend.app.api.auth import router as auth_router
from backend.app.api.investigations import router as investigations_router
from backend.app.api.search import router as search_router
from backend.app.api.leads import router as leads_router
from backend.app.api.tools import router as tools_router
from backend.app.api.export import router as export_router
from backend.app.api.settings import router as settings_router
from backend.app.api.privacy import router as privacy_router
from backend.app.api.directory import router as directory_router
from backend.app.api.crm.router import crm_router
from backend.app.core.crm_seed import seed_crm_database

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables on startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        try:
            from sqlalchemy import text
            await conn.execute(text("ALTER TABLE investigations ADD COLUMN workspace_dir VARCHAR"))
        except Exception:
            pass

    # Seed default administrator account if none exists
    async with AsyncSessionLocal() as db:
        stmt = select(User).where(User.username == "admin")
        res = await db.execute(stmt)
        admin = res.scalars().first()
        if not admin:
            default_admin = User(
                username="admin",
                email="admin@universal-intel.local",
                full_name="Chief Intelligence Officer",
                hashed_password=get_password_hash("admin123456"),
                role="admin"
            )
            db.add(default_admin)
            await db.commit()

    # Seed The Full Circle CRM database
    await seed_crm_database()

    yield
    await engine.dispose()

app = FastAPI(
    title="The Full Circle — Enterprise Sales & Intelligence CRM",
    version=settings.VERSION,
    description="Production-grade CRM & Lead Intelligence Engine for The Full Circle",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(crm_router, prefix=settings.API_V1_STR)
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(investigations_router, prefix=settings.API_V1_STR)
app.include_router(search_router, prefix=settings.API_V1_STR)
app.include_router(leads_router, prefix=settings.API_V1_STR)
app.include_router(tools_router, prefix=settings.API_V1_STR)
app.include_router(export_router, prefix=settings.API_V1_STR)
app.include_router(settings_router, prefix=settings.API_V1_STR)
app.include_router(privacy_router, prefix=settings.API_V1_STR)
app.include_router(directory_router, prefix=settings.API_V1_STR)

@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "engine": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "adapters_count": len(tool_registry.list_all())
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
