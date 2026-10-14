"use client"
import type { Sitrep } from "@/app/types"

export default function LimitationsPanel({ sitrep }: { sitrep: Sitrep }) {
  return (
    <div>
      <p className="text-xs text-gray-400 mb-2 font-medium uppercase tracking-wide">Limitations</p>
      <ul className="space-y-1.5 max-h-36 overflow-y-auto">
        {sitrep.limitations.map((lim, i) => (
          <li key={i} className="flex items-start gap-2 text-xs text-gray-400">
            <span className="text-yellow-500 mt-0.5 flex-shrink-0">•</span>
            <span>{lim}</span>
          </li>
        ))}
      </ul>
      <div className="mt-3 bg-gray-800 rounded-lg p-2.5 text-xs">
        <p className="text-gray-400 font-medium mb-1">Stats</p>
        <div className="grid grid-cols-2 gap-1">
          <span className="text-gray-500">Flood area</span><span className="text-white font-mono">{sitrep.flood.area_km2.toFixed(1)} km²</span>
          <span className="text-gray-500">Coverage</span><span className="text-white font-mono">{sitrep.flood.pct_of_bbox.toFixed(1)}%</span>
          <span className="text-gray-500">Peak rain</span><span className="text-white font-mono">{sitrep.weather.peak_mm} mm/d</span>
          <span className="text-gray-500">Anomaly</span><span className={sitrep.weather.anomaly ? "text-red-400" : "text-green-400"}>{sitrep.weather.anomaly ? "Yes" : "No"}</span>
        </div>
      </div>
    </div>
  )
}