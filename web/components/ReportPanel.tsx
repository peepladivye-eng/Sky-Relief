"use client"
import type { Report } from "@/app/types"

const STATUS_CONFIG: Record<string, { bg: string; text: string; label: string }> = {
  confirmed: { bg: "var(--chip-ok-bg)", text: "var(--chip-ok-text)", label: "Confirmed by flood map" },
  contradicted: { bg: "var(--chip-warn-bg)", text: "var(--chip-warn-text)", label: "Not aligned with flood map" },
  unverified: { bg: "var(--chip-flooded-bg)", text: "var(--chip-flooded-text)", label: "Not cross-checked" },
  silent_flooded: { bg: "var(--chip-silent-bg)", text: "var(--chip-silent-text)", label: "Signal lost area" },
}

export default function ReportPanel({ reports }: { reports: Report[] }) {
  return (
    <div>
      <div className="text-13 font-medium mb-3" style={{ color: "var(--ink-2)" }}>
        Ground reports ({reports.length})
      </div>
      <div className="space-y-3 max-h-96 overflow-y-auto pr-2">
        {reports.map(r => {
          const statusConfig = r.status ? STATUS_CONFIG[r.status] : null
          
          return (
            <div 
              key={r.id} 
              className="rounded-lg p-3"
              style={{
                background: "var(--sunken)",
                border: "1px solid var(--line-ctl)",
              }}
            >
              {/* Header */}
              <div className="flex items-start justify-between gap-2 mb-2">
                <div className="flex-1">
                  {r.place && (
                    <div className="text-13 font-semibold mb-1" style={{ color: "var(--ink)" }}>
                      {r.place}
                    </div>
                  )}
                  {statusConfig && (
                    <div 
                      className="inline-block px-2 py-0.5 text-11 font-medium rounded-full"
                      style={{
                        background: statusConfig.bg,
                        color: statusConfig.text,
                      }}
                    >
                      {statusConfig.label}
                    </div>
                  )}
                </div>
                {r.urgency && (
                  <div 
                    className="text-12 font-bold px-2 py-1 rounded"
                    style={{
                      background: r.urgency === 3 ? "var(--silent)" : r.urgency === 2 ? "var(--warn)" : "var(--confirmed)",
                      color: "white",
                    }}
                  >
                    {["", "Low", "Medium", "Urgent"][r.urgency]}
                  </div>
                )}
              </div>

              {/* Report Text */}
              <p className="text-13 leading-relaxed mb-2" style={{ color: "var(--ink-2)" }}>
                {r.text}
              </p>

              {/* Source */}
              <div className="flex items-center gap-2 text-12" style={{ color: "var(--ink-3)" }}>
                <span>{r.source}</span>
                {r.source_url && (
                  <>
                    <span>•</span>
                    <a 
                      href={r.source_url} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="transition-colors"
                      style={{ color: "var(--flood)" }}
                      onMouseEnter={(e) => e.currentTarget.style.textDecoration = "underline"}
                      onMouseLeave={(e) => e.currentTarget.style.textDecoration = "none"}
                    >
                      View source
                    </a>
                  </>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
