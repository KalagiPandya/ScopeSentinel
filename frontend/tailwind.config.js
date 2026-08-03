/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        base: {
          900: "#0B0F14",   // page background
          800: "#0F151D",   // sidebar
          700: "#131A24",   // card panel
          600: "#1A222E",   // card hover / inputs
          500: "#26303F",   // borders
        },
        ink: {
          100: "#E6EDF3",   // primary text
          300: "#9BAAB9",   // secondary text
          500: "#6B7A8D",   // muted/labels
        },
        signal: {
          DEFAULT: "#3B9EFF",
          dim: "#1E4A78",
        },
        risk: {
          low: "#4ADE80",
          medium: "#FBBF24",
          high: "#FB923C",
          critical: "#F87171",
        },
      },
      fontFamily: {
        mono: ["JetBrains Mono", "monospace"],
        sans: ["Inter", "sans-serif"],
      },
      boxShadow: {
        panel: "0 1px 0 rgba(255,255,255,0.04) inset, 0 8px 24px -12px rgba(0,0,0,0.5)",
      },
      keyframes: {
        "pulse-ring": {
          "0%": { transform: "scale(0.8)", opacity: "0.8" },
          "80%, 100%": { transform: "scale(1.8)", opacity: "0" },
        },
      },
      animation: {
        "pulse-ring": "pulse-ring 1.6s cubic-bezier(0.4,0,0.6,1) infinite",
      },
    },
  },
  plugins: [],
}
