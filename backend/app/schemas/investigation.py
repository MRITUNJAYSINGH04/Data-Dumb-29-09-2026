from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

class InvestigationMode(str, Enum):
    QUICK = "quick"
    DEEP = "deep"
    PROFESSIONAL_VERIFICATION = "professional_verification"
    LEAD_GENERATION = "lead_generation"
    COMPANY_INTELLIGENCE = "company_intelligence"

class InvestigationStatus(str, Enum):
    QUEUED = "QUEUED"
    PLANNING = "PLANNING"
    SEARCHING = "SEARCHING"
    CORRELATING = "CORRELATING"
    VERIFYING = "VERIFYING"
    GENERATING_REPORT = "GENERATING_REPORT"
    COMPLETED = "COMPLETED"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"

class VerificationStatus(str, Enum):
    VERIFIED = "verified"
    LIKELY = "likely"
    POSSIBLE = "possible"
    UNCONFIRMED = "unconfirmed"

class InvestigationInput(BaseModel):
    name: Optional[str] = Field(default=None, description="Full name of person")
    email: Optional[str] = Field(default=None, description="Public professional email")
    phone: Optional[str] = Field(default=None, description="Phone number")
    username: Optional[str] = Field(default=None, description="Known online handle/username")
    company: Optional[str] = Field(default=None, description="Company or organization")
    domain: Optional[str] = Field(default=None, description="Corporate or target domain")
    profile_urls: List[str] = Field(default_factory=list, description="Public profile URLs")
    website_urls: List[str] = Field(default_factory=list, description="Website or blog URLs")
    image: Optional[str] = Field(default=None, description="Optional public image URL or reference")
    country: Optional[str] = Field(default=None, description="Target country")
    city: Optional[str] = Field(default=None, description="Target city")
    investigation_mode: InvestigationMode = Field(
        default=InvestigationMode.QUICK,
        description="Investigation depth and focus mode"
    )
    target_industry: Optional[str] = Field(default=None, description="Target industry for lead gen/company research")
    target_role: Optional[str] = Field(default=None, description="Target role e.g. CTO, VP Engineering")
    target_company_size: Optional[str] = Field(default=None, description="Company size range e.g. 11-50, 51-200")

class NormalizedResult(BaseModel):
    source: str = Field(description="Name of the source tool or platform")
    source_type: str = Field(description="Type e.g. search_engine, public_api, code_repo, osint_tool")
    query: str = Field(description="Search term or identifier queried")
    entity_type: str = Field(description="person, company, domain, email, username, etc.")
    entity: str = Field(description="Entity label/identifier")
    attribute: str = Field(description="Attribute name e.g. job_title, repo_owner, dns_mx, presence")
    value: str = Field(description="Extracted attribute value")
    url: str = Field(description="Exact public source URL provenance")
    timestamp: str = Field(description="ISO timestamp of data retrieval")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score 0.0 to 1.0")
    status: VerificationStatus = Field(description="verified, likely, possible, unconfirmed")
    evidence: str = Field(description="Snippet, proof or supporting context")
    raw_reference: Optional[str] = Field(default="", description="Raw serialized reference data or payload")

class VectorExecutionStatus(BaseModel):
    tool: str
    layer: str
    layer_display: str
    status: str
    execution_time_seconds: float
    findings_count: int

class LeadScoreBreakdown(BaseModel):
    total_score: int = Field(ge=0, le=100, description="Composite score 0-100")
    icp_match: int = Field(default=0, ge=0, le=25)
    decision_maker: int = Field(default=0, ge=0, le=20)
    company_size: int = Field(default=0, ge=0, le=15)
    industry_relevance: int = Field(default=0, ge=0, le=15)
    technology_match: int = Field(default=0, ge=0, le=10)
    recent_activity: int = Field(default=0, ge=0, le=5)
    public_business_email: int = Field(default=0, ge=0, le=5)
    evidence_confidence: int = Field(default=0, ge=0, le=5)
    explanation: Dict[str, str] = Field(default_factory=dict)
    outreach_brief: Optional[str] = None
    suggested_icebreaker: Optional[str] = None

class ContradictionItem(BaseModel):
    attribute: str
    claim_a: Dict[str, Any]
    claim_b: Dict[str, Any]
    analysis: str

class ExecutionLogEntry(BaseModel):
    timestamp: str
    tool: str
    layer: str
    message: str
    level: str = "info"

class QualifiedLeadItem(BaseModel):
    id: str
    name: str
    role: str
    email: Optional[str] = None
    email_status: str = "verified"
    company: str
    domain: str
    social_handles: Dict[str, str] = Field(default_factory=dict)
    tech_stack: List[str] = Field(default_factory=list)
    city: Optional[str] = None
    country: Optional[str] = None
    lead_score: int = Field(ge=0, le=100, default=85)
    confidence: float = 0.90
    provenance_urls: List[str] = Field(default_factory=list)
    icebreaker: Optional[str] = None

class DirectoryCompanyResult(BaseModel):
    id: str
    name: str
    domain: str
    vertical: str
    city: str
    country: str
    description: str
    employee_count_range: str
    tech_stack: List[str]
    registration_status: str
    registry_id: Optional[str] = None
    source_url: str
    decision_makers: List[Dict[str, str]] = Field(default_factory=list)

class DirectorySearchQuery(BaseModel):
    query: Optional[str] = None
    vertical: Optional[str] = None
    city: Optional[str] = None
    technology: Optional[str] = None
    limit: int = 20

class InvestigationResponse(BaseModel):
    id: str
    title: str
    mode: InvestigationMode
    status: InvestigationStatus
    progress: int = Field(default=0, ge=0, le=100)
    current_step: str = ""
    workspace_dir: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    input_data: InvestigationInput
    modules_planned: List[str] = Field(default_factory=list)
    modules_completed: List[str] = Field(default_factory=list)
    results_count: int = 0
    entity_match_score: int = 0
    contradictions: List[ContradictionItem] = Field(default_factory=list)
    lead_score: Optional[LeadScoreBreakdown] = None
    report_markdown: Optional[str] = None
    report_json: Optional[Dict[str, Any]] = None
    vector_statuses: List[VectorExecutionStatus] = Field(default_factory=list)
    leads: List[QualifiedLeadItem] = Field(default_factory=list)
    logs: List[ExecutionLogEntry] = Field(default_factory=list)

class InvestigationSummary(BaseModel):
    id: str
    title: str
    mode: InvestigationMode
    status: InvestigationStatus
    progress: int
    current_step: str
    workspace_dir: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    results_count: int
    entity_match_score: int
