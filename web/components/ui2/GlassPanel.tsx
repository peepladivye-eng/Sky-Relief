import type { HTMLAttributes, ReactNode } from "react"

interface Props extends HTMLAttributes<HTMLElement> {
  as?: "div" | "section" | "article" | "header" | "nav" | "aside"
  strong?: boolean
  children: ReactNode
}

export default function GlassPanel({ as: Tag = "div", strong = false, className = "", children, ...props }: Props) {
  return (
    <Tag
      {...props}
      className={`glass${strong ? " glass-strong" : ""} ${className}`}
    >
      {children}
    </Tag>
  )
}
