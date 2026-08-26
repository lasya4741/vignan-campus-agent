"""Test fixtures and mock database layer for VIGNAN campus backend."""

from datetime import datetime, timezone, timedelta
import pytest
from unittest.mock import patch, MagicMock

# Sample mock campus data for unit and integration testing
MOCK_SOURCES = [
    {
        "id": "src-001",
        "source_type": "official_document",
        "source_name": "Vignan Student Handbook 2025-2026",
        "document_name": "handbook_25_26.pdf",
        "confidence": "high",
        "last_verified": "2026-08-01T00:00:00Z",
    },
    {
        "id": "src-002",
        "source_type": "department_verified",
        "source_name": "CSE Department Notice Board",
        "confidence": "high",
        "last_verified": "2026-08-15T00:00:00Z",
    }
]

MOCK_DEPARTMENTS = [
    {
        "id": "dept-cse",
        "name": "Computer Science and Engineering",
        "short_name": "CSE",
        "description": "Department of CSE",
        "block": "U Block",
        "floor_information": "3rd & 4th Floor",
        "hod_faculty_id": "fac-001",
        "source_id": "src-001",
        "confidence": "high",
        "last_verified": "2026-08-01T00:00:00Z",
        "faculty": {
            "full_name": "Dr. K. Ramesh",
            "designation": "Professor & HOD",
            "room": "U-301",
            "email": "hod_cse@vignan.ac.in",
            "phone": "0863-2344700",
        }
    },
    {
        "id": "dept-it",
        "name": "Information Technology",
        "short_name": "IT",
        "description": "Department of Information Technology",
        "block": "A Block",
        "floor_information": "2nd Floor",
        "hod_faculty_id": "fac-002",
        "source_id": "src-001",
        "confidence": "high",
        "last_verified": "2026-08-01T00:00:00Z",
        "faculty": {
            "full_name": "Dr. S. Priya",
            "designation": "Professor & HOD",
            "room": "A-205",
            "email": "hod_it@vignan.ac.in",
            "phone": "0863-2344701",
        }
    }
]

MOCK_FACULTY = [
    {
        "id": "fac-001",
        "full_name": "Dr. K. Ramesh",
        "designation": "Professor & HOD",
        "department_id": "dept-cse",
        "email": "ramesh_k@vignan.ac.in",
        "phone": "+91 9848012345",
        "room": "301",
        "block": "U Block",
        "floor": "3rd Floor",
        "profile_url": "https://vignan.ac.in/faculty/ramesh",
        "source_id": "src-001",
        "confidence": "high",
        "last_verified": "2026-08-01T00:00:00Z",
        "departments": {"name": "Computer Science and Engineering", "short_name": "CSE"},
    },
    {
        "id": "fac-002",
        "full_name": "Dr. S. Priya",
        "designation": "Associate Professor",
        "department_id": "dept-cse",
        "email": "priya_s@vignan.ac.in",
        "phone": "+91 9848012346",
        "room": "409",
        "block": "U Block",
        "floor": "4th Floor",
        "profile_url": "https://vignan.ac.in/faculty/priya",
        "source_id": "src-001",
        "confidence": "high",
        "last_verified": "2026-08-01T00:00:00Z",
        "departments": {"name": "Computer Science and Engineering", "short_name": "CSE"},
    }
]

MOCK_SUBJECTS = [
    {
        "id": "subj-dbms",
        "name": "Database Management Systems",
        "code": "CS204",
        "department_id": "dept-cse",
        "source_id": "src-001",
        "confidence": "high",
        "last_verified": "2026-08-01T00:00:00Z",
        "departments": {"name": "Computer Science and Engineering", "short_name": "CSE"},
    }
]

MOCK_FACULTY_SUBJECTS = [
    {
        "faculty_id": "fac-002",
        "subject_id": "subj-dbms",
        "source_id": "src-001",
        "confidence": "high",
    }
]

