"""Pre-import integrity validator for VIGNAN campus JSON datasets."""

import json
import os
import re
import sys
from typing import Any, Dict, List, Set, Tuple

VALID_SOURCE_TYPES = {
    "official_website",
    "official_document",
    "department_verified",
    "campus_verified",
    "student_reported",
}

VALID_LOCATION_TYPES = {
    "gate",
    "building",
    "floor",
    "room",
    "office",
    "department",
    "service",
    "canteen",
    "facility",
    "other",
}

VALID_SERVICE_CATEGORIES = {
    "xerox",
    "printing",
    "stationery",
    "canteen",
    "transport",
    "medical",
    "library",
    "pharmacy",
    "other",
}

VALID_CONFIDENCE_LEVELS = {"high", "medium", "low", "needs_verification"}


def load_json_file(file_path: str) -> List[Dict[str, Any]]:
    """Safely load JSON array from file path."""
    if not os.path.exists(file_path):
        return []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except Exception as e:
        print(f"ERROR: Failed to parse JSON file '{file_path}': {e}")
        return []


def validate_dataset(base_dir: str = "database/extracted") -> Tuple[bool, List[str], Dict[str, int]]:
    """Validate all extracted JSON datasets against relational integrity and quality rules."""
    errors = []
    stats = {}

    # Load all files
    sources = load_json_file(os.path.join(base_dir, "sources.json"))
    departments = load_json_file(os.path.join(base_dir, "departments.json"))
    faculty = load_json_file(os.path.join(base_dir, "faculty.json"))
    subjects = load_json_file(os.path.join(base_dir, "subjects.json"))
    offices = load_json_file(os.path.join(base_dir, "offices.json"))
    counsellors = load_json_file(os.path.join(base_dir, "counsellors.json"))
    academic_support = load_json_file(os.path.join(base_dir, "academic_support.json"))
    locations = load_json_file(os.path.join(base_dir, "locations.json"))
    services = load_json_file(os.path.join(base_dir, "services.json"))
    routes = load_json_file(os.path.join(base_dir, "routes.json"))

    stats = {
        "sources": len(sources),
        "departments": len(departments),
        "faculty": len(faculty),
        "subjects": len(subjects),
        "offices": len(offices),
        "counsellors": len(counsellors),
        "academic_support": len(academic_support),
        "locations": len(locations),
        "services": len(services),
        "routes": len(routes),
    }

    source_ids = {s["id"] for s in sources if "id" in s}
    dept_ids = {d["id"] for d in departments if "id" in d}
    faculty_ids = {f["id"] for f in faculty if "id" in f}
    location_ids = {l["id"] for l in locations if "id" in l}
    office_ids = {o["id"] for o in offices if "id" in o}

    # 1. Validate Sources
    for i, s in enumerate(sources):
        if not s.get("source_name"):
            errors.append(f"sources[{i}]: Missing required 'source_name'.")
        st = s.get("source_type")
        if st and st not in VALID_SOURCE_TYPES:
            errors.append(f"sources[{i}]: Invalid source_type '{st}'. Must be one of {VALID_SOURCE_TYPES}.")

    # 2. Validate Departments
    dept_names = set()
    for i, d in enumerate(departments):
        name = d.get("name")
        if not name:
            errors.append(f"departments[{i}]: Missing required 'name'.")
        elif name in dept_names:
            errors.append(f"departments[{i}]: Duplicate department name '{name}'.")
        dept_names.add(name)

        sid = d.get("source_id")
        if sid and sid not in source_ids:
            errors.append(f"departments[{i}]: Broken source_id '{sid}' not found in sources.")

        hid = d.get("hod_faculty_id")
        if hid and hid not in faculty_ids:
            errors.append(f"departments[{i}]: Broken hod_faculty_id '{hid}' not found in faculty.")

    # 3. Validate Faculty
    for i, f in enumerate(faculty):
        name = f.get("full_name")
        if not name:
            errors.append(f"faculty[{i}]: Missing required 'full_name'.")

        did = f.get("department_id")
        if did and did not in dept_ids:
            errors.append(f"faculty[{i}]: Broken department_id '{did}' not found in departments.")

        sid = f.get("source_id")
        if sid and sid not in source_ids:
            errors.append(f"faculty[{i}]: Broken source_id '{sid}' not found in sources.")

    # 4. Validate Counsellors
    for i, c in enumerate(counsellors):
        c_name = c.get("counsellor_name")
        if not c_name:
            errors.append(f"counsellors[{i}]: Missing required 'counsellor_name'.")

        fid = c.get("faculty_id")
        if fid and fid not in faculty_ids:
            errors.append(f"counsellors[{i}]: Broken faculty_id '{fid}' not found in faculty.")

        sid = c.get("source_id")
        if sid and sid not in source_ids:
            errors.append(f"counsellors[{i}]: Broken source_id '{sid}' not found in sources.")

        r_start = str(c.get("registration_range_start") or "").strip()
        r_end = str(c.get("registration_range_end") or "").strip()
        if r_start and r_end:
            # When both start and end share the same format/length or are purely numeric/alphanumeric
            if r_start.isdigit() and r_end.isdigit() and int(r_start) > int(r_end):
                errors.append(f"counsellors[{i}]: Invalid registration range: start '{r_start}' > end '{r_end}'.")
            elif len(r_start) == len(r_end) and r_start[:4] == r_end[:4] and r_start > r_end:
                errors.append(f"counsellors[{i}]: Invalid registration range: start '{r_start}' > end '{r_end}'.")

    # 5. Validate Academic Support
    for i, a in enumerate(academic_support):
        if not a.get("role_name"):
            errors.append(f"academic_support[{i}]: Missing required 'role_name'.")
        if not a.get("person_name"):
            errors.append(f"academic_support[{i}]: Missing required 'person_name'.")
        fid = a.get("faculty_id")
        if fid and fid not in faculty_ids:
            errors.append(f"academic_support[{i}]: Broken faculty_id '{fid}' not found in faculty.")
        oid = a.get("office_id")
        if oid and oid not in office_ids:
            errors.append(f"academic_support[{i}]: Broken office_id '{oid}' not found in offices.")
        sid = a.get("source_id")
        if sid and sid not in source_ids:
            errors.append(f"academic_support[{i}]: Broken source_id '{sid}' not found in sources.")

    # 6. Validate Offices
    for i, o in enumerate(offices):
        if not o.get("name"):
            errors.append(f"offices[{i}]: Missing required 'name'.")
        sid = o.get("source_id")
        if sid and sid not in source_ids:
            errors.append(f"offices[{i}]: Broken source_id '{sid}' not found in sources.")

    # 7. Validate Locations
    for i, loc in enumerate(locations):
        if not loc.get("name"):
            errors.append(f"locations[{i}]: Missing required 'name'.")
        lt = loc.get("location_type")
        if lt and lt not in VALID_LOCATION_TYPES:
            errors.append(f"locations[{i}]: Invalid location_type '{lt}'. Must be one of {VALID_LOCATION_TYPES}.")
        pid = loc.get("parent_location_id")
        if pid and pid not in location_ids:
            errors.append(f"locations[{i}]: Broken parent_location_id '{pid}' not found in locations.")
        sid = loc.get("source_id")
        if sid and sid not in source_ids:
            errors.append(f"locations[{i}]: Broken source_id '{sid}' not found in sources.")

    # 8. Validate Services
    for i, svc in enumerate(services):
        if not svc.get("name"):
            errors.append(f"services[{i}]: Missing required 'name'.")
        cat = svc.get("category")
        if cat and cat not in VALID_SERVICE_CATEGORIES:
            errors.append(f"services[{i}]: Invalid category '{cat}'. Must be one of {VALID_SERVICE_CATEGORIES}.")
        lid = svc.get("location_id")
        if lid and lid not in location_ids:
            errors.append(f"services[{i}]: Broken location_id '{lid}' not found in locations.")

    # 9. Validate Routes
    for i, r in enumerate(routes):
        s_id = r.get("start_location_id")
        d_id = r.get("destination_location_id")
        if s_id and s_id not in location_ids:
            errors.append(f"routes[{i}]: Broken start_location_id '{s_id}' not found in locations.")
        if d_id and d_id not in location_ids:
            errors.append(f"routes[{i}]: Broken destination_location_id '{d_id}' not found in locations.")
        steps = r.get("steps")
        if steps is None or not isinstance(steps, list):
            errors.append(f"routes[{i}]: Missing or non-list 'steps' field.")

    # 10. Validate Timetables
    y2_tt = load_json_file(os.path.join(base_dir, "timetables", "year2_timetable.json"))
    y3_tt = load_json_file(os.path.join(base_dir, "timetables", "year3_timetable.json"))
    all_tt = y2_tt + y3_tt
    stats["timetables_y2"] = len(y2_tt)
    stats["timetables_y3"] = len(y3_tt)

    seen_slots = set()
    for i, tt in enumerate(all_tt):
        yr = tt.get("year")
        sec = tt.get("section")
        day = tt.get("day")
        st = tt.get("start_time")
        et = tt.get("end_time")
        scode = tt.get("subject_code")
        sid = tt.get("source_id")

        if yr not in [2, 3]:
            errors.append(f"timetables[{i}]: Invalid year '{yr}'. Must be 2 or 3.")
        if not sec:
            errors.append(f"timetables[{i}]: Missing section.")
        if day not in {'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'}:
            errors.append(f"timetables[{i}]: Invalid day '{day}'.")
        if not st or not et or st >= et:
            errors.append(f"timetables[{i}]: Invalid start_time '{st}' or end_time '{et}'.")
        if not scode:
            errors.append(f"timetables[{i}]: Missing subject_code.")
        if sid and sid not in source_ids:
            errors.append(f"timetables[{i}]: Broken source_id '{sid}' not found in sources.")

        slot_key = (yr, str(sec), day, st)
        if slot_key in seen_slots:
            errors.append(f"timetables[{i}]: Duplicate timetable slot entry for {slot_key}.")
        seen_slots.add(slot_key)

    is_valid = len(errors) == 0
    return is_valid, errors, stats



def main():
    """CLI runner for validation."""
    print("=" * 60)
    print("VIGNAN Campus Data Integrity Validator")
    print("=" * 60)

    is_valid, errors, stats = validate_dataset()

    print("\nDataset Record Counts:")
    for entity, count in stats.items():
        print(f"  - {entity:<20}: {count} records")

    if is_valid:
        print("\n[SUCCESS] All datasets passed integrity and relationship validation!")
        sys.exit(0)
    else:
        print(f"\n[FAILURE] Found {len(errors)} validation error(s):")
        for err in errors:
            print(f"  ! {err}")
        sys.exit(1)


if __name__ == "__main__":
    main()
