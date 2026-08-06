"""
Unit tests for each LangGraph agent node with mocked Groq API.
No live API calls are made — all LLM responses are canned.

Run: pytest backend/tests/test_nodes.py -v -m unit
"""
import json
import os
import sys
from unittest.mock import patch, MagicMock

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from conftest import make_state, FULL_EXTRACTED_FIELDS  # noqa: E402

pytestmark = pytest.mark.unit

REQUIRED_FIELDS = [
    "complaint_source", "customer_name", "product_name", "product_strength_grade",
    "batch_lot_number", "manufacturing_date", "expiry_date", "quantity_affected",
    "complaint_type", "complaint_date", "detailed_description",
]


# ---------------------------------------------------------------------------
# TestExtractEntitiesNode
# ---------------------------------------------------------------------------
class TestExtractEntitiesNode:
    """Node 2: extract_entities — mock call_groq, test defensive JSON parsing."""

    def test_happy_path_all_fields(self):
        """Valid JSON response with all 11 fields -> extracted_fields fully populated."""
        from app.agent.nodes.extract_entities import extract_entities_node

        mock_response = json.dumps(FULL_EXTRACTED_FIELDS)
        state = make_state(raw_input="Complaint about Atorvastatin blister seal failure.")

        with patch("app.agent.nodes.extract_entities.call_groq", return_value=mock_response):
            result = extract_entities_node(state)

        ef = result["extracted_fields"]
        assert isinstance(ef, dict)
        for field in REQUIRED_FIELDS:
            assert field in ef, f"Field '{field}' missing from extracted_fields"
        assert ef["batch_lot_number"] == "ATR-2024-B0421"
        assert ef["product_name"] == "Atorvastatin 40mg Tablets"
        assert result["errors"] == []

    def test_malformed_json_falls_back_gracefully(self):
        """Malformed JSON from LLM -> all fields None, errors logged, no exception raised."""
        from app.agent.nodes.extract_entities import extract_entities_node

        state = make_state(raw_input="Some complaint text.")

        with patch("app.agent.nodes.extract_entities.call_groq", return_value="not valid json {{{"):
            result = extract_entities_node(state)

        ef = result["extracted_fields"]
        assert isinstance(ef, dict)
        for field in REQUIRED_FIELDS:
            assert field in ef
            assert ef[field] is None

        assert len(result["errors"]) == 1
        assert "JSON parse error" in result["errors"][0]

    def test_empty_json_object_fills_all_fields_with_none(self):
        """LLM returns '{}' -> all 11 required fields present but None."""
        from app.agent.nodes.extract_entities import extract_entities_node

        state = make_state(raw_input="Complaint text here.")

        with patch("app.agent.nodes.extract_entities.call_groq", return_value="{}"):
            result = extract_entities_node(state)

        ef = result["extracted_fields"]
        for field in REQUIRED_FIELDS:
            assert field in ef
            assert ef[field] is None
        assert result["errors"] == []

    def test_empty_raw_input_skips_groq(self):
        """Empty raw_input -> Groq is never called, all fields None, error logged."""
        from app.agent.nodes.extract_entities import extract_entities_node

        state = make_state(raw_input="")

        with patch("app.agent.nodes.extract_entities.call_groq") as mock_groq:
            result = extract_entities_node(state)
            mock_groq.assert_not_called()

        ef = result["extracted_fields"]
        for field in REQUIRED_FIELDS:
            assert ef[field] is None
        assert len(result["errors"]) == 1
        assert "raw_input is empty" in result["errors"][0]

    def test_partial_fields_filled_rest_none(self):
        """LLM returns only 3 of 11 fields -> all 11 keys exist, 8 are None."""
        from app.agent.nodes.extract_entities import extract_entities_node

        partial = {
            "product_name": "Atorvastatin 40mg",
            "batch_lot_number": "B-001",
            "complaint_type": "Packaging Defect",
        }
        state = make_state(raw_input="Partial complaint data.")

        with patch("app.agent.nodes.extract_entities.call_groq", return_value=json.dumps(partial)):
            result = extract_entities_node(state)

        ef = result["extracted_fields"]
        assert len(ef) == 11
        assert ef["product_name"] == "Atorvastatin 40mg"
        assert ef["customer_name"] is None
        assert ef["manufacturing_date"] is None
        assert result["errors"] == []


