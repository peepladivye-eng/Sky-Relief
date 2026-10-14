"""Mock raster tool that uses pre-computed cached flood stats."""
import json
from pathlib import Path
from schemas import FloodStats, Event
from config import CACHE_DIR

def run(event: Event) -> FloodStats:
    """
    Return cached flood stats instead of computing from GeoTIFF.
    Use this when Windows blocks rasterio DLLs.
    """
    cache_path = CACHE_DIR / event.event_id / "flood_stats.json"
    
    if not cache_path.exists():
        # Return synthetic default for demo
        return FloodStats(
            area_km2=50.0,
            pct_of_bbox=15.0,
            unknown_fraction=0.0,
            geojson={
                "type": "FeatureCollection",
                "features": [{
                    "type": "Feature",
                    "properties": {},
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[
                            [77.0, 31.8],
                            [77.1, 31.8],
                            [77.1, 31.9],
                            [77.0, 31.9],
                            [77.0, 31.8]
                        ]]
                    }
                }]
            }
        )
    
    data = json.loads(cache_path.read_text())
    return FloodStats(**data)
