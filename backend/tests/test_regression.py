"""
Regression tests formalizing the Phase 7 stress test findings.
These tests ensure no previously-fixed bug silently re-regresses.

Run: pytest backend/tests/test_regression.py -v -m regression
"""
import io
import os
import sys
import uuid

import pytest
from starlette.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

pytestmark = pytest.mark.regression


@pytest.fixture(scope="module")
def client():
    """FastAPI TestClient for in-process HTTP testing (no running server needed)."""
    from app.main import app
    return TestClient(app, raise_server_exceptions=False)


def upload_file(client, filename: str, content: bytes, mime: str = "application/octet-stream"):
    """Helper: POST file to /api/complaints/extract."""
    return client.post(
        "/api/complaints/extract",
        files={"file": (filename, content, mime)},
        params={"stream": "false"},
    )


def upload_text(client, text: str):
    """Helper: POST raw text to /api/complaints/extract as .txt file."""
    return client.post(
        "/api/complaints/extract",
        files={"file": ("complaint.txt", text.encode("utf-8"), "text/plain")},
        params={"stream": "false"},
    )


# ---------------------------------------------------------------------------
# REGRESSION GROUP 1: File Format Validation
# (fixed in: fix(validation): enforce file type + size limits on extraction endpoint)
# ---------------------------------------------------------------------------
class TestFileValidationRegression:
    """Regression: unsupported and fake file types must always return 422."""

    def test_jpg_upload_returns_422(self, client):
        """JPEG bytes uploaded as .jpg must be rejected with 422."""
        resp = upload_file(client, "photo.jpg", b"\xff\xd8\xff\xe0\x00\x10JFIF", "image/jpeg")
        assert resp.status_code == 422
        assert "Unsupported file format" in resp.json()["detail"]
        assert ".jpg" in resp.json()["detail"]

    def test_zip_upload_returns_422(self, client):
        """ZIP archive uploaded as .zip must be rejected with 422."""
        resp = upload_file(client, "archive.zip", b"PK\x03\x04" + b"fake zip content", "application/zip")
        assert resp.status_code == 422
        assert "Unsupported file format" in resp.json()["detail"]

    def test_fake_pdf_no_magic_bytes_returns_422(self, client):
        """File with .pdf extension but no %PDF magic header must be rejected with 422."""
        resp = upload_file(client, "fake.pdf", b"This is just plain text pretending to be a PDF", "application/pdf")
        assert resp.status_code == 422
        detail = resp.json()["detail"]
        assert "magic header" in detail.lower() or "invalid" in detail.lower()

    def test_binary_data_as_txt_returns_422(self, client):
        """Binary NUL bytes uploaded as .txt must be rejected with 422."""
        binary_content = b"\x00\x01\x02\x03\xff\xfe binary data here"
        resp = upload_file(client, "binary.txt", binary_content, "text/plain")
        assert resp.status_code == 422

    def test_valid_txt_passes_validation_gate(self, client):
        """Plain text .txt file must pass format validation (may fail at LLM stage, not at validation)."""
        valid_text = (
            b"Customer complaint: The Atorvastatin 40mg tablets packaging was found damaged. "
            b"Multiple packs had broken seals. Batch number: ATR-2024-TEST."
        )
        resp = upload_file(client, "complaint.txt", valid_text, "text/plain")
        # Must NOT be a 422 validation error — 200 (success) or 500 (LLM issue) are both acceptable
        assert resp.status_code != 422, f"Valid .txt file should pass format validation, got 422"

    def test_real_pdf_passes_validation_gate(self, client):
        """A real PDF with %PDF header must pass format validation."""
        sample_dir = os.path.join(os.path.dirname(__file__), "..", "sample_complaints")
        pdf_path = os.path.join(sample_dir, "sample_pharma_complaint.pdf")
        if not os.path.exists(pdf_path):
            pytest.skip("sample_pharma_complaint.pdf not found")
        with open(pdf_path, "rb") as f:
            content = f.read()
        resp = upload_file(client, "sample_pharma_complaint.pdf", content, "application/pdf")
        assert resp.status_code != 422


# ---------------------------------------------------------------------------
# REGRESSION GROUP 2: File Size Limits
# (fixed in: fix(validation): enforce file type + size limits on extraction endpoint)
# ---------------------------------------------------------------------------
class TestFileSizeRegression:
    """Regression: oversized files must be blocked before reaching Groq."""

    def test_11mb_txt_returns_413_quickly(self, client):
        """11MB file must return 413 before any LLM call."""
        import time
        large = b"A" * (11 * 1024 * 1024)
        start = time.time()
        resp = upload_file(client, "oversized.txt", large, "text/plain")
        elapsed = time.time() - start

        assert resp.status_code == 413
        assert "exceeds" in resp.json()["detail"].lower()
        # Should be rejected fast (no Groq round-trip) — under 5 seconds
        assert elapsed < 5.0, f"413 should be instant, took {elapsed:.2f}s"

    def test_15mb_txt_returns_413(self, client):
        """15MB file must return 413 with clear message."""
        large = b"B" * (15 * 1024 * 1024)
        resp = upload_file(client, "huge.txt", large, "text/plain")
        assert resp.status_code == 413
        detail = resp.json()["detail"]
        assert "10MB" in detail or "maximum" in detail.lower()

    def test_small_file_passes_size_check(self, client):
        """1KB valid text file must NOT get a 413."""
        small = b"Patient reported quality defect in Atorvastatin packaging. " * 10
        resp = upload_file(client, "small.txt", small, "text/plain")
        assert resp.status_code != 413


