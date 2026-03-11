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
      },
      boxShadow: {
        neon: "0 0 0 1px rgba(103,255,216,0.22), 0 0 30px rgba(103,255,216,0.08)",
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
