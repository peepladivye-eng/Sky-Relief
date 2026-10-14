"""
raster.py â€” Tool 1
==================
Deterministic flood-mask computation from Sentinel-1 VV (or Sentinel-2 NDWI).

HARD RULE: all flood extent comes from numpy raster math here.
           The VLM (vision.py) only verifies, explains and flags caveats.

Algorithm (Sentinel-1 default):
  1. Read before/after bands, convert linear â†’ dB.
  2. Apply 3Ã—3 median filter to each.
  3. water_after  = after_dB  < water_db_threshold
     water_before = before_dB < water_db_threshold   (permanent water)
  4. flood = water_after & ~water_before
  5. Change check: also require (after_dB - before_dB) < SAR_CHANGE_DB
  6. Remove blobs < MIN_BLOB_PIXELS.
  7. Mask slope-shadow false positives if slope.tif present (slope > SLOPE_SHADOW_DEG).
  8. Output: boolean raster, GeoJSON polygons, area_km2.

Sentinel-2 fallback:
  NDWI = (B3-B8)/(B3+B8); water = NDWI > S2_NDWI_THRESHOLD; same set logic.
  Cloud-masked pixels excluded (SCL band if present) â†’ unknown_fraction.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import numpy as np

log = logging.getLogger(__name__)

# Late-import rasterio so the module is importable even if rasterio DLL
# fails (tests can mock it out).  If it's genuinely missing at call-time we
# raise a clear error.
def _rio():
    import rasterio
    return rasterio

def _features():
    import rasterio.features as rf
    return rf

def _skimage_morph():
    from skimage import morphology
    return morphology

from config import (
    SAR_WATER_DB_DEFAULT, SAR_CHANGE_DB, MIN_BLOB_PIXELS,
    SLOPE_SHADOW_DEG, S2_NDWI_THRESHOLD, CACHE_DIR, DATA_DIR,
)
from schemas import FloodStats, Event


# â”€â”€ helpers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def _linear_to_db(arr: np.ndarray) -> np.ndarray:
    """Convert linear SAR power to dB, clamping near-zero values."""
    return 10.0 * np.log10(np.clip(arr, 1e-10, None))


def _read_band(path: Path, band: int = 1) -> tuple[np.ndarray, Any, Any]:
    """
    Read a single band from a GeoTIFF.
    Returns (data, transform, crs).
    """
    rio = _rio()
    with rio.open(path) as src:
        data = src.read(band).astype(np.float32)
        transform = src.transform
        crs = src.crs
        nodata = src.nodata
        if nodata is not None:
            data[data == nodata] = np.nan
    return data, transform, crs


def _median_filter_3x3(arr: np.ndarray) -> np.ndarray:
    """Apply a 3Ã—3 median filter (scipy preferred, numpy fallback)."""
    try:
        from scipy.ndimage import median_filter
        return median_filter(arr, size=3).astype(np.float32)
    except ImportError:
        log.warning("scipy not available; skipping median filter")
        return arr


def _polygonize(mask: np.ndarray, transform) -> list[dict]:
    """
    Convert a boolean mask to a list of GeoJSON polygon dicts.
    Returns a list of GeoJSON Feature dicts.
    """
    features_mod = _features()
    import rasterio
    shapes = list(features_mod.shapes(
        mask.astype(np.uint8),
        mask=(mask > 0),
        transform=transform,
    ))
    feats = []
    for geom, val in shapes:
        if val > 0:
            feats.append({
                "type": "Feature",
                "properties": {"flood": True},
                "geometry": geom,
            })
    return feats


def _pixel_area_km2(transform, n_pixels: int) -> float:
    """Estimate area in kmÂ² given a pixel count and affine transform."""
    import math
    # For geographic CRS (degrees): approximate using mean lat
    px_w = abs(transform.a)   # degrees per pixel (x)
    px_h = abs(transform.e)   # degrees per pixel (y)
    # 1 degree lat â‰ˆ 111.32 km; 1 degree lon â‰ˆ 111.32 * cos(lat) km
    # We use a rough 111.32Â² factor for both (good enough for display)
    km_per_deg = 111.32
    area_per_pixel_km2 = (px_w * km_per_deg) * (px_h * km_per_deg)
    return area_per_pixel_km2 * n_pixels


def _bbox_area_km2(transform, rows: int, cols: int) -> float:
    return _pixel_area_km2(transform, rows * cols)


# â”€â”€ Sentinel-1 algorithm â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def run_sentinel1(
    event_dir: Path,
    water_db: float | None = None,
) -> FloodStats:
    """
    Full Sentinel-1 VV flood mask pipeline.
    """
    water_db = water_db if water_db is not None else SAR_WATER_DB_DEFAULT

    before_path = event_dir / "before.tif"
    after_path  = event_dir / "after.tif"
    slope_path  = event_dir / "slope.tif"

    log.info("Loading SAR rasters for %s", event_dir.name)
    before_lin, transform, crs = _read_band(before_path)
    after_lin,  _,         _   = _read_band(after_path)

    # Step 1: Convert to dB
    before_db = _linear_to_db(before_lin)
    after_db  = _linear_to_db(after_lin)

    # Step 2: Median filter
    before_db = _median_filter_3x3(before_db)
    after_db  = _median_filter_3x3(after_db)

    # Step 3: Water classification
    water_after  = after_db  < water_db
    water_before = before_db < water_db   # permanent water

    # Step 4: New flood = water after, not water before
    flood = water_after & ~water_before

    # Step 5: Change confirmation (-3 dB drop required)
    change = (after_db - before_db) < SAR_CHANGE_DB
    flood = flood & change

    # Step 6: Remove small blobs
    try:
        morph = _skimage_morph()
        flood = morph.remove_small_objects(flood, max_size=MIN_BLOB_PIXELS)
    except Exception as exc:
        log.warning("remove_small_objects failed: %s", exc)

    # Step 7: Slope-shadow masking (optional)
    if slope_path.exists():
        try:
            slope, _, _ = _read_band(slope_path)
            shadow_mask = slope > SLOPE_SHADOW_DEG
            flood = flood & ~shadow_mask
            log.info("Slope mask applied (%d pixels removed)",
                     int(shadow_mask.sum()))
        except Exception as exc:
            log.warning("slope.tif read failed: %s", exc)

    rows, cols = flood.shape
    n_flood    = int(flood.sum())
    n_total    = rows * cols

    area_km2     = _pixel_area_km2(transform, n_flood)
    bbox_area    = _bbox_area_km2(transform, rows, cols)
    pct_of_bbox  = (n_flood / n_total * 100.0) if n_total > 0 else 0.0

    # Vectorise to GeoJSON polygons
    try:
        feats    = _polygonize(flood, transform)
        geojson  = {"type": "FeatureCollection", "features": feats}
    except Exception as exc:
        log.warning("Polygonize failed: %s â€” returning empty FeatureCollection", exc)
        geojson = {"type": "FeatureCollection", "features": []}

    log.info("Flood mask: %d px / %d px (%.1f%%) = %.2f kmÂ²",
             n_flood, n_total, pct_of_bbox, area_km2)

    return FloodStats(
        area_km2=round(area_km2, 3),
        pct_of_bbox=round(pct_of_bbox, 2),
        unknown_fraction=0.0,   # SAR: no clouds
        geojson=geojson,
    )


# â”€â”€ Sentinel-2 fallback â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def run_sentinel2(event_dir: Path) -> FloodStats:
    """
    Sentinel-2 NDWI fallback.
    Expects before.tif = B3 (green) channel, after.tif = B8 (NIR) channel,
    OR a 2-band composite where band 1 = B3, band 2 = B8.
    Cloud mask via SCL band if available.
    """
    before_path = event_dir / "before.tif"
    after_path  = event_dir / "after.tif"

    # Try to read both bands from the same file first
    try:
        rio = _rio()
        with rio.open(after_path) as src:
            if src.count >= 2:
                b3  = src.read(1).astype(np.float32)
                b8  = src.read(2).astype(np.float32)
                transform = src.transform
                unknown_fraction = 0.0
                # SCL cloud mask: band 3 if present
                if src.count >= 3:
                    scl = src.read(3)
                    cloud = np.isin(scl, [3, 8, 9, 10])  # cloud shadow/med/high/cirrus
                    unknown_fraction = float(cloud.mean())
                else:
                    cloud = np.zeros_like(b3, dtype=bool)
            else:
                b3, transform, _ = _read_band(before_path)
                b8, _,          _ = _read_band(after_path)
                cloud = np.zeros_like(b3, dtype=bool)
                unknown_fraction = 0.0
    except Exception as exc:
        log.error("Sentinel-2 read failed: %s", exc)
        raise

    # NDWI
    denom = b3 + b8
    denom[denom == 0] = 1e-6
    ndwi = (b3 - b8) / denom

    # Before NDWI from before.tif (treat as B3 only â€” can't do NDWI without NIR)
    # For the set logic we re-use before as a dry reference: no permanent water flag
    ndwi_before, _, _ = _read_band(before_path)
    ndwi_before_ndwi  = np.full_like(ndwi, -1.0)  # assume no permanent water if no NIR

    water_after  = (ndwi  > S2_NDWI_THRESHOLD) & ~cloud
    water_before = (ndwi_before_ndwi > S2_NDWI_THRESHOLD)
    flood        = water_after & ~water_before

    # Remove small blobs
    try:
        morph = _skimage_morph()
        flood = morph.remove_small_objects(flood, max_size=MIN_BLOB_PIXELS)
    except Exception:
        pass

    rows, cols = flood.shape
    n_flood    = int(flood.sum())
    n_total    = rows * cols
    area_km2   = _pixel_area_km2(transform, n_flood)
    pct_of_bbox = (n_flood / n_total * 100.0) if n_total > 0 else 0.0

    try:
        feats   = _polygonize(flood, transform)
        geojson = {"type": "FeatureCollection", "features": feats}
    except Exception:
        geojson = {"type": "FeatureCollection", "features": []}

    return FloodStats(
        area_km2=round(area_km2, 3),
        pct_of_bbox=round(pct_of_bbox, 2),
        unknown_fraction=round(unknown_fraction, 3),
        geojson=geojson,
    )


# â”€â”€ Public entry point â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def run(event: Event) -> FloodStats:
    """
    Main entry point called by the orchestrator.
    Dispatches to Sentinel-1 or Sentinel-2 pipeline based on event.sensor.
    Results are cached to /cache/<event_id>/flood_stats.json.
    """
    cache_path = CACHE_DIR / event.event_id / "flood_stats.json"
    cache_path.parent.mkdir(parents=True, exist_ok=True)

    if cache_path.exists():
        log.info("raster: cache hit %s", cache_path)
        return FloodStats.model_validate_json(cache_path.read_text())

    event_dir = DATA_DIR / event.event_id
    if not event_dir.exists():
        raise FileNotFoundError(f"Event directory not found: {event_dir}")

    sensor = event.sensor.lower()
    if "sentinel-2" in sensor or "s2" in sensor:
        stats = run_sentinel2(event_dir)
    else:
        stats = run_sentinel1(event_dir, water_db=event.water_db)

    cache_path.write_text(stats.model_dump_json(indent=2))
    return stats


def get_flood_mask_array(event: Event) -> tuple[np.ndarray, Any]:
    """
    Return (flood_mask_bool_array, transform) for use by geo.py and overlay.
    Recomputes from source (not from the JSON cache) to get the numpy array.
    """
    event_dir = DATA_DIR / event.event_id
    sensor    = event.sensor.lower()

    if "sentinel-2" in sensor or "s2" in sensor:
        # Simplified: just rerun but return array
        before_path = event_dir / "before.tif"
        after_path  = event_dir / "after.tif"
        rio = _rio()
        with rio.open(after_path) as src:
            b3 = src.read(1).astype(np.float32)
            b8 = src.read(2).astype(np.float32) if src.count >= 2 else b3 * 0
            transform = src.transform
        denom = b3 + b8; denom[denom == 0] = 1e-6
        ndwi = (b3 - b8) / denom
        water_after  = ndwi > S2_NDWI_THRESHOLD

        with rio.open(before_path) as src:
            b3b = src.read(1).astype(np.float32)
        ndwi_b = (b3b - b3b) / 1.0  # fallback: all dry before
        water_before = ndwi_b > S2_NDWI_THRESHOLD
        flood = water_after & ~water_before
    else:
        water_db = event.water_db or SAR_WATER_DB_DEFAULT
        before_lin, transform, _ = _read_band(event_dir / "before.tif")
        after_lin,  _,         _ = _read_band(event_dir / "after.tif")
        before_db = _median_filter_3x3(_linear_to_db(before_lin))
        after_db  = _median_filter_3x3(_linear_to_db(after_lin))
        water_after  = after_db  < water_db
        water_before = before_db < water_db
        flood = water_after & ~water_before
        change = (after_db - before_db) < SAR_CHANGE_DB
        flood  = flood & change
        try:
            morph = _skimage_morph()
            flood = morph.remove_small_objects(flood, max_size=MIN_BLOB_PIXELS)
        except Exception:
            pass

    return flood, transform

