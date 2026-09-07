from fastapi import APIRouter, HTTPException

from app.schemas.event import (
    EventAcknowledgeRequest,
    EventAcknowledgeResponse,
    EventListResponse,
    EventOut,
)
from app.services.event_service import (
    acknowledge_event,
    get_all_events,
    get_event_by_id,
)

router = APIRouter(prefix="/events", tags=["events"])


@router.get("", response_model=EventListResponse)
def list_events():
    events = get_all_events()
    return {"events": events, "count": len(events)}


@router.get("/{event_id}", response_model=EventOut)
def get_event(event_id: str):
    event = get_event_by_id(event_id)
    if event is None:
        raise HTTPException(status_code=404, detail=f"Event '{event_id}' not found")
    return event


@router.post("/{event_id}/acknowledge", response_model=EventAcknowledgeResponse)
def acknowledge(event_id: str, body: EventAcknowledgeRequest = EventAcknowledgeRequest()):
    updated = acknowledge_event(event_id)
    if updated is None:
        raise HTTPException(status_code=404, detail=f"Event '{event_id}' not found")
    return {"event": updated, "message": "Event acknowledged"}
