from typing import List

from app.schemas.event import EventOut
from app.services.event_service import get_all_events

_SEVERITY_RANK = {
    "CRITICAL": 0,
    "HIGH": 1,
    "MODERATE": 2,
    "LOW": 3,
}


def get_alerts(min_severity: str = "MODERATE") -> List[EventOut]:
    """
    Return events at or above `min_severity`, ordered by severity
    (CRITICAL first) and then by anomaly_score (highest first).
    """
    threshold = _SEVERITY_RANK.get(min_severity.upper(), _SEVERITY_RANK["MODERATE"])

    events = [
        e for e in get_all_events()
        if _SEVERITY_RANK.get(str(e.severity).upper(), 99) <= threshold
    ]
    events.sort(
        key=lambda e: (
            _SEVERITY_RANK.get(str(e.severity).upper(), 99),
            -e.anomaly_score,
        )
    )
    return events
