"""
Small normalization helpers used by the ingestion service when loading
FIRMS-compatible or otherwise "raw" thermal records, which are often
messier than our internal event contract (e.g. lat/lon as strings,
confidence as "nominal"/"high"/percentages, missing fields).
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional


def normalize_coordinate(value: Any) -> float:
    """Coerce a coordinate that may arrive as a string or int into float."""
    try:
        return float(value)
    except (TypeError, ValueError):
        raise ValueError(f"Invalid coordinate value: {value!r}")


def normalize_timestamp(value: Any) -> str:
    """
    Normalize a timestamp into an ISO-8601 UTC string ending in 'Z'.
    Accepts already-ISO strings, or FIRMS-style 'YYYY-MM-DD' + separate
    'HHMM' fields pre-merged by the caller into one string.
    """
    if isinstance(value, datetime):
        dt = value
    elif isinstance(value, str):
        cleaned = value.replace("Z", "+00:00")
        try:
            dt = datetime.fromisoformat(cleaned)
        except ValueError:
            raise ValueError(f"Invalid timestamp value: {value!r}")
    else:
        raise ValueError(f"Invalid timestamp value: {value!r}")

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def normalize_confidence(value: Any) -> float:
    """
    FIRMS sometimes reports confidence as 'low'/'nominal'/'high' (VIIRS)
    or as a 0-100 integer (MODIS). Normalize everything to a 0-1 float.
    """
    if isinstance(value, str):
        mapping = {"low": 0.3, "nominal": 0.6, "high": 0.9}
        key = value.strip().lower()
        if key in mapping:
            return mapping[key]
        try:
            value = float(value)
        except ValueError:
            raise ValueError(f"Invalid confidence value: {value!r}")

    value = float(value)
    if value > 1:
        value = value / 100.0
    if not (0 <= value <= 1):
        raise ValueError(f"Confidence out of range after normalization: {value}")
    return value


def normalize_frp(value: Any) -> float:
    try:
        frp = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"Invalid FRP value: {value!r}")
    return max(frp, 0.0)


def safe_get(record: Dict[str, Any], *keys: str, default: Optional[Any] = None) -> Any:
    """Return the first present, non-None value among several possible key names."""
    for key in keys:
        if key in record and record[key] is not None:
            return record[key]
    return default
