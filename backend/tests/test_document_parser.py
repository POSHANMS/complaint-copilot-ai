"""
Unit tests for document_parser.py service.
Tests extension whitelist, magic byte validation, and structure error handling.
No live API calls. No LLM mocking needed.

Run: pytest backend/tests/test_document_parser.py -v
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.document_parser import parse_document, parse_text, parse_pdf, parse_docx  # noqa


class TestExtensionWhitelist:
    """Tests for file extension enforcement."""

    def test_jpg_extension_rejected(self):
        with pytest.raises(ValueError, match="Unsupported file format '.jpg'"):
            parse_document(b"\xff\xd8\xff\xe0", "photo.jpg")

    def test_zip_extension_rejected(self):
        with pytest.raises(ValueError, match="Unsupported file format '.zip'"):
            parse_document(b"PK\x03\x04", "archive.zip")

    def test_png_extension_rejected(self):
        with pytest.raises(ValueError, match="Unsupported file format '.png'"):
            parse_document(b"\x89PNG", "image.png")

    def test_exe_extension_rejected(self):
        with pytest.raises(ValueError, match="Unsupported file format '.exe'"):
            parse_document(b"MZ", "malware.exe")

    def test_no_extension_rejected(self):
        with pytest.raises(ValueError, match="Unsupported file format"):
            parse_document(b"some data", "noextension")

    def test_pdf_extension_accepted(self):
        """Valid PDF extension and magic bytes -> accepted (may fail at structure level)."""
        content = b"%PDF-1.4 some content"
        # Will fail at structure parsing but must not fail at extension check
        with pytest.raises(ValueError, match=r"(PDF|page)"):  # structure error, not extension error
            parse_document(content, "empty.pdf")

    def test_txt_extension_accepted(self):
        """Valid TXT content -> accepted."""
        text, input_type = parse_document(b"Hello complaint text.", "complaint.txt")
        assert input_type == "txt"
        assert "Hello" in text

    def test_uppercase_extension_handled(self):
        """Uppercase .PDF should be treated as .pdf (case-insensitive)."""
        # Should not raise "unsupported format" for .PDF — it's recognized
        try:
            parse_document(b"%PDF-1.4", "COMPLAINT.PDF")
        except ValueError as e:
            assert "Unsupported file format" not in str(e), (
                f"Uppercase .PDF extension should be recognized, got: {e}"
            )


class TestMagicByteValidation:
    """Tests for file magic byte (content signature) verification."""

    def test_fake_pdf_no_magic_rejected(self):
        """File with .pdf extension but no %PDF header -> ValueError."""
        with pytest.raises(ValueError, match="magic header"):
            parse_document(b"This is just text content not a PDF", "fake.pdf")

    def test_fake_pdf_jpg_bytes_rejected(self):
        """JPEG bytes with .pdf extension -> rejected for missing %PDF magic."""
        with pytest.raises(ValueError, match="magic header"):
            parse_document(b"\xff\xd8\xff\xe0JFIF", "photo.pdf")

    def test_fake_docx_no_magic_rejected(self):
        """File with .docx extension but no PK magic -> ValueError."""
        with pytest.raises(ValueError, match="magic header"):
            parse_document(b"This is just text not a DOCX", "fake.docx")

    def test_binary_txt_rejected(self):
        """File with NUL bytes uploaded as .txt -> rejected as binary data."""
        with pytest.raises(ValueError, match="binary"):
            parse_document(b"\x00\x01\x02\x03 binary data", "binary.txt")


class TestPlainTextParsing:
    """Tests for parse_text() function directly."""

    def test_valid_utf8_text_parsed(self):
        text = parse_text(b"Complaint about Atorvastatin packaging defect.")
        assert "Atorvastatin" in text

    def test_valid_latin1_text_parsed(self):
        """Latin-1 encoded content (non-UTF-8) should fall back gracefully."""
        latin1_bytes = "Complément thérapeutique.".encode("latin-1")
        result = parse_text(latin1_bytes)
        assert len(result) > 5

    def test_empty_text_rejected(self):
        """Empty file -> ValueError about whitespace."""
        with pytest.raises(ValueError, match="empty"):
            parse_text(b"")

    def test_whitespace_only_rejected(self):
        """Whitespace-only file -> ValueError."""
        with pytest.raises(ValueError, match="empty"):
            parse_text(b"   \n   \t   ")

    def test_binary_null_bytes_rejected(self):
        """Content with NUL bytes -> rejected as binary."""
        with pytest.raises(ValueError, match="binary"):
            parse_text(b"\x00\x01\x02 not text")


class TestDocumentParserReturnType:
    """Tests that parse_document returns correct (text, input_type) tuples."""

    def test_txt_returns_correct_input_type(self):
        text, input_type = parse_document(b"Complaint text content here.", "complaint.txt")
        assert input_type == "txt"
        assert isinstance(text, str)

    def test_real_pdf_returns_pdf_input_type(self):
        """Real PDF sample file should parse correctly."""
        sample_dir = os.path.join(os.path.dirname(__file__), "..", "sample_complaints")
        pdf_path = os.path.join(sample_dir, "sample_pharma_complaint.pdf")
        if not os.path.exists(pdf_path):
            pytest.skip("sample_pharma_complaint.pdf not found")
        with open(pdf_path, "rb") as f:
            content = f.read()
        text, input_type = parse_document(content, "sample_pharma_complaint.pdf")
        assert input_type == "pdf"
        assert "Atorvastatin" in text

    def test_real_txt_returns_txt_input_type(self):
        """Real TXT sample file should parse correctly."""
        sample_dir = os.path.join(os.path.dirname(__file__), "..", "sample_complaints")
        txt_path = os.path.join(sample_dir, "sample_pharma_complaint.txt")
        if not os.path.exists(txt_path):
            pytest.skip("sample_pharma_complaint.txt not found")
        with open(txt_path, "rb") as f:
            content = f.read()
        text, input_type = parse_document(content, "sample_pharma_complaint.txt")
        assert input_type == "txt"
        assert "Atorvastatin" in text
