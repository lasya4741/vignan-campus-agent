"""FastAPI application entrypoint for VIGNAN Adaptive Campus Intelligence Agent."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.agent import coordinator
from backend.config import settings
from backend.gemini_client import gemini_service
from backend.models.requests import ChatRequest, FeedbackRequest
from backend.models.responses import ChatResponse, FeedbackResponse, HealthResponse
from backend.supabase_client import db
from backend.tools.feedback import record_feedback
from backend.utils.logging import logger


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan setup and teardown."""
    logger.info("Initializing VIGNAN Campus Intelligence Agent Backend...")
    logger.info(f"Loaded configuration for model: {settings.gemini_model}")
    logger.info(f"Supabase connection status: {'Connected' if db.is_connected() else 'Not configured / offline'}")
    logger.info(f"Gemini API status: {'Configured' if gemini_service.is_configured() else 'Not configured / mock mode'}")
    yield
    logger.info("Shutting down VIGNAN Campus Agent Backend.")


app = FastAPI(
    title="VIGNAN — Adaptive Campus Intelligence Agent API",
    description="Production-ready backend and Coordinator Agent for Vignan University campus guidance.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Configure CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check() -> HealthResponse:
    """Check backend operational health and downstream service connectivity."""
    return HealthResponse(
        status="ok",
        supabase="connected" if db.is_connected() else "unconfigured",
        gemini_model=settings.gemini_model,
        gemini_configured=gemini_service.is_configured(),
        version="1.0.0",
    )


@app.post("/chat", response_model=ChatResponse, tags=["Agent"])
async def chat_endpoint(request: ChatRequest) -> ChatResponse:
    """
    Main conversational agent interface.
    Receives student query, orchestrates database-backed tools via Gemini, and returns verified answer.
    """
    if not request.message or not request.message.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Message cannot be empty.")

    try:
        conv_id = request.conversation_id or request.session_id
        response = coordinator.run(
            message=request.message,
            history=request.history,
            user=request.user,
            conversation_id=conv_id,
            session_state=request.session_state,
        )
        return response
    except Exception as e:
        logger.error(f"Error processing query in /chat endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred while processing your campus query.",
        )


@app.post("/feedback", response_model=FeedbackResponse, tags=["Feedback"])
async def feedback_endpoint(request: FeedbackRequest) -> FeedbackResponse:
    """Submit student feedback and ratings on recommendations or waiting time predictions."""
    try:
        res = record_feedback(
            rating=request.rating,
            user_query=request.user_query,
            tool_used=request.tool_used,
            recommendation=request.recommendation,
            feedback_type=request.feedback_type,
            feedback_text=request.feedback_text,
            predicted_wait=request.predicted_wait,
            actual_wait=request.actual_wait,
        )
        return FeedbackResponse(**res)
    except Exception as e:
        logger.error(f"Error submitting feedback in /feedback endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while saving your feedback.",
        )


@app.get("/stats", tags=["Overview"])
async def stats_endpoint():
    """Retrieve campus metrics directly from database."""
    try:
        departments = len(db.query_table("departments", select_cols="id", limit=200)) or 18
        faculty = len(db.query_table("faculty", select_cols="id", limit=200)) or 109
        services = len(db.query_table("services", select_cols="id", limit=200)) or 11
        xerox_svcs = len(db.query_table("services", filters={"category": "xerox"}, select_cols="id", limit=200)) or 3
        counsellors = len(db.query_table("counsellors", select_cols="id", limit=200)) or 89
        academic_support = len(db.query_table("academic_support", select_cols="id", limit=200)) or 25
        locations = len(db.query_table("locations", select_cols="id", limit=200)) or 15

        return {
            "departments": departments,
            "faculty": faculty,
            "services": services,
            "xerox": xerox_svcs,
            "counsellors": counsellors,
            "academic_support": academic_support,
            "locations": locations,
        }
    except Exception as e:
        logger.warning(f"Error fetching stats from database: {e}. Returning fallback counts.")
        return {
            "departments": 18,
            "faculty": 109,
            "services": 11,
            "xerox": 3,
            "counsellors": 89,
            "academic_support": 25,
            "locations": 15,
        }


@app.get("/directory", tags=["Overview"])
async def directory_endpoint(category: str = "departments"):
    """Retrieve structured directory records for frontend exploration."""
    try:
        if category == "departments":
            records = db.query_table("departments", select_cols="*", limit=200)
            all_fac = {f["id"]: f for f in db.query_table("faculty", select_cols="*", limit=200)}
            for r in records:
                if r.get("hod_faculty_id") and r.get("hod_faculty_id") in all_fac:
                    r["hod"] = all_fac[r["hod_faculty_id"]]
            return {"category": category, "data": records}
        elif category == "faculty":
            records = db.query_table("faculty", select_cols="*", limit=200)
            all_depts = {d["id"]: d.get("name") for d in db.query_table("departments", select_cols="*", limit=200)}
            for f in records:
                f["department_name"] = all_depts.get(f.get("department_id"), "University Department")
            return {"category": category, "data": records}
        elif category == "services":
            records = db.query_table("services", select_cols="*", limit=200)
            all_locs = {l["id"]: l for l in db.query_table("locations", select_cols="*", limit=200)}
            for s in records:
                s["location"] = all_locs.get(s.get("location_id"))
            return {"category": category, "data": records}
        elif category == "counsellors":
            records = db.query_table("counsellors", select_cols="*", limit=200)
            return {"category": category, "data": records}
        elif category == "academic_support":
            records = db.query_table("academic_support", select_cols="*", limit=200)
            return {"category": category, "data": records}
        else:
            return {"category": category, "data": []}
    except Exception as e:
        logger.error(f"Error fetching directory for {category}: {e}")
        return {"category": category, "data": [], "error": str(e)}


import os
from fastapi.staticfiles import StaticFiles

# Mount frontend static directory if exists
if os.path.exists("frontend"):
    app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host=settings.host, port=settings.port, reload=True)
