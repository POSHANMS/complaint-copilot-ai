import uuid
from sqlalchemy import Column, String, Float, Boolean, Text, DateTime, JSON, Integer
from sqlalchemy.sql import func
from app.db.database import Base

class Complaint(Base):
    __tablename__ = "complaints"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    complaint_source = Column(Text, nullable=True)
    customer_name = Column(Text, nullable=True)
    product_name = Column(Text, nullable=True)
    product_strength_grade = Column(Text, nullable=True)
    batch_lot_number = Column(Text, nullable=True)
    manufacturing_date = Column(Text, nullable=True)
    expiry_date = Column(Text, nullable=True)
    quantity_affected = Column(Text, nullable=True)
    complaint_type = Column(Text, nullable=True)
    complaint_date = Column(Text, nullable=True)
    detailed_description = Column(Text, nullable=True)
    
    initial_severity = Column(Text, nullable=True)  # Critical / Major / Minor
    priority = Column(Text, nullable=True)          # High / Medium / Low
    risk_score = Column(Float, nullable=True)
    risk_reasoning = Column(Text, nullable=True)
    
    completeness_score = Column(Float, nullable=True)
    missing_fields = Column(JSON, nullable=True)
    
    is_duplicate = Column(Boolean, default=False)
    duplicate_match_id = Column(String, nullable=True)
    
    capa_recommendation = Column(Text, nullable=True)
    ai_summary = Column(Text, nullable=True)
    status = Column(Text, default="Pending Triage")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class ExtractionLog(Base):
    __tablename__ = "extraction_logs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    complaint_id = Column(String, nullable=True)
    node_name = Column(Text, nullable=False)
    input_snapshot = Column(JSON, nullable=True)
    output_snapshot = Column(JSON, nullable=True)
    latency_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    complaint_id = Column(String, nullable=True)
    role = Column(Text, nullable=False)  # 'user' | 'assistant'
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
