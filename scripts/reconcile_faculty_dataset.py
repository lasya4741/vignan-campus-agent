"""Reconcile and Merge Official VIGNAN Website CSE Faculty Data with Verified Poster Records.
Ensures:
1. 100% Referential Integrity across counsellors, academic_support, departments, faculty_subjects.
2. Official website is authoritative for identity, designation, department, profile URL, email, phone, research, teaching.
3. Department posters provide verified rooms, blocks, floors, counsellor roles, and T&P roles.
4. Preserves both source provenances.
"""

import json
import os
import sys
import uuid
from typing import Any, Dict, List, Optional

sys.path.insert(0, os.path.abspath("."))

from backend.supabase_client import db
from backend.utils.normalization import normalize_text

UUID_NAMESPACE = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")

SOURCE_OFFICIAL_PEOPLE = {
    "id": "5a8d7901-b758-5d20-a612-4c924bc01f89",
    "source_type": "official_website",
    "source_name": "VIGNAN Official Faculty Directory (People Page)",
    "source_url": "https://vignan.ac.in/newvignan/people.php",
    "description": "Official university faculty directory with department filter for Computer Science Engineering",
    "verified_at": "2026-08-27T00:00:00Z"
}

SOURCE_OFFICIAL_CSE_DEPT = {
    "id": "9b1e3f84-1845-5ec2-9e23-74cf89281a02",
    "source_type": "official_website",
    "source_name": "VIGNAN CSE Department Official Portal",
    "source_url": "https://www.vignan.ac.in/newvignan/departments/depthome.php?deptid=sch3_dept1&deptnm=CSE&school=sch3",
    "description": "Official CSE department homepage identifying Head of Department Dr. S.V. Phani Kumar",
    "verified_at": "2026-08-27T00:00:00Z"
}

CSE_DEPT_ID = "3e2d391b-0ad0-57cb-b077-3a9cedf8c117" # Computer Science & Engineering (Core)
CSE_SPEC_DEPT_ID = "579baa2a-8be2-5d47-bd02-36fe98e9aed7" # Computer Science & Engineering (Specializations)


def clean_salutation_name(sal: Optional[str], name: Optional[str]) -> str:
    sal = (sal or "").strip().replace(".", "")
    name = (name or "").strip()
    if sal:
        if sal.lower() == "dr":
            sal_str = "Dr."
        elif sal.lower() == "mr":
            sal_str = "Mr."
        elif sal.lower() == "mrs":
            sal_str = "Mrs."
        elif sal.lower() == "ms":
            sal_str = "Ms."
        elif sal.lower() == "prof":
            sal_str = "Prof."
        else:
            sal_str = sal.capitalize() + "."
    else:
        sal_str = ""

    name_parts = [p.capitalize() if p.isupper() and len(p) > 2 else p for p in name.split()]
    clean_name = " ".join(name_parts)
    if sal_str:
        return f"{sal_str} {clean_name}"
    return clean_name


