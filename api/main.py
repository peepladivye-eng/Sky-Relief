"""
main.py  —  SkyRelief FastAPI application
==========================================
Endpoints:
  GET  /health
  GET  /events                         -> list[Event]
  POST /analyze                        -> SSE stream of step + sitrep
  GET  /layers/{event_id}/{layer}      -> PNG or GeoJSON
  GET  /export/{event_id}.md           -> markdown sitrep
"""
from __future__ import annotations
import json, logging, os
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, Response, FileResponse
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

import sys
sys.path.insert(0, str(Path(__file__).parent))

from config import DATA_DIR, CACHE_DIR, API_VERSION
from schemas import Event

app = FastAPI(
    title="SkyRelief API",
    description="Multimodal Disaster Response Agent",
    version=API_VERSION,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Request / response models ─────────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    event_id: str
    extra_reports: list[str] | None = None

# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "version": API_VERSION}

# ── Events list ───────────────────────────────────────────────────────────────

@app.get("/events", response_model=list[Event])
async def list_events():
    events = []
    for event_dir in sorted(DATA_DIR.iterdir()):
        meta_path = event_dir / "meta.json"
        if meta_path.exists():
            try:
                events.append(Event.model_validate_json(meta_path.read_text()))
            except Exception as exc:
                log.warning("Skipping malformed meta.json in %s: %s", event_dir, exc)
    return events

# ── Analyze (SSE) ─────────────────────────────────────────────────────────────

@app.post("/analyze")
async def analyze(req: AnalyzeRequest):
    from agent.orchestrator import run_analysis

    async def event_generator() -> AsyncGenerator[str, None]:
        async for msg in run_analysis(req.event_id, req.extra_reports):
            yield json.dumps(msg)

    return EventSourceResponse(event_generator())

# ── Layers ────────────────────────────────────────────────────────────────────

VALID_LAYERS = {"before", "after", "flood", "overlay"}

@app.get("/events/{event_id}/osm")
async def get_osm(event_id: str):
    """Return OSM GeoJSON for roads, bridges, and settlements."""
    event_dir = DATA_DIR / event_id
    osm_path = event_dir / "osm.geojson"
    
    if not osm_path.exists():
        raise HTTPException(404, f"OSM data not found for event: {event_id}")
    
    return Response(
        content=osm_path.read_text(),
        media_type="application/json",
    )

@app.get("/layers/{event_id}/{layer}")
async def get_layer(event_id: str, layer: str):
    if layer not in VALID_LAYERS:
        raise HTTPException(400, f"layer must be one of {VALID_LAYERS}")

    event_dir = DATA_DIR / event_id
    cache_dir = CACHE_DIR / event_id
    cache_dir.mkdir(parents=True, exist_ok=True)

    if not event_dir.exists():
        raise HTTPException(404, f"Event not found: {event_id}")

    # GeoJSON flood layer
    if layer == "flood":
        flood_cache = cache_dir / "flood_stats.json"
        if flood_cache.exists():
            stats = json.loads(flood_cache.read_text())
            return Response(
                content=json.dumps(stats["geojson"]),
                media_type="application/json",
            )
        raise HTTPException(404, "Flood stats not computed yet. Run /analyze first.")

    # PNG layers
    png_map = {
        "before":  cache_dir / "before_thumb.png",
        "after":   cache_dir / "after_thumb.png",
        "overlay": cache_dir / "overlay_thumb.png",
    }
    png_path = png_map[layer]

    if not png_path.exists():
        # Render on demand
        try:
            meta = Event.model_validate_json((event_dir / "meta.json").read_text())
            from agent.tools.vision import _prepare_images
            imgs = _prepare_images(meta)
            if imgs is None:
                raise HTTPException(500, "Could not render image (rasterio unavailable)")
        except Exception as exc:
            raise HTTPException(500, str(exc))

    if not png_path.exists():
        raise HTTPException(404, f"{layer} image not found")

    return FileResponse(png_path, media_type="image/png")

# ── Markdown export ───────────────────────────────────────────────────────────

@app.get("/export/{event_id}.md")
async def export_markdown(event_id: str):
    cache_dir = CACHE_DIR / event_id

    flood_path  = cache_dir / "flood_stats.json"
    brief_path  = cache_dir / "brief.json"
    prio_path   = cache_dir / "priorities.json"
    weather_path= cache_dir / "weather.json"

    if not brief_path.exists():
        raise HTTPException(404, "Sitrep not computed yet. Run /analyze first.")

    flood   = json.loads(flood_path.read_text())  if flood_path.exists()   else {}
    brief   = json.loads(brief_path.read_text())
    prios   = json.loads(prio_path.read_text())   if prio_path.exists()    else []
    weather = json.loads(weather_path.read_text()) if weather_path.exists() else {}

    lines = [
        f"# SkyRelief Situation Report — {event_id}",
        "",
        "## Summary",
        brief.get("summary_en", ""),
        "",
        "## Hindi Summary",
        brief.get("summary_hi", ""),
        "",
        "## Flood Statistics",
        f"- Area: {flood.get('area_km2', 'N/A')} km²",
        f"- Coverage: {flood.get('pct_of_bbox', 'N/A')}% of region",
        f"- Unknown fraction: {flood.get('unknown_fraction', 0):.1%}",
        "",
        "## Rainfall",
        f"- Peak: {weather.get('peak_mm', 'N/A')} mm/day",
        f"- 3-day total: {weather.get('three_day_mm', 'N/A')} mm",
        f"- Anomaly: {'Yes' if weather.get('anomaly') else 'No'}",
        "",
        "## Priority Settlements",
    ]
    for p in prios[:10]:
        lines.append(
            f"{p['rank']}. **{p['settlement']}** — score {p['score']:.0f}/100  "
            f"| {p['recommended_action']}"
        )
        for r in p.get("reasons", [])[:2]:
            lines.append(f"   - {r}")
    lines += [
        "",
        "## WhatsApp Brief (English)",
        brief.get("whatsapp_brief_en", ""),
        "",
        "## WhatsApp Brief (Hindi)",
        brief.get("whatsapp_brief_hi", ""),
        "",
        "## Limitations",
    ]
    for lim in brief.get("limitations", []):
        lines.append(f"- {lim}")
    lines += ["", f"*Generated by SkyRelief v{API_VERSION}*"]

    md = "\n".join(lines)
    return Response(
        content=md,
        media_type="text/markdown",
        headers={"Content-Disposition": f"attachment; filename={event_id}_sitrep.md"},
    )

# ── Eval endpoint ─────────────────────────────────────────────────────────────

@app.get("/eval/{event_id}")
async def get_eval(event_id: str):
    """
    Return the last computed evaluation metrics for an event.
    Runs eval_iou.py if no cached result exists.
    Metrics are "Not measured" when reference mask is absent.
    """
    eval_cache = CACHE_DIR / event_id / "eval.json"
    eval_cache.parent.mkdir(parents=True, exist_ok=True)

    if not eval_cache.exists():
        # Run evaluation synchronously (fast — pure numpy)
        try:
            import importlib.util, sys as _sys
            spec = importlib.util.spec_from_file_location(
                "eval_iou",
                Path(__file__).parent / "scripts" / "eval_iou.py"
            )
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            result = mod.evaluate(event_id)
            eval_cache.write_text(json.dumps(result, indent=2))
        except Exception as exc:
            raise HTTPException(500, f"Eval failed: {exc}")

    return json.loads(eval_cache.read_text())


@app.get("/eval")
async def list_evals():
    """Run and return evaluation for all events."""
    results = []
    for event_dir in sorted(DATA_DIR.iterdir()):
        if (event_dir / "meta.json").exists():
            try:
                from fastapi.testclient import TestClient
                r = await get_eval(event_dir.name)
                results.append(r)
            except Exception:
                results.append({"event_id": event_dir.name, "error": "eval failed"})
    return results