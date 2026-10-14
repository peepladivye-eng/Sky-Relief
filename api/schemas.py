"""
SkyRelief — canonical Pydantic v2 schemas.
Every field is documented; every schema used in an LLM call is serialisable to JSON.
"""
from __future__ import annotations
from typing import Any
from pydantic import BaseModel, Field


class Event(BaseModel):
    event_id   : str
    name       : str
    bbox       : tuple[float, float, float, float]  # (minx, miny, maxx, maxy) WGS-84
    before_date: str                                  # ISO-8601 date
    after_date : str
    sensor     : str                                  # "sentinel-1" | "sentinel-2"
    # Optional per-event overrides for raster thresholds
    water_db   : float | None = Field(None, description="Override SAR_WATER_DB per event")


class FloodStats(BaseModel):
    area_km2        : float
    pct_of_bbox     : float
    unknown_fraction: float  # fraction of bbox with cloud/no-data (S2) or 0 for SAR
    geojson         : dict   # FeatureCollection of flood polygons


class VisionCheck(BaseModel):
    mask_plausible       : bool
    false_positive_notes : list[str]
    damage_observations  : list[str]
    caveats              : list[str]
    confidence           : float  # 0–1


class Weather(BaseModel):
    peak_mm    : float
    three_day_mm: float
    anomaly    : bool
    series     : list[dict]  # [{date, mm}]


class Report(BaseModel):
    id        : str
    text      : str
    source    : str
    source_url: str | None = None
    place     : str | None = None
    lat       : float | None = None
    lon       : float | None = None
    need      : str | None = None
    urgency   : int | None = None   # 1-3
    count     : int | None = None
    status    : str | None = None   # confirmed | contradicted | unverified | silent_flooded


class Exposure(BaseModel):
    settlement    : str
    lat           : float
    lon           : float
    flood_fraction: float
    facilities    : list[str]
    road_flooded  : bool
    silent_flooded: bool


class Priority(BaseModel):
    rank              : int
    settlement        : str
    score             : float
    reasons           : list[str]
    sources           : list[str]
    recommended_action: str


class Sitrep(BaseModel):
    event           : Event
    flood           : FloodStats
    vision          : VisionCheck
    weather         : Weather
    reports         : list[Report]
    exposures       : list[Exposure]
    priorities      : list[Priority]
    summary_en      : str
    summary_hi      : str
    whatsapp_brief_en: str
    whatsapp_brief_hi: str
    limitations     : list[str]


# ── LLM intermediate schemas ──────────────────────────────────────────────────

class ReportExtraction(BaseModel):
    """Returned by reports.py LLM call."""
    place  : str | None = None
    need   : str | None = None
    urgency: int | None = None   # 1–3
    count  : int | None = None


class BriefOutput(BaseModel):
    """Returned by brief.py LLM call."""
    summary_en       : str
    summary_hi       : str
    whatsapp_brief_en: str
    whatsapp_brief_hi: str
    limitations      : list[str]


class LLMError(BaseModel):
    """Typed error returned when LLM call fails after retries."""
    error  : str
    raw    : str | None = None
