from typing import List, Optional

from pydantic import BaseModel, Field


class FacilityOut(BaseModel):
    facility_id: str
    facility_name: str
    facility_type: str
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    baseline_value: Optional[float] = Field(default=None, ge=0)


class FacilityListResponse(BaseModel):
    facilities: List[FacilityOut]
    count: int
