"""
Full pipeline endpoint: Upload PDF → Parse → Validate → Draft responses.
This is the main endpoint a user would call after the intake wizard.
"""
import os
import tempfile
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from uuid import UUID, uuid4

from app.models.domain import PermitSession, SuiteType, SessionStatus
from app.services.pdf_parser import ExaminerNoticeParserService
from app.services.orchestrator import OrchestratorService

router = APIRouter(prefix="/api/v1", tags=["pipeline"])

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")


@router.post("/pipeline/run")
async def run_full_pipeline(
    property_address: str = Form(...),
    suite_type: str = Form(...),
    file: UploadFile = File(...),
    laneway_abutment_length: float = Form(None),
):
    """
    End-to-end pipeline: accepts a PDF and property details,
    parses deficiencies, routes to specialist agents, and returns
    a complete response package.
    """
    if not GOOGLE_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="GOOGLE_API_KEY not configured. Set it in your environment.",
        )

    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    # Create session
    try:
        st = SuiteType(suite_type.upper())
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid suite_type. Must be GARDEN or LANEWAY, got: {suite_type}",
        )

    session = PermitSession(
        property_address=property_address,
        suite_type=st,
        laneway_abutment_length=laneway_abutment_length,
    )

    # Save uploaded file
    contents = await file.read()
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(contents)
        tmp_path = tmp.name

    try:
        # Step 1: Parse
        session.status = SessionStatus.PARSING
        parser = ExaminerNoticeParserService(api_key=GOOGLE_API_KEY)
        deficiencies = parser.parse_examiner_notice(
            session_id=session.id, pdf_path=tmp_path
        )

        # Step 2: Analyze via specialist agents
        session.status = SessionStatus.ANALYZING
        orchestrator = OrchestratorService()
        result = orchestrator.process_deficiencies(session, deficiencies)

        session.status = SessionStatus.COMPLETE
        result["status"] = session.status.value

        return result

    except Exception as e:
        session.status = SessionStatus.ERROR
        raise HTTPException(status_code=500, detail=f"Pipeline failed: {str(e)}")
    finally:
        os.unlink(tmp_path)
