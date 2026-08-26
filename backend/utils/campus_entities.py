"""Campus entity normalization, alias resolution, and intent understanding for VIGNAN Campus Agent.

Maps diverse natural language phrases, synonyms, and abbreviations to verified canonical
campus entities, categories, and operational tools without hardcoding individual Q&A responses.
"""

import re
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
from backend.utils.normalization import normalize_text


class CampusIntent(str, Enum):
    FACULTY_LOOKUP = "faculty_lookup"
    DEPARTMENT_LOOKUP = "department_lookup"
    SUBJECT_LOOKUP = "subject_lookup"
    COUNSELLOR_LOOKUP = "counsellor_lookup"
    OFFICE_LOOKUP = "office_lookup"
    RESPONSIBILITY_LOOKUP = "responsibility_lookup"
    SERVICE_LOOKUP = "service_lookup"
    LOCATION_LOOKUP = "location_lookup"
    NAVIGATION_REQUEST = "navigation_request"
    LIVE_STATUS_REQUEST = "live_status_request"
    BEST_SERVICE_REQUEST = "best_service_request"
    CAMPUS_INFORMATION_REQUEST = "campus_information_request"
    OUT_OF_SCOPE_REQUEST = "out_of_scope_request"
    CLARIFICATION_REQUIRED = "clarification_required"


