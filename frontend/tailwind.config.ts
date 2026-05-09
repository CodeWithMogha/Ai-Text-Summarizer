import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./lib/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        sidebar: {
          bg: "#0F1117",
          text: "#8B8FA3",
          "text-active": "#FFFFFF",
          hover: "rgba(79, 70, 229, 0.08)",
          "active-bg": "rgba(79, 70, 229, 0.12)",
          "active-border": "#4F46E5",
        },
        accent: {
          DEFAULT: "#4F46E5",
          light: "#EEF2FF",
          hover: "#4338CA",
          50: "#EEF2FF",
          100: "#E0E7FF",
          500: "#4F46E5",
          600: "#4338CA",
          700: "#3730A3",
        },
        surface: {
          DEFAULT: "#F8F9FB",
          card: "#FFFFFF",
          border: "#E5E7EB",
          "border-hover": "#D1D5DB",
        },
      },
      fontFamily: {
        sans: ["DM Sans", "system-ui", "-apple-system", "sans-serif"],
      },
      fontSize: {
        "2xs": ["11px", "16px"],
      },
      borderRadius: {
        DEFAULT: "8px",
      },
      animation: {
        "fade-in": "fadeIn 0.3s ease-out",
        "slide-in": "slideIn 0.3s ease-out",
        "spin-slow": "spin 1.5s linear infinite",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0", transform: "translateY(4px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        slideIn: {
          "0%": { opacity: "0", transform: "translateX(-8px)" },
          "100%": { opacity: "1", transform: "translateX(0)" },
        },
      },
    },
  },
  plugins: [],
};

export default config;
