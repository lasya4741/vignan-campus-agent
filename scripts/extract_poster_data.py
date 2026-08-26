"""Data extraction script for 6 verified VIGNAN department posters."""

import json
import os
import re

EXTRACTED_DIR = "database/extracted"
os.makedirs(EXTRACTED_DIR, exist_ok=True)

# 1. SOURCES
SOURCES = [
    {
        "id": "src-venues",
        "source_type": "department_verified",
        "source_name": "CSE Department Venue Sheet",
        "document_name": "department_venues.jpg",
        "confidence": "high",
        "last_verified": "2026-08-26",
    },
    {
        "id": "src-y2-couns",
        "source_type": "department_verified",
        "source_name": "CSE II Year Counsellor Poster",
        "document_name": "year2_counsellors.jpg",
        "confidence": "high",
        "last_verified": "2026-08-26",
    },
    {
        "id": "src-y3-couns",
        "source_type": "department_verified",
        "source_name": "CSE III Year Counsellor Poster",
        "document_name": "year3_counsellors.jpg",
        "confidence": "high",
        "last_verified": "2026-08-26",
    },
    {
        "id": "src-acad-leads",
        "source_type": "department_verified",
        "source_name": "CSE III Year Academic Leads Poster",
        "document_name": "academic_leads.jpg",
        "confidence": "high",
        "last_verified": "2026-08-26",
    },
    {
        "id": "src-bosa-boa-boe-tp",
        "source_type": "department_verified",
        "source_name": "CSE BoSA BoA BoE T&P Poster",
        "document_name": "bosa_boa_boe_tp.jpg",
        "confidence": "high",
        "last_verified": "2026-08-26",
    },
    {
        "id": "src-dept-comm",
        "source_type": "department_verified",
        "source_name": "CSE Department Committees Poster",
        "document_name": "department_committees.jpg",
        "confidence": "high",
        "last_verified": "2026-08-26",
    },
]

# 2. LOCATIONS (Physical Blocks & Venues)
LOCATIONS = [
    # Blocks
    {"id": "loc-n-block", "name": "N Block", "location_type": "building", "block": "N Block", "description": "N Block Academic Building (Floors 1 to 6)", "source_id": "src-venues", "confidence": "high"},
    {"id": "loc-h-block", "name": "H Block", "location_type": "building", "block": "H Block", "description": "H Block Academic Building (Ground to 3rd Floor)", "source_id": "src-venues", "confidence": "high"},
    {"id": "loc-u-block", "name": "U Block", "location_type": "building", "block": "U Block", "description": "U Block Academic Building (Ground to 4th Floor)", "source_id": "src-venues", "confidence": "high"},
    {"id": "loc-textile-block", "name": "Textile Block", "location_type": "building", "block": "Textile Block", "description": "Textile Engineering Block", "source_id": "src-venues", "confidence": "high"},
    # Specific Rooms in N Block / U Block
    {"id": "loc-room-301", "name": "Room No. 301", "location_type": "room", "block": "N Block", "floor": "3rd Floor", "room": "301", "description": "Social Media Coordinators Meeting Room / Faculty Seating", "parent_location_id": "loc-n-block", "source_id": "src-dept-comm", "confidence": "high"},
    {"id": "loc-room-310", "name": "Room No. 310", "location_type": "room", "block": "N Block", "floor": "3rd Floor", "room": "310", "description": "Magazine Committee Meeting Room / Faculty Seating", "parent_location_id": "loc-n-block", "source_id": "src-dept-comm", "confidence": "high"},
    {"id": "loc-room-409", "name": "Room No. 409", "location_type": "room", "block": "N Block", "floor": "4th Floor", "room": "409", "description": "BoSA, BoA, BoE, T&P CSE Meeting Room & Faculty Seating", "parent_location_id": "loc-n-block", "source_id": "src-bosa-boa-boe-tp", "confidence": "high"},
]

