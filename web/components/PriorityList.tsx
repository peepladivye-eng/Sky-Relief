"use client"
import type { Priority } from "@/app/types"

export default function PriorityList({
  priorities, selected, onSelect, lang
}: {
  priorities: Priority[]
  selected: string | null
  onSelect: (s: string) => void
  lang: "en" | "hi"
}) {
  const getScoreColor = (score: number) => {
    if (score >= 70) return "var(--silent)"
    if (score >= 45) return "var(--warn)"
    return "var(--confirmed)"
  }

  return (
    <div data-testid="priority-list" className="min-h-full flex flex-col">
      <div className="flex items-baseline justify-between gap-3 px-4 pb-3 pt-4">
        <h2 className="text-lg font-bold" style={{ color: "var(--ink)" }}>Reach these first</h2>
        <span className="shrink-0 text-xs" style={{ color: "var(--ink-3)" }}>Score out of 100</span>
      </div>
      {/* Selected Settlement Detail */}
      {selected && priorities.find(p => p.settlement === selected) && (
        <div 
          className="p-4 border-b"
          style={{ borderColor: "var(--line-soft)", background: "var(--panel-2)" }}
        >
          {(() => {
            const priority = priorities.find(p => p.settlement === selected)!
            const isSilent = priority.reasons.some(
              r => r.toLowerCase().includes("silent") || r.toLowerCase().includes("no ground reports")
            )
            return (
              <>
                <div className="flex items-center gap-2 mb-3">
                  <div 
                    className="w-8 h-8 rounded-full flex items-center justify-center text-14 font-bold"
                    style={{ 
                      background: getScoreColor(priority.score),
                      color: "white"
                    }}
                  >
                    {priority.rank}
                  </div>
                  <h3 className="text-16 font-bold flex-1" style={{ color: "var(--ink)" }}>
                    {priority.settlement}
                  </h3>
                  <div className="text-22 font-bold tabular-nums" style={{ color: "var(--ink-3)", fontFamily: "var(--font-bricolage)" }}>
                    {priority.score.toFixed(0)}
                  </div>
                </div>

                {isSilent && (
                  <div 
                    className="mb-3 px-3 py-1.5 rounded-lg inline-flex items-center gap-2"
                    style={{ background: "var(--chip-silent-bg)", border: "1px solid var(--chip-silent-border)" }}
                  >
                    <span className="text-12 font-medium" style={{ color: "var(--chip-silent-text)" }}>
                      Signal lost — no ground reports nearby
                    </span>
                  </div>
                )}

                <div className="mb-3">
                  <div className="text-12 mb-1" style={{ color: "var(--ink-3)" }}>Recommended action</div>
                  <p className="text-14 font-medium" style={{ color: "var(--ink-2)" }}>
                    {priority.recommended_action}
                  </p>
                </div>

                <div>
                  <div className="text-12 mb-2" style={{ color: "var(--ink-3)" }}>Evidence</div>
                  <ul className="space-y-1.5">
                    {priority.reasons.map((reason, i) => (
                      <li key={i} className="text-13 flex items-start gap-2" style={{ color: "var(--ink-2)" }}>
                        <span style={{ color: "var(--flood)" }}>•</span>
                        <span className="flex-1">{reason}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                {priority.sources.length > 0 && (
                  <div className="mt-3 flex flex-wrap gap-2">
                    {priority.sources.slice(0, 3).map((src, i) => (
                      <span 
                        key={i}
                        className="text-11 px-2 py-1 rounded-full"
                        style={{ background: "var(--sunken)", color: "var(--ink-3)" }}
                      >
                        {src}
                      </span>
                    ))}
                  </div>
                )}
              </>
            )
          })()}
        </div>
      )}

      {/* Priority List */}
      <div className="flex-1">
        <div className="p-4 space-y-2">
          {priorities.map(p => {
            const isSilent = p.reasons.some(
              r => r.toLowerCase().includes("silent") || r.toLowerCase().includes("no ground reports")
            )
            const isSelected = selected === p.settlement

            return (
              <button
                key={p.settlement}
                onClick={() => onSelect(p.settlement)}
                className="w-full text-left p-3 rounded-lg transition-all"
                style={{
                  background: isSelected ? "var(--panel-2)" : "var(--sunken)",
                  border: `1px solid ${isSelected ? "var(--flood)" : "var(--line-ctl)"}`,
                }}
              >
                <div className="flex items-center gap-3">
                  <div 
                    className="w-7 h-7 rounded-full flex items-center justify-center text-13 font-bold flex-shrink-0"
                    style={{ 
                      background: getScoreColor(p.score),
                      color: "white"
                    }}
                  >
                    {p.rank}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-14 font-semibold truncate" style={{ color: "var(--ink)" }}>
                      {p.settlement}
                    </div>
                    <div className="text-12 truncate mt-0.5" style={{ color: "var(--ink-3)" }}>
                      {p.recommended_action}
                    </div>
                  </div>
                  <div className="text-16 font-bold tabular-nums" style={{ color: "var(--ink-2)", fontFamily: "var(--font-bricolage)" }}>
                    {p.score.toFixed(0)}
                  </div>
                </div>

                {isSilent && (
                  <div className="flex items-center gap-1.5 mt-2">
                    <div 
                      className="w-2 h-2 rounded-full"
                      style={{ background: "var(--silent)" }}
                    />
                    <span className="text-11" style={{ color: "var(--silent)" }}>
                      Signal lost
                    </span>
                  </div>
                )}
              </button>
            )
          })}
        </div>
      </div>
    </div>
  )
}
