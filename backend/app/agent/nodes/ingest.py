"""
LangGraph Node: ingest_document
Role: Parse uploaded file or raw text into raw_input string and set input_type.
No AI call — pure parsing. State update pattern: returns partial dict.
"""
from app.agent.state import ComplaintState
from app.services.document_parser import parse_document
from app.core.logging import logger


def ingest_document_node(state: ComplaintState) -> dict:
    """
    If state already has raw_input (text was pasted directly), just set input_type.
    If raw_input is empty, this node expects the caller to have pre-populated it
    via the API route (file bytes parsed before graph.invoke).
    """
    raw = state.get("raw_input", "").strip()
    input_type = state.get("input_type", "text")

    if not raw:
        logger.warning("ingest_document_node: raw_input is empty — no document content to process.")
        return {
            "raw_input": "",
            "input_type": input_type,
            "errors": state.get("errors", []) + ["ingest_document: raw_input is empty"],
        }

    logger.info(f"ingest_document_node: received input_type={input_type}, length={len(raw)} chars")
    return {
        "raw_input": raw,
        "input_type": input_type,
    }
