"""Integration tests for FastAPI REST API endpoints."""

import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "gemini_model" in data
    assert "supabase" in data


def test_chat_endpoint_valid():
    response = client.post("/chat", json={"message": "Where is the CSE department?"})
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "tool_used" in data
    assert "sources" in data
    assert "confidence" in data
    assert len(data["tool_used"]) > 0


def test_chat_endpoint_empty_message():
    response = client.post("/chat", json={"message": "   "})
    assert response.status_code == 400


def test_feedback_endpoint_valid():
    payload = {
        "rating": 5,
        "user_query": "Which xerox is best?",
        "tool_used": "find_best_service",
        "recommendation": "Main Campus Xerox",
        "predicted_wait": 4,
        "actual_wait": 3,
        "feedback_type": "wait_time",
        "feedback_text": "Great prediction!",
    }
    response = client.post("/feedback", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


def test_feedback_endpoint_invalid_rating():
    payload = {
        "rating": 10,
        "feedback_text": "Bad rating value",
    }
    response = client.post("/feedback", json=payload)
    assert response.status_code == 422  # Validation error from Pydantic


def test_openapi_docs_endpoint():
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert schema["info"]["title"] == "VIGNAN — Adaptive Campus Intelligence Agent API"
    assert "/chat" in schema["paths"]
    assert "/feedback" in schema["paths"]
    assert "/health" in schema["paths"]
    assert "/stats" in schema["paths"]
    assert "/directory" in schema["paths"]


def test_stats_endpoint():
    response = client.get("/stats")
    assert response.status_code == 200
    data = response.json()
    assert "departments" in data
    assert "faculty" in data
    assert "services" in data
    assert "xerox" in data
    assert data["departments"] >= 2
    assert data["faculty"] >= 2


def test_directory_endpoint():
    response = client.get("/directory?category=departments")
    assert response.status_code == 200
    data = response.json()
    assert data["category"] == "departments"
    assert len(data["data"]) > 0


def test_frontend_root_serving():
    response = client.get("/")
    assert response.status_code == 200
    assert "VIGNAN" in response.text
    assert "Campus Intelligence" in response.text
