"""Automated test suite for per-user profile context loading, profile isolation,
and timetable query resolution for different student profiles.
"""

import pytest
from backend.agent import CoordinatorAgent


@pytest.fixture
def agent():
    return CoordinatorAgent()


def test_student_a_year2_section8_profile(agent):
    """Student A: Year 2, Section 8, CSE profile test."""
    student_a = {
        "full_name": "Student A",
        "email": "student_a@vignan.ac.in",
        "year": 2,
        "section": "8",
        "department": "CSE"
    }

    # Query next class with Student A profile
    resp = agent.run("What is my next class?", user=student_a)
    assert resp.requires_clarification is False
    assert resp.answer is not None
    assert len(resp.answer) > 0


def test_student_b_year3_section4_profile(agent):
    """Student B: Year 3, Section 4, CSE profile test."""
    student_b = {
        "full_name": "Student B",
        "email": "student_b@vignan.ac.in",
        "year": 3,
        "section": "4",
        "department": "CSE"
    }

    # Query next class with Student B profile
    resp = agent.run("What is my next class?", user=student_b)
    assert resp.requires_clarification is False
    assert resp.answer is not None
    assert len(resp.answer) > 0


def test_profile_isolation_different_timetables(agent):
    """Verify Student A (Year 2 Section 8) and Student B (Year 3 Section 8) return distinct timetable schedules."""
    student_y2_s8 = {"year": 2, "section": "8", "department": "CSE"}
    student_y3_s8 = {"year": 3, "section": "8", "department": "CSE"}

    # Ask for daily timetable
    resp_y2 = agent.run("What is my timetable for Monday?", user=student_y2_s8)
    resp_y3 = agent.run("What is my timetable for Monday?", user=student_y3_s8)

    assert resp_y2.requires_clarification is False
    assert resp_y3.requires_clarification is False
    # Year 2 Section 8 schedule on Monday has subjects like EM, DS, PS
    # Year 3 Section 8 schedule on Monday has subjects like PC LAB, FLAT
    assert resp_y2.answer != resp_y3.answer


def test_cross_user_coreference_isolation(agent):
    """Verify that Student B starting a new session cannot access Student A's last timetable result via coreferences."""
    student_a = {
        "id": "user_a_123",
        "session_id": "session_student_a_001",
        "full_name": "Student A",
        "year": 3,
        "section": "4",
        "department": "CSE"
    }

    # Student A queries timetable
    resp_a = agent.run("What is my timetable for Monday?", user=student_a, conversation_id="session_student_a_001")
    assert resp_a.requires_clarification is False

    # Student B logs in with fresh session_id
    student_b = {
        "id": "user_b_456",
        "session_id": "session_student_b_002",
        "full_name": "Student B",
        "year": 2,
        "section": "8",
        "department": "CSE"
    }

    # Student B asks "Who teaches it?"
    resp_b = agent.run("Who teaches it?", user=student_b, conversation_id="session_student_b_002")
    
    # Must NOT return Student A's teacher or crash on Student A's context
    # Student B has no previous timetable result in session_student_b_002
    assert "Student A" not in resp_b.answer
    assert resp_b.answer != resp_a.answer


def test_user_switch_on_same_session_id_resets_memory(agent):
    """If a new user ID is supplied with the same session_id, agent resets stale memory."""
    user_a = {"id": "user_a_999", "year": 3, "section": "4", "department": "CSE"}
    resp1 = agent.run("What is my timetable for Monday?", user=user_a, conversation_id="shared_session_key")
    
    user_b = {"id": "user_b_888", "year": 2, "section": "8", "department": "CSE"}
    resp2 = agent.run("Who teaches it?", user=user_b, conversation_id="shared_session_key")

    # Since user_id switched, session state reset -> no previous timetable result inherited
    assert resp2.answer != resp1.answer

