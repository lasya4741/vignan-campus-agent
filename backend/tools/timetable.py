import json
import os
import re
from datetime import datetime, time, date as date_cls
import pytz
from typing import Any, Dict, List, Optional, Tuple

from backend.config import settings
from backend.supabase_client import db
from backend.utils.logging import logger

KOLKATA_TZ = pytz.timezone("Asia/Kolkata")

from datetime import datetime, time, timedelta, date as date_cls
import pytz
from typing import Any, Dict, List, Optional, Tuple

from backend.config import settings
from backend.supabase_client import db
from backend.utils.logging import logger
from backend.tools.navigation import build_google_maps_url

KOLKATA_TZ = pytz.timezone("Asia/Kolkata")

def get_now_kolkata() -> datetime:
    """Return current datetime in Asia/Kolkata timezone."""
    return datetime.now(KOLKATA_TZ)

def load_local_timetable_records(year: int) -> List[Dict[str, Any]]:
    """Load local extracted JSON timetable records as fallback/fast-lookup."""
    filename = "year2_timetable.json" if year == 2 else "year3_timetable.json"
    file_path = os.path.join(os.path.dirname(__file__), "..", "..", "database", "extracted", "timetables", filename)
    file_path = os.path.abspath(file_path)
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading {file_path}: {e}")
    return []

