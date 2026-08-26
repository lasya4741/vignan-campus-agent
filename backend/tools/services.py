"""Campus services search tool for VIGNAN campus agent with natural language entity normalization."""

from typing import Any, Dict, List, Optional
from backend.supabase_client import db
from backend.utils.normalization import calculate_match_score, normalize_text
from backend.utils.campus_entities import resolve_campus_entity
from backend.tools.verification import format_source_provenance


def search_service(query: str = "", category: Optional[str] = None) -> Dict[str, Any]:
    """
    Search for campus utility services (xerox, printing, stationery, canteen, transport, medical, library, pharmacy).
    Understands natural language service needs (e.g., 'print my assignment', 'where is MHP', 'lunch', 'bus pass').

    Args:
        query: Service keyword or name (e.g. 'xerox', 'color print', 'canteen near H Block', 'bus pass', 'MHP', 'food').
        category: Optional category filter ('xerox', 'printing', 'stationery', 'canteen', 'transport', 'medical', 'library', 'pharmacy', 'other').

    Returns:
        Structured list of matching services with location, offerings, and provenance.
    """
    norm_cat = normalize_text(category) if category else None

    # Resolve natural language entity (e.g., "MHP", "lunch", "photocopy", "bus pass")
    resolved_entity = resolve_campus_entity(query) if query else None
    if resolved_entity:
        if not norm_cat and resolved_entity.get("category") in ["canteen", "xerox", "transport"]:
            norm_cat = resolved_entity.get("category")

    all_services = db.query_table("services", select_cols="*")
    all_locs = {l["id"]: l for l in db.query_table("locations", select_cols="id, name, block, floor, room, description")}

    matches = []
    for s in all_services:
        s_cat = normalize_text(s.get("category"))
        s_offered = s.get("services_offered") or []
        offered_str = " ".join([normalize_text(str(x)) for x in s_offered]) if isinstance(s_offered, list) else normalize_text(str(s_offered))

        loc_info = all_locs.get(s.get("location_id"), {})
        loc_name = normalize_text(loc_info.get("name"))
        loc_block = normalize_text(loc_info.get("block"))

        # Category filter check
        if norm_cat and norm_cat != s_cat and norm_cat not in offered_str and norm_cat not in normalize_text(s.get("name")):
            continue

        if query:
            score = calculate_match_score(
                query,
                [
                    s.get("name"),
                    s.get("category"),
                    s.get("description"),
                    offered_str,
                    loc_name,
                    loc_block,
                ]
            )
            # Boost if matching resolved canonical entity
            if resolved_entity and resolved_entity.get("canonical_name"):
                if normalize_text(resolved_entity["canonical_name"]) in normalize_text(s.get("name")) or normalize_text(s.get("name")) in normalize_text(resolved_entity["canonical_name"]):
                    score += 40
        else:
            score = 1

        if score > 0:
            matches.append((score, s))

    matches.sort(key=lambda x: x[0], reverse=True)

    results = []
    for _, s in matches[:10]:
        loc_info = all_locs.get(s.get("location_id"), {})
        results.append({
            "id": s.get("id"),
            "name": s.get("name"),
            "category": s.get("category"),
            "description": s.get("description"),
            "location_id": s.get("location_id"),
            "location": {
                "name": loc_info.get("name"),
                "block": loc_info.get("block"),
                "floor": loc_info.get("floor"),
                "room": loc_info.get("room"),
                "description": loc_info.get("description"),
            } if loc_info else None,
            "services_offered": s.get("services_offered") or [],
            "provenance": format_source_provenance(s),
        })

    return {
        "count": len(results),
        "matches": results,
        "message": f"Found {len(results)} service(s)." if results else "No verified campus services found matching query.",
    }