# ---------------------------------------------------------------------------
# TestValidateCompletenessNode
# ---------------------------------------------------------------------------
class TestValidateCompletenessNode:
    """Node 3: validate_completeness — hybrid rule + LLM check."""

    def test_all_fields_present_score_100(self):
        """All 11 fields populated -> completeness 100, no missing fields."""
        from app.agent.nodes.validate_completeness import validate_completeness_node

        state = make_state(extracted_fields=FULL_EXTRACTED_FIELDS)
        llm_resp = json.dumps({"completeness_score": 100.0, "missing_fields": []})

        with patch("app.agent.nodes.validate_completeness.call_groq", return_value=llm_resp), \
             patch("app.agent.nodes.validate_completeness.log_node_execution"):
            result = validate_completeness_node(state)

        assert result["completeness_score"] == 100.0
        assert result["missing_fields"] == []
        assert result["errors"] == []

    def test_missing_3_fields_lower_score(self):
        """3 fields missing (None) -> completeness < 100, all 3 in missing_fields."""
        from app.agent.nodes.validate_completeness import validate_completeness_node

        ef = dict(FULL_EXTRACTED_FIELDS)
        ef["manufacturing_date"] = None
        ef["expiry_date"] = None
        ef["quantity_affected"] = None
        state = make_state(extracted_fields=ef)

        llm_resp = json.dumps({
            "completeness_score": 70.0,
            "missing_fields": ["manufacturing_date", "expiry_date", "quantity_affected"]
        })

        with patch("app.agent.nodes.validate_completeness.call_groq", return_value=llm_resp), \
             patch("app.agent.nodes.validate_completeness.log_node_execution"):
            result = validate_completeness_node(state)

        assert result["completeness_score"] < 100.0
        for field in ["manufacturing_date", "expiry_date", "quantity_affected"]:
            assert field in result["missing_fields"]

    def test_all_fields_missing_zero_score(self):
        """All 11 fields None -> rule-based score 0.0, all 11 in missing_fields."""
        from app.agent.nodes.validate_completeness import validate_completeness_node

        ef = {f: None for f in REQUIRED_FIELDS}
        state = make_state(extracted_fields=ef)

        llm_resp = json.dumps({"completeness_score": 0.0, "missing_fields": REQUIRED_FIELDS})

        with patch("app.agent.nodes.validate_completeness.call_groq", return_value=llm_resp), \
             patch("app.agent.nodes.validate_completeness.log_node_execution"):
            result = validate_completeness_node(state)

        assert result["completeness_score"] == 0.0
        assert len(result["missing_fields"]) == 11

    def test_llm_failure_falls_back_to_rule_based(self):
        """LLM raises exception -> falls back to rule-based check, no crash, no error appended."""
        from app.agent.nodes.validate_completeness import validate_completeness_node

        # Only 8 of 11 fields filled -> rule score = 72.7%
        ef = dict(FULL_EXTRACTED_FIELDS)
        ef["manufacturing_date"] = None
        ef["expiry_date"] = None
        ef["quantity_affected"] = None
        state = make_state(extracted_fields=ef)

        with patch("app.agent.nodes.validate_completeness.call_groq", side_effect=Exception("LLM down")), \
             patch("app.agent.nodes.validate_completeness.log_node_execution"):
            result = validate_completeness_node(state)

        # Should still return a valid score from rule-based fallback
        assert isinstance(result["completeness_score"], (int, float))
        assert result["completeness_score"] < 100.0
        # errors should NOT be appended for LLM fallback (it's expected degradation)
        assert "validate_completeness" not in str(result["errors"])


