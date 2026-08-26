"""Tests for Section-Wise Counsellor flows and profile-contextual resolution."""

import pytest
from backend.agent import coordinator
from backend.tools.counsellors import search_counsellor


def test_search_counsellor_year3_section8():
    """Verify Year 3 Section 8 returns Dr. G. Balu Narasimha Rao & Mrs. Varagani Tejaswi."""
    res = search_counsellor(year=3, section="8")
    assert res["count"] == 2
    names = [m["counsellor_name"] for m in res["matches"]]
    assert any("Balu" in n for n in names)
    assert any("Tejaswi" in n for n in names)
    for m in res["matches"]:
        assert m["room"] is not None
        assert m["phone"] is not None
        # Year 3 must NOT have registration range
        assert m["registration_range_start"] is None
        assert m["registration_range_end"] is None


def test_search_counsellor_year2_section1():
    """Verify Year 2 Section 1 returns all three counsellors with ranges."""
    res = search_counsellor(year=2, section="1")
    assert res["count"] == 3
    for m in res["matches"]:
        assert m["counsellor_name"] is not None
        assert m["room"] is not None
        assert m["phone"] is not None
        assert m["registration_range_text"] is not None


def test_agent_who_is_my_counsellor_with_year_and_section_in_profile():
    """If authenticated profile contains year=3, section=8, agent answers directly."""
    user_profile = {
        "name": "Lasya Bodapati",
        "year": 3,
        "section": "8",
        "department": "CSE"
    }
    response = coordinator.run("Who is my counsellor?", user=user_profile)
    assert response.answer is not None
    assert "Balu" in response.answer or "Tejaswi" in response.answer
    assert "search_counsellor" in response.tool_used
    assert response.requires_clarification is False


def test_agent_who_is_my_counsellor_with_year_only_in_profile():
    """If authenticated profile contains year=3 but no section, agent asks for section."""
    user_profile = {
        "name": "Lasya Bodapati",
        "year": 3,
        "section": "",
        "department": "CSE"
    }
    response = coordinator.run("Who is my counsellor?", user=user_profile)
    assert "section" in response.answer.lower()
    assert response.requires_clarification is True


def test_agent_who_is_my_counsellor_with_no_profile():
    """If user asks without profile context, agent asks for year and section."""
    response = coordinator.run("Who is my counsellor?")
    assert "year and section" in response.answer.lower() or "which section" in response.answer.lower()
    assert response.requires_clarification is True


def test_agent_explicit_year3_section8_message():
    """User asks 'Year 3 Section 8' -> returns both counsellors."""
    response = coordinator.run("Year 3 Section 8")
    assert "Balu" in response.answer or "Tejaswi" in response.answer
    assert "search_counsellor" in response.tool_used


def test_agent_explicit_year2_section1_message():
    """User asks 'Year 2 Section 1' -> returns all three Year 2 Section 1 counsellors."""
    response = coordinator.run("Year 2 Section 1")
    assert "search_counsellor" in response.tool_used
    assert "4001" in response.answer or "Oqail" in response.answer or "Priya" in response.answer


def test_agent_registration_number_year3_clarification():
    """User provides registration number for Year 3 -> explains Year 3 is section-wise."""
    user_profile = {"year": 3}
    response = coordinator.run("My registration number is 4050", user=user_profile)
    assert "section" in response.answer.lower()


def test_agent_registration_number_year2_lookup():
    """User provides registration number 4005 in Year 2 -> matches Dr. Md. Oqail Ahmad."""
    user_profile = {"year": 2}
    response = coordinator.run("My registration number is 4005", user=user_profile)
    assert "Oqail" in response.answer or "4001 - 4071" in response.answer
    assert "search_counsellor" in response.tool_used
