import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        night: "#05070d",
        steel: "#0e1625",
        panel: "#121b2d",
        neon: "#67ffd8",
        ember: "#ff9958",
        danger: "#ff5f7a",
        navy: "#0f172a",
        emerald: {
          500: "#10b981",
          600: "#059669",
        },
      },
      boxShadow: {
        neon: "0 0 0 1px rgba(103,255,216,0.22), 0 0 30px rgba(103,255,216,0.08)",
        card: "0 1px 3px rgba(0,0,0,0.1), 0 1px 2px rgba(0,0,0,0.06)",
        "card-hover": "0 4px 6px rgba(0,0,0,0.07), 0 2px 4px rgba(0,0,0,0.06)",
      },
      fontFamily: {
        sans: [
          "Inter",
          "ui-sans-serif",
          "system-ui",
          "-apple-system",
          "BlinkMacSystemFont",
          "Segoe UI",
          "sans-serif",
        ],
      },
      backgroundImage: {
        "omega-grid":
          "linear-gradient(rgba(103,255,216,0.07) 1px, transparent 1px), linear-gradient(90deg, rgba(103,255,216,0.07) 1px, transparent 1px)",
      },
    },
  },
  plugins: [],
};

export default config;
