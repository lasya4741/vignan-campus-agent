"""Data ingestion pipeline: imports verified campus JSON datasets into Supabase."""

import argparse
import json
import os
import sys
from typing import Any, Dict, List, Tuple

# Ensure parent directory is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.config import settings
from backend.supabase_client import db
from backend.utils.logging import logger
from scripts.validate_data import load_json_file, validate_dataset


def import_table_records(table_name: str, records: List[Dict[str, Any]], dry_run: bool = False) -> Tuple[int, int, int]:
    """Insert or upsert a list of records into a Supabase table with batch processing and error tracking."""
    if not records:
        return 0, 0, 0

    inserted = 0
    skipped = 0
    failed = 0

    print(f"\nProcessing '{table_name}' ({len(records)} records)...")
    if dry_run:
        for r in records:
            print(f"  [DRY-RUN] Would insert into '{table_name}': {r.get('name') or r.get('full_name') or r.get('id')}")
            inserted += 1
        return inserted, skipped, failed

    # Attempt batch upsert first
    batch_size = 50
    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        try:
            res = db.client.table(table_name).upsert(batch).execute()
            inserted += len(batch)
            print(f"  Upserted batch {i + 1} to {min(i + batch_size, len(records))} in '{table_name}'")
        except Exception as e:
            logger.warning(f"Batch upsert on {table_name} failed: {e}. Falling back to single-row processing.")
            for r in batch:
                try:
                    res = db.client.table(table_name).upsert(r).execute()
                    inserted += 1
                except Exception as inner_e:
                    logger.error(f"Failed to insert record {r.get('id')} into {table_name}: {inner_e}")
                    failed += 1

    return inserted, skipped, failed


