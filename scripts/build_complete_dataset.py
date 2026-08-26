"""Complete VIGNAN Dataset Generator.
Combines:
  - Phase 1: Verified Department Posters
  - Phase 2: Official VIGNAN Website (Faculty, HODs, Subjects)
  - Phase 3: Project-Owner Campus-Verified Locations & Services
"""

import json
import os
import re
import uuid

EXTRACTED_DIR = "database/extracted"
os.makedirs(EXTRACTED_DIR, exist_ok=True)

def gen_uuid(key: str) -> str:
    """Generate deterministic UUID from string key."""
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"vignan.ac.in/{key}"))

# ============================================================================
# 1. SOURCES
# ============================================================================
SOURCES = [
    # Posters (Phase 1)
    {
        "id": gen_uuid("src-dept-venues"),
        "source_type": "department_verified",
        "source_name": "CSE Department Venue Sheet",
        "document_name": "department_venues.jpg",
        "verified_at": "2026-08-26T00:00:00Z",
        "description": "Department Venues and Building Floor Mappings",
    },
    {
        "id": gen_uuid("src-year2-counsellors"),
        "source_type": "department_verified",
        "source_name": "CSE II Year Counsellor Poster",
        "document_name": "year2_counsellors.jpg",
        "verified_at": "2026-08-26T00:00:00Z",
        "description": "II Year Section-Wise Counsellors and Registration Ranges",
    },
    {
        "id": gen_uuid("src-year3-counsellors"),
        "source_type": "department_verified",
        "source_name": "CSE III Year Counsellor Poster",
        "document_name": "year3_counsellors.jpg",
        "verified_at": "2026-08-26T00:00:00Z",
        "description": "III Year Section-Wise Counsellors and Seating Rooms",
    },
    {
        "id": gen_uuid("src-academic-leads"),
        "source_type": "department_verified",
        "source_name": "CSE III Year Academic Leads Poster",
        "document_name": "academic_leads.jpg",
        "verified_at": "2026-08-26T00:00:00Z",
        "description": "III Year Academic Leads, Roles and Coordinators",
    },
    {
        "id": gen_uuid("src-bosa-boa-boe-tp"),
        "source_type": "department_verified",
        "source_name": "CSE BoSA BoA BoE T&P Poster",
        "document_name": "bosa_boa_boe_tp.jpg",
        "verified_at": "2026-08-26T00:00:00Z",
        "description": "BoSA, BoA, BoE, and T&P CSE Boards and Room 409 Meeting Info",
    },
    {
        "id": gen_uuid("src-dept-committees"),
        "source_type": "department_verified",
        "source_name": "CSE Department Committees Poster",
        "document_name": "department_committees.jpg",
        "verified_at": "2026-08-26T00:00:00Z",
        "description": "Social Media and Magazine Committees & Overall Coordinator",
    },
    # Official Website (Phase 2)
    {
        "id": gen_uuid("src-official-website"),
        "source_type": "official_website",
        "source_name": "VIGNAN University Official Website",
        "source_url": "https://vignan.ac.in",
        "verified_at": "2026-08-26T00:00:00Z",
        "description": "Official institutional portal for VFSTR (Deemed to be University)",
    },
    # Campus Verified Observations (Phase 3)
    {
        "id": gen_uuid("src-campus-verified"),
        "source_type": "campus_verified",
        "source_name": "VIGNAN Project-Owner Campus Observations",
        "verified_at": "2026-08-26T00:00:00Z",
        "description": "Project-owner verified on-campus physical locations, offices, canteens, and Xerox facilities",
    },
]

SRC_MAP = {s["source_name"]: s["id"] for s in SOURCES}
SRC_VENUES = SRC_MAP["CSE Department Venue Sheet"]
SRC_Y2 = SRC_MAP["CSE II Year Counsellor Poster"]
SRC_Y3 = SRC_MAP["CSE III Year Counsellor Poster"]
SRC_LEADS = SRC_MAP["CSE III Year Academic Leads Poster"]
SRC_BOARDS = SRC_MAP["CSE BoSA BoA BoE T&P Poster"]
SRC_COMM = SRC_MAP["CSE Department Committees Poster"]
SRC_WEB = SRC_MAP["VIGNAN University Official Website"]
SRC_CAMPUS = SRC_MAP["VIGNAN Project-Owner Campus Observations"]

