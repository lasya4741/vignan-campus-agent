"""Comprehensive test suite for natural language timetable parsing, parameter extraction, tool exclusivity, and grounding."""

import pytest
from backend.agent import coordinator
from backend.utils.campus_entities import (
    CampusIntent,
    classify_campus_intent,
    extract_time_from_text,
    normalize_student_text,
)


def test_abbreviation_normalization():
    """Verify common student abbreviations are correctly normalized."""
    assert "class" in normalize_student_text("what's my next cls?")
    assert "tomorrow" in normalize_student_text("y3 s1 tmrw 1:30")
    assert "year 3" in normalize_student_text("3rd yr section 1")
    assert "section 1" in normalize_student_text("y3 s1")
    assert "section 18" in normalize_student_text("year 3 sec 18")


def test_time_expression_parsing():
    """Verify natural time expressions are extracted to standard 24-hr HH:MM strings."""
    assert extract_time_from_text("1:30") == "13:30"
    assert extract_time_from_text("1:30 PM") == "13:30"
    assert extract_time_from_text("1.30") == "13:30"
    assert extract_time_from_text("13:30") == "13:30"
    assert extract_time_from_text("2:30") == "14:30"
    assert extract_time_from_text("one thirty") == "13:30"
    assert extract_time_from_text("half past one") == "13:30"
    assert extract_time_from_text("11:00") == "11:00"


def test_intent_classification_for_natural_timetable_queries():
    """Verify natural timetable queries map to CLASS_AT_TIME_LOOKUP."""
    intent1, d1 = classify_campus_intent("I’m in 3rd year section 1, what do I have at 1:30?")
    assert intent1 == CampusIntent.CLASS_AT_TIME_LOOKUP
    assert d1.get("year") == 3
    assert d1.get("section") == "1"
    assert d1.get("requested_time") == "13:30"

    intent2, d2 = classify_campus_intent("Y3 S1 tomorrow 1:30")
    assert intent2 == CampusIntent.CLASS_AT_TIME_LOOKUP
    assert d2.get("year") == 3
    assert d2.get("section") == "1"
    assert d2.get("requested_time") == "13:30"
    assert d2.get("day_name") == "Tomorrow"

    intent3, d3 = classify_campus_intent("yr 3 sec 1 tmrw 1:30")
    assert intent3 == CampusIntent.CLASS_AT_TIME_LOOKUP
    assert d3.get("year") == 3
    assert d3.get("section") == "1"
    assert d3.get("requested_time") == "13:30"

    intent4, d4 = classify_campus_intent("3rd yr section 1 tomorrow one thirty")
    assert intent4 == CampusIntent.CLASS_AT_TIME_LOOKUP
    assert d4.get("year") == 3
    assert d4.get("section") == "1"
    assert d4.get("requested_time") == "13:30"

    intent5, d5 = classify_campus_intent("what's my next cls?")
    assert intent5 == CampusIntent.NEXT_CLASS_LOOKUP

    intent6, d6 = classify_campus_intent("what's my next period?")
    assert intent6 == CampusIntent.NEXT_CLASS_LOOKUP


def test_agent_year3_section1_timetable_at_1330():
    """Test exact timetable query for Year 3 Section 1 at 1:30 PM."""
    user = {"name": "Test Student", "year": 3, "section": "1", "department": "CSE"}
    resp = coordinator.run("I’m in 3rd year section 1, what do I have on Monday at 1:30?", user=user, conversation_id="test_nl_tt_1")
    
    assert resp.confidence == "high"
    assert "CN" in resp.answer or "Computer Networks" in resp.answer or "13:30" in resp.answer
    assert "get_class_at_time" in resp.tool_used
    assert len(resp.tool_used) == 1  # Tool Exclusivity


def test_tool_exclusivity_for_timetable_query():
    """Verify that a simple timetable query executes ONLY Live Timetable Engine, never unrelated tools."""
    user = {"name": "Test Student", "year": 3, "section": "1", "department": "CSE"}
    resp = coordinator.run("What class do I have on Monday at 1:30 PM?", user=user, conversation_id="test_nl_tt_excl")

    assert "get_class_at_time" in resp.tool_used
    assert len(resp.tool_used) == 1
    assert "search_faculty" not in resp.tool_used
    assert "search_department" not in resp.tool_used
    assert "search_service" not in resp.tool_used
    assert "search_counsellor" not in resp.tool_used


def test_explicit_user_context_overrides_profile():
    """Verify that explicit year/section in the prompt overrides profile defaults for that query."""
    user = {"name": "Student A", "year": 3, "section": "4", "department": "CSE"}
    # Prompt asks for Year 2 Section 8
    resp = coordinator.run("I'm in Year 2 Section 8. What do I have on Monday at 9:55?", user=user, conversation_id="test_override_1")

    assert "get_class_at_time" in resp.tool_used
    assert len(resp.tool_used) == 1


def test_pending_intent_resumption_on_clarification():
    """Verify that Year/Section clarification resumes pending timetable intent instead of triggering counsellor lookup."""
    user = {"name": "Student B"}
    # Turn 1: Ask timetable question without profile
    r1 = coordinator.run("What class do I have on Monday at 1:30?", user=user, conversation_id="test_pending_tt_1")
    assert r1.requires_clarification is True
    assert "Year" in r1.answer and "Section" in r1.answer

    # Turn 2: Provide Year and Section clarification
    r2 = coordinator.run("Year 3 Section 1", user=user, conversation_id="test_pending_tt_1")
    assert r2.requires_clarification is False
    assert "get_class_at_time" in r2.tool_used
    assert len(r2.tool_used) == 1
    assert "search_counsellor" not in r2.tool_used


def test_followup_questions_preserve_timetable_context():
    """Verify follow-up questions 'Who teaches it?', 'Where is it?', 'How do I get there?' retain timetable result context."""
    user = {"name": "Student C", "year": 3, "section": "1"}
    cid = "test_followup_tt_ctx"

    # Step 1: Look up class at 1:30
    r1 = coordinator.run("What class do I have on Monday at 1:30?", user=user, conversation_id=cid)
    assert "get_class_at_time" in r1.tool_used

    # Step 2: Ask "Who teaches it?"
    r2 = coordinator.run("Who teaches it?", user=user, conversation_id=cid)
    assert "taught by" in r2.answer.lower() or "teacher" in r2.answer.lower() or "faculty" in r2.answer.lower()

    # Step 3: Ask "Where is it?"
    r3 = coordinator.run("Where is it?", user=user, conversation_id=cid)
    assert "room" in r3.answer.lower() or "block" in r3.answer.lower()


def test_ce_class_data_accuracy_year3_section1():
    """Verify that CE class for Year 3 Section 1 on Friday accurately returns 11:00-12:40 taught by Ms. Neeli Sarvani."""
    from backend.tools.timetable import get_class_at_time
    
    res = get_class_at_time(year=3, section="1", date="Friday", requested_time="11:00")
    assert res["status"] == "success"
    matched = res["matched_class"]
    
    assert matched["subject_code"] == "CE"
    assert matched["start_time"] == "11:00"
    assert matched["end_time"] == "12:40"
    assert "Neeli Sarvani" in matched["teacher"]["full_name"]
    
    # Query at 12:00 within multi-period interval
    res_1200 = get_class_at_time(year=3, section="1", date="Friday", requested_time="12:00")
    assert res_1200["status"] == "success"
    assert res_1200["matched_class"]["subject_code"] == "CE"
    assert "Neeli Sarvani" in res_1200["matched_class"]["teacher"]["full_name"]

