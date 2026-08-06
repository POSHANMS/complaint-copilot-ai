"""
FastAPI Route: POST /api/complaints/extract
Accepts: multipart file upload (PDF/DOCX/TXT) OR raw text body.
Runs the 7-node LangGraph complaint_pipeline via real SSE streaming (or JSON),
persists the complaint to DB, and emits node completion events in real time.
Enforces 10MB max file size limit and strict file type/magic-byte validation.
"""
import asyncio
import json
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import StreamingResponse, JSONResponse

from app.agent.graph import complaint_pipeline
from app.services.document_parser import parse_document
from app.db.database import SessionLocal
from app.db.models import Complaint
from app.core.logging import logger

router = APIRouter(prefix="/complaints", tags=["Extraction"])

MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB

NODE_PROGRESS_MAP = {
    "ingest_document":        (14, "Parsing & ingesting document..."),
    "extract_entities":       (28, "Running extract_entities node (LLM)..."),
    "validate_completeness":  (42, "Running validate_completeness node..."),
    "classify_severity_risk": (57, "Running classify_severity_risk node (LLM)..."),
    "detect_duplicate":       (71, "Running detect_duplicate node (SQL)..."),
    "recommend_capa":         (85, "Running recommend_capa node (LLM)..."),
    "generate_summary":       (95, "Running generate_summary node (LLM)..."),
}


def _persist_complaint(result: dict) -> str:
    """Save the pipeline result as a Complaint row in the DB."""
    ef = result.get("extracted_fields", {})
    try:
        db = SessionLocal()
        try:
            row = Complaint(
                complaint_source=ef.get("complaint_source"),
                customer_name=ef.get("customer_name"),
                product_name=ef.get("product_name"),
                product_strength_grade=ef.get("product_strength_grade"),
                batch_lot_number=ef.get("batch_lot_number"),
                manufacturing_date=ef.get("manufacturing_date"),
                expiry_date=ef.get("expiry_date"),
                quantity_affected=ef.get("quantity_affected"),
                complaint_type=ef.get("complaint_type"),
                complaint_date=ef.get("complaint_date"),
                detailed_description=ef.get("detailed_description"),
                initial_severity=result.get("severity"),
                priority=result.get("priority"),
                risk_score=result.get("risk_score"),
                risk_reasoning=result.get("risk_reasoning"),
                completeness_score=result.get("completeness_score"),
                missing_fields=result.get("missing_fields"),
                is_duplicate=result.get("is_duplicate", False),
                duplicate_match_id=result.get("duplicate_match_id"),
                capa_recommendation=result.get("capa_recommendation"),
                ai_summary=result.get("summary"),
            )
            db.add(row)
            db.commit()
            db.refresh(row)
            logger.info(f"Complaint persisted to DB: id={row.id}, batch={row.batch_lot_number}")
            return row.id
        finally:
            db.close()
    except Exception as e:
        logger.error(f"_persist_complaint: DB write failed — {e}")
        return None


