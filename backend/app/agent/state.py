from typing import TypedDict, List, Dict, Optional, Any

class ComplaintState(TypedDict):
    raw_input: str                 # extracted text from PDF/DOCX/TXT/EML or pasted text
    input_type: str                # "pdf" | "docx" | "txt" | "eml" | "text"
    extracted_fields: Dict[str, Any] # all form fields
    missing_fields: List[str]
    completeness_score: float
    severity: str                  # Critical / Major / Minor
    priority: str                  # High / Medium / Low
    risk_score: float
    risk_reasoning: str
    is_duplicate: bool
    duplicate_match_id: Optional[str]
    capa_recommendation: str
    summary: str
    chat_history: List[Dict[str, str]]
    errors: List[str]
