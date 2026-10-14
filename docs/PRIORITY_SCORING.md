# Priority Scoring Algorithm — Deep Dive

## Overview

SkyRelief's priority scoring system combines **6 weighted factors** to rank settlements by urgency. The score determines which communities get help first when disaster response resources are limited.

**Design Philosophy:**
- ✅ **Deterministic:** Same inputs always produce same scores (no ML randomness)
- ✅ **Transparent:** Every score links to source data (satellite, reports, sensors)
- ✅ **Tunable:** Weights defined in `config.py` can be adjusted per disaster type
- ✅ **Explainable:** Each settlement gets human-readable "reasons" list

---

## The Formula

```python
score = W_FLOOD_FRACTION   * min(1, flood_fraction)
      + W_REPORT_URGENCY   * min(1, urgency_sum / 3)
      + W_SILENT_FLOODED   * (1 if silent_flooded else 0)
      + W_FACILITIES       * min(1, num_exposed_facilities / 2)
      + W_ROAD_CUT         * (1 if road_flooded else 0)
      + W_RAIN_ANOMALY     * (1 if rain_anomaly else 0)
```

**Constraints:**
- Weights sum to **100** (enforced by assertion in `config.py`)
- Each component normalized to [0, 1] then multiplied by weight
- Final score: **0–100 scale**

---

## Factor Breakdown

### 1️⃣ Flood Fraction (Weight: 40%)

**What it measures:** Percentage of the settlement's 300m buffer that is flooded.

**Source:** `raster.py` — Deterministic raster analysis of Sentinel-1 SAR or Sentinel-2 NDWI change.

**Calculation:**
```python
# In geo.py
buffer = settlement_point.buffer(300)  # 300m radius
flood_pixels = mask[buffer_pixels] == 1
flood_fraction = flood_pixels.sum() / buffer_pixels.size

# In prioritize.py
c_flood = 40 * min(1.0, flood_fraction)
```

**Rationale:**
- Direct physical hazard indicator
- Highest weight (40%) because satellite data is most reliable
- Linear scaling: 50% flooded → 20 points, 100% flooded → 40 points

**Edge Cases:**
- `flood_fraction = 0`: Settlement not directly flooded but may have nearby reports → other factors apply
- `flood_fraction > 1`: Impossible due to normalization

**Example:**
```
Settlement: Larji Village
Buffer area: 282,743 m²
Flooded pixels: 142,000 m² → flood_fraction = 0.50
Score contribution: 40 * 0.50 = 20 points
```

---

### 2️⃣ Report Urgency (Weight: 20%)

**What it measures:** Normalized sum of urgency scores from ground reports within 900m.

**Source:** `reports.py` — LLM extracts urgency (0–3 scale) from text reports:
- **0:** Informational only
- **1:** Assistance needed (non-urgent)
- **2:** Urgent assistance required
- **3:** Life-threatening emergency

**Calculation:**
```python
# In prioritize.py
nearby_reports = [r for r in reports 
                  if haversine(settlement, r) < 900m
                  and r.status in ("confirmed", "unverified")]
urgency_sum = sum(r.urgency for r in nearby_reports)
c_urgency = 20 * min(1.0, urgency_sum / 3.0)
```

**Rationale:**
- Ground reports capture human distress satellite can't see
- Divided by 3 so a single "life-threatening" report → 20 points
- Multiple moderate reports can also max out at 20 points

**Edge Cases:**
- No reports within 900m → 0 points (may trigger "silent flooded" bonus)
- Multiple overlapping reports → urgency scores sum (capped at 3 → 20 points)

**Example:**
```
Settlement: Kullu Town
Nearby reports:
  - "Hospital flooded, patients need evacuation" (urgency=3)
  - "Food supplies running low" (urgency=1)
urgency_sum = 4 → capped at 3
Score contribution: 20 * min(1.0, 4/3) = 20 points (maxed out)
```

---

### 3️⃣ Silent Flooded (Weight: 15%) 🚨

**What it measures:** Settlement is flooded according to satellite but has ZERO ground reports.

**Source:** `fuse.py` — Cross-checks raster flood mask against report locations.