# ============================================================================
# 2. LOCATIONS
# ============================================================================
LOCATIONS = [
    # Primary Campus Buildings
    {
        "id": gen_uuid("loc-n-block"),
        "name": "N Block",
        "location_type": "building",
        "block": "N Block",
        "description": "N Block Academic Building (6 floors and 1 basement)",
        "source_id": SRC_CAMPUS,
        "confidence": "high",
        "last_verified": "2026-08-26T00:00:00Z",
    },
    {
        "id": gen_uuid("loc-u-block"),
        "name": "U Block",
        "location_type": "building",
        "block": "U Block",
        "description": "U Block Academic Building (4 floors including ground)",
        "source_id": SRC_CAMPUS,
        "confidence": "high",
        "last_verified": "2026-08-26T00:00:00Z",
    },
    {
        "id": gen_uuid("loc-h-block"),
        "name": "H Block",
        "location_type": "building",
        "block": "H Block",
        "description": "H Block Academic Building (4 floors)",
        "source_id": SRC_CAMPUS,
        "confidence": "high",
        "last_verified": "2026-08-26T00:00:00Z",
    },
    {
        "id": gen_uuid("loc-a-block"),
        "name": "A Block",
        "location_type": "building",
        "block": "A Block",
        "description": "A Block Academic & Administrative Building",
        "source_id": SRC_CAMPUS,
        "confidence": "high",
        "last_verified": "2026-08-26T00:00:00Z",
    },
    {
        "id": gen_uuid("loc-pharmacy-block"),
        "name": "Pharmacy Block",
        "location_type": "building",
        "block": "Pharmacy Block",
        "description": "Pharmacy Block building and laboratories",
        "source_id": SRC_CAMPUS,
        "confidence": "high",
        "last_verified": "2026-08-26T00:00:00Z",
    },
    {
        "id": gen_uuid("loc-textile-block"),
        "name": "Textile Block",
        "location_type": "building",
        "block": "Textile Block",
        "description": "Textile Engineering Block",
        "source_id": SRC_VENUES,
        "confidence": "high",
        "last_verified": "2026-08-26T00:00:00Z",
    },
    {
        "id": gen_uuid("loc-main-gate"),
        "name": "Main Gate",
        "location_type": "gate",
        "block": "Campus Entrance",
        "description": "Main campus gate and vehicle entrance",
        "source_id": SRC_CAMPUS,
        "confidence": "high",
        "last_verified": "2026-08-26T00:00:00Z",
    },
    # Specific Department Rooms in N Block
    {
        "id": gen_uuid("loc-room-301"),
        "name": "Room No. 301",
        "location_type": "room",
        "block": "N Block",
        "floor": "3rd Floor",
        "room": "301",
        "parent_location_id": gen_uuid("loc-n-block"),
        "description": "Social Media Coordinators Meeting Room & Faculty Seating",
        "source_id": SRC_COMM,
        "confidence": "high",
        "last_verified": "2026-08-26T00:00:00Z",
    },
    {
        "id": gen_uuid("loc-room-310"),
        "name": "Room No. 310",
        "location_type": "room",
        "block": "N Block",
        "floor": "3rd Floor",
        "room": "310",
        "parent_location_id": gen_uuid("loc-n-block"),
        "description": "Magazine Committee Meeting Room & Faculty Seating",
        "source_id": SRC_COMM,
        "confidence": "high",
        "last_verified": "2026-08-26T00:00:00Z",
    },
    {
        "id": gen_uuid("loc-room-409"),
        "name": "Room No. 409",
        "location_type": "room",
        "block": "N Block",
        "floor": "4th Floor",
        "room": "409",
        "parent_location_id": gen_uuid("loc-n-block"),
        "description": "BoSA, BoA, BoE, T&P CSE Meeting Room & Faculty Seating",
        "source_id": SRC_BOARDS,
        "confidence": "high",
        "last_verified": "2026-08-26T00:00:00Z",
    },
    # A Block Specific Floors / Offices (Phase 3)
    {
        "id": gen_uuid("loc-a-block-f1-finance"),
        "name": "Finance Office (A Block 1st Floor)",
        "location_type": "office",
        "block": "A Block",
        "floor": "1st Floor",
        "parent_location_id": gen_uuid("loc-a-block"),
        "description": "University Finance & Fee Payment Office on A Block 1st Floor",
        "source_id": SRC_CAMPUS,
        "confidence": "high",
        "last_verified": "2026-08-26T00:00:00Z",
    },
    {
        "id": gen_uuid("loc-a-block-f2-software"),
        "name": "Software Departments (A Block 2nd Floor)",
        "location_type": "department",
        "block": "A Block",
        "floor": "2nd Floor",
        "parent_location_id": gen_uuid("loc-a-block"),
        "description": "Software-related departments and labs on A Block 2nd Floor",
        "source_id": SRC_CAMPUS,
        "confidence": "high",
        "last_verified": "2026-08-26T00:00:00Z",
    },
    {
        "id": gen_uuid("loc-a-block-f3-math"),
        "name": "Mathematics & Science Faculty (A Block 3rd Floor)",
        "location_type": "department",
        "block": "A Block",
        "floor": "3rd Floor",
        "parent_location_id": gen_uuid("loc-a-block"),
        "description": "Mathematics and basic science faculty rooms on A Block 3rd Floor",
        "source_id": SRC_CAMPUS,
        "confidence": "high",
        "last_verified": "2026-08-26T00:00:00Z",
    },
    {
        "id": gen_uuid("loc-a-block-hod-cabin"),
        "name": "First Year HOD Cabin (A Block)",
        "location_type": "office",
        "block": "A Block",
        "parent_location_id": gen_uuid("loc-a-block"),
        "description": "First-year HOD office cabin located in A Block",
        "source_id": SRC_CAMPUS,
        "confidence": "high",
        "last_verified": "2026-08-26T00:00:00Z",
    },
    {
        "id": gen_uuid("loc-transport-office"),
        "name": "Transport Office (Main Gate)",
        "location_type": "office",
        "block": "Main Gate Area",
        "description": "Transport Office located on the left side of the main entrance when viewed from outside the gate; used for bus pass collection and transport inquiries",
        "source_id": SRC_CAMPUS,
        "confidence": "high",
        "last_verified": "2026-08-26T00:00:00Z",
    },
]

# ============================================================================
# 3. DEPARTMENTS & FACULTY (Merging Website + Poster Data)
# ============================================================================
DEPARTMENTS_DATA = [
    {"key": "dept-cse-core", "name": "Computer Science & Engineering (Core)", "short_name": "CSE {CORE}", "block": "N Block", "floor_information": "3,4,5 Floors", "hod_name": "Dr. Yarlagadda Jyothi", "hod_email": "hod_cse@vignan.ac.in", "desc": "Department of Computer Science & Engineering (Core)", "source_id": SRC_VENUES},
    {"key": "dept-cse-spec", "name": "Computer Science & Engineering (Specializations)", "short_name": "CSE {SPECIALIZATIONS}", "block": "N Block", "floor_information": "5,6 Floors", "hod_name": "Dr. Yarlagadda Jyothi", "hod_email": "hod_cse@vignan.ac.in", "desc": "CSE Specializations (AI & ML, Cyber Security, Data Science, CSBS)", "source_id": SRC_VENUES},
    {"key": "dept-it", "name": "Information Technology", "short_name": "IT", "block": "U Block", "floor_information": "3rd Floor", "hod_name": "Dr. Kamepalli Sujatha", "hod_email": "hod_it@vignan.ac.in", "desc": "Department of Information Technology", "source_id": SRC_VENUES},
    {"key": "dept-ece", "name": "Electronics & Communication Engineering", "short_name": "ECE", "block": "H Block", "floor_information": "2nd Floor", "hod_name": "Dr. T. Pitchaiah", "hod_email": "hod_ece@vignan.ac.in", "desc": "Department of Electronics & Communication Engineering", "source_id": SRC_VENUES},
    {"key": "dept-eee", "name": "Electrical & Electronics Engineering", "short_name": "EEE", "block": "H Block", "floor_information": "1st Floor", "hod_name": "Dr. P.V.S. Shobhan", "hod_email": "hod_eee@vignan.ac.in", "desc": "Department of Electrical & Electronics Engineering", "source_id": SRC_VENUES},
    {"key": "dept-mech", "name": "Mechanical Engineering", "short_name": "MECHANICAL", "block": "U Block", "floor_information": "Ground Floor", "hod_name": "Dr. T. Ch. Anil Kumar", "hod_email": "hod_mech@vignan.ac.in", "desc": "Department of Mechanical Engineering", "source_id": SRC_VENUES},
    {"key": "dept-civil", "name": "Civil Engineering", "short_name": "CIVIL", "block": "U Block", "floor_information": "1st Floor", "hod_name": "Dr. P. Sundara Kumar", "hod_email": "hod_civil@vignan.ac.in", "desc": "Department of Civil Engineering", "source_id": SRC_VENUES},
    {"key": "dept-chem", "name": "Chemical Engineering", "short_name": "CHEMICAL", "block": "H Block", "floor_information": "1st Floor", "hod_name": "Dr. M. Ramesh Naidu", "hod_email": "hod_chem@vignan.ac.in", "desc": "Department of Chemical Engineering", "source_id": SRC_VENUES},
    {"key": "dept-biotech", "name": "Biotechnology", "short_name": "BIO TECHNOLOGY", "block": "U Block", "floor_information": "2nd Floor", "hod_name": "Dr. T. C. Venkateswarlu", "hod_email": "hod_biotech@vignan.ac.in", "desc": "Department of Biotechnology", "source_id": SRC_VENUES},
    {"key": "dept-agri", "name": "Agriculture Engineering", "short_name": "AGRICULTURE", "block": "N Block", "floor_information": "1,2 Floors", "hod_name": "Dr. N. Narayana Rao", "hod_email": "hod_agri@vignan.ac.in", "desc": "Department of Agriculture", "source_id": SRC_VENUES},
    {"key": "dept-mgmt", "name": "Management Studies", "short_name": "MANAGEMENT STUDIES", "block": "U Block", "floor_information": "4th Floor", "hod_name": "Dr. Sarita Satpathy", "hod_email": "hod_mgmt@vignan.ac.in", "desc": "Department of Management Studies", "source_id": SRC_VENUES},
    {"key": "dept-biomed", "name": "Biomedical Engineering", "short_name": "BIO-MEDICAL", "block": "H Block", "floor_information": "3rd Floor", "hod_name": None, "hod_email": None, "desc": "Department of Biomedical Engineering", "source_id": SRC_VENUES},
    {"key": "dept-foodtech", "name": "Food Technology", "short_name": "FOOD TECH", "block": "H Block", "floor_information": "Ground & 1st Floor", "hod_name": None, "hod_email": None, "desc": "Department of Food Technology", "source_id": SRC_VENUES},
    {"key": "dept-robotics", "name": "Robotics Engineering", "short_name": "ROBOTICS", "block": "U Block", "floor_information": "Ground Floor", "hod_name": None, "hod_email": None, "desc": "Department of Robotics", "source_id": SRC_VENUES},
    {"key": "dept-law", "name": "Law", "short_name": "LAW", "block": "U Block", "floor_information": "1st Floor", "hod_name": None, "hod_email": None, "desc": "School of Law", "source_id": SRC_VENUES},
    {"key": "dept-bioinfo", "name": "Bioinformatics", "short_name": "BIO INFORMATICS", "block": "U Block", "floor_information": "2nd Floor", "hod_name": None, "hod_email": None, "desc": "Department of Bioinformatics", "source_id": SRC_VENUES},
    {"key": "dept-ca", "name": "Computer Applications", "short_name": "COMPUTER APPLICATIONS", "block": "U Block", "floor_information": "4th Floor", "hod_name": None, "hod_email": None, "desc": "Department of Computer Applications (MCA/BCA)", "source_id": SRC_VENUES},
    {"key": "dept-textile", "name": "Textile Engineering", "short_name": "TEXTILE", "block": "Textile Block", "floor_information": "Textile Block", "hod_name": None, "hod_email": None, "desc": "Department of Textile Technology", "source_id": SRC_VENUES},
]

