"""
Chat node — grounded Q&A over a specific complaint.
Model: llama-3.1-8b-instant (conversational speed)
Injects full complaint state into context for grounded, specific answers.
"""
from app.agent.llm_client import call_groq, MODEL_GEMMA
from app.agent.prompts.chat_prompt import CHAT_SYSTEM_PROMPT_TEMPLATE
from app.core.logging import logger


def _build_system_prompt(complaint) -> str:
    """Build grounded system prompt from the Complaint ORM row."""
    ef_lines = []
    ef_fields = [
        ("Complaint Source",      complaint.complaint_source),
        ("Customer Name",         complaint.customer_name),
        ("Product Name",          complaint.product_name),
        ("Strength / Grade",      complaint.product_strength_grade),
        ("Batch / Lot Number",    complaint.batch_lot_number),
        ("Manufacturing Date",    complaint.manufacturing_date),
        ("Expiry Date",           complaint.expiry_date),
        ("Quantity Affected",     complaint.quantity_affected),
        ("Complaint Type",        complaint.complaint_type),
        ("Complaint Date",        complaint.complaint_date),
        ("Detailed Description",  complaint.detailed_description),
    ]
    for label, val in ef_fields:
        ef_lines.append(f"  {label}: {val or 'N/A'}")

    missing = complaint.missing_fields or []

    return CHAT_SYSTEM_PROMPT_TEMPLATE.format(
        extracted_fields_text="\n".join(ef_lines),
        severity=complaint.initial_severity or "N/A",
        priority=complaint.priority or "N/A",
        risk_score=complaint.risk_score or 0,
        risk_reasoning=complaint.risk_reasoning or "N/A",
        completeness_score=complaint.completeness_score or 0,
        missing_fields=", ".join(missing) if missing else "None — all fields present",
        capa_recommendation=complaint.capa_recommendation or "N/A",
        is_duplicate=complaint.is_duplicate,
        duplicate_match_id=complaint.duplicate_match_id or "N/A",
        ai_summary=complaint.ai_summary or "N/A",
    )


def _build_messages(system_prompt: str, chat_history: list, user_message: str) -> list:
    """Convert DB chat_history + new user message into Groq messages format."""
    messages = [{"role": "system", "content": system_prompt}]
    for m in chat_history:
        messages.append({"role": m.role, "content": m.content})
    messages.append({"role": "user", "content": user_message})
    return messages


def chat_with_complaint(complaint, user_message: str, chat_history: list) -> str:
    """
    Generate a grounded AI response for a user question about a specific complaint.
    complaint: SQLAlchemy Complaint ORM object (fully loaded from DB).
    chat_history: list of prior ChatMessage ORM objects (ordered asc).
    user_message: the current user question string.
    Returns: AI response string.
    """
    system_prompt = _build_system_prompt(complaint)
    messages = _build_messages(system_prompt, chat_history, user_message)

    try:
        logger.info(f"chat_with_complaint: sending to Groq with {len(messages)} messages in context")
        # Direct multi-turn call using messages array
        from groq import Groq
        from app.core.config import settings

        client = Groq(api_key=settings.GROQ_API_KEY)
        response = client.chat.completions.create(
            model=MODEL_GEMMA,
            messages=messages,
            temperature=0.3,
            max_tokens=500,
        )
        reply = response.choices[0].message.content.strip()
        logger.info(f"chat_with_complaint: got response ({len(reply)} chars)")
        return reply

    except Exception as e:
        logger.error(f"chat_with_complaint: error — {e}")
        return "I encountered an error while processing your question. Please try again."
