import json
from typing import Dict, List, Optional

from app.config import DEMO_FACILITIES_FILE
from app.schemas.facility import FacilityOut

_FALLBACK_FACILITIES: List[Dict] = [
    {
        "facility_id": "FAC-001",
        "facility_name": "Demo Chemical Plant",
        "facility_type": "Industrial Facility",
        "latitude": 12.3456,
        "longitude": 78.9012,
        "baseline_value": 18.0,
    }
]

_facilities_store: Dict[str, FacilityOut] = {}


def _load_from_disk() -> List[Dict]:
    try:
        with open(DEMO_FACILITIES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return _FALLBACK_FACILITIES


def load_facilities() -> None:
    raw_facilities = _load_from_disk()
    _facilities_store.clear()
    for raw in raw_facilities:
        try:
            facility = FacilityOut(**raw)
            _facilities_store[facility.facility_id] = facility
        except Exception as exc:  # noqa: BLE001
            print(f"[facility_service] Skipping invalid facility {raw.get('facility_id')}: {exc}")


def get_all_facilities() -> List[FacilityOut]:
    return list(_facilities_store.values())


def get_facility_by_id(facility_id: str) -> Optional[FacilityOut]:
    return _facilities_store.get(facility_id)


def upsert_facility(facility: FacilityOut) -> FacilityOut:
    """Used by Member 4's geospatial module to register/update facilities."""
    _facilities_store[facility.facility_id] = facility
    return facility
