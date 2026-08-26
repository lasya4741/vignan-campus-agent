"""Tests for pre-import data integrity validation script."""

import json
import os
import tempfile
import pytest
from scripts.validate_data import validate_dataset


def test_validate_extracted_dataset():
    # The real extracted dataset in database/extracted should validate cleanly
    is_valid, errors, stats = validate_dataset("database/extracted")
    assert is_valid is True, f"Validation errors: {errors}"
    assert len(errors) == 0
    assert stats["sources"] >= 6
    assert stats["faculty"] >= 50
    assert stats["counsellors"] >= 50


def test_validate_empty_dataset():
    with tempfile.TemporaryDirectory() as tmpdir:
        is_valid, errors, stats = validate_dataset(tmpdir)
        assert is_valid is True
        assert len(errors) == 0


def test_validate_broken_relationship_detected():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create department referencing non-existent source
        depts = [{
            "id": "dept-1",
            "name": "Invalid Dept",
            "source_id": "non-existent-src-id"
        }]
        with open(os.path.join(tmpdir, "departments.json"), "w") as f:
            json.dump(depts, f)

        # Empty sources
        with open(os.path.join(tmpdir, "sources.json"), "w") as f:
            json.dump([], f)

        is_valid, errors, stats = validate_dataset(tmpdir)
        assert is_valid is False
        assert any("Broken source_id" in e for e in errors)


def test_validate_counsellor_range_inversion_detected():
    with tempfile.TemporaryDirectory() as tmpdir:
        couns = [{
            "id": "c-1",
            "counsellor_name": "Test Counsellor",
            "registration_range_start": "241FA04050",
            "registration_range_end": "241FA04010"  # Inverted!
        }]
        with open(os.path.join(tmpdir, "counsellors.json"), "w") as f:
            json.dump(couns, f)

        is_valid, errors, stats = validate_dataset(tmpdir)
        assert is_valid is False
        assert any("Invalid registration range" in e for e in errors)
