"""Unit tests for individual tool functions in backend/tools."""

import pytest
from backend.tools.faculty import search_faculty
from backend.tools.departments import search_department
from backend.tools.subjects import search_subject
from backend.tools.counsellors import search_counsellor
from backend.tools.offices import search_office
from backend.tools.academic_support import search_responsibility
from backend.tools.services import search_service
from backend.tools.live_status import get_live_status, find_best_service
from backend.tools.navigation import get_route
from backend.tools.feedback import record_feedback
from backend.tools.verification import is_live_status_expired, compare_source_quality


def test_faculty_lookup():
    # Search by full name
    res = search_faculty(query="Dr. S.V. Phani Kumar")
    assert res["count"] >= 1
    assert res["matches"][0]["full_name"] == "Dr. S.V. Phani Kumar"
    assert res["matches"][0]["provenance"]["confidence"] == "high"

    # Search by room
    res_room = search_faculty(query="NB-409")
    assert res_room["count"] >= 1
    assert "NB-409" in res_room["matches"][0]["room"] or "409" in res_room["matches"][0]["room"]

    # Search non-existent
    res_none = search_faculty(query="NonExistentPerson123")
    assert res_none["count"] == 0


def test_department_lookup():
    # Search by abbreviation
    res = search_department(query="CSE")
    assert res["count"] >= 1
    assert "Computer Science" in res["matches"][0]["name"]
    assert res["matches"][0]["block"] == "N Block"
    assert res["matches"][0]["hod"]["name"] == "Dr. S.V. Phani Kumar"

    # Search by block
    res_block = search_department(query="N Block")
    assert res_block["count"] >= 1


def test_subject_lookup():
    # Search by course name
    res = search_subject(query="DBMS")
    assert res["count"] >= 1
    assert "DBMS" in res["matches"][0]["name"] or "Database" in res["matches"][0]["name"]
    assert len(res["matches"][0]["instructors"]) >= 1


def test_counsellor_by_year_section():
    res = search_counsellor(year=2, section="1")
    assert res["count"] >= 1
    assert len(res["matches"]) >= 1


def test_counsellor_by_registration_number():
    # 4005 falls in Year 2 range 4001 - 4071
    res = search_counsellor(registration_number="4005")
    assert res["count"] >= 1
    assert res["matches"][0]["section"] == "1"


def test_counsellor_unmatched_registration_number():
    # 241FA99999 does not fall in range
    res = search_counsellor(registration_number="241FA99999")
    assert res["count"] == 0
    assert "No verified counsellor mapping found" in res["message"]


def test_office_lookup():
    res = search_office(query="Finance")
    assert res["count"] >= 1
    assert "Finance" in res["matches"][0]["name"]


def test_academic_support_placements():
    res = search_responsibility(query="placements")
    assert res["count"] >= 1
    assert "Placement" in res["matches"][0]["role_name"] or "placement" in str(res["matches"][0]["responsibilities"]).lower()


def test_service_lookup():
    res = search_service(query="xerox", category="xerox")
    assert res["count"] >= 1
    assert "Xerox" in res["matches"][0]["name"]


def test_live_status_lookup():
    res = get_live_status("svc-xerox-main")
    assert res["status"] in ["available", "unknown"]


def test_best_service_recommendation():
    res = find_best_service(category="xerox")
    assert res["recommended_service"] is not None


def test_route_lookup_available():
    res = get_route(start_location="Main Gate", destination="U Block")
    assert res["found"] is True
    assert len(res["steps"]) >= 1


def test_route_lookup_unavailable():
    res = get_route(start_location="Main Gate", destination="NonExistentZoneXYZ")
    assert res["found"] is False
    assert len(res["steps"]) == 0
    assert "unavailable" in res["message"].lower()


def test_feedback_recording():
    res = record_feedback(
        rating=5,
        user_query="Where is the finance office?",
        recommendation="Finance office is on the 1st floor of A Block.",
        feedback_text="Very accurate and fast!"
    )
    assert res["success"] is True
    assert "feedback" in res["message"].lower()


def test_verification_provenance():
    assert is_live_status_expired(None) is True
    rec_a = {"confidence": "high", "source_type": "official_website"}
    rec_b = {"confidence": "medium", "source_type": "department_poster"}


def test_xerox_near_zest_lookup():
    res = search_service(query="Where is the Xerox near Zest?")
    assert res["count"] >= 1
    top = res["matches"][0]
    assert "Zest" in top["name"]
    assert "MHP" in top["name"]


def test_year3_section8_counsellors_poster_accuracy():
    res = search_counsellor(year=3, section="8")
    assert res["count"] == 2
    names = [c["counsellor_name"] for c in res["matches"]]
    assert "Dr. G. Balu Narasimha Rao" in names
    assert "Mrs. Varagani Tejaswi" in names
    for c in res["matches"]:
        if c["counsellor_name"] == "Dr. G. Balu Narasimha Rao":
            assert c["room"] == "NB-409"
            assert c["phone"] == "9701224847"
        elif c["counsellor_name"] == "Mrs. Varagani Tejaswi":
            assert c["room"] == "NB-401A"
            assert c["phone"] == "6305179829"


def test_navigation_zest_area():
    res = get_route(start_location="Main Gate", destination="MHP / Zest Area")
    assert res["found"] is True
    assert "google_maps_url" in res
    assert "https://www.google.com/maps/dir/" in res["google_maps_url"]


