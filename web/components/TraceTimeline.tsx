"use client"
import type { StepEvent } from "@/app/types"

const TOOL_LABELS: Record<string, string> = {
  raster: "Flood mask analysis",
  geo: "Settlement exposure",
  weather: "Rainfall analysis",
  reports: "Ground reports",
  vision: "Vision verification",
  fuse: "Evidence fusion",
  prioritize: "Priority ranking",
  brief: "Situation brief",
  verify: "Source verification",
}

export default function TraceTimeline({ steps, expanded = true, onToggle }: { steps: StepEvent[]; expanded?: boolean; onToggle?: () => void }) {
  const latest = new Map<string, StepEvent>()
  for (const s of steps) latest.set(s.tool, s)
  const orderedSteps = Array.from(latest.values())

  return (
    <div>
      <button type="button" onClick={onToggle} aria-expanded={expanded} className="mb-3 flex w-full items-center justify-between text-left text-13 font-bold" style={{ color: "var(--ink)" }}>
        <span>Agent run</span>
        <span aria-hidden="true" style={{ color: "var(--ink-3)" }}>{expanded ? "−" : "+"}</span>
      </button>
      {expanded && <div className="space-y-2" role="status" aria-live="polite">
        {orderedSteps.map(step => {
          const isRunning = step.status === "running"
          const isDone = step.status === "done"
          const isError = step.status === "error"

          return (
            <div key={step.tool} className="flex items-start gap-3">
              {/* Status Icon */}
              <div className="mt-0.5 flex-shrink-0">
                {isDone && (
                  <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                    <circle cx="8" cy="8" r="7" fill="var(--confirmed)" fillOpacity="0.2" />
                    <path d="M5 8l2 2 4-4" stroke="var(--confirmed)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                )}
                {isRunning && (
                  <svg width="16" height="16" viewBox="0 0 16 16" fill="none" className="animate-spin">
                    <circle cx="8" cy="8" r="6" stroke="var(--flood)" strokeWidth="2" strokeDasharray="8 4" />
                  </svg>
                )}
                {isError && (
                  <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                    <circle cx="8" cy="8" r="7" fill="var(--silent)" fillOpacity="0.2" />
                    <path d="M6 6l4 4M10 6l-4 4" stroke="var(--silent)" strokeWidth="2" strokeLinecap="round"/>
                  </svg>
                )}
              </div>

              {/* Step Info */}
              <div className="flex-1 min-w-0">
                <div 
                  className="text-13 font-medium"
                  style={{ color: isError ? "var(--silent)" : "var(--ink)" }}
                >
                  {TOOL_LABELS[step.tool] || step.tool}
                </div>
                {step.detail && (
                  <div className="text-12 mt-0.5 truncate" style={{ color: "var(--ink-3)" }}>
                    {step.detail}
                  </div>
                )}
              </div>
            </div>
          )
        })}
      </div>}
    </div>
  )
}
