"""
Gemini-powered Examiner Notice parsing endpoint.
Takes a session ID + uploaded PDF, extracts text with PyMuPDF,
then uses Gemini 2.5 Flash to structure deficiencies.
"""
import os
import tempfile
from fastapi import APIRouter, UploadFile, File, HTTPException
from uuid import UUID

router = APIRouter(prefix="/api/v1", tags=["parsing"])

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")


@router.post("/sessions/{session_id}/parse")
async def parse_examiner_notice(session_id: str, file: UploadFile = File(...)):
    """
    Upload a PDF and get structured deficiency extraction via Gemini.
    This is the core AI endpoint.
    """
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    if not GOOGLE_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="GOOGLE_API_KEY not configured. Set it in your environment.",
        )

    contents = await file.read()

    # Write to a temp file for PyMuPDF processing
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(contents)
        tmp_path = tmp.name

    try:
        from app.services.pdf_parser import ExaminerNoticeParserService

        parser = ExaminerNoticeParserService(api_key=GOOGLE_API_KEY)
        items = parser.parse_examiner_notice(
            session_id=UUID(session_id), pdf_path=tmp_path
        )

        return {
            "session_id": session_id,
            "deficiency_count": len(items),
            "items": [item.dict() for item in items],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Parsing failed: {str(e)}")
    finally:
        os.unlink(tmp_path)
