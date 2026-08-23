/**
 * BIOWIKI — BackgroundDNA configuration.
 * Central tuning for the permanent 3D double-helix background.
 * All motion here is intentionally very slow: "living technology", never distracting.
 */

/** Primary helix colour (DNA cyan) and its glow. */
export const HELIX_COLOR = "#00F2FF";
export const HELIX_GLOW = "#00F2FF";

/** Base-pair rung palette (A/T/G/C cycling), discreet against the dark base. */
export const RUNG_COLORS = ["#00F2FF", "#FF00FF", "#39FF14", "#FFFF00"] as const;

/** Particle colour — faint white dust. */
export const PARTICLE_COLOR = "#FFFFFF";

/** Scene fog colour matches the primary background (#050505). */
export const FOG_COLOR = "#050505";

export interface HelixConfig {
  turns: number;
  pointsPerTurn: number;
  radius: number;
  height: number;
  nodeRadius: number;
  rungRadius: number;
  rungEvery: number;
  /** Sugar-phosphate backbone tube. */
  tubeRadius: number;
  tubularSegments: number;
  radialSegments: number;
}

export interface QualityProfile {
  key: "low" | "medium" | "high";
  dpr: [number, number];
  helix: HelixConfig;
  particleCount: number;
  bloom: boolean;
  fogDensity: number;
}

/**
 * Three quality tiers. The mount selects one from viewport width, device memory
 * and reduced-motion preference — graceful degradation without hidden fallbacks.
 */
export const QUALITY_PROFILES: Record<QualityProfile["key"], QualityProfile> = {
  low: {
    key: "low",
    dpr: [1, 1.25],
    helix: {
      turns: 5,
      pointsPerTurn: 10,
      radius: 2.1,
      height: 34,
      nodeRadius: 0.15,
      rungRadius: 0.03,
      rungEvery: 2,
      tubeRadius: 0.09,
      tubularSegments: 260,
      radialSegments: 6,
    },
    particleCount: 240,
    bloom: false,
    fogDensity: 0.028,
  },
  medium: {
    key: "medium",
    dpr: [1, 1.5],
    helix: {
      turns: 6,
      pointsPerTurn: 14,
      radius: 2.2,
      height: 40,
      nodeRadius: 0.16,
      rungRadius: 0.035,
      rungEvery: 1,
      tubeRadius: 0.1,
      tubularSegments: 520,
      radialSegments: 8,
    },
    particleCount: 700,
    bloom: true,
    fogDensity: 0.024,
  },
  high: {
    key: "high",
    dpr: [1, 1.75],
    helix: {
      turns: 7,
      pointsPerTurn: 18,
      radius: 2.3,
      height: 46,
      nodeRadius: 0.17,
      rungRadius: 0.04,
      rungEvery: 1,
      tubeRadius: 0.11,
      tubularSegments: 760,
      radialSegments: 10,
    },
    particleCount: 1200,
    bloom: true,
    fogDensity: 0.022,
  },
};

/** Extremely low angular velocity (radians / second). */
export const ROTATION_SPEED = 0.045;
/** Vertical float amplitude / frequency. */
export const FLOAT_AMPLITUDE = 0.6;
export const FLOAT_FREQUENCY = 0.12;
/** Organic "breathing" — subtle scale pulsing of the whole helix. */
export const BREATHE_AMPLITUDE = 0.02;
export const BREATHE_FREQUENCY = 0.35;
/** Speed of the energy pulse flowing along the backbones (shader). */
export const FLOW_SPEED = 0.35;
