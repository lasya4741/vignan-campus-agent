"""Extract all official HODs and IT faculty from people.php JSON array."""

import urllib.request
import re
import json

def extract_hods():
    url = "https://vignan.ac.in/newvignan/people.php"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        html = resp.read().decode("utf-8", errors="ignore")

    start = html.find('[{"id":')
    if start == -1:
        print("Could not find start of faculty JSON array")
        return

    end = html.find("];", start)
    if end == -1:
        print("Could not find end of faculty JSON array")
        return

    raw_json = html[start:end+1]
    all_fac = json.loads(raw_json)
    print(f"Total faculty loaded from official website: {len(all_fac)}")

    hods = []
    for f in all_fac:
        adminpos = str(f.get("adminpos") or "").upper()
        desig = str(f.get("desig") or "").upper()
        if "HOD" in adminpos or "HOD" in desig or "HEAD" in adminpos:
            hods.append(f)

    print(f"\n--- OFFICIAL HODs FOUND ({len(hods)}) ---")
    for h in hods:
        sal = (h.get("salutation") or "").strip()
        name = (h.get("name") or "").strip()
        full_name = f"{sal}. {name}".strip() if sal else name
        branch = h.get("branch")
        empcode = h.get("empcode")
        email = h.get("email")
        personalemail = h.get("personalemail")
        contact = h.get("personalcontact") or h.get("contact")
        print(f"• Dept/Branch: {branch:10} | Name: {full_name:30} | Empcode: {empcode:6} | Email: {email} | Contact: {contact}")

    # Also list all faculty in IT branch specifically
    it_fac = [f for f in all_fac if str(f.get("branch", "")).upper() == "IT" or "INFORMATION TECH" in str(f.get("branch", "")).upper()]
    print(f"\n--- ALL IT FACULTY FOUND ({len(it_fac)}) ---")
    for f in it_fac:
        sal = (f.get("salutation") or "").strip()
        name = (f.get("name") or "").strip()
        full_name = f"{sal}. {name}".strip() if sal else name
        print(f"• IT Faculty: {full_name:30} | Desig: {f.get('desig'):20} | AdminPos: {f.get('adminpos'):10} | Email: {f.get('email')} | Contact: {f.get('personalcontact')}")

    # Save to a local json file for inspection and ingestion
    with open("database/raw/official_all_hods.json", "w", encoding="utf-8") as f_out:
        json.dump({"hods": hods, "it_faculty": it_fac}, f_out, indent=2)

if __name__ == "__main__":
    extract_hods()
