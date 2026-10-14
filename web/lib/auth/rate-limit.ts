// In-memory rate limiter: 5 failed attempts per IP per minute
const attempts = new Map<string, { count: number; resetAt: number }>()
const LIMIT = 5
const WINDOW_MS = 60_000

export function checkRateLimit(ip: string): { allowed: boolean; remaining: number } {
  const now = Date.now()
  const entry = attempts.get(ip)
  if (!entry || now > entry.resetAt) {
    attempts.set(ip, { count: 1, resetAt: now + WINDOW_MS })
    return { allowed: true, remaining: LIMIT - 1 }
  }
  if (entry.count >= LIMIT) return { allowed: false, remaining: 0 }
  entry.count++
  return { allowed: true, remaining: LIMIT - entry.count }
}

export function resetRateLimit(ip: string): void {
  attempts.delete(ip)
}
