#!/usr/bin/env python3
"""
scripts/seed_demo.py

ThermoGuard AI / LandslideGuard - Deterministic Demo Seeding
Owner: Member 4 - Geospatial + Integration/QA Lead

What this does
---------------
1. Loads the golden-seed dataset (data/demo/seed_events.json).
2. Validates every event against the shared event data contract
   (required fields, types, allowed severity values).
3. Re-enriches each event's geospatial context via the point-in-polygon
   matcher, as a consistency check that the seed data and the live
   spatial-matching logic agree with each other.
4. Loads the validated events into wherever the demo needs them:
      - if a backend API is reachable, POST them there;
      - otherwise (offline, backend not started yet, hackathon wifi),
        fall back to writing a local `data/demo/seeded_events.json`
        snapshot that the frontend/backend can read directly.
   Either path is safe to re-run any number of times (idempotent) --
   this script must never be the reason a demo run fails.

Usage
-----
    python scripts/seed_demo.py
    python scripts/seed_demo.py --api-url http://localhost:8000/api/v1/ingestion/firms
    python scripts/seed_demo.py --no-enrich   # skip spatial re-validation
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any

logger = logging.getLogger("thermoguard.seed_demo")

REPO_ROOT = Path(__file__).resolve().parent.parent
SEED_FILE = REPO_ROOT / "data" / "demo" / "seed_events.json"
FACILITIES_FILE = REPO_ROOT / "geospatial" / "data" / "facilities.geojson"
OUTPUT_FILE = REPO_ROOT / "data" / "demo" / "seeded_events.json"

# Make the monorepo root importable so `geospatial.matching...` resolves
# regardless of the working directory this script is invoked from.
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

REQUIRED_FIELDS = {
    "event_id": str,
    "timestamp": str,
    "latitude": (int, float),
    "longitude": (int, float),
    "sensor": str,
    "confidence": (int, float),
    "frp": (int, float),
    "source_class": str,
    "class_confidence": (int, float),
    "context_type": str,
    "facility_id": (str, type(None)),
    "facility_name": (str, type(None)),
    "baseline_value": (int, float),
    "current_value": (int, float),
    "anomaly_score": (int, float),
    "severity": str,
    "status": str,
    "evidence": list,
}

ALLOWED_SEVERITY = {"LOW", "MODERATE", "HIGH", "CRITICAL"}


class SeedValidationError(Exception):
    """Raised when an event in the golden seed file violates the shared contract."""


def load_seed_file(path: Path = SEED_FILE) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Golden seed dataset not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def validate_event(event: dict[str, Any], scenario_id: str = "") -> list[str]:
    """Validate one event dict against the shared data contract.

    Returns a list of human-readable problems (empty list = valid).
    Never raises -- callers decide whether to treat problems as fatal.
    """
    problems: list[str] = []

    for field_name, expected_type in REQUIRED_FIELDS.items():
        if field_name not in event:
            problems.append(f"[{scenario_id}] missing required field '{field_name}'")
            continue
        if not isinstance(event[field_name], expected_type):
            problems.append(
                f"[{scenario_id}] field '{field_name}' has type "
                f"{type(event[field_name]).__name__}, expected {expected_type}"
            )

    if "severity" in event and event["severity"] not in ALLOWED_SEVERITY:
        problems.append(
            f"[{scenario_id}] severity '{event.get('severity')}' not in {sorted(ALLOWED_SEVERITY)}"
        )

    if "evidence" in event and isinstance(event["evidence"], list) and not event["evidence"]:
        problems.append(f"[{scenario_id}] evidence array is empty (must explain the result)")

    lat, lon = event.get("latitude"), event.get("longitude")
    if isinstance(lat, (int, float)) and not (-90 <= lat <= 90):
        problems.append(f"[{scenario_id}] latitude {lat} out of range")
    if isinstance(lon, (int, float)) and not (-180 <= lon <= 180):
        problems.append(f"[{scenario_id}] longitude {lon} out of range")

    return problems


def validate_all(scenarios: list[dict[str, Any]]) -> list[str]:
    all_problems: list[str] = []
    seen_ids: set[str] = set()

    for scenario in scenarios:
        scenario_id = scenario.get("scenario_id", "UNKNOWN")
        event = scenario.get("event", {})
        all_problems.extend(validate_event(event, scenario_id))

        event_id = event.get("event_id")
        if event_id in seen_ids:
            all_problems.append(f"[{scenario_id}] duplicate event_id '{event_id}'")
        seen_ids.add(event_id)

    return all_problems


def enrich_with_spatial_context(scenarios: list[dict[str, Any]]) -> list[str]:
    """Cross-check each event's stored facility_id/context_type against a
    fresh point-in-polygon match. This catches drift between the demo
    fixtures and the facilities layer (e.g. someone moved a polygon and
    forgot to update the seed data).

    Returns a list of warning strings -- mismatches are surfaced but are
    NOT treated as fatal, since the seed file is allowed to describe
    scenarios not present in the sample facilities layer (e.g. a wider
    deployment region).
    """
    warnings: list[str] = []
    try:
        from geospatial.matching.point_in_polygon import SpatialMatcher
    except ImportError as exc:
        warnings.append(f"Could not import spatial matcher, skipping enrichment check: {exc}")
        return warnings

    try:
        matcher = SpatialMatcher.from_file(FACILITIES_FILE)
    except Exception as exc:  # defensive: seeding must survive a bad facilities file
        warnings.append(f"Could not load facilities layer for enrichment check: {exc}")
        return warnings

    for scenario in scenarios:
        event = scenario.get("event", {})
        scenario_id = scenario.get("scenario_id", "UNKNOWN")
        lat, lon = event.get("latitude"), event.get("longitude")
        if lat is None or lon is None:
            continue

        result = matcher.match(lat, lon)
        expected_facility = event.get("facility_id")
        if expected_facility and result.facility_id != expected_facility:
            warnings.append(
                f"[{scenario_id}] spatial match returned facility_id="
                f"{result.facility_id!r}, seed file expects {expected_facility!r}"
            )

    return warnings


def load_into_backend(events: list[dict[str, Any]], api_url: str, timeout_s: float = 2.0) -> bool:
    """Best-effort POST of events to a live backend ingestion endpoint.

    Returns True on success, False on ANY failure (connection refused,
    timeout, non-2xx, backend not built yet, etc.) -- this function must
    never raise, because "backend isn't up yet" is an expected state
    during a hackathon build, not an error.
    """
    try:
        import requests  # local import: keep this an optional dependency
    except ImportError:
        logger.info("`requests` not installed; skipping live backend load.")
        return False

    ok = True
    for event in events:
        try:
            resp = requests.post(api_url, json=event, timeout=timeout_s)
            if resp.status_code >= 300:
                logger.warning("Backend rejected %s: HTTP %s", event.get("event_id"), resp.status_code)
                ok = False
        except requests.RequestException as exc:
            logger.info("Backend not reachable at %s (%s); will use local fallback.", api_url, exc)
            return False

    return ok


def write_local_snapshot(events: list[dict[str, Any]], path: Path = OUTPUT_FILE) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump({"seeded_at_scenario_count": len(events), "events": events}, f, indent=2)
    logger.info("Wrote %d seeded event(s) to %s", len(events), path)


def run(
    seed_path: Path = SEED_FILE,
    api_url: str | None = None,
    enrich: bool = True,
    fail_on_validation_error: bool = True,
) -> int:
    """Main entry point. Returns a process exit code (0 = success)."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    logger.info("Loading golden seed dataset from %s", seed_path)
    data = load_seed_file(seed_path)
    scenarios = data.get("scenarios", [])
    if not scenarios:
        logger.error("Seed file contains no scenarios.")
        return 1

    logger.info("Validating %d scenario(s) against the shared event contract...", len(scenarios))
    problems = validate_all(scenarios)
    if problems:
        for p in problems:
            logger.error("VALIDATION FAILED: %s", p)
        if fail_on_validation_error:
            return 1

    if enrich:
        logger.info("Cross-checking spatial context against facilities layer...")
        for warning in enrich_with_spatial_context(scenarios):
            logger.warning(warning)

    events = [s["event"] for s in scenarios]

    loaded_live = False
    if api_url:
        logger.info("Attempting to load events into live backend at %s", api_url)
        loaded_live = load_into_backend(events, api_url)

    if not loaded_live:
        logger.info("Using local fallback snapshot (no external API dependency).")
        write_local_snapshot(events)

    logger.info("Seeding complete: %d event(s) ready (baseline / critical / false-alarm).", len(events))
    return 0


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed deterministic ThermoGuard demo events.")
    parser.add_argument("--seed-file", type=Path, default=SEED_FILE)
    parser.add_argument(
        "--api-url",
        type=str,
        default=None,
        help="Backend ingestion endpoint, e.g. http://localhost:8000/api/v1/ingestion/firms. "
        "If omitted or unreachable, falls back to a local JSON snapshot.",
    )
    parser.add_argument("--no-enrich", action="store_true", help="Skip spatial context cross-check.")
    parser.add_argument(
        "--allow-invalid",
        action="store_true",
        help="Continue seeding even if some events fail contract validation (not recommended).",
    )
    return parser.parse_args(argv)


if __name__ == "__main__":
    args = _parse_args(sys.argv[1:])
    exit_code = run(
        seed_path=args.seed_file,
        api_url=args.api_url,
        enrich=not args.no_enrich,
        fail_on_validation_error=not args.allow_invalid,
    )
    sys.exit(exit_code)
