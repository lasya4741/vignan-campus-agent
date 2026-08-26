"""Student counsellor lookup tool for VIGNAN campus agent."""

from typing import Any, Dict, List, Optional
from backend.supabase_client import db
from backend.utils.normalization import is_reg_in_range, normalize_text, parse_registration_number
from backend.tools.verification import format_source_provenance


def search_counsellor(
    year: Optional[int] = None,
    section: Optional[str] = None,
    registration_number: Optional[str] = None,
    counsellor_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Find assigned student counsellors by academic year, section, student registration number, or name.

    Args:
        year: Academic year of study (e.g., 1, 2, 3, 4).
        section: Section identifier (e.g., '1', '2', '3', 'A', 'B').
        registration_number: Student roll / registration number (e.g., '4005', '241FA04015').
        counsellor_name: Optional direct counsellor name search.

    Returns:
        Structured counsellor allocation record including room, phone, section, and roll range.
    """
    all_counsellors = db.query_table("counsellors", select_cols="*")
    all_faculty = {f["id"]: f for f in db.query_table("faculty", select_cols="id, full_name, designation, email, phone, room, block, floor")}

    norm_reg = parse_registration_number(registration_number) if registration_number else None
    norm_sec = normalize_text(section) if section else None
    norm_name = normalize_text(counsellor_name) if counsellor_name else None

    matches = []
    for c in all_counsellors:
        f_info = all_faculty.get(c.get("faculty_id"), {})
        
        # Match by registration number range
        if norm_reg:
            r_start = c.get("registration_range_start")
            r_end = c.get("registration_range_end")
            # If section/year specified, also require matching section/year
            if is_reg_in_range(norm_reg, r_start, r_end):
                if year is not None and c.get("year") != year:
                    continue
                if norm_sec and normalize_text(c.get("section")) != norm_sec:
                    continue
                matches.append((100, c))
            continue

        # If both year and section are specified -> strict match
        if year is not None and norm_sec:
            if c.get("year") == year and normalize_text(c.get("section")) == norm_sec:
                matches.append((100, c))
            continue

        score = 0
        if year is not None and c.get("year") == year:
            score += 10
        if norm_sec and norm_sec == normalize_text(c.get("section")):
            score += 15
        if norm_name:
            c_name = normalize_text(c.get("counsellor_name"))
            f_name = normalize_text(f_info.get("full_name"))
            if norm_name in c_name or norm_name in f_name:
                score += 20

        if score > 0:
            matches.append((score, c))

    matches.sort(key=lambda x: x[0], reverse=True)

    results = []
    for _, c in matches:
        f_info = all_faculty.get(c.get("faculty_id"), {})
        results.append({
            "id": c.get("id"),
            "counsellor_name": c.get("counsellor_name") or f_info.get("full_name"),
            "faculty_id": c.get("faculty_id"),
            "academic_year": c.get("academic_year"),
            "year": c.get("year"),
            "section": c.get("section"),
            "phone": c.get("phone") or f_info.get("phone"),
            "room": c.get("room") or f_info.get("room"),
            "block": f_info.get("block") or ("N Block" if (c.get("room") or "").startswith("NB-") else None),
            "floor": f_info.get("floor"),
            "registration_range_start": c.get("registration_range_start"),
            "registration_range_end": c.get("registration_range_end"),
            "registration_range_text": c.get("registration_range_text"),
            "provenance": format_source_provenance(c),
        })

    if norm_reg and not results:
        message = f"No verified counsellor mapping found for registration number '{norm_reg}'."
    elif not results:
        message = "No counsellor records found matching criteria."
    else:
        message = f"Found {len(results)} matching counsellor record(s)."

    return {
        "count": len(results),
        "matches": results,
        "query_reg_no": norm_reg,
        "message": message,
    }