FACULTY_MAP = {}

def get_or_create_faculty(name, department_key="dept-cse-core", phone=None, room=None, email=None, designation=None, source_id=SRC_Y2, profile_url=None):
    norm_key = re.sub(r"[^a-zA-Z]", "", name.lower())
    if not norm_key:
        return None

    alias_map = {
        "drrenugadevi": "drrenugadevi",
        "drrrenugadevi": "drrenugadevi",
        "drrprathapkumar": "drrprathapkumar",
        "drprataapkumar": "drrprathapkumar",
        "drbalunarasimharao": "drgbalunarasimharao",
        "drgbalunarasimharao": "drgbalunarasimharao",
        "msleelavathi": "mrstanigundalaleelavathy",
        "mrstanigundalaleelavathy": "mrstanigundalaleelavathy",
        "mrpvijayababu": "mrpvijayababu",
        "mrdbalakotaiah": "mrdbalakotaiah",
        "mrkiriakumarkalagadda": "mrkkirankumar",
        "mrkkirankumar": "mrkkirankumar",
        "mreakhilbabu": "mreakhilbabu",
        "mrsarchananalluri": "mrsarchananalluri",
        "mrogandhi": "mrongolegandhi",
        "mrongolegandhi": "mrongolegandhi",
        "mrsgnavya": "mrsguggilamnavya",
        "msgnavya": "mrsguggilamnavya",
        "mrsguggilamnavya": "mrsguggilamnavya",
        "mrskjani": "mrskjani",
        "skjani": "mrskjani",
    }
    canon_key = alias_map.get(norm_key, norm_key)

    if canon_key not in FACULTY_MAP:
        fid = gen_uuid(f"faculty-{canon_key}")
        FACULTY_MAP[canon_key] = {
            "id": fid,
            "full_name": name,
            "designation": designation,
            "department_id": gen_uuid(department_key) if department_key else None,
            "email": email,
            "phone": phone,
            "room": room,
            "block": "N Block" if room and room.startswith("NB-") else ("N Block" if room in ["301", "310", "409"] else None),
            "floor": None,
            "profile_url": profile_url,
            "source_id": source_id,
            "confidence": "high",
            "last_verified": "2026-08-26T00:00:00Z",
        }
    else:
        f = FACULTY_MAP[canon_key]
        if phone and not f["phone"]: f["phone"] = phone
        if room and not f["room"]: f["room"] = room
        if email and not f["email"]: f["email"] = email
        if designation and not f["designation"]: f["designation"] = designation
        if profile_url and not f["profile_url"]: f["profile_url"] = profile_url

    return FACULTY_MAP[canon_key]["id"]

# Add HODs (Phase 2 Official Website)
for d in DEPARTMENTS_DATA:
    if d["hod_name"]:
        hid = get_or_create_faculty(
            name=d["hod_name"],
            department_key=d["key"],
            email=d["hod_email"],
            designation="Professor & Head of Department",
            source_id=SRC_WEB,
            profile_url=f"https://vignan.ac.in"
        )
        d["hod_faculty_id"] = hid
    else:
        d["hod_faculty_id"] = None

DEPARTMENTS = [
    {
        "id": gen_uuid(d["key"]),
        "name": d["name"],
        "short_name": d["short_name"],
        "description": d["desc"],
        "block": d["block"],
        "floor_information": d["floor_information"],
        "hod_faculty_id": d["hod_faculty_id"],
        "source_id": d["source_id"],
        "confidence": "high",
        "last_verified": "2026-08-26T00:00:00Z",
    }
    for d in DEPARTMENTS_DATA
]

