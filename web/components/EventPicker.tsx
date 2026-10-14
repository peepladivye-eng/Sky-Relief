"use client"
import { useEffect, useState } from "react"
import type { SkyEvent } from "@/app/types"

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export default function EventPicker({ onSelect, selected }: { onSelect: (ev: SkyEvent) => void; selected: SkyEvent | null }) {
  const [events, setEvents] = useState<SkyEvent[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)
  const [open, setOpen] = useState(false)

  useEffect(() => {
    fetch(`${API}/events`)
      .then(r => r.json())
      .then(data => { setEvents(data); setLoading(false) })
      .catch(() => { setError(true); setLoading(false) })
  }, [])

  if (loading) return <span style={{ color: "var(--ink-3)" }}>Loading...</span>
  if (error) return <span style={{ color: "var(--silent)" }}>API not available</span>

  return (
    <div className="relative">
      <button
        type="button"
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-label={selected ? `Selected event: ${selected.name}` : "Choose event"}
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 px-3 py-1.5 rounded-lg transition-colors"
        style={{
          background: "var(--sunken)",
          border: "1px solid var(--line-ctl)",
          color: "var(--ink)",
        }}
      >
        <span className="max-w-[min(32vw,20rem)] truncate text-14 font-medium max-[560px]:max-w-[26vw]">
          {selected ? selected.name : "Select event..."}
        </span>
        <svg width="12" height="12" viewBox="0 0 12 12" fill="none" className={`transition-transform ${open ? "rotate-180" : ""}`}>
          <path d="M3 4.5L6 7.5L9 4.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
      </button>

      {open && (
        <>
          <button type="button" aria-label="Close event list" className="fixed inset-0 z-40 cursor-default" onClick={() => setOpen(false)} />
          <div
            role="listbox"
            aria-label="Events"
            className="absolute left-0 top-full z-50 mt-2 max-h-[70vh] w-[min(20rem,calc(100vw-2rem))] overflow-y-auto rounded-lg shadow-lg"
            style={{
              background: "var(--panel)",
              border: "1px solid var(--line)",
              boxShadow: "var(--shadow-float)",
            }}
          >
            {events.map(ev => (
              <button
                key={ev.event_id}
                type="button"
                role="option"
                aria-selected={selected?.event_id === ev.event_id}
                onClick={() => {
                  onSelect(ev)
                  setOpen(false)
                }}
                className="w-full text-left p-3 transition-colors border-b"
                style={{
                  borderColor: "var(--line-soft)",
                  background: selected?.event_id === ev.event_id ? "var(--panel-2)" : "transparent",
                }}
                onMouseEnter={(e) => e.currentTarget.style.background = "var(--panel-2)"}
                onMouseLeave={(e) => {
                  if (selected?.event_id !== ev.event_id) {
                    e.currentTarget.style.background = "transparent"
                  }
                }}
              >
                <div className="text-14 font-medium mb-1" style={{ color: "var(--ink)" }}>
                  {ev.name}
                </div>
                <div className="text-12" style={{ color: "var(--ink-3)" }}>
                  {ev.before_date} → {ev.after_date} · {ev.sensor}
                </div>
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  )
}
