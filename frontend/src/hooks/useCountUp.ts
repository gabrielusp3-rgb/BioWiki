"use client";

import { useEffect, useRef, useState } from "react";

interface UseCountUpOptions {
  end: number;
  start?: number;
  duration?: number;
  /** Only start once the element scrolls into view. */
  once?: boolean;
}

/** easeOutExpo — fast then settling, reads as precise rather than bouncy. */
function easeOutExpo(t: number): number {
  return t === 1 ? 1 : 1 - Math.pow(2, -10 * t);
}

/**
 * Animated numeric count-up that triggers when the target element enters the
 * viewport. Respects `prefers-reduced-motion` by snapping to the final value.
 */
export function useCountUp<T extends HTMLElement>({
  end,
  start = 0,
  duration = 1800,
  once = true,
}: UseCountUpOptions) {
  const ref = useRef<T>(null);
  const [value, setValue] = useState(start);
  const startedRef = useRef(false);

  useEffect(() => {
    const node = ref.current;
    if (!node) return;

    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduced) {
      setValue(end);
      return;
    }

    let raf = 0;
    let startTime = 0;

    const run = () => {
      const step = (now: number) => {
        if (!startTime) startTime = now;
        const progress = Math.min((now - startTime) / duration, 1);
        setValue(start + (end - start) * easeOutExpo(progress));
        if (progress < 1) raf = requestAnimationFrame(step);
      };
      raf = requestAnimationFrame(step);
    };

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting && !startedRef.current) {
            startedRef.current = true;
            run();
            if (once) observer.disconnect();
          }
        });
      },
      { threshold: 0.3 },
    );

    observer.observe(node);

    return () => {
      observer.disconnect();
      if (raf) cancelAnimationFrame(raf);
    };
  }, [end, start, duration, once]);

  return { ref, value };
}
