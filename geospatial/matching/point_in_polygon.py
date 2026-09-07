"""
geospatial/matching/point_in_polygon.py

ThermoGuard AI / LandslideGuard - Geospatial Context Enrichment
Owner: Member 4 - Geospatial + Integration/QA Lead

Purpose
-------
Given a raw event coordinate (lat, lon), determine:
  1. Whether the point falls INSIDE a known facility/region polygon
     (point-in-polygon containment - highest confidence match), and
  2. If not contained by anything, the NEAREST facility/region and its
     distance (nearest-neighbor spatial match - lower confidence, but
     still useful context).

This module is deliberately defensive: it is the single most likely
place for a demo to crash if the OSM/GeoJSON layer is missing, empty,
malformed, or in the wrong CRS. Every public entry point degrades to a
safe "Unknown / No Context" result instead of raising, unless the
caller explicitly asks for strict mode.

Design notes
------------
- Input geometry is assumed to be WGS84 (EPSG:4326) lat/lon, matching
  OSM/GeoJSON convention and the shared event data contract.
- Distance is computed in a projected, metric CRS (EPSG:3857 - Web
  Mercator) so "nearest facility" and "distance_km" are meaningful
  numbers rather than degrees. EPSG:3857 introduces some distortion at
  high latitudes but is more than adequate for hackathon-scale
  regional distances and avoids the complexity of picking a per-region
  UTM zone under time pressure.
- The module is dependency-light on purpose: GeoPandas + Shapely only.
  No PostGIS/DB required, so it works identically against a live
  facilities table or a static demo GeoJSON file.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional, Union

try:
    import geopandas as gpd
    from shapely.geometry import Point
    from shapely.errors import ShapelyError
except ImportError as exc:  # pragma: no cover - environment guard
    raise ImportError(
        "point_in_polygon.py requires geopandas and shapely. "
        "Install with: pip install geopandas shapely"
    ) from exc

logger = logging.getLogger("thermoguard.geospatial.matching")

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

WGS84 = "EPSG:4326"          # lat/lon, matches event contract + OSM/GeoJSON
METRIC_CRS = "EPSG:3857"     # projected CRS used only for distance math

# Beyond this radius a facility is not considered a meaningful "nearby"
# match - the event is reported as having no facility context rather than
# being force-matched to something 80km away.
DEFAULT_MAX_NEAREST_KM = 25.0

# Columns we expect (with sane fallbacks) on the facilities/regions layer.
DEFAULT_ID_FIELD = "facility_id"
DEFAULT_NAME_FIELD = "facility_name"
DEFAULT_TYPE_FIELD = "context_type"


@dataclass
class SpatialMatchResult:
    """Normalized result of matching one point against a facility layer.

    Mirrors the fields the shared event contract expects
    (facility_id, facility_name, context_type, evidence[]), plus extra
    metadata that's useful for debugging/QA but safe to ignore.
    """

    matched: bool = False
    match_type: str = "NONE"          # "CONTAINS" | "NEAREST" | "NONE"
    facility_id: Optional[str] = None
    facility_name: Optional[str] = None
    context_type: str = "Unknown"
    distance_km: Optional[float] = None
    evidence: list[str] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "matched": self.matched,
            "match_type": self.match_type,
            "facility_id": self.facility_id,
            "facility_name": self.facility_name,
            "context_type": self.context_type,
            "distance_km": self.distance_km,
            "evidence": self.evidence,
            "extra": self.extra,
        }


class SpatialMatchError(Exception):
    """Raised only when the caller opts into strict=True."""


class SpatialMatcher:
    """Loads a facility/region GeoJSON layer once and matches points against it.

    Usage
    -----
        matcher = SpatialMatcher.from_file("geospatial/data/facilities.geojson")
        result = matcher.match(12.3456, 78.9012)
        result.to_dict()  ->  {"matched": True, "match_type": "CONTAINS", ...}

    The matcher is intentionally stateless per-call (no caching of
    per-point results) but loads/reprojects the facility layer once at
    construction time, since that's the expensive part.
    """

    def __init__(
        self,
        facilities: "gpd.GeoDataFrame",
        id_field: str = DEFAULT_ID_FIELD,
        name_field: str = DEFAULT_NAME_FIELD,
        type_field: str = DEFAULT_TYPE_FIELD,
        max_nearest_km: float = DEFAULT_MAX_NEAREST_KM,
    ) -> None:
        self._id_field = id_field
        self._name_field = name_field
        self._type_field = type_field
        self._max_nearest_km = max_nearest_km

        self._gdf_wgs84 = self._prepare_layer(facilities)
        self._gdf_metric = (
            self._gdf_wgs84.to_crs(METRIC_CRS) if not self._gdf_wgs84.empty else self._gdf_wgs84
        )

    # -- construction helpers -------------------------------------------------

    @classmethod
    def from_file(
        cls,
        path: Union[str, Path],
        strict: bool = False,
        **kwargs: Any,
    ) -> "SpatialMatcher":
        """Load a facilities/regions GeoJSON file.

        If the file is missing, empty, or unreadable and strict=False
        (default), returns a matcher backed by an EMPTY layer, so every
        subsequent .match() call cleanly returns "no context" instead of
        crashing the ingestion pipeline. This is important for demo
        resilience: a missing OSM/GeoJSON file must never take down the
        event pipeline.
        """
        path = Path(path)
        try:
            if not path.exists():
                raise FileNotFoundError(f"Facility layer not found: {path}")
            gdf = gpd.read_file(path)
            if gdf.empty:
                logger.warning("Facility layer at %s loaded but contains 0 features.", path)
        except Exception as exc:
            msg = f"Failed to load facility layer from {path}: {exc}"
            if strict:
                raise SpatialMatchError(msg) from exc
            logger.error("%s -- falling back to empty facility layer.", msg)
            gdf = gpd.GeoDataFrame(
                {kwargs.get("id_field", DEFAULT_ID_FIELD): []},
                geometry=[],
                crs=WGS84,
            )
        return cls(gdf, **kwargs)

    @classmethod
    def from_geojson_dict(cls, geojson: dict[str, Any], **kwargs: Any) -> "SpatialMatcher":
        """Build a matcher directly from a parsed GeoJSON dict (e.g. in tests)."""
        try:
            gdf = gpd.GeoDataFrame.from_features(geojson.get("features", []), crs=WGS84)
        except Exception as exc:
            logger.error("Failed to parse in-memory GeoJSON: %s -- using empty layer.", exc)
            gdf = gpd.GeoDataFrame(geometry=[], crs=WGS84)
        return cls(gdf, **kwargs)

    def _prepare_layer(self, gdf: "gpd.GeoDataFrame") -> "gpd.GeoDataFrame":
        """Normalize CRS, drop invalid/null geometries, ensure expected columns exist."""
        gdf = gdf.copy()

        if gdf.crs is None:
            logger.warning("Facility layer has no CRS defined; assuming %s.", WGS84)
            gdf = gdf.set_crs(WGS84)
        elif str(gdf.crs).upper() != WGS84:
            gdf = gdf.to_crs(WGS84)

        # Drop missing/empty geometries defensively -- a single bad OSM
        # feature should not take down spatial matching for every event.
        if not gdf.empty:
            before = len(gdf)
            gdf = gdf[gdf.geometry.notna() & ~gdf.geometry.is_empty]
            dropped = before - len(gdf)
            if dropped:
                logger.warning("Dropped %d facility feature(s) with null/empty geometry.", dropped)

            invalid_mask = ~gdf.geometry.is_valid
            if invalid_mask.any():
                logger.warning(
                    "Repairing %d invalid facility geometries with buffer(0).",
                    int(invalid_mask.sum()),
                )
                gdf.loc[invalid_mask, "geometry"] = gdf.loc[invalid_mask, "geometry"].buffer(0)

        for col in (self._id_field, self._name_field, self._type_field):
            if col not in gdf.columns:
                gdf[col] = None

        return gdf.reset_index(drop=True)

    # -- public API -------------------------------------------------------

    def match(
        self,
        lat: float,
        lon: float,
        max_nearest_km: Optional[float] = None,
        strict: bool = False,
    ) -> SpatialMatchResult:
        """Match a single (lat, lon) point against the facility/region layer.

        Resolution order:
          1. Validate the coordinate.
          2. Point-in-polygon containment check (exact match, high confidence).
          3. Nearest-neighbor search within `max_nearest_km` (fallback, lower
             confidence, distance included as evidence).
          4. No match -> SpatialMatchResult(matched=False, context_type="Unknown").

        Never raises unless strict=True and something is genuinely wrong
        (e.g. NaN coordinates) -- point-in-polygon logic here is meant to
        run inline in the live ingestion path, and a spatial-matching bug
        should degrade context, not take down the pipeline.
        """
        radius = max_nearest_km if max_nearest_km is not None else self._max_nearest_km

        try:
            self._validate_coords(lat, lon)
        except SpatialMatchError:
            if strict:
                raise
            logger.error("Invalid coordinates (lat=%r, lon=%r); returning no-context result.", lat, lon)
            return SpatialMatchResult(evidence=["Invalid or missing coordinates"])

        if self._gdf_wgs84.empty:
            return SpatialMatchResult(evidence=["No facility/region layer available"])

        point_wgs84 = Point(lon, lat)

        try:
            contains_result = self._match_contains(point_wgs84)
            if contains_result is not None:
                return contains_result

            nearest_result = self._match_nearest(lat, lon, radius)
            if nearest_result is not None:
                return nearest_result

        except (ShapelyError, ValueError) as exc:
            if strict:
                raise SpatialMatchError(f"Spatial match failed for ({lat}, {lon}): {exc}") from exc
            logger.exception("Spatial match failed for (%s, %s); returning no-context result.", lat, lon)
            return SpatialMatchResult(evidence=["Spatial match failed - see logs"])

        return SpatialMatchResult(
            evidence=[f"No facility/region within {radius:.1f} km"],
            extra={"search_radius_km": radius},
        )

    def match_batch(
        self,
        points: list[tuple[float, float]],
        max_nearest_km: Optional[float] = None,
    ) -> list[SpatialMatchResult]:
        """Convenience wrapper for enriching a list of (lat, lon) tuples,
        e.g. when seeding a batch of demo events. Never raises; a single
        bad point becomes a no-context result rather than aborting the batch.
        """
        return [self.match(lat, lon, max_nearest_km=max_nearest_km) for lat, lon in points]

    # -- internals ----------------------------------------------------------

    @staticmethod
    def _validate_coords(lat: float, lon: float) -> None:
        try:
            lat_f, lon_f = float(lat), float(lon)
        except (TypeError, ValueError) as exc:
            raise SpatialMatchError(f"Non-numeric coordinates: lat={lat!r}, lon={lon!r}") from exc

        if lat_f != lat_f or lon_f != lon_f:  # NaN check without importing math
            raise SpatialMatchError("NaN coordinates")
        if not (-90.0 <= lat_f <= 90.0) or not (-180.0 <= lon_f <= 180.0):
            raise SpatialMatchError(f"Coordinates out of range: lat={lat_f}, lon={lon_f}")

    def _match_contains(self, point_wgs84: Point) -> Optional[SpatialMatchResult]:
        """Exact point-in-polygon containment check against every facility polygon."""
        contains_mask = self._gdf_wgs84.geometry.contains(point_wgs84)
        if not contains_mask.any():
            return None

        # If multiple polygons overlap (e.g. facility inside a larger
        # industrial zone), prefer the smallest-area match -- it's the
        # most specific context. Area must be computed in the metric CRS,
        # not WGS84 degrees, or the comparison is meaningless.
        candidate_idx = self._gdf_wgs84[contains_mask].index
        areas = self._gdf_metric.loc[candidate_idx].geometry.area
        smallest_idx = areas.idxmin()
        row = self._gdf_wgs84.loc[smallest_idx]

        facility_id = row.get(self._id_field)
        facility_name = row.get(self._name_field)
        context_type = row.get(self._type_field) or "Facility"

        return SpatialMatchResult(
            matched=True,
            match_type="CONTAINS",
            facility_id=str(facility_id) if facility_id is not None else None,
            facility_name=str(facility_name) if facility_name is not None else None,
            context_type=str(context_type),
            distance_km=0.0,
            evidence=[f"Inside {context_type} boundary" + (f" ({facility_name})" if facility_name else "")],
            extra={"overlapping_matches": int(contains_mask.sum())},
        )

    def _match_nearest(self, lat: float, lon: float, max_nearest_km: float) -> Optional[SpatialMatchResult]:
        """Nearest-neighbor fallback using metric-CRS distance."""
        if self._gdf_metric.empty:
            return None

        point_metric = (
            gpd.GeoSeries([Point(lon, lat)], crs=WGS84).to_crs(METRIC_CRS).iloc[0]
        )

        distances = self._gdf_metric.geometry.distance(point_metric)
        nearest_idx = distances.idxmin()
        distance_km = float(distances.loc[nearest_idx]) / 1000.0

        if distance_km > max_nearest_km:
            return None

        row = self._gdf_wgs84.loc[nearest_idx]
        facility_id = row.get(self._id_field)
        facility_name = row.get(self._name_field)
        context_type = row.get(self._type_field) or "Nearby Facility"

        return SpatialMatchResult(
            matched=True,
            match_type="NEAREST",
            facility_id=str(facility_id) if facility_id is not None else None,
            facility_name=str(facility_name) if facility_name is not None else None,
            context_type=str(context_type),
            distance_km=round(distance_km, 3),
            evidence=[
                f"{round(distance_km, 2)} km from nearest {context_type}"
                + (f" ({facility_name})" if facility_name else "")
            ],
        )


# ---------------------------------------------------------------------------
# Module-level convenience function (for callers that don't want to manage
# a SpatialMatcher instance themselves, e.g. quick scripts / notebooks).
# ---------------------------------------------------------------------------

_default_matcher_cache: dict[str, SpatialMatcher] = {}


def match_point(
    lat: float,
    lon: float,
    facilities_path: Union[str, Path],
    max_nearest_km: float = DEFAULT_MAX_NEAREST_KM,
) -> dict[str, Any]:
    """One-shot helper: match a point against a facilities GeoJSON file on disk.

    Caches the loaded/reprojected layer per file path so repeated calls
    (e.g. from a FastAPI endpoint) don't re-read the file every time.
    Returns a plain dict (not a dataclass) for easy JSON serialization
    across the API boundary.
    """
    key = str(Path(facilities_path).resolve())
    matcher = _default_matcher_cache.get(key)
    if matcher is None:
        matcher = SpatialMatcher.from_file(facilities_path, max_nearest_km=max_nearest_km)
        _default_matcher_cache[key] = matcher
    return matcher.match(lat, lon, max_nearest_km=max_nearest_km).to_dict()


if __name__ == "__main__":  # pragma: no cover - manual smoke test
    import json
    import sys

    logging.basicConfig(level=logging.INFO)

    demo_geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "facility_id": "FAC-001",
                    "facility_name": "Demo Chemical Plant",
                    "context_type": "Industrial Facility",
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [78.900, 12.340], [78.910, 12.340],
                        [78.910, 12.350], [78.900, 12.350],
                        [78.900, 12.340],
                    ]],
                },
            }
        ],
    }

    m = SpatialMatcher.from_geojson_dict(demo_geojson)
    test_points = [(12.345, 78.905), (12.400, 78.950), (91.0, 0.0)]
    for lat, lon in test_points:
        print(f"({lat}, {lon}) ->", json.dumps(m.match(lat, lon).to_dict(), indent=2))
    sys.exit(0)
