import { NextRequest, NextResponse } from "next/server"
import bcrypt from "bcryptjs"
import { signSession, sessionCookieOptions } from "@/lib/auth/session"
import { checkRateLimit, resetRateLimit } from "@/lib/auth/rate-limit"
import type { Role } from "@/lib/auth/session"

interface DemoUser { email: string; passwordHash: string }

function getUsers(): DemoUser[] {
  try {
    const raw = process.env.SKYRELIEF_DEMO_USERS
    if (raw) return JSON.parse(raw) as DemoUser[]
  } catch {}
  // Default demo user for development (password: "skyrelief2026")
  return [{ email: "demo@skyrelief.app", passwordHash: "$2a$10$YourHashHere.replaceWithRealBcryptHash" }]
}

export async function POST(req: NextRequest) {
  const ip = req.headers.get("x-forwarded-for")?.split(",")[0]?.trim() ?? "unknown"
  const { allowed } = checkRateLimit(ip)

  if (!allowed) {
    return NextResponse.json({ error: "rate_limit" }, { status: 429 })
  }

  let body: { email?: string; password?: string; role?: Role; remember?: boolean }
  try { body = await req.json() } catch { return NextResponse.json({ error: "bad_request" }, { status: 400 }) }

  const { email, password, role = "observer", remember = false } = body
  if (!email || !password) return NextResponse.json({ error: "bad_request" }, { status: 400 })

  const users = getUsers()
  const user = users.find(u => u.email.toLowerCase() === email.toLowerCase())

  // Generic error — never reveal which field is wrong
  const invalid = () => NextResponse.json({ error: "invalid_credentials" }, { status: 401 })

  if (!user) return invalid()

  const match = await bcrypt.compare(password, user.passwordHash)
  if (!match) return invalid()

  resetRateLimit(ip)
  const token = await signSession({ sub: user.email, role }, remember)
  const opts = sessionCookieOptions(remember)

  const res = NextResponse.json({ ok: true, role })
  res.cookies.set({ ...opts, value: token })
  return res
}
