"""Ingest official HOD records across all VIGNAN departments and replace placeholder rows."""

import os
import sys
import json
import uuid
import urllib.request
from datetime import datetime, timezone

sys.path.insert(0, os.path.abspath("."))

from backend.supabase_client import db
from backend.utils.normalization import normalize_text

SOURCE_OFFICIAL_PEOPLE = "5a8d7901-b758-5d20-a612-4c924bc01f89"

# Department mapping from branch code to department code/name in database
BRANCH_TO_DEPT = {
    "IT": "Information Technology",
    "ECE": "Electronics & Communication Engineering",
    "EEE": "Electrical & Electronics Engineering",
    "MECH": "Mechanical Engineering",
    "CIVIL": "Civil Engineering",
    "BIOTECH": "Biotechnology",
    "BME": "Biomedical Engineering",
    "BI": "Bioinformatics",
    "DMS": "Management Studies",
    "CA": "Computer Applications",
    "CSE": "Computer Science & Engineering (Core)",
    "ACSE": "Advanced Computer Science & Engineering",
    "TEXTILE": "Textile Engineering",
    "FOOD": "Food Technology",
    "AGRI": "Agriculture Engineering",
    "AHS": "Agriculture Engineering",
    "CHEM": "Chemical Engineering",
    "CHEMISTRY": "Chemical Engineering",
    "LAW": "Law"
}

