"use client";

import { useEffect, useState } from "react";
import dynamic from "next/dynamic";

/**
 * Client-only mount for the WebGL background. `ssr: false` keeps Three.js out of
 * the server bundle and prevents hydration mismatches; the chunk is fetched
 * lazily after the shell paints. Until then the fixed dark gradient from
 * globals.css (body::before) stands in — no layout shift, no flash.
 */
const BackgroundDNA = dynamic(() => import("@/three/BackgroundDNA"), {
  ssr: false,
  loading: () => null,
});

export function BackgroundDNAMount() {
  const [ready, setReady] = useState(false);

  useEffect(() => {
    setReady(true);
  }, []);

  if (!ready) return null;
  return <BackgroundDNA />;
}
