"""Pydantic request models for the VIGNAN campus agent API."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., description="Student or user natural language query", min_length=1)
    conversation_id: Optional[str] = Field(None, description="Optional conversation session ID")
    history: Optional[List[Dict[str, Any]]] = Field(default_factory=list, description="Optional previous conversation context")
    user: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Optional authenticated user profile context (year, section, name, email)")


class FeedbackRequest(BaseModel):
    user_query: Optional[str] = Field(None, description="The user query that triggered the recommendation")
    tool_used: Optional[str] = Field(None, description="Tool name used by the agent")
    recommendation: Optional[str] = Field(None, description="The recommendation or answer provided")
    predicted_wait: Optional[int] = Field(None, description="Estimated wait time in minutes predicted by the system")
    actual_wait: Optional[int] = Field(None, description="Actual wait time in minutes experienced by the student")
    rating: int = Field(..., ge=1, le=5, description="Feedback rating between 1 and 5 stars")
    feedback_type: Optional[str] = Field(None, description="Category of feedback (e.g. accuracy, wait_time, general)")
    feedback_text: Optional[str] = Field(None, description="Detailed feedback remarks from the student")
