"""Comprehensive test suite for Final Agent Robustness, HOD Authority, MHP Resolution, and Google Maps Navigation."""

import re
import urllib.parse
import pytest
from backend.agent import coordinator
from backend.tools.navigation import get_route, build_google_maps_url, resolve_map_point
from backend.tools.departments import search_department
from backend.tools.faculty import search_faculty
from backend.tools.services import search_service
from backend.tools.offices import search_office


def test_hod_real_faculty_resolution():
    """Verify that all departments with HODs resolve to real faculty members, not placeholders."""
    # CSE HOD
    cse_res = search_department("CSE")
    assert cse_res["count"] > 0
    cse_hod = cse_res["matches"][0]["hod"]
    assert cse_hod is not None
    assert "Phani Kumar" in cse_hod["name"]
    assert "HOD of" not in cse_hod["name"]

    # IT HOD
    it_res = search_department("Information Technology")
    assert it_res["count"] > 0
    it_hod = it_res["matches"][0]["hod"]
    assert it_hod is not None
    assert "Sujatha" in it_hod["name"]
    assert "HOD of" not in it_hod["name"]


def test_agent_who_hod_queries():
    """Verify that 'Who' HOD queries prioritize person identity first."""
    # 1. Who is the HOD of CSE?
    resp1 = coordinator.run("Who is the HOD of CSE?")
    assert "Dr. S.V. Phani Kumar" in resp1.answer
    assert "Computer Science" in resp1.answer
    assert "HOD of CSE" not in resp1.answer

    # 2. Who heads CSE?
    resp2 = coordinator.run("Who heads CSE?")
    assert "Dr. S.V. Phani Kumar" in resp2.answer

    # 3. Who is the HOD of IT?
    resp3 = coordinator.run("Who is the HOD of IT?")
    assert "Dr. Kamepalli Sujatha" in resp3.answer
    assert "Information Technology" in resp3.answer
    assert "HOD of Information Technology" not in resp3.answer

    # 4. Who heads Information Technology?
    resp4 = coordinator.run("Who heads Information Technology?")
    assert "Dr. Kamepalli Sujatha" in resp4.answer

    # 5. Who is the head of Computer Science Engineering?
    resp5 = coordinator.run("Who is the head of Computer Science Engineering?")
    assert "Dr. S.V. Phani Kumar" in resp5.answer


def test_mhp_and_canteen_queries():
    """Verify that MHP and canteen queries properly route to MHP / Main Canteen."""
    # 1. Where is MHP?
    resp1 = coordinator.run("Where is MHP?")
    assert "MHP / Main Canteen" in resp1.answer
    assert "Central Campus" in resp1.answer or "Ground" in resp1.answer

    # 2. Where is the main canteen?
    resp2 = coordinator.run("Where is the main canteen?")
    assert "MHP / Main Canteen" in resp2.answer

    # 3. Where can I get lunch?
    resp3 = coordinator.run("Where can I get lunch?")
    assert "MHP" in resp3.answer or "Canteen" in resp3.answer

    # 4. Where do students eat?
    resp4 = coordinator.run("Where do students eat?")
    assert "MHP" in resp4.answer or "Canteen" in resp4.answer


def test_finance_and_fee_queries():
    """Verify that Finance and fee queries route to Finance & Accounts Office."""
    resp1 = coordinator.run("Where is Finance?")
    assert "Finance & Accounts Office" in resp1.answer
    assert "A Block" in resp1.answer

    resp2 = coordinator.run("Where can I pay my fees?")
    assert "Finance & Accounts Office" in resp2.answer
    assert "A Block" in resp2.answer


def test_it_and_cse_locations():
    """Verify that IT is in U Block and CSE is in N Block."""
    resp_it = coordinator.run("Where is IT?")
    assert "U Block" in resp_it.answer

    resp_cse = coordinator.run("Which block is CSE in?")
    assert "N Block" in resp_cse.answer


def test_balu_sir_queries():
    """Verify that Balu sir queries resolve correctly with room NB-409."""
    # Where is Balu sir?
    resp1 = coordinator.run("Where is Balu sir?")
    assert "Dr. G Balu Narasimha Rao" in resp1.answer
    assert "NB-409" in resp1.answer
    assert "N Block" in resp1.answer

    # Who is Balu sir?
    resp2 = coordinator.run("Who is Balu sir?")
    assert "Dr. G Balu Narasimha Rao" in resp2.answer
    assert "Assistant Professor" in resp2.answer
    assert "Computer Science" in resp2.answer

    # What does Balu sir research?
    resp3 = coordinator.run("What does Balu sir research?")
    assert "Adhoc Wireless Networks" in resp3.answer or "Machine Learning" in resp3.answer


