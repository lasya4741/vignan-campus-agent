"""Subject and course lookup tool for VIGNAN campus agent."""

from typing import Any, Dict, List, Optional
from backend.supabase_client import db
from backend.utils.normalization import calculate_match_score, normalize_text
from backend.tools.verification import format_source_provenance


def search_subject(query: str) -> Dict[str, Any]:
    """
    Search for subjects, course codes, and their assigned faculty instructors.

    Args:
        query: Subject name or course code (e.g., 'DBMS', 'Data Structures', 'CS201').

    Returns:
        Structured subject details along with verified teaching faculty list.
    """
    all_subjects = db.query_table("subjects", select_cols="*, departments(name, short_name)")

    matches = []
    for s in all_subjects:
        dept_info = s.get("departments") or {}
        score = calculate_match_score(
            query,
            [s.get("name"), s.get("code"), dept_info.get("name"), dept_info.get("short_name")]
        )
        if score > 0:
            matches.append((score, s))

    matches.sort(key=lambda x: x[0], reverse=True)

    results = []
    for _, s in matches[:10]:
        # Query assigned instructors from junction table
        junctions = db.query_table("faculty_subjects", filters={"subject_id": s["id"]})
        faculty_list = []
        for j in junctions:
            f_records = db.query_table("faculty", filters={"id": j["faculty_id"]})
            if f_records:
                f = f_records[0]
                faculty_list.append({
                    "id": f.get("id"),
                    "full_name": f.get("full_name"),
                    "designation": f.get("designation"),
                    "room": f.get("room"),
                    "block": f.get("block"),
                    "email": f.get("email"),
                })

        dept_info = s.get("departments") or {}
        results.append({
            "id": s.get("id"),
            "name": s.get("name"),
            "code": s.get("code"),
            "department": dept_info.get("name") or dept_info.get("short_name"),
            "instructors": faculty_list,
            "provenance": format_source_provenance(s),
        })

    return {
        "count": len(results),
        "matches": results,
        "message": f"Found {len(results)} subject(s)" if results else "No subject records found matching criteria.",
    }