# ---------------------------------------------------------------------------
# TestClassifyRiskNode
# ---------------------------------------------------------------------------
class TestClassifyRiskNode:
    """Node 4: classify_severity_risk — Groq heavy model, rule-based fallback."""

    def test_happy_path_critical(self):
        """Valid JSON with Critical severity -> correct fields populated."""
        from app.agent.nodes.classify_risk import classify_risk_node

        state = make_state(extracted_fields=FULL_EXTRACTED_FIELDS)
        llm_resp = json.dumps({
            "severity": "Critical",
            "priority": "High",
            "risk_score": 90.0,
            "risk_reasoning": "Seal integrity failure with patient adverse reaction reported."
        })

        with patch("app.agent.nodes.classify_risk.call_groq", return_value=llm_resp), \
             patch("app.agent.nodes.classify_risk.log_node_execution"):
            result = classify_risk_node(state)

        assert result["severity"] == "Critical"
        assert result["priority"] == "High"
        assert result["risk_score"] == 90.0
        assert len(result["risk_reasoning"]) > 10
        assert result["errors"] == []

    def test_malformed_json_uses_rule_based_fallback(self):
        """LLM returns garbage -> rule-based fallback, no exception, error logged."""
        from app.agent.nodes.classify_risk import classify_risk_node

        state = make_state(
            extracted_fields=FULL_EXTRACTED_FIELDS,
            raw_input="Patient reported discomfort and adverse reaction."
        )

        with patch("app.agent.nodes.classify_risk.call_groq", return_value="INVALID JSON"), \
             patch("app.agent.nodes.classify_risk.log_node_execution"):
            result = classify_risk_node(state)

        assert result["severity"] in ["Critical", "Major", "Minor"]
        assert result["priority"] in ["High", "Medium", "Low"]
        assert isinstance(result["risk_score"], float)
        assert len(result["errors"]) == 1
        assert "classify_severity_risk" in result["errors"][0]

    def test_unexpected_schema_uses_defaults(self):
        """LLM returns JSON with different keys -> defaults applied gracefully."""
        from app.agent.nodes.classify_risk import classify_risk_node

        state = make_state(extracted_fields=FULL_EXTRACTED_FIELDS)

        with patch("app.agent.nodes.classify_risk.call_groq", return_value='{"foo": "bar"}'), \
             patch("app.agent.nodes.classify_risk.log_node_execution"):
            result = classify_risk_node(state)

        assert result["severity"] == "Major"      # default
        assert result["priority"] == "Medium"     # default
        assert result["risk_score"] == 65.0       # default
        assert result["errors"] == []


# ---------------------------------------------------------------------------
# TestRecommendCapaNode
# ---------------------------------------------------------------------------
class TestRecommendCapaNode:
    """Node 6: recommend_capa — 5M CAPA generation with rule-based fallback."""

    def test_happy_path_machine_category(self):
        """Valid JSON with Machine category -> recommendation prefixed [Machine]."""
        from app.agent.nodes.recommend_capa import recommend_capa_node

        state = make_state(
            extracted_fields=FULL_EXTRACTED_FIELDS,
            severity="Critical"
        )
        llm_resp = json.dumps({
            "root_cause_category": "Machine",
            "capa_recommendation": "Inspect and recalibrate the blister sealing machine."
        })

        with patch("app.agent.nodes.recommend_capa.call_groq", return_value=llm_resp), \
             patch("app.agent.nodes.recommend_capa.log_node_execution"):
            result = recommend_capa_node(state)

        assert result["capa_recommendation"].startswith("[Machine]")
        assert "recalibrate" in result["capa_recommendation"]
        assert result["errors"] == []

    def test_malformed_json_uses_rule_based_fallback(self):
        """Garbage LLM response -> fallback CAPA returned, errors logged."""
        from app.agent.nodes.recommend_capa import recommend_capa_node

        state = make_state(extracted_fields=FULL_EXTRACTED_FIELDS, severity="Major")

        with patch("app.agent.nodes.recommend_capa.call_groq", return_value="garbage not json"), \
             patch("app.agent.nodes.recommend_capa.log_node_execution"):
            result = recommend_capa_node(state)

        assert isinstance(result["capa_recommendation"], str)
        assert "[" in result["capa_recommendation"]
        assert len(result["errors"]) == 1
        assert "recommend_capa" in result["errors"][0]

    def test_empty_json_object_uses_default_category(self):
        """LLM returns '{}' -> root_cause_category defaults to 'Material'."""
        from app.agent.nodes.recommend_capa import recommend_capa_node

        state = make_state(extracted_fields=FULL_EXTRACTED_FIELDS, severity="Minor")

        with patch("app.agent.nodes.recommend_capa.call_groq", return_value="{}"), \
             patch("app.agent.nodes.recommend_capa.log_node_execution"):
            result = recommend_capa_node(state)

        assert result["capa_recommendation"].startswith("[Material]")
        assert result["errors"] == []


