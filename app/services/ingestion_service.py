"""
Ingestion service — turns raw external/FIRMS-style records into
validated Event objects and stores them.

For the 10-hour MVP this supports local CSV/JSON files only. A live
NASA FIRMS API integration is intentionally out of scope: if it's
unavailable (no internet, API key issues, rate limits), the demo must
still work off the deterministic local dataset in event_service.
"""

import csv
import io
import json
from typing import Dict, List

from app.schemas.event import EventOut
from app.services.event_service import upsert_event
from app.utils.validation import (
    normalize_confidence,
    normalize_coordinate,
    normalize_frp,
    normalize_timestamp,
    safe_get,
)


def _raw_to_event_dict(raw: Dict) -> Dict:
    """
    Map a loosely-structured FIRMS-like record onto our internal event
    contract. Field names are matched flexibly since FIRMS CSV exports
    use short names like 'lat'/'lon'/'confidence'/'frp'/'acq_date'.
    """
    latitude = normalize_coordinate(safe_get(raw, "latitude", "lat"))
    longitude = normalize_coordinate(safe_get(raw, "longitude", "lon", "lng"))
    confidence = normalize_confidence(safe_get(raw, "confidence", default=0.5))
    frp = normalize_frp(safe_get(raw, "frp", "bright_ti4", default=0.0))

    timestamp_raw = safe_get(raw, "timestamp", "acq_datetime", "acq_date")
    timestamp = normalize_timestamp(timestamp_raw) if timestamp_raw else None
    if timestamp is None:
        raise ValueError("Record is missing a timestamp/acq_date field")

    event_id = safe_get(raw, "event_id")
    if not event_id:
        # Deterministic fallback ID so re-ingesting the same row doesn't
        # create duplicates: based on rounded coords + timestamp.
        event_id = f"TG-INGEST-{round(latitude, 4)}-{round(longitude, 4)}-{timestamp}"

    return {
        "event_id": str(event_id),
        "timestamp": timestamp,
        "latitude": latitude,
        "longitude": longitude,
        "sensor": safe_get(raw, "sensor", "instrument", default="OTHER"),
        "confidence": confidence,
        "frp": frp,
        "source_class": safe_get(raw, "source_class", default="Unclassified"),
        "class_confidence": safe_get(raw, "class_confidence", default=0.0),
        "context_type": safe_get(raw, "context_type", default="Unknown"),
        "facility_id": safe_get(raw, "facility_id"),
        "facility_name": safe_get(raw, "facility_name"),
        "baseline_value": safe_get(raw, "baseline_value"),
        "current_value": safe_get(raw, "current_value", default=frp),
        "anomaly_score": safe_get(raw, "anomaly_score", default=0.0),
        "severity": safe_get(raw, "severity", default="LOW"),
        "status": safe_get(raw, "status", default="NEW"),
        "evidence": safe_get(raw, "evidence", default=[]),
    }


def ingest_records(raw_records: List[Dict]) -> Dict[str, List]:
    """
    Ingest a list of raw dict records (already parsed from CSV/JSON).
    Returns a summary: {"ingested": [...event_ids], "errors": [...]}.
    Never raises — bad rows are collected as errors so one malformed
    row can't take down the whole ingestion run.
    """
    ingested: List[str] = []
    errors: List[Dict] = []

    for i, raw in enumerate(raw_records):
        try:
            event_dict = _raw_to_event_dict(raw)
            event = EventOut(**event_dict)
            upsert_event(event)
            ingested.append(event.event_id)
        except Exception as exc:  # noqa: BLE001
            errors.append({"row": i, "error": str(exc)})

    return {"ingested": ingested, "errors": errors}


def ingest_json_bytes(data: bytes) -> Dict[str, List]:
    records = json.loads(data.decode("utf-8"))
    if isinstance(records, dict):
        records = [records]
    return ingest_records(records)


def ingest_csv_bytes(data: bytes) -> Dict[str, List]:
    text = data.decode("utf-8")
    reader = csv.DictReader(io.StringIO(text))
    return ingest_records(list(reader))
