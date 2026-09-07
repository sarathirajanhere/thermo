from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.config import APP_NAME, APP_VERSION, CORS_ORIGINS
from app.services.event_service import load_events
from app.services.facility_service import load_facilities

app = FastAPI(title=APP_NAME, version=APP_VERSION)

# --- CORS (development configuration — see app/config.py for prod notes)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    """
    Seed the in-memory demo data store. This is what guarantees:
      - the API works with zero external dependencies (no internet,
        no NASA FIRMS key needed), and
      - the same deterministic demo data is present every time the
        backend restarts.
    """
    load_events()
    load_facilities()


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Return clean, predictable 422 errors instead of raw tracebacks."""
    return JSONResponse(
        status_code=422,
        content={"detail": "Invalid request data", "errors": exc.errors()},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Last-resort handler so the demo never dies with a raw 500 stack trace."""
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"},
    )


app.include_router(api_router)


@app.get("/")
def root():
    return {
        "service": APP_NAME,
        "version": APP_VERSION,
        "docs": "/docs",
        "endpoints": [
            "/health",
            "/events",
            "/events/{event_id}",
            "/facilities",
            "/alerts",
            "/events/{event_id}/acknowledge",
            "/ingestion/upload",
        ],
    }
