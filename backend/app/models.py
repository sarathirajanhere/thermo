"""
Data models for ThermoGuard AI backend.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class ThermalFeatures(BaseModel):
    brightness_temperature: Optional[float] = None
    thermal_intensity: Optional[float] = None


class TemporalFeatures(BaseModel):
    observation_count: int = Field(default=0, ge=0)
    duration_minutes: float = Field(default=0.0, ge=0.0)
    persistence_score: float = Field(default=0.0, ge=0.0, le=1.0)


class SpatialContext(BaseModel):
    context_type: str = Field(default="Other")
    facility_id: Optional[str] = None
    facility_name: Optional[str] = None
    distance_to_facility: float = Field(default=0.0, ge=0.0)
    inside_facility: bool = Field(default=False)
    nearby_features: List[str] = Field(default_factory=list)


class HistoricalContext(BaseModel):
    baseline_value: Optional[float] = None
    current_value: Optional[float] = None
    historical_observation_count: int = Field(default=0, ge=0)


class ThermalEvent(BaseModel):
    event_id: str
    timestamp: datetime
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    sensor: str = Field(default="VIIRS")
    confidence: float = Field(..., ge=0.0, le=1.0)
    frp: float = Field(default=0.0, ge=0.0)  # Fire Radiative Power in MW
    thermal_features: ThermalFeatures = Field(default_factory=ThermalFeatures)
    temporal_features: TemporalFeatures = Field(default_factory=TemporalFeatures)
    spatial_context: SpatialContext = Field(default_factory=SpatialContext)
    historical_context: HistoricalContext = Field(default_factory=HistoricalContext)


# Response models
class ClassificationResult(BaseModel):
    label: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    evidence: List[str] = Field(default_factory=list)


class BaselineResult(BaseModel):
    status: str  # AVAILABLE, INSUFFICIENT_DATA, NO_DATA, ERROR
    expected_value: Optional[float] = None
    current_value: Optional[float] = None
    deviation: Optional[float] = None
    deviation_ratio: Optional[float] = None
    variability: Optional[float] = None
    sample_count: int = Field(default=0, ge=0)


class AnomalyResult(BaseModel):
    score: float = Field(..., ge=0.0, le=1.0)
    level: str  # LOW, MEDIUM, HIGH, UNKNOWN
    evidence: List[str] = Field(default_factory=list)
    deviation: Optional[float] = None
    deviation_ratio: Optional[float] = None
    baseline_value: Optional[float] = None
    current_value: Optional[float] = None


class PriorityResult(BaseModel):
    severity: str  # LOW, MODERATE, HIGH, CRITICAL
    score: float = Field(..., ge=0.0, le=1.0)
    evidence: List[str] = Field(default_factory=list)


class IntelligenceResponse(BaseModel):
    event_id: str
    timestamp: datetime
    classification: ClassificationResult
    baseline: BaselineResult
    anomaly: AnomalyResult
    priority: PriorityResult
    processing_time_ms: Optional[float] = None


# Demo data models
class DemoEvent(BaseModel):
    event_id: str
    description: str
    event_data: ThermalEvent
    expected_classification: str
    expected_priority: str