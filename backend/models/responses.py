"""Pydantic response models for the VIGNAN campus agent API."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ToolCallRecord(BaseModel):
    tool_name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)
    result: Optional[Any] = None


class SourceMetadata(BaseModel):
    source_id: Optional[str] = None
    source_type: Optional[str] = None
    source_name: Optional[str] = None
    document_name: Optional[str] = None
    confidence: Optional[str] = "high"
    last_verified: Optional[str] = None


class LocationDetail(BaseModel):
    id: Optional[str] = None
    name: str
    location_type: Optional[str] = None
    block: Optional[str] = None
    floor: Optional[str] = None
    room: Optional[str] = None
    description: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class RouteStep(BaseModel):
    step: int
    instruction: str


class RouteDetail(BaseModel):
    origin: Optional[str] = None
    destination: Optional[str] = None
    start_location: Optional[str] = None
    destination_location: Optional[str] = None
    travel_mode: str = "walking"
    google_maps_url: Optional[str] = None
    embedded_map_available: bool = False
    embedded_map_url: Optional[str] = None
    indoor_guidance: Optional[str] = None
    steps: List[RouteStep] = Field(default_factory=list)
    estimated_minutes: Optional[float] = None


class LiveStatusDetail(BaseModel):
    service_id: str
    service_name: Optional[str] = None
    status: str
    queue_length: int = 0
    estimated_wait_minutes: Optional[int] = None
    is_expired: bool = False
    recorded_at: Optional[str] = None


class ChatResponse(BaseModel):
    answer: str = Field(..., description="The verified natural language answer from Coordinator Agent")
    tool_used: List[str] = Field(default_factory=list, description="List of tools invoked during query execution")
    tool_calls: List[ToolCallRecord] = Field(default_factory=list, description="Structured details of each tool invocation")
    sources: List[SourceMetadata] = Field(default_factory=list, description="Source provenance backing the answer")
    confidence: str = Field(default="high", description="Overall confidence level (high, medium, low, needs_verification)")
    location: Optional[LocationDetail] = Field(None, description="Structured location details if query is spatial")
    route: Optional[RouteDetail] = Field(None, description="Deterministic navigation path if route was requested")
    live_status: Optional[LiveStatusDetail] = Field(None, description="Dynamic live queue/wait time state if queried")
    requires_clarification: bool = Field(default=False, description="Flag indicating if the agent needs more user input")
    session_state: Optional[Dict[str, Any]] = Field(None, description="Updated session state dictionary tracking pending intents and active context")


class FeedbackResponse(BaseModel):
    success: bool
    feedback_id: Optional[str] = None
    message: str


class HealthResponse(BaseModel):
    status: str = "ok"
    supabase: str
    gemini_model: str
    gemini_configured: bool
    version: str = "1.0.0"
