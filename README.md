<div align="center">

# 🌊 SkyRelief

### AI-Powered Multimodal Disaster Response Intelligence System

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg)](https://fastapi.tiangolo.com)
[![Next.js 15](https://img.shields.io/badge/Next.js-15-black)](https://nextjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0-3178c6)](https://www.typescriptlang.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

**[Demo](#-demo-events) · [Quick Start](#-quick-start) · [Architecture](#-architecture) · [Docs](./docs)**

*Built for Multimodal AI Hackathon 2026 — IIT Mandi / KamandPrompt · Track: **Space***

</div>

---

## 🎯 The Problem

When floods strike, **time is life**. Emergency responders face critical challenges:

- **Information Overload:** Satellite imagery, ground reports, weather data, and maps arrive in silos
- **Where to Go First?** No systematic way to prioritize hundreds of affected settlements
- **Silent Communities:** Places cut off from communication can't report their crisis — but satellites can see them
- **Language Barriers:** Field workers need instructions in local languages, not technical jargon
- **Verification Crisis:** Misinformation spreads faster than relief — which reports are real?

**Real-world impact:** In the 2022 Assam floods, over 200,000 people were displaced. In 2023, Himachal Pradesh's monsoon disasters killed 300+ people. Response teams needed days to assess the full picture.

---

## 💡 The Solution

**SkyRelief** is an autonomous AI agent that **fuses multimodal data** to deliver actionable intelligence in minutes:

```
🛰️ Satellite Imagery + 📱 Ground Reports + 🌧️ Weather + 🗺️ Maps
                              ↓
            🤖 Multimodal AI Orchestrator
                              ↓
          📊 Ranked Action List + 📋 Situation Report
                              ↓
              🇮🇳 Hindi + English Field Briefs
```

**Key Innovation: "Silent Flooded" Detection** 🚨  
SkyRelief identifies settlements where satellites see flooding but *nobody has reported it* — likely because they're cut off. These get automatic priority boost and purple markers on the map.

---

## ✨ Features

### 🎯 Core Capabilities
- **🛰️ Deterministic Flood Detection** — Sentinel-1 SAR raster analysis with numpy (no ML black box)
- **🤖 VLM Verification** — Qwen2-VL-72B validates flood masks and flags caveats
- **🌐 Multimodal Fusion** — Cross-references satellite, reports, rainfall, and infrastructure
- **🎖️ Smart Prioritization** — 6-factor scoring: flood coverage, report urgency, silent settlements, facilities, road access, rainfall anomaly
- **🗺️ Geo-Intelligence** — Exposes hospitals, schools, bridges, and access roads from OpenStreetMap
- **📊 Source-Backed Reasoning** — Every claim links to satellite/report/sensor IDs for verification
- **🌍 Bilingual Output** — Generates WhatsApp-ready field briefs in English + Hindi
- **⚡ Real-Time SSE Streaming** — Live progress updates as the agent works

### 🔬 Technical Highlights
- **Deterministic Core:** Flood extent computed by raster math, not LLM hallucination
- **VLM as Verifier:** Vision model explains but never overwrites satellite-derived masks
- **Parallel Pipeline:** 9 tools run concurrently where possible
- **Cache-Smart:** Avoids reprocessing identical queries; handles live report injection
- **Test Coverage:** 70 passing tests including IoU validation vs reference masks

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Next.js Frontend                                 │
│            (MapLibre GL + SSE Client + Priority Dashboard)               │
└──────────────────────────────────┬──────────────────────────────────────┘
                                   │ SSE Stream
                                   ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                      FastAPI + Orchestrator Agent                        │
├─────────────────────────────────────────────────────────────────────────┤
│  Parallel Phase 1: Data Acquisition                                     │
│    1️⃣  raster.py      → Flood mask (numpy, deterministic)              │
│    3️⃣  geo.py         → Settlement exposure (shapely, geopandas)        │
│    4️⃣  weather.py     → Rainfall time series (CSV/Open-Meteo)           │
│    5️⃣  reports.py     → LLM extraction + gazetteer geocoding            │
├─────────────────────────────────────────────────────────────────────────┤
│  Phase 2: Verification & Fusion                                         │
│    2️⃣  vision.py      → VLM validates overlay (Qwen2-VL-72B)            │
│    6️⃣  fuse.py        → Cross-check reports vs mask                     │
├─────────────────────────────────────────────────────────────────────────┤
│  Phase 3: Scoring & Output                                              │
│    7️⃣  prioritize.py  → Deterministic 6-factor scoring                  │
│    8️⃣  brief.py       → LLM writes sitrep + WhatsApp brief              │
│    9️⃣  verify.py      → Drop unsourced claims (post-check)              │
└─────────────────────────────────────────────────────────────────────────┘
```

**Design Philosophy:**  
✅ **Flood extent = deterministic raster analysis**  
✅ **LLM/VLM = reasoning, explanation, translation**  
❌ **LLM never generates flood mask coordinates**

---

## 🚀 Quick Start

### Prerequisites
- **Backend:** Python 3.11+, WSL2 or Linux (Windows native: partial support)
- **Frontend:** Node.js 18+
- **API Keys:** OpenAI-compatible LLM endpoint (default: Nebius Studio)

### 1️⃣ Clone & Setup Environment

```bash
git clone https://github.com/yourusername/SkyRelief.git
cd SkyRelief

# Copy environment template
cp .env.example .env

# Edit .env and add:
# LLM_BASE_URL=https://api.studio.nebius.ai/v1
# LLM_API_KEY=your_api_key_here
# LLM_MODEL=meta-llama/Meta-Llama-3.1-70B-Instruct
# VLM_MODEL=Qwen/Qwen2-VL-72B-Instruct
```

### 2️⃣ Backend (FastAPI)

```bash
# Create virtual environment (in WSL/Linux)
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r api/requirements.txt

# Start API server
cd api
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Backend running at `http://localhost:8000` 🎉

### 3️⃣ Frontend (Next.js)

```bash
# In a new terminal
cd web
npm install

# Copy frontend env
cp .env.example .env.local
# Edit .env.local: NEXT_PUBLIC_API_URL=http://localhost:8000

# Start dev server
npm run dev
```

Frontend running at `http://localhost:3000` 🚀

### 4️⃣ Run Your First Analysis

1. Open `http://localhost:3000`
2. Select **Himachal Pradesh 2023** (hero event for IIT Mandi judges!)
3. Click **Analyze**
4. Watch the agent stream its reasoning in real-time
5. See ranked priorities, map overlay, and bilingual field brief

---

## 📊 Demo Events

| Event ID | Name | Location | Dates | Sensor | Flood Area |
|----------|------|----------|-------|--------|------------|
| `himachal_2023` | **Beas River Flood** | Mandi/Kullu, Himachal Pradesh | Jul 5–14, 2023 | Sentinel-1 | 509.8 km² |
| `assam_2022` | **Brahmaputra Flood** | Assam | Jun 10–20, 2022 | Sentinel-1 | 2,697 km² |

**Hero Event:** `himachal_2023` — Local disaster to IIT Mandi, devastating floods that isolated mountain communities.

---

## 🎖️ Priority Scoring Formula

Each settlement receives a score (0–100) based on 6 weighted factors:

| Factor | Weight | Source Tool | Description |
|--------|--------|-------------|-------------|
| **Flood Coverage** | 40% | `raster.py` | % of 300m buffer inundated |
| **Report Urgency** | 20% | `reports.py` | Normalized urgency sum (0–3 scale) |
| **Silent Flooded** 🚨 | 15% | `fuse.py` | Flooding detected but zero reports |
| **Exposed Facilities** | 10% | `geo.py` | Hospitals, schools, bridges affected |
| **Road Access Cut** | 10% | `geo.py` | Main road flooded |
| **Rainfall Anomaly** | 5% | `weather.py` | Exceptional 24h/72h rainfall |

**Formula:**
```python
score = 40 * min(1, flood_fraction)
      + 20 * min(1, urgency_sum / 3)
      + 15 * (1 if silent_flooded else 0)
      + 10 * min(1, facilities / 2)
      + 10 * (1 if road_flooded else 0)
      +  5 * (1 if rain_anomaly else 0)
```

**Tie-break:** Population (from OSM) → Alphabetical

See [docs/PRIORITY_SCORING.md](./docs/PRIORITY_SCORING.md) for detailed rationale.

---

## 🔥 The "Silent Flooded" Innovation

**Most important signal in the system.**

A settlement is marked `silent_flooded=True` when:
1. **Satellite sees flooding** (flood_fraction > 0 in 300m buffer)
2. **Zero ground reports** within 900m radius
3. **Status: confirmed or unverified**

**Why this matters:**  
Cut-off communities can't call for help. Satellite becomes their voice. These settlements get:
- ✅ **+15 point boost** in priority score
- 🟣 **Purple markers** on map
- 🚨 **Auto-flagged for immediate assessment**

**Real-world validation:**  
After the 2023 Himachal floods, several villages in Kullu district were unreachable for 48 hours. Helicopter crews confirmed severe damage despite no initial reports — exactly the "silent flooded" scenario SkyRelief detects.

---

## 🧪 Validation Results

**IoU (Intersection over Union) vs Reference Masks:**

| Event | IoU | F1 Score | Precision | Recall | Flood Area |
|-------|-----|----------|-----------|--------|------------|
| `himachal_2023` | **0.9998** | 0.9999 | 0.9999 | 0.9999 | 509.8 km² |
| `assam_2022` | **0.9999** | 0.9999 | 0.9999 | 0.9999 | 2,697 km² |

**Note on Eval Honesty:**  
The reference masks (`ref_mask.tif`) are **synthetically generated** to match fixture rasters using `scripts/generate_fixtures.py`. This means IoU near 1.0 is expected by design — it validates the pipeline, not real-world accuracy.

**For real-world validation:**  
Replace `ref_mask.tif` with:
- 🇪🇺 Copernicus Emergency Management Service activation products
- 📊 Sen1Floods11 hand-labeled chips
- 🗺️ UNOSAT flood extent polygons

**Run evaluation yourself:**
```bash
python api/scripts/eval_iou.py
```

---

## 🛠️ Tech Stack

### Backend
- **Framework:** FastAPI 0.111, uvicorn, sse-starlette
- **Data Models:** Pydantic v2
- **Geospatial:** rasterio, numpy, scipy, scikit-image, shapely, geopandas, pyproj
- **Vision:** PIL (Pillow)
- **LLM/VLM:** OpenAI-compatible client (default: Nebius Studio)
- **Testing:** pytest (70 passing tests)

### Frontend
- **Framework:** Next.js 15 (App Router)
- **Language:** TypeScript 5.0
- **Styling:** Tailwind CSS
- **Mapping:** MapLibre GL JS
- **State:** React hooks + SSE
- **Testing:** Playwright (E2E)

### Infrastructure
- **Backend Deploy:** Render, Railway, or any Docker host
- **Frontend Deploy:** Vercel
- **Storage:** File-based (GeoTIFFs, GeoJSON, CSV)

---

## 📁 Repository Structure

```
SkyRelief/
├── api/                          # FastAPI backend
│   ├── main.py                   # API routes + SSE endpoints
│   ├── llm.py                    # LLM/VLM client wrapper
│   ├── schemas.py                # Pydantic v2 data models
│   ├── config.py                 # All tunable constants
│   ├── agent/
│   │   ├── orchestrator.py       # Multi-tool agent loop
│   │   └── tools/
│   │       ├── raster.py         # Flood mask computation
│   │       ├── vision.py         # VLM verification
│   │       ├── geo.py            # Settlement exposure analysis
│   │       ├── weather.py        # Rainfall time series
│   │       ├── reports.py        # Report extraction + geocoding
│   │       ├── fuse.py           # Cross-validation
│   │       ├── prioritize.py     # Scoring algorithm
│   │       ├── brief.py          # Sitrep generation
│   │       └── verify.py         # Source verification
│   ├── scripts/
│   │   ├── generate_fixtures.py  # Create synthetic test data
│   │   ├── eval_iou.py           # IoU evaluation
│   │   ├── make_overlay.py       # PNG thumbnail generator
│   │   └── fetch_event.py        # Live data fetcher
│   └── tests/
│       ├── test_api.py
│       ├── test_tools_phase4.py
│       ├── test_tools_phase5.py
│       └── test_tools_phase6.py
├── web/                          # Next.js frontend
│   ├── app/
│   │   ├── page.tsx              # Main UI
│   │   └── types.ts              # TypeScript types
│   └── components/
│       ├── EventPicker.tsx
│       ├── MapView.tsx           # MapLibre GL flood overlay
│       ├── TraceTimeline.tsx     # Real-time agent trace
│       ├── PriorityList.tsx      # Ranked settlements
│       ├── WhatsAppBrief.tsx     # Copy-to-WhatsApp button
│       ├── ReportPanel.tsx       # Ground report viewer
│       └── LimitationsPanel.tsx
├── data/events/
│   ├── himachal_2023/            # Before/after TIFFs, OSM, rainfall
│   └── assam_2022/
├── cache/                        # Tool output cache
├── docs/
│   └── PRIORITY_SCORING.md       # Detailed scoring docs
├── .env.example
├── LICENSE
├── CONTRIBUTING.md
└── README.md
```

---

## 📖 API Reference

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/events` | List available demo events |
| `POST` | `/analyze` | Run agent analysis (SSE stream) |
| `GET` | `/layers/{event_id}/flood_mask.png` | Flood overlay image |
| `GET` | `/layers/{event_id}/settlements.geojson` | Settlement markers |
| `GET` | `/export/{event_id}.md` | Download markdown sitrep |

### SSE Stream Format

```json
{"type": "step", "tool": "raster", "status": "running", "detail": "Analyzing SAR change..."}
{"type": "step", "tool": "raster", "status": "done", "detail": "45.2 km² flooded"}
{"type": "sitrep", "data": { ...Sitrep object... }}
{"type": "complete"}
```

### Inject Live Reports

```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": "himachal_2023",
    "extra_reports": [
      "Larji bridge collapsed, 300 families stranded",
      "Kullu hospital flooded, patients evacuated"
    ]
  }'
```

---

## 🧪 Running Tests

```bash
# Activate virtual environment
source .venv/bin/activate

# Run pytest with verbose output
cd api
python -m pytest tests/ -v

# Expected output:
# ===== 70 passed in 12.34s =====
```

**Test Coverage:**
- ✅ Raster flood detection (SAR + Sentinel-2)
- ✅ Geo exposure calculations
- ✅ Weather rainfall parsing
- ✅ Report extraction + geocoding
- ✅ Fuse logic (confirmed/contradicted/unverified)
- ✅ Priority scoring with all 6 factors
- ✅ IoU evaluation vs reference masks

---

## 🚧 Limitations (Honest Assessment)

We believe in transparent AI. Here's what SkyRelief **cannot** do:

### Technical Limitations
- ❌ **Urban Flooding:** SAR C-band double-bounce effect can miss flooding in dense cities
- ❌ **Sub-10m Resolution:** Sentinel-1 pixel size ~10m; narrow streams/canals may be missed
- ❌ **Cloud Cover:** Optical (Sentinel-2) mode requires cloud-free imagery
- ❌ **Synthetic Validation:** Reference masks are generated from fixtures, not independent ground truth

### Data Limitations
- ⚠️ **Unverified Reports:** Ground reports marked with source URLs but not independently verified
- ⚠️ **OSM Completeness:** Rural facility data (hospitals, schools) may be incomplete
- ⚠️ **Geocoding:** Unknown place names show as "unverified" location
- ⚠️ **Historical Events:** Demo events use pre-downloaded data; live fetching requires API keys

### Operational Limitations
- 🔧 **API Key Required:** VLM verification needs Nebius Studio or OpenAI API key
- 🔧 **Linux Preferred:** Full pipeline tested on Ubuntu/WSL2; Windows native has rasterio issues
- 🔧 **No SMS Ingest:** Reports must be pasted manually (roadmap item)

**What we're doing about it:**
- Planning urban flood mode with Sentinel-2 + high-res Planet imagery
- Roadmap: Sen1Floods11 validation for honest IoU
- Roadmap: Twilio SMS → auto-extract reports

---

## 🗺️ Roadmap

### Phase 1: Core Disaster Types ✅
- [x] Flood detection (SAR + optical)
- [x] Settlement exposure analysis
- [x] Multimodal fusion
- [x] Priority scoring
- [x] Bilingual briefs (EN + HI)

### Phase 2: Enhanced Intelligence 🚧
- [ ] **Landslide Mode:** NDVI change + DEM slope → debris flow risk
- [ ] **Cyclone Mode:** Wind track overlay + storm surge prediction
- [ ] **Urban Flood Mode:** High-res imagery + building footprints
- [ ] **Wildfire Mode:** VIIRS thermal + NDVI burn scar

### Phase 3: Real-World Integration 📋
- [ ] **SMS Ingest:** Twilio → auto-extract → fuse pipeline
- [ ] **District Control Room API:** Export to NDMA/SDMA formats
- [ ] **WhatsApp Bot:** Direct query interface for field workers
- [ ] **Offline Mode:** Preload models for no-internet deployment

### Phase 4: Advanced Validation 🔬
- [ ] **Sen1Floods11 Eval:** Replace synthetic masks with hand-labeled chips
- [ ] **Copernicus EMS Comparison:** Benchmark vs official activation products
- [ ] **Field Validation:** Partner with disaster response NGOs for ground truth

### Phase 5: Scale & Performance ⚡
- [ ] **GPU Acceleration:** CUDA kernels for raster ops
- [ ] **Distributed Processing:** Celery workers for large AOIs
- [ ] **Incremental Updates:** Stream processing for ongoing events
- [ ] **Mobile App:** React Native field data collection

---

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTING.md](./CONTRIBUTING.md) for:
- Development setup
- Code style guidelines (Black, isort, mypy)
- Testing requirements
- PR process

**Quick Contribution Ideas:**
- 🐛 Add test cases for edge cases
- 📚 Improve documentation
- 🌐 Add new language translations
- 🗺️ Contribute OSM data for Indian districts
- 🧪 Validate with real Copernicus EMS products

---

## 📜 License

MIT License — see [LICENSE](./LICENSE)

Copyright (c) 2026 SkyRelief Contributors

---

## 🙏 Acknowledgments

- **Satellite Data:** Copernicus Sentinel-1/2 (ESA)
- **Maps:** OpenStreetMap contributors
- **LLM/VLM:** Meta Llama 3.1, Alibaba Qwen2-VL (via Nebius Studio)
- **Inspiration:** Real-world flood response challenges in India
- **Hackathon:** Multimodal AI Hackathon 2026 — IIT Mandi / KamandPrompt

---

## 📬 Contact

- **Issues:** [GitHub Issues](https://github.com/yourusername/SkyRelief/issues)
- **Discussions:** [GitHub Discussions](https://github.com/yourusername/SkyRelief/discussions)
- **Email:** your.email@example.com

---

<div align="center">

**Built with ❤️ for humanitarian crisis response**

*When disaster strikes, every minute counts. SkyRelief gives responders the intelligence to save lives.*

[⭐ Star this repo](https://github.com/yourusername/SkyRelief) if you believe AI can help disaster response!

</div>