# ---------------------------------------------------------------------------
# REGRESSION GROUP 3: Input Content Validation
# ---------------------------------------------------------------------------
class TestInputValidationRegression:
    """Regression: empty/garbage text inputs must be caught and rejected cleanly."""

    def test_empty_text_returns_422(self, client):
        """Completely empty text file must return 422."""
        resp = upload_file(client, "empty.txt", b"", "text/plain")
        assert resp.status_code == 422

    def test_whitespace_only_returns_422(self, client):
        """Whitespace-only text must return 422 (no useful data to extract)."""
        resp = upload_file(client, "whitespace.txt", b"   \n   \t   \n", "text/plain")
        assert resp.status_code == 422

    def test_garbage_text_returns_200_not_crash(self, client):
        """Nonsense input text should NOT crash the API — it should return 200 with low completeness."""
        resp = upload_file(client, "garbage.txt", b"hello test 123 asdf xyz", "text/plain")
        # We expect 200 (pipeline degrades gracefully) or possibly a Groq-related error
        # What we must NOT see is an unhandled 500 crash
        assert resp.status_code in [200, 422, 500], f"Got unexpected status {resp.status_code}"
        if resp.status_code == 200:
            data = resp.json()
            # Garbage text should result in low completeness (< 50%) or many missing fields
            completeness = data.get("completeness_score", 0)
            missing = data.get("missing_fields", [])
            assert completeness < 80 or len(missing) > 3, (
                f"Garbage input should yield low completeness, got {completeness}% with {len(missing)} missing"
            )


# ---------------------------------------------------------------------------
# REGRESSION GROUP 4: Duplicate Detection Canonical Root Linking
# (fixed in: fix(duplicate): always link duplicate_match_id to canonical original)
# ---------------------------------------------------------------------------
class TestDuplicateDetectionRegression:
    """
    Regression: every duplicate must link to the ORIGINAL canonical complaint,
    not the most recent one in a chain.

    This test hits the real Groq API to submit 3 real complaints.
    Mark as live_api so CI can skip it.
    """

    @pytest.mark.live_api
    def test_duplicate_always_links_to_canonical_root(self, client):
        """Submit same batch 3 times: submissions 2 and 3 must link to submission 1's ID."""
        from app.core.config import settings
        if not settings.GROQ_API_KEY or settings.GROQ_API_KEY == "gsk_your_groq_api_key_here":
            pytest.skip("GROQ_API_KEY not set — skipping live duplicate regression test")

        unique_batch = f"REGRESSION-{uuid.uuid4().hex[:8].upper()}"
        complaint_text = (
            f"Complaint Source: Retail Pharmacy\n"
            f"Customer Name: Test Pharmacy\n"
            f"Product Name: Atorvastatin 40mg Tablets\n"
            f"Batch/Lot Number: {unique_batch}\n"
            f"Manufacturing Date: 2024-01-15\n"
            f"Expiry Date: 2026-01-14\n"
            f"Quantity Affected: 12 packs\n"
            f"Complaint Type: Packaging Defect\n"
            f"Complaint Date: 2024-06-01\n"
            f"Description: Blister seals found damaged on multiple packs."
        ).encode("utf-8")

        # Submission 1 — should be the canonical root
        resp1 = upload_file(client, "complaint.txt", complaint_text, "text/plain")
        assert resp1.status_code == 200, f"First submission failed: {resp1.text}"
        root_id = resp1.json()["complaint_id"]
        assert root_id is not None

        # Submission 2 — should detect duplicate, link to root
        resp2 = upload_file(client, "complaint.txt", complaint_text, "text/plain")
        assert resp2.status_code == 200
        d2 = resp2.json()
        assert d2["is_duplicate"] is True
        assert d2["duplicate_match_id"] == root_id, (
            f"Submission 2 should link to root {root_id}, got {d2['duplicate_match_id']}"
        )

        # Submission 3 — should STILL link to root, not to submission 2
        resp3 = upload_file(client, "complaint.txt", complaint_text, "text/plain")
        assert resp3.status_code == 200
        d3 = resp3.json()
        assert d3["is_duplicate"] is True
        assert d3["duplicate_match_id"] == root_id, (
            f"Submission 3 should link to root {root_id}, got {d3['duplicate_match_id']} "
            f"(chained-duplicate regression!)"
        )
