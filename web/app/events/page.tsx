"use client"
import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import type { SkyEvent } from "@/app/types"
import { useI18n } from "@/lib/i18n/context"
import UserMenu from "@/components/ui2/UserMenu"

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"

export default function EventsPage() {
  const { s, lang, setLang } = useI18n()
  const router = useRouter()
  const [events, setEvents] = useState<SkyEvent[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")

  useEffect(() => {
    fetch(`${API}/events`)
      .then(r => r.json())
      .then((data: SkyEvent[]) => {
        setEvents(data)
        if (data.length === 1) {
          router.replace(`/events/${data[0].event_id}`)
        }
      })
      .catch(() => setError("Could not load events from the API."))
      .finally(() => setLoading(false))
  }, [router])

  return (
    <main className="relative min-h-dvh page-enter" style={{ background: "var(--bg)", color: "var(--ink)" }}>
      <div className="aurora" />

      {/* Top bar */}
      <header
        className="glass-strong relative z-20 flex h-14 items-center gap-3 border-b px-4"
        style={{ borderColor: "var(--line)", borderRadius: 0 }}
      >
        <Link href="/" className="flex items-center gap-2" aria-label="SkyRelief home">
          <SkyReliefMark />
          <span className="text-lg font-bold" style={{ fontFamily: "var(--font-bricolage)" }}>SkyRelief</span>
        </Link>
        <div className="flex-1" />
        <div className="neu-seg" role="group" aria-label="Language">
          <button type="button" className={`neu-seg-btn${lang === "en" ? " active" : ""}`} onClick={() => setLang("en")}>EN</button>
          <button type="button" className={`neu-seg-btn${lang === "hi" ? " active" : ""}`} onClick={() => setLang("hi")} style={{ fontFamily: "var(--font-devanagari)" }}>हिन्दी</button>
        </div>
        <UserMenu sub="guest" role="observer" lang={lang} />
      </header>

      <div className="relative z-10 mx-auto max-w-4xl px-4 py-12">
        <h1 className="mb-8 text-3xl font-bold" style={{ fontFamily: "var(--font-bricolage)", color: "var(--ink)" }}>
          {s.eventsTitle}
        </h1>

        {loading && (
          <p className="text-sm" style={{ color: "var(--ink-3)" }}>{s.eventsLoading}</p>
        )}

        {error && (
          <p className="rounded-xl border px-4 py-3 text-sm" style={{ background: "var(--chip-sl-bg)", color: "var(--chip-sl-text)", borderColor: "var(--chip-sl-bd)" }}>
            {error}
          </p>
        )}

        {!loading && !error && events.length === 0 && (
          <p className="rounded-xl border px-4 py-3 text-sm" style={{ background: "var(--panel)", color: "var(--ink-3)", borderColor: "var(--line)" }}>
            {s.eventsEmpty}
          </p>
        )}

        <div className="grid gap-4 sm:grid-cols-2">
          {events.map(ev => (
            <Link
              key={ev.event_id}
              href={`/events/${ev.event_id}`}
              className="neu-raised block p-5 transition-all hover:scale-[1.01]"
              style={{ textDecoration: "none" }}
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="font-semibold leading-snug" style={{ color: "var(--ink)" }}>{ev.name}</p>
                  <p className="mt-1 text-xs" style={{ color: "var(--ink-3)" }}>
                    {ev.before_date} → {ev.after_date}
                  </p>
                  <p className="mt-0.5 text-xs" style={{ color: "var(--ink-3)" }}>{ev.sensor}</p>
                </div>
                <span
                  className="shrink-0 rounded-full px-2 py-0.5 text-xs font-semibold chip-fl"
                >
                  {ev.sensor.includes("1") ? "SAR" : "Optical"}
                </span>
              </div>
            </Link>
          ))}
        </div>
      </div>
    </main>
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
