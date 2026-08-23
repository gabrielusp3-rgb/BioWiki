"use client";

import { Canvas, useFrame } from "@react-three/fiber";
import { useMemo, useRef } from "react";
import * as THREE from "three";

const DNA_COLOR = "#00F2FF";
const PAIRS = 42;
const RADIUS = 2.2;
const RISE = 0.42;
const TURNS = 0.55;

function Helix() {
  const group = useRef<THREE.Group>(null);

  const { strandA, strandB, rungs } = useMemo(() => {
    const a: THREE.Vector3[] = [];
    const b: THREE.Vector3[] = [];
    const r: { mid: THREE.Vector3; len: number; rot: number }[] = [];
    for (let i = 0; i < PAIRS; i++) {
      const angle = i * TURNS;
      const y = (i - PAIRS / 2) * RISE;
      const pa = new THREE.Vector3(
        Math.cos(angle) * RADIUS,
        y,
        Math.sin(angle) * RADIUS,
      );
      const pb = new THREE.Vector3(
        Math.cos(angle + Math.PI) * RADIUS,
        y,
        Math.sin(angle + Math.PI) * RADIUS,
      );
      a.push(pa);
      b.push(pb);
      r.push({
        mid: pa.clone().add(pb).multiplyScalar(0.5),
        len: pa.distanceTo(pb),
        rot: angle,
      });
    }
    return { strandA: a, strandB: b, rungs: r };
  }, []);

  useFrame((_, delta) => {
    if (group.current) group.current.rotation.y += delta * 0.12;
  });

  return (
    <group ref={group}>
      {strandA.map((p, i) => (
        <mesh key={`a-${i}`} position={p}>
          <sphereGeometry args={[0.16, 16, 16]} />
          <meshStandardMaterial
            color={DNA_COLOR}
            emissive={DNA_COLOR}
            emissiveIntensity={0.6}
            roughness={0.3}
          />
        </mesh>
      ))}
      {strandB.map((p, i) => (
        <mesh key={`b-${i}`} position={p}>
          <sphereGeometry args={[0.16, 16, 16]} />
          <meshStandardMaterial
            color="#7C5CFF"
            emissive="#7C5CFF"
            emissiveIntensity={0.4}
            roughness={0.3}
          />
        </mesh>
      ))}
      {rungs.map((r, i) => (
        <mesh
          key={`r-${i}`}
          position={r.mid}
          rotation={[0, -r.rot, Math.PI / 2]}
        >
          <cylinderGeometry args={[0.03, 0.03, r.len, 8]} />
          <meshStandardMaterial
            color="#ffffff"
            emissive={DNA_COLOR}
            emissiveIntensity={0.15}
            transparent
            opacity={0.35}
          />
        </mesh>
      ))}
    </group>
  );
}

function Particles() {
  const ref = useRef<THREE.Points>(null);
  const positions = useMemo(() => {
    const count = 500;
    const arr = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      arr[i * 3] = (Math.random() - 0.5) * 40;
      arr[i * 3 + 1] = (Math.random() - 0.5) * 40;
      arr[i * 3 + 2] = (Math.random() - 0.5) * 40;
    }
    return arr;
  }, []);

  useFrame((_, delta) => {
    if (ref.current) ref.current.rotation.y += delta * 0.02;
  });

  return (
    <points ref={ref}>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" args={[positions, 3]} />
      </bufferGeometry>
      <pointsMaterial
        size={0.06}
        color={DNA_COLOR}
        transparent
        opacity={0.5}
        sizeAttenuation
      />
    </points>
  );
}

export default function BackgroundDNA() {
  return (
    <div
      aria-hidden
      style={{
        position: "fixed",
        inset: 0,
        zIndex: -1,
        pointerEvents: "none",
        background:
          "radial-gradient(circle at 70% 30%, rgba(0,242,255,0.06), transparent 55%), #050505",
      }}
    >
      <Canvas camera={{ position: [0, 0, 14], fov: 45 }} dpr={[1, 1.5]}>
        <ambientLight intensity={0.4} />
        <pointLight position={[10, 10, 10]} intensity={40} color={DNA_COLOR} />
        <pointLight position={[-10, -6, -8]} intensity={25} color="#7C5CFF" />
        <Particles />
        <Helix />
      </Canvas>
    </div>
  );
}
