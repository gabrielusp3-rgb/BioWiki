"use client";

import { useEffect, useMemo, useState } from "react";
import { Canvas } from "@react-three/fiber";
import { PerformanceMonitor } from "@react-three/drei";
import { BackgroundScene } from "@/three/BackgroundScene";
import { QUALITY_PROFILES, type QualityProfile } from "@/three/config";

/**
 * Selects an initial quality tier from viewport width, device memory and the
 * user's reduced-motion preference. Runs once on mount (client only).
 */
function pickInitialProfile(): QualityProfile {
  if (typeof window === "undefined") return QUALITY_PROFILES.medium;

  const reducedMotion = window.matchMedia?.(
    "(prefers-reduced-motion: reduce)",
  ).matches;
  const width = window.innerWidth;
  const memory = (navigator as Navigator & { deviceMemory?: number }).deviceMemory ?? 4;
  const cores = navigator.hardwareConcurrency ?? 4;

  if (reducedMotion || width < 768 || memory <= 2 || cores <= 2) {
    return QUALITY_PROFILES.low;
  }
  if (width < 1280 || memory <= 4) {
    return QUALITY_PROFILES.medium;
  }
  return QUALITY_PROFILES.high;
}

export default function BackgroundDNA() {
  const [profile, setProfile] = useState<QualityProfile>(() => pickInitialProfile());
  const [prefersReduced, setPrefersReduced] = useState(false);
  const [tabHidden, setTabHidden] = useState(false);
  const [splashUp, setSplashUp] = useState(false);

  useEffect(() => {
    const media = window.matchMedia("(prefers-reduced-motion: reduce)");
    const update = () => setPrefersReduced(media.matches);
    update();
    media.addEventListener("change", update);
    return () => media.removeEventListener("change", update);
  }, []);

  useEffect(() => {
    const onVisibility = () => setTabHidden(document.hidden);
    onVisibility();
    document.addEventListener("visibilitychange", onVisibility);
    return () => document.removeEventListener("visibilitychange", onVisibility);
  }, []);

  useEffect(() => {
    const start = () => setSplashUp(true);
    const end = () => setSplashUp(false);
    window.addEventListener("biowiki-splash-start", start);
    window.addEventListener("biowiki-splash-end", end);
    setSplashUp(document.documentElement.dataset.biowikiSplash === "1");
    return () => {
      window.removeEventListener("biowiki-splash-start", start);
      window.removeEventListener("biowiki-splash-end", end);
    };
  }, []);

  // Downgrade one tier if the runtime frame rate degrades.
  const handleDecline = () => {
    setProfile((current) => {
      if (current.key === "high") return QUALITY_PROFILES.medium;
      if (current.key === "medium") return QUALITY_PROFILES.low;
      return current;
    });
  };

  const camera = useMemo(
    () => ({ position: [0, 0, 13] as [number, number, number], fov: 46, near: 0.1, far: 120 }),
    [],
  );

  return (
    <div
      aria-hidden
      style={{
        position: "fixed",
        inset: 0,
        width: "100%",
        height: "100%",
        zIndex: -1,
        pointerEvents: "none",
      }}
    >
      <Canvas
        camera={camera}
        dpr={profile.dpr}
        frameloop={prefersReduced || tabHidden || splashUp ? "demand" : "always"}
        gl={{
          antialias: true,
          alpha: true,
          powerPreference: "high-performance",
          stencil: false,
          depth: true,
        }}
        style={{ width: "100%", height: "100%", background: "transparent" }}
      >
        <PerformanceMonitor onDecline={handleDecline} flipflops={3}>
          <BackgroundScene profile={profile} />
        </PerformanceMonitor>
      </Canvas>
    </div>
  );
}
