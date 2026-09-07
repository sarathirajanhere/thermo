"""
Event API endpoints for ThermoGuard AI.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
import logging
from datetime import datetime

from ..models import ThermalEvent, IntelligenceResponse
from ...ai.pipelines.intelligence_pipeline import analyze_thermal_event

logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory storage for demo events (in production, this would be a database)
demo_events_store: dict = {}
next_event_id = 1


@router.get("/", response_model=List[dict])
async def get_events(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    severity: Optional[str] = None,
    context_type: Optional[str] = None
):
    """
    Get list of thermal events with optional filtering.
    Returns basic event data for map display.
    """
    # For MVP, return demo events or empty list
    # In production, this would query database with filters
    events = list(demo_events_store.values())

    # Apply filters
    if severity:
        # Would filter by analyzed priority severity
        pass
    if context_type:
        # Would filter by spatial context
        pass

    # Apply pagination
    paginated_events = events[offset:offset + limit]

    # Return simplified event data for map/list view
    return [
        {
            "event_id": event.event_id,
            "timestamp": event.timestamp.isoformat(),
            "latitude": event.latitude,
            "longitude": event.longitude,
            "frp": event.frp,
            "confidence": event.confidence,
            "context_type": event.spatial_context.context_type,
            "inside_facility": event.spatial_context.inside_facility
        }
        for event in paginated_events
    ]


@router.get("/{event_id}", response_model=IntelligenceResponse)
async def get_event_intelligence(event_id: str):
    """
    Get full intelligence analysis for a specific event.
    """
    if event_id not in demo_events_store:
        raise HTTPException(status_code=404, detail="Event not found")

    event = demo_events_store[event_id]

    try:
        # Analyze the event using our AI pipeline
        intelligence_result = analyze_thermal_event(event.dict())
        return intelligence_result
    except Exception as e:
        logger.error(f"Error analyzing event {event_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=dict)
async def create_event(event: ThermalEvent):
    """
    Create a new thermal event (for demo/testing).
    """
    global next_event_id

    # Use provided event_id or generate one
    event_id = event.event_id or f"TG-{next_event_id:06d}"
    if not event.event_id:
        next_event_id += 1

    # Store the event
    demo_events_store[event_id] = event

    logger.info(f"Created event {event_id}")

    return {
        "event_id": event_id,
        "message": "Event created successfully",
        "timestamp": event.timestamp.isoformat()
    }


@router.post("/{event_id}/acknowledge")
async def acknowledge_event(event_id: str):
    """
    Acknowledge an event (change its status).
    """
    if event_id not in demo_events_store:
        raise HTTPException(status_code=404, detail="Event not found")

    # In a full implementation, we'd update the event status in database
    logger.info(f"Event {event_id} acknowledged")

    return {
        "event_id": event_id,
        "message": "Event acknowledged",
        "status": "ACKNOWLEDGED"
    }


@router.delete("/{event_id}")
async def delete_event(event_id: str):
    """
    Delete an event (for demo cleanup).
    """
    if event_id not in demo_events_store:
        raise HTTPException(status_code=404, detail="Event not found")

    del demo_events_store[event_id]
    logger.info(f"Deleted event {event_id}")

    return {"message": "Event deleted successfully"}


# Initialize some demo events on startup
def initialize_demo_events():
    """Create demo events for testing."""
    global next_event_id

    # Demo event 1: Routine gas flare (should be LOW/MODERATE priority)
    routine_flare = ThermalEvent(
        event_id="TG-DEMO-001",
        timestamp=datetime.now(),
        latitude=12.3456,
        longitude=78.9012,
        sensor="VIIRS",
        confidence=0.92,
        frp=18.5,
        thermal_features={
            "brightness_temperature": 320.0,
            "thermal_intensity": 18.5
        },
        temporal_features={
            "observation_count": 4,
            "duration_minutes": 25.0,
            "persistence_score": 0.6
        },
        spatial_context={
            "context_type": "Industrial Facility",
            "facility_id": "FAC-001",
            "facility_name": "Demo Chemical Plant",
            "distance_to_facility": 0.0,
            "inside_facility": True,
            "nearby_features": ["Storage Tanks", "Pipeline", "Processing Unit"]
        },
        historical_context={
            "baseline_value": 17.0,
            "current_value": 18.5,
            "historical_observation_count": 25
        }
    )

    # Demo event 2: Potential industrial fire (should be CRITICAL priority)
    industrial_fire = ThermalEvent(
        event_id="TG-DEMO-002",
        timestamp=datetime.now(),
        latitude=12.3458,
        longitude=78.9015,
        sensor="VIIRS",
        confidence=0.94,
        frp=45.0,
        thermal_features={
            "brightness_temperature": 345.0,
            "thermal_intensity": 45.0
        },
        temporal_features={
            "observation_count": 6,
            "duration_minutes": 50.0,
            "persistence_score": 0.85
        },
        spatial_context={
            "context_type": "Industrial Facility",
            "facility_id": "FAC-002",
            "facility_name": "Refinery Complex",
            "distance_to_facility": 0.0,
            "inside_facility": True,
            "nearby_features": ["Storage Tanks", "Processing Unit", "Pipeline", "Flare Stack"]
        },
        historical_context={
            "baseline_value": 16.0,
            "current_value": 45.0,
            "historical_observation_count": 30
        }
    )

    # Demo event 3: Forest fire (should be Forest Fire classification, lower priority)
    forest_fire = ThermalEvent(
        event_id="TG-DEMO-003",
        timestamp=datetime.now(),
        latitude=12.5000,
        longitude=79.0000,
        sensor="VIIRS",
        confidence=0.88,
        frp=32.0,
        thermal_features={
            "brightness_temperature": 335.0,
            "thermal_intensity": 32.0
        },
        temporal_features={
            "observation_count": 3,
            "duration_minutes": 40.0,
            "persistence_score": 0.5
        },
        spatial_context={
            "context_type": "Forest",
            "facility_id": None,
            "facility_name": None,
            "distance_to_facility": 15.2,
            "inside_facility": False,
            "nearby_features": ["Tree Cover", "Vegetation"]
        },
        historical_context={
            "baseline_value": 0.5,
            "current_value": 32.0,
            "historical_observation_count": 2
        }
    )

    # Store demo events
    demo_events_store["TG-DEMO-001"] = routine_flare
    demo_events_store["TG-DEMO-002"] = industrial_fire
    demo_events_store["TG-DEMO-003"] = forest_fire

    next_event_id = 4
    logger.info("Initialized 3 demo events")


# Initialize demo events when module is loaded
initialize_demo_events()