import { SignJWT, jwtVerify } from "jose"
import { cookies } from "next/headers"
import { NextRequest } from "next/server"

const COOKIE = "sr_session"
const ALG = "HS256"

export type Role = "responder" | "analyst" | "observer"

export interface SessionPayload {
  sub: string
  role: Role
  iat?: number
  exp?: number
}

function getSecret(): Uint8Array {
  const s = process.env.SKYRELIEF_SESSION_SECRET ?? "dev-secret-change-in-production-min32chars!!"
  return new TextEncoder().encode(s)
}

export async function signSession(
  payload: Omit<SessionPayload, "iat" | "exp">,
  remember: boolean
): Promise<string> {
  const exp = remember ? "7d" : "8h"
  return new SignJWT({ sub: payload.sub, role: payload.role })
    .setProtectedHeader({ alg: ALG })
    .setIssuedAt()
    .setExpirationTime(exp)
    .sign(getSecret())
}

export async function verifySession(token: string): Promise<SessionPayload | null> {
  try {
    const { payload } = await jwtVerify(token, getSecret())
    return payload as unknown as SessionPayload
  } catch {
    return null
  }
}

export async function getSession(): Promise<SessionPayload | null> {
  const store = await cookies()
  const token = store.get(COOKIE)?.value
  if (!token) return null
  return verifySession(token)
}

export async function getSessionFromRequest(req: NextRequest): Promise<SessionPayload | null> {
  const token = req.cookies.get(COOKIE)?.value
  if (!token) return null
  return verifySession(token)
}

export function sessionCookieOptions(remember: boolean) {
  return {
    name: COOKIE,
    httpOnly: true,
    sameSite: "lax" as const,
    secure: process.env.NODE_ENV === "production",
    maxAge: remember ? 60 * 60 * 24 * 7 : undefined,
    path: "/",
  }
}
