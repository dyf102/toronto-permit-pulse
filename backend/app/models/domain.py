from enum import Enum
from datetime import datetime
from uuid import UUID, uuid4
from pydantic import BaseModel, Field

class SessionStatus(str, Enum):
    INTAKE = "INTAKE"
    UPLOADING = "UPLOADING"
    PARSING = "PARSING"
    ANALYZING = "ANALYZING"
    CLARIFYING = "CLARIFYING"
    DRAFTING = "DRAFTING"
    COMPLETE = "COMPLETE"
    ERROR = "ERROR"

class SuiteType(str, Enum):
    GARDEN = "GARDEN"
    LANEWAY = "LANEWAY"

class DeficiencyCategory(str, Enum):
    ZONING = "ZONING"
    OBC = "OBC"
    FIRE_ACCESS = "FIRE_ACCESS"
    TREE_PROTECTION = "TREE_PROTECTION"
    LANDSCAPING = "LANDSCAPING"
    SERVICING = "SERVICING"
    OTHER = "OTHER"

class ResolutionStatus(str, Enum):
    RESOLVED = "RESOLVED"
    DRAWING_REVISION_NEEDED = "DRAWING_REVISION_NEEDED"
    VARIANCE_REQUIRED = "VARIANCE_REQUIRED"
    LDA_REQUIRED = "LDA_REQUIRED"
    OUT_OF_SCOPE = "OUT_OF_SCOPE"

class PermitSession(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    status: SessionStatus = SessionStatus.INTAKE
    property_address: str
    suite_type: SuiteType
    bylaw_context: str | None = None
    is_former_municipal_zoning: bool = False
    laneway_abutment_length: float | None = None
    pre_approved_plan_number: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None

class DeficiencyItem(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    session_id: UUID | None = None
    category: DeficiencyCategory
    raw_notice_text: str
    extracted_action: str
    agent_confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    order_index: int | None = None

class Citation(BaseModel):
    bylaw: str
    section: str
    version: str
    effective_date: str | None = None

class GeneratedResponse(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    deficiency_id: UUID
    draft_text: str
    citations: list[Citation] = []
    resolution_status: ResolutionStatus
    variance_magnitude: str | None = None
    agent_reasoning: str

class ClarificationExchange(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    session_id: UUID
    agent_name: str
    question_text: str
    user_response: str | None = None
    asked_at: datetime = Field(default_factory=datetime.utcnow)
    answered_at: datetime | None = None

class ExaminerNoticeExtractionResult(BaseModel):
    """Structured output expected from the Claude model when parsing notice."""
    items: list[DeficiencyItem]
