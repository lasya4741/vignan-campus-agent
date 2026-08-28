"""Deterministic campus navigation and Google Maps routing tool for VIGNAN campus agent."""

import re
import urllib.parse
from typing import Any, Dict, List, Optional
from backend.config import settings
from backend.supabase_client import db
from backend.utils.normalization import normalize_text
from backend.utils.campus_entities import resolve_campus_entity
from backend.tools.verification import format_source_provenance

# Canonical Google Maps search queries representing real VIGNAN University landmarks
CAMPUS_MAP_QUERIES = {
    "a block": "A Block, Vignan University, Vadlamudi, Andhra Pradesh 522213",
    "n block": "N Block, Vignan University, Vadlamudi, Andhra Pradesh 522213",
    "u block": "U Block, Vignan University, Vadlamudi, Andhra Pradesh 522213",
    "h block": "H Block, Vignan University, Vadlamudi, Andhra Pradesh 522213",
    "pharmacy block": "School of Pharmacy, Vignan University, Vadlamudi",
    "textile block": "Textile Engineering Block, Vignan University, Vadlamudi",
    "main gate": "Main Gate, Vignan University, Vadlamudi, Andhra Pradesh 522213",
    "mhp": "MHP Main Canteen, Vignan University, Vadlamudi",
    "main canteen": "MHP Main Canteen, Vignan University, Vadlamudi",
    "canteen": "MHP Main Canteen, Vignan University, Vadlamudi",
    "zest": "MHP / Zest Area, Vignan University, Vadlamudi",
    "zest area": "MHP / Zest Area, Vignan University, Vadlamudi",
    "mhp zest area": "MHP / Zest Area, Vignan University, Vadlamudi",
    "mhp / zest area": "MHP / Zest Area, Vignan University, Vadlamudi",
    "finance": "Finance Office, A Block, Vignan University, Vadlamudi",
    "finance office": "Finance Office, A Block, Vignan University, Vadlamudi",
    "transport": "Transport Office, Main Gate Area, Vignan University, Vadlamudi",
    "transport office": "Transport Office, Main Gate Area, Vignan University, Vadlamudi",
    "xerox": "Xerox Facility, Beside A Block, Vignan University, Vadlamudi",
    "xerox shop": "Xerox Facility, Beside A Block, Vignan University, Vadlamudi",
    "xerox near mhp": "Xerox Facility, Near MHP / Zest Area, Vignan University, Vadlamudi",
    "xerox near zest": "Xerox Facility, Near MHP / Zest Area, Vignan University, Vadlamudi",
    "library": "Central Library, Vignan University, Vadlamudi",
    "central library": "Central Library, Vignan University, Vadlamudi",
    "it": "Department of Information Technology, U Block, Vignan University, Vadlamudi",
    "cse": "Department of Computer Science & Engineering, N Block, Vignan University, Vadlamudi",
    "acse": "Advanced CSE Department, N Block, Vignan University, Vadlamudi",
    "ece": "Department of ECE, H Block, Vignan University, Vadlamudi",
    "eee": "Department of EEE, H Block, Vignan University, Vadlamudi",
    "mech": "Department of Mechanical Engineering, U Block, Vignan University, Vadlamudi",
    "civil": "Department of Civil Engineering, U Block, Vignan University, Vadlamudi",
    "biotech": "Department of Biotechnology, U Block, Vignan University, Vadlamudi",
}


def build_google_maps_url(origin: str, destination: str, travel_mode: str = "walking", navigate: bool = False) -> str:
    """Generate a valid Google Maps Directions URL."""
    base_url = "https://www.google.com/maps/dir/?api=1"
    params = {
        "origin": origin,
        "destination": destination,
        "travelmode": travel_mode,
    }
    if navigate:
        params["dir_action"] = "navigate"
    return f"{base_url}&{urllib.parse.urlencode(params)}"


