# SkyRelief — Multimodal Disaster Response Agent

> *Give SkyRelief a flood-hit region and date. It compares before/after satellite imagery, fuses it with ground reports, rainfall data and map data, finds **where help is needed first**, and outputs a situation report + field brief in English and Hindi.*

Hackathon: Multimodal AI Hackathon 2026 (IIT Mandi / KamandPrompt) · Track: **Space**

---

## Quick Start

### Backend (API)

```bash
# From repo root in WSL or Linux
cd SkyRelief
source .venv/bin/activate        # or: ~/skyrelief_venv/bin/activate

# Copy env and add your LLM API key
cp .env.example .env
# Edit .env: set LLM_API_KEY, LLM_MODEL, VLM_MODEL

# Start the API
cd api
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend (Web)

```bash
cd web
npm install
npm run dev        # http://localhost:3000
```

---

## Architecture

```
Next.js + MapLibre  --SSE-->  FastAPI  -->  Orchestrator
                                               |
              ┌────────────────────────────────┴────────────────────────┐
              │                                                          │
         [parallel]                                                      │
    1. raster.py  flood mask (deterministic numpy)                       │
    3. geo.py     settlement exposure (shapely)                          │
    4. weather.py rainfall series (CSV / Open-Meteo)                    │
    5. reports.py LLM extraction + gazetteer geocoding                   │
              │                                                          │
    2. vision.py  VLM verifies mask overlay (Qwen VL)                   │
    6. fuse.py    cross-check reports vs mask                            │
    7. prioritize.py  score & rank settlements                           │
    8. brief.py   LLM writes sitrep + WhatsApp brief (EN + HI)          │
    9. verify.py  drop unsourced claims                                  │
              └──────────────────────────────────────────────────────────┘
```

**Hard rule:** Flood extent comes from deterministic raster math (numpy). The VLM only verifies, explains and flags caveats. It never overwrites the mask.

---

## Priority Score Formula

Weights are defined in `api/config.py` and sum to 100:

| Component | Weight | Source |
|---|---|---|
| Flood fraction of 300 m buffer | **40** | `raster.py` |
| Normalised report urgency sum | **20** | `reports.py` |
| Silent flooded (no reports despite flooding) | **15** | `fuse.py` |
| Exposed facilities (hospitals, schools, bridges) | **10** | `geo.py` |
| Access road flooded | **10** | `geo.py` |
| Rainfall anomaly flag | **5** | `weather.py` |

Tie-break: population (from OSM) → alphabetical.

---

## The "Silent Flooded" Insight

The most important signal in the system. A settlement is marked `silent_flooded=True` when:
- The flood mask covers > 0% of its 300 m buffer **AND**
- There are zero confirmed/unverified ground reports within 900 m

This means satellite sees flooding but nobody has reported it — likely because communications are down. These settlements get a **+15 point boost** in the priority score and are highlighted in purple on the map.

---

## Eval Results

IoU vs synthetic reference mask (generated to match fixture rasters exactly):

| Event | IoU | F1 | Flood Area |
|---|---|---|---|
| himachal_2023 | **0.9998** | 0.9999 | 509.8 km² |
| assam_2022 | **0.9999** | 0.9999 | 2697.0 km² |

> **Note:** The reference mask (`ref_mask.tif`) is synthetically generated to match the flood extent baked into the fixture rasters — so IoU near 1.0 is expected by design. For real-world validation, replace `ref_mask.tif` with a Copernicus EMS activation product or a Sen1Floods11 hand-labelled chip.

Run eval yourself:
```bash
python api/scripts/eval_iou.py
```

---

## Demo Events

| ID | Name | Sensor | Dates |
|---|---|---|---|
| `himachal_2023` | Beas River Flood — Mandi/Kullu, Himachal Pradesh | Sentinel-1 | Jul 5–14 2023 |
| `assam_2022` | Brahmaputra Flood — Assam | Sentinel-1 | Jun 10–20 2022 |

The Himachal event is the **hero event** — local to IIT Mandi judges.

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Health check |
| `GET` | `/events` | List demo events |
| `POST` | `/analyze` | Run agent → SSE stream |
| `GET` | `/layers/{event_id}/{layer}` | PNG or GeoJSON map layer |
| `GET` | `/export/{event_id}.md` | Download markdown sitrep |

**SSE stream format:**
```json
{"type": "step", "tool": "raster", "status": "done", "detail": "45.2 km2 flooded"}
{"type": "sitrep", "data": { ...Sitrep... }}
```

**Live report paste:**
```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"event_id": "himachal_2023", "extra_reports": ["Larji bridge washed out, 300 families stranded"]}'
```

---

## Environment Variables

```
LLM_BASE_URL=https://api.studio.nebius.ai/v1
LLM_API_KEY=your_key_here
LLM_MODEL=meta-llama/Meta-Llama-3.1-70B-Instruct
VLM_MODEL=Qwen/Qwen2-VL-72B-Instruct
LIVE_DATA=0
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Set `LIVE_DATA=1` to enable live Sentinel/Open-Meteo/Overpass fetching. Requires `pystac-client` and `planetary-computer`.

