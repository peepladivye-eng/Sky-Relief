# SkyRelief UI Design Direction

## Product goal

Design SkyRelief as a map-first emergency response desk. A responder should be able to answer three questions quickly:

1. What is happening in this event?
2. Which settlements should be reached first?
3. What evidence supports that recommendation, and what remains uncertain?

The interface presents analysis for human review. It must not imply that a model recommendation is a confirmed field assessment.

## Core layout

### Desktop: 1440 px reference

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│ SkyRelief   Event and dates   Sensor              EN | हि   Run analysis     │
├──────────────────────────────────────────────────────────────────────────────┤
│ ┌─────────────────┐                              ┌─────────────────────────┐ │
│ │ Flood summary   │                              │ Reach these first       │ │
│ │ area / share    │          MAP                 │ ranked settlements     │ │
│ │ rainfall        │    flood extent + places     │ selected: evidence +   │ │
│ ├─────────────────┤                              │ recommended action      │ │
│ │ Analysis trace  │                              └─────────────────────────┘ │
│ │ collapsed steps │                                                        │
│ └─────────────────┘                                                        │
│ ┌────────────────────────── BOTTOM DOCK ──────────────────────────────────┐ │
│ │ Ground reports | WhatsApp brief | Limits and evaluation                 │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────────┘
```

- Keep the map as the primary workspace, with the existing MapLibre map and OpenStreetMap tiles.
- Use a 56 px top bar. Place event selection, event date range, and sensor there alongside language and analysis controls.
- Float a compact event summary and collapsible analysis trace on the left; place ranked settlements and the selected settlement's evidence on the right.
- Place Ground reports, WhatsApp brief, and Limits and evaluation in a collapsible bottom dock. Keep dock content internally scrollable so the map remains usable.
- Fit the event bounds with padding for the visible panels. Do not let selecting a settlement zoom so tightly that the surrounding flood context disappears.

### Small screens

Below 1000 px, use a 420 px map block first, followed by the event summary, priority list and selected settlement details, then the dock sections. At 390 px, use compact headers and collapsible content; keep the selected settlement and its action visible without horizontal scrolling. All controls should have touch-friendly hit areas.

## Screen content

### Top bar

- SkyRelief name and a simple flood-response mark.
- Event selector showing the event name, before/after dates and sensor from `SkyEvent`.
- English/Hindi language control.
- Primary `Run analysis` action with a clear disabled/running state.
- Keep the same `/events` loading and `/analyze` request behavior.

### Event summary and analysis progress

- Show flooded area (`flood.area_km2`), percentage (`flood.pct_of_bbox`), peak rainfall (`weather.peak_mm`) and an anomaly label only when `weather.anomaly` is true.
- Use large tabular numerals and explicit units. Keep `unknown_fraction` visible as a data coverage caveat where meaningful.
- Present SSE tool steps in a collapsed-by-default `Analysis progress` card. Expand to see each step's label and detail. Running, done, and error states must be visually and textually distinct.
- If an SSE error or request failure occurs, show a useful inline message and preserve the last successful sitrep when one exists.

### Map

- Continue to use the existing MapLibre map, current tile source, flood GeoJSON and settlement exposure coordinates.
- Show flood extent as translucent blue with a clear outline. Show settlement markers with a readable rank/selection treatment; avoid making score colors the only way to distinguish urgency.
- Mark `silent_flooded` settlements distinctly, with a short explanation that the flood mask shows flooding but there are no nearby reports. Do not label these as confirmed phone or tower outages.
- Selecting a marker or list row should select the same settlement and show its evidence. Keep callouts short and grounded in returned fields.
- Keep a compact map key for marks currently shown. Respect reduced motion for signal rings.

### Priority drawer

- Title: `Reach these first` with a concise explanation that rows follow the API ranking.
- Preserve `priorities` order and display the API `rank`, `settlement`, and `score` without recomputing them.
- Each row shows a status cue derived from matching `Exposure` data and a short action cue from `recommended_action`.
- On selection, show `reasons`, `sources`, and `recommended_action` in a detail card. Make source names readable; keep raw source identifiers out of user-facing copy.
- Use score colors carefully: pair every color with a label or icon and do not present a numeric score as a probability or certainty.

### Bottom dock

**Ground reports**

- Show report place, urgency, report text, source, optional source link, and flood-map status as separate pieces of information.
- Translate `confirmed`, `contradicted`, and `unverified` into plain, evidence-based labels. Explain that `contradicted` means the report is not aligned with the mapped flood result; it does not prove the report false.
- Move the existing paste-report form here. Keep its current behavior: submit the extra report through the existing `/analyze` flow and refresh the ranking from the returned sitrep.

**WhatsApp brief**

- Show the existing English or Hindi brief, a language switch, and a copy action with a visible `Copied` confirmation.
- Show the longer situation summary as a secondary expandable section. Do not silently rewrite API-generated content.
- Verify Hindi text encoding and translations before reusing the current strings; the inspected UI files contain garbled Hindi characters.

**Limits and evaluation**

- Show `sitrep.limitations`, `vision.caveats`, false-positive notes and confidence where present, with plain labels distinguishing caveats from measured results.
- Explain that the flood area is derived from the satellite mask and that field reports may be incomplete.
- Avoid claiming real-world model accuracy from synthetic fixtures. Keep evaluation context clear if shown.

## Data and trust rules

Use the existing TypeScript contracts in `web/app/types.ts` and the API schemas in `api/schemas.py` as the source of truth. Render only values actually returned by the API. Hide unsupported elements or label them unavailable; do not fabricate data.

Fields available to the UI include event dates/sensor/bounds, flood area and percentage, vision confidence and caveats, rainfall/anomaly, reports and source URLs, settlement coordinates and exposure flags, priorities/reasons/sources/actions, limitations, summaries and briefs, and live step events.

The current API does not provide structured road-damage geometry, bridge condition, tower status, or verified route-to-base data. Do not draw those marks or show those controls. `Exposure.road_flooded` is a boolean and `VisionCheck.damage_observations` is free text; neither supports precise road/bridge damage mapping. `silent_flooded` means flooded with no nearby reports, not proven communications failure.

Keep API endpoints, payloads, SSE event handling, scoring/ranking, and data files unchanged during UI work.

## Visual system

- Extend the current tokens in `web/styles/tokens.css`; do not create a competing palette. Use the dark blue-gray surface, restrained flood blue, amber for caveats, red/pink for communication gaps, and teal only for verified positive states.
- Use consistent 12 px panel corners, 8 px control corners, 16–18 px panel padding, and subtle borders. Avoid gradients, glow and heavy blur effects.
- Use a clear sans-serif UI font and tabular numerals for measurements. Keep body text readable and sentence case throughout.
- Use visible focus styles, semantic buttons/tabs, `aria-pressed` for toggles, and polite live announcements for analysis progress and result updates.
- Honor `prefers-reduced-motion`; animation must not carry meaning by itself.

## Component mapping in the current app

| Current file/component | Design role |
|---|---|
| `web/app/page.tsx` | App shell, shared state, event/run/report flow, responsive layout |
| `web/components/EventPicker.tsx` | Top-bar event selector and loading/error states |
| `web/components/MapView.tsx` | Main map, flood/settlement styling, selection, fit bounds, legend |
| `web/components/DeckGLOverlay.tsx` | Reduced-motion-aware silent-flooded marker rings |
| `web/components/PriorityList.tsx` | Ranked drawer, selection, reasons and action detail |
| `web/components/TraceTimeline.tsx` | Collapsible analysis progress |
| `web/components/ReportPanel.tsx` | Reports tab and report status/source presentation |
| `web/components/WhatsAppBrief.tsx` | Brief tab, language, copy confirmation and summary |
| `web/components/LimitationsPanel.tsx` | Limits and evaluation tab |
| `web/styles/tokens.css`, `web/app/globals.css` | Shared visual tokens, responsive rules, focus and motion preferences |

## Implementation checkpoints

1. Record the current `/events` and `/analyze` request behavior, SSE flow, map source/layer IDs, and current desktop/mobile screenshots.
2. Build the responsive shell and tokens while keeping the existing map and handlers working.
3. Move the existing summary metrics and trace into the left column; keep their values sourced from `Sitrep` and `StepEvent`.
4. Build the priority drawer and selection detail using API priority order and existing map selection.
5. Move reports, report submission, brief, and limitations into the bottom dock without changing request payloads.
6. Refine map paint, selection and markers only from existing fields; omit unsupported damage and route visuals.
7. Verify desktop and mobile layout, English/Hindi rendering, keyboard access, reduced motion, and unchanged API behavior.

At each checkpoint, compare behavior with the baseline before continuing. Keep the existing end-to-end flows working and do not modify `api/` or `data/` as part of the UI redesign.
