"""
Export endpoint: accepts the pipeline result JSON and returns a PDF
resubmission package as a downloadable file.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Any, Dict, List, Optional
import io

from app.services.pdf_export import ResubmissionPackageGenerator

router = APIRouter(prefix="/api/v1", tags=["export"])


class CitationPayload(BaseModel):
    bylaw: str = ""
    section: str = ""
    version: str = ""


class DeficiencyPayload(BaseModel):
    id: Optional[str] = None
    session_id: Optional[str] = None
    category: str = "OTHER"
    raw_notice_text: str = ""
    extracted_action: str = ""
    agent_confidence: float = 0.8
    order_index: Optional[int] = None


class ResponsePayload(BaseModel):
    id: Optional[str] = None
    deficiency_id: Optional[str] = None
    draft_text: str = ""
    citations: List[CitationPayload] = []
    resolution_status: str = "OUT_OF_SCOPE"
    variance_magnitude: Optional[str] = None
    agent_reasoning: str = ""


class ResultItem(BaseModel):
    deficiency: DeficiencyPayload
    response: Optional[ResponsePayload] = None
    agent: str = "AI Agent"
    error: Optional[str] = None


class UnhandledItem(BaseModel):
    deficiency: DeficiencyPayload
    reason: str = ""


class SummaryPayload(BaseModel):
    total_deficiencies: int = 0
    processed: int = 0
    unhandled: int = 0
    by_category: Dict[str, int] = {}


class ExportRequest(BaseModel):
    session_id: str = ""
    suite_type: str = "GARDEN"
    property_address: str = ""
    summary: SummaryPayload = SummaryPayload()
    results: List[ResultItem] = []
    unhandled: List[UnhandledItem] = []
    status: str = "COMPLETE"


@router.post("/export/pdf")
async def export_pdf(payload: ExportRequest):
    """
    Generate and return a PDF resubmission package.
    Accepts the same JSON structure returned by /pipeline/run.
    """
    try:
        # Convert Pydantic models to dicts for the generator
        data = payload.dict()
        generator = ResubmissionPackageGenerator(data)
        pdf_bytes = generator.generate()

        # Build filename
        addr_slug = (
            payload.property_address
            .replace(",", "")
            .replace(" ", "_")
            .lower()[:40]
        )
        filename = f"resubmission_package_{addr_slug}.pdf"

        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Length": str(len(pdf_bytes)),
            },
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"PDF generation failed: {str(e)}",
        )
