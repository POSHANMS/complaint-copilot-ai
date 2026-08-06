"""
Smoke tests for the 3-node LangGraph complaint pipeline.
Tests both .txt and .pdf input paths.
Run with: pytest backend/tests/test_graph.py -v
"""
import os
import sys
import pytest

# Ensure backend app is importable from tests directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.agent.graph import complaint_pipeline
from app.services.document_parser import parse_document

SAMPLE_DIR = os.path.join(os.path.dirname(__file__), "..", "sample_complaints")
TXT_FILE = os.path.join(SAMPLE_DIR, "sample_pharma_complaint.txt")
PDF_FILE = os.path.join(SAMPLE_DIR, "sample_pharma_complaint.pdf")


def make_initial_state(raw_input: str, input_type: str) -> dict:
    return {
        "raw_input": raw_input,
        "input_type": input_type,
        "extracted_fields": {},
        "missing_fields": [],
        "completeness_score": 0.0,
        "severity": "",
        "priority": "",
        "risk_score": 0.0,
        "risk_reasoning": "",
        "is_duplicate": False,
        "duplicate_match_id": None,
        "capa_recommendation": "",
        "summary": "",
        "chat_history": [],
        "errors": [],
    }


class TestGraphSmokeTxt:
    """Test the 3-node pipeline using plain text input."""

    def test_txt_file_exists(self):
        assert os.path.exists(TXT_FILE), f"Sample TXT not found at {TXT_FILE}"

    def test_txt_parser(self):
        with open(TXT_FILE, "rb") as f:
            content = f.read()
        text, input_type = parse_document(content, "sample_pharma_complaint.txt")
        assert input_type == "txt"
        assert len(text) > 100
        assert "Atorvastatin" in text

    def test_pipeline_txt_end_to_end(self):
        """Run the full 3-node graph on a TXT complaint. Verify fields and summary."""
        with open(TXT_FILE, "rb") as f:
            content = f.read()
        text, input_type = parse_document(content, "sample_pharma_complaint.txt")
        state = make_initial_state(text, input_type)
        result = complaint_pipeline.invoke(state)

        # Graph should complete without crashing
        assert result is not None

        # No unexpected fatal errors
        assert "extract_entities: unexpected error" not in str(result.get("errors", []))

        # extracted_fields should be a dict
        fields = result.get("extracted_fields", {})
        assert isinstance(fields, dict)

        # Key fields we expect to be extracted from the sample complaint
        assert fields.get("product_name") is not None, "product_name should be extracted"
        assert fields.get("batch_lot_number") is not None, "batch_lot_number should be extracted"

        # Summary should be a non-empty string
        summary = result.get("summary", "")
        assert isinstance(summary, str)
        assert len(summary) > 20, "Summary should be at least 20 characters"

        print(f"\n[TXT TEST] Extracted fields: {fields}")
        print(f"[TXT TEST] Summary: {summary}")


class TestGraphSmokePdf:
    """Test the 3-node pipeline using PDF input (exercises pdfplumber path)."""

    def test_pdf_file_exists(self):
        assert os.path.exists(PDF_FILE), f"Sample PDF not found at {PDF_FILE}"

    def test_pdf_parser(self):
        with open(PDF_FILE, "rb") as f:
            content = f.read()
        text, input_type = parse_document(content, "sample_pharma_complaint.pdf")
        assert input_type == "pdf"
        assert len(text) > 50
        assert "Atorvastatin" in text

    def test_pipeline_pdf_end_to_end(self):
        """Run the full 3-node graph on a PDF complaint."""
        with open(PDF_FILE, "rb") as f:
            content = f.read()
        text, input_type = parse_document(content, "sample_pharma_complaint.pdf")
        state = make_initial_state(text, input_type)
        result = complaint_pipeline.invoke(state)

        assert result is not None
        fields = result.get("extracted_fields", {})
        assert isinstance(fields, dict)
        assert fields.get("product_name") is not None, "product_name should be extracted from PDF"
        summary = result.get("summary", "")
        assert len(summary) > 20

        print(f"\n[PDF TEST] Extracted fields: {fields}")
        print(f"[PDF TEST] Summary: {summary}")
