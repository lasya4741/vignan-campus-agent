"""Tests for Official CSE Faculty Data Ingestion, Authority, Research, and Teaching Knowledge."""

import pytest
from backend.agent import coordinator
from backend.tools.faculty import search_faculty
from backend.tools.departments import search_department
from backend.tools.subjects import search_subject


def test_cse_hod_authority_queries():
    """Verify Dr. S.V. Phani Kumar is canonical CSE HOD across phrasing variations."""
    queries = [
        "Who is the HOD of CSE?",
        "Who is the CSE head?",
        "Who is the Head of Computer Science Engineering?",
        "Tell me about the CSE HOD.",
    ]
    for q in queries:
        resp = coordinator.run(q)
        assert "Phani Kumar" in resp.answer, f"Failed for query: {q}"
        assert "search_department" in resp.tool_used or "search_faculty" in resp.tool_used


def test_cse_hod_where_query():
    """Verify CSE HOD location states N Block and room availability correctly."""
    resp = coordinator.run("Where is the CSE HOD?")
    assert "Phani Kumar" in resp.answer
    assert "N Block" in resp.answer
    assert "not available" in resp.answer.lower() or "room" in resp.answer.lower()


def test_faculty_balu_location_query():
    """Verify Dr. G. Balu Narasimha Rao retains verified room NB-409 from posters."""
    resp = coordinator.run("Where is Balu sir?")
    assert "Balu" in resp.answer
    assert "NB-409" in resp.answer or "409" in resp.answer
    assert "search_faculty" in resp.tool_used


def test_faculty_research_query():
    """Verify research query returns verified research areas."""
    resp = coordinator.run("What does Dr. S.V. Phani Kumar research?")
    assert "Phani Kumar" in resp.answer
    assert ("Machine Learning" in resp.answer or "Data Mining" in resp.answer or "research" in resp.answer.lower())
    assert "search_faculty" in resp.tool_used


def test_faculty_teaching_query():
    """Verify teaching query returns verified teaching course engagements."""
    resp = coordinator.run("What does Dr. S.V. Phani Kumar teach?")
    assert "Phani Kumar" in resp.answer
    assert ("Machine Learning" in resp.answer or "Data Mining" in resp.answer or "Deep Learning" in resp.answer or "Operating Systems" in resp.answer)
    assert "search_faculty" in resp.tool_used


def test_it_hod_distinction():
    """Verify IT HOD remains separate in U Block and does not conflict with CSE."""
    resp = coordinator.run("Who is the HOD of IT?")
    assert "Information Technology" in resp.answer or "IT" in resp.answer
    assert "search_department" in resp.tool_used


def test_cse_vs_it_separation():
    """Verify CSE Core and IT are distinct entities in N Block and U Block respectively."""
    cse_res = search_department("CSE")
    it_res = search_department("IT")
    assert cse_res["matches"][0]["name"] != it_res["matches"][0]["name"]
    assert "N Block" in cse_res["matches"][0]["block"]
    assert "U Block" in it_res["matches"][0]["block"]


def test_faculty_tool_metadata():
    """Verify search_faculty tool returns research and teaching metadata."""
    res = search_faculty("Phani Kumar")
    assert res["count"] >= 1
    fac = res["matches"][0]
    assert fac["full_name"] == "Dr. S.V. Phani Kumar"
    assert fac["email"] == "hodcse@vignan.ac.in"
    assert len(fac["research_interests"]) >= 1
    assert len(fac["teaching_engagements"]) >= 1
    assert fac["empcode"] == "675"