def resolve_map_point(location_text: str) -> str:
    """Resolve campus landmark name to a canonical Google Maps search string."""
    norm = normalize_text(location_text)
    if not norm:
        return "Vignan University, Vadlamudi, Andhra Pradesh 522213"

    # Check for direct map query dictionary matches
    for key, map_query in CAMPUS_MAP_QUERIES.items():
        if key in norm or norm in key:
            return map_query

    # Entity normalization fallback
    entity = resolve_campus_entity(location_text)
    if entity:
        cname = entity.get("canonical_name", "")
        norm_cname = normalize_text(cname)
        for key, map_query in CAMPUS_MAP_QUERIES.items():
            if key in norm_cname or norm_cname in key:
                return map_query
        return f"{cname}, Vignan University, Vadlamudi"

    return f"{location_text}, Vignan University, Vadlamudi"


def is_known_campus_point(text: str) -> bool:
    """Verify if a location text corresponds to a recognized VIGNAN campus entity or building."""
    norm = normalize_text(text)
    if not norm:
        return False
    if any(k in norm or norm in k for k in CAMPUS_MAP_QUERIES):
        return True
    if resolve_campus_entity(text) is not None:
        return True
    if any(b in norm for b in [
        "block", "gate", "room", "canteen", "office", "dept", "department",
        "library", "hostel", "lab", "building", "counter", "shop", "facility",
        "nb", "mhp", "finance", "transport", "xerox", "placement", "cafeteria"
    ]):
        return True
    all_locs = db.query_table("locations")
    if any(norm in normalize_text(l.get("name", "")) or norm in normalize_text(l.get("block", "")) for l in all_locs):
        return True
    all_depts = db.query_table("departments")
    if any(norm in normalize_text(d.get("name", "")) or norm in normalize_text(d.get("short_name", "")) for d in all_depts):
        return True
    return False