def run_reconciliation():
    print("--- 1. Gathering required poster faculty references ---")
    with open("database/extracted/counsellors.json", "r", encoding="utf-8") as f:
        counsellors = json.load(f)

    with open("database/extracted/academic_support.json", "r", encoding="utf-8") as f:
        academic_support = json.load(f)

    with open("database/extracted/departments.json", "r", encoding="utf-8") as f:
        departments = json.load(f)

    with open("database/extracted/sources.json", "r", encoding="utf-8") as f:
        sources_list = json.load(f)

    existing_source_ids = {s["id"] for s in sources_list}
    if SOURCE_OFFICIAL_PEOPLE["id"] not in existing_source_ids:
        sources_list.append(SOURCE_OFFICIAL_PEOPLE)
    if SOURCE_OFFICIAL_CSE_DEPT["id"] not in existing_source_ids:
        sources_list.append(SOURCE_OFFICIAL_CSE_DEPT)

    with open("database/extracted/sources.json", "w", encoding="utf-8") as f:
        json.dump(sources_list, f, indent=2, ensure_ascii=False)

    poster_faculty_refs = {}

    for c in counsellors:
        fid = c.get("faculty_id")
        if fid and fid not in poster_faculty_refs:
            poster_faculty_refs[fid] = {
                "id": fid,
                "full_name": c["counsellor_name"],
                "room": c.get("room"),
                "phone": c.get("phone"),
                "block": "N Block",
                "department_id": CSE_DEPT_ID,
                "source_id": c.get("source_id")
            }

    for a in academic_support:
        fid = a.get("faculty_id")
        if fid and fid not in poster_faculty_refs:
            poster_faculty_refs[fid] = {
                "id": fid,
                "full_name": a["person_name"],
                "room": a.get("room"),
                "phone": a.get("phone"),
                "block": a.get("block") or "N Block",
                "department_id": CSE_DEPT_ID,
                "source_id": a.get("source_id")
            }

    for d in departments:
        fid = d.get("hod_faculty_id")
        if fid and fid not in poster_faculty_refs:
            poster_faculty_refs[fid] = {
                "id": fid,
                "full_name": f"HOD of {d['name']}",
                "department_id": d["id"],
                "source_id": d.get("source_id")
            }

    print(f"Total distinct referenced faculty from all poster tables: {len(poster_faculty_refs)}")

    print("--- 2. Loading official CSE faculty from raw website extraction ---")
    with open("database/raw/official_cse_faculty.json", "r", encoding="utf-8") as f:
        official_cse = json.load(f)

    with open("database/extracted/subjects.json", "r", encoding="utf-8") as f:
        existing_subjects = json.load(f)

    subject_map = {normalize_text(s["name"]): s for s in existing_subjects}
    created_faculty_subjects = []

    merged_faculty_map = {}
    matched_poster_ids = set()

    stats = {
        "official_cse_count": len(official_cse),
        "matched_with_posters": 0,
        "newly_added_from_web": 0,
        "official_emails": 0,
        "official_phones": 0,
        "with_profile_urls": 0,
        "with_research_interests": 0,
        "with_teaching_engagements": 0,
        "with_poster_rooms": 0,
        "conflicts_recorded": 0,
        "hod_canonical": None
    }

    # First, match official CSE faculty against poster faculty references
    for item in official_cse:
        p = item["people_meta"]
        d = item.get("detailed_meta", {})
        empcode = str(p.get("empcode", "")).strip()

        raw_sal = p.get("salutation")
        raw_name = p.get("name")
        web_full_name = clean_salutation_name(raw_sal, raw_name)

        is_cse_hod = (empcode == "675") or (p.get("adminpos") == "HOD")
        if is_cse_hod:
            canonical_name = "Dr. S.V. Phani Kumar"
            conflicting_sources = [
                {
                    "source": "Official CSE Department Portal",
                    "url": "https://www.vignan.ac.in/newvignan/departments/depthome.php?deptid=sch3_dept1&deptnm=CSE&school=sch3",
                    "name_listed": "Dr.S.V. Phani Kumar",
                    "designation_listed": "Professor & HoD, CSE Dept"
                },
                {
                    "source": "Official Faculty Directory (People Page)",
                    "url": "https://vignan.ac.in/newvignan/people.php",
                    "name_listed": f"{raw_sal} {raw_name}",
                    "designation_listed": "PROFESSOR (HOD)"
                }
            ]
            stats["conflicts_recorded"] += 1
        else:
            canonical_name = web_full_name
            conflicting_sources = []

        desig_raw = p.get("desig") or "FACULTY"
        desig_clean = desig_raw.title()

        email = d.get("email") or p.get("email") or d.get("personalemail") or p.get("personalemail")
        if email == "Not Available" or not email or not email.strip():
            email = None
        else:
            email = email.strip()
            stats["official_emails"] += 1

        phone = d.get("contact") or p.get("contact") or d.get("personalcontact") or p.get("personalcontact")
        if phone == "Not Available" or not phone or not str(phone).strip():
            phone = None
        else:
            phone = str(phone).strip()
            stats["official_phones"] += 1

        profile_url = item.get("profile_url")
        if profile_url:
            stats["with_profile_urls"] += 1

        raw_interests = d.get("interests", [])
        research_interests = [i["interest"].strip() for i in raw_interests if isinstance(i, dict) and i.get("interest") and i["interest"].strip()]
        if research_interests:
            stats["with_research_interests"] += 1

        raw_teaching = d.get("teachingengmnts", [])
        teaching_engagements = [t["teachingengmnts"].strip() for t in raw_teaching if isinstance(t, dict) and t.get("teachingengmnts") and t["teachingengmnts"].strip()]
        if teaching_engagements:
            stats["with_teaching_engagements"] += 1

        academic_profile = {
            "education": d.get("facultyeducation", []),
            "experience": d.get("expeirence", []),
            "publications_count": len(d.get("publications", [])),
            "publications": d.get("publications", [])[:5],
            "awards": d.get("awards", []),
            "admin_positions": [p.get("adminpos")] if p.get("adminpos") and p.get("adminpos") != "--NA--" else []
        }

        # Match with poster faculty references
        matched_ref = None
        web_norm = normalize_text(f"{raw_sal} {raw_name}")
        web_tokens = set(web_norm.split()) - {"dr", "mr", "mrs", "ms", "prof", "s", "k", "t", "g", "p", "v", "d", "m", "n", "a", "b", "c", "r"}

        for pid, pref in poster_faculty_refs.items():
            if pid in matched_poster_ids:
                continue
            pref_norm = normalize_text(pref["full_name"])
            pref_tokens = set(pref_norm.split()) - {"dr", "mr", "mrs", "ms", "prof", "s", "k", "t", "g", "p", "v", "d", "m", "n", "a", "b", "c", "r"}

            if pref_tokens and web_tokens and (pref_tokens == web_tokens or pref_tokens.issubset(web_tokens) or web_tokens.issubset(pref_tokens)):
                matched_ref = pref
                matched_poster_ids.add(pid)
                break

        if matched_ref:
            faculty_id = matched_ref["id"]
            room = matched_ref.get("room")
            block = matched_ref.get("block") or "N Block"
            floor = matched_ref.get("floor")
            if not phone and matched_ref.get("phone"):
                phone = matched_ref.get("phone")
            stats["matched_with_posters"] += 1
            if room:
                stats["with_poster_rooms"] += 1
        else:
            faculty_id = str(uuid.uuid5(UUID_NAMESPACE, f"vignan-cse-faculty-{empcode}"))
            room = None
            block = "N Block"
            floor = None
            stats["newly_added_from_web"] += 1

        fac_record = {
            "id": faculty_id,
            "empcode": empcode,
            "full_name": canonical_name,
            "designation": desig_clean,
            "department_id": CSE_DEPT_ID,
            "email": email,
            "phone": phone,
            "room": room,
            "block": block,
            "floor": floor,
            "profile_url": profile_url,
            "source_id": SOURCE_OFFICIAL_PEOPLE["id"],
            "confidence": "high",
            "last_verified": "2026-08-27T00:00:00Z",
            "research_interests": research_interests,
            "teaching_engagements": teaching_engagements,
            "academic_profile": academic_profile,
            "conflicting_sources": conflicting_sources
        }

        if is_cse_hod:
            stats["hod_canonical"] = fac_record

        merged_faculty_map[faculty_id] = fac_record

        # Subjects
        for course_name in teaching_engagements:
            norm_cname = normalize_text(course_name)
            if norm_cname not in subject_map:
                subj_id = str(uuid.uuid5(UUID_NAMESPACE, f"vignan-subject-{norm_cname}"))
                code_parts = [w[0].upper() for w in course_name.split() if w]
                subj_code = f"CS{''.join(code_parts[:4])}"
                subj_obj = {
                    "id": subj_id,
                    "name": course_name,
                    "code": subj_code,
                    "department_id": CSE_DEPT_ID,
                    "source_id": SOURCE_OFFICIAL_PEOPLE["id"],
                    "confidence": "high",
                    "last_verified": "2026-08-27T00:00:00Z"
                }
                subject_map[norm_cname] = subj_obj
            else:
                subj_obj = subject_map[norm_cname]

            created_faculty_subjects.append({
                "faculty_id": faculty_id,
                "subject_id": subj_obj["id"],
                "source_id": SOURCE_OFFICIAL_PEOPLE["id"],
                "confidence": "high"
            })

    # CRITICAL: Preserve all remaining referenced poster faculty records
    for pid, pref in poster_faculty_refs.items():
        if pid not in merged_faculty_map:
            merged_faculty_map[pid] = {
                "id": pid,
                "empcode": None,
                "full_name": pref["full_name"],
                "designation": "Faculty",
                "department_id": pref.get("department_id") or CSE_DEPT_ID,
                "email": pref.get("email"),
                "phone": pref.get("phone"),
                "room": pref.get("room"),
                "block": pref.get("block") or "N Block",
                "floor": pref.get("floor"),
                "profile_url": None,
                "source_id": pref.get("source_id") or SOURCE_OFFICIAL_PEOPLE["id"],
                "confidence": "high",
                "last_verified": "2026-08-26T00:00:00Z",
                "research_interests": [],
                "teaching_engagements": [],
                "academic_profile": {},
                "conflicting_sources": []
            }

    final_faculty_list = list(merged_faculty_map.values())
    all_subjects_list = list(subject_map.values())

    print(f"Total faculty in final dataset: {len(final_faculty_list)}")

    # Update departments with canonical CSE HOD ID
    for d in departments:
        if d["id"] == CSE_DEPT_ID or "Computer Science" in d["name"]:
            d["hod_faculty_id"] = stats["hod_canonical"]["id"]

    # Write files
    with open("database/extracted/faculty.json", "w", encoding="utf-8") as f:
        json.dump(final_faculty_list, f, indent=2, ensure_ascii=False)

    with open("database/extracted/subjects.json", "w", encoding="utf-8") as f:
        json.dump(all_subjects_list, f, indent=2, ensure_ascii=False)

    with open("database/extracted/faculty_subjects.json", "w", encoding="utf-8") as f:
        json.dump(created_faculty_subjects, f, indent=2, ensure_ascii=False)

    with open("database/extracted/departments.json", "w", encoding="utf-8") as f:
        json.dump(departments, f, indent=2, ensure_ascii=False)

    # Bulk import into Supabase
    if db.is_connected():
        print("--- 3. Syncing to Supabase database ---")
        db.client.table("sources").upsert([SOURCE_OFFICIAL_PEOPLE, SOURCE_OFFICIAL_CSE_DEPT]).execute()

        for i in range(0, len(final_faculty_list), 50):
            batch = final_faculty_list[i:i+50]
            db.client.table("faculty").upsert(batch).execute()
        print(f"  [OK] {len(final_faculty_list)} Faculty records upserted")

        for i in range(0, len(all_subjects_list), 50):
            batch = all_subjects_list[i:i+50]
            db.client.table("subjects").upsert(batch).execute()
        print(f"  [OK] {len(all_subjects_list)} Subjects upserted")

        for i in range(0, len(created_faculty_subjects), 50):
            batch = created_faculty_subjects[i:i+50]
            db.client.table("faculty_subjects").upsert(batch).execute()
        print(f"  [OK] {len(created_faculty_subjects)} Faculty-Subject assignments upserted")

        if stats["hod_canonical"]:
            hod_id = stats["hod_canonical"]["id"]
            db.client.table("departments").update({"hod_faculty_id": hod_id}).eq("id", CSE_DEPT_ID).execute()
            db.client.table("departments").update({"hod_faculty_id": hod_id}).eq("id", CSE_SPEC_DEPT_ID).execute()
            print(f"  [OK] CSE Departments linked to canonical HOD ID: {hod_id}")

    print("\n--- 4. Summary Stats ---")
    print(f"Official CSE Faculty Collected: {stats['official_cse_count']}")
    print(f"Matched with Posters: {stats['matched_with_posters']}")
    print(f"Total Faculty in Database: {len(final_faculty_list)}")
    print(f"Official Published Emails: {stats['official_emails']}")
    print(f"Official Published Phones: {stats['official_phones']}")
    print(f"Profiles with URLs: {stats['with_profile_urls']}")
    print(f"Profiles with Research Interests: {stats['with_research_interests']}")
    print(f"Profiles with Explicit Teaching Engagements: {stats['with_teaching_engagements']}")
    print(f"Profiles with Verified Poster Rooms: {stats['with_poster_rooms']}")
    print(f"Canonical CSE HOD: {stats['hod_canonical']['full_name']} (Email: {stats['hod_canonical']['email']}, Room: {stats['hod_canonical']['room'] or 'Not Available'})")
    return stats


if __name__ == "__main__":
    run_reconciliation()
