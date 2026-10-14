"use client"
import { Suspense, useState, FormEvent, useEffect } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import Link from "next/link"
import type { Role } from "@/lib/auth/session"
import { ROLE_CONFIG } from "@/lib/auth/roles"
import { useI18n } from "@/lib/i18n/context"

type Status = "idle" | "loading" | "error" | "rate_limit" | "success"

function LoginForm() {
  const { s, lang, setLang } = useI18n()
  const router = useRouter()
  const params = useSearchParams()
  const next = params.get("next") ?? "/events"

  const [role, setRole] = useState<Role>("responder")
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [showPw, setShowPw] = useState(false)
  const [remember, setRemember] = useState(true)
  const [showForgot, setShowForgot] = useState(false)
  const [status, setStatus] = useState<Status>("idle")
  const [shake, setShake] = useState(false)

  // Clear error on Escape
  useEffect(() => {
    const h = (e: KeyboardEvent) => { if (e.key === "Escape") setStatus("idle") }
    window.addEventListener("keydown", h)
    return () => window.removeEventListener("keydown", h)
  }, [])

  const submit = async (e: FormEvent) => {
    e.preventDefault()
    if (status === "loading") return
    setStatus("loading")
    try {
      const res = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password, role, remember }),
      })
      if (res.ok) {
        setStatus("success")
        setTimeout(() => router.push(decodeURIComponent(next)), 800)
      } else {
        const data = await res.json() as { error: string }
        setStatus(data.error === "rate_limit" ? "rate_limit" : "error")
        setShake(true)
        setTimeout(() => setShake(false), 400)
      }
    } catch {
      setStatus("error")
      setShake(true)
      setTimeout(() => setShake(false), 400)
    }
  }

  const guestLogin = async () => {
    const res = await fetch("/api/auth/guest", { method: "POST" })
    if (res.ok) router.push(decodeURIComponent(next))
  }

  const roles: { key: Role; label: string; labelHi: string; icon: React.ReactNode }[] = [
    {
      key: "responder", label: s.rResp, labelHi: s.rResp,
      icon: <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M12 3l8 4v5c0 5-3.5 8-8 9-4.5-1-8-4-8-9V7z"/></svg>,
    },
    {
      key: "analyst", label: s.rAna, labelHi: s.rAna,
      icon: <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M4 19V9M10 19V5M16 19v-7M21 19H3"/></svg>,
    },
    {
      key: "observer", label: s.rObs, labelHi: s.rObs,
      icon: <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/></svg>,
    },
  ]

  const errorMsg = status === "rate_limit" ? s.loginRateLimit : s.loginError
  const btnLabel = status === "loading" ? s.loginLoading : status === "success" ? s.loginSuccess : s.loginBtn
  const roleDesc = ROLE_CONFIG[role][lang === "hi" ? "descriptionHi" : "description"]

  return (
    <main className="relative min-h-dvh flex items-center justify-center p-4" style={{ background: "var(--bg)" }}>
      {/* Aurora */}
      <div className="aurora" />

      {/* Back link */}
      <Link
        href="/"
        className="absolute left-6 top-5 z-10 flex items-center gap-2"
        aria-label="SkyRelief home"
      >
        <SkyReliefMark />
        <span className="text-xl font-bold" style={{ fontFamily: "var(--font-bricolage)" }}>SkyRelief</span>
      </Link>

      {/* Card */}
      <div
        className={`glass relative z-10 w-full max-w-[460px] p-8 flex flex-col gap-5 page-enter${shake ? " animate-shake" : ""}`}
        style={{ borderRadius: 28 }}
      >
        <div>
          <h1 className="text-[28px] font-bold leading-tight" style={{ fontFamily: "var(--font-bricolage)", color: "var(--ink)" }}>
            {s.loginTitle}
          </h1>
          <p className="mt-2 text-sm" style={{ color: "var(--ink-3)" }}>{s.loginSub}</p>
        </div>

        {/* Role picker */}
        <fieldset style={{ border: 0, padding: 0, margin: 0 }}>
          <legend className="mb-2 text-xs font-semibold" style={{ color: "var(--ink-2)" }}>{s.roleLabel}</legend>
          <div className="grid grid-cols-3 gap-2">
            {roles.map(r => {
              const active = role === r.key
              return (
                <button
                  key={r.key}
                  type="button"
                  aria-pressed={active}
                  onClick={() => setRole(r.key)}
                  className={`flex flex-col items-center gap-2 rounded-[18px] px-3 py-3 text-xs font-semibold transition-all ${active ? "clay text-white" : "neu-raised"}`}
                  style={active ? {} : { color: "var(--ink-3)" }}
                >
                  {r.icon}
                  {r.label}
                </button>
              )
            })}
          </div>
          <p className="mt-2 text-xs" style={{ color: "var(--ink-3)", minHeight: 18 }} aria-live="polite">
            {roleDesc}
          </p>
        </fieldset>

        <form onSubmit={submit} noValidate className="flex flex-col gap-4">
          {/* Email */}
          <div>
            <label htmlFor="email" className="mb-2 block text-xs font-semibold" style={{ color: "var(--ink-2)" }}>
              {s.email}
            </label>
            <input
              id="email"
              type="email"
              autoComplete="username"
              placeholder="name@example.com"
              value={email}
              onChange={e => setEmail(e.target.value)}
              required
              className="neu-inset block w-full px-4 text-sm"
              style={{ height: 50, color: "var(--ink)" }}
            />
          </div>

          {/* Password */}
          <div>
            <label htmlFor="password" className="mb-2 block text-xs font-semibold" style={{ color: "var(--ink-2)" }}>
              {s.password}
            </label>
            <div className="relative">
              <input
                id="password"
                type={showPw ? "text" : "password"}
                autoComplete="current-password"
                placeholder="••••••••"
                value={password}
                onChange={e => setPassword(e.target.value)}
                required
                className="neu-inset block w-full px-4 text-sm"
                style={{ height: 50, paddingRight: 80, color: "var(--ink)" }}
              />
              <button
                type="button"
                aria-label={showPw ? s.hidePwLabel : s.showPwLabel}
                onClick={() => setShowPw(v => !v)}
                className="absolute right-2 top-2 rounded-lg px-2 py-1.5 text-xs font-semibold"
                style={{ color: "var(--ink-3)" }}
              >
                {showPw ? s.hidePw : s.showPw}
              </button>
            </div>
          </div>

          {/* Remember + Forgot */}
          <div className="flex items-center justify-between gap-3">
            <button
              type="button"
              role="switch"
              aria-checked={remember}
              onClick={() => setRemember(v => !v)}
              className="flex items-center gap-2 text-sm"
              style={{ color: "var(--ink-2)", background: "none", border: 0 }}
            >
              <span
                className="relative inline-block h-6 w-11 rounded-full transition-colors"
                style={{ background: remember ? "var(--flood-fill)" : "var(--line-ctl)" }}
              >
                <span
                  className="absolute top-0.5 h-5 w-5 rounded-full bg-white shadow transition-all"
                  style={{ left: remember ? "calc(100% - 22px)" : 2 }}
                />
              </span>
              {s.remember}
            </button>
            <button
              type="button"
              onClick={() => setShowForgot(v => !v)}
              className="text-sm font-medium"
              style={{ color: "var(--flood)", background: "none", border: 0 }}
            >
              {s.forgot}
            </button>
          </div>

          {showForgot && (
            <p className="rounded-xl px-4 py-3 text-xs" style={{ background: "rgba(255,255,255,0.06)", color: "var(--ink-3)" }}>
              {s.forgotHelp}
            </p>
          )}

          {/* Error */}
          {(status === "error" || status === "rate_limit") && (
            <p role="alert" className="rounded-xl border px-4 py-3 text-sm" style={{ background: "var(--chip-sl-bg)", color: "var(--chip-sl-text)", borderColor: "var(--chip-sl-bd)" }}>
              {errorMsg}
            </p>
          )}
          {status === "success" && (
            <p role="status" className="rounded-xl border px-4 py-3 text-sm" style={{ background: "var(--chip-ok-bg)", color: "var(--chip-ok-text)", borderColor: "var(--chip-ok-bd)" }}>
              {s.loginSuccess}
            </p>
          )}

          {/* Submit */}
          <button
            type="submit"
            disabled={status === "loading" || status === "success"}
            className="clay flex w-full items-center justify-center gap-2 text-base font-semibold text-white"
            style={{ height: 54, borderRadius: 20 }}
          >
            {status === "loading" && (
              <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/40 border-t-white" aria-hidden="true" />
            )}
            {btnLabel}
          </button>
        </form>

        {/* Divider */}
        <div className="flex items-center gap-3 text-xs" style={{ color: "var(--ink-3)" }}>
          <span className="flex-1 border-t" style={{ borderColor: "var(--line-soft)" }} />
          {s.or}
          <span className="flex-1 border-t" style={{ borderColor: "var(--line-soft)" }} />
        </div>

        {/* Guest */}
        <button
          type="button"
          onClick={guestLogin}
          className="glass flex w-full items-center justify-center rounded-[18px] py-3 text-sm font-semibold"
          style={{ color: "var(--ink-2)" }}
        >
          {s.guest}
        </button>

        {/* Note */}
        <p className="text-center text-xs leading-relaxed" style={{ color: "var(--ink-3)" }}>{s.loginNote}</p>

        {/* Language switcher */}
        <div className="flex items-center justify-center gap-3 text-xs">
          <button type="button" aria-pressed={lang === "en"} onClick={() => setLang("en")} className="font-semibold" style={{ color: lang === "en" ? "var(--flood)" : "var(--ink-3)", background: "none", border: 0 }}>English</button>
          <span style={{ color: "var(--line-ctl)" }}>|</span>
          <button type="button" aria-pressed={lang === "hi"} onClick={() => setLang("hi")} className="font-semibold" style={{ color: lang === "hi" ? "var(--flood)" : "var(--ink-3)", background: "none", border: 0, fontFamily: "var(--font-devanagari)" }}>हिन्दी</button>
        </div>
      </div>

      <style>{`
        @keyframes shake { 0%,100%{transform:translateX(0)} 25%{transform:translateX(-3px)} 75%{transform:translateX(3px)} }
        .animate-shake { animation: shake 0.32s ease-in-out; }
      `}</style>
    </main>
  )
}

function SkyReliefMark() {
  return (
    <svg aria-hidden="true" width="28" height="28" viewBox="0 0 30 30" fill="none">
      <circle cx="15" cy="15" r="13" stroke="var(--silent)" strokeWidth="2" strokeDasharray="3 3" />
      <circle cx="15" cy="15" r="7" stroke="var(--ink)" strokeWidth="2" strokeDasharray="3 3" />
      <circle cx="15" cy="15" r="2.6" fill="var(--ink)" />
    </svg>
  )
}

export default function LoginPage() {
  return (
    <Suspense fallback={<div style={{ minHeight: "100dvh", background: "var(--bg)" }} />}>
      <LoginForm />
    </Suspense>
  )
}
