import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

DEMO_EVENTS_FILE = os.path.join(DATA_DIR, "demo_events.json")
DEMO_FACILITIES_FILE = os.path.join(DATA_DIR, "demo_facilities.json")

# --- CORS -------------------------------------------------------------
# Development: allow the typical Vite/CRA dev server ports from localhost.
# PRODUCTION NOTE: replace this list with your deployed frontend's exact
# origin(s), e.g. ["https://thermoguard.yourdomain.com"], and remove the
# wildcard/localhost entries before deploying.
CORS_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

APP_NAME = "ThermoGuard AI Backend"
APP_VERSION = "0.1.0"
