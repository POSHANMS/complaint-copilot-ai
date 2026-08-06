"""
Document Parser Service
Supports: PDF (pdfplumber), DOCX (python-docx), plain text (.txt)
Strictly validates file extension, magic bytes, and structure.
"""
import io
from app.core.logging import logger

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}


def parse_text(content: bytes) -> str:
    """Parse plain text bytes. Fails if content contains binary NUL bytes."""
    if b"\x00" in content[:1024]:
        raise ValueError("File contains binary data and is not valid plain text.")
    try:
        decoded = content.decode("utf-8")
    except UnicodeDecodeError:
        try:
            decoded = content.decode("latin-1")
        except Exception as e:
            raise ValueError(f"Could not decode text file: {e}")
    
    if not decoded.strip():
        raise ValueError("Text file is empty or contains only whitespace.")
    return decoded


def parse_pdf(content: bytes) -> str:
    """Parse PDF bytes using pdfplumber. Enforces %PDF magic bytes signature."""
    if not content.startswith(b"%PDF"):
        raise ValueError("File extension is .pdf but content lacks %PDF magic header (invalid or fake PDF).")

    try:
        import pdfplumber
        text_parts = []
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            if not pdf.pages:
                raise ValueError("PDF document contains no pages.")
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        result = "\n".join(text_parts).strip()
        if not result:
            raise ValueError("PDF opened successfully but contained no extractable text.")
        return result
    except ValueError:
        raise
    except Exception as e:
        logger.error(f"PDF parsing error: {e}")
        raise ValueError(f"Failed to parse PDF document structure. File may be corrupted or invalid ({e}).")


def parse_docx(content: bytes) -> str:
    """Parse DOCX bytes using python-docx. Enforces PK zip magic bytes signature."""
    if not content.startswith(b"PK\x03\x04"):
        raise ValueError("File extension is .docx but content lacks PK zip magic header (invalid or fake DOCX).")

    try:
        from docx import Document
        doc = Document(io.BytesIO(content))
        paragraphs = [para.text.strip() for para in doc.paragraphs if para.text.strip()]
        result = "\n".join(paragraphs).strip()
        if not result:
            raise ValueError("DOCX opened successfully but contained no extractable text.")
        return result
    except ValueError:
        raise
    except Exception as e:
        logger.error(f"DOCX parsing error: {e}")
        raise ValueError(f"Failed to parse DOCX document structure. File may be corrupted or invalid ({e}).")


def parse_document(content: bytes, filename: str) -> tuple[str, str]:
    """
    Validate file extension and magic bytes, then parse.
    Returns: (raw_text: str, input_type: str)
    Raises: ValueError on unsupported format, magic byte mismatch, or parse failure.
    """
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"Unsupported file format '{ext}'. Allowed formats are: .pdf, .docx, .txt")

    if ext == ".pdf":
        return parse_pdf(content), "pdf"
    elif ext == ".docx":
        return parse_docx(content), "docx"
    elif ext == ".txt":
        return parse_text(content), "txt"
    else:
        raise ValueError(f"Unsupported file format '{ext}'.")
