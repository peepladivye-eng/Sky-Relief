"""
orchestrator.py
===============
Agent loop:  plan -> run tools 1,3,4,5 (parallel) -> tool 2 on tool-1 output
             -> fuse -> prioritize -> brief -> verify -> return Sitrep

SSE events emitted via an async generator so main.py can stream them to the
frontend.  Each step yields:
  {"type": "step", "tool": "<name>", "status": "running|done|error", "detail": "..."}
Final yield:
  {"type": "sitrep", "data": <Sitrep as dict>}
"""
from __future__ import annotations
import asyncio, json, logging, time
from typing import AsyncGenerator
log = logging.getLogger(__name__)

from schemas import Event, Sitrep

def _load_event(event_id: str) -> Event:
    from config import DATA_DIR
    import json as _json
    path = DATA_DIR / event_id / "meta.json"
    if not path.exists():
        raise FileNotFoundError(f"No event found: {event_id}")
    return Event.model_validate(_json.loads(path.read_text()))

def _step(tool: str, status: str, detail: str = "") -> dict:
    return {"type": "step", "tool": tool, "status": status, "detail": detail, "ts": time.time()}

async def run_analysis(
    event_id: str,
    extra_reports: list[str] | None = None,
) -> AsyncGenerator[dict, None]:
    """
    Main agent loop.  Yields SSE-compatible dicts.
    All tool calls are run in executor threads (they are synchronous/blocking).
    """
    loop = asyncio.get_event_loop()

    def _run(fn, *args, **kwargs):
        return loop.run_in_executor(None, lambda: fn(*args, **kwargs))

    try:
        event = _load_event(event_id)
    except FileNotFoundError as exc:
        yield {"type": "error", "detail": str(exc)}
        return

    # ── Tool imports ──────────────────────────────────────────────────────
    from agent.tools import raster, geo, weather, reports as reports_tool
    from agent.tools import vision, fuse, prioritize, brief, verify

    # ── Step 1: raster (flood mask) ───────────────────────────────────────
    yield _step("raster", "running", "Computing flood mask from SAR imagery")
    try:
        flood_stats = await _run(raster.run, event)
        yield _step("raster", "done",
                    f"Flood area: {flood_stats.area_km2:.1f} km2 "
                    f"({flood_stats.pct_of_bbox:.1f}% of region)")
    except Exception as exc:
        log.exception("raster failed")
        yield _step("raster", "error", str(exc))
        yield {"type": "error", "detail": f"raster failed: {exc}"}
        return

    # ── Steps 3,4,5 in parallel: geo, weather, reports ───────────────────
    yield _step("geo",     "running", "Computing settlement exposure")
    yield _step("weather", "running", "Analysing rainfall series")
    yield _step("reports", "running", "Loading and extracting ground reports")

    try:
        # Load reports first (needed by geo for silent_flooded)
        reports_list = await _run(reports_tool.run, event, extra_reports)
        geo_future     = _run(geo.run,     event, flood_stats, reports_list)
        weather_future = _run(weather.run, event)
        exposures, weather_data = await asyncio.gather(geo_future, weather_future)

        yield _step("geo",     "done",
                    f"{len(exposures)} settlements assessed, "
                    f"{sum(1 for e in exposures if e.flood_fraction > 0)} flooded")
        yield _step("weather", "done",
                    f"Peak {weather_data.peak_mm} mm/day, "
                    f"anomaly={'yes' if weather_data.anomaly else 'no'}")
        yield _step("reports", "done",
                    f"{len(reports_list)} reports loaded "
                    f"({sum(1 for r in reports_list if r.lat is not None)} geocoded)")
    except Exception as exc:
        log.exception("parallel tools failed")
        yield _step("geo", "error", str(exc))
        yield {"type": "error", "detail": f"parallel tools failed: {exc}"}
        return

    # ── Step 2: vision (VLM verification) ────────────────────────────────
    yield _step("vision", "running", "VLM verifying flood mask overlay")
    try:
        vision_check = await _run(vision.run, event, flood_stats)
        yield _step("vision", "done",
                    f"mask_plausible={vision_check.mask_plausible}, "
                    f"confidence={vision_check.confidence:.2f}")
    except Exception as exc:
        log.warning("vision failed (non-fatal): %s", exc)
        from agent.tools.vision import _OFFLINE_VISION
        vision_check = _OFFLINE_VISION
        yield _step("vision", "error", f"Using offline stub: {exc}")

    # ── Fuse ──────────────────────────────────────────────────────────────
    yield _step("fuse", "running", "Cross-checking reports vs flood mask")
    try:
        fused_reports, fused_exposures = await _run(
            fuse.run, event, reports_list, flood_stats, exposures
        )
        confirmed  = sum(1 for r in fused_reports if r.status == "confirmed")
        silent_ct  = sum(1 for e in fused_exposures if e.silent_flooded)
        yield _step("fuse", "done",
                    f"{confirmed} confirmed reports, {silent_ct} silent-flooded settlements")
    except Exception as exc:
        log.exception("fuse failed")
        yield _step("fuse", "error", str(exc))
        yield {"type": "error", "detail": f"fuse failed: {exc}"}
        return

    # ── Prioritize ────────────────────────────────────────────────────────
    yield _step("prioritize", "running", "Scoring and ranking settlements")
    try:
        priorities = await _run(
            prioritize.run, event, fused_exposures, fused_reports, weather_data
        )
        yield _step("prioritize", "done",
                    f"Top priority: {priorities[0].settlement} "
                    f"(score {priorities[0].score:.0f})")
    except Exception as exc:
        log.exception("prioritize failed")
        yield _step("prioritize", "error", str(exc))
        yield {"type": "error", "detail": f"prioritize failed: {exc}"}
        return

    # ── Brief ─────────────────────────────────────────────────────────────
    yield _step("brief", "running", "Writing situation report and WhatsApp briefs")
    try:
        brief_out = await _run(
            brief.run, event, flood_stats, vision_check,
            weather_data, priorities, fused_exposures
        )
        yield _step("brief", "done", "Sitrep + Hindi brief generated")
    except Exception as exc:
        log.exception("brief failed")
        yield _step("brief", "error", str(exc))
        yield {"type": "error", "detail": f"brief failed: {exc}"}
        return

    # ── Verify ────────────────────────────────────────────────────────────
    yield _step("verify", "running", "Verifying all claims have source ids")
    sitrep = Sitrep(
        event=event,
        flood=flood_stats,
        vision=vision_check,
        weather=weather_data,
        reports=fused_reports,
        exposures=fused_exposures,
        priorities=priorities,
        summary_en=brief_out.summary_en,
        summary_hi=brief_out.summary_hi,
        whatsapp_brief_en=brief_out.whatsapp_brief_en,
        whatsapp_brief_hi=brief_out.whatsapp_brief_hi,
        limitations=brief_out.limitations,
    )
    try:
        sitrep, dropped = await _run(verify.run, sitrep)
        yield _step("verify", "done",
                    f"{len(dropped)} unsourced sentences removed" if dropped
                    else "All claims sourced")
    except Exception as exc:
        log.warning("verify failed (non-fatal): %s", exc)
        yield _step("verify", "error", str(exc))

    # ── Final sitrep ──────────────────────────────────────────────────────
    yield {"type": "sitrep", "data": sitrep.model_dump()}