# 3. DEPARTMENTS
DEPARTMENTS = [
    {"id": "dept-cse-core", "name": "Computer Science & Engineering (Core)", "short_name": "CSE {CORE}", "description": "Department of Computer Science & Engineering (Core)", "block": "N Block", "floor_information": "3,4,5 Floors", "source_id": "src-venues", "confidence": "high"},
    {"id": "dept-cse-spec", "name": "Computer Science & Engineering (Specializations)", "short_name": "CSE {SPECIALIZATIONS}", "description": "CSE Specializations (AI, ML, DS, Cyber Security, etc.)", "block": "N Block", "floor_information": "5,6 Floors", "source_id": "src-venues", "confidence": "high"},
    {"id": "dept-chem", "name": "Chemical Engineering", "short_name": "CHEMICAL", "description": "Department of Chemical Engineering", "block": "H Block", "floor_information": "1st Floor", "source_id": "src-venues", "confidence": "high"},
    {"id": "dept-eee", "name": "Electrical & Electronics Engineering", "short_name": "EEE", "description": "Department of Electrical & Electronics Engineering", "block": "H Block", "floor_information": "1st Floor", "source_id": "src-venues", "confidence": "high"},
    {"id": "dept-ece", "name": "Electronics & Communication Engineering", "short_name": "ECE", "description": "Department of Electronics & Communication Engineering", "block": "H Block", "floor_information": "2nd Floor", "source_id": "src-venues", "confidence": "high"},
    {"id": "dept-biomed", "name": "Biomedical Engineering", "short_name": "BIO-MEDICAL", "description": "Department of Biomedical Engineering", "block": "H Block", "floor_information": "3rd Floor", "source_id": "src-venues", "confidence": "high"},
    {"id": "dept-foodtech", "name": "Food Technology", "short_name": "FOOD TECH", "description": "Department of Food Technology", "block": "H Block", "floor_information": "Ground & 1st Floor", "source_id": "src-venues", "confidence": "high"},
    {"id": "dept-mech", "name": "Mechanical Engineering", "short_name": "MECHANICAL", "description": "Department of Mechanical Engineering", "block": "U Block", "floor_information": "Ground Floor", "source_id": "src-venues", "confidence": "high"},
    {"id": "dept-robotics", "name": "Robotics Engineering", "short_name": "ROBOTICS", "description": "Department of Robotics", "block": "U Block", "floor_information": "Ground Floor", "source_id": "src-venues", "confidence": "high"},
    {"id": "dept-civil", "name": "Civil Engineering", "short_name": "CIVIL", "description": "Department of Civil Engineering", "block": "U Block", "floor_information": "1st Floor", "source_id": "src-venues", "confidence": "high"},
    {"id": "dept-law", "name": "Law", "short_name": "LAW", "description": "School of Law", "block": "U Block", "floor_information": "1st Floor", "source_id": "src-venues", "confidence": "high"},
    {"id": "dept-biotech", "name": "Biotechnology", "short_name": "BIO TECHNOLOGY", "description": "Department of Biotechnology", "block": "U Block", "floor_information": "2nd Floor", "source_id": "src-venues", "confidence": "high"},
    {"id": "dept-bioinfo", "name": "Bioinformatics", "short_name": "BIO INFORMATICS", "description": "Department of Bioinformatics", "block": "U Block", "floor_information": "2nd Floor", "source_id": "src-venues", "confidence": "high"},
    {"id": "dept-it", "name": "Information Technology", "short_name": "IT", "description": "Department of Information Technology", "block": "U Block", "floor_information": "3rd Floor", "source_id": "src-venues", "confidence": "high"},
    {"id": "dept-mgmt", "name": "Management Studies", "short_name": "MANAGEMENT STUDIES", "description": "Department of Management Studies", "block": "U Block", "floor_information": "4th Floor", "source_id": "src-venues", "confidence": "high"},
    {"id": "dept-ca", "name": "Computer Applications", "short_name": "COMPUTER APPLICATIONS", "description": "Department of Computer Applications (MCA/BCA)", "block": "U Block", "floor_information": "4th Floor", "source_id": "src-venues", "confidence": "high"},
    {"id": "dept-agri", "name": "Agriculture Engineering", "short_name": "AGRICULTURE", "description": "Department of Agriculture", "block": "N Block", "floor_information": "1,2 Floors", "source_id": "src-venues", "confidence": "high"},
    {"id": "dept-textile", "name": "Textile Engineering", "short_name": "TEXTILE", "description": "Department of Textile Technology", "block": "Textile Block", "floor_information": "Textile Block", "source_id": "src-venues", "confidence": "high"},
]