# ---------------------------------------------------------------------------
# TestGenerateSummaryNode
# ---------------------------------------------------------------------------
class TestGenerateSummaryNode:
    """Node 7: generate_summary — executive summary generation."""

    def test_happy_path_returns_summary(self):
        """Valid LLM response -> summary stored correctly."""
        from app.agent.nodes.generate_summary import generate_summary_node

        expected_summary = (
            "A Critical complaint about Atorvastatin 40mg batch ATR-2024-B0421 was reported "
            "by MedStore Plus regarding seal integrity failure."
        )
        state = make_state(extracted_fields=FULL_EXTRACTED_FIELDS)

        with patch("app.agent.nodes.generate_summary.call_groq", return_value=f"  {expected_summary}  "):
            result = generate_summary_node(state)

        assert result["summary"] == expected_summary  # strip() applied
        assert result["errors"] == []

    def test_groq_failure_returns_fallback_message(self):
        """Groq exception -> returns 'Summary generation failed.', error logged."""
        from app.agent.nodes.generate_summary import generate_summary_node

        state = make_state(extracted_fields=FULL_EXTRACTED_FIELDS)

        with patch("app.agent.nodes.generate_summary.call_groq", side_effect=Exception("API down")):
            result = generate_summary_node(state)

        assert result["summary"] == "Summary generation failed."
        assert len(result["errors"]) == 1
        assert "generate_summary" in result["errors"][0]

    def test_empty_extracted_fields_still_calls_groq(self):
        """Empty extracted_fields -> Groq is still called (fallback prompt with raw_input)."""
        from app.agent.nodes.generate_summary import generate_summary_node

        state = make_state(
            extracted_fields={},
            raw_input="Customer complaint about packaging quality issue."
        )

        with patch("app.agent.nodes.generate_summary.call_groq", return_value="Summary produced from raw text.") as mock_groq:
            result = generate_summary_node(state)

        mock_groq.assert_called_once()
        assert result["summary"] == "Summary produced from raw text."


# ---------------------------------------------------------------------------
# TestExtractNegativeConstraints
# ---------------------------------------------------------------------------
class TestExtractNegativeConstraints:
    """Test the chat_node._extract_negative_constraints helper for severity grounding."""

    def test_no_hospitalization_detected(self):
        """'no hospitalisation' in description -> constraint includes 'No hospitalization'."""
        from app.agent.nodes.chat_node import _extract_negative_constraints

        complaint = MagicMock()
        complaint.detailed_description = "Patient reported blister seal failure. No hospitalisation occurred."
        complaint.risk_reasoning = "Seal integrity failure confirmed."

        result = _extract_negative_constraints(complaint)
        assert "No hospitalization was required or reported" in result

    def test_resolved_symptoms_detected(self):
        """'resolved' in description -> constraint includes 'Symptoms were temporary and resolved'."""
        from app.agent.nodes.chat_node import _extract_negative_constraints

        complaint = MagicMock()
        complaint.detailed_description = "Symptoms resolved after stopping the medication."
        complaint.risk_reasoning = ""

        result = _extract_negative_constraints(complaint)
        assert "Symptoms were temporary and resolved" in result

    def test_no_constraints_found_uses_fallback(self):
        """Empty description and reasoning -> non-fatal/default constraint returned."""
        from app.agent.nodes.chat_node import _extract_negative_constraints

        complaint = MagicMock()
        complaint.detailed_description = ""
        complaint.risk_reasoning = ""

        result = _extract_negative_constraints(complaint)
        assert "life-threatening" in result.lower()

    def test_mild_adverse_effect_detected(self):
        """'mild' in description -> constraint about mild characterization added."""
        from app.agent.nodes.chat_node import _extract_negative_constraints

        complaint = MagicMock()
        complaint.detailed_description = "Patient experienced a mild allergic reaction."
        complaint.risk_reasoning = ""

        result = _extract_negative_constraints(complaint)
        assert "mild" in result.lower()
