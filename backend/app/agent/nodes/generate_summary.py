"""
LangGraph Node: generate_summary
Model: llama-3.1-8b-instant
Role: Generates a 2-3 sentence executive summary of the extracted complaint
for display in the AI Copilot panel.
"""
from app.agent.state import ComplaintState
from app.agent.llm_client import call_groq, MODEL_GEMMA
from app.core.logging import logger

SUMMARY_SYSTEM_PROMPT = """You are a Pharmaceutical Quality Management System (QMS) AI assistant.
Write a concise 2-3 sentence executive summary of the complaint for a Quality Manager.
Be factual, clinical, and professional. Reference the product, batch number, complaint type,
and severity if available. Do NOT include recommendations — just summarize the complaint."""


def generate_summary_node(state: ComplaintState) -> dict:
    extracted = state.get("extracted_fields", {})
    raw_input = state.get("raw_input", "")
    errors = list(state.get("errors", []))

    # Build context for the summary prompt
    fields_text = "\n".join(
        f"  {k}: {v}" for k, v in extracted.items() if v is not None
    ) or "  (no fields extracted)"

    prompt = f"""Summarize the following pharmaceutical complaint for a Quality Manager.

Extracted Fields:
{fields_text}

Original Document Text:
{raw_input[:1500]}

Write a 2-3 sentence executive summary:"""

    try:
        logger.info("generate_summary_node: calling Groq llama-3.1-8b-instant for summary")
        summary = call_groq(
            prompt=prompt,
            system_prompt=SUMMARY_SYSTEM_PROMPT,
            model=MODEL_GEMMA,
            temperature=0.2,
        )
        summary = summary.strip()
        logger.info(f"generate_summary_node: summary generated ({len(summary)} chars)")
        return {"summary": summary, "errors": errors}

    except Exception as e:
        logger.error(f"generate_summary_node: error — {e}")
        errors.append(f"generate_summary: error: {e}")
        return {
            "summary": "Summary generation failed.",
            "errors": errors,
        }
