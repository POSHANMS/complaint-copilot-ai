"""
LangGraph Node: extract_entities
Model: llama-3.1-8b-instant (fast structured extraction)
Role: Calls Groq with a strict JSON extraction prompt and populates extracted_fields.
Defensive parsing — never crashes the graph. Falls back gracefully on JSON errors.
"""
import json
import re
from app.agent.state import ComplaintState
from app.agent.llm_client import call_groq, MODEL_GEMMA
from app.agent.prompts.extraction_prompt import EXTRACTION_SYSTEM_PROMPT, EXTRACTION_USER_TEMPLATE
from app.core.logging import logger

REQUIRED_FIELDS = [
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


def _extract_json_from_response(text: str) -> dict:
    """
    Try to extract a JSON object from the LLM response.
    Handles cases where the model wraps JSON in markdown code fences.
    """
    # Strip markdown code fences if present
    cleaned = re.sub(r"```(?:json)?\s*", "", text).strip().rstrip("```").strip()
    return json.loads(cleaned)


def extract_entities_node(state: ComplaintState) -> dict:
    raw_input = state.get("raw_input", "")
    errors = list(state.get("errors", []))

    if not raw_input:
        logger.warning("extract_entities_node: raw_input is empty, skipping Groq call.")
        errors.append("extract_entities: raw_input is empty")
        return {"extracted_fields": {f: None for f in REQUIRED_FIELDS}, "errors": errors}

    prompt = EXTRACTION_USER_TEMPLATE.format(raw_input=raw_input)

    try:
        logger.info("extract_entities_node: calling Groq llama-3.1-8b-instant for extraction")
        response_text = call_groq(
            prompt=prompt,
            system_prompt=EXTRACTION_SYSTEM_PROMPT,
            model=MODEL_GEMMA,
            temperature=0.0,
        )
        extracted = _extract_json_from_response(response_text)
        # Ensure all required fields exist (fill missing with None)
        for field in REQUIRED_FIELDS:
            if field not in extracted:
                extracted[field] = None
        logger.info(f"extract_entities_node: extraction successful, fields={list(extracted.keys())}")
        return {"extracted_fields": extracted, "errors": errors}

    except json.JSONDecodeError as e:
        logger.error(f"extract_entities_node: JSON parse error — {e}")
        errors.append(f"extract_entities: JSON parse error: {e}")
        return {
            "extracted_fields": {f: None for f in REQUIRED_FIELDS},
            "errors": errors,
        }
    except Exception as e:
        logger.error(f"extract_entities_node: unexpected error — {e}")
        errors.append(f"extract_entities: unexpected error: {e}")
        return {
            "extracted_fields": {f: None for f in REQUIRED_FIELDS},
            "errors": errors,
        }