MOCK_COUNSELLORS = [
    {
        "id": "couns-001",
        "academic_year": "2025-2026",
        "year": 2,
        "section": "A",
        "counsellor_name": "Dr. S. Priya",
        "faculty_id": "fac-002",
        "phone": "+91 9848012346",
        "room": "409",
        "registration_range_start": "241FA04001",
        "registration_range_end": "241FA04030",
        "registration_range_text": "241FA04001 to 241FA04030",
        "source_id": "src-002",
        "confidence": "high",
        "last_verified": "2026-08-15T00:00:00Z",
        "faculty": {
            "full_name": "Dr. S. Priya",
            "designation": "Associate Professor",
            "room": "409",
            "block": "U Block",
            "floor": "4th Floor",
            "phone": "+91 9848012346",
            "email": "priya_s@vignan.ac.in",
        }
    }
]

MOCK_OFFICES = [
    {
        "id": "off-001",
        "name": "Administrative Office",
        "purpose": "Admissions, fees, document verification",
        "room": "GF-01",
        "block": "Admin Block",
        "floor": "Ground Floor",
        "phone": "0863-2344710",
        "email": "admin@vignan.ac.in",
        "description": "Main administrative office for student administration",
        "source_id": "src-001",
        "confidence": "high",
        "last_verified": "2026-08-01T00:00:00Z",
    }
]

MOCK_ACADEMIC_SUPPORT = [
    {
        "id": "supp-001",
        "role_name": "Training & Placement Dean",
        "person_name": "Prof. T. Venkatesh",
        "faculty_id": "fac-001",
        "responsibilities": "Campus placement drives, company registrations, mock interviews",
        "office_id": "off-001",
        "room": "TP-101",
        "phone": "+91 9848099999",
        "email": "placements@vignan.ac.in",
        "source_id": "src-001",
        "confidence": "high",
        "last_verified": "2026-08-01T00:00:00Z",
        "faculty": {
            "full_name": "Prof. T. Venkatesh",
            "room": "TP-101",
            "block": "Placement Block",
            "phone": "+91 9848099999",
            "email": "placements@vignan.ac.in",
        },
        "offices": {"name": "Placement Cell", "room": "TP-101", "block": "Placement Block"},
    }
]

MOCK_LOCATIONS = [
    {
        "id": "loc-gate",
        "name": "Main Gate",
        "location_type": "gate",
        "block": "Campus Entrance",
        "description": "Main vehicular and pedestrian campus entrance",
        "source_id": "src-001",
        "confidence": "high",
    },
    {
        "id": "loc-u-block",
        "name": "U Block",
        "location_type": "building",
        "block": "U Block",
        "description": "Academic building for CSE & Dean Offices",
        "source_id": "src-001",
        "confidence": "high",
    },
    {
        "id": "loc-409",
        "name": "Room 409",
        "location_type": "room",
        "block": "U Block",
        "floor": "4th Floor",
        "room": "409",
        "description": "Faculty cubicle & Counselling Room",
        "source_id": "src-001",
        "confidence": "high",
    }
]

MOCK_SERVICES = [
    {
        "id": "svc-xerox-main",
        "name": "Main Campus Xerox & Stationery",
        "category": "xerox",
        "description": "Photocopying, spiral binding, color printing",
        "location_id": "loc-u-block",
        "services_offered": ["xerox", "color printing", "spiral binding", "stationery"],
        "source_id": "src-001",
        "confidence": "high",
        "locations": {
            "id": "loc-u-block",
            "name": "U Block Ground Floor",
            "block": "U Block",
            "floor": "Ground Floor",
            "room": "G-05",
        }
    },
    {
        "id": "svc-xerox-library",
        "name": "Library Digital Print Corner",
        "category": "xerox",
        "description": "Document printing and scanning",
        "location_id": "loc-gate",
        "services_offered": ["xerox", "printing", "scanning"],
        "source_id": "src-001",
        "confidence": "high",
        "locations": {
            "id": "loc-gate",
            "name": "Central Library 1st Floor",
            "block": "Library Block",
            "floor": "1st Floor",
            "room": "L-102",
        }
    }
]

