import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        bg: "var(--bg)",
        panel: "var(--panel)",
        "panel-2": "var(--panel-2)",
        sunken: "var(--sunken)",
        line: "var(--line)",
        "line-soft": "var(--line-soft)",
        "line-ctl": "var(--line-ctl)",
        ink: "var(--ink)",
        "ink-2": "var(--ink-2)",
        "ink-3": "var(--ink-3)",
        flood: "var(--flood)",
        "flood-fill": "var(--flood-fill)",
        silent: "var(--silent)",
        confirmed: "var(--confirmed)",
        warn: "var(--warn)",
      },
      borderRadius: {
        panel: "var(--radius-panel)",
        control: "var(--radius-control)",
        chip: "var(--radius-chip)",
      },
      boxShadow: {
        float: "var(--shadow-float)",
      },
      fontFamily: {
        display: ["Bricolage Grotesque", "sans-serif"],
        sans: ["Hanken Grotesk", "sans-serif"],
        hindi: ["Noto Sans Devanagari", "sans-serif"],
      },
      fontSize: {
        12: "12px",
        13: "13px",
        14: "14px",
        15: "15px",
        16: "16px",
        18: "18px",
        22: "22px",
        46: "46px",
      },
      transitionDuration: {
        hover: "var(--transition-hover)",
      },
    },
  },
  plugins: [],
};
export default config;