# 4. OFFICES & BOARDS
OFFICES = [
    {
        "id": "off-bosa-cse",
        "name": "BoSA – Board of Student Affairs (CSE)",
        "purpose": "Student Club Activities & Events, Student Discipline Monitoring, Student Issues & Grievance Support, Student Achievements & OD Recommendations, Student Counselling & Guidance, Student Welfare Activities",
        "room": "409",
        "block": "N Block",
        "floor": "4th Floor",
        "phone": "9985333934",
        "email": None,
        "description": "Board of Student Affairs for CSE Department",
        "source_id": "src-bosa-boa-boe-tp",
        "confidence": "high",
    },
    {
        "id": "off-boa-cse",
        "name": "BoA – Board of Academics (CSE)",
        "purpose": "Syllabus Coverage Monitoring, Course Progress Monitoring, Academic Credit Issues, Attendance Monitoring, Course Registration Support, Academic Regulations & Guidelines, Faculty-Student Academic Coordination, Value Added Courses Monitoring, Academic Queries and Support",
        "room": "409",
        "block": "N Block",
        "floor": "4th Floor",
        "phone": "9701463728",
        "email": None,
        "description": "Board of Academics for CSE Department",
        "source_id": "src-bosa-boa-boe-tp",
        "confidence": "high",
    },
    {
        "id": "off-boe-cse",
        "name": "BoE – Board of Examinations (CSE)",
        "purpose": "Internal Examination Issues, Semester End Examination Queries, Hall Ticket Issues, Examination Registration, Revaluation & Challenge Valuation Guidance, Makeup/Supplementary Examination Support, Results & Grade Related Queries, Examination Notifications",
        "room": "409",
        "block": "N Block",
        "floor": "4th Floor",
        "phone": "7569888963",
        "email": None,
        "description": "Board of Examinations for CSE Department",
        "source_id": "src-bosa-boa-boe-tp",
        "confidence": "high",
    },
    {
        "id": "off-tp-cse",
        "name": "T&P-CSE – Training & Placements (CSE)",
        "purpose": "Campus Recruitment Training, Placements, Certificate Programs, Training Attendance",
        "room": "409",
        "block": "N Block",
        "floor": "4th Floor",
        "phone": "9701224847",
        "email": None,
        "description": "Training & Placement Cell for CSE Department",
        "source_id": "src-bosa-boa-boe-tp",
        "confidence": "high",
    },
    {
        "id": "off-social-media-cse",
        "name": "CSE Social Media Committee",
        "purpose": "Department Website content updates, Instagram, LinkedIn & other social media management, Event coverage, Faculty & Student Achievement promotions, FDPs/Workshops/Guest Lecture publicity, Placement/Internship/Hackathon updates, Content writing & poster design, Brand consistency, Archiving digital media",
        "room": "301",
        "block": "N Block",
        "floor": "3rd Floor",
        "phone": "7337373032",
        "email": "jk_cse@vignan.ac.in",
        "description": "Social Media and Public Relations Committee for CSE Department",
        "source_id": "src-dept-comm",
        "confidence": "high",
    },
    {
        "id": "off-magazine-cse",
        "name": "CSE Magazine Committee",
        "purpose": "Collect articles, technical papers & creative write-ups, Compile Faculty & Student achievements, Document department events and success stories, Edit proofread and format magazine content, Design and layout of newsletter, Publish semester/annual department magazine, Preserve departmental milestones, Promote literary and technical contributions",
        "room": "310",
        "block": "N Block",
        "floor": "3rd Floor",
        "phone": "9790628946",
        "email": "magazine_cse@vignan.ac.in",
        "description": "Department Magazine and Publication Committee for CSE Department",
        "source_id": "src-dept-comm",
        "confidence": "high",
    },
]

# Raw faculty data mapping across posters
FACULTY_DATA = {}

def add_faculty(name, phone=None, room=None, email=None, designation=None, source_id="src-y2-couns"):
    # Normalize name key for deduplication
    norm_key = re.sub(r"[^a-zA-Z]", "", name.lower())
    if not norm_key:
        return None

    # Specific alias consolidation
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

    if canon_key not in FACULTY_DATA:
        FACULTY_DATA[canon_key] = {
            "id": f"fac-{len(FACULTY_DATA) + 1:03d}",
            "full_name": name,
            "designation": designation,
            "department_id": "dept-cse-core",
            "email": email,
            "phone": phone,
            "room": room,
            "block": "N Block" if room and room.startswith("NB-") else ("N Block" if room in ["301", "310", "409"] else None),
            "floor": None,
            "profile_url": None,
            "source_id": source_id,
            "confidence": "high",
            "last_verified": "2026-08-26",
        }
    else:
        existing = FACULTY_DATA[canon_key]
        if phone and not existing["phone"]:
            existing["phone"] = phone
        if room and not existing["room"]:
            existing["room"] = room
        if email and not existing["email"]:
            existing["email"] = email
        if designation and not existing["designation"]:
            existing["designation"] = designation

    return FACULTY_DATA[canon_key]["id"]

