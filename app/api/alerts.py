from fastapi import APIRouter, Query

from app.schemas.alert import AlertListResponse
from app.services.alert_service import get_alerts

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("", response_model=AlertListResponse)
def list_alerts(
    min_severity: str = Query(
        default="MODERATE",
        description="Minimum severity to include: LOW, MODERATE, HIGH, or CRITICAL",
    )
):
    alerts = get_alerts(min_severity=min_severity)
    return {"alerts": alerts, "count": len(alerts)}
