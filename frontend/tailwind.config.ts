import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#F8F9FA",
        card: "#FFFFFF",
        "primary-text": "#0F172A",
        "secondary-text": "#64748B",
        border: "#E2E8F0",
        "row-hover": "#F1F5F9",
        positive: "#10B981",
        "positive-dark": "#059669",
        negative: "#EF4444",
        "accent-blue": "#3B82F6",
        "header-accent": "#1E2937",
        "strong-signal": "#059669",
        "marginal-signal": "#F59E0B",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["ui-monospace", "SFMono-Regular", "monospace"],
      },
      borderRadius: {
        DEFAULT: "8px",
      },
      boxShadow: {
        soft: "0 1px 3px rgba(0,0,0,0.04)",
        card: "0 1px 2px rgba(0,0,0,0.05), 0 1px 4px rgba(0,0,0,0.03)",
      },
    },
  },
  plugins: [],
};

export default config;
