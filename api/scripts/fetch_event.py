"""
fetch_event.py
==============
Downloads live Sentinel-1/2 imagery, rainfall, and OSM data for an event.
Only runs when LIVE_DATA=1.  Otherwise prints instructions for manual download.

Usage:
    LIVE_DATA=1 python api/scripts/fetch_event.py himachal_2023
"""
from __future__ import annotations
import os, sys, json
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT / "api"))

from config import LIVE_DATA, DATA_DIR


def fetch(event_id: str) -> None:
    event_dir = DATA_DIR / event_id
    meta_path = event_dir / "meta.json"
    if not meta_path.exists():
        print(f"ERROR: No meta.json for {event_id}")
        return

    with open(meta_path) as f:
        meta = json.load(f)

    print(f"\n=== {event_id}: {meta['name']} ===")

    if not LIVE_DATA:
        print("LIVE_DATA=0 — using pre-downloaded fixtures.")
        print("To fetch live data, set LIVE_DATA=1 and ensure:")
        print("  1. pystac-client + planetary-computer installed")
        print("  2. Open-Meteo API accessible")
        print("  3. Overpass API accessible")
        print("Fixture files already present:")
        for f in ["before.tif", "after.tif", "rainfall.csv", "osm.geojson", "reports.json"]:
            exists = (event_dir / f).exists()
            print(f"  {'OK' if exists else 'MISSING'}: {f}")
        return

    # Live fetch
    minx, miny, maxx, maxy = meta["bbox"]
    before_date = meta["before_date"]
    after_date  = meta["after_date"]

    # Rainfall
    print("Fetching rainfall from Open-Meteo...")
    try:
        import httpx
        lat = (miny + maxy) / 2
        lon = (minx + maxx) / 2
        url = (f"https://archive-api.open-meteo.com/v1/archive"
               f"?latitude={lat:.4f}&longitude={lon:.4f}"
               f"&start_date={before_date}&end_date={after_date}"
               f"&daily=precipitation_sum&timezone=Asia%2FKolkata")
        r = httpx.get(url, timeout=30)
        r.raise_for_status()
        data = r.json()
        dates  = data["daily"]["time"]
        precip = data["daily"]["precipitation_sum"]
        lines  = ["date,mm"] + [f"{d},{p or 0.0}" for d, p in zip(dates, precip)]
        (event_dir / "rainfall.csv").write_text("\n".join(lines))
        print(f"  rainfall.csv: {len(dates)} days")
    except Exception as exc:
        print(f"  ERROR: {exc}")

    # OSM data
    print("Fetching OSM data from Overpass...")
    try:
        import httpx
        query = f"""
[out:json][timeout:60];
(
  node["place"~"village|town|city"]({miny},{minx},{maxy},{maxx});
  node["amenity"~"hospital|clinic|school"]({miny},{minx},{maxy},{maxx});
  node["man_made"="bridge"]({miny},{minx},{maxy},{maxx});
  way["highway"~"primary|secondary|trunk"]({miny},{minx},{maxy},{maxx});
);
out geom;
"""
        r = httpx.post("https://overpass-api.de/api/interpreter",
                       data={"data": query}, timeout=60)
        r.raise_for_status()
        # Convert to GeoJSON (simplified)
        osm_data = r.json()
        features = []
        for el in osm_data.get("elements", []):
            tags = el.get("tags", {})
            if el["type"] == "node":
                t = "settlement" if "place" in tags else \
                    "hospital"   if tags.get("amenity") in ("hospital","clinic") else \
                    "school"     if tags.get("amenity") == "school" else "bridge"
                features.append({
                    "type": "Feature",
                    "properties": {"type": t, "name": tags.get("name","Unknown")},
                    "geometry": {"type": "Point", "coordinates": [el["lon"], el["lat"]]}
                })
        fc = {"type": "FeatureCollection", "features": features}
        (event_dir / "osm.geojson").write_text(json.dumps(fc, indent=2))
        print(f"  osm.geojson: {len(features)} features")
    except Exception as exc:
        print(f"  ERROR: {exc}")

    print("\nNote: Sentinel-1/2 imagery download requires planetary-computer credentials.")
    print("See: https://planetarycomputer.microsoft.com/docs/quickstarts/reading-stac/")


if __name__ == "__main__":
    event_ids = sys.argv[1:] or ["himachal_2023", "assam_2022"]
    for eid in event_ids:
        fetch(eid)