from typing import List

from pydantic import BaseModel

from app.schemas.event import EventOut


class AlertListResponse(BaseModel):
    alerts: List[EventOut]
    count: int
