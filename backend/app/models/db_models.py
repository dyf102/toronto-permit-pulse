import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Boolean, DateTime, ForeignKey, Text, Integer, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship

from app.db.database import Base
from app.models.domain import SessionStatus, SuiteType, DeficiencyCategory

class PermitSessionDB(Base):
    __tablename__ = "permit_sessions"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    status = Column(SQLEnum(SessionStatus), nullable=False, default=SessionStatus.INTAKE)
    property_address = Column(String, nullable=False)
    suite_type = Column(SQLEnum(SuiteType), nullable=False)
    bylaw_context = Column(String, nullable=True)
    is_former_municipal_zoning = Column(Boolean, default=False)
    laneway_abutment_length = Column(Float, nullable=True)
    pre_approved_plan_number = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    deficiencies = relationship("DeficiencyItemDB", back_populates="session", cascade="all, delete-orphan")

class DeficiencyItemDB(Base):
    __tablename__ = "deficiency_items"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(PGUUID(as_uuid=True), ForeignKey("permit_sessions.id"), nullable=False)
    category = Column(SQLEnum(DeficiencyCategory), nullable=False)
    raw_notice_text = Column(Text, nullable=False)
    extracted_action = Column(Text, nullable=False)
    agent_confidence = Column(Float, default=1.0)
    order_index = Column(Integer, nullable=False)

    session = relationship("PermitSessionDB", back_populates="deficiencies")
