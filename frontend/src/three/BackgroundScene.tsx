"use client";

import { Suspense } from "react";
import { EffectComposer, Bloom } from "@react-three/postprocessing";
import { DoubleHelix } from "@/three/DoubleHelix";
import { Particles } from "@/three/Particles";
import { FOG_COLOR, HELIX_GLOW, type QualityProfile } from "@/three/config";

export function BackgroundScene({ profile }: { profile: QualityProfile }) {
  return (
    <>
      <fogExp2 attach="fog" args={[FOG_COLOR, profile.fogDensity]} />

      {/* Professional 3-point rig + faint ambient. */}
      <ambientLight intensity={0.3} />
      {/* Key — cyan, front-right. */}
      <pointLight position={[6, 10, 8]} intensity={45} color={HELIX_GLOW} distance={64} decay={2} />
      {/* Fill — violet, back-left, softens the shadow side. */}
      <pointLight position={[-8, -6, -6]} intensity={20} color="#7C5CFF" distance={54} decay={2} />
      {/* Rim — cool white behind, separates the helix from the dark base. */}
      <pointLight position={[0, 2, -14]} intensity={24} color="#BFF7FF" distance={60} decay={2} />
      {/* Directional sheen to keep the whole strand legible while rotating. */}
      <directionalLight position={[4, 8, 6]} intensity={0.4} color={HELIX_GLOW} />

      <Suspense fallback={null}>
        <DoubleHelix config={profile.helix} />
        <Particles count={profile.particleCount} />
      </Suspense>

      {profile.bloom && (
        <EffectComposer>
          <Bloom
            intensity={0.75}
            luminanceThreshold={0.18}
            luminanceSmoothing={0.9}
            radius={0.6}
            mipmapBlur
          />
        </EffectComposer>
      )}
    </>
  );
}
