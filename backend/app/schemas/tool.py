from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime

class ToolStatus(BaseModel):
    id: str
    name: str
    layer: Optional[str] = "layer1_infrastructure"
    layer_display: Optional[str] = "Layer 1: Infrastructure & Perimeter Recon"
    category: str
    description: str
    installed: bool
    version: str
    license: str
    enabled: bool
    last_execution: Optional[datetime] = None
    success_rate: float
    avg_execution_time_seconds: float
    supported_identifiers: List[str]

class ToolToggleRequest(BaseModel):
    enabled: bool

class SearchQueryRequest(BaseModel):
    query: str
    category: Optional[str] = "general"
    limit: Optional[int] = 10
