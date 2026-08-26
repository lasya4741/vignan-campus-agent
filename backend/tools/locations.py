"""Campus physical location lookup tool for VIGNAN campus agent with entity normalization."""

from typing import Any, Dict, List, Optional
from backend.supabase_client import db
from backend.utils.normalization import calculate_match_score, normalize_room, normalize_text
from backend.utils.campus_entities import resolve_campus_entity
from backend.tools.verification import format_source_provenance


def get_location(
    query: str,
    block: Optional[str] = None,
    room: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Look up physical campus locations, gates, buildings, blocks, floors, rooms, and facilities.

    Args:
        query: Location name, landmark, or natural phrasing (e.g., 'Main Gate', 'Finance', 'U Block', 'Pharmacy Block', 'MHP', '409').
        block: Optional building block filter (e.g., 'U Block', 'A Block').
        room: Optional exact room number/identifier (preserved verbatim).

    Returns:
        Structured location hierarchy with block, floor, room, coordinates, and provenance.
    """
    norm_block = normalize_text(block) if block else None
    norm_room = normalize_room(room) if room else None

    resolved_entity = resolve_campus_entity(query)
    canonical_target = resolved_entity.get("canonical_name", "") if resolved_entity else ""

    all_locs = db.query_table("locations", select_cols="*")
    locs_by_id = {l["id"]: l for l in all_locs}

    matches = []
    for loc in all_locs:
        l_name = normalize_text(loc.get("name"))
        l_block = normalize_text(loc.get("block"))
        l_room = normalize_room(loc.get("room"))

        # Exact room match filter if specified
        if norm_room and norm_room.lower() != l_room.lower():
            continue

        # Block filter if specified
        if norm_block and norm_block not in l_block and norm_block not in l_name:
            continue

        score = calculate_match_score(
            query,
            [loc.get("name"), loc.get("location_type"), loc.get("block"), loc.get("room"), loc.get("description")]
        )
        if canonical_target and (normalize_text(canonical_target) in l_name or l_name in normalize_text(canonical_target)):
            score += 35
        if score > 0:
            matches.append((score, loc))

    matches.sort(key=lambda x: x[0], reverse=True)

    results = []
    for _, loc in matches[:10]:
        parent_id = loc.get("parent_location_id")
        parent_info = locs_by_id.get(parent_id, {}) if parent_id else {}
        results.append({
            "id": loc.get("id"),
            "name": loc.get("name"),
            "location_type": loc.get("location_type"),
            "block": loc.get("block"),
            "floor": loc.get("floor"),
            "room": loc.get("room"),
            "description": loc.get("description"),
            "parent_location": {
                "name": parent_info.get("name"),
                "block": parent_info.get("block"),
                "floor": parent_info.get("floor"),
            } if parent_info else None,
            "provenance": format_source_provenance(loc),
        })

    return {
        "count": len(results),
        "matches": results,
        "message": f"Found {len(results)} location(s)." if results else "No verified campus location records found matching query.",
    }