def run_import(base_dir: str = "database/extracted", dry_run: bool = False):
    """Execute complete dataset ingestion pipeline in strict topological order."""
    print("=" * 60)
    print(f"VIGNAN Campus Data Ingestion Pipeline {'(DRY RUN MODE)' if dry_run else ''}")
    print("=" * 60)

    # Step 1: Pre-import integrity validation
    print("\n1. Running pre-import data integrity validation...")
    is_valid, errors, stats = validate_dataset(base_dir)
    if not is_valid:
        print(f"[ABORT] Cannot proceed with import. Found {len(errors)} integrity errors:")
        for e in errors:
            print(f"  ! {e}")
        sys.exit(1)

    total_available_records = sum(stats.values())
    if total_available_records == 0:
        print("[INFO] All extracted JSON datasets are currently empty.")
        sys.exit(0)

    # Step 2: Supabase connection check
    if not dry_run and not db.is_connected():
        print("[ERROR] Supabase client is not connected. Please check SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in .env.")
        sys.exit(1)

    # Step 3: Ingestion in strict foreign-key dependency order
    summary = {}

    # 1. Sources
    sources = load_json_file(os.path.join(base_dir, "sources.json"))
    ins, skip, fail = import_table_records("sources", sources, dry_run=dry_run)
    summary["sources"] = {"inserted": ins, "skipped": skip, "failed": fail}

    # 2. Locations
    locations = load_json_file(os.path.join(base_dir, "locations.json"))
    ins, skip, fail = import_table_records("locations", locations, dry_run=dry_run)
    summary["locations"] = {"inserted": ins, "skipped": skip, "failed": fail}

    # 3. Departments (Pass 1: insert without hod_faculty_id to avoid circular FK before faculty exist)
    departments = load_json_file(os.path.join(base_dir, "departments.json"))
    departments_pass1 = [dict(d, hod_faculty_id=None) for d in departments]
    ins, skip, fail = import_table_records("departments", departments_pass1, dry_run=dry_run)
    summary["departments"] = {"inserted": ins, "skipped": skip, "failed": fail}

    # 4. Faculty
    faculty = load_json_file(os.path.join(base_dir, "faculty.json"))
    ins, skip, fail = import_table_records("faculty", faculty, dry_run=dry_run)
    summary["faculty"] = {"inserted": ins, "skipped": skip, "failed": fail}

    # 5. Departments (Pass 2: link hod_faculty_id)
    if not dry_run:
        for d in departments:
            if d.get("hod_faculty_id"):
                try:
                    db.client.table("departments").update({"hod_faculty_id": d["hod_faculty_id"]}).eq("id", d["id"]).execute()
                except Exception as e:
                    logger.warning(f"Failed to link HOD {d['hod_faculty_id']} to department {d['id']}: {e}")

    # 6. Subjects
    subjects = load_json_file(os.path.join(base_dir, "subjects.json"))
    ins, skip, fail = import_table_records("subjects", subjects, dry_run=dry_run)
    summary["subjects"] = {"inserted": ins, "skipped": skip, "failed": fail}

    # 7. Faculty Subjects
    faculty_subjects = load_json_file(os.path.join(base_dir, "faculty_subjects.json"))
    ins, skip, fail = import_table_records("faculty_subjects", faculty_subjects, dry_run=dry_run)
    summary["faculty_subjects"] = {"inserted": ins, "skipped": skip, "failed": fail}

    # 8. Offices
    offices = load_json_file(os.path.join(base_dir, "offices.json"))
    ins, skip, fail = import_table_records("offices", offices, dry_run=dry_run)
    summary["offices"] = {"inserted": ins, "skipped": skip, "failed": fail}

    # 9. Counsellors
    counsellors = load_json_file(os.path.join(base_dir, "counsellors.json"))
    ins, skip, fail = import_table_records("counsellors", counsellors, dry_run=dry_run)
    summary["counsellors"] = {"inserted": ins, "skipped": skip, "failed": fail}

    # 10. Academic Support
    academic_support = load_json_file(os.path.join(base_dir, "academic_support.json"))
    ins, skip, fail = import_table_records("academic_support", academic_support, dry_run=dry_run)
    summary["academic_support"] = {"inserted": ins, "skipped": skip, "failed": fail}

    # 11. Services
    services = load_json_file(os.path.join(base_dir, "services.json"))
    ins, skip, fail = import_table_records("services", services, dry_run=dry_run)
    summary["services"] = {"inserted": ins, "skipped": skip, "failed": fail}

    # 12. Routes
    routes = load_json_file(os.path.join(base_dir, "routes.json"))
    ins, skip, fail = import_table_records("routes", routes, dry_run=dry_run)
    summary["routes"] = {"inserted": ins, "skipped": skip, "failed": fail}

    # 13. Timetables (Year 2 & Year 3)
    y2_tt = load_json_file(os.path.join(base_dir, "timetables", "year2_timetable.json"))
    y3_tt = load_json_file(os.path.join(base_dir, "timetables", "year3_timetable.json"))
    tt_records = []
    for r in (y2_tt + y3_tt):
        rec = dict(r)
        if "day" in rec and "day_of_week" not in rec:
            rec["day_of_week"] = rec.pop("day")
        if "academic_year" in rec:
            rec["source_academic_year"] = rec.pop("academic_year")
        if "project_target_year" in rec:
            rec["project_target_academic_year"] = rec.pop("project_target_year")
        rec.pop("project_usage", None)
        rec.pop("faculty", None)
        tt_records.append(rec)

    ins, skip, fail = import_table_records("timetables", tt_records, dry_run=dry_run)
    summary["timetables"] = {"inserted": ins, "skipped": skip, "failed": fail}


    print("\n" + "=" * 60)
    print("Import Summary Report:")
    print("=" * 60)
    for tbl, s in summary.items():
        print(f"  - {tbl:<20}: Inserted={s['inserted']}, Skipped={s['skipped']}, Failed={s['failed']}")
    print("\nImport pipeline completed successfully!")


def main():
    parser = argparse.ArgumentParser(description="Import verified JSON datasets into Supabase database.")
    parser.add_argument("--dry-run", action="store_true", help="Validate and simulate insertion without modifying database.")
    parser.add_argument("--dir", default="database/extracted", help="Path to directory containing JSON files.")
    args = parser.parse_args()

    run_import(base_dir=args.dir, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
