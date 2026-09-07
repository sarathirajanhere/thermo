"""
Main FastAPI application for ThermoGuard AI backend.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging
from typing import List, Dict, Any

# Import our AI intelligence pipeline
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from ai.pipelines.intelligence_pipeline import analyze_thermal_event, get_event_intelligence

# Import existing backend modules if they exist
try:
    from .api import events, facilities, alerts
except ImportError:
    # Create placeholder routers if they don't exist yet
    from fastapi import APIRouter
    events = APIRouter()
    facilities = APIRouter()
    alerts = APIRouter()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="ThermoGuard AI API",
    description="AI-powered thermal event analysis for industrial fire detection",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(events.router, prefix="/api/v1/events", tags=["events"])
app.include_router(facilities.router, prefix="/api/v1/facilities", tags=["facilities"])
app.include_router(alerts.router, prefix="/api/v1/alerts", tags=["alerts"])

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "ThermoGuard AI API",
        "version": "0.1.0",
        "status": "operational"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

@app.post("/api/v1/analyze")
async def analyze_event(event: Dict[str, Any]):
    """
    Analyze a thermal event using the AI pipeline.

    Args:
        event: Normalized thermal event dictionary

    Returns:
        Intelligence analysis result
    """
    try:
        logger.info(f"Analyzing event: {event.get('event_id', 'unknown')}")
        result = analyze_thermal_event(event)
        return result
    except Exception as e:
        logger.error(f"Error analyzing event: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/events/{event_id}")
async def get_event_intelligence_endpoint(event_id: str):
    """
    Get intelligence analysis for a specific event by ID.
    In a full implementation, this would fetch the event from database first.

    Args:
        event_id: Event identifier

    Returns:
        Intelligence analysis result
    """
    # For MVP, we'll return a mock event or error
    # In reality, this would fetch from database and then analyze
    raise HTTPException(
        status_code=501,
        detail="Event retrieval not implemented - use POST /api/v1/analyze with event data"
    )

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)