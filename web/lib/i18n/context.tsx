"use client"
import { createContext, useContext, useState, useCallback, type ReactNode } from "react"
import { type Lang, type Strings, t } from "./strings"

interface I18nCtx {
  lang: Lang
  s: Strings
  setLang: (l: Lang) => void
}

const Ctx = createContext<I18nCtx>({ lang: "en", s: t("en"), setLang: () => {} })

export function I18nProvider({ children, defaultLang = "en" }: { children: ReactNode; defaultLang?: Lang }) {
  const [lang, setLangState] = useState<Lang>(defaultLang)
  const setLang = useCallback((l: Lang) => {
    setLangState(l)
    if (typeof document !== "undefined") {
      document.documentElement.lang = l
      try { localStorage.setItem("sr_lang", l) } catch {}
    }
  }, [])
  return <Ctx.Provider value={{ lang, s: t(lang), setLang }}>{children}</Ctx.Provider>
}

export function useI18n() { return useContext(Ctx) }
