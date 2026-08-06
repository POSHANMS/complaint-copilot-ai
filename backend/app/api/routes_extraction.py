"""
FastAPI Route: POST /api/complaints/extract
Accepts: multipart file upload (PDF/DOCX/TXT) OR raw text body.
Runs the 3-node LangGraph complaint_pipeline and returns structured JSON.
"""
import asyncio
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional

from app.agent.graph import complaint_pipeline
from app.services.document_parser import parse_document
from app.core.logging import logger

router = APIRouter(prefix="/complaints", tags=["Extraction"])


@router.post("/extract")
async def extract_complaint(
    file: Optional[UploadFile] = File(default=None),
    raw_text: Optional[str] = Form(default=None),
):
    """
    Trigger the LangGraph extraction pipeline.
    - Upload a PDF/DOCX/TXT file, OR
    - Send raw_text as a form field.
    Returns: extracted_fields + summary + errors.
    """
    raw_input = ""
    input_type = "text"

    if file and file.filename:
        content = await file.read()
        raw_input, input_type = parse_document(content, file.filename)
        logger.info(f"extract_complaint: parsed file '{file.filename}' -> {len(raw_input)} chars")
    elif raw_text:
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

    # Initial state for the graph
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

    try:
        logger.info("extract_complaint: invoking LangGraph complaint_pipeline")
        # LangGraph sync invoke — run in thread pool to avoid blocking event loop
        result = await asyncio.get_event_loop().run_in_executor(
            None, complaint_pipeline.invoke, initial_state
        )
        return JSONResponse(content={
            "status": "ok",
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
        raise HTTPException(status_code=500, detail=f"Pipeline error: {str(e)}")
