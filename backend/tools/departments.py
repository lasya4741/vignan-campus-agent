"""Department search tool for VIGNAN campus agent with natural alias resolution and multi-column retrieval."""

import re
from typing import Any, Dict, List, Optional
from backend.supabase_client import db
from backend.utils.normalization import calculate_match_score, normalize_text
from backend.utils.campus_entities import resolve_campus_entity
from backend.tools.verification import format_source_provenance


def search_department(query: str) -> Dict[str, Any]:
    """
    Search for departments by name, abbreviation (e.g. 'CSE', 'ECE', 'IT'), building block, or floor.

    Args:
        query: Department name, abbreviation, building block, or natural phrasing (e.g. 'IT', 'U Block', 'CSE', 'Which block has IT', 'Who is the HOD of CSE').

    Returns:
        Structured department details including block, floor, HOD, and provenance.
    """
    norm_query = normalize_text(query)
    all_depts = db.query_table("departments", select_cols="*")
    all_faculty = {f["id"]: f for f in db.query_table("faculty", select_cols="id, full_name, designation, email, phone, room, profile_url")}

    # Detect if query is specifically asking about a building block with word boundaries
    requested_block = None
    for b in ["u block", "n block", "h block", "a block", "textile block", "pharmacy block"]:
        if re.search(rf"\b{re.escape(b)}\b", norm_query):
            requested_block = b
            break

    # Check entity resolution
    entity_meta = resolve_campus_entity(query)
    canonical_target = entity_meta.get("canonical_name", "") if entity_meta else ""
    short_target = entity_meta.get("short_name", "") if entity_meta else ""

    # Priority distinction between CSE Core and ACSE
    is_acse_query = "acse" in norm_query or "advanced computer" in norm_query or "advanced cse" in norm_query

    matches = []
    for d in all_depts:
        d_name_norm = normalize_text(d.get("name"))
        d_short_norm = normalize_text(d.get("short_name"))
        d_block = normalize_text(d.get("block"))

        # If user asked for a specific block and not a department, filter
        if requested_block and not canonical_target and requested_block != d_block:
            continue

        score = calculate_match_score(
            query,
            [
                d.get("name"),
                d.get("short_name"),
                d.get("block"),
                d.get("floor_information"),
                d.get("description"),
            ]
        )

        # Handle CSE Core vs ACSE vs IT distinctions
        if is_acse_query:
            if "advanced" in d_name_norm or d_short_norm == "acse":
                score += 100
        else:
            # Regular CSE / Computer Science Engineering query -> Boost CSE Core
            if any(w in norm_query for w in ["computer science", "cse", "cs dept", "cse core", "cse department"]):
                if "core" in d_name_norm or d_short_norm == "cse":
                    score += 60
                elif "advanced" in d_name_norm:
                    score -= 40

        # Bonus if matching resolved canonical entity
        if canonical_target and (normalize_text(canonical_target) in d_name_norm or d_name_norm in normalize_text(canonical_target)):
            score += 50
        if short_target and normalize_text(short_target) == d_short_norm:
            score += 45

        if requested_block and requested_block == d_block:
            score += 30

        if score > 0:
            matches.append((score, d))

    matches.sort(key=lambda x: x[0], reverse=True)

    results = []
    for _, d in matches:
        hod_id = d.get("hod_faculty_id")
        hod_info = all_faculty.get(hod_id) if hod_id else {}
        results.append({
            "id": d.get("id"),
            "name": d.get("name"),
            "short_name": d.get("short_name"),
            "description": d.get("description"),
            "block": d.get("block"),
            "floor_information": d.get("floor_information"),
            "hod": {
                "id": hod_info.get("id"),
                "name": hod_info.get("full_name"),
                "designation": hod_info.get("designation") or "Professor & Head of Department",
                "room": hod_info.get("room"),
                "email": hod_info.get("email"),
                "phone": hod_info.get("phone"),
                "profile_url": hod_info.get("profile_url"),
            } if hod_info and hod_info.get("full_name") else None,
            "provenance": format_source_provenance(d),
        })

    return {
        "count": len(results),
        "matches": results,
        "message": f"Found {len(results)} department(s)" if results else "No department records found matching criteria.",
    }
