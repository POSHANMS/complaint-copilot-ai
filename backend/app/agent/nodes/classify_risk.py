"""
LangGraph Node: classify_severity_risk
Model: llama-3.3-70b-versatile (heavy reasoning model)
Role: Assesses complaint severity (Critical/Major/Minor), priority (High/Medium/Low),
risk_score (0-100), and provides a 2-3 sentence specific risk reasoning.
Writes entry to extraction_logs table for auditability.
"""
import json
import re
import time
from app.agent.state import ComplaintState
from app.agent.llm_client import call_groq, MODEL_LLAMA_HEAVY
from app.agent.prompts.risk_prompt import RISK_SYSTEM_PROMPT, RISK_USER_TEMPLATE
from app.db.database import log_node_execution
from app.core.logging import logger

def _clean_json_response(text: str) -> dict:
    cleaned = re.sub(r"```(?:json)?\s*", "", text).strip().rstrip("```").strip()
    return json.loads(cleaned)

def classify_risk_node(state: ComplaintState) -> dict:
    start_time = time.time()
    extracted = state.get("extracted_fields", {})
    desc = extracted.get("detailed_description") or state.get("raw_input", "")
    errors = list(state.get("errors", []))

    extracted_fields_text = "\n".join(
        f"  {k}: {v}" for k, v in extracted.items() if v is not None
    ) or "  (No fields available)"

    prompt = RISK_USER_TEMPLATE.format(
        extracted_fields_text=extracted_fields_text,
        detailed_description=desc
    )

    try:
        logger.info("classify_risk_node: calling Groq llama-3.3-70b-versatile for risk assessment")
        response_text = call_groq(
            prompt=prompt,
            system_prompt=RISK_SYSTEM_PROMPT,
            model=MODEL_LLAMA_HEAVY,
            temperature=0.1
        )
        parsed = _clean_json_response(response_text)

        severity = parsed.get("severity", "Major")
        priority = parsed.get("priority", "Medium")
        risk_score = float(parsed.get("risk_score", 65.0))
        risk_reasoning = parsed.get("risk_reasoning", "Risk classification based on reported complaint details.")

        latency_ms = int((time.time() - start_time) * 1000)
        output_snap = {
            "severity": severity,
            "priority": priority,
            "risk_score": risk_score,
            "risk_reasoning": risk_reasoning
        }

        # Audit logging
        log_node_execution(
            node_name="classify_severity_risk",
            input_snapshot={"extracted_fields": extracted, "description": desc[:300]},
            output_snapshot=output_snap,
            latency_ms=latency_ms
        )

        logger.info(f"classify_risk_node: severity={severity}, priority={priority}, score={risk_score}")
        return {
            "severity": severity,
            "priority": priority,
            "risk_score": risk_score,
            "risk_reasoning": risk_reasoning,
            "errors": errors
        }

    except Exception as e:
        logger.error(f"classify_risk_node: error — {e}")
        errors.append(f"classify_severity_risk error: {e}")
        # Rule-based fallback if LLM call fails
        desc_lower = desc.lower()
        if "discomfort" in desc_lower or "adverse" in desc_lower or "hospital" in desc_lower:
            fallback_sev = "Critical"
            fallback_prio = "High"
            fallback_score = 85.0
            fallback_reason = "Critical severity assigned due to reported patient adverse health reaction and seal integrity failure."
        else:
            fallback_sev = "Major"
            fallback_prio = "Medium"
            fallback_score = 65.0
            fallback_reason = "Major quality defect reported affecting product packaging and presentation."

        return {
            "severity": fallback_sev,
            "priority": fallback_prio,
            "risk_score": fallback_score,
            "risk_reasoning": fallback_reason,
            "errors": errors
        }