now_str = datetime.now(timezone.utc).isoformat()
future_str = (datetime.now(timezone.utc) + timedelta(minutes=30)).isoformat()

MOCK_LIVE_STATUS = [
    {
        "id": "live-001",
        "service_id": "svc-xerox-main",
        "status": "available",
        "queue_length": 2,
        "estimated_wait_minutes": 4,
        "reported_by": "station_operator",
        "confidence": "high",
        "recorded_at": now_str,
        "expires_at": future_str,
        "services": {
            "name": "Main Campus Xerox & Stationery",
            "category": "xerox",
            "locations": {"name": "U Block Ground Floor", "block": "U Block", "room": "G-05"},
        }
    },
    {
        "id": "live-002",
        "service_id": "svc-xerox-library",
        "status": "busy",
        "queue_length": 10,
        "estimated_wait_minutes": 25,
        "reported_by": "station_operator",
        "confidence": "high",
        "recorded_at": now_str,
        "expires_at": future_str,
        "services": {
            "name": "Library Digital Print Corner",
            "category": "xerox",
            "locations": {"name": "Central Library", "block": "Library Block", "room": "L-102"},
        }
    }
]

MOCK_ROUTES = [
    {
        "id": "route-001",
        "start_location_id": "loc-gate",
        "destination_location_id": "loc-u-block",
        "steps": [
            {"step": 1, "instruction": "Enter through Main Gate."},
            {"step": 2, "instruction": "Walk straight along the central road for 80 meters."},
            {"step": 3, "instruction": "U Block will be on your left side."}
        ],
        "estimated_minutes": 2.5,
        "source_id": "src-001",
        "confidence": "high",
        "start": {"name": "Main Gate", "block": "Entrance", "room": None},
        "dest": {"name": "U Block", "block": "U Block", "room": None},
    }
]


import json
import os

EXTRACTED_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "database", "extracted")


def _get_table_data(table_name: str):
    json_path = os.path.join(EXTRACTED_DIR, f"{table_name}.json")
    extracted = []
    if os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                extracted = json.load(f)
        except Exception:
            extracted = []

    mock_map = {
        "sources": MOCK_SOURCES,
        "departments": MOCK_DEPARTMENTS,
        "faculty": MOCK_FACULTY,
        "subjects": MOCK_SUBJECTS,
        "faculty_subjects": MOCK_FACULTY_SUBJECTS,
        "counsellors": MOCK_COUNSELLORS,
        "offices": MOCK_OFFICES,
        "academic_support": MOCK_ACADEMIC_SUPPORT,
        "locations": MOCK_LOCATIONS,
        "services": MOCK_SERVICES,
        "live_status": MOCK_LIVE_STATUS,
        "routes": MOCK_ROUTES,
        "feedback": [],
    }

    if extracted:
        return extracted
    return mock_map.get(table_name, [])


def mock_query_table(table_name: str, select_cols: str = "*", filters: dict = None, limit: int = 1000):
    """Dispatch mock table responses."""
    data = _get_table_data(table_name)
    if filters:
        filtered = []
        for row in data:
            match = True
            for k, v in filters.items():
                if row.get(k) != v:
                    match = False
                    break
            if match:
                filtered.append(row)
        return filtered[:limit]
    return data[:limit]


@pytest.fixture(autouse=True)
def mock_supabase_db(monkeypatch):
    """Automatically patch SupabaseService with mock database data for testing."""
    from backend.supabase_client import db
    monkeypatch.setattr(db, "query_table", mock_query_table)
    monkeypatch.setattr(db, "insert_record", lambda table, record: {"id": "mock-insert-id", **record})
    monkeypatch.setattr(db, "is_connected", lambda: True)
