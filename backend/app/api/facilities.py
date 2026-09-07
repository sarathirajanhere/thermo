"""
Facility API endpoints for ThermoGuard AI.
"""

from fastapi import APIRouter, HTTPException
from typing import List, Optional
import logging

from ..models import ThermalEvent  # Reuse for facility data structure

logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory storage for demo facilities
demo_facilities_store: dict = {}


@router.get("/", response_model=List[dict])
async def get_facilities(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    facility_type: Optional[str] = None
):
    """
    Get list of industrial facilities.
    """
    facilities = list(demo_facilities_store.values())

    # Apply filters
    if facility_type:
        facilities = [f for f in facilities if f.get('type') == facility_type]

    # Apply pagination
    paginated_facilities = facilities[offset:offset + limit]

    return [
        {
            "facility_id": fac.facility_id,
            "facility_name": fac.facility_name,
            "facility_type": fac.facility_type,
            "latitude": fac.latitude,
            "longitude": fac.longitude,
            "active": fac.active
        }
        for fac in paginated_facilities
    ]


@router.get("/{facility_id}")
async def get_facility(facility_id: str):
    """
    Get specific facility information.
    """
    if facility_id not in demo_facilities_store:
        raise HTTPException(status_code=404, detail="Facility not found")

    return demo_facilities_store[facility_id]


@router.post("/", response_model=dict)
async def create_facility(facility: dict):
    """
    Create a new facility (for demo/testing).
    """
    facility_id = facility.get('facility_id') or f"FAC-{len(demo_facilities_store) + 1:03d}"
    facility['facility_id'] = facility_id

    demo_facilities_store[facility_id] = facility
    logger.info(f"Created facility {facility_id}")

    return {
        "facility_id": facility_id,
        "message": "Facility created successfully"
    }


# Initialize some demo facilities
def initialize_demo_facilities():
    """Create demo facilities for testing."""

    facilities_data = [
        {
            "facility_id": "FAC-001",
            "facility_name": "Demo Chemical Plant",
            "facility_type": "Chemical Plant",
            "latitude": 12.3456,
            "longitude": 78.9012,
            "active": True,
            "baseline_frp": 17.0,
            "typical_activities": ["chemical processing", "storage", "flaring"]
        },
        {
            "facility_id": "FAC-002",
            "facility_name": "Refinery Complex",
            "facility_type": "Oil Refinery",
            "latitude": 12.3458,
            "longitude": 78.9015,
            "active": True,
            "baseline_frp": 16.0,
            "typical_activities": ["refining", "storage", "flaring", "processing"]
        },
        {
            "facility_id": "FAC-003",
            "facility_name": "Power Generation Station",
            "facility_type": "Power Plant",
            "latitude": 12.4000,
            "longitude": 78.9500,
            "active": True,
            "baseline_frp": 12.0,
            "typical_activities": ["power generation", "cooling", "transmission"]
        }
    ]

    for facility in facilities_data:
        demo_facilities_store[facility["facility_id"]] = facility

    logger.info(f"Initialized {len(facilities_data)} demo facilities")


# Initialize demo facilities when module is loaded
initialize_demo_facilities()