"""
Event schema — this is THE shared contract between:
  - Backend (this file)
  - Frontend (Member 1) — consumes this JSON shape
  - AI module (Member 3) — fills source_class / class_confidence /
    anomaly_score / severity
  - Geospatial module (Member 4) — fills context_type / facility_id /
    facility_name / evidence

Do NOT rename fields here without telling the whole team — every other
module is coded against these exact field names.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.common import ContextType, EventStatus, Sensor, Severity


class EventBase(BaseModel):
    event_id: str = Field(..., min_length=1, description="Unique event identifier, e.g. TG-IND-0247")
    timestamp: datetime = Field(..., description="UTC timestamp of the thermal detection")
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    sensor: Sensor = Field(default=Sensor.OTHER)
    confidence: float = Field(..., ge=0, le=1, description="Raw detection confidence (0-1)")
    frp: float = Field(..., ge=0, description="Fire Radiative Power (MW)")

    # AI classification fields (Member 3)
    source_class: str = Field(default="Unclassified")
    class_confidence: float = Field(default=0.0, ge=0, le=1)

    # Geospatial context fields (Member 4)
    context_type: ContextType = Field(default=ContextType.UNKNOWN)
    facility_id: Optional[str] = None
    facility_name: Optional[str] = None

    # Anomaly / baseline fields (Member 3)
    baseline_value: Optional[float] = Field(default=None, ge=0)
    current_value: Optional[float] = Field(default=None, ge=0)
    anomaly_score: float = Field(default=0.0, ge=0, le=1)

    # Priority / workflow fields
    severity: Severity = Field(default=Severity.LOW)
    status: EventStatus = Field(default=EventStatus.NEW)
    evidence: List[str] = Field(default_factory=list)

    @field_validator("timestamp", mode="before")
    @classmethod
    def parse_timestamp(cls, value):
        """Accept both 'Z'-suffixed and offset ISO timestamps."""
        if isinstance(value, str):
            return value.replace("Z", "+00:00")
        return value

    @field_validator("evidence", mode="before")
    @classmethod
    def default_evidence(cls, value):
        return value or []


class EventCreate(EventBase):
    """Used by the ingestion layer when loading raw/external records."""
    pass


class EventOut(EventBase):
    """What the API returns. Same shape as EventBase for the MVP."""

    model_config = ConfigDict(use_enum_values=True)


class EventListResponse(BaseModel):
    events: List[EventOut]
    count: int


class EventAcknowledgeRequest(BaseModel):
    note: Optional[str] = Field(default=None, description="Optional operator note")


class EventAcknowledgeResponse(BaseModel):
    event: EventOut
    message: str = "Event acknowledged"
