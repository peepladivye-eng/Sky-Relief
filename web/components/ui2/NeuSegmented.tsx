"use client"
interface Option<T extends string> { value: T; label: string; labelHi?: string }

interface Props<T extends string> {
  options: Option<T>[]
  value: T
  onChange: (v: T) => void
  lang?: "en" | "hi"
  ariaLabel?: string
}

export default function NeuSegmented<T extends string>({ options, value, onChange, lang = "en", ariaLabel }: Props<T>) {
  return (
    <div className="neu-seg" role="group" aria-label={ariaLabel}>
      {options.map(o => (
        <button
          key={o.value}
          type="button"
          className={`neu-seg-btn${value === o.value ? " active" : ""}`}
          aria-pressed={value === o.value}
          onClick={() => onChange(o.value)}
        >
          {lang === "hi" && o.labelHi ? o.labelHi : o.label}
        </button>
      ))}
    </div>
  )
}
