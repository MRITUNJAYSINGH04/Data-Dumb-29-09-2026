from enum import Enum
from typing import Optional, List
from pydantic import BaseModel

class ExportFormat(str, Enum):
    JSON = "json"
    CSV = "csv"
    MARKDOWN = "markdown"
    HTML = "html"
    PDF = "pdf"

class ExportRequest(BaseModel):
    investigation_id: str
    format: ExportFormat
    include_raw_evidence: bool = True
    include_contradictions: bool = True
    include_lead_score: bool = True
