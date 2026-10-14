import { NextResponse, type NextRequest } from "next/server"
import { getSessionFromRequest } from "@/lib/auth/session"

// Use Node.js runtime so jose can access crypto primitives
export const runtime = "nodejs"

export const config = { matcher: ["/events/:path*"] }

export async function middleware(req: NextRequest) {
  const session = await getSessionFromRequest(req)
  if (!session) {
    const next = encodeURIComponent(req.nextUrl.pathname + req.nextUrl.search)
    return NextResponse.redirect(new URL(`/login?next=${next}`, req.url))
  }
  return NextResponse.next()
}
