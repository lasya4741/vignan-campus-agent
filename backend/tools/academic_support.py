"""Academic support and responsibility lookup tool for VIGNAN campus agent with entity normalization."""

from typing import Any, Dict, List, Optional
from backend.supabase_client import db
from backend.utils.normalization import calculate_match_score, normalize_text
from backend.utils.campus_entities import resolve_campus_entity
from backend.tools.verification import format_source_provenance


def search_responsibility(query: str) -> Dict[str, Any]:
    """
    Search for who handles specific student/academic responsibilities, grievances, or processes.

    Examples:
        - 'Who handles placements?'
        - 'Where does the placement coordinator sit?'
        - 'Who handles revaluation?'
        - 'Who handles student grievances?'
        - 'Who handles NPTEL / slow learners?'
        - 'Where do I go for bus pass?'

    Args:
        query: Responsibility keyword, role, or process (e.g., 'placements', 'revaluation', 'grievances', 'NPTEL', 'placement coordinator').

    Returns:
        Structured response with responsible coordinators, offices, contact, room, and provenance.
    """
    all_support = db.query_table("academic_support", select_cols="*")
    all_faculty = {f["id"]: f for f in db.query_table("faculty", select_cols="id, full_name, designation, email, phone, room, block")}
    all_offices = {o["id"]: o for o in db.query_table("offices", select_cols="id, name, room, block, phone, email, purpose, description")}

    resolved_entity = resolve_campus_entity(query)
    canonical_target = resolved_entity.get("canonical_name", "") if resolved_entity else ""

    matches = []
    for s in all_support:
        score = calculate_match_score(
            query,
            [s.get("role_name"), s.get("person_name"), s.get("responsibilities"), s.get("room")]
        )
        if canonical_target and (normalize_text(canonical_target) in normalize_text(s.get("role_name", "")) or normalize_text(canonical_target) in normalize_text(s.get("responsibilities", ""))):
            score += 35
        if score > 0:
            matches.append((score, s))

    # Also search offices for matching operational purpose
    office_matches = []
    for o in all_offices.values():
        o_score = calculate_match_score(
            query,
            [o.get("name"), o.get("purpose"), o.get("description")]
        )
        if canonical_target and (normalize_text(canonical_target) in normalize_text(o.get("name", "")) or normalize_text(canonical_target) in normalize_text(o.get("purpose", ""))):
            o_score += 30
        if o_score > 0:
            office_matches.append(o)

    matches.sort(key=lambda x: x[0], reverse=True)

    results = []
    for _, s in matches:
        f_info = all_faculty.get(s.get("faculty_id"), {})
        o_info = all_offices.get(s.get("office_id"), {})

        resolved_room = s.get("room") or f_info.get("room") or o_info.get("room")
        resolved_phone = s.get("phone") or f_info.get("phone") or o_info.get("phone")
        resolved_email = s.get("email") or f_info.get("email") or o_info.get("email")
        resolved_block = f_info.get("block") or o_info.get("block") or ("N Block" if resolved_room in ["301", "310", "409"] else None)

        results.append({
            "id": s.get("id"),
            "role_name": s.get("role_name"),
            "person_name": s.get("person_name") or f_info.get("full_name"),
            "responsibilities": s.get("responsibilities"),
            "office": o_info.get("name"),
            "room": resolved_room,
            "block": resolved_block,
            "phone": resolved_phone,
            "email": resolved_email,
            "provenance": format_source_provenance(s),
        })

    # Include related office entries if direct person was not matched or as supporting context
    for o in office_matches:
        results.append({
            "id": o.get("id"),
            "role_name": f"Office: {o.get('name')}",
            "person_name": o.get("name"),
            "responsibilities": o.get("purpose") or o.get("description"),
            "office": o.get("name"),
            "room": o.get("room"),
            "block": o.get("block"),
            "phone": o.get("phone"),
            "email": o.get("email"),
            "provenance": format_source_provenance(o),
        })

    return {
        "count": len(results),
        "matches": results,
        "message": f"Found {len(results)} responsible person/office record(s)." if results else "No verified academic support record found.",
    }