# 5. II YEAR COUNSELLORS
YEAR2_COUNSELLORS_RAW = [
    # Sec 1
    {"year": 2, "sec": "1", "name": "Dr. Md. Oqail Ahmad", "phone": "8439243408", "room": "NB-410", "r_start": "4001", "r_end": "4071"},
    {"year": 2, "sec": "1", "name": "Mr. Hitendra Singh", "phone": "8529127355", "room": "NB-420", "r_start": "4073", "r_end": "4132"},
    {"year": 2, "sec": "1", "name": "Ms. Shaik Nazeera", "phone": "9618896300", "room": "NB-401A", "r_start": "4134", "r_end": "4175"},
    # Sec 2
    {"year": 2, "sec": "2", "name": "Dr. B. Suvarna", "phone": "7093171146", "room": "NB-409", "r_start": "4116", "r_end": "4315"},
    {"year": 2, "sec": "2", "name": "Mrs. Archana Nalluri", "phone": "8985716984", "room": "NB-320", "r_start": "4316", "r_end": "4805"},
    # Sec 3
    {"year": 2, "sec": "3", "name": "Mrs. Sd. Shareefunnisa", "phone": "8074308730", "room": "NB-403", "r_start": "4458", "r_end": "4560"},
    {"year": 2, "sec": "3", "name": "Ms. Tupakula Tahera", "phone": "9347667759", "room": "NB-420", "r_start": "4562", "r_end": "4634"},
    {"year": 2, "sec": "3", "name": "Ms. Kalluri Mercy Bhikshvathi", "phone": "9014592698", "room": "NB-520", "r_start": "4635", "r_end": "4H12"},
    # Sec 4
    {"year": 2, "sec": "4", "name": "Mrs. M. Bhargavi", "phone": "7095812130", "room": "NB-403", "r_start": "4212", "r_end": "4757"},
    {"year": 2, "sec": "4", "name": "Mr. Swetabh Sinhku", "phone": "7893038516", "room": "NB-313", "r_start": "4762", "r_end": "4829"},
    {"year": 2, "sec": "4", "name": "Mrs. Polepali Sai Veera Venkata Samhitha", "phone": "7337475699", "room": "NB-320", "r_start": "4835", "r_end": "4G97"},
    # Sec 5
    {"year": 2, "sec": "5", "name": "Ms. Gudipati Sravya", "phone": "8897176559", "room": "NB-410", "r_start": "4069", "r_end": "4A03"},
    {"year": 2, "sec": "5", "name": "Mr. Adavi Aditya Venkateswara Kumar", "phone": "6301666022", "room": "NB-520", "r_start": "4A05", "r_end": "4165"},
    # Sec 6
    {"year": 2, "sec": "6", "name": "Dr. Prashant Upadhyay", "phone": "9805406546", "room": "NB-310", "r_start": "4026", "r_end": "4893"},
    {"year": 2, "sec": "6", "name": "Ms. Muhammad Gulshan Firdous", "phone": "6281590963", "room": "NB-420", "r_start": "4897", "r_end": "4C72"},
    {"year": 2, "sec": "6", "name": "Ms. Y. Sesha Naga Bindu Lalitha Sri", "phone": "8712269324", "room": "NB-520", "r_start": "4C77", "r_end": "4194"},
    # Sec 7
    {"year": 2, "sec": "7", "name": "Mr. Talluri Latesh Babu", "phone": "9550818722", "room": "NB-510", "r_start": "4131", "r_end": "4E50"},
    {"year": 2, "sec": "7", "name": "Ms. G. Siva Naga Malleswari", "phone": "6300448477", "room": "NB-420", "r_start": "4E51", "r_end": "4G38"},
    # Sec 8
    {"year": 2, "sec": "8", "name": "Dr. T. R. Rajesh", "phone": "9676560542", "room": "NB-509", "r_start": "4035", "r_end": "4G27"},
    {"year": 2, "sec": "8", "name": "Mr. Loganathan M", "phone": "9976418789", "room": "NB-520", "r_start": "4G44", "r_end": "4140"},
    # Sec 9
    {"year": 2, "sec": "9", "name": "Mr. Syed Nafees Ahamed", "phone": "8790469105", "room": "NB-401A", "r_start": "4091", "r_end": "4144"},
    {"year": 2, "sec": "9", "name": "Ms. Kollabathula Nimnagasri", "phone": "7642481619", "room": "NB-420", "r_start": "4145", "r_end": "4197"},
    {"year": 2, "sec": "9", "name": "Mr. Maturi Ashok Gupta", "phone": "9247294748", "room": "NB-304", "r_start": "261LA4001", "r_end": "261LA4028"},
    # Sec 10
    {"year": 2, "sec": "10", "name": "Mr. U. Venkateswara Rao", "phone": "9966259492", "room": "NB-301A", "r_start": "4005", "r_end": "4072"},
    {"year": 2, "sec": "10", "name": "Mr. Gudipati Rishi Kesava", "phone": "8919250534", "room": "NB-420", "r_start": "4074", "r_end": "4161"},
    # Sec 11
    {"year": 2, "sec": "11", "name": "Mr. Kiran Kumar Kalagadda", "phone": "9494965571", "room": "NB-403", "r_start": "4043", "r_end": "4225"},
    {"year": 2, "sec": "11", "name": "Ms. Marella Sirisha", "phone": "8008990401", "room": "NB-520", "r_start": "4226", "r_end": "4295"},
    {"year": 2, "sec": "11", "name": "Ms. Vutukuri Geetha Nagalakshmi", "phone": "8106350764", "room": "NB-420", "r_start": "4296", "r_end": "4H43"},
    # Sec 12
    {"year": 2, "sec": "12", "name": "Ms. Yeminani Sravani", "phone": "7032293225", "room": "NB-510", "r_start": "4054", "r_end": "4399"},
    {"year": 2, "sec": "12", "name": "Mr. Mihir Bhatt", "phone": "8840896873", "room": "NB-420", "r_start": "4401", "r_end": "4462"},
    {"year": 2, "sec": "12", "name": "Dr. G. Saubhagya Ranjan Biswal", "phone": "9525588508", "room": "NB-310", "r_start": "4466", "r_end": "4803"},
    # Sec 13
    {"year": 2, "sec": "13", "name": "Ms. Pavani Karra", "phone": "9100234298", "room": "NB-520", "r_start": "4112", "r_end": "4614"},
    {"year": 2, "sec": "13", "name": "Ms. Kolli Bhavya Sri", "phone": "9346464229", "room": "NB-520", "r_start": "4617", "r_end": "4C20"},
    # Sec 14
    {"year": 2, "sec": "14", "name": "Dr. M. Sunil Babu", "phone": "8333001991", "room": "NB-509", "r_start": "4162", "r_end": "4804"},
    {"year": 2, "sec": "14", "name": "Mr. Sourav Mondal", "phone": "9631422643", "room": "NB-310", "r_start": "4807", "r_end": "4874"},
    # Sec 15
    {"year": 2, "sec": "15", "name": "Mrs. S. Anitha", "phone": "9505044559", "room": "NB-301A", "r_start": "4004", "r_end": "4096"},
    {"year": 2, "sec": "15", "name": "Mr. Shyam Sundar Jannu Soloman", "phone": "7995624716", "room": "NB-401A", "r_start": "4099", "r_end": "4148"},
    # Sec 16
    {"year": 2, "sec": "16", "name": "Dr. Gabbi Reddy Keerthi", "phone": "9491139513", "room": "NB-509", "r_start": "4127", "r_end": "4C06"},
    {"year": 2, "sec": "16", "name": "Ms. Shaik Charishma", "phone": "8247490119", "room": "NB-320", "r_start": "4C13", "r_end": "4F35"},
    # Sec 17
    {"year": 2, "sec": "17", "name": "Mrs. Tanigundala Leelavathy", "phone": "8919420637", "room": "NB-409", "r_start": "4125", "r_end": "4E35"},
    {"year": 2, "sec": "17", "name": "Ms. P. Deepthi Sowmya", "phone": "9100967181", "room": "NB-520", "r_start": "4E39", "r_end": "4F71"},
    # Sec 18
    {"year": 2, "sec": "18", "name": "Mrs. Ch. Swarna Lalitha", "phone": "6281716181", "room": "NB-520", "r_start": "4043", "r_end": "4084"},
    {"year": 2, "sec": "18", "name": "Ms. Pathan Razia Sultana", "phone": "9505246169", "room": "NB-420", "r_start": "4G50", "r_end": "261LA4033"},
    # Sec 19
    {"year": 2, "sec": "19", "name": "Mr. E. Akhil Babu", "phone": "8465999059", "room": "NB-401A", "r_start": "4662", "r_end": "4H96"},
    {"year": 2, "sec": "19", "name": "Mr. Anuvalasetty Naga Harshith Vardhan", "phone": "7075717333", "room": "NB-520", "r_start": "4102", "r_end": "261LA4032"},
]

