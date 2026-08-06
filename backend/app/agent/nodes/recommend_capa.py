"""
LangGraph Node: recommend_capa
Model: llama-3.3-70b-versatile (heavy reasoning model)
Role: Generates draft CAPA (Corrective and Preventive Action) recommendation
using the 5M Root Cause Framework (Material, Method, Machine, Man, Environment).
Writes entry to extraction_logs table for auditability.
"""
import json
import re
import time
from app.agent.state import ComplaintState
from app.agent.llm_client import call_groq, MODEL_LLAMA_HEAVY
from app.agent.prompts.capa_prompt import CAPA_SYSTEM_PROMPT, CAPA_USER_TEMPLATE
from app.db.database import log_node_execution
from app.core.logging import logger

def _clean_json_response(text: str) -> dict:
    cleaned = re.sub(r"```(?:json)?\s*", "", text).strip().rstrip("```").strip()
    return json.loads(cleaned)

def recommend_capa_node(state: ComplaintState) -> dict:
    start_time = time.time()
    extracted = state.get("extracted_fields", {})
    complaint_type = extracted.get("complaint_type", "Quality Defect")
    severity = state.get("severity", "Major")
    desc = extracted.get("detailed_description") or state.get("raw_input", "")
    errors = list(state.get("errors", []))

    extracted_text = "\n".join(
        f"  {k}: {v}" for k, v in extracted.items() if v is not None
    ) or "  (No fields available)"

    prompt = CAPA_USER_TEMPLATE.format(
        complaint_type=complaint_type,
        severity=severity,
        extracted_text=extracted_text,
        detailed_description=desc
    )

    try:
        logger.info("recommend_capa_node: calling Groq llama-3.3-70b-versatile for 5M CAPA recommendation")
        response_text = call_groq(
            prompt=prompt,
            system_prompt=CAPA_SYSTEM_PROMPT,
            model=MODEL_LLAMA_HEAVY,
            temperature=0.1
        )
        parsed = _clean_json_response(response_text)

        category = parsed.get("root_cause_category", "Material")
        capa_text = parsed.get("capa_recommendation", "")

        # Format complete recommendation string with 5M Category Tag
        full_recommendation = f"[{category}] {capa_text}"

        latency_ms = int((time.time() - start_time) * 1000)

        # Audit logging
        log_node_execution(
            node_name="recommend_capa",
            input_snapshot={"complaint_type": complaint_type, "severity": severity},
            output_snapshot={
                "root_cause_category": category,
                "capa_recommendation": full_recommendation
            },
            latency_ms=latency_ms
        )

        logger.info(f"recommend_capa_node: 5M category={category}")
        return {
            "capa_recommendation": full_recommendation,
            "errors": errors
        }

    except Exception as e:
        logger.error(f"recommend_capa_node: error — {e}")
        errors.append(f"recommend_capa error: {e}")
        # Rule-based fallback
        fallback = f"[Material] Immediate containment: Quarantine batch {extracted.get('batch_lot_number', 'retained')} and issue distribution hold. Initiate root-cause investigation into blister sealing foil integrity and humidity exposure. Re-validate packaging line sealing parameters."
        return {
            "capa_recommendation": fallback,
            "errors": errors
        }
