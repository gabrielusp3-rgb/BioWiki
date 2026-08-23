import { Color, ShaderMaterial } from "three";

/**
 * Custom backbone shader.
 * Combines a fresnel rim (depth / volume cue) with a slow energy pulse flowing
 * along the tube length (uv.x). Output is un-tonemapped so Bloom lifts the
 * bright cyan into a soft glow. Written procedurally — no external assets.
 */
const vertexShader = /* glsl */ `
  varying vec2 vUv;
  varying vec3 vNormalW;
  varying vec3 vViewDir;

  void main() {
    vUv = uv;
    vec4 worldPosition = modelMatrix * vec4(position, 1.0);
    vNormalW = normalize(mat3(modelMatrix) * normal);
    vViewDir = normalize(cameraPosition - worldPosition.xyz);
    gl_Position = projectionMatrix * viewMatrix * worldPosition;
  }
`;

const fragmentShader = /* glsl */ `
  uniform vec3 uColor;
  uniform vec3 uGlow;
  uniform float uTime;
  uniform float uFlowSpeed;

  varying vec2 vUv;
  varying vec3 vNormalW;
  varying vec3 vViewDir;

  void main() {
    // Fresnel — brighter at grazing angles for a glassy, volumetric edge.
    float fresnel = pow(1.0 - max(dot(normalize(vNormalW), normalize(vViewDir)), 0.0), 2.2);

    // Energy pulses travelling along the backbone.
    float flow = sin(vUv.x * 42.0 - uTime * uFlowSpeed * 6.2831);
    float pulse = smoothstep(0.55, 1.0, flow) * 0.6;

    // Steady base emission along the strand.
    float base = 0.35 + 0.25 * sin(vUv.x * 12.0 + uTime * 0.4);

    vec3 color = uColor * base + uGlow * (fresnel * 0.9 + pulse);
    float alpha = clamp(0.5 + fresnel * 0.5 + pulse, 0.0, 1.0);

    gl_FragColor = vec4(color, alpha);
  }
`;

export function createHelixMaterial(color: string, glow: string): ShaderMaterial {
  return new ShaderMaterial({
    vertexShader,
    fragmentShader,
    transparent: true,
    depthWrite: true,
    uniforms: {
      uColor: { value: new Color(color) },
      uGlow: { value: new Color(glow) },
      uTime: { value: 0 },
      uFlowSpeed: { value: 0.35 },
    },
  });
}
