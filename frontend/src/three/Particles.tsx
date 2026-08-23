"use client";

import { useEffect, useMemo, useRef } from "react";
import { useFrame } from "@react-three/fiber";
import {
  AdditiveBlending,
  Color,
  type Points as ThreePoints,
  type ShaderMaterial,
} from "three";
import { HELIX_GLOW, PARTICLE_COLOR } from "@/three/config";

/**
 * GPU particle field for the BackgroundDNA.
 * All motion is computed in the vertex shader (no per-frame CPU allocations),
 * so thousands of points animate continuously at a very low GPU/CPU cost.
 * Two layers — fine dust + sparse cyan motes — give parallax depth and tie the
 * field to the helix by sharing its cyan glow.
 */

const vertexShader = /* glsl */ `
  uniform float uTime;
  uniform float uSize;
  uniform float uPixelRatio;

  attribute float aScale;
  attribute float aPhase;
  attribute float aSpeed;
  attribute float aAmp;

  varying float vTwinkle;
  varying float vDepthFade;

  void main() {
    vec3 p = position;

    // Extremely slow organic drift + gentle swirl around the Y axis.
    float t = uTime * aSpeed;
    p.y += sin(t + aPhase) * aAmp;
    float swirl = uTime * 0.02 * aSpeed;
    float c = cos(swirl);
    float s = sin(swirl);
    p.xz = mat2(c, -s, s, c) * p.xz;

    vec4 mvPosition = modelViewMatrix * vec4(p, 1.0);

    // Perspective size attenuation.
    gl_PointSize = uSize * aScale * uPixelRatio * (60.0 / -mvPosition.z);

    // Fade with distance for depth; twinkle for a living, discreet shimmer.
    vDepthFade = clamp(1.0 - (-mvPosition.z - 6.0) / 34.0, 0.15, 1.0);
    vTwinkle = 0.6 + 0.4 * sin(uTime * aSpeed * 1.7 + aPhase);

    gl_Position = projectionMatrix * mvPosition;
  }
`;

const fragmentShader = /* glsl */ `
  uniform vec3 uColor;
  uniform float uOpacity;

  varying float vTwinkle;
  varying float vDepthFade;

  void main() {
    // Soft circular sprite with a bright core.
    vec2 uv = gl_PointCoord - 0.5;
    float d = length(uv);
    float disc = smoothstep(0.5, 0.0, d);
    float core = smoothstep(0.22, 0.0, d) * 0.6;

    float alpha = (disc + core) * uOpacity * vDepthFade * vTwinkle;
    if (alpha < 0.004) discard;

    gl_FragColor = vec4(uColor, alpha);
  }
`;

interface LayerConfig {
  count: number;
  radius: number;
  height: number;
  color: string;
  size: number;
  opacity: number;
  ampRange: [number, number];
  speedRange: [number, number];
}

function useLayerGeometry(config: LayerConfig) {
  return useMemo(() => {
    const { count, radius, height, ampRange, speedRange } = config;
    const positions = new Float32Array(count * 3);
    const scales = new Float32Array(count);
    const phases = new Float32Array(count);
    const speeds = new Float32Array(count);
    const amps = new Float32Array(count);

    for (let i = 0; i < count; i += 1) {
      // Cylindrical volume around the helix axis, denser near the centre.
      const r = radius * Math.cbrt(Math.random());
      const theta = Math.random() * Math.PI * 2;
      positions[i * 3] = Math.cos(theta) * r;
      positions[i * 3 + 1] = (Math.random() - 0.5) * height;
      positions[i * 3 + 2] = Math.sin(theta) * r;

      scales[i] = 0.4 + Math.random() * 1.2;
      phases[i] = Math.random() * Math.PI * 2;
      speeds[i] = speedRange[0] + Math.random() * (speedRange[1] - speedRange[0]);
      amps[i] = ampRange[0] + Math.random() * (ampRange[1] - ampRange[0]);
    }

    return { positions, scales, phases, speeds, amps };
  }, [config]);
}

function ParticleLayer({ config }: { config: LayerConfig }) {
  const ref = useRef<ThreePoints>(null);
  const { positions, scales, phases, speeds, amps } = useLayerGeometry(config);

  const pixelRatio =
    typeof window !== "undefined" ? Math.min(window.devicePixelRatio, 2) : 1;

  const material = useMemo<ShaderMaterial["uniforms"]>(
    () => ({
      uTime: { value: 0 },
      uSize: { value: config.size },
      uPixelRatio: { value: pixelRatio },
      uColor: { value: new Color(config.color) },
      uOpacity: { value: config.opacity },
    }),
    [config.size, config.color, config.opacity, pixelRatio],
  );

  const shaderRef = useRef<ShaderMaterial>(null);

  useFrame((state) => {
    const p = ref.current;
    if (shaderRef.current) {
      shaderRef.current.uniforms.uTime.value = state.clock.elapsedTime;
    }
    if (p) {
      // Barely perceptible whole-field rotation for extra parallax.
      p.rotation.y = state.clock.elapsedTime * 0.008;
    }
  });

  return (
    <points ref={ref}>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" args={[positions, 3]} count={config.count} />
        <bufferAttribute attach="attributes-aScale" args={[scales, 1]} count={config.count} />
        <bufferAttribute attach="attributes-aPhase" args={[phases, 1]} count={config.count} />
        <bufferAttribute attach="attributes-aSpeed" args={[speeds, 1]} count={config.count} />
        <bufferAttribute attach="attributes-aAmp" args={[amps, 1]} count={config.count} />
      </bufferGeometry>
      <shaderMaterial
        ref={shaderRef}
        vertexShader={vertexShader}
        fragmentShader={fragmentShader}
        uniforms={material}
        transparent
        depthWrite={false}
        blending={AdditiveBlending}
        toneMapped={false}
      />
    </points>
  );
}

interface ParticlesProps {
  count: number;
  radius?: number;
  height?: number;
}

export function Particles({ count, radius = 16, height = 44 }: ParticlesProps) {
  // Two layers derived from the requested count → thousands of points in total,
  // without touching any other module's configuration.
  const layers = useMemo<LayerConfig[]>(
    () => [
      {
        count: Math.round(count * 1.6),
        radius,
        height,
        color: PARTICLE_COLOR,
        size: 6,
        opacity: 0.14,
        ampRange: [0.15, 0.6],
        speedRange: [0.05, 0.16],
      },
      {
        count: Math.round(count * 0.5),
        radius: radius * 0.55,
        height: height * 0.9,
        color: HELIX_GLOW,
        size: 9,
        opacity: 0.1,
        ampRange: [0.2, 0.8],
        speedRange: [0.04, 0.12],
      },
    ],
    [count, radius, height],
  );

  // Regenerate cleanly when layer identity changes.
  useEffect(() => undefined, [layers]);

  return (
    <group>
      {layers.map((layer, index) => (
        <ParticleLayer key={`layer-${index}`} config={layer} />
      ))}
    </group>
  );
}
