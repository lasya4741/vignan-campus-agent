"""Ingest Official VIGNAN Website CSE Faculty Data, Subjects, and Teaching Engagements.
Authoritative source: https://vignan.ac.in/newvignan/people.php (Computer Science Engineering filter)
and https://www.vignan.ac.in/newvignan/departments/depthome.php?deptid=sch3_dept1&deptnm=CSE&school=sch3
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


def process_and_save_data():
    print("--- 1. Loading raw official CSE profiles and existing poster data ---")
    with open("database/extracted/sources.json", "r", encoding="utf-8") as f:
        sources_list = json.load(f)

    # Ensure official sources are in sources_list
    existing_source_ids = {s["id"] for s in sources_list}
    if SOURCE_OFFICIAL_PEOPLE["id"] not in existing_source_ids:
        sources_list.append(SOURCE_OFFICIAL_PEOPLE)
    if SOURCE_OFFICIAL_CSE_DEPT["id"] not in existing_source_ids:
        sources_list.append(SOURCE_OFFICIAL_CSE_DEPT)

    with open("database/extracted/sources.json", "w", encoding="utf-8") as f:
        json.dump(sources_list, f, indent=2, ensure_ascii=False)

    with open("database/extracted/faculty.json", "r", encoding="utf-8") as f:
        existing_faculty = json.load(f)

    with open("database/raw/official_cse_faculty.json", "r", encoding="utf-8") as f:
        official_cse = json.load(f)

    with open("database/extracted/subjects.json", "r", encoding="utf-8") as f:
        existing_subjects = json.load(f)

    subject_map = {normalize_text(s["name"]): s for s in existing_subjects}
    matched_existing_ids = set()
    merged_faculty = []
    created_faculty_subjects = []

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

        # Match with poster records
        matched_poster = None
        web_norm = normalize_text(f"{raw_sal} {raw_name}")
        web_tokens = set(web_norm.split()) - {"dr", "mr", "mrs", "ms", "prof", "s", "k", "t", "g", "p", "v", "d", "m", "n", "a", "b", "c", "r"}

        for ef in existing_faculty:
            if ef["id"] in matched_existing_ids:
                continue
            ef_norm = normalize_text(ef["full_name"])
            ef_tokens = set(ef_norm.split()) - {"dr", "mr", "mrs", "ms", "prof", "s", "k", "t", "g", "p", "v", "d", "m", "n", "a", "b", "c", "r"}

            if ef_tokens and web_tokens and (ef_tokens == web_tokens or ef_tokens.issubset(web_tokens) or web_tokens.issubset(ef_tokens)):
                matched_poster = ef
                matched_existing_ids.add(ef["id"])
                break

        if matched_poster:
            faculty_id = matched_poster["id"]
            room = matched_poster.get("room")
            block = matched_poster.get("block") or "N Block"
            floor = matched_poster.get("floor")
            if not phone and matched_poster.get("phone"):
                phone = matched_poster.get("phone")
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

        merged_faculty.append(fac_record)

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

    # Preserve non-CSE faculty from poster extraction (HODs of other depts)
    for ef in existing_faculty:
        if ef["id"] not in matched_existing_ids and ef.get("department_id") != CSE_DEPT_ID:
            merged_faculty.append(ef)

    print("--- 2. Writing updated local JSON files in database/extracted/ ---")
    with open("database/extracted/faculty.json", "w", encoding="utf-8") as f:
        json.dump(merged_faculty, f, indent=2, ensure_ascii=False)

    all_subjects_list = list(subject_map.values())
    with open("database/extracted/subjects.json", "w", encoding="utf-8") as f:
        json.dump(all_subjects_list, f, indent=2, ensure_ascii=False)

    with open("database/extracted/faculty_subjects.json", "w", encoding="utf-8") as f:
        json.dump(created_faculty_subjects, f, indent=2, ensure_ascii=False)

    # Update departments.json with canonical CSE HOD id
    with open("database/extracted/departments.json", "r", encoding="utf-8") as f:
        depts = json.load(f)

    for d in depts:
        if d["id"] == CSE_DEPT_ID or "Computer Science" in d["name"]:
            d["hod_faculty_id"] = stats["hod_canonical"]["id"]

    with open("database/extracted/departments.json", "w", encoding="utf-8") as f:
        json.dump(depts, f, indent=2, ensure_ascii=False)

    print("--- 3. Bulk importing verified official data into Supabase ---")
    if db.is_connected():
        # 1. Upsert Sources
        db.client.table("sources").upsert([SOURCE_OFFICIAL_PEOPLE, SOURCE_OFFICIAL_CSE_DEPT]).execute()
        print("  [OK] Sources upserted")

        # 2. Upsert Faculty in batches of 50
        for i in range(0, len(merged_faculty), 50):
            batch = merged_faculty[i:i+50]
            db.client.table("faculty").upsert(batch).execute()
        print(f"  [OK] {len(merged_faculty)} Faculty records upserted")

        # 3. Upsert Subjects in batches of 50
        for i in range(0, len(all_subjects_list), 50):
            batch = all_subjects_list[i:i+50]
            db.client.table("subjects").upsert(batch).execute()
        print(f"  [OK] {len(all_subjects_list)} Subjects upserted")

        # 4. Upsert Faculty Subjects in batches of 50
        for i in range(0, len(created_faculty_subjects), 50):
            batch = created_faculty_subjects[i:i+50]
            db.client.table("faculty_subjects").upsert(batch).execute()
        print(f"  [OK] {len(created_faculty_subjects)} Faculty-Subject assignments upserted")

        # 5. Update Department HOD
        if stats["hod_canonical"]:
            hod_id = stats["hod_canonical"]["id"]
            db.client.table("departments").update({"hod_faculty_id": hod_id}).eq("id", CSE_DEPT_ID).execute()
            db.client.table("departments").update({"hod_faculty_id": hod_id}).eq("id", CSE_SPEC_DEPT_ID).execute()
            print(f"  [OK] CSE Departments linked to canonical HOD ID: {hod_id}")

    print("\n--- 4. Ingestion Complete ---")
    print(f"Total Official CSE Faculty: {stats['official_cse_count']}")
    print(f"Matched with Posters: {stats['matched_with_posters']}")
    print(f"Newly Added from Web: {stats['newly_added_from_web']}")
    print(f"Total Faculty in Knowledge Base: {len(merged_faculty)}")
    print(f"Official Published Emails: {stats['official_emails']}")
    print(f"Official Published Phones: {stats['official_phones']}")
    print(f"Profiles with URLs: {stats['with_profile_urls']}")
    print(f"Profiles with Research Interests: {stats['with_research_interests']}")
    print(f"Profiles with Explicit Teaching Engagements: {stats['with_teaching_engagements']}")
    print(f"Profiles with Verified Poster Rooms: {stats['with_poster_rooms']}")
    print(f"Total Subjects: {len(all_subjects_list)}")
    print(f"Total Faculty-Subject Links: {len(created_faculty_subjects)}")
    if stats["hod_canonical"]:
        print(f"Canonical CSE HOD: {stats['hod_canonical']['full_name']} (Email: {stats['hod_canonical']['email']}, Room: {stats['hod_canonical']['room'] or 'Not Available'})")

    return stats


if __name__ == "__main__":
    process_and_save_data()