def fetch_faculty_details(empcode):
    """Fetch complete academic profile for an empcode from getfaculty.php."""
    url = "https://vignan.ac.in/newvignan/getfaculty.php"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Content-Type": "application/json",
        "Accept": "application/json, text/plain, */*"
    }
    payload = json.dumps({"id": str(empcode).strip()}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data
    except Exception as e:
        print(f"  [WARN] Failed to fetch details for empcode {empcode}: {e}")
        return None

def sync_hods():
    print("--- 1. Loading existing extracted data & official HODs ---")
    with open("database/extracted/departments.json", "r", encoding="utf-8") as f:
        departments = json.load(f)
    with open("database/extracted/faculty.json", "r", encoding="utf-8") as f:
        faculty = json.load(f)
    with open("database/raw/official_all_hods.json", "r", encoding="utf-8") as f:
        raw_hods_data = json.load(f)

    official_hods = raw_hods_data.get("hods", [])
    print(f"Loaded {len(official_hods)} official HOD records from raw data.")

    dept_by_name = {d["name"]: d for d in departments}

    # Track existing faculty by empcode and normalized name
    fac_by_empcode = {f.get("empcode"): f for f in faculty if f.get("empcode")}
    fac_by_name = {normalize_text(f["full_name"]): f for f in faculty}

    updated_faculty = list(faculty)
    hod_updates_by_dept = {}

    for h in official_hods:
        branch = str(h.get("branch") or "").upper().strip()
        dept_name = BRANCH_TO_DEPT.get(branch)
        if not dept_name:
            # Check if branch matches partial department name
            for k, dname in BRANCH_TO_DEPT.items():
                if k in branch or branch in k:
                    dept_name = dname
                    break
        if not dept_name or dept_name not in dept_by_name:
            continue

        target_dept = dept_by_name[dept_name]
        empcode = str(h.get("empcode") or "").strip()
        sal = (h.get("salutation") or "").strip()
        raw_name = (h.get("name") or "").strip()
        full_name = f"{sal}. {raw_name}".strip() if sal else raw_name
        email = (h.get("email") or "").strip() or None
        phone = (h.get("personalcontact") or h.get("contact") or "").strip() or None
        profile_url = f"https://vignan.ac.in/facultyprofiles/index.php?empid={empcode}" if empcode else None

        # Fetch full academic details
        print(f"Fetching full details for HOD: {full_name} ({dept_name}, empcode: {empcode})...")
        details = fetch_faculty_details(empcode)
        research_interests = []
        teaching_engagements = []
        academic_profile = {}

        if details and isinstance(details, dict):
            for r in details.get("research", []):
                val = r.get("research_interest") or r.get("researchinterest")
                if val and val.strip():
                    research_interests.append(val.strip())
            for t in details.get("teaching", []):
                val = t.get("teaching_engagement") or t.get("teachingengagement") or t.get("subject")
                if val and val.strip():
                    teaching_engagements.append(val.strip())
            academic_profile = {
                "education": details.get("education", []),
                "experience": details.get("experience", []),
                "awards": details.get("awards", []),
                "admin_positions": [h.get("adminpos")] if h.get("adminpos") else [],
                "publications_count": len(details.get("journal", [])) + len(details.get("conference", []))
            }

        # Check if already exists in faculty
        matched_fac = fac_by_empcode.get(empcode) or fac_by_name.get(normalize_text(full_name))

        if matched_fac:
            matched_fac["empcode"] = empcode
            matched_fac["department_id"] = target_dept["id"]
            matched_fac["designation"] = (h.get("desig") or matched_fac.get("designation") or "Professor").title()
            if email and not matched_fac.get("email"):
                matched_fac["email"] = email
            if phone and not matched_fac.get("phone"):
                matched_fac["phone"] = phone
            if profile_url:
                matched_fac["profile_url"] = profile_url
            if research_interests:
                matched_fac["research_interests"] = research_interests
            if teaching_engagements:
                matched_fac["teaching_engagements"] = teaching_engagements
            if academic_profile:
                matched_fac["academic_profile"] = academic_profile
            fac_id = matched_fac["id"]
        else:
            fac_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"vignan.faculty.{empcode or full_name}"))
            new_fac = {
                "id": fac_id,
                "full_name": full_name,
                "designation": (h.get("desig") or "Professor").title(),
                "department_id": target_dept["id"],
                "email": email,
                "phone": phone,
                "room": None,
                "block": target_dept.get("block"),
                "floor": None,
                "profile_url": profile_url,
                "source_id": SOURCE_OFFICIAL_PEOPLE,
                "confidence": "high",
                "last_verified": datetime.now(timezone.utc).isoformat(),
                "empcode": empcode,
                "research_interests": research_interests,
                "teaching_engagements": teaching_engagements,
                "academic_profile": academic_profile,
                "conflicting_sources": []
            }
            updated_faculty.append(new_fac)
            fac_by_empcode[empcode] = new_fac
            fac_by_name[normalize_text(full_name)] = new_fac

        hod_updates_by_dept[target_dept["id"]] = fac_id
        target_dept["hod_faculty_id"] = fac_id
        print(f"  [OK] Assigned HOD for {dept_name} -> {full_name} ({fac_id})")

    # Special case: Computer Science & Engineering (Specializations) shares HOD with Core
    cse_core = dept_by_name.get("Computer Science & Engineering (Core)")
    cse_spec = dept_by_name.get("Computer Science & Engineering (Specializations)")
    if cse_core and cse_spec:
        cse_spec["hod_faculty_id"] = cse_core.get("hod_faculty_id")

    # 2. Filter out any placeholder faculty rows ("HOD of ...")
    clean_faculty = []
    placeholder_ids = set()
    for f in updated_faculty:
        if f["full_name"].startswith("HOD of "):
            placeholder_ids.add(f["id"])
        else:
            clean_faculty.append(f)

    clean_fac_ids = {f["id"] for f in clean_faculty}

    # Ensure all departments have valid HOD foreign keys or None
    for d in departments:
        if d.get("hod_faculty_id") in placeholder_ids or (d.get("hod_faculty_id") and d["hod_faculty_id"] not in clean_fac_ids):
            d["hod_faculty_id"] = None

    print(f"\n--- 2. Placeholder faculty rows to remove: {len(placeholder_ids)} ---")
    print(f"Clean canonical faculty count: {len(clean_faculty)}")

    # 3. Save to extracted json files
    with open("database/extracted/faculty.json", "w", encoding="utf-8") as f:
        json.dump(clean_faculty, f, indent=2, ensure_ascii=False)
    with open("database/extracted/departments.json", "w", encoding="utf-8") as f:
        json.dump(departments, f, indent=2, ensure_ascii=False)

    print("  [OK] Saved extracted JSON files.")

    # 4. Sync to Supabase
    if db.is_connected():
        print("\n--- 3. Syncing to Supabase database ---")
        if placeholder_ids:
            for pid in placeholder_ids:
                try:
                    db.client.table("faculty").delete().eq("id", pid).execute()
                except Exception as e:
                    print(f"  [WARN] Failed to delete placeholder {pid}: {e}")
            print(f"  [OK] Deleted {len(placeholder_ids)} placeholder rows from Supabase.")

        for i in range(0, len(clean_faculty), 50):
            batch = clean_faculty[i:i+50]
            db.client.table("faculty").upsert(batch).execute()
        print(f"  [OK] Upserted {len(clean_faculty)} canonical faculty rows.")

        for d in departments:
            db.client.table("departments").update({"hod_faculty_id": d.get("hod_faculty_id")}).eq("id", d["id"]).execute()
        print(f"  [OK] Updated departments hod_faculty_id in Supabase.")

    print("\nHOD Synchronization Complete!")

if __name__ == "__main__":
    sync_hods()
