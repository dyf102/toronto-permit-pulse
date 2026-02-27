from typing import Optional
from pydantic import BaseModel
from app.models.domain import SuiteType


class CreateSessionRequest(BaseModel):
    property_address: str
    suite_type: SuiteType
    laneway_abutment_length: Optional[float] = None
    pre_approved_plan_number: Optional[str] = None


class CreateSessionResponse(BaseModel):
    session_id: str
    status: str
    upload_url: str


class UploadCompleteRequest(BaseModel):
    filename: str
    file_size: int
