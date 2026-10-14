"""
fuse.py â€” Tool 6
================
Cross-checks ground reports against the flood mask to assign each report
a status, and identifies "silent flooded" settlements.

Fusion rules (per spec Â§7):
  confirmed     â€” report location is inside / within 500 m of any flood pixel
  contradicted  â€” report location is > 2 km from any flood pixel
  unverified    â€” otherwise (no coordinates, or in the ambiguous band)

Silent flooded:
  Any settlement with flood_fraction > 0 that has zero confirmed/unverified
  reports within 900 m is marked silent_flooded=True on its Exposure record.

Flood mask proximity is tested against the GeoJSON polygon union returned by
raster.py.  When shapely is unavailable (DLL-blocked dev machine) we fall
back to a bounding-box check so the pipeline keeps running.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import numpy as np

log = logging.getLogger(__name__)

from config import CONFIRM_RADIUS_M, CONTRADICT_RADIUS_M, CACHE_DIR
from schemas import Event, Report, Exposure, FloodStats
from agent.tools.geo import _haversine_m

# â”€â”€ shapely availability guard â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def _shapely_ok() -> bool:
    try:
        from shapely.geometry import shape  # noqa: F401
        return True
    except Exception:
        return False


# â”€â”€ Flood polygon helper â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def _flood_centroid_list(flood_geojson: dict) -> list[tuple[float, float]]:
    """
    Return a list of (lat, lon) centroids for every flood polygon.
    Used as a fast proximity check when shapely is unavailable.
    """
    centroids: list[tuple[float, float]] = []
    for feat in flood_geojson.get("features", []):
        geom = feat.get("geometry", {})
        try:
            coords = geom.get("coordinates", [[]])
            if geom.get("type") == "Polygon":
                ring  = np.array(coords[0])
                c_lon = float(ring[:, 0].mean())
                c_lat = float(ring[:, 1].mean())
                centroids.append((c_lat, c_lon))
            elif geom.get("type") == "MultiPolygon":
                for poly in coords:
                    ring  = np.array(poly[0])
                    centroids.append((float(ring[:, 1].mean()),
                                      float(ring[:, 0].mean())))
        except Exception:
            pass
    return centroids


def _nearest_flood_dist_m(lat: float, lon: float, flood_geojson: dict) -> float:
    """
    Return minimum distance in metres from (lat, lon) to any flood polygon.
    Uses shapely if available; otherwise uses polygon centroids as a proxy.
    Returns float('inf') if no flood polygons exist.
    """
    feats = flood_geojson.get("features", [])
    if not feats:
        return float("inf")

    if _shapely_ok():
        from shapely.geometry import shape, Point
        from pyproj import Transformer

        # Project to UTM for accurate distance
        zone   = int((lon + 180) / 6) + 1
        epsg   = 32600 + zone if lat >= 0 else 32700 + zone
        to_utm = Transformer.from_crs("EPSG:4326", f"EPSG:{epsg}", always_xy=True)

        px, py = to_utm.transform(lon, lat)
        pt_utm = Point(px, py)

        min_dist = float("inf")
        for feat in feats:
            try:
                geom_wgs = shape(feat["geometry"])
                # Transform polygon to UTM via coordinate array (no deprecated ops.transform)
                import numpy as _np
                from shapely.geometry import Polygon as _Poly, MultiPolygon as _MPoly
                if geom_wgs.geom_type == "Polygon":
                    ext = _np.array(geom_wgs.exterior.coords)
                    xs, ys = to_utm.transform(ext[:,0], ext[:,1])
                    geom_utm = _Poly(zip(xs, ys))
                else:
                    geom_utm = geom_wgs  # fallback for non-polygon
                d = pt_utm.distance(geom_utm)
                if d < min_dist:
                    min_dist = d
                    if min_dist == 0:
                        break
            except Exception:
                pass
        return min_dist
    else:
        # Fallback: use polygon centroids
        centroids = _flood_centroid_list(flood_geojson)
        if not centroids:
            return float("inf")
        return min(
            _haversine_m(lat, lon, c_lat, c_lon)
            for c_lat, c_lon in centroids
        )


# â”€â”€ Public entry point â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def run(
    event: Event,
    reports: list[Report],
    flood_stats: FloodStats,
    exposures: list[Exposure],
) -> tuple[list[Report], list[Exposure]]:
    """
    1. Assign status to each report.
    2. Re-evaluate silent_flooded on each Exposure (authoritative pass,
       using confirmed/unverified report set, not just raw locations).

    Returns updated (reports, exposures).
    Results cached.
    """
    cache_path = CACHE_DIR / event.event_id / "fused.json"
    cache_path.parent.mkdir(parents=True, exist_ok=True)

    # Check cache â€” but only for the base fixture reports (no extra_reports)
    has_live = any(r.source == "live_input" for r in reports)
    if cache_path.exists() and not has_live:
        log.info("fuse: cache hit %s", cache_path)
        data = json.loads(cache_path.read_text())
        fused_reports   = [Report.model_validate(r)   for r in data["reports"]]
        fused_exposures = [Exposure.model_validate(e) for e in data["exposures"]]
        return fused_reports, fused_exposures

    flood_geojson = flood_stats.geojson

    # â”€â”€ Step 1: assign status to each report â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    fused_reports: list[Report] = []
    has_flood_pixels = bool(flood_geojson.get("features"))

    for rep in reports:
        if rep.lat is None or rep.lon is None:
            # No coordinates â†’ cannot assess proximity â†’ unverified
            status = "unverified"
        elif not has_flood_pixels:
            # No flood mask at all â†’ cannot confirm or contradict
            status = "unverified"
        else:
            dist = _nearest_flood_dist_m(rep.lat, rep.lon, flood_geojson)
            if dist <= CONFIRM_RADIUS_M:
                status = "confirmed"
            elif dist >= CONTRADICT_RADIUS_M:
                status = "contradicted"
            else:
                status = "unverified"

        fused_reports.append(rep.model_copy(update={"status": status}))

    log.info(
        "fuse: %d confirmed  %d unverified  %d contradicted  %d no-coords",
        sum(1 for r in fused_reports if r.status == "confirmed"),
        sum(1 for r in fused_reports if r.status == "unverified"),
        sum(1 for r in fused_reports if r.status == "contradicted"),
        sum(1 for r in fused_reports if r.lat is None),
    )

    # â”€â”€ Step 2: re-evaluate silent_flooded on exposures â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    # A settlement is silent_flooded if:
    #   - flood_fraction > 0  AND
    #   - no confirmed or unverified report within 900 m
    active_report_locs: list[tuple[float, float]] = [
        (r.lat, r.lon)
        for r in fused_reports
        if r.status in ("confirmed", "unverified")
        and r.lat is not None
        and r.lon is not None
    ]

    fused_exposures: list[Exposure] = []
    silent_count = 0
    for exp in exposures:
        has_nearby_report = any(
            _haversine_m(exp.lat, exp.lon, r_lat, r_lon) < 900.0
            for r_lat, r_lon in active_report_locs
        )
        is_silent = (exp.flood_fraction > 0) and (not has_nearby_report)
        if is_silent:
            silent_count += 1
        fused_exposures.append(exp.model_copy(update={"silent_flooded": is_silent}))

    log.info("fuse: %d silent-flooded settlements", silent_count)

    # â”€â”€ Cache (fixture-only; skip for live requests) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    if not has_live:
        cache_path.write_text(json.dumps({
            "reports":   [r.model_dump() for r in fused_reports],
            "exposures": [e.model_dump() for e in fused_exposures],
        }, indent=2))

    return fused_reports, fused_exposures

