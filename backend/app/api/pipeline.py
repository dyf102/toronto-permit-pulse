"""
Full pipeline endpoint: Upload PDF → Parse → Validate → Draft responses.
Includes both synchronous and SSE streaming variants.
"""
import asyncio
import json
import os
import tempfile
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse
from uuid import UUID, uuid4

from app.models.domain import PermitSession, SuiteType, SessionStatus
from app.services.pdf_parser import ExaminerNoticeParserService
from app.services.orchestrator import OrchestratorService

router = APIRouter(prefix="/api/v1", tags=["pipeline"])

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")


def _sse_event(event: str, data: dict) -> str:
    """Format a single SSE event."""
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


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

    contents = await file.read()
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(contents)
        tmp_path = tmp.name

    try:
        session.status = SessionStatus.PARSING
        parser = ExaminerNoticeParserService(api_key=GOOGLE_API_KEY)
        deficiencies = parser.parse_examiner_notice(
            session_id=session.id, pdf_path=tmp_path
        )

        session.status = SessionStatus.ANALYZING
        orchestrator = OrchestratorService()
        result = orchestrator.process_deficiencies(session, deficiencies)

        session.status = SessionStatus.COMPLETE
        result["status"] = session.status.value
        result["session_id"] = str(session.id)
        result["property_address"] = property_address
        result["suite_type"] = suite_type.upper()

        return result

    except Exception as e:
        session.status = SessionStatus.ERROR
        raise HTTPException(status_code=500, detail=f"Pipeline failed: {str(e)}")
    finally:
        os.unlink(tmp_path)


@router.post("/pipeline/stream")
async def stream_pipeline(
    property_address: str = Form(...),
    suite_type: str = Form(...),
    file: UploadFile = File(...),
    laneway_abutment_length: float = Form(None),
):
    """
    SSE streaming variant of the pipeline. Returns a text/event-stream
    response with real-time progress updates as each stage completes.

    Events emitted:
      - progress: { stage, description, percent }
      - item:     { index, total, category, action }
      - complete: { <full result payload> }
      - error:    { message }
    """
    if not GOOGLE_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="GOOGLE_API_KEY not configured. Set it in your environment.",
        )

    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    try:
        st = SuiteType(suite_type.upper())
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid suite_type. Must be GARDEN or LANEWAY, got: {suite_type}",
        )

    # Read the file before entering the generator
    contents = await file.read()

    async def event_generator():
        tmp_path = None
        try:
            # --- Stage 1: Upload received ---
            yield _sse_event("progress", {
                "stage": "upload",
                "description": "PDF uploaded successfully",
                "percent": 10,
            })
            await asyncio.sleep(0)

            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                tmp.write(contents)
                tmp_path = tmp.name

            # --- Stage 2: Parsing ---
            yield _sse_event("progress", {
                "stage": "parse",
                "description": "Parsing Examiner's Notice with Gemini Vision…",
                "percent": 20,
            })
            await asyncio.sleep(0)

            session = PermitSession(
                property_address=property_address,
                suite_type=st,
                laneway_abutment_length=laneway_abutment_length,
            )
            session.status = SessionStatus.PARSING

            parser = ExaminerNoticeParserService(api_key=GOOGLE_API_KEY)
            loop = asyncio.get_event_loop()
            deficiencies = await loop.run_in_executor(
                None, parser.parse_examiner_notice, session.id, tmp_path
            )

            yield _sse_event("progress", {
                "stage": "parse",
                "description": f"Found {len(deficiencies)} deficiency item(s)",
                "percent": 40,
            })
            await asyncio.sleep(0)

            # --- Stage 3: Analyzing each item ---
            yield _sse_event("progress", {
                "stage": "analyze",
                "description": "Routing to specialist agents…",
                "percent": 45,
            })
            await asyncio.sleep(0)

            session.status = SessionStatus.ANALYZING
            from app.services.agents import get_agent_for_deficiency

            results = []
            unhandled = []
            total = len(deficiencies)

            for idx, item in enumerate(deficiencies):
                agent = get_agent_for_deficiency(item)
                pct = 45 + int((idx / max(total, 1)) * 40)

                if agent:
                    yield _sse_event("item", {
                        "index": idx + 1,
                        "total": total,
                        "category": item.category.value,
                        "action": item.extracted_action or "Analyzing…",
                        "agent": agent.agent_name,
                    })
                    await asyncio.sleep(0)

                    try:
                        response = await loop.run_in_executor(
                            None, agent.validate, item
                        )
                        results.append({
                            "deficiency": item.dict(),
                            "response": response.dict(),
                            "agent": agent.agent_name,
                        })
                    except Exception as e:
                        results.append({
                            "deficiency": item.dict(),
                            "response": None,
                            "agent": agent.agent_name,
                            "error": str(e),
                        })
                else:
                    unhandled.append({
                        "deficiency": item.dict(),
                        "reason": f"No agent registered for category: {item.category}",
                    })

                yield _sse_event("progress", {
                    "stage": "analyze",
                    "description": f"Processed item {idx + 1} of {total}",
                    "percent": pct,
                })
                await asyncio.sleep(0)

            # --- Stage 4: Packaging ---
            yield _sse_event("progress", {
                "stage": "draft",
                "description": "Packaging response document…",
                "percent": 90,
            })
            await asyncio.sleep(0)

            summary = {
                "total_deficiencies": total,
                "processed": len(results),
                "unhandled": len(unhandled),
                "by_category": {},
            }
            for item in deficiencies:
                cat = item.category.value
                summary["by_category"][cat] = summary["by_category"].get(cat, 0) + 1

            result = {
                "session_id": str(session.id),
                "suite_type": suite_type.upper(),
                "property_address": property_address,
                "summary": summary,
                "results": results,
                "unhandled": unhandled,
                "status": "COMPLETE",
            }

            yield _sse_event("progress", {
                "stage": "complete",
                "description": "Analysis complete",
                "percent": 100,
            })
            yield _sse_event("complete", result)

        except Exception as e:
            yield _sse_event("error", {"message": str(e)})

        finally:
            if tmp_path:
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
