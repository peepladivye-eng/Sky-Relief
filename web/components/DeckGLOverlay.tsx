"use client"
import { useEffect, useState } from "react"
import { MapboxOverlay } from "@deck.gl/mapbox"
import { ScatterplotLayer } from "@deck.gl/layers"
import type { Exposure } from "@/app/types"

interface Props {
  map: any  // MapLibre map instance
  exposures: Exposure[]
  mapReady: boolean
}

/**
 * Animated pulsing rings for silent-flooded villages.
 * Uses deck.gl ScatterplotLayer with time-based radius scaling.
 */
export default function DeckGLOverlay({ map, exposures, mapReady }: Props) {
  const [time, setTime] = useState(0)

  // Animation loop
  useEffect(() => {
    if (!mapReady) return
    let frameId: number
    const animate = () => {
      setTime(t => (t + 0.02) % 1)  // 0–1 over ~2s
      frameId = requestAnimationFrame(animate)
    }
    frameId = requestAnimationFrame(animate)
    return () => cancelAnimationFrame(frameId)
  }, [mapReady])

  // Create deck.gl overlay
  useEffect(() => {
    if (!map || !mapReady) return

    const silentVillages = exposures
      .filter(e => e.silent_flooded)
      .map(e => ({ coordinates: [e.lon, e.lat], name: e.settlement }))

    // Pulsing ring effect: radius grows then fades
    const pulse = Math.sin(time * Math.PI * 2) * 0.5 + 0.5  // 0–1 sine wave

    const overlay = new MapboxOverlay({
      interleaved: true,
      layers: [
        new ScatterplotLayer({
          id: "silent-ring",
          data: silentVillages,
          getPosition: (d: { coordinates: [number, number] }) => d.coordinates,
          getRadius: () => 400 + pulse * 200,  // 400–600m
          getFillColor: [168, 85, 247, 30],  // purple-500 with low opacity
          getLineColor: [168, 85, 247, 120 + pulse * 135],  // fade 120–255
          getLineWidth: 3,
          stroked: true,
          filled: false,
          lineWidthUnits: "pixels",
          radiusUnits: "meters",
          pickable: false,
        }),
      ],
    })

    map.addControl(overlay as any)
    return () => {
      map.removeControl(overlay as any)
    }
  }, [map, mapReady, exposures, time])

  return null
}
