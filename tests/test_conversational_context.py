"""Automated pytest test suite for conversational context memory, intent routing,
pending intent resumption, coreference resolution, and regression checks.
"""

import pytest
from backend.agent import CoordinatorAgent
from backend.utils.campus_entities import CampusIntent, classify_campus_intent


@pytest.fixture
def agent():
    return CoordinatorAgent()


def test_intent_classification_first_class_on_day():
    intent, details = classify_campus_intent("What is my first class tomorrow?")
    assert intent == CampusIntent.FIRST_CLASS_ON_DAY
    assert details.get("day_name") == "Tomorrow"

    intent, details = classify_campus_intent("What do I have first on Monday?")
    assert intent == CampusIntent.FIRST_CLASS_ON_DAY
    assert details.get("day_name") == "Monday"


def test_counsellor_vs_short_context_intent(agent):
    # Explicit counsellor queries MUST trigger counsellor intent
    resp = agent.run("Who is my counsellor for Year 3 Section 1?")
    assert "Assigned Counsellors" in resp.answer or "Counsellor" in resp.answer

    # Short context response when pending intent exists MUST resume pending intent, NOT counsellor lookup
    conv_id = "test_pending_resumption"
    agent.run("What is my next class?", conversation_id=conv_id)
    resp2 = agent.run("Year 3 Section 1", conversation_id=conv_id)
    assert "Assigned Counsellors" not in resp2.answer
    assert resp2.requires_clarification is False


def test_multi_turn_timetable_clarification_flow(agent):
    conv_id = "test_conv_flow_1"

    # Turn 1: Ask for first class tomorrow without profile
    resp1 = agent.run("What is my first class tomorrow?", conversation_id=conv_id)
    assert resp1.requires_clarification is True
    assert "specify your **Year**" in resp1.answer or "section" in resp1.answer.lower()

    # Turn 2: User responds with clarification "Year 3 Section 8"
    resp2 = agent.run("Year 3 Section 8", conversation_id=conv_id)
    assert resp2.requires_clarification is False
    assert "counsellor" not in resp2.answer.lower()
    assert "PC LAB" in resp2.answer or "FLAT" in resp2.answer or "first class" in resp2.answer.lower()

    # Turn 3: "Who teaches it?"
    resp3 = agent.run("Who teaches it?", conversation_id=conv_id)
    assert "taught by" in resp3.answer.lower() or "teacher" in resp3.answer.lower() or "faculty" in resp3.answer.lower()

    # Turn 4: "Where is it?"
    resp4 = agent.run("Where is it?", conversation_id=conv_id)
    assert "Room" in resp4.answer or "Block" in resp4.answer

    # Turn 5: "How do I get there?"
    resp5 = agent.run("How do I get there?", conversation_id=conv_id)
    assert "Google Maps" in resp5.answer or "Navigation" in resp5.answer or "Head to" in resp5.answer


def test_first_class_tomorrow_flow(agent):
    conv_id = "test_conv_first_class"

    # Turn 1: "What is my first class tomorrow?" without profile
    resp1 = agent.run("What is my first class tomorrow?", conversation_id=conv_id)
    assert resp1.requires_clarification is True

    # Turn 2: "Year 3 Section 1"
    resp2 = agent.run("Year 3 Section 1", conversation_id=conv_id)
    assert resp2.requires_clarification is False
    assert "first class" in resp2.answer.lower()
    assert "hod" not in resp2.answer.lower()
    assert "counsellor" not in resp2.answer.lower()


def test_authenticated_profile_priority(agent):
    user_prof = {"year": 3, "section": "8", "department": "CSE"}

    # Directly calls next_class without asking clarification
    resp = agent.run("What is my next class?", user=user_prof)
    assert resp.requires_clarification is False
    assert "SE" in resp.answer or "next class" in resp.answer.lower() or "no more classes" in resp.answer.lower()


def test_hod_regression(agent):
    resp = agent.run("Who is the HOD of CSE?")
    assert "HOD" in resp.answer or "Head" in resp.answer or "Dr." in resp.answer
