"""Verification layer and provenance resolution for VIGNAN campus data."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from backend.config import settings

SOURCE_PRIORITY = {
    "official_website": 1,
    "official_document": 2,
    "department_verified": 3,
    "campus_verified": 4,
    "student_reported": 5,
}

CONFIDENCE_RANKS = {
    "high": 3,
    "medium": 2,
    "low": 1,
    "needs_verification": 0,
}


def parse_timestamp(ts: Any) -> Optional[datetime]:
    """Safely parse various datetime formats into UTC datetime."""
    if not ts:
        return None
    if isinstance(ts, datetime):
        return ts if ts.tzinfo else ts.replace(tzinfo=timezone.utc)
    try:
        dt = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except Exception:
        return None


def is_live_status_expired(record: Optional[Dict[str, Any]], max_age_minutes: int = 45) -> bool:
    """
    Check if a dynamic live_status record is expired.
    Evaluates explicit `expires_at` timestamp or checks age since `recorded_at`.
    """
    if not record or not isinstance(record, dict):
        return True

    now = datetime.now(timezone.utc)

    # Check explicit expiration if present
    expires_at = parse_timestamp(record.get("expires_at"))
    if expires_at:
        return now > expires_at

    # Check recorded_at age fallback
    recorded_at = parse_timestamp(record.get("recorded_at"))
    if recorded_at:
        age_minutes = (now - recorded_at).total_seconds() / 60.0
        return age_minutes > max_age_minutes

    return False


def format_source_provenance(record: Dict[str, Any], source_record: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Format structured provenance metadata for any returned campus record."""
    source_id = record.get("source_id")
    confidence = record.get("confidence", "high")
    last_verified = record.get("last_verified")

    source_type = None
    source_name = None
    document_name = None

    if source_record:
        source_type = source_record.get("source_type")
        source_name = source_record.get("source_name")
        document_name = source_record.get("document_name")

    return {
        "source_id": str(source_id) if source_id else None,
        "source_type": source_type,
        "source_name": source_name,
        "document_name": document_name,
        "confidence": confidence,
        "last_verified": str(last_verified) if last_verified else None,
    }


def compare_source_quality(record_a: Dict[str, Any], record_b: Dict[str, Any]) -> int:
    """
    Compare two records for source precedence.
    Returns:
       1 if record_a is preferred,
      -1 if record_b is preferred,
       0 if tied.
    Takes into account recency and source authority.
    """
    # Compare confidence first
    conf_a = CONFIDENCE_RANKS.get(record_a.get("confidence", "low"), 1)
    conf_b = CONFIDENCE_RANKS.get(record_b.get("confidence", "low"), 1)
    if conf_a != conf_b:
        return 1 if conf_a > conf_b else -1

    # Compare recency (newer timestamp preferred)
    ts_a = parse_timestamp(record_a.get("last_verified") or record_a.get("updated_at"))
    ts_b = parse_timestamp(record_b.get("last_verified") or record_b.get("updated_at"))
    if ts_a and ts_b:
        if (ts_a - ts_b).total_seconds() > 86400 * 30:  # More than 30 days newer
            return 1
        elif (ts_b - ts_a).total_seconds() > 86400 * 30:
            return -1

    return 0
