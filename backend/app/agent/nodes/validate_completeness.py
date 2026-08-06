"""
LangGraph Node: validate_completeness
Model: llama-3.1-8b-instant
Role: Hybrid completeness validator combining rule-based missing field detection
and LLM field confidence evaluation. Calculates completeness_score (0-100%)
and lists missing_fields.
Writes entry to extraction_logs table for auditability.
"""
import json
import re
import time
from app.agent.state import ComplaintState
from app.agent.llm_client import call_groq, MODEL_GEMMA
from app.db.database import log_node_execution
from app.core.logging import logger

REQUIRED_FIELDS_SCHEMA = [
    "complaint_source",
    "customer_name",
    "product_name",
    "product_strength_grade",
    "batch_lot_number",
    "manufacturing_date",
    "expiry_date",
    "quantity_affected",
    "complaint_type",
    "complaint_date",
    "detailed_description",
]

COMPLETENESS_SYSTEM_PROMPT = """You are a Pharma QMS Data Quality Specialist.
Evaluate the extracted complaint fields for completeness and validity.

Return ONLY a strict JSON object:
{
  "completeness_score": float between 0.0 and 100.0,
  "missing_fields": ["list", "of", "missing_or_invalid_field_names"]
}

Rules:
- Give full points for valid, populated fields.
- Deduct points for null, missing, ambiguous, or placeholder values.
- Return ONLY the JSON object."""

def validate_completeness_node(state: ComplaintState) -> dict:
    start_time = time.time()
    extracted = state.get("extracted_fields", {})
    errors = list(state.get("errors", []))

    # 1. Rule-based check
    rule_missing = []
    total_fields = len(REQUIRED_FIELDS_SCHEMA)
    filled_count = 0

    for field in REQUIRED_FIELDS_SCHEMA:
        val = extracted.get(field)
        if val is None or str(val).strip() == "" or str(val).lower() == "null":
            rule_missing.append(field)
        else:
            filled_count += 1

    rule_score = round((filled_count / total_fields) * 100.0, 1)

    # 2. LLM sanity check if there are fields to evaluate
    try:
        fields_text = json.dumps(extracted, indent=2)
        prompt = f"Evaluate completeness of these extracted complaint fields:\n{fields_text}\nRule-detected missing fields: {rule_missing}"

        response_text = call_groq(
            prompt=prompt,
            system_prompt=COMPLETENESS_SYSTEM_PROMPT,
            model=MODEL_GEMMA,
            temperature=0.0
        )

        cleaned = re.sub(r"```(?:json)?\s*", "", response_text).strip().rstrip("```").strip()
        parsed = json.loads(cleaned)

        llm_score = float(parsed.get("completeness_score", rule_score))
        llm_missing = parsed.get("missing_fields", rule_missing)

        # Merge rule-based & LLM lists (unique entries)
        missing_fields = list(dict.fromkeys(rule_missing + llm_missing))
        completeness_score = round((rule_score * 0.6) + (llm_score * 0.4), 1) if missing_fields else 100.0

    except Exception as e:
        logger.warning(f"validate_completeness_node: LLM evaluation fallback to rule check — {e}")
        missing_fields = rule_missing
        completeness_score = rule_score

    latency_ms = int((time.time() - start_time) * 1000)

    # Audit logging
    log_node_execution(
        node_name="validate_completeness",
        input_snapshot={"extracted_fields": extracted},
        output_snapshot={
            "completeness_score": completeness_score,
            "missing_fields": missing_fields
        },
        latency_ms=latency_ms
    )

    logger.info(f"validate_completeness_node: score={completeness_score}%, missing={missing_fields}")
    return {
        "completeness_score": completeness_score,
        "missing_fields": missing_fields,
        "errors": errors
    }
