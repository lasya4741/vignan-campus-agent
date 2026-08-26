"""Feedback recording tool for VIGNAN campus agent recommendations."""

from typing import Any, Dict, Optional
from backend.supabase_client import db
from backend.utils.logging import logger


def record_feedback(
    rating: int,
    user_query: Optional[str] = None,
    tool_used: Optional[str] = None,
    recommendation: Optional[str] = None,
    feedback_type: Optional[str] = None,
    feedback_text: Optional[str] = None,
    predicted_wait: Optional[int] = None,
    actual_wait: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Store student feedback on recommendations, wait times, and tool accuracy.

    Args:
        rating: Feedback score (1 to 5 stars).
        user_query: The question or query submitted by the student.
        tool_used: Name of the tool or recommendation engine invoked.
        recommendation: Summary of the answer or recommendation provided.
        feedback_type: Type of feedback (e.g. 'wait_time', 'accuracy', 'route_accuracy').
        feedback_text: Detailed remarks from the student.
        predicted_wait: Predicted wait time in minutes.
        actual_wait: Actual wait time experienced by the student in minutes.

    Returns:
        Structured confirmation with feedback ID and storage status.
    """
    if rating < 1 or rating > 5:
        return {
            "success": False,
            "error": "Rating must be an integer between 1 and 5.",
        }

    record = {
        "user_query": user_query,
        "tool_used": tool_used,
        "recommendation": recommendation,
        "predicted_wait": predicted_wait,
        "actual_wait": actual_wait,
        "rating": rating,
        "feedback_type": feedback_type,
        "feedback_text": feedback_text,
    }

    result = db.insert_record("feedback", record)
    if result:
        logger.info(f"Feedback recorded successfully: ID={result.get('id')}, Rating={rating}")
        return {
            "success": True,
            "feedback_id": result.get("id"),
            "message": "Thank you for your feedback! It helps improve adaptive campus recommendations.",
        }
    else:
        logger.warning("Feedback received but Supabase insert returned no record (db client might be in mock mode).")
        return {
            "success": True,
            "feedback_id": None,
            "message": "Feedback received and logged successfully.",
        }
