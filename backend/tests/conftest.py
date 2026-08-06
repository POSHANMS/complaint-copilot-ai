"""
Shared pytest fixtures and configuration for complaint-copilot-ai test suite.
"""
import os
import sys

# ALWAYS set SQLite DATABASE_URL BEFORE any app imports
os.environ["DATABASE_URL"] = "sqlite:///./test_complaints.db"
os.environ["GROQ_API_KEY"] = "gsk_mocked_dummy_test_key_for_pytest_1234567890"

# Ensure backend app directory is importable from tests/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
import app.db.models  # Ensures all ORM models are registered with Base metadata
from app.db.database import Base, engine
Base.metadata.create_all(bind=engine)


def make_state(**overrides) -> dict:
    """Build a minimal valid ComplaintState dict. Override any field with kwargs."""
    base = {
        "raw_input": "Sample pharma complaint text about product quality.",
        "input_type": "txt",
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
    base.update(overrides)
    return base


FULL_EXTRACTED_FIELDS = {
    "complaint_source": "Retail Pharmacy — MedStore Plus",
    "customer_name": "MedStore Plus, Bengaluru",
    "product_name": "Atorvastatin 40mg Tablets",
    "product_strength_grade": "40mg",
    "batch_lot_number": "ATR-2024-B0421",
    "manufacturing_date": "2024-01-15",
    "expiry_date": "2026-01-14",
    "quantity_affected": "48 blister packs",
    "complaint_type": "Packaging Defect",
    "complaint_date": "2024-06-15",
    "detailed_description": (
        "Multiple blister packs found with broken seal integrity. "
        "No hospitalization occurred. Symptoms resolved upon discontinuing product use."
    ),
}

SAMPLE_DIR = os.path.join(os.path.dirname(__file__), "..", "sample_complaints")
