"use client"
import { useEffect, useRef, useState } from "react"
import type { SkyEvent, Sitrep } from "@/app/types"
import DeckGLOverlay from "./DeckGLOverlay"

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

// We use a minimal interface so we never call MapLibre methods on an unloaded instance
interface MLMap {
  fitBounds: (bounds: [[number,number],[number,number]], opts: object) => void
  flyTo: (opts: object) => void
  loaded: () => boolean
  isStyleLoaded: () => boolean
  getLayer: (id: string) => unknown
  removeLayer: (id: string) => void
  getSource: (id: string) => unknown
  removeSource: (id: string) => void
  addSource: (id: string, spec: object) => void
  addLayer: (spec: object) => void
  setLayoutProperty: (layerId: string, name: string, value: unknown) => void
  on: (event: string, layerOrCb: string | ((e: unknown) => void), cb?: (e: unknown) => void) => void
  getCanvas: () => HTMLCanvasElement
  getStyle: () => { sources: Record<string, unknown>; layers: Array<{ id: string }> }
  remove: () => void
}

interface Props {
  event: SkyEvent | null
  sitrep: Sitrep | null
  selectedSettlement: string | null
  onSelectSettlement: (s: string) => void
  mapLayer: "before" | "after"
  showFlood: boolean
  showRoads: boolean
  showTowers: boolean
}