# Canonical campus entities with verified aliases and category mappings
CANONICAL_ENTITIES: Dict[str, Dict[str, Any]] = {
    "mhp_canteen": {
        "canonical_name": "MHP / Main Canteen",
        "category": "canteen",
        "aliases": [
            "mhp canteen", "main canteen", "main cafeteria", "mhp",
            "mhp / main canteen", "zest area", "mhp / zest area", "mhp zest area", "zest",
            "cafeteria", "canteen", "food", "lunch", "snacks",
            "breakfast", "mess", "food court", "eating area", "dining",
            "where do students eat", "where can i get food", "where can i get lunch",
            "get lunch", "get food"
        ],
        "default_block": "MHP / Zest Area",
        "primary_tool": "search_service",
    },
    "xerox_facility": {
        "canonical_name": "Xerox Facility — Near MHP / Zest Area",
        "category": "xerox",
        "aliases": [
            "xerox near mhp", "xerox near zest", "xerox near the mhp zest area",
            "xerox near zest area", "mhp xerox", "zest xerox", "xerox in zest",
            "xerox near main canteen", "xerox facility near mhp", "xerox facility near zest",
            "where is the xerox near mhp", "where is the xerox near zest", "where is the xerox near the mhp zest area",
            "xerox shop", "copy shop", "printing shop", "photo copy",
            "photocopy", "xerox", "printing", "print", "color print",
            "print assignment", "zerox", "spiral binding", "printout",
            "print out", "document print", "copy", "i need a photocopy",
            "where can i photocopy", "where can i print"
        ],
        "default_block": "A Block / MHP / Zest Area",
        "primary_tool": "search_service",
    },
    "transport_office": {
        "canonical_name": "Transport Office & Bus Pass Counter",
        "category": "transport",
        "aliases": [
            "transport department", "transport office", "bus pass office",
            "bus office", "bus route", "bus passes", "bus pass",
            "transport", "buses", "bus fee", "bus counter", "college bus",
            "route schedule", "where do i get my bus pass"
        ],
        "default_block": "Main Gate Area",
        "primary_tool": "search_service",
    },
    "finance_office": {
        "canonical_name": "Finance & Accounts Office",
        "category": "office",
        "aliases": [
            "finance office", "finance & accounts office", "fee payment office",
            "fees office", "fee payment", "pay fees", "fees section", "tuition fee",
            "fee counter", "accounts office", "finance", "fees", "accounts", "challan",
            "where do i pay my fees", "where can i pay my fees", "where do i go for fee payment"
        ],
        "default_block": "A Block 1st Floor",
        "primary_tool": "search_office",
    },
    "dept_it": {
        "canonical_name": "Information Technology",
        "short_name": "IT",
        "category": "department",
        "aliases": [
            "information technology", "it department", "it dept",
            "department of it", "it faculty", "it block", "it",
            "who heads it", "who heads information technology", "it hod", "hod of it"
        ],
        "default_block": "U Block",
        "primary_tool": "search_department",
    },
    "dept_cse": {
        "canonical_name": "Computer Science & Engineering (Core)",
        "short_name": "CSE",
        "category": "department",
        "aliases": [
            "computer science engineering", "computer science and engineering",
            "computer science & engineering", "computer science",
            "cse core", "cse department", "cse spec", "cse specializations",
            "department of cse", "cse faculty", "cse block", "cse",
            "who heads cse", "who heads computer science", "cse hod", "hod of cse"
        ],
        "default_block": "N Block",
        "primary_tool": "search_department",
    },
    "dept_acse": {
        "canonical_name": "Advanced Computer Science & Engineering",
        "short_name": "ACSE",
        "category": "department",
        "aliases": [
            "advanced computer science engineering", "advanced computer science and engineering",
            "advanced computer science", "advanced cse", "acse department", "acse"
        ],
        "default_block": "N Block",
        "primary_tool": "search_department",
    },
    "dept_ece": {
        "canonical_name": "Electronics & Communication Engineering",
        "short_name": "ECE",
        "category": "department",
        "aliases": [
            "electronics & communication engineering", "electronics and communication engineering",
            "electronics and communication", "ece department", "ece"
        ],
        "default_block": "H Block",
        "primary_tool": "search_department",
    },
    "dept_eee": {
        "canonical_name": "Electrical & Electronics Engineering",
        "short_name": "EEE",
        "category": "department",
        "aliases": ["electrical and electronics engineering", "eee department", "eee"],
        "default_block": "H Block",
        "primary_tool": "search_department",
    },
    "dept_biotech": {
        "canonical_name": "Biotechnology",
        "short_name": "Biotech",
        "category": "department",
        "aliases": ["biotechnology", "bio technology", "biotech department", "biotech"],
        "default_block": "U Block",
        "primary_tool": "search_department",
    },
    "dept_chemical": {
        "canonical_name": "Chemical Engineering",
        "short_name": "Chemical",
        "category": "department",
        "aliases": ["chemical engineering", "chemical department", "chemical"],
        "default_block": "H Block",
        "primary_tool": "search_department",
    },
    "dept_civil": {
        "canonical_name": "Civil Engineering",
        "short_name": "Civil",
        "category": "department",
        "aliases": ["civil engineering", "civil department", "civil"],
        "default_block": "U Block",
        "primary_tool": "search_department",
    },
    "dept_mech": {
        "canonical_name": "Mechanical Engineering",
        "short_name": "Mech",
        "category": "department",
        "aliases": ["mechanical engineering", "mech department", "mechanical", "mech"],
        "default_block": "U Block",
        "primary_tool": "search_department",
    },
    "dept_food_tech": {
        "canonical_name": "Food Technology",
        "short_name": "Food Tech",
        "category": "department",
        "aliases": ["food technology", "food tech department", "food tech"],
        "default_block": "H Block",
        "primary_tool": "search_department",
    },
    "dept_pharmacy": {
        "canonical_name": "Pharmacy Block / School of Pharmacy",
        "short_name": "Pharmacy",
        "category": "department",
        "aliases": ["pharmacy block", "school of pharmacy", "pharmacy", "pharma"],
        "default_block": "Pharmacy Block",
        "primary_tool": "get_location",
    },
    "dept_textile": {
        "canonical_name": "Textile Engineering",
        "short_name": "Textile",
        "category": "department",
        "aliases": ["textile engineering", "textile block", "textile"],
        "default_block": "Textile Block",
        "primary_tool": "search_department",
    },
    "dept_law": {
        "canonical_name": "Law",
        "short_name": "Law",
        "category": "department",
        "aliases": ["department of law", "school of law", "law department", "law"],
        "default_block": "U Block",
        "primary_tool": "search_department",
    },
    "dept_management": {
        "canonical_name": "Management Studies",
        "short_name": "MBA",
        "category": "department",
        "aliases": ["management studies", "business school", "management", "mba", "bba"],
        "default_block": "U Block",
        "primary_tool": "search_department",
    },
    "placements": {
        "canonical_name": "Training & Placements (T&P)",
        "category": "responsibility",
        "aliases": [
            "training and placement", "training & placements", "placement coordinator",
            "campus placement", "placement cell", "t&p-cse", "placements", "placement",
            "jobs", "internships", "t&p", "who handles placements"
        ],
        "default_block": "N Block",
        "primary_tool": "search_responsibility",
    },
    "grievances": {
        "canonical_name": "Student Grievances & Affairs",
        "category": "responsibility",
        "aliases": [
            "student grievances", "student grievance", "anti ragging", "women grievance",
            "grievances", "grievance", "complaints", "discipline", "ragging", "student issues"
        ],
        "default_block": "N Block",
        "primary_tool": "search_responsibility",
    },
    "examinations": {
        "canonical_name": "Board of Examinations (BoE)",
        "category": "responsibility",
        "aliases": [
            "board of examinations", "revaluation", "re valuation", "hall ticket",
            "grade card", "condonation", "supplementary", "examinations", "exam", "exams",
            "boe", "marks", "results", "r grade"
        ],
        "default_block": "N Block",
        "primary_tool": "search_responsibility",
    },
    "student_affairs": {
        "canonical_name": "Board of Student Affairs (BoSA)",
        "category": "responsibility",
        "aliases": ["board of student affairs", "student activities", "bosa", "clubs", "fest", "events"],
        "default_block": "N Block",
        "primary_tool": "search_responsibility",
    },
    "academics_board": {
        "canonical_name": "Board of Academics (BoA)",
        "category": "responsibility",
        "aliases": ["board of academics", "curriculum", "syllabus", "boa", "course feedback", "attendance publishing"],
        "default_block": "N Block",
        "primary_tool": "search_responsibility",
    },
}