# ============================================================================
# 4. COUNSELLORS (Phase 1 Posters)
# ============================================================================
YEAR2_COUNSELLORS_RAW = [
    {"year": 2, "sec": "1", "name": "Dr. Md. Oqail Ahmad", "phone": "8439243408", "room": "NB-410", "r_start": "4001", "r_end": "4071"},
    {"year": 2, "sec": "1", "name": "Mr. Hitendra Singh", "phone": "8529127355", "room": "NB-420", "r_start": "4073", "r_end": "4132"},
    {"year": 2, "sec": "1", "name": "Ms. Shaik Nazeera", "phone": "9618896300", "room": "NB-401A", "r_start": "4134", "r_end": "4175"},
    {"year": 2, "sec": "2", "name": "Dr. B. Suvarna", "phone": "7093171146", "room": "NB-409", "r_start": "4116", "r_end": "4315"},
    {"year": 2, "sec": "2", "name": "Mrs. Archana Nalluri", "phone": "8985716984", "room": "NB-320", "r_start": "4316", "r_end": "4805"},
    {"year": 2, "sec": "3", "name": "Mrs. Sd. Shareefunnisa", "phone": "8074308730", "room": "NB-403", "r_start": "4458", "r_end": "4560"},
    {"year": 2, "sec": "3", "name": "Ms. Tupakula Tahera", "phone": "9347667759", "room": "NB-420", "r_start": "4562", "r_end": "4634"},
    {"year": 2, "sec": "3", "name": "Ms. Kalluri Mercy Bhikshvathi", "phone": "9014592698", "room": "NB-520", "r_start": "4635", "r_end": "4H12"},
    {"year": 2, "sec": "4", "name": "Mrs. M. Bhargavi", "phone": "7095812130", "room": "NB-403", "r_start": "4212", "r_end": "4757"},
    {"year": 2, "sec": "4", "name": "Mr. Swetabh Sinhku", "phone": "7893038516", "room": "NB-313", "r_start": "4762", "r_end": "4829"},
    {"year": 2, "sec": "4", "name": "Mrs. Polepali Sai Veera Venkata Samhitha", "phone": "7337475699", "room": "NB-320", "r_start": "4835", "r_end": "4G97"},
    {"year": 2, "sec": "5", "name": "Ms. Gudipati Sravya", "phone": "8897176559", "room": "NB-410", "r_start": "4069", "r_end": "4A03"},
    {"year": 2, "sec": "5", "name": "Mr. Adavi Aditya Venkateswara Kumar", "phone": "6301666022", "room": "NB-520", "r_start": "4A05", "r_end": "4165"},
    {"year": 2, "sec": "6", "name": "Dr. Prashant Upadhyay", "phone": "9805406546", "room": "NB-310", "r_start": "4026", "r_end": "4893"},
    {"year": 2, "sec": "6", "name": "Ms. Muhammad Gulshan Firdous", "phone": "6281590963", "room": "NB-420", "r_start": "4897", "r_end": "4C72"},
    {"year": 2, "sec": "6", "name": "Ms. Y. Sesha Naga Bindu Lalitha Sri", "phone": "8712269324", "room": "NB-520", "r_start": "4C77", "r_end": "4194"},
    {"year": 2, "sec": "7", "name": "Mr. Talluri Latesh Babu", "phone": "9550818722", "room": "NB-510", "r_start": "4131", "r_end": "4E50"},
    {"year": 2, "sec": "7", "name": "Ms. G. Siva Naga Malleswari", "phone": "6300448477", "room": "NB-420", "r_start": "4E51", "r_end": "4G38"},
    {"year": 2, "sec": "8", "name": "Dr. T. R. Rajesh", "phone": "9676560542", "room": "NB-509", "r_start": "4035", "r_end": "4G27"},
    {"year": 2, "sec": "8", "name": "Mr. Loganathan M", "phone": "9976418789", "room": "NB-520", "r_start": "4G44", "r_end": "4140"},
    {"year": 2, "sec": "9", "name": "Mr. Syed Nafees Ahamed", "phone": "8790469105", "room": "NB-401A", "r_start": "4091", "r_end": "4144"},
    {"year": 2, "sec": "9", "name": "Ms. Kollabathula Nimnagasri", "phone": "7642481619", "room": "NB-420", "r_start": "4145", "r_end": "4197"},
    {"year": 2, "sec": "9", "name": "Mr. Maturi Ashok Gupta", "phone": "9247294748", "room": "NB-304", "r_start": "261LA4001", "r_end": "261LA4028"},
    {"year": 2, "sec": "10", "name": "Mr. U. Venkateswara Rao", "phone": "9966259492", "room": "NB-301A", "r_start": "4005", "r_end": "4072"},
    {"year": 2, "sec": "10", "name": "Mr. Gudipati Rishi Kesava", "phone": "8919250534", "room": "NB-420", "r_start": "4074", "r_end": "4161"},
    {"year": 2, "sec": "11", "name": "Mr. Kiran Kumar Kalagadda", "phone": "9494965571", "room": "NB-403", "r_start": "4043", "r_end": "4225"},
    {"year": 2, "sec": "11", "name": "Ms. Marella Sirisha", "phone": "8008990401", "room": "NB-520", "r_start": "4226", "r_end": "4295"},
    {"year": 2, "sec": "11", "name": "Ms. Vutukuri Geetha Nagalakshmi", "phone": "8106350764", "room": "NB-420", "r_start": "4296", "r_end": "4H43"},
    {"year": 2, "sec": "12", "name": "Ms. Yeminani Sravani", "phone": "7032293225", "room": "NB-510", "r_start": "4054", "r_end": "4399"},
    {"year": 2, "sec": "12", "name": "Mr. Mihir Bhatt", "phone": "8840896873", "room": "NB-420", "r_start": "4401", "r_end": "4462"},
    {"year": 2, "sec": "12", "name": "Dr. G. Saubhagya Ranjan Biswal", "phone": "9525588508", "room": "NB-310", "r_start": "4466", "r_end": "4803"},
    {"year": 2, "sec": "13", "name": "Ms. Pavani Karra", "phone": "9100234298", "room": "NB-520", "r_start": "4112", "r_end": "4614"},
    {"year": 2, "sec": "13", "name": "Ms. Kolli Bhavya Sri", "phone": "9346464229", "room": "NB-520", "r_start": "4617", "r_end": "4C20"},
    {"year": 2, "sec": "14", "name": "Dr. M. Sunil Babu", "phone": "8333001991", "room": "NB-509", "r_start": "4162", "r_end": "4804"},
    {"year": 2, "sec": "14", "name": "Mr. Sourav Mondal", "phone": "9631422643", "room": "NB-310", "r_start": "4807", "r_end": "4874"},
    {"year": 2, "sec": "15", "name": "Mrs. S. Anitha", "phone": "9505044559", "room": "NB-301A", "r_start": "4004", "r_end": "4096"},
    {"year": 2, "sec": "15", "name": "Mr. Shyam Sundar Jannu Soloman", "phone": "7995624716", "room": "NB-401A", "r_start": "4099", "r_end": "4148"},
    {"year": 2, "sec": "16", "name": "Dr. Gabbi Reddy Keerthi", "phone": "9491139513", "room": "NB-509", "r_start": "4127", "r_end": "4C06"},
    {"year": 2, "sec": "16", "name": "Ms. Shaik Charishma", "phone": "8247490119", "room": "NB-320", "r_start": "4C13", "r_end": "4F35"},
    {"year": 2, "sec": "17", "name": "Mrs. Tanigundala Leelavathy", "phone": "8919420637", "room": "NB-409", "r_start": "4125", "r_end": "4E35"},
    {"year": 2, "sec": "17", "name": "Ms. P. Deepthi Sowmya", "phone": "9100967181", "room": "NB-520", "r_start": "4E39", "r_end": "4F71"},
    {"year": 2, "sec": "18", "name": "Mrs. Ch. Swarna Lalitha", "phone": "6281716181", "room": "NB-520", "r_start": "4043", "r_end": "4084"},
    {"year": 2, "sec": "18", "name": "Ms. Pathan Razia Sultana", "phone": "9505246169", "room": "NB-420", "r_start": "4G50", "r_end": "261LA4033"},
    {"year": 2, "sec": "19", "name": "Mr. E. Akhil Babu", "phone": "8465999059", "room": "NB-401A", "r_start": "4662", "r_end": "4H96"},
    {"year": 2, "sec": "19", "name": "Mr. Anuvalasetty Naga Harshith Vardhan", "phone": "7075717333", "room": "NB-520", "r_start": "4102", "r_end": "261LA4032"},
]

