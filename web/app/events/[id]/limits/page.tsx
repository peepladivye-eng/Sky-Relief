import { redirect } from "next/navigation"
import Link from "next/link"
import { getSession } from "@/lib/auth/session"

interface Props { params: Promise<{ id: string }> }

export default async function LimitsPage({ params }: Props) {
  const session = await getSession()
  if (!session) redirect("/login")

  const { id } = await params
  const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"

  // Fetch sitrep data server-side
  let limitations: string[] = []
  let evalData: { flood_mask_iou?: string; cut_off_precision?: string; bridges_precision?: string } = {}
  try {
    const cacheRes = await fetch(`${API}/eval/${id}`, { next: { revalidate: 60 } })
    if (cacheRes.ok) evalData = await cacheRes.json() as typeof evalData
  } catch {}

  // Limitations are in the brief cache
  try {
    const briefRes = await fetch(`${API}/export/${id}.md`, { next: { revalidate: 60 } })
    if (briefRes.ok) {
      const md = await briefRes.text()
      const section = md.split("## Limitations")[1]
      if (section) {
        limitations = section.split("\n").filter(l => l.startsWith("- ")).map(l => l.slice(2).trim())
      }
    }
  } catch {}

  return (
    <main className="relative min-h-dvh" style={{ background: "var(--bg)", color: "var(--ink)" }}>
      <div className="aurora" />
      <div className="relative z-10 mx-auto max-w-3xl px-4 py-10 page-enter">
        <Link
          href={`/events/${id}`}
          className="mb-6 inline-flex items-center gap-2 text-sm font-semibold"
          style={{ color: "var(--flood)" }}
        >
          ← Back to map
        </Link>

        <h1 className="mb-8 text-3xl font-bold" style={{ fontFamily: "var(--font-bricolage)", color: "var(--ink)" }}>
          Limits and evaluation
        </h1>

        {/* Limitations */}
        <section className="neu-raised mb-6 p-6">
          <h2 className="mb-4 text-lg font-bold" style={{ color: "var(--ink)" }}>What this can miss</h2>
          {limitations.length > 0 ? (
            <ul className="space-y-3 text-sm leading-relaxed" style={{ color: "var(--ink-2)", paddingLeft: "1.25rem" }}>
              {limitations.map((l, i) => <li key={i}>{l}</li>)}
            </ul>
          ) : (
            <ul className="space-y-3 text-sm leading-relaxed" style={{ color: "var(--ink-2)", paddingLeft: "1.25rem" }}>
              <li>The language model check was skipped because no API key is set.</li>
              <li>Radar can miss flooded buildings in cities (double-bounce effect).</li>
              <li>Reports can be incomplete. Villages with signal lost are unverified.</li>
              <li>The flood mask resolution is about 10 m.</li>
              <li>Steep terrain shadow and layover can mimic water in mountain areas.</li>
            </ul>
          )}
        </section>

        {/* Evaluation table */}
        <section className="neu-raised p-6">
          <h2 className="mb-4 text-lg font-bold" style={{ color: "var(--ink)" }}>Evaluation</h2>
          <table className="w-full text-sm" style={{ borderCollapse: "collapse" }}>
            <tbody>
              {[
                ["Flood mask overlap (IoU)", evalData.flood_mask_iou ?? "Not measured"],
                ["Cut-off villages, precision and recall", evalData.cut_off_precision ?? "Not measured"],
                ["Bridges likely out, precision and recall", evalData.bridges_precision ?? "Not measured"],
              ].map(([label, value]) => (
                <tr key={label} style={{ borderTop: "1px solid var(--line-soft)" }}>
                  <td className="py-3 pr-4" style={{ color: "var(--ink-2)" }}>{label}</td>
                  <td className="py-3 text-right" style={{ color: "var(--ink-3)", whiteSpace: "nowrap" }}>{value}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>

        <p className="mt-6 text-xs leading-relaxed" style={{ color: "var(--ink-3)" }}>
          Evaluation figures are computed only where a reference flood extent is available (e.g., Copernicus EMS, UNOSAT). &quot;Not measured&quot; means no reference was found for this event — not that the system performed poorly.
        </p>
      </div>
    </main>
  )
}
