import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Text, JSON
from backend.app.core.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    user_id = Column(String, nullable=True, index=True)
    action = Column(String, nullable=False, index=True)
    target_type = Column(String, nullable=False) # investigation, user, export, purge, tool
    target_id = Column(String, nullable=True)
    details = Column(JSON, default=dict)
    ip_address = Column(String, nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
