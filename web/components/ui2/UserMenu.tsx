"use client"
import { useState, useRef, useEffect } from "react"
import { useRouter } from "next/navigation"
import type { Role } from "@/lib/auth/session"
import { ROLE_CONFIG } from "@/lib/auth/roles"

interface Props {
  sub: string
  role: Role
  lang?: "en" | "hi"
  eventId?: string
}

export default function UserMenu({ sub, role, lang = "en", eventId }: Props) {
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)
  const router = useRouter()
  const cfg = ROLE_CONFIG[role]
  const initials = sub === "guest" ? "G" : sub.slice(0, 2).toUpperCase()

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener("mousedown", handler)
    return () => document.removeEventListener("mousedown", handler)
  }, [])

  const logout = async () => {
    await fetch("/api/auth/logout", { method: "POST" })
    router.push("/")
    router.refresh()
  }

  return (
    <div ref={ref} className="relative">
      <button
        type="button"
        aria-haspopup="true"
        aria-expanded={open}
        onClick={() => setOpen(v => !v)}
        className="flex items-center gap-2 rounded-xl px-2 py-1 transition-colors hover:bg-white/5"
      >
        <span
          className="flex h-8 w-8 items-center justify-center rounded-full text-sm font-bold text-white"
          style={{ background: "var(--flood-fill)" }}
        >
          {initials}
        </span>
        <span
          className="hidden rounded-full px-2 py-0.5 text-xs font-semibold sm:inline-block"
          style={{ background: "var(--panel-2)", color: "var(--ink-3)", border: "1px solid var(--line-ctl)" }}
        >
          {lang === "hi" ? cfg.labelHi : cfg.label}
        </span>
      </button>

      {open && (
        <div
          className="glass absolute right-0 top-full z-50 mt-2 min-w-[180px] overflow-hidden p-1"
          style={{ borderRadius: "14px" }}
        >
          {eventId && (
            <MenuItem onClick={() => { router.push("/events"); setOpen(false) }}>
              Switch event
            </MenuItem>
          )}
          {eventId && (
            <MenuItem onClick={() => { router.push(`/events/${eventId}/limits`); setOpen(false) }}>
              {lang === "hi" ? "सीमाएँ" : "Limits and evaluation"}
            </MenuItem>
          )}
          <div style={{ height: 1, background: "var(--line-soft)", margin: "4px 0" }} />
          <MenuItem onClick={logout} danger>
            {lang === "hi" ? "साइन आउट" : "Sign out"}
          </MenuItem>
        </div>
      )}
    </div>
  )
}

function MenuItem({ children, onClick, danger = false }: { children: React.ReactNode; onClick: () => void; danger?: boolean }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="w-full rounded-lg px-3 py-2 text-left text-sm font-medium transition-colors hover:bg-white/5"
      style={{ color: danger ? "var(--silent)" : "var(--ink-2)" }}
    >
      {children}
    </button>
  )
}
