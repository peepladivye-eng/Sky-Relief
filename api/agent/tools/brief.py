"""
brief.py - Tool 8
=================
LLM writes the situation report + WhatsApp brief in English and Hindi.

Prompt contract (spec section 10):
  Input = structured facts only (Priority list, stats, weather, limitations).
  "Write only from supplied facts. Each sentence must end with source ids
   in brackets. Hindi must be plain, field-usable language."

Falls back to a template-based brief when LLM is unavailable.
"""
from __future__ import annotations
import logging
log = logging.getLogger(__name__)
from config import CACHE_DIR
from schemas import Event, FloodStats, VisionCheck, Weather, Priority, Exposure, BriefOutput, LLMError
from llm import llm_json, llm_available

_SYSTEM = (
    "You are a disaster-response situation report writer. "
    "You write concise, factual reports for field officers and NGO coordinators. "
    "RULES: "
    "1. Write ONLY from the supplied structured facts. Do NOT add information. "
    "2. Every sentence must end with source ids in square brackets, e.g. [raster:himachal_2023]. "
    "3. Hindi summary must use plain, field-usable language (avoid bureaucratic terms). "
    "4. WhatsApp brief must be under 300 characters per language. "
    "5. List limitations honestly. "
    "Return ONLY valid JSON, no markdown fences."
)

def _build_user_prompt(
    event: Event,
    flood: FloodStats,
    vision: VisionCheck,
    weather: Weather,
    priorities: list[Priority],
    exposures: list[Exposure],
) -> str:
    top5 = priorities[:5]
    silent = [e.settlement for e in exposures if e.silent_flooded]
    facts = {
        "event": {"id": event.event_id, "name": event.name,
                  "before": event.before_date, "after": event.after_date},
        "flood": {"area_km2": flood.area_km2, "pct_of_bbox": flood.pct_of_bbox,
                  "source": f"raster:{event.event_id}"},
        "weather": {"peak_mm": weather.peak_mm, "three_day_mm": weather.three_day_mm,
                    "anomaly": weather.anomaly, "source": f"rainfall:{event.event_id}"},
        "vision": {"mask_plausible": vision.mask_plausible,
                   "false_positives": vision.false_positive_notes,
                   "damage": vision.damage_observations,
                   "confidence": vision.confidence},
        "top_priority_settlements": [
            {"rank": p.rank, "settlement": p.settlement, "score": p.score,
             "action": p.recommended_action, "sources": p.sources}
            for p in top5
        ],
        "silent_flooded_settlements": silent,
        "limitations": vision.caveats + [
            "Ground reports may be incomplete or unverified.",
            "Flood mask resolution ~10 m; urban inundation may be underestimated.",
        ],
    }
    import json
    return (
        "Write a situation report and WhatsApp briefs from these facts:\n\n"
        + json.dumps(facts, indent=2)
        + "\n\nReturn JSON: {\"summary_en\": str, \"summary_hi\": str, "
          "\"whatsapp_brief_en\": str, \"whatsapp_brief_hi\": str, \"limitations\": [str]}"
    )

def _template_brief(event, flood, weather, priorities, exposures) -> BriefOutput:
    """Template-based fallback when LLM is unavailable."""
    top = priorities[0] if priorities else None
    silent = [e.settlement for e in exposures if e.silent_flooded]
    src = f"raster:{event.event_id}"

    summary_en = (
        f"FLOOD SITUATION REPORT — {event.name} [{src}]. "
        f"Inundated area: {flood.area_km2:.1f} km² ({flood.pct_of_bbox:.1f}% of region) [{src}]. "
        f"Peak rainfall: {weather.peak_mm:.0f} mm/day [rainfall:{event.event_id}]. "
    )
    if top:
        summary_en += (
            f"Highest priority: {top.settlement} (score {top.score:.0f}/100) — "
            f"{top.recommended_action} [{', '.join(top.sources[:2])}]. "
        )
    if silent:
        summary_en += (
            f"ALERT: {len(silent)} settlement(s) flooded with no ground reports "
            f"(possible comms blackout): {', '.join(silent[:3])} [{src}]."
        )

    summary_hi = (
        f"बाढ़ स्थिति रिपोर्ट — {event.name} [{src}]। "
        f"जलमग्न क्षेत्र: {flood.area_km2:.1f} वर्ग किमी [{src}]। "
        f"अधिकतम वर्षा: {weather.peak_mm:.0f} मिमी/दिन [rainfall:{event.event_id}]। "
    )
    if top:
        summary_hi += f"सर्वोच्च प्राथमिकता: {top.settlement} — {top.recommended_action} [{', '.join(top.sources[:2])}]। "
    if silent:
        summary_hi += f"चेतावनी: {len(silent)} गाँव जलमग्न, कोई रिपोर्ट नहीं: {', '.join(silent[:3])} [{src}]।"

    wa_en = f"FLOOD ALERT {event.name[:20]}: {flood.area_km2:.0f}km² flooded [{src}]."
    if top:
        wa_en += f" Priority: {top.settlement} — {top.recommended_action[:40]}."
    if silent:
        wa_en += f" {len(silent)} silent-flooded villages!"
    wa_en = wa_en[:300]

    wa_hi = f"बाढ़ चेतावनी {event.name[:15]}: {flood.area_km2:.0f} वर्ग किमी जलमग्न [{src}]।"
    if top:
        wa_hi += f" प्राथमिकता: {top.settlement}।"
    if silent:
        wa_hi += f" {len(silent)} गाँव संपर्क से बाहर!"
    wa_hi = wa_hi[:300]

    limitations = [
        "VLM visual verification not performed (API key not configured).",
        "SAR C-band may miss urban flooding (double-bounce effect).",
        "Ground reports may be incomplete; silent-flooded villages unverified.",
        "Flood mask resolution ~10 m.",
    ]
    return BriefOutput(summary_en=summary_en, summary_hi=summary_hi,
                       whatsapp_brief_en=wa_en, whatsapp_brief_hi=wa_hi,
                       limitations=limitations)

def run(event, flood, vision, weather, priorities, exposures) -> BriefOutput:
    cache_path = CACHE_DIR / event.event_id / "brief.json"
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    if cache_path.exists():
        log.info("brief: cache hit %s", cache_path)
        return BriefOutput.model_validate_json(cache_path.read_text())
    if not llm_available():
        log.info("brief: LLM not configured - using template")
        result = _template_brief(event, flood, weather, priorities, exposures)
        cache_path.write_text(result.model_dump_json(indent=2))
        return result
    user_prompt = _build_user_prompt(event, flood, vision, weather, priorities, exposures)
    result = llm_json(system=_SYSTEM, user=user_prompt, schema=BriefOutput, temperature=0.3)
    if isinstance(result, LLMError):
        log.warning("brief LLM failed: %s - using template", result.error)
        result = _template_brief(event, flood, weather, priorities, exposures)
    cache_path.write_text(result.model_dump_json(indent=2))
    log.info("brief: generated summary_en length=%d", len(result.summary_en))
    return result