# 6. III YEAR COUNSELLORS
YEAR3_COUNSELLORS_RAW = [
    # Sec 1
    {"year": 3, "sec": "1", "name": "Mr. Gujjula Murali", "phone": "9553116627", "room": "NB-410"},
    {"year": 3, "sec": "1", "name": "Ms. Gaddam Tejaswi", "phone": "9398046056", "room": "NB-401A"},
    # Sec 2
    {"year": 3, "sec": "2", "name": "Dr. R. Renugadevi", "phone": "9342247173", "room": "NB-403"},
    {"year": 3, "sec": "2", "name": "Ms. Peeka Anusha", "phone": "6309699033", "room": "NB-403"},
    # Sec 3
    {"year": 3, "sec": "3", "name": "Dr. Phanindra Thota", "phone": "8096465667", "room": "NB-403"},
    {"year": 3, "sec": "3", "name": "Mr. Lalu Naick. B", "phone": "7842061881", "room": "NB-320"},
    # Sec 4
    {"year": 3, "sec": "4", "name": "Dr. R. Prathap Kumar", "phone": "7569888963", "room": "NB-409"},
    {"year": 3, "sec": "4", "name": "Dr. M. Raja Rao", "phone": "8979803148", "room": "NB-410"},
    # Sec 5
    {"year": 3, "sec": "5", "name": "Ms. Upalanchi Vara Lakshmi", "phone": "8142214788", "room": "NB-520"},
    {"year": 3, "sec": "5", "name": "Mr. Shashi Mani", "phone": "9262978555", "room": "NB-401A"},
    # Sec 6
    {"year": 3, "sec": "6", "name": "Mr. Shaik Sikindar", "phone": "9581964409", "room": "NB-410"},
    {"year": 3, "sec": "6", "name": "Ms. Kandula Divya", "phone": "8328282185", "room": "NB-420"},
    # Sec 7
    {"year": 3, "sec": "7", "name": "Dr. O. Bhaskar", "phone": "6301577419", "room": "NB-510"},
    {"year": 3, "sec": "7", "name": "Ms. Vyshnavi Kagga", "phone": "9182743520", "room": "NB-210"},
    # Sec 8
    {"year": 3, "sec": "8", "name": "Dr. G. Balu Narasimha Rao", "phone": "9701224847", "room": "NB-409"},
    {"year": 3, "sec": "8", "name": "Mrs. Varagani Tejaswi", "phone": "6305179829", "room": "NB-401A"},
    # Sec 9
    {"year": 3, "sec": "9", "name": "Mr. Ongole Gandhi", "phone": "9701463728", "room": "NB-409"},
    {"year": 3, "sec": "9", "name": "Mr. Munipalli Veerendra", "phone": "9573632919", "room": "NB-210"},
    # Sec 10
    {"year": 3, "sec": "10", "name": "Mr. Sk. Khadersha", "phone": "8309300881", "room": "NB-520"},
    {"year": 3, "sec": "10", "name": "Ms. Bhimavarapu Jyothika", "phone": "7989366515", "room": "NB-210"},
    # Sec 11
    {"year": 3, "sec": "11", "name": "Mr. Bathula Anil Babu", "phone": "8688070939", "room": "NB-510"},
    {"year": 3, "sec": "11", "name": "Mr. Palavelli Vamsi Krishna", "phone": "6309663292", "room": "NB-210"},
    # Sec 12
    {"year": 3, "sec": "12", "name": "Mrs. D. Tipura", "phone": "8977267707", "room": "NB-303"},
    {"year": 3, "sec": "12", "name": "Mrs. Guggilam Navya", "phone": "7794993678", "room": "NB-409"},
    # Sec 13
    {"year": 3, "sec": "13", "name": "Mrs. Anusha Kakumanu", "phone": "7799053996", "room": "NB-410"},
    {"year": 3, "sec": "13", "name": "Ms. Ravuri Lalitha", "phone": "6302034022", "room": "NB-520"},
    # Sec 14
    {"year": 3, "sec": "14", "name": "Mr. Dega Balakotaiah", "phone": "9059093829", "room": "NB-409"},
    {"year": 3, "sec": "14", "name": "Ms. Swathi Koganti", "phone": "9491664577", "room": "NB-301A"},
    # Sec 15
    {"year": 3, "sec": "15", "name": "Ms. Yalavarthi Sai Eswari", "phone": "8074131669", "room": "NB-510"},
    {"year": 3, "sec": "15", "name": "Mr. Y. Rama Mohan", "phone": "9494399849", "room": "NB-510"},
    # Sec 16
    {"year": 3, "sec": "16", "name": "Dr. Chinna Gopi Simhadri", "phone": "9700330708", "room": "NB-520"},
    {"year": 3, "sec": "16", "name": "Dr. G. Veera Bhadra Chary", "phone": "8978975688", "room": "NB-410"},
    # Sec 17
    {"year": 3, "sec": "17", "name": "Mr. Madugula Anil", "phone": "9493322982", "room": "NB-410"},
    {"year": 3, "sec": "17", "name": "Ms. Arumalla Gopya Sri", "phone": "8919398629", "room": "NB-520"},
    # Sec 18
    {"year": 3, "sec": "18", "name": "Ms. Shaik Kareena Yashmin", "phone": "7801017820", "room": "NB-210"},
    {"year": 3, "sec": "18", "name": "Mr. Kudupudi Raj Kiran", "phone": "9542687850", "room": "NB-420"},
    # Sec 19
    {"year": 3, "sec": "19", "name": "Mr. D. Senthil", "phone": "8925096166", "room": "NB-301A"},
    {"year": 3, "sec": "19", "name": "Mr. Kanna Hareesh", "phone": "9948723118", "room": "NB-401A"},
    # Sec 20
    {"year": 3, "sec": "20", "name": "Mr. P. Venkata Rajulu", "phone": "9705021183", "room": "NB-303"},
    {"year": 3, "sec": "20", "name": "Mr. Shaik Dehtaj", "phone": "9010380116", "room": "NB-210"},
    # Sec 21
    {"year": 3, "sec": "21", "name": "Ms. Nese Bandhike Akhilandeswari", "phone": "9347927112", "room": "NB-210"},
    {"year": 3, "sec": "21", "name": "Ms. Annam Durga Bhavani", "phone": "9347927112", "room": "NB-210"},
    # Sec 22
    {"year": 3, "sec": "22", "name": "Dr. J. Veeranjaneyulu", "phone": "9492246551", "room": "NB-509"},
    {"year": 3, "sec": "22", "name": "Ms. Christiana Rose Elizabeth Korrapati", "phone": "7816092857", "room": "NB-420"},
]

