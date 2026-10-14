"use client"
import { useState } from "react"
import type { Sitrep } from "@/app/types"

export default function WhatsAppBrief({ sitrep, lang }: { sitrep: Sitrep; lang: "en" | "hi" }) {
  const [copied, setCopied] = useState(false)
  const text = lang === "hi" ? sitrep.whatsapp_brief_hi : sitrep.whatsapp_brief_en

  const handleCopy = async () => {
    await navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-2">
        <p className="text-xs text-gray-400 font-medium uppercase tracking-wide">WhatsApp Brief</p>
        <button onClick={handleCopy} className="text-xs bg-green-700 hover:bg-green-600 text-white px-2 py-1 rounded-md transition-colors">
          {copied ? "✓ Copied!" : "📋 Copy"}
        </button>
      </div>
      <div className="bg-gray-800 rounded-lg p-3">
        <p className="text-sm text-gray-200 leading-relaxed whitespace-pre-wrap">{text}</p>
        <p className="text-xs text-gray-500 mt-2">{text.length}/300 chars</p>
      </div>
      <p className="text-xs text-gray-400 mt-3 mb-1 font-medium uppercase tracking-wide">Summary</p>
      <div className="bg-gray-800 rounded-lg p-3 max-h-32 overflow-y-auto">
        <p className="text-xs text-gray-300 leading-relaxed whitespace-pre-wrap">
          {lang === "hi" ? sitrep.summary_hi : sitrep.summary_en}
        </p>
      </div>
    </div>
  )
}