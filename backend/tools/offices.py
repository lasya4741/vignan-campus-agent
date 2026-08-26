"""Campus office lookup tool for VIGNAN campus agent with entity normalization."""

from typing import Any, Dict, List, Optional
from backend.supabase_client import db
from backend.utils.normalization import calculate_match_score, normalize_text
from backend.utils.campus_entities import resolve_campus_entity
from backend.tools.verification import format_source_provenance


def search_office(query: str) -> Dict[str, Any]:
    """
    Search for campus administrative and student service offices.
    Understands aliases like 'fees', 'pay fees', 'accounts', 'bus pass', 'exam cell'.

    Args:
        query: Office name, purpose, building block, or natural action (e.g., 'Finance', 'Where to pay fees', 'Admin Office').

    Returns:
        Structured office details with room, block, floor, contact info, and provenance.
    """
    all_offices = db.query_table("offices")

    resolved_entity = resolve_campus_entity(query)
    canonical_target = resolved_entity.get("canonical_name", "") if resolved_entity else ""

    matches = []
    for o in all_offices:
        score = calculate_match_score(
            query,
            [o.get("name"), o.get("purpose"), o.get("room"), o.get("block"), o.get("description")]
        )
        if canonical_target and (normalize_text(canonical_target) in normalize_text(o.get("name", "")) or normalize_text(o.get("name", "")) in normalize_text(canonical_target)):
            score += 40
        if score > 0:
            matches.append((score, o))

    matches.sort(key=lambda x: x[0], reverse=True)

    results = []
    for _, o in matches:
        results.append({
            "id": o.get("id"),
            "name": o.get("name"),
            "purpose": o.get("purpose"),
            "room": o.get("room"),
            "block": o.get("block"),
            "floor": o.get("floor"),
            "phone": o.get("phone"),
            "email": o.get("email"),
            "description": o.get("description"),
            "provenance": format_source_provenance(o),
        })

    return {
        "count": len(results),
        "matches": results,
        "message": f"Found {len(results)} office(s)" if results else "No office records found matching criteria.",
    }
