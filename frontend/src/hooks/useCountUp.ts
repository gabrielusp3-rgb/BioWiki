"use client";

import { useEffect, useRef, useState } from "react";

interface UseCountUpOptions {
  end: number;
  start?: number;
  duration?: number;
}

/** easeOutExpo — fast then settling, reads as precise rather than bouncy. */
function easeOutExpo(t: number): number {
  return t === 1 ? 1 : 1 - Math.pow(2, -10 * t);
}

/**
 * Animated numeric count-up. Respects `prefers-reduced-motion` by snapping
 * to the final value.
 *
 * Animation starts as soon as the target is known. Viewport gating previously
 * left category-page totals stuck at 0 (splash overlay + IntersectionObserver
 * threshold) while the table below already listed real records.
 *
 * If `end` changes after the first run, the displayed value follows the new
 * total instead of freezing at the first target.
 */
export function useCountUp<T extends HTMLElement>({
  end,
  start = 0,
  duration = 1800,
}: UseCountUpOptions) {
  const ref = useRef<T>(null);
  const [value, setValue] = useState(start);
  const startedRef = useRef(false);

  useEffect(() => {
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduced) {
      setValue(end);
      return;
    }

    if (startedRef.current) {
      setValue(end);
      return;
    }

    let raf = 0;
    let startTime = 0;
    startedRef.current = true;

    const step = (now: number) => {
      if (!startTime) startTime = now;
      const progress = Math.min((now - startTime) / duration, 1);
      setValue(start + (end - start) * easeOutExpo(progress));
      if (progress < 1) raf = requestAnimationFrame(step);
    };
    raf = requestAnimationFrame(step);

    return () => {
      if (raf) cancelAnimationFrame(raf);
    };
  }, [end, start, duration]);

  return { ref, value };
}
