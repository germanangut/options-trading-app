import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Public Sans", "sans-serif"],
      },
      colors: {
        surface: {
          0: "rgb(var(--surface-0) / <alpha-value>)",
          1: "rgb(var(--surface-1) / <alpha-value>)",
          2: "rgb(var(--surface-2) / <alpha-value>)",
          3: "rgb(var(--surface-3) / <alpha-value>)",
          overlay: "rgb(var(--surface-overlay) / <alpha-value>)",
        },
        ink: {
          1: "rgb(var(--ink-1) / <alpha-value>)",
          2: "rgb(var(--ink-2) / <alpha-value>)",
          3: "rgb(var(--ink-3) / <alpha-value>)",
          4: "rgb(var(--ink-4) / <alpha-value>)",
        },
        accent: {
          DEFAULT: "rgb(var(--accent) / <alpha-value>)",
          soft: "rgb(var(--accent-soft) / <alpha-value>)",
        },
        success: {
          DEFAULT: "rgb(var(--success) / <alpha-value>)",
          soft: "rgb(var(--success-soft) / <alpha-value>)",
        },
        warning: {
          DEFAULT: "rgb(var(--warning) / <alpha-value>)",
          soft: "rgb(var(--warning-soft) / <alpha-value>)",
        },
        danger: {
          DEFAULT: "rgb(var(--danger) / <alpha-value>)",
          soft: "rgb(var(--danger-soft) / <alpha-value>)",
        },
        bullish: "rgb(var(--bullish) / <alpha-value>)",
        bearish: "rgb(var(--bearish) / <alpha-value>)",
        neutral: {
          soft: "rgb(var(--neutral-soft) / <alpha-value>)",
        },
      },
      borderRadius: {
        panel: "var(--radius-panel)",
        card: "var(--radius-card)",
        pill: "var(--radius-pill)",
      },
      boxShadow: {
        panel: "var(--shadow-panel)",
        elevated: "var(--shadow-elevated)",
      },
    },
  },
  plugins: [],
} satisfies Config;
