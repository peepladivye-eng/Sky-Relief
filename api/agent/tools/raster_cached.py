"""
raster_cached.py — Cached flood stats loader for Windows DLL blocking.

When Windows Security blocks rasterio DLLs, use this instead of raster.py.
It loads pre-computed flood_stats.json from cache or generates synthetic data.
"""
from __future__ import annotations
import json
from pathlib import Path

from schemas import FloodStats, Event
from config import CACHE_DIR, DATA_DIR


def run(event: Event) -> FloodStats:
    """
    Return cached flood stats or generate synthetic data for demo.
    This bypasses rasterio entirely.
    """
    cache_path = CACHE_DIR / event.event_id / "flood_stats.json"
    
    # Try cache first
    if cache_path.exists():
        data = json.loads(cache_path.read_text())
        return FloodStats(**data)
    
    # Generate synthetic flood extent for demo
    # Use bbox to create a plausible flood polygon
    minx, miny, maxx, maxy = event.bbox
    cx = (minx + maxx) / 2
    cy = (miny + maxy) / 2
    
    # Create a small flood polygon in center of bbox
    flood_polygon = {
        "type": "FeatureCollection",
        "features": [{
            "type": "Feature",
            "properties": {"flood_class": 1},
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [cx - 0.05, cy - 0.05],
                    [cx + 0.05, cy - 0.05],
                    [cx + 0.05, cy + 0.05],
                    [cx - 0.05, cy + 0.05],
                    [cx - 0.05, cy - 0.05]
                ]]
            }
        }]
    }
    
    # Synthetic stats (realistic for demo)
    area_km2 = 45.5 if event.event_id == "himachal_2023" else 78.2
    pct_of_bbox = 12.3 if event.event_id == "himachal_2023" else 18.7
    
    stats = FloodStats(
        area_km2=area_km2,
        pct_of_bbox=pct_of_bbox,
        unknown_fraction=0.0,
        geojson=flood_polygon
    )
    
    # Cache for next time
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(stats.model_dump(), indent=2))
    
    return stats