# Process Faculty and Counsellors
COUNSELLORS = []

# Add Year 2 Counsellors
for c in YEAR2_COUNSELLORS_RAW:
    fac_id = add_faculty(c["name"], phone=c["phone"], room=c["room"], source_id="src-y2-couns")
    r_text = f"{c['r_start']} - {c['r_end']}" if c.get("r_start") and c.get("r_end") else None
    COUNSELLORS.append({
        "id": f"couns-y2-s{c['sec']}-{len(COUNSELLORS)+1}",
        "academic_year": "2026-2027",
        "year": 2,
        "section": c["sec"],
        "counsellor_name": c["name"],
        "faculty_id": fac_id,
        "phone": c["phone"],
        "room": c["room"],
        "registration_range_start": c.get("r_start"),
        "registration_range_end": c.get("r_end"),
        "registration_range_text": r_text,
        "source_id": "src-y2-couns",
        "confidence": "high",
        "last_verified": "2026-08-26",
    })

# Add Year 3 Counsellors
for c in YEAR3_COUNSELLORS_RAW:
    fac_id = add_faculty(c["name"], phone=c["phone"], room=c["room"], source_id="src-y3-couns")
    COUNSELLORS.append({
        "id": f"couns-y3-s{c['sec']}-{len(COUNSELLORS)+1}",
        "academic_year": "2026-2027",
        "year": 3,
        "section": c["sec"],
        "counsellor_name": c["name"],
        "faculty_id": fac_id,
        "phone": c["phone"],
        "room": c["room"],
        "registration_range_start": None,
        "registration_range_end": None,
        "registration_range_text": None,
        "source_id": "src-y3-couns",
        "confidence": "high",
        "last_verified": "2026-08-26",
    })