# General out-of-scope question triggers that are clearly non-campus
OUT_OF_SCOPE_PATTERNS = [
    r"\b(write a python|write python|write a code|write me a python|python script|solve this code|binary search program|write code|code in python|write java code|write c\+\+)\b",
    r"\b(who won|president of the usa|prime minister of|white house|election results|donald trump|joe biden|narendra modi)\b",
    r"\b(what is quantum physics|theory of relativity|photosynthesis process|how black holes work|laws of thermodynamics|what is machine learning|explain quantum|quantum computing)\b",
    r"\b(tell me a joke|tell a joke|tell me a story|sing a song|write a poem)\b",
    r"\b(cricket match score|ipl score|football match|world cup winner|olympics score|who won the cricket|who won the match)\b",
    r"\b(what is the capital of|recipe for chocolate cake|make pizza)\b",
]

OUT_OF_SCOPE_REFUSAL = (
    "I'm the VIGNAN Campus Intelligence Assistant. I can help with verified information "
    "about VIGNAN University, including faculty, departments, offices, services, counsellors, "
    "and campus locations."
)


def strip_honorifics(name: Optional[str]) -> str:
    """Remove common academic/polite honorifics and extract the core name token."""
    if not name:
        return ""
    cleaned = re.sub(r"(?i)\b(dr|prof|mr|mrs|ms|er)\.?\b", " ", str(name))
    cleaned = re.sub(r"(?i)\b(sir|madam)\b", " ", cleaned)
    cleaned = re.sub(r"[^\w\s]", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def is_out_of_scope(message: str) -> bool:
    """Determine if user query is strictly outside the domain of VIGNAN campus intelligence."""
    norm = normalize_text(message)
    if not norm:
        return False

    for pat in OUT_OF_SCOPE_PATTERNS:
        if re.search(pat, norm):
            return True

    # Check if explicitly asking about campus elements
    if any(w in norm for w in [
        "vignan", "campus", "hod", "faculty", "counsellor", "counselor", "block",
        "room", "floor", "gate", "xerox", "canteen", "fees", "placement", "mhp",
        "syllabus", "subject", "teacher", "dr", "prof", "professor", "sir", "madam", "head of", "department"
    ]):
        return False

    return False


def resolve_campus_entity(query: str) -> Optional[Dict[str, Any]]:
    """Match a natural language query or keyword to a canonical campus entity."""
    norm = normalize_text(query)
    if not norm:
        return None

    # Check exact matches first
    for entity_key, meta in CANONICAL_ENTITIES.items():
        if norm == normalize_text(meta["canonical_name"]) or norm == normalize_text(meta.get("short_name", "")):
            return meta

    # Check aliases (longer aliases first to prevent partial shadow)
    matched_meta = None
    max_len = 0
    for entity_key, meta in CANONICAL_ENTITIES.items():
        for alias in meta["aliases"]:
            if norm == alias or (len(alias) >= 2 and re.search(rf"\b{re.escape(alias)}\b", norm)):
                if len(alias) > max_len:
                    max_len = len(alias)
                    matched_meta = meta

    return matched_meta


def classify_campus_intent(message: str, user_context: Optional[Dict[str, Any]] = None) -> Tuple[CampusIntent, Dict[str, Any]]:
    """
    Lightweight rule-guided natural-language intent classification and entity extraction.
    Works as the offline / verification dispatch layer alongside Gemini's native reasoning.
    """
    norm = normalize_text(message)
    details: Dict[str, Any] = {}

    # 1. Check Out of Scope
    if is_out_of_scope(message):
        return CampusIntent.OUT_OF_SCOPE_REQUEST, {"refusal": OUT_OF_SCOPE_REFUSAL}

    # 2. Navigation / Routes (check before location/department)
    is_nav = any(w in norm for w in [
        "how do i get to", "how to reach", "take me to", "directions to", "route to",
        "way to", "navigate to", "path to", "route from", "directions from", "how can i reach",
        "how do i go from", "show me the route", "how do i get from", "directions", "navigation"
    ])
    if is_nav and any(w in norm for w in ["from", "to", "reach", "take me", "show me the route", "route", "directions", "way"]):
        return CampusIntent.NAVIGATION_REQUEST, details

    # 3. Counsellor Flow
    is_counsellor = any(w in norm for w in ["counsellor", "counselor", "mentor", "advisor", "who is my counsellor", "who is my counselor", "who is my class counsellor"])
    reg_match = re.search(r"\b\d{2,3}[a-zA-Z]{1,3}\d{3,5}\b", message) or re.search(r"\b\d{4}\b", message)
    year_match = re.search(r"\b([1-4])(?:st|nd|rd|th)?\s*year\b", norm) or re.search(r"\byear\s*([1-4])\b", norm)
    sec_match = re.search(r"\bsection\s*([a-zA-Z0-9]+)\b", norm) or re.search(r"\bsec\s*([a-zA-Z0-9]+)\b", norm)

    if is_counsellor or (reg_match and not any(w in norm for w in ["faculty", "cabin", "hod", "dean"])) or (year_match and sec_match and not any(w in norm for w in ["faculty", "subject", "course"])):
        details["year"] = int(year_match.group(1)) if year_match else (user_context.get("year") if user_context else None)
        details["section"] = sec_match.group(1).upper() if sec_match else (user_context.get("section") if user_context else None)
        details["registration_number"] = reg_match.group(0) if reg_match else None
        return CampusIntent.COUNSELLOR_LOOKUP, details

    # 4. Best Service / Live Status Recommendation
    is_best_service = any(w in norm for w in ["which xerox is free", "least crowded", "shortest queue", "which canteen is free", "best xerox", "fastest xerox", "recommend xerox", "which xerox should i use", "where should i go right now"])
    if is_best_service:
        cat = "canteen" if any(w in norm for w in ["canteen", "food", "mhp"]) else "xerox"
        details["category"] = cat
        return CampusIntent.BEST_SERVICE_REQUEST, details

    # 5. Live Queue Status
    is_live = any(w in norm for w in ["queue", "crowded", "how busy", "wait time", "waiting time", "current status", "is it open", "how many students"])
    if is_live and any(w in norm for w in ["xerox", "canteen", "mhp", "print", "photocopy", "counter"]):
        return CampusIntent.LIVE_STATUS_REQUEST, details

    # 6. Ambiguous Office Clarification Request
    if norm in ["where is the office", "where is the office?", "where is office", "office location", "college office"]:
        return CampusIntent.CLARIFICATION_REQUIRED, {
            "question": "Which office are you looking for – Finance & Accounts, Transport, Placements (T&P), Board of Examinations (BoE), or Board of Student Affairs (BoSA)?"
        }

    # 7. Department / HOD Lookup (High Priority)
    is_hod_query = any(w in norm for w in [
        "who is the hod", "who heads", "who is the head of", "who leads",
        "hod of", "head of department", "head of the department", "department head", "dept head",
        "who is hod", "head of computer science", "head of information technology", "head of cse", "head of it"
    ])
    is_dept_block_query = any(w in norm for w in [
        "which block has", "what building is", "where is the department", "which departments are in",
        "departments in", "departments list", "list departments", "which block is it in", "which block has it",
        "which block has cse", "which block is cse", "which block is it", "which block is", "what block is", "in which block is"
    ])
    if is_hod_query or is_dept_block_query:
        return CampusIntent.DEPARTMENT_LOOKUP, details

    # 8. Responsibilities / Campus Leads
    is_resp = any(w in norm for w in ["placement", "placements", "t&p", "crt", "grievance", "grievances", "complaint", "anti ragging", "hall ticket", "revaluation", "boe", "bosa", "boa", "student affairs", "clubs", "coordinator", "who handles placements"])
    if is_resp and not any(w in norm for w in ["where is it department", "where is cse department"]):
        return CampusIntent.RESPONSIBILITY_LOOKUP, details

    # 9. Offices (Finance / Fees)
    if any(w in norm for w in ["finance", "fee", "fees", "challan", "accounts office", "finance office", "pay fees", "fees section", "tuition fee", "where can i pay my fees", "where do i pay my fees", "where is finance"]):
        return CampusIntent.OFFICE_LOOKUP, details

    # 10. Services (Canteen, MHP, Zest, Xerox, Printing, Transport, Bus Pass)
    if any(w in norm for w in [
        "mhp", "zest", "zest area", "canteen", "food", "lunch", "cafeteria", "breakfast", "mess", "dining",
        "where is mhp", "where's mhp", "where is zest", "where is the main canteen", "where is the main cafeteria", "where can i get lunch", "where can i get food", "where do students eat",
        "xerox", "photocopy", "printing", "print", "copy shop", "where can i photocopy", "i need a photocopy", "where can i print", "where is the copy shop",
        "transport", "bus pass", "bus route", "buses", "where do i get my bus pass", "where is transport", "where is the bus office", "where is the transport office"
    ]):
        return CampusIntent.SERVICE_LOOKUP, details

    # 11. Faculty Lookup / Research / Teaching / Identity
    is_fac = any(w in norm for w in [
        "dr", "prof", "professor", "sir", "madam", "teacher", "cabin", "meet dr", "where is dr",
        "who is dr", "where can i meet", "room number of", "research", "researches", "teach", "teaches",
        "courses of", "subjects of", "what does", "who is balu", "where is balu", "balu sir", "where can i meet balu"
    ])
    if is_fac:
        return CampusIntent.FACULTY_LOOKUP, details

    # 12. Direct Department Name Mention (e.g., "Where is IT?", "Where is CSE?")
    if any(w in norm for w in ["where is it", "where is cse", "where is ece", "where is eee", "where is mechanical", "where is civil", "where is biotechnology", "where is chemical"]):
        return CampusIntent.DEPARTMENT_LOOKUP, details

    # 13. Physical Location / Blocks
    if any(w in norm for w in ["block", "building", "gate", "ground", "auditorium", "pharmacy block", "textile block", "n block", "u block", "h block", "a block"]):
        return CampusIntent.LOCATION_LOOKUP, details

    # 14. General Campus Information (e.g. how many departments)
    if any(w in norm for w in ["how many departments", "how many courses", "about vignan", "university overview", "tell me about vignan"]):
        return CampusIntent.CAMPUS_INFORMATION_REQUEST, details

    # Default to semantic entity resolution
    resolved = resolve_campus_entity(message)
    if resolved:
        pt = resolved.get("primary_tool")
        if pt == "search_service":
            return CampusIntent.SERVICE_LOOKUP, details
        elif pt == "search_office":
            return CampusIntent.OFFICE_LOOKUP, details
        elif pt == "search_department":
            return CampusIntent.DEPARTMENT_LOOKUP, details
        elif pt == "search_responsibility":
            return CampusIntent.RESPONSIBILITY_LOOKUP, details
        elif pt == "get_location":
            return CampusIntent.LOCATION_LOOKUP, details

    return CampusIntent.FACULTY_LOOKUP, details