YEAR3_COUNSELLORS_RAW = [
    {"year": 3, "sec": "1", "name": "Mr. Gujjula Murali", "phone": "9553116627", "room": "NB-410"},
    {"year": 3, "sec": "1", "name": "Ms. Gaddam Tejaswi", "phone": "9398046056", "room": "NB-401A"},
    {"year": 3, "sec": "2", "name": "Dr. R. Renugadevi", "phone": "9342247173", "room": "NB-403"},
    {"year": 3, "sec": "2", "name": "Ms. Peeka Anusha", "phone": "6309699033", "room": "NB-403"},
    {"year": 3, "sec": "3", "name": "Dr. Phanindra Thota", "phone": "8096465667", "room": "NB-403"},
    {"year": 3, "sec": "3", "name": "Mr. Lalu Naick. B", "phone": "7842061881", "room": "NB-320"},
    {"year": 3, "sec": "4", "name": "Dr. R. Prathap Kumar", "phone": "7569888963", "room": "NB-409"},
    {"year": 3, "sec": "4", "name": "Dr. M. Raja Rao", "phone": "8979803148", "room": "NB-410"},
    {"year": 3, "sec": "5", "name": "Ms. Upalanchi Vara Lakshmi", "phone": "8142214788", "room": "NB-520"},
    {"year": 3, "sec": "5", "name": "Mr. Shashi Mani", "phone": "9262978555", "room": "NB-401A"},
    {"year": 3, "sec": "6", "name": "Mr. Shaik Sikindar", "phone": "9581964409", "room": "NB-410"},
    {"year": 3, "sec": "6", "name": "Ms. Kandula Divya", "phone": "8328282185", "room": "NB-420"},
    {"year": 3, "sec": "7", "name": "Dr. O. Bhaskar", "phone": "6301577419", "room": "NB-510"},
    {"year": 3, "sec": "7", "name": "Ms. Vyshnavi Kagga", "phone": "9182743520", "room": "NB-210"},
    {"year": 3, "sec": "8", "name": "Dr. G. Balu Narasimha Rao", "phone": "9701224847", "room": "NB-409"},
    {"year": 3, "sec": "8", "name": "Mrs. Varagani Tejaswi", "phone": "6305179829", "room": "NB-401A"},
    {"year": 3, "sec": "9", "name": "Mr. Ongole Gandhi", "phone": "9701463728", "room": "NB-409"},
    {"year": 3, "sec": "9", "name": "Mr. Munipalli Veerendra", "phone": "9573632919", "room": "NB-210"},
    {"year": 3, "sec": "10", "name": "Mr. Sk. Khadersha", "phone": "8309300881", "room": "NB-520"},
    {"year": 3, "sec": "10", "name": "Ms. Bhimavarapu Jyothika", "phone": "7989366515", "room": "NB-210"},
    {"year": 3, "sec": "11", "name": "Mr. Bathula Anil Babu", "phone": "8688070939", "room": "NB-510"},
    {"year": 3, "sec": "11", "name": "Mr. Palavelli Vamsi Krishna", "phone": "6309663292", "room": "NB-210"},
    {"year": 3, "sec": "12", "name": "Mrs. D. Tipura", "phone": "8977267707", "room": "NB-303"},
    {"year": 3, "sec": "12", "name": "Mrs. Guggilam Navya", "phone": "7794993678", "room": "NB-409"},
    {"year": 3, "sec": "13", "name": "Mrs. Anusha Kakumanu", "phone": "7799053996", "room": "NB-410"},
    {"year": 3, "sec": "13", "name": "Ms. Ravuri Lalitha", "phone": "6302034022", "room": "NB-520"},
    {"year": 3, "sec": "14", "name": "Mr. Dega Balakotaiah", "phone": "9059093829", "room": "NB-409"},
    {"year": 3, "sec": "14", "name": "Ms. Swathi Koganti", "phone": "9491664577", "room": "NB-301A"},
    {"year": 3, "sec": "15", "name": "Ms. Yalavarthi Sai Eswari", "phone": "8074131669", "room": "NB-510"},
    {"year": 3, "sec": "15", "name": "Mr. Y. Rama Mohan", "phone": "9494399849", "room": "NB-510"},
    {"year": 3, "sec": "16", "name": "Dr. Chinna Gopi Simhadri", "phone": "9700330708", "room": "NB-520"},
    {"year": 3, "sec": "16", "name": "Dr. G. Veera Bhadra Chary", "phone": "8978975688", "room": "NB-410"},
    {"year": 3, "sec": "17", "name": "Mr. Madugula Anil", "phone": "9493322982", "room": "NB-410"},
    {"year": 3, "sec": "17", "name": "Ms. Arumalla Gopya Sri", "phone": "8919398629", "room": "NB-520"},
    {"year": 3, "sec": "18", "name": "Ms. Shaik Kareena Yashmin", "phone": "7801017820", "room": "NB-210"},
    {"year": 3, "sec": "18", "name": "Mr. Kudupudi Raj Kiran", "phone": "9542687850", "room": "NB-420"},
    {"year": 3, "sec": "19", "name": "Mr. D. Senthil", "phone": "8925096166", "room": "NB-301A"},
    {"year": 3, "sec": "19", "name": "Mr. Kanna Hareesh", "phone": "9948723118", "room": "NB-401A"},
    {"year": 3, "sec": "20", "name": "Mr. P. Venkata Rajulu", "phone": "9705021183", "room": "NB-303"},
    {"year": 3, "sec": "20", "name": "Mr. Shaik Dehtaj", "phone": "9010380116", "room": "NB-210"},
    {"year": 3, "sec": "21", "name": "Ms. Nese Bandhike Akhilandeswari", "phone": "9347927112", "room": "NB-210"},
    {"year": 3, "sec": "21", "name": "Ms. Annam Durga Bhavani", "phone": "9347927112", "room": "NB-210"},
    {"year": 3, "sec": "22", "name": "Dr. J. Veeranjaneyulu", "phone": "9492246551", "room": "NB-509"},
    {"year": 3, "sec": "22", "name": "Ms. Christiana Rose Elizabeth Korrapati", "phone": "7816092857", "room": "NB-420"},
]

COUNSELLORS = []
for c in YEAR2_COUNSELLORS_RAW:
    fid = get_or_create_faculty(c["name"], phone=c["phone"], room=c["room"], source_id=SRC_Y2)
    r_text = f"{c['r_start']} - {c['r_end']}" if c.get("r_start") and c.get("r_end") else None
    COUNSELLORS.append({
        "id": gen_uuid(f"couns-y2-s{c['sec']}-{c['name']}"),
        "academic_year": "2026-2027",
        "year": 2,
        "section": c["sec"],
        "counsellor_name": c["name"],
        "faculty_id": fid,
        "phone": c["phone"],
        "room": c["room"],
        "registration_range_start": c.get("r_start"),
        "registration_range_end": c.get("r_end"),
        "registration_range_text": r_text,
        "source_id": SRC_Y2,
        "confidence": "high",
        "last_verified": "2026-08-26T00:00:00Z",
    })

for c in YEAR3_COUNSELLORS_RAW:
    fid = get_or_create_faculty(c["name"], phone=c["phone"], room=c["room"], source_id=SRC_Y3)
    COUNSELLORS.append({
        "id": gen_uuid(f"couns-y3-s{c['sec']}-{c['name']}"),
        "academic_year": "2026-2027",
        "year": 3,
        "section": c["sec"],
        "counsellor_name": c["name"],
        "faculty_id": fid,
        "phone": c["phone"],
        "room": c["room"],
        "registration_range_start": None,
        "registration_range_end": None,
        "registration_range_text": None,
        "source_id": SRC_Y3,
        "confidence": "high",
        "last_verified": "2026-08-26T00:00:00Z",
    })

