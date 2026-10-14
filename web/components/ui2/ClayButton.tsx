import type { ButtonHTMLAttributes, ReactNode } from "react"

interface Props extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "blue" | "pink" | "teal" | "amber"
  size?: "sm" | "md" | "lg"
  children: ReactNode
}

const sizeMap = {
  sm: "h-9 px-4 text-sm rounded-2xl",
  md: "h-[54px] px-7 text-base rounded-[20px]",
  lg: "h-16 px-10 text-lg rounded-[22px]",
}

const variantMap = {
  blue: "clay",
  pink: "clay clay-pink",
  teal: "clay clay-teal",
  amber: "clay clay-amber",
}

export default function ClayButton({ variant = "blue", size = "md", className = "", children, ...props }: Props) {
  return (
    <button
      {...props}
      className={`inline-flex items-center justify-center gap-2 font-semibold text-white transition-all ${sizeMap[size]} ${variantMap[variant]} ${className}`}
    >
      {children}
    </button>
  )
}
