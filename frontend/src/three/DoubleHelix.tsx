"use client";

import { useEffect, useMemo, useRef } from "react";
import { useFrame } from "@react-three/fiber";
import { Instance, Instances } from "@react-three/drei";
import { Color, type Group, type ShaderMaterial } from "three";
import { HelixCurve } from "@/three/HelixCurve";
import { createHelixMaterial } from "@/three/helixMaterial";
import {
  BREATHE_AMPLITUDE,
  BREATHE_FREQUENCY,
  FLOAT_AMPLITUDE,
  FLOAT_FREQUENCY,
  FLOW_SPEED,
  HELIX_COLOR,
  HELIX_GLOW,
  ROTATION_SPEED,
  RUNG_COLORS,
  type HelixConfig,
} from "@/three/config";

interface NodeInstance {
  position: [number, number, number];
}

interface RungInstance {
  position: [number, number, number];
  rotationY: number;
  color: string;
}

function buildNodesAndRungs(config: HelixConfig): {
  nodes: NodeInstance[];
  rungs: RungInstance[];
} {
  const { turns, pointsPerTurn, radius, height } = config;
  const total = turns * pointsPerTurn;
  const nodes: NodeInstance[] = [];
  const rungs: RungInstance[] = [];

  for (let i = 0; i <= total; i += 1) {
    const t = i / total;
    const angle = t * turns * Math.PI * 2;
    const y = (t - 0.5) * height;
    const x = Math.cos(angle) * radius;
    const z = Math.sin(angle) * radius;

    nodes.push({ position: [x, y, z] });
    nodes.push({ position: [-x, y, -z] });

    if (i % config.rungEvery === 0) {
      rungs.push({
        position: [0, y, 0],
        rotationY: angle,
        color: RUNG_COLORS[i % RUNG_COLORS.length],
      });
    }
  }

  return { nodes, rungs };
}

export function DoubleHelix({ config }: { config: HelixConfig }) {
  const group = useRef<Group>(null);

  const curves = useMemo(
    () => [
      new HelixCurve(config.turns, config.radius, config.height, 0),
      new HelixCurve(config.turns, config.radius, config.height, Math.PI),
    ],
    [config.turns, config.radius, config.height],
  );

  const material = useMemo(() => {
    const mat = createHelixMaterial(HELIX_COLOR, HELIX_GLOW);
    mat.uniforms.uFlowSpeed.value = FLOW_SPEED;
    return mat;
  }, []);

  useEffect(() => () => material.dispose(), [material]);

  const { nodes, rungs } = useMemo(() => buildNodesAndRungs(config), [config]);
  const rungLength = config.radius * 2;
  const nodeColor = useMemo(() => new Color(HELIX_COLOR), []);

  useFrame((state) => {
    const g = group.current;
    const time = state.clock.elapsedTime;
    (material as ShaderMaterial).uniforms.uTime.value = time;

    if (!g) return;
    g.rotation.y = time * ROTATION_SPEED;
    g.position.y = Math.sin(time * FLOAT_FREQUENCY) * FLOAT_AMPLITUDE;
    const breathe = 1 + Math.sin(time * BREATHE_FREQUENCY) * BREATHE_AMPLITUDE;
    g.scale.setScalar(breathe);
  });

  return (
    <group ref={group}>
      {/* Sugar-phosphate backbones — procedural tubes with the custom shader. */}
      {curves.map((curve, index) => (
        <mesh key={`strand-${index}`} material={material}>
          <tubeGeometry
            args={[curve, config.tubularSegments, config.tubeRadius, config.radialSegments, false]}
          />
        </mesh>
      ))}

      {/* Nucleotide nodes along both strands. */}
      <Instances limit={nodes.length} range={nodes.length}>
        <sphereGeometry args={[config.nodeRadius, 12, 12]} />
        <meshStandardMaterial
          color={nodeColor}
          emissive={nodeColor}
          emissiveIntensity={1.6}
          roughness={0.3}
          metalness={0.1}
          toneMapped={false}
        />
        {nodes.map((node, index) => (
          <Instance key={`node-${index}`} position={node.position} />
        ))}
      </Instances>

      {/* Base-pair rungs — thin cylinders crossing the axis, A/T/G/C coloured. */}
      <Instances limit={rungs.length} range={rungs.length}>
        <cylinderGeometry args={[config.rungRadius, config.rungRadius, rungLength, 6]} />
        <meshStandardMaterial
          emissive="#FFFFFF"
          emissiveIntensity={0.6}
          roughness={0.5}
          metalness={0}
          toneMapped={false}
        />
        {rungs.map((rung, index) => (
          <Instance
            key={`rung-${index}`}
            position={rung.position}
            rotation={[0, -rung.rotationY, Math.PI / 2]}
            color={rung.color}
          />
        ))}
      </Instances>
    </group>
  );
}
