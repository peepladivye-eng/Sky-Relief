"""
reports.py — Tool 5
===================
Loads ground reports from fixture (or extra_reports passed at runtime),
calls the LLM to extract structured fields, then geocodes via a fixture
gazetteer built from the event's osm.geojson.

LLM prompt contract:
  "Extract place, need, urgency 1-3, count.
   If absent, null. Never infer a location that is not in the text."

Every report gets:
  id, text, source, source_url, place, lat, lon, need, urgency, count
  status is set to None here; fuse.py fills it in.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

log = logging.getLogger(__name__)

from config import CACHE_DIR, DATA_DIR
from schemas import Event, Report, ReportExtraction, LLMError
from llm import llm_json, llm_available

# ── Prompt ────────────────────────────────────────────────────────────────────

_SYSTEM = (
    "You are a disaster-response data extraction assistant. "
    "Extract information from a ground report. "
    "Return ONLY valid JSON matching the schema. "
    "Rules: "
    "1. Never infer a location that is not explicitly mentioned in the text. "
    "2. urgency: 1=low, 2=medium, 3=urgent. Null if not determinable. "
    "3. count: number of people affected, null if not mentioned. "
    "4. place: exact location name as written in the text, null if absent. "
    "5. need: primary need (e.g. food, evacuation, medical, shelter), null if unclear."
)

_USER_TEMPLATE = (
    'Extract from this disaster ground report:\n\n"{text}"\n\n'
    "Return JSON: "
    '{"place": string|null, "need": string|null, "urgency": int|null, "count": int|null}'
)


# ── Gazetteer (built from osm.geojson settlement + facility names) ────────────

def _build_gazetteer(event_dir: Path) -> dict[str, tuple[float, float]]:
    """
    Return {lowercased_name: (lat, lon)} from all named OSM features.
    Used for geocoding extracted place names without an LLM call.
    """
    osm_path = event_dir / "osm.geojson"
    if not osm_path.exists():
        return {}
    with open(osm_path) as f:
        osm = json.load(f)

    gazetteer: dict[str, tuple[float, float]] = {}
    for feat in osm.get("features", []):
        geom = feat.get("geometry", {})
        if geom.get("type") != "Point":
            continue
        name = feat.get("properties", {}).get("name", "")
        if not name:
            continue
        lon, lat = geom["coordinates"][:2]
        # Index by full name and each word (for partial matching)
        gazetteer[name.lower()] = (float(lat), float(lon))
        for word in name.lower().split():
            if len(word) >= 4 and word not in gazetteer:
                gazetteer[word] = (float(lat), float(lon))
    return gazetteer


def _geocode(place: str | None, gazetteer: dict) -> tuple[float | None, float | None]:
    """
    Look up a place name in the gazetteer.
    Returns (lat, lon) or (None, None).
    """
    if not place:
        return None, None
    key = place.lower().strip()
    if key in gazetteer:
        return gazetteer[key]
    # Try partial match: any gazetteer key that starts with or contains key
    for g_key, coords in gazetteer.items():
        if key in g_key or g_key in key:
            return coords
    return None, None


# ── LLM extraction (with offline fallback) ────────────────────────────────────

def _extract_fields(text: str) -> ReportExtraction:
    """
    Call LLM to extract place/need/urgency/count.
    Falls back to a simple heuristic extraction if LLM unavailable.
    """
    if not llm_available():
        return _heuristic_extract(text)

    result = llm_json(
        system=_SYSTEM,
        user=_USER_TEMPLATE.format(text=text),
        schema=ReportExtraction,
        temperature=0.1,
    )
    if isinstance(result, LLMError):
        log.warning("LLM extraction failed: %s — using heuristic", result.error)
        return _heuristic_extract(text)
    return result


def _heuristic_extract(text: str) -> ReportExtraction:
    """
    Simple keyword-based extraction for offline/demo mode.
    Not a substitute for the LLM but keeps the pipeline running.
    """
    import re

    # Urgency keywords
    urgency = None
    high_kw   = ["emergency", "urgent", "immediate", "stranded", "missing",
                  "submerged", "no contact", "evacuate", "rescue"]
    medium_kw = ["flood", "damaged", "blocked", "waterlogged", "affected",
                 "disrupted", "request"]
    low_kw    = ["improving", "manageable", "distributed", "relief camp"]
    tl = text.lower()
    if any(k in tl for k in high_kw):
        urgency = 3
    elif any(k in tl for k in medium_kw):
        urgency = 2
    elif any(k in tl for k in low_kw):
        urgency = 1

    # Count: first number followed by "people", "families", "persons", "residents"
    count = None
    m = re.search(r"(\d[\d,]*)\s+(?:people|families|persons|residents|villagers)", tl)
    if m:
        try:
            count = int(m.group(1).replace(",", ""))
        except ValueError:
            pass

    # Need keywords
    need = None
    need_map = {
        "evacuation": ["evacuat", "rescue", "airli"],
        "food":        ["food", "ration", "provision", "hunger"],
        "medical":     ["medical", "hospital", "medicine", "doctor", "patient"],
        "shelter":     ["shelter", "relief camp", "camp"],
        "road":        ["road", "highway", "blocked", "clearance"],
        "water":       ["drinking water", "clean water"],
        "power":       ["power", "generator", "electricity"],
    }
    for need_label, keywords in need_map.items():
        if any(k in tl for k in keywords):
            need = need_label
            break

    return ReportExtraction(place=None, need=need, urgency=urgency, count=count)


# ── Public entry point ────────────────────────────────────────────────────────

def run(
    event: Event,
    extra_texts: list[str] | None = None,
) -> list[Report]:
    """
    Load, extract, and geocode all reports for an event.
    extra_texts: raw strings pasted at demo time (live paste path).
    Results cached; extra_reports bypass cache and are merged in.
    """
    cache_path = CACHE_DIR / event.event_id / "reports.json"
    cache_path.parent.mkdir(parents=True, exist_ok=True)

    # Load fixture reports
    fixture_path = DATA_DIR / event.event_id / "reports.json"
    if not fixture_path.exists():
        log.warning("No reports.json for %s", event.event_id)
        raw_reports: list[dict] = []
    else:
        with open(fixture_path) as f:
            raw_reports = json.load(f)

    # Add extra_texts as ad-hoc report dicts
    extra_raw: list[dict] = []
    if extra_texts:
        for i, txt in enumerate(extra_texts):
            extra_raw.append({
                "id":         f"live_{i+1:03d}",
                "text":       txt,
                "source":     "live_input",
                "source_url": None,
                "place":      None,
                "lat":        None,
                "lon":        None,
                "need":       None,
                "urgency":    None,
                "count":      None,
                "status":     None,
            })

    gazetteer = _build_gazetteer(DATA_DIR / event.event_id)

    all_raw = raw_reports + extra_raw
    reports: list[Report] = []

    for raw in all_raw:
        rid  = raw.get("id", f"r_{len(reports)+1:03d}")
        text = raw.get("text", "")

        # Use pre-filled fixture fields if present; otherwise extract via LLM
        if raw.get("place") is not None and raw.get("urgency") is not None:
            # Fixture already has extracted fields — geocode only if lat/lon missing
            place   = raw.get("place")
            need    = raw.get("need")
            urgency = raw.get("urgency")
            count   = raw.get("count")
        else:
            extracted = _extract_fields(text)
            place   = extracted.place
            need    = extracted.need
            urgency = extracted.urgency
            count   = extracted.count

        # Geocode
        lat = raw.get("lat")
        lon = raw.get("lon")
        if (lat is None or lon is None) and place:
            lat, lon = _geocode(place, gazetteer)

        reports.append(Report(
            id=rid,
            text=text,
            source=raw.get("source", "unknown"),
            source_url=raw.get("source_url"),
            place=place,
            lat=lat,
            lon=lon,
            need=need,
            urgency=urgency,
            count=count,
            status=None,  # fuse.py sets this
        ))

    # Cache fixture reports (not extras — they're per-request)
    if not extra_texts:
        cache_path.write_text(
            json.dumps([r.model_dump() for r in reports], indent=2)
        )

    log.info("reports: %d total (%d geocoded)",
             len(reports),
             sum(1 for r in reports if r.lat is not None))
    return reports