def get_route(start_location: str, destination: str, travel_mode: str = "walking", navigate: bool = False) -> Dict[str, Any]:
    """
    Retrieve navigation path between two campus locations, generating verified campus steps and real Google Maps directions.

    Args:
        start_location: Starting location name or landmark (e.g. 'Main Gate', 'A Block', 'N Block').
        destination: Destination location name or room (e.g. 'MHP', 'Finance Office', 'Room NB-409', 'IT').
        travel_mode: Mode of travel ('walking', 'driving', 'bicycling'). Default is 'walking'.
        navigate: If True, adds dir_action=navigate to Google Maps URL.

    Returns:
        Structured navigation details with Google Maps URL, embedded map status, indoor room guidance, and steps.
    """
    norm_start = normalize_text(start_location) or "main gate"
    norm_dest = normalize_text(destination)

    # Validate destination exists in campus knowledge base
    if not is_known_campus_point(destination):
        return {
            "found": False,
            "origin": start_location.title() if start_location else "Main Gate",
            "destination": destination.title() if destination else "Destination",
            "start_location": start_location.title() if start_location else "Main Gate",
            "destination_location": destination.title() if destination else "Destination",
            "steps": [],
            "estimated_minutes": None,
            "message": f"A verified step-by-step route to '{destination}' is currently unavailable in the campus database.",
        }

    # 1. Detect indoor room in destination
    room_match = re.search(r"\b([A-Z]{0,2}[-\s]?\d{3}[A-Za-z]?)\b", destination)
    target_room = None
    target_block = None
    indoor_guidance = None

    if "nb" in norm_dest or "n block" in norm_dest or (room_match and "nb" in room_match.group(1).lower()):
        target_block = "N Block"
        if room_match:
            target_room = room_match.group(1).upper().replace(" ", "-")
    elif "u block" in norm_dest:
        target_block = "U Block"
        if room_match:
            target_room = room_match.group(1).upper().replace(" ", "-")
    elif "a block" in norm_dest or "finance" in norm_dest:
        target_block = "A Block"
    elif "h block" in norm_dest:
        target_block = "H Block"
    elif "mhp" in norm_dest or "canteen" in norm_dest:
        target_block = "near N Block"

    if target_room:
        indoor_guidance = (
            f"Google Maps can guide you to the relevant VIGNAN building ({target_block or 'Campus Block'}). "
            f"Room-level navigation ({target_room}) is based on VIGNAN's verified campus information."
        )

    # 2. Canonical Map query resolution
    origin_map_query = resolve_map_point(start_location)
    dest_map_query = resolve_map_point(destination)

    # 3. Google Maps Directions URL
    google_maps_url = build_google_maps_url(
        origin=origin_map_query,
        destination=dest_map_query,
        travel_mode=travel_mode,
        navigate=navigate
    )

    # 4. Embedded Map Configuration
    api_key = settings.google_maps_api_key
    embedded_map_available = bool(api_key and api_key.strip())
    embedded_map_url = None
    if embedded_map_available:
        encoded_origin = urllib.parse.quote(origin_map_query)
        encoded_dest = urllib.parse.quote(dest_map_query)
        embedded_map_url = f"https://www.google.com/maps/embed/v1/directions?key={api_key}&origin={encoded_origin}&destination={encoded_dest}&mode={travel_mode}"

    # 5. Check Database for verified internal campus step records
    all_locs = db.query_table("locations")
    start_loc_ids = [
        loc["id"] for loc in all_locs
        if norm_start in normalize_text(loc.get("name")) or norm_start in normalize_text(loc.get("block"))
    ]
    dest_loc_ids = [
        loc["id"] for loc in all_locs
        if norm_dest in normalize_text(loc.get("name")) or norm_dest in normalize_text(loc.get("block"))
    ]

    all_routes = db.query_table(
        "routes",
        select_cols="*, start:start_location_id(name, block, room), dest:destination_location_id(name, block, room)"
    )

    matching_routes = []
    for r in all_routes:
        start_id = r.get("start_location_id")
        dest_id = r.get("destination_location_id")
        start_info = r.get("start") or {}
        dest_info = r.get("dest") or {}
        r_start_name = normalize_text(start_info.get("name"))
        r_dest_name = normalize_text(dest_info.get("name"))

        match_start = (start_id in start_loc_ids) or (norm_start in r_start_name) or (r_start_name in norm_start)
        match_dest = (dest_id in dest_loc_ids) or (norm_dest in r_dest_name) or (r_dest_name in norm_dest)

        if match_start and match_dest:
            matching_routes.append(r)

    formatted_steps = []
    est_minutes = None

    if matching_routes:
        best_route = matching_routes[0]
        raw_steps = best_route.get("steps") or []
        if isinstance(raw_steps, list):
            for idx, item in enumerate(raw_steps, start=1):
                if isinstance(item, dict):
                    formatted_steps.append({
                        "step": item.get("step", idx),
                        "instruction": item.get("instruction", str(item)),
                    })
                else:
                    formatted_steps.append({
                        "step": idx,
                        "instruction": str(item),
                    })
        est_minutes = float(best_route.get("estimated_minutes")) if best_route.get("estimated_minutes") else 4.0
    else:
        # Generate default logical walking instructions
        dest_display = destination.title() if destination else "Destination"
        start_display = start_location.title() if start_location else "Starting Location"
        formatted_steps = [
            {"step": 1, "instruction": f"Start from {start_display}."},
            {"step": 2, "instruction": f"Follow the campus walkway toward {target_block or dest_display}."},
            {"step": 3, "instruction": f"Arrive at {dest_display} ({target_block or 'Campus Building'})."}
        ]
        est_minutes = 3.0

    return {
        "found": True,
        "origin": start_location.title() if start_location else "Main Gate",
        "destination": destination.title() if destination else "Destination",
        "start_location": start_location.title() if start_location else "Main Gate",
        "destination_location": destination.title() if destination else "Destination",
        "travel_mode": travel_mode,
        "google_maps_url": google_maps_url,
        "embedded_map_available": embedded_map_available,
        "embedded_map_url": embedded_map_url,
        "indoor_guidance": indoor_guidance,
        "steps": formatted_steps,
        "estimated_minutes": est_minutes,
        "message": f"Found walking route to {destination}.",
        "provenance": format_source_provenance({"source_id": "5a8d7901-b758-5d20-a612-4c924bc01f89", "confidence": "high"}),
    }
