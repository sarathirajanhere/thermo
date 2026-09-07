from fastapi import APIRouter

from app.schemas.facility import FacilityListResponse
from app.services.facility_service import get_all_facilities

router = APIRouter(prefix="/facilities", tags=["facilities"])


@router.get("", response_model=FacilityListResponse)
def list_facilities():
    facilities = get_all_facilities()
    return {"facilities": facilities, "count": len(facilities)}
