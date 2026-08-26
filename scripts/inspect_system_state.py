"""Inspect current database records, HOD relationships, services, offices, locations, and tool setup."""

import os
import sys
import json

sys.path.insert(0, os.path.abspath("."))

from backend.supabase_client import db

def inspect():
    print("==================================================")
    print("PART 1 — SYSTEM INSPECTION REPORT")
    print("==================================================")

    # 1. Departments & HODs
    print("\n--- 1. DEPARTMENTS & HOD ASSIGNMENTS ---")
    depts = db.query_table("departments")
    fac_all = {f["id"]: f for f in db.query_table("faculty")}

    for d in depts:
        hod_id = d.get("hod_faculty_id")
        hod_info = "NO_HOD_SET"
        if hod_id:
            if hod_id in fac_all:
                f = fac_all[hod_id]
                hod_info = f"{f.get('full_name')} (ID: {f.get('id')}, Email: {f.get('email')}, Empcode: {f.get('empcode')})"
            else:
                hod_info = f"INVALID_ORPHAN_FK (ID: {hod_id})"
        print(f"• [{d.get('code')}] {d.get('name')}: HOD -> {hod_info}")

    # 2. Services
    print("\n--- 2. SERVICES ---")
    services = db.query_table("services")
    for s in services:
        print(f"• {s.get('name')} | Cat: {s.get('category')} | Block: {s.get('block')} | Loc: {s.get('location_description')}")

    # 3. Offices
    print("\n--- 3. OFFICES ---")
    offices = db.query_table("offices")
    for o in offices:
        print(f"• {o.get('name')} | Block: {o.get('block')} | Floor: {o.get('floor')} | Room: {o.get('room')}")

    # 4. Locations
    print("\n--- 4. LOCATIONS ---")
    locs = db.query_table("locations")
    for l in locs:
        print(f"• {l.get('name')} | Block: {l.get('block')} | Type: {l.get('type')}")

    # 5. Check IT Department specifically
    print("\n--- 5. IT DEPARTMENT & IT FACULTY ---")
    it_depts = [d for d in depts if d.get("code") == "IT" or "Information Technology" in d.get("name", "")]
    for itd in it_depts:
        print(f"IT Dept: {itd}")
    it_fac = [f for f in fac_all.values() if f.get("department_id") in [d["id"] for d in it_depts]]
    print(f"Faculty linked to IT Dept: {len(it_fac)}")
    for f in it_fac[:5]:
        print(f"  - {f.get('full_name')} ({f.get('designation')}, Room: {f.get('room')}, Phone: {f.get('phone')})")

    # 6. Check MHP / Main Canteen
    print("\n--- 6. MHP / CANTEEN RECORDS ---")
    mhp_srv = [s for s in services if "mhp" in s.get("name", "").lower() or "canteen" in s.get("name", "").lower()]
    for s in mhp_srv:
        print(f"  Service: {s.get('name')} -> {s.get('location_description')} ({s.get('block')})")
    mhp_loc = [l for l in locs if "mhp" in l.get("name", "").lower() or "canteen" in l.get("name", "").lower()]
    for l in mhp_loc:
        print(f"  Location: {l.get('name')} -> {l.get('block')} ({l.get('type')})")

if __name__ == "__main__":
    inspect()
