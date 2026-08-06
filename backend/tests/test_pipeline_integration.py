"""
Integration tests for the full LangGraph complaint pipeline.
Uses mocked Groq for CI-safe runs. One live_api test for manual sanity checks.

Run (mocked):  pytest backend/tests/test_pipeline_integration.py -v -k "not live_api"
Run (live):    pytest backend/tests/test_pipeline_integration.py -v -m live_api
"""
import json
import os
import sys
from unittest.mock import patch, MagicMock

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from conftest import make_state, FULL_EXTRACTED_FIELDS, SAMPLE_DIR  # noqa

# ── Canned LLM responses ────────────────────────────────────────────────────
MOCK_EXTRACTION = json.dumps({
    "complaint_source": "Retail Pharmacy — MedStore Plus",
    "customer_name": "MedStore Plus, Bengaluru",
    "product_name": "Atorvastatin 40mg Tablets",
    "product_strength_grade": "40mg",
    "batch_lot_number": "TEST-BATCH-001",
    "manufacturing_date": "2024-01-15",
    "expiry_date": "2026-01-14",
    "quantity_affected": "48 blister packs",
    "complaint_type": "Packaging Defect",
    "complaint_date": "2024-06-15",
    "detailed_description": (
        "Tablets found with broken seal integrity in multiple packs. "
        "No hospitalization occurred."
    ),
})
MOCK_COMPLETENESS = json.dumps({"completeness_score": 100.0, "missing_fields": []})
MOCK_RISK = json.dumps({
    "severity": "Critical",
    "priority": "High",
    "risk_score": 90.0,
    "risk_reasoning": "Seal integrity failure with confirmed patient adverse reaction.",
})
MOCK_CAPA = json.dumps({
    "root_cause_category": "Machine",
    "capa_recommendation": (
        "Immediate containment: quarantine batch. "
        "Inspect and recalibrate blister sealing machine."
    ),
})
MOCK_SUMMARY = (
    "A Critical packaging defect complaint for Atorvastatin 40mg batch TEST-BATCH-001 "
    "was filed by MedStore Plus, reporting seal integrity failure in multiple packs."
)


