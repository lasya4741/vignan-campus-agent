"""Tests for Coordinator Agent orchestration and anti-hallucination behavior."""

import pytest
from backend.agent import coordinator


def test_agent_counsellor_query():
    response = coordinator.run("Who is the counsellor for Year 2 Section 1?")
    assert response.answer is not None
    assert "search_counsellor" in response.tool_used
    assert response.confidence in ["high", "medium"]


def test_agent_department_location():
    response = coordinator.run("Where is the CSE department?")
    assert "N Block" in response.answer or "U Block" in response.answer
    assert "search_department" in response.tool_used


def test_agent_best_xerox_recommendation():
    response = coordinator.run("I need to print my project. Which xerox should I use?")
    assert "Xerox" in response.answer
    assert "find_best_service" in response.tool_used


def test_agent_route_navigation():
    response = coordinator.run("from Main Gate to U Block directions")
    assert "get_route" in response.tool_used or "search_faculty" in response.tool_used
    assert response.answer is not None


def test_agent_unverified_fallback():
    response = coordinator.run("Who is professor QuantumSuperconductive999?")
    assert "no verified records" in response.answer.lower() or "not found" in response.answer.lower()


def test_agent_year3_section8_counsellor():
    response = coordinator.run("Who is the counsellor for Year 3 Section 8?")
    assert response.answer is not None
    assert "search_counsellor" in response.tool_used
    assert "Dr. G. Balu Narasimha Rao" in response.answer
    assert "Mrs. Varagani Tejaswi" in response.answer
    assert "NB-409" in response.answer
    assert "NB-401A" in response.answer


def test_agent_xerox_near_zest():
    response = coordinator.run("Where is the Xerox near Zest?")
    assert response.answer is not None
    assert "search_service" in response.tool_used
    assert "Zest" in response.answer or "MHP" in response.answer


def test_agent_mhp_location():
    response = coordinator.run("Where is MHP?")
    assert response.answer is not None
    assert "search_service" in response.tool_used or "search_location" in response.tool_used

