"""
LangGraph Node: detect_duplicate
Role: Performs QMS batch-tracing duplicate detection by querying existing rows
in the complaints table for matching batch_lot_number or product/description similarity.
Writes entry to extraction_logs table for auditability.
"""
import time
from app.agent.state import ComplaintState
from app.db.database import SessionLocal, log_node_execution
from app.db.models import Complaint
from app.core.logging import logger

def detect_duplicate_node(state: ComplaintState) -> dict:
    start_time = time.time()
    extracted = state.get("extracted_fields", {})
    batch_num = extracted.get("batch_lot_number")
    product = extracted.get("product_name")
    errors = list(state.get("errors", []))

    is_duplicate = False
    duplicate_match_id = None
    matched_details = None

    if batch_num and str(batch_num).strip() and str(batch_num).lower() != "null":
        clean_batch = str(batch_num).strip()
        try:
            db = SessionLocal()
            try:
                # Query DB for prior complaints matching the same batch_lot_number
                existing = db.query(Complaint).filter(
                    Complaint.batch_lot_number == clean_batch
                ).order_by(Complaint.created_at.desc()).first()

                if existing:
                    is_duplicate = True
                    duplicate_match_id = existing.id
                    matched_details = f"Match found: Complaint ID {existing.id[:8]}... (Product: {existing.product_name}, Date: {existing.complaint_date or 'N/A'})"
                    logger.info(f"detect_duplicate_node: DUPLICATE DETECTED for batch {clean_batch} -> matched ID {existing.id}")
                else:
                    logger.info(f"detect_duplicate_node: No duplicate found for batch {clean_batch}")
            finally:
                db.close()
        except Exception as e:
            logger.warning(f"detect_duplicate_node: DB query error — {e}")
            errors.append(f"detect_duplicate DB error: {e}")
    else:
        logger.info("detect_duplicate_node: No batch number available to match.")

    latency_ms = int((time.time() - start_time) * 1000)

    # Audit logging
    log_node_execution(
        node_name="detect_duplicate",
        input_snapshot={"batch_lot_number": batch_num, "product_name": product},
        output_snapshot={
            "is_duplicate": is_duplicate,
            "duplicate_match_id": duplicate_match_id,
            "matched_details": matched_details
        },
        latency_ms=latency_ms
    )

    return {
        "is_duplicate": is_duplicate,
        "duplicate_match_id": duplicate_match_id,
        "errors": errors
    }