# 7. ACADEMIC SUPPORT (Academic Leads, Boards, Committees)
ACADEMIC_SUPPORT = []

def add_academic_support(role_name, person_name, phone=None, email=None, room=None, responsibilities=None, office_id=None, source_id="src-acad-leads"):
    fac_id = add_faculty(person_name, phone=phone, room=room, email=email, source_id=source_id)
    ACADEMIC_SUPPORT.append({
        "id": f"supp-{len(ACADEMIC_SUPPORT)+1:03d}",
        "role_name": role_name,
        "person_name": person_name,
        "faculty_id": fac_id,
        "responsibilities": responsibilities,
        "office_id": office_id,
        "room": room,
        "phone": phone,
        "email": email,
        "source_id": source_id,
        "confidence": "high",
        "last_verified": "2026-08-26",
    })

# III Year Academic Leads
acad_lead_resp = "Daily Course Work Monitoring, Course Feedback, Syllabus Depth Coverage, Attendance Monitoring, Attendance Weekly / Monthly Publishing, Condonation and R Grade List Finalization, Follow-up of Slow Learners, Conduct of Value Added Courses, Industry Interface Courses / Course Content Coverage with Industry Personnel"
add_academic_support("III-Year Academic Lead", "Dr. Renuga Devi", phone="9342247173", responsibilities=acad_lead_resp, source_id="src-acad-leads")
add_academic_support("III-Year Academic Lead", "Dr. Vinoj", phone="9751489857", responsibilities=acad_lead_resp, source_id="src-acad-leads")
add_academic_support("III-Year Academic Lead", "Mrs. V. Anusha", phone="9704754065", responsibilities=acad_lead_resp, source_id="src-acad-leads")

# Academic Leads Grid
add_academic_support("Student Affairs Coordinator", "Mr. P. Vijaya Babu", phone="9985333934", room="409", office_id="off-bosa-cse", responsibilities="Student affairs coordination, student activities and grievance handling", source_id="src-acad-leads")
add_academic_support("Student Affairs Coordinator", "Mr. D. Balakotaiah", phone="9059093829", room="409", office_id="off-bosa-cse", responsibilities="Student affairs coordination, student activities and grievance handling", source_id="src-acad-leads")
add_academic_support("Exam Related Activities Coordinator", "Dr. R. Prathap Kumar", phone="7569888963", room="409", office_id="off-boe-cse", responsibilities="Internal and semester-end exam issues, hall tickets, exam registration, revaluation", source_id="src-acad-leads")
add_academic_support("Slow Learners, Backlogs & Summer Semester Coordinator", "Mr. T. Narasimha Rao", phone="9441075258", responsibilities="Maintaining records of students with backlogs, coordinating remedial and mentoring sessions, and organizing summer semester courses in collaboration with course-wise faculty", source_id="src-acad-leads")
add_academic_support("NSS Club Coordinator", "Mr. K. Kiran Kumar", phone="9494965571", room="NB-403", responsibilities="NSS club coordination and student community initiatives", source_id="src-acad-leads")
add_academic_support("NSS Club Coordinator", "Mr. E. Akhil Babu", phone="8465999059", room="NB-401A", responsibilities="NSS club coordination and student community initiatives", source_id="src-acad-leads")
add_academic_support("NSS Club Coordinator", "Mrs. Archana Nalluri", phone="8985716984", room="NB-320", responsibilities="NSS club coordination and student community initiatives", source_id="src-acad-leads")
add_academic_support("BoA Coordinator (Value Added Courses)", "Mrs. G. Navya", phone="7794993678", room="409", office_id="off-boa-cse", responsibilities="Coordination and monitoring of Value Added Courses", source_id="src-acad-leads")
add_academic_support("BoA Coordinator (Value Added Courses)", "Mr. O. Gandhi", phone="9701463728", room="409", office_id="off-boa-cse", responsibilities="Coordination and monitoring of Value Added Courses", source_id="src-acad-leads")
add_academic_support("NPTEL Coordinator", "Mr. Sk. Jani", phone="8247840320", room="301", responsibilities="NPTEL course registrations, certifications, and student guidance", source_id="src-acad-leads")

