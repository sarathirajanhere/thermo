"""
Event service — the single source of truth for events during the MVP.

Design choice (per the 10-hour constraint): a simple in-memory list,
seeded from a deterministic JSON file on startup, with writes flushed
back to that same JSON file. This means:
  - No database/PostGIS setup required.
  - Demo data is deterministic (same file every run).
  - Acknowledged status survives a backend restart, because we
    persist changes back to disk.
  - If the JSON file is ever missing/corrupted, we fall back to a
    tiny built-in dataset so the demo never breaks.
"""

import json
import os
from typing import Dict, List, Optional

from app.config import DEMO_EVENTS_FILE
from app.schemas.event import EventOut

_FALLBACK_EVENTS: List[Dict] = [
    {
        "event_id": "TG-FALLBACK-0001",
        "timestamp": "2026-09-07T00:00:00Z",
        "latitude": 12.3456,
        "longitude": 78.9012,
        "sensor": "VIIRS",
        "confidence": 0.75,
        "frp": 20.0,
        "source_class": "Potential Industrial Fire",
        "class_confidence": 0.7,
        "context_type": "Industrial Facility",
        "facility_id": "FAC-001",
        "facility_name": "Demo Chemical Plant",
        "baseline_value": 18.0,
        "current_value": 20.0,
        "anomaly_score": 0.4,
        "severity": "MODERATE",
        "status": "NEW",
        "evidence": ["Fallback demo event: primary data file was unavailable"],
    }
]

_events_store: Dict[str, EventOut] = {}


def _load_from_disk() -> List[Dict]:
    try:
        with open(DEMO_EVENTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return _FALLBACK_EVENTS


def _save_to_disk() -> None:
    """Persist current in-memory events back to the demo JSON file."""
    try:
        os.makedirs(os.path.dirname(DEMO_EVENTS_FILE), exist_ok=True)
        payload = [e.model_dump(mode="json") for e in _events_store.values()]
        with open(DEMO_EVENTS_FILE, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
    except OSError:
        # Non-fatal for the demo: in-memory state is still correct,
        # it just won't survive a restart if the disk write fails.
        pass


def load_events() -> None:
    """Call once at startup to seed the in-memory store."""
    raw_events = _load_from_disk()
    _events_store.clear()
    for raw in raw_events:
        try:
            event = EventOut(**raw)
            _events_store[event.event_id] = event
        except Exception as exc:  # noqa: BLE001
            print(f"[event_service] Skipping invalid demo event {raw.get('event_id')}: {exc}")


def get_all_events() -> List[EventOut]:
    return list(_events_store.values())


def get_event_by_id(event_id: str) -> Optional[EventOut]:
    return _events_store.get(event_id)


def upsert_event(event: EventOut) -> EventOut:
    """
    Insert a new event or overwrite an existing one with the same
    event_id. Used by ingestion and by Member 3 / Member 4's future
    write-back integrations.
    """
    _events_store[event.event_id] = event
    _save_to_disk()
    return event


def acknowledge_event(event_id: str) -> Optional[EventOut]:
    event = _events_store.get(event_id)
    if event is None:
        return None
    updated = event.model_copy(update={"status": "ACKNOWLEDGED"})
    _events_store[event_id] = updated
    _save_to_disk()
    return updated


def clear_events() -> None:
    """Mainly useful for tests."""
    _events_store.clear()
