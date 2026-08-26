"""Tests for Campus Directory endpoints and data schema correctness."""

import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_directory_faculty_real_data():
    """Verify faculty directory returns real names and fields without placeholder strings."""
    response = client.get("/directory?category=faculty")
    assert response.status_code == 200
    data = response.json()
    assert data["category"] == "faculty"
    records = data["data"]
    assert len(records) > 0

    for f in records:
        assert "full_name" in f
        assert f["full_name"] != "VIGNAN Record"
        assert f["full_name"] is not None
        assert "department_name" in f


def test_directory_departments_real_data():
    """Verify department directory returns real department names and HODs."""
    response = client.get("/directory?category=departments")
    assert response.status_code == 200
    data = response.json()
    records = data["data"]
    assert len(records) > 0

    for d in records:
        assert "name" in d
        assert d["name"] != "VIGNAN Record"
        assert "short_name" in d


def test_directory_services_real_data():
    """Verify services directory returns real service names and categories."""
    response = client.get("/directory?category=services")
    assert response.status_code == 200
    data = response.json()
    records = data["data"]
    assert len(records) > 0

    for s in records:
        assert "name" in s
        assert s["name"] != "VIGNAN Record"
        assert "category" in s


def test_directory_academic_support_real_data():
    """Verify academic leads directory returns real person names and roles."""
    response = client.get("/directory?category=academic_support")
    assert response.status_code == 200
    data = response.json()
    records = data["data"]
    assert len(records) > 0

    for a in records:
        assert "person_name" in a
        assert a["person_name"] != "VIGNAN Record"
        assert "role_name" in a