# BoSA, BoA, BoE, T&P CSE Posters
add_academic_support("BoSA Coordinator", "Mr. P. Vijaya Babu", phone="9985333934", room="409", office_id="off-bosa-cse", responsibilities="Student Club Activities & Events, Student Discipline Monitoring, Student Issues & Grievance Support, Student Achievements & OD Recommendations, Student Counselling and Guidance, Student Welfare Activities", source_id="src-bosa-boa-boe-tp")
add_academic_support("BoSA Coordinator", "Mr. D. Balakotaiah", phone="9059093829", room="409", office_id="off-bosa-cse", responsibilities="Student Club Activities & Events, Student Discipline Monitoring, Student Issues & Grievance Support, Student Achievements & OD Recommendations, Student Counselling and Guidance, Student Welfare Activities", source_id="src-bosa-boa-boe-tp")
add_academic_support("BoA Coordinator", "Mr. O. Gandhi", phone="9701463728", room="409", office_id="off-boa-cse", responsibilities="Syllabus Coverage Monitoring, Course Progress Monitoring, Academic Credit Issues, Attendance Monitoring, Course Registration Support, Academic Regulations & Guidelines, Faculty-Student Academic Coordination, Value Added Courses Monitoring, Academic Queries and Support", source_id="src-bosa-boa-boe-tp")
add_academic_support("BoA Coordinator", "Ms. G. Navya", phone="7794993678", room="409", office_id="off-boa-cse", responsibilities="Syllabus Coverage Monitoring, Course Progress Monitoring, Academic Credit Issues, Attendance Monitoring, Course Registration Support, Academic Regulations & Guidelines, Faculty-Student Academic Coordination, Value Added Courses Monitoring, Academic Queries and Support", source_id="src-bosa-boa-boe-tp")
add_academic_support("BoE Coordinator", "Dr. Prataap Kumar", phone="7569888963", room="409", office_id="off-boe-cse", responsibilities="Internal Examination Issues, Semester End Examination Queries, Hall Ticket Issues, Examination Registration, Revaluation & Challenge Valuation Guidance, Makeup/Supplementary Examination Support, Results & Grade Related Queries, Examination Notifications", source_id="src-bosa-boa-boe-tp")
add_academic_support("T&P-CSE Coordinator", "Dr. Balu Narasimharao", phone="9701224847", room="409", office_id="off-tp-cse", responsibilities="Campus Recruitment Training, Placements, Certificate Programs, Training Attendance", source_id="src-bosa-boa-boe-tp")
add_academic_support("T&P-CSE Coordinator", "Ms. Leelavathi", phone="8919420637", room="409", office_id="off-tp-cse", responsibilities="Campus Recruitment Training, Placements, Certificate Programs, Training Attendance", source_id="src-bosa-boa-boe-tp")

# Department Committees
add_academic_support("Social Media Coordinator", "K. Jyotsna", phone="7337373032", email="jk_cse@vignan.ac.in", room="301", office_id="off-social-media-cse", responsibilities="Department Website content updates, Instagram, LinkedIn & other social media management, Event coverage, Faculty & Student Achievement promotions, FDPs/Workshops/Guest Lecture publicity, Placement/Internship/Hackathon updates, Content writing & poster design, Brand consistency, Archiving digital media", source_id="src-dept-comm")
add_academic_support("Social Media Coordinator", "Sk. Jani", phone="8247840320", email="jk_cse@vignan.ac.in", room="301", office_id="off-social-media-cse", responsibilities="Department Website content updates, Instagram, LinkedIn & other social media management, Event coverage, Faculty & Student Achievement promotions, FDPs/Workshops/Guest Lecture publicity, Placement/Internship/Hackathon updates, Content writing & poster design, Brand consistency, Archiving digital media", source_id="src-dept-comm")
add_academic_support("Magazine Committee Member", "Dr. Vijitha Ananthi", phone="9790628946", email="magazine_cse@vignan.ac.in", room="310", office_id="off-magazine-cse", responsibilities="Collect articles, technical papers & creative write-ups, Compile Faculty & Student achievements, Document department events, Edit proofread and format magazine content, Design newsletter layout, Publish department magazine", source_id="src-dept-comm")
add_academic_support("Magazine Committee Member", "V. Sai Spandana", phone="9948368555", email="magazine_cse@vignan.ac.in", room="310", office_id="off-magazine-cse", responsibilities="Collect articles, technical papers & creative write-ups, Compile Faculty & Student achievements, Document department events, Edit proofread and format magazine content, Design newsletter layout, Publish department magazine", source_id="src-dept-comm")
add_academic_support("Department Overall Coordinator", "Mr. P. Vijaya Babu", phone="9985333934", room="409", responsibilities="Overall coordination of department activities, social media, magazine and student affairs", source_id="src-dept-comm")

# Convert Faculty dict to list
FACULTY_LIST = list(FACULTY_DATA.values())

# 8. SUBJECTS, SERVICES, ROUTES
# Keep verified empty lists or verified minimal structures
SUBJECTS = []
SERVICES = []
ROUTES = []

def save_json(filename, data):
    path = os.path.join(EXTRACTED_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Saved {filename} ({len(data)} records)")

def run():
    print("Writing extracted dataset...")
    save_json("sources.json", SOURCES)
    save_json("locations.json", LOCATIONS)
    save_json("departments.json", DEPARTMENTS)
    save_json("offices.json", OFFICES)
    save_json("faculty.json", FACULTY_LIST)
    save_json("counsellors.json", COUNSELLORS)
    save_json("academic_support.json", ACADEMIC_SUPPORT)
    save_json("subjects.json", SUBJECTS)
    save_json("services.json", SERVICES)
    save_json("routes.json", ROUTES)
    print("\nDataset extraction complete!")

if __name__ == "__main__":
    run()
