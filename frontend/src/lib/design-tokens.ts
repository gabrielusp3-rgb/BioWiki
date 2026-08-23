/**
 * BIOWIKI — Design Tokens
 * Single source of truth for the visual language: Brutal Premium · Liquid Glass · Dark Mode.
 * Values here mirror the CSS custom properties declared in `styles/tokens.css`
 * and feed the Tailwind theme in `tailwind.config.ts`.
 */

export const colors = {
  background: {
    primary: "#050505",
    secondary: "#0A0A0A",
    tertiary: "#101010",
  },
  text: {
    primary: "#FFFFFF",
    secondary: "#8A8A8A",
    muted: "#5A5A5A",
  },
  glass: {
    surface: "rgba(255, 255, 255, 0.03)",
    surfaceStrong: "rgba(255, 255, 255, 0.06)",
    border: "rgba(255, 255, 255, 0.10)",
    divider: "rgba(255, 255, 255, 0.08)",
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
} as const;

export const typography = {
  fontDisplay: '"Space Grotesk", "Segoe UI", system-ui, sans-serif',
  fontBody: '"Inter", "Segoe UI", system-ui, sans-serif',
  fontMono: '"JetBrains Mono", "SFMono-Regular", ui-monospace, monospace',
  weight: {
    regular: 400,
    medium: 500,
    semibold: 600,
    bold: 700,
  },
  tracking: {
    tight: "-0.02em",
    normal: "0em",
    wide: "0.08em",
    wider: "0.16em",
  },
} as const;

/** 4px base spacing scale. */
export const spacing = {
  0: "0px",
  1: "4px",
  2: "8px",
  3: "12px",
  4: "16px",
  5: "20px",
  6: "24px",
  8: "32px",
  10: "40px",
  12: "48px",
  16: "64px",
  20: "80px",
  24: "96px",
  32: "128px",
} as const;

export const radii = {
  /** Brutal Premium — corners are never rounded. */
  none: "0px",
} as const;

export const shadows = {
  glass: "0 20px 80px rgba(0, 0, 0, 0.8)",
  glassSoft: "0 10px 40px rgba(0, 0, 0, 0.6)",
  panel: "0 30px 120px rgba(0, 0, 0, 0.85)",
  inset: "inset 0 1px 0 rgba(255, 255, 255, 0.05)",
} as const;

export const glow = {
  dna: "0 0 24px rgba(0, 242, 255, 0.25)",
  rna: "0 0 24px rgba(255, 0, 255, 0.25)",
  protein: "0 0 24px rgba(57, 255, 20, 0.25)",
  crispr: "0 0 24px rgba(255, 255, 0, 0.25)",
  virus: "0 0 24px rgba(255, 68, 68, 0.25)",
  genome: "0 0 24px rgba(124, 92, 255, 0.25)",
} as const;

export const blur = {
  glass: "20px",
  panel: "28px",
} as const;

export const motion = {
  duration: {
    fast: 0.18,
    base: 0.32,
    slow: 0.6,
    slowest: 1.2,
  },
  ease: {
    /** Calm, scientific easing — no bounce. */
    standard: [0.22, 1, 0.36, 1] as [number, number, number, number],
    entrance: [0.16, 1, 0.3, 1] as [number, number, number, number],
    exit: [0.4, 0, 1, 1] as [number, number, number, number],
  },
} as const;

export const zIndex = {
  background: -1,
  base: 0,
  raised: 10,
  sticky: 100,
  navbar: 200,
  sidebar: 250,
  overlay: 900,
  modal: 1000,
  toast: 1100,
} as const;

export const breakpoints = {
  sm: "640px",
  md: "768px",
  lg: "1024px",
  xl: "1280px",
  "2xl": "1536px",
} as const;

/** Ordered list of biological categories used across badges, tags and viewers. */
export const categories = [
  "dna",
  "rna",
  "protein",
  "crispr",
  "virus",
  "genome",
] as const;

export type CategoryKey = (typeof categories)[number];

/** Base-pair colouring used by the sequence viewer (A/T/G/C). */
export const baseColors = {
  A: "#00F2FF",
  T: "#FF00FF",
  G: "#39FF14",
  C: "#FFFF00",
  U: "#FF00FF",
  N: "#8A8A8A",
} as const;

export type BaseKey = keyof typeof baseColors;

export const designTokens = {
  colors,
  typography,
  spacing,
  radii,
  shadows,
  glow,
  blur,
  motion,
  zIndex,
  breakpoints,
  categories,
  baseColors,
} as const;

export default designTokens;
