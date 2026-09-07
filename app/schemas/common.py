"""
Shared enums and constants used across schemas.
Keeping these centralized avoids typos like "Critical" vs "CRITICAL"
which would otherwise break the frontend/AI/geospatial contract.
"""

from enum import Enum


class Severity(str, Enum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class EventStatus(str, Enum):
    NEW = "NEW"
    INVESTIGATING = "INVESTIGATING"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    CONFIRMED = "CONFIRMED"
    FALSE_ALARM = "FALSE_ALARM"
    RESOLVED = "RESOLVED"


class Sensor(str, Enum):
    VIIRS = "VIIRS"
    MODIS = "MODIS"
    OTHER = "OTHER"


class ContextType(str, Enum):
    INDUSTRIAL_FACILITY = "Industrial Facility"
    NON_INDUSTRIAL = "Non-Industrial"
    UNKNOWN = "Unknown"
