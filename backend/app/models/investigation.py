import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class Investigation(Base):
    __tablename__ = "investigations"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    title = Column(String, nullable=False)
    mode = Column(String, nullable=False, default="quick")
    status = Column(String, nullable=False, default="QUEUED", index=True)
    progress = Column(Integer, default=0, nullable=False)
    current_step = Column(String, default="", nullable=False)
    workspace_dir = Column(String, nullable=True)
    
    input_data = Column(JSON, nullable=False)
    modules_planned = Column(JSON, default=list, nullable=False)
    modules_completed = Column(JSON, default=list, nullable=False)
    
    entity_match_score = Column(Integer, default=0, nullable=False)
    contradictions = Column(JSON, default=list, nullable=False)
    lead_score = Column(JSON, nullable=True)
    
    report_markdown = Column(Text, nullable=True)
    report_json = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="investigations")
    evidence_items = relationship("EvidenceItem", back_populates="investigation", cascade="all, delete-orphan")
    graph_nodes = relationship("GraphNode", back_populates="investigation", cascade="all, delete-orphan")
    graph_edges = relationship("GraphEdge", back_populates="investigation", cascade="all, delete-orphan")

class EvidenceItem(Base):
    __tablename__ = "evidence_items"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    investigation_id = Column(String, ForeignKey("investigations.id", ondelete="CASCADE"), nullable=False, index=True)
    source = Column(String, nullable=False, index=True)
    source_type = Column(String, nullable=False)
    query = Column(String, nullable=False)
    entity_type = Column(String, nullable=False)
    entity = Column(String, nullable=False)
    attribute = Column(String, nullable=False)
    value = Column(Text, nullable=False)
    url = Column(Text, nullable=False)
    timestamp = Column(String, nullable=False)
    confidence = Column(Float, nullable=False, default=0.5)
    status = Column(String, nullable=False, default="unconfirmed") # verified, likely, possible, unconfirmed
    evidence = Column(Text, nullable=False)
    raw_reference = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    investigation = relationship("Investigation", back_populates="evidence_items")

class GraphNode(Base):
    __tablename__ = "graph_nodes"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    investigation_id = Column(String, ForeignKey("investigations.id", ondelete="CASCADE"), nullable=False, index=True)
    node_id = Column(String, nullable=False)
    label = Column(String, nullable=False)
    node_type = Column(String, nullable=False)
    properties = Column(JSON, default=dict)

    investigation = relationship("Investigation", back_populates="graph_nodes")

class GraphEdge(Base):
    __tablename__ = "graph_edges"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    investigation_id = Column(String, ForeignKey("investigations.id", ondelete="CASCADE"), nullable=False, index=True)
    source_node_id = Column(String, nullable=False)
    target_node_id = Column(String, nullable=False)
    relationship_type = Column(String, nullable=False)
    confidence = Column(Float, nullable=False, default=0.7)
    evidence = Column(Text, nullable=False)

    investigation = relationship("Investigation", back_populates="graph_edges")