export default function MapView({ 
  event, 
  sitrep, 
  selectedSettlement, 
  onSelectSettlement,
  mapLayer,
  showFlood,
  showRoads,
  showTowers
}: Props) {
  const containerRef = useRef<HTMLDivElement>(null)
  const mapRef = useRef<MLMap | null>(null)
  const [mapReady, setMapReady] = useState(false)

  // ── Initialise map once ────────────────────────────────────────────────────
  useEffect(() => {
    if (!containerRef.current || mapRef.current) return

    let instance: MLMap | null = null

    import("maplibre-gl").then(({ Map, NavigationControl }) => {
      if (!containerRef.current) return
      const m = new Map({
        container: containerRef.current,
        style: {
          version: 8,
          sources: {
            osm: {
              type: "raster",
              tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],
              tileSize: 256,
              attribution: "© OpenStreetMap contributors",
            },
          },
          layers: [{ id: "osm-tiles", type: "raster", source: "osm" }],
        },
        center: [80.0, 22.0],
        zoom: 4,
        attributionControl: { compact: true },
      })
      m.addControl(new NavigationControl({ showCompass: false }), "top-right")
      m.on("load", () => {
        mapRef.current = m as unknown as MLMap
        instance = mapRef.current
        setMapReady(true)
      })
    })

    return () => {
      if (instance) {
        instance.remove()
        mapRef.current = null
        setMapReady(false)
      }
    }
  }, [])

  // ── Fly to event bbox ──────────────────────────────────────────────────────
  useEffect(() => {
    if (!event || !mapRef.current || !mapReady) return
    const [minx, miny, maxx, maxy] = event.bbox
    const mobile = window.matchMedia("(max-width: 1000px)").matches
    mapRef.current.fitBounds([[minx, miny], [maxx, maxy]], {
      padding: mobile ? { top: 24, bottom: 24, left: 24, right: 24 } : { top: 24, bottom: 24, left: 352, right: 24 },
      duration: 1000,
    })
  }, [event, mapReady])

  // ── Add/update flood + settlement layers ───────────────────────────────────
  useEffect(() => {
    const m = mapRef.current
    if (!m || !mapReady || !sitrep || !event) return
    // Double-check style is loaded before touching layers
    if (!m.isStyleLoaded()) return

    const safeRemoveLayer = (id: string) => { try { if (m.getLayer(id)) m.removeLayer(id) } catch {} }
    const safeRemoveSource = (id: string) => { try { if (m.getSource(id)) m.removeSource(id) } catch {} }

    safeRemoveLayer("flood-fill")
    safeRemoveLayer("flood-line")
    safeRemoveLayer("settlements")
    safeRemoveLayer("settlements-label")
    safeRemoveLayer("roads")
    safeRemoveLayer("roads-highlight")
    safeRemoveLayer("bridges")
    safeRemoveLayer("bridges-highlight")
    safeRemoveLayer("towers")
    safeRemoveLayer("towers-highlight")
    safeRemoveSource("flood")
    safeRemoveSource("settlements")
    safeRemoveSource("osm-roads")
    safeRemoveSource("osm-bridges")
    safeRemoveSource("towers")

    // Flood layer
    m.addSource("flood", { type: "geojson", data: sitrep.flood.geojson as object })
    m.addLayer({ id: "flood-fill", type: "fill", source: "flood",
      paint: { "fill-color": "#3b82f6", "fill-opacity": 0.40 } })
    m.addLayer({ id: "flood-line", type: "line", source: "flood",
      paint: { "line-color": "#60a5fa", "line-width": 1.5 } })

    // Settlement circles — colour by priority + silent-flooded flag
    const features = sitrep.priorities.map(p => {
      const exp = sitrep.exposures.find(e => e.settlement === p.settlement)
      return {
        type: "Feature" as const,
        properties: {
          name: p.settlement,
          rank: p.rank,
          score: p.score,
          silent: exp?.silent_flooded ?? false,
          action: p.recommended_action,
        },
        geometry: {
          type: "Point" as const,
          coordinates: [exp?.lon ?? 0, exp?.lat ?? 0],
        },
      }
    })

    m.addSource("settlements", { type: "geojson", data: { type: "FeatureCollection", features } })

    m.addLayer({
      id: "settlements",
      type: "circle",
      source: "settlements",
      paint: {
        "circle-radius": ["interpolate", ["linear"], ["get", "score"], 0, 5, 100, 14],
        "circle-color": [
          "case",
          ["get", "silent"],  "#a855f7",
          [">=", ["get", "score"], 70], "#ef4444",
          [">=", ["get", "score"], 45], "#f97316",
          "#eab308",
        ],
        "circle-stroke-color": "#ffffff",
        "circle-stroke-width": 2,
        "circle-opacity": 0.9,
      },
    })

    m.addLayer({
      id: "settlements-label",
      type: "symbol",
      source: "settlements",
      layout: {
        "text-field": ["concat", "#", ["to-string", ["get", "rank"]], " ", ["get", "name"]],
        "text-size": 11,
        "text-offset": [0, 1.6],
        "text-anchor": "top",
        "text-max-width": 8,
      },
      paint: {
        "text-color": "#ffffff",
        "text-halo-color": "#000000",
        "text-halo-width": 1,
      },
    })

    const syncMapIdsForRegression = () => {
      const style = m.getStyle()
      if (!containerRef.current || !style) return
      containerRef.current.dataset.mapSourceIds = Object.keys(style.sources).sort().join(",")
      containerRef.current.dataset.mapLayerIds = style.layers.map(layer => layer.id).sort().join(",")
    }
    syncMapIdsForRegression()

    // Click handler
    m.on("click", "settlements", (e) => {
      const fe = (e as { features?: Array<{ properties?: { name?: string } }> }).features
      const name = fe?.[0]?.properties?.name
      if (name) onSelectSettlement(name)
    })
    m.on("mouseenter", "settlements", () => { m.getCanvas().style.cursor = "pointer" })
    m.on("mouseleave", "settlements", () => { m.getCanvas().style.cursor = "" })

    // ── Roads and Bridges from OSM ─────────────────────────────────────────────
    // Load OSM GeoJSON and extract roads (LineStrings) and bridges (Points)
    fetch(`${API}/events/${event.event_id}/osm`)
      .then(res => res.json())
      .then((osmData: { features: Array<{ properties: { type: string }; geometry: object }> }) => {
        // Ensure sources are removed before adding (in case fetch completes after a re-render)
        safeRemoveLayer("roads")
        safeRemoveSource("osm-roads")
        safeRemoveLayer("bridges")
        safeRemoveSource("osm-bridges")

        // Roads (LineStrings)
        const roadFeatures = osmData.features.filter(f => f.properties.type === "road")
        m.addSource("osm-roads", { 
          type: "geojson", 
          data: { type: "FeatureCollection", features: roadFeatures } 
        })
        m.addLayer({
          id: "roads",
          type: "line",
          source: "osm-roads",
          paint: {
            "line-color": "#FFB84D",
            "line-width": 3,
            "line-opacity": 0.8,
          },
          layout: { visibility: showRoads ? "visible" : "none" }
        })

        // Bridges (Points)
        const bridgeFeatures = osmData.features.filter(f => f.properties.type === "bridge")
        m.addSource("osm-bridges", { 
          type: "geojson", 
          data: { type: "FeatureCollection", features: bridgeFeatures } 
        })
        m.addLayer({
          id: "bridges",
          type: "circle",
          source: "osm-bridges",
          paint: {
            "circle-radius": 6,
            "circle-color": "#FFB84D",
            "circle-stroke-color": "#FF8C00",
            "circle-stroke-width": 2,
            "circle-opacity": 0.9,
          },
          layout: { visibility: showRoads ? "visible" : "none" }
        })
        syncMapIdsForRegression()
      })
      .catch(err => console.warn("Failed to load OSM data:", err))

    // ── Towers (settlements with facilities) ───────────────────────────────────
    const towerFeatures = sitrep.exposures
      .filter(exp => exp.facilities && exp.facilities.length > 0)
      .map(exp => ({
        type: "Feature" as const,
        properties: {
          name: exp.settlement,
          facilities: exp.facilities.join(", "),
        },
        geometry: {
          type: "Point" as const,
          coordinates: [exp.lon, exp.lat],
        },
      }))

    m.addSource("towers", { 
      type: "geojson", 
      data: { type: "FeatureCollection", features: towerFeatures } 
    })
    m.addLayer({
      id: "towers",
      type: "symbol",
      source: "towers",
      layout: {
        "icon-image": "marker-15",
        "icon-size": 1.5,
        "text-field": "📡",
        "text-size": 20,
        "text-offset": [0, 0],
        visibility: showTowers ? "visible" : "none"
      },
      paint: {
        "text-color": "#10B981",
      }
    })
    syncMapIdsForRegression()
  }, [sitrep, mapReady, onSelectSettlement, event, showRoads, showTowers])

  // ── Toggle flood layer visibility ──────────────────────────────────────────
  useEffect(() => {
    const m = mapRef.current
    if (!m || !mapReady || !sitrep) return
    try {
      if (m.getLayer("flood-fill") && m.getLayer("flood-line")) {
        m.setLayoutProperty("flood-fill", "visibility", showFlood ? "visible" : "none")
        m.setLayoutProperty("flood-line", "visibility", showFlood ? "visible" : "none")
      }
    } catch {}
  }, [showFlood, mapReady, sitrep])

  // ── Toggle roads and bridges visibility ────────────────────────────────────
  useEffect(() => {
    const m = mapRef.current
    if (!m || !mapReady || !sitrep || !event) return
    try {
      if (m.getLayer("roads")) {
        m.setLayoutProperty("roads", "visibility", showRoads ? "visible" : "none")
      }
      if (m.getLayer("bridges")) {
        m.setLayoutProperty("bridges", "visibility", showRoads ? "visible" : "none")
      }
    } catch {}
  }, [showRoads, mapReady, sitrep, event])

  // ── Toggle towers visibility ───────────────────────────────────────────────
  useEffect(() => {
    const m = mapRef.current
    if (!m || !mapReady || !sitrep) return
    try {
      if (m.getLayer("towers")) {
        m.setLayoutProperty("towers", "visibility", showTowers ? "visible" : "none")
      }
    } catch {}
  }, [showTowers, mapReady, sitrep])

  // ── Fly to selected settlement ─────────────────────────────────────────────
  useEffect(() => {
    const m = mapRef.current
    if (!m || !mapReady || !selectedSettlement || !sitrep) return
    const exp = sitrep.exposures.find(e => e.settlement === selectedSettlement)
    if (exp) m.flyTo({ center: [exp.lon, exp.lat], zoom: 12, duration: 800 })
  }, [selectedSettlement, mapReady, sitrep])

  return (
    <div className="relative w-full h-full min-h-64 bg-gray-900">
      <div ref={containerRef} data-testid="map-canvas" data-map-source-ids="osm" data-map-layer-ids="osm-tiles" className="absolute inset-0" />

      {/* deck.gl animated rings for silent-flooded */}
      {sitrep && mapRef.current && (
        <DeckGLOverlay 
          map={mapRef.current} 
          exposures={sitrep.exposures} 
          mapReady={mapReady} 
        />
      )}

      {/* Empty state */}
      {!event && (
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          <div className="text-center text-gray-600">
            <p className="text-5xl mb-3">🛰️</p>
            <p className="text-sm font-medium">Select an event and run analysis</p>
          </div>
        </div>
      )}

    </div>
  )
}