# ============================================================================
# 5. OFFICES & BOARDS
# ============================================================================
OFFICES = [
    {
        "id": gen_uuid("off-bosa-cse"),
        "name": "BoSA – Board of Student Affairs (CSE)",
        "purpose": "Student Club Activities & Events, Student Discipline Monitoring, Student Issues & Grievance Support, Student Achievements & OD Recommendations, Student Counselling & Guidance, Student Welfare Activities",
        "room": "409",
        "block": "N Block",
        "floor": "4th Floor",
        "phone": "9985333934",
        "email": None,
        "description": "Board of Student Affairs for CSE Department",
        "source_id": SRC_BOARDS,
        "confidence": "high",
        "last_verified": "2026-08-26T00:00:00Z",
    },
    {
        "id": gen_uuid("off-boa-cse"),
        "name": "BoA – Board of Academics (CSE)",
        "purpose": "Syllabus Coverage Monitoring, Course Progress Monitoring, Academic Credit Issues, Attendance Monitoring, Course Registration Support, Academic Regulations & Guidelines, Faculty-Student Academic Coordination, Value Added Courses Monitoring, Academic Queries and Support",
        "room": "409",
        "block": "N Block",
        "floor": "4th Floor",
        "phone": "9701463728",
        "email": None,
        "description": "Board of Academics for CSE Department",
        "source_id": SRC_BOARDS,
        "confidence": "high",
        "last_verified": "2026-08-26T00:00:00Z",
    },
    {
        "id": gen_uuid("off-boe-cse"),
        "name": "BoE – Board of Examinations (CSE)",
        "purpose": "Internal Examination Issues, Semester End Examination Queries, Hall Ticket Issues, Examination Registration, Revaluation & Challenge Valuation Guidance, Makeup/Supplementary Examination Support, Results & Grade Related Queries, Examination Notifications",
        "room": "409",
        "block": "N Block",
        "floor": "4th Floor",
        "phone": "7569888963",
        "email": None,
        "description": "Board of Examinations for CSE Department",
        "source_id": SRC_BOARDS,
        "confidence": "high",
        "last_verified": "2026-08-26T00:00:00Z",
    },
    {
        "id": gen_uuid("off-tp-cse"),
        "name": "T&P-CSE – Training & Placements (CSE)",
        "purpose": "Campus Recruitment Training, Placements, Certificate Programs, Training Attendance",
        "room": "409",
        "block": "N Block",
        "floor": "4th Floor",
        "phone": "9701224847",
        "email": None,
        "description": "Training & Placement Cell for CSE Department",
        "source_id": SRC_BOARDS,
        "confidence": "high",
        "last_verified": "2026-08-26T00:00:00Z",
    },
    {
        "id": gen_uuid("off-social-media-cse"),
        "name": "CSE Social Media Committee",
        "purpose": "Department Website content updates, Instagram, LinkedIn & other social media management, Event coverage, Faculty & Student Achievement promotions, FDPs/Workshops/Guest Lecture publicity, Placement/Internship/Hackathon updates, Content writing & poster design, Brand consistency, Archiving digital media",
        "room": "301",
        "block": "N Block",
        "floor": "3rd Floor",
        "phone": "7337373032",
        "email": "jk_cse@vignan.ac.in",
        "description": "Social Media and Public Relations Committee for CSE Department",
        "source_id": SRC_COMM,
        "confidence": "high",
        "last_verified": "2026-08-26T00:00:00Z",
    },
    {
        "id": gen_uuid("off-magazine-cse"),
        "name": "CSE Magazine Committee",
        "purpose": "Collect articles, technical papers & creative write-ups, Compile Faculty & Student achievements, Document department events and success stories, Edit proofread and format magazine content, Design and layout of newsletter, Publish semester/annual department magazine, Preserve departmental milestones, Promote literary and technical contributions",
        "room": "310",
        "block": "N Block",
        "floor": "3rd Floor",
        "phone": "9790628946",
        "email": "magazine_cse@vignan.ac.in",
        "description": "Department Magazine and Publication Committee for CSE Department",
        "source_id": SRC_COMM,
        "confidence": "high",
        "last_verified": "2026-08-26T00:00:00Z",
    },
    # Phase 3 Offices (Finance, Transport)
    {
        "id": gen_uuid("off-finance-vignan"),
        "name": "Finance & Accounts Office",
        "purpose": "Tuition fee payment, scholarship disbursement, dues clearance, and student accounts",
        "room": None,
        "block": "A Block",
        "floor": "1st Floor",
        "phone": None,
        "email": "finance@vignan.ac.in",
        "description": "University Central Finance and Accounts Office situated on A Block 1st Floor",
        "source_id": SRC_CAMPUS,
        "confidence": "high",
        "last_verified": "2026-08-26T00:00:00Z",
    },
    {
        "id": gen_uuid("off-transport-main"),
        "name": "Transport Office",
        "purpose": "Bus pass registration, renewal, bus route details, transport fee receipts, and transport complaints",
        "room": None,
        "block": "Main Gate Area",
        "floor": "Ground Floor",
        "phone": None,
        "email": "transport@vignan.ac.in",
        "description": "Transport Office located on the left side of the main entrance when viewed from outside the gate; used for bus pass collection and transport information",
        "source_id": SRC_CAMPUS,
        "confidence": "high",
        "last_verified": "2026-08-26T00:00:00Z",
    },
]

# ============================================================================
# 6. ACADEMIC SUPPORT
# ============================================================================
ACADEMIC_SUPPORT = []

def add_academic_support(role_name, person_name, phone=None, email=None, room=None, responsibilities=None, office_key=None, source_id=SRC_LEADS):
    fid = get_or_create_faculty(person_name, phone=phone, room=room, email=email, source_id=source_id)
    ACADEMIC_SUPPORT.append({
        "id": gen_uuid(f"support-{role_name}-{person_name}"),
        "role_name": role_name,
        "person_name": person_name,
        "faculty_id": fid,
        "responsibilities": responsibilities,
        "office_id": gen_uuid(office_key) if office_key else None,
        "room": room,
        "phone": phone,
        "email": email,
        "source_id": source_id,
        "confidence": "high",
        "last_verified": "2026-08-26T00:00:00Z",
    })

acad_lead_resp = "Daily Course Work Monitoring, Course Feedback, Syllabus Depth Coverage, Attendance Monitoring, Attendance Weekly / Monthly Publishing, Condonation and R Grade List Finalization, Follow-up of Slow Learners, Conduct of Value Added Courses, Industry Interface Courses / Course Content Coverage with Industry Personnel"
add_academic_support("III-Year Academic Lead", "Dr. Renuga Devi", phone="9342247173", responsibilities=acad_lead_resp, source_id=SRC_LEADS)
add_academic_support("III-Year Academic Lead", "Dr. Vinoj", phone="9751489857", responsibilities=acad_lead_resp, source_id=SRC_LEADS)
add_academic_support("III-Year Academic Lead", "Mrs. V. Anusha", phone="9704754065", responsibilities=acad_lead_resp, source_id=SRC_LEADS)

