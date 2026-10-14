import Link from "next/link"

export default function NotFound() {
  return (
    <main className="relative flex min-h-dvh flex-col items-center justify-center gap-6 p-8 text-center" style={{ background: "var(--bg)", color: "var(--ink)" }}>
      <div className="aurora" />
      <div className="relative z-10 page-enter">
        <p className="mb-2 text-7xl font-bold" style={{ fontFamily: "var(--font-bricolage)", color: "var(--flood)" }}>404</p>
        <h1 className="mb-3 text-2xl font-bold">Page not found</h1>
        <p className="mb-8 text-sm" style={{ color: "var(--ink-3)" }}>The page you are looking for does not exist.</p>
        <Link href="/" className="clay inline-flex items-center rounded-[16px] px-6 py-3 text-sm font-semibold text-white">
          Go home
        </Link>
      </div>
    </main>
  )
}
