"use client";

import { useEffect, useState } from "react";
import dynamic from "next/dynamic";

const BackgroundDNA = dynamic(() => import("./BackgroundDNA"), {
  ssr: false,
  loading: () => null,
});

export function BackgroundDNAMount() {
  const [ready, setReady] = useState(false);
  useEffect(() => setReady(true), []);
  if (!ready) return null;
  return <BackgroundDNA />;
}