add_academic_support("Student Affairs Coordinator", "Mr. P. Vijaya Babu", phone="9985333934", room="409", office_key="off-bosa-cse", responsibilities="Student affairs coordination, student activities and grievance handling", source_id=SRC_LEADS)
add_academic_support("Student Affairs Coordinator", "Mr. D. Balakotaiah", phone="9059093829", room="409", office_key="off-bosa-cse", responsibilities="Student affairs coordination, student activities and grievance handling", source_id=SRC_LEADS)
add_academic_support("Exam Related Activities Coordinator", "Dr. R. Prathap Kumar", phone="7569888963", room="409", office_key="off-boe-cse", responsibilities="Internal and semester-end exam issues, hall tickets, exam registration, revaluation", source_id=SRC_LEADS)
add_academic_support("Slow Learners, Backlogs & Summer Semester Coordinator", "Mr. T. Narasimha Rao", phone="9441075258", responsibilities="Maintaining records of students with backlogs, coordinating remedial and mentoring sessions, and organizing summer semester courses in collaboration with course-wise faculty", source_id=SRC_LEADS)
add_academic_support("NSS Club Coordinator", "Mr. K. Kiran Kumar", phone="9494965571", room="NB-403", responsibilities="NSS club coordination and student community initiatives", source_id=SRC_LEADS)
add_academic_support("NSS Club Coordinator", "Mr. E. Akhil Babu", phone="8465999059", room="NB-401A", responsibilities="NSS club coordination and student community initiatives", source_id=SRC_LEADS)
add_academic_support("NSS Club Coordinator", "Mrs. Archana Nalluri", phone="8985716984", room="NB-320", responsibilities="NSS club coordination and student community initiatives", source_id=SRC_LEADS)
add_academic_support("BoA Coordinator (Value Added Courses)", "Mrs. G. Navya", phone="7794993678", room="409", office_key="off-boa-cse", responsibilities="Coordination and monitoring of Value Added Courses", source_id=SRC_LEADS)
add_academic_support("BoA Coordinator (Value Added Courses)", "Mr. O. Gandhi", phone="9701463728", room="409", office_key="off-boa-cse", responsibilities="Coordination and monitoring of Value Added Courses", source_id=SRC_LEADS)
add_academic_support("NPTEL Coordinator", "Mr. Sk. Jani", phone="8247840320", room="301", responsibilities="NPTEL course registrations, certifications, and student guidance", source_id=SRC_LEADS)

add_academic_support("BoSA Coordinator", "Mr. P. Vijaya Babu", phone="9985333934", room="409", office_key="off-bosa-cse", responsibilities="Student Club Activities & Events, Student Discipline Monitoring, Student Issues & Grievance Support, Student Achievements & OD Recommendations, Student Counselling and Guidance, Student Welfare Activities", source_id=SRC_BOARDS)
add_academic_support("BoSA Coordinator", "Mr. D. Balakotaiah", phone="9059093829", room="409", office_key="off-bosa-cse", responsibilities="Student Club Activities & Events, Student Discipline Monitoring, Student Issues & Grievance Support, Student Achievements & OD Recommendations, Student Counselling and Guidance, Student Welfare Activities", source_id=SRC_BOARDS)
add_academic_support("BoA Coordinator", "Mr. O. Gandhi", phone="9701463728", room="409", office_key="off-boa-cse", responsibilities="Syllabus Coverage Monitoring, Course Progress Monitoring, Academic Credit Issues, Attendance Monitoring, Course Registration Support, Academic Regulations & Guidelines, Faculty-Student Academic Coordination, Value Added Courses Monitoring, Academic Queries and Support", source_id=SRC_BOARDS)
add_academic_support("BoA Coordinator", "Ms. G. Navya", phone="7794993678", room="409", office_key="off-boa-cse", responsibilities="Syllabus Coverage Monitoring, Course Progress Monitoring, Academic Credit Issues, Attendance Monitoring, Course Registration Support, Academic Regulations & Guidelines, Faculty-Student Academic Coordination, Value Added Courses Monitoring, Academic Queries and Support", source_id=SRC_BOARDS)
add_academic_support("BoE Coordinator", "Dr. Prataap Kumar", phone="7569888963", room="409", office_key="off-boe-cse", responsibilities="Internal Examination Issues, Semester End Examination Queries, Hall Ticket Issues, Examination Registration, Revaluation & Challenge Valuation Guidance, Makeup/Supplementary Examination Support, Results & Grade Related Queries, Examination Notifications", source_id=SRC_BOARDS)
add_academic_support("T&P-CSE Coordinator", "Dr. Balu Narasimharao", phone="9701224847", room="409", office_key="off-tp-cse", responsibilities="Campus Recruitment Training, Placements, Certificate Programs, Training Attendance", source_id=SRC_BOARDS)
add_academic_support("T&P-CSE Coordinator", "Ms. Leelavathi", phone="8919420637", room="409", office_key="off-tp-cse", responsibilities="Campus Recruitment Training, Placements, Certificate Programs, Training Attendance", source_id=SRC_BOARDS)

add_academic_support("Social Media Coordinator", "K. Jyotsna", phone="7337373032", email="jk_cse@vignan.ac.in", room="301", office_key="off-social-media-cse", responsibilities="Department Website content updates, Instagram, LinkedIn & other social media management, Event coverage, Faculty & Student Achievement promotions, FDPs/Workshops/Guest Lecture publicity, Placement/Internship/Hackathon updates, Content writing & poster design, Brand consistency, Archiving digital media", source_id=SRC_COMM)
add_academic_support("Social Media Coordinator", "Sk. Jani", phone="8247840320", email="jk_cse@vignan.ac.in", room="301", office_key="off-social-media-cse", responsibilities="Department Website content updates, Instagram, LinkedIn & other social media management, Event coverage, Faculty & Student Achievement promotions, FDPs/Workshops/Guest Lecture publicity, Placement/Internship/Hackathon updates, Content writing & poster design, Brand consistency, Archiving digital media", source_id=SRC_COMM)
add_academic_support("Magazine Committee Member", "Dr. Vijitha Ananthi", phone="9790628946", email="magazine_cse@vignan.ac.in", room="310", office_key="off-magazine-cse", responsibilities="Collect articles, technical papers & creative write-ups, Compile Faculty & Student achievements, Document department events, Edit proofread and format magazine content, Design newsletter layout, Publish department magazine", source_id=SRC_COMM)
add_academic_support("Magazine Committee Member", "V. Sai Spandana", phone="9948368555", email="magazine_cse@vignan.ac.in", room="310", office_key="off-magazine-cse", responsibilities="Collect articles, technical papers & creative write-ups, Compile Faculty & Student achievements, Document department events, Edit proofread and format magazine content, Design newsletter layout, Publish department magazine", source_id=SRC_COMM)
add_academic_support("Department Overall Coordinator", "Mr. P. Vijaya Babu", phone="9985333934", room="409", responsibilities="Overall coordination of department activities, social media, magazine and student affairs", source_id=SRC_COMM)

FACULTY_LIST = list(FACULTY_MAP.values())

# ============================================================================
# 7. SUBJECTS & FACULTY_SUBJECTS (Phase 2 Official Website)
# ============================================================================
SUBJECTS_DATA = [
    {"name": "Database Management Systems", "code": "22CS201", "dept_key": "dept-cse-core"},
    {"name": "Data Structures & Algorithms", "code": "22CS203", "dept_key": "dept-cse-core"},
    {"name": "Operating Systems", "code": "22CS207", "dept_key": "dept-cse-core"},
    {"name": "Computer Networks", "code": "22CS301", "dept_key": "dept-cse-core"},
    {"name": "Theory of Computation", "code": "22CS205", "dept_key": "dept-cse-core"},
]

