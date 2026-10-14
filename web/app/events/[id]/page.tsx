import { redirect } from "next/navigation"
import { getSession } from "@/lib/auth/session"
import ResponseDesk from "@/components/ResponseDesk"

interface EventPageProps {
  params: Promise<{ id: string }>
}

export default async function CommandCenterPage({ params }: EventPageProps) {
  // Middleware already guards this route, but double-check server-side
  const session = await getSession()
  if (!session) redirect("/login")
  
  const { id } = await params
  return <ResponseDesk initialEventId={id} />
}
