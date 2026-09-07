"""
tests/integration/test_event_pipeline.py

ThermoGuard AI / LandslideGuard - Integration / QA Suite
Owner: Member 4 - Geospatial + Integration/QA Lead

Scope
-----
These tests validate the CONTRACT boundaries between workstreams, not
the internals of any one module:

  1. Geospatial: incoming coordinates correctly associate with spatial
     zones (point-in-polygon + nearest-neighbor fallback), and degrade
     safely when there is no nearby context.
  2. Data contract: every event (golden seed AND ad-hoc) satisfies the
     shared schema all four members agreed on.
  3. Severity/priority: anomaly thresholds map to the right severity
     band, using the same rule the AI/priority module is expected to
     apply, so Frontend/Backend/AI integration doesn't silently drift.
  4. Resilience: the pipeline never raises when external context
     (facility layer, OSM data) is missing or a coordinate is malformed
     -- it degrades to a safe default instead.

Run with:
    pytest tests/integration/test_event_pipeline.py -v
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from geospatial.matching.point_in_polygon import (  # noqa: E402
    SpatialMatcher,
    SpatialMatchError,
)
from scripts.seed_demo import (  # noqa: E402
    ALLOWED_SEVERITY,
    load_seed_file,
    validate_all,
    validate_event,
)

FACILITIES_PATH = REPO_ROOT / "geospatial" / "data" / "facilities.geojson"
SEED_PATH = REPO_ROOT / "data" / "demo" / "seed_events.json"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def matcher() -> SpatialMatcher:
    """Real matcher backed by the checked-in demo facilities layer."""
    return SpatialMatcher.from_file(FACILITIES_PATH)


@pytest.fixture(scope="module")
def empty_matcher() -> SpatialMatcher:
    """Matcher backed by an empty layer, simulating a missing/failed OSM fetch."""
    return SpatialMatcher.from_geojson_dict({"type": "FeatureCollection", "features": []})


@pytest.fixture(scope="module")
def seed_data() -> dict:
    return load_seed_file(SEED_PATH)


@pytest.fixture(scope="module")
def seed_events(seed_data: dict) -> list[dict]:
    return [scenario["event"] for scenario in seed_data["scenarios"]]


def _event_by_scenario(seed_data: dict, scenario_id: str) -> dict:
    for scenario in seed_data["scenarios"]:
        if scenario["scenario_id"] == scenario_id:
            return scenario["event"]
    raise KeyError(f"No scenario '{scenario_id}' in seed data")


# ---------------------------------------------------------------------------
# 1. Spatial matching -- point-in-polygon / nearest-neighbor
# ---------------------------------------------------------------------------

class TestSpatialMatching:
    def test_point_inside_facility_is_contained(self, matcher: SpatialMatcher):
        result = matcher.match(12.345, 78.905)  # inside FAC-001 polygon
        assert result.matched is True
        assert result.match_type == "CONTAINS"
        assert result.facility_id == "FAC-001"
        assert result.distance_km == 0.0
        assert result.evidence  # must always explain the match

    def test_point_inside_second_facility(self, matcher: SpatialMatcher):
        result = matcher.match(12.503, 78.704)  # inside FAC-002 polygon
        assert result.matched is True
        assert result.facility_id == "FAC-002"
        assert result.context_type == "Industrial Facility"

    def test_point_near_but_outside_facility_uses_nearest(self, matcher: SpatialMatcher):
        # Just outside the FAC-001 polygon boundary, within search radius.
        result = matcher.match(12.345, 78.930, max_nearest_km=25.0)
        assert result.matched is True
        assert result.match_type == "NEAREST"
        assert result.facility_id == "FAC-001"
        assert result.distance_km is not None and result.distance_km > 0

    def test_point_far_from_everything_returns_no_context_not_a_crash(self, matcher: SpatialMatcher):
        # Middle of the ocean -- nowhere near any demo facility.
        result = matcher.match(0.0, 0.0, max_nearest_km=25.0)
        assert result.matched is False
        assert result.context_type == "Unknown"
        assert result.evidence  # still explains WHY there's no match

    def test_crop_burning_region_matches_agricultural_context(self, matcher: SpatialMatcher):
        result = matcher.match(15.821, 78.026)  # inside REG-CROP-01
        assert result.matched is True
        assert result.context_type == "Agricultural Land"
        assert result.facility_id == "REG-CROP-01"

    @pytest.mark.parametrize(
        "lat,lon",
        [
            (91.0, 0.0),      # latitude out of range
            (0.0, 200.0),     # longitude out of range
            (float("nan"), 78.9),
        ],
    )
    def test_invalid_coordinates_degrade_safely_by_default(self, matcher: SpatialMatcher, lat, lon):
        result = matcher.match(lat, lon)  # strict=False (default)
        assert result.matched is False
        assert result.context_type == "Unknown"

    def test_invalid_coordinates_raise_in_strict_mode(self, matcher: SpatialMatcher):
        with pytest.raises(SpatialMatchError):
            matcher.match(91.0, 0.0, strict=True)

    def test_missing_facility_layer_never_crashes_pipeline(self, empty_matcher: SpatialMatcher):
        # Simulates OSM/GeoJSON fetch having failed entirely.
        result = empty_matcher.match(12.345, 78.905)
        assert result.matched is False
        assert result.context_type == "Unknown"

    def test_nonexistent_facilities_file_falls_back_to_empty_layer(self):
        # Loading from a bad path must not raise -- it degrades to "no context".
        matcher_from_missing_file = SpatialMatcher.from_file(REPO_ROOT / "does" / "not" / "exist.geojson")
        result = matcher_from_missing_file.match(12.345, 78.905)
        assert result.matched is False

    def test_batch_matching_survives_one_bad_point(self, matcher: SpatialMatcher):
        points = [(12.345, 78.905), (float("nan"), 0.0), (12.503, 78.704)]
        results = matcher.match_batch(points)
        assert len(results) == 3
        assert results[0].matched is True
        assert results[1].matched is False  # the bad point, degraded not raised
        assert results[2].matched is True


# ---------------------------------------------------------------------------
# 2. Shared data contract compliance
# ---------------------------------------------------------------------------

class TestDataContract:
    def test_seed_file_loads(self, seed_data: dict):
        assert "scenarios" in seed_data
        assert len(seed_data["scenarios"]) == 3

    def test_seed_file_covers_all_three_required_scenarios(self, seed_data: dict):
        labels = {s["scenario_label"] for s in seed_data["scenarios"]}
        assert labels == {"Normal / Baseline", "Critical Anomaly", "False Alarm / Non-Target Context"}

    def test_all_seed_events_satisfy_shared_contract(self, seed_data: dict):
        problems = validate_all(seed_data["scenarios"])
        assert problems == [], f"Contract violations: {problems}"

    def test_event_ids_are_unique(self, seed_events: list[dict]):
        ids = [e["event_id"] for e in seed_events]
        assert len(ids) == len(set(ids))

    def test_every_event_has_non_empty_evidence(self, seed_events: list[dict]):
        for event in seed_events:
            assert isinstance(event["evidence"], list)
            assert len(event["evidence"]) >= 1

    @pytest.mark.parametrize(
        "bad_event,expected_problem_substring",
        [
            ({}, "missing required field"),
            ({"event_id": "X", "severity": "SUPER_BAD"}, "severity"),
            ({"event_id": "X", "latitude": 999, "longitude": 0}, "latitude"),
        ],
    )
    def test_validate_event_catches_broken_events(self, bad_event, expected_problem_substring):
        # A partially-filled event should be flagged, never silently accepted.
        problems = validate_event(bad_event, scenario_id="TEST")
        assert any(expected_problem_substring in p for p in problems)

    def test_validate_event_accepts_a_well_formed_event(self, seed_events: list[dict]):
        problems = validate_event(seed_events[0], scenario_id="TEST")
        assert problems == []


# ---------------------------------------------------------------------------
# 3. Severity / anomaly threshold behavior
# ---------------------------------------------------------------------------

def anomaly_to_severity(anomaly_score: float) -> str:
    """Reference threshold rule shared with the AI/priority module.

    Mirrors the bands the priority engine is expected to apply:
        < 0.25         -> LOW
        0.25 - 0.5     -> MODERATE
        0.5  - 0.75    -> HIGH
        >= 0.75        -> CRITICAL
    Kept here (duplicated deliberately, not imported) so this test suite
    also catches the AI module silently changing its thresholds without
    updating the integration contract.
    """
    if anomaly_score >= 0.75:
        return "CRITICAL"
    if anomaly_score >= 0.5:
        return "HIGH"
    if anomaly_score >= 0.25:
        return "MODERATE"
    return "LOW"


class TestSeverityThresholds:
    def test_baseline_event_is_low_severity(self, seed_data: dict):
        event = _event_by_scenario(seed_data, "SCN-A-BASELINE")
        assert event["severity"] == "LOW"
        assert anomaly_to_severity(event["anomaly_score"]) == "LOW"

    def test_critical_event_crosses_critical_threshold(self, seed_data: dict):
        event = _event_by_scenario(seed_data, "SCN-B-CRITICAL")
        assert event["severity"] == "CRITICAL"
        assert event["current_value"] > event["baseline_value"]
        assert anomaly_to_severity(event["anomaly_score"]) == "CRITICAL"

    def test_false_alarm_event_stays_low_despite_thermal_signal(self, seed_data: dict):
        event = _event_by_scenario(seed_data, "SCN-C-FALSE-ALARM")
        assert event["severity"] == "LOW"
        assert event["source_class"] == "Crop Burning"

    @pytest.mark.parametrize(
        "score,expected",
        [(0.0, "LOW"), (0.24, "LOW"), (0.25, "MODERATE"), (0.49, "MODERATE"),
         (0.5, "HIGH"), (0.74, "HIGH"), (0.75, "CRITICAL"), (1.0, "CRITICAL")],
    )
    def test_threshold_boundaries_are_exact(self, score, expected):
        assert anomaly_to_severity(score) == expected

    def test_declared_severity_never_disagrees_with_reference_thresholds(self, seed_events: list[dict]):
        # Guards against demo fixtures drifting out of sync with the
        # priority rule the AI module is expected to implement.
        for event in seed_events:
            assert anomaly_to_severity(event["anomaly_score"]) == event["severity"], (
                f"{event['event_id']}: anomaly_score={event['anomaly_score']} "
                f"implies {anomaly_to_severity(event['anomaly_score'])}, "
                f"but severity field says {event['severity']}"
            )


# ---------------------------------------------------------------------------
# 4. End-to-end: coordinate -> spatial context -> contract-valid, correctly
#    severed event, with no crash even when context enrichment fails.
# ---------------------------------------------------------------------------

class TestEndToEndPipeline:
    def test_seed_event_coordinates_match_their_declared_facility(
        self, matcher: SpatialMatcher, seed_data: dict
    ):
        for scenario in seed_data["scenarios"]:
            event = scenario["event"]
            result = matcher.match(event["latitude"], event["longitude"])
            assert result.facility_id == event["facility_id"], (
                f"{scenario['scenario_id']}: spatial match says facility_id="
                f"{result.facility_id!r}, seed event declares {event['facility_id']!r}"
            )

    def test_pipeline_survives_full_context_loss(self, empty_matcher: SpatialMatcher, seed_events: list[dict]):
        """Simulate the OSM/facilities layer being completely unavailable at
        demo time. Every event must still produce a contract-valid,
        non-crashing result -- just with degraded (Unknown) context.
        """
        for event in seed_events:
            spatial_result = empty_matcher.match(event["latitude"], event["longitude"]).to_dict()
            assert spatial_result["matched"] is False
            assert spatial_result["context_type"] == "Unknown"

            # Severity logic must still run off the event's own anomaly_score,
            # independent of whether spatial context was available.
            severity = anomaly_to_severity(event["anomaly_score"])
            assert severity in ALLOWED_SEVERITY

    def test_full_seed_file_round_trips_through_json(self, seed_data: dict):
        # Catches accidental non-JSON-serializable values sneaking into fixtures.
        serialized = json.dumps(seed_data)
        reloaded = json.loads(serialized)
        assert reloaded == seed_data
