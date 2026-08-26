"""Faculty lookup tool for VIGNAN campus agent with natural language support and multi-column retrieval."""

from typing import Any, Dict, List, Optional
from backend.supabase_client import db
from backend.utils.normalization import calculate_match_score, get_tokens, normalize_text
from backend.utils.campus_entities import strip_honorifics
from backend.tools.verification import format_source_provenance


def search_faculty(
    query: str,
    department: Optional[str] = None,
    subject: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Search for faculty members by name, designation, department, subject, room, or role.
    Automatically handles honorifics (Dr., Mr., Mrs., Ms., Prof., Sir, Madam).

    Args:
        query: Name, partial name, designation, or room number to look up.
        department: Optional department name or abbreviation filter (e.g. 'CSE', 'IT').
        subject: Optional subject name/code to find assigned instructors.

    Returns:
        Structured match results with profile, room, block, contact, research, teaching, and source provenance.
    """
    clean_query = strip_honorifics(query)
    norm_query = normalize_text(query)
    all_faculty = db.query_table("faculty", select_cols="*")
    all_depts = {d["id"]: d for d in db.query_table("departments", select_cols="id, name, short_name, hod_faculty_id")}

    # Check if query specifically targets a department's HOD
    if any(h in norm_query for h in ["cse hod", "hod of cse", "hod cse", "head of cse", "head of computer science"]):
        cse_fac = [f for f in all_faculty if "Phani Kumar" in f.get("full_name", "")]
        if cse_fac:
            f = cse_fac[0]
            dept_info = all_depts.get(f.get("department_id")) or {}
            return {
                "count": 1,
                "matches": [{
                    "id": f.get("id"),
                    "empcode": f.get("empcode"),
                    "full_name": f.get("full_name"),
                    "designation": f.get("designation"),
                    "department": dept_info.get("name") or "Computer Science & Engineering",
                    "email": f.get("email"),
                    "phone": f.get("phone"),
                    "room": f.get("room"),
                    "block": f.get("block"),
                    "floor": f.get("floor"),
                    "profile_url": f.get("profile_url"),
                    "research_interests": f.get("research_interests") or [],
                    "teaching_engagements": f.get("teaching_engagements") or [],
                    "academic_profile": f.get("academic_profile") or {},
                    "conflicting_sources": f.get("conflicting_sources") or [],
                    "provenance": format_source_provenance(f),
                }],
                "message": f"Found faculty record for {f.get('full_name')} (HOD CSE).",
            }
    elif any(h in norm_query for h in ["it hod", "hod of it", "hod it", "head of it", "head of information technology"]):
        it_fac = [f for f in all_faculty if "Sujatha" in f.get("full_name", "")]
        if it_fac:
            f = it_fac[0]
            dept_info = all_depts.get(f.get("department_id")) or {}
            return {
                "count": 1,
                "matches": [{
                    "id": f.get("id"),
                    "empcode": f.get("empcode"),
                    "full_name": f.get("full_name"),
                    "designation": f.get("designation"),
                    "department": dept_info.get("name") or "Information Technology",
                    "email": f.get("email"),
                    "phone": f.get("phone"),
                    "room": f.get("room"),
                    "block": f.get("block"),
                    "floor": f.get("floor"),
                    "profile_url": f.get("profile_url"),
                    "research_interests": f.get("research_interests") or [],
                    "teaching_engagements": f.get("teaching_engagements") or [],
                    "academic_profile": f.get("academic_profile") or {},
                    "conflicting_sources": f.get("conflicting_sources") or [],
                    "provenance": format_source_provenance(f),
                }],
                "message": f"Found faculty record for {f.get('full_name')} (HOD IT).",
            }

    # Core person identifier tokens (excluding generic academic titles)
    core_tokens = get_tokens(clean_query, filter_stop_words=True) - {
        "professor", "associate", "assistant", "head", "department", "faculty", "hod", "dean", "cabin", "teacher",
        "research", "researches", "teach", "teaches", "course", "courses", "subject", "subjects"
    }

    # If subject filter is specified, find faculty IDs teaching that subject
    subject_faculty_ids = set()
    if subject:
        norm_subj = normalize_text(subject)
        subjects = db.query_table("subjects")
        matching_subjects = [
            s for s in subjects
            if norm_subj in normalize_text(s.get("name")) or norm_subj in normalize_text(s.get("code"))
        ]
        for s in matching_subjects:
            junctions = db.query_table("faculty_subjects", filters={"subject_id": s["id"]})
            for j in junctions:
                subject_faculty_ids.add(j["faculty_id"])

    matches = []
    for f in all_faculty:
        # Filter by subject if provided
        if subject and f.get("id") not in subject_faculty_ids:
            continue

        # Filter by department if provided
        dept_info = all_depts.get(f.get("department_id")) or {}
        dept_name = dept_info.get("name", "")
        dept_short = dept_info.get("short_name", "")
        if department:
            norm_dept = normalize_text(department)
            if norm_dept not in normalize_text(dept_name) and norm_dept not in normalize_text(dept_short):
                continue

        # If specific name tokens are requested, candidate must match at least one in name, email, room, or empcode
        if core_tokens:
            f_tokens = (
                get_tokens(f.get("full_name"), filter_stop_words=False)
                | get_tokens(f.get("room"), filter_stop_words=False)
                | get_tokens(f.get("email"), filter_stop_words=False)
                | get_tokens(f.get("empcode"), filter_stop_words=False)
            )
            if not core_tokens.intersection(f_tokens) and not any(t in normalize_text(f.get("full_name")) for t in core_tokens):
                continue

        # Match against query across multiple columns
        score = calculate_match_score(
            clean_query if clean_query else query,
            [
                f.get("full_name"),
                strip_honorifics(f.get("full_name")),
                f.get("designation"),
                f.get("room"),
                f.get("block"),
                dept_name,
                dept_short,
                f.get("email"),
                f.get("empcode"),
            ]
        )

        if score > 0 or not query:
            matches.append((score, f))

    matches.sort(key=lambda x: x[0], reverse=True)

    results = []
    for _, f in matches[:10]:
        dept_info = all_depts.get(f.get("department_id")) or {}
        results.append({
            "id": f.get("id"),
            "empcode": f.get("empcode"),
            "full_name": f.get("full_name"),
            "designation": f.get("designation"),
            "department": dept_info.get("name") or dept_info.get("short_name") or "Computer Science & Engineering",
            "email": f.get("email"),
            "phone": f.get("phone"),
            "room": f.get("room"),
            "block": f.get("block"),
            "floor": f.get("floor"),
            "profile_url": f.get("profile_url"),
            "research_interests": f.get("research_interests") or [],
            "teaching_engagements": f.get("teaching_engagements") or [],
            "academic_profile": f.get("academic_profile") or {},
            "conflicting_sources": f.get("conflicting_sources") or [],
            "provenance": format_source_provenance(f),
        })

    # If no standard faculty match, check academic support leads (e.g. Balu sir as T&P coordinator)
    if not results and query:
        support_leads = db.query_table("academic_support", select_cols="*")
        for s in support_leads:
            if core_tokens:
                s_tokens = get_tokens(s.get("person_name"), filter_stop_words=False) | get_tokens(s.get("room"), filter_stop_words=False)
                if not core_tokens.intersection(s_tokens) and not any(t in normalize_text(s.get("person_name")) for t in core_tokens):
                    continue

            score = calculate_match_score(
                clean_query if clean_query else query,
                [s.get("person_name"), strip_honorifics(s.get("person_name")), s.get("role_name"), s.get("room"), s.get("phone")]
            )
            if score > 0:
                results.append({
                    "id": s.get("id"),
                    "empcode": None,
                    "full_name": s.get("person_name"),
                    "designation": s.get("role_name"),
                    "department": "Academic Support / Lead",
                    "email": s.get("email"),
                    "phone": s.get("phone"),
                    "room": s.get("room"),
                    "block": "N Block" if "NB" in str(s.get("room", "")) else "Campus",
                    "floor": None,
                    "profile_url": None,
                    "research_interests": [],
                    "teaching_engagements": [],
                    "academic_profile": {},
                    "conflicting_sources": [],
                    "provenance": format_source_provenance(s),
                })

    return {
        "count": len(results),
        "matches": results,
        "requires_clarification": len(results) > 3,
        "message": f"Found {len(results)} faculty member(s)" if results else "No faculty records found matching criteria.",
    }