@router.post("/extract")
async def extract_complaint(
    request: Request,
    file: Optional[UploadFile] = File(default=None),
    raw_text: Optional[str] = Form(default=None),
    stream: bool = True,
):
    """
    Trigger the 7-node LangGraph extraction pipeline.
    Enforces 10MB file size limit and strict file format / magic-byte validation.
    If stream=True (default), streams SSE node_complete events as nodes execute.
    If stream=False, returns standard JSON.
    """
    raw_input = ""
    input_type = "text"

    if file and file.filename:
        content = await file.read()
        if len(content) > MAX_FILE_SIZE_BYTES:
            size_mb = len(content) / (1024 * 1024)
            raise HTTPException(
                status_code=413,
                detail=f"File '{file.filename}' exceeds maximum allowed size limit of 10MB ({size_mb:.1f}MB uploaded)."
            )

        try:
            raw_input, input_type = parse_document(content, file.filename)
            logger.info(f"extract_complaint: parsed file '{file.filename}' -> {len(raw_input)} chars")
        except ValueError as ve:
            raise HTTPException(status_code=422, detail=str(ve))

    elif raw_text:
        text_bytes = raw_text.encode('utf-8')
        if len(text_bytes) > MAX_FILE_SIZE_BYTES:
            size_mb = len(text_bytes) / (1024 * 1024)
            raise HTTPException(
                status_code=413,
                detail=f"Pasted text exceeds maximum allowed size limit of 10MB ({size_mb:.1f}MB submitted)."
            )
        raw_input = raw_text.strip()
        input_type = "text"
        logger.info(f"extract_complaint: received raw_text ({len(raw_input)} chars)")
    else:
        raise HTTPException(
            status_code=422,
            detail="Provide either a file upload or raw_text form field."
        )

    if not raw_input:
        raise HTTPException(
            status_code=422,
            detail="Could not extract any text from the provided input."
        )

    initial_state = {
        "raw_input": raw_input,
        "input_type": input_type,
        "extracted_fields": {},
        "missing_fields": [],
        "completeness_score": 0.0,
        "severity": "",
        "priority": "",
        "risk_score": 0.0,
        "risk_reasoning": "",
        "is_duplicate": False,
        "duplicate_match_id": None,
        "capa_recommendation": "",
        "summary": "",
        "chat_history": [],
        "errors": [],
    }

    if not stream:
        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None, complaint_pipeline.invoke, initial_state
            )
            saved_id = await asyncio.get_event_loop().run_in_executor(
                None, _persist_complaint, result
            )
            return JSONResponse(content={
                "status": "ok",
                "complaint_id": saved_id,
                "input_type": result.get("input_type"),
                "extracted_fields": result.get("extracted_fields", {}),
                "severity": result.get("severity"),
                "priority": result.get("priority"),
                "risk_score": result.get("risk_score"),
                "risk_reasoning": result.get("risk_reasoning"),
                "completeness_score": result.get("completeness_score"),
                "missing_fields": result.get("missing_fields"),
                "is_duplicate": result.get("is_duplicate"),
                "duplicate_match_id": result.get("duplicate_match_id"),
                "capa_recommendation": result.get("capa_recommendation"),
                "summary": result.get("summary", ""),
                "errors": result.get("errors", []),
            })
        except Exception as e:
            logger.error(f"extract_complaint: pipeline error — {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def sse_event_generator():
        accumulated_state = dict(initial_state)
        logger.info("SSE Stream started for complaint extraction")

        try:
            async for event in complaint_pipeline.astream(initial_state):
                if await request.is_disconnected():
                    logger.info("SSE client disconnected — halting graph stream")
                    break

                for node_name, state_update in event.items():
                    accumulated_state.update(state_update)
                    progress, label = NODE_PROGRESS_MAP.get(
                        node_name, (50, f"Running {node_name}...")
                    )
                    
                    sse_data = {
                        "node": node_name,
                        "status": "complete",
                        "progress": progress,
                        "label": label,
                        "partial_state": state_update
                    }
                    logger.info(f"SSE Emit: {node_name} ({progress}%)")
                    yield f"event: node_complete\ndata: {json.dumps(sse_data)}\n\n"

            saved_id = await asyncio.get_event_loop().run_in_executor(
                None, _persist_complaint, accumulated_state
            )

            final_data = {
                "node": "END",
                "status": "complete",
                "progress": 100,
                "label": "Extraction complete!",
                "complaint_id": saved_id,
                "final_state": {
                    "extracted_fields": accumulated_state.get("extracted_fields", {}),
                    "severity": accumulated_state.get("severity"),
                    "priority": accumulated_state.get("priority"),
                    "risk_score": accumulated_state.get("risk_score"),
                    "risk_reasoning": accumulated_state.get("risk_reasoning"),
                    "completeness_score": accumulated_state.get("completeness_score"),
                    "missing_fields": accumulated_state.get("missing_fields"),
                    "is_duplicate": accumulated_state.get("is_duplicate"),
                    "duplicate_match_id": accumulated_state.get("duplicate_match_id"),
                    "capa_recommendation": accumulated_state.get("capa_recommendation"),
                    "summary": accumulated_state.get("summary", ""),
                }
            }
            yield f"event: complete\ndata: {json.dumps(final_data)}\n\n"

        except Exception as e:
            logger.error(f"SSE generator exception: {e}")
            err_data = {"node": "ERROR", "status": "error", "error": str(e)}
            yield f"event: error\ndata: {json.dumps(err_data)}\n\n"

    return StreamingResponse(
        sse_event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
