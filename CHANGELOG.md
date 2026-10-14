# Changelog

All notable changes to SkyRelief will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- Landslide detection mode
- Cyclone/storm surge mode
- SMS ingest via Twilio
- WhatsApp bot interface
- Sen1Floods11 validation

---

## [1.0.0] - 2026-01-15

### 🎉 Initial Release

**Multimodal AI Hackathon 2026 Submission**

#### ✨ Features
- **Flood Detection:** Sentinel-1 SAR raster analysis with deterministic numpy computation
- **VLM Verification:** Qwen2-VL-72B validates flood masks and provides explanations
- **Settlement Exposure:** 300m buffer analysis with facility detection (hospitals, schools, bridges)
- **Silent Flooded Detection:** Identifies cut-off communities via satellite-only signal
- **6-Factor Scoring:** Deterministic priority algorithm (40% flood coverage, 20% report urgency, 15% silent flooded, 10% facilities, 10% road access, 5% rainfall)
- **Multimodal Fusion:** Cross-validates satellite, ground reports, rainfall, and OSM data
- **Bilingual Briefs:** Auto-generates situation reports in English + Hindi
- **Real-Time SSE:** Live agent progress streaming to frontend
- **Interactive Map:** MapLibre GL with flood overlay and priority markers
- **Source Verification:** Every claim links to satellite/report/sensor IDs

#### 🗺️ Demo Events
- `himachal_2023`: Beas River Flood (Mandi/Kullu, Jul 2023) — 509.8 km²
- `assam_2022`: Brahmaputra Flood (Assam, Jun 2022) — 2,697 km²

#### 🛠️ Tech Stack
- **Backend:** FastAPI 0.111, Python 3.11+, Pydantic v2
- **Geospatial:** rasterio, numpy, geopandas, shapely
- **AI:** OpenAI-compatible client (Nebius Studio)
- **Frontend:** Next.js 15, TypeScript, Tailwind CSS, MapLibre GL
- **Testing:** pytest (70 tests), Playwright

#### 📚 Documentation
- Comprehensive README with architecture diagram
- PRIORITY_SCORING.md: Deep dive into scoring algorithm
- ARCHITECTURE.md: System design and component breakdown
- CONTRIBUTING.md: Development guidelines

#### 🧪 Validation
- IoU vs synthetic reference masks: 0.9998 (himachal), 0.9999 (assam)
- 70 passing tests covering all tools
- E2E tests for full analysis workflow

#### 🚀 Deployment
- Vercel-ready frontend
- Docker-ready backend
- Environment variable configuration
- Cache-based optimization

---

## Version History

### How to Read This Changelog

**Categories:**
- `✨ Added` - New features
- `🐛 Fixed` - Bug fixes
- `♻️ Changed` - Changes in existing functionality
- `🗑️ Deprecated` - Soon-to-be removed features
- `❌ Removed` - Removed features
- `🔒 Security` - Vulnerability fixes
- `📚 Documentation` - Documentation changes
- `⚡ Performance` - Performance improvements

**Version Format:** `MAJOR.MINOR.PATCH`
- **MAJOR:** Breaking changes
- **MINOR:** New features (backward-compatible)
- **PATCH:** Bug fixes (backward-compatible)

---

## [Unreleased] - Future Roadmap

### Phase 2: Enhanced Intelligence 🔮
- [ ] Landslide mode: NDVI change + DEM slope analysis
- [ ] Cyclone mode: Wind track overlay + storm surge
- [ ] Urban flood mode: High-res imagery + building footprints
- [ ] Wildfire mode: VIIRS thermal + NDVI burn scar

### Phase 3: Real-World Integration 🌍
- [ ] SMS ingest: Twilio → auto-extract → fuse
- [ ] District control room API: NDMA/SDMA export formats
- [ ] WhatsApp bot: Direct query interface
- [ ] Offline mode: Preload models for no-internet deployment

### Phase 4: Advanced Validation 🔬
- [ ] Sen1Floods11 evaluation with hand-labeled chips
- [ ] Copernicus EMS comparison benchmark
- [ ] Field validation with disaster response NGOs

### Phase 5: Scale & Performance ⚡
- [ ] GPU acceleration for raster operations
- [ ] Celery workers for large AOIs
- [ ] Incremental updates for ongoing events
- [ ] React Native mobile app

---

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md) for how to propose changes to this project.

---

## Links

- **Repository:** https://github.com/yourusername/SkyRelief
- **Issues:** https://github.com/yourusername/SkyRelief/issues
- **Discussions:** https://github.com/yourusername/SkyRelief/discussions