**Calculation:**
```python
# In fuse.py
silent_flooded = (
    flood_fraction > 0
    and len(nearby_reports) == 0
)

# In prioritize.py
c_silent = 15 * (1.0 if silent_flooded else 0.0)
```

**Rationale:**
- **Most critical innovation in the system**
- Indicates communications cut off → likely severe situation
- Binary (0 or 15 points) — either silent or not
- Real-world validation: Kullu district 2023 had silent villages for 48h

**Why 15%?**
- High enough to bump settlements into top priorities
- Lower than flood_fraction (40%) because it's an inference, not direct measurement
- Higher than facilities (10%) because lack of communication is more urgent

**Edge Cases:**
- Settlement with 0.1% flood_fraction + zero reports → still gets +15 points
- Settlement with reports of "all clear" → `silent_flooded = False` (reports exist)

**Example:**
```
Settlement: Remote Mountain Village
flood_fraction: 0.35
Reports within 900m: 0
silent_flooded: TRUE
Score contribution: 15 points

Typical outcome: This village jumps ahead of another with flood_fraction=0.40
but confirmed reports (which show people can communicate).
```

---

### 4️⃣ Exposed Facilities (Weight: 10%)

**What it measures:** Count of critical infrastructure (hospitals, schools, bridges) within flooded areas.

**Source:** `geo.py` — Extracts from OpenStreetMap and intersects with flood mask.

**Facility Types:**
- Hospitals, clinics, health centers
- Schools, colleges
- Bridges, major road junctions
- Emergency services (police, fire stations)

**Calculation:**
```python
# In geo.py
facilities = osm_features.filter(
    type__in=['hospital', 'school', 'bridge'],
    geometry__intersects=flood_mask
)
num_exposed = len(facilities)

# In prioritize.py
c_facilities = 10 * min(1.0, num_exposed / 2.0)
```

**Rationale:**
- Losing a hospital affects entire region, not just one settlement
- Schools = evacuation centers + high daytime occupancy
- Bridges = access arteries for rescue operations
- Normalized by 2 so 2+ facilities → 10 points

**Edge Cases:**
- No OSM data for region → 0 points (not penalized for data gaps)
- Multiple facilities of same type → each counts separately

**Example:**
```
Settlement: District Headquarters
Exposed facilities:
  - District Hospital (flooded)
  - Government High School (flooded)
  - Bridge on NH-21 (damaged)
num_exposed = 3 → min(1.0, 3/2) = 1.0
Score contribution: 10 * 1.0 = 10 points
```

---

### 5️⃣ Road Access Cut (Weight: 10%)

**What it measures:** Main access road to settlement is flooded (binary flag).

**Source:** `geo.py` — Checks if OSM highway=primary/secondary/tertiary intersects flood mask within 500m of settlement.

**Calculation:**
```python
# In geo.py
roads = osm_features.filter(
    type='highway',
    highway__in=['primary', 'secondary', 'tertiary'],
    geometry__buffer(500)__intersects=settlement_point
)
road_flooded = any(road.intersects(flood_mask) for road in roads)

# In prioritize.py
c_road = 10 * (1.0 if road_flooded else 0.0)
```

**Rationale:**
- Flooded road → helicopter/boat access needed → higher cost
- Delays rescue even if settlement itself not severely flooded
- Binary (0 or 10 points) because "partially flooded" still blocks vehicles

**Edge Cases:**
- Multiple roads flooded → still just 10 points (not cumulative)
- Footpath/trail flooded → doesn't count (only major roads)
- No OSM road data → 0 points (conservative)

**Example:**
```
Settlement: Riverside Village
NH-305 (primary highway) crosses flood zone 200m away
road_flooded: TRUE
Score contribution: 10 points

Result: Village prioritized for helicopter access route.
```

---

### 6️⃣ Rainfall Anomaly (Weight: 5%)

**What it measures:** Exceptional rainfall in past 24h or 72h suggesting flash flood risk.

**Source:** `weather.py` — Analyzes rainfall CSV or live Open-Meteo data.

