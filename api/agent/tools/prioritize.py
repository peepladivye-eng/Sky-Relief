"""
prioritize.py — Tool 7
======================
Deterministic scoring → ranked action list.

Score formula (from config.py weights, must sum to 100):

  score = W_FLOOD_FRACTION   * min(1, flood_fraction)               # flood coverage of 300 m buffer
        + W_REPORT_URGENCY   * min(1, urgency_sum / 3)              # normalised urgency
        + W_SILENT_FLOODED   * (1 if silent_flooded else 0)         # satellite-only signal
        + W_FACILITIES       * min(1, num_exposed_facilities / 2)   # hospitals/schools/bridges
        + W_ROAD_CUT         * (1 if road_flooded else 0)           # access road flooded
        + W_RAIN_ANOMALY     * rain_anomaly_flag                    # rainfall anomaly

Tie-break: population (if available in OSM) then alphabetical by name.

Each Priority record carries:
  - reasons:  human-readable list of what drove the score
  - sources:  source ids that back each reason (for the Verifier)
  - recommended_action: short action string derived from the need mix
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

log = logging.getLogger(__name__)

from config import (
    W_FLOOD_FRACTION, W_REPORT_URGENCY, W_SILENT_FLOODED,
    W_FACILITIES, W_ROAD_CUT, W_RAIN_ANOMALY,
    CACHE_DIR, DATA_DIR,
)
from schemas import Event, Exposure, Report, Weather, Priority

# ── recommended_action lookup ─────────────────────────────────────────────────

_ACTION_MAP: dict[str, str] = {
    "evacuation":   "Immediate evacuation required",
    "rescue":       "Search and rescue operation needed",
    "medical":      "Deploy medical team and supplies",
    "food":         "Emergency food and water distribution",
    "shelter":      "Set up relief camp / shelter",
    "road":         "Road clearance or alternate route needed",
    "water":        "Drinking water supply urgently required",
    "power":        "Generator / power restoration needed",
    "engineering":  "Structural / embankment inspection required",
    "helicopter":   "Helicopter access required",
    "access":       "Aerial or boat access required",
    "unknown":      "Ground verification team needed",
}

_DEFAULT_ACTION = "Immediate assessment and relief dispatch"


def _recommended_action(needs: list[str]) -> str:
    """Pick the most urgent recommended action from a list of need strings."""
    priority_order = [
        "evacuation", "rescue", "medical", "helicopter", "access",
        "food", "water", "shelter", "road", "power", "engineering",
    ]
    for key in priority_order:
        for n in needs:
            if n and key in n.lower():
                return _ACTION_MAP[key]
    if needs:
        # Fall through: use the first non-null need
        for n in needs:
            if n:
                for k, v in _ACTION_MAP.items():
                    if k in n.lower():
                        return v
    return _DEFAULT_ACTION


# ── population lookup ─────────────────────────────────────────────────────────

def _population_map(event_dir: Path) -> dict[str, int]:
    """Return {settlement_name: population} from osm.geojson."""
    osm_path = event_dir / "osm.geojson"
    if not osm_path.exists():
        return {}
    with open(osm_path) as f:
        osm = json.load(f)
    pop: dict[str, int] = {}
    for feat in osm.get("features", []):
        props = feat.get("properties", {})
        if props.get("type") == "settlement":
            name = props.get("name", "")
            p    = props.get("population")
            if name and p is not None:
                pop[name] = int(p)
    return pop


# ── main scoring ──────────────────────────────────────────────────────────────

def run(
    event: Event,
    exposures: list[Exposure],
    reports: list[Report],
    weather: Weather,
) -> list[Priority]:
    """
    Score and rank all settlements with flood_fraction > 0 (or with reports).
    Results cached.
    """
    cache_path = CACHE_DIR / event.event_id / "priorities.json"
    cache_path.parent.mkdir(parents=True, exist_ok=True)

    has_live = any(r.source == "live_input" for r in reports)

    if cache_path.exists() and not has_live:
        log.info("prioritize: cache hit %s", cache_path)
        raw = json.loads(cache_path.read_text())
        return [Priority.model_validate(p) for p in raw]

    rain_flag    = 1.0 if weather.anomaly else 0.0
    pop_map      = _population_map(DATA_DIR / event.event_id)
    event_source = f"raster:{event.event_id}"

    # Index confirmed/unverified reports by settlement proximity
    from agent.tools.geo import _haversine_m

    def reports_near(lat: float, lon: float, radius_m: float = 900.0) -> list[Report]:
        return [
            r for r in reports
            if r.lat is not None
            and r.lon is not None
            and r.status in ("confirmed", "unverified")
            and _haversine_m(lat, lon, r.lat, r.lon) < radius_m
        ]

    priorities: list[Priority] = []

    # Score every settlement (even un-flooded ones with a report nearby)
    candidate_names = {e.settlement for e in exposures}
    exp_by_name     = {e.settlement: e for e in exposures}

    for name, exp in exp_by_name.items():
        nearby = reports_near(exp.lat, exp.lon)

        urgency_sum = sum((r.urgency or 0) for r in nearby)

        # ── Score components ─────────────────────────────────────────────
        c_flood     = W_FLOOD_FRACTION * min(1.0, exp.flood_fraction)
        c_urgency   = W_REPORT_URGENCY * min(1.0, urgency_sum / 3.0)
        c_silent    = W_SILENT_FLOODED * (1.0 if exp.silent_flooded else 0.0)
        c_facilities= W_FACILITIES    * min(1.0, len(exp.facilities) / 2.0)
        c_road      = W_ROAD_CUT      * (1.0 if exp.road_flooded else 0.0)
        c_rain      = W_RAIN_ANOMALY  * rain_flag

        score = c_flood + c_urgency + c_silent + c_facilities + c_road + c_rain

        # ── Reason strings with source ids ───────────────────────────────
        reasons: list[str] = []
        sources: list[str] = [event_source]

        if exp.flood_fraction > 0:
            reasons.append(
                f"{exp.flood_fraction*100:.0f}% of 300 m buffer flooded "
                f"[{event_source}]"
            )
        if exp.silent_flooded:
            reasons.append(
                f"No ground reports despite flooding — likely cut off "
                f"[{event_source}]"
            )
        if nearby:
            for r in nearby[:3]:  # cap at 3 for readability
                reasons.append(
                    f"Report urgency {r.urgency}/3: {r.text[:60]}… "
                    f"[{r.id}]"
                )
                sources.append(r.id)
        if exp.facilities:
            fac_str = ", ".join(exp.facilities[:3])
            reasons.append(f"Exposed facilities: {fac_str} [{event_source}]")
        if exp.road_flooded:
            reasons.append(f"Access road flooded [{event_source}]")
        if weather.anomaly:
            reasons.append(
                f"Rainfall anomaly: peak {weather.peak_mm} mm, "
                f"3-day {weather.three_day_mm} mm [rainfall:{event.event_id}]"
            )
            sources.append(f"rainfall:{event.event_id}")

        # ── Recommended action ───────────────────────────────────────────
        needs = [r.need for r in nearby] + (
            ["evacuation"] if exp.silent_flooded else []
        )
        action = _recommended_action(needs)

        priorities.append(Priority(
            rank=0,           # filled after sort
            settlement=name,
            score=round(score, 2),
            reasons=reasons if reasons else ["No data — monitor"],
            sources=list(dict.fromkeys(sources)),  # deduplicate, preserve order
            recommended_action=action,
        ))

    # ── Sort: score desc; tie-break population desc, then name asc ───────
    priorities.sort(
        key=lambda p: (
            -p.score,
            -pop_map.get(p.settlement, 0),
            p.settlement,
        )
    )
    for i, p in enumerate(priorities):
        priorities[i] = p.model_copy(update={"rank": i + 1})

    # Cache
    if not has_live:
        cache_path.write_text(
            json.dumps([p.model_dump() for p in priorities], indent=2)
        )

    log.info(
        "prioritize: %d settlements ranked; top=%s (%.1f)",
        len(priorities),
        priorities[0].settlement if priorities else "—",
        priorities[0].score if priorities else 0,
    )
    return priorities
