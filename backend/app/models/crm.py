import uuid
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Text, JSON, ForeignKey, Index
)
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

def generate_uuid():
    return str(uuid.uuid4())

def utc_now():
    return datetime.now(timezone.utc)

# ---------------------------------------------------------
# 1. Organization & Multi-Tenancy
# ---------------------------------------------------------
class Organization(Base):
    __tablename__ = "organizations"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    name = Column(String, nullable=False)
    slug = Column(String, unique=True, index=True, nullable=False)
    domain = Column(String, nullable=True)
    settings = Column(JSON, default=dict)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    users = relationship("CRMUser", back_populates="organization", cascade="all, delete-orphan")
    teams = relationship("Team", back_populates="organization", cascade="all, delete-orphan")
    companies = relationship("Company", back_populates="organization", cascade="all, delete-orphan")
    leads = relationship("Lead", back_populates="organization", cascade="all, delete-orphan")
    opportunities = relationship("Opportunity", back_populates="organization", cascade="all, delete-orphan")

# ---------------------------------------------------------
# 2. Teams, Roles & Permissions
# ---------------------------------------------------------
class Team(Base):
    __tablename__ = "teams"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    org_id = Column(String, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    organization = relationship("Organization", back_populates="teams")
    members = relationship("CRMUser", back_populates="team")

class Role(Base):
    __tablename__ = "roles"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    name = Column(String, unique=True, nullable=False) # SUPERADMIN, ADMIN, SALES_MANAGER, SALES_EXECUTIVE, DATA_RESEARCHER, VIEWER
    description = Column(String, nullable=True)
    permissions = Column(JSON, default=list) # Array of permission strings e.g. ["leads.view", "leads.edit"]
    created_at = Column(DateTime, default=utc_now, nullable=False)

class CRMUser(Base):
    __tablename__ = "crm_users"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    org_id = Column(String, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)
    team_id = Column(String, ForeignKey("teams.id", ondelete="SET NULL"), nullable=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    first_name = Column(String, default="")
    last_name = Column(String, default="")
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="SALES_EXECUTIVE", nullable=False, index=True) # SUPERADMIN, ADMIN, SALES_MANAGER, SALES_EXECUTIVE, DATA_RESEARCHER, VIEWER
    phone = Column(String, default="")
    avatar = Column(String, default="")
    status = Column(String, default="Active", nullable=False) # Active, Suspended, Disabled
    quota = Column(Float, default=800000.0) # Monthly / Quarterly target in ₹ INR
    won_revenue = Column(Float, default=0.0)
    active_deals_count = Column(Integer, default=0)
    profile_data = Column(JSON, default=dict)
    preferences = Column(JSON, default=dict)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    last_login_at = Column(DateTime, nullable=True)

    organization = relationship("Organization", back_populates="users")
    team = relationship("Team", back_populates="members")
    assigned_leads = relationship("Lead", back_populates="assigned_user", foreign_keys="Lead.assigned_user_id")
    owned_opportunities = relationship("Opportunity", back_populates="owner", foreign_keys="Opportunity.owner_id")
    assigned_tasks = relationship("Task", back_populates="assigned_user", foreign_keys="Task.assigned_to_id")

# ---------------------------------------------------------
# 3. Companies & Contacts (Company 360)
# ---------------------------------------------------------
class Company(Base):
    __tablename__ = "companies"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    org_id = Column(String, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String, nullable=False, index=True)
    legal_name = Column(String, nullable=True)
    website = Column(String, nullable=True, index=True)
    domain = Column(String, nullable=True, index=True)
    industry = Column(String, default="General Enterprise", index=True)
    description = Column(Text, default="")
    hq_location = Column(String, default="")
    city = Column(String, default="")
    state = Column(String, default="")
    country = Column(String, default="India")
    employee_count = Column(Integer, default=50)
    revenue_range = Column(String, default="")
    founded_year = Column(Integer, nullable=True)
    company_type = Column(String, default="B2B") # B2B, B2C, Enterprise, Institution
    status = Column(String, default="Prospect", index=True) # Prospect, Client, Churned, Active
    technology_stack = Column(JSON, default=list)
    website_intelligence = Column(JSON, default=dict)
    social_links = Column(JSON, default=dict)
    classification = Column(String, default="")
    company_score = Column(Integer, default=70)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    organization = relationship("Organization", back_populates="companies")
    contacts = relationship("Contact", back_populates="company", cascade="all, delete-orphan")
    leads = relationship("Lead", back_populates="company")
    opportunities = relationship("Opportunity", back_populates="company")

class Contact(Base):
    __tablename__ = "contacts"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    org_id = Column(String, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    company_id = Column(String, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    first_name = Column(String, default="")
    last_name = Column(String, default="")
    full_name = Column(String, nullable=False, index=True)
    designation = Column(String, default="")
    department = Column(String, default="")
    seniority = Column(String, default="Manager") # C-Level, VP, Director, Manager, Specialist, Dean, Head
    email = Column(String, index=True, nullable=True)
    phone = Column(String, index=True, nullable=True)
    alternate_phone = Column(String, nullable=True)
    linkedin_url = Column(String, nullable=True)
    location = Column(String, default="")
    is_decision_maker = Column(Boolean, default=False, index=True)
    verification_status = Column(String, default="verified") # verified, likely, unconfirmed
    status = Column(String, default="Active") # Active, Bounced, Do Not Contact
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    company = relationship("Company", back_populates="contacts")
    leads = relationship("Lead", back_populates="contact")

# ---------------------------------------------------------
# 4. Leads (17 Calling Dispositions & Lifecycle)
# ---------------------------------------------------------
class Lead(Base):
    __tablename__ = "leads"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    org_id = Column(String, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    company_id = Column(String, ForeignKey("companies.id", ondelete="SET NULL"), nullable=True, index=True)
    contact_id = Column(String, ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True, index=True)

    name = Column(String, nullable=False, index=True)
    company_name = Column(String, nullable=False, index=True)
    designation = Column(String, default="")
    department = Column(String, default="")
    seniority = Column(String, default="Manager")
    email = Column(String, index=True, nullable=True)
    phone = Column(String, index=True, nullable=True)
    alternate_phone = Column(String, nullable=True)
    website = Column(String, nullable=True)
    city = Column(String, default="")
    state = Column(String, default="")
    country = Column(String, default="India")
    industry = Column(String, default="General Enterprise")
    company_type = Column(String, default="Enterprise")
    employee_count = Column(Integer, default=50)
    revenue_range = Column(String, default="")
    linkedin_url = Column(String, nullable=True)

    source = Column(String, default="Website (thefullcircle.in)", index=True)
    source_reference = Column(String, default="") # Import Job ID or campaign ref

    # Lifecycle status: New -> Researching -> Verified -> Qualified -> Contacted -> Interested -> Meeting Scheduled -> Proposal Sent -> Negotiation -> Won -> Lost
    status = Column(String, default="New", index=True, nullable=False)

    # 17 Calling Dispositions (LionO360 workflow)
    calling_disposition = Column(String, default="Open Leads", index=True, nullable=False)

    priority = Column(String, default="Medium", index=True) # High, Medium, Low
    lead_score = Column(Integer, default=65, index=True) # 0 - 100
    score_breakdown = Column(JSON, default=dict)
    score_reason = Column(Text, default="")
    classification = Column(String, default="")

    assigned_user_id = Column(String, ForeignKey("crm_users.id", ondelete="SET NULL"), nullable=True, index=True)
    assigned_user_name = Column(String, default="")
    assigned_team_id = Column(String, ForeignKey("teams.id", ondelete="SET NULL"), nullable=True)

    last_contacted_at = Column(DateTime, nullable=True)
    next_followup_at = Column(DateTime, nullable=True)
    custom_fields = Column(JSON, default=dict)

    is_qualified = Column(Boolean, default=False)
    converted_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=utc_now, nullable=False, index=True)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    organization = relationship("Organization", back_populates="leads")
    company = relationship("Company", back_populates="leads")
    contact = relationship("Contact", back_populates="leads")
    assigned_user = relationship("CRMUser", back_populates="assigned_leads", foreign_keys=[assigned_user_id])

# ---------------------------------------------------------
# 5. Pipeline Stages & Opportunities
# ---------------------------------------------------------
class PipelineStage(Base):
    __tablename__ = "pipeline_stages"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    org_id = Column(String, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    stage_key = Column(String, nullable=False) # discovery, proposal, negotiation, won, lost
    label = Column(String, nullable=False)
    probability = Column(Integer, default=50) # 0 - 100%
    display_order = Column(Integer, default=1)
    color = Column(String, default="#3b82f6")
    description = Column(String, default="")

class Opportunity(Base):
    __tablename__ = "opportunities"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    org_id = Column(String, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    company_id = Column(String, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    contact_id = Column(String, ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True)
    associated_lead_id = Column(String, ForeignKey("leads.id", ondelete="SET NULL"), nullable=True)

    title = Column(String, nullable=False, index=True)
    company_name = Column(String, nullable=False)
    contact_name = Column(String, default="")
    contact_email = Column(String, default="")

    value = Column(Float, default=0.0, nullable=False) # In ₹ INR
    stage = Column(String, default="discovery", index=True, nullable=False) # discovery, proposal, negotiation, won, lost
    probability = Column(Integer, default=30) # 0 - 100%
    expected_close_date = Column(DateTime, nullable=True)
    priority = Column(String, default="Medium") # High, Medium, Low

    owner_id = Column(String, ForeignKey("crm_users.id", ondelete="SET NULL"), nullable=True, index=True)
    owner_name = Column(String, default="")
    owner_avatar = Column(String, default="")

    notes_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=utc_now, nullable=False, index=True)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    organization = relationship("Organization", back_populates="opportunities")
    company = relationship("Company", back_populates="opportunities")
    owner = relationship("CRMUser", back_populates="owned_opportunities", foreign_keys=[owner_id])

# ---------------------------------------------------------
# 6. Activities, Tasks & Timeline
# ---------------------------------------------------------
class Activity(Base):
    __tablename__ = "activities"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    org_id = Column(String, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    entity_type = Column(String, nullable=False, index=True) # lead, deal, contact, company, general
    entity_id = Column(String, nullable=True, index=True)
    entity_name = Column(String, nullable=True)

    type = Column(String, nullable=False, index=True) # call, email, meeting, note, stage_change, task, import, assignment
    title = Column(String, nullable=False)
    description = Column(Text, default="")
    author_id = Column(String, nullable=True)
    author_name = Column(String, default="Mritunjay Singh")
    author_avatar = Column(String, nullable=True)

    status = Column(String, nullable=True) # pending, completed
    due_date = Column(DateTime, nullable=True)
    priority = Column(String, nullable=True)
    extra_data = Column(JSON, default=dict)
    timestamp = Column(DateTime, default=utc_now, nullable=False, index=True)

class Task(Base):
    __tablename__ = "tasks"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    org_id = Column(String, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    type = Column(String, default="follow_up") # call, email, meeting, follow_up, research, custom
    title = Column(String, nullable=False)
    description = Column(Text, default="")
    due_date = Column(DateTime, nullable=False, index=True)
    priority = Column(String, default="Medium", index=True) # High, Medium, Low
    status = Column(String, default="pending", index=True) # pending, in_progress, completed, overdue, cancelled

    assigned_to_id = Column(String, ForeignKey("crm_users.id", ondelete="CASCADE"), nullable=False, index=True)
    assigned_to_name = Column(String, default="")

    lead_id = Column(String, ForeignKey("leads.id", ondelete="SET NULL"), nullable=True)
    lead_name = Column(String, nullable=True)
    company_id = Column(String, ForeignKey("companies.id", ondelete="SET NULL"), nullable=True)
    company_name = Column(String, nullable=True)
    opportunity_id = Column(String, ForeignKey("opportunities.id", ondelete="SET NULL"), nullable=True)

    created_at = Column(DateTime, default=utc_now, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    assigned_user = relationship("CRMUser", back_populates="assigned_tasks", foreign_keys=[assigned_to_id])

# ---------------------------------------------------------
# 7. Data Import Engine (Large File & Batch Management)
# ---------------------------------------------------------
class ImportJob(Base):
    __tablename__ = "import_jobs"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    org_id = Column(String, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String, nullable=True)
    user_name = Column(String, default="")

    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=True)
    file_size_bytes = Column(Integer, default=0)

    total_rows = Column(Integer, default=0)
    processed_rows = Column(Integer, default=0)
    created_rows = Column(Integer, default=0)
    updated_rows = Column(Integer, default=0)
    duplicate_rows = Column(Integer, default=0)
    invalid_rows = Column(Integer, default=0)

    status = Column(String, default="QUEUED", index=True) # QUEUED, RUNNING, COMPLETED, FAILED, CANCELLED
    deduplication_rule = Column(String, default="email_or_phone") # email, phone, linkedin, company_domain, upsert
    column_mapping = Column(JSON, default=dict)
    sample_preview = Column(JSON, default=list)

    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    errors = relationship("ImportRowError", back_populates="import_job", cascade="all, delete-orphan")

class ImportRowError(Base):
    __tablename__ = "import_row_errors"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    import_id = Column(String, ForeignKey("import_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    row_index = Column(Integer, nullable=False)
    reason = Column(String, nullable=False)
    raw_payload = Column(JSON, default=dict)

    import_job = relationship("ImportJob", back_populates="errors")

# ---------------------------------------------------------
# 8. Website Intelligence & Scans
# ---------------------------------------------------------
class WebsiteScan(Base):
    __tablename__ = "website_scans"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    url = Column(String, nullable=False, index=True)
    domain = Column(String, nullable=False, index=True)
    title = Column(String, default="")
    meta_description = Column(Text, default="")
    business_type = Column(String, default="B2B Enterprise")
    industry = Column(String, default="")
    services = Column(JSON, default=list)
    technologies = Column(JSON, default=list)
    contact_info = Column(JSON, default=dict)
    social_links = Column(JSON, default=dict)
    target_match_pct = Column(Integer, default=85)
    confidence_score = Column(Integer, default=90)
    priority = Column(String, default="HIGH")
    extracted_text_snippet = Column(Text, default="")
    scanned_at = Column(DateTime, default=utc_now, nullable=False)

# ---------------------------------------------------------
# 9. Automations Engine & Runs
# ---------------------------------------------------------
class AutomationWorkflow(Base):
    __tablename__ = "automations"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    org_id = Column(String, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(String, default="")
    trigger_type = Column(String, nullable=False) # LEAD_CREATED, STATUS_CHANGED, IMPORT_COMPLETED, SCORE_THRESHOLD
    trigger_config = Column(JSON, default=dict)
    conditions = Column(JSON, default=list)
    actions = Column(JSON, default=list)
    is_active = Column(Boolean, default=True)
    execution_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

class AutomationRun(Base):
    __tablename__ = "automation_runs"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    automation_id = Column(String, ForeignKey("automations.id", ondelete="CASCADE"), nullable=False, index=True)
    trigger_event = Column(String, nullable=False)
    status = Column(String, default="SUCCESS") # SUCCESS, FAILED
    error_message = Column(Text, nullable=True)
    executed_at = Column(DateTime, default=utc_now, nullable=False)

# ---------------------------------------------------------
# 10. Campaigns & Outreach
# ---------------------------------------------------------
class Campaign(Base):
    __tablename__ = "campaigns"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    org_id = Column(String, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String, nullable=False)
    channel = Column(String, default="Email") # Email, WhatsApp, Calling, LinkedIn
    status = Column(String, default="Draft") # Draft, Active, Completed, Paused
    audience_count = Column(Integer, default=0)
    sent_count = Column(Integer, default=0)
    delivered_count = Column(Integer, default=0)
    opened_count = Column(Integer, default=0)
    clicked_count = Column(Integer, default=0)
    replied_count = Column(Integer, default=0)
    converted_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=utc_now, nullable=False)

# ---------------------------------------------------------
# 11. Notifications, Audit Logs & Google Sheets
# ---------------------------------------------------------
class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    org_id = Column(String, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String, nullable=True, index=True)
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    type = Column(String, default="system") # deal, lead, task, system, import
    is_read = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

class CRMAuditLog(Base):
    __tablename__ = "crm_audit_logs"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    org_id = Column(String, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String, nullable=True, index=True)
    user_name = Column(String, default="System")
    action = Column(String, nullable=False, index=True) # CREATE, UPDATE, DELETE, IMPORT, EXPORT, ASSIGN, CONVERT
    entity = Column(String, nullable=False, index=True) # Lead, Company, Contact, Deal, Task
    entity_id = Column(String, nullable=True, index=True)
    old_values = Column(JSON, default=dict)
    new_values = Column(JSON, default=dict)
    ip_address = Column(String, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False, index=True)

class GoogleSheetsIntegration(Base):
    __tablename__ = "google_sheets_integrations"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    org_id = Column(String, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    spreadsheet_id = Column(String, nullable=False)
    spreadsheet_name = Column(String, default="")
    sheet_name = Column(String, default="")
    sync_direction = Column(String, default="import_only") # import_only, bi_directional
    column_mapping = Column(JSON, default=dict)
    field_ownership = Column(JSON, default=dict)
    last_sync_at = Column(DateTime, nullable=True)
    last_row_processed = Column(Integer, default=0)
    sync_status = Column(String, default="CONNECTED") # CONNECTED, SYNCING, ERROR, DISCONNECTED
    created_at = Column(DateTime, default=utc_now, nullable=False)