SUBJECTS = [
    {
        "id": gen_uuid(f"subj-{s['code']}"),
        "name": s["name"],
        "code": s["code"],
        "department_id": gen_uuid(s["dept_key"]),
        "source_id": SRC_WEB,
        "confidence": "high",
        "last_verified": "2026-08-26T00:00:00Z",
    }
    for s in SUBJECTS_DATA
]

FACULTY_SUBJECTS = []

# ============================================================================
# 8. SERVICES (Phase 3 Campus Verified)
# ============================================================================
SERVICES = [
    # Transport Services
    {
        "id": gen_uuid("svc-transport-office"),
        "name": "Transport Office & Bus Pass Counter",
        "category": "transport",
        "description": "Transport information, bus route details, bus pass collection and fee inquiries located at Main Gate",
        "location_id": gen_uuid("loc-transport-office"),
        "services_offered": ["bus pass collection", "transport information", "route schedules", "bus passes"],
        "source_id": SRC_CAMPUS,
        "confidence": "high",
        "last_verified": "2026-08-26T00:00:00Z",
    },
    # Xerox / Printing Facilities
    {
        "id": gen_uuid("svc-xerox-beside-a-block"),
        "name": "Xerox Facility — Beside A Block",
        "category": "xerox",
        "description": "Photocopy and printing facility situated beside A Block",
        "location_id": gen_uuid("loc-a-block"),
        "services_offered": ["xerox", "photocopy", "black and white printing", "stationery"],
        "source_id": SRC_CAMPUS,
        "confidence": "high",
        "last_verified": "2026-08-26T00:00:00Z",
    },
    {
        "id": gen_uuid("svc-xerox-a-block-lift"),
        "name": "Xerox Facility — A Block Side Lift",
        "category": "xerox",
        "description": "Xerox facility on A Block ground floor near the side lift",
        "location_id": gen_uuid("loc-a-block"),
        "services_offered": ["xerox", "photocopy", "document printing"],
        "source_id": SRC_CAMPUS,
        "confidence": "high",
        "last_verified": "2026-08-26T00:00:00Z",
    },
    {
        "id": "a936383f-8216-557e-92d1-91e17a7e93f5",
        "name": "Xerox Facility — Near MHP / Zest Area",
        "category": "xerox",
        "description": "Xerox and printing facility situated near/between Zest and MHP area",
        "location_id": None,
        "services_offered": ["xerox", "photocopy", "color printing", "spiral binding"],
        "source_id": SRC_CAMPUS,
        "confidence": "high",
        "last_verified": "2026-08-26T00:00:00Z",
    },
    # Canteens & Food Facilities
    {
        "id": gen_uuid("svc-canteen-h-block"),
        "name": "H Block Canteen",
        "category": "canteen",
        "description": "Canteen facility located at H Block",
        "location_id": gen_uuid("loc-h-block"),
        "services_offered": ["breakfast", "lunch", "snacks", "beverages", "tea", "coffee"],
        "source_id": SRC_CAMPUS,
        "confidence": "high",
        "last_verified": "2026-08-26T00:00:00Z",
    },
    {
        "id": gen_uuid("svc-canteen-h-block-internal"),
        "name": "H Block Internal Canteen",
        "category": "canteen",
        "description": "Internal food stall and refreshments counter inside H Block",
        "location_id": gen_uuid("loc-h-block"),
        "services_offered": ["snacks", "refreshments", "juice", "beverages"],
        "source_id": SRC_CAMPUS,
        "confidence": "high",
        "last_verified": "2026-08-26T00:00:00Z",
    },
    {
        "id": gen_uuid("svc-canteen-a-block-f3"),
        "name": "A Block 3rd Floor Canteen",
        "category": "canteen",
        "description": "Refreshments and snacks canteen situated on A Block 3rd Floor",
        "location_id": gen_uuid("loc-a-block"),
        "services_offered": ["tea", "coffee", "snacks", "packaged food"],
        "source_id": SRC_CAMPUS,
        "confidence": "high",
        "last_verified": "2026-08-26T00:00:00Z",
    },
    {
        "id": gen_uuid("svc-canteen-mhp-main"),
        "name": "MHP / Main Canteen",
        "category": "canteen",
        "description": "Main campus dining hall and central canteen at MHP",
        "location_id": None,
        "services_offered": ["meals", "thali", "breakfast", "fast food", "beverages", "ice cream"],
        "source_id": SRC_CAMPUS,
        "confidence": "high",
        "last_verified": "2026-08-26T00:00:00Z",
    },
    {
        "id": gen_uuid("svc-canteen-faculty-h-block"),
        "name": "Faculty Lunch Area beside H Block",
        "category": "canteen",
        "description": "Dedicated faculty dining and lunch area located beside H Block",
        "location_id": gen_uuid("loc-h-block"),
        "services_offered": ["faculty lunch", "dining area", "water facility"],
        "source_id": SRC_CAMPUS,
        "confidence": "high",
        "last_verified": "2026-08-26T00:00:00Z",
    },
    {
        "id": gen_uuid("svc-canteen-u-block-side"),
        "name": "U Block Side Canteen",
        "category": "canteen",
        "description": "Canteen situated at the side of U Block",
        "location_id": gen_uuid("loc-u-block"),
        "services_offered": ["snacks", "tea", "coffee", "cool drinks", "bakery"],
        "source_id": SRC_CAMPUS,
        "confidence": "high",
        "last_verified": "2026-08-26T00:00:00Z",
    },
    {
        "id": gen_uuid("svc-canteen-u-block-ground-internal"),
        "name": "U Block Ground Floor Internal Canteen",
        "category": "canteen",
        "description": "Internal food counter situated on the ground floor of U Block",
        "location_id": gen_uuid("loc-u-block"),
        "services_offered": ["quick snacks", "tea", "water", "beverages"],
        "source_id": SRC_CAMPUS,
        "confidence": "high",
        "last_verified": "2026-08-26T00:00:00Z",
    },
]

# ============================================================================
# 9. ROUTES (Phase 4 — Empty / Uninvented)
# ============================================================================
ROUTES = []

def save_json(filename, data):
    path = os.path.join(EXTRACTED_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Saved {filename} ({len(data)} records)")

def run():
    print("=" * 60)
    print("Building Full VIGNAN Multi-Source Dataset (Phases 1, 2, 3)...")
    print("=" * 60)
    save_json("sources.json", SOURCES)
    save_json("locations.json", LOCATIONS)
    save_json("departments.json", DEPARTMENTS)
    save_json("offices.json", OFFICES)
    save_json("faculty.json", FACULTY_LIST)
    save_json("counsellors.json", COUNSELLORS)
    save_json("academic_support.json", ACADEMIC_SUPPORT)
    save_json("subjects.json", SUBJECTS)
    save_json("faculty_subjects.json", FACULTY_SUBJECTS)
    save_json("services.json", SERVICES)
    save_json("routes.json", ROUTES)
    print("\nDataset generation complete!")

if __name__ == "__main__":
    run()