def test_placements_and_responsibilities():
    """Verify that placement queries resolve to T&P."""
    resp = coordinator.run("Who handles placements?")
    assert "Training & Placements" in resp.answer or "T&P" in resp.answer or "Balu" in resp.answer


def test_xerox_and_printing_queries():
    """Verify that Xerox queries route properly."""
    resp1 = coordinator.run("Where can I Xerox?")
    assert "Xerox" in resp1.answer

    resp2 = coordinator.run("Which Xerox should I use?")
    assert "Xerox" in resp2.answer
    assert "Recommended" in resp2.answer or "Facility" in resp2.answer


def test_transport_office_queries():
    """Verify transport office and bus pass queries."""
    resp1 = coordinator.run("Where is the Transport Office?")
    assert "Transport Office" in resp1.answer
    assert "Main Gate" in resp1.answer

    resp2 = coordinator.run("Where do I get my bus pass?")
    assert "Transport" in resp2.answer
    assert "Main Gate" in resp2.answer


def test_counsellor_queries():
    """Verify counsellor queries with and without user context."""
    # Missing profile
    resp1 = coordinator.run("Who is my counsellor?")
    assert "Year and Section" in resp1.answer
    assert resp1.requires_clarification is True

    # With profile
    user_prof = {"year": 3, "section": "8"}
    resp2 = coordinator.run("Who is my counsellor?", user=user_prof)
    assert "Year 3, Section 8" in resp2.answer
    assert resp2.requires_clarification is False

    # Explicit query
    resp3 = coordinator.run("Year 3 Section 8.")
    assert "Section 8" in resp3.answer


def test_google_maps_navigation_routes():
    """Verify Google Maps route generation across varied natural phrasing."""
    # 1. From A Block to MHP
    resp1 = coordinator.run("How do I get from A Block to MHP?")
    assert resp1.route is not None
    assert "A Block" in resp1.route.origin
    assert "Mhp" in resp1.route.destination or "MHP" in resp1.route.destination
    assert resp1.route.travel_mode == "walking"
    assert "https://www.google.com/maps/dir/?api=1" in resp1.route.google_maps_url
    assert "travelmode=walking" in resp1.route.google_maps_url

    # 2. How do I get to Finance?
    resp2 = coordinator.run("How do I get to Finance?")
    assert resp2.route is not None
    assert "Finance" in resp2.route.destination
    assert "google.com/maps" in resp2.route.google_maps_url

    # 3. Take me to the Transport Office
    resp3 = coordinator.run("Take me to the Transport Office.")
    assert resp3.route is not None
    assert "Transport" in resp3.route.destination
    assert "google.com/maps" in resp3.route.google_maps_url

    # 4. How can I reach IT?
    resp4 = coordinator.run("How can I reach IT?")
    assert resp4.route is not None
    assert "google.com/maps" in resp4.route.google_maps_url

    # 5. Show me the route to the Xerox shop
    resp5 = coordinator.run("Show me the route to the Xerox shop.")
    assert resp5.route is not None
    assert "google.com/maps" in resp5.route.google_maps_url


def test_room_level_indoor_guidance():
    """Verify that indoor rooms (e.g. NB-409) explain building guidance vs room guidance."""
    res = get_route(start_location="Main Gate", destination="Room NB-409")
    assert res["found"] is True
    assert res["indoor_guidance"] is not None
    assert "Room-level navigation" in res["indoor_guidance"]
    assert "NB-409" in res["indoor_guidance"]
    assert "N Block" in res["indoor_guidance"]


def test_cse_hod_teaching_and_research():
    """Verify CSE HOD verified teaching engagements and research interests."""
    resp_teach = coordinator.run("What does the CSE HOD teach?")
    assert "Data Mining" in resp_teach.answer or "Machine Learning" in resp_teach.answer or "Deep Learning" in resp_teach.answer

    resp_res = coordinator.run("What does the CSE HOD research?")
    assert "Machine Learning" in resp_res.answer or "Text Mining" in resp_res.answer


def test_out_of_scope_rejection():
    """Verify strict domain boundary refusal on non-campus questions."""
    for q in [
        "Write Python code.",
        "Explain quantum computing.",
        "What is machine learning?",
        "Who won the cricket match?",
        "Tell me a joke."
    ]:
        resp = coordinator.run(q)
        assert "VIGNAN Campus Intelligence Assistant" in resp.answer
        assert "verified information about VIGNAN University" in resp.answer
