"""
weather.py — Tool 4
===================
Parses the rainfall CSV and produces:
  - peak_mm         : highest daily rainfall in the series
  - three_day_mm    : sum of the three highest consecutive days
  - anomaly         : True if peak > 100 mm or 3-day sum > 200 mm (monsoon thresholds)
  - series          : full list of {date, mm} dicts

Optionally (LIVE_DATA=1): fetches from Open-Meteo archive API for bbox centroid.
"""
from __future__ import annotations

import csv
import json
import logging
from pathlib import Path

log = logging.getLogger(__name__)

from config import LIVE_DATA, CACHE_DIR, DATA_DIR
from schemas import Event, Weather

# ── Thresholds for anomaly flag ───────────────────────────────────────────────
PEAK_ANOMALY_MM       = 100.0   # IMD "very heavy rain" threshold
THREE_DAY_ANOMALY_MM  = 200.0   # IMD cumulative extreme threshold


def _load_csv(path: Path) -> list[dict]:
    """Parse date,mm CSV into list of {date, mm} dicts."""
    rows = []
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                rows.append({"date": row["date"].strip(), "mm": float(row["mm"])})
            except (KeyError, ValueError) as exc:
                log.warning("Skipping malformed rainfall row: %s — %s", row, exc)
    return rows


def _three_day_max(series: list[dict]) -> float:
    """Return the maximum rolling 3-day sum in the series."""
    if len(series) < 3:
        return sum(r["mm"] for r in series)
    values = [r["mm"] for r in series]
    return max(
        sum(values[i:i+3])
        for i in range(len(values) - 2)
    )


def _fetch_live(event: Event) -> list[dict]:
    """
    Fetch rainfall from Open-Meteo archive API (only when LIVE_DATA=1).
    Returns list of {date, mm}.
    """
    import httpx
    minx, miny, maxx, maxy = event.bbox
    lat = (miny + maxy) / 2
    lon = (minx + maxx) / 2

    url = (
        "https://archive-api.open-meteo.com/v1/archive"
        f"?latitude={lat:.4f}&longitude={lon:.4f}"
        f"&start_date={event.before_date}&end_date={event.after_date}"
        "&daily=precipitation_sum&timezone=Asia%2FKolkata"
    )
    log.info("weather: fetching live data from Open-Meteo")
    with httpx.Client(timeout=30) as client:
        r = client.get(url)
        r.raise_for_status()
    data = r.json()

    dates = data.get("daily", {}).get("time", [])
    precip = data.get("daily", {}).get("precipitation_sum", [])
    return [
        {"date": d, "mm": float(p or 0.0)}
        for d, p in zip(dates, precip)
    ]


def run(event: Event) -> Weather:
    """
    Main entry point.  Results cached to /cache/<event_id>/weather.json.
    """
    cache_path = CACHE_DIR / event.event_id / "weather.json"
    cache_path.parent.mkdir(parents=True, exist_ok=True)

    if cache_path.exists():
        log.info("weather: cache hit %s", cache_path)
        return Weather.model_validate_json(cache_path.read_text())

    if LIVE_DATA:
        try:
            series = _fetch_live(event)
            log.info("weather: live fetch returned %d days", len(series))
        except Exception as exc:
            log.warning("Live weather fetch failed (%s); falling back to fixture", exc)
            series = None
    else:
        series = None

    if series is None:
        rainfall_path = DATA_DIR / event.event_id / "rainfall.csv"
        if not rainfall_path.exists():
            log.warning("No rainfall.csv for %s; returning zeros", event.event_id)
            return Weather(peak_mm=0.0, three_day_mm=0.0, anomaly=False, series=[])
        series = _load_csv(rainfall_path)

    if not series:
        return Weather(peak_mm=0.0, three_day_mm=0.0, anomaly=False, series=[])

    peak_mm      = max(r["mm"] for r in series)
    three_day_mm = _three_day_max(series)
    anomaly      = (peak_mm >= PEAK_ANOMALY_MM) or (three_day_mm >= THREE_DAY_ANOMALY_MM)

    result = Weather(
        peak_mm=round(peak_mm, 1),
        three_day_mm=round(three_day_mm, 1),
        anomaly=anomaly,
        series=series,
    )
    cache_path.write_text(result.model_dump_json(indent=2))
    log.info("weather: peak=%.1f mm  3-day=%.1f mm  anomaly=%s",
             peak_mm, three_day_mm, anomaly)
    return result