**Anomaly Criteria:**
```python
anomaly = (
    peak_24h > 150 mm  # Heavy to extremely heavy
    or three_day > 300 mm  # Prolonged intense rain
)
```

**Calculation:**
```python
# In weather.py
rain_flag = 1.0 if anomaly else 0.0

# In prioritize.py
c_rain = 5 * rain_flag
```

**Rationale:**
- Lowest weight (5%) because applies to entire region, not settlement-specific
- Still important: ongoing rain → situation may worsen
- Binary because we only care if anomaly threshold crossed

**Why so low?**
- Rainfall data has lower spatial resolution (~10km) vs satellite (10m)
- All settlements in affected region get same bonus
- Main value: tie-breaker when settlements have similar flood_fraction

**Example:**
```
Event: Himachal Pradesh 2023
Peak 24h rainfall: 185 mm (anomaly threshold: 150 mm)
rain_flag: 1.0
Score contribution: 5 points for ALL settlements in event area
```

---

## Tie-Breaking

When two settlements have identical scores:

1. **Population (descending):** Higher population = more people at risk
   - Source: OSM `population` tag on settlement nodes
   - Missing data treated as 0

2. **Alphabetical (ascending):** Deterministic secondary tie-break
   - Ensures consistent ordering across runs

```python
# In prioritize.py
priorities.sort(
    key=lambda p: (
        -p.score,                      # Primary: score descending
        -pop_map.get(p.settlement, 0), # Secondary: population descending
        p.settlement,                  # Tertiary: alphabetical ascending
    )
)
```

---

## Weight Rationale

| Factor | Weight | Why? |
|--------|--------|------|
| Flood Fraction | 40% | Most reliable data (satellite, deterministic) |
| Report Urgency | 20% | Human distress signal, second most important |
| Silent Flooded | 15% | Critical inference, unique innovation |
| Exposed Facilities | 10% | Regional impact, not just local |
| Road Access Cut | 10% | Logistics multiplier |
| Rainfall Anomaly | 5% | Region-wide, lowest spatial resolution |

**Design Constraint:**
```python
assert (40 + 20 + 15 + 10 + 10 + 5) == 100
```

---

## Sensitivity Analysis

### Scenario 1: Urban Hospital Flood
```
flood_fraction: 0.30 → 12 points
urgency (3 reports, avg 2): 2*3/3 = 2 → 13.3 points
silent_flooded: FALSE → 0 points
facilities (hospital + school): 2 → 10 points
road_flooded: TRUE → 10 points
rain_anomaly: TRUE → 5 points
TOTAL: 50.3 points → Rank #1 or #2
```

### Scenario 2: Silent Mountain Village
```
flood_fraction: 0.25 → 10 points
urgency: 0 → 0 points
silent_flooded: TRUE → 15 points
facilities: 0 → 0 points
road_flooded: TRUE → 10 points
rain_anomaly: TRUE → 5 points
TOTAL: 40 points → Rank #3-5 (pushed up by silent_flooded)
```

### Scenario 3: Reported but Not Flooded
```
flood_fraction: 0.05 → 2 points
urgency (1 report, urgency=2): 2/3 → 13.3 points
silent_flooded: FALSE → 0 points
facilities: 0 → 0 points
road_flooded: FALSE → 0 points
rain_anomaly: TRUE → 5 points
TOTAL: 20.3 points → Rank #10-15
```

**Key Insight:** Silent flooded villages (Scenario 2) rank higher than reported low-flood areas (Scenario 3), demonstrating the innovation's impact.

---

## Tuning Weights

Weights are defined in `api/config.py` and can be adjusted per disaster type:

### Flood Events (Current)
```python
W_FLOOD_FRACTION = 40.0
W_REPORT_URGENCY = 20.0
W_SILENT_FLOODED = 15.0
W_FACILITIES = 10.0
W_ROAD_CUT = 10.0
W_RAIN_ANOMALY = 5.0
```

