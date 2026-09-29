from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from backend.app.schemas.investigation import DirectoryCompanyResult, DirectorySearchQuery
from backend.app.services.directory_service import directory_service
from backend.app.core.deps import get_current_user
from backend.app.models.user import User

router = APIRouter(prefix="/directory", tags=["Startup & Company Directory"])

@router.post("/search", response_model=List[DirectoryCompanyResult])
async def search_directory_post(
    search_query: DirectorySearchQuery,
    current_user: User = Depends(get_current_user)
):
    """Searches open company directories, registries, and GitHub orgs by vertical/city/tech."""
    return await directory_service.search(search_query)

@router.get("/search", response_model=List[DirectoryCompanyResult])
async def search_directory_get(
    q: Optional[str] = Query(None, description="Freeform query e.g. 'AI startups in Pune' or 'SaaS using Python'"),
    vertical: Optional[str] = Query(None, description="Vertical/Industry e.g. 'AI', 'SaaS', 'Fintech'"),
    city: Optional[str] = Query(None, description="Target city e.g. 'Pune', 'San Francisco', 'Bengaluru'"),
    technology: Optional[str] = Query(None, description="Tech stack e.g. 'Python', 'FastAPI', 'Rust'"),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user)
):
    """GET endpoint to search open company directories and firmographics."""
    search_query = DirectorySearchQuery(
        query=q,
        vertical=vertical,
        city=city,
        technology=technology,
        limit=limit
    )
    return await directory_service.search(search_query)
