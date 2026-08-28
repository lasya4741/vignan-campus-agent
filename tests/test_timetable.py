import pytest
from datetime import datetime
from backend.tools.timetable import (
    get_current_class,
    get_next_class,
    get_daily_timetable,
    get_class_at_time,
    get_next_timetable_event,
    get_class_location,
    query_timetable
)
from backend.agent import CoordinatorAgent

def test_year2_section8_monday_regression():
    """Mandatory regression test for Year 2 Section 8 Monday at 10:00 AM."""
    dt_str = "2026-08-24T10:00:00+05:30"  # 2026-08-24 is a Monday
    res = get_current_class(year=2, section="8", current_datetime=dt_str)
    
    assert res["status"] == "success"
    curr = res["current_class"]
    assert curr["subject_code"] == "DBMS"
    assert curr["start_time"] == "09:55"
    assert curr["end_time"] == "10:45"
    assert curr["room"] == "N-314A"
    
    next_cls = res["next_class"]
    assert next_cls is not None
    assert next_cls["subject_code"] == "DS"
    assert next_cls["start_time"] == "12:40"
    assert next_cls["end_time"] in ["13:30", "14:20"]

def test_year3_section8_monday_regression():
    """Mandatory regression test for Year 3 Section 8 Monday at 08:30 AM."""
    dt_str = "2026-08-24T08:30:00+05:30"  # Monday
    res = get_current_class(year=3, section="8", current_datetime=dt_str)
    
    assert res["status"] == "success"
    curr = res["current_class"]
    assert "PC LAB" in curr["subject_code"]
    assert curr["room"] == "N-407"

def test_year3_section1_and_section22_simulations():
    """Simulation tests for Year 3 Section 1 and Section 22."""
    res_sec1 = query_timetable(year=3, section="1", day_of_week="Monday")
    assert len(res_sec1) > 0
    assert res_sec1[0]["section_default_room"] == "N-407"
    
    res_sec22 = query_timetable(year=3, section="22", day_of_week="Monday")
    assert len(res_sec22) > 0
    assert res_sec22[0]["section_default_room"] == "N-517"

def test_year_separation():
    """Ensure Year 2 Section 8 and Year 3 Section 8 remain completely distinct."""
    y2 = query_timetable(year=2, section="8", day_of_week="Monday")
    y3 = query_timetable(year=3, section="8", day_of_week="Monday")
    
    assert len(y2) > 0
    assert len(y3) > 0
    assert y2[0]["year"] == 2
    assert y3[0]["year"] == 3
    assert y2[0]["section_default_room"] != y3[0]["section_default_room"]

def test_class_at_time():
    """Test retrieving class at a specific time (e.g. 14:30 / 2:30 PM)."""
    res = get_class_at_time(year=2, section="8", date="2026-08-24", requested_time="14:30")
    assert res["status"] == "success"
    mc = res["matched_class"]
    assert mc["subject_code"] == "DMS"

def test_daily_timetable():
    """Test retrieving daily timetable for Monday."""
    res = get_daily_timetable(year=2, section="8", date="2026-08-24")
    assert res["status"] == "success"
    assert res["day"] == "Monday"
    assert len(res["schedule"]) > 0

def test_class_location_resolution():
    """Test resolving location and building for room N-314A."""
    res = get_class_location(year=2, section="8", target="current", current_datetime="2026-08-24T10:00:00+05:30")
    assert res["status"] == "success"
    assert res["room"] == "N-314A"
    assert res["building"] == "N Block"
    assert "N Block" in res["navigation_guidance"]

def test_agent_profile_auto_context():
    """Test agent uses user profile context (Year=2, Section=8) automatically."""
    agent = CoordinatorAgent()
    user_context = {"year": 2, "section": "8", "department": "CSE"}
    
    response = agent.run("What class do I have now?", user=user_context)
    assert response.confidence == "high"
    assert response.requires_clarification is False
    assert "DBMS" in response.answer or "class" in response.answer.lower()

def test_agent_missing_profile_clarification():
    """Test agent asks for section when profile section is missing."""
    agent = CoordinatorAgent()
    user_context = {"year": 2}
    
    response = agent.run("What class do I have now?", user=user_context)
    assert response.requires_clarification is True
    assert "section" in response.answer.lower()
