from fastapi import APIRouter, UploadFile, File, HTTPException
from uuid import uuid4
from typing import Dict
from app.api.schemas import CreateSessionRequest, CreateSessionResponse, UploadCompleteRequest
from app.models.domain import PermitSession, SessionStatus

router = APIRouter(prefix="/api/v1", tags=["sessions"])

# In-memory session store for MVP (swap for PostgreSQL later)
sessions: Dict[str, PermitSession] = {}


@router.post("/sessions", response_model=CreateSessionResponse)
async def create_session(req: CreateSessionRequest):
    """
    Creates a new permit review session from the Intake Wizard data.
    Returns a session ID and a placeholder upload URL.
    """
    session = PermitSession(
        property_address=req.property_address,
        suite_type=req.suite_type,
        laneway_abutment_length=req.laneway_abutment_length,
        pre_approved_plan_number=req.pre_approved_plan_number,
    )
    session.status = SessionStatus.UPLOADING
    sessions[str(session.id)] = session

    # In production, this would be a GCS pre-signed URL
    upload_url = f"/api/v1/sessions/{session.id}/upload"

    return CreateSessionResponse(
        session_id=str(session.id),
        status=session.status.value,
        upload_url=upload_url,
    )


@router.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """
    Retrieves the current state of a permit session.
    """
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.post("/sessions/{session_id}/upload")
async def upload_notice(session_id: str, file: UploadFile = File(...)):
    """
    Receives the Examiner's Notice PDF and triggers parsing pipeline.
    """
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    # Read file contents (in production, stream to GCS)
    contents = await file.read()
    file_size_mb = len(contents) / (1024 * 1024)

    if file_size_mb > 250:
        raise HTTPException(status_code=413, detail="File exceeds 250 MB limit")

    # Update session status
    session.status = SessionStatus.PARSING
    sessions[session_id] = session

    return {
        "session_id": session_id,
        "status": session.status.value,
        "filename": file.filename,
        "file_size_mb": round(file_size_mb, 2),
        "message": "PDF received. Parsing pipeline initiated.",
    }
