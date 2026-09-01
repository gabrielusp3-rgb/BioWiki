"use client";

import { cn } from "@/lib/cn";
import type { CategoryKey } from "@/lib/design-tokens";
import { CATEGORY_META } from "@/lib/categories";
import { useCountUp } from "@/hooks/useCountUp";
import { formatStatistic } from "@/lib/statistics";

export interface StatCardProps {
  value: number;
  label: string;
  suffix?: string;
  category?: CategoryKey;
  /** Optional index shown as a monospace ordinal (e.g. "01"). */
  index?: number;
  className?: string;
}

export function StatCard({
  value,
  label,
  suffix,
  category,
  index,
  className,
}: StatCardProps) {
  const { ref, value: animated } = useCountUp<HTMLDivElement>({ end: value });
  const meta = category ? CATEGORY_META[category] : undefined;
  const accent = meta?.color ?? "#00F2FF";

  return (
    <div
      ref={ref}
      aria-label={`${formatStatistic(value, suffix)} ${label}`}
      style={{ ["--glow-color" as string]: `${accent}40` }}
      className={cn(
        "glass hairline group relative flex flex-col justify-between gap-6 p-6 transition-colors duration-300 hover:border-white/20",
        className,
      )}
    >
      {/* Category accent bar */}
      <span
        aria-hidden
        className="absolute inset-x-0 top-0 h-px opacity-70 transition-opacity duration-300 group-hover:opacity-100"
        style={{ background: accent }}
      />

      <div className="flex items-center justify-between">
        {index !== undefined && (
          <span className="font-mono text-[11px] text-content-muted">
            {String(index).padStart(2, "0")}
          </span>
        )}
        <span
          className="h-1.5 w-1.5"
          style={{ backgroundColor: accent, boxShadow: `0 0 10px ${accent}` }}
        />
      </div>

      <div className="flex flex-col gap-2">
        <span
          className="font-display text-4xl font-bold tracking-tightest tabular-nums text-content-primary sm:text-5xl"
          style={{ textShadow: `0 0 32px ${accent}33` }}
        >
          {formatStatistic(animated, suffix)}
        </span>
        <span className="eyebrow text-content-secondary">{label}</span>
      </div>
    </div>
  );
}
