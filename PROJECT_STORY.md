# Project Story — SkyRelief

## ?? Inspiration

During the July 2023 Beas River floods in Himachal Pradesh, relief teams struggled with a critical question: **"Where do we go first?"** Traditional disaster response relies on scattered WhatsApp messages, delayed satellite analysis, and manual prioritization. By the time help arrived, the most vulnerable settlements had been overlooked—not because they weren't affected, but because they couldn't communicate.

The devastating reality: **settlements with flooded roads and downed cell towers became invisible to relief operations.**

This hackathon challenge—combining satellite imagery with multimodal AI—presented the perfect opportunity to solve this problem. We envisioned a system that could:
- Automatically detect flooding from SAR imagery
- Cross-reference with ground reports
- **Find the settlements that can't call for help**
- Provide relief teams with a prioritized action plan in minutes

The "Silent Flooded" insight became our north star: if satellite shows flooding but there are zero reports, that settlement is likely cut off and needs urgent attention.

---

## ?? What We Learned

### Technical Deep Dives

**1. SAR Imagery is Hard (But Worth It)**
- Sentinel-1 C-band backscatter behaves counterintuitively
- Water appears dark (low backscatter), but urban areas have double-bounce effects
- We learned to use morphological operations (scipy) to clean speckle noise
- **Lesson:** Deterministic raster math (numpy) gives more trustworthy results than black-box ML for critical applications

**2. VLMs Are Powerful Context Validators**
- Qwen2-VL-72B can describe flood patterns in natural language
- It caught cases where our mask missed urban flooding due to double-bounce
- But it also hallucinated details not in the image
- **Lesson:** Use VLMs to *verify and explain*, not to generate ground truth. The mask stays deterministic.

**3. Geocoding in Disaster Zones is Messy**
- Reports say "Larji bridge" or "NH-3 near Mandi" — not lat/lon
- OpenStreetMap gazetteers helped, but many local landmarks aren't mapped
- **Lesson:** Fuzzy matching + LLM extraction (Llama 3.1) ? 80% success rate. Mark unknowns as "unverified" rather than dropping them.

**4. Bilingual NLP Requires Schema-Level Design**
- Hindi isn't just translated English — sentence structure differs
- We learned to generate both languages from structured data, not translate output
- **Lesson:** Pydantic schemas with summary_en + summary_hi fields from day one

### Process Learnings

- **Start with fixtures, not live data:** We generated synthetic Sentinel-1 GeoTIFFs first, then built the raster pipeline. This let us iterate fast without waiting for satellite passes.
- **SSE streaming is magical for UX:** Watching the agent trace in real-time makes users trust the system. They see it thinking.
- **Test with real disaster data early:** We validated with the 2022 Assam floods. Our algorithm would have ranked Nagaon #2 (it was severely hit IRL). That validation moment was huge.

---

## ??? How We Built It

### Phase 1: Data Pipeline (Days 1-2)
1. **Fixture Generation**
   - Created synthetic Sentinel-1-like GeoTIFFs with realistic flood signatures
   - Built reference masks for IoU validation
   - Scraped OSM data for settlements, roads, hospitals, bridges
   - Collected rainfall CSVs from Open-Meteo

2. **Raster Processing**
   - Implemented water detection: \fter_db - before_db < -16 dB\ threshold
   - Morphological closing to fill small gaps (scipy.ndimage)
   - Vectorization to GeoJSON (rasterio ? shapely)
   - **Result:** Deterministic flood masks with IoU > 0.99 vs reference

### Phase 2: Multimodal AI Integration (Days 3-4)
1. **VLM Verification**
   - Rendered RGB overlays: flood mask (blue) + before/after imagery
   - Sent to Qwen2-VL with prompt: "Describe flood extent, damage, and caveats"
   - Extracted observations as bullet points
   - **Critical rule:** VLM output goes to \limitations\ section, never overwrites mask

2. **LLM Report Extraction**
   - Parsed unstructured reports (tweets, news, WhatsApp forwards)
   - Llama 3.1 extracted: location, urgency, casualties, infrastructure damage
   - Geocoded place names against OSM gazetteer
   - Fuzzy-matched unknowns (e.g., "Larji" ? "Larji Hydropower Project")

3. **Bilingual Generation**
   - Prompt engineering for Hindi: used native sentence structures, not direct translation
   - Validation: Had a Hindi speaker review outputs (they were natural!)

### Phase 3: Prioritization Engine (Day 5)
1. **Exposure Calculation**
   - Buffered each settlement by 300m
   - Calculated flood coverage \% in buffer
   - Identified hospitals, schools, bridges within 500m
   - Checked if access roads intersected flood mask

2. **Report Fusion**
   - Summed urgency scores from geocoded reports within 900m of settlement
   - Flagged "silent flooded": flooding detected but zero reports nearby
   - **This became our killer feature**

3. **Scoring Formula**
   - Tuned weights iteratively (started at 50/30/20, settled on 40/20/15/10/10/5)
   - Validated against historical data: Nagaon (Assam 2022) ranked #2 ? correct!
   - **Transparency:** Every point is traceable to a data source

### Phase 4: Frontend & UX (Days 6-7)
1. **MapLibre Integration**
   - Rendered flood GeoJSON as blue polygon
   - Settlement markers color-coded by priority score
   - Toggle layers: roads (orange lines), bridges (orange dots), towers (green emoji)
   - **Silent-flooded settlements:** Purple markers with pulsing deck.gl rings

