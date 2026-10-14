"use client"

import { useCallback, useEffect, useRef, useState } from "react"
import type { AgentEvent, Sitrep, SkyEvent, StepEvent } from "@/app/types"
import EventPicker from "@/components/EventPicker"
import LimitationsPanel from "@/components/LimitationsPanel"
import MapView from "@/components/MapView"
import PriorityList from "@/components/PriorityList"
import ReportPanel from "@/components/ReportPanel"
import TraceTimeline from "@/components/TraceTimeline"
import WhatsAppBrief from "@/components/WhatsAppBrief"

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
type DockTab = "reports" | "brief" | "limits"

interface ResponseDeskProps {
  initialEventId?: string
}

export default function ResponseDesk({ initialEventId }: ResponseDeskProps) {
  const [selectedEvent, setSelectedEvent] = useState<SkyEvent | null>(null)
  const [steps, setSteps] = useState<StepEvent[]>([])
  const [sitrep, setSitrep] = useState<Sitrep | null>(null)
  const [running, setRunning] = useState(false)
  const [lang, setLang] = useState<"en" | "hi">("en")
  const [extraReport, setExtraReport] = useState("")
  const [selectedSettlement, setSelectedSettlement] = useState<string | null>(null)
  const [dockTab, setDockTab] = useState<DockTab>("reports")
  const [dockOpen, setDockOpen] = useState(true)
  // Layer toggles
  const [mapLayer, setMapLayer] = useState<"before" | "after">("after")
  const [showFlood, setShowFlood] = useState(true)
  const [showRoads, setShowRoads] = useState(false)
  const [showTowers, setShowTowers] = useState(false)
  const abortRef = useRef<AbortController | null>(null)

  const selectEvent = (event: SkyEvent) => {
    setSelectedEvent(event)
    setSitrep(null)
    setSteps([])
    setSelectedSettlement(null)
  }

  const runAnalysis = useCallback(async (extraReports?: string[]) => {
    if (!selectedEvent || running) return
    setRunning(true)
    setSteps([])
    if (!extraReports) setSitrep(null)
    abortRef.current = new AbortController()

    try {
      const res = await fetch(`${API}/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ event_id: selectedEvent.event_id, extra_reports: extraReports }),
        signal: abortRef.current.signal,
      })
      const reader = res.body?.getReader()
      if (!reader) throw new Error("Stream unavailable")
      const decoder = new TextDecoder()
      let buffer = ""

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split("\n")
        buffer = lines.pop() || ""
        for (const line of lines) {
          if (!line.startsWith("data: ")) continue
          try {
            const ev: AgentEvent = JSON.parse(line.slice(6))
            if (ev.type === "step") setSteps(s => [...s, ev])
            if (ev.type === "sitrep") setSitrep(ev.data)
            if (ev.type === "partial") {
              setSteps(s => {
                const last = s[s.length - 1]
                if (last && last.tool === ev.tool && last.status === "running") {
                  return [...s.slice(0, -1), { ...last, detail: ev.detail || last.detail }]
                }
                return s
              })
            }
          } catch { /* ignore malformed lines */ }
        }
      }
    } catch (err: unknown) {
      if (err instanceof Error && err.name !== "AbortError") console.error(err)
    } finally {
      setRunning(false)
    }
  }, [selectedEvent, running])

  const submitReport = () => {
    if (!extraReport.trim()) return
    void runAnalysis([extraReport.trim()])
    setExtraReport("")
  }

  return (
    <main
      className="h-dvh overflow-hidden flex flex-col"
      style={{ background: "var(--bg)", color: "var(--ink)" }}
    >
      {/* ── Top Bar ── */}
      <header
        className="h-14 shrink-0 flex items-center gap-3 px-4 border-b z-30"
        style={{ background: "var(--panel)", borderColor: "var(--line)" }}
      >
        <a href="#main-map" className="flex items-center gap-2 shrink-0" aria-label="SkyRelief home">
          <SkyReliefMark />
          <span className="text-lg font-bold tracking-tight" style={{ fontFamily: "var(--font-bricolage)" }}>
            SkyRelief
          </span>
        </a>

        <EventPicker onSelect={selectEvent} selected={selectedEvent} />

        <div className="flex-1" />

        <button
          type="button"
          className="hidden sm:inline-flex rounded-lg border px-3 py-2 text-xs font-semibold"
          style={{ borderColor: "var(--line-ctl)", background: "var(--panel-2)", color: "var(--ink-2)" }}
          onClick={() => setDockTab("limits")}
        >
          Limits and evaluation
        </button>

        {/* Language toggle */}
        <div
          className="flex shrink-0 overflow-hidden rounded-lg border"
          role="group" aria-label="Language"
          style={{ borderColor: "var(--line-ctl)", background: "var(--sunken)" }}
        >
          {(["en", "hi"] as const).map(l => (
            <button
              key={l}
              type="button"
              aria-pressed={lang === l}
              onClick={() => setLang(l)}
              className="px-2.5 py-2 text-xs font-semibold transition-colors"
              style={{
                background: lang === l ? "var(--flood-fill)" : "transparent",
                color: lang === l ? "#fff" : "var(--ink-3)",
              }}
            >
              {l === "en" ? "EN" : "हिन्दी"}
            </button>
          ))}
        </div>

        {/* Run button */}
        <button
          type="button"
          data-testid="run-analysis"
          onClick={() => void runAnalysis()}
          disabled={!selectedEvent || running}
          className="shrink-0 rounded-lg px-4 py-2 text-sm font-semibold text-white transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          style={{ background: selectedEvent && !running ? "var(--flood-fill)" : "var(--line-ctl)" }}
        >
          {running ? "Analysing…" : "Run analysis"}
        </button>
      </header>

      {/* ── Body: 3-column grid ── */}
      <div className="flex-1 min-h-0 grid" style={{ gridTemplateColumns: "240px 1fr 320px" }}>

        {/* ── LEFT SIDEBAR ── */}
        <aside
          className="flex flex-col gap-3 overflow-y-auto p-3 border-r"
          style={{ borderColor: "var(--line)", background: "var(--panel)" }}
        >
          {/* Flooded area stat */}
          {sitrep ? (
            <>
              <StatCard>
                <p className="text-xs font-semibold mb-1" style={{ color: "var(--ink-3)" }}>Flooded area</p>
                <div className="flex items-baseline gap-1">
                  <span
                    className="text-[40px] font-bold leading-none tabular-nums"
                    style={{ color: "var(--ink)", fontFamily: "var(--font-bricolage)" }}
                  >
                    {sitrep.flood.area_km2.toFixed(1)}
                  </span>
                  <span className="text-base" style={{ color: "var(--ink-3)" }}>km²</span>
                </div>
                <p className="mt-2 text-sm font-semibold tabular-nums" style={{ color: "var(--ink-2)" }}>
                  {sitrep.flood.pct_of_bbox.toFixed(1)}% of the region is under water
                </p>
                <div
                  className="mt-3 pt-3 flex items-center gap-2 border-t"
                  style={{ borderColor: "var(--line-soft)" }}
                >
                  <span
                    className="text-lg font-bold tabular-nums"
                    style={{ color: "var(--ink)", fontFamily: "var(--font-bricolage)" }}
                  >
                    {sitrep.weather.peak_mm.toFixed(1)} mm
                  </span>
                  <span className="text-xs" style={{ color: "var(--ink-3)" }}>peak rainfall</span>
                  {sitrep.weather.anomaly && (
                    <span
                      className="rounded-full px-2 py-0.5 text-xs font-semibold border"
                      style={{ color: "var(--warn)", background: "#3A2A0E", borderColor: "#6A4A1A" }}
                    >
                      Above normal
                    </span>
                  )}
                </div>
              </StatCard>

              {/* Damage & access */}
              {sitrep.vision.damage_observations.filter(o => !/skipped|not performed|not available/i.test(o)).length > 0 && (
                <StatCard>
                  <p className="text-xs font-semibold mb-2" style={{ color: "var(--ink-3)" }}>Damage and access</p>
                  <ul className="space-y-1.5 text-sm" style={{ color: "var(--ink-2)" }}>
                    {sitrep.vision.damage_observations
                      .filter(o => !/skipped|not performed|not available/i.test(o))
                      .map((o, i) => <li key={i}>{o}</li>)}
                  </ul>
                </StatCard>
              )}

              {/* Analysis progress */}
              {steps.length > 0 && (
                <StatCard>
                  <TraceTimeline steps={steps} expanded={running} onToggle={() => {}} />
                </StatCard>
              )}
            </>
          ) : (
            <>
              {/* Pre-analysis state */}
              <StatCard>
                <p className="text-xs font-semibold mb-2" style={{ color: "var(--ink-3)" }}>
                  {selectedEvent ? selectedEvent.name : "No event selected"}
                </p>
                {selectedEvent ? (
                  <p className="text-xs leading-relaxed" style={{ color: "var(--ink-3)" }}>
                    {selectedEvent.before_date} → {selectedEvent.after_date}
                    <br />{selectedEvent.sensor}
                  </p>
                ) : (
                  <p className="text-sm" style={{ color: "var(--ink-3)" }}>
                    Choose an event from the top bar to begin.
                  </p>
                )}
                {selectedEvent && !running && (
                  <button
                    type="button"
                    onClick={() => void runAnalysis()}
                    className="mt-3 w-full rounded-lg px-4 py-2 text-sm font-semibold text-white"
                    style={{ background: "var(--flood-fill)" }}
                  >
                    Run analysis
                  </button>
                )}
                {running && (
                  <p className="mt-3 text-sm font-semibold" style={{ color: "var(--flood)" }}>
                    Analysis in progress…
                  </p>
                )}
              </StatCard>

              {steps.length > 0 && (
                <StatCard>
                  <TraceTimeline steps={steps} expanded={running} onToggle={() => {}} />
                </StatCard>
              )}
            </>
          )}
        </aside>

        {/* ── CENTER: Map + layer toggles + bottom dock ── */}
        <div className="flex flex-col min-h-0 min-w-0">
          {/* Map fills available space */}
          <div id="main-map" className="flex-1 relative min-h-0">
            <MapView
              event={selectedEvent}
              sitrep={sitrep}
              selectedSettlement={selectedSettlement}
              onSelectSettlement={setSelectedSettlement}
              mapLayer={mapLayer}
              showFlood={showFlood}
              showRoads={showRoads}
              showTowers={showTowers}
            />

            {/* Layer toggle bar — bottom of map area */}
            {sitrep && (
              <div
                className="absolute bottom-4 left-1/2 -translate-x-1/2 flex items-center gap-1 rounded-xl px-2 py-1.5 z-10"
                style={{ background: "var(--panel)", border: "1px solid var(--line-ctl)", boxShadow: "0 10px 30px #00000066" }}
              >
                {/* Before / After toggle */}
                <div
                  className="flex rounded-lg overflow-hidden mr-1"
                  style={{ border: "1px solid var(--line-ctl)" }}
                >
                  {(["before", "after"] as const).map(l => (
                    <button
                      key={l}
                      type="button"
                      aria-pressed={mapLayer === l}
                      onClick={() => setMapLayer(l)}
                      className="px-3 py-1.5 text-xs font-semibold transition-colors capitalize"
                      style={{
                        background: mapLayer === l ? "var(--flood-fill)" : "transparent",
                        color: mapLayer === l ? "#fff" : "var(--ink-3)",
                      }}
                    >
                      {l}
                    </button>
                  ))}
                </div>

                <div className="w-px h-5 mx-0.5" style={{ background: "var(--line-ctl)" }} />

                {/* Floodwater */}
                <LayerBtn
                  active={showFlood}
                  onClick={() => setShowFlood(v => !v)}
                  color="var(--flood-fill)"
                  label="Floodwater"
                />

                {/* Roads / Bridges */}
                <LayerBtn
                  active={showRoads}
                  onClick={() => setShowRoads(v => !v)}
                  color="var(--warn)"
                  label="Roads & bridges"
                />

                {/* Phone towers */}
                <LayerBtn
                  active={showTowers}
                  onClick={() => setShowTowers(v => !v)}
                  color="var(--confirmed)"
                  label="Infrastructure"
                />
              </div>
            )}
          </div>

          {/* ── Bottom dock ── */}
          {sitrep && (
            <div
              className="shrink-0 border-t"
              style={{ borderColor: "var(--line)", background: "var(--panel)" }}
            >
              {/* Dock tab bar */}
              <div
                className="flex items-center border-b px-2"
                style={{ borderColor: "var(--line-soft)" }}
              >
                <div role="tablist" aria-label="Analysis details" className="flex flex-1">
                  {([ 
                    ["reports", "Ground reports"],
                    ["brief", "WhatsApp brief"],
                    ["limits", "Limits and evaluation"],
                  ] as const).map(([id, label]) => (
                    <button
                      key={id}
                      type="button"
                      role="tab"
                      aria-selected={dockTab === id}
                      onClick={() => setDockTab(id)}
                      className="h-10 shrink-0 border-b-2 px-4 text-xs font-semibold transition-colors"
                      style={{
                        color: dockTab === id ? "var(--ink)" : "var(--ink-3)",
                        borderColor: dockTab === id ? "var(--flood)" : "transparent",
                      }}
                    >
                      {label}
                    </button>
                  ))}
                </div>
                <button
                  type="button"
                  aria-expanded={dockOpen}
                  onClick={() => setDockOpen(v => !v)}
                  className="shrink-0 rounded-md px-3 py-1 text-xs font-semibold"
                  style={{ color: "var(--ink-2)" }}
                >
                  {dockOpen ? "Collapse" : "Expand"}
                </button>
              </div>

              {/* Dock content */}
              {dockOpen && (
                <div className="overflow-y-auto p-4" style={{ maxHeight: "220px" }}>
                  {dockTab === "reports" && (
                    <div className="grid gap-3" style={{ gridTemplateColumns: "1fr 220px" }}>
                      <ReportPanel reports={sitrep.reports} />
                      <div>
                        <label
                          htmlFor="ground-report"
                          className="block mb-2 text-sm font-semibold"
                          style={{ color: "var(--ink)" }}
                        >
                          Add a ground report
                        </label>
                        <textarea
                          id="ground-report"
                          value={extraReport}
                          onChange={e => setExtraReport(e.target.value)}
                          placeholder="Paste a report in English or Hindi"
                          rows={4}
                          className="w-full resize-y rounded-lg p-3 text-sm"
                          style={{
                            background: "var(--sunken)",
                            border: "1px solid var(--line-ctl)",
                            color: "var(--ink-2)",
                          }}
                        />
                        <button
                          type="button"
                          onClick={submitReport}
                          disabled={!extraReport.trim() || running}
                          className="mt-2 w-full rounded-lg px-4 py-2 text-sm font-semibold text-white disabled:opacity-50 disabled:cursor-not-allowed"
                          style={{ background: extraReport.trim() && !running ? "var(--flood-fill)" : "var(--line-ctl)" }}
                        >
                          Add report and re-rank
                        </button>
                      </div>
                    </div>
                  )}
                  {dockTab === "brief" && <WhatsAppBrief sitrep={sitrep} lang={lang} />}
                  {dockTab === "limits" && <LimitationsPanel sitrep={sitrep} />}
                </div>
              )}
            </div>
          )}
        </div>

        {/* ── RIGHT SIDEBAR ── */}
        <aside
          className="flex flex-col min-h-0 border-l"
          style={{ borderColor: "var(--line)", background: "var(--panel)" }}
          data-testid="right-panel"
        >
          {/* Tab bar — right sidebar shows priorities by default; Brief/Limits sync the dock */}
          <div
            role="tablist"
            aria-label="Priority panel"
            className="flex shrink-0 border-b"
            style={{ borderColor: "var(--line-soft)" }}
          >
            {([ 
              ["priorities", "Reach first"],
              ["brief", "Brief"],
              ["limits", "Limits"],
            ] as const).map(([tab, label]) => {
              const isActive = tab === "priorities"
                ? dockTab !== "brief" && dockTab !== "limits"
                : dockTab === tab
              return (
                <button
                  key={tab}
                  type="button"
                  role="tab"
                  aria-selected={isActive}
                  onClick={() => {
                    if (tab === "priorities") {
                      setDockTab("reports")
                    } else {
                      setDockTab(tab as DockTab)
                    }
                  }}
                  className="flex-1 border-b-2 py-3 text-xs font-semibold transition-colors"
                  style={{
                    borderColor: isActive ? "var(--flood)" : "transparent",
                    color: isActive ? "var(--ink)" : "var(--ink-3)",
                  }}
                >
                  {label}
                </button>
              )
            })}
          </div>

          {/* Scrollable content */}
          <div className="flex-1 min-h-0 overflow-y-auto" data-testid="right-panel-scroll">
            {!sitrep && !running && (
              <div className="flex flex-col items-center justify-center h-full px-5 py-10 text-center">
                <p className="text-4xl mb-3">🛰️</p>
                <h2 className="text-base font-bold mb-2" style={{ color: "var(--ink)" }}>No analysis yet</h2>
                <p className="text-sm leading-relaxed mb-5 max-w-[200px]" style={{ color: "var(--ink-3)" }}>
                  Run the analysis to see which settlements need help first.
                </p>
                <button
                  type="button"
                  onClick={() => void runAnalysis()}
                  disabled={!selectedEvent}
                  className="rounded-lg px-4 py-2 text-sm font-semibold text-white disabled:opacity-50"
                  style={{ background: "var(--flood-fill)" }}
                >
                  Run analysis
                </button>
              </div>
            )}
            {!sitrep && running && <PrioritySkeleton />}
            {sitrep && dockTab !== "brief" && dockTab !== "limits" && (
              <PriorityList
                priorities={sitrep.priorities}
                selected={selectedSettlement}
                onSelect={setSelectedSettlement}
                lang={lang}
              />
            )}
            {sitrep && dockTab === "brief" && (
              <div className="p-4"><WhatsAppBrief sitrep={sitrep} lang={lang} /></div>
            )}
            {sitrep && dockTab === "limits" && (
              <div className="p-4"><LimitationsPanel sitrep={sitrep} /></div>
            )}
          </div>
        </aside>
      </div>
    </main>
  )
}

/* ── Sub-components ─────────────────────────────────────────────────────────── */

function StatCard({ children }: { children: React.ReactNode }) {
  return (
    <div
      className="rounded-xl p-4"
      style={{
        background: "var(--panel-2)",
        border: "1px solid var(--line)",
      }}
    >
      {children}
    </div>
  )
}

function LayerBtn({
  active,
  onClick,
  color,
  label,
}: {
  active: boolean
  onClick: () => void
  color: string
  label: string
}) {
  return (
    <button
      type="button"
      aria-pressed={active}
      onClick={onClick}
      className="flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-semibold transition-colors"
      style={{
        background: active ? `${color}22` : "transparent",
        color: active ? color : "var(--ink-3)",
        border: `1px solid ${active ? color : "transparent"}`,
      }}
    >
      <span
        className="w-2 h-2 rounded-full shrink-0"
        style={{ background: active ? color : "var(--ink-3)" }}
      />
      {label}
    </button>
  )
}

function PrioritySkeleton() {
  return (
    <div aria-label="Loading priorities" aria-live="polite" className="space-y-3 p-4">
      {[0, 1, 2, 3].map(i => (
        <div
          key={i}
          className="h-[58px] animate-pulse rounded-lg"
          style={{ background: "var(--panel-2)", border: "1px solid var(--line)" }}
        />
      ))}
    </div>
  )
}

function SkyReliefMark() {
  return (
    <svg aria-hidden="true" width="26" height="26" viewBox="0 0 30 30" fill="none">
      <circle cx="15" cy="15" r="13" stroke="var(--silent)" strokeWidth="2" strokeDasharray="3 3" />
      <circle cx="15" cy="15" r="7" stroke="var(--ink)" strokeWidth="2" />
      <circle cx="15" cy="15" r="2.5" fill="var(--flood)" />
    </svg>
  )
}