def merge_continuous_slots(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Merge adjacent timetable entries for the same subject, class type, and room into a single continuous block."""
    if not records:
        return []
    
    merged = []
    current = None

    for rec in records:
        if current is None:
            current = dict(rec)
            continue
        
        curr_et = str(current.get("end_time", "")).strip()
        rec_st = str(rec.get("start_time", "")).strip()
        
        same_subject = (str(current.get("subject_code", "")).strip().upper() == str(rec.get("subject_code", "")).strip().upper())
        same_type = (str(current.get("class_type", "")).strip().upper() == str(rec.get("class_type", "")).strip().upper())
        same_room = (str(current.get("room", "")).strip().upper() == str(rec.get("room", "")).strip().upper())
        
        if curr_et and rec_st and curr_et[:5] == rec_st[:5] and same_subject and same_type and same_room:
            current["end_time"] = rec.get("end_time")
        else:
            merged.append(current)
            current = dict(rec)
            
    if current:
        merged.append(current)
        
    return merged

def query_timetable(year: int, section: str, day_of_week: Optional[str] = None) -> List[Dict[str, Any]]:
    """Query timetable entries for a specific year, section, and optional day."""
    sec_str = str(section).strip().replace("Section ", "").replace("sec", "")
    
    records = []
    source_used = "local_fallback"

    # 1. Try Supabase first if connected
    if db.is_connected():
        try:
            query = db.client.table("timetables").select("*").eq("year", year).eq("section", sec_str)
            if day_of_week:
                query = query.eq("day_of_week", day_of_week.capitalize())
            res = query.order("start_time").execute()
            if res.data:
                for r in res.data:
                    rec = dict(r)
                    if "day_of_week" in rec:
                        rec["day"] = rec["day_of_week"]
                    if rec.get("start_time"):
                        rec["start_time"] = str(rec["start_time"])[:5]
                    if rec.get("end_time"):
                        rec["end_time"] = str(rec["end_time"])[:5]
                    records.append(rec)
                source_used = "live_supabase"
        except Exception as e:
            logger.warning(f"Supabase timetable query failed: {e}. Falling back to local dataset.")
            records = []
            
    # 2. Fallback to local JSON datasets if Supabase returned nothing or failed
    if not records:
        local_recs = load_local_timetable_records(year)
        for r in local_recs:
            r_sec = str(r.get("section", "")).strip().replace("Section ", "").replace("sec", "")
            r_day = r.get("day") or r.get("day_of_week")
            if str(r.get("year")) == str(year) and r_sec == sec_str:
                if day_of_week is None or r_day.lower() == day_of_week.lower():
                    records.append(dict(r))
        source_used = "local_fallback"
                
    # Sort by start_time
    records.sort(key=lambda x: x.get("start_time", ""))
    merged_records = merge_continuous_slots(records)
    logger.info(f"Timetable queried for Year {year} Sec {section} ({day_of_week}) -> source={source_used}, {len(merged_records)} blocks")
    return merged_records

SUBJECT_FACULTY_MAP = {
    # Year 2 Subjects
    "DLD": ["CSDLD", "Digital Logic Design"],
    "DS": ["CSDS", "22CS203", "Data Structure", "Data Structures"],
    "DBMS": ["22CS201", "CSDMS", "CSD", "Database Management Systems"],
    "DBMS LAB": ["22CS201", "CSDMS", "CSD", "Database Management Systems"],
    "AI": ["CSAI", "Artificial Intelligence", "Artificial Intelleigence"],
    "DMS": ["25MT202", "CSDMS", "Discrete Mathematical Structures"],
    "OOPS": ["CSOTJ", "CSDMLT", "Object Oriented Programming"],
    "OOPS LAB": ["CSOTJ", "CSDMLT", "Object Oriented Programming"],

    # Year 3 Subjects
    "ML": ["24CS306", "CSML", "Machine Learning"],
    "ML LAB": ["24CS306", "CSML", "Machine Learning"],
    "CN": ["24CS303", "CSCN", "Computer Networks"],
    "CN LAB": ["24CS303", "CSCN", "Computer Networks"],
    "FLAT": ["CSFLAT", "Formal Languages & Automata Theory", "Formal Languages and Automata Theory"],
    "SE": ["CSSE", "Software Engineering"],
    "MFEF": ["CSMFEF", "Managerial Economics & Financial Analysis", "Managerial Finance"],
    "CE": ["CSCE", "Competitive Engineering", "Professional Ethics"],
    "OT": ["CSOT", "Optimization Techniques"],
    "PC LAB": ["CSCPDS", "Professional Communication Lab", "Programming"],
}

def get_subject_faculty(subject_code: str) -> Optional[Dict[str, Any]]:
    """Resolve faculty teaching a given subject code using live Supabase or local fallback."""
    if not subject_code:
        return None

    code_clean = subject_code.strip().upper()
    target_names = SUBJECT_FACULTY_MAP.get(code_clean, [code_clean])

    # 1. Try Live Supabase
    if db.is_connected():
        try:
            subj_ids = []
            for tgt in target_names:
                res = db.client.table("subjects").select("id, name, code").or_(f"code.eq.{tgt},name.ilike.%{tgt}%").execute()
                if res.data:
                    for s in res.data:
                        subj_ids.append(s["id"])
            
            if not subj_ids:
                res = db.client.table("subjects").select("id, name, code").ilike("code", f"%{code_clean}%").execute()
                if res.data:
                    for s in res.data:
                        subj_ids.append(s["id"])

            for s_id in subj_ids:
                fs_res = db.client.table("faculty_subjects").select("faculty_id").eq("subject_id", s_id).execute()
                if fs_res.data:
                    fac_id = fs_res.data[0]["faculty_id"]
                    fac_res = db.client.table("faculty").select("full_name, designation, room, email, phone").eq("id", fac_id).execute()
                    if fac_res.data:
                        return fac_res.data[0]
        except Exception as e:
            logger.warning(f"Supabase faculty subject lookup failed: {e}")

    # 2. Local fallback
    try:
        subj_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "database", "extracted", "subjects.json"))
        fac_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "database", "extracted", "faculty.json"))
        fs_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "database", "extracted", "faculty_subjects.json"))

        if os.path.exists(subj_file) and os.path.exists(fac_file) and os.path.exists(fs_file):
            with open(subj_file, "r", encoding="utf-8") as f:
                subjs = json.load(f)
            with open(fac_file, "r", encoding="utf-8") as f:
                facs = json.load(f)
            with open(fs_file, "r", encoding="utf-8") as f:
                f_subjs = json.load(f)

            matched_subj = None
            for s in subjs:
                s_code = (s.get("code") or "").strip().upper()
                s_name = (s.get("name") or "").strip().upper()
                if s_code == code_clean or any(t.upper() == s_code or t.upper() in s_name for t in target_names):
                    matched_subj = s
                    break

            if matched_subj:
                s_id = matched_subj["id"]
                matched_fs = [fs for fs in f_subjs if fs.get("subject_id") == s_id]
                if matched_fs:
                    f_id = matched_fs[0]["faculty_id"]
                    for f in facs:
                        if f["id"] == f_id:
                            return f
    except Exception as e:
        logger.warning(f"Local faculty subject lookup error: {e}")

    return None

def parse_time_str(t_str: str) -> time:
    """Parse time string like '09:55' or '09:55:00' into datetime.time object."""
    parts = t_str.strip().split(":")
    return time(int(parts[0]), int(parts[1]))

def parse_datetime_input(current_datetime: Optional[str] = None) -> Tuple[datetime, str, time]:
    """Parse current_datetime input or use current India time."""
    if current_datetime:
        try:
            dt = datetime.fromisoformat(current_datetime)
            if dt.tzinfo is None:
                dt = KOLKATA_TZ.localize(dt)
            else:
                dt = dt.astimezone(KOLKATA_TZ)
        except Exception:
            dt = get_now_kolkata()
    else:
        dt = get_now_kolkata()
        
    day_name = dt.strftime("%A")
    current_t = dt.time()
    return dt, day_name, current_t

def resolve_room_and_building(room_str: Optional[str]) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Resolve room, block/building, and floor from room string (e.g. N-314A -> Room N-314A, N Block, 3rd Floor).
    """
    if not room_str or room_str.upper() in ["NONE", "NULL", "BREAK"]:
        return None, None, None
        
    room_clean = room_str.strip()
    block = None
    floor = None
    
    if room_clean.startswith("N-") or room_clean.startswith("N"):
        block = "N Block"
        m_floor = re.search(r'N-(\d)', room_clean)
        if m_floor:
            f_num = m_floor.group(1)
            floor_map = {"1": "1st Floor", "2": "2nd Floor", "3": "3rd Floor", "4": "4th Floor", "5": "5th Floor"}
            floor = floor_map.get(f_num, f"{f_num}th Floor")
    elif "C2-LAB" in room_clean.upper():
        block = "Chebrolu Hanumayya Block (C-Block)"
        floor = "2nd Floor"
        
    return room_clean, block, floor

NON_ACADEMIC_KEYWORDS = [
    "BREAK", "SELF LEARNING", "ADVANCED LEARNING", "COUNSELLING", "COUN", "LIBRARY", "LIB", "SPORTS"
]

def is_academic_class(entry: Dict[str, Any]) -> bool:
    """Check if entry is an academic subject class vs break/self learning/counselling/sports."""
    ctype = (entry.get("class_type") or "").upper()
    scode = (entry.get("subject_code") or "").upper()
    if ctype in ["BREAK", "SELF LEARNING", "COUNSELLING", "CO-CURRICULAR / ACTIVITY"]:
        if any(kw in scode for kw in ["SELF LEARNING", "ADVANCED LEARNING", "COUNSELLING", "BREAK", "LIBRARY", "SPORTS"]):
            return False
    if any(kw in scode for kw in ["BREAK", "SELF LEARNING", "ADVANCED LEARNING", "COUNSELLING", "LIBRARY", "SPORTS"]):
        return False
    return True

def get_current_class(year: int, section: str, current_datetime: Optional[str] = None) -> Dict[str, Any]:
    """
    Determine the current active class for the student.
    Returns current class details, room, next academic class details, and verified teacher details if available.
    """
    dt, day_name, current_t = parse_datetime_input(current_datetime)
    records = query_timetable(year, section, day_name)
    
    current_entry = None
    
    for entry in records:
        st = parse_time_str(entry["start_time"])
        et = parse_time_str(entry["end_time"])
        
        if st <= current_t < et:
            current_entry = entry
            break

    next_class_res = get_next_class(year, section, current_datetime)
    next_academic_data = next_class_res.get("next_class") if next_class_res.get("status") == "success" else None
                
    if not current_entry:
        return {
            "status": "no_active_class",
            "message": "You don't have a scheduled class right now.",
            "day": day_name,
            "current_time": current_t.strftime("%H:%M"),
            "next_class": next_academic_data
        }
        
    # Check if current entry is a break
    if current_entry.get("class_type") == "Break" or current_entry.get("subject_code", "").upper() == "BREAK":
        return {
            "status": "break",
            "message": "You're currently on a break.",
            "day": day_name,
            "current_time": current_t.strftime("%H:%M"),
            "break_start": current_entry["start_time"],
            "break_end": current_entry["end_time"],
            "next_class": next_academic_data
        }
        
    room_name, block, floor = resolve_room_and_building(current_entry.get("room"))
    teacher = get_subject_faculty(current_entry.get("subject_code"))
    
    return {
        "status": "success",
        "current_class": {
            "subject_code": current_entry.get("subject_code"),
            "subject_name": current_entry.get("subject_name"),
            "class_type": current_entry.get("class_type"),
            "start_time": current_entry.get("start_time"),
            "end_time": current_entry.get("end_time"),
            "room": room_name or current_entry.get("section_default_room"),
            "block": block,
            "floor": floor,
            "teacher": teacher
        },
        "next_class": next_academic_data
    }

def get_next_class(year: int, section: str, current_datetime: Optional[str] = None) -> Dict[str, Any]:
    """Find the next upcoming academic class for the student with verified teacher details."""
    dt, day_name, current_t = parse_datetime_input(current_datetime)
    records = query_timetable(year, section, day_name)
    
    next_entry = None
    for entry in records:
        st = parse_time_str(entry["start_time"])
        if current_t < st:
            if is_academic_class(entry):
                next_entry = entry
                break
                
    if not next_entry:
        return {
            "status": "no_more_classes_today",
            "message": "No more classes scheduled for today.",
            "day": day_name
        }
        
    room_name, block, floor = resolve_room_and_building(next_entry.get("room"))
    teacher = get_subject_faculty(next_entry.get("subject_code"))
    
    return {
        "status": "success",
        "next_class": {
            "subject_code": next_entry.get("subject_code"),
            "subject_name": next_entry.get("subject_name"),
            "class_type": next_entry.get("class_type"),
            "start_time": next_entry.get("start_time"),
            "end_time": next_entry.get("end_time"),
            "room": room_name or next_entry.get("section_default_room"),
            "block": block,
            "floor": floor,
            "teacher": teacher
        }
    }



def get_next_timetable_event(year: int, section: str, current_datetime: Optional[str] = None) -> Dict[str, Any]:
    """Find the next immediate timetable event (including break, counselling, self learning, etc.)."""
    dt, day_name, current_t = parse_datetime_input(current_datetime)
    records = query_timetable(year, section, day_name)
    
    next_event = None
    for entry in records:
        st = parse_time_str(entry["start_time"])
        if current_t < st:
            next_event = entry
            break
            
    if not next_event:
        return {
            "status": "no_more_events_today",
            "message": "No more events scheduled for today."
        }
        
    return {
        "status": "success",
        "next_event": {
            "event_name": next_event.get("subject_code"),
            "class_type": next_event.get("class_type"),
            "start_time": next_event.get("start_time"),
            "end_time": next_event.get("end_time"),
            "room": next_event.get("room")
        }
    }

def get_daily_timetable(year: int, section: str, date: Optional[str] = None) -> Dict[str, Any]:
    """Retrieve full day's timetable schedule for the student."""
    if date:
        try:
            d_obj = datetime.strptime(date, "%Y-%m-%d")
            day_name = d_obj.strftime("%A")
        except Exception:
            day_name = date.capitalize()
    else:
        dt = get_now_kolkata()
        day_name = dt.strftime("%A")
        
    records = query_timetable(year, section, day_name)
    
    formatted_entries = []
    for r in records:
        room_name, block, floor = resolve_room_and_building(r.get("room"))
        formatted_entries.append({
            "start_time": r.get("start_time"),
            "end_time": r.get("end_time"),
            "subject_code": r.get("subject_code"),
            "class_type": r.get("class_type"),
            "room": room_name or r.get("section_default_room"),
            "block": block
        })
        
    return {
        "status": "success",
        "year": year,
        "section": section,
        "day": day_name,
        "total_classes": len(formatted_entries),
        "schedule": formatted_entries
    }

def get_class_at_time(year: int, section: str, date: Optional[str] = None, requested_time: Optional[str] = None) -> Dict[str, Any]:
    """Find what class is scheduled for a specific time."""
    if not requested_time:
        return {"status": "error", "message": "Please specify a requested_time (e.g. '11:00' or '14:30')."}
        
    if date:
        try:
            d_obj = datetime.strptime(date, "%Y-%m-%d")
            day_name = d_obj.strftime("%A")
        except Exception:
            day_name = date.capitalize()
    else:
        dt = get_now_kolkata()
        day_name = dt.strftime("%A")
        
    # Parse requested_time string
    try:
        if ":" in requested_time:
            parts = requested_time.strip().split(":")
            req_t = time(int(parts[0]), int(parts[1]))
        else:
            h = int(requested_time.strip())
            req_t = time(h, 0)
    except Exception:
        return {"status": "error", "message": f"Could not parse time '{requested_time}'."}
        
    records = query_timetable(year, section, day_name)
    matched_entry = None
    for entry in records:
        st = parse_time_str(entry["start_time"])
        et = parse_time_str(entry["end_time"])
        if st <= req_t < et:
            matched_entry = entry
            break
            
    if not matched_entry:
        return {
            "status": "no_class",
            "message": "No class is scheduled for that time according to the current timetable.",
            "requested_time": requested_time,
            "day": day_name
        }
        
    room_name, block, floor = resolve_room_and_building(matched_entry.get("room"))
    return {
        "status": "success",
        "matched_class": {
            "subject_code": matched_entry.get("subject_code"),
            "subject_name": matched_entry.get("subject_name"),
            "class_type": matched_entry.get("class_type"),
            "start_time": matched_entry.get("start_time"),
            "end_time": matched_entry.get("end_time"),
            "room": room_name or matched_entry.get("section_default_room"),
            "block": block
        }
    }

def get_class_location(year: int, section: str, target: str = "current", current_datetime: Optional[str] = None) -> Dict[str, Any]:
    """Retrieve room, building block, floor, navigation details, and Google Maps URL for current or next class."""
    if target == "next":
        class_info = get_next_class(year, section, current_datetime)
        cls_data = class_info.get("next_class")
    else:
        class_info = get_current_class(year, section, current_datetime)
        cls_data = class_info.get("current_class")
        
    if not cls_data:
        return {
            "status": "no_class_found",
            "message": f"No {target} class found to locate."
        }
        
    room_str = cls_data.get("room")
    room_name, block, floor = resolve_room_and_building(room_str)
    
    b_dest = f"{block or 'N Block'}, Vignan University, Vadlamudi, Andhra Pradesh 522213"
    gmaps_url = build_google_maps_url(
        origin="Main Gate, Vignan University, Vadlamudi, Andhra Pradesh 522213",
        destination=b_dest,
        travel_mode="walking",
        navigate=True
    )
    
    return {
        "status": "success",
        "target": target,
        "subject_code": cls_data.get("subject_code"),
        "room": room_name,
        "building": block or "N Block",
        "floor": floor or "Ground/Main Floor",
        "navigation_guidance": f"Head to {block or 'N Block'}, take the stairs/elevator to {floor or 'your designated floor'}, and proceed to Room {room_name}.",
        "google_maps_url": gmaps_url
    }


def get_first_class_on_day(year: int, section: str, date: Optional[str] = None) -> Dict[str, Any]:
    """Retrieve the first academic timetable entry on the requested day (today, tomorrow, or weekday)."""
    if date:
        d_lower = date.lower().strip()
        dt_now = get_now_kolkata()
        if d_lower == "today":
            day_name = dt_now.strftime("%A")
        elif d_lower == "tomorrow":
            day_name = (dt_now + timedelta(days=1)).strftime("%A")
        else:
            try:
                d_obj = datetime.strptime(date, "%Y-%m-%d")
                day_name = d_obj.strftime("%A")
            except Exception:
                day_name = date.capitalize()
    else:
        dt_now = get_now_kolkata()
        day_name = dt_now.strftime("%A")

    records = query_timetable(year, section, day_name)
    academic_records = [r for r in records if is_academic_class(r)]

    if not academic_records:
        return {
            "status": "no_classes_found",
            "message": f"No academic classes scheduled for {day_name}.",
            "day": day_name
        }

    first_entry = academic_records[0]
    room_name, block, floor = resolve_room_and_building(first_entry.get("room"))
    teacher = get_subject_faculty(first_entry.get("subject_code"))

    return {
        "status": "success",
        "day": day_name,
        "first_class": {
            "subject_code": first_entry.get("subject_code"),
            "subject_name": first_entry.get("subject_name"),
            "class_type": first_entry.get("class_type"),
            "start_time": first_entry.get("start_time"),
            "end_time": first_entry.get("end_time"),
            "room": room_name or first_entry.get("section_default_room"),
            "block": block,
            "floor": floor,
            "teacher": teacher
        }
    }


