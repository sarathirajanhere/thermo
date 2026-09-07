from fastapi import APIRouter

from app.config import APP_NAME, APP_VERSION

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check():
    return {"status": "ok", "service": APP_NAME, "version": APP_VERSION}
