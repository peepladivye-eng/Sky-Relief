# SkyRelief Tech Stack

## Frontend

### Core Framework
- **Next.js 15.3** (React 18.3)
  - App Router architecture
  - Server-side rendering disabled (client-only app)
  - TypeScript strict mode

### Mapping & Visualization
- **MapLibre GL JS 4.7** — open-source map renderer
  - Raster tile base layer (OpenStreetMap)
  - GeoJSON vector overlays (flood polygons, settlements)
  - Custom circle/symbol layers with data-driven styling
  
- **deck.gl 9.4** — WebGL-powered geospatial visualization
  - `@deck.gl/mapbox` for MapLibre integration
  - `ScatterplotLayer` for animated pulsing rings (silent-flooded villages)
  - GPU-accelerated rendering for smooth 60fps animations

### Styling
- **Tailwind CSS 3.4** — utility-first CSS framework
  - Dark theme (`bg-gray-950` base, `gray-900` surfaces)
  - Custom color scale for priority levels
  - Responsive breakpoints (mobile-first)

### HTTP & Streaming
- **Fetch API** (native) — SSE (Server-Sent Events) for real-time agent progress
  - Manual `ReadableStream` parsing (no external SSE library)
  - Reconnection logic not implemented (single-run analysis)

### Testing
- **Playwright 1.49** — end-to-end browser automation
  - Chromium + Firefox cross-browser tests
  - `@axe-core/playwright` for WCAG AA accessibility checks
  - Smoke tests, analysis flow, keyboard navigation

### Dev Tools
- **ESLint** — Next.js recommended config
- **TypeScript 5.7** — strict type checking
- **PostCSS + Autoprefixer** — CSS processing

---

## Backend

### Core Framework
- **FastAPI 0.115+** — async Python web framework
  - Uvicorn ASGI server
  - Pydantic v2 for schema validation
  - SSE streaming via `EventSourceResponse`

### Geospatial Processing
- **rasterio** — read/write GeoTIFF, raster algebra
- **shapely 2.0** — polygon operations, buffering, intersection
- **pyproj** — CRS transformations (WGS-84 ↔ UTM)
- **scipy** — morphological filters (binary_erosion, binary_dilation)
- **numpy** — raster mask generation, array ops

### AI/LLM
- **httpx** — async HTTP client for OpenAI-compatible APIs
  - Supports: OpenAI, Groq, Together AI, Nebius, Ollama
  - Retry logic for JSON parse failures
  - Base64 image encoding for vision models

### Data Handling
- **pandas** — CSV parsing (rainfall time series)
- **json** (stdlib) — fixture loading, report extraction

### Testing
- **pytest** — unit + integration tests
  - 70 tests (all passing in WSL environment)
  - Fixtures for deterministic raster generation
  - Cache-based mocking (no external API calls in tests)

---

## Data Formats

### Input Data (per event)
- **Rasters**: GeoTIFF (float32, single-band)
  - `before.tif`, `after.tif` — Sentinel SAR or optical
  - `ref_mask.tif` — ground truth flood mask (for eval)
- **Vector**: GeoJSON (WGS-84)
  - `osm.geojson` — settlements, hospitals, schools, roads, bridges
- **Tabular**: CSV
  - `rainfall.csv` — daily time series (14+ days)
- **Reports**: JSON
  - `reports.json` — curated news snippets with source URLs
- **Metadata**: JSON
  - `meta.json` — bbox, dates, sensor, optional thresholds

### Output Data
- **Sitrep JSON** — complete analysis result
  - Flood stats (area, polygons)
  - VisionCheck (plausibility, confidence)
  - Weather (peak, anomaly)
  - Reports (extracted + geocoded)
  - Exposures (per-settlement flood fraction)
  - Priorities (ranked with reasons + sources)
  - Briefs (EN/HI summaries, WhatsApp format)

---

## Deployment (Not Included)

This is a **hackathon demo** setup:
- Backend: manual `uvicorn` start (no Docker, no CI/CD)
- Frontend: `npm run dev` (no static export, no CDN)
- Data: local filesystem (`data/events/`, `cache/`)

For production:
- Backend: containerize with gunicorn/uvicorn workers, deploy to cloud VM/K8s
- Frontend: `next build` + static hosting (Vercel, Netlify) or Node server
- Data: move to object storage (S3/GCS) + PostGIS for vector queries
- Auth: add API key middleware (not implemented)
- Monitoring: OpenTelemetry traces, structured logs

---

## Confirmed Design Decisions

### Why deck.gl?
- **MapLibre native circles** cannot animate smoothly (require map re-render per frame)
- **deck.gl ScatterplotLayer** uses WebGL shaders → 60fps pulsing rings with zero jank
- **Trade-off**: adds 500KB gzipped to bundle, but required for spec's "dashed pulsing ring" UX

### Why MapLibre over Mapbox GL?
- **Open-source license** (BSD) vs. proprietary Mapbox GL JS v2+
- **No API key required** for self-hosted raster tiles
- **API-compatible** with Mapbox GL plugins (deck.gl works seamlessly)

### Why SSE over WebSockets?
- **Simpler protocol** — HTTP GET with `text/event-stream`, no handshake
- **One-way data flow** — agent → frontend (no user interrupts mid-analysis)
- **Automatic reconnect** in browsers (though not leveraged here)

### Why No State Management Library?
- **React useState** sufficient for single-session analysis flow
- **No multi-user state**, no optimistic updates, no time-travel debugging
- Avoids Redux/Zustand complexity

### Why TypeScript Strict Mode?
- **Catches undefined/null bugs** at compile time (critical for nested geospatial objects)
- **Self-documenting** API types (no separate OpenAPI spec needed)
- **Refactor-safe** (renaming fields updates all call sites)

---

## Known Limitations

1. **No Progressive Web App (PWA)** — offline mode not supported
2. **No real-time collaboration** — single-user session only
3. **No undo/redo** — analysis is append-only
4. **No auth** — open API (ok for internal demo, not production)
5. **No map tile caching** — every page load fetches OSM tiles fresh
6. **Playwright E2E mocks API** — full integration tests require running backend
7. **deck.gl animation not paused** — runs even when map out of view (minor perf hit)

---

## Future Enhancements (Out of Scope)

- **3D terrain visualization** (Mapbox/Cesium)
- **Multi-event comparison** (side-by-side maps)
- **Export to PDF/KML** (print-ready reports)
- **Mobile app** (React Native + offline sync)
- **Real-time satellite feed** (WebSocket updates from processing pipeline)