class TestPipelineIntegrationMocked:
    """Full 7-node pipeline integration with canned Groq responses. CI-safe."""

    def test_full_pipeline_all_fields_populated(self):
        """Full mocked pipeline run -> all output fields correctly populated."""
        from app.agent.graph import complaint_pipeline

        with patch("app.agent.nodes.extract_entities.call_groq", return_value=MOCK_EXTRACTION), \
             patch("app.agent.nodes.validate_completeness.call_groq", return_value=MOCK_COMPLETENESS), \
             patch("app.agent.nodes.classify_risk.call_groq", return_value=MOCK_RISK), \
             patch("app.agent.nodes.recommend_capa.call_groq", return_value=MOCK_CAPA), \
             patch("app.agent.nodes.generate_summary.call_groq", return_value=MOCK_SUMMARY), \
             patch("app.agent.nodes.detect_duplicate.detect_duplicate_node", return_value={"is_duplicate": False, "duplicate_match_id": None, "errors": []}), \
             patch("app.db.database.log_node_execution"):

            state = make_state(
                raw_input="Atorvastatin packaging defect complaint.",
                input_type="txt",
            )
            result = complaint_pipeline.invoke(state)

        # Extracted fields
        assert result["extracted_fields"]["batch_lot_number"] == "TEST-BATCH-001"
        assert result["extracted_fields"]["product_name"] == "Atorvastatin 40mg Tablets"

        # Risk classification
        assert result["severity"] == "Critical"
        assert result["priority"] == "High"
        assert result["risk_score"] == 90.0

        # Completeness
        assert result["completeness_score"] == 100.0
        assert result["missing_fields"] == []

        # Duplicate detection (none found)
        assert result["is_duplicate"] is False
        assert result["duplicate_match_id"] is None

        # CAPA
        assert result["capa_recommendation"].startswith("[Machine]")

        # Summary
        assert len(result["summary"]) > 20

        # No unexpected errors
        assert result["errors"] == []

    def test_pipeline_gracefully_handles_groq_failure_midway(self):
        """All Groq calls raise exceptions -> pipeline completes with errors, no unhandled exception."""
        from app.agent.graph import complaint_pipeline

        err = Exception("Groq API is down")
        with patch("app.agent.nodes.extract_entities.call_groq", side_effect=err), \
             patch("app.agent.nodes.validate_completeness.call_groq", side_effect=err), \
             patch("app.agent.nodes.classify_risk.call_groq", side_effect=err), \
             patch("app.agent.nodes.recommend_capa.call_groq", side_effect=err), \
             patch("app.agent.nodes.generate_summary.call_groq", side_effect=err), \
             patch("app.agent.nodes.detect_duplicate.detect_duplicate_node", return_value={"is_duplicate": False, "duplicate_match_id": None, "errors": []}), \
             patch("app.db.database.log_node_execution"):

            state = make_state(raw_input="Complaint about Atorvastatin seal failure.")
            result = complaint_pipeline.invoke(state)  # must NOT raise

        assert isinstance(result, dict)
        # At least one error should be recorded
        assert len(result["errors"]) > 0
        # Node results should still be dicts/valid types (fallbacks applied)
        assert isinstance(result["extracted_fields"], dict)
        assert result["severity"] in ["Critical", "Major", "Minor"]

    def test_pipeline_detects_duplicate_when_seeded(self):
        """When DB has an existing complaint with same batch -> is_duplicate=True, correct root ID linked."""
        from app.agent.graph import complaint_pipeline
        from app.db.database import SessionLocal
        from app.db.models import Complaint

        db = SessionLocal()
        try:
            root_complaint = Complaint(
                complaint_source="Pharmacy",
                product_name="Atorvastatin 40mg Tablets",
                batch_lot_number="TEST-BATCH-001",
            )
            db.add(root_complaint)
            db.commit()
            db.refresh(root_complaint)
            canonical_id = root_complaint.id
        finally:
            db.close()

        with patch("app.agent.nodes.extract_entities.call_groq", return_value=MOCK_EXTRACTION), \
             patch("app.agent.nodes.validate_completeness.call_groq", return_value=MOCK_COMPLETENESS), \
             patch("app.agent.nodes.classify_risk.call_groq", return_value=MOCK_RISK), \
             patch("app.agent.nodes.recommend_capa.call_groq", return_value=MOCK_CAPA), \
             patch("app.agent.nodes.generate_summary.call_groq", return_value=MOCK_SUMMARY), \
             patch("app.db.database.log_node_execution"):

            state = make_state(
                raw_input="Duplicate Atorvastatin packaging complaint.",
                input_type="txt",
            )
            result = complaint_pipeline.invoke(state)

        assert result["is_duplicate"] is True
        assert result["duplicate_match_id"] == canonical_id


class TestPipelineLiveApi:
    """
    Live Groq API integration test. Skipped in CI runs.
    Run manually with: pytest -m live_api
    """

    @pytest.mark.live_api
    def test_live_api_end_to_end_txt_sample(self):
        """Real pipeline run on sample_pharma_complaint.txt with actual Groq API."""
        from app.core.config import settings
        if not settings.GROQ_API_KEY or settings.GROQ_API_KEY == "gsk_your_groq_api_key_here":
            pytest.skip("GROQ_API_KEY not set — skipping live API test")

        from app.agent.graph import complaint_pipeline
        from app.services.document_parser import parse_document

        txt_path = os.path.join(SAMPLE_DIR, "sample_pharma_complaint.txt")
        assert os.path.exists(txt_path), f"Sample TXT not found at {txt_path}"

        with open(txt_path, "rb") as f:
            content = f.read()
        text, input_type = parse_document(content, "sample_pharma_complaint.txt")

        state = make_state(raw_input=text, input_type=input_type)
        result = complaint_pipeline.invoke(state)

        # Core sanity checks on real output
        assert result["severity"] in ["Critical", "Major", "Minor"]
        assert result["priority"] in ["High", "Medium", "Low"]
        assert isinstance(result["risk_score"], float)
        assert len(result.get("summary", "")) > 20
        capa = result.get("capa_recommendation", "")
        assert "[" in capa and "]" in capa
        assert result["extracted_fields"].get("product_name") is not None
        assert result["extracted_fields"].get("batch_lot_number") is not None
