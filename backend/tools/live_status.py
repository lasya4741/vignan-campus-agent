"""Live status monitoring and adaptive service recommendation engine for VIGNAN campus."""

from typing import Any, Dict, List, Optional
from backend.supabase_client import db
from backend.utils.normalization import normalize_text
from backend.tools.verification import format_source_provenance, is_live_status_expired


def get_live_status(service_id: str) -> Dict[str, Any]:
    """
    Retrieve dynamic real-time status, queue length, and wait time for a campus service.

    Args:
        service_id: UUID of the service to check.

    Returns:
        Structured live status details, including expiration verification.
    """
    statuses = db.query_table(
        "live_status",
        filters={"service_id": service_id},
        select_cols="*, services(name, category, location_id, locations(name, block, room))",
        limit=5
    )

    if not statuses:
        return {
            "service_id": service_id,
            "status": "unknown",
            "queue_length": None,
            "estimated_wait_minutes": None,
            "is_expired": True,
            "message": "No dynamic live status recorded for this service.",
        }

    # Pick the most recent record
    statuses.sort(key=lambda s: s.get("recorded_at") or "", reverse=True)
    latest = statuses[0]
    is_expired = is_live_status_expired(latest)

    svc_info = latest.get("services") or {}
    loc_info = svc_info.get("locations") or {}

    return {
        "service_id": service_id,
        "service_name": svc_info.get("name"),
        "category": svc_info.get("category"),
        "location": loc_info.get("name") or (f"{loc_info.get('block')} {loc_info.get('room')}" if loc_info.get('block') else None),
        "status": "unknown" if is_expired else latest.get("status"),
        "raw_status": latest.get("status"),
        "queue_length": latest.get("queue_length"),
        "estimated_wait_minutes": latest.get("estimated_wait_minutes"),
        "reported_by": latest.get("reported_by"),
        "recorded_at": latest.get("recorded_at"),
        "expires_at": latest.get("expires_at"),
        "is_expired": is_expired,
        "confidence": latest.get("confidence", "high"),
        "message": "Live status expired — please verify on-site." if is_expired else f"Status: {latest.get('status')} (est. wait: {latest.get('estimated_wait_minutes', 0)} mins).",
    }


def find_best_service(category: str, required_service: Optional[str] = None) -> Dict[str, Any]:
    """
    Adaptive decision engine: evaluates candidate campus services in real-time,
    compares queue lengths and wait times, and recommends the best option.

    Example:
        User: 'I need to print my project. Which Xerox should I use?'
        Engine compares available print shops, checks live queues, selects lowest wait time.

    Args:
        category: Service category ('xerox', 'printing', 'canteen', 'stationery', 'medical', 'library').
        required_service: Specific required feature (e.g., 'color printing', 'spiral binding', 'tea').

    Returns:
        Recommendation decision, reasoning, estimated wait, location, and alternatives.
    """
    norm_cat = normalize_text(category)
    norm_req = normalize_text(required_service) if required_service else None

    # Step 1: Find matching services in category
    services = db.query_table(
        "services",
        select_cols="*, locations(id, name, block, floor, room, description)"
    )

    candidate_services = []
    for s in services:
        s_cat = normalize_text(s.get("category"))
        s_offered = s.get("services_offered") or []
        offered_str = " ".join([normalize_text(str(x)) for x in s_offered]) if isinstance(s_offered, list) else normalize_text(str(s_offered))

        if norm_cat in s_cat or norm_cat in offered_str:
            if norm_req and norm_req not in offered_str and norm_req not in normalize_text(s.get("description", "")) and norm_req not in normalize_text(s.get("name")):
                continue
            candidate_services.append(s)

    if not candidate_services:
        return {
            "recommended_service": None,
            "decision_reason": f"No verified campus service found offering '{category}'.",
            "candidates_evaluated": 0,
            "options": [],
        }

    # Step 2: Fetch and rank live statuses for all candidates
    evaluated_options = []
    for s in candidate_services:
        live = get_live_status(s["id"])
        loc = s.get("locations") or {}

        status_val = live["status"]  # will be 'unknown' if expired
        raw_status = live["raw_status"] if not live["is_expired"] else "unknown"
        queue = live["queue_length"] if (live["queue_length"] is not None and not live["is_expired"]) else 999
        wait = live["estimated_wait_minutes"] if (live["estimated_wait_minutes"] is not None and not live["is_expired"]) else 999

        # Score computation (lower score is better)
        penalty = 0
        if raw_status == "closed":
            penalty += 1000
        elif raw_status == "full":
            penalty += 500
        elif raw_status == "busy":
            penalty += 50
        elif raw_status == "available":
            penalty += 0
        else:  # unknown / expired
            penalty += 100

        score = (wait * 2) + queue + penalty

        evaluated_options.append({
            "service_id": s["id"],
            "name": s["name"],
            "category": s["category"],
            "location_name": loc.get("name"),
            "block": loc.get("block"),
            "room": loc.get("room"),
            "status": raw_status,
            "is_expired": live["is_expired"],
            "queue_length": live["queue_length"] if not live["is_expired"] else None,
            "estimated_wait_minutes": live["estimated_wait_minutes"] if not live["is_expired"] else None,
            "score": score,
            "services_offered": s.get("services_offered"),
            "provenance": format_source_provenance(s),
        })

    evaluated_options.sort(key=lambda o: o["score"])
    best = evaluated_options[0]

    # Build clear, transparent explanation for why this service was selected
    if best["status"] == "available":
        reason = f"Recommended '{best['name']}' at {best['location_name'] or best['block']} because it is currently available with an estimated wait time of {best['estimated_wait_minutes'] or 0} minutes (queue length: {best['queue_length'] or 0})."
    elif best["status"] == "busy":
        reason = f"Recommended '{best['name']}' as it currently has the shortest queue among operating locations (est. wait: {best['estimated_wait_minutes']} mins)."
    elif best["status"] == "unknown":
        reason = f"Selected '{best['name']}' at {best['location_name'] or best['block']}. Note: Live queue sensor data is currently unrecorded/expired for this location."
    else:
        reason = f"Selected '{best['name']}' as the primary verified location for {category}."

    return {
        "recommended_service": {
            "service_id": best["service_id"],
            "name": best["name"],
            "location": best["location_name"] or f"{best['block']} {best['room']}",
            "block": best["block"],
            "room": best["room"],
            "status": best["status"],
            "estimated_wait_minutes": best["estimated_wait_minutes"],
            "queue_length": best["queue_length"],
        },
        "decision_reason": reason,
        "candidates_evaluated": len(evaluated_options),
        "options": evaluated_options,
    }
