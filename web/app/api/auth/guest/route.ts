import { NextResponse } from "next/server"
import { signSession, sessionCookieOptions } from "@/lib/auth/session"

export async function POST() {
  const token = await signSession({ sub: "guest", role: "observer" }, false)
  const opts = sessionCookieOptions(false)
  const res = NextResponse.json({ ok: true, role: "observer" })
  res.cookies.set({ ...opts, value: token })
  return res
}
