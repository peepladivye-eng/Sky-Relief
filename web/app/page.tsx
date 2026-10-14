"use client"
import Link from "next/link"
import { useI18n } from "@/lib/i18n/context"

export default function HomePage() {
  const { s, lang, setLang } = useI18n()

  return (
    <div className="relative min-h-dvh overflow-x-hidden page-enter" style={{ background: "var(--bg)", color: "var(--ink)" }}>
      <div className="aurora" />

      {/* Skip link */}
      <a href="#main-content" className="sr-only focus:not-sr-only focus:absolute focus:z-50 focus:rounded focus:bg-white focus:p-2 focus:text-black">
        Skip to main content
      </a>

      {/* ── Nav pill ── */}
      <header className="sticky top-4 z-30 mx-auto flex max-w-6xl px-4">
        <nav className="glass flex w-full items-center gap-4 px-5 py-3" style={{ borderRadius: 999 }} aria-label="Main navigation">
          <Link href="/" className="flex items-center gap-2 shrink-0" aria-label="SkyRelief home">
            <SkyReliefMark />
            <span className="text-xl font-bold" style={{ fontFamily: "var(--font-bricolage)" }}>SkyRelief</span>
          </Link>
          <div className="hidden items-center gap-5 md:flex" role="list">
            {([["#product", s.nProduct], ["#how", s.nHow], ["#evidence", s.nEvidence], ["#limits", s.nLimits]] as const).map(([href, label]) => (
              <a key={href} href={href} className="text-sm font-semibold transition-colors hover:text-white" style={{ color: "var(--ink-2)" }}>{label}</a>
            ))}
          </div>
          <div className="flex-1" />
          <div className="neu-seg hidden sm:flex" role="group" aria-label="Language">
            <button type="button" className={`neu-seg-btn${lang === "en" ? " active" : ""}`} onClick={() => setLang("en")}>EN</button>
            <button type="button" className={`neu-seg-btn${lang === "hi" ? " active" : ""}`} onClick={() => setLang("hi")} style={{ fontFamily: "var(--font-devanagari)" }}>हिन्दी</button>
          </div>
          <Link href="/login" className="hidden text-sm font-semibold transition-colors hover:text-white sm:inline" style={{ color: "var(--ink-2)" }}>{s.signIn}</Link>
          <Link href="/login" className="clay inline-flex items-center rounded-2xl px-5 py-2 text-sm font-semibold text-white">{s.openCc}</Link>
        </nav>
      </header>

      <main id="main-content">
        {/* ── Hero ── */}
        <section id="product" className="mx-auto grid max-w-6xl grid-cols-1 gap-10 px-4 pb-16 pt-16 md:grid-cols-2 md:items-center md:pt-20">
          {/* Left */}
          <div>
            <span className="mb-5 inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-semibold" style={{ borderColor: "var(--line-ctl)", color: "var(--ink-2)", background: "var(--panel)" }}>
              <span className="h-2 w-2 rounded-full" style={{ background: "var(--silent)" }} />
              {s.badge}
            </span>
            <h1 className="mb-5 text-[clamp(2.2rem,5vw,4rem)] font-bold leading-[1.04] tracking-tight" style={{ fontFamily: "var(--font-bricolage)", color: "var(--ink)", textWrap: "balance" } as React.CSSProperties}>
              {s.h1}
            </h1>
            <p className="mb-8 text-lg leading-relaxed" style={{ color: "var(--ink-2)", maxWidth: 520 }}>{s.sub}</p>
            <div className="mb-6 flex flex-wrap gap-3">
              <Link href="/login" className="clay inline-flex items-center rounded-[20px] px-7 text-base font-semibold text-white" style={{ height: 54 }}>
                {s.ctaPrimary}
              </Link>
              <Link href="/login" className="glass inline-flex items-center rounded-[20px] px-7 text-base font-semibold" style={{ height: 54, color: "var(--ink)" }}>
                {s.signIn}
              </Link>
            </div>
            <div className="flex flex-wrap gap-2">
              {[["var(--flood)", "Sentinel-1"], ["var(--confirmed)", "OpenStreetMap"], ["var(--warn)", s.srcRain], ["var(--ink-3)", s.srcReports]].map(([color, label]) => (
                <span key={label} className="inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-semibold" style={{ borderColor: "var(--line-ctl)", color: "var(--ink-2)", background: "var(--panel)" }}>
                  <span className="h-2 w-2 rounded-full" style={{ background: color }} />
                  {label}
                </span>
              ))}
            </div>
          </div>

          {/* Right: stacked glass cards */}
          <div className="relative h-[420px]">
            {/* Map illustration */}
            <div className="glass absolute inset-0 overflow-hidden" style={{ borderRadius: 22 }}>
              <MapIllustration />
              <span className="absolute left-3 top-3 rounded-full border px-2 py-0.5 text-xs font-semibold" style={{ background: "rgba(10,19,26,.75)", borderColor: "var(--line-ctl)", color: "var(--ink-3)" }}>
                {s.illus}
              </span>
            </div>
            {/* Stat card 1 */}
            <div className="glass absolute -left-4 bottom-10 w-[220px] p-4" style={{ borderRadius: 18 }}>
              <p className="text-[34px] font-bold leading-none tabular-nums" style={{ fontFamily: "var(--font-bricolage)", color: "var(--ink)" }}>
                2,697 <span className="text-base font-normal" style={{ color: "var(--ink-3)" }}>km²</span>
              </p>
              <p className="mt-1 text-xs" style={{ color: "var(--ink-2)" }}>{s.statArea}</p>
              <p className="text-xs" style={{ color: "var(--ink-3)" }}>{s.statEvent}</p>
            </div>
            {/* Stat card 2 */}
            <div className="glass absolute -right-2 bottom-0 w-[220px] p-4" style={{ borderRadius: 18 }}>
              <div className="flex items-center justify-between gap-2">
                <span className="font-bold" style={{ color: "var(--ink)" }}>Hojai</span>
                <span className="chip-sl rounded-full px-2 py-0.5 text-xs font-semibold">{s.signalLost}</span>
              </div>
              <p className="mt-2 text-xs" style={{ color: "var(--ink-2)" }}>
                {s.statScore} <span className="text-lg font-bold tabular-nums" style={{ color: "var(--ink)", fontFamily: "var(--font-bricolage)" }}>70</span>
              </p>
            </div>
          </div>
        </section>

        {/* ── Evidence strip ── */}
        <section id="evidence" className="mx-auto max-w-6xl px-4 py-8">
          <div className="glass flex flex-wrap items-center justify-between gap-4 px-6 py-5">
            <p className="text-base" style={{ color: "var(--ink)", maxWidth: 520 }}>{s.evidence}</p>
            <div className="flex flex-wrap gap-2">
              {[s.chRadar, s.srcRain, s.srcReports, s.chRoad, s.chTower].map(chip => (
                <span key={chip} className="rounded-full border px-3 py-1 text-xs font-semibold" style={{ borderColor: "var(--line-ctl)", color: "var(--ink-2)", background: "var(--panel-2)" }}>{chip}</span>
              ))}
            </div>
          </div>
        </section>

        {/* ── Features ── */}
        <section className="mx-auto max-w-6xl px-4 py-12">
          <h2 className="mb-2 text-[2rem] font-bold tracking-tight" style={{ fontFamily: "var(--font-bricolage)", color: "var(--ink)" }}>{s.featTitle}</h2>
          <p className="mb-8 text-base" style={{ color: "var(--ink-3)" }}>{s.featLead}</p>
          <div className="grid gap-5 sm:grid-cols-3">
            {[
              { variant: "pink" as const,  icon: <SignalLostIcon />, h: s.f1h, p: s.f1p },
              { variant: "blue" as const,  icon: <RoadsIcon />,      h: s.f2h, p: s.f2p },
              { variant: "teal" as const,  icon: <BriefIcon />,      h: s.f3h, p: s.f3p },
            ].map(f => (
              <article key={f.h} className="rounded-[22px] border p-6" style={{ background: "var(--panel)", borderColor: "var(--line)" }}>
                <div className={`clay clay-${f.variant} mb-4 flex h-14 w-14 items-center justify-center`} style={{ borderRadius: 18 }}>
                  {f.icon}
                </div>
                <h3 className="mb-2 text-xl font-bold" style={{ fontFamily: "var(--font-bricolage)", color: "var(--ink)" }}>{f.h}</h3>
                <p className="text-sm leading-relaxed" style={{ color: "var(--ink-3)" }}>{f.p}</p>
              </article>
            ))}
          </div>
        </section>

        {/* ── How it works ── */}
        <section id="how" className="mx-auto max-w-6xl px-4 py-12">
          <h2 className="mb-8 text-[2rem] font-bold tracking-tight" style={{ fontFamily: "var(--font-bricolage)", color: "var(--ink)" }}>{s.howTitle}</h2>
          <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
            {[
              { icon: <RadarIcon />, h: s.s1h, p: s.s1p },
              { icon: <MaskIcon />,  h: s.s2h, p: s.s2p },
              { icon: <CheckIcon />, h: s.s3h, p: s.s3p },
              { icon: <RankIcon />,  h: s.s4h, p: s.s4p },
            ].map((step, i) => (
              <article key={step.h} className="neu-raised flex flex-col gap-3 p-6">
                <div className="neu-inset flex h-10 w-10 items-center justify-center" style={{ color: "var(--flood)" }}>
                  {step.icon}
                </div>
                <p className="text-xs font-semibold" style={{ color: "var(--ink-3)" }}>0{i + 1}</p>
                <h3 className="text-lg font-bold" style={{ fontFamily: "var(--font-bricolage)", color: "var(--ink)" }}>{step.h}</h3>
                <p className="text-sm leading-relaxed" style={{ color: "var(--ink-3)" }}>{step.p}</p>
              </article>
            ))}
          </div>
        </section>

        {/* ── Honest by design ── */}
        <section id="limits" className="mx-auto max-w-6xl px-4 py-12">
          <div className="neu-raised grid gap-8 p-8 md:grid-cols-2 md:items-center">
            <div>
              <h2 className="mb-3 text-[2rem] font-bold tracking-tight" style={{ fontFamily: "var(--font-bricolage)", color: "var(--ink)" }}>{s.honTitle}</h2>
              <p className="text-base leading-relaxed" style={{ color: "var(--ink-3)" }}>{s.honLead}</p>
            </div>
            <div className="flex flex-col gap-3">
              {[
                { color: "var(--warn)",  h: s.h1h, p: s.h1p },
                { color: "var(--ink-3)", h: s.h2h, p: s.h2p },
                { color: "var(--silent)",h: s.h3h, p: s.h3p },
              ].map(row => (
                <div key={row.h} className="neu-raised flex items-start gap-3 p-4">
                  <span className="mt-1 h-2 w-2 shrink-0 rounded-full" style={{ background: row.color }} />
                  <div>
                    <p className="font-semibold text-sm" style={{ color: "var(--ink)" }}>{row.h}</p>
                    <p className="text-xs leading-relaxed mt-0.5" style={{ color: "var(--ink-3)" }}>{row.p}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ── CTA ── */}
        <section className="mx-auto max-w-6xl px-4 py-12">
          <div className="glass glass-strong flex flex-col items-center gap-5 px-8 py-12 text-center">
            <h2 className="text-[2rem] font-bold tracking-tight" style={{ fontFamily: "var(--font-bricolage)", color: "var(--ink)", textWrap: "balance" } as React.CSSProperties}>{s.ctaTitle}</h2>
            <p className="text-base" style={{ color: "var(--ink-3)" }}>{s.ctaLead}</p>
            <div className="flex flex-wrap justify-center gap-3">
              <Link href="/login" className="clay inline-flex items-center rounded-[20px] px-8 text-base font-semibold text-white" style={{ height: 54 }}>
                {s.ctaPrimary}
              </Link>
              <Link href="/login" className="glass inline-flex items-center rounded-[20px] px-8 text-base font-semibold" style={{ height: 54, color: "var(--ink)" }}>
                {s.readLimits}
              </Link>
            </div>
          </div>
        </section>
      </main>

      {/* ── Footer ── */}
      <footer className="border-t px-4 py-8" style={{ borderColor: "var(--line)" }}>
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-4">
          <p className="text-sm" style={{ color: "var(--ink-3)" }}>{s.foot}</p>
          <div className="flex gap-4 text-sm" style={{ color: "var(--ink-3)" }}>
            <a href="#product" className="hover:text-white">{s.nProduct}</a>
            <a href="#limits" className="hover:text-white">{s.nLimits}</a>
            <div className="neu-seg" role="group" aria-label="Language">
              <button type="button" className={`neu-seg-btn${lang === "en" ? " active" : ""}`} onClick={() => setLang("en")}>EN</button>
              <button type="button" className={`neu-seg-btn${lang === "hi" ? " active" : ""}`} onClick={() => setLang("hi")} style={{ fontFamily: "var(--font-devanagari)" }}>हि</button>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}

/* ── Inline SVG icons ───────────────────────────────────────────── */
function SkyReliefMark() {
  return (
    <svg aria-hidden="true" width="28" height="28" viewBox="0 0 30 30" fill="none">
      <circle cx="15" cy="15" r="13" stroke="var(--silent)" strokeWidth="2" strokeDasharray="3 3" />
      <circle cx="15" cy="15" r="7" stroke="var(--ink)" strokeWidth="2" />
      <circle cx="15" cy="15" r="2.5" fill="var(--flood)" />
    </svg>
  )
}
function SignalLostIcon() { return <svg width="28" height="28" viewBox="0 0 30 30" fill="none" stroke="#fff" strokeWidth="2.2" strokeLinecap="round" aria-hidden="true"><circle cx="15" cy="15" r="11" strokeDasharray="3.5 4" /><circle cx="15" cy="15" r="4.5" /></svg> }
function RoadsIcon() { return <svg width="28" height="28" viewBox="0 0 30 30" fill="none" stroke="#fff" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M4 22c4-8 7-8 11-3s8 2 11-6" /><path d="M13 7l4 4M17 7l-4 4" /></svg> }
function BriefIcon() { return <svg width="28" height="28" viewBox="0 0 30 30" fill="none" stroke="#fff" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M5 7h20v13H13l-5 4v-4H5z" /><path d="M10 12h10M10 16h6" /></svg> }
function RadarIcon() { return <svg width="20" height="20" viewBox="0 0 22 22" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden="true"><path d="M3 8h7M3 14h7M12 5v12M15 8h4M15 14h4" /></svg> }
function MaskIcon() { return <svg width="20" height="20" viewBox="0 0 22 22" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden="true"><path d="M3 12c3-5 5-5 8 0s5 5 8 0" /></svg> }
function CheckIcon() { return <svg width="20" height="20" viewBox="0 0 22 22" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><circle cx="8" cy="11" r="5" /><circle cx="14" cy="11" r="5" /></svg> }
function RankIcon() { return <svg width="20" height="20" viewBox="0 0 22 22" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M4 6h14M4 11h10M4 16h6" /></svg> }

function MapIllustration() {
  return (
    <svg viewBox="0 0 560 400" width="100%" height="100%" preserveAspectRatio="xMidYMid slice" role="img" aria-label="Illustration of a river floodplain with a blue flood band and a signal-lost village marked in pink">
      <rect width="560" height="400" fill="#0B151C" />
      <path d="M0,300 C120,270 240,320 360,300 S520,290 560,310 L560,400 L0,400Z" fill="#0F1D26" />
      <g fill="none" stroke="#fff" strokeOpacity=".05"><path d="M0,120 C140,90 260,150 400,120 S520,100 560,110" /><path d="M0,150 C140,120 260,180 400,150 S520,130 560,140" /></g>
      <path d="M580,100 C470,140 400,120 320,140 S160,180 60,190 S-40,205 -60,208" stroke="#2F7FE8" strokeOpacity=".65" strokeWidth="76" fill="none" strokeLinecap="round" />
      <path d="M330,150 C335,220 300,260 312,300" stroke="#2F7FE8" strokeOpacity=".6" strokeWidth="34" fill="none" strokeLinecap="round" />
      <path d="M580,112 C470,152 400,132 320,152 S160,192 60,202" stroke="#4C9BFF" strokeWidth="3" fill="none" />
      <g transform="translate(312,296)">
        <circle className="signal-ping signal-ping-d2" r="26" fill="none" stroke="#FF5C80" strokeWidth="2" strokeDasharray="4 4" />
        <circle className="signal-ping signal-ping-d3" r="26" fill="none" stroke="#FF5C80" strokeWidth="2" strokeDasharray="4 4" />
        <circle r="14" fill="none" stroke="#FF5C80" strokeWidth="2" strokeDasharray="4 4" />
        <circle r="4" fill="#0B151C" stroke="#E7EEF0" strokeWidth="2" />
      </g>
    </svg>
  )
}
