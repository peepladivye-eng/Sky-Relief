import type { Metadata } from "next"
import { Bricolage_Grotesque, Hanken_Grotesk, Noto_Sans_Devanagari } from "next/font/google"
import "./globals.css"
import { I18nProvider } from "@/lib/i18n/context"

const bricolage = Bricolage_Grotesque({
  subsets: ["latin"],
  variable: "--font-bricolage",
  display: "swap",
})

const hanken = Hanken_Grotesk({
  subsets: ["latin"],
  variable: "--font-hanken",
  display: "swap",
})

const notoDevanagari = Noto_Sans_Devanagari({
  subsets: ["devanagari"],
  weight: ["400", "500", "600"],
  variable: "--font-devanagari",
  display: "swap",
})

export const metadata: Metadata = {
  title: "SkyRelief — Multimodal Disaster Response",
  description: "Satellite + AI flood response agent. Finds flooded villages that need help first.",
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body
        className={`${hanken.variable} ${bricolage.variable} ${notoDevanagari.variable}`}
        style={{ fontFamily: "var(--font-hanken, 'Hanken Grotesk'), system-ui, sans-serif" }}
        suppressHydrationWarning
      >
        <I18nProvider>
          {children}
        </I18nProvider>
      </body>
    </html>
  )
}
