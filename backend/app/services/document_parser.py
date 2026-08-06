"""
Document Parser Service
Supports: plain text, PDF (pdfplumber), DOCX (python-docx)
EML support deferred to later step.
"""
import io
from app.core.logging import logger


def parse_text(content: bytes) -> str:
    """Parse plain text bytes."""
    return content.decode("utf-8", errors="ignore")


def parse_pdf(content: bytes) -> str:
    """Parse PDF bytes using pdfplumber. Returns all page text concatenated."""
    try:
        import pdfplumber
        text_parts = []
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        return "\n".join(text_parts)
    except Exception as e:
        logger.error(f"PDF parsing error: {e}")
        return ""


def parse_docx(content: bytes) -> str:
    """Parse DOCX bytes using python-docx. Returns all paragraphs joined."""
    try:
        from docx import Document
        doc = Document(io.BytesIO(content))
        paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
        return "\n".join(paragraphs)
    except Exception as e:
        logger.error(f"DOCX parsing error: {e}")
        return ""


def parse_document(content: bytes, filename: str) -> tuple[str, str]:
    """
    Dispatch to the appropriate parser based on file extension.
    
    Returns:
        (raw_text: str, input_type: str)
        input_type is one of: "pdf" | "docx" | "txt" | "text"
    """
    lower = filename.lower()

    if lower.endswith(".pdf"):
        return parse_pdf(content), "pdf"
    elif lower.endswith(".docx"):
        return parse_docx(content), "docx"
    elif lower.endswith(".txt"):
        return parse_text(content), "txt"
    else:
        # Fallback: treat as plain text
        return parse_text(content), "text"