### Hypothetical: Urban Flash Flood
```python
W_FLOOD_FRACTION = 35.0   # Lower (urban SAR less reliable)
W_REPORT_URGENCY = 25.0   # Higher (more reports expected)
W_SILENT_FLOODED = 10.0   # Lower (urban areas rarely silent)
W_FACILITIES = 15.0       # Higher (dense infrastructure)
W_ROAD_CUT = 10.0         # Same
W_RAIN_ANOMALY = 5.0      # Same
```

### Hypothetical: Remote Rural Flood
```python
W_FLOOD_FRACTION = 40.0   # Same
W_REPORT_URGENCY = 15.0   # Lower (fewer reports expected)
W_SILENT_FLOODED = 20.0   # Higher (common in remote areas)
W_FACILITIES = 5.0        # Lower (sparse infrastructure)
W_ROAD_CUT = 15.0         # Higher (few roads = critical)
W_RAIN_ANOMALY = 5.0      # Same
```

**To experiment:**
1. Edit `api/config.py`
2. Clear cache: `rm -rf cache/*`
3. Re-run analysis
4. Compare before/after rankings

---

## Validation & Calibration

### How to Validate Weights

1. **Historical Events:** Compare rankings against actual response priorities
2. **Expert Review:** Show to disaster response professionals for feedback
3. **Field Validation:** Ground truth from post-disaster assessments
4. **Sensitivity Testing:** Vary weights ±5% and check ranking stability

### Known Limitations

- **OSM Completeness:** Rural areas may lack facility/road data → underscored
- **Report Bias:** Urban areas generate more reports → may overshadow rural silent_flooded
- **Rainfall Resolution:** ~10km grid may miss localized cloudbursts
- **Population Data:** OSM population tags sparse in India

**Mitigation Strategies:**
- Conservative defaults: missing data = 0 points (not penalized)
- Silent flooded weight high enough to overcome report bias
- Manual review of top 10 priorities before deployment

---

## Source Attribution

Every score includes a `reasons` list and `sources` list for verification:

```json
{
  "rank": 1,
  "settlement": "Larji Village",
  "score": 52.5,
  "reasons": [
    "45% of 300 m buffer flooded [raster:himachal_2023]",
    "No ground reports despite flooding — likely cut off [raster:himachal_2023]",
    "Access road flooded [raster:himachal_2023]",
    "Rainfall anomaly: peak 185 mm, 3-day 320 mm [rainfall:himachal_2023]"
  ],
  "sources": [
    "raster:himachal_2023",
    "rainfall:himachal_2023"
  ],
  "recommended_action": "Immediate evacuation required"
}
```

**Verifier Tool (`verify.py`):**
- Checks that every reason links to a valid source
- Flags any claims without backing data
- Ensures no LLM hallucination in final output

---

## Future Enhancements

### Planned
- **Temporal Decay:** Reduce urgency scores for reports >24h old
- **Multi-Hazard:** Combine flood + landslide scores for mountain events
- **Dynamic Weights:** ML model learns optimal weights from historical outcomes
- **Confidence Intervals:** Add ±uncertainty to scores based on data quality

### Research Directions
- Bayesian scoring: incorporate prior probabilities from historical flood maps
- Network analysis: model road graph to find isolated clusters
- Social media sentiment: augment report urgency with Twitter/WhatsApp analysis

---

## References

- **Flood Risk Assessment:** UNDRR Guidelines for Disaster Risk Assessment
- **SAR Flood Mapping:** Sentinel-1 Toolbox (SNAP) flood mapping tutorial
- **Humanitarian Priority:** OCHA's Humanitarian Needs Overview methodology
- **Weight Optimization:** Multi-Criteria Decision Analysis (MCDA) literature

---

## Questions?

- **Why not use ML?** Deterministic scoring is transparent, explainable, and debuggable. No training data needed.
- **Why these 6 factors?** Based on disaster response literature + available data sources. Open to expansion!
- **Why not equal weights?** Not all signals equally reliable. Satellite (40%) > reports (20%) > inferences (15%/10%/5%).
- **Can I adjust weights?** Yes! Edit `config.py` and test on demo events. Share findings in GitHub Issues.

---

**Built for transparency. Every number has a source. Every decision has a reason.**

*If you're using SkyRelief in real disaster response, please share feedback on weight tuning!*
