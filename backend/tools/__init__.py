"""Tool layer for VIGNAN campus agent, exposing all database-backed lookup functions."""

from backend.tools.faculty import search_faculty
from backend.tools.departments import search_department
from backend.tools.subjects import search_subject
from backend.tools.counsellors import search_counsellor
from backend.tools.offices import search_office
from backend.tools.academic_support import search_responsibility
from backend.tools.services import search_service
from backend.tools.locations import get_location
from backend.tools.live_status import get_live_status, find_best_service
from backend.tools.navigation import get_route
from backend.tools.feedback import record_feedback

# Registry of callable tools for the Gemini Coordinator Agent
ALL_TOOLS = {
    "search_faculty": search_faculty,
    "search_department": search_department,
    "search_subject": search_subject,
    "search_counsellor": search_counsellor,
    "search_office": search_office,
    "search_responsibility": search_responsibility,
    "search_service": search_service,
    "get_location": get_location,
    "get_live_status": get_live_status,
    "find_best_service": find_best_service,
    "get_route": get_route,
    "record_feedback": record_feedback,
}

TOOL_CALLABLE_LIST = [
    search_faculty,
    search_department,
    search_subject,
    search_counsellor,
    search_office,
    search_responsibility,
    search_service,
    get_location,
    get_live_status,
    find_best_service,
    get_route,
    record_feedback,
]

__all__ = [
    "search_faculty",
    "search_department",
    "search_subject",
    "search_counsellor",
    "search_office",
    "search_responsibility",
    "search_service",
    "get_location",
    "get_live_status",
    "find_best_service",
    "get_route",
    "record_feedback",
    "ALL_TOOLS",
    "TOOL_CALLABLE_LIST",
]