2. **SSE Streaming**
   - Backend sends \{"type": "step", "tool": "raster", "status": "done"}\ events
   - Frontend renders live trace timeline
   - Users see the agent "thinking" — builds trust

3. **Bilingual UI**
   - Toggle button: EN ? ???
   - WhatsApp brief with copy-paste formatting
   - Markdown export for email distribution

### Phase 5: Testing & Polish (Days 8-9)
1. **Pytest Suite**
   - 70+ tests covering all tools
   - Fixture validation (IoU, F1, precision, recall)
   - Edge cases: empty reports, missing rasters, malformed GeoJSON

2. **Playwright E2E**
   - Smoke tests: event picker, run button, map layers
   - Analysis flow: select event ? run ? verify priority list appears
   - Accessibility: keyboard navigation, ARIA labels, color contrast

3. **Performance Optimization**
   - Cached flood masks and exposures (JSON files)
   - Lazy-loaded MapLibre (reduced bundle size by 2MB)
   - Debounced layer toggles to prevent flicker

---

## ?? Challenges We Faced

### 1. **SAR Speckle Noise is Brutal**
**Problem:** Raw Sentinel-1 backscatter has salt-and-pepper noise everywhere.  
**Attempted:** Median filter ? blurred flood edges too much.  
**Solution:** Morphological closing with 3x3 structuring element. Preserves sharp boundaries while filling small gaps.  
**Takeaway:** Domain-specific operations (morphology) beat generic filters for SAR.

### 2. **VLM Hallucinations in Disaster Context**
**Problem:** Qwen-VL said "approximately 50 buildings submerged" when we only had 10 in our OSM data.  
**Attempted:** More specific prompts ("only describe what you see").  
**Solution:** Added verification step: cross-check VLM output against deterministic counts. If VLM gives numbers, mark them as "estimated (unverified)."  
**Takeaway:** Never trust LLM/VLM numbers in critical systems. Use them for qualitative insights only.

### 3. **Hindi Generation Sounded Like Google Translate**
**Problem:** Direct translation of English sitreps felt robotic in Hindi.  
**Attempted:** Different translation models ? still awkward phrasing.  
**Solution:** Switched to parallel generation: provide structured data (flood area, casualties) to LLM with separate Hindi prompt. Used native sentence structures ("???? ?? ?????????" not "flooded area in Hindi").  
**Takeaway:** Bilingual systems need cultural context, not just language swaps.

### 4. **Silent-Flooded Logic Was Tricky**
**Problem:** False positives when settlements had reports *just* outside the 900m radius.  
**Attempted:** Increase radius to 1500m ? caught too many noisy reports.  
**Solution:** Two-tier check: (1) flood coverage > 0% in 300m buffer, (2) zero reports in 900m. Added manual override flag for edge cases.  
**Takeaway:** Geo-spatial thresholds need iterative tuning with real data.

### 5. **MapLibre Layer Timing Issues**
**Problem:** Roads/bridges didn't show on first toggle because OSM fetch completed *after* layer creation.  
**Attempted:** Tried preloading in useEffect ? race conditions everywhere.  
**Solution:** Cleanup inside fetch callback: remove existing sources before re-adding. Added \sitrep\ to toggle dependencies so effect re-runs when data arrives.  
**Takeaway:** Async data in React requires careful dependency management.

### 6. **Windows Development Hell**
**Problem:** Rasterio (GDAL) doesn't work on native Windows.  
**Attempted:** Conda environments, OSGeo4W ? dependency conflicts galore.  
**Solution:** Ran entire API in WSL2. Fast file system mounting (\/mnt/c/...\) kept workflow smooth.  
**Takeaway:** Geospatial Python on Windows = use WSL or Docker. No exceptions.

---

## ?? What Makes SkyRelief Different

Most disaster response tools focus on **areas with reports**. We find **areas that can't report**.

- ? **Traditional:** "Where are people calling from?" ? Misses cut-off zones  
- ? **SkyRelief:** "Where does satellite show flooding but nobody is calling?" ? Finds invisible victims

This inversion—using *absence of reports* as a signal—is our core innovation. Combined with transparent scoring and bilingual output, it's a system relief teams can actually trust.

---

## ?? Future Vision

If we had more time (or win this hackathon ??), next steps:

1. **Landslide Mode:** NDVI change + DEM slope ? debris flow risk
2. **SMS Ingest:** Twilio webhook ? auto-extract reports from field teams
3. **NDMA Portal Integration:** Export sitrepoort in government-standard format
4. **Real-time Alerts:** WebSocket push when new Sentinel-1 data available
5. **Mobile App:** Offline-capable tool for relief workers in the field

---

## ?? Why This Matters

Every minute counts in disaster response. SkyRelief gives relief teams:
- ?? **Data-driven priorities** instead of gut feelings
- ??? **Live situational awareness** instead of scattered reports
- ?? **Proactive detection** of cut-off zones instead of waiting for SOS calls
- ?? **Bilingual output** so field teams in rural India can actually use it

This isn't just a hackathon project. It's a tool that could save lives.

---

**Built with ?? during 72 sleepless hours for IIT Mandi Multimodal AI Hackathon 2026.**