---

## Stack

- **Backend:** Python 3.11+, FastAPI, Pydantic v2, uvicorn, sse-starlette
- **Geo:** rasterio, numpy, scipy, scikit-image, shapely, geopandas, pyproj
- **LLM/VLM:** OpenAI-compatible client (`llm.py`), default Nebius Token Factory (Qwen VL)
- **Frontend:** Next.js 15, TypeScript, Tailwind CSS, MapLibre GL
- **Deploy:** Vercel (web) + Render/Railway (api)

---

## Running Tests

```bash
# In WSL or Linux with venv active
python -m pytest api/tests/ -v
# Expected: 70 passed, 0 failed
```

---

## Repo Structure

```
SkyRelief/
  api/
    main.py              FastAPI app
    llm.py               LLM/VLM client (OpenAI-compatible)
    schemas.py           Pydantic v2 schemas
    config.py            All tunable constants
    agent/
      orchestrator.py    Agent loop + SSE generator
      tools/
        raster.py        Flood mask computation (SAR/S2)
        vision.py        VLM mask verification
        geo.py           Settlement exposure
        weather.py       Rainfall analysis
        reports.py       LLM extraction + geocoding
        fuse.py          Report vs mask cross-check
        prioritize.py    Deterministic scoring
        brief.py         Sitrep + WhatsApp brief writer
        verify.py        Source verification
    scripts/
      generate_fixtures.py  Create synthetic rasters
      eval_iou.py           IoU evaluation
      make_overlay.py       Render PNG thumbnails
      fetch_event.py        Live data fetch (LIVE_DATA=1)
    tests/
  data/events/
    himachal_2023/       before.tif, after.tif, ref_mask.tif,
                         meta.json, rainfall.csv, osm.geojson, reports.json
    assam_2022/          same structure
  web/
    app/
      page.tsx           Main UI
      types.ts           Shared TypeScript types
    components/
      EventPicker.tsx
      MapView.tsx        MapLibre GL with flood layer + settlement markers
      TraceTimeline.tsx  Live agent trace
      PriorityList.tsx   Ranked settlements with silent-flood badge
      WhatsAppBrief.tsx  Copy-to-WhatsApp button
      ReportPanel.tsx    Ground report list with status badges
      LimitationsPanel.tsx
  .env.example
  README.md
```

---

## Limitations (Honest)

- SAR C-band (Sentinel-1) can miss urban flooding due to double-bounce effect
- Flood mask resolution ~10 m; sub-pixel inundation not captured
- Ground reports are unverified (marked with source URLs, never fabricated numbers)
- Synthetic fixtures mean IoU near 1.0; real-world IoU typically 0.5–0.8
- VLM visual verification requires API key; offline mode uses a conservative stub
- Geocoding relies on fixture gazetteer; unknown place names show as `unverified`

---

## Roadmap

- **Landslide mode:** NDVI change + DEM slope → debris flow risk scoring
- **Cyclone mode:** wind track overlay + storm surge prediction
- **SMS ingest:** Receive reports via Twilio SMS → auto-extract + fuse
- **District control room integration:** Export sitrep to NDMA portal format
- **Sen1Floods11 validation:** Swap fixture masks for hand-labelled chips for honest IoU

---

*Built for Multimodal AI Hackathon 2026 — IIT Mandi / KamandPrompt*