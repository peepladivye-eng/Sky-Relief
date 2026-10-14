"""
geo.py — Tool 3
===============
Intersects the flood polygon layer with OSM vector data to produce
a per-settlement Exposure table.
"""
from __future__ import annotations
import json, logging
from pathlib import Path
from typing import Any
import numpy as np
log = logging.getLogger(__name__)
from config import SETTLEMENT_BUFFER_M, CACHE_DIR, DATA_DIR
from schemas import Event, Exposure, Report

def _shapely():
    from shapely.geometry import shape, Point, MultiPolygon, Polygon
    from shapely.ops import unary_union
    return shape, Point, MultiPolygon, Polygon, unary_union

def _pyproj():
    from pyproj import Transformer
    return Transformer

def _wgs84_to_utm_transformer(lon, lat):
    Transformer = _pyproj()
    zone = int((lon + 180) / 6) + 1
    epsg = 32600 + zone if lat >= 0 else 32700 + zone
    return (Transformer.from_crs("EPSG:4326", f"EPSG:{epsg}", always_xy=True),
            Transformer.from_crs(f"EPSG:{epsg}", "EPSG:4326", always_xy=True))

def _buffer_wgs84(lon, lat, radius_m):
    from shapely.geometry import Point as ShapelyPoint, Polygon as ShapelyPolygon
    to_utm, from_utm = _wgs84_to_utm_transformer(lon, lat)
    x_utm, y_utm = to_utm.transform(lon, lat)
    pt_utm = ShapelyPoint(x_utm, y_utm)
    buf_utm = pt_utm.buffer(radius_m)
    ext = np.array(buf_utm.exterior.coords)
    xs, ys = from_utm.transform(ext[:, 0], ext[:, 1])
    return ShapelyPolygon(zip(xs, ys))

def _flood_polygon_union(flood_geojson):
    shape_fn, _, _, _, unary_union_fn = _shapely()
    geoms = []
    for feat in flood_geojson.get("features", []):
        try:
            geoms.append(shape_fn(feat["geometry"]))
        except Exception:
            pass
    return unary_union_fn(geoms) if geoms else None

def _haversine_m(lat1, lon1, lat2, lon2):
    R = 6_371_000.0
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    dphi = np.radians(lat2 - lat1)
    dlam = np.radians(lon2 - lon1)
    a = np.sin(dphi/2)**2 + np.cos(phi1)*np.cos(phi2)*np.sin(dlam/2)**2
    return 2 * R * np.arcsin(np.sqrt(a))

def run(event, flood_stats, reports):
    cache_path = CACHE_DIR / event.event_id / "exposures.json"
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    if cache_path.exists():
        log.info("geo: cache hit %s", cache_path)
        raw = json.loads(cache_path.read_text())
        return [Exposure.model_validate(r) for r in raw]
    osm_path = DATA_DIR / event.event_id / "osm.geojson"
    with open(osm_path) as f:
        osm = json.load(f)
    flood_union = _flood_polygon_union(flood_stats.geojson)
    if flood_union is None:
        log.warning("geo: no flood polygons")
    shape_fn, Point_fn, _, _, _ = _shapely()
    settlements, facilities, roads = [], [], []
    for feat in osm.get("features", []):
        t = feat.get("properties", {}).get("type", "")
        if t == "settlement": settlements.append(feat)
        elif t in ("hospital", "school", "bridge"): facilities.append(feat)
        elif t == "road": roads.append(feat)
    report_locs = [(r.lat, r.lon) for r in reports if r.lat is not None and r.lon is not None]
    exposures = []
    for s_feat in settlements:
        props = s_feat.get("properties", {})
        name = props.get("name", "Unknown")
        coords = s_feat["geometry"]["coordinates"]
        s_lon, s_lat = float(coords[0]), float(coords[1])
        try:
            buf = _buffer_wgs84(s_lon, s_lat, SETTLEMENT_BUFFER_M)
        except Exception as exc:
            log.warning("buffer failed for %s: %s", name, exc)
            buf = None
        flood_fraction = 0.0
        if buf is not None and flood_union is not None:
            try:
                intersection = buf.intersection(flood_union)
                flood_fraction = float(np.clip(intersection.area / buf.area if buf.area > 0 else 0.0, 0.0, 1.0))
            except Exception as exc:
                log.warning("intersection failed for %s: %s", name, exc)
        exposed_facilities = []
        if buf is not None:
            for fac in facilities:
                fac_coords = fac["geometry"]["coordinates"]
                fac_pt = Point_fn(float(fac_coords[0]), float(fac_coords[1]))
                try:
                    if buf.contains(fac_pt) or buf.touches(fac_pt):
                        exposed_facilities.append(f"{fac['properties']['type']}:{fac['properties']['name']}")
                except Exception:
                    pass
        road_flooded = False
        if flood_union is not None and buf is not None:
            for road in roads:
                try:
                    road_geom = shape_fn(road["geometry"])
                    road_in_buf = road_geom.intersection(buf)
                    if not road_in_buf.is_empty and road_in_buf.intersection(flood_union).length > 0:
                        road_flooded = True
                        break
                except Exception:
                    pass
        has_report = any(_haversine_m(s_lat, s_lon, r_lat, r_lon) < SETTLEMENT_BUFFER_M * 3
                         for r_lat, r_lon in report_locs)
        silent_flooded = (flood_fraction > 0) and (not has_report)
        exposures.append(Exposure(settlement=name, lat=s_lat, lon=s_lon,
                                   flood_fraction=round(flood_fraction, 4),
                                   facilities=exposed_facilities,
                                   road_flooded=road_flooded, silent_flooded=silent_flooded))
    exposures.sort(key=lambda e: e.flood_fraction, reverse=True)
    cache_path.write_text(json.dumps([e.model_dump() for e in exposures], indent=2))
    log.info("geo: %d exposures (%d flooded)", len(exposures), sum(1 for e in exposures if e.flood_fraction > 0))
    return exposures

def road_km_flooded(event, flood_stats):
    osm_path = DATA_DIR / event.event_id / "osm.geojson"
    if not osm_path.exists(): return 0.0
    with open(osm_path) as f:
        osm = json.load(f)
    shape_fn, _, _, _, _ = _shapely()
    flood_union = _flood_polygon_union(flood_stats.geojson)
    if flood_union is None: return 0.0
    total_deg = 0.0
    for feat in osm.get("features", []):
        if feat.get("properties", {}).get("type") == "road":
            try:
                total_deg += shape_fn(feat["geometry"]).intersection(flood_union).length
            except Exception:
                pass
    return round(total_deg * 111.32, 2)
