import type { Config } from "tailwindcss";

/**
 * BIOWIKI — Tailwind theme.
 * The theme is a direct projection of the design tokens onto Tailwind's utility system.
 * Corners are never rounded (Brutal Premium); the only radius available is `none`.
 */
const config: Config = {
  darkMode: "class",
  content: [
    "./src/app/**/*.{ts,tsx}",
    "./src/components/**/*.{ts,tsx}",
    "./src/lib/**/*.{ts,tsx}",
  ],
  theme: {
    screens: {
      sm: "640px",
      md: "768px",
      lg: "1024px",
      xl: "1280px",
      "2xl": "1536px",
    },
    extend: {
      colors: {
        bg: {
          DEFAULT: "#050505",
          primary: "#050505",
          secondary: "#0A0A0A",
          tertiary: "#101010",
        },
        content: {
          DEFAULT: "#FFFFFF",
          primary: "#FFFFFF",
          secondary: "#8A8A8A",
          muted: "#5A5A5A",
        },
        glass: {
          surface: "rgba(255,255,255,0.03)",
          strong: "rgba(255,255,255,0.06)",
          border: "rgba(255,255,255,0.10)",
          divider: "rgba(255,255,255,0.08)",
        },
        category: {
          dna: "#00F2FF",
          rna: "#FF00FF",
          protein: "#39FF14",
          crispr: "#FFFF00",
          virus: "#FF4444",
          genome: "#7C5CFF",
        },
        state: {
          success: "#39FF14",
          warning: "#FFFF00",
          danger: "#FF4444",
          info: "#00F2FF",
        },
      },
      fontFamily: {
        display: ["var(--font-space-grotesk)", '"Segoe UI"', "system-ui", "sans-serif"],
        body: ["var(--font-inter)", '"Segoe UI"', "system-ui", "sans-serif"],
        mono: ['"JetBrains Mono"', '"SFMono-Regular"', "ui-monospace", "monospace"],
      },
      letterSpacing: {
        tightest: "-0.02em",
        wide: "0.08em",
        wider: "0.16em",
      },
      borderRadius: {
        none: "0px",
        DEFAULT: "0px",
        sm: "0px",
        md: "0px",
        lg: "0px",
        full: "0px",
      },
      spacing: {
        "18": "72px",
        "22": "88px",
        "30": "120px",
      },
      boxShadow: {
        glass: "0 20px 80px rgba(0,0,0,0.8)",
        "glass-soft": "0 10px 40px rgba(0,0,0,0.6)",
        panel: "0 30px 120px rgba(0,0,0,0.85)",
        "glow-dna": "0 0 24px rgba(0,242,255,0.25)",
        "glow-rna": "0 0 24px rgba(255,0,255,0.25)",
        "glow-protein": "0 0 24px rgba(57,255,20,0.25)",
        "glow-crispr": "0 0 24px rgba(255,255,0,0.25)",
        "glow-virus": "0 0 24px rgba(255,68,68,0.25)",
        "glow-genome": "0 0 24px rgba(124,92,255,0.25)",
      },
      backdropBlur: {
        glass: "20px",
        panel: "28px",
      },
      backdropSaturate: {
        glass: "1.8",
      },
      maxWidth: {
        container: "1440px",
        prose: "72ch",
      },
      keyframes: {
        "fade-in": {
          from: { opacity: "0" },
          to: { opacity: "1" },
        },
        "fade-in-up": {
          from: { opacity: "0", transform: "translateY(16px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
        "scale-in": {
          from: { opacity: "0", transform: "scale(0.98)" },
          to: { opacity: "1", transform: "scale(1)" },
        },
        shimmer: {
          "100%": { transform: "translateX(100%)" },
        },
        "pulse-glow": {
          "0%, 100%": { opacity: "0.5" },
          "50%": { opacity: "1" },
        },
        "border-flow": {
          "0%, 100%": { backgroundPosition: "0% 50%" },
          "50%": { backgroundPosition: "100% 50%" },
        },
      },
      animation: {
        "fade-in": "fade-in 0.32s cubic-bezier(0.22,1,0.36,1) both",
        "fade-in-up": "fade-in-up 0.6s cubic-bezier(0.16,1,0.3,1) both",
        "scale-in": "scale-in 0.32s cubic-bezier(0.22,1,0.36,1) both",
        shimmer: "shimmer 2.2s cubic-bezier(0.4,0,0.6,1) infinite",
        "pulse-glow": "pulse-glow 3.4s ease-in-out infinite",
        "border-flow": "border-flow 6s ease infinite",
      },
      transitionTimingFunction: {
        standard: "cubic-bezier(0.22,1,0.36,1)",
        entrance: "cubic-bezier(0.16,1,0.3,1)",
      },
    },
  },
  plugins: [],
};

export default config;
