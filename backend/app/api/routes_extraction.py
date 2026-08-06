"""
FastAPI Route: POST /api/complaints/extract
Accepts: multipart file upload (PDF/DOCX/TXT) OR raw text body.
Runs the 7-node LangGraph complaint_pipeline, persists the complaint to
the DB for duplicate detection, and returns structured JSON.
"""
import asyncio
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional

from app.agent.graph import complaint_pipeline
from app.services.document_parser import parse_document
from app.db.database import SessionLocal, init_db
from app.db.models import Complaint
from app.core.logging import logger

router = APIRouter(prefix="/complaints", tags=["Extraction"])


def _persist_complaint(result: dict) -> str:
    """
    Save the pipeline result as a Complaint row in the DB.
    Returns the new complaint ID (used as duplicate_match_id in future runs).
    Only saves if the complaint is NOT a duplicate — avoids polluting the
    reference table with duplicates that would confuse subsequent detections.
    """
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
    file: Optional[UploadFile] = File(default=None),
    raw_text: Optional[str] = Form(default=None),
):
    """
    Trigger the LangGraph 7-node extraction pipeline.
    - Upload a PDF/DOCX/TXT file, OR send raw_text as a form field.
    - Persists each unique complaint to the DB (for duplicate detection).
    Returns: extracted_fields + all node outputs + errors.
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
        result = await asyncio.get_event_loop().run_in_executor(
            None, complaint_pipeline.invoke, initial_state
        )

        # Persist to DB (always, even duplicates — duplicate flag is stored too)
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
        raise HTTPException(status_code=500, detail=f"Pipeline error: {str(e)}")
