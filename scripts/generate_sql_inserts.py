"""Generate SQL statements from extracted JSON datasets."""

import json
import os

EXTRACTED_DIR = "database/extracted"
OUTPUT_SQL = "database/seeds/verified_seed_data.sql"

def sql_escape(val):
    if val is None:
        return "NULL"
    if isinstance(val, bool):
        return "TRUE" if val else "FALSE"
    if isinstance(val, (int, float)):
        return str(val)
    if isinstance(val, (dict, list)):
        return "'" + json.dumps(val).replace("'", "''") + "'::jsonb"
    s = str(val).replace("'", "''")
    return f"'{s}'"

def generate():
    tables = [
        ("sources", "sources.json", ["id", "source_type", "source_name", "source_url", "description", "document_name", "verified_at", "notes"]),
        ("locations", "locations.json", ["id", "name", "location_type", "block", "floor", "room", "description", "latitude", "longitude", "parent_location_id", "source_id", "confidence", "last_verified"]),
        ("departments", "departments.json", ["id", "name", "short_name", "description", "block", "floor_information", "hod_faculty_id", "source_id", "confidence", "last_verified"]),
        ("faculty", "faculty.json", ["id", "full_name", "designation", "department_id", "email", "phone", "room", "block", "floor", "profile_url", "source_id", "confidence", "last_verified"]),
        ("subjects", "subjects.json", ["id", "name", "code", "department_id", "source_id", "confidence", "last_verified"]),
        ("offices", "offices.json", ["id", "name", "purpose", "room", "block", "floor", "phone", "email", "description", "source_id", "confidence", "last_verified"]),
        ("counsellors", "counsellors.json", ["id", "academic_year", "year", "section", "counsellor_name", "faculty_id", "phone", "room", "registration_range_start", "registration_range_end", "registration_range_text", "source_id", "confidence", "last_verified"]),
        ("academic_support", "academic_support.json", ["id", "role_name", "person_name", "faculty_id", "responsibilities", "office_id", "room", "phone", "email", "source_id", "confidence", "last_verified"]),
        ("services", "services.json", ["id", "name", "category", "description", "location_id", "services_offered", "source_id", "confidence", "last_verified"]),
        ("routes", "routes.json", ["id", "start_location_id", "destination_location_id", "steps", "estimated_minutes", "source_id", "confidence"]),
    ]

    sql_statements = ["-- VIGNAN Verified Campus Data Seed Script", "BEGIN;"]

    # 1. Sources
    with open(os.path.join(EXTRACTED_DIR, "sources.json"), "r", encoding="utf-8") as f:
        sources = json.load(f)
    for s in sources:
        cols = ["id", "source_type", "source_name", "source_url", "description", "document_name", "verified_at"]
        vals = [sql_escape(s.get(c)) for c in cols]
        sql_statements.append(f"INSERT INTO sources ({', '.join(cols)}) VALUES ({', '.join(vals)}) ON CONFLICT (id) DO UPDATE SET {', '.join([f'{c} = EXCLUDED.{c}' for c in cols if c != 'id'])};")

    # 2. Locations
    with open(os.path.join(EXTRACTED_DIR, "locations.json"), "r", encoding="utf-8") as f:
        locations = json.load(f)
    for l in locations:
        cols = ["id", "name", "location_type", "block", "floor", "room", "description", "parent_location_id", "source_id", "confidence", "last_verified"]
        vals = [sql_escape(l.get(c)) for c in cols]
        sql_statements.append(f"INSERT INTO locations ({', '.join(cols)}) VALUES ({', '.join(vals)}) ON CONFLICT (id) DO UPDATE SET {', '.join([f'{c} = EXCLUDED.{c}' for c in cols if c != 'id'])};")

    # 3. Departments (Pass 1: without hod_faculty_id)
    with open(os.path.join(EXTRACTED_DIR, "departments.json"), "r", encoding="utf-8") as f:
        departments = json.load(f)
    for d in departments:
        cols = ["id", "name", "short_name", "description", "block", "floor_information", "source_id", "confidence", "last_verified"]
        vals = [sql_escape(d.get(c)) for c in cols]
        sql_statements.append(f"INSERT INTO departments ({', '.join(cols)}) VALUES ({', '.join(vals)}) ON CONFLICT (id) DO UPDATE SET {', '.join([f'{c} = EXCLUDED.{c}' for c in cols if c != 'id'])};")

    # 4. Faculty
    with open(os.path.join(EXTRACTED_DIR, "faculty.json"), "r", encoding="utf-8") as f:
        faculty = json.load(f)
    for fac in faculty:
        cols = ["id", "full_name", "designation", "department_id", "email", "phone", "room", "block", "floor", "profile_url", "source_id", "confidence", "last_verified"]
        vals = [sql_escape(fac.get(c)) for c in cols]
        sql_statements.append(f"INSERT INTO faculty ({', '.join(cols)}) VALUES ({', '.join(vals)}) ON CONFLICT (id) DO UPDATE SET {', '.join([f'{c} = EXCLUDED.{c}' for c in cols if c != 'id'])};")

    # 5. Departments (Pass 2: link HODs)
    for d in departments:
        if d.get("hod_faculty_id"):
            sql_statements.append(f"UPDATE departments SET hod_faculty_id = {sql_escape(d['hod_faculty_id'])} WHERE id = {sql_escape(d['id'])};")

    # 6. Subjects
    with open(os.path.join(EXTRACTED_DIR, "subjects.json"), "r", encoding="utf-8") as f:
        subjects = json.load(f)
    for subj in subjects:
        cols = ["id", "name", "code", "department_id", "source_id", "confidence", "last_verified"]
        vals = [sql_escape(subj.get(c)) for c in cols]
        sql_statements.append(f"INSERT INTO subjects ({', '.join(cols)}) VALUES ({', '.join(vals)}) ON CONFLICT (id) DO UPDATE SET {', '.join([f'{c} = EXCLUDED.{c}' for c in cols if c != 'id'])};")

    # 7. Offices
    with open(os.path.join(EXTRACTED_DIR, "offices.json"), "r", encoding="utf-8") as f:
        offices = json.load(f)
    for o in offices:
        cols = ["id", "name", "purpose", "room", "block", "floor", "phone", "email", "description", "source_id", "confidence", "last_verified"]
        vals = [sql_escape(o.get(c)) for c in cols]
        sql_statements.append(f"INSERT INTO offices ({', '.join(cols)}) VALUES ({', '.join(vals)}) ON CONFLICT (id) DO UPDATE SET {', '.join([f'{c} = EXCLUDED.{c}' for c in cols if c != 'id'])};")

    # 8. Counsellors
    with open(os.path.join(EXTRACTED_DIR, "counsellors.json"), "r", encoding="utf-8") as f:
        counsellors = json.load(f)
    for c in counsellors:
        cols = ["id", "academic_year", "year", "section", "counsellor_name", "faculty_id", "phone", "room", "registration_range_start", "registration_range_end", "registration_range_text", "source_id", "confidence", "last_verified"]
        vals = [sql_escape(c.get(c_name)) for c_name in cols]
        sql_statements.append(f"INSERT INTO counsellors ({', '.join(cols)}) VALUES ({', '.join(vals)}) ON CONFLICT (id) DO UPDATE SET {', '.join([f'{col} = EXCLUDED.{col}' for col in cols if col != 'id'])};")

    # 9. Academic Support
    with open(os.path.join(EXTRACTED_DIR, "academic_support.json"), "r", encoding="utf-8") as f:
        academic_support = json.load(f)
    for a in academic_support:
        cols = ["id", "role_name", "person_name", "faculty_id", "responsibilities", "office_id", "room", "phone", "email", "source_id", "confidence", "last_verified"]
        vals = [sql_escape(a.get(col)) for col in cols]
        sql_statements.append(f"INSERT INTO academic_support ({', '.join(cols)}) VALUES ({', '.join(vals)}) ON CONFLICT (id) DO UPDATE SET {', '.join([f'{col} = EXCLUDED.{col}' for col in cols if col != 'id'])};")

    # 10. Services
    with open(os.path.join(EXTRACTED_DIR, "services.json"), "r", encoding="utf-8") as f:
        services = json.load(f)
    for s in services:
        cols = ["id", "name", "category", "description", "location_id", "services_offered", "source_id", "confidence", "last_verified"]
        vals = [sql_escape(s.get(col)) for col in cols]
        sql_statements.append(f"INSERT INTO services ({', '.join(cols)}) VALUES ({', '.join(vals)}) ON CONFLICT (id) DO UPDATE SET {', '.join([f'{col} = EXCLUDED.{col}' for col in cols if col != 'id'])};")

    # 11. Timetables (Year 2 & Year 3)
    for tt_file in ["timetables/year2_timetable.json", "timetables/year3_timetable.json"]:
        tt_path = os.path.join(EXTRACTED_DIR, tt_file)
        if os.path.exists(tt_path):
            with open(tt_path, "r", encoding="utf-8") as f:
                records = json.load(f)
            for r in records:
                cols = ["year", "section", "day_of_week", "start_time", "end_time", "subject_code", "subject_name", "class_type", "room", "section_default_room", "faculty", "source_id", "confidence", "last_verified"]
                rec_map = {
                    "year": r.get("year"),
                    "section": str(r.get("section")),
                    "day_of_week": r.get("day"),
                    "start_time": r.get("start_time"),
                    "end_time": r.get("end_time"),
                    "subject_code": r.get("subject_code"),
                    "subject_name": r.get("subject_name"),
                    "class_type": r.get("class_type"),
                    "room": r.get("room"),
                    "section_default_room": r.get("section_default_room"),
                    "faculty": r.get("faculty"),
                    "source_id": r.get("source_id"),
                    "confidence": r.get("confidence"),
                    "last_verified": r.get("last_verified")
                }
                vals = [sql_escape(rec_map.get(col)) for col in cols]
                sql_statements.append(f"INSERT INTO timetables ({', '.join(cols)}) VALUES ({', '.join(vals)});")

    sql_statements.append("COMMIT;")

    os.makedirs(os.path.dirname(OUTPUT_SQL), exist_ok=True)
    with open(OUTPUT_SQL, "w", encoding="utf-8") as f:
        f.write("\n".join(sql_statements))
    print(f"Generated {OUTPUT_SQL} with {len(sql_statements)} statements.")

if __name__ == "__main__":
    generate()
