"""Tests for general natural-language campus intelligence, intent classification,
entity normalization, paraphrased queries, out-of-scope detection, and multi-tool routing.
"""

import pytest
from backend.agent import coordinator
from backend.utils.campus_entities import (
    CampusIntent,
    OUT_OF_SCOPE_REFUSAL,
    classify_campus_intent,
    is_out_of_scope,
    resolve_campus_entity,
    strip_honorifics,
)


def test_entity_normalization_helpers():
    """Verify alias mapping and honorific stripping."""
    assert strip_honorifics("Dr. Balu sir") == "Balu"
    assert strip_honorifics("Prof. Jyothi Madam") == "Jyothi"
    assert strip_honorifics("Mrs. Varagani Tejaswi") == "Varagani Tejaswi"
    assert strip_honorifics("Mr. Hitendra Singh") == "Hitendra Singh"

    mhp = resolve_campus_entity("where is MHP canteen?")
    assert mhp is not None
    assert mhp["canonical_name"] == "MHP / Main Canteen"

    it = resolve_campus_entity("Which block is IT in?")
    assert it is not None
    assert it["short_name"] == "IT"

    fees = resolve_campus_entity("Where can I pay my fees?")
    assert fees is not None
    assert fees["canonical_name"] == "Finance & Accounts Office"


def test_out_of_scope_detection():
    """Verify non-campus inquiries are flagged as out of scope."""
    out_of_scope_queries = [
        "Write me a Python program to sort a list.",
        "Who won yesterday's cricket match?",
        "What is quantum physics?",
        "Tell me a joke.",
        "Who is the president of the USA?",
        "What is machine learning?",
    ]
    for q in out_of_scope_queries:
        assert is_out_of_scope(q), f"Expected '{q}' to be classified as out of scope."
        res = coordinator.run(q)
        assert OUT_OF_SCOPE_REFUSAL in res.answer


def test_clarification_on_ambiguous_office():
    """Verify 'Where is the office?' asks for clarification."""
    intent, details = classify_campus_intent("Where is the office?")
    assert intent == CampusIntent.CLARIFICATION_REQUIRED

    res = coordinator.run("Where is the office?")
    assert res.requires_clarification is True
    assert "Which office" in res.answer or "Finance" in res.answer


def test_paraphrased_canteen_and_mhp():
    """Verify 'Where is MHP?', 'Where is the main canteen?', 'Where can I get food?', 'I need lunch' resolve to Canteen/MHP."""
    queries = [
        "Where is MHP?",
        "Where is the main canteen?",
        "Where can I get food?",
        "Where is the main cafeteria?",
        "I need lunch.",
    ]
    for q in queries:
        res = coordinator.run(q)
        assert res.answer, f"Empty answer for '{q}'"
        assert any(term in res.answer.lower() for term in ["mhp", "canteen", "cafeteria", "food", "lunch", "h block", "n block"]), (
            f"Failed for '{q}': {res.answer}"
        )


def test_paraphrased_finance_and_fees():
    """Verify 'Where is Finance?', 'Where can I pay fees?', 'Where is the fees section?' resolve to Finance Office."""
    queries = [
        "Where is Finance?",
        "Where is the Finance Office?",
        "Where can I pay my fees?",
        "Where is the fees section?",
        "Which floor is Finance on?",
    ]
    for q in queries:
        res = coordinator.run(q)
        assert "finance" in res.answer.lower() or "a block" in res.answer.lower(), f"Failed for '{q}': {res.answer}"


def test_paraphrased_xerox_and_printing():
    """Verify 'Where can I Xerox?', 'Where can I photocopy?', 'Where is the copy shop?', 'I need to print my assignment' resolve to Xerox."""
    queries = [
        "Where can I Xerox?",
        "Where can I photocopy?",
        "Where is the copy shop?",
        "I need to print my assignment.",
        "Is there a Xerox shop near A Block?",
    ]
    for q in queries:
        res = coordinator.run(q)
        assert "xerox" in res.answer.lower() or "print" in res.answer.lower() or "a block" in res.answer.lower(), f"Failed for '{q}': {res.answer}"


def test_paraphrased_department_queries():
    """Verify department queries in natural phrasing."""
    it_res = coordinator.run("Where is IT?")
    assert "information technology" in it_res.answer.lower() or "u block" in it_res.answer.lower() or "a block" in it_res.answer.lower()

    it_block_res = coordinator.run("Which block has IT?")
    assert "u block" in it_block_res.answer.lower() or "a block" in it_block_res.answer.lower()

    cse_res = coordinator.run("What building is CSE in?")
    assert "n block" in cse_res.answer.lower() or "u block" in cse_res.answer.lower() or "computer science" in cse_res.answer.lower()

    u_block_depts = coordinator.run("Which departments are in U Block?")
    assert "u block" in u_block_depts.answer.lower()
    assert any(term in u_block_depts.answer.lower() for term in ["information technology", "mechanical", "civil", "biotechnology", "computer science"])


def test_faculty_honorific_and_role_queries():
    """Verify faculty inquiries with honorifics like 'Balu sir' and 'Dr. Balu'."""
    balu_res = coordinator.run("Where is Balu sir?")
    assert "balu" in balu_res.answer.lower()
    assert "409" in balu_res.answer.lower() or "nb-409" in balu_res.answer.lower()

    placement_res = coordinator.run("Who handles placements?")
    assert "placement" in placement_res.answer.lower() or "balu" in placement_res.answer.lower() or "venkatesh" in placement_res.answer.lower()

    seat_res = coordinator.run("Where does the placement coordinator sit?")
    assert any(loc in seat_res.answer.lower() for loc in ["409", "nb-409", "tp-101", "n block", "u block", "placement"])


def test_transport_and_bus_pass_queries():
    """Verify bus pass and transport queries."""
    res1 = coordinator.run("Where is the transport office?")
    assert "transport" in res1.answer.lower() or "main gate" in res1.answer.lower()

    res2 = coordinator.run("Where can I get my bus pass?")
    assert "transport" in res2.answer.lower() or "bus pass" in res2.answer.lower() or "main gate" in res2.answer.lower()


def test_location_and_block_queries():
    """Verify queries for specific campus blocks like Pharmacy Block."""
    pharm_res = coordinator.run("Where is Pharmacy?")
    assert "pharmacy" in pharm_res.answer.lower()

    pharm_block_res = coordinator.run("Where is the Pharmacy Block?")
    assert "pharmacy" in pharm_block_res.answer.lower()


def test_live_recommendation_and_queue():
    """Verify 'Which Xerox should I use?' and 'Which Xerox has the shortest queue?'."""
    rec_res = coordinator.run("Which Xerox has the shortest queue?")
    assert "xerox" in rec_res.answer.lower()
    assert "queue" in rec_res.answer.lower() or "status" in rec_res.answer.lower() or "recommended" in rec_res.answer.lower()


def test_navigation_queries():
    """Verify natural navigation phrases."""
    nav_res = coordinator.run("Take me to MHP.")
    assert nav_res.answer is not None

    nav_res2 = coordinator.run("How do I get to Finance?")
    assert nav_res2.answer is not None


def test_campus_general_info_queries():
    """Verify general campus questions like department counts."""
    dept_count_res = coordinator.run("How many departments are there?")
    assert "department" in dept_count_res.answer.lower()
