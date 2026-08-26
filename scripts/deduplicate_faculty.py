"""Deduplicate faculty records in Supabase and local JSON, retaining the single canonical identity per person."""

import json
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.abspath("."))

from backend.supabase_client import db
from backend.utils.normalization import normalize_text


def deduplicate():
    print("--- 1. Loading Supabase faculty records ---")
    facs = db.query_table("faculty")
    print(f"Total faculty rows in Supabase: {len(facs)}")

    with open("database/extracted/counsellors.json", "r", encoding="utf-8") as f:
        counsellors = json.load(f)
    with open("database/extracted/academic_support.json", "r", encoding="utf-8") as f:
        academic_support = json.load(f)
    with open("database/extracted/departments.json", "r", encoding="utf-8") as f:
        departments = json.load(f)

    referenced_ids = set()
    for c in counsellors:
        if c.get("faculty_id"):
            referenced_ids.add(c["faculty_id"])
    for a in academic_support:
        if a.get("faculty_id"):
            referenced_ids.add(a["faculty_id"])
    for d in departments:
        if d.get("hod_faculty_id"):
            referenced_ids.add(d["hod_faculty_id"])

    print(f"Referenced foreign key faculty IDs: {len(referenced_ids)}")

    by_name = defaultdict(list)
    for f in facs:
        by_name[normalize_text(f["full_name"])].append(f)

    canonical_faculty = []
    ids_to_delete = []

    for name_norm, records in by_name.items():
        if len(records) == 1:
            canonical_faculty.append(records[0])
            continue

        # Choose the best canonical record:
        # Priority 1: Record referenced in foreign keys
        # Priority 2: Record with verified poster room
        # Priority 3: Record with empcode/email
        sorted_records = sorted(
            records,
            key=lambda r: (
                1 if r["id"] in referenced_ids else 0,
                1 if r.get("room") else 0,
                1 if r.get("empcode") else 0,
                1 if r.get("email") else 0
            ),
            reverse=True
        )

        canonical = sorted_records[0]
        duplicates = sorted_records[1:]

        # Merge metadata from duplicates into canonical
        for d in duplicates:
            ids_to_delete.append(d["id"])
            if not canonical.get("empcode") and d.get("empcode"):
                canonical["empcode"] = d["empcode"]
            if not canonical.get("email") and d.get("email"):
                canonical["email"] = d["email"]
            if not canonical.get("phone") and d.get("phone"):
                canonical["phone"] = d["phone"]
            if not canonical.get("room") and d.get("room"):
                canonical["room"] = d["room"]
            if not canonical.get("profile_url") and d.get("profile_url"):
                canonical["profile_url"] = d["profile_url"]
            if not canonical.get("research_interests") and d.get("research_interests"):
                canonical["research_interests"] = d["research_interests"]
            if not canonical.get("teaching_engagements") and d.get("teaching_engagements"):
                canonical["teaching_engagements"] = d["teaching_engagements"]
            if not canonical.get("academic_profile") and d.get("academic_profile"):
                canonical["academic_profile"] = d["academic_profile"]
            if not canonical.get("conflicting_sources") and d.get("conflicting_sources"):
                canonical["conflicting_sources"] = d["conflicting_sources"]

        canonical_faculty.append(canonical)

    print(f"Duplicates to delete: {len(ids_to_delete)}")
    print(f"Canonical faculty to retain: {len(canonical_faculty)}")

    # Delete redundant duplicates from Supabase
    if ids_to_delete and db.is_connected():
        for d_id in ids_to_delete:
            db.client.table("faculty").delete().eq("id", d_id).execute()
        print(f"  [OK] Deleted {len(ids_to_delete)} duplicate rows from Supabase")

    # Upsert clean canonical faculty
    if db.is_connected():
        for i in range(0, len(canonical_faculty), 50):
            batch = canonical_faculty[i:i+50]
            db.client.table("faculty").upsert(batch).execute()
        print(f"  [OK] Upserted {len(canonical_faculty)} clean canonical faculty records")

    # Update extracted JSON
    with open("database/extracted/faculty.json", "w", encoding="utf-8") as f:
        json.dump(canonical_faculty, f, indent=2, ensure_ascii=False)

    print("Deduplication complete!")


if __name__ == "__main__":
    deduplicate()
